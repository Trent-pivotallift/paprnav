from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.models.core import (
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADPublication,
    ADSourceDocument,
    ADSourcePageRendition,
    ADSourcePageTextVersion,
    ADV4CandidateProposal,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposalEvent,
    ADV4CandidateSubmission,
    ADV4CandidateSubmissionRelationship,
    AirworthinessDirective,
    Organization,
    OrganizationMembership,
    User,
)
from app.services.ad_evidence import _hash_parts
from app.services import ad_v4_candidates as v4_service
from app.services.ad_v4_candidates import ADV4Error, DOMAINS, canonical_bytes, parse_v4_request_bytes, store_v4_candidate


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def _seed(db: Session):
    token = uuid.uuid4().hex
    user = User(email=f"v4-{token}@example.test", name="V4 Admin", password_hash="x", status="active")
    organization = Organization(name=f"Paprnav {token}", type="platform")
    db.add_all([user, organization]); db.flush()
    membership = OrganizationMembership(organization_id=organization.id, user_id=user.id, role="platform_admin", status="active")
    directive = AirworthinessDirective(ad_number="2024-14-03", title="V4 fixture", source_content_hash="1" * 64, status="candidate", extraction_status="not_started", review_status="not_started")
    document = ADSourceDocument(source_system="federal_register", source_type="document_pdf", source_identifier=token, storage_backend="local", storage_key=f"fixture/{token}.pdf", media_type="application/pdf", content_hash=hashlib.sha256(token.encode()).hexdigest(), storage_bytes=1, captured_at=datetime.now(timezone.utc), status="retained")
    db.add_all([membership, directive, document]); db.flush()
    db.add(ADPublication(directive_id=directive.id, source_document_id=document.id, source_system="federal_register", source_type="document_pdf", source_identifier=token, content_hash=document.content_hash)); db.flush()
    rendition = ADSourcePageRendition(source_document_id=document.id, source_content_hash=document.content_hash, page_number=1, renderer_name="fixture", renderer_version="1", renderer_configuration_hash=hashlib.sha256(b"render").hexdigest(), media_type="image/png", width_px=1, height_px=1, storage_backend="local", storage_key=f"fixture/{token}.png", rendition_hash=hashlib.sha256(b"png").hexdigest(), storage_bytes=1)
    db.add(rendition); db.flush()
    page_text = "Official retained AD requirement text."
    text_version = ADSourcePageTextVersion(rendition_id=rendition.id, source_document_id=document.id, source_content_hash=document.content_hash, page_number=1, extractor_name="fixture", extractor_version="1", extractor_configuration_hash=hashlib.sha256(b"extract").hexdigest(), page_text=page_text, text_hash=hashlib.sha256(page_text.encode()).hexdigest(), text_classification="native")
    db.add(text_version); db.flush()
    fragment_hash = _hash_parts(directive.id, document.id, document.content_hash, rendition.id, text_version.id, 1, 1, 0, len(page_text), None, None, None, None, None, page_text, "fixture", "1")
    fragment = ADEvidenceFragment(directive_id=directive.id, source_document_id=document.id, source_content_hash=document.content_hash, rendition_id=rendition.id, page_text_version_id=text_version.id, page_start=1, page_end=1, character_start=0, character_end=len(page_text), exact_text=page_text, fragment_hash=fragment_hash, parser_name="fixture", parser_version="1", created_by_user_id=user.id)
    db.add(fragment); db.flush()
    event_hash = _hash_parts(fragment.id, fragment.fragment_hash, "admitted", user.id, "fixture admission", 0, None)
    event = ADEvidenceFragmentLifecycleEvent(fragment_id=fragment.id, event_type="admitted", actor_user_id=user.id, reason="fixture admission", sequence_number=0, predecessor_event_hash=None, event_hash=event_hash)
    db.add(event); db.commit()
    return user.id, membership.id, directive.id, document.id, document.content_hash, fragment.id, fragment.fragment_hash


