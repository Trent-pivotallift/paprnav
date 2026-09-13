from __future__ import annotations

import hashlib
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from app.services.ad_v4_obligation_mapping_v1 import DOMAINS, RESOURCE_LIMITS
from app.services.ad_v4_obligations import (
    ObligationIntegrityError,
    obligation_record_bytes,
)


POSTGRES_URL = os.getenv("PAPRNAV_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="PAPRNAV_TEST_POSTGRES_URL required for cross-language serialization",
)
SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "app/db/migrations/sql/20260911_0028_obligation_expectations.sql"
)

COUNTS = {
    "semanticNodeCount": 0,
    "datumCount": 1,
    "evidenceLinkCount": 2,
    "documentCount": 3,
    "valueAssertionCount": 4,
    "requirementCount": 5,
    "actionCount": 6,
    "actionStepCount": 7,
    "actionDocumentRefCount": 8,
    "branchCount": 9,
    "expressionCount": 10,
    "expressionEdgeCount": 11,
    "requirementDependencyCount": 12,
    "timingGroupCount": 13,
    "timingTermCount": 14,
    "recurrenceCount": 15,
    "terminatingEffectCount": 16,
    "terminationEdgeCount": 17,
    "recurrenceGroupCount": 18,
    "recurrenceGroupMemberCount": 19,
    "amocProvisionCount": 20,
    "correctionBindingCount": 21,
}

GOLDEN_RECORDS = {
    "row_with_ordinal": (
        "row",
        {
            "table": "evidence-link",
            "identity": {
                "projectionId": "aox_fixture",
                "semanticNodeId": "aon_fixture",
                "purpose": "requirement_clause",
                "evidenceKey": "evidence-main",
                "ordinal": 0,
            },
        },
    ),
    "projection_envelope": (
        "projection",
        {
            "proposalId": "avp_fixture",
            "directiveId": "directive_fixture",
            "validatorVersion": "paprnav-ad-v4-validator-2",
            "canonicalizationVersion": "paprnav-ad-v4-c14n-2",
            "proposalCanonicalHash": "1" * 64,
            "evidenceBindingHash": "2" * 64,
            "appProjectionId": "avx_fixture",
            "appProjectionHash": "3" * 64,
            "appMaterializerVersion": "paprnav-ad-v4-app-materializer-2",
            "materializerVersion": "paprnav-ad-v4-obligation-materializer-1",
            "mappingVersion": "paprnav-ad-v4-obligation-mapping-1",
            "mappingDigest": "4" * 64,
            "obligationSubtreeHash": "5" * 64,
            "gate": "candidate_only",
            "counts": COUNTS,
        },
    ),
    "request_payload": (
        "request",
        {
            "action": "materialize_ad_v4_obligations",
            "directiveId": "directive_fixture",
            "proposalId": "avp_fixture",
            "appProjectionId": "avx_fixture",
            "validatorVersion": "paprnav-ad-v4-validator-2",
            "canonicalizationVersion": "paprnav-ad-v4-c14n-2",
            "appMaterializerVersion": "paprnav-ad-v4-app-materializer-2",
            "materializerVersion": "paprnav-ad-v4-obligation-materializer-1",
            "mappingVersion": "paprnav-ad-v4-obligation-mapping-1",
            "mappingDigest": "4" * 64,
        },
    ),
    "authorization_claims": (
        "authClaims",
        {
            "actorUserId": "user_fixture",
            "authorizingMembershipId": "membership_fixture",
            "organizationId": "organization_fixture",
            "role": "platform_admin",
            "status": "active",
            "endpointAction": "materialize_ad_v4_obligations",
            "authPolicyVersion": "1",
        },
    ),
    "root_event_with_nulls": (
        "event",
        {
            "eventType": "materialized",
            "projectionId": "aox_fixture",
            "proposalId": "avp_fixture",
            "appProjectionId": "avx_fixture",
            "sequenceNumber": 0,
            "predecessorEventHash": None,
            "proposalCanonicalHash": "1" * 64,
            "evidenceBindingHash": "2" * 64,
            "appProjectionHash": "3" * 64,
            "obligationSubtreeHash": "5" * 64,
            "projectionHash": "6" * 64,
            "correctionBindingSetHash": "7" * 64,
            "causingRequestId": "aoq_fixture",
            "cause": None,
        },
    ),
    "legacy_correction_binding": (
        "legacyApplicabilityRow",
        {
            "table": "correction-binding",
            "identity": {"refId": "avf_fixture", "semanticId": "avn_fixture"},
        },
    ),
    "legacy_correction_root": (
        "legacyApplicabilityRow",
        {
            "table": "correction",
            "identity": {
                "proposalId": "avp_fixture",
                "correctionKey": "correction-main",
            },
        },
    ),
    "legacy_correction_reference": (
        "legacyApplicabilityRow",
        {
            "table": "correction-ref",
            "identity": {
                "correctionId": "avc_fixture",
                "namespace": "requirements",
                "key": "requirement-main",
            },
        },
    ),
    "obligation_correction_binding": (
        "row",
        {
            "table": "correction-binding",
            "identity": {"refId": "avf_fixture", "semanticId": "aon_fixture"},
        },
    ),
    "correction_binding_set": (
        "correctionBindingSet",
        [{
            "bindingId": "avk_fixture",
            "bindingHash": "8" * 64,
            "bindingSlice": "slice_3b",
            "generation": 1,
            "correctionRefId": "avf_fixture",
            "targetProjectionId": "aox_fixture",
            "targetSemanticNodeId": "aon_fixture",
        }],
    ),
    "utf16_key_order": (
        "row",
        {"\ue000": "bmp", "😀": "astral", "array": [None, False, 0, True, 12]},
    ),
    "string_escaping": (
        "row",
        {"value": "line\nquote\"slash\\control\u0001\u2028é"},
    ),
    "empty_prefix_nested": (
        "row",
        {"": {}, "a": [], "aa": {"nested": [None, False, True, 0]}},
    ),
    "control_escapes": (
        "row",
        {"value": "\b\t\n\f\r\"\\/\u0001\u2029é😀"},
    ),
    "integer_max": ("row", {"value": 2_147_483_647}),
}

