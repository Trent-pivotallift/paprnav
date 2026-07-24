from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import IngestionJob, LogbookEntry, LogbookEntryEvidence, OCRCorrection, OCRRun, OCRTextSpan, Upload
from app.api.routes.ingestion import create_ordered_ocr_correction
from app.schemas.ingestion import OCRCorrectionRequest
from app.services.ocr_provider import OCRPageResult, OCRProviderResult, OCRSpanResult
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


def test_owner_can_onboard_aircraft_with_cost_tags(client: TestClient, demo_data: dict[str, object]) -> None:
    login(client, "owner.test@paprnav.local")

    create_response = client.post(
        "/api/v1/aircraft",
        json={
            "nNumber": "N987ZZ",
            "make": "Piper",
            "model": "PA-28-180",
            "serialNumber": "28-1234",
            "engineMake": "Lycoming",
            "engineModel": "O-360-A4A",
        },
    )

    assert create_response.status_code == 201
    aircraft = create_response.json()
    assert aircraft["nNumberNormalized"] == "N987ZZ"
    assert aircraft["customerAccountTag"].startswith("acct-org_")
    assert aircraft["aircraftCostTag"].startswith("aircraft-ac_")


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
        data={"section": "airframe", "pilotConsentAccepted": "true"},
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
    assert upload["pilotConsentAccepted"] is True
    assert upload["initialOcrBillableToTag"].startswith("acct-org_")
    assert upload["costAllocationTags"]["Project"] == "paprnav"
    assert upload["costAllocationTags"]["CustomerAccount"] == upload["initialOcrBillableToTag"]
    assert upload["costAllocationTags"]["Aircraft"].startswith("aircraft-ac_")
    assert ingestion_job["uploadId"] == upload["id"]
    assert ingestion_job["status"] == "queued"

    download_response = client.get(upload["downloadUrl"])
    assert download_response.status_code == 200
    assert download_response.content == original_bytes

    no_consent_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe"},
        files={"file": ("logbook.pdf", BytesIO(original_bytes), "application/pdf")},
    )
    assert no_consent_response.status_code == 400
    assert no_consent_response.json()["detail"] == "Pilot consent is required before upload processing"

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


def test_ingestion_page_image_download_for_image_upload(client: TestClient, db_session: Session, demo_data: dict[str, object]) -> None:
    aircraft_id = demo_data["aircraft"].id
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("logbook-page.png", BytesIO(png_bytes), "image/png")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]
    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job)

    detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert detail_response.status_code == 200
    page = detail_response.json()["pages"][0]
    assert page["imageDownloadUrl"] == f"/api/v1/ingestion-jobs/{job_id}/pages/{page['id']}/image"

    image_response = client.get(page["imageDownloadUrl"])
    assert image_response.status_code == 200
    assert image_response.headers["content-type"].startswith("image/png")
    assert image_response.content == png_bytes


