from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateProposal,
    ADV4FeatureGate,
    ADV4ReviewCaseEvent,
    AirworthinessDirective,
)
from app.services.ad_v4_candidates import (
    CANONICALIZATION_VERSION_V2,
    DOMAINS_V2,
    VALIDATOR_VERSION_V2,
)
from conftest import add_membership, create_organization, create_user, login


def _seed_review_source(db):
    admin = create_user(db, "v4.review.admin@paprnav.local", "V4 Review Admin")
    platform = create_organization(db, "Paprnav V4 Review", "platform")
    membership = add_membership(db, platform, admin, "platform_admin")
    directive = AirworthinessDirective(
        ad_number="2026-09-13",
        title="V4 rejection-only review fixture",
        source_content_hash="a" * 64,
        status="candidate",
        extraction_status="not_started",
        review_status="not_started",
    )
    db.add(directive)
    db.flush()

    proposal_bytes = b"{}"
    proposal = ADV4CandidateProposal(
        directive_id=directive.id,
        schema_version="ad_extraction_v4",
        canonicalization_version=CANONICALIZATION_VERSION_V2,
        validator_version=VALIDATOR_VERSION_V2,
        canonical_bytes=proposal_bytes,
        parsed_json={"evidenceBindings": {}},
        canonical_hash=hashlib.sha256(
            DOMAINS_V2["proposal"] + proposal_bytes
        ).hexdigest(),
        evidence_binding_bytes=b"{}",
        evidence_binding_hash="b" * 64,
        binding_count=0,
        gate="candidate_only",
    )
    db.add(proposal)
    db.add_all([
        ADV4FeatureGate(gate_key=key, enabled=enabled, changed_by="review-test")
        for key, enabled in (
            ("validator2_write_enabled", False),
            ("materializer3a_enabled", False),
            ("materializer3b_enabled", False),
            ("reviewer4_draft_enabled", True),
            ("reviewer4_decision_enabled", True),
        )
    ])
    db.commit()
    return admin, membership, directive, proposal


def _enable_app(monkeypatch) -> None:
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_READS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", "true")
    monkeypatch.setenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", "true")
    get_settings.cache_clear()


def _headers(membership_id: str, key: str | None = None) -> dict[str, str]:
    headers = {"Paprnav-Acting-Membership-Id": membership_id}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def test_rejection_only_review_lifecycle_is_immutable_and_idempotent(
    client: TestClient, db_session, monkeypatch,
) -> None:
    _enable_app(monkeypatch)
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)

    observed = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert observed.status_code == 200, observed.text
    snapshot = observed.json()
    assert snapshot["inputIdentity"]["proposal"]["state"] == "integrity_error"
    assert snapshot["inputIdentity"]["applicabilityProjection"]["state"] == "missing"
    observed_again = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert observed_again.status_code == 200
    assert observed_again.json()["inputIdentityHash"] == snapshot["inputIdentityHash"]
    assert observed_again.json()["observationHash"] != snapshot["observationHash"]

    create_body = {
        "expectedAuthorizationObservationHash": snapshot[
            "authorizationObservationHashes"
        ]["create_ad_v4_review_case"],
        "expectedInputIdentityHash": snapshot["inputIdentityHash"],
    }
    created = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-cases",
        json=create_body,
        headers=_headers(membership.id, "case-create"),
    )
    assert created.status_code == 201, created.text
    case = created.json()
    assert case["state"] == "draft"
    assert case["idempotentRetry"] is False

    retried = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-cases",
        json=create_body,
        headers=_headers(membership.id, "case-create"),
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["caseId"] == case["caseId"]
    assert retried.json()["idempotentRetry"] is True

    draft = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/drafts",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["save_ad_v4_review_draft"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "annotations": [{"pointer": "/requirements", "text": "Needs remediation"}],
            "intendedAction": "reject",
        },
        headers=_headers(membership.id, "draft-one"),
    )
    assert draft.status_code == 201, draft.text
    case = draft.json()
    assert len(case["drafts"]) == 1

    requested = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/review-request",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["request_ad_v4_review"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "draftRevisionId": case["draftRevisionId"],
        },
        headers=_headers(membership.id, "request-one"),
    )
    assert requested.status_code == 201, requested.text
    case = requested.json()
    assert case["state"] == "pending_review"
    assert case["reviewRequest"]["authorshipSourceCount"] == 0

    rejected = client.post(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}/rejection",
        json={
            "expectedAuthorizationObservationHash": case[
                "authorizationObservationHashes"
            ]["reject_ad_v4_review"],
            "expectedPredecessorEventHash": case["latestEventHash"],
            "expectedRequestId": case["reviewRequestId"],
            "expectedInputIdentityHash": case["inputIdentityHash"],
            "reasonCodes": ["remediation_requested", "candidate_integrity"],
            "explanation": "Candidate requires a schema-valid resubmission.",
        },
        headers=_headers(membership.id, "reject-one"),
    )
    assert rejected.status_code == 201, rejected.text
    final = rejected.json()
    assert final["state"] == "rejected"
    assert final["signoff"]["action"] == "reject"
    assert final["rejection"]["reasonCodes"] == [
        "candidate_integrity", "remediation_requested",
    ]
    assert [event["eventType"] for event in final["events"]] == [
        "case_created", "draft_saved", "review_requested", "review_rejected",
    ]
    assert db_session.get(AirworthinessDirective, directive.id).status == "candidate"

    detail = client.get(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}",
        headers=_headers(membership.id),
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["latestEventHash"] == final["latestEventHash"]

    terminal = db_session.query(ADV4ReviewCaseEvent).filter_by(
        case_id=case["caseId"], event_type="review_rejected"
    ).one()
    terminal.event_hash = "0" * 64
    db_session.commit()
    corrupted = client.get(
        f"/api/v1/ads/v4/review-cases/{case['caseId']}",
        headers=_headers(membership.id),
    )
    assert corrupted.status_code == 409
    assert corrupted.json()["detail"]["code"] == "review_integrity"


def test_review_routes_fail_closed_when_read_capability_is_disabled(
    client: TestClient, db_session,
) -> None:
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)
    response = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "capability_disabled"


def test_review_authorization_uses_fresh_membership_state(
    client: TestClient, db_session, monkeypatch,
) -> None:
    _enable_app(monkeypatch)
    admin, membership, directive, proposal = _seed_review_source(db_session)
    login(client, admin.email)
    membership.status = "inactive"
    db_session.commit()

    response = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals/"
        f"{proposal.id}/review-observation",
        headers=_headers(membership.id),
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"
