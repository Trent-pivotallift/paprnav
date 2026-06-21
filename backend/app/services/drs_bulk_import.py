from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADPublication, ADSourceSnapshot, AirworthinessDirective
from app.services.ad_applicability import ensure_issue, get_or_create_target, upsert_target_applicability
from app.services.ad_identity import AD_NUMBER_PATTERN, normalize_ad_number

PARSER_NAME = "drs_bulk_importer"
PARSER_VERSION = "0.1.0"


def import_drs_bulk_rows(
    db: Session,
    rows: list[dict[str, Any]],
    *,
    source_url: str | None = None,
    filename: str | None = None,
    content_hash: str | None = None,
    captured_at: datetime | None = None,
) -> dict[str, int]:
    snapshot = upsert_snapshot(
        db,
        source_type="bulk_rows",
        source_url=source_url,
        filename=filename,
        content_hash=content_hash or hash_rows(rows),
        captured_at=captured_at,
        row_count=len(rows),
        table_inventory={"rows": len(rows)},
        metadata={"fixtureFirst": True},
    )
    stats = {"rows_seen": 0, "directives_upserted": 0, "publications_upserted": 0, "applicabilities_upserted": 0, "issues": 0}
    for row in rows:
        stats["rows_seen"] += 1
        ad_number = normalize_ad_number(first_value(row, "adNumber", "ADNumber", "ad_number", "AD No.", "AD"))
        if ad_number is None:
            ensure_issue(db, directive=None, issue_type="drs_row_missing_ad_number", severity="high", payload={"row": row})
            stats["issues"] += 1
            continue

        directive = upsert_directive(db, row, ad_number, snapshot.content_hash)
        stats["directives_upserted"] += 1
        publication = upsert_publication(db, directive, snapshot, row, ad_number)
        stats["publications_upserted"] += 1

        targets = target_rows_from_row(row)
        if not targets:
            ensure_issue(
                db,
                directive=directive,
                issue_type="drs_row_missing_applicability",
                severity="medium",
                payload={"adNumber": ad_number, "row": row},
            )
            stats["issues"] += 1
            continue

        for target_row in targets:
            target = get_or_create_target(db, **target_row)
            upsert_target_applicability(
                db,
                directive=directive,
                target=target,
                source_publication=publication,
                basis="drs_bulk_row",
                compliance_actions=list_values(row, "complianceActions", "Compliance", "Action", "Subject"),
                compliance_intervals=list_values(row, "complianceIntervals", "Interval"),
                citations=[{"source": "drs_bulk_row", "identifier": publication.source_identifier}],
                confidence=0.84,
                status=publication.status or "current",
            )
            stats["applicabilities_upserted"] += 1
    db.flush()
    return stats


def import_drs_bulk_zip(db: Session, zip_path: str | Path, *, source_url: str | None = None) -> dict[str, int]:
    path = Path(zip_path)
    content = path.read_bytes()
    content_hash = hashlib.sha256(content).hexdigest()
    stats = {"rows_seen": 0, "directives_upserted": 0, "publications_upserted": 0, "applicabilities_upserted": 0, "issues": 0}
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        accdb_members = [name for name in members if name.lower().endswith(".accdb")]
        snapshot = upsert_snapshot(
            db,
            source_type="bulk_zip",
            source_url=source_url,
            filename=path.name,
            content_hash=content_hash,
            captured_at=datetime.now(timezone.utc),
            row_count=None,
            table_inventory={"zipMembers": members, "accessDatabases": accdb_members},
            metadata={"accessParsing": "not_available_without_external_driver"},
        )
        if not accdb_members:
            ensure_issue(db, directive=None, issue_type="drs_zip_missing_access_database", severity="high", payload={"filename": path.name, "members": members})
            stats["issues"] += 1
            return stats
        for member in accdb_members:
            data = archive.read(member)
            text = decode_possible_utf16(data)
            numbers = sorted({normalize_ad_number(match.group(1)) for match in AD_NUMBER_PATTERN.finditer(text)})
            for ad_number in [number for number in numbers if number]:
                row = {"adNumber": ad_number, "Subject": f"DRS bulk ZIP record {ad_number}", "Status": "unknown", "Identifier": f"{member}:{ad_number}"}
                directive = upsert_directive(db, row, ad_number, snapshot.content_hash)
                publication = upsert_publication(db, directive, snapshot, row, ad_number)
                ensure_issue(
                    db,
                    directive=directive,
                    issue_type="drs_zip_applicability_unparsed",
                    severity="medium",
                    payload={"adNumber": ad_number, "accessDatabase": member},
                )
                stats["rows_seen"] += 1
                stats["directives_upserted"] += 1
                stats["publications_upserted"] += 1
                stats["issues"] += 1
    db.flush()
    return stats


