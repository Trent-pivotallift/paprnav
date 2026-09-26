#!/usr/bin/env python3
"""Build deterministic API, frontend, or sealed bootstrap contexts from Git."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = REPO_ROOT / ".ai/pilot-package-c-context-v1.json"
BOUNDARY_POLICY = REPO_ROOT / ".ai/pilot-release-boundary-v1.json"
MANIFEST_NAME = "release-context.json"


class ContextError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True)
    if check and result.returncode:
        raise ContextError(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result


def resolve_commit(ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ContextError("release ref must be an explicit non-option Git ref")
    return git("rev-parse", "--verify", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def tree_entries(commit: str) -> dict[str, tuple[str, str]]:
    raw = git("ls-tree", "-rz", "--full-tree", commit).stdout
    result: dict[str, tuple[str, str]] = {}
    for record in raw.rstrip(b"\0").split(b"\0") if raw else []:
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8", "strict")
        if path in result or kind != "blob":
            raise ContextError("release tree contains duplicate or unsupported entries")
        result[path] = (mode, object_id)
    return result


def dirty_paths() -> set[str]:
    raw = git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    records = raw.rstrip(b"\0").split(b"\0") if raw else []
    result: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 4:
            raise ContextError("unparseable Git status record")
        status_code = record[:2].decode("ascii")
        result.add(record[3:].decode("utf-8", "strict"))
        if "R" in status_code or "C" in status_code:
            index += 1
            if index >= len(records):
                raise ContextError("unparseable Git rename/copy record")
            result.add(records[index].decode("utf-8", "strict"))
        index += 1
    return result


def validate_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if not path or path.startswith("/") or ".." in parsed.parts or str(parsed) != path:
        raise ContextError("unsafe context path")


def is_forbidden(path: str, policy: dict[str, Any]) -> bool:
    return path in policy["forbiddenPaths"] or any(
        path.startswith(prefix) for prefix in policy["forbiddenPrefixes"]
    ) or "20260916_0030" in path


def candidate_authority(commit: str) -> dict[str, Any]:
    """Apply Package A's one canonical candidate/protected-blob gate."""

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import verify_pilot_release_boundary as boundary

    boundary_policy = json.loads(
        BOUNDARY_POLICY.read_text(encoding="utf-8"),
        object_pairs_hook=boundary.unique_json_object,
    )
    result = boundary.verify_release(REPO_ROOT, commit, boundary_policy)
    if result["status"] != "pass":
        raise ContextError("Package A candidate authority failed: " + "; ".join(result["errors"]))
    return boundary_policy


def overlay_files(
    path: Path | None,
    commit: str,
    policy: dict[str, Any],
    boundary_policy: dict[str, Any],
) -> tuple[dict[str, bytes], list[str]]:
    dirty = dirty_paths()
    if path is None:
        if dirty:
            raise ContextError("working tree is dirty and no reviewed overlay manifest was supplied")
        return {}, []
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if set(manifest) != {"version", "sourceCommit", "reviewedInputs", "preservedExclusions"}:
        raise ContextError("overlay manifest has an unexpected schema")
    if manifest.get("version") != "paprnav-reviewed-overlay-v2" or manifest.get("sourceCommit") != commit:
        raise ContextError("overlay manifest version or source commit differs")
    entries = manifest.get("reviewedInputs")
    preserved = manifest.get("preservedExclusions")
    if not isinstance(entries, list) or not isinstance(preserved, list) or not (entries or preserved):
        raise ContextError("overlay manifest has no reviewed inputs or preserved exclusions")
    if not all(isinstance(item, str) for item in preserved) or len(preserved) != len(set(preserved)):
        raise ContextError("preserved exclusions must be unique paths")
    for source_path in preserved:
        validate_path(source_path)
    expected_paths: set[str] = set()
    result: dict[str, bytes] = {}
    protected_paths = set(boundary_policy.get("approvedMigrationAuthoritySha256", {})) | set(
        boundary_policy.get("protectedBlobSha256", {})
    )
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ContextError("overlay entry has an unexpected schema")
        source_path = entry["path"]
        if not isinstance(source_path, str) or not isinstance(entry["sha256"], str):
            raise ContextError("overlay entry path and sha256 must be strings")
        validate_path(source_path)
        if is_forbidden(source_path, policy):
            raise ContextError("overlay manifest contains a forbidden path")
        if source_path in protected_paths:
            raise ContextError("Package A protected authority may not be supplied by an overlay")
        if source_path in preserved:
            raise ContextError("a path cannot be both a reviewed input and a preserved exclusion")
        absolute = REPO_ROOT / source_path
        info = absolute.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ContextError("overlay path is not one ordinary file")
        content = absolute.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ContextError("overlay file hash differs")
        expected_paths.add(source_path)
        result[source_path] = content
    expected_paths.update(preserved)
    if dirty != expected_paths:
        raise ContextError("dirty working-tree inventory differs from the reviewed overlay manifest")
    return result, sorted(preserved)


