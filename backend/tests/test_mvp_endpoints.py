from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import IngestionJob, LogbookEntryEvidence
from app.services.ingestion import process_ingestion_job
from tests.conftest import TEST_PASSWORD, login


def test_auth_register_me_and_logout(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": " New.User@Paprnav.Local ", "name": "New User", "password": TEST_PASSWORD},
    )
    assert register_response.status_code == 201
    assert register_response.json()["user"]["email"] == "new.user@paprnav.local"

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["name"] == "New User"

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    logged_out_response = client.get("/api/v1/auth/me")
    assert logged_out_response.status_code == 401


def test_profile_update_persists_current_user(client: TestClient, demo_data: dict[str, object]) -> None:
    login(client, "owner.test@paprnav.local")

    update_response = client.patch("/api/v1/auth/profile", json={"name": "Olivia Updated"})
    assert update_response.status_code == 200
    assert update_response.json()["user"]["name"] == "Olivia Updated"
    assert update_response.json()["user"]["email"] == "owner.test@paprnav.local"

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["name"] == "Olivia Updated"


def test_aircraft_visibility_and_auth_boundaries(client: TestClient, demo_data: dict[str, object]) -> None:
    unauthenticated_response = client.get("/api/v1/aircraft")
    assert unauthenticated_response.status_code == 401

    login(client, "owner.test@paprnav.local")
    owner_response = client.get("/api/v1/aircraft")
    assert owner_response.status_code == 200
    owner_aircraft = owner_response.json()["aircraft"]
    assert len(owner_aircraft) == 1
    assert owner_aircraft[0]["nNumber"] == "N123AB"

    shop_client = TestClient(client.app)
    login(shop_client, "shop.test@paprnav.local")
    shop_response = shop_client.get("/api/v1/aircraft")
    assert shop_response.status_code == 200
    assert [item["nNumber"] for item in shop_response.json()["aircraft"]] == ["N123AB"]

    stranger_client = TestClient(client.app)
    login(stranger_client, "stranger.test@paprnav.local")
    stranger_response = stranger_client.get("/api/v1/aircraft")
    assert stranger_response.status_code == 200
    assert stranger_response.json()["aircraft"] == []


def test_owner_can_assign_aircraft_to_maintenance_shop(client: TestClient, demo_data: dict[str, object]) -> None:
    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")

    list_response = client.get(f"/api/v1/aircraft/{aircraft_id}/assignments")
    assert list_response.status_code == 200
    assert [item["organizationName"] for item in list_response.json()["assignments"]] == ["Maintenance Shop"]

    create_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/assignments",
        json={"maintenanceUserEmail": "unassigned.shop@paprnav.local"},
    )
    assert create_response.status_code == 201
    assert create_response.json()["organizationName"] == "Unassigned Maintenance Shop"
    assert create_response.json()["role"] == "maintainer"

    assigned_shop_client = TestClient(client.app)
    login(assigned_shop_client, "unassigned.shop@paprnav.local")
    visible_response = assigned_shop_client.get("/api/v1/aircraft")
    assert visible_response.status_code == 200
    assert [item["nNumber"] for item in visible_response.json()["aircraft"]] == ["N123AB"]

    blocked_response = assigned_shop_client.post(
        f"/api/v1/aircraft/{aircraft_id}/assignments",
        json={"maintenanceUserEmail": "shop.test@paprnav.local"},
    )
    assert blocked_response.status_code == 403


