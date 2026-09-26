#!/usr/bin/env python3
"""Build, verify, or launch a sealed context from reviewed Git commit blobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

import verify_pilot_release_boundary as boundary


CONTEXT_POLICY = {
    "version": "paprnav-sealed-migration-context-v1",
    "manifestName": "migration-context.json",
    "sourceGitMode": "100644",
    "sourceToDestination": {
        "backend/alembic.ini": "alembic.ini",
        "backend/app/": "app/",
    },
}
MANIFEST_NAME = CONTEXT_POLICY["manifestName"]
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


class ContextError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def safe_path(raw: bytes) -> str:
    try:
        value = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContextError("context path is not UTF-8") from exc
    if not value or "\\" in value or "\0" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ContextError("context path is not a canonical relative path")
    return value


def destination_path(source: bytes) -> str:
    source_text = safe_path(source)
    if source_text == "backend/alembic.ini":
        return "alembic.ini"
    if source_text.startswith("backend/app/"):
        return safe_path(source[len(b"backend/"):])
    raise ContextError("source has no approved context destination")


def tree_records(repo: Path, commit: str) -> dict[bytes, tuple[bytes, bytes]]:
    raw = boundary.git(repo, "ls-tree", "-rz", commit).stdout
    if not raw or not raw.endswith(b"\0"):
        raise ContextError("invalid NUL-delimited Git tree records")
    records: dict[bytes, tuple[bytes, bytes]] = {}
    for record in raw[:-1].split(b"\0"):
        try:
            header, path = record.split(b"\t", 1)
            mode, kind, object_id = header.split(b" ")
        except ValueError as exc:
            raise ContextError("invalid Git tree record") from exc
        if path in records:
            raise ContextError("duplicate Git tree path")
        if not re.fullmatch(b"[0-9a-f]{40}|[0-9a-f]{64}", object_id):
            raise ContextError("invalid Git object identity")
        records[path] = (mode, kind)
    return records


def context_spec(repo: Path, ref: str, policy: dict[str, Any]) -> tuple[dict, dict[str, bytes]]:
    if policy.get("migrationContext") != CONTEXT_POLICY:
        raise ContextError("migration context policy differs from the reviewed mapping/modes")
    # Resolve once; every subsequent read uses the immutable commit identity.
    commit = boundary.resolve_commit(repo, ref)
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ContextError("release ref did not resolve to an exact commit")
    source_paths = policy.get("approvedMigrationAuthoritySha256", {})
    destinations: set[str] = set()
    for source in source_paths:
        try:
            destination = destination_path(source.encode("utf-8", "strict"))
        except UnicodeEncodeError as exc:
            raise ContextError("context path is not UTF-8") from exc
        if destination in destinations or destination == MANIFEST_NAME:
            raise ContextError("duplicate context destination")
        destinations.add(destination)
    release = boundary.verify_release(repo, commit, policy)
    if release["status"] != "pass":
        raise ContextError("release source check failed: " + "; ".join(release["errors"]))
    records = tree_records(repo, commit)
    if set(records) != set(boundary.tree_paths(repo, commit)):
        raise ContextError("Git name and mode inventories differ")
    files: dict[str, bytes] = {}
    entries: list[dict] = []
    for source, expected_hash in sorted(source_paths.items()):
        raw_source = source.encode("utf-8")
        destination = destination_path(raw_source)
        if records.get(raw_source) != (b"100644", b"blob"):
            raise ContextError("context source is missing or has an unapproved Git mode/type")
        content = boundary.blob_bytes(repo, commit, raw_source)
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise ContextError("context source hash differs")
        files[destination] = content
        entries.append({"sourcePath": source, "destinationPath": destination,
                        "gitMode": "100644", "sizeBytes": len(content), "sha256": expected_hash})
    body = {"version": CONTEXT_POLICY["version"], "sourceCommit": commit, "files": entries}
    manifest = {**body, "manifestSha256": hashlib.sha256(canonical_json(body)).hexdigest()}
    files[MANIFEST_NAME] = canonical_json(manifest)
    return manifest, files


def open_directory(path: Path) -> int:
    """Walk from / using descriptors, refusing symlink ancestors as well."""
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise ContextError("destination traversal is forbidden")
    fd = os.open(absolute.anchor, DIRECTORY_FLAGS)
    try:
        for part in absolute.parts[1:]:
            next_fd = os.open(part, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def file_directories(files: dict[str, bytes]) -> set[str]:
    return {"/".join(path.split("/")[:i]) for path in files for i in range(1, len(path.split("/")))}


def build_context(repo: Path, ref: str, policy: dict, destination: Path) -> dict:
    manifest, files = context_spec(repo, ref, policy)
    destination = destination.absolute()
    if destination.name in {"", ".", ".."}:
        raise ContextError("a new context directory is required")
    parent_fd = open_directory(destination.parent)
    try:
        # No overwrite, merge, reuse, or symlink following is permitted.
        os.mkdir(destination.name, mode=0o700, dir_fd=parent_fd)
        root_fd = os.open(destination.name, DIRECTORY_FLAGS, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    directories = {"": root_fd}
    try:
        for path in sorted(file_directories(files), key=lambda item: (item.count("/"), item)):
            parent, _, name = path.rpartition("/")
            os.mkdir(name, mode=0o700, dir_fd=directories[parent])
            directories[path] = os.open(name, DIRECTORY_FLAGS, dir_fd=directories[parent])
        for path, content in sorted(files.items()):
            parent, _, name = path.rpartition("/")
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directories[parent])
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fchmod(output.fileno(), 0o444)
        for path in sorted(directories, key=lambda item: (item.count("/"), item), reverse=True):
            os.fchmod(directories[path], 0o555)
    finally:
        # On an I/O failure an incomplete directory is left for inspection. It
        # cannot be reused and cannot pass exact verification.
        for fd in directories.values():
            os.close(fd)
    verify_files(destination, files)
    return manifest


def verify_files(destination: Path, expected_files: dict[str, bytes]) -> None:
    seen_files: set[str] = set()
    seen_dirs: set[str] = set()

    def walk(fd: int, prefix: str) -> None:
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o555:
            raise ContextError("context directory is not read-only")
        for name in sorted(os.listdir(fd)):
            relative = prefix + name
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                seen_dirs.add(relative)
                child = os.open(name, DIRECTORY_FLAGS, dir_fd=fd)
                try:
                    walk(child, relative + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                if relative not in expected_files:
                    raise ContextError("context contains an unlisted file")
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                with os.fdopen(child, "rb") as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o444 or info.st_nlink != 1:
                        raise ContextError("context file has an unapproved type/mode/link count")
                    if source.read() != expected_files[relative]:
                        raise ContextError("context file or manifest bytes differ")
                seen_files.add(relative)
            else:
                raise ContextError("context contains a symlink or non-regular file")

    root = open_directory(destination)
    try:
        walk(root, "")
    finally:
        os.close(root)
    if seen_files != set(expected_files) or seen_dirs != file_directories(expected_files):
        raise ContextError("context inventory differs")


def verify_context(repo: Path, ref: str, policy: dict, destination: Path) -> dict:
    manifest, files = context_spec(repo, ref, policy)
    verify_files(destination, files)
    return manifest


def launch_environment(runtime_environment: dict[str, str]) -> dict[str, str]:
    database_url = runtime_environment.get("DATABASE_URL", "")
    if not database_url.strip():
        raise ContextError("DATABASE_URL must be supplied at launch; development fallback is forbidden")
    return {"DATABASE_URL": database_url, "PAPRNAV_DISABLE_DOTENV": "1",
            "PYTHONDONTWRITEBYTECODE": "1", "PAPRNAV_ENV": "pilot"}


def launch_command(destination: Path, policy: dict, interpreter: str) -> list[str]:
    # -I ignores PYTHON* environment variables, so -B is required as well as
    # PYTHONDONTWRITEBYTECODE for explicit bytecode suppression.
    return [str(Path(interpreter).absolute()), "-I", "-B", "-m", "alembic", "-c",
            str(destination.absolute() / "alembic.ini"), "upgrade", policy["expectedMigrationHeads"][0]]


def run_context(repo: Path, ref: str, policy: dict, destination: Path,
                runtime_environment: dict[str, str], interpreter: str = sys.executable) -> dict:
    environment = launch_environment(runtime_environment)
    manifest = verify_context(repo, ref, policy, destination)
    result = subprocess.run(launch_command(destination, policy, interpreter),
                            cwd=destination, env=environment, capture_output=True)
    # Never forward child output: driver/configuration exceptions can contain
    # the runtime URL. The source manifest never records runtime credentials.
    if result.returncode:
        raise ContextError("migration process failed; child output suppressed")
    verify_context(repo, ref, policy, destination)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "run"))
    parser.add_argument("--ref", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--policy", default=boundary.DEFAULT_POLICY_PATH)
    args = parser.parse_args()
    try:
        repo = Path(boundary.path_text(boundary.git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.rstrip(b"\n")))
        policy_path = (repo / args.policy).resolve()
        policy_path.relative_to(repo)
        policy = json.loads(policy_path.read_text(encoding="utf-8"), object_pairs_hook=boundary.unique_json_object)
        if args.action == "build":
            manifest = build_context(repo, args.ref, policy, args.destination)
        elif args.action == "verify":
            manifest = verify_context(repo, args.ref, policy, args.destination)
        else:
            manifest = run_context(repo, args.ref, policy, args.destination, dict(os.environ))
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps({"status": "pass", "sourceCommit": manifest["sourceCommit"],
                      "manifestSha256": manifest["manifestSha256"], "fileCount": len(manifest["files"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
