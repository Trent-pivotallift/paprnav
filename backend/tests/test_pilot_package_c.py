from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from fnmatch import fnmatchcase
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
from types import ModuleType, SimpleNamespace
from typing import Any
from urllib.parse import unquote

from alembic.config import Config
import psycopg
import pytest
from sqlalchemy.engine import make_url

from app.core.config import get_settings


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bootstrap() -> ModuleType:
    return load_module("paprnav_package_c_bootstrap", REPO_ROOT / "infra/bootstrap/bootstrap.py")


@pytest.fixture(scope="module")
def release_builder() -> ModuleType:
    return load_module("paprnav_package_c_release_builder", REPO_ROOT / "scripts/build_pilot_release_context.py")


def test_ecs_json_key_becomes_the_actual_application_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    terraform = (REPO_ROOT / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    selector = '${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::'
    assert terraform.count(selector) == 2
    assert 'name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn' not in terraform

    published = json.dumps(
        {"DATABASE_URL": "postgresql+psycopg://paprnav_app:p%40ss@db.internal:5432/paprnav"}
    )
    injected = json.loads(published)["DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", injected)
    get_settings.cache_clear()
    assert get_settings().database_url == injected


@pytest.mark.parametrize(
    "password",
    [
        "admin@%reserved",
        "colon:/question?#brackets[]percent%at@",
    ],
)
def test_admin_credentials_survive_url_and_configparser(
    bootstrap: ModuleType,
    password: str,
) -> None:
    connection = {
        "host": "db.internal",
        "port": 5432,
        "dbname": "paprnav",
        "user": "paprnav_admin",
        "password": password,
        "sslmode": "require",
    }
    environment_url = bootstrap.alembic_environment_url(connection)
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", environment_url)
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.username == "paprnav_admin"
    assert parsed.password == password
    assert parsed.host == "db.internal"


def test_migration_passes_only_configparser_safe_url(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "admin@%reserved"

    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {
                "SecretString": json.dumps(
                    {
                        "username": "paprnav_admin",
                        "password": password,
                    }
                )
            }

    captured: dict[str, str] = {}

    def run(*_: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs["env"])  # type: ignore[arg-type]
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    bootstrap.run_migration(Secrets())
    assert "%%" in captured["DATABASE_URL"]
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", captured["DATABASE_URL"])
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.password == password


def test_admin_connection_uses_only_managed_credentials_and_terraform_endpoint(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "pilot-db.example.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", "paprnav")
    connection = bootstrap.admin_connection(Secrets())
    assert connection == {
        "host": "pilot-db.example.internal",
        "port": 5432,
        "dbname": "paprnav",
        "user": "paprnav_admin",
        "password": "secret",
        "sslmode": "require",
    }


@pytest.mark.parametrize("host", [None, "", " ", "https://db.internal", "db..internal"])
def test_admin_connection_rejects_missing_blank_or_invalid_host(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    host: str | None,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    if host is None:
        monkeypatch.delenv("PAPRNAV_DATABASE_HOST", raising=False)
    else:
        monkeypatch.setenv("PAPRNAV_DATABASE_HOST", host)
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    with pytest.raises(bootstrap.BootstrapError, match="(required environment|database host)"):
        bootstrap.admin_connection(Secrets())


@pytest.mark.parametrize(
    ("port", "message"),
    [
        (None, "required environment"),
        ("", "required environment"),
        ("postgres", "port environment input is invalid"),
        (" 5432", "port environment input is invalid"),
        ("0", "outside 1..65535"),
        ("65536", "outside 1..65535"),
    ],
)
def test_admin_connection_rejects_missing_invalid_or_out_of_range_port(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    port: str | None,
    message: str,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    if port is None:
        monkeypatch.delenv("PAPRNAV_DATABASE_PORT", raising=False)
    else:
        monkeypatch.setenv("PAPRNAV_DATABASE_PORT", port)
    with pytest.raises(bootstrap.BootstrapError, match=message):
        bootstrap.admin_connection(Secrets())


def test_admin_connection_rejects_wrong_username(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "postgres", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    with pytest.raises(bootstrap.BootstrapError, match="wrong username"):
        bootstrap.admin_connection(Secrets())


def test_admin_connection_secret_location_fields_cannot_override_environment(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({
                "username": "paprnav_admin",
                "password": "secret",
                "host": "attacker.example.net",
                "port": 1,
                "dbname": "other",
            })}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", "paprnav")
    connection = bootstrap.admin_connection(Secrets())
    assert (connection["host"], connection["port"], connection["dbname"]) == (
        "db.internal",
        5432,
        "paprnav",
    )


def test_terraform_gates_are_blocking_and_bind_external_dns_identity() -> None:
    variables = (REPO_ROOT / "infra/terraform/variables.tf").read_text(encoding="utf-8")
    main = (REPO_ROOT / "infra/terraform/main.tf").read_text(encoding="utf-8")
    load_balancer = (REPO_ROOT / "infra/terraform/load_balancer.tf").read_text(encoding="utf-8")
    outputs = (REPO_ROOT / "infra/terraform/outputs.tf").read_text(encoding="utf-8")
    versions = (REPO_ROOT / "infra/terraform/versions.tf").read_text(encoding="utf-8")
    assert 'check "external_inputs"' not in variables
    assert 'check "image_repositories"' not in main
    assert 'resource "terraform_data" "deployment_input_gate"' in main
    assert 'resource "terraform_data" "certificate_input_gate"' in main
    assert main.count("precondition {") >= 8
    assert 'variable "dns_zone_name"' in variables
    assert 'variable "route53_zone_id"' not in variables
    assert 'data "aws_route53_zone" "pilot"' not in main
    assert 'resource "aws_route53_record"' not in load_balancer
    assert 'dns_provider   = "squarespace"' in main
    assert "dns_zone_name  = var.dns_zone_name" in main
    assert 'endswith(var.pilot_hostname, ".${lower(trimsuffix(var.dns_zone_name, "."))}")' in main
    assert 'provider    = "Squarespace"' in outputs
    assert 'type        = "CNAME"' in outputs
    assert "value       = aws_lb.main.dns_name" in outputs

    assert 'variable "pilot_certificate_arn"' in variables
    assert 'data "aws_acm_certificate" "pilot"' in main
    for exact_filter in (
        'domain      = var.pilot_hostname',
        'statuses    = ["ISSUED"]',
        'types       = ["AMAZON_ISSUED"]',
        'key_types   = ["RSA_2048"]',
        'tags        = { Project = "paprnav" }',
        'most_recent = false',
    ):
        assert exact_filter in main
    for bound_value in (
        "data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn",
        "data.aws_acm_certificate.pilot.domain == var.pilot_hostname",
        'data.aws_acm_certificate.pilot.status == "ISSUED"',
        'lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"',
        '"arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"',
    ):
        assert bound_value in main
    assert 'resource "aws_acm_certificate"' not in load_balancer
    assert 'resource "aws_acm_certificate_validation"' not in load_balancer
    assert 'resource "aws_route53_record" "certificate_validation"' not in load_balancer
    assert "certificate_arn   = data.aws_acm_certificate.pilot.arn" in load_balancer
    assert "depends_on = [terraform_data.certificate_input_gate]" in load_balancer
    assert 'version = "= 5.100.0"' in versions

    expected = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:"
    good = expected + "a" * 64
    wrong_repository = "527257972989.dkr.ecr.us-east-1.amazonaws.com/other/api@sha256:" + "a" * 64
    mutable = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api:latest"
    assert good.startswith(expected)
    assert not wrong_repository.startswith(expected)
    assert not mutable.startswith(expected)


def test_bootstrap_task_definitions_bind_exact_rds_location_without_overrides() -> None:
    terraform = (REPO_ROOT / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    assert terraform.count(
        '{ name = "PAPRNAV_DATABASE_HOST", value = aws_db_instance.postgres.address }'
    ) == 1
    assert terraform.count(
        '{ name = "PAPRNAV_DATABASE_PORT", value = tostring(aws_db_instance.postgres.port) }'
    ) == 1
    assert "PAPRNAV_DATABASE_HOST" not in terraform.split("bootstrap_common_environment = [", 1)[0]
    assert "PAPRNAV_DATABASE_PORT" not in terraform.split("bootstrap_common_environment = [", 1)[0]
    assert "containerOverrides" not in terraform
    assert "overrides" not in terraform


def one(values: list[Any]) -> Any:
    assert len(values) == 1
    return values[0]


@pytest.fixture(scope="module")
def waf_plan() -> dict[str, Any]:
    # Supply the actual output of `terraform test -json -verbose` from an
    # isolated, current-source module. No handwritten HCL parser or substitute
    # regex/normalization table is used. Terraform also asserts the field and
    # transformation structure directly in package_c.tftest.hcl.
    path = os.getenv("PAPRNAV_PACKAGE_C_TERRAFORM_TEST_JSON")
    if not path:
        pytest.skip("generate the current Package C Terraform mock-plan JSON to run the WAF oracle")
    records = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.startswith("{"):
                continue  # `terraform validate` may precede the JSON stream.
            item = json.loads(line)
            if item.get("type") == "test_plan":
                # Provider schemas are large and are not part of this oracle.
                item["test_plan"].pop("provider_schemas", None)
            if item.get("type") in ("test_plan", "test_summary"):
                records.append(item)
    assert one([item["test_summary"] for item in records if item.get("type") == "test_summary"])["status"] == "pass"
    plan = one([
        item["test_plan"] for item in records
        if item.get("type") == "test_plan" and item.get("@testrun") == "waf_auth_and_upload_contract"
    ])
    return {item["address"]: item["change"]["after"] for item in plan["resource_changes"]}


def active_block(block: dict[str, Any]) -> tuple[str, Any]:
    return one([(key, value) for key, value in block.items() if value not in (None, [], {})])


def waf_matches(statement: dict[str, Any], patterns: dict[str, list[str]], request: dict[str, Any]) -> bool:
    """Evaluate only the emitted WAF subset; unknown constructs fail the test."""
    kind, values = active_block(statement)
    clause = one(values)
    if kind == "and_statement":
        return all(waf_matches(child, patterns, request) for child in clause["statement"])
    if kind == "not_statement":
        return not waf_matches(one(clause["statement"]), patterns, request)
    if kind == "rate_based_statement":
        return waf_matches(one(clause["scope_down_statement"]), patterns, request)
    field, selection = active_block(one(clause["field_to_match"]))
    if field == "method":
        value = request["method"]
    elif field == "uri_path":
        value = request["path"]
    elif field == "single_header":
        value = request["headers"].get(one(selection)["name"], "")
    elif field == "body":
        assert one(selection)["oversize_handling"] == "MATCH"
        value = request["body"]
    else:
        raise AssertionError(f"unsupported WAF field: {field}")
    for transform in sorted(clause["text_transformation"], key=lambda item: item["priority"]):
        operation = transform["type"]
        if operation == "URL_DECODE":
            value = unquote(value)
        elif operation == "LOWERCASE":
            value = value.lower()
        else:
            assert operation == "NONE", f"unsupported WAF transform: {operation}"
    if kind == "regex_pattern_set_reference_statement":
        return any(re.search(pattern, value) is not None for pattern in patterns[clause["arn"]])
    if kind == "byte_match_statement":
        if clause["positional_constraint"] == "EXACTLY":
            return value == clause["search_string"]
        assert clause["positional_constraint"] == "STARTS_WITH"
        return value.startswith(clause["search_string"])
    assert kind == "size_constraint_statement"
    assert clause["comparison_operator"] == "GT"
    return len(value) > clause["size"]


def assert_waf_contract(plan: dict[str, Any]) -> None:
    acl = plan["aws_wafv2_web_acl.pilot"]
    rules = {rule["name"]: rule for rule in acl["rule"]}
    patterns = {
        value["arn"]: [item["regex_string"] for item in value["regular_expression"]]
        for address, value in plan.items() if address.startswith("aws_wafv2_regex_pattern_set.")
    }
    assert len(rules) == 4 and len(patterns) == 3
    assert not one(acl["visibility_config"])["sampled_requests_enabled"]
    assert all(not one(rule["visibility_config"])["sampled_requests_enabled"] for rule in rules.values())
    request = {"method": "POST", "path": "", "headers": {}, "body": b"x" * 8193}
    auth_cases = {
        "login-rate-limit": (30, 100, [
            "/api/v1/auth/login", "/api/v1/auth/login/", "/api/v1/auth/%6cogin",
            "/api/v1/auth/%6Cogin/", "/api/v1/auth%2flogin%2f",
        ]),
        "invitation-rate-limit": (40, 50, [
            "/api/v1/auth/invitations", "/api/v1/auth/invitations/",
            "/api/v1/auth/%69nvitations", "/api/v1/auth/invitations/accept",
            "/api/v1/auth/invitations/accept/", "/api/v1/auth/invitations/%61ccept",
            "/api/v1/auth/invitations/%61ccept/", "/api/v1/auth/invitations%2Faccept%2F",
        ]),
    }
    for name, (priority, limit, paths) in auth_cases.items():
        rule = rules[name]
        assert rule["priority"] == priority and active_block(one(rule["action"]))[0] == "block"
        statement = one(rule["statement"])
        rate = one(statement["rate_based_statement"])
        assert rate["aggregate_key_type"] == "IP" and rate["limit"] == limit
        predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
        assert len(predicates) == 2
        for predicate in predicates:
            kind, values = active_block(predicate)
            value = one(values)
            expected_field, expected_transform = (
                ("method", "NONE") if kind == "byte_match_statement" else ("uri_path", "URL_DECODE")
            )
            assert active_block(one(value["field_to_match"]))[0] == expected_field
            assert value["text_transformation"] == [{"priority": 0, "type": expected_transform}]
        for path in paths:
            assert waf_matches(statement, patterns, {**request, "path": path}), path
            assert not waf_matches(statement, patterns, {**request, "method": "GET", "path": path}), path
        assert not waf_matches(statement, patterns, {**request, "path": paths[0] + "-extra"})
        assert not waf_matches(statement, patterns, {**request, "method": "%50OST", "path": paths[0]})
        other = "/api/v1/auth/invitations/accept" if name == "login-rate-limit" else "/api/v1/auth/login"
        assert not waf_matches(statement, patterns, {**request, "path": other})

    # Bind the raw upload exception AND its body-size/managed-rule context.
    managed = rules["aws-managed-common"]
    assert managed["priority"] == 10
    common = one(one(managed["statement"])["managed_rule_group_statement"])
    assert common["name"] == "AWSManagedRulesCommonRuleSet" and common["vendor_name"] == "AWS"
    override = one(common["rule_action_override"])
    assert override["name"] == "SizeRestrictions_BODY"
    assert active_block(one(override["action_to_use"]))[0] == "count"
    oversize = rules["block-oversize-body-except-reviewed-upload"]
    assert oversize["priority"] == 20 and active_block(one(oversize["action"]))[0] == "block"
    statement = one(oversize["statement"])
    predicates = one(statement["and_statement"])["statement"]
    assert one(predicates[0]["size_constraint_statement"])["size"] == 8192
    exception = one(one(predicates[1]["not_statement"])["statement"])
    upload_predicates = one(exception["and_statement"])["statement"]
    assert len(upload_predicates) == 3
    uri = one(upload_predicates[1]["regex_pattern_set_reference_statement"])
    assert active_block(one(uri["field_to_match"]))[0] == "uri_path"
    assert uri["text_transformation"] == [{"priority": 0, "type": "NONE"}]
    assert patterns[uri["arn"]] == [r"^/api/v1/aircraft/[^/]+/uploads$"]
    upload = {**request, "path": "/api/v1/aircraft/plane/uploads", "headers": {"content-type": "multipart/form-data; boundary=pilot"}}
    assert not waf_matches(statement, patterns, upload)
    for change in (
        {"method": "GET"}, {"path": upload["path"] + "/"},
        {"path": "/api/v1/aircraft/plane/%75ploads"},
        {"path": "/api/v1/aircraft/plane%2Fuploads"},
        {"path": "/api/v1/aircraft/plane/uploads-extra"},
        {"headers": {"content-type": "application/json"}},
        {"path": "/api/v1/auth/invitations/accept"},
    ):
        assert waf_matches(statement, patterns, {**upload, **change}), change
    assert not waf_matches(statement, patterns, {**request, "body": b"x" * 8192})
    assert waf_matches(statement, patterns, request)


def test_waf_generated_auth_normalization_and_raw_upload_exception(waf_plan: dict[str, Any]) -> None:
    assert_waf_contract(waf_plan)
    # The exact remediation-1 defect must be rejected by this same oracle.
    old = deepcopy(waf_plan)
    invitation = next(rule for rule in old["aws_wafv2_web_acl.pilot"]["rule"] if rule["name"] == "invitation-rate-limit")
    rate = one(one(invitation["statement"])["rate_based_statement"])
    predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
    one(predicates[0]["byte_match_statement"])["text_transformation"][0]["type"] = "URL_DECODE"
    one(predicates[1]["regex_pattern_set_reference_statement"])["text_transformation"][0]["type"] = "NONE"
    with pytest.raises(AssertionError):
        assert_waf_contract(old)


def test_acm_policy_is_exactly_read_only_and_account_region_bounded() -> None:
    generator = load_module(
        "paprnav_package_c_policy_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    hostname = "pilot.paprnav.com"
    policy = generator.generate(
        "paprnav.com",
        hostname,
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/ea9571ad-3bc5-4ed5-96d9-070bcad47d60",
    )
    statements = policy["deployPolicySupplement"]["Statement"]
    acm_statements = [item for item in statements if any(action.lower().startswith("acm:") for action in item["Action"])]
    actions = {action for item in acm_statements for action in item["Action"]}
    assert actions == {
        "acm:ListCertificates",
        "acm:DescribeCertificate",
        "acm:ListTagsForCertificate",
        "acm:GetCertificate",
    }
    assert all("*" not in action for action in actions)
    assert all("ExportCertificate" not in action for action in actions)

    inventory = one([item for item in acm_statements if item["Action"] == ["acm:ListCertificates"]])
    metadata = one([item for item in acm_statements if "acm:DescribeCertificate" in item["Action"]])
    assert inventory["Resource"] == "*"
    assert metadata["Resource"] == "arn:aws:acm:us-east-1:527257972989:certificate/*"
    for item in (inventory, metadata):
        assert item["Condition"] == {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    matrix_acm = one([row for row in matrix["rows"] if any(action.startswith("acm:") for action in row["actions"])])
    assert set(matrix_acm["actions"]) == actions
    assert "mutation" not in matrix_acm["condition"].lower()


def test_generated_supplement_is_separate_quota_feasible_and_exactly_attachable() -> None:
    generator = load_module(
        "paprnav_package_e_policy_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    baseline_path = REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json"
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    generated = generator.generate(
        "paprnav.com",
        "pilot.paprnav.com",
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/ea9571ad-3bc5-4ed5-96d9-070bcad47d60",
    )
    assert baseline_path.read_bytes() == baseline_bytes

    compact = lambda value: json.dumps(value, separators=(",", ":"))
    supplement = generated["deployPolicySupplement"]
    invalid_merge = {
        "Version": "2012-10-17",
        "Statement": baseline["Statement"] + supplement["Statement"],
    }
    assert len(compact(baseline)) == 5011
    assert len(compact(supplement)) == 4194
    assert len(compact(invalid_merge)) == 9167
    assert hashlib.sha256(baseline_bytes).hexdigest() == "da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e"
    assert hashlib.sha256(compact(supplement).encode()).hexdigest() == "54e9853b4cb82b6240ddcd05f4b4641124d63d270856acb01e06acd9320eca65"
    assert hashlib.sha256(compact(invalid_merge).encode()).hexdigest() == "adc3893a8a9dab14441f20312e181869f3a662daaf8402880b17cb88635657c2"
    limits = generated["publicationPreconditions"]
    assert len(compact(baseline)) <= limits["customerManagedPolicyCharacterLimit"]
    assert len(compact(supplement)) <= limits["customerManagedPolicyCharacterLimit"]
    assert len(compact(invalid_merge)) > limits["customerManagedPolicyCharacterLimit"]
    assert limits == {
        "customerManagedPolicyCharacterLimit": 6144,
        "requiredAvailableRoleAttachmentSlots": 1,
        "requiredAvailablePolicyVersionSlotsWhenExisting": 1,
        "managedPolicyVersionLimit": 5,
    }

    baseline_arn = "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy"
    supplement_arn = baseline_arn + "-pilot-supplement"
    deploy_role_arn = "arn:aws:iam::527257972989:role/paprnav-terraform-deploy"
    assert generated["baselinePolicyArn"] == baseline_arn
    assert generated["supplementPolicyArn"] == supplement_arn
    assert generated["deployRoleArn"] == deploy_role_arn

    updater = generated["operatorUpdaterProofPolicy"]["Statement"]
    lifecycle = one([item for item in updater if item["Sid"] == "ManageExactPilotSupplement"])
    assert lifecycle["Resource"] == supplement_arn
    assert set(lifecycle["Action"]) == {
        "iam:CreatePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:ListEntitiesForPolicy",
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion",
        "iam:TagPolicy",
    }
    attachment = one([item for item in updater if item["Sid"] == "AttachExactPilotSupplement"])
    assert attachment["Action"] == ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
    assert attachment["Resource"] == deploy_role_arn
    assert attachment["Condition"] == {"ArnEquals": {"iam:PolicyARN": supplement_arn}}
    assert all(baseline_arn != item["Resource"] for item in updater)

    deletion = generated["operatorSeparatelyAuthorizedDeletionProofPolicy"]["Statement"]
    assert deletion == [{
        "Sid": "DeleteExactPilotSupplementOnly",
        "Effect": "Allow",
        "Action": ["iam:DeletePolicyVersion", "iam:DeletePolicy"],
        "Resource": supplement_arn,
    }]
    assert not any(
        action in {"iam:DeletePolicy", "iam:DeletePolicyVersion"}
        for item in updater
        for action in item["Action"]
    )

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    assert matrix["deployPolicyArn"] == baseline_arn
    assert matrix["supplementPolicyArn"] == supplement_arn
    assert matrix["deployRoleArn"] == deploy_role_arn
    assert matrix["publicationPreconditions"] == limits
    assert "baseline remains attached and unchanged" in matrix["effectiveAuthorizationNote"]
    updater_rows = [row for row in matrix["rows"] if row["principal"] == "named IAM policy updater"]
    assert len(updater_rows) == 2
    matrix_lifecycle = one([row for row in updater_rows if "iam:CreatePolicy" in row["actions"]])
    matrix_attachment = one([row for row in updater_rows if "iam:AttachRolePolicy" in row["actions"]])
    assert matrix_lifecycle["resourceTemplate"] == "${SUPPLEMENT_POLICY_ARN}"
    assert matrix_attachment["resourceTemplate"] == "${DEPLOY_ROLE_ARN}"
    assert matrix_attachment["condition"] == "ArnEquals iam:PolicyARN=${SUPPLEMENT_POLICY_ARN}"
    deletion_row = one([
        row for row in matrix["rows"]
        if row["principal"] == "separately authorized IAM rollback/deletion operator"
    ])
    assert set(deletion_row["actions"]) == {"iam:DeletePolicy", "iam:DeletePolicyVersion"}
    assert deletion_row["resourceTemplate"] == "${SUPPLEMENT_POLICY_ARN}"
    assert "Not included in ordinary updater authority" in deletion_row["condition"]


def generated_pilot_policy() -> dict[str, Any]:
    generator = load_module(
        "paprnav_package_e_iam_amendment_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    return generator.generate(
        "paprnav.com",
        "pilot.paprnav.com",
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/ea9571ad-3bc5-4ed5-96d9-070bcad47d60",
    )


def live_pilot_supplement_v1() -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "backend/tests/fixtures/iam/paprnav-terraform-deploy-pilot-supplement-v1.json").read_text(
            encoding="utf-8"
        )
    )


def policy_semantics(document: dict[str, Any]) -> list[str]:
    """Normalize non-semantic IAM scalar/list and statement-order differences."""
    normalized = []
    for item in document["Statement"]:
        statement = {
            "Effect": item["Effect"],
            "Action": sorted(item["Action"] if isinstance(item["Action"], list) else [item["Action"]]),
            "Resource": sorted(item["Resource"] if isinstance(item["Resource"], list) else [item["Resource"]]),
        }
        if "Condition" in item:
            statement["Condition"] = item["Condition"]
        normalized.append(json.dumps(statement, sort_keys=True, separators=(",", ":")))
    return sorted(normalized)


def statement_by_sid(statements: list[dict[str, Any]], sid: str) -> dict[str, Any]:
    return one([item for item in statements if item["Sid"] == sid])


def test_generated_policy_excludes_route53_and_binds_external_dns() -> None:
    generated = generated_pilot_policy()
    assert generated["version"] == "paprnav-pilot-generated-prerequisites-v5"
    assert generated["inputs"]["dnsProvider"] == "Squarespace"
    assert generated["inputs"]["dnsZoneName"] == "paprnav.com"
    assert generated["inputs"]["pilotHostname"] == "pilot.paprnav.com"
    actions = {
        action
        for statement in generated["deployPolicySupplement"]["Statement"]
        for action in statement["Action"]
    }
    assert not any(action.startswith("route53:") for action in actions)
    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text())
    assert matrix["externalDns"] == {
        "provider": "Squarespace",
        "zoneName": "paprnav.com",
        "pilotHostname": "pilot.paprnav.com",
        "recordType": "CNAME",
        "terraformDnsMutation": False,
    }
    assert "route53" not in json.dumps(matrix).lower()


def test_generated_supplement_is_live_v1_plus_only_proven_lifecycle_deltas() -> None:
    fixture_path = REPO_ROOT / "backend/tests/fixtures/iam/paprnav-terraform-deploy-pilot-supplement-v1.json"
    assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == (
        "72050286d45bfabb04a83637e5cfb67f81efe563e7b194001305107838e94100"
    )
    live = live_pilot_supplement_v1()
    generated = generated_pilot_policy()
    desired = generated["deployPolicySupplement"]
    expected = deepcopy(live)
    live_by_sid = {item["Sid"]: item for item in live["Statement"]}
    expected_by_sid = {item["Sid"]: item for item in expected["Statement"]}

    expected_by_sid["AcmCertificateMetadata"]["Action"].append("acm:GetCertificate")
    expected_by_sid["WafAssociatePilotAlb"]["Resource"] = [
        expected_by_sid["WafAssociatePilotAlb"]["Resource"],
        "arn:aws:elasticloadbalancing:us-east-1:527257972989:loadbalancer/app/paprnav-pilot/*",
    ]
    expected["Statement"].append({
        "Sid": "SchedulerInventory",
        "Effect": "Allow",
        "Action": "scheduler:ListSchedules",
        "Resource": "*",
        "Condition": {"StringEquals": {"aws:RequestedRegion": "us-east-1"}},
    })
    assert policy_semantics(desired) == policy_semantics(expected)

    desired_by_sid = {item["Sid"]: item for item in desired["Statement"]}
    assert set(desired_by_sid) == set(live_by_sid) | {"SchedulerInventory"}
    for sid, live_statement in live_by_sid.items():
        desired_statement = desired_by_sid[sid]
        assert desired_statement.get("Condition") == live_statement.get("Condition")
        if sid not in {"AcmCertificateMetadata", "WafAssociatePilotAlb"}:
            assert policy_semantics({"Statement": [desired_statement]}) == policy_semantics(
                {"Statement": [live_statement]}
            )

    authority = load_module("pilot_iam_live_delta", REPO_ROOT / "scripts/pilot_iam_authority.py")
    baseline = json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text())
    missing = set()
    for row in authority.requirements(authority.bound_sources(), generated["inputs"]):
        if row.get("decision") == "allow" and not authority.allowed(
            [baseline, live], row["action"], row["resource"], row["context"]
        ):
            missing.add((row["action"], row["resource"]))
    assert missing == {
        ("acm:GetCertificate", "arn:aws:acm:us-east-1:527257972989:certificate/*"),
        ("scheduler:ListSchedules", "*"),
        ("wafv2:AssociateWebACL", "arn:aws:elasticloadbalancing:us-east-1:527257972989:loadbalancer/app/paprnav-pilot/*"),
        ("wafv2:DisassociateWebACL", "arn:aws:elasticloadbalancing:us-east-1:527257972989:loadbalancer/app/paprnav-pilot/*"),
    }


def test_scheduler_waf_and_updater_actions_are_exactly_scoped() -> None:
    generated = generated_pilot_policy()
    statements = generated["deployPolicySupplement"]["Statement"]
    scheduler_statements = [
        item for item in statements
        if any(action.startswith("scheduler:") for action in item["Action"])
    ]
    scheduler_actions = {action for item in scheduler_statements for action in item["Action"]}
    assert scheduler_actions == {
        "scheduler:ListSchedules",
        "scheduler:GetSchedule",
        "scheduler:CreateSchedule",
        "scheduler:UpdateSchedule",
        "scheduler:DeleteSchedule",
    }
    inventory = statement_by_sid(statements, "SchedulerInventory")
    assert inventory["Resource"] == "*"
    assert inventory["Condition"] == {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}
    schedule = statement_by_sid(statements, "ManageExactWorkerSchedule")
    assert schedule["Resource"] == "arn:aws:scheduler:us-east-1:527257972989:schedule/default/paprnav-pilot-worker"
    pass_role = statement_by_sid(statements, "PassExactWorkerSchedulerRole")
    assert pass_role == {
        "Sid": "PassExactWorkerSchedulerRole",
        "Effect": "Allow",
        "Action": ["iam:PassRole"],
        "Resource": "arn:aws:iam::527257972989:role/paprnav-pilot-worker-scheduler-role",
        "Condition": {"StringEquals": {"iam:PassedToService": "scheduler.amazonaws.com"}},
    }

    waf_tags = [item for item in statements if "wafv2:ListTagsForResource" in item["Action"]]
    assert waf_tags == [statement_by_sid(statements, "WafManagePilotResources")]
    assert waf_tags[0]["Resource"] == [
        "arn:aws:wafv2:us-east-1:527257972989:regional/webacl/paprnav-*/*",
        "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-*/*",
    ]

    updater = statement_by_sid(
        generated["operatorUpdaterProofPolicy"]["Statement"],
        "ManageExactPilotSupplement",
    )
    assert "iam:ListEntitiesForPolicy" in updater["Action"]
    assert updater["Resource"] == generated["supplementPolicyArn"]


def test_secret_value_actions_stay_outside_deploy_and_stop_gate_is_explicit() -> None:
    forbidden = {
        "secretsmanager:UpdateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
    }
    supplement = generated_pilot_policy()["deployPolicySupplement"]["Statement"]
    supplement_actions = {action for item in supplement for action in item["Action"]}
    assert supplement_actions.isdisjoint(forbidden)

    baseline = json.loads(
        (REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text(encoding="utf-8")
    )
    broad_secret = statement_by_sid(baseline["Statement"], "SecretsAndParametersForPaprnNav")
    pilot_secret_arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:/paprnav/pilot/database-url-AbCdEf"
    secret_patterns = [value for value in broad_secret["Resource"] if ":secretsmanager:" in value]
    assert secret_patterns == ["arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav-*"]
    assert not any(fnmatchcase(pilot_secret_arn, pattern) for pattern in secret_patterns)

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    gate = matrix["secretUpdateStopGate"]
    assert set(gate["excludedDeployActions"]) == forbidden
    assert set(gate["terraformResources"]) == {
        "aws_secretsmanager_secret.database_url",
        "aws_secretsmanager_secret.invitation_signing",
        "aws_secretsmanager_secret.first_admin_password",
    }
    secret_lifecycle = one([
        row for row in matrix["terraformLifecycle"]
        if row["terraformTypes"] == ["aws_secretsmanager_secret"]
    ])
    assert "STOP:secretsmanager:UpdateSecret" in secret_lifecycle["lifecycle"]["update"]


def test_policy_matrix_covers_every_terraform_aws_type_and_runtime_boundary() -> None:
    authority = load_module("pilot_iam_coverage", REPO_ROOT / "scripts/pilot_iam_authority.py")
    baseline = json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text())
    result = authority.coverage(generated_pilot_policy(), baseline)
    assert result["instances"] == 96
    assert len(result["requirements"]) == 740
    assert len([row for row in result["requirements"] if row["decision"] == "stop-secret-update"]) == 3
    assert set(row["address"] for row in result["requirements"]) == set(authority.instances(authority.bound_sources()))
    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    actual_types: set[str] = set()
    for path in sorted((REPO_ROOT / "infra/terraform").glob("*.tf")):
        source = path.read_text(encoding="utf-8")
        for kind, resource_type in re.findall(r'^(resource|data) "(aws_[^"]+)"', source, re.MULTILINE):
            actual_types.add(f"data.{resource_type}" if kind == "data" else resource_type)
    covered_types = {
        resource_type
        for row in matrix["terraformLifecycle"]
        for resource_type in row["terraformTypes"]
    }
    local_only = set(matrix["localOnlyTerraformTypes"])
    assert covered_types.isdisjoint(local_only)
    assert covered_types | local_only == actual_types
    for row in matrix["terraformLifecycle"]:
        assert row["authority"]
        if all(value.startswith("data.") for value in row["terraformTypes"]):
            assert set(row["lifecycle"]) == {"read"}
        else:
            assert set(row["lifecycle"]) == {"create", "read", "update", "delete"}
        assert all(actions for actions in row["lifecycle"].values())

    runtime = {row["principal"]: row for row in matrix["runtimeSeparation"]}
    assert runtime["frontend task role"]["permissions"] == []
    assert runtime["API task role"]["permissions"] == [
        "artifact bucket object CRUD/tagging",
        "artifact bucket list",
    ]
    assert "Textract detect/start/get" in runtime["worker task role"]["permissions"]
    assert "PutSecretValue/DescribeSecret for app database secret" in runtime["runtime-role task role"]["permissions"]
    assert all("PutSecretValue" not in permission for permission in runtime["API execution role"]["permissions"])


def test_publication_state_oracle_preserves_pre_state_and_stops_on_ambiguous_use() -> None:
    authority = load_module("pilot_iam_publication", REPO_ROOT / "scripts/pilot_iam_authority.py")
    for exists, attached, branch in [(False, False, "absent"), (True, False, "detached-existing"), (True, True, "attached-existing")]:
        pre = iam_snapshot(authority, exists, attached)
        result = authority.publication(pre, "b" * 64)
        assert result["branch"] == branch and result["mutationAuthorized"] is False
        assert [s["action"] for s in result["steps"]] == (["iam:CreatePolicyVersion"] if exists else ["iam:CreatePolicy"]) + ([] if attached else ["iam:AttachRolePolicy"])
        assert authority.publication(pre, "b" * 64, deepcopy(pre))["steps"] == []


@pytest.fixture
def iam_authority() -> ModuleType:
    return load_module("pilot_iam_authority_test", REPO_ROOT / "scripts/pilot_iam_authority.py")


@pytest.mark.parametrize("mutation", ["missing-action", "wrong-resource", "wrong-condition", "secret-values", "runtime"])
def test_iam_executable_coverage_rejects_policy_and_runtime_mutations(iam_authority: ModuleType, mutation: str) -> None:
    generated = generated_pilot_policy()
    baseline = json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text())
    schedule = statement_by_sid(generated["deployPolicySupplement"]["Statement"], "ManageExactWorkerSchedule")
    if mutation == "missing-action":
        schedule["Action"].remove("scheduler:UpdateSchedule")
    elif mutation == "wrong-resource":
        schedule["Resource"] += "-other"
    elif mutation == "wrong-condition":
        statement_by_sid(generated["deployPolicySupplement"]["Statement"], "PassExactWorkerSchedulerRole")["Condition"]["StringEquals"]["iam:PassedToService"] = "ecs-tasks.amazonaws.com"
    elif mutation == "secret-values":
        statement_by_sid(baseline["Statement"], "SecretsAndParametersForPaprnNav")["Resource"].append("arn:aws:secretsmanager:us-east-1:527257972989:secret:/paprnav/pilot/*")
    else:
        sources = iam_authority.bound_sources()
        sources["ecs_runtime.tf"] = sources["ecs_runtime.tf"].replace('actions   = ["s3:GetObject",', 'actions   = ["secretsmanager:GetSecretValue",', 1)
        with pytest.raises(iam_authority.Stop, match="runtime authority drift"):
            iam_authority.runtime_boundary(sources)
        return
    with pytest.raises(iam_authority.Stop):
        iam_authority.coverage(generated, baseline)


def test_iam_source_drift_and_uncatalogued_instances_fail_closed(iam_authority: ModuleType, tmp_path: Path) -> None:
    import shutil
    shutil.copytree(REPO_ROOT / "infra/terraform", tmp_path / "infra/terraform", ignore=shutil.ignore_patterns(".terraform"))
    (tmp_path / "infra/aws-iam").mkdir()
    shutil.copy(REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json", tmp_path / "infra/aws-iam")
    path = tmp_path / "infra/terraform/ecs_runtime.tf"
    path.write_text(path.read_text().replace("worker-task-role", "other-task-role") + "\n# changed\n")
    with pytest.raises(iam_authority.Stop, match="source drift"):
        iam_authority.bound_sources(tmp_path)
    sources = iam_authority.bound_sources()
    sources["new.tf"] = 'resource "aws_ses_domain_identity" "unreviewed" {}'
    with pytest.raises(iam_authority.Stop, match="uncatalogued"):
        iam_authority.requirements(sources, generated_pilot_policy()["inputs"])


def bind_plan_semantics(authority: ModuleType, plan: dict) -> None:
    """Add the small known-value surface consumed by the production plan gate."""
    changes = {item["address"]: item for item in plan["resource_changes"]}

    def after(address: str) -> dict:
        return changes[address]["change"]["after"]

    def policy(*statements: dict) -> str:
        return json.dumps({"Version": "2012-10-17", "Statement": list(statements)})

    ecs_trust = policy({"Effect": "Allow", "Action": "sts:AssumeRole", "Principal": {"Service": "ecs-tasks.amazonaws.com"}})
    scheduler_trust = policy({"Effect": "Allow", "Action": "sts:AssumeRole", "Principal": {"Service": "scheduler.amazonaws.com"}})
    role_names = {
        **{f'aws_iam_role.ecs_execution["{name}"]': f"paprnav-pilot-{name}-execution-role" for name in ("api", "frontend", "worker", "bootstrap")},
        "aws_iam_role.api_task": "paprnav-pilot-api-task-role",
        "aws_iam_role.frontend_task": "paprnav-pilot-frontend-task-role",
        "aws_iam_role.worker_task": "paprnav-pilot-worker-task-role",
        "aws_iam_role.migration_reference_task": "paprnav-pilot-migration-reference-task-role",
        "aws_iam_role.runtime_role_task": "paprnav-pilot-runtime-role-task-role",
        "aws_iam_role.first_admin_task": "paprnav-pilot-first-admin-task-role",
        "aws_iam_role.worker_scheduler": "paprnav-pilot-worker-scheduler-role",
    }
    role_arns = {}
    for address, name in role_names.items():
        role_arns[address] = f"arn:aws:iam::{authority.ACCOUNT}:role/{name}"
        after(address).update(name=name, arn=role_arns[address], assume_role_policy=scheduler_trust if address.endswith("worker_scheduler") else ecs_trust)
    for name in ("api", "frontend", "worker", "bootstrap"):
        after(f'aws_iam_role_policy_attachment.ecs_execution_managed["{name}"]').update(
            role=role_names[f'aws_iam_role.ecs_execution["{name}"]'],
            policy_arn=authority.ECS_EXECUTION_POLICY_ARN,
        )

    secret_arns = {}
    for index, (address, name) in enumerate(authority.SECRET_NAMES.items(), 1):
        secret_arns[address] = f"arn:aws:secretsmanager:{authority.REGION}:{authority.ACCOUNT}:secret:{name}-AbCdE{index}"
        values = after(address)
        values["arn"] = secret_arns[address]
        before = changes[address]["change"].get("before")
        if isinstance(before, dict):
            before["arn"] = secret_arns[address]
        if values.get("name") == "irrelevant":
            values["name"] = name
    master_secret = f"arn:aws:secretsmanager:{authority.REGION}:{authority.ACCOUNT}:secret:rds!db-AbCdEf"
    after("aws_db_instance.postgres")["master_user_secret"] = [{"secret_arn": master_secret}]
    bucket = f"arn:aws:s3:::paprnav-pilot-artifacts-{authority.ACCOUNT}"
    after("aws_s3_bucket.app_artifacts")["arn"] = bucket
    cluster = f"arn:aws:ecs:{authority.REGION}:{authority.ACCOUNT}:cluster/paprnav-pilot"
    after("aws_ecs_cluster.main")["arn"] = cluster

    task_roles = {
        "aws_ecs_task_definition.api": ("api", "api", "api_task"),
        "aws_ecs_task_definition.frontend": ("frontend", "frontend", "frontend_task"),
        "aws_ecs_task_definition.worker": ("worker", "worker", "worker_task"),
        'aws_ecs_task_definition.bootstrap["migration"]': ("bootstrap-migration", "bootstrap", "migration_reference_task"),
        'aws_ecs_task_definition.bootstrap["reference"]': ("bootstrap-reference", "bootstrap", "migration_reference_task"),
        'aws_ecs_task_definition.bootstrap["runtime-role"]': ("bootstrap-runtime-role", "bootstrap", "runtime_role_task"),
        'aws_ecs_task_definition.bootstrap["first-admin"]': ("bootstrap-first-admin", "bootstrap", "first_admin_task"),
    }
    task_arns = {}
    for address, (suffix, execution, task) in task_roles.items():
        family = f"paprnav-pilot-{suffix}"
        task_arns[address] = f"arn:aws:ecs:{authority.REGION}:{authority.ACCOUNT}:task-definition/{family}:1"
        after(address).update(
            family=family,
            arn=task_arns[address],
            execution_role_arn=role_arns[f'aws_iam_role.ecs_execution["{execution}"]'],
            task_role_arn=role_arns[f"aws_iam_role.{task}"],
        )

    reads = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    artifact = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
    policies = {
        "aws_iam_role_policy.api_execution_secrets": ("paprnav-pilot-api-execution-secrets", role_names['aws_iam_role.ecs_execution["api"]'], policy({"Effect": "Allow", "Action": reads, "Resource": [secret_arns["aws_secretsmanager_secret.database_url"], secret_arns["aws_secretsmanager_secret.invitation_signing"]]})),
        "aws_iam_role_policy.worker_execution_secrets": ("paprnav-pilot-worker-execution-secrets", role_names['aws_iam_role.ecs_execution["worker"]'], policy({"Effect": "Allow", "Action": reads, "Resource": secret_arns["aws_secretsmanager_secret.database_url"]})),
        "aws_iam_role_policy.api_task": ("paprnav-pilot-api-task", role_names["aws_iam_role.api_task"], policy({"Effect": "Allow", "Action": artifact, "Resource": f"{bucket}/*"}, {"Effect": "Allow", "Action": "s3:ListBucket", "Resource": bucket})),
        "aws_iam_role_policy.worker_task": ("paprnav-pilot-worker-task", role_names["aws_iam_role.worker_task"], policy({"Effect": "Allow", "Action": artifact, "Resource": f"{bucket}/*"}, {"Effect": "Allow", "Action": "s3:ListBucket", "Resource": bucket}, {"Effect": "Allow", "Action": ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"], "Resource": "*"})),
        "aws_iam_role_policy.migration_reference_secrets": ("paprnav-pilot-migration-reference-secrets", role_names["aws_iam_role.migration_reference_task"], policy({"Effect": "Allow", "Action": reads, "Resource": master_secret})),
        "aws_iam_role_policy.runtime_role_secrets": ("paprnav-pilot-runtime-role-secrets", role_names["aws_iam_role.runtime_role_task"], policy({"Effect": "Allow", "Action": reads, "Resource": master_secret}, {"Effect": "Allow", "Action": ["secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"], "Resource": secret_arns["aws_secretsmanager_secret.database_url"]})),
        "aws_iam_role_policy.first_admin_secrets": ("paprnav-pilot-first-admin-secrets", role_names["aws_iam_role.first_admin_task"], policy({"Effect": "Allow", "Action": reads, "Resource": [master_secret, secret_arns["aws_secretsmanager_secret.first_admin_password"]]})),
        "aws_iam_role_policy.worker_scheduler": ("paprnav-pilot-worker-scheduler", role_names["aws_iam_role.worker_scheduler"], policy({"Effect": "Allow", "Action": "ecs:RunTask", "Resource": task_arns["aws_ecs_task_definition.worker"], "Condition": {"ArnEquals": {"ecs:cluster": cluster}}}, {"Effect": "Allow", "Action": "iam:PassRole", "Resource": [role_arns['aws_iam_role.ecs_execution["worker"]'], role_arns["aws_iam_role.worker_task"]], "Condition": {"StringEquals": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}}})),
    }
    for address, (name, role, document) in policies.items():
        after(address).update(name=name, role=role, policy=document)

    after("aws_scheduler_schedule.worker").update(
        name="paprnav-pilot-worker",
        group_name="default",
        state="DISABLED",
        target=[{
            "arn": cluster,
            "role_arn": role_arns["aws_iam_role.worker_scheduler"],
            "ecs_parameters": [{"task_definition_arn": task_arns["aws_ecs_task_definition.worker"]}],
        }],
    )
    after("aws_lb_listener.https").update(certificate_arn=authority.PILOT_CERTIFICATE_ARN, protocol="HTTPS", port=443)
    plan["resource_changes"].append({
        "address": "data.aws_acm_certificate.pilot",
        "type": "aws_acm_certificate",
        "change": {
            "actions": ["read"],
            "before": None,
            "after_unknown": {},
            "after": {
                "arn": authority.PILOT_CERTIFICATE_ARN,
                "domain": authority.PILOT_HOSTNAME,
                "status": "ISSUED",
                "most_recent": False,
                "statuses": ["ISSUED"],
                "types": ["AMAZON_ISSUED"],
                "key_types": ["RSA_2048"],
                "tags": {"Project": "paprnav", "Environment": "pilot"},
            },
        },
    })
    dns = {
        "provider": "Squarespace",
        "name": authority.PILOT_HOSTNAME,
        "type": "CNAME",
        "value": "paprnav-pilot-123456.us-east-1.elb.amazonaws.com",
        "ttl_seconds": 300,
    }
    plan["output_changes"] = {"pilot_dns_cname": {"actions": ["create"], "before": None, "after": dns, "after_unknown": False}}
    plan["planned_values"] = {"outputs": {"pilot_dns_cname": {"sensitive": False, "type": ["object", {}], "value": deepcopy(dns)}}}


def secret_plan(authority: ModuleType, create: bool = False) -> dict:
    generated = generated_pilot_policy()
    plan = {"format_version": "1.2", "complete": True, "errored": False, "variables": {k: {"value": v} for k, v in {
        "project": "paprnav", "environment": "pilot", "aws_region": authority.REGION, "aws_account_id": authority.ACCOUNT,
        "external_mode": True, "pilot_hostname": authority.PILOT_HOSTNAME, "dns_zone_name": authority.DNS_ZONE_NAME,
        "pilot_certificate_arn": authority.PILOT_CERTIFICATE_ARN,
        "policy_updater_principal_arn": generated["inputs"]["operatorUpdaterPrincipalArn"],
    }.items()}, "resource_changes": []}
    for address, typ in authority.instances(authority.bound_sources()).items():
        if typ == "local" or typ.startswith("data."):
            continue
        values = {"name": authority.SECRET_NAMES.get(address, "irrelevant"), "description": "reviewed description", "kms_key_id": None, "tags": {}, "tags_all": {"Project": "paprnav"}}
        plan["resource_changes"].append({"address": address, "type": typ, "change": {"actions": ["create"] if create else ["no-op"], "before": None if create else deepcopy(values), "after": values, "after_unknown": {"arn": True, "id": True, "policy": True, "replica": True, "name_prefix": True} if create and address in authority.SECRET_NAMES else {}}})
    bind_plan_semantics(authority, plan)
    return plan


def run_secret_plan(authority: ModuleType, plan: dict) -> dict:
    return authority.validate_plan_changes(plan, generated_pilot_policy(), json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text()))


@pytest.mark.parametrize("create", [False, True])
def test_iam_plan_gate_allows_create_and_tag_only(iam_authority: ModuleType, create: bool) -> None:
    plan = secret_plan(iam_authority, create)
    if not create:
        for item in plan["resource_changes"]:
            if item["address"] in iam_authority.SECRET_NAMES:
                item["change"]["actions"] = ["update"]
                item["change"]["after"]["tags"] = {"Owner": "reviewed"}
    assert run_secret_plan(iam_authority, plan)["decision"] == "saved-plan-binding-required"


@pytest.mark.parametrize("mutation", ["description", "kms_key_id", "unknown-description", "unknown-tags", "unknown-object", "missing-metadata", "legacy-name", "legacy-before", "legacy-arn", "missing-secret", "unknown-variable", "new-secret", "replacement", "targeted", "mixed"])
def test_iam_plan_gate_rejects_whole_plan_before_any_apply(iam_authority: ModuleType, mutation: str) -> None:
    plan = secret_plan(iam_authority)
    item = next(x for x in plan["resource_changes"] if x["address"] == "aws_secretsmanager_secret.database_url")
    change = item["change"]
    change["actions"] = ["update"]
    if mutation in {"description", "kms_key_id"}:
        change["after"][mutation] = "changed"
    elif mutation.startswith("unknown-") and mutation != "unknown-variable":
        field = mutation.removeprefix("unknown-")
        change["after_unknown"] = True if field == "object" else {field: True}
    elif mutation == "missing-metadata":
        change["after"].pop("kms_key_id")
    elif mutation in {"legacy-name", "legacy-before"}:
        change["before" if mutation == "legacy-before" else "after"]["name"] = "paprnav-pilot-database-url"
    elif mutation == "legacy-arn":
        change["after"]["arn"] = f"arn:aws:secretsmanager:{iam_authority.REGION}:{iam_authority.ACCOUNT}:secret:paprnav-pilot-database-url-AbCdEf"
    elif mutation == "missing-secret":
        plan["resource_changes"].remove(item)
    elif mutation == "unknown-variable":
        plan["variables"].pop("project")
    elif mutation == "new-secret":
        item["address"] += "_other"
    elif mutation == "replacement":
        change["actions"] = ["delete", "create"]
    elif mutation == "targeted":
        plan["complete"] = False
    elif mutation == "mixed":
        change["after"]["description"] = "requires UpdateSecret"
        next(x for x in plan["resource_changes"] if x["address"] == "aws_ecs_cluster.main")["change"]["actions"] = ["update"]
    with pytest.raises(iam_authority.Stop):
        run_secret_plan(iam_authority, plan)


@pytest.mark.parametrize(
    "mutation",
    ["route53-input", "certificate", "unknown-policy", "wildcard-runtime", "principal", "task-role", "scheduler", "dns-unknown", "deferred"],
)
def test_iam_plan_semantics_rejects_unreviewed_runtime_and_handoff_values(
    iam_authority: ModuleType,
    mutation: str,
) -> None:
    plan = secret_plan(iam_authority)
    changes = {item["address"]: item for item in plan["resource_changes"]}
    if mutation == "route53-input":
        plan["variables"]["route53_zone_id"] = {"value": "ZSTALE"}
    elif mutation == "certificate":
        changes["aws_lb_listener.https"]["change"]["after"]["certificate_arn"] += "-other"
    elif mutation in {"unknown-policy", "wildcard-runtime"}:
        change = changes["aws_iam_role_policy.api_task"]["change"]
        if mutation == "unknown-policy":
            change["after"]["policy"] = None
            change["after_unknown"] = {"policy": True}
        else:
            document = json.loads(change["after"]["policy"])
            document["Statement"][0]["Resource"] = "*"
            change["after"]["policy"] = json.dumps(document)
    elif mutation == "principal":
        role = changes["aws_iam_role.worker_scheduler"]["change"]["after"]
        document = json.loads(role["assume_role_policy"])
        document["Statement"][0]["Principal"]["Service"] = "*"
        role["assume_role_policy"] = json.dumps(document)
    elif mutation == "task-role":
        changes["aws_ecs_task_definition.api"]["change"]["after"]["task_role_arn"] = changes["aws_iam_role.frontend_task"]["change"]["after"]["arn"]
    elif mutation == "scheduler":
        target = changes["aws_scheduler_schedule.worker"]["change"]["after"]["target"][0]
        target["role_arn"] = changes["aws_iam_role.api_task"]["change"]["after"]["arn"]
    elif mutation == "dns-unknown":
        plan["output_changes"]["pilot_dns_cname"]["after_unknown"] = {"value": True}
    else:
        plan["deferred_changes"] = [{"reason": "provider_config_unknown"}]
    with pytest.raises(iam_authority.Stop):
        run_secret_plan(iam_authority, plan)


def iam_snapshot(authority: ModuleType, exists: bool = True, attached: bool = False) -> dict:
    def page(request: dict, **response: object) -> list:
        return [{"request": request, "response": {"IsTruncated": False, **response}}]
    state = {"policyArn": authority.POLICY, "roleArn": authority.ROLE, "quotas": {"rolePolicyLimit": 10, "policyCount": 2, "policyLimit": 1500},
             "rolePolicyPages": page({"RoleName": authority.ROLE.rsplit("/", 1)[1]}, AttachedPolicies=[{"PolicyArn": authority.POLICY.removesuffix("-pilot-supplement")}] + ([{"PolicyArn": authority.POLICY}] if attached else [])),
             "policy": None, "getPolicyError": "NoSuchEntity", "entityPages": {}, "versionPages": []}
    if exists:
        state["getPolicyError"] = None
        state["policy"] = {"Arn": authority.POLICY, "PolicyId": "ANPAreviewed", "DefaultVersionId": "v1", "AttachmentCount": int(attached), "PermissionsBoundaryUsageCount": 0}
        state["versionPages"] = page({"PolicyArn": authority.POLICY}, Versions=[{"VersionId": "v1", "IsDefaultVersion": True, "DocumentSha256": "a" * 64}])
        for usage in ("PermissionsPolicy", "PermissionsBoundary"):
            state["entityPages"][usage] = page({"PolicyArn": authority.POLICY, "PolicyUsageFilter": usage}, PolicyUsers=[], PolicyGroups=[], PolicyRoles=[{"RoleName": authority.ROLE.rsplit("/", 1)[1]}] if attached and usage == "PermissionsPolicy" else [])
    return state


@pytest.mark.parametrize("usage", ["PermissionsPolicy", "PermissionsBoundary"])
@pytest.mark.parametrize("case", ["valid-pagination", "later-page", "incomplete", "wrong-marker", "wrong-filter"])
def test_iam_publication_exhausts_both_consumer_page_chains(iam_authority: ModuleType, usage: str, case: str) -> None:
    state = iam_snapshot(iam_authority)
    pages = state["entityPages"][usage]
    last = deepcopy(pages[0])
    last["request"]["Marker"] = "next"
    pages[0]["response"].update(IsTruncated=True, Marker="next")
    if case != "incomplete":
        pages.append(last)
    if case == "later-page":
        last["response"]["PolicyRoles"] = [{"RoleName": "unexpected-consumer"}]
    if case == "wrong-marker":
        last["request"]["Marker"] = "wrong"
    if case == "wrong-filter":
        last["request"]["PolicyUsageFilter"] = "All"
    if case == "valid-pagination":
        assert iam_authority.publication(state, "b" * 64)["status"] == "pass"
    else:
        with pytest.raises(iam_authority.Stop):
            iam_authority.publication(state, "b" * 64)


@pytest.mark.parametrize("case", ["role-quota", "policy-quota", "version-quota", "boundary", "shared", "denied", "incomplete-versions", "incomplete-attachments"])
def test_iam_publication_preflight_rejects_unproved_or_exhausted_state(iam_authority: ModuleType, case: str) -> None:
    state = iam_snapshot(iam_authority, exists=case not in {"policy-quota", "denied"})
    if case == "role-quota":
        state["quotas"]["rolePolicyLimit"] = 0
    elif case == "policy-quota":
        state["quotas"]["policyLimit"] = state["quotas"]["policyCount"]
    elif case == "version-quota":
        state["versionPages"][0]["response"]["Versions"].extend({"VersionId": f"v{x}", "IsDefaultVersion": False, "DocumentSha256": "c" * 64} for x in range(2, 6))
    elif case in {"boundary", "shared"}:
        state["entityPages"]["PermissionsBoundary" if case == "boundary" else "PermissionsPolicy"][0]["response"]["PolicyUsers"] = [{"UserName": "unexpected"}]
    elif case == "denied":
        state["getPolicyError"] = "AccessDenied"
    else:
        state["versionPages" if case == "incomplete-versions" else "rolePolicyPages"][0]["response"].update(IsTruncated=True, Marker="lost")
    with pytest.raises(iam_authority.Stop):
        iam_authority.publication(state, "b" * 64)


@pytest.mark.parametrize("pre_exists,pre_attached", [(False, False), (True, False), (True, True)])
@pytest.mark.parametrize("stage", ["no-call", "created-version", "default-changed", "attached"])
def test_iam_ambiguous_recovery_uses_observed_default_and_attachment(iam_authority: ModuleType, pre_exists: bool, pre_attached: bool, stage: str) -> None:
    pre = iam_snapshot(iam_authority, pre_exists, pre_attached)
    observed = deepcopy(pre)
    if stage != "no-call":
        observed = iam_snapshot(iam_authority, True, pre_attached or stage == "attached")
        versions = observed["versionPages"][0]["response"]["Versions"]
        if pre_exists:
            versions.append({"VersionId": "v2", "IsDefaultVersion": stage != "created-version", "DocumentSha256": "b" * 64})
            if stage != "created-version":
                versions[0]["IsDefaultVersion"] = False
                observed["policy"]["DefaultVersionId"] = "v2"
        else:
            versions[0]["DocumentSha256"] = "b" * 64
    result = iam_authority.publication(pre, "b" * 64, observed)
    actions = [x["action"] for x in result["steps"]]
    assert ("iam:SetDefaultPolicyVersion" in actions) == (pre_exists and stage in {"default-changed", "attached"})
    assert ("iam:DetachRolePolicy" in actions) == (not pre_attached and stage == "attached")
    assert all("Delete" not in action for action in actions)
    assert result["targetDefault"] == ("v1" if pre_exists else None)
    assert result["targetAttached"] == pre_attached


def test_iam_recovery_restores_lost_attachment_and_rejects_unattributed_versions(iam_authority: ModuleType) -> None:
    pre = iam_snapshot(iam_authority, True, True)
    observed = iam_snapshot(iam_authority, True, False)
    result = iam_authority.publication(pre, "b" * 64, observed)
    assert [x["action"] for x in result["steps"]] == ["iam:AttachRolePolicy"]
    observed["versionPages"][0]["response"]["Versions"][0]["DocumentSha256"] = "f" * 64
    with pytest.raises(iam_authority.Stop, match="prior version"):
        iam_authority.publication(pre, "b" * 64, observed)


def test_iam_cli_commands_use_shared_authority_and_fail_closed(iam_authority: ModuleType, tmp_path: Path) -> None:
    import subprocess
    generated_path, plan_path, pre_path = [tmp_path / name for name in ("generated.json", "plan.json", "pre.json")]
    generated_path.write_text(json.dumps(generated_pilot_policy()))
    plan_path.write_text(json.dumps(secret_plan(iam_authority, True)))
    pre_path.write_text(json.dumps(iam_snapshot(iam_authority)))
    saved_path = tmp_path / "plan.tfplan"
    saved_path.write_bytes(saved_plan_archive(iam_authority.bound_sources()))
    # Stub only the external Terraform decoder. Core archive/configuration and
    # JSON agreement checks execute in production. This is not a live AWS plan.
    viewer = tmp_path / "terraform-reader"
    viewer.write_text(f"#!{sys.executable}\nimport pathlib,sys\nprint(pathlib.Path(sys.argv[-1]).with_suffix('.json').read_text())\n")
    viewer.chmod(0o700)
    common = [sys.executable, str(REPO_ROOT / "scripts/pilot_iam_authority.py")]
    commands = [
        ["coverage", "--generated", str(generated_path)],
        ["plan", "--generated", str(generated_path), "--plan-json", str(plan_path), "--saved-plan", str(saved_path), "--terraform-bin", str(viewer)],
        ["publication", "--pre-state", str(pre_path), "--candidate-sha256", "b" * 64],
        ["recovery", "--pre-state", str(pre_path), "--observed-state", str(pre_path), "--candidate-sha256", "b" * 64],
    ]
    for command in commands:
        result = subprocess.run(common + command, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["status"] == "pass"
    plan_path.write_text("{}")
    result = subprocess.run(common + commands[1], capture_output=True, text=True, check=False)
    assert result.returncode == 2 and json.loads(result.stdout)["status"] == "stop"
    result = subprocess.run(common + ["recovery", "--pre-state", str(pre_path), "--candidate-sha256", "b" * 64], capture_output=True, text=True, check=False)
    assert result.returncode == 2 and "observed state" in json.loads(result.stdout)["reason"]


def saved_plan_archive(sources: dict[str, str]) -> bytes:
    import io
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("tfplan", b"external decoder fixture")
        archive.writestr("tfconfig/modules.json", json.dumps([{"Key": "", "Dir": "."}]))
        for name, source in sources.items():
            archive.writestr("tfconfig/m-/" + name, source)
    return buffer.getvalue()


@pytest.mark.parametrize("mutation", ["suffix-grant", "conditional-grant", "scheduler-star", "missing-acm-get", "route53-grant", "literal-brackets"])
def test_iam_reviewed_policy_construction_rejects_all_contract_changes(iam_authority: ModuleType, mutation: str) -> None:
    generated = generated_pilot_policy()
    statements = generated["deployPolicySupplement"]["Statement"]
    if mutation in {"suffix-grant", "conditional-grant"}:
        stmt = {"Effect": "Allow", "Action": list(iam_authority.EXCLUDED), "Resource": "arn:aws:secretsmanager:us-east-1:527257972989:secret:/paprnav/pilot/database-url-ZZZZZZ"}
        if mutation == "conditional-grant":
            stmt["Condition"] = {"StringEquals": {"aws:PrincipalTag/Unexpected": "yes"}}
        statements.append(stmt)
        with pytest.raises(iam_authority.Stop, match="forbidden secret-domain"):
            iam_authority.forbidden_secret_overlap([generated["deployPolicySupplement"]])
    elif mutation == "scheduler-star":
        statement_by_sid(statements, "ManageExactWorkerSchedule")["Resource"] = "*"
    elif mutation == "missing-acm-get":
        statement_by_sid(statements, "AcmCertificateMetadata")["Action"].remove("acm:GetCertificate")
    elif mutation == "route53-grant":
        statements.append({"Effect": "Allow", "Action": ["route53:ListHostedZones"], "Resource": "*"})
    else:
        statement_by_sid(statements, "ManageExactWorkerSchedule")["Resource"] = "arn:aws:scheduler:us-east-1:527257972989:schedule/default/paprnav-pilot-worke[r]"
    with pytest.raises(iam_authority.Stop, match="reviewed construction"):
        iam_authority.coverage(generated, json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text()))


def test_iam_glob_languages_and_missing_context_deny(iam_authority: ModuleType) -> None:
    assert not iam_authority.iam_match("paprnav-pilot-worke[r]", "paprnav-pilot-worker")
    assert iam_authority.iam_match("paprnav-pilot-worke[r]", "paprnav-pilot-worke[r]")
    assert iam_authority.iam_match("paprnav-?ilot-*", "paprnav-pilot-worker")
    assert iam_authority.resource_covers("arn:*:secret:/paprnav/pilot/*", "arn:aws:secret:/paprnav/pilot/name-??????")
    assert not iam_authority.resource_covers("name-ZZZZZZ", "name-*")
    assert iam_authority.pattern_relation("name-ZZZZZZ", "name-*", False)
    assert not iam_authority.pattern_relation("name-[A]", "name-A", False)
    policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "scheduler:DeleteSchedule", "Resource": "*"},
        {"Effect": "Deny", "Action": "scheduler:DeleteSchedule", "Resource": "*", "Condition": {"ForAllValues:StringEquals": {"aws:TagKeys": ["Project"]}}},
    ]}
    for context in ({}, {"aws:TagKeys": []}, {"aws:TagKeys": None}, {"aws:TagKeys": ["Project"]}):
        assert not iam_authority.allowed([policy], "scheduler:DeleteSchedule", "arn:aws:scheduler:us-east-1:527257972989:schedule/default/paprnav-pilot-worker", context)
    assert iam_authority.allowed([policy], "scheduler:DeleteSchedule", "schedule", {"aws:TagKeys": ["Other"]})
    policy["Statement"][1]["Condition"] = {"Unsupported": {"key": "value"}}
    with pytest.raises(iam_authority.Stop, match="unsupported IAM condition"):
        iam_authority.allowed([policy], "scheduler:DeleteSchedule", "schedule", {})


@pytest.mark.parametrize("filename", ["override.tf.json", "extra.tf.json", "override.tf", "extra_override.tf"])
def test_iam_rejects_every_unreviewed_terraform_config_format(iam_authority: ModuleType, tmp_path: Path, filename: str) -> None:
    import shutil
    shutil.copytree(REPO_ROOT / "infra/terraform", tmp_path / "infra/terraform", ignore=shutil.ignore_patterns(".terraform"))
    (tmp_path / "infra/aws-iam").mkdir()
    shutil.copy(REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json", tmp_path / "infra/aws-iam")
    (tmp_path / "infra/terraform" / filename).write_text(json.dumps({"resource": {"aws_iam_role_policy": {"api_task": {"policy": json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]})}}}}))
    with pytest.raises(iam_authority.Stop, match="configuration is not reviewed"):
        iam_authority.bound_sources(tmp_path)


def test_iam_plan_binds_binary_configuration_and_its_json(iam_authority: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    baseline = json.loads((REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json").read_text())
    generated = generated_pilot_policy()
    plan = secret_plan(iam_authority, True)
    path = tmp_path / "saved.tfplan"
    sources = iam_authority.bound_sources()
    path.write_bytes(saved_plan_archive(sources))
    observed_rendering = deepcopy(plan)
    monkeypatch.setattr(iam_authority.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, json.dumps(observed_rendering), ""))
    assert iam_authority.plan_gate(plan, generated, baseline, saved_plan=path)["decision"] == "eligible-for-M6-review"
    with pytest.raises(iam_authority.Stop, match="saved-plan"):
        iam_authority.plan_gate(plan, generated, baseline)
    changed = deepcopy(plan)
    next(item for item in changed["resource_changes"] if item["address"] == "aws_iam_role_policy.api_task")["change"]["after"]["policy"] = json.dumps({"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]})
    with pytest.raises(iam_authority.Stop, match="JSON differs"):
        iam_authority.plan_gate(changed, generated, baseline, saved_plan=path)
    sources["override.tf.json"] = json.dumps({"resource": {"aws_iam_role_policy": {"api_task": {"policy": "widened"}}}})
    path.write_bytes(saved_plan_archive(sources))
    with pytest.raises(iam_authority.Stop, match="saved plan configuration differs"):
        iam_authority.plan_gate(plan, generated, baseline, saved_plan=path)


@pytest.mark.parametrize("error", ["AccessDenied", "NoSuchEntity", "Throttling", "", False, {}])
@pytest.mark.parametrize("target", ["preflight", "recovery-pre", "recovery-observed"])
def test_iam_snapshot_rejects_every_success_error_contradiction(iam_authority: ModuleType, error: object, target: str) -> None:
    pre = iam_snapshot(iam_authority, True, True)
    observed = deepcopy(pre)
    (observed if target == "recovery-observed" else pre)["getPolicyError"] = error
    with pytest.raises(iam_authority.Stop, match="contradictory GetPolicy"):
        iam_authority.publication(pre, "b" * 64, None if target == "preflight" else observed)


def test_release_builder_candidate_gate_and_preserved_dirt_separation(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_policy = {
        "approvedMigrationAuthoritySha256": {"backend/app/core/config.py": "0" * 64},
        "protectedBlobSha256": {"backend/app/models/core.py": "1" * 64},
    }
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    reviewed_path = "backend/Dockerfile"
    preserved_path = "backend/app/models/core.py"
    absolute = tmp_path / reviewed_path
    absolute.parent.mkdir(parents=True)
    absolute.write_text("FROM scratch\n", encoding="utf-8")
    manifest = tmp_path / "overlay.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "paprnav-reviewed-overlay-v2",
                "sourceCommit": "a" * 40,
                "reviewedInputs": [
                    {"path": reviewed_path, "sha256": release_builder.hashlib.sha256(absolute.read_bytes()).hexdigest()}
                ],
                "preservedExclusions": [preserved_path],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release_builder, "dirty_paths", lambda: {reviewed_path, preserved_path})
    reviewed, preserved = release_builder.overlay_files(
        manifest,
        "a" * 40,
        {"forbiddenPaths": [], "forbiddenPrefixes": []},
        boundary_policy,
    )
    assert reviewed == {reviewed_path: b"FROM scratch\n"}
    assert preserved == [preserved_path]

    protected_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    protected_manifest["reviewedInputs"] = [
        {"path": preserved_path, "sha256": "1" * 64}
    ]
    protected_manifest["preservedExclusions"] = [reviewed_path]
    manifest.write_text(json.dumps(protected_manifest), encoding="utf-8")
    with pytest.raises(release_builder.ContextError, match="protected authority"):
        release_builder.overlay_files(
            manifest,
            "a" * 40,
            {"forbiddenPaths": [], "forbiddenPrefixes": []},
            boundary_policy,
        )


def test_release_builder_blocks_failed_package_a_authority(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = load_module(
        "verify_pilot_release_boundary",
        REPO_ROOT / "scripts/verify_pilot_release_boundary.py",
    )
    monkeypatch.setitem(sys.modules, "verify_pilot_release_boundary", boundary)

    policy_path = tmp_path / "boundary.json"
    policy_path.write_text('{"version":"test"}\n', encoding="utf-8")
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(release_builder, "BOUNDARY_POLICY", policy_path)
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {"status": "pass", "errors": []})
    assert release_builder.candidate_authority("a" * 40) == {"version": "test"}
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {
        "status": "fail",
        "errors": ["protected release blob differs"],
    })
    with pytest.raises(release_builder.ContextError, match="protected release blob differs"):
        release_builder.candidate_authority("a" * 40)


def postgres_connection_args() -> dict[str, object]:
    raw = os.getenv("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL", "")
    if not raw:
        pytest.skip("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL is not set")
    parsed = make_url(raw)
    if not parsed.database or not parsed.database.startswith("paprnav_package_c_"):
        pytest.fail("Package C PostgreSQL tests require a disposable paprnav_package_c_* database")
    return {
        "host": parsed.host,
        "port": parsed.port or 5432,
        "dbname": parsed.database,
        "user": parsed.username,
        "password": parsed.password,
        "sslmode": "disable",
    }


def prepare_first_admin_database(connection_args: dict[str, object], bootstrap: ModuleType) -> None:
    # Synthetic transaction/control fixture only. It does not establish that
    # first-admin succeeds against the full sealed 0029 migrated schema.
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS pilot_control CASCADE")
            cursor.execute("DROP TABLE IF EXISTS product_events, organization_memberships, organizations, users CASCADE")
            cursor.execute(
                "CREATE TABLE users (id varchar(36) PRIMARY KEY, email text NOT NULL, name text NOT NULL, "
                "password_hash text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organizations (id varchar(36) PRIMARY KEY, name text NOT NULL, type text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organization_memberships (id varchar(36) PRIMARY KEY, organization_id varchar(36) NOT NULL, "
                "user_id varchar(36) NOT NULL, role text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE product_events (id varchar(36) PRIMARY KEY, actor_user_id varchar(36), "
                "organization_id varchar(36), event_type text, event_source text, subject_type text, "
                "subject_id varchar(36), properties_json json)"
            )
            bootstrap.install_control_schema(cursor)
        connection.commit()


def relation_counts(connection_args: dict[str, object]) -> list[int]:
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            result = []
            for relation in (
                "users",
                "organizations",
                "organization_memberships",
                "product_events",
                "pilot_control.bootstrap_consumptions",
            ):
                cursor.execute(f"SELECT count(*) FROM {relation}")
                result.append(cursor.fetchone()[0])
            return result


def test_first_admin_failure_boundaries_and_concurrency(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_args = postgres_connection_args()
    prepare_first_admin_database(connection_args, bootstrap)

    class Secrets:
        def get_secret_value(self, *, SecretId: str) -> dict[str, str]:
            if SecretId == "admin":
                return {"SecretString": json.dumps({
                    "username": "paprnav_admin",
                    "password": connection_args["password"],
                })}
            assert SecretId == "first-admin"
            return {"SecretString": json.dumps({"password": "first-admin-password"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin")
    monkeypatch.setenv("PAPRNAV_FIRST_ADMIN_SECRET_ARN", "first-admin")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", str(connection_args["host"]))
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", str(connection_args["port"]))
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", str(connection_args["dbname"]))
    monkeypatch.setenv("PAPRNAV_DATABASE_SSLMODE", "disable")
    identity = {"email": "first@example.com", "name": "First Admin", "organization": "Paprnav"}
    for point in ("user", "organization", "membership", "audit", "consumption"):
        monkeypatch.setenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER", point)
        with pytest.raises(bootstrap.BootstrapError, match="injected failure"):
            bootstrap.run_first_admin(Secrets(), identity=identity)
        assert relation_counts(connection_args) == [0, 0, 0, 0, 0]
    monkeypatch.delenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER")

    barrier = threading.Barrier(2)

    def synchronized_connect(**kwargs: object) -> psycopg.Connection:
        barrier.wait(timeout=10)
        return psycopg.connect(**kwargs)

    identities = (
        identity,
        {"email": "other@example.com", "name": "Other Admin", "organization": "Other"},
    )

    def attempt(value: dict[str, str]) -> str:
        try:
            bootstrap.run_first_admin(Secrets(), connect=synchronized_connect, identity=value)
            return "success"
        except bootstrap.BootstrapError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(attempt, identities))
    assert outcomes == ["rejected", "success"]
    assert relation_counts(connection_args) == [1, 1, 1, 1, 1]

    with pytest.raises(bootstrap.BootstrapError, match="permanently unavailable"):
        bootstrap.run_first_admin(Secrets(), identity=identity)


def test_three_dockerfiles_are_pinned_non_root_and_bootstrap_inventory_is_sealed() -> None:
    api = (REPO_ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    frontend = (REPO_ROOT / "frontend/paprnav-frontend/Dockerfile").read_text(encoding="utf-8")
    bootstrap = (REPO_ROOT / "infra/bootstrap/Dockerfile").read_text(encoding="utf-8")
    assert "@sha256:" in api and "USER 10001:10001" in api
    assert "@sha256:" in frontend and "USER 10001:10001" in frontend
    assert "@sha256:" in bootstrap and "USER 10001:10001" in bootstrap
    assert "COPY --chown=root:root migration/ /migration/" in bootstrap
    assert "backend/" not in bootstrap and "frontend/" not in bootstrap
    context_policy = json.loads((REPO_ROOT / ".ai/pilot-package-c-context-v1.json").read_text(encoding="utf-8"))
    assert all("0030" in path for path in context_policy["forbiddenPaths"][:3])