def test_logbook_entry_crud_and_cross_aircraft_boundary(client: TestClient, demo_data: dict[str, object]) -> None:
    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")

    create_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/logbook-entries",
        json={
            "section": "airframe",
            "entryDate": "2026-06-17",
            "description": "Annual inspection completed.",
            "performerName": "A. Mechanic",
            "performerCredential": "A&P IA",
            "tachTime": 123.45,
        },
    )
    assert create_response.status_code == 201
    entry = create_response.json()
    assert entry["sourceType"] == "manual"
    assert entry["reviewStatus"] == "verified"

    list_response = client.get(f"/api/v1/aircraft/{aircraft_id}/logbook-entries?section=airframe")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["entries"]] == [entry["id"]]

    update_response = client.patch(
        f"/api/v1/aircraft/{aircraft_id}/logbook-entries/{entry['id']}",
        json={"reviewStatus": "needs_review", "description": "Annual inspection reviewed."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["reviewStatus"] == "needs_review"

    stranger_client = TestClient(client.app)
    login(stranger_client, "stranger.test@paprnav.local")
    hidden_response = stranger_client.get(f"/api/v1/aircraft/{aircraft_id}/logbook-entries/{entry['id']}")
    assert hidden_response.status_code == 404


def test_upload_create_download_validation_and_access_boundary(client: TestClient, demo_data: dict[str, object]) -> None:
    aircraft_id = demo_data["aircraft"].id
    original_bytes = b"%PDF-1.4 paprnav test upload"
    login(client, "owner.test@paprnav.local")

    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe"},
        files={"file": ("logbook.pdf", BytesIO(original_bytes), "application/pdf")},
    )
    assert upload_response.status_code == 201
    upload = upload_response.json()["upload"]
    ingestion_job = upload_response.json()["ingestionJob"]
    assert upload["originalFilename"] == "logbook.pdf"
    assert upload["contentType"] == "application/pdf"
    assert upload["fileSizeBytes"] == len(original_bytes)
    assert upload["status"] == "stored"
    assert upload["downloadUrl"] == f"/api/v1/uploads/{upload['id']}/download"
    assert ingestion_job["uploadId"] == upload["id"]
    assert ingestion_job["status"] == "queued"

    download_response = client.get(upload["downloadUrl"])
    assert download_response.status_code == 200
    assert download_response.content == original_bytes

    invalid_type_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe"},
        files={"file": ("notes.txt", BytesIO(b"not a scan"), "text/plain")},
    )
    assert invalid_type_response.status_code == 415

    invalid_section_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "avionics"},
        files={"file": ("logbook.pdf", BytesIO(original_bytes), "application/pdf")},
    )
    assert invalid_section_response.status_code == 400

    stranger_client = TestClient(client.app)
    login(stranger_client, "stranger.test@paprnav.local")
    hidden_upload_response = stranger_client.get(upload["downloadUrl"])
    assert hidden_upload_response.status_code == 404


def test_ocr_ingestion_verification_correction_and_entry_extraction(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")

    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe"},
        files={"file": ("multipage-logbook.pdf", BytesIO(b"%PDF-1.4 multipage fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]

    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job)

    detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["job"]["status"] == "awaiting_page_review"
    assert detail["job"]["ocrStatus"] == "complete"
    assert len(detail["pages"]) == 2
    low_confidence_spans = [
        span
        for page in detail["pages"]
        for span in page["spans"]
        if span["confidence"] is not None and span["confidence"] < 80
    ]
    assert low_confidence_spans

    verify_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/page-verification",
        json={
            "pages": [
                {"pageId": page["id"], "currentPageOrder": page["currentPageOrder"]}
                for page in detail["pages"]
            ],
            "isOrderConfirmed": True,
            "isComplete": True,
            "missingOrUncertainNotes": None,
        },
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["job"]["verificationStatus"] == "verified"

    correction_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/ocr-corrections",
        json={
            "ocrTextSpanId": low_confidence_spans[0]["id"],
            "correctedText": low_confidence_spans[0]["text"],
            "correctionReason": "low_confidence",
        },
    )
    assert correction_response.status_code == 201
    assert correction_response.json()["originalConfidence"] < 80

    extract_response = client.post(f"/api/v1/ingestion-jobs/{job_id}/extract-logbook-entries")
    assert extract_response.status_code == 200
    entries = extract_response.json()["entries"]
    assert len(entries) == 2
    assert entries[0]["section"] == "airframe"

    evidence_count = db_session.scalar(
        select(func.count()).select_from(LogbookEntryEvidence).where(LogbookEntryEvidence.ingestion_job_id == job_id)
    )
    assert evidence_count is not None
    assert evidence_count > 0
