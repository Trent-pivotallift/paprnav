from pathlib import Path

import pytest
from PIL import Image

from app.core.config import get_settings
from app.models.core import IngestionPage, OCRTextSpan
from app.services.ingestion import (
    entry_drafts_from_page,
    parse_date,
    parse_float_field,
    parse_performer,
    span_requires_raw_ocr_correction,
    strip_date,
)
from app.services.layout_first_ocr import (
    LayoutFirstVLMOCRProvider,
    LayoutRegion,
    OllamaGLMRegionRecognizer,
    RegionRecognition,
    crop_layout_region,
    layout_region_from_glm,
    recognized_content_to_text,
)
from app.services.ocr_provider import get_ocr_provider


class FakeLayoutDetector:
    model_version = "fake-layout-v1"

    def __init__(self, regions: list[LayoutRegion]) -> None:
        self.regions = regions

    def detect(self, image) -> list[LayoutRegion]:
        return self.regions


class FakeRegionRecognizer:
    model_version = "fake-recognizer-v1"

    def __init__(self, responses: list[RegionRecognition]) -> None:
        self.responses = responses

    def recognize(self, image, task_type: str) -> RegionRecognition:
        return self.responses.pop(0)


class FakeHTTPResponse:
    def __init__(self, body: dict) -> None:
        self.body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.body


class FakeHTTPClient:
    def __init__(self, body: dict) -> None:
        self.body = body
        self.requests = []

    def post(self, url: str, **kwargs) -> FakeHTTPResponse:
        self.requests.append({"url": url, **kwargs})
        return FakeHTTPResponse(self.body)


def region(
    region_id: str,
    *,
    order: int,
    left: float,
    confidence: float,
) -> LayoutRegion:
    return LayoutRegion(
        provider_region_id=region_id,
        reading_order=order,
        label="table",
        task_type="table",
        layout_confidence=confidence,
        bbox_left=left,
        bbox_top=0.08,
        bbox_width=0.44,
        bbox_height=0.82,
        polygon=[
            [left, 0.08],
            [left + 0.44, 0.08],
            [left + 0.44, 0.90],
            [left, 0.90],
        ],
    )


def write_test_png(path: Path) -> None:
    path.parent.mkdir(parents=True)
    Image.new("RGB", (1000, 800), "white").save(path)


def test_layout_crop_adds_bounded_context_without_crossing_page_edges() -> None:
    image = Image.new("RGB", (1000, 800), "white")
    interior = region("interior", order=1, left=0.10, confidence=90)
    assert crop_layout_region(image, interior).size == (460, 672)

    edge = LayoutRegion(
        provider_region_id="edge",
        reading_order=1,
        label="text",
        task_type="text",
        layout_confidence=90,
        bbox_left=0,
        bbox_top=0,
        bbox_width=0.20,
        bbox_height=0.20,
    )
    assert crop_layout_region(image, edge).size == (210, 168)
    with pytest.raises(ValueError, match="padding"):
        crop_layout_region(image, edge, padding_ratio=0.1)
    large_image = Image.new("RGB", (5000, 4000), "white")
    resized_crop = crop_layout_region(large_image, interior)
    assert max(resized_crop.size) == 2048
    with pytest.raises(ValueError, match="maximum dimension"):
        crop_layout_region(image, edge, max_dimension_px=500)


