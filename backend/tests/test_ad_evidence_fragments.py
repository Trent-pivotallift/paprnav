from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.routes.ads import serialize_source_document
from app.core.config import get_settings
from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADPublication,
    ADSourceDocument,
    ADSourcePageRendition,
    ADSourcePageTextVersion,
    AirworthinessDirective,
)
from tests.conftest import add_membership, create_organization, create_user, login


def _retained_directive_pdf(
    db: Session,
    tmp_path: Path,
    *,
    ad_number: str,
    source_identifier: str,
    filename: str,
) -> tuple[AirworthinessDirective, ADSourceDocument, Path]:
    local_root = Path(get_settings().local_storage_path)
    storage_key = f"ad-sources/test/{filename}"
    pdf_path = local_root / storage_key
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    writer = canvas.Canvas(str(pdf_path))
    writer.drawString(72, 720, "Unrelated agency notice on page one.")
    writer.showPage()
    lines = (
        "14 CFR Part 39",
        "Section 39.13 is amended by adding the following new airworthiness directive:",
        f"AD {ad_number} Example Aircraft.",
        "This AD applies to Example Model 100 airplanes.",
        "Before further flight, inspect the retained fitting for cracks.",
        "[FR Doc. 2026-12345]",
    )
    y = 720
    for line in lines:
        writer.drawString(72, y, line)
        y -= 24
    writer.save()
    retained_bytes = pdf_path.read_bytes()
    document = ADSourceDocument(
        source_system="federal_register",
        source_type="document_pdf",
        source_identifier=source_identifier,
        storage_backend="local",
        storage_key=storage_key,
        media_type="application/pdf",
        content_hash=hashlib.sha256(retained_bytes).hexdigest(),
        storage_bytes=len(retained_bytes),
        captured_at=datetime.now(timezone.utc),
        status="retained",
    )
    directive = AirworthinessDirective(
        ad_number=ad_number,
        title="Example Aircraft",
        status="candidate",
        source_content_hash=document.content_hash,
        extraction_status="needs_review",
        review_status="pending",
    )
    db.add_all([directive, document])
    db.flush()
    db.add(ADPublication(
        directive_id=directive.id,
        source_document_id=document.id,
        source_system="federal_register",
        source_type="document_pdf",
        source_identifier=source_identifier,
        status="retained",
        content_hash=document.content_hash,
    ))
    db.commit()
    return directive, document, pdf_path


def _platform_admin(db: Session, email: str = "evidence.admin@paprnav.local") -> None:
    admin = create_user(db, email, "Evidence Admin")
    organization = create_organization(db, "Paprnav Evidence Operations", "platform")
    add_membership(db, organization, admin, "platform_admin")
    db.commit()


def test_source_document_navigation_uses_exact_bounded_page_range() -> None:
    document = ADSourceDocument(
        id="asd_navigation",
        source_system="govinfo",
        source_type="issue_pdf",
        source_identifier="FR-2024-07-16",
        storage_backend="local",
        storage_key="ad-sources/navigation.pdf",
        media_type="application/pdf",
        content_hash="a" * 64,
        storage_bytes=100,
        captured_at=datetime.now(timezone.utc),
        status="retained",
    )

    response = serialize_source_document(document, relevant_page_numbers=[40, 35, 37, 37])

    assert response.relevantPageStart == 35
    assert response.relevantPageEnd == 40
    assert response.relevantPageNumbers == [35, 37, 40]
    assert response.relevantPagesContiguous is False
    assert response.contentUrl.endswith("/asd_navigation/content")
    assert response.navigationUrl.endswith("/asd_navigation/content#page=35")


