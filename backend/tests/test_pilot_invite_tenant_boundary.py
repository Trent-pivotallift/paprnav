from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.core import (
    AuthSession,
    OrganizationMembership,
    ProductEvent,
    User,
    UserFeedback,
    WorkflowStatusEvent,
)
from app.services.invitations import InvitationError, create_invitation, verify_invitation
from app.services.observability import record_product_event
from app.services.session_revocation import revoke_auth_sessions
from tests.conftest import (
    TEST_PASSWORD,
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)


PILOT_ORIGIN = "https://pilot.example.test"
INVITE_SECRET = "pilot-invitation-secret-that-is-at-least-32-bytes"
V4_SETTINGS = (
    "PAPRNAV_AD_V4_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED",
    "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_READS_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED",
)


@pytest.fixture()
def pilot_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", PILOT_ORIGIN)
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    for name in V4_SETTINGS:
        monkeypatch.setenv(name, "false")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url=PILOT_ORIGIN) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def make_platform_admin(db: Session, email: str = "pilot.admin@example.test") -> User:
    user = create_user(db, email, "Pilot Administrator")
    organization = create_organization(db, "Pilot Operations", "platform")
    add_membership(db, organization, user, "platform_admin")
    db.commit()
    return user


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("PAPRNAV_SESSION_COOKIE_SECURE", "false"),
        ("PAPRNAV_INVITE_SIGNING_SECRET", "short"),
        ("PAPRNAV_CORS_ORIGINS", "http://pilot.example.test"),
        ("PAPRNAV_CORS_ORIGINS", f"{PILOT_ORIGIN},https://second.example.test"),
    ),
)
def test_pilot_startup_rejects_missing_trust_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", PILOT_ORIGIN)
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    for setting in V4_SETTINGS:
        monkeypatch.setenv(setting, "false")
    monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        create_app()


def issue_invitation(client: TestClient, *, role: str = "owner_admin", organization_type: str = "owner") -> str:
    response = client.post(
        "/api/v1/auth/invitations",
        headers={"Origin": PILOT_ORIGIN},
        json={
            "email": "Invitee@Example.Test ",
            "name": "Invited Owner",
            "organizationName": "Invited Hangar",
            "organizationType": organization_type,
            "role": role,
            "expiresInHours": 24,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()["invitationCode"]


def test_pilot_invitation_acceptance_is_atomic_and_non_replayable(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    admin = make_platform_admin(db_session)
    login_response = pilot_client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    assert "Secure" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert "SameSite=lax" in login_response.headers["set-cookie"]

    code = issue_invitation(pilot_client)
    accepted = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": code, "password": "invited-password"},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.headers["cache-control"] == "no-store"
    assert accepted.json()["user"]["email"] == "invitee@example.test"
    assert accepted.json()["user"]["memberships"][0]["role"] == "owner_admin"

    user = db_session.scalar(select(User).where(User.email == "invitee@example.test"))
    membership = db_session.scalar(
        select(OrganizationMembership).where(OrganizationMembership.user_id == user.id)
    )
    assert membership.organization.type == "owner"
    assert db_session.scalar(
        select(ProductEvent).where(
            ProductEvent.event_type == "invite_accepted",
            ProductEvent.subject_id == user.id,
        )
    )
    assert db_session.scalar(select(AuthSession).where(AuthSession.user_id == user.id))

    replay = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": code, "password": "invited-password"},
    )
    invalid = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": "invalid", "password": "invited-password"},
    )
    assert (replay.status_code, replay.json()) == (invalid.status_code, invalid.json())


@pytest.mark.parametrize(
    ("organization_type", "role"),
    (("owner", "maintenance_admin"), ("maintenance_shop", "owner_admin")),
)
def test_invitation_generation_rejects_cross_domain_roles(
    pilot_client: TestClient,
    db_session: Session,
    organization_type: str,
    role: str,
) -> None:
    admin = make_platform_admin(db_session)
    assert pilot_client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": TEST_PASSWORD},
    ).status_code == 200
    response = pilot_client.post(
        "/api/v1/auth/invitations",
        headers={"Origin": PILOT_ORIGIN},
        json={
            "email": "invitee@example.test",
            "name": "Invitee",
            "organizationName": "Invited Organization",
            "organizationType": organization_type,
            "role": role,
        },
    )
    assert response.status_code == 422


def test_invitation_verification_rejects_expired_future_and_tampered_codes() -> None:
    now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    expired, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now - timedelta(days=2),
        ttl=timedelta(hours=1),
    )
    future, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now + timedelta(minutes=6),
        ttl=timedelta(hours=1),
    )
    valid, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now,
        ttl=timedelta(hours=1),
    )
    payload, encoded_signature = valid.split(".", maxsplit=1)
    signature = bytearray(base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4)))
    signature[0] ^= 0x01
    tampered_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    tampered = f"{payload}.{tampered_signature}"
    assert tampered != valid

    for code in (expired, future, tampered):
        with pytest.raises(InvitationError):
            verify_invitation(code, secret=INVITE_SECRET, now=now)


def test_pilot_registration_and_cookie_authenticated_cross_origin_mutations_fail_closed(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, "pilot.user@example.test", "Pilot User")
    db_session.commit()
    assert pilot_client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.test", "name": "New", "password": "new-password"},
    ).status_code == 404
    assert pilot_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    ).status_code == 200

    payload = {"name": "Updated Pilot"}
    assert pilot_client.patch("/api/v1/auth/profile", json=payload).status_code == 403
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Origin": "https://evil.example"},
        json=payload,
    ).status_code == 403
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Origin": PILOT_ORIGIN},
        json=payload,
    ).status_code == 200
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Referer": f"{PILOT_ORIGIN}/profile"},
        json=payload,
    ).status_code == 200