def test_s3_upload_download_streams_from_configured_bucket(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    class FakeS3Body:
        def iter_chunks(self):
            yield b"%PDF-1.4 "
            yield b"s3 body"

    class FakeS3Client:
        def __init__(self) -> None:
            self.request = None

        def get_object(self, *, Bucket: str, Key: str) -> dict:
            self.request = {"Bucket": Bucket, "Key": Key}
            return {"Body": FakeS3Body()}

    aircraft = demo_data["aircraft"]
    owner_user = demo_data["owner_user"]
    upload = Upload(
        id="upl_s3_download_test",
        aircraft_id=aircraft.id,
        uploaded_by_user_id=owner_user.id,
        original_filename="s3-logbook.pdf",
        content_type="application/pdf",
        file_size_bytes=16,
        storage_backend="s3",
        storage_key="uploads/ac_1/upl_1/s3-logbook.pdf",
        sha256="abc123",
        status="stored",
        pilot_consent_accepted=True,
    )
    db_session.add(upload)
    db_session.commit()

    fake_client = FakeS3Client()
    monkeypatch.setenv("PAPRNAV_S3_UPLOAD_BUCKET", "paprnav-pilot-artifacts-527257972989")
    monkeypatch.setattr("app.api.routes.uploads.get_s3_client", lambda _region: fake_client)
    get_settings.cache_clear()

    login(client, "owner.test@paprnav.local")
    response = client.get(f"/api/v1/uploads/{upload.id}/download")

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 s3 body"
    assert fake_client.request == {
        "Bucket": "paprnav-pilot-artifacts-527257972989",
        "Key": "uploads/ac_1/upl_1/s3-logbook.pdf",
    }
    get_settings.cache_clear()


def test_ocr_ingestion_verification_correction_and_entry_extraction(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")

    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("multipage-logbook.pdf", BytesIO(b"%PDF-1.4 multipage fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]

    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job)

    ocr_run = db_session.scalar(select(OCRRun).where(OCRRun.ingestion_job_id == job_id))
    assert ocr_run is not None
    assert ocr_run.billing_status == "chargeable"
    assert ocr_run.billable_account_tag is not None
    assert ocr_run.billable_account_tag.startswith("acct-org_")
    assert ocr_run.billable_aircraft_tag is not None
    assert ocr_run.billable_aircraft_tag.startswith("aircraft-ac_")
    assert ocr_run.billable_page_count == 2

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

    original_performer_text = low_confidence_spans[0]["text"]
    correction_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/ocr-corrections",
        json={
            "ocrTextSpanId": low_confidence_spans[0]["id"],
            "correctedText": "Performer: Alice Mechanic A&P",
            "correctionReason": "low_confidence",
        },
    )
    assert correction_response.status_code == 201
    assert correction_response.json()["originalConfidence"] < 80
    assert correction_response.json()["correctionOrder"] == 1

    second_correction_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/ocr-corrections",
        json={
            "ocrTextSpanId": low_confidence_spans[0]["id"],
            "correctedText": "Performer: Amelia Mechanic A&P IA",
            "correctionReason": "low_confidence",
        },
    )
    assert second_correction_response.status_code == 201
    assert second_correction_response.json()["correctionOrder"] == 2

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

    first_entry = db_session.scalar(
        select(LogbookEntry).where(LogbookEntry.id == entries[0]["id"])
    )
    assert first_entry is not None
    assert first_entry.performer_name == "Amelia Mechanic"
    assert first_entry.performer_credential == "A&P IA"
    evidence_by_field = {evidence.field_name: evidence for evidence in first_entry.evidence_links}
    assert set(evidence_by_field) == {
        "entry_date",
        "description",
        "performer_name",
        "performer_credential",
        "tach_time",
        "hobbs_time",
        "total_time",
    }
    assert evidence_by_field["entry_date"].ocr_text_span_id == evidence_by_field["description"].ocr_text_span_id
    assert evidence_by_field["performer_name"].ocr_text_span_id == evidence_by_field["performer_credential"].ocr_text_span_id
    assert evidence_by_field["tach_time"].ocr_text_span_id == evidence_by_field["hobbs_time"].ocr_text_span_id
    assert evidence_by_field["tach_time"].ocr_text_span_id == evidence_by_field["total_time"].ocr_text_span_id
    performer_span = db_session.get(OCRTextSpan, evidence_by_field["performer_name"].ocr_text_span_id)
    assert performer_span is not None
    assert performer_span.text == original_performer_text
    assert evidence_by_field["performer_name"].evidence_type == "correction"
    latest_correction = db_session.get(OCRCorrection, evidence_by_field["performer_name"].ocr_correction_id)
    assert latest_correction is not None
    assert latest_correction.correction_order == 2
    assert latest_correction.corrected_text == "Performer: Amelia Mechanic A&P IA"


def test_ordered_ocr_correction_retries_once_after_order_collision(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    aircraft_id = demo_data["aircraft"].id
    owner_user = demo_data["owner_user"]
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("retry-logbook.pdf", BytesIO(b"%PDF-1.4 retry fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job = db_session.get(IngestionJob, upload_response.json()["ingestionJob"]["id"])
    assert job is not None
    process_ingestion_job(db_session, job)
    span = db_session.scalar(
        select(OCRTextSpan)
        .where(OCRTextSpan.ingestion_page_id == job.pages[0].id)
        .where(OCRTextSpan.confidence < 80)
    )
    assert span is not None

    original_flush = db_session.flush
    collision_count = 0

    def flaky_flush(*args, **kwargs):
        nonlocal collision_count
        if collision_count == 0:
            collision_count += 1
            raise IntegrityError("insert ocr_corrections", {}, Exception("simulated order collision"))
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db_session, "flush", flaky_flush)

    correction = create_ordered_ocr_correction(
        db_session,
        job=job,
        span=span,
        current_user=owner_user,
        payload=OCRCorrectionRequest(
            ocrTextSpanId=span.id,
            correctedText="Performer: Retry Mechanic A&P",
            correctionReason="low_confidence",
        ),
    )

    assert collision_count == 1
    assert correction.correction_order == 1
    assert correction.corrected_text == "Performer: Retry Mechanic A&P"


def test_ordered_ocr_correction_returns_409_after_repeated_order_collisions(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
    monkeypatch,
) -> None:
    aircraft_id = demo_data["aircraft"].id
    owner_user = demo_data["owner_user"]
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("conflict-logbook.pdf", BytesIO(b"%PDF-1.4 conflict fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job = db_session.get(IngestionJob, upload_response.json()["ingestionJob"]["id"])
    assert job is not None
    process_ingestion_job(db_session, job)
    span = db_session.scalar(
        select(OCRTextSpan)
        .where(OCRTextSpan.ingestion_page_id == job.pages[0].id)
        .where(OCRTextSpan.confidence < 80)
    )
    assert span is not None

    def always_collide(*_args, **_kwargs):
        raise IntegrityError("insert ocr_corrections", {}, Exception("simulated order collision"))

    monkeypatch.setattr(db_session, "flush", always_collide)

    with pytest.raises(HTTPException) as exc_info:
        create_ordered_ocr_correction(
            db_session,
            job=job,
            span=span,
            current_user=owner_user,
            payload=OCRCorrectionRequest(
                ocrTextSpanId=span.id,
                correctedText="Performer: Conflict Mechanic A&P",
                correctionReason="low_confidence",
            ),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Unable to assign OCR correction order; retry the correction"


def test_ocr_extraction_orders_entries_by_date_then_page(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    class OutOfOrderDateProvider:
        provider_name = "out_of_order_fixture"
        provider_version = "0.1.0"
        configuration_hash = "date-order-fixture"

        def process_upload(self, **_kwargs):
            return OCRProviderResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                configuration_hash=self.configuration_hash,
                pages=[
                    OCRPageResult(
                        source_page_number=1,
                        page_label="Page 1",
                        width_px=100,
                        height_px=100,
                        rotation_degrees=0,
                        extraction_confidence=90,
                        spans=[
                            OCRSpanResult(
                                provider_block_id="p1-line",
                                span_type="LINE",
                                text="2026-04-10 Later maintenance accomplished.",
                                confidence=95,
                                bbox_left=0,
                                bbox_top=0,
                                bbox_width=1,
                                bbox_height=0.1,
                                bbox_units="ratio",
                                reading_order=1,
                            )
                        ],
                    ),
                    OCRPageResult(
                        source_page_number=2,
                        page_label="Page 2",
                        width_px=100,
                        height_px=100,
                        rotation_degrees=0,
                        extraction_confidence=90,
                        spans=[
                            OCRSpanResult(
                                provider_block_id="p2-line",
                                span_type="LINE",
                                text="2026-03-01 Earlier maintenance accomplished.",
                                confidence=95,
                                bbox_left=0,
                                bbox_top=0,
                                bbox_width=1,
                                bbox_height=0.1,
                                bbox_units="ratio",
                                reading_order=1,
                            )
                        ],
                    ),
                    OCRPageResult(
                        source_page_number=3,
                        page_label="Page 3",
                        width_px=100,
                        height_px=100,
                        rotation_degrees=0,
                        extraction_confidence=90,
                        spans=[
                            OCRSpanResult(
                                provider_block_id="p3-line",
                                span_type="LINE",
                                text="2026-04-10 Same date later page.",
                                confidence=95,
                                bbox_left=0,
                                bbox_top=0,
                                bbox_width=1,
                                bbox_height=0.1,
                                bbox_units="ratio",
                                reading_order=1,
                            )
                        ],
                    ),
                ],
            )

    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("out-of-order.pdf", BytesIO(b"%PDF-1.4 date order fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]

    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job, provider=OutOfOrderDateProvider())

    detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert detail_response.status_code == 200
    pages = detail_response.json()["pages"]
    verify_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/page-verification",
        json={
            "pages": [{"pageId": page["id"], "currentPageOrder": page["currentPageOrder"]} for page in pages],
            "isOrderConfirmed": True,
            "isComplete": True,
        },
    )
    assert verify_response.status_code == 200

    extract_response = client.post(f"/api/v1/ingestion-jobs/{job_id}/extract-logbook-entries")
    assert extract_response.status_code == 200
    extracted = extract_response.json()["entries"]
    assert [entry["entryDate"] for entry in extracted] == ["2026-03-01", "2026-04-10", "2026-04-10"]
    assert [entry["description"] for entry in extracted] == [
        "Earlier maintenance accomplished.",
        "Later maintenance accomplished.",
        "Same date later page.",
    ]

    list_response = client.get(f"/api/v1/aircraft/{aircraft_id}/logbook-entries?section=airframe")
    assert list_response.status_code == 200
    listed = [entry for entry in list_response.json()["entries"] if entry["sourceType"] == "ocr_ingestion"]
    assert [entry["description"] for entry in listed[-3:]] == [
        "Earlier maintenance accomplished.",
        "Later maintenance accomplished.",
        "Same date later page.",
    ]


def test_ocr_extraction_marks_missing_date_as_fallback_evidence(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    class MissingDateProvider:
        provider_name = "missing_date_fixture"
        provider_version = "0.1.0"
        configuration_hash = "missing-date-fixture"

        def process_upload(self, **_kwargs):
            return OCRProviderResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                configuration_hash=self.configuration_hash,
                pages=[
                    OCRPageResult(
                        source_page_number=1,
                        page_label="Page 1",
                        width_px=100,
                        height_px=100,
                        rotation_degrees=0,
                        extraction_confidence=92,
                        spans=[
                            OCRSpanResult(
                                provider_block_id="missing-date-line",
                                span_type="LINE",
                                text="Annual inspection completed with no readable date.",
                                confidence=96,
                                bbox_left=0,
                                bbox_top=0,
                                bbox_width=1,
                                bbox_height=0.1,
                                bbox_units="ratio",
                                reading_order=1,
                            )
                        ],
                    )
                ],
            )

    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("missing-date.pdf", BytesIO(b"%PDF-1.4 missing date fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]

    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job, provider=MissingDateProvider())

    detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert detail_response.status_code == 200
    pages = detail_response.json()["pages"]
    verify_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/page-verification",
        json={
            "pages": [{"pageId": page["id"], "currentPageOrder": page["currentPageOrder"]} for page in pages],
            "isOrderConfirmed": True,
            "isComplete": True,
        },
    )
    assert verify_response.status_code == 200

    extract_response = client.post(f"/api/v1/ingestion-jobs/{job_id}/extract-logbook-entries")
    assert extract_response.status_code == 200
    extracted = extract_response.json()["entries"]
    assert len(extracted) == 1
    assert extracted[0]["entryDate"] is None
    assert extracted[0]["reviewStatus"] == "needs_review"

    entry = db_session.scalar(select(LogbookEntry).where(LogbookEntry.id == extracted[0]["id"]))
    assert entry is not None
    assert entry.entry_date is None
    evidence_by_field = {evidence.field_name: evidence for evidence in entry.evidence_links}
    assert evidence_by_field["entry_date"].evidence_type == "fallback"
    assert evidence_by_field["entry_date"].ocr_text_span_id == evidence_by_field["description"].ocr_text_span_id


def test_ocr_extraction_splits_multiple_logbook_entries_on_one_analysis_page(
    client: TestClient,
    db_session: Session,
    demo_data: dict[str, object],
) -> None:
    def line(block_id: str, text: str, top: float, left: float = 0.52, confidence: float = 92.0) -> OCRSpanResult:
        return OCRSpanResult(
            provider_block_id=block_id,
            span_type="LINE",
            text=text,
            confidence=confidence,
            bbox_left=left,
            bbox_top=top,
            bbox_width=0.42,
            bbox_height=0.03,
            bbox_units="ratio",
            reading_order=int(top * 1000),
        )

    def structure(block_id: str, span_type: str, top: float, left: float = 0.50) -> OCRSpanResult:
        return OCRSpanResult(
            provider_block_id=block_id,
            span_type=span_type,
            text=f"[{span_type.lower()}]",
            confidence=90,
            bbox_left=left,
            bbox_top=top,
            bbox_width=0.45,
            bbox_height=0.1,
            bbox_units="ratio",
            reading_order=int(top * 1000),
        )

    class TwoEntryAnalysisProvider:
        provider_name = "aws_textract"
        provider_version = "start_document_analysis_v1"
        configuration_hash = "analysis-two-entry-fixture"

        def process_upload(self, **_kwargs):
            return OCRProviderResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                configuration_hash=self.configuration_hash,
                pages=[
                    OCRPageResult(
                        source_page_number=1,
                        page_label="Analysis page 1",
                        width_px=100,
                        height_px=100,
                        rotation_degrees=0,
                        extraction_confidence=90,
                        spans=[
                            structure("table", "TABLE", 0.05),
                            structure("sig-1", "SIGNATURE", 0.42),
                            structure("sig-2", "SIGNATURE", 0.77),
                            line("header", "Description of Inspections, Tests, Repairs and Alterations", 0.06),
                            line("rs-shop", "RS Aircraft Service", 0.20, left=0.18),
                            line("rs-date", "12-17-12 Tach = 1276.8 Total Time = 5405.5 N3671L", 0.27, left=0.08),
                            line("rs-desc", "Performed an annual inspection using FAR 43 Appendix D checklist as a guide.", 0.31, left=0.05),
                            line("rs-elt", "Battery serviced. ELT battery replaced dated Dec. 2014.", 0.35, left=0.05),
                            line("rs-performer", "Ronald Stegemoller A&P 2192007 I.A.", 0.44, left=0.10),
                            line("jones-shop", "Jones Avionics FAA CRS# YJ3R478Y", 0.20, left=0.70),
                            line("jones-date", "Date: 4/13/13", 0.29, left=0.72),
                            line("jones-desc", "Altimeter, Transponder, Automatic Altitude reporting system", 0.40, left=0.68),
                            line("jones-cert", "Tested and inspected and meets the requirements of FAA 14 CFR 91.411, 91.413", 0.48, left=0.68),
                            line("jones-performer", "Inspector M. Jones W.O. Reference #12305", 0.62, left=0.70),
                        ],
                    )
                ],
            )

    aircraft_id = demo_data["aircraft"].id
    login(client, "owner.test@paprnav.local")
    upload_response = client.post(
        f"/api/v1/aircraft/{aircraft_id}/uploads",
        data={"section": "airframe", "pilotConsentAccepted": "true"},
        files={"file": ("two-entry.pdf", BytesIO(b"%PDF-1.4 two entry fixture"), "application/pdf")},
    )
    assert upload_response.status_code == 201
    job_id = upload_response.json()["ingestionJob"]["id"]

    job = db_session.get(IngestionJob, job_id)
    assert job is not None
    process_ingestion_job(db_session, job, provider=TwoEntryAnalysisProvider())

    detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert detail_response.status_code == 200
    pages = detail_response.json()["pages"]
    verify_response = client.post(
        f"/api/v1/ingestion-jobs/{job_id}/page-verification",
        json={
            "pages": [{"pageId": page["id"], "currentPageOrder": page["currentPageOrder"]} for page in pages],
            "isOrderConfirmed": True,
            "isComplete": True,
        },
    )
    assert verify_response.status_code == 200

    extract_response = client.post(f"/api/v1/ingestion-jobs/{job_id}/extract-logbook-entries")
    assert extract_response.status_code == 200
    extracted = extract_response.json()["entries"]
    assert len(extracted) == 2
    assert [entry["entryDate"] for entry in extracted] == ["2012-12-17", "2013-04-13"]
    assert extracted[0]["reviewStatus"] == "needs_review"
    assert extracted[1]["reviewStatus"] == "needs_review"
    assert "RS Aircraft Service" in extracted[0]["description"]
    assert "annual inspection" in extracted[0]["description"]
    assert "Jones Avionics" in extracted[1]["description"]
    assert "Transponder" in extracted[1]["description"]

    post_extract_detail_response = client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert post_extract_detail_response.status_code == 200
    extracted_candidates = post_extract_detail_response.json()["extractedEntries"]
    assert len(extracted_candidates) == 2
    assert [entry["entryDate"] for entry in extracted_candidates] == ["2012-12-17", "2013-04-13"]
    assert extracted_candidates[0]["tachTime"] == 1276.8
    assert extracted_candidates[0]["totalTime"] == 5405.5
    assert extracted_candidates[0]["region"]["bboxUnits"] == "ratio"
    assert extracted_candidates[0]["region"]["bboxWidth"] > 0
    candidate_evidence = extracted_candidates[0]["evidence"]
    candidate_evidence_fields = {evidence["fieldName"] for evidence in candidate_evidence}
    assert {"entry_date", "description", "tach_time", "total_time"}.issubset(candidate_evidence_fields)
    date_evidence = next(evidence for evidence in candidate_evidence if evidence["fieldName"] == "entry_date")
    assert date_evidence["evidenceType"] == "ocr_span"
    assert date_evidence["span"]["spanType"] == "LINE"
    assert date_evidence["span"]["bboxLeft"] is not None

    entries = db_session.scalars(
        select(LogbookEntry)
        .join(LogbookEntryEvidence)
        .where(LogbookEntryEvidence.ingestion_job_id == job_id)
        .order_by(LogbookEntry.entry_date)
    ).unique().all()
    assert len(entries) == 2
    assert entries[0].tach_time == 1276.8
    assert entries[0].total_time == 5405.5
    first_evidence_fields = {evidence.field_name for evidence in entries[0].evidence_links}
    assert {"entry_date", "description", "tach_time", "total_time"}.issubset(first_evidence_fields)

    update_response = client.patch(
        f"/api/v1/aircraft/{aircraft_id}/logbook-entries/{entries[0].id}",
        json={
            "entryDate": "2012-12-17",
            "description": "RS Aircraft Service reviewed annual inspection text.",
            "tachTime": 1277.0,
            "totalTime": None,
            "reviewStatus": "needs_review",
        },
    )
    assert update_response.status_code == 200
    db_session.expire_all()
    override_evidence = db_session.scalars(
        select(LogbookEntryEvidence).where(
            LogbookEntryEvidence.logbook_entry_id == entries[0].id,
            LogbookEntryEvidence.evidence_type == "human_override",
        )
    ).all()
    override_fields = {evidence.field_name for evidence in override_evidence}
    assert {"description", "tach_time", "total_time"}.issubset(override_fields)
    tach_override = next(evidence for evidence in override_evidence if evidence.field_name == "tach_time")
    assert tach_override.review_metadata["previousValue"] == 1276.8
    assert tach_override.review_metadata["newValue"] == 1277.0
