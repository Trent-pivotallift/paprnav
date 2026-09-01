# Adversarial engineering review

## Roles

- **Coordinator:** owns scope, gates, finding dispositions, and final closure.
- **Builder:** prepares the decision packet, implements a bounded slice, and
  supplies verification evidence.
- **Codex adversary:** independently attempts to disprove the design and the
  implementation. It does not edit during a review pass.
- **Claude critic:** supplies independent-model criticism from a mechanically
  assembled packet. It does not decide whether a finding is valid or closed.

Role briefs live in `.ai/agents/`. Runtime agents are ephemeral Codex subagents;
the briefs, ledger, and review packets are the durable infrastructure.

Reviewer independence is enforced by the coordinating Codex runtime assigning a
separate subagent. `reviews.json` is an auditable record of that assignment, not
cryptographic proof: anyone able to rewrite the repository can also rewrite its
validator. The coordinator records the actual returned runtime identity.

## Mandatory gates

### 1. Frame

Create `.ai/review-runs/<task-id>/decision.md`. State the problem, invariants,
alternatives, design, affected reads and writes, migration/rollback behavior,
test strategy, and uncertainty.

### 2. Design adversary

Before implementation, give a separate Codex agent the decision packet and
repository access. Record design findings in `findings.json`. Resolve blockers
before changing a migration, public contract, or safety-critical behavior.

Record the result using a new immutable artifact path, then advance:

```bash
python3 scripts/build-review-packet.py --task T123 --base HEAD --stage design
python3 scripts/record-review.py --task T123 --stage design \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-design-final.md
python3 scripts/advance-review-run.py --task T123 --to implementation
```

### 3. Implement by vertical slice

Advance the run from `design_reviewed` to `implementation` before editing.
Keep schema/validation, persistence, publication, derived state, calibration,
and UI slices independently reviewable where practical. The builder records
changed scope, deviations from design, and verification results.

### 4. Implementation adversary

The adversary traces each invariant through source, validation, persistence,
all consumers, correction/supersession, authorization, and tests. It inspects
the actual working tree rather than relying on a selected diff.

Record a passed implementation review before closure:

```bash
python3 scripts/record-review.py --task T123 --stage implementation \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-implementation-final.md
```

### 5. External critic

Generate a review packet with `scripts/build-review-packet.py`. Invoke Claude
only when independent-model disagreement is valuable. Triage its findings in
Codex; never accept or reject them automatically.

### 6. Closure

Re-review fixes, attach verification evidence, and produce `closure.md`.
Completion requires no open blocker, no unexplained scope omission, and a final
review of the resulting working tree.

The final independent reviewer records the mandatory closure stage:

```bash
python3 scripts/record-review.py --task T123 --stage closure \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-closure-final.md
python3 scripts/validate-review-run.py --task T123
```

For the one-time infrastructure bootstrap only, reconstruct the unavailable
early transition after a recorded design pass:

```bash
python3 scripts/advance-review-run.py --task review-infrastructure \
  --to design_reviewed --bootstrap-reason "review tooling bootstrap"
python3 scripts/advance-review-run.py --task review-infrastructure --to implementation
```

## Finding states

`open`, `fix_in_progress`, `fixed_pending_verification`, `closed`,
`accepted_risk`, `rejected_finding`, and `deferred`.

Accepted risk requires an owner and rationale. Closed and rejected findings
require evidence. Deferred blockers do not permit closure.

## Review-run layout

```text
.ai/review-runs/<task-id>/
├── decision.md
├── manifest.json
├── findings.json
├── adversarial-design.md
├── adversarial-implementation.md
├── claude-packet.md
├── claude-critic.md
└── closure.md
```

Raw Claude event streams and debug logs are local diagnostics and should remain
ignored. Human-readable reviews, ledgers, and closure evidence may be committed.

## Compatibility and rollback

The packet requirement is an intentional breaking cutover for
`scripts/claude-review.sh`. Repository search found no automated caller; the
tracked consumer was `.ai/CLAUDE_REVIEWER.md`, updated with the wrapper. Rollback
requires reverting `scripts/claude-review.sh`,
`scripts/claude-review.env.example`, `.ai/CLAUDE_REVIEWER.md`, and the new review
infrastructure together to their pre-change Git versions. Deleting only new
files is not a complete rollback.