def _request(
    directive_id,
    document_id,
    source_hash,
    fragment_id,
    fragment_hash,
    *,
    decision_key="decision-v4-test",
    relationships=None,
    extra_binding=None,
    reverse_bindings=False,
):
    ev = "ev-official"
    bindings = [(ev, {"fragmentId": fragment_id, "fragmentHash": fragment_hash})]
    document_evidence = [ev]
    if extra_binding is not None:
        bindings.append(("ev-secondary", {
            "fragmentId": extra_binding[0], "fragmentHash": extra_binding[1],
        }))
        document_evidence.append("ev-secondary")
    if reverse_bindings:
        bindings.reverse()
    proposal = {
        "schemaVersion": "ad_extraction_v4", "decisionKey": decision_key,
        "directiveIdentity": {"directiveId": directive_id, "adNumber": {"state": "known", "value": "2024-14-03", "evidenceKeys": [ev]}},
        "officialDocuments": [{"officialDocumentKey": "official-rule", "documentRole": "ad_rule", "sourceDocumentId": document_id, "sourceContentHash": source_hash, "publicationDocumentNumber": "2024-15529", "evidenceKeys": document_evidence}],
        "evidenceBindings": dict(bindings),
        "incorporatedDocuments": [], "productScopes": [{"scopeKey": "scope-main", "productRole": "airframe", "evidenceKeys": [ev]}],
        "conditionDefinitions": [], "applicabilityRules": [{"ruleKey": "rule-main", "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"}, "exclusionRuleKeys": [], "evidenceKeys": [ev]}],
        "requirements": [{"requirementKey": "requirement-main", "sequence": "1", "activationExpression": {"nodeType": "rule_ref", "ruleKey": "rule-main"}, "requirementType": "corrective_action", "action": {"actionType": "other_reviewed", "approvedDataDocumentRefKeys": [], "evidenceKeys": [ev]}, "prerequisiteRequirementKeys": [], "branch": {"kind": "required", "evidenceKeys": [ev]}, "initialTiming": {"state": "unknown", "reason": "not_yet_reviewed", "temporalScope": {"kind": "directive_version"}, "evidenceKeys": [ev]}, "recurrence": {"kind": "none", "evidenceKeys": [ev]}, "terminatingEffect": {"kind": "none", "evidenceKeys": [ev]}, "evidenceKeys": [ev]}],
        "recurrenceGroups": [], "applicabilitySearchHints": [], "amocAuthorityProvisions": [], "supersessionRelations": [], "authoritativeCorrections": [],
    }
    return parse_v4_request_bytes(json.dumps({
        "proposal": proposal,
        "submissionContext": {"relationships": relationships or []},
    }, separators=(",", ":")).encode())


def _second_fragment(db: Session, directive_id: str, document_id: str, source_hash: str, user_id: str):
    text_version = db.scalar(select(ADSourcePageTextVersion).where(ADSourcePageTextVersion.source_document_id == document_id))
    exact_text = text_version.page_text[:8]
    fragment_hash = _hash_parts(
        directive_id, document_id, source_hash, text_version.rendition_id, text_version.id,
        1, 1, 0, len(exact_text), None, None, None, None, None, exact_text, "fixture", "1",
    )
    fragment = ADEvidenceFragment(
        directive_id=directive_id, source_document_id=document_id, source_content_hash=source_hash,
        rendition_id=text_version.rendition_id, page_text_version_id=text_version.id,
        page_start=1, page_end=1, character_start=0, character_end=len(exact_text),
        exact_text=exact_text, fragment_hash=fragment_hash, parser_name="fixture", parser_version="1",
        created_by_user_id=user_id,
    )
    db.add(fragment); db.flush()
    reason = "secondary fixture admission"
    event_hash = _hash_parts(fragment.id, fragment.fragment_hash, "admitted", user_id, reason, 0, None)
    db.add(ADEvidenceFragmentLifecycleEvent(
        fragment_id=fragment.id, event_type="admitted", actor_user_id=user_id, reason=reason,
        sequence_number=0, predecessor_event_hash=None, event_hash=event_hash,
    ))
    db.commit()
    return fragment.id, fragment.fragment_hash


def _alembic(revision: str) -> subprocess.CompletedProcess[str]:
    assert POSTGRES_URL
    environment = os.environ.copy()
    environment["DATABASE_URL"] = POSTGRES_URL
    return subprocess.run(
        [sys.executable, "-m", "alembic", revision.split()[0], revision.split()[1]],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        text=True,
        capture_output=True,
        timeout=25,
        check=False,
    )


def test_00_empty_v4_migration_downgrade_upgrade_round_trip():
    downgrade = _alembic("downgrade 20260830_0025")
    assert downgrade.returncode == 0, downgrade.stdout + downgrade.stderr
    upgrade = _alembic("upgrade 20260901_0026")
    assert upgrade.returncode == 0, upgrade.stdout + upgrade.stderr


