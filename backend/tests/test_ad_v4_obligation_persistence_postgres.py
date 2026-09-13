from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
import uuid
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
import time

import pytest
from fastapi import HTTPException
from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    UniqueConstraint,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.api.routes import ads as ads_routes
from app.core.config import get_settings
from app.db.session import repeatable_read_only_session
from app.models.core import (
    Base,
    ADEvidenceFragment,
    ADEvidenceFragmentLifecycleEvent,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateCorrectionRef,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateObligationProjection,
    ADV4CandidateObligationMaterializationRequest,
    ADV4CandidateObligationProjectionEvent,
    ADV4CandidateObligationRequirement,
    ADV4CandidateProposal,
    OrganizationMembership,
    User,
)
from app.services.ad_evidence import _hash_parts
from app.services.ad_v4_obligation_mapping_v1 import MAPPING_DIGEST
from app.services.ad_v4_applicability import _node_value, materialize_applicability
from app.services.ad_v4_candidates import (
    CANONICALIZATION_VERSION_V2,
    DOMAINS_V2,
    VALIDATOR_VERSION_V2,
    canonical_bytes,
    parse_v4_request_bytes,
    store_v4_candidate,
    validate_v4_envelope,
)
from app.services.ad_v4_obligation_persistence import (
    _materialization_request_values,
    _projection_event_values,
    materialize_obligations,
    persist_obligation_materialization,
    reconstruct_obligation_projection,
)
from app.services.ad_v4_obligations import (
    ObligationApplicabilityTarget,
    ObligationCorrectionReference,
    ObligationIntegrityError,
    materialize_obligation_projection_graph,
)
from test_ad_v4_applicability_postgres import _enable, _store
from test_ad_v4_postgres import _request, _seed


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PAPRNAV_TEST_POSTGRES_URL required",
)


def _differences(left, right, path=""):
    if type(left) is not type(right):
        return [(path, left, right)]
    if isinstance(left, dict):
        differences = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}/{key}"
            if key not in left or key not in right:
                differences.append((child, left.get(key), right.get(key)))
            else:
                differences.extend(_differences(left[key], right[key], child))
        return differences
    if isinstance(left, list):
        differences = []
        for index in range(max(len(left), len(right))):
            child = f"{path}/{index}"
            if index >= len(left) or index >= len(right):
                differences.append((child, left[index] if index < len(left) else None,
                                    right[index] if index < len(right) else None))
            else:
                differences.extend(_differences(left[index], right[index], child))
        return differences
    return [] if left == right else [(path, left, right)]


@pytest.mark.parametrize("value", [
    "idem:usr_test:mem_test:materialize_ad_v4_obligations:1:key",
    "projection:avp_test:paprnav-ad-v4-app-materializer-2",
    "projection:avp_test:paprnav-ad-v4-obligation-materializer-1",
    "projection:\N{LATIN SMALL LETTER E WITH ACUTE}:unicode",
])
def test_postgres_advisory_key_matches_python(value: str) -> None:
    expected = int.from_bytes(
        hashlib.sha256(value.encode()).digest()[:8],
        "big",
        signed=True,
    )
    engine = _engine()
    try:
        with engine.connect() as connection:
            assert connection.scalar(
                text("SELECT paprnav_v4_lock_key(:value)"),
                {"value": value},
            ) == expected
    finally:
        engine.dispose()


def _engine():
    return create_engine(
        POSTGRES_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={
            "connect_timeout": 5,
            "options": (
                "-c statement_timeout=30000 "
                "-c lock_timeout=5000 "
                "-c idle_in_transaction_session_timeout=60000"
            ),
        },
    )


