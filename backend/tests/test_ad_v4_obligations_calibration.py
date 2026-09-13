from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import ADV4FeatureGate, AirworthinessDirective
from app.services.ad_evidence import admit_evidence_fragment
from app.services.ad_v4_applicability import materialize_applicability
from app.services.ad_v4_candidates import (
    CANONICALIZATION_VERSION_V2,
    VALIDATOR_VERSION_V2,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
)
from app.services.ad_v4_obligation_persistence import (
    materialize_obligations,
    reconstruct_obligation_projection,
)
from conftest import add_membership, create_organization, create_user
from test_ad_v4_applicability_calibration import validator2_calibration_envelope
from test_ad_v4_calibration import (
    SOURCES,
    _executable,
    _load_template,
    _packet_fragments,
    _retain_packet_sources,
)


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
OBLIGATION_KEYS = (
    "incorporatedDocuments",
    "requirements",
    "recurrenceGroups",
    "amocAuthorityProvisions",
)
RELEASED_V3_STATE_TABLES = (
    "airworthiness_directives",
    "ad_supersessions",
    "applicability_targets",
    "ad_publications",
    "ad_target_applicability",
    "ad_compliance_requirements",
    "ad_compliance_triggers",
    "ad_amoc_provisions",
    "ad_compliance_events",
    "aircraft_time_states",
    "aircraft_ad_due_states",
    "ad_coverage_sets",
    "ad_coverage_subscriptions",
    "ad_extraction_reviews",
    "ad_extraction_review_decisions",
    "ad_match_results",
    "ad_match_due_state_links",
    "ad_match_evidence",
    "ad_match_adjudications",
)


def _enable_all_gates(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED", "true")
    get_settings.cache_clear()
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        for gate in (
            "validator2_write_enabled",
            "materializer3a_enabled",
            "materializer3b_enabled",
        ):
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate(:gate,true,'calibration')"
            ), {"gate": gate})
        db.commit()
        return
    db.add_all([
        ADV4FeatureGate(
            gate_key=gate,
            enabled=True,
            changed_by="calibration",
        )
        for gate in (
            "validator2_write_enabled",
            "materializer3a_enabled",
            "materializer3b_enabled",
        )
    ])
    db.flush()


def _assert_packet_semantics(packet_key: str, subtree: dict) -> None:
    requirements = subtree["requirements"]
    if packet_key == "2024-14-03":
        assert len(requirements) == 2
        assert {item["action"]["actionType"] for item in requirements} == {
            "software_update",
            "installation_prohibition",
        }
    elif packet_key == "2011-10-09":
        assert len(requirements) == 10
        assert sum(
            len(item.get("prerequisiteRequirementKeys", []))
            for item in requirements
        ) == 9
        groups = subtree["recurrenceGroups"]
        assert len(groups) == 1
        assert len(groups[0]["requirementKeys"]) == 10
        assert groups[0]["initialTiming"]["logic"] == "whichever_first"
        assert groups[0]["recurringTiming"]["logic"] == "whichever_first"
    elif packet_key == "2002-13-04":
        assert len(requirements) == 4
        assert any(item["branch"]["kind"] == "conditional" for item in requirements)
        assert any(
            item["action"]["actionType"] == "installation_prohibition"
            for item in requirements
        )
    elif packet_key == "1998-17-11":
        assert len(requirements) == 4
        assert len(subtree["incorporatedDocuments"]) == 1
        assert any(
            item["branch"]["kind"] == "alternative_member"
            for item in requirements
        )
        assert any(
            item["action"]["actionType"] == "rework"
            for item in requirements
        )
        assert any(
            item["action"]["approvedDataDocumentRefKeys"]
            for item in requirements
        )
    elif packet_key == "2008-26-10":
        assert len(subtree["incorporatedDocuments"]) == 4
        assert len(requirements) == 6
        assert len(subtree["amocAuthorityProvisions"]) == 1


def _released_v3_state_snapshot(db: Session) -> dict[str, list] | None:
    if db.bind is None or db.bind.dialect.name != "postgresql":
        return None
    db.flush()
    snapshot = {}
    for table in RELEASED_V3_STATE_TABLES:
        snapshot[table] = db.scalar(text(
            f"SELECT coalesce(jsonb_agg(to_jsonb(source_row) "
            f"ORDER BY to_jsonb(source_row)::text),'[]'::jsonb) "
            f"FROM {table} source_row"
        ))
    return snapshot


