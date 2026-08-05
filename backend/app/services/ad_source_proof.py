from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from app.services.ad_identity import parse_ad_identity
from app.services.drs_bulk_import import (
    first_value,
    parse_access_members_with_mdbtools,
    split_values,
)


PROOF_VERSION = "ad_source_target_proof_v1"
SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def run_drs_target_proof(
    *,
    drs_zip_path: str | Path,
    airframe_results_path: str | Path,
    engine_results_path: str | Path,
) -> dict[str, Any]:
    drs_path = Path(drs_zip_path)
    airframe_path = Path(airframe_results_path)
    engine_path = Path(engine_results_path)
    with zipfile.ZipFile(drs_path) as archive:
        accdb_members = [
            name for name in archive.namelist() if name.lower().endswith(".accdb")
        ]
        parsed = parse_access_members_with_mdbtools(archive, accdb_members)

    all_rows = parsed["rows"]
    manual_airframe = read_drs_result_xlsx(airframe_path)
    manual_engine = read_drs_result_xlsx(engine_path)
    bulk_172g = filter_drs_rows(all_rows, model="172G")
    bulk_172g_aircraft = filter_drs_rows(
        all_rows,
        model="172G",
        product_type="Aircraft",
    )
    bulk_o300d = filter_drs_rows(
        all_rows,
        model="O-300-D",
        product_type="Engine",
    )

    airframe_comparison = compare_ad_sets(manual_airframe, bulk_172g)
    engine_comparison = compare_ad_sets(manual_engine, bulk_o300d)
    access_exported_count = sum(
        count
        for database in parsed["tables"].values()
        for count in database["rowCounts"].values()
    )
    checks = {
        "access_database_present": len(accdb_members) == 1,
        "access_parser_complete": bool(all_rows) and not parsed["errors"],
        "access_rows_accounted": access_exported_count
        == len(all_rows) + len(parsed["unparsed_rows"]),
        "airframe_manual_inventory_unique": manual_identifiers_are_unique(
            manual_airframe
        ),
        "engine_manual_inventory_unique": manual_identifiers_are_unique(
            manual_engine
        ),
        "airframe_manual_page_is_subset_of_bulk": airframe_comparison[
            "manualIsSubset"
        ],
        "airframe_manual_pagination_gap_classified": (
            not airframe_comparison["matches"]
            and bool(airframe_comparison["bulkOnly"])
        ),
        "engine_manual_page_is_subset_of_bulk": engine_comparison[
            "manualIsSubset"
        ],
        "engine_manual_pagination_gap_classified": (
            not engine_comparison["matches"]
            and bool(engine_comparison["bulkOnly"])
        ),
        "airframe_scope_is_explicit": all(
            normalized_product_type(row) == "aircraft"
            for row in bulk_172g_aircraft
        ),
        "engine_scope_is_explicit": all(
            normalized_product_type(row) == "engine" for row in bulk_o300d
        ),
    }
    manifest = {
        "proofVersion": PROOF_VERSION,
        "artifacts": {
            "drsBulk": artifact_manifest(drs_path),
            "airframeManualResults": artifact_manifest(airframe_path),
            "engineManualResults": artifact_manifest(engine_path),
        },
        "sourceManifest": {
            "accessMembers": accdb_members,
            "accessTables": parsed["tables"],
            "parseErrors": parsed["errors"],
            "bulkRowCount": len(all_rows),
            "unparsedRowCount": len(parsed["unparsed_rows"]),
            "unparsedRows": parsed["unparsed_rows"],
            "exportedRowCount": access_exported_count,
        },
        "targets": {
            "cessna172GModelIndex": {
                "manualRowCount": len(manual_airframe),
                "bulkRowCount": len(bulk_172g),
                "productTypeCounts": dict(
                    sorted(
                        Counter(
                            first_value(row, "Product Type", "ProductType")
                            or "unknown"
                            for row in bulk_172g
                        ).items()
                    )
                ),
                "aircraftOnlyRowCount": len(bulk_172g_aircraft),
                "comparison": airframe_comparison,
                "manualExportComplete": airframe_comparison["matches"],
                "manualExportClassification": (
                    "complete"
                    if airframe_comparison["matches"]
                    else "first_page_only"
                ),
                "coverageClassification": (
                    "needs_adjudication"
                    if not bulk_172g_aircraft
                    else "catalogued"
                ),
                "coverageReason": (
                    "DRS model-index results contain no Aircraft product rows; "
                    "the retained rows remain valid appliance candidates."
                    if not bulk_172g_aircraft
                    else "DRS contains explicit Aircraft product rows for model 172G."
                ),
            },
            "continentalO300D": {
                "manualRowCount": len(manual_engine),
                "bulkRowCount": len(bulk_o300d),
                "productTypeCounts": dict(
                    sorted(
                        Counter(
                            first_value(row, "Product Type", "ProductType")
                            or "unknown"
                            for row in bulk_o300d
                        ).items()
                    )
                ),
                "comparison": engine_comparison,
                "manualExportComplete": engine_comparison["matches"],
                "manualExportClassification": (
                    "complete"
                    if engine_comparison["matches"]
                    else "first_page_only"
                ),
                "coverageClassification": (
                    "catalogued"
                    if engine_comparison["matches"]
                    else "needs_adjudication"
                ),
            },
        },
        "checks": checks,
        "verification": {
            "passed": sum(bool(value) for value in checks.values()),
            "total": len(checks),
        },
    }
    return manifest


