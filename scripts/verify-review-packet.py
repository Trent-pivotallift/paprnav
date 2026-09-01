#!/usr/bin/env python3
"""Reject stale or mismatched packets before external review."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

from review_packet_fingerprint import current_scope_fingerprint


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--packet", required=True)
    args = parser.parse_args()
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    manifest = json.loads((run_dir / "manifest.json").read_text())
    packet = (repo / args.packet).resolve()
    expected_hash = (run_dir / "review-packet.sha256").read_text().strip()
    errors = []
    if manifest.get("taskId") != args.task or manifest.get("stage") != args.stage or manifest.get("baseRef") != args.base:
        errors.append("task, stage, or base does not match manifest")
    if not packet.is_file() or hashlib.sha256(packet.read_bytes()).hexdigest() != expected_hash:
        errors.append("packet is missing or changed")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
    current, outside = current_scope_fingerprint(repo, manifest, args.task)
    if outside != manifest.get("outOfScopeDirtyFiles"):
        errors.append("dirty out-of-scope inventory changed after packet generation")
    if current != manifest.get("scopeFingerprint"):
        errors.append("working tree changed after packet generation")
    if errors:
        raise SystemExit("; ".join(errors))
    print("review packet is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