def test_session_revocation_invalidates_existing_cookie(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, "revoke.me@example.test", "Revoke Me")
    db_session.commit()
    with TestClient(pilot_client.app, base_url=PILOT_ORIGIN) as user_client:
        assert user_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": TEST_PASSWORD},
        ).status_code == 200
        assert user_client.get("/api/v1/auth/me").status_code == 200
        assert revoke_auth_sessions(db_session, user_id=user.id) == 1
        db_session.commit()
        assert user_client.get("/api/v1/auth/me").status_code == 401
        assert db_session.scalar(
            select(ProductEvent).where(
                ProductEvent.event_type == "operator_sessions_revoked",
                ProductEvent.subject_id == user.id,
            )
        )


def test_observability_is_tenant_scoped_and_feedback_updates_are_admin_only(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(db_session, "scope.owner@example.test", "Scope Owner")
    stranger = create_user(db_session, "scope.stranger@example.test", "Scope Stranger")
    admin = create_user(db_session, "scope.admin@example.test", "Scope Admin")
    owner_org = create_organization(db_session, "Scope Hangar", "owner")
    stranger_org = create_organization(db_session, "Other Hangar", "owner")
    platform_org = create_organization(db_session, "Pilot Operations", "platform")
    owner_membership = add_membership(db_session, owner_org, owner, "owner_admin")
    add_membership(db_session, stranger_org, stranger, "owner_admin")
    add_membership(db_session, platform_org, admin, "platform_admin")
    aircraft = create_aircraft(db_session, owner_org, owner, "N321ZZ")
    other_aircraft = create_aircraft(db_session, stranger_org, stranger, "N654YY")
    record_product_event(
        db_session,
        event_type="visible_aircraft_event",
        subject_type="aircraft",
        subject_id=aircraft.id,
        actor=owner,
        aircraft_id=aircraft.id,
        organization_id=owner_org.id,
    )
    record_product_event(
        db_session,
        event_type="other_aircraft_event",
        subject_type="aircraft",
        subject_id=other_aircraft.id,
        actor=stranger,
        aircraft_id=other_aircraft.id,
        organization_id=stranger_org.id,
    )
    record_product_event(
        db_session,
        event_type="personal_event",
        subject_type="profile",
        subject_id=owner.id,
        actor=owner,
    )
    record_product_event(
        db_session,
        event_type="org_only_event",
        subject_type="organization",
        subject_id=owner_org.id,
        actor=owner,
        organization_id=owner_org.id,
    )
    db_session.add_all(
        [
            WorkflowStatusEvent(
                workflow_type="ad_matching",
                workflow_id=aircraft.id,
                new_status="complete",
                actor_type="worker",
            ),
            WorkflowStatusEvent(
                workflow_type="ad_ingestion",
                workflow_id="global",
                new_status="complete",
                actor_type="worker",
            ),
            UserFeedback(
                submitted_by_user_id=owner.id,
                organization_id=owner_org.id,
                aircraft_id=aircraft.id,
                subject_type="aircraft",
                subject_id=aircraft.id,
                feedback_type="demo_note",
                message="Visible feedback",
                severity="medium",
                status="open",
            ),
            UserFeedback(
                submitted_by_user_id=stranger.id,
                organization_id=stranger_org.id,
                aircraft_id=other_aircraft.id,
                subject_type="aircraft",
                subject_id=other_aircraft.id,
                feedback_type="demo_note",
                message="Other feedback",
                severity="medium",
                status="open",
            ),
        ]
    )
    db_session.commit()

    login(client, owner.email)
    response = client.get("/api/v1/observability")
    assert response.status_code == 200
    payload = response.json()
    event_types = {event["eventType"] for event in payload["events"]}
    assert {"visible_aircraft_event", "personal_event", "auth_login"} <= event_types
    assert {"other_aircraft_event", "org_only_event"}.isdisjoint(event_types)
    assert [event["workflowType"] for event in payload["workflowEvents"]] == ["ad_matching"]
    assert [item["message"] for item in payload["feedback"]] == ["Visible feedback"]
    feedback_id = payload["feedback"][0]["id"]
    assert client.get(
        "/api/v1/observability",
        params={"user_id": stranger.id},
    ).status_code == 403
    assert client.patch(
        f"/api/v1/observability/feedback/{feedback_id}",
        json={"status": "triaged"},
    ).status_code == 403

    owner_membership.status = "revoked"
    db_session.commit()
    revoked_payload = client.get("/api/v1/observability").json()
    revoked_event_types = {event["eventType"] for event in revoked_payload["events"]}
    assert {"personal_event", "auth_login"} <= revoked_event_types
    assert "visible_aircraft_event" not in revoked_event_types
    assert revoked_payload["workflowEvents"] == []
    assert revoked_payload["feedback"] == []

    client.post("/api/v1/auth/logout")
    login(client, admin.email)
    admin_payload = client.get("/api/v1/observability/admin").json()
    assert {event["eventType"] for event in admin_payload["events"]} >= {
        "visible_aircraft_event",
        "other_aircraft_event",
    }
    assert client.patch(
        f"/api/v1/observability/feedback/{feedback_id}",
        json={"status": "triaged"},
    ).status_code == 200