def test_postgres_candidate_integrity_concurrency_and_immutability():
    assert POSTGRES_URL
    engine = create_engine(
        POSTGRES_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={
            "connect_timeout": 5,
            "options": (
                "-c statement_timeout=10000 "
                "-c lock_timeout=5000 "
                "-c idle_in_transaction_session_timeout=15000"
            ),
        },
    )
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        user_id, membership_id, directive_id, document_id, source_hash, fragment_id, fragment_hash = _seed(db)
        secondary_fragment = _second_fragment(db, directive_id, document_id, source_hash, user_id)
    parsed = _request(directive_id, document_id, source_hash, fragment_id, fragment_hash)

    def write():
        with SessionLocal() as db:
            actor = db.get(User, user_id)
            stored = store_v4_candidate(db, directive_id=directive_id, parsed=parsed, actor=actor, membership_id=membership_id, idempotency_key="concurrent-key")
            db.commit()
            return stored.proposal.id, stored.submission.id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(write) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0] == results[1]

    different_a = _request(
        directive_id, document_id, source_hash, fragment_id, fragment_hash,
        decision_key="different-payload-a",
    )
    different_b = _request(
        directive_id, document_id, source_hash, fragment_id, fragment_hash,
        decision_key="different-payload-b",
    )

    def conflicting_write(value):
        with SessionLocal() as conflict_db:
            conflict_actor = conflict_db.get(User, user_id)
            try:
                stored = store_v4_candidate(
                    conflict_db, directive_id=directive_id, parsed=value, actor=conflict_actor,
                    membership_id=membership_id, idempotency_key="same-key-different-payload",
                )
                conflict_db.commit()
                return ("ok", stored.proposal.id)
            except ADV4Error as exc:
                conflict_db.rollback()
                return (exc.code, None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        conflict_results = [
            future.result(timeout=20)
            for future in (pool.submit(conflicting_write, different_a), pool.submit(conflicting_write, different_b))
        ]
    assert sorted(item[0] for item in conflict_results) == ["idempotency_conflict", "ok"]

    two_fragment_a = _request(
        directive_id, document_id, source_hash, fragment_id, fragment_hash,
        decision_key="two-fragment-a", extra_binding=secondary_fragment,
    )
    two_fragment_b = _request(
        directive_id, document_id, source_hash, fragment_id, fragment_hash,
        decision_key="two-fragment-b", extra_binding=secondary_fragment, reverse_bindings=True,
    )

    def two_fragment_write(value, key):
        with SessionLocal() as fragment_db:
            fragment_actor = fragment_db.get(User, user_id)
            result = store_v4_candidate(
                fragment_db, directive_id=directive_id, parsed=value, actor=fragment_actor,
                membership_id=membership_id, idempotency_key=key,
            )
            fragment_db.commit()
            return result.proposal.id

    with ThreadPoolExecutor(max_workers=2) as pool:
        two_fragment_results = [
            future.result(timeout=20)
            for future in (
                pool.submit(two_fragment_write, two_fragment_a, "two-fragment-a"),
                pool.submit(two_fragment_write, two_fragment_b, "two-fragment-b"),
            )
        ]
    assert len(set(two_fragment_results)) == 2
    with SessionLocal() as db:
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateProposal)) == 4
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateSubmission)) == 4
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateProposalEvent)) == 4
        first_proposal = db.get(ADV4CandidateProposal, results[0][0])
        assert first_proposal is not None
        actor = db.get(User, user_id)
        correction = _request(
            directive_id,
            document_id,
            source_hash,
            fragment_id,
            fragment_hash,
            decision_key="decision-v4-correction",
            relationships=[{
                "relationshipKey": "corrects-first",
                "relationType": "corrects_candidate",
                "predecessorProposalId": first_proposal.id,
                "reason": "PostgreSQL relationship integrity proof",
                "evidenceKeys": ["ev-official"],
            }],
        )
        corrected = store_v4_candidate(
            db,
            directive_id=directive_id,
            parsed=correction,
            actor=actor,
            membership_id=membership_id,
            idempotency_key="correction-key",
        )
        db.commit()
        assert corrected.proposal.id != first_proposal.id
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateSubmissionRelationship)) == 1

        closes_cycle = _request(
            directive_id, document_id, source_hash, fragment_id, fragment_hash,
            relationships=[{
                "relationshipKey": "cycle-back-to-correction",
                "relationType": "corrects_candidate",
                "predecessorProposalId": corrected.proposal.id,
                "reason": "Must reject a two-proposal correction cycle",
                "evidenceKeys": ["ev-official"],
            }],
        )
        with pytest.raises(ADV4Error) as cycle:
            store_v4_candidate(
                db, directive_id=directive_id, parsed=closes_cycle, actor=actor,
                membership_id=membership_id, idempotency_key="cycle-back",
            )
        assert cycle.value.code == "cyclic_reference"
        db.rollback()

        template_submission = db.get(ADV4CandidateSubmission, results[0][1])
        direct_submission_id = "avs_" + uuid.uuid4().hex
        direct_relation = {
            "relationshipKey": "direct-cycle-back",
            "relationType": "corrects_candidate",
            "predecessorProposalId": corrected.proposal.id,
            "reason": "Direct SQL cycle must be rejected by the database",
            "evidenceKeys": ["ev-official"],
        }
        direct_request = {
            "version": "ad-v4-submission-v1",
            "directiveId": directive_id,
            "proposalCanonicalHash": first_proposal.canonical_hash,
            "relationships": [direct_relation],
        }
        direct_request_bytes = canonical_bytes(direct_request)
        direct_relationship_envelope = {
            "version": "ad-v4-submission-relationship-v1",
            "submissionId": direct_submission_id,
            **direct_relation,
        }
        direct_relationship_bytes = canonical_bytes(direct_relationship_envelope)
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submissions (
                    id,proposal_id,directive_id,actor_kind,actor_user_id,
                    authorizing_membership_id,organization_id,actor_role,actor_status,
                    auth_policy_name,auth_policy_version,auth_claims_hash,endpoint_action,
                    idempotency_key,request_hash,request_canonical_bytes,raw_transport_hash
                ) VALUES (:id,:proposal_id,:directive_id,:actor_kind,:actor_user_id,
                    :membership_id,:organization_id,:actor_role,:actor_status,:policy_name,
                    :policy_version,:claims_hash,:endpoint_action,:idempotency,:request_hash,
                    :request_bytes,:raw_hash)
            """), {
                "id": direct_submission_id, "proposal_id": first_proposal.id,
                "directive_id": directive_id, "actor_kind": template_submission.actor_kind,
                "actor_user_id": template_submission.actor_user_id,
                "membership_id": template_submission.authorizing_membership_id,
                "organization_id": template_submission.organization_id,
                "actor_role": template_submission.actor_role,
                "actor_status": template_submission.actor_status,
                "policy_name": template_submission.auth_policy_name,
                "policy_version": template_submission.auth_policy_version,
                "claims_hash": template_submission.auth_claims_hash,
                "endpoint_action": template_submission.endpoint_action,
                "idempotency": "direct-sql-cycle", "request_bytes": direct_request_bytes,
                "request_hash": hashlib.sha256(DOMAINS["submission"] + direct_request_bytes).hexdigest(),
                "raw_hash": hashlib.sha256(direct_request_bytes).hexdigest(),
            })
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submission_relationships (
                    id,submission_id,relationship_key,relation_type,predecessor_proposal_id,
                    reason,evidence_keys,canonical_bytes,relationship_hash
                ) VALUES (:id,:submission_id,:relationship_key,:relation_type,:predecessor,
                    :reason,CAST(:evidence_keys AS jsonb),:canonical_bytes,:relationship_hash)
            """), {
                "id": "avr_" + uuid.uuid4().hex, "submission_id": direct_submission_id,
                "relationship_key": direct_relation["relationshipKey"],
                "relation_type": direct_relation["relationType"],
                "predecessor": direct_relation["predecessorProposalId"],
                "reason": direct_relation["reason"],
                "evidence_keys": json.dumps(direct_relation["evidenceKeys"]),
                "canonical_bytes": direct_relationship_bytes,
                "relationship_hash": hashlib.sha256(DOMAINS["relationship"] + direct_relationship_bytes).hexdigest(),
            })
            db.commit()
        db.rollback()

        def write_correction_origin(key: str) -> tuple[str, str]:
            with SessionLocal() as origin_db:
                origin_actor = origin_db.get(User, user_id)
                origin = store_v4_candidate(
                    origin_db,
                    directive_id=directive_id,
                    parsed=correction,
                    actor=origin_actor,
                    membership_id=membership_id,
                    idempotency_key=key,
                )
                origin_db.commit()
                return origin.proposal.id, origin.submission.id

        with ThreadPoolExecutor(max_workers=2) as pool:
            origin_results = [
                future.result(timeout=20)
                for future in (
                    pool.submit(write_correction_origin, "correction-origin-a"),
                    pool.submit(write_correction_origin, "correction-origin-b"),
                )
            ]
        assert {proposal_id for proposal_id, _ in origin_results} == {corrected.proposal.id}
        assert len({submission_id for _, submission_id in origin_results}) == 2
        db.expire_all()
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateSubmissionRelationship)) == 3

        immutable_rows = {
            "ad_v4_candidate_proposals": first_proposal.id,
            "ad_v4_candidate_evidence_bindings": db.scalar(select(ADV4CandidateEvidenceBinding.id)),
            "ad_v4_candidate_submissions": results[0][1],
            "ad_v4_candidate_submission_relationships": db.scalar(select(ADV4CandidateSubmissionRelationship.id)),
            "ad_v4_candidate_proposal_events": db.scalar(select(ADV4CandidateProposalEvent.id)),
        }
        for table_name, row_id in immutable_rows.items():
            with pytest.raises(DBAPIError):
                db.execute(text(f"UPDATE {table_name} SET id=id WHERE id=:id"), {"id": row_id})
                db.commit()
            db.rollback()
            with pytest.raises(DBAPIError):
                db.execute(text(f"DELETE FROM {table_name} WHERE id=:id"), {"id": row_id})
                db.commit()
            db.rollback()

        forged_id = "avp_" + uuid.uuid4().hex
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_proposals (
                    id,directive_id,schema_version,canonicalization_version,validator_version,
                    canonical_bytes,parsed_json,canonical_hash,evidence_binding_bytes,
                    evidence_binding_hash,binding_count,gate
                ) SELECT :id,directive_id,schema_version,canonicalization_version,validator_version,
                    canonical_bytes,parsed_json,:bad,evidence_binding_bytes,evidence_binding_hash,binding_count,gate
                FROM ad_v4_candidate_proposals WHERE id=:source_id
            """), {"id": forged_id, "source_id": first_proposal.id, "bad": "0" * 64})
            db.commit()
        db.rollback()

        binding = db.scalar(select(ADV4CandidateEvidenceBinding))
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_evidence_bindings (
                    id,proposal_id,directive_id,evidence_key,fragment_id,fragment_hash,
                    admitted_event_id,admitted_event_hash
                ) VALUES (:id,:proposal_id,:directive_id,'ev-forged',:fragment_id,:bad,
                    :event_id,:event_hash)
            """), {
                "id": "avb_" + uuid.uuid4().hex,
                "proposal_id": binding.proposal_id,
                "directive_id": binding.directive_id,
                "fragment_id": binding.fragment_id,
                "bad": "0" * 64,
                "event_id": binding.admitted_event_id,
                "event_hash": binding.admitted_event_hash,
            })
            db.commit()
        db.rollback()

        submission = db.get(ADV4CandidateSubmission, results[0][1])
        forged_claims = {
            "userId": submission.actor_user_id,
            "membershipId": submission.authorizing_membership_id,
            "organizationId": submission.organization_id,
            "role": submission.actor_role,
            "status": submission.actor_status,
            "policy": "attacker-selected-policy",
            "version": submission.auth_policy_version,
        }
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submissions (
                    id,proposal_id,directive_id,actor_kind,actor_user_id,
                    authorizing_membership_id,organization_id,actor_role,actor_status,
                    auth_policy_name,auth_policy_version,auth_claims_hash,endpoint_action,
                    idempotency_key,request_hash,request_canonical_bytes,raw_transport_hash
                ) VALUES (:id,:proposal_id,:directive_id,:actor_kind,:actor_user_id,
                    :membership_id,:organization_id,:actor_role,:actor_status,:policy_name,
                    :policy_version,:claims_hash,:endpoint_action,:idempotency,:request_hash,
                    :request_bytes,:raw_hash)
            """), {
                "id": "avs_" + uuid.uuid4().hex,
                "proposal_id": submission.proposal_id,
                "directive_id": submission.directive_id,
                "actor_kind": submission.actor_kind,
                "actor_user_id": submission.actor_user_id,
                "membership_id": submission.authorizing_membership_id,
                "organization_id": submission.organization_id,
                "actor_role": submission.actor_role,
                "actor_status": submission.actor_status,
                "policy_name": "attacker-selected-policy",
                "policy_version": submission.auth_policy_version,
                "claims_hash": hashlib.sha256(canonical_bytes(forged_claims)).hexdigest(),
                "endpoint_action": submission.endpoint_action,
                "idempotency": "forged-self-consistent-auth",
                "request_hash": submission.request_hash,
                "request_bytes": submission.request_canonical_bytes,
                "raw_hash": submission.raw_transport_hash,
            })
            db.commit()
        db.rollback()

        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submissions (
                    id,proposal_id,directive_id,actor_kind,actor_user_id,
                    authorizing_membership_id,organization_id,actor_role,actor_status,
                    auth_policy_name,auth_policy_version,auth_claims_hash,endpoint_action,
                    idempotency_key,request_hash,request_canonical_bytes,raw_transport_hash
                ) VALUES (:id,:proposal_id,:directive_id,:actor_kind,:actor_user_id,
                    :membership_id,:organization_id,:actor_role,:actor_status,:policy_name,
                    :policy_version,:claims_hash,:endpoint_action,:idempotency,:request_hash,
                    :request_bytes,:raw_hash)
            """), {
                "id": "avs_" + uuid.uuid4().hex,
                "proposal_id": submission.proposal_id,
                "directive_id": submission.directive_id,
                "actor_kind": submission.actor_kind,
                "actor_user_id": submission.actor_user_id,
                "membership_id": submission.authorizing_membership_id,
                "organization_id": submission.organization_id,
                "actor_role": submission.actor_role,
                "actor_status": submission.actor_status,
                "policy_name": submission.auth_policy_name,
                "policy_version": submission.auth_policy_version,
                "claims_hash": submission.auth_claims_hash,
                "endpoint_action": submission.endpoint_action,
                "idempotency": "forged-envelope",
                "request_hash": submission.request_hash,
                "request_bytes": b"{}",
                "raw_hash": submission.raw_transport_hash,
            })
            db.commit()
        db.rollback()

        relationship = db.scalar(select(ADV4CandidateSubmissionRelationship))
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submission_relationships (
                    id,submission_id,relationship_key,relation_type,predecessor_proposal_id,
                    reason,evidence_keys,canonical_bytes,relationship_hash
                ) VALUES (:id,:submission_id,'forged-key',:relation_type,:predecessor,
                    :reason,CAST(:evidence_keys AS jsonb),:canonical_bytes,:bad)
            """), {
                "id": "avr_" + uuid.uuid4().hex,
                "submission_id": relationship.submission_id,
                "relation_type": relationship.relation_type,
                "predecessor": relationship.predecessor_proposal_id,
                "reason": relationship.reason,
                "evidence_keys": json.dumps(relationship.evidence_keys),
                "canonical_bytes": relationship.canonical_bytes,
                "bad": "0" * 64,
            })
            db.commit()
        db.rollback()

        late_relationship = {
            "version": "ad-v4-submission-relationship-v1",
            "submissionId": relationship.submission_id,
            "relationshipKey": "late-extra-relationship",
            "relationType": relationship.relation_type,
            "predecessorProposalId": relationship.predecessor_proposal_id,
            "reason": "Late child must not escape the signed submission envelope",
            "evidenceKeys": relationship.evidence_keys,
        }
        late_bytes = canonical_bytes(late_relationship)
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_submission_relationships (
                    id,submission_id,relationship_key,relation_type,predecessor_proposal_id,
                    reason,evidence_keys,canonical_bytes,relationship_hash
                ) VALUES (:id,:submission_id,:relationship_key,:relation_type,:predecessor,
                    :reason,CAST(:evidence_keys AS jsonb),:canonical_bytes,:relationship_hash)
            """), {
                "id": "avr_" + uuid.uuid4().hex,
                "submission_id": late_relationship["submissionId"],
                "relationship_key": late_relationship["relationshipKey"],
                "relation_type": late_relationship["relationType"],
                "predecessor": late_relationship["predecessorProposalId"],
                "reason": late_relationship["reason"],
                "evidence_keys": json.dumps(late_relationship["evidenceKeys"]),
                "canonical_bytes": late_bytes,
                "relationship_hash": hashlib.sha256(DOMAINS["relationship"] + late_bytes).hexdigest(),
            })
            db.commit()
        db.rollback()

        event = db.scalar(select(ADV4CandidateProposalEvent))
        with pytest.raises(DBAPIError):
            db.execute(text("""
                INSERT INTO ad_v4_candidate_proposal_events (
                    id,proposal_id,directive_id,created_by_submission_id,event_type,
                    sequence_number,proposal_canonical_hash,evidence_binding_hash,
                    predecessor_event_hash,canonical_bytes,event_hash
                ) VALUES (:id,:proposal_id,:directive_id,:submission_id,:event_type,
                    :sequence,:proposal_hash,:binding_hash,NULL,:canonical_bytes,:bad)
            """), {
                "id": "ave_" + uuid.uuid4().hex,
                "proposal_id": event.proposal_id,
                "directive_id": event.directive_id,
                "submission_id": event.created_by_submission_id,
                "event_type": event.event_type,
                "sequence": event.sequence_number,
                "proposal_hash": event.proposal_canonical_hash,
                "binding_hash": event.evidence_binding_hash,
                "canonical_bytes": event.canonical_bytes,
                "bad": "0" * 64,
            })
            db.commit()
        db.rollback()

        lifecycle_fragment_id, lifecycle_fragment_hash = secondary_fragment
        admitted = db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
            ADEvidenceFragmentLifecycleEvent.fragment_id == lifecycle_fragment_id,
            ADEvidenceFragmentLifecycleEvent.event_type == "admitted",
        ))
        assert admitted is not None
        admitted_hash = admitted.event_hash

    lifecycle_barrier = threading.Barrier(2)

    def append_lifecycle_successor(label: str) -> str:
        with SessionLocal() as lifecycle_db:
            reason = f"Concurrent V4 evidence invalidation {label}"
            lifecycle_barrier.wait(timeout=10)
            try:
                lifecycle_db.execute(text("""
                    INSERT INTO ad_evidence_fragment_lifecycle_events (
                        id,fragment_id,event_type,actor_user_id,reason,sequence_number,
                        predecessor_event_hash,event_hash
                    ) VALUES (
                        :id,:fragment_id,'quarantined',:actor_id,:reason,1,:predecessor,
                        paprnav_hash_parts(:fragment_id_hash,:fragment_hash,'quarantined',
                          :actor_id_hash,:reason,'1',:predecessor_hash)
                    )
                """), {
                    "id": "afe_" + uuid.uuid4().hex, "fragment_id": lifecycle_fragment_id,
                    "fragment_id_hash": lifecycle_fragment_id, "fragment_hash": lifecycle_fragment_hash,
                    "actor_id": user_id, "actor_id_hash": user_id, "reason": reason,
                    "predecessor": admitted_hash, "predecessor_hash": admitted_hash,
                })
                lifecycle_db.commit()
                return "committed"
            except DBAPIError:
                lifecycle_db.rollback()
                return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        lifecycle_results = [
            future.result(timeout=20)
            for future in (
                pool.submit(append_lifecycle_successor, "a"),
                pool.submit(append_lifecycle_successor, "b"),
            )
        ]
    assert sorted(lifecycle_results) == ["committed", "rejected"]
    engine.dispose()


