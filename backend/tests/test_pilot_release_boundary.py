from __future__ import annotations

import asyncio
import copy
import importlib.util
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import PILOT_FORBIDDEN_V4_SETTINGS, get_settings
from app.main import create_app, is_ad_v4_path


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / ".ai" / "pilot-release-boundary-v1.json"
V4_ENV_BY_SETTING = {
    "ad_v4_routes_enabled": "PAPRNAV_AD_V4_ROUTES_ENABLED",
    "ad_v4_validator2_writes_enabled": "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED",
    "ad_v4_slice3a_routes_enabled": "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED",
    "ad_v4_slice3b_routes_enabled": "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED",
    "ad_v4_slice4_reads_enabled": "PAPRNAV_AD_V4_SLICE4_READS_ENABLED",
    "ad_v4_slice4_drafts_enabled": "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED",
    "ad_v4_slice4_decisions_enabled": "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED",
}
EXPECTED_V4_OPERATIONS = {
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/applicability-projections"),
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals"),
    ("POST", "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals"),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection/reconstruction",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection/reconstruction",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-observation",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-cases",
    ),
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/obligation-projections"),
    ("GET", "/api/v1/ads/v4/candidate-proposals/{proposal_id}"),
    ("GET", "/api/v1/ads/v4/review-cases"),
    ("GET", "/api/v1/ads/v4/review-cases/{case_id}"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/drafts"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/rejection"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/review-request"),
}


@pytest.fixture(autouse=True)
def restore_temporary_context_permissions(tmp_path: Path):
    """Let pytest remove contexts deliberately made read-only by the tests."""

    yield
    for current, directories, files in os.walk(tmp_path, topdown=False):
        for name in [*directories, *files]:
            path = Path(current) / name
            if not path.is_symlink():
                path.chmod(0o700)
        Path(current).chmod(0o700)


def load_release_verifier() -> ModuleType:
    path = REPO_ROOT / "scripts" / "verify_pilot_release_boundary.py"
    spec = importlib.util.spec_from_file_location("verify_pilot_release_boundary", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure_pilot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", "https://pilot.example.test")
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv(
        "PAPRNAV_INVITE_SIGNING_SECRET",
        "pilot-invitation-secret-that-is-at-least-32-bytes",
    )
    for env_name in V4_ENV_BY_SETTING.values():
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()


def concrete_path(path: str) -> str:
    return re.sub(r"\{[^}/]+\}", "00000000-0000-0000-0000-000000000000", path)


def v4_operations(app) -> list[tuple[str, str]]:
    operations: list[tuple[str, str]] = []
    for path, path_item in app.openapi()["paths"].items():
        if is_ad_v4_path(path):
            operations.extend(
                (method.upper(), path)
                for method in path_item
                if method.lower() in {"get", "post", "put", "patch", "delete"}
            )
    return sorted(operations)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/v1/ads/v4", True),
        ("/api/v1/ads/directives/id/v4/candidate-proposals", True),
        ("//api//v1//ads//v4//review-cases", True),
        ("/api/v1/ads/v4ish/candidate-proposals", False),
        ("/api/v1/aircraft/v4", False),
        ("/api/v2/ads/v4", False),
    ],
)
def test_v4_path_family_matcher(path: str, expected: bool) -> None:
    assert is_ad_v4_path(path) is expected


