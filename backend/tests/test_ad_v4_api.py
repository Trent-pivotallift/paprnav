from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError

from app.api.routes import ads as ads_routes
from app.api.routes.ads import _candidate_database_error
from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateProposal,
    ADV4CandidateSubmission,
    AirworthinessDirective,
)
from app.services.ad_evidence import _hash_parts
from conftest import TEST_PASSWORD, add_membership, create_organization, create_user, login


@pytest.mark.parametrize(
    ("sqlstate", "code"),
    (
        ("P0001", "candidate_integrity"),
        ("23514", "candidate_integrity"),
        ("40P01", "transaction_conflict"),
        ("40001", "transaction_conflict"),
        ("57014", "transaction_conflict"),
        ("55P03", "transaction_conflict"),
    ),
)
def test_candidate_database_failures_have_controlled_api_mapping(
    sqlstate: str, code: str,
) -> None:
    translated = _candidate_database_error(SimpleNamespace(
        orig=SimpleNamespace(sqlstate=sqlstate),
    ))
    assert translated is not None
    assert translated.code == code
    assert translated.http_status == 409
    assert _candidate_database_error(SimpleNamespace(
        orig=SimpleNamespace(sqlstate="XX000"),
    )) is None


def _seed_candidate_source(db):
    admin = create_user(db, "v4.api.admin@paprnav.local", "V4 API Admin")
    platform = create_organization(db, "Paprnav V4", "platform")
    membership = add_membership(db, platform, admin, "platform_admin")
    directive = AirworthinessDirective(
        ad_number="2024-14-03",
        title="V4 API fixture",
        source_content_hash="a" * 64,
        status="candidate",
        extraction_status="not_started",
        review_status="not_started",
    )
    db.add(directive)
    db.flush()
    fragment = ADEvidenceFragment(
        directive_id=directive.id,
        source_document_id="asd_v4_api",
        source_content_hash="b" * 64,
        rendition_id="asr_v4_api",
        page_text_version_id="ast_v4_api",
        page_start=1,
        page_end=1,
        character_start=0,
        character_end=13,
        exact_text="Official text",
        fragment_hash="c" * 64,
        parser_name="fixture",
        parser_version="1",
        created_by_user_id=admin.id,
    )
    db.add(fragment)
    db.flush()
    reason = "fixture admission"
    event = ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id,
        event_type="admitted",
        actor_user_id=admin.id,
        reason=reason,
        sequence_number=0,
        predecessor_event_hash=None,
        event_hash=_hash_parts(
            fragment.id,
            fragment.fragment_hash,
            "admitted",
            admin.id,
            reason,
            0,
            None,
        ),
    )
    db.add(event)
    db.commit()
    return admin, membership, directive, fragment


def _envelope(directive, fragment):
    evidence_key = "ev-official"
    return {
        "proposal": {
            "schemaVersion": "ad_extraction_v4",
            "decisionKey": "decision-v4-api",
            "directiveIdentity": {
                "directiveId": directive.id,
                "adNumber": {
                    "state": "known",
                    "value": directive.ad_number,
                    "evidenceKeys": [evidence_key],
                },
            },
            "officialDocuments": [{
                "officialDocumentKey": "official-rule",
                "documentRole": "ad_rule",
                "sourceDocumentId": fragment.source_document_id,
                "sourceContentHash": fragment.source_content_hash,
                "publicationDocumentNumber": "2024-15529",
                "evidenceKeys": [evidence_key],
            }],
            "evidenceBindings": {
                evidence_key: {
                    "fragmentId": fragment.id,
                    "fragmentHash": fragment.fragment_hash,
                },
            },
            "incorporatedDocuments": [],
            "productScopes": [{
                "scopeKey": "scope-main",
                "productRole": "airframe",
                "evidenceKeys": [evidence_key],
            }],
            "conditionDefinitions": [],
            "applicabilityRules": [{
                "ruleKey": "rule-main",
                "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"},
                "exclusionRuleKeys": [],
                "evidenceKeys": [evidence_key],
            }],
            "requirements": [{
                "requirementKey": "requirement-main",
                "sequence": "1",
                "activationExpression": {"nodeType": "rule_ref", "ruleKey": "rule-main"},
                "requirementType": "corrective_action",
                "action": {"actionType": "other_reviewed", "approvedDataDocumentRefKeys": [], "evidenceKeys": [evidence_key]},
                "prerequisiteRequirementKeys": [],
                "branch": {"kind": "required", "evidenceKeys": [evidence_key]},
                "initialTiming": {"state": "unknown", "reason": "not_yet_reviewed", "temporalScope": {"kind": "directive_version"}, "evidenceKeys": [evidence_key]},
                "recurrence": {"kind": "none", "evidenceKeys": [evidence_key]},
                "terminatingEffect": {"kind": "none", "evidenceKeys": [evidence_key]},
                "evidenceKeys": [evidence_key],
            }],
            "recurrenceGroups": [],
            "applicabilitySearchHints": [],
            "amocAuthorityProvisions": [],
            "supersessionRelations": [],
            "authoritativeCorrections": [],
        },
        "submissionContext": {"relationships": []},
    }


