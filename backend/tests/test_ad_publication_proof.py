import httpx

from app.services.ad_publication_proof import (
    document_contains_ad,
    drs_publish_date,
    fetch_and_retain_pdf,
    sanitized_source_url,
)


def test_publication_proof_uses_exact_ad_identity_and_drs_date() -> None:
    document = {
        "title": "Airworthiness Directives; Continental engines",
        "abstract": "This rule adopts AD 2023-17-04.",
    }

    assert document_contains_ad(document, "2023-17-04") is True
    assert document_contains_ad(document, "2022-04-04") is False
    assert drs_publish_date({"Publish Date": "09/21/2023"}) == "2023-09-21"


def test_publication_proof_removes_api_keys_from_provenance_urls() -> None:
    sanitized = sanitized_source_url(
        "https://api.govinfo.gov/packages/FR-2026-01-01/pdf?api_key=secret&x=1"
    )

    assert sanitized == "https://api.govinfo.gov/packages/FR-2026-01-01/pdf?x=1"
    assert "secret" not in sanitized


def test_publication_pdf_fetch_retries_and_retains_sanitized_url(
    tmp_path,
    monkeypatch,
) -> None:
    responses = iter(
        [
            httpx.Response(502),
            httpx.Response(200, content=b"%PDF-1.4\n% valid fixture\n"),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        response = next(responses)
        response.request = request
        return response

    monkeypatch.setattr("app.services.ad_publication_proof.time.sleep", lambda _: None)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        retained = fetch_and_retain_pdf(
            client,
            root=tmp_path,
            source_type="govinfo-issue-pdf",
            identifier="FR-2026-01-01",
            url="https://api.govinfo.gov/packages/FR-2026-01-01/pdf",
            params={"api_key": "secret"},
        )

    assert retained["mediaType"] == "application/pdf"
    assert retained["sourceUrl"] == "https://api.govinfo.gov/packages/FR-2026-01-01/pdf"
    assert "secret" not in retained["sourceUrl"]