def _persist_complete_graph(
    db: Session,
    *,
    with_correction: bool = False,
    via_service: bool = False,
    duplicate_action_requirement: bool = False,
    commit_graph: bool = True,
    maximum_decimal: bool = False,
    fail_after_graph_flush: int | None = None,
) -> ADV4CandidateObligationProjection:
    suffix = uuid.uuid4().hex[:12]
    if with_correction or duplicate_action_requirement or maximum_decimal:
        (
            user_id, membership_id, directive_id, document_id,
            source_hash, fragment_id, fragment_hash,
        ) = _seed(db, ad_number=f"2099-{suffix[:2]}-{suffix[2:4]}")
        parsed = _request(
            directive_id, document_id, source_hash, fragment_id, fragment_hash,
            decision_key=f"obligation-{suffix}",
        )
        proposal_value = parsed.value["proposal"]
        if duplicate_action_requirement:
            duplicate = deepcopy(proposal_value["requirements"][0])
            duplicate["requirementKey"] = "requirement-second"
            duplicate["sequence"] = "2"
            proposal_value["requirements"].append(duplicate)
        if maximum_decimal:
            proposal_value["requirements"][0]["initialTiming"] = {
                "logic": "all",
                "terms": [{
                    "metric": "calendar",
                    "interval": "1" * 16_384,
                    "unit": "days",
                    "comparator": "within",
                    "anchor": "effective_date",
                    "evidenceKeys": ["ev-official"],
                }],
                "evidenceKeys": ["ev-official"],
            }
        if with_correction:
            proposal_value["officialDocuments"].extend([{
                "officialDocumentKey": key,
                "documentRole": "official_correction",
                "sourceDocumentId": document_id,
                "sourceContentHash": source_hash,
                "publicationDocumentNumber": number,
                "evidenceKeys": ["ev-official"],
            } for key, number in (
                ("official-original", "ORIGINAL"),
                ("official-correction", "CORRECTION"),
            )])
            proposal_value["officialDocuments"].sort(
                key=lambda value: value["officialDocumentKey"],
            )
            proposal_value["authoritativeCorrections"] = [{
                "correctionKey": "correction-main",
                "correctionType": "official_correction",
                "originalDocumentRefKey": "official-original",
                "correctingDocumentRefKey": "official-correction",
                "changedSemanticRefs": [{
                    "namespace": "requirements", "key": "requirement-main",
                }],
                "evidenceKeys": ["ev-official"],
            }]
        parsed = parse_v4_request_bytes(json.dumps(
            parsed.value, separators=(",", ":"),
        ).encode())
        validated_proposal, _ = validate_v4_envelope(
            parsed, directive_id, validator_version=VALIDATOR_VERSION_V2,
        )
        proposal_payload = canonical_bytes(
            validated_proposal, CANONICALIZATION_VERSION_V2,
        )
        proposal_hash = hashlib.sha256(
            DOMAINS_V2["proposal"] + proposal_payload,
        ).hexdigest()
        canonical_json, parsed_json, hash_matches, directive_matches = db.execute(text("""
            SELECT convert_from(:payload,'UTF8')::jsonb,CAST(:parsed AS jsonb),
                   encode(sha256(convert_to(
                     'paprnav:ad_extraction_v4:proposal:paprnav-ad-v4-c14n-2','UTF8')
                     ||decode('00','hex')||CAST(:payload AS bytea)),'hex')=:hash,
                   CAST(:parsed AS jsonb)->'directiveIdentity'->>'directiveId'=:directive_id
        """), {
            "payload": proposal_payload,
            "parsed": json.dumps(validated_proposal, separators=(",", ":")),
            "hash": proposal_hash,
            "directive_id": directive_id,
        }).one()
        assert canonical_json == parsed_json, _differences(canonical_json, parsed_json)
        assert hash_matches and directive_matches
        stored = store_v4_candidate(
            db, directive_id=directive_id, parsed=parsed,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key=f"candidate-obligation-{suffix}",
            validator_version=VALIDATOR_VERSION_V2,
        )
        db.commit()
        proposal_id = stored.proposal.id
    else:
        user_id, membership_id, directive_id, proposal_id = _store(
            db,
            validator_version=VALIDATOR_VERSION_V2,
            suffix=f"obligation-{suffix}",
            ad_number=f"2099-{suffix[:2]}-{suffix[2:4]}",
        )
    app_result = materialize_applicability(
        db,
        directive_id=directive_id,
        proposal_id=proposal_id,
        actor=db.get(User, user_id),
        membership_id=membership_id,
        idempotency_key=f"obligation-app-{suffix}",
    )
    db.commit()

    if via_service:
        result = materialize_obligations(
            db,
            directive_id=directive_id,
            proposal_id=proposal_id,
            app_projection_id=app_result.projection.id,
            actor=db.get(User, user_id),
            membership_id=membership_id,
            idempotency_key=f"obligation-materialize-{suffix}",
        )
        db.commit()
        return result.projection

    proposal = db.get(ADV4CandidateProposal, proposal_id)
    assert proposal is not None
    app_projection = app_result.projection
    app_nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
        ADV4CandidateAppSemanticNode.projection_id == app_projection.id,
        ADV4CandidateAppSemanticNode.node_type.in_((
            "product_scope", "condition", "applicability_rule",
        )),
    )).all()
    app_targets = tuple(ObligationApplicabilityTarget(
        id=node.id,
        identity_hash=node.identity_hash,
        proposal_id=node.proposal_id,
        projection_id=node.projection_id,
        node_type=node.node_type,
        node_key=node.node_key,
        source_pointer=node.source_pointer,
        canonical_node_bytes=canonical_bytes(
            _node_value(proposal.parsed_json, node.source_pointer),
            CANONICALIZATION_VERSION_V2,
        ),
        canonical_node_hash=node.canonical_node_hash,
    ) for node in app_nodes)
    evidence_bindings = {
        row.evidence_key: row.id
        for row in db.scalars(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == proposal_id,
        )).all()
    }
    foundation_refs = tuple(ObligationCorrectionReference(
        id=row.id,
        correction_id=row.correction_id,
        proposal_id=row.proposal_id,
        canonical_ordinal=row.canonical_ordinal,
        namespace=row.namespace,
        semantic_key=row.semantic_key,
        owner_slice=row.owner_slice,
        reference_hash=row.reference_hash,
    ) for row in db.scalars(select(ADV4CandidateCorrectionRef).where(
        ADV4CandidateCorrectionRef.proposal_id == proposal.id,
    )).all())
    graph = materialize_obligation_projection_graph(
        proposal_id=proposal.id,
        directive_id=proposal.directive_id,
        proposal_canonical_hash=proposal.canonical_hash,
        evidence_binding_hash=proposal.evidence_binding_hash,
        app_projection_id=app_projection.id,
        app_projection_hash=app_projection.projection_hash,
        canonical_proposal=proposal.parsed_json,
        evidence_bindings=evidence_bindings,
        app_targets=app_targets,
        foundation_refs=foundation_refs,
    )
    membership = db.get(OrganizationMembership, membership_id)
    assert membership is not None
    if fail_after_graph_flush == 0:
        raise RuntimeError("injected before obligation root")
    original_flush = db.flush
    flush_count = 0

    def injected_flush(*args, **kwargs):
        nonlocal flush_count
        original_flush(*args, **kwargs)
        flush_count += 1
        if flush_count == fail_after_graph_flush:
            raise RuntimeError(f"injected after graph flush {flush_count}")

    if fail_after_graph_flush is not None:
        db.flush = injected_flush  # type: ignore[method-assign]
    try:
        materialization = persist_obligation_materialization(
            db, graph,
            actor_user_id=user_id,
            authorizing_membership_id=membership_id,
            organization_id=membership.organization_id,
            actor_role=membership.role,
            actor_status=membership.status,
            idempotency_key=f"obligation-materialize-{suffix}",
        )
    finally:
        db.flush = original_flush  # type: ignore[method-assign]
    projection = materialization.projection
    db.flush()
    typed_subtree = db.scalar(text(
        "SELECT paprnav_v4_candidate_obligation_typed_subtree(:id)"
    ), {"id": projection.id})
    expected_subtree = db.scalar(text(
        "SELECT convert_from(obligation_subtree_bytes,'UTF8')::jsonb "
        "FROM ad_v4_candidate_obligation_projections WHERE id=:id"
    ), {"id": projection.id})
    assert typed_subtree == expected_subtree, _differences(
        typed_subtree, expected_subtree,
    )
    if commit_graph:
        db.commit()
    return projection


def _assert_update_rejected(
    engine, *, projection_id: str, table: str, trigger_ordinal: int,
    update_sql: str, message: str,
) -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(
                f"ALTER TABLE {table} DISABLE TRIGGER "
                f"trg_aob_{trigger_ordinal}_immutable"
            ))
            connection.execute(text(update_sql), {"projection_id": projection_id})
            with pytest.raises(DBAPIError, match=message):
                connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        finally:
            transaction.rollback()


def _assert_correction_mutation_rejected(
    engine, *, projection_id: str, mutation_sql: str, message: str,
) -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(
                "ALTER TABLE ad_v4_candidate_correction_semantic_bindings "
                "DISABLE TRIGGER "
                "trg_ad_v4_candidate_correction_semantic_bindings_immutable"
            ))
            result = connection.execute(
                text(mutation_sql), {"projection_id": projection_id},
            )
            assert result.rowcount == 1
            with pytest.raises(
                DBAPIError, match=message,
            ):
                connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        finally:
            transaction.rollback()


def _assert_read_rejected(
    engine, *, projection_id: str, table: str, immutable_trigger: str,
    mutation_sql: str, message: str,
) -> None:
    with Session(engine, expire_on_commit=False) as db:
        transaction = db.begin()
        try:
            db.execute(text(
                f"ALTER TABLE {table} DISABLE TRIGGER {immutable_trigger}"
            ))
            result = db.execute(
                text(mutation_sql), {"projection_id": projection_id},
            )
            assert result.rowcount == 1
            projection = db.get(ADV4CandidateObligationProjection, projection_id)
            assert projection is not None
            with pytest.raises(ObligationIntegrityError, match=message):
                reconstruct_obligation_projection(db, projection)
        finally:
            transaction.rollback()