def test_candidate_binding_and_lifecycle_transition_serialize_without_stale_evidence(monkeypatch):
    """A transition cannot overtake a candidate after its admitted-root validation."""

    assert POSTGRES_URL
    engine = create_engine(
        POSTGRES_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={
            "connect_timeout": 5,
            "options": (
                "-c statement_timeout=10000 "
                "-c lock_timeout=5000 "
                "-c idle_in_transaction_session_timeout=15000"
            ),
        },
    )
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as seed_db:
        user_id, membership_id, directive_id, document_id, source_hash, fragment_id, fragment_hash = _seed(seed_db)
        admitted = seed_db.scalar(select(ADEvidenceFragmentLifecycleEvent).where(
            ADEvidenceFragmentLifecycleEvent.fragment_id == fragment_id,
            ADEvidenceFragmentLifecycleEvent.event_type == "admitted",
        ))
        assert admitted is not None
        admitted_hash = admitted.event_hash

    parsed = _request(directive_id, document_id, source_hash, fragment_id, fragment_hash)
    validated_and_locked = threading.Event()
    release_candidate = threading.Event()
    transition_started = threading.Event()
    transition_done = threading.Event()
    original_snapshot = v4_service._binding_snapshot
    pause_guard = threading.Lock()
    paused = False

    def pausing_snapshot(db, candidate_directive_id, proposal):
        nonlocal paused
        snapshots = original_snapshot(db, candidate_directive_id, proposal)
        with pause_guard:
            should_pause = not paused
            if should_pause:
                paused = True
        if should_pause:
            validated_and_locked.set()
            assert release_candidate.wait(timeout=10), "candidate pause was not released"
        return snapshots

    monkeypatch.setattr(v4_service, "_binding_snapshot", pausing_snapshot)

    def write_candidate() -> str:
        with SessionLocal() as candidate_db:
            actor = candidate_db.get(User, user_id)
            stored = v4_service.store_v4_candidate(
                candidate_db, directive_id=directive_id, parsed=parsed, actor=actor,
                membership_id=membership_id, idempotency_key="candidate-transition-race",
            )
            candidate_db.commit()
            return stored.proposal.id

    def transition_fragment() -> str:
        with SessionLocal() as transition_db:
            reason = "Transition racing candidate evidence binding"
            transition_db.execute(text("SET application_name = 'paprnav_v4_lifecycle_transition'"))
            transition_started.set()
            transition_db.execute(text("""
                INSERT INTO ad_evidence_fragment_lifecycle_events (
                    id,fragment_id,event_type,actor_user_id,reason,sequence_number,
                    predecessor_event_hash,event_hash
                ) VALUES (
                    :id,:fragment_id,'quarantined',:actor_id,:reason,1,:predecessor,
                    paprnav_hash_parts(:fragment_id_hash,:fragment_hash,'quarantined',
                      :actor_id_hash,:reason,'1',:predecessor_hash)
                )
            """), {
                "id": "afe_" + uuid.uuid4().hex, "fragment_id": fragment_id,
                "fragment_id_hash": fragment_id, "fragment_hash": fragment_hash,
                "actor_id": user_id, "actor_id_hash": user_id, "reason": reason,
                "predecessor": admitted_hash, "predecessor_hash": admitted_hash,
            })
            transition_db.commit()
            transition_done.set()
            return "committed"

    with ThreadPoolExecutor(max_workers=2) as pool:
        candidate_future = pool.submit(write_candidate)
        assert validated_and_locked.wait(timeout=10)
        transition_future = pool.submit(transition_fragment)
        assert transition_started.wait(timeout=10)
        deadline = time.monotonic() + 3
        observed_lock_wait = False
        while time.monotonic() < deadline:
            with engine.connect() as observer:
                observed_lock_wait = bool(observer.scalar(text("""
                    SELECT EXISTS (
                      SELECT 1 FROM pg_stat_activity
                      WHERE application_name='paprnav_v4_lifecycle_transition'
                        AND wait_event_type='Lock'
                    )
                """)))
            if observed_lock_wait:
                break
            time.sleep(0.02)
        assert observed_lock_wait, "lifecycle transition never reached the candidate-held row lock"
        assert not transition_done.is_set()
        release_candidate.set()
        proposal_id = candidate_future.result(timeout=20)
        assert transition_future.result(timeout=20) == "committed"

    with SessionLocal() as verify_db:
        assert verify_db.get(ADV4CandidateProposal, proposal_id) is not None
        actor = verify_db.get(User, user_id)
        changed = _request(
            directive_id, document_id, source_hash, fragment_id, fragment_hash,
            decision_key="candidate-after-transition",
        )
        with pytest.raises(ADV4Error) as stale:
            v4_service.store_v4_candidate(
                verify_db, directive_id=directive_id, parsed=changed, actor=actor,
                membership_id=membership_id, idempotency_key="candidate-after-transition",
            )
        assert stale.value.code == "evidence_not_admitted"
        verify_db.rollback()
    engine.dispose()


