#!/usr/bin/env bash
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  echo "claude is not on PATH. Install/authenticate Claude Code first." >&2
  exit 127
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

base_ref="${1:-origin/main}"
if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
  base_ref="HEAD"
fi

mkdir -p .ai/reviews
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_path="${CLAUDE_REVIEW_OUTPUT:-.ai/reviews/claude-review-${timestamp}.md}"
review_model="${CLAUDE_REVIEW_MODEL:-sonnet}"
review_focus="${CLAUDE_REVIEW_FOCUS:-High-stakes changes in the current working tree.}"
review_paths="${CLAUDE_REVIEW_PATHS:-All changed and untracked files relevant to the review focus.}"
artifact_stem="${output_path%.md}"
events_path="${CLAUDE_REVIEW_EVENTS:-${artifact_stem}.events.jsonl}"
debug_path="${CLAUDE_REVIEW_DEBUG:-${artifact_stem}.debug.log}"
partial_path="${CLAUDE_REVIEW_PARTIAL:-${artifact_stem}.partial.md}"

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
You are reviewing the paprnav repository as an external code reviewer.

Review scope:
- Current working tree in: ${repo_root}
- Compare against base ref: ${base_ref}
- Include staged and unstaged changes.
- Review focus: ${review_focus}
- Focus paths: ${review_paths}
- Read listed untracked files directly; they do not appear in ordinary git diff output.
- Do not edit files.
- Do not run destructive commands.

Review stance:
- Lead with concrete findings, ordered by severity.
- Focus on high-stakes work: complex or critical logic, security/privacy decisions, AWS/IAM/Terraform decisions, cost/billing decisions, data-loss risks, migration risks, and meaningful missing tests.
- Do not spend review attention on low-level patterned edits unless they create one of the risks above.
- Ground each finding in file paths and line numbers when possible.
- Separate confirmed issues from questions or speculative risks.
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
1. Findings
2. Open Questions
3. Verification Notes
4. Brief Summary
PROMPT
)"

echo "Running Claude review against ${base_ref}..."
echo "Writing review to ${output_path}"
echo "Streaming events to ${events_path}"
echo "Writing diagnostics to ${debug_path}"
echo "Preserving partial text at ${partial_path}"

if ! claude "${claude_args[@]}" "$prompt" |
  python3 scripts/claude-review-stream.py \
    --output "$output_path" \
    --events "$events_path" \
    --partial "$partial_path"; then
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

echo
echo "Claude review saved to ${output_path}"
echo "Claude event stream saved to ${events_path}"
echo "Claude diagnostics saved to ${debug_path}"
