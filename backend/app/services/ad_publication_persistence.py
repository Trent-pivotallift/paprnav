from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.core import (
    ADPublication,
    ADReconciliationIssue,
    ADSourceDocument,
    ADSourceSnapshot,
    AirworthinessDirective,
)
from app.services.ad_identity import parse_ad_identity
from app.services.ad_source_catalog import retain_source_document


PARSER_NAME = "ad_publication_proof_persistence"
PARSER_VERSION = "0.1.0"
ARTIFACT_COMPLETE_PROOF_VERSION = "ad_publication_reconciliation_v2"


def apply_publication_proof_file(
    db: Session,
    path: str | Path,
    *,
    artifact_root: str | Path | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    source = Path(path)
    data = source.read_bytes()
    return apply_publication_proof(
        db,
        json.loads(data),
        content_hash=hashlib.sha256(data).hexdigest(),
        filename=source.name,
        artifact_root=Path(artifact_root) if artifact_root else source.parent,
        settings=settings,
    )


def apply_publication_proof(
    db: Session,
    manifest: dict[str, Any],
    *,
    content_hash: str,
    filename: str,
    artifact_root: str | Path | None = None,
    settings: Settings | None = None,
) -> dict[str, int]:
    settings = settings or get_settings()
    retained_root = Path(artifact_root).resolve() if artifact_root else None
    validate_publication_manifest(manifest)
    artifact_inventory = publication_artifact_inventory(manifest)
    snapshot = db.scalar(
        select(ADSourceSnapshot).where(
            ADSourceSnapshot.source_system == "publication_reconciliation",
            ADSourceSnapshot.content_hash == content_hash,
        )
    )
    if snapshot is None:
        snapshot = ADSourceSnapshot(
            source_system="publication_reconciliation",
            source_type="federal_register_govinfo_proof",
            filename=filename,
            content_hash=content_hash,
            captured_at=datetime.now(timezone.utc),
            status="complete",
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            row_count=int(manifest.get("targetDirectiveCount") or 0),
            table_inventory=artifact_inventory,
            metadata_json={},
            storage_bytes=int(manifest.get("retainedBytes") or 0) or None,
        )
        db.add(snapshot)
        db.flush()
    snapshot.table_inventory = artifact_inventory
    snapshot.storage_bytes = int(manifest.get("retainedBytes") or 0) or None
    snapshot.metadata_json = {
        "proofVersion": manifest.get("proofVersion"),
        "verification": manifest.get("verification"),
        "checks": manifest.get("checks"),
        "federalRegisterExactMatchCount": manifest.get(
            "federalRegisterExactMatchCount"
        ),
        "govinfoPackageCount": manifest.get("govinfoPackageCount"),
        "unresolvedPublicationDates": manifest.get("unresolvedPublicationDates"),
        "unresolvedGovInfoPackages": manifest.get("unresolvedGovInfoPackages"),
    }

    stats = {
        "records_seen": 0,
        "federal_register_publications": 0,
        "govinfo_publications": 0,
        "needs_adjudication": 0,
        "missing_directives": 0,
        "source_documents": 0,
        "publications_linked_to_documents": 0,
    }
    packages = manifest.get("govinfoPackages") or {}
    for record in manifest.get("records") or []:
        stats["records_seen"] += 1
        search_document = retain_manifest_artifact(
            db,
            artifact=record.get("federalRegisterSearchArtifact"),
            artifact_root=retained_root,
            settings=settings,
            snapshot=snapshot,
            source_system="federal_register",
            source_type="search_response",
            source_identifier=str(record.get("sourceAdNumber") or "unknown"),
            publication_date=parse_iso_date(record.get("publicationDate")),
            metadata={"canonicalAdNumber": record.get("canonicalAdNumber")},
        )
        if search_document is not None:
            stats["source_documents"] += 1

        identity = parse_ad_identity(record.get("sourceAdNumber"))
        directive = (
            db.scalar(
                select(AirworthinessDirective).where(
                    AirworthinessDirective.ad_number == identity.canonical_number
                )
            )
            if identity
            else None
        )
        if directive is None:
            ensure_publication_issue(
                db,
                snapshot=snapshot,
                directive=None,
                issue_type="publication_proof_missing_directive",
                payload={"record": record},
            )
            stats["missing_directives"] += 1
            continue

        record_hash = hashlib.sha256(
            json.dumps(record, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        federal_register_documents = {
            str(item.get("documentNumber")): item
            for item in record.get("federalRegisterDocuments") or []
            if item.get("documentNumber")
        }
        for document_number in record.get("federalRegisterExactMatches") or []:
            retained_documents: list[ADSourceDocument] = []
            document_artifacts = federal_register_documents.get(str(document_number)) or {}
            for source_type, artifact_key in (
                ("document_payload", "payloadArtifact"),
                ("document_pdf", "pdfArtifact"),
            ):
                retained = retain_manifest_artifact(
                    db,
                    artifact=document_artifacts.get(artifact_key),
                    artifact_root=retained_root,
                    settings=settings,
                    snapshot=snapshot,
                    source_system="federal_register",
                    source_type=source_type,
                    source_identifier=str(document_number),
                    parent_source_identifier=str(record.get("sourceAdNumber") or ""),
                    publication_date=parse_iso_date(record.get("publicationDate")),
                    metadata={"canonicalAdNumber": record.get("canonicalAdNumber")},
                )
                if retained is not None:
                    retained_documents.append(retained)
                    stats["source_documents"] += 1
            primary_document = next(
                (
                    document
                    for document in retained_documents
                    if document.media_type == "application/pdf"
                ),
                retained_documents[0] if retained_documents else search_document,
            )
            publication = upsert_publication(
                db,
                directive=directive,
                snapshot=snapshot,
                source_system="federal_register",
                source_type="api_exact_match",
                source_identifier=str(document_number),
                publication_date=parse_iso_date(record.get("publicationDate")),
                status="resolved",
                content_hash=record_hash,
                metadata=record,
                source_document=primary_document,
            )
            if publication.source_document_id:
                stats["publications_linked_to_documents"] += 1
            stats["federal_register_publications"] += 1

        package_id = record.get("govinfoPackageId")
        package = packages.get(package_id) if package_id else None
        if package and package.get("status") == "resolved":
            retained_documents = []
            for source_type, artifact_key in (
                ("package_summary", "summaryArtifact"),
                ("issue_pdf", "pdfArtifact"),
            ):
                retained = retain_manifest_artifact(
                    db,
                    artifact=package.get(artifact_key),
                    artifact_root=retained_root,
                    settings=settings,
                    snapshot=snapshot,
                    source_system="govinfo",
                    source_type=source_type,
                    source_identifier=str(package_id),
                    publication_date=parse_iso_date(
                        package.get("dateIssued") or record.get("publicationDate")
                    ),
                    metadata={"adNumbers": package.get("adNumbers") or []},
                )
                if retained is not None:
                    retained_documents.append(retained)
                    stats["source_documents"] += 1
            primary_document = next(
                (
                    document
                    for document in retained_documents
                    if document.media_type == "application/pdf"
                ),
                retained_documents[0] if retained_documents else None,
            )
            publication = upsert_publication(
                db,
                directive=directive,
                snapshot=snapshot,
                source_system="govinfo",
                source_type="federal_register_issue",
                source_identifier=str(package_id),
                publication_date=parse_iso_date(
                    package.get("dateIssued") or record.get("publicationDate")
                ),
                status="resolved",
                content_hash=package.get("sha256"),
                metadata=package,
                pdf_url=package.get("pdfUrl"),
                source_document=primary_document,
            )
            if publication.source_document_id:
                stats["publications_linked_to_documents"] += 1
            stats["govinfo_publications"] += 1

        if record.get("publicationStatus") == "needs_adjudication":
            ensure_publication_issue(
                db,
                snapshot=snapshot,
                directive=directive,
                issue_type="historical_publication_needs_adjudication",
                payload={
                    "sourceAdNumber": record.get("sourceAdNumber"),
                    "reason": record.get("publicationGapReason"),
                },
            )
            stats["needs_adjudication"] += 1
    db.flush()
    return stats


def publication_artifact_inventory(manifest: dict[str, Any]) -> dict[str, int]:
    records = manifest.get("records") or []
    packages = (manifest.get("govinfoPackages") or {}).values()
    return {
        "records": len(records),
        "govinfoPackages": len(manifest.get("govinfoPackages") or {}),
        "federalRegisterSearchPayloads": sum(
            bool(record.get("federalRegisterSearchArtifact")) for record in records
        ),
        "federalRegisterDocumentPayloads": sum(
            bool(document.get("payloadArtifact"))
            for record in records
            for document in record.get("federalRegisterDocuments") or []
        ),
        "federalRegisterDocumentPdfs": sum(
            bool(document.get("pdfArtifact"))
            for record in records
            for document in record.get("federalRegisterDocuments") or []
        ),
        "govinfoPackageSummaries": sum(
            bool(package.get("summaryArtifact")) for package in packages
        ),
        "govinfoIssuePdfs": sum(
            bool(package.get("pdfArtifact"))
            for package in (manifest.get("govinfoPackages") or {}).values()
        ),
    }


def validate_publication_manifest(manifest: dict[str, Any]) -> None:
    verification = manifest.get("verification") or {}
    if verification and int(verification.get("passed") or 0) != int(
        verification.get("total") or 0
    ):
        raise ValueError("Publication proof verification is incomplete")
    checks = manifest.get("checks") or {}
    artifact_complete_required = (
        manifest.get("proofVersion") == ARTIFACT_COMPLETE_PROOF_VERSION
        or "every_federal_register_match_retains_payload_and_pdf" in checks
        or "every_resolved_govinfo_package_retains_payload_and_pdf" in checks
    )
    if not artifact_complete_required:
        return

    records = manifest.get("records") or []
    if any(not record.get("federalRegisterSearchArtifact") for record in records):
        raise ValueError("Artifact-complete proof is missing a Federal Register search payload")
    for record in records:
        expected = {
            str(value) for value in record.get("federalRegisterExactMatches") or []
        }
        documents = {
            str(document.get("documentNumber")): document
            for document in record.get("federalRegisterDocuments") or []
        }
        if expected != set(documents):
            raise ValueError("Artifact-complete proof has incomplete Federal Register documents")
        if any(
            not document.get("payloadArtifact") or not document.get("pdfArtifact")
            for document in documents.values()
        ):
            raise ValueError("Artifact-complete proof has incomplete Federal Register artifacts")
    if any(
        package.get("status") == "resolved"
        and (not package.get("summaryArtifact") or not package.get("pdfArtifact"))
        for package in (manifest.get("govinfoPackages") or {}).values()
    ):
        raise ValueError("Artifact-complete proof has incomplete GovInfo artifacts")


def upsert_publication(
    db: Session,
    *,
    directive: AirworthinessDirective,
    snapshot: ADSourceSnapshot,
    source_system: str,
    source_type: str,
    source_identifier: str,
    publication_date: date | None,
    status: str,
    content_hash: str | None,
    metadata: dict[str, Any],
    pdf_url: str | None = None,
    source_document: ADSourceDocument | None = None,
) -> ADPublication:
    publication = db.scalar(
        select(ADPublication).where(
            ADPublication.directive_id == directive.id,
            ADPublication.source_system == source_system,
            ADPublication.source_type == source_type,
            ADPublication.source_identifier == source_identifier,
        )
    )
    if publication is None:
        publication = ADPublication(
            directive_id=directive.id,
            source_system=source_system,
            source_type=source_type,
            source_identifier=source_identifier,
        )
        db.add(publication)
    publication.source_snapshot_id = snapshot.id
    publication.publication_date = publication_date
    publication.status = status
    publication.content_hash = content_hash
    publication.metadata_json = metadata
    publication.pdf_url = pdf_url
    if source_document is not None:
        publication.source_document_id = source_document.id
    db.flush()
    return publication


def retain_manifest_artifact(
    db: Session,
    *,
    artifact: dict[str, Any] | None,
    artifact_root: Path | None,
    settings: Settings,
    snapshot: ADSourceSnapshot,
    source_system: str,
    source_type: str,
    source_identifier: str,
    publication_date: date | None,
    metadata: dict[str, Any],
    parent_source_identifier: str | None = None,
) -> ADSourceDocument | None:
    if not artifact:
        return None
    if artifact_root is None:
        raise ValueError("artifact_root is required when publication artifacts are present")
    relative_path = Path(str(artifact.get("path") or ""))
    if not relative_path.parts or relative_path.is_absolute():
        raise ValueError("Publication artifact path must be relative")
    path = (artifact_root / relative_path).resolve()
    if artifact_root != path and artifact_root not in path.parents:
        raise ValueError("Publication artifact path escapes artifact_root")
    data = path.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    expected_hash = str(artifact.get("sha256") or "")
    if actual_hash != expected_hash:
        raise ValueError(f"Publication artifact hash mismatch for {relative_path}")
    expected_bytes = artifact.get("bytes")
    if expected_bytes is not None and len(data) != int(expected_bytes):
        raise ValueError(f"Publication artifact size mismatch for {relative_path}")
    media_type = str(artifact.get("mediaType") or "application/octet-stream")
    if media_type == "application/pdf" and not data.startswith(b"%PDF-"):
        raise ValueError(f"Publication artifact is not a PDF: {relative_path}")
    document, _ = retain_source_document(
        db,
        data=data,
        source_system=source_system,
        source_type=source_type,
        source_identifier=source_identifier,
        parent_source_identifier=parent_source_identifier,
        source_url=artifact.get("sourceUrl"),
        filename=str(artifact.get("filename") or relative_path.name),
        media_type=media_type,
        settings=settings,
        source_snapshot=snapshot,
        publication_date=publication_date,
        metadata={**metadata, "manifestArtifact": artifact},
    )
    if document.source_snapshot_id is None:
        document.source_snapshot_id = snapshot.id
    return document


def ensure_publication_issue(
    db: Session,
    *,
    snapshot: ADSourceSnapshot,
    directive: AirworthinessDirective | None,
    issue_type: str,
    payload: dict[str, Any],
) -> ADReconciliationIssue:
    issue = db.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.source_snapshot_id == snapshot.id,
            ADReconciliationIssue.directive_id
            == (directive.id if directive else None),
            ADReconciliationIssue.issue_type == issue_type,
            ADReconciliationIssue.status == "open",
        )
    )
    if issue is None:
        issue = ADReconciliationIssue(
            source_snapshot_id=snapshot.id,
            directive_id=directive.id if directive else None,
            issue_type=issue_type,
            severity="medium",
            payload=payload,
        )
        db.add(issue)
    else:
        issue.payload = payload
    db.flush()
    return issue


def parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None
