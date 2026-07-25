from __future__ import annotations

import re
from typing import Any

from app.services.ad_identity import normalize_ad_number


SCHEMA_VERSION = "maintenance_entry_v1"
EXPLICIT_AD_PATTERN = re.compile(
    r"\bAD\s*((?:\d{4}|\d{2})-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
ACTION_PATTERN = re.compile(
    r"\b(checked|complied|inspected|installed|lubricated|overhauled|"
    r"removed|repaired|replaced|serviced|tested)\b",
    re.IGNORECASE,
)
NEGATED_COMPLIANCE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:not|never)\b[^\n]*\b(?:comply|complied|compliance)"
    r"|(?:cannot|can't)\b[^\n]*\b(?:comply|complied)"
    r"|no\s+compliance"
    r"|compliance\s+(?:was\s+)?not\s+(?:completed|performed)"
    r")\b",
    re.IGNORECASE,
)
NEGATED_INSPECTION_PATTERN = re.compile(
    r"\b(?:"
    r"(?:not|never)\b[^\n]*\b(?:inspect|inspected|inspection)"
    r"|(?:cannot|can't)\b[^\n]*\b(?:inspect|inspected)"
    r"|inspection\s+(?:was\s+)?not\s+(?:completed|performed)"
    r")\b",
    re.IGNORECASE,
)
PART_NUMBER_PATTERN = re.compile(
    r"\b(?:P/N|Part\s+(?:No\.?|Number))\s*[:#]?\s*"
    r"([A-Z0-9][A-Z0-9 .-]{1,}?)"
    r"(?=\s+(?:S/N|Ser\.?\s*No\.?|Serial\s+(?:No\.?|Number))\b|[,;]|$)",
    re.IGNORECASE,
)
SERIAL_NUMBER_PATTERN = re.compile(
    r"\b(?:S/N|Ser\.?\s*No\.?|Serial\s+(?:No\.?|Number))\s*[:#]?\s*"
    r"([A-Z0-9][A-Z0-9.-]{1,})",
    re.IGNORECASE,
)
WORK_ORDER_PATTERN = re.compile(
    r"\bW\.?\s*O\.?\s*(?:Reference|Ref\.?)?\s*#?\s*([A-Z0-9-]+)",
    re.IGNORECASE,
)
REGISTRATION_PATTERN = re.compile(r"\bN#?\s*([0-9]{1,5}[A-Z]{0,2})\b", re.IGNORECASE)


def extract_structured_maintenance_data(lines: list[str]) -> dict[str, Any]:
    clean_lines = [line.strip() for line in lines if line.strip()]
    text = "\n".join(clean_lines)
    segments = split_segments(clean_lines)

    inspection_types: list[str] = []
    lowered = text.lower()
    if "annual inspection" in lowered:
        inspection_types.append("annual")
    if re.search(r"\b100\s*[- ]?\s*hour inspection\b", lowered):
        inspection_types.append("100_hour")
    if "altimeter" in lowered and (
        "91.411" in lowered or "automatic altitude reporting system" in lowered
    ):
        inspection_types.append("altimeter_static_system")
    if "transponder" in lowered and "91.413" in lowered:
        inspection_types.append("transponder")
    if re.search(r"\belt\b", lowered) and re.search(
        r"\b(?:checked|inspected|replaced|tested)\b",
        lowered,
    ):
        inspection_types.append("elt")

    maintenance_actions = []
    for segment in segments:
        actions = [
            match.group(1).lower()
            for match in ACTION_PATTERN.finditer(segment)
        ]
        if actions:
            maintenance_actions.append(
                {
                    "action": actions[0],
                    "text": segment,
                }
            )

    ad_references = []
    for segment in segments:
        ad_matches = list(EXPLICIT_AD_PATTERN.finditer(segment))
        for index, match in enumerate(ad_matches):
            normalized = normalize_ad_number(match.group(0))
            if normalized is None:
                continue
            reference_context = ad_reference_context(
                segment,
                match,
                previous_match=(
                    ad_matches[index - 1]
                    if index > 0
                    else None
                ),
                next_match=(
                    ad_matches[index + 1]
                    if index + 1 < len(ad_matches)
                    else None
                ),
            )
            ad_references.append(
                {
                    "adNumber": normalized,
                    "asPrinted": match.group(1),
                    "dispositionCandidate": ad_disposition(reference_context),
                    "complianceMethodCandidate": compliance_method(reference_context),
                    "recurringCandidate": bool(
                        re.search(
                            r"\b(?:due\s+each|next\s+due|recurring|each\s+\d+)",
                            reference_context,
                            re.IGNORECASE,
                        )
                    ),
                    "dueText": due_text(reference_context),
                    "text": reference_context,
                }
            )

    component_references = []
    for segment in segments:
        part_numbers = PART_NUMBER_PATTERN.findall(segment)
        serial_numbers = SERIAL_NUMBER_PATTERN.findall(segment)
        if part_numbers or serial_numbers:
            component_references.append(
                {
                    "partNumbers": unique_values(part_numbers),
                    "serialNumbers": unique_values(serial_numbers),
                    "text": segment,
                }
            )

    work_order_match = WORK_ORDER_PATTERN.search(text)
    registration_match = REGISTRATION_PATTERN.search(text)
    return_to_service_segment = next(
        (
            segment
            for segment in segments
            if "certif" in segment.lower()
            and (
                "airworthy condition" in segment.lower()
                or "return to service" in segment.lower()
            )
        ),
        None,
    )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "inspectionTypes": unique_values(inspection_types),
        "maintenanceActions": maintenance_actions,
        "adReferences": ad_references,
        "componentReferences": component_references,
        "facilityName": facility_name(clean_lines),
        "workOrderReference": work_order_match.group(1) if work_order_match else None,
        "aircraftRegistration": (
            f"N{registration_match.group(1).upper()}"
            if registration_match
            else None
        ),
        "returnToService": {
            "presentCandidate": return_to_service_segment is not None,
            "text": return_to_service_segment,
        },
    }