def test_safe_pilot_configuration_disables_all_v4_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_pilot(monkeypatch)

    settings = get_settings()
    assert settings.environment == "pilot"
    assert all(not getattr(settings, name) for name in PILOT_FORBIDDEN_V4_SETTINGS)

    app = create_app()
    operations = v4_operations(app)
    assert set(operations) == EXPECTED_V4_OPERATIONS

    with TestClient(app) as client:
        for method, path in operations:
            response = client.request(
                method,
                concrete_path(path),
                content=b"{not-json",
                headers={"Origin": "https://untrusted.example"},
            )
            assert response.status_code == 404, (method, path, response.text)
            assert response.json() == {"detail": "Not Found"}

        preflight = client.options(
            concrete_path(operations[0][1]),
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert preflight.status_code == 404
        assert preflight.json() == {"detail": "Not Found"}
        assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("encoded_delimiter", ["%3Fquery", "%23fragment"])
def test_encoded_path_delimiters_cannot_reach_authentication(
    monkeypatch: pytest.MonkeyPatch,
    encoded_delimiter: str,
) -> None:
    configure_pilot(monkeypatch)
    app = create_app()
    auth_reached = False

    def authentication_sentinel():
        nonlocal auth_reached
        auth_reached = True
        raise AssertionError("authentication boundary was reached")

    app.dependency_overrides[get_current_user] = authentication_sentinel
    path = (
        f"/api/v1/ads/directives/id{encoded_delimiter}/v4/candidate-proposals"
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(path)
        preflight = client.options(
            path,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert preflight.status_code == 404
    assert preflight.json() == {"detail": "Not Found"}
    assert auth_reached is False


def test_decoded_scope_path_and_root_path_gate_without_reading_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_pilot(monkeypatch)
    app = create_app()
    handler_reached = False

    @app.post("/api/v1/ads/{identifier}/v4/body-sentinel")
    async def body_sentinel(identifier: str, request: Request):
        nonlocal handler_reached
        handler_reached = True
        await request.body()
        return {"identifier": identifier}

    messages: list[dict] = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mount/api/v1/ads/id?query/v4/body-sentinel",
        "raw_path": b"/mount/api/v1/ads/id%3Fquery/v4/body-sentinel",
        "root_path": "/mount",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }

    async def body_read_sentinel():
        raise AssertionError("request body was read")

    async def send(message: dict) -> None:
        messages.append(message)

    asyncio.run(app(scope, body_read_sentinel, send))

    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    assert start["status"] == 404
    assert json.loads(body) == {"detail": "Not Found"}
    assert handler_reached is False


@pytest.mark.parametrize("setting_name", PILOT_FORBIDDEN_V4_SETTINGS)
def test_pilot_startup_rejects_each_v4_capability(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
) -> None:
    configure_pilot(monkeypatch)
    monkeypatch.setenv(V4_ENV_BY_SETTING[setting_name], "true")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match=setting_name):
        create_app()


def test_local_environment_retains_v4_route_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "local")
    for env_name in V4_ENV_BY_SETTING.values():
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()

    assert get_settings().ad_v4_routes_enabled is True
    assert set(v4_operations(create_app())) == EXPECTED_V4_OPERATIONS


def test_pre_package_a_commit_fails_only_for_target_configuration() -> None:
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    result = verifier.verify_release(REPO_ROOT, policy["approvedBaselineCommit"], policy)

    assert result["status"] == "fail"
    assert result["errors"] == [
        "migration authority blob differs: backend/app/core/config.py"
    ]
    assert result["migrationHeads"] == ["20260913_0029"]
    assert result["excludedPathsPresent"] == []
    protected = result["protectedBlobs"]["backend/app/models/core.py"]
    assert protected["actualSha256"] == protected["expectedSha256"]


@pytest.fixture(scope="module")
def approved_candidate_tree() -> dict[bytes, bytes]:
    """Real baseline blobs plus the reviewed Package A config target bytes."""
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    baseline = policy["approvedBaselineCommit"]
    paths = verifier.migration_authority_paths(verifier.tree_paths(REPO_ROOT, baseline))
    tree = {
        path: verifier.blob_bytes(REPO_ROOT, baseline, path)
        for path in paths
    }
    tree[b"backend/app/core/config.py"] = (REPO_ROOT / "backend/app/core/config.py").read_bytes()
    return tree


