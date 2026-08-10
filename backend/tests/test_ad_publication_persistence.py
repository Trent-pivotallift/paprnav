import hashlib
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.core import (
    ADCostLedgerEntry,
    ADPublication,
    ADReconciliationIssue,
    ADSourceDocument,
    ADSourceSnapshot,
)
from app.services.ad_publication_persistence import apply_publication_proof
from app.services.drs_bulk_import import import_drs_bulk_rows


def test_publication_proof_augments_drs_catalog_idempotently(db_session) -> None:
    import_drs_bulk_rows(
        db_session,
        [
            {
                "AD Number": "2026-01-02",
                "Product Type": "Aircraft",
                "Make": "Cessna",
                "Model": "172G",
                "Status": "Current",
                "guid": "drs-row",
            }
        ],
        content_hash="a" * 64,
    )
    manifest = {
        "proofVersion": "test",
        "targetDirectiveCount": 1,
        "federalRegisterExactMatchCount": 1,
        "govinfoPackageCount": 1,
        "verification": {"passed": 5, "total": 5},
        "records": [
            {
                "sourceAdNumber": "2026-01-02",
                "publicationDate": "2026-02-03",
                "publicationStatus": "resolved_govinfo",
                "federalRegisterExactMatches": ["2026-12345"],
                "govinfoPackageId": "FR-2026-02-03",
            }
        ],
        "govinfoPackages": {
            "FR-2026-02-03": {
                "status": "resolved",
                "sha256": "b" * 64,
                "dateIssued": "2026-02-03",
                "pdfUrl": "https://api.govinfo.gov/example.pdf",
            }
        },
    }

    first = apply_publication_proof(
        db_session,
        manifest,
        content_hash="c" * 64,
        filename="publication-proof.json",
    )
    second = apply_publication_proof(
        db_session,
        manifest,
        content_hash="c" * 64,
        filename="publication-proof.json",
    )

    assert first == second
    assert first["federal_register_publications"] == 1
    assert first["govinfo_publications"] == 1
    assert db_session.scalar(select(func.count()).select_from(ADSourceSnapshot)) == 2
    assert db_session.scalar(select(func.count()).select_from(ADPublication)) == 3
    assert db_session.scalar(select(func.count()).select_from(ADReconciliationIssue)) == 0


def test_publication_proof_retains_payloads_and_pdfs_idempotently(
    db_session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(tmp_path / "storage"))
    get_settings.cache_clear()
    import_drs_bulk_rows(
        db_session,
        [
            {
                "AD Number": "2026-01-02",
                "Product Type": "Aircraft",
                "Make": "Cessna",
                "Model": "172G",
                "Status": "Current",
                "guid": "drs-row-artifacts",
            }
        ],
        content_hash="d" * 64,
    )
    initial_cost_entries = len(
        db_session.scalars(select(ADCostLedgerEntry)).all()
    )

    def artifact(name: str, data: bytes, media_type: str, source_url: str) -> dict:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {
            "path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "mediaType": media_type,
            "sourceUrl": source_url,
            "filename": path.name,
        }

    fr_search = artifact(
        "federal-register-search/ad.json",
        b'{"count": 1}',
        "application/json",
        "https://www.federalregister.gov/api/v1/documents.json",
    )
    fr_payload = artifact(
        "federal-register-document/rule.json",
        b'{"document_number": "2026-12345"}',
        "application/json",
        "https://www.federalregister.gov/d/2026-12345.json",
    )
    fr_pdf = artifact(
        "federal-register-document-pdf/rule.pdf",
        b"%PDF-1.4\n% retained FR rule\n",
        "application/pdf",
        "https://www.govinfo.gov/content/pkg/example.pdf",
    )
    govinfo_summary = artifact(
        "govinfo-summary/issue.json",
        b'{"packageId": "FR-2026-02-03"}',
        "application/json",
        "https://api.govinfo.gov/packages/FR-2026-02-03/summary",
    )
    govinfo_pdf = artifact(
        "govinfo-issue-pdf/issue.pdf",
        b"%PDF-1.4\n% retained GovInfo issue\n",
        "application/pdf",
        "https://api.govinfo.gov/packages/FR-2026-02-03/pdf",
    )
    manifest = {
        "proofVersion": "test-with-artifacts",
        "targetDirectiveCount": 1,
        "retainedBytes": sum(
            item["bytes"]
            for item in (
                fr_search,
                fr_payload,
                fr_pdf,
                govinfo_summary,
                govinfo_pdf,
            )
        ),
        "records": [
            {
                "sourceAdNumber": "2026-01-02",
                "canonicalAdNumber": "2026-01-02",
                "publicationDate": "2026-02-03",
                "publicationStatus": "resolved_govinfo",
                "federalRegisterExactMatches": ["2026-12345"],
                "federalRegisterSearchArtifact": fr_search,
                "federalRegisterDocuments": [
                    {
                        "documentNumber": "2026-12345",
                        "payloadArtifact": fr_payload,
                        "pdfArtifact": fr_pdf,
                    }
                ],
                "govinfoPackageId": "FR-2026-02-03",
            }
        ],
        "govinfoPackages": {
            "FR-2026-02-03": {
                "status": "resolved",
                "dateIssued": "2026-02-03",
                "pdfUrl": govinfo_pdf["sourceUrl"],
                "summaryArtifact": govinfo_summary,
                "pdfArtifact": govinfo_pdf,
                "adNumbers": ["2026-01-02"],
            }
        },
    }

    first = apply_publication_proof(
        db_session,
        manifest,
        content_hash="e" * 64,
        filename="publication-proof.json",
        artifact_root=tmp_path,
    )
    second = apply_publication_proof(
        db_session,
        manifest,
        content_hash="e" * 64,
        filename="publication-proof.json",
        artifact_root=tmp_path,
    )

    assert first == second
    assert first["source_documents"] == 5
    assert first["publications_linked_to_documents"] == 2
    documents = db_session.scalars(select(ADSourceDocument)).all()
    assert len(documents) == 5
    assert len(db_session.scalars(select(ADCostLedgerEntry)).all()) == initial_cost_entries + 5
    linked = db_session.scalars(
        select(ADPublication).where(ADPublication.source_document_id.is_not(None))
    ).all()
    assert len(linked) == 2
    assert {publication.source_document.media_type for publication in linked} == {
        "application/pdf"
    }
    assert all(
        (tmp_path / "storage" / document.storage_key).exists()
        for document in documents
    )
    snapshot = db_session.scalar(
        select(ADSourceSnapshot).where(
            ADSourceSnapshot.source_system == "publication_reconciliation"
        )
    )
    assert snapshot.storage_bytes == manifest["retainedBytes"]
    assert snapshot.table_inventory["federalRegisterDocumentPdfs"] == 1
    assert snapshot.table_inventory["govinfoIssuePdfs"] == 1
    get_settings.cache_clear()


def test_artifact_complete_manifest_rejects_missing_source_artifacts(
    db_session,
) -> None:
    with pytest.raises(
        ValueError,
        match="missing a Federal Register search payload",
    ):
        apply_publication_proof(
            db_session,
            {
                "proofVersion": "ad_publication_reconciliation_v2",
                "verification": {"passed": 7, "total": 7},
                "records": [{"sourceAdNumber": "2026-01-02"}],
                "govinfoPackages": {},
            },
            content_hash="f" * 64,
            filename="incomplete-publication-proof.json",
        )
