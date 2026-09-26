#!/usr/bin/env python3
"""Verify an explicit Git commit, not the working tree, as a pilot release input."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


DEFAULT_POLICY_PATH = ".ai/pilot-release-boundary-v1.json"
MIGRATION_TREE_PREFIX = b"backend/app/db/migrations/"
MIGRATION_PREFIX = MIGRATION_TREE_PREFIX + b"versions/"
# Reviewed repository inputs to the sealed migration context. This source
# verifier does not establish isolation of a full application's import path.
MIGRATION_SUPPORT_PATHS = frozenset({
    b"backend/alembic.ini",
    b"backend/app/__init__.py",
    b"backend/app/core/__init__.py",
    b"backend/app/core/config.py",
    b"backend/app/db/__init__.py",
    b"backend/app/db/base.py",
    b"backend/app/models/__init__.py",
    b"backend/app/models/core.py",
})


def path_text(path: bytes) -> str:
    """Lossless JSON-facing name; json.dumps escapes controls and surrogates."""
    return path.decode("utf-8", errors="surrogateescape")


def git(repo: Path, *args: str | bytes, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result


def resolve_commit(repo: Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ValueError("release ref must be an explicit non-option Git ref")
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def tree_paths(repo: Path, commit: str) -> list[bytes]:
    raw = git(repo, "ls-tree", "-rz", "--name-only", commit).stdout
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise ValueError("Git tree inventory is not NUL terminated")
    paths = raw[:-1].split(b"\0")
    if any(not path for path in paths) or len(paths) != len(set(paths)):
        raise ValueError("Git tree inventory has empty or duplicate paths")
    return sorted(paths)


def blob_bytes(repo: Path, commit: str, path: bytes) -> bytes:
    return git(repo, "show", commit.encode("ascii") + b":" + path).stdout


def excluded_paths(paths: list[bytes], policy: dict[str, Any]) -> list[bytes]:
    exact = {path.encode("utf-8", "surrogateescape") for path in policy.get("excludedTreePaths", [])}
    prefixes = tuple(path.encode("utf-8", "surrogateescape") for path in policy.get("excludedTreePrefixes", []))
    return sorted(path for path in paths if path in exact or path.startswith(prefixes))


def assignment_value(tree: ast.Module, name: str) -> Any:
    stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == name
    ]
    assignments: list[ast.expr] = []
    for node in tree.body:
        target_name = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            target_name = target.id if isinstance(target, ast.Name) else None
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target_name = node.target.id if isinstance(node.target, ast.Name) else None
            value = node.value
        if target_name == name and value is not None:
            assignments.append(value)
    if len(stores) != 1 or len(assignments) != 1:
        raise ValueError(
            f"migration must declare {name} exactly once at module scope; "
            f"found {len(stores)} assignments"
        )
    return ast.literal_eval(assignments[0])


def migration_heads(repo: Path, commit: str, paths: list[bytes]) -> list[str]:
    revisions: set[str] = set()
    predecessors: set[str] = set()
    graph: dict[str, tuple[str, ...]] = {}
    for path in paths:
        if not path.startswith(MIGRATION_PREFIX) or not path.endswith(b".py"):
            continue
        tree = ast.parse(blob_bytes(repo, commit, path).decode("utf-8"), filename=path_text(path))
        revision = assignment_value(tree, "revision")
        down_revision = assignment_value(tree, "down_revision")
        # The approved graph has no branch aliases or dependency edges. Reject
        # them explicitly rather than silently deriving a partial graph.
        for name in ("branch_labels", "depends_on"):
            if assignment_value(tree, name) is not None:
                raise ValueError(f"unsupported migration {name} in {path_text(path)}")
        if not isinstance(revision, str) or not revision:
            raise ValueError(f"invalid migration revision in {path}")
        if revision in revisions:
            raise ValueError(f"duplicate migration revision: {revision}")
        revisions.add(revision)
        if isinstance(down_revision, str):
            if not down_revision:
                raise ValueError(f"invalid down_revision in {path_text(path)}")
            predecessors.add(down_revision)
            graph[revision] = (down_revision,)
        elif isinstance(down_revision, (tuple, list)):
            if not down_revision or not all(isinstance(item, str) and item for item in down_revision):
                raise ValueError(f"invalid down_revision in {path}")
            if len(set(down_revision)) != len(down_revision):
                raise ValueError(f"duplicate down_revision in {path}")
            graph[revision] = tuple(down_revision)
            predecessors.update(down_revision)
        elif down_revision is None:
            graph[revision] = ()
        elif down_revision is not None:
            raise ValueError(f"invalid down_revision in {path}")
    if not revisions:
        raise ValueError("release tree has no Alembic revisions")
    missing = sorted(predecessors - revisions)
    if missing:
        raise ValueError(f"migration predecessors are missing: {missing}")

    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(revision: str) -> None:
        if revision in visiting:
            raise ValueError(f"migration graph contains a cycle at {revision}")
        if revision in visited:
            return
        visiting.add(revision)
        for predecessor in graph[revision]:
            visit(predecessor)
        visiting.remove(revision)
        visited.add(revision)

    for revision in sorted(revisions):
        visit(revision)
    roots = sorted(revision for revision, parents in graph.items() if not parents)
    if len(roots) != 1:
        raise ValueError(f"migration graph must have exactly one root: {roots}")
    return sorted(revisions - predecessors)


def migration_authority_paths(paths: list[bytes]) -> list[bytes]:
    return sorted(path for path in paths if path.startswith(MIGRATION_TREE_PREFIX)
                  or path in MIGRATION_SUPPORT_PATHS)


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def verify_migration_inventory(
    repo: Path,
    commit: str,
    paths: list[bytes],
    policy: dict[str, Any],
) -> tuple[dict[str, dict[str, str]], list[str]]:
    expected = policy.get("approvedMigrationAuthoritySha256", {})
    if not isinstance(expected, dict) or not expected:
        return {}, ["approved migration authority inventory is missing"]
    expected = {path.encode("utf-8", "surrogateescape"): value for path, value in expected.items()}
    actual_paths = migration_authority_paths(paths)
    expected_paths = sorted(expected)
    errors: list[str] = []
    if not MIGRATION_SUPPORT_PATHS.issubset(expected) or migration_authority_paths(expected_paths) != expected_paths:
        errors.append("approved migration authority inventory has an invalid scope")
    if actual_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(actual_paths))
        unapproved = sorted(set(actual_paths) - set(expected_paths))
        errors.append(
            f"migration authority inventory differs: missing {missing}, unapproved {unapproved}"
        )

    results: dict[str, dict[str, str]] = {}
    for path in sorted(set(actual_paths) & set(expected_paths)):
        expected_hash = expected[path]
        actual_hash = hashlib.sha256(blob_bytes(repo, commit, path)).hexdigest()
        results[path_text(path)] = {
            "expectedSha256": expected_hash,
            "actualSha256": actual_hash,
        }
        if actual_hash != expected_hash:
            errors.append(f"migration authority blob differs: {path_text(path)}")
    return results, errors


def verify_release(repo: Path, ref: str, policy: dict[str, Any]) -> dict[str, Any]:
    commit = resolve_commit(repo, ref)
    baseline = str(policy["approvedBaselineCommit"])
    ancestor = git(repo, "merge-base", "--is-ancestor", baseline, commit, check=False)
    errors: list[str] = []
    if ancestor.returncode:
        errors.append(f"approved baseline {baseline} is not an ancestor of {commit}")

    paths = tree_paths(repo, commit)
    found_excluded = excluded_paths(paths, policy)
    if found_excluded:
        errors.append(f"release tree contains excluded paths: {found_excluded}")

    protected_results: dict[str, dict[str, str]] = {}
    for path, expected_hash in sorted(policy.get("protectedBlobSha256", {}).items()):
        try:
            actual_hash = hashlib.sha256(blob_bytes(repo, commit, path.encode("utf-8", "surrogateescape"))).hexdigest()
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        protected_results[path] = {"expectedSha256": expected_hash, "actualSha256": actual_hash}
        if actual_hash != expected_hash:
            errors.append(f"protected release blob differs: {path}")

    try:
        migration_blobs, migration_blob_errors = verify_migration_inventory(
            repo, commit, paths, policy
        )
        errors.extend(migration_blob_errors)
    except RuntimeError as exc:
        migration_blobs = {}
        errors.append(str(exc))

    try:
        heads = migration_heads(repo, commit, paths)
    except (SyntaxError, UnicodeDecodeError, ValueError, RuntimeError) as exc:
        heads = []
        errors.append(str(exc))
    expected_heads = sorted(policy.get("expectedMigrationHeads", []))
    if heads != expected_heads:
        errors.append(f"migration heads differ: expected {expected_heads}, got {heads}")

    return {
        "version": policy["version"],
        "status": "pass" if not errors else "fail",
        "commit": commit,
        "approvedBaselineCommit": baseline,
        "migrationHeads": heads,
        "expectedMigrationHeads": expected_heads,
        "migrationAuthorityBlobs": migration_blobs,
        "excludedPathsPresent": [path_text(path) for path in found_excluded],
        "protectedBlobs": protected_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True, help="Explicit Git commit or ref to inspect")
    parser.add_argument("--policy", default=DEFAULT_POLICY_PATH)
    args = parser.parse_args()

    repo = Path(path_text(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.rstrip(b"\n")))
    policy_path = (repo / args.policy).resolve()
    try:
        policy_path.relative_to(repo)
    except ValueError as exc:
        raise SystemExit("policy path must remain inside the repository") from exc
    policy = json.loads(policy_path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_object)
    result = verify_release(repo, args.ref, policy)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
