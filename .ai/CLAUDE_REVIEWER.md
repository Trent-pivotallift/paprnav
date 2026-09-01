# Claude external critic

Claude is an independent critic inside the Codex-led adversarial review process.
It is not the primary reviewer, decision owner, or closure authority. Read
`.ai/REVIEW_PROCESS.md` for the complete workflow.

## Infrastructure

- `scripts/build-review-packet.py` mechanically assembles scope and context.
- `scripts/claude-review.sh` invokes Claude Code in read-only plan mode.
- `scripts/claude-review-stream.py` preserves streamed output and diagnostics.
- `.ai/review-runs/<task-id>/` stores the decision, manifest, ledger, review,
  and closure artifacts.
- `.env.claude-review` optionally bridges an API key into ignored local state.

## Run

```bash
scripts/create-review-run.sh T123
python3 scripts/build-review-packet.py --task T123 --base HEAD --stage external-critic
scripts/claude-review.sh --task T123 --stage external-critic --base HEAD
```

The wrapper refuses to run without a review packet, manifest, and finding
ledger. Claude must inspect direct repository context, state scope limitations,
and return stable finding IDs. Codex validates and dispositions every finding.

Use Sonnet by default. Override `CLAUDE_REVIEW_MODEL` only for unusually
critical or architecture-heavy work. Raw events, debug logs, and partial output
remain ignored; interrupted runs are not successful reviews.

Do not paste credentials into chat or commit `.env.claude-review`.