def test_99_occupied_v4_downgrade_refuses_without_deleting_audit_rows():
    downgrade = _alembic("downgrade 20260830_0025")
    assert downgrade.returncode != 0
    assert "contains immutable V4 candidates" in downgrade.stdout + downgrade.stderr
    assert POSTGRES_URL
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260901_0026"
        assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_proposals")) >= 2
    engine.dispose()


def test_98_occupied_downgrade_waits_for_concurrent_origin_then_refuses():
    assert POSTGRES_URL
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        proposal = db.scalar(
            select(ADV4CandidateProposal)
            .where(ADV4CandidateProposal.binding_count == 1)
            .order_by(ADV4CandidateProposal.created_at, ADV4CandidateProposal.id)
        )
        assert proposal is not None
        original = db.scalar(select(ADV4CandidateSubmission).where(
            ADV4CandidateSubmission.proposal_id == proposal.id,
        ))
        actor = db.get(User, original.actor_user_id)
        envelope = {"proposal": proposal.parsed_json, "submissionContext": {"relationships": []}}
        store_v4_candidate(
            db, directive_id=proposal.directive_id,
            parsed=parse_v4_request_bytes(json.dumps(envelope, separators=(",", ":")).encode()),
            actor=actor, membership_id=original.authorizing_membership_id,
            idempotency_key="downgrade-race-origin",
        )
        environment = os.environ.copy()
        environment["DATABASE_URL"] = POSTGRES_URL
        process = subprocess.Popen(
            [sys.executable, "-m", "alembic", "downgrade", "20260830_0025"],
            cwd=os.path.dirname(os.path.dirname(__file__)), env=environment,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        time.sleep(0.4)
        assert process.poll() is None, "downgrade did not wait for the concurrent candidate transaction"
        db.commit()
        stdout, stderr = process.communicate(timeout=20)
    assert process.returncode != 0
    assert "contains immutable V4 candidates" in stdout + stderr
    engine.dispose()