def test_complete_graph_commits_and_extra_direct_sql_row_fails_closed():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db)
            reconstructed = reconstruct_obligation_projection(db, projection)
            assert set(reconstructed) == {
                "incorporatedDocuments", "requirements",
                "recurrenceGroups", "amocAuthorityProvisions",
            }
            assert db.scalar(text(
                "SELECT paprnav_v4_candidate_obligation_typed_subtree(:id)"
                " = convert_from(obligation_subtree_bytes,'UTF8')::jsonb "
                "FROM ad_v4_candidate_obligation_projections WHERE id=:id"
            ), {"id": projection.id}) is True

            with pytest.raises(DBAPIError, match="structural counts differ"):
                db.execute(text("""
                    INSERT INTO ad_v4_candidate_obligation_action_steps(
                      semantic_node_id,proposal_id,projection_id,action_node_id,
                      canonical_ordinal,step_text)
                    SELECT id,proposal_id,projection_id,
                           (SELECT semantic_node_id
                              FROM ad_v4_candidate_obligation_actions
                             WHERE projection_id=:projection_id LIMIT 1),
                           999,'injected'
                      FROM ad_v4_candidate_obligation_semantic_nodes
                     WHERE projection_id=:projection_id LIMIT 1
                """), {"projection_id": projection.id})
                db.commit()
            db.rollback()
            assert db.get(ADV4CandidateObligationProjection, projection.id) is not None
    finally:
        engine.dispose()


def test_new_graph_later_insert_after_anchor_cannot_bypass_deferred_validation():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, commit_graph=False)

            # Process the valid graph's anchor, then exercise the hostile case:
            # a direct-SQL client re-defers and writes again in the same xact.
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            db.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            db.execute(text("""
                INSERT INTO ad_v4_candidate_obligation_action_steps(
                  semantic_node_id,proposal_id,projection_id,action_node_id,
                  canonical_ordinal,step_text)
                SELECT id,proposal_id,projection_id,
                       (SELECT semantic_node_id
                          FROM ad_v4_candidate_obligation_actions
                         WHERE projection_id=:projection_id LIMIT 1),
                       999,'injected-after-anchor'
                  FROM ad_v4_candidate_obligation_semantic_nodes
                 WHERE projection_id=:projection_id LIMIT 1
            """), {"projection_id": projection.id})
            with pytest.raises(DBAPIError, match="structural counts differ"):
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            db.rollback()
    finally:
        engine.dispose()


def test_postgres_persists_exact_maximum_decimal_text_boundary():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, maximum_decimal=True)
            interval_text, interval_numeric = db.execute(text("""
                SELECT interval_text,interval_numeric::text
                  FROM ad_v4_candidate_obligation_timing_terms
                 WHERE projection_id=:projection_id
            """), {"projection_id": projection.id}).one()
            assert interval_text == "1" * 16_384
            assert interval_numeric == interval_text
            reconstruct_obligation_projection(db, projection)
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("phase", "fail_after_flush"),
    (
        ("before_root", 0),
        ("after_root", 1),
        ("after_semantic_nodes", 2),
        ("after_children_and_correction", 3),
        ("after_request", 4),
        ("after_event", 5),
        ("after_forced_constraints", None),
    ),
)
def test_materialization_failure_phase_rolls_back_every_slice3b_row(
    phase: str, fail_after_flush: int | None,
):
    engine = _engine()
    obligation_tables = tuple(
        table for table in inspect(engine).get_table_names()
        if table.startswith("ad_v4_candidate_obligation_")
    )

    def read_counts(executor) -> dict[str, int]:
        result = {
            table: executor.scalar(text(f"SELECT count(*) FROM {table}"))
            for table in obligation_tables
        }
        result["slice3b_correction_bindings"] = executor.scalar(text(
                "SELECT count(*) "
                "FROM ad_v4_candidate_correction_semantic_bindings "
                "WHERE binding_slice='slice_3b'"
        ))
        return result

    def committed_counts() -> dict[str, int]:
        with engine.connect() as connection:
            return read_counts(connection)

    try:
        before = committed_counts()
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'failure-phase-test')"
            ))
            db.commit()
            with pytest.raises(RuntimeError, match="injected"):
                if phase == "after_forced_constraints":
                    _persist_complete_graph(
                        db, with_correction=True, commit_graph=False,
                    )
                    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
                    raise RuntimeError("injected after forced constraints")
                _persist_complete_graph(
                    db,
                    with_correction=True,
                    commit_graph=False,
                    fail_after_graph_flush=fail_after_flush,
                )
            transient = read_counts(db)
            if phase == "before_root":
                assert transient == before
            else:
                assert transient["ad_v4_candidate_obligation_projections"] == (
                    before["ad_v4_candidate_obligation_projections"] + 1
                )
            if phase in {
                "after_semantic_nodes",
                "after_children_and_correction",
                "after_request",
                "after_event",
                "after_forced_constraints",
            }:
                assert transient[
                    "ad_v4_candidate_obligation_semantic_nodes"
                ] > before["ad_v4_candidate_obligation_semantic_nodes"]
            if phase in {
                "after_children_and_correction",
                "after_request",
                "after_event",
                "after_forced_constraints",
            }:
                assert transient[
                    "ad_v4_candidate_obligation_requirements"
                ] > before["ad_v4_candidate_obligation_requirements"]
                assert transient["slice3b_correction_bindings"] == (
                    before["slice3b_correction_bindings"] + 1
                )
            if phase in {
                "after_request", "after_event", "after_forced_constraints",
            }:
                assert transient[
                    "ad_v4_candidate_obligation_materialization_requests"
                ] == before[
                    "ad_v4_candidate_obligation_materialization_requests"
                ] + 1
            if phase in {"after_event", "after_forced_constraints"}:
                assert transient[
                    "ad_v4_candidate_obligation_projection_events"
                ] == before[
                    "ad_v4_candidate_obligation_projection_events"
                ] + 1
            db.rollback()
        assert committed_counts() == before
    finally:
        engine.dispose()


def test_verified_read_fails_closed_across_integrity_surfaces():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(db).id

        cases = (
            (
                "ad_v4_candidate_obligation_actions", "trg_aob_8_immutable",
                "UPDATE ad_v4_candidate_obligation_actions "
                "SET action_type='repair' WHERE projection_id=:projection_id",
                "action owners differs",
            ),
            (
                "ad_v4_candidate_obligation_semantic_nodes",
                "trg_aob_2_immutable",
                "UPDATE ad_v4_candidate_obligation_semantic_nodes "
                "SET canonical_node_hash=repeat('0',64) "
                "WHERE id=(SELECT id FROM "
                "ad_v4_candidate_obligation_semantic_nodes "
                "WHERE projection_id=:projection_id LIMIT 1)",
                "semantic nodes differs",
            ),
            (
                "ad_v4_candidate_obligation_evidence_links",
                "trg_aob_4_immutable",
                "UPDATE ad_v4_candidate_obligation_evidence_links "
                "SET purpose='branch_clause' WHERE id=(SELECT id FROM "
                "ad_v4_candidate_obligation_evidence_links "
                "WHERE projection_id=:projection_id LIMIT 1)",
                "evidence links differs",
            ),
            (
                "ad_v4_candidate_obligation_projection_events",
                "trg_aob_23_immutable",
                "UPDATE ad_v4_candidate_obligation_projection_events "
                "SET event_hash=repeat('0',64) "
                "WHERE projection_id=:projection_id",
                "projection event differs",
            ),
            (
                "ad_v4_candidate_obligation_actions", "trg_aob_8_immutable",
                "UPDATE ad_v4_candidate_obligation_actions "
                "SET requirement_node_id=semantic_node_id "
                "WHERE projection_id=:projection_id",
                "action owners differs",
            ),
            (
                "ad_v4_candidate_obligation_projection_events",
                "trg_aob_23_immutable",
                "DELETE FROM ad_v4_candidate_obligation_projection_events "
                "WHERE projection_id=:projection_id",
                "projection event sequence differs",
            ),
        )
        for table, trigger, mutation, message in cases:
            _assert_read_rejected(
                engine, projection_id=projection_id, table=table,
                immutable_trigger=trigger, mutation_sql=mutation,
                message=message,
            )
    finally:
        engine.dispose()