def test_layout_first_provider_preserves_regions_and_separate_confidence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PAPRNAV_OCR_MAX_PDF_PAGES", "3")
    monkeypatch.setenv(
        "PAPRNAV_LAYOUT_FIRST_COMPUTE_RATE_USD_PER_HOUR",
        "36",
    )
    timestamps = iter([100.0, 102.0])
    monkeypatch.setattr(
        "app.services.layout_first_ocr.time.monotonic",
        lambda: next(timestamps),
    )
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "logbook.png"
    write_test_png(upload_path)
    detector = FakeLayoutDetector(
        [
            region("right-entry", order=2, left=0.52, confidence=89.0),
            region("left-entry", order=1, left=0.02, confidence=75.0),
        ]
    )
    recognizer = FakeRegionRecognizer(
        [
            RegionRecognition(
                text="12-17-12 Tach = 1276.8 Total Time = 5405.5",
                metadata={"latency_ms": 10.0},
            ),
            RegionRecognition(
                text="Date 2/5/13 Jones Avionics",
                metadata={"latency_ms": 12.0},
            ),
        ]
    )
    provider = LayoutFirstVLMOCRProvider(
        detector=detector,
        recognizer=recognizer,
        storage_root=str(storage_root),
    )

    result = provider.process_upload(
        original_filename="logbook.png",
        content_type="image/png",
        storage_backend="local",
        storage_key="uploads/logbook.png",
    )

    assert result.provider_name == "layout_first_vlm"
    assert result.billable_page_count == 1
    assert result.metadata["third_party_processing"] is False
    assert result.metadata["layout_device"] == "cpu"
    assert result.metadata["recognition_runtime"] == "ollama"
    assert result.metadata["layout_model"] == "fake-layout-v1"
    assert result.metadata["recognition_model"] == "fake-recognizer-v1"
    assert result.metadata["processing_seconds"] == 2
    assert result.metadata["pricing_unit"] == "compute_hour"
    assert result.metadata["pricing_rate_usd"] == 36
    assert result.metadata["estimated_cost_usd"] == 0.02
    assert result.pages[0].width_px == 1000
    assert result.pages[0].height_px == 800
    assert result.pages[0].extraction_confidence is None
    assert [span.provider_block_id for span in result.pages[0].spans] == [
        "left-entry",
        "right-entry",
    ]
    first_span = result.pages[0].spans[0]
    assert first_span.span_type == "REGION_TABLE"
    assert first_span.confidence is None
    assert first_span.polygon[0] == [0.02, 0.08]
    assert first_span.relationships[0]["layout"]["confidence"] == 75.0
    assert first_span.relationships[0]["recognition"]["confidence"] is None


def test_layout_first_provider_rejects_out_of_range_geometry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "logbook.png"
    write_test_png(upload_path)
    invalid_region = LayoutRegion(
        provider_region_id="bad-region",
        reading_order=1,
        label="text",
        task_type="text",
        layout_confidence=90,
        bbox_left=0.9,
        bbox_top=0.1,
        bbox_width=0.2,
        bbox_height=0.2,
    )
    provider = LayoutFirstVLMOCRProvider(
        detector=FakeLayoutDetector([invalid_region]),
        recognizer=FakeRegionRecognizer([RegionRecognition(text="not used")]),
        storage_root=str(storage_root),
    )

    with pytest.raises(ValueError, match="extends past page width"):
        provider.process_upload(
            original_filename="logbook.png",
            content_type="image/png",
            storage_backend="local",
            storage_key="uploads/logbook.png",
        )


def test_layout_first_provider_rejects_invalid_polygon(
    tmp_path: Path,
) -> None:
    get_settings.cache_clear()
    storage_root = tmp_path / "storage"
    upload_path = storage_root / "uploads" / "logbook.png"
    write_test_png(upload_path)
    invalid_region = LayoutRegion(
        provider_region_id="bad-polygon",
        reading_order=1,
        label="table",
        task_type="table",
        layout_confidence=90,
        bbox_left=0.02,
        bbox_top=0.08,
        bbox_width=0.44,
        bbox_height=0.82,
        polygon=[[0.02, 0.08], [1.1, 0.08], [0.46, 0.9]],
    )
    provider = LayoutFirstVLMOCRProvider(
        detector=FakeLayoutDetector([invalid_region]),
        recognizer=FakeRegionRecognizer([RegionRecognition(text="not used")]),
        storage_root=str(storage_root),
    )

    with pytest.raises(ValueError, match="out-of-range polygon"):
        provider.process_upload(
            original_filename="logbook.png",
            content_type="image/png",
            storage_backend="local",
            storage_key="uploads/logbook.png",
        )


