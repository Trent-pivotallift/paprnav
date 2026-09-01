#!/usr/bin/env bash
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  echo "claude is not on PATH. Install/authenticate Claude Code first." >&2
  exit 127
fi

task_id=""
review_stage="external-critic"
base_ref="HEAD"
packet_path=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --task) task_id="${2:-}"; shift 2 ;;
    --stage) review_stage="${2:-}"; shift 2 ;;
    --base) base_ref="${2:-}"; shift 2 ;;
    --packet) packet_path="${2:-}"; shift 2 ;;
    -h|--help)
      echo "usage: $0 --task <task-id> [--stage <stage>] [--base <ref>] [--packet <path>]"
      exit 0
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$task_id" || ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "--task with a safe task id is required" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

env_file="${CLAUDE_REVIEW_ENV_FILE:-.env.claude-review}"
if [[ -f "$env_file" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
fi

if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
  echo "base ref does not exist: $base_ref" >&2
  exit 2
fi

run_dir=".ai/review-runs/${task_id}"
if [[ -z "$packet_path" ]]; then
  packet_path="${run_dir}/review-packet.md"
fi
if [[ ! -f "$packet_path" ]]; then
  echo "review packet does not exist: $packet_path" >&2
  echo "run: python3 scripts/build-review-packet.py --task $task_id --base $base_ref --stage $review_stage" >&2
  exit 2
fi
if [[ ! -f "${run_dir}/manifest.json" || ! -f "${run_dir}/findings.json" ]]; then
  echo "review run lacks manifest or finding ledger: $run_dir" >&2
  exit 2
fi

python3 scripts/verify-review-packet.py \
  --task "$task_id" \
  --stage "$review_stage" \
  --base "$base_ref" \
  --packet "$packet_path"

mkdir -p "$run_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_path="${CLAUDE_REVIEW_OUTPUT:-${run_dir}/claude-${review_stage}-${timestamp}.md}"
output_dir="${output_path%/*}"
output_name="${output_path##*/}"
if [[ "$output_dir" != "$run_dir" || ! "$output_name" =~ ^claude-external-critic-[A-Za-z0-9][A-Za-z0-9_-]*\.md$ ]]; then
  echo "Claude review output must be claude-external-critic-<suffix>.md inside $run_dir" >&2
  exit 2
fi
review_model="${CLAUDE_REVIEW_MODEL:-sonnet}"
artifact_stem="${output_path%.md}"
events_path="${CLAUDE_REVIEW_EVENTS:-${artifact_stem}.events.jsonl}"
debug_path="${CLAUDE_REVIEW_DEBUG:-${artifact_stem}.debug.log}"
partial_path="${CLAUDE_REVIEW_PARTIAL:-${artifact_stem}.partial.md}"
for artifact_path in "$events_path" "$debug_path" "$partial_path"; do
  artifact_dir="${artifact_path%/*}"
  artifact_name="${artifact_path##*/}"
  if [[ "$artifact_dir" != "$run_dir" || ! "$artifact_name" =~ ^claude-external-critic-[A-Za-z0-9._-]+\.(events\.jsonl|debug\.log|partial\.md)$ ]]; then
    echo "Claude diagnostic artifacts must stay inside $run_dir" >&2
    exit 2
  fi
done

claude_args=(
  --print
  --permission-mode plan
  --model "$review_model"
  --verbose
  --output-format stream-json
  --include-partial-messages
  --debug-file "$debug_path"
  --name "paprnav-review-${timestamp}"
)

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  claude_args=(--bare "${claude_args[@]}")
fi

prompt="$(cat <<PROMPT
You are the independent Claude critic for paprnav review run ${task_id}, stage
${review_stage}. Read the complete packet at ${packet_path} before reviewing.

Review scope:
- Current working tree in: ${repo_root}
- Compare against base ref: ${base_ref}
- Include staged and unstaged changes.
- Treat the packet manifest as a starting point, not a scope boundary.
- Read listed untracked files directly; they do not appear in ordinary git diff output.
- Search for affected callers, readers, migrations, jobs, administrative scripts,
  tests, contracts, and documentation omitted from the manifest.
- Do not edit files.
- Do not run destructive commands.

Review stance:
- Lead with concrete findings, ordered by severity.
- Focus on high-stakes work: complex or critical logic, security/privacy decisions, AWS/IAM/Terraform decisions, cost/billing decisions, data-loss risks, migration risks, and meaningful missing tests.
- Do not spend review attention on low-level patterned edits unless they create one of the risks above.
- Ground each finding in file paths and line numbers when possible.
- Separate confirmed issues from questions or speculative risks.
- Do not repeat closed ledger findings unless their closure evidence is inadequate.
- Give each finding a stable ID prefixed ${task_id}-CC-.
- Format every finding heading exactly as: ### ${task_id}-CC-NNN — short title
- For each finding state the violated invariant, evidence, impact, and required closure.
- Keep summary brief and secondary.

Useful context:
- paprnav ingests aircraft maintenance log PDFs, performs OCR, extracts structured logbook entries, and supports AD review/matching.
- Current cloud direction is AWS pilot deployment with S3 storage, Textract OCR, Terraform remote state, customer/account/aircraft billing tags, and least-privilege runtime roles.
- Local defaults should remain safe for development and CI.

Suggested commands if needed:
- git status --short
- git diff --stat ${base_ref}
- git diff ${base_ref} -- . ':(exclude)backend/.data' ':(exclude)**/.venv' ':(exclude)**/.terraform'
- cd backend && PYTHONPATH=. .venv/bin/pytest
- cd frontend/paprnav-frontend && npm run lint

Return Markdown with sections:
1. Scope Limitations
2. Findings
3. Open Questions
4. Verification Notes
5. Brief Summary

After Scope Limitations and before prose Findings, emit this required machine
block. Populate one object per finding, or use an empty array. Do not wrap it in
any additional fence or omit any field:

<!-- CLAUDE_FINDINGS_JSON -->
\`\`\`json
[
  {
    "id": "${task_id}-CC-001",
    "severity": "high",
    "invariant": "...",
    "summary": "...",
    "evidence": ["path:line and fact"],
    "impact": "...",
    "requiredClosure": "..."
  }
]
\`\`\`
PROMPT
)"

echo "Running Claude review against ${base_ref}..."
echo "Review run ${task_id}, stage ${review_stage}"
echo "Reading packet from ${packet_path}"
echo "Writing review to ${output_path}"
echo "Streaming events to ${events_path}"
echo "Writing diagnostics to ${debug_path}"
echo "Preserving partial text at ${partial_path}"

if ! claude "${claude_args[@]}" "$prompt" |
  python3 scripts/claude-review-stream.py \
    --output "$output_path" \
    --events "$events_path" \
    --partial "$partial_path"; then
  if [[ -f "$output_path" ]]; then
    mv "$output_path" "${artifact_stem}.error.md"
  fi
  cat >&2 <<'ERR'

Claude review failed.

If the failure says "Not logged in" from Codex but Claude works in your normal
terminal, bridge auth by creating an ignored local file:

  cp scripts/claude-review.env.example .env.claude-review
  chmod 600 .env.claude-review
  $EDITOR .env.claude-review

Then set ANTHROPIC_API_KEY in that file, or export it only for the command:

  ANTHROPIC_API_KEY=... scripts/claude-review.sh

Do not paste the key into chat. Do not commit .env.claude-review.
ERR
  exit 1
fi

if ! python3 scripts/extract-claude-findings.py \
  --review "$output_path" \
  --output "${artifact_stem}.findings.json"; then
  mv "$output_path" "${artifact_stem}.error.md"
  exit 1
fi

echo
echo "Claude review saved to ${output_path}"
echo "Claude event stream saved to ${events_path}"
echo "Claude diagnostics saved to ${debug_path}"
