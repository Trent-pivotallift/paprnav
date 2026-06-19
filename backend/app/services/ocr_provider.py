from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRSpanResult:
    provider_block_id: str
    span_type: str
    text: str
    confidence: float
    bbox_left: float
    bbox_top: float
    bbox_width: float
    bbox_height: float
    bbox_units: str
    reading_order: int
    relationships: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class OCRPageResult:
    source_page_number: int
    page_label: str
    width_px: int
    height_px: int
    rotation_degrees: float
    extraction_confidence: float
    spans: list[OCRSpanResult]


@dataclass(frozen=True)
class OCRProviderResult:
    provider_name: str
    provider_version: str
    configuration_hash: str
    pages: list[OCRPageResult]


class OCRProvider:
    provider_name: str
    provider_version: str
    configuration_hash: str

    def process_upload(self, *, original_filename: str, content_type: str) -> OCRProviderResult:
        raise NotImplementedError


class DeterministicFixtureOCRProvider(OCRProvider):
    provider_name = "deterministic_fixture"
    provider_version = "0.1.0"
    configuration_hash = "fixture-logbook-v1"

    def process_upload(self, *, original_filename: str, content_type: str) -> OCRProviderResult:
        page_count = 2 if content_type == "application/pdf" else 1
        pages = [self._annual_page(1)]
        if page_count > 1:
            pages.append(self._oil_change_page(2))
        return OCRProviderResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            configuration_hash=self.configuration_hash,
            pages=pages,
        )

    def _annual_page(self, page_number: int) -> OCRPageResult:
        return OCRPageResult(
            source_page_number=page_number,
            page_label="Airframe page 1",
            width_px=2550,
            height_px=3300,
            rotation_degrees=0,
            extraction_confidence=96.0,
            spans=[
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-1",
                    span_type="LINE",
                    text="2026-01-15 Annual inspection completed in accordance with 14 CFR Part 43 Appendix D.",
                    confidence=94.0,
                    bbox_left=0.08,
                    bbox_top=0.12,
                    bbox_width=0.84,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=1,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-2",
                    span_type="LINE",
                    text="Performer: A. Mechanic A&P IA",
                    confidence=62.0,
                    bbox_left=0.08,
                    bbox_top=0.18,
                    bbox_width=0.48,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=2,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p1-line-3",
                    span_type="LINE",
                    text="Tach: 1022.4 Hobbs: 1188.2 Total: 3201.7",
                    confidence=88.0,
                    bbox_left=0.08,
                    bbox_top=0.24,
                    bbox_width=0.58,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=3,
                ),
            ],
        )

    def _oil_change_page(self, page_number: int) -> OCRPageResult:
        return OCRPageResult(
            source_page_number=page_number,
            page_label="Engine page 1",
            width_px=2550,
            height_px=3300,
            rotation_degrees=0,
            extraction_confidence=91.0,
            spans=[
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-1",
                    span_type="LINE",
                    text="2026-02-12 Changed engine oil and filter; inspected screen with no defects noted.",
                    confidence=93.0,
                    bbox_left=0.08,
                    bbox_top=0.12,
                    bbox_width=0.82,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=1,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-2",
                    span_type="LINE",
                    text="Performer: M. Mechanic A&P",
                    confidence=82.0,
                    bbox_left=0.08,
                    bbox_top=0.18,
                    bbox_width=0.42,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=2,
                ),
                OCRSpanResult(
                    provider_block_id="fixture-p2-line-3",
                    span_type="LINE",
                    text="Tach: 1035.8",
                    confidence=58.0,
                    bbox_left=0.08,
                    bbox_top=0.24,
                    bbox_width=0.24,
                    bbox_height=0.04,
                    bbox_units="ratio",
                    reading_order=3,
                ),
            ],
        )


def get_ocr_provider() -> OCRProvider:
    return DeterministicFixtureOCRProvider()
