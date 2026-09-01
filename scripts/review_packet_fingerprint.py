#!/usr/bin/env python3
"""Canonical working-tree fingerprint helpers for review packets."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from collections.abc import Iterable
from typing import Any


def git(repo: pathlib.Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def _in_scope(path: str, scopes: Iterable[str]) -> bool:
    return not scopes or any(
        path == scope or path.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def changed_inventory(
    repo: pathlib.Path, base: str, task: str, scopes: list[str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    entries: dict[str, str] = {}
    for line in git(repo, "diff", "--name-status", base, "--").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            entries[fields[-1]] = fields[0]
    for line in git(
        repo, "status", "--porcelain=v1", "--untracked-files=all"
    ).splitlines():
        if len(line) >= 4:
            entries[line[3:].split(" -> ", 1)[-1]] = line[:2]
    candidates = [
        {"path": path, "status": entries[path]}
        for path in sorted(entries)
        if not path.startswith(f".ai/review-runs/{task}/")
    ]
    inside = [item for item in candidates if _in_scope(item["path"], scopes)]
    return inside, [item for item in candidates if item not in inside]


def metadata(repo: pathlib.Path, item: dict[str, Any]) -> dict[str, Any]:
    result = dict(item)
    path = repo / str(item["path"])
    if not path.is_file():
        return {**result, "size": 0, "sha256": None, "readStatus": "absent"}
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return {
            **result,
            "size": None,
            "sha256": None,
            "readStatus": f"read_error:{type(exc).__name__}",
        }
    return {
        **result,
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "readStatus": "readable",
    }


def scope_fingerprint(
    head: str,
    files: list[dict[str, Any]],
    review_inputs: list[dict[str, Any]],
) -> str:
    encoded = json.dumps(
        {"head": head, "files": files + review_inputs},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def current_scope_fingerprint(
    repo: pathlib.Path, manifest: dict[str, Any], task: str
) -> tuple[str, list[dict[str, str]]]:
    """Reproduce a manifest fingerprint from current files and review inputs."""

    inventory, outside = changed_inventory(
        repo,
        str(manifest["baseRef"]),
        task,
        list(manifest.get("scopePaths", [])),
    )
    prior_by_path = {
        str(item["path"]): item for item in manifest.get("files", [])
    }
    files = [
        metadata(
            repo,
            {
                **dict(prior_by_path.get(item["path"], item)),
                **item,
            },
        )
        for item in inventory
    ]
    review_inputs = [
        metadata(repo, dict(item)) for item in manifest.get("reviewInputs", [])
    ]
    head = git(repo, "rev-parse", "HEAD").strip()
    return scope_fingerprint(head, files, review_inputs), outside
