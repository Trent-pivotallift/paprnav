from __future__ import annotations

import json
import copy
import hashlib
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.core import (
    ADV4CandidateAppProjection,
    ADV4CandidateAppChangeDependency,
    ADV4CandidateAppCondition,
    ADV4CandidateAppDatum,
    ADV4CandidateAppDesignationGroup,
    ADV4CandidateAppDesignationGroupMember,
    ADV4CandidateAppEvidenceLink,
    ADV4CandidateAppExpression,
    ADV4CandidateAppExpressionEdge,
    ADV4CandidateAppProjectionEvent,
    ADV4CandidateAppDesignationValue,
    ADV4CandidateAppIdentityMapping,
    ADV4CandidateAppProductScope,
    ADV4CandidateAppRule,
    ADV4CandidateAppRuleExclusion,
    ADV4CandidateAppSearchHint,
    ADV4CandidateAppSearchHintGroup,
    ADV4CandidateAppSearchHintMember,
    ADV4CandidateAppSemanticNode,
    ADV4CandidateAppValueAssertion,
    ADV4CandidateEvidenceBinding,
    ADV4CandidateProposal,
    ADV4CandidateCorrection,
    User,
)
from app.services.ad_v4_applicability import EVENT_DOMAIN, PROJECTION_DOMAIN, SUBTREE_DOMAIN, _row_id, materialize_applicability, reconstruct_applicability
from app.services.ad_v4_candidates import DOMAINS_V2, VALIDATOR_VERSION, VALIDATOR_VERSION_V2, parse_v4_request_bytes, store_v4_candidate
from app.services.ad_v4_candidates import CANONICALIZATION_VERSION_V2, canonical_bytes
from test_ad_v4_postgres import _request, _seed


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="PAPRNAV_TEST_POSTGRES_URL required")


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = POSTGRES_URL or ""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args], cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment, text=True, capture_output=True, timeout=25, check=False,
    )


def _engine():
    return create_engine(
        POSTGRES_URL,
        pool_pre_ping=True,
        pool_timeout=5,
        connect_args={"connect_timeout": 5, "options": "-c statement_timeout=10000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000"},
    )


def _enable(db: Session) -> None:
    db.execute(text("SELECT paprnav_set_v4_feature_gate('validator2_write_enabled',true,'postgres-test')"))
    db.execute(text("SELECT paprnav_set_v4_feature_gate('materializer3a_enabled',true,'postgres-test')"))
    db.commit()
    os.environ["PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED"] = "true"
    os.environ["PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED"] = "true"
    get_settings.cache_clear()


def _store(
    db: Session,
    *,
    validator_version: str,
    suffix: str,
    listed_designation: bool = False,
    ad_number: str = "2024-14-03",
    supersession_relations: list[dict] | None = None,
    typed_scope_shapes: bool = False,
    listed_non_model: bool = False,
    condition_matrix: bool = False,
    rule_matrix: bool = False,
    hint_matrix: bool = False,
    dual_evidence: bool = False,
):
    user_id, membership_id, directive_id, document_id, source_hash, fragment_id, fragment_hash = _seed(
        db, ad_number=ad_number,
    )
    actor = db.get(User, user_id)
    parsed = _request(
        directive_id, document_id, source_hash, fragment_id, fragment_hash,
        decision_key=f"decision-{suffix}",
        listed_designation=listed_designation,
        ad_number=ad_number,
        supersession_relations=supersession_relations,
        typed_scope_shapes=typed_scope_shapes,
        listed_non_model=listed_non_model,
        extra_binding=(fragment_id, fragment_hash) if dual_evidence else None,
    )
    if condition_matrix:
        proposal = parsed.value["proposal"]
        context_evidence = ["ev-official"]
        occurrence_evidence = ["ev-secondary"] if dual_evidence else context_evidence
        conditions = []
        condition_types = [
            "identity", "identifier_range", "installed_equipment",
            "modification_or_stc", "configuration_attribute",
            "temporal_overlap", "source_inclusion", "source_exclusion",
            "reviewed_manual_predicate",
        ]
        operators = [
            "identity_equals", "identity_in", "identifier_in_range",
            "is_installed", "is_not_installed", "equals", "overlaps",
            "includes", "excludes", "requires_review",
        ]
        for type_index, condition_type in enumerate(condition_types):
            for operator_index, operator in enumerate(operators):
                conditions.append({
                    "conditionKey": f"condition-pair-{type_index:02d}-{operator_index:02d}",
                    "conditionType": condition_type, "operator": operator,
                    "subject": {
                        "attributeKey": "matrix-value",
                        "attributeValue": {
                            "state": "known",
                            "value": f"pair-{type_index:02d}-{operator_index:02d}",
                            "evidenceKeys": occurrence_evidence,
                        },
                    },
                    "temporalBasis": {"kind": "at_applicability_evaluation"},
                    "evidenceKeys": context_evidence,
                })
        fields = [
            "manufacturer", "modelOrSeries", "partNumber", "serialNumber",
            "stcNumber", "attributeValue",
        ]
        for field_index, field in enumerate(fields):
            for state_index, state in enumerate(("known", "unknown", "not_applicable")):
                union = {"state": state, "evidenceKeys": occurrence_evidence}
                if state == "known":
                    union["value"] = f"known-{field}-{field_index}"
                else:
                    union["reason"] = "not_observed" if state == "unknown" else (
                        "n" * 512 if field == "attributeValue" else f"not-applicable-{field}"
                    )
                    union["temporalScope"] = {"kind": "directive_version"}
                conditions.append({
                    "conditionKey": f"condition-union-{field_index:02d}-{state_index}",
                    "conditionType": "identity", "operator": "identity_equals",
                    "subject": {field: union},
                    "temporalBasis": {"kind": "directive_version"},
                    "comparatorVersion": "source-comparator-v1",
                    "evidenceKeys": context_evidence,
                })
        associations = ["all_members", "any_member", "source_group", "unknown"]
        display_states = ["known", "unknown", "not_applicable", "known"]
        manufacturer_states = ["known", "unknown", "not_applicable", "known"]

        def known_string(state: str, value: str) -> dict:
            if state == "known":
                return {"state": "known", "value": value, "evidenceKeys": occurrence_evidence}
            return {
                "state": state,
                "reason": "not_observed" if state == "unknown" else f"not-applicable-{value}",
                "temporalScope": {"kind": "source_observation"},
                "evidenceKeys": occurrence_evidence,
            }

        for group_index, association in enumerate(associations):
            group = {
                "groupKey": f"condition-group-{group_index}",
                "sourceDisplayText": known_string(display_states[group_index], f"display-{group_index}"),
                "association": association,
                "members": [
                    {
                        "memberKey": f"member-{group_index}-model",
                        "designationKind": "model",
                        "sourceDesignation": f"Model {group_index}",
                        "manufacturer": known_string(manufacturer_states[group_index], f"Maker {group_index}"),
                        "evidenceKeys": occurrence_evidence,
                    },
                    {
                        "memberKey": f"member-{group_index}-series",
                        "designationKind": "series_expression",
                        "expressionText": f"Series {group_index}A through {group_index}Z",
                        "evaluationState": "unknown",
                        "reason": "unsupported_expression",
                        "manufacturer": known_string(manufacturer_states[(group_index + 1) % 4], f"Series Maker {group_index}"),
                        "evidenceKeys": occurrence_evidence,
                    },
                ],
                "evidenceKeys": context_evidence,
            }
            if association == "unknown":
                group["reason"] = "source_ambiguous"
                group["temporalScope"] = {"kind": "source_observation"}
            conditions.append({
                "conditionKey": f"condition-group-{group_index}",
                "conditionType": "identity", "operator": "identity_in",
                "subject": {"productRole": "airframe", "designationGroup": group},
                "temporalBasis": {"kind": "source_observation"},
                "evidenceKeys": context_evidence,
            })
        proposal["conditionDefinitions"] = sorted(
            conditions, key=lambda item: item["conditionKey"],
        )
        parsed = parse_v4_request_bytes(json.dumps(parsed.value, separators=(",", ":")).encode())
    if rule_matrix:
        proposal = parsed.value["proposal"]
        proposal["conditionDefinitions"] = [{
            "conditionKey": "condition-rule", "conditionType": "identity",
            "operator": "identity_equals",
            "subject": {
                "attributeKey": "configuration", "attributeValue": {
                    "state": "known", "value": "configured",
                    "evidenceKeys": ["ev-official"],
                },
            },
            "temporalBasis": {"kind": "at_applicability_evaluation"},
            "evidenceKeys": ["ev-official"],
        }]
        deep_scope: dict = {
            "nodeType": "all", "operands": [
                {"nodeType": "scope_ref", "scopeKey": "scope-main"},
                {"nodeType": "scope_ref", "scopeKey": "scope-main"},
            ],
        }
        for _ in range(34):
            deep_scope = {"nodeType": "not", "operand": deep_scope}
        proposal["applicabilityRules"] = [
            {
                "ruleKey": "rule-base",
                "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"},
                "exclusionRuleKeys": [], "evidenceKeys": ["ev-official"],
            },
            {
                "ruleKey": "rule-complex", "scopeExpression": deep_scope,
                "conditionExpression": {
                    "nodeType": "any", "operands": [
                        {"nodeType": "predicate_ref", "conditionKey": "condition-rule"},
                        {"nodeType": "not", "operand": {
                            "nodeType": "predicate_ref", "conditionKey": "condition-rule",
                        }},
                        {"nodeType": "rule_ref", "ruleKey": "rule-base"},
                    ],
                },
                "exclusionRuleKeys": ["rule-base", "rule-terminal"],
                "evidenceKeys": ["ev-official"],
            },
            {
                "ruleKey": "rule-terminal",
                "scopeExpression": {"nodeType": "scope_ref", "scopeKey": "scope-main"},
                "exclusionRuleKeys": [], "evidenceKeys": ["ev-official"],
            },
        ]
        proposal["requirements"][0]["activationExpression"] = {
            "nodeType": "rule_ref", "ruleKey": "rule-complex",
        }
        parsed = parse_v4_request_bytes(json.dumps(parsed.value, separators=(",", ":")).encode())
    if hint_matrix:
        proposal = parsed.value["proposal"]
        states = ("known", "unknown", "not_applicable")
        roles = ("airframe", "engine", "propeller", "appliance", "installed_part", "modification")

        def hint_string(state: str, label: str, *, long_reason: bool = False) -> dict:
            if state == "known":
                return {"state": "known", "value": label, "evidenceKeys": ["ev-official"]}
            return {
                "state": state,
                "reason": "not_observed" if state == "unknown" else ("h" * 512 if long_reason else f"not-applicable-{label}"),
                "temporalScope": {"kind": "source_observation"},
                "evidenceKeys": ["ev-official"],
            }

        hints = []
        for index, role in enumerate(roles):
            association = ("paired", "source_group", "unknown")[index % 3]
            group = {
                "groupKey": f"hint-group-{index}",
                "manufacturer": hint_string(states[index % 3], f"Group Maker {index}"),
                "association": association,
                "members": [
                    {
                        "memberKey": f"hint-member-{index}-model",
                        "designationKind": "model",
                        "sourceDesignation": f"Model {index}",
                        "manufacturer": hint_string(states[(index + 1) % 3], f"Model Maker {index}"),
                        "evidenceKeys": ["ev-official"],
                    },
                    {
                        "memberKey": f"hint-member-{index}-series",
                        "designationKind": "series_expression",
                        "expressionText": f"Series {index}A through {index}Z",
                        "evaluationState": "unknown",
                        "reason": "unsupported_expression",
                        "manufacturer": hint_string(
                            states[(index + 2) % 3], f"Series Maker {index}",
                            long_reason=index == 0,
                        ),
                        "evidenceKeys": ["ev-official"],
                    },
                ],
                "evidenceKeys": ["ev-official"],
            }
            if association == "unknown":
                group["reason"] = "source_ambiguous"
                group["temporalScope"] = {"kind": "source_observation"}
            hints.append({
                "hintKey": f"hint-{index}-{role.replace('_', '-')}", "productRole": role,
                "sourceDisplayText": hint_string(states[index % 3], f"Hint display {index}"),
                "manufacturerModelGroups": [group],
                "controlling": False, "exhaustive": False,
                "evidenceKeys": ["ev-official"],
            })
        proposal["applicabilitySearchHints"] = sorted(hints, key=lambda item: item["hintKey"])
        parsed = parse_v4_request_bytes(json.dumps(parsed.value, separators=(",", ":")).encode())
    stored = store_v4_candidate(
        db, directive_id=directive_id,
        parsed=parsed,
        actor=actor, membership_id=membership_id, idempotency_key=f"candidate-{suffix}",
        validator_version=validator_version,
    )
    db.commit()
    return user_id, membership_id, directive_id, stored.proposal.id