def test_glm_layout_score_requires_documented_zero_to_one_scale() -> None:
    with pytest.raises(ValueError, match="documented 0-1 scale"):
        layout_region_from_glm(
            {
                "bbox_2d": [0, 0, 500, 500],
                "score": 75,
            },
            fallback_index=0,
        )


def test_ollama_recognizer_converts_table_html_without_inventing_confidence() -> None:
    client = FakeHTTPClient(
        {
            "response": (
                '<table><tr><td>Date</td><td>2/5/13</td></tr>'
                "<tr><td>Jones Avionics</td><td>N3671L</td></tr></table>"
            ),
            "eval_count": 42,
        }
    )
    recognizer = OllamaGLMRegionRecognizer(
        base_url="http://127.0.0.1:11434",
        model="glm-ocr:latest",
        timeout_seconds=30,
        http_client=client,
    )

    result = recognizer.recognize(Image.new("RGB", (100, 100), "white"), "table")

    assert result.text == "Date\n2/5/13\nJones Avionics\nN3671L"
    assert result.confidence is None
    assert result.metadata["content_format"] == "html_table"
    assert "raw_content" not in result.metadata
    assert result.metadata["raw_content_bytes"] > 0
    assert result.metadata["raw_content_persisted"] is False
    assert result.metadata["raw_artifact_location"] is None
    assert result.metadata["eval_count"] == 42
    request = client.requests[0]
    assert request["url"] == "http://127.0.0.1:11434/api/generate"
    assert request["json"]["prompt"] == "Table Recognition:"
    assert request["json"]["images"][0]


def test_ollama_recognizer_rejects_remote_endpoint() -> None:
    with pytest.raises(ValueError, match="only permits a loopback"):
        OllamaGLMRegionRecognizer(
            base_url="https://ocr.example.com",
            model="glm-ocr:latest",
            timeout_seconds=30,
        )


def test_recognized_content_keeps_plain_text_unchanged() -> None:
    assert recognized_content_to_text("12-17-12 Tach = 1276.8") == (
        "12-17-12 Tach = 1276.8",
        "text",
    )


def test_parse_date_handles_region_ocr_concatenated_labels() -> None:
    parsed, extracted = parse_date("Jones Avionics Date12/5/13N#3671L")

    assert extracted is True
    assert parsed.isoformat() == "2013-12-05"


def test_parse_date_uses_earliest_entry_date_before_iso_ad_reference() -> None:
    parsed, extracted = parse_date(
        "12-10-14 Tach-1293.2. Complied with AD 2011-10-09 on both seats."
    )

    assert extracted is True
    assert parsed.isoformat() == "2014-12-10"


def test_parse_date_skips_invalid_earlier_candidate() -> None:
    parsed, extracted = parse_date(
        "Date 99-99-99 corrected to 12-10-14."
    )

    assert extracted is True
    assert parsed.isoformat() == "2014-12-10"


def test_parse_float_field_accepts_hyphen_separator() -> None:
    assert parse_float_field(["Tach - 1289.83"], "Tach") == 1289.83


def test_parse_float_field_rejects_one_digit_conflict_with_standalone_table_value() -> None:
    assert parse_float_field(["4454.2", "TOTAL TIME: 4954 Hrs."], "Total") is None


def test_parse_performer_extracts_typed_mechanic_and_credential() -> None:
    assert parse_performer(["Ronald Stegemoller", "A&P# 2192007 I.A."]) == (
        "Ronald Stegemoller",
        "A&P#2192007 I.A.",
    )


def test_parse_performer_extracts_repair_facility_and_work_order() -> None:
    assert parse_performer(
        [
            "Jones Avionics FAA CRS#YVJR478Y",
            "W.O. Reference #12305",
        ]
    ) == ("Jones Avionics", "FAA CRS#YVJR478Y; W.O. #12305")