def _round_trip_five_packets(
    db: Session,
    *,
    storage_root: Path,
) -> None:
    for packet in SOURCES["packets"]:
        packet_key = packet["packet"]
        actor = create_user(
            db,
            f"v4-obligation-{packet_key}@example.test",
            "V4 Obligation Calibration Admin",
        )
        organization = create_organization(
            db,
            f"V4 Obligation Calibration {packet_key}",
            "platform",
        )
        membership = add_membership(db, organization, actor, "platform_admin")
        directive = AirworthinessDirective(
            ad_number=packet["adNumber"],
            title="",
            status="candidate",
            source_content_hash=packet["documents"][0]["sha256"],
        )
        db.add(directive)
        db.flush()
        retained = _retain_packet_sources(db, packet, directive, storage_root)
        db.expire(directive, ["publications"])
        admitted = {}
        for item in _packet_fragments(packet_key).values():
            document = retained[item["sourceKey"]]
            locators = item.get("locators", {})
            fragment, _ = admit_evidence_fragment(
                db,
                directive_id=directive.id,
                source_document_id=document.id,
                page_number=int(item["pageNumber"]),
                expected_source_content_hash=document.content_hash,
                expected_page_text_hash=item["pageTextHash"],
                character_start=int(item["characterStart"]),
                character_end=int(item["characterEnd"]),
                actor=actor,
                reason="Slice-3B calibration",
                paragraph_locator=locators.get("paragraph"),
                table_locator=locators.get("table"),
                row_locator=locators.get("row"),
                note_locator=locators.get("note"),
            )
            admitted[item["evidenceKey"]] = fragment
        envelope = validator2_calibration_envelope(
            packet_key,
            _executable(
                packet,
                _load_template(packet),
                admitted_fragments=admitted,
                retained_documents=retained,
                directive_id=directive.id,
            ),
        )
        stored = store_v4_candidate(
            db,
            directive_id=directive.id,
            parsed=parse_v4_request_bytes(json.dumps(
                envelope,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()),
            actor=actor,
            membership_id=membership.id,
            idempotency_key=f"v2-obligation-calibration-{packet_key}",
            validator_version=VALIDATOR_VERSION_V2,
        )
        app_result = materialize_applicability(
            db,
            directive_id=directive.id,
            proposal_id=stored.proposal.id,
            actor=actor,
            membership_id=membership.id,
            idempotency_key=f"v3a-obligation-calibration-{packet_key}",
        )
        released_v3_before = _released_v3_state_snapshot(db)
        obligation_result = materialize_obligations(
            db,
            directive_id=directive.id,
            proposal_id=stored.proposal.id,
            app_projection_id=app_result.projection.id,
            actor=actor,
            membership_id=membership.id,
            idempotency_key=f"v3b-obligation-calibration-{packet_key}",
        )
        subtree = reconstruct_obligation_projection(
            db,
            obligation_result.projection,
        )
        expected = {
            key: envelope["proposal"][key]
            for key in OBLIGATION_KEYS
        }
        assert canonical_bytes(
            subtree,
            CANONICALIZATION_VERSION_V2,
        ) == canonical_bytes(expected, CANONICALIZATION_VERSION_V2)
        _assert_packet_semantics(packet_key, subtree)
        assert _released_v3_state_snapshot(db) == released_v3_before
        # Slice-3A/3B materialization deliberately forces deferred constraints
        # immediate. Commit each real packet so the next evidence admission
        # begins a new transaction with its admission-root trigger deferred.
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.commit()


def test_five_packet_obligation_round_trip(
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_all_gates(db_session, monkeypatch)
    storage_root = tmp_path / "retained-evidence"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    get_settings.cache_clear()
    _round_trip_five_packets(db_session, storage_root=storage_root)


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PAPRNAV_TEST_POSTGRES_URL required",
)
def test_five_packet_obligation_postgres_deferred_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    storage_root = tmp_path / "retained-evidence-postgres"
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(storage_root))
    with Session(engine, expire_on_commit=False) as db:
        _enable_all_gates(db, monkeypatch)
        _round_trip_five_packets(db, storage_root=storage_root)
        db.commit()
    engine.dispose()
