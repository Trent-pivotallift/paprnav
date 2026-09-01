#!/usr/bin/env python3
"""Record a review attestation against the current packet fingerprint."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess

from review_packet_fingerprint import current_scope_fingerprint


def require_current_packet(
    repo: pathlib.Path,
    run_dir: pathlib.Path,
    manifest: dict[str, object],
    task: str,
) -> None:
    packet_path = run_dir / "review-packet.md"
    packet_hash_path = run_dir / "review-packet.sha256"
    if manifest.get("taskId") != task or manifest.get("stage") != "closure":
        raise SystemExit("closure re-attestation requires a closure-stage packet")
    if not packet_path.is_file() or not packet_hash_path.is_file():
        raise SystemExit("closure re-attestation requires a generated review packet")
    expected_packet_hash = packet_hash_path.read_text().strip()
    if hashlib.sha256(packet_path.read_bytes()).hexdigest() != expected_packet_hash:
        raise SystemExit("closure re-attestation requires the unchanged review packet")
    current, outside = current_scope_fingerprint(repo, manifest, task)
    if outside != manifest.get("outOfScopeDirtyFiles"):
        raise SystemExit("closure re-attestation found changed out-of-scope files")
    if current != manifest.get("scopeFingerprint"):
        raise SystemExit("closure re-attestation requires a current packet fingerprint")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--stage", required=True, choices=("design", "implementation", "closure"))
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--builder", required=True)
    parser.add_argument("--outcome", required=True, choices=("pass", "fail"))
    parser.add_argument("--artifact", required=True)
    parser.add_argument(
        "--reattest",
        action="store_true",
        help="append a fresh closure PASS or FAIL attestation to an already closed run",
    )
    args = parser.parse_args()
    if args.reattest and args.stage != "closure":
        raise SystemExit("re-attestation is allowed only for the closure stage")
    if not args.reviewer.strip() or not args.builder.strip() or args.reviewer == args.builder:
        raise SystemExit("nonempty reviewer and builder identities must be distinct")
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    manifest = json.loads((run_dir / "manifest.json").read_text())
    if not all(manifest.get(key) for key in ("baseRef", "head", "scopeFingerprint")):
        raise SystemExit("generate a current review packet before recording a review")
    artifact = (repo / args.artifact).resolve()
    if repo not in artifact.parents or not artifact.is_file():
        raise SystemExit("artifact must be an existing repository file")
    reviews_path = run_dir / "reviews.json"
    reviews = json.loads(reviews_path.read_text())
    artifact_relative = str(artifact.relative_to(repo))
    if any(review.get("artifact") == artifact_relative for review in reviews):
        raise SystemExit("review artifacts are immutable; use a new artifact path")
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text())
    phase = state.get("phase")
    if args.reattest:
        if phase != "closed":
            raise SystemExit("closure re-attestation requires an already closed run")
        if not any(
            review.get("stage") == "closure" and review.get("outcome") == "pass"
            for review in reviews
        ):
            raise SystemExit("closure re-attestation requires a prior closure PASS")
        require_current_packet(repo, run_dir, manifest, args.task)
    else:
        if args.stage == "design" and phase != "framed" and not state.get("bootstrapException"):
            raise SystemExit("design review is only valid in the framed phase")
        if args.stage == "implementation" and phase != "implementation":
            raise SystemExit("implementation review requires the implementation phase")
        if args.stage == "closure" and phase != "implementation_reviewed":
            raise SystemExit("closure review requires a passed implementation review")
    attestation = {
        "stage": args.stage,
        "reviewer": args.reviewer,
        "builder": args.builder,
        "outcome": args.outcome,
        "reviewedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "baseRef": manifest["baseRef"],
        "head": manifest["head"],
        "scopeFingerprint": manifest["scopeFingerprint"],
        "artifact": artifact_relative,
        "artifactSha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    if args.reattest:
        attestation["reattest"] = True
    reviews.append(attestation)
    reviews_path.write_text(json.dumps(reviews, indent=2) + "\n")
    if args.reattest:
        if args.outcome == "fail":
            state["phase"] = "implementation_reviewed"
            state_path.write_text(json.dumps(state, indent=2) + "\n")
        return 0
    if args.outcome == "pass":
        if args.stage == "design" and not state.get("bootstrapException"):
            state["phase"] = "design_reviewed"
        elif args.stage == "implementation":
            state["phase"] = "implementation_reviewed"
        elif args.stage == "closure":
            state["phase"] = "closed"
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    else:
        if args.stage == "design" and not state.get("bootstrapException"):
            state["phase"] = "framed"
        elif args.stage == "implementation":
            state["phase"] = "implementation"
        elif args.stage == "closure":
            state["phase"] = "implementation_reviewed"
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