def _materialize_stored(
    db: Session,
    *,
    validator_version: str,
    suffix: str,
    listed_designation: bool = False,
    ad_number: str = "2024-14-03",
    supersession_relations: list[dict] | None = None,
    typed_scope_shapes: bool = False,
    listed_non_model: bool = False,
    condition_matrix: bool = False,
    rule_matrix: bool = False,
    hint_matrix: bool = False,
    dual_evidence: bool = False,
):
    user_id, membership_id, directive_id, proposal_id = _store(
        db,
        validator_version=validator_version,
        suffix=suffix,
        listed_designation=listed_designation,
        ad_number=ad_number,
        supersession_relations=supersession_relations,
        typed_scope_shapes=typed_scope_shapes,
        listed_non_model=listed_non_model,
        condition_matrix=condition_matrix,
        rule_matrix=rule_matrix,
        hint_matrix=hint_matrix,
        dual_evidence=dual_evidence,
    )
    result = materialize_applicability(
        db,
        directive_id=directive_id,
        proposal_id=proposal_id,
        actor=db.get(User, user_id),
        membership_id=membership_id,
        idempotency_key=f"materialize-{suffix}",
    )
    db.commit()
    return result.projection


def test_00_empty_upgrade_and_v1_only_downgrade_reupgrade() -> None:
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode == 0, down.stdout + down.stderr
    up = _alembic("upgrade", "20260907_0027")
    assert up.returncode == 0, up.stdout + up.stderr
    engine = _engine()
    with Session(engine) as db:
        _store(db, validator_version=VALIDATOR_VERSION, suffix="v1-only")
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode == 0, down.stdout + down.stderr
    up = _alembic("upgrade", "20260907_0027")
    assert up.returncode == 0, up.stdout + up.stderr
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_proposals WHERE validator_version='paprnav-ad-v4-validator-1'")) == 1
    engine.dispose()


def test_01_v2_empty_projection_downgrade_refusal_preserves_head() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="v2-downgrade-refusal")
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode != 0
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260907_0027"
        assert connection.scalar(text("SELECT count(*) FROM ad_v4_candidate_app_projections")) == 0
    engine.dispose()


def test_02_projection_integrity_immutability_and_occupied_downgrade() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="projection")
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
            membership_id=membership_id, idempotency_key="materialize-projection",
        )
        db.commit()
        assert reconstruct_applicability(db, result.projection)["productScopes"]
        projection_id = result.projection.id
        with pytest.raises(DBAPIError):
            db.execute(text("UPDATE ad_v4_candidate_app_projections SET gate='released' WHERE id=:id"), {"id": projection_id})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_projections
              SELECT 'avx_forged',repeat('f',64),proposal_id,directive_id,schema_version,
                     validator_version,canonicalization_version,repeat('0',64),evidence_binding_hash,
                     materializer_version,applicability_subtree_bytes,applicability_subtree_hash,
                     projection_canonical_bytes,projection_hash,gate,semantic_node_count,datum_count,
                     evidence_link_count,identity_mapping_count,now()
                FROM ad_v4_candidate_app_projections WHERE id=:id
            """), {"id": projection_id})
            db.commit()
        db.rollback()
        other = db.scalar(select(ADV4CandidateProposal).where(ADV4CandidateProposal.validator_version == VALIDATOR_VERSION))
        node = db.scalar(select(ADV4CandidateAppSemanticNode).where(ADV4CandidateAppSemanticNode.projection_id == projection_id))
        with pytest.raises(DBAPIError):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_data
                (id,projection_id,proposal_id,semantic_node_id,json_pointer,parent_pointer,property_name,array_ordinal,value_kind,string_value,boolean_value,value_hash)
              VALUES ('avd_cross',:projection,:proposal,:node,'/forged','', 'forged',NULL,'string','x',NULL,repeat('0',64))
            """), {"projection": projection_id, "proposal": other.id, "node": node.id})
            db.commit()
        db.rollback()
    down = _alembic("downgrade", "20260901_0026")
    assert down.returncode != 0
    engine.dispose()


def test_03_concurrent_retry_and_gate_disable_serialize_without_partial_rows() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(db, validator_version=VALIDATOR_VERSION_V2, suffix="concurrent")
    barrier = threading.Barrier(2)

    def write():
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            value = materialize_applicability(
                db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
                membership_id=membership_id, idempotency_key="same-materialization",
            )
            db.commit()
            return value.projection.id

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = [future.result(timeout=15) for future in [pool.submit(write), pool.submit(write)]]
    assert len(set(ids)) == 1
    with SessionLocal() as db:
        assert db.scalar(
            select(text("count(*)")).select_from(ADV4CandidateAppProjection).where(
                ADV4CandidateAppProjection.proposal_id == proposal_id
            )
        ) == 1
        db.execute(text("SELECT paprnav_set_v4_feature_gate('validator2_write_enabled',false,'postgres-test-disable')"))
        db.commit()
        with pytest.raises(Exception):
            materialize_applicability(
                db, directive_id=directive_id, proposal_id=proposal_id, actor=db.get(User, user_id),
                membership_id=membership_id, idempotency_key="disabled-after-existing",
            )
    engine.dispose()


def test_04_valid_projection_root_without_children_is_rejected_at_commit() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="empty-graph",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="capture-valid-root",
        )
        db.flush()
        root_values = {
            column.name: getattr(result.projection, column.name)
            for column in ADV4CandidateAppProjection.__table__.columns
        }
        db.rollback()

        db.execute(ADV4CandidateAppProjection.__table__.insert().values(**root_values))
        with pytest.raises(DBAPIError, match="relational graph is incomplete"):
            db.commit()
        db.rollback()
        assert db.get(ADV4CandidateAppProjection, root_values["id"]) is None
    engine.dispose()