def upsert_snapshot(
    db: Session,
    *,
    source_type: str,
    source_url: str | None,
    filename: str | None,
    content_hash: str,
    captured_at: datetime | None,
    row_count: int | None,
    table_inventory: dict[str, Any],
    metadata: dict[str, Any],
) -> ADSourceSnapshot:
    snapshot = db.scalar(select(ADSourceSnapshot).where(ADSourceSnapshot.content_hash == content_hash, ADSourceSnapshot.source_system == "drs"))
    if snapshot is None:
        snapshot = ADSourceSnapshot(
            source_system="drs",
            source_type=source_type,
            source_url=source_url,
            filename=filename,
            content_hash=content_hash,
            captured_at=captured_at or datetime.now(timezone.utc),
            status="complete",
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            row_count=row_count,
            table_inventory=table_inventory,
            metadata_json=metadata,
        )
        db.add(snapshot)
    else:
        snapshot.row_count = row_count
        snapshot.table_inventory = table_inventory
        snapshot.metadata_json = metadata
    db.flush()
    return snapshot


def upsert_directive(db: Session, row: dict[str, Any], ad_number: str, source_hash: str) -> AirworthinessDirective:
    directive = db.scalar(select(AirworthinessDirective).where(AirworthinessDirective.ad_number == ad_number))
    title = first_value(row, "title", "Title", "subject", "Subject", "ADSubject") or f"Airworthiness Directive {ad_number}"
    status = normalize_status(first_value(row, "status", "Status", "ADStatus"))
    if directive is None:
        directive = AirworthinessDirective(
            discovery_record_id=None,
            ad_number=ad_number,
            title=title,
            status=status,
            source_content_hash=source_hash,
            extraction_status="not_started",
            review_status="not_started",
        )
        db.add(directive)
    else:
        directive.title = title or directive.title
        directive.status = status or directive.status
        directive.source_content_hash = source_hash
    db.flush()
    return directive


def upsert_publication(db: Session, directive: AirworthinessDirective, snapshot: ADSourceSnapshot, row: dict[str, Any], ad_number: str) -> ADPublication:
    identifier = first_value(row, "identifier", "Identifier", "Guid", "GUID", "documentId", "DocumentId") or ad_number
    publication = db.scalar(
        select(ADPublication).where(
            ADPublication.directive_id == directive.id,
            ADPublication.source_system == "drs",
            ADPublication.source_type == "bulk_access_row",
            ADPublication.source_identifier == str(identifier),
        )
    )
    if publication is None:
        publication = ADPublication(
            directive_id=directive.id,
            source_system="drs",
            source_type="bulk_access_row",
            source_identifier=str(identifier),
        )
        db.add(publication)
    publication.source_snapshot_id = snapshot.id
    publication.title = directive.title
    publication.publication_date = parse_date(first_value(row, "publicationDate", "PublicationDate", "PostedDate", "IssueDate"))
    publication.effective_date = parse_date(first_value(row, "effectiveDate", "EffectiveDate"))
    publication.html_url = first_value(row, "htmlUrl", "HtmlUrl", "DocumentUrl", "URL")
    publication.pdf_url = first_value(row, "pdfUrl", "PdfUrl")
    publication.status = normalize_status(first_value(row, "status", "Status", "ADStatus"))
    publication.content_hash = snapshot.content_hash
    publication.metadata_json = row
    db.flush()
    return publication


def target_rows_from_row(row: dict[str, Any]) -> list[dict[str, str | None]]:
    product_type = first_value(row, "productType", "ProductType", "Product Type", "Category") or "Aircraft"
    product_subtype = first_value(row, "productSubtype", "ProductSubtype", "Product Subtype", "Subcategory")
    makes = split_values(first_value(row, "make", "Make", "Manufacturer", "Mfr"))
    models = split_values(first_value(row, "model", "Model", "Models"))
    if not makes and not models:
        return []
    if not makes:
        makes = [None]
    if not models:
        models = [None]
    return [
        {"product_type": product_type, "product_subtype": product_subtype, "make": make, "model": model}
        for make in makes
        for model in models
    ]


def first_value(row: dict[str, Any], *keys: str) -> str | None:
    lowered = {key.lower(): value for key, value in row.items()}
    for key in keys:
        value = row.get(key, lowered.get(key.lower()))
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def split_values(value: str | None) -> list[str | None]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"\s*(?:\||;|,)\s*", value) if part.strip()]


def list_values(row: dict[str, Any], *keys: str) -> list[Any]:
    value = first_value(row, *keys)
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return parsed
    return [value]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def normalize_status(value: str | None) -> str:
    if not value:
        return "current"
    cleaned = value.strip().lower().replace(" ", "_")
    if cleaned in {"active", "current", "final", "published"}:
        return "current"
    if "supersed" in cleaned:
        return "superseded"
    if "cancel" in cleaned or "rescinded" in cleaned:
        return "rescinded"
    return cleaned[:64]


def hash_rows(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def decode_possible_utf16(data: bytes) -> str:
    for encoding in ("utf-16le", "utf-16", "utf-8", "latin-1"):
        try:
            return data.decode(encoding, errors="ignore")
        except UnicodeError:
            continue
    return ""