def test_parse_performer_does_not_invent_work_order_from_intervening_text() -> None:
    assert parse_performer(
        ["Jones Avionics FAA CRS#YVJR478Y", "Inspector W.O. Certified Reference to #20,000 ft"]
    ) == ("Jones Avionics", "FAA CRS#YVJR478Y")


def test_parse_performer_does_not_treat_signature_date_label_as_name() -> None:
    assert parse_performer(["This date Carlis Jones", "A&P 497795"]) == (
        None,
        "A&P#497795",
    )


def test_strip_date_preserves_ad_reference_inside_description() -> None:
    text = "Complied with AD 11-10-09 on seats and rails."

    assert strip_date(text) == text
    assert strip_date("12-17-12 Tach = 1276.8") == "Tach = 1276.8"


def test_entry_description_removes_selected_date_and_preserves_ad_reference() -> None:
    page = IngestionPage(
        id="page-date",
        ingestion_job_id="job-date",
        upload_id="upload-date",
        source_page_number=1,
        current_page_order=1,
        width_px=1000,
        height_px=800,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id="span-date",
            ocr_run_id="run-date",
            ingestion_page_id="page-date",
            provider_block_id="entry-date",
            span_type="REGION_TABLE",
            text=(
                "Jones Avionics FAA Repair Station 281-433-6077Date12/5/13N#3671L\n"
                "Complied with AD 11-10-09 on seats and rails."
            ),
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0.51,
            bbox_top=0.05,
            bbox_width=0.47,
            bbox_height=0.88,
            bbox_units="ratio",
            reading_order=1,
        )
    ]

    drafts = entry_drafts_from_page(page)

    assert len(drafts) == 1
    assert drafts[0].entry_date.isoformat() == "2013-12-05"
    assert "12/5/13" not in drafts[0].description
    assert "DateN#3671L" not in drafts[0].description
    assert "6077N#3671L" in drafts[0].description
    assert "AD 11-10-09" in drafts[0].description


def test_header_only_multiline_region_does_not_create_entry() -> None:
    page = IngestionPage(
        id="page-header",
        ingestion_job_id="job-header",
        upload_id="upload-header",
        source_page_number=1,
        current_page_order=1,
        width_px=1000,
        height_px=800,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id="span-header",
            ocr_run_id="run-header",
            ingestion_page_id="page-header",
            provider_block_id="header",
            span_type="REGION_TABLE",
            text=(
                "YEAR\nDATE\nRECORDING\nTODAY'S\nTOTAL TIME IN SERVICE\n"
                "Description of Inspections, Tests, Repairs and Alterations\n"
                "Entries must be endorsed"
            ),
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0,
            bbox_top=0,
            bbox_width=1,
            bbox_height=0.2,
            bbox_units="ratio",
            reading_order=1,
        )
    ]

    assert entry_drafts_from_page(page) == []


def test_unfamiliar_header_only_region_does_not_create_entry() -> None:
    page = IngestionPage(
        id="page-alt-header",
        ingestion_job_id="job-alt-header",
        upload_id="upload-alt-header",
        source_page_number=1,
        current_page_order=1,
        width_px=1000,
        height_px=800,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id="span-alt-header",
            ocr_run_id="run-alt-header",
            ingestion_page_id="page-alt-header",
            provider_block_id="alt-header",
            span_type="REGION_TABLE",
            text="AIRFRAME LOG\nDescription of Work Performed\nCertified By",
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0,
            bbox_top=0,
            bbox_width=1,
            bbox_height=0.2,
            bbox_units="ratio",
            reading_order=1,
        )
    ]

    assert entry_drafts_from_page(page) == []