@pytest.fixture
def candidate_verifier(approved_candidate_tree, monkeypatch):
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    tree = dict(approved_candidate_tree)
    verifier.candidate_modes = {}
    commit = "a" * 40

    def candidate_git(repo, *args, check=True):
        if args[:3] == ("ls-tree", "-rz", "--name-only") and args[-1] in {"candidate", commit}:
            # Exercise the raw Git output parser, including every unusual byte
            # name supplied by the negative cases below.
            return subprocess.CompletedProcess(args, 0, b"\0".join(sorted(tree)) + b"\0", b"")
        if args == ("ls-tree", "-rz", commit):
            records = []
            for path in sorted(tree):
                mode, kind = verifier.candidate_modes.get(path, (b"100644", b"blob"))
                records.append(mode + b" " + kind + b" " + b"0" * 40 + b"\t" + path)
            return subprocess.CompletedProcess(args, 0, b"\0".join(records) + b"\0", b"")
        if args == ("merge-base", "--is-ancestor", policy["approvedBaselineCommit"], commit):
            return subprocess.CompletedProcess(args, 0, b"", b"")
        if args[0] == "show":
            path = args[1].split(b":", 1)[1]
            if path not in tree:
                raise RuntimeError(f"missing tree path: {path!r}")
            return subprocess.CompletedProcess(args, 0, tree[path], b"")
        raise AssertionError(f"unexpected Git command: {args}")

    monkeypatch.setattr(verifier, "git", candidate_git)
    monkeypatch.setattr(verifier, "resolve_commit", lambda repo, ref: commit)
    return verifier, policy, tree


def test_approved_target_candidate_passes_complete_authority(candidate_verifier) -> None:
    verifier, policy, _ = candidate_verifier
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "pass", result["errors"]
    assert result["migrationHeads"] == ["20260913_0029"]
    assert result["excludedPathsPresent"] == []
    assert len(result["migrationAuthorityBlobs"]) == 44
    assert set(result["migrationAuthorityBlobs"]) == set(policy["approvedMigrationAuthoritySha256"])
    assert all(item["actualSha256"] == item["expectedSha256"]
               for item in result["migrationAuthorityBlobs"].values())
    assert json.loads(json.dumps(result, sort_keys=True)) == result


def test_release_verifier_fails_for_protected_blob_or_head_policy_drift(candidate_verifier) -> None:
    verifier, policy, _ = candidate_verifier
    wrong_blob = copy.deepcopy(policy)
    wrong_blob["protectedBlobSha256"]["backend/app/models/core.py"] = "0" * 64
    blob_result = verifier.verify_release(REPO_ROOT, "candidate", wrong_blob)
    assert blob_result["status"] == "fail"
    assert "protected release blob differs: backend/app/models/core.py" in blob_result[
        "errors"
    ]

    wrong_head = copy.deepcopy(policy)
    wrong_head["expectedMigrationHeads"] = ["not-the-reviewed-head"]
    head_result = verifier.verify_release(REPO_ROOT, "candidate", wrong_head)
    assert head_result["status"] == "fail"
    assert any(error.startswith("migration heads differ:") for error in head_result["errors"])


def test_release_verifier_recognizes_exact_and_prefix_exclusions() -> None:
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    paths = [
        policy["excludedTreePaths"][0].encode(),
        policy["excludedTreePrefixes"][0].encode() + b"decision.md",
        b"backend/app/main.py",
    ]

    assert verifier.excluded_paths(paths, policy) == sorted(paths[:2])


def test_release_verifier_rejects_changed_migration_content(candidate_verifier) -> None:
    verifier, policy, tree = candidate_verifier
    target = b"backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py"
    tree[target] += b'\nrevision = "unreviewed_revision"\n'
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)

    assert result["status"] == "fail"
    assert f"migration authority blob differs: {target.decode()}" in result["errors"]
    assert any(
        "revision exactly once at module scope; found 2 assignments" in error
        for error in result["errors"]
    )


AUTHORITY_MUTATION_TARGETS = [
    "backend/alembic.ini",
    "backend/app/db/migrations/env.py",
    "backend/app/db/migrations/script.py.mako",
    "backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql",
    "backend/app/db/migrations/sql/20260911_0028_obligation_integrity.sql",
    "backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql",
    "backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py",
    "backend/app/core/config.py",
    "backend/app/db/base.py",
    "backend/app/models/core.py",
    "backend/app/__init__.py",
    "backend/app/core/__init__.py",
    "backend/app/db/__init__.py",
    "backend/app/models/__init__.py",
]