def test_false_root_events_cannot_cause_obligation_staleness():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(db).id

        for event_type, cause_kind, source_model, source_filter in (
            (
                "parent_app_stale", "app_projection_event",
                ADV4CandidateAppProjectionEvent,
                lambda projection: (
                    ADV4CandidateAppProjectionEvent.projection_id
                    == projection.app_projection_id
                ),
            ),
            (
                "evidence_invalidated", "evidence_lifecycle_event",
                ADEvidenceFragmentLifecycleEvent,
                lambda projection: ADEvidenceFragmentLifecycleEvent.id.in_(
                    select(ADV4CandidateEvidenceBinding.admitted_event_id).where(
                        ADV4CandidateEvidenceBinding.proposal_id
                        == projection.proposal_id,
                    )
                ),
            ),
        ):
            with Session(engine, expire_on_commit=False) as db:
                transaction = db.begin()
                try:
                    projection = db.get(
                        ADV4CandidateObligationProjection, projection_id,
                    )
                    root = db.scalar(select(
                        ADV4CandidateObligationProjectionEvent,
                    ).where(
                        ADV4CandidateObligationProjectionEvent.projection_id
                        == projection_id,
                        ADV4CandidateObligationProjectionEvent.sequence_number == 0,
                    ))
                    cause = db.scalar(select(source_model).where(
                        source_filter(projection),
                    ).order_by(source_model.sequence_number))
                    assert projection is not None and root is not None and cause is not None
                    cause_hash = (
                        cause.event_hash
                        if cause_kind != "candidate_relationship"
                        else cause.relationship_hash
                    )
                    event = ADV4CandidateObligationProjectionEvent(
                        **_projection_event_values(
                            projection,
                            correction_binding_set_hash=(
                                root.correction_binding_set_hash
                            ),
                            causing_request_id=root.causing_request_id,
                            event_type=event_type,
                            sequence_number=1,
                            predecessor_event_hash=root.event_hash,
                            cause_kind=cause_kind,
                            cause_id=cause.id,
                            cause_hash=cause_hash,
                        ),
                    )
                    db.add(event)
                    db.flush([event])
                    with pytest.raises(
                        ObligationIntegrityError,
                        match="projection event cause differs",
                    ):
                        reconstruct_obligation_projection(db, projection)
                    with pytest.raises(
                        DBAPIError,
                        match="projection event differs",
                    ):
                        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
                finally:
                    transaction.rollback()
    finally:
        engine.dispose()


def test_equal_payload_forward_child_identity_swap_fails_closed():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(
                db, duplicate_action_requirement=True,
            ).id
            requirements = db.scalars(select(
                ADV4CandidateObligationRequirement,
            ).where(
                ADV4CandidateObligationRequirement.projection_id
                == projection_id,
            ).order_by(
                ADV4CandidateObligationRequirement.canonical_ordinal,
            )).all()
            assert len(requirements) == 2

        mutation = """
            UPDATE ad_v4_candidate_obligation_requirements source
               SET action_node_id=target.action_node_id
              FROM ad_v4_candidate_obligation_requirements target
             WHERE source.projection_id=:projection_id
               AND target.projection_id=:projection_id
               AND source.requirement_key='requirement-main'
               AND target.requirement_key='requirement-second'
        """
        _assert_update_rejected(
            engine,
            projection_id=projection_id,
            table="ad_v4_candidate_obligation_requirements",
            trigger_ordinal=7,
            update_sql=mutation,
            message="exact owner child/reference differs",
        )
        _assert_read_rejected(
            engine,
            projection_id=projection_id,
            table="ad_v4_candidate_obligation_requirements",
            immutable_trigger="trg_aob_7_immutable",
            mutation_sql=mutation,
            message="requirement owners differs",
        )
    finally:
        engine.dispose()


def test_combined_graph_walk_deduplicates_layered_dag_reachability():
    migration_sql = (
        Path(__file__).parents[1]
        / "app/db/migrations/sql/20260911_0028_obligation_integrity.sql"
    ).read_text(encoding="utf-8")
    assert "walk(origin,current,path,cycle)" not in migration_sql
    assert "walk(origin,current) AS" in migration_sql

    engine = _engine()
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout='1000ms'"))
            reachable_pairs = connection.scalar(text("""
                WITH RECURSIVE nodes(layer,side,id) AS (
                  SELECT layer,side,layer*2+side
                    FROM generate_series(0,25) layer
                    CROSS JOIN generate_series(0,1) side
                ), graph(source_id,target_id) AS (
                  SELECT source.id,target.id
                    FROM nodes source JOIN nodes target
                      ON target.layer=source.layer+1
                ), walk(origin,current) AS (
                  SELECT source_id,target_id FROM graph
                  UNION
                  SELECT walk.origin,graph.target_id
                    FROM walk JOIN graph ON graph.source_id=walk.current
                )
                SELECT count(*) FROM walk
            """))
            assert reachable_pairs == 1300
    finally:
        engine.dispose()


def test_authorized_service_create_same_key_retry_and_new_request_reuse():
    engine = _engine()
    try:
        os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
        get_settings.cache_clear()
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
            get_settings.cache_clear()
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, via_service=True)
            first_request = db.scalar(select(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            ))
            assert first_request is not None
            actor = db.get(User, first_request.actor_user_id)
            assert actor is not None

            retry = materialize_obligations(
                db,
                directive_id=projection.directive_id,
                proposal_id=projection.proposal_id,
                app_projection_id=projection.app_projection_id,
                actor=actor,
                membership_id=first_request.authorizing_membership_id,
                idempotency_key=first_request.idempotency_key,
            )
            assert retry.idempotent_retry and not retry.created
            assert retry.projection.id == projection.id
            assert retry.request.id == first_request.id

            reused = materialize_obligations(
                db,
                directive_id=projection.directive_id,
                proposal_id=projection.proposal_id,
                app_projection_id=projection.app_projection_id,
                actor=actor,
                membership_id=first_request.authorizing_membership_id,
                idempotency_key=f"{first_request.idempotency_key}-new",
            )
            db.commit()
            assert not reused.idempotent_retry and not reused.created
            assert reused.projection.id == projection.id
            assert reused.request.id != first_request.id
            assert db.scalar(select(func.count()).select_from(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            )) == 2
            assert db.scalar(select(func.count()).select_from(
                ADV4CandidateObligationProjectionEvent,
            ).where(
                ADV4CandidateObligationProjectionEvent.projection_id
                == projection.id,
            )) == 1
            reconstruct_obligation_projection(db, projection)
    finally:
        get_settings.cache_clear()
        engine.dispose()