def _headers(membership_id: str, key: str = "v4-api-key") -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Idempotency-Key": key,
        "Paprnav-Acting-Membership-Id": membership_id,
    }


@pytest.mark.parametrize(
    ("sqlstate", "code"),
    (
        ("P0001", "candidate_integrity"),
        ("23514", "candidate_integrity"),
        ("40P01", "transaction_conflict"),
        ("40001", "transaction_conflict"),
        ("57014", "transaction_conflict"),
        ("55P03", "transaction_conflict"),
    ),
)
def test_candidate_post_translates_expected_database_failures(
    client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch,
    sqlstate: str, code: str,
) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    login(client, admin.email)

    class DriverFailure(Exception):
        pass

    driver_failure = DriverFailure("injected candidate database failure")
    driver_failure.sqlstate = sqlstate

    def fail_candidate_write(*args, **kwargs):
        raise DBAPIError("injected", {}, driver_failure)

    monkeypatch.setattr(ads_routes, "store_v4_candidate", fail_candidate_write)
    response = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        json=_envelope(directive, fragment),
        headers=_headers(membership.id, f"candidate-db-{sqlstate}"),
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == code


def test_admin_raw_post_retry_list_detail_and_v3_isolation(client: TestClient, db_session) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    login(client, admin.email)
    before = client.get("/api/v1/ads/directives", params={"includeUnreviewed": "true"})
    assert before.status_code == 200

    raw = json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode()
    created = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id),
    )
    assert created.status_code == 201
    assert created.json()["gate"] == "candidate_only"
    assert created.json()["contentReused"] is False

    retry = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id),
    )
    assert retry.status_code == 200
    assert retry.json()["idempotentRetry"] is True
    assert retry.json()["submissionId"] == created.json()["submissionId"]
    second_origin = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "v4-api-second-origin"),
    )
    assert second_origin.status_code == 200
    assert second_origin.json()["contentReused"] is True
    assert second_origin.json()["submissionId"] != created.json()["submissionId"]

    listing = client.get(f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["total"] == 1
    submissions = listing.json()["candidates"][0]["submissions"]
    assert len(submissions) == 2
    assert {item["actorUserId"] for item in submissions} == {admin.id}
    assert {item["authorizingMembershipId"] for item in submissions} == {membership.id}
    assert {item["authPolicyName"] for item in submissions} == {"paprnav-platform-admin-candidate-write"}
    assert all(item["requestHash"] and item["rawTransportHash"] for item in submissions)
    detail = client.get(f"/api/v1/ads/v4/candidate-proposals/{created.json()['proposalId']}")
    assert detail.status_code == 200
    assert detail.json()["canonicalHash"] == created.json()["canonicalHash"]

    first_origin = client.get(
        f"/api/v1/ads/v4/candidate-proposals/{created.json()['proposalId']}",
        params={"submissionLimit": 1, "submissionOffset": 0},
    )
    second_origin_page = client.get(
        f"/api/v1/ads/v4/candidate-proposals/{created.json()['proposalId']}",
        params={"submissionLimit": 1, "submissionOffset": 1},
    )
    assert first_origin.status_code == second_origin_page.status_code == 200
    assert first_origin.json()["submissionCount"] == 2
    assert first_origin.json()["submissionLimit"] == 1
    assert first_origin.json()["submissionOffset"] == 0
    assert second_origin_page.json()["submissionOffset"] == 1
    assert first_origin.json()["submissions"][0]["submissionId"] != second_origin_page.json()["submissions"][0]["submissionId"]

    second_content = _envelope(directive, fragment)
    second_content["proposal"]["decisionKey"] = "decision-v4-api-second"
    another = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=json.dumps(second_content, separators=(",", ":")).encode(),
        headers=_headers(membership.id, "v4-api-second-content"),
    )
    assert another.status_code == 201
    first_candidate_page = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        params={"limit": 1, "offset": 0},
    )
    second_candidate_page = client.get(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        params={"limit": 1, "offset": 1},
    )
    assert first_candidate_page.json()["count"] == second_candidate_page.json()["count"] == 1
    assert first_candidate_page.json()["total"] == second_candidate_page.json()["total"] == 2
    assert first_candidate_page.json()["candidates"][0]["proposalId"] != second_candidate_page.json()["candidates"][0]["proposalId"]

    after = client.get("/api/v1/ads/directives", params={"includeUnreviewed": "true"})
    assert after.status_code == 200
    assert after.json() == before.json()
    assert db_session.query(ADV4CandidateProposal).count() == 2
    db_session.refresh(directive)
    assert directive.status == "candidate"
    assert directive.extraction_status == "not_started"
    assert directive.review_status == "not_started"