EXPECTED_DOMAIN_HASHES = {
    "row_with_ordinal": "f180934c53b5ac86e7fbd1c73ec59086a4af73d0833e2c652361910e68e11c33",
    "projection_envelope": "4312387ca8365ca2ee768a56a0b44dbf9a063ee1b753f5165192fa4c2d056fb1",
    "request_payload": "0cee8662d5d4442b671da89aa950a2cc80f55e8b8e099acbc7d393fee35840cc",
    "authorization_claims": "a65a25c47d19b99fe02faf37734975fd049f15e48473a7ead9f5cc51b966e530",
    "root_event_with_nulls": "f32f4f86e7fb6c92c3dfe6aa8fdb5435229752b3f325cf8908a3ea510ccaed64",
    "legacy_correction_binding": "ec72fadb662602a1c843474b40b8f9418ba47eb5df4993c55b4a51e6778386c1",
    "legacy_correction_root": "e5b58d258036f29363dd1c52af03894cd6ec7629337e1f538cec75f71da18d50",
    "legacy_correction_reference": "842c2ca403cb7ca0f0ca4d6e5ee2393bc2a72e9708ee9194a4cc679fed1029d4",
    "obligation_correction_binding": "341d5e12022bb7d13b1dfd11fe0289d329ba2817c9745ab58780ea49d5ec5cc6",
    "correction_binding_set": "6a3ea6c231cac9d1b144a9a0f8217ce1e2367a606aaf4db31938169ff67b0b4a",
    "utf16_key_order": "31348ee7164577045ae74c406fe1d423a42d51789ecf1f457c20097441df0289",
    "string_escaping": "da676d49b1503fbbe31f0b0ba35eef51a28665b6a0439746e916b713565a56fa",
    "empty_prefix_nested": "40264e834cdc92be4308a91b53bf5fa40aa6082adae338a11965d7e516b47373",
    "control_escapes": "b6c568086de358323ea848ae3afd5abbb8c0422e41aa4a7f23c0b2fc30651f1b",
    "integer_max": "18b9be9ff4d1ef7e2cc5367d5041cbc22ffa803fe430186d85977e3ce2eadbd3",
}


@pytest.fixture(scope="module")
def postgres_connection():
    with _installed_serializer_connection() as connection:
        yield connection


@contextmanager
def _installed_serializer_connection():
    engine = create_engine(POSTGRES_URL)
    connection = None
    transaction = None
    try:
        connection = engine.connect()
        transaction = connection.begin()
        with connection.connection.driver_connection.cursor() as cursor:
            cursor.execute(SQL_PATH.read_text(encoding="utf-8"))
        yield connection
    finally:
        if transaction is not None and transaction.is_active:
            transaction.rollback()
        if connection is not None:
            connection.close()
        engine.dispose()


def _postgres_record_bytes(connection, value) -> bytes:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return _postgres_record_bytes_from_payload(connection, payload)


def _postgres_record_bytes_from_payload(connection, payload: str) -> bytes:
    result = connection.execute(
        text(
            "SELECT convert_to("
            "paprnav_v4_obligation_record(CAST(:payload AS jsonb)), 'UTF8')"
        ),
        {"payload": payload},
    ).scalar_one()
    return bytes(result)


@pytest.mark.parametrize("name", GOLDEN_RECORDS)
def test_python_postgresql_internal_record_goldens_are_byte_identical(
    postgres_connection, name,
):
    domain_name, value = GOLDEN_RECORDS[name]
    python_bytes = obligation_record_bytes(value)
    postgres_bytes = _postgres_record_bytes(postgres_connection, value)
    assert postgres_bytes == python_bytes
    expected_hash = hashlib.sha256(DOMAINS[domain_name] + python_bytes).hexdigest()
    assert expected_hash == EXPECTED_DOMAIN_HASHES[name]
    postgres_hash = postgres_connection.execute(
        text(
            "SELECT encode(sha256(CAST(:domain AS bytea) || convert_to("
            "paprnav_v4_obligation_record(CAST(:payload AS jsonb)), 'UTF8')), "
            "'hex')"
        ),
        {
            "domain": DOMAINS[domain_name],
            "payload": json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        },
    ).scalar_one()
    assert postgres_hash == expected_hash


