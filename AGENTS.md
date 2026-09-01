# Paprnav agent workflow

Use the adversarial review process for changes involving regulatory or safety
semantics, schemas or migrations, authorization, audit evidence, destructive
data operations, provider/billing decisions, infrastructure/IAM, or public API
contracts. Read `.ai/REVIEW_PROCESS.md` and use the repository-local
`adversarial-review` skill.

For qualifying work:

1. Create a review run and write the decision packet before implementation.
2. Use a separate Codex subagent for design review. The builder may not review
   its own work.
3. Resolve design blockers before migrations, contracts, or implementation.
4. Implement one coherent vertical slice at a time.
5. Use a separate Codex subagent to adversarially review every high-risk slice.
6. Use Claude only as an external critic at selected decision boundaries, after
   the Codex adversarial loop has produced a complete review packet.
7. Record every finding and disposition. Do not declare completion while a
   blocker remains open or closure evidence is absent.

The coordinating Codex runtime must create the reviewer assignment and record
the returned reviewer identity; repository scripts cannot authenticate runtime
identity and are not a security boundary. The adversarial reviewer is read-only
unless the coordinator explicitly assigns a later fix task. Reviewers must
inspect staged, unstaged, and untracked files,
plus callers, readers, migrations, administrative scripts, tests, and relevant
contracts. A scope omission is a review finding, not an implicit exclusion.

Claude output is review input rather than authority. The coordinating Codex
agent validates and dispositions each finding as fixed, rejected with evidence,
accepted risk with an owner, or deferred with rationale.
