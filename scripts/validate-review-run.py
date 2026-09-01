#!/usr/bin/env python3
"""Validate evidence and final-state gates for a review run."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess

from review_packet_fingerprint import current_scope_fingerprint


STATUSES = {"open", "fix_in_progress", "fixed_pending_verification", "closed", "accepted_risk", "rejected_finding", "deferred"}
TERMINAL = {"closed", "accepted_risk", "rejected_finding", "deferred"}
SEVERITIES = {"blocker", "high", "medium", "low"}
STAGES = {"design", "implementation", "external_critic", "closure"}
REQUIRED = {"id", "stage", "reviewer", "severity", "status", "invariant", "summary", "evidence", "impact", "requiredClosure", "closureEvidence"}
ALLOWED = REQUIRED | {"disposition", "owner", "revisitCondition", "supersedes"}


def sections_have_content(text: str, headings: list[str]) -> list[str]:
    missing: list[str] = []
    lines = text.splitlines()
    for heading in headings:
        try:
            start = lines.index(f"## {heading}") + 1
        except ValueError:
            missing.append(heading)
            continue
        content = []
        for line in lines[start:]:
            if line.startswith("## "):
                break
            if line.strip():
                content.append(line)
        if not content:
            missing.append(heading)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    if not args.task or any(not (char.isalnum() or char in "._-") for char in args.task):
        raise SystemExit("invalid task id")
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    errors: list[str] = []
    required_files = ("decision.md", "findings.json", "manifest.json", "reviews.json", "state.json", "closure.md")
    for name in required_files:
        if not (run_dir / name).is_file():
            errors.append(f"missing {name}")
    if errors:
        print("\n".join(errors))
        return 1
    try:
        findings = json.loads((run_dir / "findings.json").read_text())
        manifest = json.loads((run_dir / "manifest.json").read_text())
        reviews = json.loads((run_dir / "reviews.json").read_text())
        state = json.loads((run_dir / "state.json").read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"invalid review data: {exc}")
        return 1
    if not isinstance(findings, list):
        errors.append("findings.json must contain an array")
        findings = []
    if not isinstance(reviews, list):
        errors.append("reviews.json must contain an array")
        reviews = []

    seen: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"finding[{index}] must be an object")
            continue
        missing = REQUIRED - finding.keys()
        label = finding.get("id") or f"finding[{index}]"
        if missing:
            errors.append(f"{label} lacks required fields: {sorted(missing)}")
        extras = finding.keys() - ALLOWED
        if extras:
            errors.append(f"{label} has unsupported fields: {sorted(extras)}")
        if not isinstance(finding.get("id"), str) or not finding.get("id", "").strip() or label in seen:
            errors.append(f"missing or duplicate finding id: {label}")
        seen.add(str(label))
        if finding.get("stage") not in STAGES or finding.get("severity") not in SEVERITIES or finding.get("status") not in STATUSES:
            errors.append(f"{label} has invalid stage, severity, or status")
        for field in ("reviewer", "invariant", "summary", "impact", "requiredClosure"):
            if not isinstance(finding.get(field), str) or not finding.get(field).strip():
                errors.append(f"{label} has empty {field}")
        if not isinstance(finding.get("evidence"), list) or not finding.get("evidence") or any(not isinstance(item, (str, dict)) or (isinstance(item, str) and not item.strip()) for item in finding.get("evidence", [])):
            errors.append(f"{label} lacks evidence")
        if not isinstance(finding.get("closureEvidence"), list) or any(not isinstance(item, str) or not item.strip() for item in finding.get("closureEvidence", [])):
            errors.append(f"{label} has invalid closure evidence")
        if "supersedes" in finding and (not isinstance(finding["supersedes"], list) or any(not isinstance(item, str) for item in finding["supersedes"])):
            errors.append(f"{label} has invalid supersedes")
        for field in ("disposition", "owner", "revisitCondition"):
            if field in finding and finding[field] is not None and not isinstance(finding[field], str):
                errors.append(f"{label} has invalid {field}")
        status = finding.get("status")
        if status not in TERMINAL:
            errors.append(f"{label} is not dispositioned: {status}")
        if finding.get("severity") == "blocker" and status == "deferred":
            errors.append(f"{label} is a deferred blocker")
        if status in {"closed", "rejected_finding"} and not finding.get("closureEvidence"):
            errors.append(f"{label} lacks closure evidence")
        if status in {"accepted_risk", "deferred"} and not all(finding.get(key) for key in ("owner", "disposition", "revisitCondition")):
            errors.append(f"{label} {status} lacks owner, rationale, or revisit condition")

    if not manifest.get("generatedAt") or not manifest.get("baseRef") or not manifest.get("scopeFingerprint"):
        errors.append("manifest has not been generated with a fingerprint")
    if manifest.get("outOfScopeDirtyFiles") and not manifest.get("outOfScopeReason"):
        errors.append("out-of-scope dirty files lack a reason")
    current, current_outside = current_scope_fingerprint(repo, manifest, args.task)
    if manifest.get("scopeFingerprint") != current:
        errors.append("working tree changed after packet generation")
    if current_outside != manifest.get("outOfScopeDirtyFiles"):
        errors.append("dirty out-of-scope inventory changed after packet generation")

    latest_by_stage: dict[str, dict[str, object]] = {}
    review_required = {"stage", "reviewer", "builder", "outcome", "reviewedAt", "baseRef", "head", "scopeFingerprint", "artifact", "artifactSha256"}
    for index, review in enumerate(reviews):
        if not isinstance(review, dict) or review_required - review.keys():
            errors.append(f"review[{index}] is malformed")
            continue
        if any(not isinstance(review.get(field), str) or not review.get(field, "").strip() for field in review_required):
            errors.append(f"review[{index}] has empty or non-string fields")
            continue
        if review["stage"] not in {"design", "implementation", "closure"} or review["outcome"] not in {"pass", "fail"}:
            errors.append(f"review[{index}] has invalid stage or outcome")
            continue
        latest_by_stage[str(review["stage"])] = review
        if review["reviewer"] == review["builder"]:
            errors.append(f"{review['stage']} reviewer is the builder")
        artifact = repo / str(review["artifact"])
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != review["artifactSha256"]:
            errors.append(f"review artifact missing or changed: {review['artifact']}")
    design_review = latest_by_stage.get("design")
    implementation_review = latest_by_stage.get("implementation")
    closure_review = latest_by_stage.get("closure")
    if not design_review or design_review.get("outcome") != "pass":
        errors.append("no passed independent design review")
    if not implementation_review or implementation_review.get("outcome") != "pass":
        errors.append("no passed independent implementation review")
    if not closure_review or closure_review.get("outcome") != "pass":
        errors.append("no passed independent closure review")
    if closure_review and closure_review.get("scopeFingerprint") != manifest.get("scopeFingerprint"):
        errors.append("final closure review does not cover current scope fingerprint")
    if state.get("phase") != "closed":
        errors.append(f"review phase is not closed: {state.get('phase')}")

    ledger_ids = {str(item.get("id")) for item in findings if isinstance(item, dict)}
    successful_claude = [
        path for path in run_dir.glob("claude-external-critic-*.md")
        if not path.name.endswith((".error.md", ".partial.md"))
    ]
    for claude_path in successful_claude:
        sidecar = claude_path.with_suffix(".findings.json")
        if not sidecar.is_file():
            errors.append(f"Claude review lacks structured findings: {claude_path.name}")
            continue
        try:
            candidates = json.loads(sidecar.read_text())
        except json.JSONDecodeError:
            errors.append(f"Claude findings are invalid JSON: {sidecar.name}")
            continue
        if not isinstance(candidates, list):
            errors.append(f"Claude findings must be an array: {sidecar.name}")
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("id"), str):
                errors.append(f"Claude finding is malformed in {sidecar.name}")
                continue
            candidate_id = candidate["id"]
            required_candidate = {"id", "severity", "invariant", "summary", "evidence", "impact", "requiredClosure"}
            if required_candidate - candidate.keys() or candidate.get("severity") not in SEVERITIES or not isinstance(candidate.get("evidence"), list) or not candidate.get("evidence"):
                errors.append(f"Claude finding is structurally invalid: {candidate_id}")
            if not re.fullmatch(rf"{re.escape(args.task)}-CC-\d+", candidate_id):
                errors.append(f"Claude finding has invalid ID: {candidate_id}")
            if candidate_id not in ledger_ids:
                errors.append(f"Claude finding is not dispositioned in ledger: {candidate_id}")

    decision = (run_dir / "decision.md").read_text()
    closure = (run_dir / "closure.md").read_text()
    for section in sections_have_content(decision, ["Objective", "Safety and correctness invariants", "Proposed design", "Test strategy"]):
        errors.append(f"decision section is empty: {section}")
    for section in sections_have_content(closure, ["Outcome", "Invariants verified", "Verification performed", "Final scope reviewed", "Not verified"]):
        errors.append(f"closure section is empty: {section}")
    if errors:
        print("review run is not closable:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"review run is closable: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