def test_05_extra_relational_child_is_rejected_by_deferred_validation() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="extra-child",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="extra-child-projection",
        )
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_data
            (id,projection_id,proposal_id,semantic_node_id,json_pointer,
             parent_pointer,property_name,array_ordinal,value_kind,string_value,
             boolean_value,value_hash)
          VALUES
            ('avd_extra',:projection,:proposal,NULL,'/forged','',
             'forged',NULL,'string','forged',NULL,repeat('0',64))
        """), {"projection": result.projection.id, "proposal": proposal_id})
        with pytest.raises(DBAPIError, match="relational graph is incomplete"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    engine.dispose()


def test_06_forged_semantic_identity_is_rejected_by_deferred_validation() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="semantic-forgery",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="semantic-forgery-projection",
        )
        node = db.scalar(select(ADV4CandidateAppSemanticNode).where(
            ADV4CandidateAppSemanticNode.projection_id == result.projection.id
        ))
        projection_id = result.projection.id
        node_id = node.id
        db.commit()
        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_semantic_nodes "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_semantic_nodes_immutable"
        ))
        db.execute(text(
            "UPDATE ad_v4_candidate_app_semantic_nodes SET node_key='forged' WHERE id=:id"
        ), {"id": node_id})
        with pytest.raises(DBAPIError, match="semantic node differs"):
            db.execute(
                text("SELECT paprnav_v4_candidate_app_require_complete(:projection)"),
                {"projection": projection_id},
            )
        db.rollback()
    engine.dispose()


def test_07_listed_designation_semantic_nodes_commit_and_verify() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="listed-designation", listed_designation=True,
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="listed-designation-projection",
        )
        db.commit()
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppSemanticNode
        ).where(
            ADV4CandidateAppSemanticNode.projection_id == result.projection.id,
            ADV4CandidateAppSemanticNode.node_type == "designation_value",
        )) == 2
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppDesignationValue
        ).where(ADV4CandidateAppDesignationValue.projection_id == result.projection.id)) == 2
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppIdentityMapping
        ).where(ADV4CandidateAppIdentityMapping.projection_id == result.projection.id)) == 2
        assert reconstruct_applicability(db, result.projection)["productScopes"][0]["modelScope"]["sourceDesignations"] == [
            "Model 100", "Model 200",
        ]
    engine.dispose()


def test_14_typed_product_owner_tamper_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="typed-owner-tamper", listed_designation=True,
        )
        product = db.scalar(select(ADV4CandidateAppProductScope).where(
            ADV4CandidateAppProductScope.projection_id == projection.id
        ))
        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_product_scopes "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_product_scopes_immutable"
        ))
        db.execute(text(
            "UPDATE ad_v4_candidate_app_product_scopes SET product_role='engine' "
            "WHERE semantic_node_id=:node"
        ), {"node": product.semantic_node_id})
        with pytest.raises(DBAPIError, match="product-scope owner graph differs"):
            db.execute(
                text("SELECT paprnav_v4_candidate_app_require_complete(:projection)"),
                {"projection": projection.id},
            )
        db.rollback()
    engine.dispose()


def test_15_product_manufacturer_range_and_series_owners_commit() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="typed-scope-shapes", listed_designation=True,
            typed_scope_shapes=True,
        )
        reconstructed = reconstruct_applicability(db, projection)
        product = reconstructed["productScopes"][0]
        assert product["manufacturer"]["sourceValue"] == "Example Aircraft"
        assert product["serialScope"]["ranges"][0]["upperInclusive"] is False
        assert product["partNumberScope"]["expression"] == "PN-10 through PN-19"
        assert db.scalar(text(
            "SELECT count(*) FROM ad_v4_candidate_app_value_assertions WHERE projection_id=:p"
        ), {"p": projection.id}) == 1
        assert db.scalar(text(
            "SELECT count(*) FROM ad_v4_candidate_app_designation_ranges WHERE projection_id=:p"
        ), {"p": projection.id}) == 1
    engine.dispose()


def test_16_listed_serial_and_part_values_are_not_model_identities() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="listed-non-model", listed_designation=True,
            listed_non_model=True,
        )
        values = db.scalars(select(ADV4CandidateAppDesignationValue).where(
            ADV4CandidateAppDesignationValue.projection_id == projection.id
        )).all()
        assert len(values) == 6
        assert sum(value.identity_mapping_node_id is not None for value in values) == 2
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppIdentityMapping
        ).where(ADV4CandidateAppIdentityMapping.projection_id == projection.id)) == 2
        assert reconstruct_applicability(db, projection)["productScopes"][0]["serialScope"]["sourceDesignations"] == ["SN-100", "SN-200"]
        model_mapping = db.scalar(select(ADV4CandidateAppIdentityMapping).where(
            ADV4CandidateAppIdentityMapping.projection_id == projection.id
        ))
        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_identity_mappings "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_identity_mappings_immutable"
        ))
        db.execute(text(
            "UPDATE ad_v4_candidate_app_identity_mappings SET identity_kind='series' WHERE id=:id"
        ), {"id": model_mapping.id})
        with pytest.raises(DBAPIError, match="identity-mapping identity differs|designation-value owner graph differs"):
            db.execute(
                text("SELECT paprnav_v4_candidate_app_require_complete(:projection)"),
                {"projection": projection.id},
            )
        db.rollback()
    engine.dispose()


def test_08_negative_correction_ordinal_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        _, _, _, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2, suffix="negative-correction-ordinal",
        )
        db.add(ADV4CandidateCorrection(
            id="avc_negative", identity_hash="a" * 64, proposal_id=proposal_id,
            correction_key="negative", correction_type="official_correction",
            original_document_ref_key="official-rule",
            correcting_document_ref_key="official-rule",
            original_document_identity_hash="b" * 64,
            correcting_document_identity_hash="b" * 64,
            canonical_hash="c" * 64, canonical_ordinal=-1,
            foundation_version="paprnav-ad-v4-correction-foundation-1",
            generation=1, expected_ref_count=0, expected_evidence_count=0,
        ))
        with pytest.raises(DBAPIError, match="ordinal_nonnegative"):
            db.flush()
        db.rollback()
    engine.dispose()


def test_09_exact_supersession_creates_target_local_cause_and_stale_event() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        predecessor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="supersession-predecessor", ad_number="2020-01-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="supersession-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-01-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "outgoing_supersedes",
        ))
        incoming = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "incoming_supersession_signal",
        ))
        event = db.scalar(select(ADV4CandidateAppProjectionEvent).where(
            ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
            ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
        ))
        assert outgoing is not None and incoming is not None and event is not None
        assert outgoing.resolution_state == "resolved_candidate"
        assert outgoing.target_projection_id == predecessor.id
        assert incoming.source_dependency_id == outgoing.id
        assert event.causing_dependency_id == incoming.id
        assert event.reason_code == "candidate_supersession_signal"
        reconstruct_applicability(db, predecessor)
        reconstruct_applicability(db, successor)

        forged_value = {
            "version": "ad-v4-applicability-event-v2",
            "eventType": "stale_marked",
            "projectionId": predecessor.id,
            "proposalId": predecessor.proposal_id,
            "sequence": "2",
            "reasons": ["candidate_supersession_signal"],
            "cause": {"kind": "supersession_dependency", "id": outgoing.id},
            "predecessorEventHash": event.event_hash,
        }
        forged_bytes = canonical_bytes(forged_value, CANONICALIZATION_VERSION_V2)
        with pytest.raises(DBAPIError, match="event chain/envelope mismatch"):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_projection_events
                (id,projection_id,proposal_id,sequence_number,event_type,reason_code,
                 causing_request_id,causing_relationship_id,causing_lifecycle_event_id,
                 causing_dependency_id,predecessor_event_hash,canonical_bytes,event_hash,actor_kind)
              VALUES
                ('avz_cross_projection_cause',:projection,:proposal,2,'stale_marked',
                 'candidate_supersession_signal',NULL,NULL,NULL,:dependency,:predecessor,
                 :canonical_bytes,:event_hash,'system_repair')
            """), {
                "projection": predecessor.id,
                "proposal": predecessor.proposal_id,
                "dependency": outgoing.id,
                "predecessor": event.event_hash,
                "canonical_bytes": forged_bytes,
                "event_hash": hashlib.sha256(EVENT_DOMAIN + forged_bytes).hexdigest(),
            })
            db.flush()
        db.rollback()
    engine.dispose()


def test_10_mismatched_successor_remains_unresolved_without_side_effect() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        predecessor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="mismatch-predecessor", ad_number="2020-02-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="mismatch-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-02-01",
                "successorAdNumber": "2025-01-01",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
        ))
        assert outgoing.resolution_state == "unresolved"
        assert outgoing.unresolved_reason == "successor_not_this_proposal"
        assert outgoing.target_projection_id is None
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
        )) == 0
        assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppProjectionEvent).where(
            ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
            ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
        )) == 0
    engine.dispose()


def test_11_ambiguous_predecessor_remains_ambiguous_without_side_effect() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        first = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-predecessor-a", ad_number="2020-03-01",
        )
        second = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-predecessor-b", ad_number="2020-03-01",
        )
        successor = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="ambiguous-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-03-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
        ))
        assert outgoing.resolution_state == "ambiguous"
        assert outgoing.unresolved_reason == "multiple_predecessor_candidates"
        assert outgoing.target_projection_id is None
        for predecessor in (first, second):
            assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppChangeDependency).where(
                ADV4CandidateAppChangeDependency.projection_id == predecessor.id,
            )) == 0
            assert db.scalar(select(text("count(*)")).select_from(ADV4CandidateAppProjectionEvent).where(
                ADV4CandidateAppProjectionEvent.projection_id == predecessor.id,
                ADV4CandidateAppProjectionEvent.event_type == "stale_marked",
            )) == 0
    engine.dispose()