def write_proof_manifest(manifest: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(destination)


def read_drs_result_xlsx(path: str | Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = read_shared_strings(archive)
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relationship_targets = {
            rel.attrib["Id"]: rel.attrib["Target"] for rel in rels
        }
        sheet = workbook.find(f"{{{SPREADSHEET_NS}}}sheets/{{{SPREADSHEET_NS}}}sheet")
        if sheet is None:
            return []
        relationship_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        target = relationship_targets[relationship_id].lstrip("/")
        if not target.startswith("xl/"):
            target = f"xl/{target}"
        root = ElementTree.fromstring(archive.read(target))

    matrix: list[list[str]] = []
    for row in root.findall(f".//{{{SPREADSHEET_NS}}}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{{{SPREADSHEET_NS}}}c"):
            reference = cell.attrib.get("r", "A1")
            index = column_index(reference)
            values[index] = xlsx_cell_value(cell, shared_strings)
        if values:
            matrix.append(
                [values.get(index, "") for index in range(max(values) + 1)]
            )
    if not matrix:
        return []
    headers = [value.strip() for value in matrix[0]]
    return [
        {
            header: row[index].strip() if index < len(row) else ""
            for index, header in enumerate(headers)
            if header
        }
        for row in matrix[1:]
        if any(value.strip() for value in row)
    ]


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(text.text or "" for text in item.iter(f"{{{SPREADSHEET_NS}}}t"))
        for item in root.findall(f"{{{SPREADSHEET_NS}}}si")
    ]


def xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find(f"{{{SPREADSHEET_NS}}}v")
    if cell_type == "inlineStr":
        return "".join(
            text.text or "" for text in cell.iter(f"{{{SPREADSHEET_NS}}}t")
        )
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        return shared_strings[int(value.text)]
    return value.text


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    if not letters:
        return 0
    result = 0
    for letter in letters.group(0):
        result = result * 26 + ord(letter) - ord("A") + 1
    return result - 1


def filter_drs_rows(
    rows: list[dict[str, Any]],
    *,
    model: str,
    product_type: str | None = None,
) -> list[dict[str, Any]]:
    expected_model = normalize_token(model)
    expected_type = normalize_token(product_type) if product_type else None
    selected = []
    for row in rows:
        models = split_values(first_value(row, "Model", "Models"))
        if expected_model not in {normalize_token(value) for value in models if value}:
            continue
        if expected_type and normalized_product_type(row) != expected_type:
            continue
        status = normalize_token(first_value(row, "Status") or "current")
        if status not in {"historical", "current"}:
            continue
        selected.append(row)
    return selected


def compare_ad_sets(
    manual_rows: list[dict[str, Any]],
    bulk_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    manual = source_ad_numbers(manual_rows)
    bulk = source_ad_numbers(bulk_rows)
    return {
        "manualIdentifiers": sorted(manual),
        "bulkIdentifiers": sorted(bulk),
        "manualOnly": sorted(manual - bulk),
        "bulkOnly": sorted(bulk - manual),
        "manualIsSubset": manual <= bulk,
        "matches": manual == bulk,
    }


def source_ad_numbers(rows: list[dict[str, Any]]) -> set[str]:
    identities = []
    for row in rows:
        raw = first_value(row, "AD Number", "ADNumber", "adNumber")
        identity = parse_ad_identity(raw)
        if identity:
            identities.append(identity.source_number)
    return set(identities)


def manual_identifiers_are_unique(rows: list[dict[str, Any]]) -> bool:
    identities = []
    for row in rows:
        identity = parse_ad_identity(first_value(row, "AD Number"))
        if identity:
            identities.append(identity.source_number)
    return len(identities) == len(set(identities)) == len(rows)


def normalized_product_type(row: dict[str, Any]) -> str:
    return normalize_token(first_value(row, "Product Type", "ProductType") or "")


def normalize_token(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def artifact_manifest(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }
