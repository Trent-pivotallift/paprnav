#!/usr/bin/env python3
"""Extract the required structured Claude finding block from a review."""

import argparse
import json
import pathlib
import re

parser = argparse.ArgumentParser()
parser.add_argument("--review", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
text = pathlib.Path(args.review).read_text(encoding="utf-8")
match = re.search(r"<!-- CLAUDE_FINDINGS_JSON -->\s*```json\s*(\[.*?\])\s*```", text, re.DOTALL)
if not match:
    raise SystemExit("Claude review lacks CLAUDE_FINDINGS_JSON block")
try:
    findings = json.loads(match.group(1))
except json.JSONDecodeError as exc:
    raise SystemExit(f"invalid Claude findings JSON: {exc}") from exc
if not isinstance(findings, list):
    raise SystemExit("Claude findings JSON must be an array")
pathlib.Path(args.output).write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