def test_raw_parser_boundary_and_transport_headers_fail_closed(client: TestClient, db_session) -> None:
    admin, membership, directive, _ = _seed_candidate_source(db_session)
    login(client, admin.email)
    duplicate = b'{"proposal":{},"proposal":{},"submissionContext":{"relationships":[]}}'
    rejected = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=duplicate,
        headers=_headers(membership.id, "duplicate"),
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "duplicate_key"

    wrong_media = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=b"{}",
        headers={**_headers(membership.id, "media"), "Content-Type": "text/plain"},
    )
    assert wrong_media.status_code == 415
    encoded = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=b"{}",
        headers={**_headers(membership.id, "encoding"), "Content-Encoding": "gzip"},
    )
    assert encoded.status_code == 415
    oversized = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=b"{" + (b" " * 2_000_001) + b"}",
        headers={**_headers(membership.id, "stream-limit"), "Content-Length": "1"},
    )
    assert oversized.status_code == 413

    deeply_nested = b'{"x":' + (b'[' * 10_000) + b'"leaf"' + (b']' * 10_000) + b'}'
    deep_rejected = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=deeply_nested,
        headers=_headers(membership.id, "deep-json"),
    )
    assert deep_rejected.status_code == 413
    assert deep_rejected.json()["detail"]["code"] == "resource_limit"


def test_non_platform_memberships_cannot_write_or_audit(client: TestClient, db_session) -> None:
    _, _, directive, fragment = _seed_candidate_source(db_session)
    cases = (
        ("owner.v4@paprnav.local", "owner", "owner_admin", "active"),
        ("shop.v4@paprnav.local", "maintenance_shop", "maintenance_admin", "active"),
        ("inactive.v4@paprnav.local", "platform", "platform_admin", "inactive"),
        ("revoked.v4@paprnav.local", "platform", "platform_admin", "inactive"),
    )
    raw = json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode()
    for index, (email, org_type, role, membership_status) in enumerate(cases):
        user = create_user(db_session, email, email)
        organization = create_organization(db_session, f"Org {index}", org_type)
        membership = add_membership(db_session, organization, user, role)
        membership.status = membership_status
        db_session.commit()
        login(client, email)
        denied = client.post(
            f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
            content=raw,
            headers=_headers(membership.id, f"denied-{index}"),
        )
        assert denied.status_code == 403
        assert client.get(f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals").status_code == 403
        assert client.get("/api/v1/ads/v4/candidate-proposals/missing").status_code == 403
        client.post("/api/v1/auth/logout")


def test_audit_read_fails_closed_on_self_consistent_but_wrong_policy(client: TestClient, db_session) -> None:
    admin, membership, directive, fragment = _seed_candidate_source(db_session)
    login(client, admin.email)
    raw = json.dumps(_envelope(directive, fragment), separators=(",", ":")).encode()
    created = client.post(
        f"/api/v1/ads/directives/{directive.id}/v4/candidate-proposals",
        content=raw,
        headers=_headers(membership.id, "audit-integrity"),
    )
    assert created.status_code == 201
    submission = db_session.get(ADV4CandidateSubmission, created.json()["submissionId"])
    submission.auth_policy_name = "attacker-selected-policy"
    db_session.commit()
    rejected = client.get(
        f"/api/v1/ads/v4/candidate-proposals/{created.json()['proposalId']}",
    )
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "candidate_integrity"
