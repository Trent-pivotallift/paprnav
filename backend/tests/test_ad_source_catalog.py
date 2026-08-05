from pathlib import Path

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.models.core import ADCostLedgerEntry, ADSourceDocument
from app.services.ad_source_catalog import GovInfoClient, retain_source_document


def test_source_document_retention_is_content_addressed_and_idempotent(
    db_session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_LOCAL_STORAGE_PATH", str(tmp_path))
    get_settings.cache_clear()

    first, first_created = retain_source_document(
        db_session,
        data=b"official source",
        source_system="govinfo",
        source_type="pdf",
        source_identifier="FR-1993-07-13-document",
        source_url="https://www.govinfo.gov/example.pdf",
        filename="example.pdf",
        media_type="application/pdf",
    )
    second, second_created = retain_source_document(
        db_session,
        data=b"official source",
        source_system="govinfo",
        source_type="pdf",
        source_identifier="FR-1993-07-13-document",
        source_url="https://www.govinfo.gov/example.pdf",
        filename="example.pdf",
        media_type="application/pdf",
    )

    assert first_created is True
    assert second_created is False
    assert first.id == second.id
    assert (tmp_path / first.storage_key).read_bytes() == b"official source"
    assert len(db_session.scalars(select(ADSourceDocument)).all()) == 1
    assert len(db_session.scalars(select(ADCostLedgerEntry)).all()) == 1
    get_settings.cache_clear()


def test_govinfo_search_paginates_until_offset_is_exhausted(monkeypatch) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        calls.append(body)
        if '"offsetMark":"*"' in body:
            return httpx.Response(
                200,
                json={"count": 2, "offsetMark": "next", "results": [{"packageId": "one"}]},
            )
        return httpx.Response(
            200,
            json={"count": 2, "offsetMark": "next", "results": [{"packageId": "two"}]},
        )

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", client_factory)
    result = GovInfoClient(api_key="test").search_all("collection:FR test")

    assert [item["packageId"] for item in result["results"]] == ["one", "two"]
    assert result["retrievedCount"] == 2
    assert len(calls) == 2
