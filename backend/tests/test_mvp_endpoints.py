from io import BytesIO

from fastapi.testclient import TestClient

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
    assert upload["originalFilename"] == "logbook.pdf"
    assert upload["contentType"] == "application/pdf"
    assert upload["fileSizeBytes"] == len(original_bytes)
    assert upload["status"] == "stored"
    assert upload["downloadUrl"] == f"/api/v1/uploads/{upload['id']}/download"

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
