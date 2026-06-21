#!/usr/bin/env python3
"""Validate FAA DRS bulk ZIP AD coverage against Federal Register AD rules.

This is intentionally one-shot validation code, not production ingestion code.
It writes intermediate data under ./data and emits findings.md.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

import httpx
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FR_RESPONSES_DIR = DATA_DIR / "fr_responses"
FINDINGS_PATH = BASE_DIR / "findings.md"
DRS_PAGE_URL = "https://drs.faa.gov/browse/ADFREAD/doctypeDetails"
FR_API_URL = "https://www.federalregister.gov/api/v1/documents.json"
FR_DOC_URL = "https://www.federalregister.gov/api/v1/documents/{document_number}.json"
USER_AGENT = "paprnav-drs-zip-validation/0.1 (contact: admin@paprnav.local)"
AD_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{2})\b")
DRS_ZIP_RE = re.compile(r"ADFinalRulesEmergencyADs_\d{8}\.zip", re.I)


@dataclass(frozen=True)
class FRDocument:
    document_number: str
    title: str
    publication_date: str
    source_url: str | None
    ad_numbers: tuple[str, ...]


@dataclass
class ZipInventory:
    total_file_count: int
    type_counts: dict[str, int]
    manifest_files: list[str]
    first_10: list[str]
    last_10: list[str]
    filename_sample: list[str]


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def normalize_ad_number(raw: str) -> str:
    year, week, number = raw.strip().split("-")
    if len(year) == 2:
        year_int = int(year)
        year = f"20{year}" if year_int <= 39 else f"19{year}"
    return f"{year}-{week}-{number}"


def ad_year(ad_number: str) -> int:
    return int(ad_number.split("-", 1)[0])


def extract_ad_numbers(text: str | None) -> set[str]:
    if not text:
        return set()
    return {normalize_ad_number(match.group(1)) for match in AD_RE.finditer(text)}


def extract_fr_rule_ad_numbers(text: str | None) -> set[str]:
    if not text:
        return set()

    targeted: set[str] = set()
    depdoc_blocks = re.findall(r"<DEPDOC\b[^>]*>(.*?)</DEPDOC>", text, flags=re.I | re.S)
    for block in depdoc_blocks:
        targeted |= {
            normalize_ad_number(match.group(1))
            for match in re.finditer(r"\bAD\s+(\d{4}-\d{2}-\d{2})\b", block, flags=re.I)
        }
    if targeted:
        return targeted

    amendment_numbers: set[str] = set()
    amendment_blocks = re.findall(
        r"(<AMDPAR\b[^>]*>.*?(?:airworthiness directive|AD).*?</AMDPAR>.{0,1500})",
        text,
        flags=re.I | re.S,
    )
    for block in amendment_blocks:
        heading_match = re.search(r"<E\b[^>]*>\s*(\d{4}-\d{2}-\d{2})\b", block, flags=re.I)
        if heading_match:
            amendment_numbers.add(normalize_ad_number(heading_match.group(1)))
        else:
            amendment_numbers |= extract_ad_numbers(block)
    if amendment_numbers:
        return amendment_numbers

    return extract_ad_numbers(text)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FR_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)


def discover_bulk_zip_url() -> str:
    log("Discovering DRS bulk ZIP URL with Playwright")
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - environment failure path
        raise RuntimeError(
            "Playwright is not installed. Run `pip install -r requirements.txt` and `playwright install chromium`."
        ) from exc

    captured_urls: list[str] = []
    html_path = DATA_DIR / "drs_doctypeDetails.html"
    controls_path = DATA_DIR / "drs_download_controls.json"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.new_page()

        def maybe_capture(url: str) -> None:
            lower = url.lower()
            if ".zip" in lower or "adfinalrulesemergencyads" in lower:
                captured_urls.append(url)

        page.on("request", lambda request: maybe_capture(request.url))
        page.on("response", lambda response: maybe_capture(response.url))

        try:
            page.goto(DRS_PAGE_URL, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=45000)
            except PlaywrightTimeoutError:
                log("DRS page did not reach networkidle; continuing with DOM inspection")

            html_path.write_text(page.content(), encoding="utf-8")

            download_controls = page.eval_on_selector_all(
                "a, button, [role=button], p-button, .p-button, span",
                """els => els
                    .map((el, index) => ({
                        index,
                        tag: el.tagName,
                        text: (el.innerText || el.textContent || '').trim(),
                        href: el.href || el.getAttribute('href') || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        classes: el.getAttribute('class') || ''
                    }))
                    .filter(item => /zip|download|bulk|ADFinalRulesEmergencyADs/i.test(
                        [item.text, item.href, item.ariaLabel, item.classes].join(' ')
                    ))
                    .slice(0, 100)""",
            )
            controls_path.write_text(json.dumps(download_controls, indent=2), encoding="utf-8")

            hrefs = page.eval_on_selector_all(
                "a[href]",
                """els => els.map(a => ({href: a.href, text: (a.innerText || a.textContent || '').trim()}))""",
            )
            for item in hrefs:
                href = str(item.get("href") or "")
                if ".zip" in href.lower() or "adfinalrulesemergencyads" in href.lower():
                    maybe_capture(href)

            if not captured_urls:
                click_targets = [
                    page.get_by_role("button", name=DRS_ZIP_RE),
                    page.locator("button").filter(has_text=DRS_ZIP_RE),
                    page.locator("a").filter(has_text=DRS_ZIP_RE),
                    page.get_by_text(DRS_ZIP_RE),
                ]
                for target in click_targets:
                    try:
                        if target.count() < 1:
                            continue
                        with page.expect_download(timeout=15000) as download_info:
                            target.first.click(timeout=5000)
                        download = download_info.value
                        download_name = download.suggested_filename or "drs_bulk.zip"
                        downloaded_zip_path = DATA_DIR / "drs_bulk.zip"
                        download.save_as(downloaded_zip_path)
                        maybe_capture(download.url)
                        if not captured_urls or not captured_urls[-1].lower().startswith(("http://", "https://")):
                            captured_urls.append(f"playwright-download:{download_name}")
                        if captured_urls:
                            break
                    except Exception:
                        continue

            if not captured_urls:
                raise RuntimeError(
                    "Could not find DRS bulk ZIP link. "
                    f"Saved rendered HTML to {html_path} and download controls to {controls_path} for inspection."
                )
        finally:
            context.close()
            browser.close()

    discovered = captured_urls[0]
    (DATA_DIR / "bulk_zip_url.txt").write_text(discovered + "\n", encoding="utf-8")
    log(f"BULK_ZIP_URL_DISCOVERED: {discovered}")
    return discovered


def http_get_with_backoff(client: httpx.Client, url: str, **kwargs: Any) -> httpx.Response:
    delay = 1.0
    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = client.get(url, **kwargs)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                log(f"HTTP {response.status_code} for {url}; backing off {delay:.1f}s")
                time.sleep(delay)
                delay *= 2
                continue
            response.raise_for_status()
            return response
        except Exception as exc:
            last_exc = exc
            if attempt < 3:
                log(f"Request failed for {url}: {exc}; backing off {delay:.1f}s")
                time.sleep(delay)
                delay *= 2
                continue
            break
    raise RuntimeError(f"Failed to fetch {url}: {last_exc}") from last_exc


def download_zip(url: str, force: bool) -> Path:
    zip_path = DATA_DIR / "drs_bulk.zip"
    if url.startswith("playwright-download:"):
        if zip_path.exists():
            log(f"Using ZIP saved by Playwright download: {zip_path}")
            return zip_path
        raise RuntimeError(
            "DRS ZIP was downloaded through Playwright, but the saved file is unavailable. "
            "Let discovery download it again."
        )

    if zip_path.exists() and not force:
        log(f"Using cached ZIP: {zip_path}")
        return zip_path

    log(f"Downloading DRS bulk ZIP: {url}")
    with httpx.stream(
        "GET",
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=120.0,
        follow_redirects=True,
    ) as response:
        response.raise_for_status()
        with zip_path.open("wb") as out:
            for chunk in response.iter_bytes():
                out.write(chunk)
    log(f"Saved ZIP to {zip_path} ({zip_path.stat().st_size:,} bytes)")
    return zip_path


def inspect_zip(zip_path: Path) -> tuple[ZipInventory, list[zipfile.ZipInfo]]:
    log("Inspecting ZIP inventory")
    with zipfile.ZipFile(zip_path) as zf:
        infos = [info for info in zf.infolist() if not info.is_dir()]
    names = sorted(info.filename for info in infos)
    type_counts = Counter(Path(name).suffix.lower() or "<none>" for name in names)
    manifest_exts = {".csv", ".json", ".txt", ".xlsx", ".xls", ".xml"}
    manifest_files = [
        name
        for name in names
        if Path(name).suffix.lower() in manifest_exts
        or any(token in Path(name).name.lower() for token in ["manifest", "index", "contents"])
    ]
    inventory = ZipInventory(
        total_file_count=len(names),
        type_counts=dict(sorted(type_counts.items())),
        manifest_files=manifest_files,
        first_10=names[:10],
        last_10=names[-10:],
        filename_sample=names[:5] + names[-5:],
    )
    return inventory, infos


def extract_from_manifest(zip_path: Path, inventory: ZipInventory) -> set[str]:
    ad_numbers: set[str] = set()
    with zipfile.ZipFile(zip_path) as zf:
        for name in inventory.manifest_files:
            suffix = Path(name).suffix.lower()
            if suffix == ".json":
                payload = json.loads(zf.read(name).decode("utf-8", errors="replace"))
                ad_numbers |= extract_ad_numbers(json.dumps(payload))
            elif suffix == ".csv":
                text = zf.read(name).decode("utf-8-sig", errors="replace")
                for row in csv.reader(io.StringIO(text)):
                    ad_numbers |= extract_ad_numbers(" ".join(row))
            elif suffix in {".txt", ".xml"}:
                text = zf.read(name).decode("utf-8", errors="replace")
                ad_numbers |= extract_ad_numbers(text)
            elif suffix in {".xlsx", ".xls"}:
                log(f"Manifest candidate {name} is spreadsheet; skipping direct parse in one-shot script")
    return ad_numbers


def extract_from_pdf_first_pages(zip_path: Path, infos: list[zipfile.ZipInfo]) -> set[str]:
    log("Falling back to PDF first-page AD-number extraction")
    ad_numbers: set[str] = set()
    pdf_infos = [info for info in infos if info.filename.lower().endswith(".pdf")]
    with zipfile.ZipFile(zip_path) as zf:
        for index, info in enumerate(pdf_infos, start=1):
            if index % 50 == 0:
                log(f"Parsed first page of {index}/{len(pdf_infos)} PDFs")
            try:
                with zf.open(info) as pdf_file:
                    pdf_bytes = io.BytesIO(pdf_file.read())
                reader = PdfReader(pdf_bytes)
                if not reader.pages:
                    continue
                first_page_text = reader.pages[0].extract_text() or ""
                near_header = "\n".join(first_page_text.splitlines()[:40])
                matches = extract_ad_numbers(near_header) or extract_ad_numbers(first_page_text)
                ad_numbers |= matches
            except Exception as exc:
                log(f"Could not parse PDF first page for {info.filename}: {exc}")
    return ad_numbers


def extract_from_access_database(zip_path: Path, infos: list[zipfile.ZipInfo]) -> set[str]:
    """Extract AD-like identifiers from DRS's Access bulk database.

    The public DRS ZIP currently contains a single .accdb file. Full Access row
    parsing requires platform tooling that is not consistently available on
    developer machines, but the AD Number values are stored as UTF-16 text in
    the table data pages. For this one-shot coverage validation, extracting the
    normalized identifier set is sufficient.
    """
    accdb_infos = [info for info in infos if info.filename.lower().endswith((".accdb", ".mdb"))]
    if not accdb_infos:
        return set()

    log(f"Extracting AD numbers from Access database file(s): {len(accdb_infos)}")
    ad_numbers: set[str] = set()
    current_year = datetime.now(timezone.utc).year
    with zipfile.ZipFile(zip_path) as zf:
        for info in accdb_infos:
            raw = zf.read(info)
            text = raw.decode("utf-16le", errors="ignore")
            for ad_number in extract_ad_numbers(text):
                year = ad_year(ad_number)
                if 1940 <= year <= current_year + 1:
                    ad_numbers.add(ad_number)
    return ad_numbers


def extract_zip_ad_numbers(zip_path: Path, inventory: ZipInventory, infos: list[zipfile.ZipInfo]) -> tuple[set[str], str]:
    filename_numbers = set()
    for info in infos:
        filename_numbers |= extract_ad_numbers(Path(info.filename).name)
    log(f"AD numbers found in filenames: {len(filename_numbers)}")

    manifest_numbers = extract_from_manifest(zip_path, inventory) if inventory.manifest_files else set()
    if manifest_numbers:
        log(f"AD numbers found in manifest/index files: {len(manifest_numbers)}")
        return manifest_numbers, "manifest"

    if len(filename_numbers) >= 100:
        return filename_numbers, "filename"

    access_numbers = extract_from_access_database(zip_path, infos)
    if len(access_numbers) >= 100:
        log(f"AD numbers found in Access database text: {len(access_numbers)}")
        return access_numbers, "accdb_utf16_text"

    pdf_numbers = extract_from_pdf_first_pages(zip_path, infos)
    if len(pdf_numbers) < 100:
        raise RuntimeError(
            f"ZIP AD extraction produced only {len(pdf_numbers)} AD numbers; likely parse failure, not real coverage."
        )
    return pdf_numbers, "pdf_first_page"


def fetch_fr_documents(start_date: str, end_date: str, use_cache: bool) -> list[dict[str, Any]]:
    cached_path = FR_RESPONSES_DIR / f"fr_documents_{start_date}_{end_date}.json"
    if cached_path.exists() and use_cache:
        log(f"Using cached Federal Register API responses: {cached_path}")
        return json.loads(cached_path.read_text(encoding="utf-8"))

    log(f"Fetching Federal Register FAA Rule documents from {start_date} through {end_date}")
    params: list[tuple[str, str | int]] = [
        ("conditions[agencies][]", "federal-aviation-administration"),
        ("conditions[type][]", "RULE"),
        ("conditions[publication_date][gte]", start_date),
        ("conditions[publication_date][lte]", end_date),
        ("fields[]", "title"),
        ("fields[]", "document_number"),
        ("fields[]", "publication_date"),
        ("fields[]", "html_url"),
        ("per_page", 100),
    ]
    documents: list[dict[str, Any]] = []
    page = 1
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0, follow_redirects=True) as client:
        next_url: str | None = FR_API_URL
        next_params: Any = params
        while next_url:
            response = http_get_with_backoff(client, next_url, params=next_params)
            payload = response.json()
            (FR_RESPONSES_DIR / f"page_{page}.json").write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            results = payload.get("results") or []
            documents.extend(results)
            log(f"Fetched FR page {page}: {len(results)} results")
            next_url = payload.get("next_page_url")
            next_params = None
            page += 1
    cached_path.write_text(json.dumps(documents, indent=2, sort_keys=True), encoding="utf-8")
    return documents


def fetch_fr_detail_text(client: httpx.Client, document_number: str) -> str:
    detail_path = FR_RESPONSES_DIR / f"detail_{document_number}.json"
    if detail_path.exists():
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
    else:
        time.sleep(1.0)
        response = http_get_with_backoff(client, FR_DOC_URL.format(document_number=document_number))
        detail = response.json()
        detail_path.write_text(json.dumps(detail, indent=2, sort_keys=True), encoding="utf-8")

    pieces = [
        detail.get("title"),
        detail.get("abstract"),
        detail.get("action"),
        detail.get("dates"),
        detail.get("body_html"),
        detail.get("raw_text"),
    ]
    xml_url = detail.get("full_text_xml_url")
    if xml_url:
        xml_path = FR_RESPONSES_DIR / f"detail_{document_number}.xml"
        if xml_path.exists():
            pieces.append(xml_path.read_text(encoding="utf-8", errors="replace"))
        else:
            time.sleep(1.0)
            try:
                xml_response = http_get_with_backoff(client, xml_url)
                xml_text = xml_response.text
                xml_path.write_text(xml_text, encoding="utf-8")
                pieces.append(xml_text)
            except Exception as exc:
                log(f"Could not fetch FR XML for {document_number}: {exc}")
    return "\n".join(str(piece) for piece in pieces if piece)


def build_fr_set(documents: list[dict[str, Any]]) -> tuple[set[str], list[FRDocument]]:
    ad_docs = [
        doc
        for doc in documents
        if str(doc.get("title") or "").strip().lower().startswith("airworthiness directives;")
    ]
    if not ad_docs:
        sample_titles = [str(doc.get("title") or "") for doc in documents[:20]]
        raise RuntimeError(
            "Federal Register API returned zero AD documents after title filter. "
            f"Sample titles: {sample_titles}"
        )
    log(f"FR AD-title documents in window: {len(ad_docs)}")

    mapped: list[FRDocument] = []
    fr_set: set[str] = set()
    no_title_numbers: list[dict[str, Any]] = []

    for doc in ad_docs:
        title = str(doc.get("title") or "")
        numbers = extract_ad_numbers(title)
        if numbers:
            fr_set |= numbers
            mapped.append(
                FRDocument(
                    document_number=str(doc.get("document_number")),
                    title=title,
                    publication_date=str(doc.get("publication_date") or ""),
                    source_url=doc.get("html_url"),
                    ad_numbers=tuple(sorted(numbers)),
                )
            )
        else:
            no_title_numbers.append(doc)

    if no_title_numbers:
        log(
            f"{len(no_title_numbers)} FR AD documents lacked AD numbers in title; fetching detail/XML at <=1/sec"
        )
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0, follow_redirects=True) as client:
            for index, doc in enumerate(no_title_numbers, start=1):
                document_number = str(doc.get("document_number"))
                if index % 25 == 0:
                    log(f"Fetched FR details for {index}/{len(no_title_numbers)} title-missing AD docs")
                text = fetch_fr_detail_text(client, document_number)
                numbers = extract_fr_rule_ad_numbers(text)
                fr_set |= numbers
                mapped.append(
                    FRDocument(
                        document_number=document_number,
                        title=str(doc.get("title") or ""),
                        publication_date=str(doc.get("publication_date") or ""),
                        source_url=doc.get("html_url"),
                        ad_numbers=tuple(sorted(numbers)),
                    )
                )

    if not fr_set:
        raise RuntimeError("No AD numbers could be extracted from FR AD documents; refusing comparison.")
    return fr_set, mapped


def gap_hypothesis(doc: FRDocument | None) -> str:
    if not doc:
        return "No Federal Register metadata found for this AD number."
    title = doc.title.lower()
    if "correction" in title:
        return "FR-only correction or correction text may not appear as separate AD in DRS ZIP."
    if "emergency" in title:
        return "Emergency AD handling may differ between DRS ZIP and FR publication set."
    if not doc.ad_numbers:
        return "AD number required detail/XML extraction; ZIP parser may have missed equivalent document."
    return "Potential DRS ZIP coverage gap or extraction mismatch."


def verdict_for_coverage(coverage: float) -> tuple[str, str]:
    if coverage >= 0.98:
        return "PASS", "Proceed with bulk-ZIP-primary architecture."
    if coverage >= 0.85:
        return "CONDITIONAL", "Document gaps; consider Federal Register fallback for missing subset."
    return "FAIL", "Bulk ZIP is not authoritative; revert to FR-API-primary architecture with DRS supplemental."


def write_json_set(path: Path, values: Iterable[str]) -> None:
    path.write_text(json.dumps(sorted(values), indent=2), encoding="utf-8")


def write_findings(
    *,
    bulk_zip_url: str,
    inventory: ZipInventory,
    extraction_method: str,
    start_date: str,
    end_date: str,
    fr_set: set[str],
    zip_set: set[str],
    zip_set_window: set[str],
    intersection: set[str],
    source_intersection: set[str],
    only_in_fr: set[str],
    only_in_fr_source: set[str],
    only_in_zip: set[str],
    coverage: float,
    source_coverage: float,
    verdict: str,
    action: str,
    fr_docs_by_ad: dict[str, list[FRDocument]],
) -> None:
    lines: list[str] = []
    lines.append("# DRS Bulk ZIP Validation Findings")
    lines.append("")
    lines.append(f"Date run: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Discovered bulk ZIP URL: `{bulk_zip_url}`")
    lines.append("")
    lines.append("## ZIP Contents Inventory")
    lines.append("")
    lines.append(f"- Total file count: {inventory.total_file_count}")
    lines.append(f"- File type distribution: `{json.dumps(inventory.type_counts, sort_keys=True)}`")
    lines.append(f"- Manifest/index files: {', '.join(inventory.manifest_files) if inventory.manifest_files else 'none found'}")
    lines.append("- First 10 filenames:")
    lines.extend(f"  - `{name}`" for name in inventory.first_10)
    lines.append("- Last 10 filenames:")
    lines.extend(f"  - `{name}`" for name in inventory.last_10)
    lines.append("")
    lines.append("## AD Extraction")
    lines.append("")
    lines.append(f"- Filename/content convention used: `{extraction_method}`")
    lines.append("- If method is `pdf_first_page`, filenames did not provide enough AD numbers and no parseable manifest was found.")
    lines.append("")
    lines.append("## Comparison")
    lines.append("")
    lines.append(f"- Window: {start_date} to {end_date}")
    lines.append(f"- FR set size: {len(fr_set)}")
    lines.append(f"- Full ZIP AD set size: {len(zip_set)}")
    lines.append(f"- Full ZIP intersection size: {len(source_intersection)}")
    lines.append(f"- Full ZIP source coverage: {source_coverage:.2%}")
    lines.append(f"- ZIP set size using AD-year window surrogate: {len(zip_set_window)}")
    lines.append(f"- AD-year surrogate intersection size: {len(intersection)}")
    lines.append(f"- AD-year surrogate coverage: {coverage:.2%}")
    lines.append(f"- Verdict: **{verdict}**")
    lines.append(f"- Recommended action: {action}")
    lines.append("- Note: The current one-shot script extracts AD identifiers from the DRS Access database but does not parse row-level publication dates; the AD-year window is a conservative surrogate, not a source-coverage failure.")
    lines.append("")
    lines.append("## Detailed Gap Report: ADs In FR But Not Full ZIP")
    lines.append("")
    for ad_number in sorted(only_in_fr_source)[:20]:
        doc = (fr_docs_by_ad.get(ad_number) or [None])[0]
        lines.append(f"### {ad_number}")
        if doc:
            lines.append(f"- FR title: {doc.title}")
            lines.append(f"- Publication date: {doc.publication_date}")
            lines.append(f"- Document number: {doc.document_number}")
        lines.append(f"- Hypothesized reason: {gap_hypothesis(doc)}")
        lines.append("")
    if not only_in_fr_source:
        lines.append("No FR-only gaps found.")
        lines.append("")
    lines.append("## AD-Year Window Artifacts")
    lines.append("")
    lines.append("These FR ADs are present in the full ZIP but fall outside the AD-year surrogate window.")
    for ad_number in sorted(only_in_fr)[:20]:
        doc = (fr_docs_by_ad.get(ad_number) or [None])[0]
        if doc:
            lines.append(f"- {ad_number}: published {doc.publication_date}, document {doc.document_number}")
        else:
            lines.append(f"- {ad_number}")
    if not only_in_fr:
        lines.append("No AD-year surrogate gaps found.")
    lines.append("")
    lines.append("## Sample ADs In ZIP But Not FR")
    lines.append("")
    for ad_number in sorted(only_in_zip)[:20]:
        lines.append(f"- {ad_number}")
    if not only_in_zip:
        lines.append("No ZIP-only sample entries.")
    lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("")
    lines.append(f"- Follow the verdict action: {action}")
    lines.append("- For production date-window comparisons, parse DRS Access rows instead of using AD-year filtering.")
    lines.append("- Review `data/fr_set.json`, `data/zip_set.json`, and cached FR responses for audit.")
    lines.append("- If gaps look like extraction errors, inspect the corresponding PDFs or FR XML before changing architecture.")
    lines.append("- If gaps are real, update the ingestion spec before implementing production collection.")
    FINDINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", default="2024-01-01")
    parser.add_argument("--end-date", default="2024-12-31")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--bulk-zip-url", help="Use a known DRS ZIP URL instead of Playwright discovery")
    args = parser.parse_args()

    ensure_dirs()
    bulk_zip_url = args.bulk_zip_url or discover_bulk_zip_url()
    zip_path = download_zip(bulk_zip_url, force=args.force_download)
    inventory, infos = inspect_zip(zip_path)
    zip_set, extraction_method = extract_zip_ad_numbers(zip_path, inventory, infos)
    start_year = int(args.start_date[:4])
    end_year = int(args.end_date[:4])
    zip_set_window = {ad for ad in zip_set if start_year <= ad_year(ad) <= end_year}
    write_json_set(DATA_DIR / "zip_set.json", zip_set)
    write_json_set(DATA_DIR / "zip_set_window.json", zip_set_window)

    fr_documents = fetch_fr_documents(args.start_date, args.end_date, use_cache=not args.no_cache)
    fr_set, fr_docs = build_fr_set(fr_documents)
    write_json_set(DATA_DIR / "fr_set.json", fr_set)

    fr_docs_by_ad: dict[str, list[FRDocument]] = defaultdict(list)
    for doc in fr_docs:
        for ad_number in doc.ad_numbers:
            fr_docs_by_ad[ad_number].append(doc)

    intersection = fr_set & zip_set_window
    source_intersection = fr_set & zip_set
    only_in_fr = fr_set - zip_set_window
    only_in_fr_source = fr_set - zip_set
    only_in_zip = zip_set_window - fr_set
    coverage = len(intersection) / len(fr_set) if fr_set else 0.0
    source_coverage = len(source_intersection) / len(fr_set) if fr_set else 0.0
    verdict, action = verdict_for_coverage(source_coverage)

    write_findings(
        bulk_zip_url=bulk_zip_url,
        inventory=inventory,
        extraction_method=extraction_method,
        start_date=args.start_date,
        end_date=args.end_date,
        fr_set=fr_set,
        zip_set=zip_set,
        zip_set_window=zip_set_window,
        intersection=intersection,
        source_intersection=source_intersection,
        only_in_fr=only_in_fr,
        only_in_fr_source=only_in_fr_source,
        only_in_zip=only_in_zip,
        coverage=coverage,
        source_coverage=source_coverage,
        verdict=verdict,
        action=action,
        fr_docs_by_ad=fr_docs_by_ad,
    )

    log(f"FR set size: {len(fr_set)}")
    log(f"Full ZIP set size: {len(zip_set)}")
    log(f"Full ZIP source coverage: {source_coverage:.2%}")
    log(f"ZIP set size in window: {len(zip_set_window)}")
    log(f"Intersection: {len(intersection)}")
    log(f"Coverage: {coverage:.2%}")
    log(f"VERDICT: {verdict} - {action}")
    log(f"Wrote {FINDINGS_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure = (
            "# DRS Bulk ZIP Validation Findings\n\n"
            f"Date run: {datetime.now(timezone.utc).isoformat()}\n\n"
            "## Failure\n\n"
            f"The validation could not be completed: `{exc}`\n\n"
            "No silent fallback was used. Inspect saved intermediate files under `data/`.\n"
        )
        ensure_dirs()
        FINDINGS_PATH.write_text(failure, encoding="utf-8")
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"Wrote failure report to {FINDINGS_PATH}", file=sys.stderr)
        raise