def test_admin_fragment_admission_is_hash_bound_deduplicated_and_single_page(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    tmp_path: Path,
) -> None:
    directive, document, _ = _retained_directive_pdf(
        db_session,
        tmp_path,
        ad_number="2026-12-01",
        source_identifier="2026-12345",
        filename="evidence.pdf",
    )
    _platform_admin(db_session)
    login(client, "evidence.admin@paprnav.local")
    page_url = f"/api/v1/ads/source-documents/{document.id}/pages/2"
    missing_page = client.get(page_url, params={
        "directiveId": directive.id,
        "expectedSourceContentHash": document.content_hash,
    })
    assert missing_page.status_code == 404
    assert db_session.scalar(select(func.count()).select_from(ADSourcePageRendition)) == 0
    page_response = client.post(f"{page_url}/materialization", json={
        "directiveId": directive.id,
        "expectedSourceContentHash": document.content_hash,
    })
    assert page_response.status_code == 200, page_response.text
    page_read = client.get(page_url, params={
        "directiveId": directive.id,
        "expectedSourceContentHash": document.content_hash,
    })
    assert page_read.status_code == 200
    assert page_read.json() == page_response.json()
    page = page_response.json()
    action = "Before further flight, inspect the retained fitting for cracks."
    start = page["pageText"].index(action)
    payload = {
        "directiveId": directive.id,
        "pageNumber": 2,
        "expectedSourceContentHash": document.content_hash,
        "expectedPageTextHash": page["pageTextHash"],
        "characterStart": start,
        "characterEnd": start + len(action),
        "paragraphLocator": "(g)",
        "reason": "Exact compliance clause selected from retained rule.",
    }
    first = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json=payload,
    )
    assert first.status_code == 200, first.text
    assert first.json()["created"] is True
    assert first.json()["exactText"] == action
    assert first.json()["pageStart"] == first.json()["pageEnd"] == 2

    repeated = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json=payload,
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["created"] is False
    assert repeated.json()["id"] == first.json()["id"]
    assert db_session.scalar(select(func.count()).select_from(ADSourcePageRendition)) == 1
    assert db_session.scalar(select(func.count()).select_from(ADSourcePageTextVersion)) == 1
    assert db_session.scalar(select(func.count()).select_from(ADEvidenceFragment)) == 1
    assert db_session.scalar(select(func.count()).select_from(ADEvidenceFragmentLifecycleEvent)) == 1

    # A maintenance shop may inspect aircraft-scoped state but may not mutate
    # the shared regulatory evidence domain.
    login(client, "shop.test@paprnav.local")
    forbidden_page = client.get(page_url, params={
        "directiveId": directive.id,
        "expectedSourceContentHash": document.content_hash,
    })
    assert forbidden_page.status_code == 403
    forbidden = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json=payload,
    )
    assert forbidden.status_code == 403
    assert db_session.scalar(select(func.count()).select_from(ADEvidenceFragment)) == 1


