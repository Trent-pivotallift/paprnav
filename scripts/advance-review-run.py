#!/usr/bin/env python3
"""Advance a review run through its monotonic implementation phase."""

import argparse
import json
import pathlib
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True)
parser.add_argument("--to", required=True, choices=("design_reviewed", "implementation"))
parser.add_argument("--bootstrap-reason")
args = parser.parse_args()
repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
run_dir = repo / ".ai" / "review-runs" / args.task
state_path = run_dir / "state.json"
state = json.loads(state_path.read_text())
reviews = json.loads((run_dir / "reviews.json").read_text())
design_reviews = [review for review in reviews if review.get("stage") == "design"]
design_passed = bool(design_reviews) and design_reviews[-1].get("outcome") == "pass"
if not design_passed:
    raise SystemExit("passed design attestation is missing")
if args.to == "design_reviewed":
    if state.get("phase") != "framed" or not args.bootstrap_reason:
        raise SystemExit("bootstrap transition requires framed phase and --bootstrap-reason")
    state["bootstrapException"] = args.bootstrap_reason
    state["phase"] = "design_reviewed"
else:
    if state.get("phase") != "design_reviewed":
        raise SystemExit("run must have passed design review before implementation")
    state["phase"] = "implementation"
state_path.write_text(json.dumps(state, indent=2) + "\n")
