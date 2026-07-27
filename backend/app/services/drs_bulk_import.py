from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from csv import DictReader
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import ADPublication, ADReconciliationIssue, ADSourceSnapshot, AirworthinessDirective
from app.services.ad_applicability import ensure_issue, get_or_create_target, upsert_target_applicability
from app.services.ad_costs import record_ad_cost_entry
from app.services.ad_coverage import refresh_coverage_sets_for_snapshot
from app.services.ad_identity import AD_NUMBER_PATTERN, normalize_ad_number

PARSER_NAME = "drs_bulk_importer"
PARSER_VERSION = "0.2.0"
MDB_TABLES = "mdb-tables"
MDB_EXPORT = "mdb-export"


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
        storage_bytes=None,
    )
    return import_drs_rows_into_snapshot(db, rows, snapshot)


def import_drs_rows_into_snapshot(db: Session, rows: list[dict[str, Any]], snapshot: ADSourceSnapshot) -> dict[str, int]:
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
    refresh_coverage_sets_for_snapshot(db, snapshot)
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
            metadata={"accessParsing": "pending"},
            status="in_progress",
            storage_bytes=len(content),
        )
        if not accdb_members:
            snapshot.status = "failed"
            snapshot.metadata_json = {"accessParsing": "failed", "error": "zip_missing_access_database"}
            ensure_snapshot_issue(
                db,
                snapshot=snapshot,
                issue_type="drs_zip_missing_access_database",
                severity="high",
                payload={"filename": path.name, "members": members},
            )
            stats["issues"] += 1
            return stats

        table_parse = parse_access_members_with_mdbtools(archive, accdb_members)
        snapshot.table_inventory = {
            "zipMembers": members,
            "accessDatabases": accdb_members,
            "accessTables": table_parse["tables"],
        }
        if table_parse["rows"]:
            snapshot.source_type = "bulk_access"
            snapshot.status = "complete"
            snapshot.row_count = len(table_parse["rows"])
            snapshot.metadata_json = {
                "accessParsing": "mdbtools",
                "parserCommands": [MDB_TABLES, MDB_EXPORT],
                "parseErrors": table_parse["errors"],
            }
            parsed_stats = import_drs_rows_into_snapshot(db, table_parse["rows"], snapshot)
            for key, value in parsed_stats.items():
                stats[key] += value
            if table_parse["errors"]:
                ensure_snapshot_issue(
                    db,
                    snapshot=snapshot,
                    issue_type="drs_access_table_parse_partial",
                    severity="medium",
                    payload={"filename": path.name, "errors": table_parse["errors"][:10]},
                )
                stats["issues"] += 1
            return stats

        fallback_reason = table_parse["fallback_reason"]
        snapshot.status = "partial"
        snapshot.metadata_json = {
            "accessParsing": fallback_reason,
            "parserCommands": [MDB_TABLES, MDB_EXPORT],
            "parseErrors": table_parse["errors"],
            "fallback": "binary_ad_number_scan",
        }
        ensure_snapshot_issue(
            db,
            snapshot=snapshot,
            issue_type="drs_access_table_parse_unavailable",
            severity="high",
            payload={
                "filename": path.name,
                "reason": fallback_reason,
                "errors": table_parse["errors"][:10],
            },
        )
        stats["issues"] += 1
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
        snapshot.row_count = stats["rows_seen"]
        if stats["rows_seen"] == 0:
            snapshot.status = "failed"
            ensure_snapshot_issue(
                db,
                snapshot=snapshot,
                issue_type="drs_zip_no_parseable_ad_numbers",
                severity="high",
                payload={"filename": path.name, "accessDatabases": accdb_members},
            )
            stats["issues"] += 1
    db.flush()
    return stats


def parse_access_members_with_mdbtools(archive: zipfile.ZipFile, accdb_members: list[str]) -> dict[str, Any]:
    if not shutil.which(MDB_TABLES) or not shutil.which(MDB_EXPORT):
        return {"rows": [], "tables": {}, "errors": [], "fallback_reason": "mdbtools_unavailable"}

    rows: list[dict[str, Any]] = []
    tables: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="paprnav-drs-") as tmpdir:
        tmp_path = Path(tmpdir)
        for member in accdb_members:
            accdb_path = tmp_path / Path(member).name
            accdb_path.write_bytes(archive.read(member))
            table_names = list_access_tables(accdb_path, member, errors)
            tables[member] = {"names": table_names, "rowCounts": {}, "columns": {}}
            for table_name in table_names:
                exported_rows = export_access_table(accdb_path, member, table_name, errors)
                tables[member]["rowCounts"][table_name] = len(exported_rows)
                tables[member]["columns"][table_name] = sorted(exported_rows[0].keys()) if exported_rows else []
                for row in exported_rows:
                    if normalize_ad_number(first_value(row, "adNumber", "ADNumber", "ad_number", "AD No.", "AD")):
                        normalized = dict(row)
                        normalized.setdefault("sourceAccessDatabase", member)
                        normalized.setdefault("sourceAccessTable", table_name)
                        rows.append(normalized)
    reason = "no_parseable_access_rows" if not rows else "not_needed"
    return {"rows": rows, "tables": tables, "errors": errors, "fallback_reason": reason}


def list_access_tables(accdb_path: Path, member: str, errors: list[dict[str, str]]) -> list[str]:
    try:
        result = subprocess.run(
            [MDB_TABLES, "-1", str(accdb_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        errors.append({"accessDatabase": member, "stage": "tables", "error": str(exc)})
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def export_access_table(accdb_path: Path, member: str, table_name: str, errors: list[dict[str, str]]) -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            [MDB_EXPORT, str(accdb_path), "--", table_name],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        errors.append({"accessDatabase": member, "table": table_name, "stage": "export", "error": str(exc)})
        return []
    return [dict(row) for row in DictReader(result.stdout.splitlines())]


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
    status: str = "complete",
    storage_bytes: int | None = None,
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
            status=status,
            parser_name=PARSER_NAME,
            parser_version=PARSER_VERSION,
            row_count=row_count,
            table_inventory=table_inventory,
            metadata_json=metadata,
            storage_bytes=storage_bytes,
        )
        db.add(snapshot)
    else:
        snapshot.row_count = row_count
        snapshot.table_inventory = table_inventory
        snapshot.metadata_json = metadata
        snapshot.status = status
        snapshot.parser_name = PARSER_NAME
        snapshot.parser_version = PARSER_VERSION
        if storage_bytes is not None:
            snapshot.storage_bytes = storage_bytes
    db.flush()
    record_ad_cost_entry(
        db,
        idempotency_key=f"drs-source-storage:{snapshot.content_hash}",
        scope_type="shared_source",
        cost_category="source_storage",
        usage_quantity=snapshot.storage_bytes or 0,
        usage_unit="physical_byte",
        source_snapshot_id=snapshot.id,
        actual_cost_usd=0,
        allocated_cost_usd=0,
        attribution_status="platform_shared_unallocated",
        metadata={
            "sourceSystem": "drs",
            "billingActive": False,
            "costCalibrationStatus": "uncalibrated",
        },
    )
    return snapshot


def ensure_snapshot_issue(
    db: Session,
    *,
    snapshot: ADSourceSnapshot,
    issue_type: str,
    severity: str,
    payload: dict[str, Any],
) -> ADReconciliationIssue:
    issue = db.scalar(
        select(ADReconciliationIssue).where(
            ADReconciliationIssue.source_snapshot_id == snapshot.id,
            ADReconciliationIssue.issue_type == issue_type,
            ADReconciliationIssue.status == "open",
        )
    )
    if issue is None:
        issue = ADReconciliationIssue(
            source_snapshot_id=snapshot.id,
            issue_type=issue_type,
            severity=severity,
            payload=payload,
        )
        db.add(issue)
    else:
        issue.severity = severity
        issue.payload = payload
    db.flush()
    return issue


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
    for encoding in ("utf-8", "utf-16le", "utf-16", "latin-1"):
        try:
            return data.decode(encoding, errors="ignore")
        except UnicodeError:
            continue
    return ""
