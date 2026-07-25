from app.services.maintenance_extraction import extract_structured_maintenance_data


def test_extracts_explicit_ad_reference_without_treating_dates_as_ads() -> None:
    result = extract_structured_maintenance_data(
        [
            "12-17-12 Tach = 1276.8 Total Time = 5405.5 N3671L",
            "Performed an annual inspection using FAR 43 Appendix D checklist.",
            "ELT battery replaced dated Dec. 2014.",
        ]
    )

    assert result["inspectionTypes"] == ["annual", "elt"]
    assert result["aircraftRegistration"] == "N3671L"
    assert result["adReferences"] == []


def test_extracts_ad_claim_as_reviewable_candidate() -> None:
    result = extract_structured_maintenance_data(
        [
            "C/W AD 2014-10-09 by replacement of the ELT battery.",
            "Next due each 12 calendar months.",
        ]
    )

    assert result["adReferences"] == [
        {
            "adNumber": "2014-10-09",
            "asPrinted": "2014-10-09",
            "dispositionCandidate": "complied",
            "complianceMethodCandidate": "replacement of the ELT battery",
            "recurringCandidate": False,
            "dueText": None,
            "text": "C/W AD 2014-10-09 by replacement of the ELT battery.",
        }
    ]


def test_extracts_legacy_ad_claim_and_recurring_due_text() -> None:
    result = extract_structured_maintenance_data(
        [
            "C/W AD 11-10-09 on seats, rollers & rails by inspecting - "
            "due each annual/100 hrs.",
        ]
    )

    reference = result["adReferences"][0]
    assert reference["adNumber"] == "2011-10-09"
    assert reference["dispositionCandidate"] == "complied"
    assert reference["complianceMethodCandidate"] == "inspecting"
    assert reference["recurringCandidate"] is True
    assert reference["dueText"] == "due each annual/100 hrs"


def test_negated_ad_actions_never_become_positive_compliance() -> None:
    cases = {
        "AD 2024-01-02 was not complied with.": "not_complied",
        "Did not comply with AD 2024-01-02.": "not_complied",
        "AD 2024-01-02 has not yet been complied with.": "not_complied",
        "AD 2024-01-02 will not be complied with until parts arrive.": "not_complied",
        "AD 2024-01-02 cannot be complied with due to a parts backorder.": "not_complied",
        "AD 2024-01-02 is not going to be complied with at this time.": "not_complied",
        "AD 2024-01-02 was not inspected.": "not_inspected",
        "Inspection was not completed for AD 2024-01-02.": "not_inspected",
        "AD 2024-01-02 will not be inspected until parts arrive.": "not_inspected",
        "AD 2024-01-02 cannot be inspected at this time.": "not_inspected",
        (
            "AD 2024-01-02 will not be at this time due to an extended parts "
            "backorder situation from the overseas supplier complied with."
        ): "not_complied",
        "AD 2024-01-02 was not, in fact, complied with.": "not_complied",
        "AD 2024-01-02 was not, per the mechanic, inspected.": "not_inspected",
        "Did not comply, AD 2024-01-02 remains pending parts.": "mentioned",
    }

    for text, expected_disposition in cases.items():
        result = extract_structured_maintenance_data([text])

        assert result["adReferences"][0]["dispositionCandidate"] == expected_disposition