def test_fragment_api_fails_closed_for_wrong_document_hash_page_and_selection(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    directive, document, document_path = _retained_directive_pdf(
        db_session,
        tmp_path,
        ad_number="2026-12-01",
        source_identifier="2026-12345",
        filename="correct.pdf",
    )
    other_directive, other_document, _ = _retained_directive_pdf(
        db_session,
        tmp_path,
        ad_number="2026-12-02",
        source_identifier="2026-12346",
        filename="other.pdf",
    )
    _platform_admin(db_session, "negative.evidence.admin@paprnav.local")
    login(client, "negative.evidence.admin@paprnav.local")

    wrong_document = client.get(
        f"/api/v1/ads/source-documents/{other_document.id}/pages/2",
        params={
            "directiveId": directive.id,
            "expectedSourceContentHash": other_document.content_hash,
        },
    )
    assert wrong_document.status_code == 422
    assert "not attributable" in wrong_document.json()["detail"]

    wrong_hash = client.get(
        f"/api/v1/ads/source-documents/{document.id}/pages/2",
        params={
            "directiveId": directive.id,
            "expectedSourceContentHash": "0" * 64,
        },
    )
    assert wrong_hash.status_code == 409

    omitted_page = client.get(
        f"/api/v1/ads/source-documents/{document.id}/pages/1",
        params={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    )
    assert omitted_page.status_code == 422
    assert "absent from the bounded official section" in omitted_page.json()["detail"]

    page = client.post(
        f"/api/v1/ads/source-documents/{document.id}/pages/2/materialization",
        json={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    ).json()
    rendition = db_session.scalar(select(ADSourcePageRendition))
    assert rendition is not None
    rendition_path = Path(get_settings().local_storage_path) / rendition.storage_key
    original_rendition = rendition_path.read_bytes()
    rendition_path.write_bytes(b"tampered PNG")
    tampered_rendition = client.get(
        f"/api/v1/ads/source-documents/{document.id}/pages/2",
        params={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    )
    assert tampered_rendition.status_code == 409
    assert "rendition" in tampered_rendition.json()["detail"].lower()
    rendition_path.write_bytes(original_rendition)
    base_payload = {
        "directiveId": directive.id,
        "pageNumber": 2,
        "expectedSourceContentHash": document.content_hash,
        "expectedPageTextHash": page["pageTextHash"],
        "characterStart": 0,
        "characterEnd": 5,
        "reason": "Negative boundary test.",
    }
    stale_page = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json={**base_payload, "expectedPageTextHash": "f" * 64},
    )
    assert stale_page.status_code == 409
    out_of_bounds = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json={**base_payload, "characterEnd": len(page["pageText"]) + 1},
    )
    assert out_of_bounds.status_code == 422
    reversed_selection = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments",
        json={**base_payload, "characterStart": 5, "characterEnd": 5},
    )
    assert reversed_selection.status_code == 422

    document_path.write_bytes(b"%PDF-1.4\ntampered\n%%EOF\n")
    tampered = client.get(
        f"/api/v1/ads/source-documents/{document.id}/pages/2",
        params={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    )
    assert tampered.status_code == 409
    assert other_directive.id != directive.id


def test_new_rendition_requires_successful_storage_readback(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    directive, document, _ = _retained_directive_pdf(
        db_session,
        tmp_path,
        ad_number="2026-12-03",
        source_identifier="2026-12347",
        filename="corrupt-readback.pdf",
    )
    _platform_admin(db_session, "readback.evidence.admin@paprnav.local")
    login(client, "readback.evidence.admin@paprnav.local")
    monkeypatch.setattr("app.services.ad_evidence.read_stored_file_bytes", lambda **_: b"corrupt")

    response = client.post(
        f"/api/v1/ads/source-documents/{document.id}/pages/2/materialization",
        json={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    )

    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(ADSourcePageRendition)) == 0


def test_fragment_reuse_fails_closed_without_valid_admission_root(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    directive, document, _ = _retained_directive_pdf(
        db_session,
        tmp_path,
        ad_number="2026-12-04",
        source_identifier="2026-12348",
        filename="missing-admission.pdf",
    )
    _platform_admin(db_session, "root.evidence.admin@paprnav.local")
    login(client, "root.evidence.admin@paprnav.local")
    page = client.post(
        f"/api/v1/ads/source-documents/{document.id}/pages/2/materialization",
        json={
            "directiveId": directive.id,
            "expectedSourceContentHash": document.content_hash,
        },
    ).json()
    action = "Before further flight, inspect the retained fitting for cracks."
    start = page["pageText"].index(action)
    payload = {
        "directiveId": directive.id,
        "pageNumber": 2,
        "expectedSourceContentHash": document.content_hash,
        "expectedPageTextHash": page["pageTextHash"],
        "characterStart": start,
        "characterEnd": start + len(action),
        "reason": "Admission root validation.",
    }
    assert client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments", json=payload
    ).status_code == 200
    db_session.execute(delete(ADEvidenceFragmentLifecycleEvent))
    db_session.commit()

    repeated = client.post(
        f"/api/v1/ads/source-documents/{document.id}/fragments", json=payload
    )

    assert repeated.status_code == 409
    assert "admission root" in repeated.json()["detail"]
