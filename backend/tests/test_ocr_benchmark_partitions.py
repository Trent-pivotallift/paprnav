import json
from pathlib import Path


MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / ".ai"
    / "OCR_BENCHMARK_PARTITIONS.json"
)


def test_ocr_benchmark_partitions_are_complete_disjoint_and_frozen() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    partitions = manifest["partitions"]

    assert manifest["version"] == "2026-07-25-v1"
    assert manifest["policy"] == {
        "ocrRefinementPercent": 25,
        "fullIngestionPercent": 50,
        "ingestionAdHoldoutPercent": 25,
        "holdoutMayInfluenceRefinement": False,
    }
    assert {
        name: partition["pageCount"]
        for name, partition in partitions.items()
    } == {
        "ocr_refinement": 11,
        "full_ingestion": 22,
        "ingestion_ad_holdout": 11,
    }

    for document, expected_pages in (("aircraft", set(range(1, 16))), ("engine", set(range(1, 30)))):
        assigned = [
            page
            for partition in partitions.values()
            for page in partition["pages"][document]
        ]
        assert len(assigned) == len(set(assigned))
        assert set(assigned) == expected_pages

    derived = manifest["derivedFiles"]["N3671L_page2.pdf"]
    assert derived["duplicateOf"] == {"document": "aircraft", "page": 2}
    assert derived["countAsUniquePage"] is False