@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
@pytest.mark.parametrize("mutation", ["remove", "rename", "content"])
def test_complete_authority_rejects_candidate_drift(candidate_verifier, target, mutation) -> None:
    verifier, policy, tree = candidate_verifier
    path = target.encode()
    if mutation == "remove":
        del tree[path]
    elif mutation == "rename":
        tree[path + b".renamed"] = tree.pop(path)
    else:
        if path.endswith(b".sql"):
            tree[path] += b"\nDROP TABLE users;\n"
        elif path.endswith(b".ini"):
            tree[path] = tree[path].replace(b"script_location = app/db/migrations", b"script_location = unreviewed")
        elif path.endswith(b".mako"):
            tree[path] += b"\n${unreviewed_template_input}\n"
        else:
            tree[path] += b'\nraise RuntimeError("unreviewed execution")\n'
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    expected = "migration authority blob differs:" if mutation == "content" else "migration authority inventory differs:"
    assert any(error.startswith(expected) for error in result["errors"])
    if target == "backend/app/models/core.py" and mutation == "content":
        assert "protected release blob differs: backend/app/models/core.py" in result["errors"]


@pytest.mark.parametrize("path", [
    b"backend/app/db/migrations/versions/new.py",
    b"backend/app/db/migrations/sql/new.sql",
    b"backend/app/db/migrations/sql/new.json",
    b"backend/app/db/migrations/other-sidecar.bin",
    b"backend/app/db/migrations/new.ini",
    b"backend/app/db/migrations/new.mako",
])
def test_complete_authority_rejects_candidate_additions(candidate_verifier, path) -> None:
    verifier, policy, tree = candidate_verifier
    tree[path] = b"unapproved migration input"
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    assert any(error.startswith("migration authority inventory differs:") for error in result["errors"])


@pytest.mark.parametrize("suffix", [
    b'quote".json', b"back\\slash.json", b"tab\t.json", b"line\nbreak.json",
    "non-ascii-é.json".encode(), b"non-utf8-\xff.json",
])
@pytest.mark.parametrize("prefix", [
    b"backend/app/db/migrations/sql/",
    b".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/",
])
def test_raw_git_path_bytes_cannot_evade_boundaries(candidate_verifier, suffix, prefix) -> None:
    verifier, policy, tree = candidate_verifier
    path = prefix + suffix
    tree[path] = b"unreviewed"
    assert path in verifier.tree_paths(REPO_ROOT, "candidate")
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    if prefix.startswith(b".ai/"):
        assert result["excludedPathsPresent"] == [path.decode("utf-8", "surrogateescape")]
    else:
        assert any(error.startswith("migration authority inventory differs:") for error in result["errors"])
    rendered = json.dumps(result, sort_keys=True, ensure_ascii=True)
    assert json.loads(rendered) == result
    assert rendered.encode("ascii")


def migration_source(revision, predecessor, extra=b"") -> bytes:
    return (f"revision = {revision!r}\ndown_revision = {predecessor!r}\n"
            "branch_labels = None\ndepends_on = None\n").encode() + extra


