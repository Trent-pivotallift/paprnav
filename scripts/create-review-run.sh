#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <task-id>" >&2
  exit 2
fi

task_id="$1"
if [[ ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "task-id must contain only letters, numbers, dot, underscore, or hyphen" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
run_dir="$repo_root/.ai/review-runs/$task_id"
if [[ -e "$run_dir" ]]; then
  echo "review run already exists: $run_dir" >&2
  exit 1
fi

mkdir -p "$run_dir"
sed "s/{{TASK_ID}}/$task_id/g" "$repo_root/.ai/review-templates/DECISION_PACKET.md" > "$run_dir/decision.md"
sed "s/{{TASK_ID}}/$task_id/g" "$repo_root/.ai/review-templates/CLOSURE_REPORT.md" > "$run_dir/closure.md"
printf '[]\n' > "$run_dir/findings.json"
printf '[]\n' > "$run_dir/reviews.json"
printf '{\n  "phase": "framed",\n  "bootstrapException": null\n}\n' > "$run_dir/state.json"
printf '{\n  "taskId": "%s",\n  "generatedAt": null,\n  "baseRef": null,\n  "head": null,\n  "files": []\n}\n' "$task_id" > "$run_dir/manifest.json"

echo "created review run: $run_dir"
