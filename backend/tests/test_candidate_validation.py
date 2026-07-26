from datetime import date
from types import SimpleNamespace

from app.services.candidate_validation import validate_entry_candidate


def draft(**overrides):
    values = {
        "date_was_extracted": True,
        "entry_date": date(2012, 12, 17),
        "description": "Annual inspection completed.",
        "performer_name": "A. Mechanic",
        "performer_credential": "A&P 2192007 IA",
        "tach_time": 1276.8,
        "hobbs_time": None,
        "total_time": 5405.5,
        "field_spans": {
            "description": SimpleNamespace(text="Annual inspection completed."),
            "performer_name": SimpleNamespace(text="A. Mechanic A&P 2192007 IA"),
            "performer_credential": SimpleNamespace(text="A. Mechanic A&P 2192007 IA"),
            "tach_time": SimpleNamespace(text="Tach = 1276.8"),
            "total_time": SimpleNamespace(text="Total Time = 5405.5"),
        },
        "lines": [
            "12-17-12 Tach = 1276.8 Total Time = 5405.5",
            "Annual inspection completed. AD 2011-10-09 complied with.",
        ],
        "requires_review": False,
        "page": SimpleNamespace(source_page_number=2),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_provider_neutral_validation_accepts_supported_candidate() -> None:
    result = validate_entry_candidate(draft(), today=date(2026, 7, 26))

    assert result["status"] == "passed"
    assert result["acceptedForAutomaticVerification"] is True
    assert result["explicitAdReferences"] == ["2011-10-09"]
    assert result["adReferencesInferred"] is False


def test_validation_rejects_missing_date_and_numeric_conflict() -> None:
    result = validate_entry_candidate(
        draft(
            date_was_extracted=False,
            entry_date=None,
            tach_time=6000.0,
            total_time=5405.5,
        ),
        today=date(2026, 7, 26),
    )

    codes = {issue["code"] for issue in result["issues"]}
    assert result["status"] == "rejected"
    assert result["acceptedForAutomaticVerification"] is False
    assert "source_supported_date_missing" in codes
    assert "tach_time_exceeds_total_time" in codes


def test_zero_requires_explicit_source_value() -> None:
    result = validate_entry_candidate(
        draft(
            tach_time=0,
            field_spans={
                **draft().field_spans,
                "tach_time": SimpleNamespace(text="Tach unavailable"),
            },
        )
    )

    assert "zero_not_explicit_in_source" in {
        issue["code"] for issue in result["issues"]
    }