@pytest.mark.parametrize(("sources", "error"), [
    ([migration_source("root", None), migration_source("cycle_a", "cycle_b"), migration_source("cycle_b", "cycle_a")], "contains a cycle"),
    ([migration_source("root", None), migration_source("other", "missing")], "predecessors are missing"),
    ([migration_source("root", None), migration_source("root", None)], "duplicate migration revision"),
    ([migration_source("root", None), migration_source("other", ["root", "root"])], "duplicate down_revision"),
    ([migration_source("root", None), migration_source("other", [1])], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", "")], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", [])], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", None)], "exactly one root"),
    ([migration_source("root", "root")], "contains a cycle"),
    ([migration_source("root", None, b'\nrevision = "override"\n')], "revision exactly once"),
    ([migration_source("root", None, b'\ndef mutate():\n    revision = "override"\n')], "revision exactly once"),
    ([migration_source("root", None, b'\ndown_revision = "override"\n')], "down_revision exactly once"),
    ([migration_source("root", None, b'\nbranch_labels = None\n')], "branch_labels exactly once"),
    ([migration_source("root", None, b'\ndepends_on = None\n')], "depends_on exactly once"),
    ([migration_source("root", None).replace(b"depends_on = None", b'depends_on = "missing"')], "unsupported migration depends_on"),
    ([migration_source("root", None).replace(b"branch_labels = None", b'branch_labels = "alias"')], "unsupported migration branch_labels"),
])
def test_complete_graph_rejects_invalid_candidate_metadata(sources, error) -> None:
    verifier = load_release_verifier()
    tree = {f"backend/app/db/migrations/versions/{i}.py".encode(): source
            for i, source in enumerate(sources)}
    verifier.blob_bytes = lambda repo, commit, path: tree[path]
    with pytest.raises(ValueError, match=error):
        verifier.migration_heads(REPO_ROOT, "candidate", sorted(tree))