def test_12_concurrent_second_predecessor_cannot_invalidate_unique_resolution() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        first = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-predecessor-a", ad_number="2020-04-01",
        )
        p2_user, p2_membership, p2_directive, p2_proposal = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-predecessor-b", ad_number="2020-04-01",
        )
        s_user, s_membership, s_directive, s_proposal = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="race-successor", ad_number="2024-14-03",
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-04-01",
                "successorAdNumber": "2024-14-03",
                "evidenceKeys": ["ev-official"],
            }],
        )

    barrier = threading.Barrier(2)

    def materialize_one(user_id, membership_id, directive_id, proposal_id, key):
        with SessionLocal() as db:
            barrier.wait(timeout=5)
            try:
                result = materialize_applicability(
                    db, directive_id=directive_id, proposal_id=proposal_id,
                    actor=db.get(User, user_id), membership_id=membership_id,
                    idempotency_key=key,
                )
                db.commit()
                return ("committed", result.projection.id)
            except Exception as exc:
                db.rollback()
                return (getattr(exc, "code", type(exc).__name__), None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        p2_future = pool.submit(
            materialize_one, p2_user, p2_membership, p2_directive, p2_proposal, "race-p2",
        )
        successor_future = pool.submit(
            materialize_one, s_user, s_membership, s_directive, s_proposal, "race-successor",
        )
        p2_result = p2_future.result(timeout=20)
        successor_result = successor_future.result(timeout=20)

    assert successor_result[0] == "committed"
    assert p2_result[0] in {"committed", "supersession_resolution_conflict"}
    with SessionLocal() as db:
        successor = db.get(ADV4CandidateAppProjection, successor_result[1])
        outgoing = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == successor.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "outgoing_supersedes",
        ))
        matching_predecessors = []
        for projection in db.scalars(select(ADV4CandidateAppProjection).where(
            ADV4CandidateAppProjection.id != successor.id
        )).all():
            candidate = db.get(ADV4CandidateProposal, projection.proposal_id)
            ad = candidate.parsed_json["directiveIdentity"]["adNumber"]
            if ad.get("state") == "known" and ad.get("value") == "2020-04-01":
                matching_predecessors.append(projection.id)
        if p2_result[0] == "committed":
            assert len(matching_predecessors) == 2
            assert outgoing.resolution_state == "ambiguous"
            assert outgoing.target_projection_id is None
        else:
            assert matching_predecessors == [first.id]
            assert outgoing.resolution_state == "resolved_candidate"
            assert outgoing.target_projection_id == first.id
    engine.dispose()


def test_13_direct_projection_insert_participates_in_database_ad_lock() -> None:
    engine = _engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        _enable(db)
        user_id, membership_id, directive_id, proposal_id = _store(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="direct-lock", ad_number="2030-01-01",
        )
        result = materialize_applicability(
            db, directive_id=directive_id, proposal_id=proposal_id,
            actor=db.get(User, user_id), membership_id=membership_id,
            idempotency_key="capture-direct-lock-root",
        )
        db.flush()
        root_values = {
            column.name: getattr(result.projection, column.name)
            for column in ADV4CandidateAppProjection.__table__.columns
        }
        db.rollback()

    ready = threading.Event()
    release = threading.Event()

    def hold_database_lock():
        with SessionLocal() as db:
            db.execute(
                text("SELECT paprnav_v4_lock_app_ad_numbers(:proposal)"),
                {"proposal": proposal_id},
            )
            ready.set()
            release.wait(timeout=5)
            db.rollback()

    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(hold_database_lock)
        assert ready.wait(timeout=5)
        try:
            with SessionLocal() as db:
                db.execute(text("SET LOCAL lock_timeout='300ms'"))
                with pytest.raises(DBAPIError, match="lock timeout"):
                    db.execute(ADV4CandidateAppProjection.__table__.insert().values(**root_values))
                    db.flush()
                db.rollback()
        finally:
            release.set()
        holder.result(timeout=5)
    engine.dispose()


def test_17_complete_condition_family_commits_and_reconstructs() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="condition-family", condition_matrix=True,
        )
        reconstructed = reconstruct_applicability(db, projection)
        conditions = reconstructed["conditionDefinitions"]
        assert len(conditions) == 112  # 90 type/operator + 18 union + 4 groups
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppCondition
        ).where(ADV4CandidateAppCondition.projection_id == projection.id)) == 112
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppDesignationGroup
        ).where(ADV4CandidateAppDesignationGroup.projection_id == projection.id)) == 4
        assert db.scalar(select(text("count(*)")).select_from(
            ADV4CandidateAppDesignationGroupMember
        ).where(ADV4CandidateAppDesignationGroupMember.projection_id == projection.id)) == 8
        longest_reason = db.scalar(select(ADV4CandidateAppValueAssertion.reason).where(
            ADV4CandidateAppValueAssertion.projection_id == projection.id,
            ADV4CandidateAppValueAssertion.state == "not_applicable",
        ).order_by(text("length(reason) DESC")))
        assert longest_reason is not None and len(longest_reason) == 512
    engine.dispose()


