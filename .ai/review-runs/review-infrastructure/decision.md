# Decision packet: review-infrastructure

## Objective

Create durable Paprnav infrastructure for a Codex builder, an independent Codex
adversarial reviewer, and a Claude external critic.

## User-visible outcome

High-risk work enters review at design time, iterates by implementation slice,
and closes through an evidence-backed finding ledger.

## Safety and correctness invariants

- The builder cannot certify its own work.
- A design blocker prevents implementation from passing its gate.
- Claude output is independently validated rather than automatically accepted.
- Packets identify staged, unstaged, untracked, and explicitly excluded scope.
- Closure rejects unresolved blockers and unsupported dispositions.

## Current behavior

Claude receives a generic working-tree prompt late in implementation. Paprnav
has historical review documents but no repository agent policy or finding
ledger.

## Proposed design

Use root `AGENTS.md` for orchestration policy, a repository-local skill for the
reusable workflow, `.ai/agents` for role briefs, `.ai/review-runs` for durable
state, deterministic scripts for packet/ledger checks, and Claude Code CLI only
for external criticism.

## Alternatives considered

A bespoke multi-agent API service was rejected because Codex already provides
runtime subagents. Claude as primary reviewer was rejected because it lacks the
task's iterative decision context.

## Trust, authorization, and audit boundaries

The coordinator dispositions findings. Builder and reviewers supply evidence.
Claude runs read-only in plan mode. Local credentials and raw diagnostics stay
ignored.

## Read paths and consumers

Codex reads `AGENTS.md`, the local skill, role briefs, packets, and ledgers.
Humans read Markdown reports. Claude reads a mechanically generated packet and
direct repository files.

## Write paths and administrative paths

Run creation writes task templates. Packet assembly writes manifest and packet.
Validation reads run artifacts. Claude streaming writes review and diagnostics.

## Migration, compatibility, correction, and rollback

There is no database migration. Existing `.ai/reviews` remain historical. The
Claude command interface intentionally changes to require a task packet; repo
search found no automated caller. Rollback must revert the modified Claude
wrapper, environment example, and documentation together with the new
infrastructure to their pre-change Git versions.

## Test strategy

Run shell syntax checks, Python compilation, skill validation, review-run
creation, scoped packet generation, negative closure validation, and an
independent Codex adversarial review.

## Expected file scope

`AGENTS.md`, `.agents/skills/adversarial-review`, `.ai/agents`,
`.ai/review-templates`, `.ai/REVIEW_PROCESS.md`, `.ai/CLAUDE_REVIEWER.md`,
`.gitignore`, and the review scripts.

## Known uncertainty

Repository-local skill discovery may require a new Codex task before it appears
in the available-skill catalog. The system skill validator currently lacks its
PyYAML runtime dependency in this environment. Repository attestations cannot
authenticate Codex runtime identity; the coordinator must record the identity
returned by the actual subagent tool.
