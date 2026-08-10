from __future__ import annotations

import hashlib
import json
import time
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


PUBLICATION_PROOF_VERSION = "ad_publication_reconciliation_v2"
PDF_MAGIC = b"%PDF-"


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
        search_artifact = retain_json(
            root,
            "federal-register-search",
            identity.source_number,
            search.raw_response,
            source_url=f"{fr_client.base_url}/api/v1/documents.json",
        )
        federal_register_documents: list[dict[str, Any]] = []
        with httpx.Client(timeout=45, follow_redirects=True) as artifact_client:
            for item in exact_results:
                document_number = str(item.get("document_number") or "").strip()
                if not document_number:
                    raise ValueError("Exact Federal Register result is missing document_number")
                payload_artifact = retain_json(
                    root,
                    "federal-register-document",
                    document_number,
                    item,
                    source_url=item.get("json_url") or item.get("html_url"),
                )
                pdf_url = str(item.get("pdf_url") or "").strip()
                if not pdf_url:
                    raise ValueError(
                        f"Federal Register document {document_number} is missing pdf_url"
                    )
                pdf_artifact = fetch_and_retain_pdf(
                    artifact_client,
                    root=root,
                    source_type="federal-register-document-pdf",
                    identifier=document_number,
                    url=pdf_url,
                )
                federal_register_documents.append(
                    {
                        "documentNumber": document_number,
                        "payloadArtifact": payload_artifact,
                        "pdfArtifact": pdf_artifact,
                    }
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
                "federalRegisterSearchArtifact": search_artifact,
                "federalRegisterDocuments": federal_register_documents,
                "federalRegisterDifference": (
                    None if exact_results else "no_exact_modern_api_match"
                ),
            }
        )

    package_results: dict[str, dict[str, Any]] = {}
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        for package_id, ad_numbers in sorted(package_ads.items()):
            response = request_with_retries(
                client,
                f"{govinfo_base_url.rstrip('/')}/packages/{package_id}/summary",
                params={"api_key": govinfo_api_key},
                identifier=package_id,
            )
            if response.status_code == 200:
                payload = response.json()
                retained = retain_json(
                    root,
                    "govinfo-summary",
                    package_id,
                    payload,
                    source_url=sanitized_source_url(response.request.url),
                )
                pdf_url = (payload.get("download") or {}).get("pdfLink")
                if not pdf_url:
                    raise ValueError(f"GovInfo package {package_id} is missing pdfLink")
                pdf_artifact = fetch_and_retain_pdf(
                    client,
                    root=root,
                    source_type="govinfo-issue-pdf",
                    identifier=package_id,
                    url=str(pdf_url),
                    params={"api_key": govinfo_api_key},
                )
                package_results[package_id] = {
                    "status": "resolved",
                    "adNumbers": sorted(ad_numbers),
                    "sha256": retained["sha256"],
                    "bytes": retained["bytes"],
                    "dateIssued": payload.get("dateIssued"),
                    "pdfUrl": pdf_url,
                    "summaryArtifact": retained,
                    "pdfArtifact": pdf_artifact,
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
        "every_federal_register_match_retains_payload_and_pdf": all(
            len(item.get("federalRegisterDocuments") or [])
            == len(item.get("federalRegisterExactMatches") or [])
            and all(
                document.get("payloadArtifact") and document.get("pdfArtifact")
                for document in item.get("federalRegisterDocuments") or []
            )
            for item in records
        ),
        "every_resolved_govinfo_package_retains_payload_and_pdf": all(
            package.get("status") != "resolved"
            or (package.get("summaryArtifact") and package.get("pdfArtifact"))
            for package in package_results.values()
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
        "retainedBytes": sum(
            path.stat().st_size for path in root.rglob("*") if path.is_file()
        ),
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
    *,
    source_url: str | None = None,
) -> dict[str, Any]:
    data = (json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n").encode()
    return retain_bytes(
        root,
        source_type,
        identifier,
        data,
        filename=f"{safe_id(identifier)}.json",
        media_type="application/json",
        source_url=source_url,
    )


def fetch_and_retain_pdf(
    client: httpx.Client,
    *,
    root: Path,
    source_type: str,
    identifier: str,
    url: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    filename = f"{safe_id(identifier)}.pdf"
    existing = find_retained_artifact(
        root,
        source_type=source_type,
        filename=filename,
        media_type="application/pdf",
        source_url=url,
    )
    if existing is not None:
        return existing
    response = request_with_retries(
        client,
        url,
        params=params,
        identifier=identifier,
    )
    if response.is_error:
        raise RuntimeError(
            f"Remote PDF request failed for {identifier} at "
            f"{sanitized_source_url(url)} with HTTP {response.status_code}"
        )
    data = response.content
    if not data.startswith(PDF_MAGIC):
        raise ValueError(f"Remote PDF for {identifier} does not have a PDF signature")
    return retain_bytes(
        root,
        source_type,
        identifier,
        data,
        filename=filename,
        media_type="application/pdf",
        source_url=sanitized_source_url(response.url),
    )


def request_with_retries(
    client: httpx.Client,
    url: str,
    *,
    params: dict[str, str] | None,
    identifier: str,
    max_attempts: int = 6,
) -> httpx.Response:
    for attempt in range(max_attempts):
        try:
            response = client.get(url, params=params)
        except httpx.HTTPError:
            if attempt == max_attempts - 1:
                raise RuntimeError(
                    f"Remote request failed for {identifier} at "
                    f"{sanitized_source_url(url)}"
                ) from None
            time.sleep(2**attempt)
            continue
        if response.status_code not in {429, 500, 502, 503, 504}:
            return response
        if attempt == max_attempts - 1:
            raise RuntimeError(
                f"Remote request failed for {identifier} at "
                f"{sanitized_source_url(url)} with HTTP {response.status_code}"
            )
        time.sleep(2**attempt)
    raise RuntimeError(f"Remote request attempts exhausted for {identifier}")


def find_retained_artifact(
    root: Path,
    *,
    source_type: str,
    filename: str,
    media_type: str,
    source_url: str,
) -> dict[str, Any] | None:
    candidates = list((root / source_type).glob(f"*/*/{filename}"))
    if len(candidates) != 1:
        return None
    path = candidates[0]
    data = path.read_bytes()
    if media_type == "application/pdf" and not data.startswith(PDF_MAGIC):
        return None
    digest = hashlib.sha256(data).hexdigest()
    if path.parent.name != digest:
        return None
    return {
        "path": str(path.relative_to(root)),
        "sha256": digest,
        "bytes": len(data),
        "mediaType": media_type,
        "sourceUrl": sanitized_source_url(source_url),
        "filename": filename,
    }


def retain_bytes(
    root: Path,
    source_type: str,
    identifier: str,
    data: bytes,
    *,
    filename: str,
    media_type: str,
    source_url: str | None,
) -> dict[str, Any]:
    digest = hashlib.sha256(data).hexdigest()
    path = root / source_type / digest[:2] / digest / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return {
        "path": str(path.relative_to(root)),
        "sha256": digest,
        "bytes": len(data),
        "mediaType": media_type,
        "sourceUrl": source_url,
        "filename": filename,
    }


def sanitized_source_url(value: str | httpx.URL) -> str:
    url = httpx.URL(value)
    for parameter in ("api_key", "key"):
        url = url.copy_remove_param(parameter)
    return str(url)


def safe_id(value: str) -> str:
    return "".join(character if character.isalnum() or character in "._-" else "_" for character in value)
