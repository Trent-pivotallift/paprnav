from app.services.page_planning import (
    logical_region_specs,
    native_text_routing_assessment,
)


def test_side_by_side_page_creates_two_coordinate_preserving_regions() -> None:
    regions = logical_region_specs(
        {"attributes": ["scanned", "side_by_side", "continuation_sensitive"]}
    )

    assert [region["regionKey"] for region in regions] == ["left", "right"]
    assert [region["readingOrder"] for region in regions] == [1, 2]
    assert sum(region["bboxWidth"] for region in regions) == 1.0
    assert all(region["bboxHeight"] == 1.0 for region in regions)


def test_uncertain_orientation_keeps_complete_source_page_region() -> None:
    regions = logical_region_specs(
        {"attributes": ["wide_layout", "orientation_unverified"]}
    )

    assert len(regions) == 1
    assert regions[0]["regionKey"] == "full"
    assert regions[0]["regionType"] == "source_page"


def test_native_routing_gate_requires_every_structural_and_visual_check() -> None:
    assessment = native_text_routing_assessment(
        {
            "reliableCandidate": True,
            "validGlyphRatio": 1.0,
            "positionedSampleRatio": 1.0,
            "plausibleFontRatio": 1.0,
            "duplicateLineRatio": 0.0,
            "extractorAgreement": 1.0,
            "estimatedImageCoverage": 0.0,
        },
        {
            "routingClass": "native_text",
            "attributes": ["typed", "dense", "single_page"],
        },
    )

    assert assessment["eligibleIfActivated"] is True
    assert assessment["wouldBypassTextract"] is True
    assert assessment["activationStatus"] == "active_controlled_fixture_gate_v1"


def test_native_routing_gate_rejects_mixed_or_uncertain_page() -> None:
    assessment = native_text_routing_assessment(
        {
            "reliableCandidate": True,
            "validGlyphRatio": 1.0,
            "positionedSampleRatio": 1.0,
            "plausibleFontRatio": 1.0,
            "duplicateLineRatio": 0.0,
            "extractorAgreement": 1.0,
            "estimatedImageCoverage": 0.0,
        },
        {
            "routingClass": "mixed",
            "attributes": ["typed", "orientation_unverified"],
        },
    )

    assert assessment["eligibleIfActivated"] is False
    assert assessment["wouldBypassTextract"] is False
    assert "orientation_unverified" in assessment["disqualifyingAttributes"]