def test_18_condition_family_direct_sql_corruption_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="condition-corruption", condition_matrix=True,
            dual_evidence=True,
        )
        second_projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="condition-cross-target", condition_matrix=True,
        )
        projection_id = projection.id
        condition = db.scalar(select(ADV4CandidateAppCondition).where(
            ADV4CandidateAppCondition.projection_id == projection_id,
            ADV4CandidateAppCondition.condition_key == "condition-union-00-0",
        ))
        assertion = db.scalar(select(ADV4CandidateAppValueAssertion).where(
            ADV4CandidateAppValueAssertion.parent_semantic_node_id == condition.semantic_node_id,
        ))
        group = db.scalar(select(ADV4CandidateAppDesignationGroup).where(
            ADV4CandidateAppDesignationGroup.projection_id == projection_id,
            ADV4CandidateAppDesignationGroup.group_key == "condition-group-0",
        ))
        member = db.scalar(select(ADV4CandidateAppDesignationGroupMember).where(
            ADV4CandidateAppDesignationGroupMember.group_node_id == group.semantic_node_id,
            ADV4CandidateAppDesignationGroupMember.designation_kind == "model",
        ))
        mapping = db.scalar(select(ADV4CandidateAppIdentityMapping).where(
            ADV4CandidateAppIdentityMapping.source_occurrence_node_id == member.semantic_node_id,
        ))
        evidence = db.scalar(select(ADV4CandidateAppEvidenceLink).where(
            ADV4CandidateAppEvidenceLink.semantic_node_id == group.semantic_node_id,
        ))
        secondary_binding = db.scalar(select(ADV4CandidateEvidenceBinding).where(
            ADV4CandidateEvidenceBinding.proposal_id == projection.proposal_id,
            ADV4CandidateEvidenceBinding.evidence_key == "ev-secondary",
        ))
        second_group = db.scalar(select(ADV4CandidateAppDesignationGroup).where(
            ADV4CandidateAppDesignationGroup.projection_id == second_projection.id,
            ADV4CandidateAppDesignationGroup.group_key == "condition-group-1",
        ))
        db.commit()

        swapped_link_id, swapped_link_hash = _row_id("avl", "evidence-link", {
            "projectionId": projection_id, "nodeId": group.semantic_node_id,
            "purpose": "condition_clause", "evidenceKey": "ev-secondary",
        })
        cross_mapping_id, cross_mapping_hash = _row_id("avi", "identity-mapping", {
            "projectionId": projection_id, "kind": "model",
            "occurrence": assertion.semantic_node_id,
        })

        corruptions = [
            (
                "ad_v4_candidate_app_conditions", condition.semantic_node_id,
                "UPDATE ad_v4_candidate_app_conditions SET operator='equals' WHERE semantic_node_id=:id",
                "condition owner graph differs",
            ),
            (
                "ad_v4_candidate_app_value_assertions", assertion.semantic_node_id,
                "UPDATE ad_v4_candidate_app_value_assertions SET text_value='different' WHERE semantic_node_id=:id",
                "condition value-assertion graph differs",
            ),
            (
                "ad_v4_candidate_app_value_assertions", assertion.semantic_node_id,
                "UPDATE ad_v4_candidate_app_value_assertions SET state='unknown',text_value=NULL,reason='not_observed',temporal_scope='directive_version' WHERE semantic_node_id=:id",
                "condition value-assertion graph differs",
            ),
            (
                "ad_v4_candidate_app_conditions", condition.semantic_node_id,
                "UPDATE ad_v4_candidate_app_conditions SET comparator_presence='present',comparator_version='forged-v1' WHERE semantic_node_id=:id",
                "condition owner graph differs",
            ),
            (
                "ad_v4_candidate_app_designation_groups", group.semantic_node_id,
                "UPDATE ad_v4_candidate_app_designation_groups SET association='any_member' WHERE semantic_node_id=:id",
                "condition designation-group graph differs",
            ),
            (
                "ad_v4_candidate_app_designation_group_members", member.semantic_node_id,
                "UPDATE ad_v4_candidate_app_designation_group_members SET canonical_ordinal=9 WHERE semantic_node_id=:id",
                "semantic node differs|condition designation-member graph differs",
            ),
            (
                "ad_v4_candidate_app_identity_mappings", mapping.id,
                "UPDATE ad_v4_candidate_app_identity_mappings SET evidence_parent_node_id=:parent WHERE id=:id",
                "condition identity-mapping graph differs",
                {"parent": condition.semantic_node_id},
            ),
            (
                "ad_v4_candidate_app_identity_mappings", mapping.id,
                "UPDATE ad_v4_candidate_app_identity_mappings SET reason='not_yet_reviewed',temporal_scope='source_observation' WHERE id=:id",
                "condition identity-mapping graph differs",
            ),
            (
                "ad_v4_candidate_app_identity_mappings", mapping.id,
                "UPDATE ad_v4_candidate_app_identity_mappings SET id=:new_id,identity_hash=:new_hash,source_occurrence_node_id=:occurrence,source_value='Maker 0' WHERE id=:id",
                "identity-mapping identity differs|condition identity-mapping graph differs",
                {"new_id": cross_mapping_id, "new_hash": cross_mapping_hash, "occurrence": assertion.semantic_node_id},
            ),
            (
                "ad_v4_candidate_app_evidence_links", evidence.id,
                "UPDATE ad_v4_candidate_app_evidence_links SET purpose='subject_value' WHERE id=:id",
                "relational graph is incomplete|condition evidence graph differs",
            ),
            (
                "ad_v4_candidate_app_evidence_links", evidence.id,
                "UPDATE ad_v4_candidate_app_evidence_links SET id=:new_id,evidence_key='ev-secondary',candidate_binding_id=:binding,link_hash=:link_hash WHERE id=:id",
                "relational graph is incomplete|condition evidence graph differs",
                {"new_id": swapped_link_id, "binding": secondary_binding.id, "link_hash": swapped_link_hash},
            ),
            (
                "ad_v4_candidate_app_semantic_nodes", group.semantic_node_id,
                "UPDATE ad_v4_candidate_app_semantic_nodes SET canonical_node_hash=repeat('f',64) WHERE id=:id",
                "semantic node differs",
            ),
            (
                "ad_v4_candidate_app_semantic_nodes", group.semantic_node_id,
                "UPDATE ad_v4_candidate_app_semantic_nodes SET node_type='search_hint_group' WHERE id=:id",
                "semantic node differs|semantic ownership differs",
            ),
            (
                "ad_v4_candidate_app_designation_groups", group.semantic_node_id,
                "DELETE FROM ad_v4_candidate_app_designation_groups WHERE semantic_node_id=:id",
                "relational graph is incomplete|semantic ownership differs",
            ),
            (
                "ad_v4_candidate_app_identity_mappings", mapping.id,
                "DELETE FROM ad_v4_candidate_app_identity_mappings WHERE id=:id",
                "relational graph is incomplete|semantic ownership differs",
            ),
            (
                "ad_v4_candidate_app_evidence_links", evidence.id,
                "DELETE FROM ad_v4_candidate_app_evidence_links WHERE id=:id",
                "relational graph is incomplete|condition evidence graph differs",
            ),
        ]
        for corruption in corruptions:
            table_name, row_id, statement, expected_error, *extra = corruption
            db.execute(text(
                f"ALTER TABLE {table_name} DISABLE TRIGGER trg_{table_name}_immutable"
            ))
            parameters = {"id": row_id, **(extra[0] if extra else {})}
            db.execute(text(statement), parameters)
            with pytest.raises(DBAPIError, match=expected_error):
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            db.rollback()

        # Composite same-projection ownership rejects a cross-projection parent
        # before deferred validation can even observe an ambiguous graph.
        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_designation_group_members "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_designation_group_members_immutable"
        ))
        with pytest.raises(DBAPIError):
            db.execute(text(
                "UPDATE ad_v4_candidate_app_designation_group_members SET group_node_id=:other "
                "WHERE semantic_node_id=:id"
            ), {"other": second_group.semantic_node_id, "id": member.semantic_node_id})
            db.flush()
        db.rollback()

        extra_link_id, extra_link_hash = _row_id("avl", "evidence-link", {
            "projectionId": projection_id, "nodeId": group.semantic_node_id,
            "purpose": "condition_clause", "evidenceKey": "ev-secondary",
        })
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_evidence_links(
            id,projection_id,proposal_id,semantic_node_id,candidate_binding_id,
            evidence_key,purpose,canonical_ordinal,link_hash)
          VALUES(:id,:projection,:proposal,:node,:binding,'ev-secondary',
            'condition_clause',1,:hash)
        """), {
            "id": extra_link_id, "projection": projection_id,
            "proposal": projection.proposal_id, "node": group.semantic_node_id,
            "binding": secondary_binding.id, "hash": extra_link_hash,
        })
        with pytest.raises(DBAPIError, match="relational graph is incomplete|condition evidence graph differs"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()

        unknown_condition = db.scalar(select(ADV4CandidateAppCondition).where(
            ADV4CandidateAppCondition.projection_id == projection_id,
            ADV4CandidateAppCondition.condition_key == "condition-union-00-1",
        ))
        unknown_assertion = db.scalar(select(ADV4CandidateAppValueAssertion).where(
            ADV4CandidateAppValueAssertion.parent_semantic_node_id == unknown_condition.semantic_node_id,
        ))
        unknown_node = db.get(ADV4CandidateAppSemanticNode, unknown_assertion.semantic_node_id)
        mapping_node_id, mapping_node_hash = _row_id("avn", "semantic-node", {
            "projectionId": projection_id, "nodeType": "identity_mapping",
            "nodeKey": unknown_node.id, "pointer": unknown_node.source_pointer,
        })
        extra_mapping_id, extra_mapping_hash = _row_id("avi", "identity-mapping", {
            "projectionId": projection_id, "kind": "manufacturer",
            "occurrence": unknown_node.id,
        })
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_semantic_nodes(
            id,identity_hash,projection_id,proposal_id,parent_node_id,node_type,
            node_key,source_pointer,canonical_node_hash,canonical_ordinal)
          VALUES(:id,:identity,:projection,:proposal,:occurrence,'identity_mapping',
            :node_key,:pointer,:canonical_hash,0)
        """), {
            "id": mapping_node_id, "identity": mapping_node_hash,
            "projection": projection_id, "proposal": projection.proposal_id,
            "occurrence": unknown_node.id, "node_key": unknown_node.id,
            "pointer": unknown_node.source_pointer,
            "canonical_hash": unknown_node.canonical_node_hash,
        })
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_identity_mappings(
            id,semantic_node_id,projection_id,proposal_id,source_occurrence_node_id,
            evidence_parent_node_id,identity_kind,source_value,normalization_origin,
            normalized_state,normalized_value,reason,temporal_scope,
            normalization_namespace,normalization_version,review_state,identity_hash)
          VALUES(:id,:node,:projection,:proposal,:occurrence,:parent,'manufacturer',
            'forged','source_only','unknown',NULL,'not_extracted','directive_version',
            NULL,NULL,'unreviewed_candidate',:identity)
        """), {
            "id": extra_mapping_id, "node": mapping_node_id,
            "projection": projection_id, "proposal": projection.proposal_id,
            "occurrence": unknown_node.id, "parent": unknown_condition.semantic_node_id,
            "identity": extra_mapping_hash,
        })
        with pytest.raises(DBAPIError, match="semantic-node set is incomplete|relational graph is incomplete"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()

        # A fully validated generation cannot mask a later Family-1 insert.
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        with pytest.raises(DBAPIError, match="semantic ownership differs"):
            db.execute(text("""
              INSERT INTO ad_v4_candidate_app_conditions(
                semantic_node_id,projection_id,proposal_id,condition_key,
                condition_type,operator,temporal_basis,comparator_presence,
                comparator_version,subject_product_role_presence,subject_product_role,
                subject_attribute_key_presence,subject_attribute_key,
                designation_group_presence,designation_group_node_id,
                evaluation_state,evaluator_contract)
              VALUES(:node,:projection,:proposal,'forged-extra-condition','identity',
                'identity_equals','directive_version','property_absent',NULL,
                'property_absent',NULL,'property_absent',NULL,'property_absent',NULL,
                'unevaluated','none')
            """), {
                "node": group.semantic_node_id, "projection": projection_id,
                "proposal": projection.proposal_id,
            })
            db.flush()
        db.rollback()
    engine.dispose()


def test_19_complete_rule_expression_family_commits_and_reconstructs() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="rule-family", rule_matrix=True,
        )
        reconstructed = reconstruct_applicability(db, projection)
        assert [rule["ruleKey"] for rule in reconstructed["applicabilityRules"]] == [
            "rule-base", "rule-complex", "rule-terminal",
        ]
        rules = db.scalars(select(ADV4CandidateAppRule).where(
            ADV4CandidateAppRule.projection_id == projection.id
        )).all()
        expressions = db.scalars(select(ADV4CandidateAppExpression).where(
            ADV4CandidateAppExpression.projection_id == projection.id
        )).all()
        edges = db.scalars(select(ADV4CandidateAppExpressionEdge).where(
            ADV4CandidateAppExpressionEdge.projection_id == projection.id
        )).all()
        exclusions = db.scalars(select(ADV4CandidateAppRuleExclusion).where(
            ADV4CandidateAppRuleExclusion.projection_id == projection.id
        )).all()
        assert len(rules) == 3
        assert {row.expression_node_type for row in expressions} == {
            "scope_ref", "predicate_ref", "rule_ref", "not", "all", "any",
        }
        assert {row.expression_context for row in expressions} == {"scope", "condition"}
        assert len(edges) == len(expressions) - 4  # four expression roots
        assert len(exclusions) == 2
        assert max(len(row.expression_path) for row in expressions) > 255
        assert max(
            len(node.node_key) for node in db.scalars(select(ADV4CandidateAppSemanticNode).where(
                ADV4CandidateAppSemanticNode.projection_id == projection.id,
                ADV4CandidateAppSemanticNode.node_type == "expression",
            )).all()
        ) > 255
    engine.dispose()


def test_20_rule_expression_direct_sql_corruption_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="rule-corruption", rule_matrix=True,
        )
        other = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="rule-cross-target",
        )
        complex_rule = db.scalar(select(ADV4CandidateAppRule).where(
            ADV4CandidateAppRule.projection_id == projection.id,
            ADV4CandidateAppRule.rule_key == "rule-complex",
        ))
        base_rule = db.scalar(select(ADV4CandidateAppRule).where(
            ADV4CandidateAppRule.projection_id == projection.id,
            ADV4CandidateAppRule.rule_key == "rule-base",
        ))
        terminal_rule = db.scalar(select(ADV4CandidateAppRule).where(
            ADV4CandidateAppRule.projection_id == projection.id,
            ADV4CandidateAppRule.rule_key == "rule-terminal",
        ))
        condition_root = db.scalar(select(ADV4CandidateAppExpression).where(
            ADV4CandidateAppExpression.owning_rule_node_id == complex_rule.semantic_node_id,
            ADV4CandidateAppExpression.expression_context == "condition",
            ADV4CandidateAppExpression.expression_path == "/",
        ))
        scope_leaf = db.scalar(select(ADV4CandidateAppExpression).where(
            ADV4CandidateAppExpression.owning_rule_node_id == complex_rule.semantic_node_id,
            ADV4CandidateAppExpression.expression_node_type == "scope_ref",
        ))
        rule_ref = db.scalar(select(ADV4CandidateAppExpression).where(
            ADV4CandidateAppExpression.owning_rule_node_id == complex_rule.semantic_node_id,
            ADV4CandidateAppExpression.expression_node_type == "rule_ref",
        ))
        not_expression = db.scalar(select(ADV4CandidateAppExpression).where(
            ADV4CandidateAppExpression.owning_rule_node_id == complex_rule.semantic_node_id,
            ADV4CandidateAppExpression.expression_node_type == "not",
        ).order_by(ADV4CandidateAppExpression.expression_path))
        not_edge = db.scalar(select(ADV4CandidateAppExpressionEdge).where(
            ADV4CandidateAppExpressionEdge.parent_expression_id == not_expression.semantic_node_id,
        ))
        first_exclusion = db.scalar(select(ADV4CandidateAppRuleExclusion).where(
            ADV4CandidateAppRuleExclusion.rule_node_id == complex_rule.semantic_node_id,
            ADV4CandidateAppRuleExclusion.canonical_ordinal == 0,
        ))
        rule_evidence = db.scalar(select(ADV4CandidateAppEvidenceLink).where(
            ADV4CandidateAppEvidenceLink.semantic_node_id == complex_rule.semantic_node_id,
        ))
        scope_node = db.get(ADV4CandidateAppSemanticNode, scope_leaf.semantic_node_id)
        other_scope = db.scalar(select(ADV4CandidateAppProductScope).where(
            ADV4CandidateAppProductScope.projection_id == other.id,
        ))
        db.commit()

        corruptions = [
            (
                "ad_v4_candidate_app_rules", complex_rule.semantic_node_id,
                "UPDATE ad_v4_candidate_app_rules SET condition_presence='property_absent',condition_expression_node_id=NULL WHERE semantic_node_id=:id",
                "rule owners differ",
            ),
            (
                "ad_v4_candidate_app_expressions", scope_leaf.semantic_node_id,
                "UPDATE ad_v4_candidate_app_expressions SET expression_path='/forged' WHERE semantic_node_id=:id",
                "expression owners or references differ",
            ),
            (
                "ad_v4_candidate_app_expressions", rule_ref.semantic_node_id,
                "UPDATE ad_v4_candidate_app_expressions SET referenced_rule_node_id=:target WHERE semantic_node_id=:id",
                "expression owners or references differ",
                {"target": terminal_rule.semantic_node_id},
            ),
            (
                "ad_v4_candidate_app_expressions", condition_root.semantic_node_id,
                "UPDATE ad_v4_candidate_app_expressions SET expression_node_type='all' WHERE semantic_node_id=:id",
                "expression owners or references differ",
            ),
            (
                "ad_v4_candidate_app_expression_edges", not_edge.parent_expression_id,
                "UPDATE ad_v4_candidate_app_expression_edges SET sequence=9 WHERE parent_expression_id=:id AND sequence=0",
                "expression edge graph differs|semantic node differs",
            ),
            (
                "ad_v4_candidate_app_expression_edges", not_edge.parent_expression_id,
                "DELETE FROM ad_v4_candidate_app_expression_edges WHERE parent_expression_id=:id AND sequence=0",
                "expression edge graph differs",
            ),
            (
                "ad_v4_candidate_app_rule_exclusions", first_exclusion.rule_node_id,
                "UPDATE ad_v4_candidate_app_rule_exclusions SET excluded_rule_node_id=:target WHERE rule_node_id=:id AND canonical_ordinal=0",
                "rule exclusions differ|dependency graph is cyclic",
                {"target": complex_rule.semantic_node_id},
            ),
            (
                "ad_v4_candidate_app_rule_exclusions", first_exclusion.rule_node_id,
                "DELETE FROM ad_v4_candidate_app_rule_exclusions WHERE rule_node_id=:id AND canonical_ordinal=0",
                "rule exclusions differ",
            ),
            (
                "ad_v4_candidate_app_evidence_links", rule_evidence.id,
                "UPDATE ad_v4_candidate_app_evidence_links SET purpose='condition_clause' WHERE id=:id",
                "relational graph is incomplete|rule evidence graph differs",
            ),
            (
                "ad_v4_candidate_app_semantic_nodes", scope_node.id,
                "UPDATE ad_v4_candidate_app_semantic_nodes SET parent_node_id=:target WHERE id=:id",
                "semantic node differs|expression edge graph differs",
                {"target": base_rule.semantic_node_id},
            ),
            (
                "ad_v4_candidate_app_rules", base_rule.semantic_node_id,
                "DELETE FROM ad_v4_candidate_app_rules WHERE semantic_node_id=:id",
                "semantic ownership differs|rule owners differ",
            ),
        ]
        for corruption in corruptions:
            table_name, row_id, statement, expected_error, *extra = corruption
            db.execute(text(
                f"ALTER TABLE {table_name} DISABLE TRIGGER trg_{table_name}_immutable"
            ))
            db.execute(text(statement), {"id": row_id, **(extra[0] if extra else {})})
            with pytest.raises(DBAPIError, match=expected_error):
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            db.rollback()

        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_expressions "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_expressions_immutable"
        ))
        with pytest.raises(DBAPIError):
            db.execute(text(
                "UPDATE ad_v4_candidate_app_expressions SET scope_node_id=:other "
                "WHERE semantic_node_id=:id"
            ), {"other": other_scope.semantic_node_id, "id": scope_leaf.semantic_node_id})
            db.flush()
        db.rollback()

        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_expressions "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_expressions_immutable"
        ))
        with pytest.raises(DBAPIError, match="expression_type|expression type|check constraint"):
            db.execute(text(
                "UPDATE ad_v4_candidate_app_expressions SET expression_node_type='requirement_state_ref' "
                "WHERE semantic_node_id=:id"
            ), {"id": scope_leaf.semantic_node_id})
            db.flush()
        db.rollback()

        root_expression = db.get(ADV4CandidateAppSemanticNode, condition_root.semantic_node_id)
        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        with pytest.raises(DBAPIError, match="expression edge graph differs|dependency graph is cyclic"):
            db.execute(ADV4CandidateAppExpressionEdge.__table__.insert().values(
                projection_id=projection.id, proposal_id=projection.proposal_id,
                owning_rule_node_id=complex_rule.semantic_node_id,
                expression_context="condition",
                parent_expression_id=rule_ref.semantic_node_id,
                child_expression_id=root_expression.id, sequence=0,
            ))
        db.rollback()

        db.add(ADV4CandidateAppRule(
            semantic_node_id=scope_leaf.semantic_node_id,
            projection_id=projection.id, proposal_id=projection.proposal_id,
            rule_key="forged-extra-rule",
            scope_expression_node_id=scope_leaf.semantic_node_id,
            condition_presence="property_absent",
            condition_expression_node_id=None, evaluator_contract="none",
        ))
        with pytest.raises(DBAPIError, match="semantic ownership differs|rule owners differ"):
            db.flush()
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()

        # A direct writer that restamps the candidate/projection envelope and
        # datum tree still cannot project the requirement-only expression arm.
        candidate = db.get(ADV4CandidateProposal, projection.proposal_id)
        forged = copy.deepcopy(candidate.parsed_json)
        forged_expression = {
            "nodeType": "requirement_state_ref",
            "requirementKey": "requirement-main",
            "requirementState": "satisfied",
        }
        forged["applicabilityRules"][0]["scopeExpression"] = forged_expression
        subtree = {
            key: forged[key] for key in (
                "productScopes", "conditionDefinitions", "applicabilityRules",
                "applicabilitySearchHints",
            )
        }
        proposal_bytes = canonical_bytes(forged, CANONICALIZATION_VERSION_V2)
        proposal_hash = hashlib.sha256(DOMAINS_V2["proposal"] + proposal_bytes).hexdigest()
        subtree_bytes = canonical_bytes(subtree, CANONICALIZATION_VERSION_V2)
        subtree_hash = hashlib.sha256(SUBTREE_DOMAIN + subtree_bytes).hexdigest()
        envelope = json.loads(projection.projection_canonical_bytes)
        envelope["proposalCanonicalHash"] = proposal_hash
        envelope["applicabilitySubtreeHash"] = subtree_hash
        projection_bytes = canonical_bytes(envelope, CANONICALIZATION_VERSION_V2)
        expression_pointer = "/applicabilityRules/0/scopeExpression"
        forged_node = db.scalar(select(ADV4CandidateAppSemanticNode).where(
            ADV4CandidateAppSemanticNode.projection_id == projection.id,
            ADV4CandidateAppSemanticNode.source_pointer == expression_pointer,
        ))
        forged_rule_node = db.get(
            ADV4CandidateAppSemanticNode, base_rule.semantic_node_id,
        )
        node_type_datum = db.scalar(select(ADV4CandidateAppDatum).where(
            ADV4CandidateAppDatum.projection_id == projection.id,
            ADV4CandidateAppDatum.json_pointer == f"{expression_pointer}/nodeType",
        ))
        scope_key_datum = db.scalar(select(ADV4CandidateAppDatum).where(
            ADV4CandidateAppDatum.projection_id == projection.id,
            ADV4CandidateAppDatum.json_pointer == f"{expression_pointer}/scopeKey",
        ))
        for table_name in (
            "ad_v4_candidate_proposals", "ad_v4_candidate_app_projections",
            "ad_v4_candidate_app_semantic_nodes", "ad_v4_candidate_app_data",
        ):
            db.execute(text(
                f"ALTER TABLE {table_name} DISABLE TRIGGER trg_{table_name}_immutable"
            ))
        candidate.parsed_json = forged
        candidate.canonical_bytes = proposal_bytes
        candidate.canonical_hash = proposal_hash
        projection.proposal_canonical_hash = proposal_hash
        projection.applicability_subtree_bytes = subtree_bytes
        projection.applicability_subtree_hash = subtree_hash
        projection.projection_canonical_bytes = projection_bytes
        projection.projection_hash = hashlib.sha256(PROJECTION_DOMAIN + projection_bytes).hexdigest()
        projection.datum_count += 1
        forged_node.canonical_node_hash = hashlib.sha256(
            canonical_bytes(forged_expression, CANONICALIZATION_VERSION_V2)
        ).hexdigest()
        forged_rule_node.canonical_node_hash = hashlib.sha256(
            canonical_bytes(forged["applicabilityRules"][0], CANONICALIZATION_VERSION_V2)
        ).hexdigest()
        node_type_datum.string_value = "requirement_state_ref"
        node_type_datum.value_hash = _row_id("avd", "datum", {
            "projectionId": projection.id,
            "pointer": node_type_datum.json_pointer,
            "kind": "string", "value": "requirement_state_ref",
        })[1]
        db.delete(scope_key_datum)
        for property_name, value in (
            ("requirementKey", "requirement-main"),
            ("requirementState", "satisfied"),
        ):
            pointer = f"{expression_pointer}/{property_name}"
            datum_id, datum_hash = _row_id("avd", "datum", {
                "projectionId": projection.id, "pointer": pointer,
                "kind": "string", "value": value,
            })
            db.add(ADV4CandidateAppDatum(
                id=datum_id, projection_id=projection.id,
                proposal_id=projection.proposal_id,
                semantic_node_id=forged_node.id, json_pointer=pointer,
                parent_pointer=expression_pointer, property_name=property_name,
                array_ordinal=None, value_kind="string", string_value=value,
                boolean_value=None, value_hash=datum_hash,
            ))
        db.flush()
        with pytest.raises(DBAPIError, match="requirement-state reference"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    engine.dispose()


def test_21_complete_search_hint_family_commits_and_reconstructs() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="search-hint-family", hint_matrix=True,
        )
        reconstructed = reconstruct_applicability(db, projection)
        hints = reconstructed["applicabilitySearchHints"]
        assert len(hints) == 6
        assert {hint["productRole"] for hint in hints} == {
            "airframe", "engine", "propeller", "appliance",
            "installed_part", "modification",
        }
        assert {
            group["association"] for hint in hints
            for group in hint["manufacturerModelGroups"]
        } == {"paired", "source_group", "unknown"}
        assert db.scalar(select(func.count()).select_from(ADV4CandidateAppSearchHint).where(
            ADV4CandidateAppSearchHint.projection_id == projection.id
        )) == 6
        assert db.scalar(select(func.count()).select_from(ADV4CandidateAppSearchHintGroup).where(
            ADV4CandidateAppSearchHintGroup.projection_id == projection.id
        )) == 6
        assert db.scalar(select(func.count()).select_from(ADV4CandidateAppSearchHintMember).where(
            ADV4CandidateAppSearchHintMember.projection_id == projection.id
        )) == 12
        hint_nodes = db.scalars(select(ADV4CandidateAppSemanticNode).where(
            ADV4CandidateAppSemanticNode.projection_id == projection.id,
            ADV4CandidateAppSemanticNode.source_pointer.like("/applicabilitySearchHints/%"),
        )).all()
        assert len([node for node in hint_nodes if node.node_type == "value_assertion"]) == 24
        hint_mappings = db.scalars(select(ADV4CandidateAppIdentityMapping).join(
            ADV4CandidateAppSemanticNode,
            ADV4CandidateAppIdentityMapping.source_occurrence_node_id == ADV4CandidateAppSemanticNode.id,
        ).where(
            ADV4CandidateAppIdentityMapping.projection_id == projection.id,
            ADV4CandidateAppSemanticNode.source_pointer.like("/applicabilitySearchHints/%"),
        )).all()
        assert len(hint_mappings) == 18
        assert sum(row.identity_kind == "model" for row in hint_mappings) == 6
        assert sum(row.identity_kind == "series" for row in hint_mappings) == 6
        assert sum(row.identity_kind == "manufacturer" for row in hint_mappings) == 6
        assert any(
            member.manufacturer_reason == "h" * 512
            for member in db.scalars(select(ADV4CandidateAppSearchHintMember).where(
                ADV4CandidateAppSearchHintMember.projection_id == projection.id
            )).all()
        )
    engine.dispose()


def test_22_search_hint_direct_sql_corruption_is_rejected() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="search-hint-corruption", hint_matrix=True,
        )
        other = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="search-hint-cross-target", hint_matrix=True,
        )
        hint = db.scalar(select(ADV4CandidateAppSearchHint).where(
            ADV4CandidateAppSearchHint.projection_id == projection.id
        ).order_by(ADV4CandidateAppSearchHint.hint_key))
        group = db.scalar(select(ADV4CandidateAppSearchHintGroup).where(
            ADV4CandidateAppSearchHintGroup.hint_node_id == hint.semantic_node_id
        ))
        members = db.scalars(select(ADV4CandidateAppSearchHintMember).where(
            ADV4CandidateAppSearchHintMember.group_node_id == group.semantic_node_id
        ).order_by(ADV4CandidateAppSearchHintMember.canonical_ordinal)).all()
        display = db.get(ADV4CandidateAppValueAssertion, hint.source_display_assertion_node_id)
        group_manufacturer = db.get(
            ADV4CandidateAppValueAssertion, group.manufacturer_assertion_node_id,
        )
        member_manufacturer = db.get(
            ADV4CandidateAppValueAssertion, members[0].manufacturer_assertion_node_id,
        )
        designation_mapping = db.scalar(select(ADV4CandidateAppIdentityMapping).where(
            ADV4CandidateAppIdentityMapping.semantic_node_id
            == members[0].designation_identity_mapping_node_id
        ))
        second_mapping = db.scalar(select(ADV4CandidateAppIdentityMapping).where(
            ADV4CandidateAppIdentityMapping.semantic_node_id
            == members[1].designation_identity_mapping_node_id
        ))
        hint_evidence = db.scalar(select(ADV4CandidateAppEvidenceLink).where(
            ADV4CandidateAppEvidenceLink.semantic_node_id == hint.semantic_node_id
        ))
        other_hint = db.scalar(select(ADV4CandidateAppSearchHint).where(
            ADV4CandidateAppSearchHint.projection_id == other.id
        ))
        ids = {
            "hint": hint.semantic_node_id, "group": group.semantic_node_id,
            "member": members[0].semantic_node_id,
            "second_mapping": second_mapping.semantic_node_id,
            "display": display.semantic_node_id,
            "group_manufacturer": group_manufacturer.semantic_node_id,
            "member_manufacturer": member_manufacturer.semantic_node_id,
            "mapping": designation_mapping.id, "evidence": hint_evidence.id,
            "other_hint": other_hint.semantic_node_id,
        }
        proposal_id = projection.proposal_id
        projection_id = projection.id
        db.commit()

        corruptions = [
            (
                "ad_v4_candidate_app_search_hints", ids["hint"],
                "UPDATE ad_v4_candidate_app_search_hints SET product_role='engine' WHERE semantic_node_id=:id",
                "search-hint owners differ",
            ),
            (
                "ad_v4_candidate_app_value_assertions", ids["display"],
                "UPDATE ad_v4_candidate_app_value_assertions SET text_value='forged display' WHERE semantic_node_id=:id",
                "search-hint assertion graph differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_groups", ids["group"],
                "UPDATE ad_v4_candidate_app_search_hint_groups SET association='source_group' WHERE semantic_node_id=:id",
                "search-hint group graph differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_groups", ids["group"],
                "UPDATE ad_v4_candidate_app_search_hint_groups SET canonical_ordinal=3 WHERE semantic_node_id=:id",
                "search-hint group graph differs|semantic node differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_groups", ids["group"],
                "UPDATE ad_v4_candidate_app_search_hint_groups SET manufacturer_assertion_node_id=:target WHERE semantic_node_id=:id",
                "search-hint group graph differs",
                {"target": ids["member_manufacturer"]},
            ),
            (
                "ad_v4_candidate_app_value_assertions", ids["group_manufacturer"],
                "UPDATE ad_v4_candidate_app_value_assertions SET text_value='forged maker' WHERE semantic_node_id=:id",
                "search-hint assertion graph differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_members", ids["member"],
                "UPDATE ad_v4_candidate_app_search_hint_members SET source_designation='forged model' WHERE semantic_node_id=:id",
                "search-hint member graph differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_members", ids["member"],
                "UPDATE ad_v4_candidate_app_search_hint_members SET canonical_ordinal=7 WHERE semantic_node_id=:id",
                "search-hint member graph differs|semantic node differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_members", ids["member"],
                "UPDATE ad_v4_candidate_app_search_hint_members SET designation_identity_mapping_node_id=:target WHERE semantic_node_id=:id",
                "search-hint member graph differs",
                {"target": ids["second_mapping"]},
            ),
            (
                "ad_v4_candidate_app_value_assertions", ids["member_manufacturer"],
                "UPDATE ad_v4_candidate_app_value_assertions SET reason='unavailable' WHERE semantic_node_id=:id",
                "search-hint assertion graph differs",
            ),
            (
                "ad_v4_candidate_app_identity_mappings", ids["mapping"],
                "UPDATE ad_v4_candidate_app_identity_mappings SET evidence_parent_node_id=:target WHERE id=:id",
                "search-hint identity-mapping graph differs",
                {"target": ids["hint"]},
            ),
            (
                "ad_v4_candidate_app_evidence_links", ids["evidence"],
                "UPDATE ad_v4_candidate_app_evidence_links SET purpose='scope_clause' WHERE id=:id",
                "relational graph is incomplete|search-hint evidence graph differs",
            ),
            (
                "ad_v4_candidate_app_search_hint_members", ids["member"],
                "DELETE FROM ad_v4_candidate_app_search_hint_members WHERE semantic_node_id=:id",
                "semantic ownership differs|search-hint member graph differs",
            ),
        ]
        for corruption in corruptions:
            table_name, row_id, statement, expected_error, *extra = corruption
            db.execute(text(
                f"ALTER TABLE {table_name} DISABLE TRIGGER trg_{table_name}_immutable"
            ))
            db.execute(text(statement), {"id": row_id, **(extra[0] if extra else {})})
            with pytest.raises(DBAPIError, match=expected_error):
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            db.rollback()

        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_search_hint_groups "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_search_hint_groups_immutable"
        ))
        with pytest.raises(DBAPIError):
            db.execute(text(
                "UPDATE ad_v4_candidate_app_search_hint_groups SET hint_node_id=:target "
                "WHERE semantic_node_id=:id"
            ), {"id": ids["group"], "target": ids["other_hint"]})
            db.flush()
        db.rollback()

        db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        with pytest.raises(DBAPIError, match="semantic ownership differs|search-hint owners differ"):
            db.add(ADV4CandidateAppSearchHint(
                semantic_node_id=ids["group"], projection_id=projection_id,
                proposal_id=proposal_id, hint_key="forged-extra-hint",
                product_role="airframe",
                source_display_assertion_node_id=ids["display"],
                controlling=False, exhaustive=False,
            ))
            db.flush()
        db.rollback()

        # A direct writer cannot make an extra canonical hint property valid by
        # restamping every envelope, semantic hash, datum, and stored count.
        projection = db.get(ADV4CandidateAppProjection, projection_id)
        candidate = db.get(ADV4CandidateProposal, proposal_id)
        forged = copy.deepcopy(candidate.parsed_json)
        forged_hint = forged["applicabilitySearchHints"][0]
        forged_hint["unsafePromotion"] = "controlling"
        subtree = {
            key: forged[key] for key in (
                "productScopes", "conditionDefinitions", "applicabilityRules",
                "applicabilitySearchHints",
            )
        }
        proposal_bytes = canonical_bytes(forged, CANONICALIZATION_VERSION_V2)
        proposal_hash = hashlib.sha256(DOMAINS_V2["proposal"] + proposal_bytes).hexdigest()
        subtree_bytes = canonical_bytes(subtree, CANONICALIZATION_VERSION_V2)
        subtree_hash = hashlib.sha256(SUBTREE_DOMAIN + subtree_bytes).hexdigest()
        projection_envelope = json.loads(projection.projection_canonical_bytes)
        projection_envelope["proposalCanonicalHash"] = proposal_hash
        projection_envelope["applicabilitySubtreeHash"] = subtree_hash
        projection_bytes = canonical_bytes(projection_envelope, CANONICALIZATION_VERSION_V2)
        hint_node = db.get(ADV4CandidateAppSemanticNode, ids["hint"])
        forged_pointer = "/applicabilitySearchHints/0/unsafePromotion"
        for table_name in (
            "ad_v4_candidate_proposals", "ad_v4_candidate_app_projections",
            "ad_v4_candidate_app_semantic_nodes", "ad_v4_candidate_app_data",
        ):
            db.execute(text(
                f"ALTER TABLE {table_name} DISABLE TRIGGER trg_{table_name}_immutable"
            ))
        candidate.parsed_json = forged
        candidate.canonical_bytes = proposal_bytes
        candidate.canonical_hash = proposal_hash
        projection.proposal_canonical_hash = proposal_hash
        projection.applicability_subtree_bytes = subtree_bytes
        projection.applicability_subtree_hash = subtree_hash
        projection.projection_canonical_bytes = projection_bytes
        projection.projection_hash = hashlib.sha256(PROJECTION_DOMAIN + projection_bytes).hexdigest()
        projection.datum_count += 1
        hint_node.canonical_node_hash = hashlib.sha256(
            canonical_bytes(forged_hint, CANONICALIZATION_VERSION_V2)
        ).hexdigest()
        datum_id, datum_hash = _row_id("avd", "datum", {
            "projectionId": projection.id, "pointer": forged_pointer,
            "kind": "string", "value": "controlling",
        })
        db.add(ADV4CandidateAppDatum(
            id=datum_id, projection_id=projection.id, proposal_id=proposal_id,
            semantic_node_id=hint_node.id, json_pointer=forged_pointer,
            parent_pointer="/applicabilitySearchHints/0",
            property_name="unsafePromotion", array_ordinal=None,
            value_kind="string", string_value="controlling",
            boolean_value=None, value_hash=datum_hash,
        ))
        db.flush()
        with pytest.raises(DBAPIError, match="search-hint owners differ"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    engine.dispose()


def test_23_global_typed_reconstruction_and_dependency_owner_partition() -> None:
    engine = _engine()
    with Session(engine) as db:
        _enable(db)
        projection = _materialize_stored(
            db, validator_version=VALIDATOR_VERSION_V2,
            suffix="global-typed-reconstruction", typed_scope_shapes=True,
            rule_matrix=True, hint_matrix=True, dual_evidence=True,
            supersession_relations=[{
                "relationType": "supersedes",
                "predecessorAdNumber": "2020-99-01",
                "successorAdNumber": "2025-99-01",
                "evidenceKeys": ["ev-official"],
            }],
        )
        candidate = db.get(ADV4CandidateProposal, projection.proposal_id)
        expected = {
            key: candidate.parsed_json[key] for key in (
                "productScopes", "conditionDefinitions", "applicabilityRules",
                "applicabilitySearchHints",
            )
        }
        assert db.scalar(
            text("SELECT paprnav_v4_candidate_app_typed_subtree(:projection)"),
            {"projection": projection.id},
        ) == expected
        assert reconstruct_applicability(db, projection) == expected

        bad_owner = db.scalar(select(ADV4CandidateAppChangeDependency).where(
            ADV4CandidateAppChangeDependency.projection_id == projection.id,
            ADV4CandidateAppChangeDependency.dependency_kind == "outgoing_supersedes",
        ))
        db.commit()
        db.execute(text("""
          INSERT INTO ad_v4_candidate_app_change_dependencies
            (id,projection_id,proposal_id,semantic_node_id,dependency_key,
             dependency_kind,predecessor_ad_number,successor_ad_number,
             resolution_state,unresolved_reason,target_projection_id,
             source_dependency_id,dependency_hash)
          VALUES
            ('avj_global_duplicate',:projection,:proposal,:node,
             'supersedes:forged-global-owner','outgoing_supersedes',
             'forged-global-owner','2025-99-01','unresolved',
             'successor_not_this_proposal',NULL,NULL,repeat('e',64))
        """), {
            "projection": projection.id,
            "proposal": projection.proposal_id,
            "node": bad_owner.semantic_node_id,
        })
        with pytest.raises(DBAPIError, match="semantic ownership differs"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()

        db.execute(text(
            "ALTER TABLE ad_v4_candidate_app_projections "
            "DISABLE TRIGGER trg_ad_v4_candidate_app_projections_immutable"
        ))
        db.execute(text(
            "UPDATE ad_v4_candidate_app_projections "
            "SET semantic_node_count=semantic_node_count+1 WHERE id=:projection"
        ), {"projection": projection.id})
        with pytest.raises(DBAPIError, match="relational graph is incomplete"):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    engine.dispose()
