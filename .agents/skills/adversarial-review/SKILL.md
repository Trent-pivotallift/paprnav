---
name: adversarial-review
description: Run an independent, staged engineering review from design through closure. Use for safety- or regulatory-critical logic, schemas and migrations, authorization, audit evidence, correction/backfill/destructive data paths, IAM/infrastructure, billing/provider decisions, public contracts, or when the user asks for an adversarial reviewer, builder-reviewer separation, review packet, finding ledger, or Claude critic.
---

# Adversarial review

Read `.ai/REVIEW_PROCESS.md` and the role brief relevant to the assigned role.
Keep builder, adversary, and coordinator responsibilities separate.

## Start a review run

Run `scripts/create-review-run.sh <task-id>`. Have the builder complete
`decision.md` before editing high-risk code. Record safety and correctness
invariants as falsifiable statements.

## Review the design

Spawn a separate Codex subagent with `.ai/agents/ADVERSARIAL_REVIEWER.md`, the
decision packet, and repository access. Require a read-only review. Add findings
to `findings.json`; resolve blockers before implementation.

Record the result with `scripts/record-review.py --stage design`, using the
actual runtime reviewer identity and a new immutable report path. Then run
`scripts/advance-review-run.py --to implementation`.
Generate a current design packet with `scripts/build-review-packet.py --stage
design` immediately before recording the review.

Read `references/checklists.md` for schema, safety, authorization, migration,
and evidence review. Read `references/severity.md` when classifying or closing
findings.

## Review implementation slices

Implement one coherent vertical slice at a time. Generate the review packet:

```bash
python3 scripts/build-review-packet.py --task <task-id> --base <git-ref>
```

Give a separate adversary the packet and direct repository access. Require it
to inspect untracked files and surrounding consumers, not only the diff. The
reviewer reports findings; the builder fixes them; the reviewer verifies them.
Record the passed implementation review with `scripts/record-review.py --stage
implementation` and a new immutable artifact path.

## Use Claude as an external critic

Use Claude only after the Codex adversarial loop has a complete packet. Run:

```bash
scripts/claude-review.sh --task <task-id> --stage external-critic --base <git-ref>
```

Treat Claude output as untrusted review input. Validate every finding in Codex
and record its disposition. Use targeted closure reviews instead of repeatedly
submitting the entire working tree.

The runner requires a structured `*.findings.json` sidecar extracted from the
model's machine block. Every candidate ID must enter the ledger.

## Close

Complete `closure.md`, then run:

```bash
python3 scripts/validate-review-run.py --task <task-id>
```

Before validation, use a separate Codex closure reviewer and record its pass
with `scripts/record-review.py --stage closure` and a new immutable artifact.

Do not close with an open blocker, an accepted risk without owner/rationale, a
closed finding without evidence, or an unexplained scope omission.