def split_segments(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def ad_reference_context(
    segment: str,
    match: re.Match,
    *,
    previous_match: re.Match | None,
    next_match: re.Match | None,
) -> str:
    search_start = previous_match.end() if previous_match is not None else 0
    clause_start = citation_start_boundary(
        segment,
        search_start=search_start,
        citation_start=match.start(),
    )
    clause_end = len(segment)
    if next_match is not None:
        clause_end = citation_end_boundary(
            segment,
            citation_end=match.end(),
            search_end=next_match.start(),
        )
    return segment[clause_start + 1 : clause_end].strip()


def citation_start_boundary(
    segment: str,
    *,
    search_start: int,
    citation_start: int,
) -> int:
    boundaries = citation_boundary_positions(
        segment,
        search_start,
        citation_start,
    )
    return max(boundaries, default=search_start - 1)


def citation_end_boundary(
    segment: str,
    *,
    citation_end: int,
    search_end: int,
) -> int:
    boundaries = citation_boundary_positions(
        segment,
        citation_end,
        search_end,
    )
    return max(boundaries, default=search_end)


def citation_boundary_positions(
    segment: str,
    start: int,
    end: int,
) -> list[int]:
    sentence_boundaries = [
        start + match.start()
        for match in re.finditer(r"\.(?=\s|$)", segment[start:end])
    ]
    punctuation_boundaries = [
        start + match.start()
        for match in re.finditer(r"[,;]", segment[start:end])
    ]
    return sentence_boundaries + punctuation_boundaries


def ad_disposition(text: str) -> str:
    if re.search(r"\b(?:n/?a|not applicable)\b", text, re.IGNORECASE):
        return "not_applicable"
    if NEGATED_COMPLIANCE_PATTERN.search(text):
        return "not_complied"
    if NEGATED_INSPECTION_PATTERN.search(text):
        return "not_inspected"
    positive_context = positive_disposition_context(text)
    if re.search(
        r"(?:\bc\s*/\s*w\b|\bcomplied(?:\s+with)?\b)",
        positive_context,
        re.IGNORECASE,
    ):
        return "complied"
    if re.search(
        r"\b(?:inspect(?:ed|ing)?|inspection\s+completed)\b",
        positive_context,
        re.IGNORECASE,
    ):
        return "inspected"
    return "mentioned"


def positive_disposition_context(text: str) -> str:
    ad_match = EXPLICIT_AD_PATTERN.search(text)
    search_start = ad_match.end() if ad_match is not None else 0
    boundaries = citation_boundary_positions(text, search_start, len(text))
    clause_end = min(boundaries, default=len(text))
    return text[:clause_end]


def compliance_method(text: str) -> str | None:
    match = re.search(
        r"\bby\s+([a-z][a-z0-9 /-]{2,60}?)(?:\s*[-;,.]|\s+due\b|$)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def due_text(text: str) -> str | None:
    match = re.search(
        r"\bdue\s+([^.;]{1,100})",
        text,
        re.IGNORECASE,
    )
    return match.group(0).strip() if match else None


def facility_name(lines: list[str]) -> str | None:
    for line in lines:
        if re.search(
            r"\b(?:aircraft service|avionics|repair station)\b",
            line,
            re.IGNORECASE,
        ):
            return line[:255]
    return None


def unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))
