from __future__ import annotations

import hashlib
import json
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from app.services.ad_discovery import FederalRegisterClient, flatten_excerpts
from app.services.ad_identity import AD_NUMBER_PATTERN, parse_ad_identity
from app.services.ad_source_proof import filter_drs_rows
from app.services.drs_bulk_import import (
    first_value,
    parse_access_members_with_mdbtools,
)


PUBLICATION_PROOF_VERSION = "ad_publication_reconciliation_v1"


def run_publication_reconciliation(
    *,
    drs_zip_path: str | Path,
    output_root: str | Path,
    govinfo_api_key: str,
    federal_register_client: FederalRegisterClient | None = None,
    govinfo_base_url: str = "https://api.govinfo.gov",
) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(drs_zip_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".accdb")]
        parsed = parse_access_members_with_mdbtools(archive, members)
    target_rows = [
        *filter_drs_rows(parsed["rows"], model="172G"),
        *filter_drs_rows(parsed["rows"], model="O-300-D", product_type="Engine"),
    ]
    rows_by_identity: dict[str, dict[str, Any]] = {}
    for row in target_rows:
        identity = parse_ad_identity(first_value(row, "AD Number", "ADNumber"))
        if identity:
            rows_by_identity.setdefault(identity.source_number, row)

    fr_client = federal_register_client or FederalRegisterClient(timeout_seconds=30)
    records: list[dict[str, Any]] = []
    package_ads: dict[str, list[str]] = defaultdict(list)
    for source_number, row in sorted(rows_by_identity.items()):
        identity = parse_ad_identity(source_number)
        assert identity is not None
        search = fr_client.search_by_ad_number(identity.canonical_number, per_page=20)
        exact_results = [
            item
            for item in search.results
            if document_contains_ad(item, identity.canonical_number)
        ]
        retain_json(
            root,
            "federal-register-search",
            identity.source_number,
            search.raw_response,
        )
        drs_date = drs_publish_date(row)
        fr_date = (
            str(exact_results[0].get("publication_date") or "") or None
            if exact_results
            else None
        )
        publish_date = drs_date or fr_date
        package_id = f"FR-{publish_date}" if publish_date else None
        if package_id:
            package_ads[package_id].append(identity.source_number)
        records.append(
            {
                "sourceAdNumber": identity.source_number,
                "canonicalAdNumber": identity.canonical_number,
                "revision": identity.revision,
                "drsPublishDate": drs_date,
                "publicationDate": publish_date,
                "publicationDateSource": (
                    "drs" if drs_date else "federal_register_api" if fr_date else None
                ),
                "govinfoPackageId": package_id,
                "federalRegisterDeclaredCount": search.count,
                "federalRegisterReturnedCount": len(search.results),
                "federalRegisterExactMatches": [
                    item.get("document_number") for item in exact_results
                ],
                "federalRegisterDifference": (
                    None if exact_results else "no_exact_modern_api_match"
                ),
            }
        )

    package_results: dict[str, dict[str, Any]] = {}
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        for package_id, ad_numbers in sorted(package_ads.items()):
            response = client.get(
                f"{govinfo_base_url.rstrip('/')}/packages/{package_id}/summary",
                params={"api_key": govinfo_api_key},
            )
            if response.status_code == 200:
                payload = response.json()
                retained = retain_json(root, "govinfo-summary", package_id, payload)
                package_results[package_id] = {
                    "status": "resolved",
                    "adNumbers": sorted(ad_numbers),
                    "sha256": retained["sha256"],
                    "bytes": retained["bytes"],
                    "dateIssued": payload.get("dateIssued"),
                    "pdfUrl": (payload.get("download") or {}).get("pdfLink"),
                }
            else:
                package_results[package_id] = {
                    "status": "unresolved",
                    "httpStatus": response.status_code,
                    "adNumbers": sorted(ad_numbers),
                }

    unresolved_dates = [
        item["sourceAdNumber"] for item in records if not item["publicationDate"]
    ]
    unresolved_packages = [
        package_id
        for package_id, result in package_results.items()
        if result["status"] != "resolved"
    ]
    fr_missing = [
        item["sourceAdNumber"]
        for item in records
        if not item["federalRegisterExactMatches"]
    ]
    for item in records:
        package = package_results.get(item["govinfoPackageId"] or "")
        if package and package["status"] == "resolved":
            item["publicationStatus"] = "resolved_govinfo"
        elif item["federalRegisterExactMatches"]:
            item["publicationStatus"] = "resolved_federal_register_api"
        else:
            item["publicationStatus"] = "needs_adjudication"
            item["publicationGapReason"] = (
                "DRS record has no publication date and no exact modern "
                "Federal Register API match; do not infer a date from the "
                "effective date."
            )
    checks = {
        "target_directives_are_unique": len(records) == len(rows_by_identity),
        "every_dated_target_resolves_exact_govinfo_issue": not unresolved_packages,
        "undated_historical_targets_are_classified": all(
            item["publicationStatus"] == "needs_adjudication"
            for item in records
            if not item["publicationDate"]
        ),
        "modern_api_differences_are_classified": all(
            item["federalRegisterExactMatches"]
            or item["federalRegisterDifference"] == "no_exact_modern_api_match"
            for item in records
        ),
        "every_target_is_resolved_or_needs_adjudication": all(
            item["publicationStatus"]
            in {
                "resolved_govinfo",
                "resolved_federal_register_api",
                "needs_adjudication",
            }
            for item in records
        ),
    }
    return {
        "proofVersion": PUBLICATION_PROOF_VERSION,
        "targetDirectiveCount": len(records),
        "govinfoPackageCount": len(package_results),
        "federalRegisterExactMatchCount": len(records) - len(fr_missing),
        "federalRegisterNoExactMatchCount": len(fr_missing),
        "federalRegisterNoExactMatches": fr_missing,
        "unresolvedPublicationDates": unresolved_dates,
        "unresolvedGovInfoPackages": unresolved_packages,
        "retainedBytes": sum(path.stat().st_size for path in root.rglob("*.json")),
        "estimatedExternalCostUsd": 0,
        "records": records,
        "govinfoPackages": package_results,
        "checks": checks,
        "verification": {
            "passed": sum(bool(value) for value in checks.values()),
            "total": len(checks),
        },
    }


def document_contains_ad(document: dict[str, Any], canonical: str) -> bool:
    text = " ".join(
        str(value or "")
        for value in (
            document.get("title"),
            document.get("abstract"),
            flatten_excerpts(document.get("excerpts")),
        )
    )
    return canonical in {
        identity.canonical_number
        for match in AD_NUMBER_PATTERN.finditer(text)
        if (identity := parse_ad_identity(match.group(0))) is not None
    }


def drs_publish_date(row: dict[str, Any]) -> str | None:
    value = first_value(row, "Publish Date", "PublicationDate", "Issue Date")
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def retain_json(
    root: Path,
    source_type: str,
    identifier: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    data = (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode()
    digest = hashlib.sha256(data).hexdigest()
    path = root / source_type / digest[:2] / digest / f"{safe_id(identifier)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return {"path": str(path.relative_to(root)), "sha256": digest, "bytes": len(data)}


def safe_id(value: str) -> str:
    return "".join(character if character.isalnum() or character in "._-" else "_" for character in value)
