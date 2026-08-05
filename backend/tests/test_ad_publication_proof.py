from app.services.ad_publication_proof import document_contains_ad, drs_publish_date


def test_publication_proof_uses_exact_ad_identity_and_drs_date() -> None:
    document = {
        "title": "Airworthiness Directives; Continental engines",
        "abstract": "This rule adopts AD 2023-17-04.",
    }

    assert document_contains_ad(document, "2023-17-04") is True
    assert document_contains_ad(document, "2022-04-04") is False
    assert drs_publish_date({"Publish Date": "09/21/2023"}) == "2023-09-21"
