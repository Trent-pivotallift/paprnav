#!/usr/bin/env python3
"""Build a deterministic review packet from Git state and review artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess

from review_packet_fingerprint import scope_fingerprint


def git(repo: pathlib.Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def task_id(value: str) -> str:
    if not value or any(not (char.isalnum() or char in "._-") for char in value):
        raise argparse.ArgumentTypeError("invalid task id")
    return value


def changed_files(repo: pathlib.Path, base: str) -> list[dict[str, str]]:
    entries: dict[str, str] = {}
    for line in git(repo, "diff", "--name-status", base, "--").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            entries[fields[-1]] = fields[0]
    for line in git(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if len(line) >= 4:
            path = line[3:].split(" -> ", 1)[-1]
            entries[path] = line[:2]
    return [{"path": path, "status": entries[path]} for path in sorted(entries)]


def in_scope(path: str, scopes: list[str]) -> bool:
    return not scopes or any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in scopes)


def metadata(repo: pathlib.Path, item: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = dict(item)
    path = repo / item["path"]
    if not path.is_file():
        return {**result, "size": 0, "sha256": None, "readStatus": "absent"}
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return {**result, "size": None, "sha256": None, "readStatus": f"read_error:{type(exc).__name__}"}
    return {**result, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "readStatus": "readable"}


def read_utf8(path: pathlib.Path) -> tuple[str, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return "", "binary_or_non_utf8"
    except OSError as exc:
        return "", f"read_error:{type(exc).__name__}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=task_id)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--stage", default="implementation")
    parser.add_argument("--path", action="append", default=[], dest="paths")
    parser.add_argument(
        "--review-input",
        action="append",
        default=[],
        dest="review_inputs",
        help="repository-relative file whose bytes must be bound to this review",
    )
    parser.add_argument("--out-of-scope-reason")
    args = parser.parse_args()

    repo = pathlib.Path(git(pathlib.Path.cwd(), "rev-parse", "--show-toplevel").strip())
    if not git(repo, "rev-parse", "--verify", "--quiet", args.base, check=False).strip():
        raise SystemExit(f"base ref does not exist: {args.base}")
    run_dir = repo / ".ai" / "review-runs" / args.task
    decision, findings = run_dir / "decision.md", run_dir / "findings.json"
    if not decision.is_file() or not findings.is_file():
        raise SystemExit(f"review run is incomplete: {run_dir}")

    all_files = changed_files(repo, args.base)
    implementation_candidates = [
        item for item in all_files
        if not item["path"].startswith(f".ai/review-runs/{args.task}/")
    ]
    scoped = [
        item for item in implementation_candidates
        if in_scope(item["path"], args.paths)
    ]
    out_of_scope = [item for item in implementation_candidates if item not in scoped]
    if out_of_scope and not args.out_of_scope_reason:
        raise SystemExit("dirty files exist outside scope; provide --out-of-scope-reason")
    files = [metadata(repo, item) for item in scoped]
    unreadable = [item for item in files if str(item["readStatus"]).startswith("read_error")]
    if unreadable:
        raise SystemExit(f"cannot read scoped files: {[item['path'] for item in unreadable]}")

    requested_review_inputs = [
        decision.relative_to(repo).as_posix(),
        findings.relative_to(repo).as_posix(),
        *args.review_inputs,
    ]
    review_input_paths: list[str] = []
    for requested in requested_review_inputs:
        relative = pathlib.Path(requested)
        if relative.is_absolute():
            raise SystemExit(f"review input must be repository-relative: {requested}")
        resolved = (repo / relative).resolve()
        try:
            normalized = resolved.relative_to(repo).as_posix()
        except ValueError as exc:
            raise SystemExit(f"review input escapes repository: {requested}") from exc
        review_input_paths.append(normalized)
    review_input_paths = list(dict.fromkeys(review_input_paths))
    review_inputs = [
        metadata(repo, {"path": path, "status": "review_input"})
        for path in review_input_paths
    ]
    unavailable_inputs = [
        item for item in review_inputs if item["readStatus"] != "readable"
    ]
    if unavailable_inputs:
        raise SystemExit(
            f"review inputs must be readable files: {[item['path'] for item in unavailable_inputs]}"
        )

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    head = git(repo, "rev-parse", "HEAD").strip()
    manifest = {
        "taskId": args.task,
        "stage": args.stage,
        "generatedAt": generated_at,
        "baseRef": args.base,
        "head": head,
        "scopePaths": args.paths,
        "scopeFingerprint": scope_fingerprint(head, files, review_inputs),
        "files": files,
        "reviewInputs": review_inputs,
        "outOfScopeDirtyFiles": out_of_scope,
        "outOfScopeReason": args.out_of_scope_reason,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    untracked: list[str] = []
    for item in files:
        if item["status"] != "??":
            continue
        relative = pathlib.Path(str(item["path"]))
        text, error = read_utf8(repo / relative)
        if error:
            untracked.append(f"### `{relative}`\n\nContent omitted: `{error}`; size={item['size']}; sha256={item['sha256']}.")
            continue
        truncated = len(text) > 200_000
        untracked.append(
            f"### `{relative}`\n\nsize={item['size']}; sha256={item['sha256']}; "
            f"truncated={str(truncated).lower()}\n\n```text\n{text[:200_000]}\n```"
        )

    decision_text, _ = read_utf8(decision)
    findings_text, _ = read_utf8(findings)
    bound_inputs: list[str] = []
    for item in review_inputs:
        path = repo / str(item["path"])
        text, error = read_utf8(path)
        if error:
            bound_inputs.append(
                f"### `{item['path']}`\n\nContent omitted: `{error}`; "
                f"size={item['size']}; sha256={item['sha256']}."
            )
            continue
        bound_inputs.append(
            f"### `{item['path']}`\n\nsize={item['size']}; sha256={item['sha256']}\n\n"
            f"```text\n{text}\n```"
        )
    diff_args = ["diff", args.base, "--", *args.paths] if args.paths else ["diff", args.base, "--"]
    packet = f"""# Review packet: {args.task}

Stage: {args.stage}
Generated: {generated_at}
Base: `{args.base}`
Head: `{head}`
Scope fingerprint: `{manifest['scopeFingerprint']}`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

{decision_text}

## Current finding ledger

```json
{findings_text}
```

## Hash-bound review inputs

{chr(10).join(bound_inputs)}

## Changed-file manifest

```json
{json.dumps(manifest, indent=2)}
```

## Diff against base

```diff
{git(repo, *diff_args)}
```

## Untracked text files

{chr(10).join(untracked) if untracked else 'None.'}
"""
    packet_path = run_dir / "review-packet.md"
    packet_path.write_text(packet)
    (run_dir / "review-packet.sha256").write_text(hashlib.sha256(packet.encode()).hexdigest() + "\n")
    print(packet_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