def test_authorized_retry_appends_each_genuine_stale_cause_once():
    engine = _engine()
    try:
        os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
        get_settings.cache_clear()
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, via_service=True)
            request = db.scalar(select(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            ))
            binding = db.scalar(select(ADV4CandidateEvidenceBinding).where(
                ADV4CandidateEvidenceBinding.proposal_id
                == projection.proposal_id,
            ))
            fragment = db.get(ADEvidenceFragment, binding.fragment_id)
            admitted = db.get(
                ADEvidenceFragmentLifecycleEvent, binding.admitted_event_id,
            )
            assert request is not None and fragment is not None and admitted is not None
            reason = "stale-repair regression quarantine"
            invalidated = ADEvidenceFragmentLifecycleEvent(
                fragment_id=fragment.id,
                event_type="quarantined",
                actor_user_id=request.actor_user_id,
                reason=reason,
                sequence_number=1,
                predecessor_event_hash=admitted.event_hash,
                event_hash=_hash_parts(
                    fragment.id,
                    fragment.fragment_hash,
                    "quarantined",
                    request.actor_user_id,
                    reason,
                    1,
                    admitted.event_hash,
                ),
            )
            db.add(invalidated)
            db.commit()

            actor = db.get(User, request.actor_user_id)
            first = materialize_obligations(
                db,
                directive_id=projection.directive_id,
                proposal_id=projection.proposal_id,
                app_projection_id=projection.app_projection_id,
                actor=actor,
                membership_id=request.authorizing_membership_id,
                idempotency_key=request.idempotency_key,
            )
            db.commit()
            assert first.idempotent_retry is True
            events = db.scalars(select(
                ADV4CandidateObligationProjectionEvent,
            ).where(
                ADV4CandidateObligationProjectionEvent.projection_id
                == projection.id,
            ).order_by(
                ADV4CandidateObligationProjectionEvent.sequence_number,
            )).all()
            assert [event.event_type for event in events] == [
                "materialized", "parent_app_stale", "evidence_invalidated",
            ]
            assert len({(event.cause_kind, event.cause_id) for event in events[1:]}) == 2
            reconstruct_obligation_projection(
                db, projection, require_fresh=False,
            )
            with pytest.raises(
                ObligationIntegrityError,
                match="obligation evidence differs",
            ):
                reconstruct_obligation_projection(db, projection)

            second = materialize_obligations(
                db,
                directive_id=projection.directive_id,
                proposal_id=projection.proposal_id,
                app_projection_id=projection.app_projection_id,
                actor=actor,
                membership_id=request.authorizing_membership_id,
                idempotency_key=request.idempotency_key,
            )
            db.commit()
            assert second.idempotent_retry is True
            assert db.scalar(select(func.count()).select_from(
                ADV4CandidateObligationProjectionEvent,
            ).where(
                ADV4CandidateObligationProjectionEvent.projection_id
                == projection.id,
            )) == 3
    finally:
        get_settings.cache_clear()
        engine.dispose()


def test_nonserialized_authority_and_restamped_ordinal_corruption_fails_closed():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(db).id

        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_requirements", trigger_ordinal=7,
            update_sql="""
                UPDATE ad_v4_candidate_obligation_requirements
                   SET sequence_value=2000 WHERE projection_id=:projection_id
            """,
            message="child count/numeric projection differs",
        )
        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_actions", trigger_ordinal=8,
            update_sql="""
                UPDATE ad_v4_candidate_obligation_actions
                   SET requirement_node_id=semantic_node_id
                 WHERE projection_id=:projection_id
            """,
            message="typed-owner parent differs",
        )
        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_expressions", trigger_ordinal=11,
            update_sql="""
                UPDATE ad_v4_candidate_obligation_expressions
                   SET context='recurrence_condition',expression_path='/forged'
                 WHERE projection_id=:projection_id
            """,
            message="expression ownership/arity differs",
        )
        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_evidence_links", trigger_ordinal=4,
            update_sql="""
                UPDATE ad_v4_candidate_obligation_evidence_links e
                   SET canonical_ordinal=100,
                       link_hash=encode(sha256(
                         convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
                         ||decode('00','hex')||convert_to(
                           paprnav_v4_obligation_record(jsonb_build_object(
                             'table','evidence-link','identity',jsonb_build_object(
                               'projectionId',e.projection_id,
                               'semanticNodeId',e.semantic_node_id,
                               'purpose',e.purpose,'evidenceKey',e.evidence_key,
                               'ordinal',100))),'UTF8')),'hex'),
                       id='aoe_'||substr(encode(sha256(
                         convert_to('paprnav:ad_extraction_v4:obligation-row:1','UTF8')
                         ||decode('00','hex')||convert_to(
                           paprnav_v4_obligation_record(jsonb_build_object(
                             'table','evidence-link','identity',jsonb_build_object(
                               'projectionId',e.projection_id,
                               'semanticNodeId',e.semantic_node_id,
                               'purpose',e.purpose,'evidenceKey',e.evidence_key,
                               'ordinal',100))),'UTF8')),'hex'),1,32)
                 WHERE e.id=(SELECT id
                   FROM ad_v4_candidate_obligation_evidence_links
                  WHERE projection_id=:projection_id LIMIT 1)
            """,
            message="evidence ordinal sequence differs",
        )
    finally:
        engine.dispose()


def test_disabled_gate_and_missing_or_forged_audit_envelope_fail_closed():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',false,'postgres-test')"
            ))
            db.commit()
            with pytest.raises(
                DBAPIError,
                match="request gate differs|parent/envelope differs",
            ):
                _persist_complete_graph(db)
            db.rollback()

        with Session(engine, expire_on_commit=False) as db:
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(db).id

        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_materialization_requests",
            trigger_ordinal=1,
            update_sql="""
                UPDATE ad_v4_candidate_obligation_materialization_requests
                   SET auth_claims_hash=repeat('0',64)
                 WHERE projection_id=:projection_id
            """,
            message="materialization request differs",
        )
        _assert_update_rejected(
            engine, projection_id=projection_id,
            table="ad_v4_candidate_obligation_projection_events",
            trigger_ordinal=23,
            update_sql="""
                DELETE FROM ad_v4_candidate_obligation_projection_events
                 WHERE projection_id=:projection_id
            """,
            message="projection event chain differs",
        )
    finally:
        engine.dispose()


