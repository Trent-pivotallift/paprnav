from __future__ import annotations

import hashlib
import os
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas
from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADPublication,
    ADSourceDocument,
    ADSourcePageRendition,
    ADSourcePageTextVersion,
    AirworthinessDirective,
    User,
)
from app.services.ad_evidence import admit_evidence_fragment
from app.services.ad_extraction import bounded_source_document_pages, extract_full_text_pages


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PAPRNAV_TEST_POSTGRES_URL is required for PostgreSQL concurrency verification",
)


def test_00_downgrade_waits_for_concurrent_evidence_then_refuses(
    tmp_path: Path,
) -> None:
    """A concurrent commit cannot land between downgrade preflight and DROP."""

    assert POSTGRES_URL is not None
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    identity = uuid.uuid4().hex
    with Session(engine) as db:
        document = ADSourceDocument(
            source_system="federal_register",
            source_type="document_pdf",
            source_identifier=f"downgrade-race-{identity}",
            storage_backend="local",
            storage_key=f"ad-sources/downgrade-race-{identity}.pdf",
            media_type="application/pdf",
            content_hash=hashlib.sha256(identity.encode()).hexdigest(),
            storage_bytes=1,
            captured_at=datetime.now(timezone.utc),
            status="retained",
        )
        db.add(document)
        db.commit()
        document_id = document.id
        source_hash = document.content_hash

    writer = engine.connect()
    transaction = writer.begin()
    writer.execute(text("LOCK TABLE ad_source_page_renditions IN ROW EXCLUSIVE MODE"))
    writer.execute(text("""
        INSERT INTO ad_source_page_renditions (
            id, source_document_id, source_content_hash, page_number,
            renderer_name, renderer_version, renderer_configuration_hash,
            media_type, width_px, height_px, storage_backend, storage_key,
            rendition_hash, storage_bytes
        ) VALUES (
            :id, :document_id, :source_hash, 1,
            'race-proof', '1', :configuration_hash,
            'image/png', 1, 1, 'local', :storage_key,
            :rendition_hash, 1
        )
    """), {
        "id": f"asr_{identity}",
        "document_id": document_id,
        "source_hash": source_hash,
        "configuration_hash": hashlib.sha256(b"race-config").hexdigest(),
        "storage_key": f"ad-evidence-pages/race-{identity}.png",
        "rendition_hash": hashlib.sha256(b"x").hexdigest(),
    })

    result: dict[str, subprocess.CompletedProcess[str]] = {}

    def downgrade() -> None:
        environment = os.environ.copy()
        environment["DATABASE_URL"] = POSTGRES_URL
        result["process"] = subprocess.run(
            ["alembic", "downgrade", "20260823_0024"],
            cwd=Path(__file__).parents[1],
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    thread = threading.Thread(target=downgrade, daemon=True)
    thread.start()
    time.sleep(1)
    assert thread.is_alive(), "downgrade did not wait for the concurrent evidence transaction"
    transaction.commit()
    writer.close()
    thread.join(timeout=30)
    process = result["process"]
    assert process.returncode != 0
    assert "contains immutable AD evidence" in f"{process.stdout}\n{process.stderr}"
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260830_0025"
        assert connection.scalar(text(
            "SELECT count(*) FROM ad_source_page_renditions WHERE id = :id"
        ), {"id": f"asr_{identity}"}) == 1
    engine.dispose()


def test_concurrent_fragment_admission_serializes_and_immutable_rows_reject_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert POSTGRES_URL is not None
    storage_root = tmp_path / "ad-evidence-storage"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    monkeypatch.setenv("PAPRNAV_STORAGE_BACKEND", "local")
    get_settings.cache_clear()
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    identity = uuid.uuid4().hex
    storage_key = f"ad-sources/postgres/{identity}.pdf"
    source_path = storage_root / storage_key
    source_path.parent.mkdir(parents=True, exist_ok=True)
    writer = canvas.Canvas(str(source_path))
    lines = (
        "14 CFR Part 39",
        "Section 39.13 is amended by adding the following new airworthiness directive:",
        "AD 2026-12-01 Example Aircraft.",
        "This AD applies to Example Model 100 airplanes.",
        "Before further flight, inspect the retained fitting for cracks.",
        "[FR Doc. 2026-12345]",
    )
    y = 720
    for line in lines:
        writer.drawString(72, y, line)
        y -= 24
    writer.save()
    source_bytes = source_path.read_bytes()

    with SessionLocal() as db:
        actor = User(
            email=f"concurrency-{identity}@paprnav.test",
            name="Concurrency Verifier",
            password_hash="not-used",
            status="active",
        )
        document = ADSourceDocument(
            source_system="federal_register",
            source_type="document_pdf",
            source_identifier=f"postgres-{identity}",
            storage_backend="local",
            storage_key=storage_key,
            media_type="application/pdf",
            content_hash=hashlib.sha256(source_bytes).hexdigest(),
            storage_bytes=len(source_bytes),
            captured_at=datetime.now(timezone.utc),
            status="retained",
        )
        directive = AirworthinessDirective(
            ad_number="2026-12-01",
            title="Example Aircraft",
            status="candidate",
            source_content_hash=document.content_hash,
            extraction_status="needs_review",
            review_status="pending",
        )
        db.add_all([actor, document, directive])
        db.flush()
        db.add(ADPublication(
            directive_id=directive.id,
            source_document_id=document.id,
            source_system="federal_register",
            source_type="document_pdf",
            source_identifier=f"postgres-{identity}",
            status="retained",
            content_hash=document.content_hash,
        ))
        db.commit()
        actor_id = actor.id
        directive_id = directive.id
        document_id = document.id
        source_hash = document.content_hash

    with SessionLocal() as db:
        directive = db.get(AirworthinessDirective, directive_id)
        assert directive is not None
        pages = bounded_source_document_pages(
            extract_full_text_pages(directive),
            ad_number=directive.ad_number,
            title=directive.title,
        )
        assert len(pages) == 1
        page_text = pages[0]["text"]
    page_text_hash = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
    action = "Before further flight, inspect the retained fitting for cracks."
    character_start = page_text.index(action)
    barrier = threading.Barrier(2)

    def admit() -> tuple[str, bool]:
        with SessionLocal() as db:
            actor = db.get(User, actor_id)
            assert actor is not None
            barrier.wait(timeout=10)
            fragment, created = admit_evidence_fragment(
                db,
                directive_id=directive_id,
                source_document_id=document_id,
                page_number=1,
                expected_source_content_hash=source_hash,
                expected_page_text_hash=page_text_hash,
                character_start=character_start,
                character_end=character_start + len(action),
                actor=actor,
                reason="PostgreSQL serialized admission proof.",
                paragraph_locator="(g)",
            )
            db.commit()
            return fragment.id, created

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result(timeout=30) for future in (executor.submit(admit), executor.submit(admit))]

    assert len({fragment_id for fragment_id, _ in results}) == 1
    assert sorted(created for _, created in results) == [False, True]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(ADSourcePageRendition).where(
            ADSourcePageRendition.source_document_id == document_id
        )) == 1
        assert db.scalar(
            select(func.count())
            .select_from(ADSourcePageTextVersion)
            .join(ADSourcePageRendition)
            .where(ADSourcePageRendition.source_document_id == document_id)
        ) == 1
        assert db.scalar(select(func.count()).select_from(ADEvidenceFragment).where(
            ADEvidenceFragment.directive_id == directive_id
        )) == 1
        assert db.scalar(
            select(func.count())
            .select_from(ADEvidenceFragmentLifecycleEvent)
            .join(ADEvidenceFragment)
            .where(ADEvidenceFragment.directive_id == directive_id)
        ) == 1

        fragment = db.scalar(select(ADEvidenceFragment).where(
            ADEvidenceFragment.directive_id == directive_id
        ))
        assert fragment is not None
        admitted_fragment_id = fragment.id
        rendition = db.get(ADSourcePageRendition, fragment.rendition_id)
        text_version = db.get(ADSourcePageTextVersion, fragment.page_text_version_id)
        event = db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
            ADEvidenceFragmentLifecycleEvent.fragment_id == fragment.id,
            ADEvidenceFragmentLifecycleEvent.event_type == "admitted",
        ))
        assert rendition is not None and text_version is not None and event is not None
        root_event_hash = event.event_hash
        fragment_hash = fragment.fragment_hash

        second_action = "This AD applies to Example Model 100 airplanes."
        second_start = page_text.index(second_action)
        actor = db.get(User, actor_id)
        assert actor is not None
        second_fragment, second_created = admit_evidence_fragment(
            db,
            directive_id=directive_id,
            source_document_id=document_id,
            page_number=1,
            expected_source_content_hash=source_hash,
            expected_page_text_hash=page_text_hash,
            character_start=second_start,
            character_end=second_start + len(second_action),
            actor=actor,
            reason="Cross-fragment predecessor proof fixture.",
            paragraph_locator="(c)",
        )
        assert second_created is True
        db.commit()
        second_root_hash = db.scalar(select(ADEvidenceFragmentLifecycleEvent.event_hash).where(
            ADEvidenceFragmentLifecycleEvent.fragment_id == second_fragment.id,
            ADEvidenceFragmentLifecycleEvent.event_type == "admitted",
        ))
        assert second_root_hash is not None

        with pytest.raises(DBAPIError, match="lifecycle predecessor mismatch"):
            db.execute(text("""
                INSERT INTO ad_evidence_fragment_lifecycle_events (
                    id, fragment_id, event_type, actor_user_id, reason,
                    sequence_number, predecessor_event_hash, event_hash
                ) VALUES (
                    :id, :fragment_id, 'quarantined', :actor_id, :reason,
                    1, :predecessor_hash,
                    paprnav_hash_parts(
                        :fragment_id_hash, :fragment_hash, 'quarantined',
                        :actor_id_hash, :reason, '1', :predecessor_hash_hash
                    )
                )
            """), {
                "id": f"afe_{uuid.uuid4().hex}",
                "fragment_id": fragment.id,
                "fragment_id_hash": fragment.id,
                "fragment_hash": fragment_hash,
                "actor_id": actor_id,
                "actor_id_hash": actor_id,
                "reason": "Cross-fragment predecessor must fail.",
                "predecessor_hash": second_root_hash,
                "predecessor_hash_hash": second_root_hash,
            })
            db.flush()
        db.rollback()

        successor_barrier = threading.Barrier(2)

        def append_successor(label: str) -> str:
            with SessionLocal() as successor_db:
                reason = f"Concurrent canonical successor {label}."
                successor_barrier.wait(timeout=10)
                try:
                    successor_db.execute(text("""
                        INSERT INTO ad_evidence_fragment_lifecycle_events (
                            id, fragment_id, event_type, actor_user_id, reason,
                            sequence_number, predecessor_event_hash, event_hash
                        ) VALUES (
                            :id, :fragment_id, 'quarantined', :actor_id, :reason,
                            1, :predecessor_hash,
                            paprnav_hash_parts(
                                :fragment_id_hash, :fragment_hash, 'quarantined',
                                :actor_id_hash, :reason, '1', :predecessor_hash_hash
                            )
                        )
                    """), {
                        "id": f"afe_{uuid.uuid4().hex}",
                        "fragment_id": admitted_fragment_id,
                        "fragment_id_hash": admitted_fragment_id,
                        "fragment_hash": fragment_hash,
                        "actor_id": actor_id,
                        "actor_id_hash": actor_id,
                        "reason": reason,
                        "predecessor_hash": root_event_hash,
                        "predecessor_hash_hash": root_event_hash,
                    })
                    successor_db.commit()
                except DBAPIError:
                    successor_db.rollback()
                    return "rejected"
                return "committed"

        with ThreadPoolExecutor(max_workers=2) as executor:
            successor_results = [
                future.result(timeout=30)
                for future in (
                    executor.submit(append_successor, "A"),
                    executor.submit(append_successor, "B"),
                )
            ]
        assert sorted(successor_results) == ["committed", "rejected"]
        assert db.scalar(select(func.count()).select_from(
            ADEvidenceFragmentLifecycleEvent
        ).where(
            ADEvidenceFragmentLifecycleEvent.fragment_id == admitted_fragment_id,
            ADEvidenceFragmentLifecycleEvent.sequence_number == 1,
        )) == 1

        mutations = (
            (ADSourcePageRendition, rendition.id, {"renderer_name": "tampered"}),
            (ADSourcePageTextVersion, text_version.id, {"extractor_name": "tampered"}),
            (ADEvidenceFragment, fragment.id, {"exact_text": "tampered"}),
            (ADEvidenceFragmentLifecycleEvent, event.id, {"reason": "tampered"}),
        )
        for model, row_id, values in mutations:
            with pytest.raises(DBAPIError, match="immutable AD evidence"):
                db.execute(update(model).where(model.id == row_id).values(**values))
            db.rollback()
            with pytest.raises(DBAPIError, match="immutable AD evidence"):
                db.execute(delete(model).where(model.id == row_id))
            db.rollback()

        with pytest.raises(DBAPIError, match="source chain mismatch"):
            db.execute(text("""
                INSERT INTO ad_evidence_fragments (
                    id, directive_id, source_document_id, source_content_hash,
                    rendition_id, page_text_version_id, page_start, page_end,
                    character_start, character_end, exact_text, fragment_hash,
                    parser_name, parser_version, created_by_user_id
                ) SELECT
                    :id, directive_id, source_document_id, :wrong_hash,
                    rendition_id, page_text_version_id, page_start, page_end,
                    character_start, character_end, exact_text, :fragment_hash,
                    parser_name, parser_version, created_by_user_id
                FROM ad_evidence_fragments WHERE id = :source_id
            """), {
                "id": f"aef_{uuid.uuid4().hex}",
                "wrong_hash": "0" * 64,
                "fragment_hash": "1" * 64,
                "source_id": fragment.id,
            })
            db.flush()
        db.rollback()

        with pytest.raises(DBAPIError, match="selector exceeds page text"):
            db.execute(text("""
                INSERT INTO ad_evidence_fragments (
                    id, directive_id, source_document_id, source_content_hash,
                    rendition_id, page_text_version_id, page_start, page_end,
                    paragraph_locator, table_locator, row_locator, note_locator,
                    character_start, character_end, region_map_hash, exact_text,
                    fragment_hash, parser_name, parser_version, created_by_user_id
                ) SELECT
                    :id, f.directive_id, f.source_document_id, f.source_content_hash,
                    f.rendition_id, f.page_text_version_id, f.page_start, f.page_end,
                    NULL, NULL, NULL, NULL, 0, char_length(t.page_text) + 5, NULL,
                    t.page_text,
                    paprnav_hash_parts(
                        f.directive_id, f.source_document_id, f.source_content_hash,
                        f.rendition_id, f.page_text_version_id,
                        f.page_start::text, f.page_end::text, '0',
                        (char_length(t.page_text) + 5)::text,
                        NULL, NULL, NULL, NULL, NULL, t.page_text,
                        f.parser_name, f.parser_version
                    ),
                    f.parser_name, f.parser_version, f.created_by_user_id
                FROM ad_evidence_fragments f
                JOIN ad_source_page_text_versions t ON t.id = f.page_text_version_id
                WHERE f.id = :source_id
            """), {"id": f"aef_{uuid.uuid4().hex}", "source_id": fragment.id})
            db.flush()
        db.rollback()

        with pytest.raises(DBAPIError, match="parser provenance mismatch"):
            db.execute(text("""
                INSERT INTO ad_evidence_fragments (
                    id, directive_id, source_document_id, source_content_hash,
                    rendition_id, page_text_version_id, page_start, page_end,
                    paragraph_locator, table_locator, row_locator, note_locator,
                    character_start, character_end, region_map_hash, exact_text,
                    fragment_hash, parser_name, parser_version, created_by_user_id
                ) SELECT
                    :id, f.directive_id, f.source_document_id, f.source_content_hash,
                    f.rendition_id, f.page_text_version_id, f.page_start, f.page_end,
                    NULL, NULL, NULL, NULL, 0, 2, NULL,
                    substring(t.page_text FROM 1 FOR 2),
                    paprnav_hash_parts(
                        f.directive_id, f.source_document_id, f.source_content_hash,
                        f.rendition_id, f.page_text_version_id,
                        f.page_start::text, f.page_end::text, '0', '2',
                        NULL, NULL, NULL, NULL, NULL,
                        substring(t.page_text FROM 1 FOR 2),
                        'forged-parser', f.parser_version
                    ),
                    'forged-parser', f.parser_version, f.created_by_user_id
                FROM ad_evidence_fragments f
                JOIN ad_source_page_text_versions t ON t.id = f.page_text_version_id
                WHERE f.id = :source_id
            """), {"id": f"aef_{uuid.uuid4().hex}", "source_id": fragment.id})
            db.flush()
        db.rollback()

        with pytest.raises(DBAPIError, match="lifecycle event hash mismatch"):
            db.execute(text("""
                INSERT INTO ad_evidence_fragment_lifecycle_events (
                    id, fragment_id, event_type, actor_user_id, reason,
                    sequence_number, predecessor_event_hash, event_hash
                ) VALUES (
                    :id, :fragment_id, 'admitted', :actor_id, 'forged root',
                    0, NULL, :event_hash
                )
            """), {
                "id": f"afe_{uuid.uuid4().hex}",
                "fragment_id": fragment.id,
                "actor_id": actor_id,
                "event_hash": "f" * 64,
            })
            db.flush()
        db.rollback()

    with pytest.raises(DBAPIError, match="lacks a valid admission root"):
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO ad_evidence_fragments (
                    id, directive_id, source_document_id, source_content_hash,
                    rendition_id, page_text_version_id, page_start, page_end,
                    paragraph_locator, table_locator, row_locator, note_locator,
                    character_start, character_end, region_map_hash, exact_text,
                    fragment_hash, parser_name, parser_version, created_by_user_id
                ) SELECT
                    :id, f.directive_id, f.source_document_id, f.source_content_hash,
                    f.rendition_id, f.page_text_version_id, f.page_start, f.page_end,
                    NULL, NULL, NULL, NULL, 0, 1, NULL,
                    substring(t.page_text FROM 1 FOR 1),
                    paprnav_hash_parts(
                        f.directive_id, f.source_document_id, f.source_content_hash,
                        f.rendition_id, f.page_text_version_id,
                        f.page_start::text, f.page_end::text, '0', '1',
                        NULL, NULL, NULL, NULL, NULL,
                        substring(t.page_text FROM 1 FOR 1),
                        f.parser_name, f.parser_version
                    ),
                    f.parser_name, f.parser_version, f.created_by_user_id
                FROM ad_evidence_fragments f
                JOIN ad_source_page_text_versions t ON t.id = f.page_text_version_id
                WHERE f.id = :source_id
            """), {"id": f"aef_{uuid.uuid4().hex}", "source_id": admitted_fragment_id})

    engine.dispose()
    get_settings.cache_clear()
