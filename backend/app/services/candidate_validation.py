from __future__ import annotations

from datetime import date
import re
from typing import Any


VALIDATION_PROFILE = "logbook-candidate-validation-v1"
AD_REFERENCE_PATTERN = re.compile(
    r"\bAD(?:s|'s)?\s*[:#]?\s*(\d{2,4})[-/](\d{1,2})[-/](\d{1,2})\b",
    flags=re.IGNORECASE,
)
CREDENTIAL_PATTERN = re.compile(
    r"\b(?:A\s*&\s*P|IA|FAA\s+CRS|CRS|repair\s+station|certificate)\b|"
    r"\b[A-Z0-9]{5,12}\b",
    flags=re.IGNORECASE,
)


def validate_entry_candidate(draft: Any, *, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    issues: list[dict[str, Any]] = []
    field_results: dict[str, dict[str, Any]] = {}

    if not draft.date_was_extracted or draft.entry_date is None:
        add_issue(issues, "entry_date", "source_supported_date_missing", "blocking")
        field_results["entry_date"] = field_result(None, False, "unsupported")
    elif draft.entry_date > today:
        add_issue(issues, "entry_date", "future_date", "blocking")
        field_results["entry_date"] = field_result(draft.entry_date.isoformat(), False, "rejected")
    elif draft.entry_date.year < 1900:
        add_issue(issues, "entry_date", "implausible_historical_date", "blocking")
        field_results["entry_date"] = field_result(draft.entry_date.isoformat(), False, "rejected")
    else:
        field_results["entry_date"] = field_result(draft.entry_date.isoformat(), True, "candidate")

    description_supported = bool(draft.description.strip() and draft.field_spans.get("description"))
    field_results["description"] = field_result(
        draft.description or None,
        description_supported,
        "candidate" if description_supported else "unsupported",
    )
    if not description_supported:
        add_issue(issues, "description", "source_supported_description_missing", "blocking")

    numeric_values = {
        "tach_time": draft.tach_time,
        "hobbs_time": draft.hobbs_time,
        "total_time": draft.total_time,
    }
    for field_name, value in numeric_values.items():
        supported = value is None or field_name in draft.field_spans
        disposition = "null" if value is None else "candidate" if supported else "unsupported"
        field_results[field_name] = field_result(value, supported, disposition)
        if value is not None and value < 0:
            add_issue(issues, field_name, "negative_time_value", "blocking")
        if value == 0 and not explicit_zero_for_field(draft, field_name):
            add_issue(issues, field_name, "zero_not_explicit_in_source", "blocking")

    for meter_field in ("tach_time", "hobbs_time"):
        meter_value = numeric_values[meter_field]
        total_value = numeric_values["total_time"]
        if meter_value is not None and total_value is not None and meter_value > total_value:
            add_issue(
                issues,
                meter_field,
                f"{meter_field}_exceeds_total_time",
                "blocking",
            )

    performer_supported = draft.performer_name is None or "performer_name" in draft.field_spans
    field_results["performer_name"] = field_result(
        draft.performer_name,
        performer_supported,
        "null" if draft.performer_name is None else "candidate" if performer_supported else "unsupported",
    )
    if draft.performer_name and (
        len(draft.performer_name.strip()) < 3
        or not re.search(r"[A-Za-z]", draft.performer_name)
    ):
        add_issue(issues, "performer_name", "performer_name_not_credible", "blocking")

    credential_supported = (
        draft.performer_credential is None
        or "performer_credential" in draft.field_spans
    )
    field_results["performer_credential"] = field_result(
        draft.performer_credential,
        credential_supported,
        "null"
        if draft.performer_credential is None
        else "candidate"
        if credential_supported
        else "unsupported",
    )
    if draft.performer_credential and not CREDENTIAL_PATTERN.search(
        draft.performer_credential
    ):
        add_issue(
            issues,
            "performer_credential",
            "performer_credential_pattern_uncertain",
            "review",
        )

    source_text = "\n".join(draft.lines)
    explicit_ad_references = sorted(
        {
            "-".join(match.groups())
            for match in AD_REFERENCE_PATTERN.finditer(source_text)
        }
    )
    if draft.requires_review:
        add_issue(issues, None, "multiple_entry_segmentation_requires_review", "review")

    blocking = [issue for issue in issues if issue["severity"] == "blocking"]
    return {
        "profile": VALIDATION_PROFILE,
        "status": "rejected" if blocking else "passed_with_review" if issues else "passed",
        "acceptedForAutomaticVerification": not issues,
        "issues": issues,
        "fieldResults": field_results,
        "explicitAdReferences": explicit_ad_references,
        "adReferencesInferred": False,
        "sourcePageNumber": draft.page.source_page_number,
    }


def field_result(value: Any, source_supported: bool, disposition: str) -> dict[str, Any]:
    return {
        "value": value,
        "sourceSupported": source_supported,
        "disposition": disposition,
    }


def add_issue(
    issues: list[dict[str, Any]],
    field_name: str | None,
    code: str,
    severity: str,
) -> None:
    issues.append({"field": field_name, "code": code, "severity": severity})


def explicit_zero_for_field(draft: Any, field_name: str) -> bool:
    span = draft.field_spans.get(field_name)
    if span is None:
        return False
    label = field_name.removesuffix("_time").replace("_", r"\s*")
    return bool(
        re.search(
            rf"\b{label}\b\s*[:=]?\s*0(?:\.0+)?\b",
            span.text,
            flags=re.IGNORECASE,
        )
    )