def test_direct_request_guard_rechecks_all_gates_and_active_actor():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db)
            baseline = db.scalar(select(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            ))
            assert baseline is not None
            projection_id = projection.id
            baseline_values = {
                "actor_user_id": baseline.actor_user_id,
                "authorizing_membership_id": baseline.authorizing_membership_id,
                "organization_id": baseline.organization_id,
                "actor_role": baseline.actor_role,
                "actor_status": baseline.actor_status,
            }

        for gate_key in (
            "validator2_write_enabled", "materializer3a_enabled",
            "materializer3b_enabled",
        ):
            with Session(engine, expire_on_commit=False) as db:
                db.execute(text(
                    "SELECT paprnav_set_v4_feature_gate("
                    ":gate,false,'direct-request-regression')"
                ), {"gate": gate_key})
                db.commit()
                projection = db.get(
                    ADV4CandidateObligationProjection, projection_id,
                )
                values = _materialization_request_values(
                    projection,
                    **baseline_values,
                    idempotency_key=f"disabled-{gate_key}-{uuid.uuid4().hex}",
                )
                db.add(ADV4CandidateObligationMaterializationRequest(**values))
                with pytest.raises(DBAPIError, match="request gate differs"):
                    db.flush()
                db.rollback()
                db.execute(text(
                    "SELECT paprnav_set_v4_feature_gate("
                    ":gate,true,'direct-request-regression')"
                ), {"gate": gate_key})
                db.commit()

        with Session(engine, expire_on_commit=False) as db:
            db.execute(text(
                "UPDATE users SET status='inactive' WHERE id=:actor_id"
            ), {"actor_id": baseline_values["actor_user_id"]})
            db.commit()
            projection = db.get(
                ADV4CandidateObligationProjection, projection_id,
            )
            values = _materialization_request_values(
                projection,
                **baseline_values,
                idempotency_key=f"inactive-actor-{uuid.uuid4().hex}",
            )
            db.add(ADV4CandidateObligationMaterializationRequest(**values))
            with pytest.raises(DBAPIError, match="request authority differs"):
                db.flush()
            db.rollback()
            db.execute(text(
                "UPDATE users SET status='active' WHERE id=:actor_id"
            ), {"actor_id": baseline_values["actor_user_id"]})
            db.commit()
    finally:
        engine.dispose()


def test_direct_request_guard_prevents_root_proposal_lock_inversion():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db)
            baseline = db.scalar(select(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            ))
            assert baseline is not None
            projection_id = projection.id
            proposal_id = projection.proposal_id
            actor_id = baseline.actor_user_id
            membership_id = baseline.authorizing_membership_id
            baseline_values = {
                "actor_user_id": actor_id,
                "authorizing_membership_id": membership_id,
                "organization_id": baseline.organization_id,
                "actor_role": baseline.actor_role,
                "actor_status": baseline.actor_status,
            }

        entered = Event()

        def append_request() -> None:
            with Session(engine, expire_on_commit=False) as writer:
                writer.execute(text(
                    "SET LOCAL application_name='t081-direct-request-writer'"
                ))
                root = writer.get(
                    ADV4CandidateObligationProjection, projection_id,
                )
                values = _materialization_request_values(
                    root,
                    **baseline_values,
                    idempotency_key=f"lock-order-{uuid.uuid4().hex}",
                )
                writer.add(ADV4CandidateObligationMaterializationRequest(**values))
                entered.set()
                writer.flush()
                writer.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
                writer.rollback()

        with engine.connect() as blocker:
            transaction = blocker.begin()
            blocker.execute(text(
                "SELECT id FROM users WHERE id=:id FOR UPDATE"
            ), {"id": actor_id})
            blocker.execute(text(
                "SELECT id FROM organization_memberships WHERE id=:id FOR UPDATE"
            ), {"id": membership_id})
            blocker.execute(text(
                "SELECT id FROM ad_v4_candidate_proposals "
                "WHERE id=:id FOR UPDATE"
            ), {"id": proposal_id})
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(append_request)
                assert entered.wait(timeout=2)
                waiting = False
                for _ in range(100):
                    waiting = bool(blocker.scalar(text("""
                        SELECT EXISTS(
                          SELECT 1 FROM pg_stat_activity
                           WHERE application_name='t081-direct-request-writer'
                             AND wait_event_type='Lock')
                    """)))
                    if waiting:
                        break
                    time.sleep(0.01)
                assert waiting
                blocker.execute(text(
                    "SELECT id FROM ad_v4_candidate_obligation_projections "
                    "WHERE id=:id FOR UPDATE"
                ), {"id": projection_id})
                transaction.rollback()
                future.result(timeout=5)
    finally:
        engine.dispose()


def test_slice3b_correction_binding_commits_and_both_projection_validators_agree():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, with_correction=True)
            assert db.scalar(text("""
                SELECT count(*) FROM ad_v4_candidate_correction_semantic_bindings
                 WHERE obligation_projection_id=:projection_id
                   AND binding_slice='slice_3b' AND generation=1
            """), {"projection_id": projection.id}) == 1
            db.execute(text(
                "SELECT paprnav_v4_candidate_obligation_require_complete(:id)"
            ), {"id": projection.id})
            db.execute(text("""
                SELECT paprnav_v4_candidate_app_require_complete(app_projection_id)
                  FROM ad_v4_candidate_obligation_projections WHERE id=:id
            """), {"id": projection.id})
    finally:
        engine.dispose()


def test_slice3b_missing_or_restamped_misclassified_correction_binding_fails_closed():
    engine = _engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'postgres-test')"
            ))
            db.commit()
            projection_id = _persist_complete_graph(
                db, with_correction=True,
            ).id

        _assert_correction_mutation_rejected(
            engine, projection_id=projection_id,
            mutation_sql="""
                DELETE FROM ad_v4_candidate_correction_semantic_bindings
                 WHERE obligation_projection_id=:projection_id
                   AND binding_slice='slice_3b'
            """,
            message="obligation structural counts differ",
        )
        _assert_correction_mutation_rejected(
            engine, projection_id=projection_id,
            mutation_sql="""
                UPDATE ad_v4_candidate_correction_semantic_bindings b
                   SET obligation_semantic_node_id=n.id,
                       binding_hash=encode(sha256(
                         convert_to(
                           'paprnav:ad_extraction_v4:obligation-row:1','UTF8')
                         ||decode('00','hex')||convert_to(
                           paprnav_v4_obligation_record(jsonb_build_object(
                             'table','correction-binding','identity',
                             jsonb_build_object(
                               'refId',b.correction_ref_id,
                               'semanticId',n.id))),'UTF8')),'hex'),
                       id='avk_'||substr(encode(sha256(
                         convert_to(
                           'paprnav:ad_extraction_v4:obligation-row:1','UTF8')
                         ||decode('00','hex')||convert_to(
                           paprnav_v4_obligation_record(jsonb_build_object(
                             'table','correction-binding','identity',
                             jsonb_build_object(
                               'refId',b.correction_ref_id,
                               'semanticId',n.id))),'UTF8')),'hex'),1,32)
                  FROM ad_v4_candidate_obligation_semantic_nodes n
                 WHERE b.obligation_projection_id=:projection_id
                   AND b.binding_slice='slice_3b'
                   AND n.projection_id=:projection_id
                   AND n.node_type='action'
            """,
            message=(
                "correction foundation is incomplete|"
                "obligation correction binding differs"
            ),
        )
    finally:
        engine.dispose()