def test_ad_disposition_is_scoped_to_each_citation_clause() -> None:
    result = extract_structured_maintenance_data(
        [
            "Squawk not corrected, AD 2012-01-02 complied with per SB 123, "
            "AD 2013-02-03 was not complied with pending parts.",
        ]
    )

    references = {
        reference["adNumber"]: reference
        for reference in result["adReferences"]
    }
    assert references["2012-01-02"]["dispositionCandidate"] == "complied"
    assert references["2012-01-02"]["text"] == (
        "AD 2012-01-02 complied with per SB 123"
    )
    assert references["2013-02-03"]["dispositionCandidate"] == "not_complied"

    reverse_result = extract_structured_maintenance_data(
        [
            "AD 2011-01-01 was not, in fact, complied with pending parts, "
            "AD 2012-01-02 complied with per SB 123.",
        ]
    )
    reverse_references = {
        reference["adNumber"]: reference
        for reference in reverse_result["adReferences"]
    }
    assert reverse_references["2011-01-01"]["dispositionCandidate"] == (
        "not_complied"
    )
    assert reverse_references["2012-01-02"]["dispositionCandidate"] == "complied"

    sentence_result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 was not complied with. "
            "AD 2020-02-02 complied with per SB 123.",
        ]
    )
    sentence_references = {
        reference["adNumber"]: reference
        for reference in sentence_result["adReferences"]
    }
    assert sentence_references["2020-01-01"]["dispositionCandidate"] == (
        "not_complied"
    )
    assert sentence_references["2020-02-02"]["dispositionCandidate"] == (
        "complied"
    )

    unrelated_result = extract_structured_maintenance_data(
        [
            "SB 456 was not complied with, "
            "AD 2012-01-02 complied with per note.",
        ]
    )
    assert unrelated_result["adReferences"][0]["dispositionCandidate"] == (
        "complied"
    )

    abbreviation_result = extract_structured_maintenance_data(
        [
            "Ser. No. 12345 not complied, "
            "AD 2020-02-02 complied with per SB 123.",
        ]
    )
    assert abbreviation_result["adReferences"][0]["dispositionCandidate"] == (
        "complied"
    )


def test_ad_context_preserves_regulation_decimal_and_disposition() -> None:
    result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 IAW FAR 43.13 was not complied with.",
            "AD 2020-02-02 per FAR 91.411 was inspected.",
        ]
    )

    references = {
        reference["adNumber"]: reference
        for reference in result["adReferences"]
    }
    assert references["2020-01-01"]["dispositionCandidate"] == "not_complied"
    assert references["2020-01-01"]["text"] == (
        "AD 2020-01-01 IAW FAR 43.13 was not complied with."
    )
    assert references["2020-02-02"]["dispositionCandidate"] == "inspected"


def test_unrelated_trailing_action_cannot_promote_ad_disposition() -> None:
    result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 was noted, "
            "additional unrelated task complied with per SB 42, "
            "AD 2020-02-02 was not complied with.",
        ]
    )

    references = {
        reference["adNumber"]: reference
        for reference in result["adReferences"]
    }
    assert references["2020-01-01"]["dispositionCandidate"] == "mentioned"
    assert references["2020-02-02"]["dispositionCandidate"] == "not_complied"

    single_result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 was noted, "
            "unrelated task complied with per SB 42.",
        ]
    )
    assert single_result["adReferences"][0]["dispositionCandidate"] == (
        "mentioned"
    )
    single_multi_delimiter_result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 was noted, unrelated task complied with, "
            "per SB 42, additional note.",
        ]
    )
    assert single_multi_delimiter_result["adReferences"][0][
        "dispositionCandidate"
    ] == "mentioned"

    multi_delimiter_result = extract_structured_maintenance_data(
        [
            "AD 2020-01-01 was noted, unrelated task complied with, "
            "per SB 42, AD 2020-02-02 was inspected.",
        ]
    )
    multi_delimiter_references = {
        reference["adNumber"]: reference
        for reference in multi_delimiter_result["adReferences"]
    }
    assert multi_delimiter_references["2020-01-01"][
        "dispositionCandidate"
    ] == "mentioned"
    assert multi_delimiter_references["2020-02-02"][
        "dispositionCandidate"
    ] == "inspected"


def test_extracts_inspection_component_and_work_order_candidates() -> None:
    result = extract_structured_maintenance_data(
        [
            "Jones Avionics FAA CRS# YJ3R478Y",
            "Altimeter P/N 51391 S/N 2176",
            "Transponder P/N Narka AT150 Ser. No. 46163",
            "Tested and inspected per 14 CFR 91.411 and 91.413.",
            "W.O. Reference #12305",
        ]
    )

    assert result["inspectionTypes"] == [
        "altimeter_static_system",
        "transponder",
    ]
    assert result["facilityName"] == "Jones Avionics FAA CRS# YJ3R478Y"
    assert result["workOrderReference"] == "12305"
    assert result["componentReferences"] == [
        {
            "partNumbers": ["51391"],
            "serialNumbers": ["2176"],
            "text": "Altimeter P/N 51391 S/N 2176",
        },
        {
            "partNumbers": ["Narka AT150"],
            "serialNumbers": ["46163"],
            "text": "Transponder P/N Narka AT150 Ser. No. 46163",
        },
    ]