@pytest.fixture
def context_builder(candidate_verifier, monkeypatch):
    verifier, policy, tree = candidate_verifier
    monkeypatch.setitem(sys.modules, "verify_pilot_release_boundary", verifier)
    spec = importlib.util.spec_from_file_location(
        "build_pilot_migration_context", REPO_ROOT / "scripts/build_pilot_migration_context.py"
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder, verifier, policy, tree


def test_sealed_context_reproducible_and_excludes_arbitrary_checkout_inputs(context_builder, tmp_path):
    builder, _, policy, tree = context_builder
    for name in ("psycopg", "sqlalchemy", "alembic", "sitecustomize", "random_" + uuid.uuid4().hex):
        tree[f"backend/{name}.py".encode()] = b'raise RuntimeError("checkout sentinel")\n'
        tree[f"backend/{name}/__init__.py".encode()] = b'raise RuntimeError("checkout sentinel")\n'
    tree[b"backend/.env"] = b"DATABASE_URL=must-never-enter-the-context\n"
    tree[b"backend/app/core/config/__init__.py"] = b'raise RuntimeError("checkout sentinel")\n'
    tree[b"backend/app/__pycache__/__init__.cpython-312.pyc"] = b"unreviewed bytecode"
    first, second = tmp_path / "first", tmp_path / "second"
    first_manifest = builder.build_context(REPO_ROOT, "candidate", policy, first)
    second_manifest = builder.build_context(REPO_ROOT, "candidate", policy, second)
    assert first_manifest == second_manifest
    assert builder.verify_context(REPO_ROOT, "candidate", policy, first) == first_manifest
    body = {key: value for key, value in first_manifest.items() if key != "manifestSha256"}
    assert hashlib.sha256(builder.canonical_json(body)).hexdigest() == first_manifest["manifestSha256"]
    expected = {source.removeprefix("backend/") for source in policy["approvedMigrationAuthoritySha256"]}
    expected.add("migration-context.json")
    assert {str(path.relative_to(first)) for path in first.rglob("*") if path.is_file()} == expected
    for entry in first_manifest["files"]:
        assert entry["destinationPath"] == entry["sourcePath"].removeprefix("backend/")
        assert entry["gitMode"] == "100644"
        assert entry["sizeBytes"] == len(tree[entry["sourcePath"].encode()])
    for relative in expected:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
        assert stat.S_IMODE((first / relative).stat().st_mode) == 0o444
    assert stat.S_IMODE(first.stat().st_mode) == 0o555
    assert b"must-never-enter" not in (first / "migration-context.json").read_bytes()


@pytest.mark.parametrize("mode_kind", [(b"120000", b"blob"), (b"160000", b"commit"), (b"100755", b"blob"), (b"040000", b"tree")])
@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
def test_builder_rejects_changed_source_modes_before_output(context_builder, tmp_path, mode_kind, target):
    builder, verifier, policy, _ = context_builder
    verifier.candidate_modes[target.encode()] = mode_kind
    destination = tmp_path / "context"
    with pytest.raises(builder.ContextError, match="unapproved Git mode/type"):
        builder.build_context(REPO_ROOT, "candidate", policy, destination)
    assert not destination.exists()


@pytest.mark.parametrize("mutation", ["remove", "rename", "content"])
@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
def test_builder_rejects_changed_source_inventory_and_bytes(context_builder, tmp_path, mutation, target):
    builder, _, policy, tree = context_builder
    path = target.encode()
    if mutation == "remove":
        del tree[path]
    elif mutation == "rename":
        tree[path + b".renamed"] = tree.pop(path)
    else:
        tree[path] += b"\n# candidate mutation\n"
    with pytest.raises(builder.ContextError, match="release source check failed"):
        builder.build_context(REPO_ROOT, "candidate", policy, tmp_path / "context")
    assert not (tmp_path / "context").exists()


@pytest.mark.parametrize("path", [b"/absolute", b"backend/../alembic.ini", b"backend//alembic.ini", b"backend/./alembic.ini", b"backend/invalid-\xff.py", b"backend\\alembic.ini"])
def test_context_paths_reject_noncanonical_or_non_utf8_names(context_builder, path):
    builder, _, _, _ = context_builder
    with pytest.raises(builder.ContextError):
        builder.destination_path(path)


def test_context_rejects_duplicate_git_names_and_json_keys(context_builder, monkeypatch):
    builder, verifier, _, _ = context_builder
    record = b"100644 blob " + b"0" * 40 + b"\tbackend/alembic.ini\0"
    monkeypatch.setattr(verifier, "git", lambda *args: subprocess.CompletedProcess(args, 0, record + record, b""))
    with pytest.raises(builder.ContextError, match="duplicate Git tree path"):
        builder.tree_records(REPO_ROOT, "a" * 40)
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        json.loads('{"sourcePath":"first","sourcePath":"second"}', object_pairs_hook=verifier.unique_json_object)


def test_real_git_modes_and_pre_package_a_builder_fail_closed(context_builder, tmp_path, monkeypatch):
    builder, _, policy, _ = context_builder
    monkeypatch.setattr(builder, "boundary", load_release_verifier())
    baseline = policy["approvedBaselineCommit"]
    records = builder.tree_records(REPO_ROOT, baseline)
    assert all(records[path.encode()] == (b"100644", b"blob")
               for path in policy["approvedMigrationAuthoritySha256"])
    with pytest.raises(builder.ContextError, match="migration authority blob differs: backend/app/core/config.py"):
        builder.build_context(REPO_ROOT, baseline, policy, tmp_path / "context")
    assert not (tmp_path / "context").exists()


@pytest.mark.parametrize("existing_kind", ["directory", "file", "symlink", "parent_symlink"])
def test_context_never_reuses_or_follows_existing_destinations(context_builder, tmp_path, existing_kind):
    builder, _, policy, _ = context_builder
    existing = tmp_path / "existing"
    if existing_kind == "directory":
        existing.mkdir()
    elif existing_kind == "file":
        existing.write_text("preserve me")
    else:
        target = tmp_path / "target"
        target.mkdir()
        existing.symlink_to(target, target_is_directory=True)
    destination = existing / "child" if existing_kind == "parent_symlink" else existing
    with pytest.raises(OSError):
        builder.build_context(REPO_ROOT, "candidate", policy, destination)
    if existing_kind == "file":
        assert existing.read_text() == "preserve me"
    if existing_kind in {"symlink", "parent_symlink"}:
        assert not list((tmp_path / "target").iterdir())


@pytest.mark.parametrize("target", [source.removeprefix("backend/") for source in AUTHORITY_MUTATION_TARGETS] + ["migration-context.json"])
@pytest.mark.parametrize("mutation", ["remove", "rename", "content", "symlink", "mode"])
def test_context_verification_rejects_tampering_in_every_manifest_class(context_builder, tmp_path, target, mutation):
    builder, _, policy, _ = context_builder
    context = tmp_path / "context"
    builder.build_context(REPO_ROOT, "candidate", policy, context)
    path = context / target
    path.parent.chmod(0o755)
    if mutation == "remove":
        path.unlink()
    elif mutation == "rename":
        path.rename(path.with_name(path.name + ".renamed"))
    elif mutation == "content":
        path.chmod(0o644)
        path.write_bytes(path.read_bytes() + b"\nmutated\n")
        path.chmod(0o444)
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to(tmp_path / "outside-context")
    else:
        path.chmod(0o644)
    path.parent.chmod(0o555)
    with pytest.raises(builder.ContextError):
        builder.verify_context(REPO_ROOT, "candidate", policy, context)


@pytest.mark.parametrize("extra", [".env", "psycopg.py", "app/__pycache__/injected.pyc", "empty-directory/"])
def test_context_verification_rejects_extra_files_or_directories(context_builder, tmp_path, extra):
    builder, _, policy, _ = context_builder
    context = tmp_path / "context"
    builder.build_context(REPO_ROOT, "candidate", policy, context)
    for parent in [context, context / "app"]:
        parent.chmod(0o755)
    target = context / extra.rstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    if extra.endswith("/"):
        target.mkdir(mode=0o555)
    else:
        target.write_bytes(b"unapproved")
        target.chmod(0o444)
    for parent in [target.parent, context / "app", context]:
        parent.chmod(0o555)
    with pytest.raises(builder.ContextError):
        builder.verify_context(REPO_ROOT, "candidate", policy, context)


IMPORT_BOUNDARY_ORACLE = r'''
import json, os, sys, sysconfig
from pathlib import Path
import alembic, sqlalchemy
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

class DriverLoaded(Exception):
    pass

report = {"engineCalled": False, "sentinel": False, "driverOrigin": None, "driverName": None}
original_engine_from_config = sqlalchemy.engine_from_config
def observed_engine_from_config(*args, **kwargs):
    report["engineCalled"] = True
    engine = original_engine_from_config(*args, **kwargs)
    report["driverOrigin"] = str(Path(engine.dialect.dbapi.__file__).resolve())
    report["driverName"] = engine.dialect.dbapi.__name__
    raise DriverLoaded()
sqlalchemy.engine_from_config = observed_engine_from_config
config = Config(str(Path.cwd() / "alembic.ini"))
scripts = ScriptDirectory.from_config(config)
try:
    with EnvironmentContext(config, scripts):
        scripts.run_env()
except DriverLoaded:
    pass
except RuntimeError as exc:
    if str(exc) != "CHECKOUT_PSYCOPG_SENTINEL":
        raise
    report["sentinel"] = True
report["imports"] = {"alembic": str(Path(alembic.__file__).resolve()),
                     "sqlalchemy": str(Path(sqlalchemy.__file__).resolve())}
report["sitePackages"] = sorted({str(Path(sysconfig.get_path(name)).resolve()) for name in ("purelib", "platlib")})
report["sysPath"] = [str(Path(path or ".").resolve()) for path in sys.path]
report["bytecodeDisabled"] = sys.dont_write_bytecode
from app.core.config import get_settings
report["explicitDatabaseSelected"] = get_settings().database_url == os.environ["DATABASE_URL"]
report["dotenvDisabled"] = os.environ["PAPRNAV_DISABLE_DOTENV"] == "1"
report["dotenvNotLoaded"] = get_settings().storage_backend != "dotenv-sentinel"
print(json.dumps(report, sort_keys=True))
'''


@pytest.mark.parametrize("sentinel_path", [b"backend/psycopg.py", b"backend/psycopg/__init__.py"])
def test_real_alembic_engine_imports_checkout_sentinel_only_in_vulnerable_control(context_builder, tmp_path, sentinel_path):
    builder, _, policy, tree = context_builder
    tree[sentinel_path] = b'raise RuntimeError("CHECKOUT_PSYCOPG_SENTINEL")\n'
    tree[b"backend/.env"] = b"PAPRNAV_STORAGE_BACKEND=dotenv-sentinel\nDATABASE_URL=forbidden-fallback\n"
    candidate = tmp_path / "candidate"
    for source, content in tree.items():
        target = candidate / source.decode()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    sealed = tmp_path / "sealed"
    builder.build_context(REPO_ROOT, "candidate", policy, sealed)
    database_url = "postgresql+psycopg://oracle:never-connect@127.0.0.1:1/oracle"
    environment = builder.launch_environment({"DATABASE_URL": database_url, "PAPRNAV_DISABLE_DOTENV": "0", "PYTHONPATH": str(REPO_ROOT / "backend")})
    reports = []
    for cwd in [candidate / "backend", sealed]:
        process = subprocess.run([sys.executable, "-I", "-B", "-c", IMPORT_BOUNDARY_ORACLE],
                                 cwd=cwd, env=environment, capture_output=True, text=True)
        assert process.returncode == 0, process.stderr
        assert database_url not in process.stdout + process.stderr
        reports.append(json.loads(process.stdout))
    vulnerable, protected = reports
    assert vulnerable["engineCalled"] and vulnerable["sentinel"]
    assert vulnerable["driverOrigin"] is None
    assert str(candidate / "backend") in vulnerable["sysPath"]
    assert protected["engineCalled"] and not protected["sentinel"]
    assert protected["driverOrigin"] is not None
    assert protected["driverName"] == "psycopg"
    for origin in [protected["driverOrigin"], *protected["imports"].values()]:
        assert any(Path(origin).is_relative_to(site) for site in protected["sitePackages"])
        assert not Path(origin).is_relative_to(sealed)
    for entry in protected["sysPath"]:
        assert not Path(entry).is_relative_to(candidate)
        # This project's interpreter is in an ignored backend/.venv directory.
        # Only its exact canonical installed-package root is allowed there;
        # no checkout source directory or editable-install path may be present.
        if Path(entry).is_relative_to(REPO_ROOT):
            assert entry in protected["sitePackages"]
    assert protected["bytecodeDisabled"] and protected["dotenvDisabled"] and protected["explicitDatabaseSelected"]
    assert vulnerable["dotenvNotLoaded"] and protected["dotenvNotLoaded"]
    assert not list(sealed.rglob("__pycache__"))
    assert builder.verify_context(REPO_ROOT, "candidate", policy, sealed)


def test_launcher_requires_database_and_suppresses_child_secret_output(context_builder, tmp_path, monkeypatch):
    builder, _, policy, _ = context_builder
    for env in ({}, {"DATABASE_URL": ""}, {"DATABASE_URL": "  "}):
        with pytest.raises(builder.ContextError, match="DATABASE_URL must be supplied"):
            builder.run_context(REPO_ROOT, "candidate", policy, tmp_path / "absent", env)
    secret_url = "postgresql+psycopg://operator:runtime-secret@db/pilot"
    environment = builder.launch_environment({"DATABASE_URL": secret_url, "PAPRNAV_DISABLE_DOTENV": "0", "PYTHONPATH": "untrusted"})
    assert environment == {"DATABASE_URL": secret_url, "PAPRNAV_DISABLE_DOTENV": "1", "PYTHONDONTWRITEBYTECODE": "1", "PAPRNAV_ENV": "pilot"}
    context = tmp_path / "sealed"
    manifest = builder.build_context(REPO_ROOT, "candidate", policy, context)
    assert secret_url not in json.dumps(manifest)

    def failing_child(command, **kwargs):
        assert command == builder.launch_command(context, policy, sys.executable)
        assert command[1:5] == ["-I", "-B", "-m", "alembic"]
        assert command[-2:] == ["upgrade", "20260913_0029"]
        assert kwargs["cwd"] == context
        assert kwargs["env"] == environment
        assert kwargs["capture_output"] is True
        return subprocess.CompletedProcess(command, 1, secret_url.encode(), secret_url.encode())

    monkeypatch.setattr(builder.subprocess, "run", failing_child)
    with pytest.raises(builder.ContextError, match="child output suppressed") as failure:
        builder.run_context(REPO_ROOT, "candidate", policy, context, environment)
    assert secret_url not in str(failure.value)