def test_dateless_maintenance_action_still_creates_review_candidate() -> None:
    page = IngestionPage(
        id="page-dateless",
        ingestion_job_id="job-dateless",
        upload_id="upload-dateless",
        source_page_number=1,
        current_page_order=1,
        width_px=1000,
        height_px=800,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id="span-dateless",
            ocr_run_id="run-dateless",
            ingestion_page_id="page-dateless",
            provider_block_id="dateless-entry",
            span_type="REGION_TEXT",
            text="Replaced engine oil filter and inspected aircraft.",
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0.2,
            bbox_top=0.2,
            bbox_width=0.6,
            bbox_height=0.2,
            bbox_units="ratio",
            reading_order=1,
        )
    ]

    drafts = entry_drafts_from_page(page)

    assert len(drafts) == 1
    assert drafts[0].entry_date is None
    assert drafts[0].description == (
        "Replaced engine oil filter and inspected aircraft."
    )


def test_region_without_recognition_confidence_uses_candidate_review() -> None:
    region_span = OCRTextSpan(
        span_type="REGION_TABLE",
        text="Date 2/5/13 Jones Avionics",
        confidence=None,
        confidence_scale="0_100",
        bbox_units="ratio",
        reading_order=1,
    )
    low_confidence_line = OCRTextSpan(
        span_type="LINE",
        text="uncertain text",
        confidence=60,
        confidence_scale="0_100",
        bbox_units="ratio",
        reading_order=1,
    )

    assert span_requires_raw_ocr_correction(region_span) is False
    assert span_requires_raw_ocr_correction(low_confidence_line) is True


def test_region_spans_split_two_entries_and_preserve_absent_times_as_null() -> None:
    page = IngestionPage(
        id="page-1",
        ingestion_job_id="job-1",
        upload_id="upload-1",
        source_page_number=1,
        current_page_order=1,
        width_px=3000,
        height_px=800,
    )
    page.ocr_spans = [
        OCRTextSpan(
            id="span-left",
            ocr_run_id="run-1",
            ingestion_page_id="page-1",
            provider_block_id="left-entry",
            span_type="REGION_TABLE",
            text=(
                "YEAR\nDATE\nDescription of Inspections, Tests, Repairs and Alterations\n"
                "Entries must be endorsed. (See back pages for other entries.)\n"
                "RS Aircraft Service\n12-17-12\n"
                "Tach = 1276.8\nTotal Time = 5405.5\n"
                "Performed an annual inspection."
            ),
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0.02,
            bbox_top=0.08,
            bbox_width=0.47,
            bbox_height=0.82,
            bbox_units="ratio",
            reading_order=1,
        ),
        OCRTextSpan(
            id="span-right",
            ocr_run_id="run-1",
            ingestion_page_id="page-1",
            provider_block_id="right-entry",
            span_type="REGION_TABLE",
            text=(
                "YEAR:_DATE\nJones Avionics FAA CRS YVJR478Y\n"
                "Date\n2/5/13\nN3671L\nAltimeter and transponder inspected."
            ),
            confidence=None,
            confidence_scale="0_100",
            bbox_left=0.51,
            bbox_top=0.05,
            bbox_width=0.47,
            bbox_height=0.88,
            bbox_units="ratio",
            reading_order=2,
        ),
    ]

    drafts = entry_drafts_from_page(page)

    assert len(drafts) == 2
    assert all(draft.min_confidence is None for draft in drafts)
    assert drafts[0].entry_date.isoformat() == "2012-12-17"
    assert drafts[0].tach_time == 1276.8
    assert drafts[0].total_time == 5405.5
    assert drafts[1].entry_date.isoformat() == "2013-02-05"
    assert drafts[1].tach_time is None
    assert drafts[1].total_time is None
    assert drafts[0].requires_review is True
    assert drafts[1].requires_review is True


def test_ocr_provider_selection_uses_layout_first_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_OCR_PROVIDER", "layout_first_vlm")
    get_settings.cache_clear()

    provider = get_ocr_provider()

    assert isinstance(provider, LayoutFirstVLMOCRProvider)