def test_obligation_database_catalog_matches_orm_and_trigger_registry():
    engine = _engine()
    try:
        inspector = inspect(engine)
        migration = importlib.import_module(
            "app.db.migrations.versions."
            "20260911_0028_add_ad_v4_obligations"
        )
        table_names = tuple(migration.OBLIGATION_TABLES)
        assert set(table_names) == {
            name for name in Base.metadata.tables
            if name.startswith("ad_v4_candidate_obligation_")
        }
        for table_name in table_names:
            model_table = Base.metadata.tables[table_name]
            catalog_columns = {
                row["name"]: row for row in inspector.get_columns(table_name)
            }
            assert set(catalog_columns) == {
                column.name for column in model_table.columns
            }
            for column in model_table.columns:
                assert catalog_columns[column.name]["nullable"] == column.nullable

            checks = inspector.get_check_constraints(table_name)
            unique_column_sets = {
                tuple(row["column_names"])
                for row in inspector.get_unique_constraints(table_name)
            }
            foreign_keys = {
                (
                    tuple(row["constrained_columns"]),
                    row["referred_table"],
                    tuple(row["referred_columns"]),
                )
                for row in inspector.get_foreign_keys(table_name)
            }
            expected_check_count = sum(
                isinstance(constraint, CheckConstraint)
                for constraint in model_table.constraints
            )
            assert len(checks) >= expected_check_count
            for constraint in model_table.constraints:
                if constraint.name is None:
                    continue
                if isinstance(constraint, CheckConstraint):
                    continue
                elif isinstance(constraint, UniqueConstraint):
                    assert tuple(
                        column.name for column in constraint.columns
                    ) in unique_column_sets
                elif isinstance(constraint, ForeignKeyConstraint):
                    elements = tuple(constraint.elements)
                    assert (
                        tuple(element.parent.name for element in elements),
                        elements[0].column.table.name,
                        tuple(element.column.name for element in elements),
                    ) in foreign_keys

            actual_indexes = {
                (tuple(row["column_names"]), bool(row["unique"]))
                for row in inspector.get_indexes(table_name)
            }
            for index in model_table.indexes:
                expected_columns = tuple(
                    column.name for column in index.columns
                )
                if index.unique:
                    assert (expected_columns, True) in actual_indexes
                else:
                        assert any(
                            actual_columns[:len(expected_columns)] == expected_columns
                            for actual_columns, _ in actual_indexes
                        ), (table_name, expected_columns, actual_indexes)

        with engine.connect() as connection:
            triggers = connection.execute(text("""
                SELECT c.relname,t.tgname
                  FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                 WHERE NOT t.tgisinternal AND c.relname=ANY(:tables)
            """), {"tables": list(table_names)}).all()
            by_table: dict[str, set[str]] = {}
            for table_name, trigger_name in triggers:
                by_table.setdefault(table_name, set()).add(trigger_name)
            for ordinal, table_name in enumerate(table_names):
                assert {
                    f"trg_aob_{ordinal}_immutable",
                    f"trg_aob_{ordinal}_dirty",
                    f"trg_aob_{ordinal}_complete",
                } <= by_table.get(table_name, set())
            correction_triggers = {
                row[0] for row in connection.execute(text("""
                    SELECT t.tgname FROM pg_trigger t
                    WHERE NOT t.tgisinternal
                      AND t.tgrelid=(
                        'ad_v4_candidate_correction_semantic_bindings'
                        ::regclass)
                """))
            }
            assert {
                "trg_ad_v4_candidate_correction_semantic_bindings_immutable",
                "trg_ad_v4_correction_binding_slice3a_insert_complete",
                "trg_ad_v4_correction_binding_slice3a_update_complete",
                "trg_ad_v4_correction_binding_slice3a_delete_complete",
                "trg_aob_correction_insert_complete",
                "trg_aob_correction_update_complete",
                "trg_aob_correction_delete_complete",
            } <= correction_triggers
            assert connection.scalar(text(
                "SELECT paprnav_v4_obligation_mapping_digest()"
            )) == MAPPING_DIGEST
    finally:
        engine.dispose()