@pytest.mark.parametrize("value", [
    {"value": -1},
    {"value": 1.0},
    {"value": 1.5},
    {"nested": [0, {"value": 0.01}]},
])
def test_postgresql_internal_record_rejects_negative_and_noninteger_numbers(
    postgres_connection, value,
):
    savepoint = postgres_connection.begin_nested()
    try:
        with pytest.raises(DBAPIError, match="unsupported internal canonical number"):
            _postgres_record_bytes(postgres_connection, value)
    finally:
        savepoint.rollback()


def test_python_internal_record_rejects_lone_surrogate_cleanly():
    with pytest.raises(ObligationIntegrityError, match="Unicode scalar"):
        obligation_record_bytes({"value": "\ud800"})


@pytest.mark.parametrize(
    "value",
    [
        {"value": "\x00"},
        {"\x00": "value"},
        {"nested": [{"value": "\x00"}]},
        {"nested": [{"\x00": "value"}]},
    ],
)
def test_postgresql_jsonb_and_python_reject_nul_at_the_common_boundary(
    postgres_connection, value,
):
    with pytest.raises(ObligationIntegrityError, match=r"U\+0000"):
        obligation_record_bytes(value)
    savepoint = postgres_connection.begin_nested()
    try:
        with pytest.raises(DBAPIError, match="unsupported Unicode escape sequence"):
            _postgres_record_bytes(postgres_connection, value)
    finally:
        savepoint.rollback()


def test_python_postgresql_integer_and_depth_boundaries_agree(postgres_connection):
    maximum = RESOURCE_LIMITS["maxInternalInteger"]
    expected = f'{{"value":{maximum}}}'.encode()
    assert obligation_record_bytes({"value": maximum}) == expected
    assert _postgres_record_bytes(postgres_connection, {"value": maximum}) == expected

    for value in (maximum + 1, 10**4500):
        with pytest.raises(ObligationIntegrityError, match="storage limit"):
            obligation_record_bytes({"value": value})
    oversized_payloads = (
        json.dumps({"value": maximum + 1}, separators=(",", ":")),
        '{"value":1' + "0" * 4500 + "}",
    )
    for payload in oversized_payloads:
        savepoint = postgres_connection.begin_nested()
        try:
            with pytest.raises(DBAPIError, match="storage limit"):
                _postgres_record_bytes_from_payload(postgres_connection, payload)
        finally:
            savepoint.rollback()

    at_limit = "leaf"
    for _ in range(RESOURCE_LIMITS["maxDepth"]):
        at_limit = [at_limit]
    assert _postgres_record_bytes(postgres_connection, at_limit) == obligation_record_bytes(at_limit)

    over_limit = [at_limit]
    with pytest.raises(ObligationIntegrityError, match="depth"):
        obligation_record_bytes(over_limit)
    savepoint = postgres_connection.begin_nested()
    try:
        with pytest.raises(DBAPIError, match="depth"):
            _postgres_record_bytes(postgres_connection, over_limit)
    finally:
        savepoint.rollback()


@pytest.mark.parametrize(
    "payload,expected",
    [
        ("-0", b"0"),
        ("1e0", b"1"),
        ("1e1", b"10"),
        ("1.0e1", b"10"),
    ],
)
def test_postgresql_jsonb_integral_numeric_normalization_is_pinned(
    postgres_connection, payload, expected,
):
    assert _postgres_record_bytes_from_payload(postgres_connection, payload) == expected


def test_postgresql_sql_null_is_distinct_from_json_null(postgres_connection):
    assert postgres_connection.execute(
        text("SELECT paprnav_v4_obligation_record(NULL::jsonb)")
    ).scalar_one_or_none() is None
    assert _postgres_record_bytes(postgres_connection, None) == b"null"


def test_generated_sql_setup_failure_always_cleans_resources(monkeypatch):
    state = {"rolled_back": False, "closed": False, "disposed": False}

    class Transaction:
        is_active = True

        def rollback(self):
            state["rolled_back"] = True

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _sql):
            raise RuntimeError("injected installation failure")

    class Connection:
        connection = type(
            "DriverProxy",
            (),
            {"driver_connection": type("Driver", (), {"cursor": lambda _self: Cursor()})()},
        )()

        def begin(self):
            return Transaction()

        def close(self):
            state["closed"] = True

    class Engine:
        def connect(self):
            return Connection()

        def dispose(self):
            state["disposed"] = True

    monkeypatch.setattr(sys.modules[__name__], "create_engine", lambda _url: Engine())
    with pytest.raises(RuntimeError, match="injected installation failure"):
        with _installed_serializer_connection():
            pass
    assert state == {"rolled_back": True, "closed": True, "disposed": True}
