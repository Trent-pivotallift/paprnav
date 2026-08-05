from pathlib import Path

from app.services.ad_source_proof import (
    compare_ad_sets,
    filter_drs_rows,
    read_drs_result_xlsx,
)


def test_filter_and_comparison_preserve_revision_and_product_scope() -> None:
    rows = [
        {
            "AD Number": "94-05-05 R1",
            "Status": "Current",
            "Product Type": "Engine",
            "Model": "O-300-A | O-300-D",
        },
        {
            "AD Number": "98-21-21 R1",
            "Status": "Current",
            "Product Type": "Appliance",
            "Model": "172G | 172H",
        },
    ]

    selected = filter_drs_rows(rows, model="O-300-D", product_type="Engine")
    comparison = compare_ad_sets(
        [{"AD Number": "94-05-05 R1"}],
        selected,
    )

    assert comparison["matches"] is True
    assert comparison["manualIsSubset"] is True
    assert comparison["bulkIdentifiers"] == ["1994-05-05 R1"]


def test_read_drs_result_xlsx_reads_user_control_fixture() -> None:
    path = Path(
        ".data/ad-source-proof/manual/drs/cessna-172g/2026-08-04/"
        "O-300-D_lists.xlsx"
    )
    if not path.exists():
        return

    rows = read_drs_result_xlsx(path)

    assert len(rows) == 10
    assert rows[0]["AD Number"] == "2023-17-04"
    assert {row["Product Type"] for row in rows} == {"Engine"}