def test_downgrade_root_first_lock_order_refuses_without_deadlock():
    engine = _engine()
    process = None
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'downgrade-lock-test')"
            ))

        with engine.connect() as writer:
            transaction = writer.begin()
            try:
                writer.execute(text(
                    "LOCK TABLE ad_v4_candidate_obligation_projections "
                    "IN ROW EXCLUSIVE MODE"
                ))
                environment = os.environ.copy()
                application_name = f"t081-s3b-downgrade-{uuid.uuid4().hex}"
                query_separator = "&" if "?" in POSTGRES_URL else "?"
                environment["DATABASE_URL"] = (
                    f"{POSTGRES_URL}{query_separator}"
                    f"application_name={application_name}"
                )
                process = subprocess.Popen(
                    [
                        sys.executable, "-m", "alembic", "downgrade",
                        "20260907_0027",
                    ],
                    cwd=Path(__file__).resolve().parents[1],
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                waiting_on_root = False
                observed_waits = []
                with engine.connect().execution_options(
                    isolation_level="AUTOCOMMIT",
                ) as observer:
                    for _ in range(100):
                        observed_waits = observer.execute(text("""
                            SELECT activity.application_name,
                                   left(activity.query,120),waiting.locktype,
                                   waiting.relation::regclass::text,
                                   waiting.mode,waiting.granted
                            FROM pg_stat_activity activity
                            JOIN pg_locks waiting
                              ON waiting.pid=activity.pid
                           WHERE activity.datname=current_database()
                             AND NOT waiting.granted
                        """)).all()
                        waiting_on_root = observer.scalar(text("""
                            SELECT EXISTS (
                              SELECT 1
                                FROM pg_stat_activity activity
                                   JOIN pg_locks waiting
                                      ON waiting.pid=activity.pid
                                   WHERE activity.datname=current_database()
                                     AND activity.application_name=
                                       :application_name
                                     AND waiting.locktype='relation'
                                 AND waiting.relation=(
                                   'ad_v4_candidate_obligation_projections'
                                   ::regclass)
                                     AND waiting.mode='AccessExclusiveLock'
                                     AND NOT waiting.granted)
                        """), {"application_name": application_name})
                        if waiting_on_root:
                            break
                        if process.poll() is not None:
                            stdout, stderr = process.communicate()
                            pytest.fail(
                                "downgrade exited before reaching the root lock: "
                                + repr(observed_waits) + stdout + stderr
                            )
                        time.sleep(0.05)
                assert waiting_on_root, (
                    "downgrade was not observed waiting on the projection root"
                )

                # A parent-first downgrade cannot already hold this child lock
                # while it waits for the writer's root lock.
                writer.execute(text("SET LOCAL lock_timeout='1s'"))
                writer.execute(text(
                    "LOCK TABLE ad_v4_candidate_correction_semantic_bindings "
                    "IN ROW EXCLUSIVE MODE"
                ))
            finally:
                transaction.rollback()

        assert process is not None
        stdout, stderr = process.communicate(timeout=20)
        combined = stdout + stderr
        assert process.returncode != 0
        assert "materializer3b gate is enabled" in combined
        assert "40P01" not in combined
        assert "deadlock detected" not in combined
        with engine.connect() as connection:
            assert connection.scalar(text(
                "SELECT version_num FROM alembic_version"
            )) == "20260911_0028"
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            process.communicate(timeout=5)
        engine.dispose()


@pytest.mark.parametrize(
    ("route_kind", "transition_kind"),
    (
        ("detail", "evidence_lifecycle"),
        ("detail", "candidate_relationship"),
        ("detail", "parent_app_stale"),
        ("reconstruction", "evidence_lifecycle"),
        ("reconstruction", "candidate_relationship"),
        ("reconstruction", "parent_app_stale"),
        ("list", "evidence_lifecycle"),
        ("list", "candidate_relationship"),
        ("list", "parent_app_stale"),
    ),
)
def test_get_snapshot_is_wholly_before_concurrent_verified_transition(
    route_kind: str, transition_kind: str, monkeypatch: pytest.MonkeyPatch,
):
    engine = _engine()
    try:
        os.environ["PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED"] = "true"
        get_settings.cache_clear()
        with Session(engine, expire_on_commit=False) as db:
            _enable(db)
            db.execute(text(
                "SELECT paprnav_set_v4_feature_gate("
                "'materializer3b_enabled',true,'snapshot-test')"
            ))
            db.commit()
            projection = _persist_complete_graph(db, via_service=True)
            request = db.scalar(select(
                ADV4CandidateObligationMaterializationRequest,
            ).where(
                ADV4CandidateObligationMaterializationRequest.projection_id
                == projection.id,
            ))
            binding = db.scalar(select(ADV4CandidateEvidenceBinding).where(
                ADV4CandidateEvidenceBinding.proposal_id == projection.proposal_id,
            ))
            admitted = db.get(
                ADEvidenceFragmentLifecycleEvent, binding.admitted_event_id,
            )
            assert request is not None and binding is not None and admitted is not None
            actor_id = request.actor_user_id
            membership_id = request.authorizing_membership_id
            proposal_id = projection.proposal_id
            app_projection_id = projection.app_projection_id
            fragment_id = binding.fragment_id
            directive_id = projection.directive_id
            actor_snapshot = db.get(User, actor_id)
            assert actor_snapshot is not None

        def append_quarantine(
            writer: Session, reason: str, *, commit: bool = True,
        ) -> None:
            fragment = writer.get(ADEvidenceFragment, fragment_id)
            root = writer.get(ADEvidenceFragmentLifecycleEvent, admitted.id)
            assert fragment is not None and root is not None
            writer.add(ADEvidenceFragmentLifecycleEvent(
                fragment_id=fragment.id,
                event_type="quarantined",
                actor_user_id=actor_id,
                reason=reason,
                sequence_number=1,
                predecessor_event_hash=root.event_hash,
                event_hash=_hash_parts(
                    fragment.id, fragment.fragment_hash, "quarantined",
                    actor_id, reason, 1, root.event_hash,
                ),
            ))
            if commit:
                writer.commit()

        if transition_kind == "evidence_lifecycle":
            count_sql = (
                "SELECT count(*) FROM ad_evidence_fragment_lifecycle_events "
                "WHERE fragment_id=:target"
            )
            target = fragment_id

            def transition() -> None:
                with Session(engine) as writer:
                    append_quarantine(writer, f"{route_kind} snapshot quarantine")

        elif transition_kind == "candidate_relationship":
            count_sql = (
                "SELECT count(*) FROM ad_v4_candidate_submission_relationships "
                "WHERE predecessor_proposal_id=:target"
            )
            target = proposal_id

            def transition() -> None:
                with Session(engine) as writer:
                    proposal = writer.get(ADV4CandidateProposal, proposal_id)
                    actor = writer.get(User, actor_id)
                    assert proposal is not None and actor is not None
                    corrected = deepcopy(proposal.parsed_json)
                    corrected["decisionKey"] = (
                        f"{corrected['decisionKey']}-snapshot-correction"
                    )
                    evidence_key = sorted(corrected["evidenceBindings"])[0]
                    parsed = parse_v4_request_bytes(json.dumps({
                        "proposal": corrected,
                        "submissionContext": {"relationships": [{
                            "relationshipKey": "snapshot-corrects-parent",
                            "relationType": "corrects_candidate",
                            "predecessorProposalId": proposal_id,
                            "reason": "snapshot relationship transition",
                            "evidenceKeys": [evidence_key],
                        }]},
                    }, separators=(",", ":")).encode())
                    store_v4_candidate(
                        writer,
                        directive_id=proposal.directive_id,
                        parsed=parsed,
                        actor=actor,
                        membership_id=membership_id,
                        idempotency_key=f"snapshot-correction-{uuid.uuid4().hex}",
                        validator_version=VALIDATOR_VERSION_V2,
                    )
                    writer.commit()

        else:
            count_sql = (
                "SELECT count(*) FROM ad_v4_candidate_app_projection_events "
                "WHERE projection_id=:target AND event_type='stale_marked'"
            )
            target = app_projection_id

            def transition() -> None:
                with Session(engine) as writer:
                    append_quarantine(
                        writer, f"{route_kind} parent snapshot quarantine",
                        commit=False,
                    )
                    root = writer.get(
                        ADV4CandidateObligationProjection, projection.id,
                    )
                    actor = writer.get(User, actor_id)
                    assert root is not None and actor is not None
                    materialize_obligations(
                        writer,
                        directive_id=root.directive_id,
                        proposal_id=root.proposal_id,
                        app_projection_id=root.app_projection_id,
                        actor=actor,
                        membership_id=membership_id,
                        idempotency_key=f"snapshot-stale-{uuid.uuid4().hex}",
                    )
                    writer.commit()

        with engine.connect() as connection:
            before = connection.scalar(text(count_sql), {"target": target})

        snapshot_ready = Event()
        writer_done = Event()
        original_authorize = ads_routes.authorize_obligation_audit

        def paused_authorize(read_db, current_user, acting_membership_id):
            result = original_authorize(
                read_db, current_user, acting_membership_id,
            )
            snapshot_ready.set()
            assert writer_done.wait(timeout=10)
            return result

        monkeypatch.setattr(
            ads_routes, "authorize_obligation_audit", paused_authorize,
        )

        def call_route():
            with Session(engine) as outer_db:
                if route_kind == "detail":
                    return ads_routes.get_v4_obligation_projection(
                        directive_id,
                        proposal_id,
                        acting_membership_id=membership_id,
                        current_user=actor_snapshot,
                        db=outer_db,
                    )
                if route_kind == "reconstruction":
                    return ads_routes.get_v4_obligation_reconstruction(
                        directive_id,
                        proposal_id,
                        acting_membership_id=membership_id,
                        current_user=actor_snapshot,
                        db=outer_db,
                    )
                return ads_routes.list_v4_obligation_projections(
                    directive_id,
                    limit=50,
                    offset=0,
                    acting_membership_id=membership_id,
                    current_user=actor_snapshot,
                    db=outer_db,
                )

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(call_route)
            assert snapshot_ready.wait(timeout=10)
            try:
                transition()
            finally:
                writer_done.set()
            response = future.result(timeout=20)
        if route_kind == "list":
            assert response.total >= 1
        else:
            assert response.projectionId == projection.id

        with pytest.raises(HTTPException) as after_transition:
            call_route()
        assert after_transition.value.status_code == 409

        with repeatable_read_only_session(engine) as read_db:
            with pytest.raises(DBAPIError, match="read-only transaction"):
                read_db.execute(text(
                    "UPDATE ad_v4_feature_gates SET changed_by='forbidden-read' "
                    "WHERE gate_key='materializer3b_enabled'"
                ))

        with engine.connect() as connection:
            assert connection.scalar(
                text(count_sql), {"target": target},
            ) > before
    finally:
        get_settings.cache_clear()
        engine.dispose()