def git_blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}").stdout


def selected_sources(
    context_name: str,
    commit: str,
    policy: dict[str, Any],
    overlays: dict[str, bytes],
) -> dict[str, bytes]:
    config = policy["contexts"][context_name]
    prefix = config["sourcePrefix"]
    entries = tree_entries(commit)
    candidate_paths = set(entries) | set(overlays)
    selected: dict[str, bytes] = {}
    for source_path in sorted(candidate_paths):
        if not source_path.startswith(prefix):
            continue
        if is_forbidden(source_path, policy):
            raise ContextError("release input contains a forbidden path")
        if any(source_path.startswith(item) for item in config["excludePrefixes"]):
            continue
        if PurePosixPath(source_path).name in config["excludeNames"]:
            continue
        if source_path in overlays:
            content = overlays[source_path]
        else:
            mode, _ = entries[source_path]
            if mode != "100644":
                raise ContextError("release input is not a regular non-executable file")
            content = git_blob(commit, source_path)
        destination = source_path[len(prefix):]
        validate_path(destination)
        selected[destination] = content
    missing = sorted(path for path in config["requiredPaths"] if path not in candidate_paths)
    if missing:
        raise ContextError(f"required release inputs are absent: {missing}")
    return selected


def add_sealed_migration(commit: str, files: dict[str, bytes]) -> str:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import build_pilot_migration_context as migration

    policy = json.loads(BOUNDARY_POLICY.read_text(encoding="utf-8"))
    manifest, migration_files = migration.context_spec(REPO_ROOT, commit, policy)
    for path, content in migration_files.items():
        files[f"migration/{path}"] = content
    return manifest["manifestSha256"]


def context_spec(
    context_name: str,
    ref: str,
    policy: dict[str, Any],
    overlay_manifest: Path | None,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    if context_name not in policy["contexts"]:
        raise ContextError("unknown release context")
    commit = resolve_commit(ref)
    boundary_policy = candidate_authority(commit)
    overlays, preserved_exclusions = overlay_files(
        overlay_manifest,
        commit,
        policy,
        boundary_policy,
    )
    selected = selected_sources(context_name, commit, policy, overlays)
    source_prefix = policy["contexts"][context_name]["sourcePrefix"]
    files = {f"bootstrap/{path}" if context_name == "bootstrap" else path: content
             for path, content in selected.items()}
    migration_digest = None
    if policy["contexts"][context_name].get("sealedMigrationContext"):
        migration_digest = add_sealed_migration(commit, files)
    entries = [
        {"path": path, "sizeBytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        for path, content in sorted(files.items())
    ]
    body = {
        "version": policy["version"],
        "context": context_name,
        "sourceCommit": commit,
        "sourcePrefix": source_prefix,
        "reviewedInputsSha256": hashlib.sha256(canonical([
            {"path": path, "sha256": hashlib.sha256(content).hexdigest()}
            for path, content in sorted(overlays.items())
        ])).hexdigest(),
        "preservedExclusions": preserved_exclusions,
        "migrationManifestSha256": migration_digest,
        "buildArgs": policy["contexts"][context_name]["buildArgs"],
        "platforms": policy["expectedPlatforms"],
        "files": entries,
    }
    manifest = {**body, "manifestSha256": hashlib.sha256(canonical(body)).hexdigest()}
    files[MANIFEST_NAME] = canonical(manifest)
    return manifest, files


def write_context(destination: Path, files: dict[str, bytes]) -> None:
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ContextError("destination must not exist")
    if destination.parent.resolve() != destination.parent.absolute():
        raise ContextError("destination parent may not traverse a symlink")
    destination.mkdir(mode=0o755)
    for relative, content in sorted(files.items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        target.write_bytes(content)
        target.chmod(0o444)


def verify_context(destination: Path, expected: dict[str, bytes]) -> None:
    actual: set[str] = set()
    for path in destination.rglob("*"):
        relative = path.relative_to(destination).as_posix()
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o444:
            raise ContextError("context contains a symlink, hard link, or mode drift")
        if relative not in expected or path.read_bytes() != expected[relative]:
            raise ContextError("context inventory or bytes differ")
        actual.add(relative)
    if actual != set(expected):
        raise ContextError("context is missing expected files")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--context", choices=("api", "frontend", "bootstrap"), required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--overlay-manifest", type=Path)
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        manifest, files = context_spec(args.context, args.ref, policy, args.overlay_manifest)
        if args.action == "build":
            write_context(args.destination, files)
        verify_context(args.destination, files)
    except (ContextError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({
        "status": "pass",
        "context": args.context,
        "sourceCommit": manifest["sourceCommit"],
        "manifestSha256": manifest["manifestSha256"],
        "fileCount": len(manifest["files"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
