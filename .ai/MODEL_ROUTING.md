# Paprnav model-routing policy

This policy is mandatory for every Codex task in this repository. Route each
meaningful phase independently; do not choose one model for an entire task when
later phases have different risk or review needs.

## Routing tiers

Choose the highest tier triggered by the work. Complexity, safety impact, and
review history override convenience or expected speed.

| Work | Preferred routing |
| --- | --- |
| Mechanical, localized, low-risk edits with an obvious oracle and limited blast radius | GPT-5.6 Luna (`gpt-5.6-luna`) or GPT-5.6 Terra (`gpt-5.6-terra`), medium |
| Coherent multi-file implementation whose design is already approved | GPT-5.6 Sol (`gpt-5.6-sol`), high |
| Schema or migration design; authorization; regulatory or safety semantics; invariant synthesis; adversarial review; closure review | GPT-6 Astra (`gpt-6-astra`), high or xhigh |

Use xhigh for interacting invariants, ambiguous trust boundaries, concurrency or
rollback reasoning, closure after substantive findings, or when high effort has
not resolved the review class. Use high for a well-framed problem with explicit
invariants and a strong test oracle.

Low-risk routing applies only when all of these are true:

- the change is localized and mechanically checkable;
- failure cannot alter authorization, regulatory meaning, safety behavior,
  persisted schema, audit evidence, billing/provider choice, or a public
  contract;
- rollback is straightforward; and
- no review-history escalation below applies.

When a phase mixes tiers, use the highest triggered tier or split it into
bounded phases with explicit handoffs. An approved design is required before
routing coherent high-risk implementation to Sol; design and invariant work
remain Astra work.

## Risk-adjusted planning and review cadence

For multi-phase work, score each remaining package independently from 1 (low)
to 5 (high) on risk, technical complexity, dependency centrality, and
uncertainty. Record dependencies, downstream consumers, reversibility, the
strength of deterministic oracles, design-approval state, and relevant review
history. File count and apparent edit size are not risk scores: a one-line ACL
or migration change can be high-risk, while a large generated rewrite can be
mechanical.

Optimize expected total effort, including likely rework and review cost. Route
to Astra earlier when ambiguity, centrality, or repeated findings make a Sol
pass likely to require another implementation/review loop. Conversely, use
Terra medium or Sol medium for deterministic work mechanically derived from an
approved authority, even when it touches many generated files.

Review once at each meaningful invariant-bearing family boundary:

- review a coherent design together with its generated contracts, manifests,
  hashes, counts, and deterministic validator results;
- do not create standalone reviewer turns for each generated artifact or for
  mechanical implementation that stays within the approved design;
- request one implementation review after the coherent family and its full
  positive/negative evidence are complete;
- repeat a review or broad test only when changed dependencies can invalidate
  prior evidence; and
- retain independent design, implementation, and closure review for high-risk
  schema, migration, authorization, regulatory, IAM, or invariant work.

If an agent has completed the technical analysis but continues expanding prose,
direct it to publish a compact reviewable artifact and return. Drafting length
is not additional verification.

## Review-history escalation

Count substantive failures within the current finding family or review loop.
Formatting-only feedback and infrastructure/transient failures do not count.

1. After the first substantive failed review, increase reasoning effort for the
   next pass and reassess whether the issue is a local defect, a missing
   invariant, a design error, an oracle gap, or a scope omission.
2. After the second failed review, or whenever the same finding family recurs,
   route the next pass to GPT-6 Astra and stop counterexample-by-counterexample
   patching. Restate the complete invariant and close the coherent family with
   its positive and negative matrix.
3. After the third unsuccessful loop, pause implementation. Identify and record
   the missing invariant, architecture decision, or shared test oracle before
   further code changes. Resume only after that gap is resolved and, for work
   governed by the adversarial-review process, independently reviewed.

Examples:

- A first concurrency-review failure moves the next pass to higher effort and
  reclassifies the issue as lock ordering, transaction isolation, or test
  coverage before editing.
- A second malformed-row counterexample in the same schema family moves the
  work to Astra and replaces one-off trigger patches with a complete union and
  corruption matrix.
- A third reconstruction mismatch stops implementation until the canonical
  mapping invariant and shared oracle are explicit.

Escalation never authorizes broader product scope or bypasses an approval gate.

## Builder and reviewer separation

Builder/reviewer separation is mandatory regardless of model. A model upgrade
does not make self-review independent. Qualifying work must still follow
`AGENTS.md`, `.ai/REVIEW_PROCESS.md`, and the repository-local
`adversarial-review` skill.

- Assign design, implementation, and closure adversaries as separate read-only
  project subagents unless the coordinator explicitly assigns a later fix task.
- Do not let the builder attest its own review stage, even when builder and
  reviewer would use the same model family.
- Record the actual runtime reviewer identity; a model name is not an identity.

## Dynamic availability and fallbacks

Use the preferred model when it is available. Otherwise choose the closest
available capability tier that can safely perform the phase:

1. For Astra-routed work, prefer the strongest available model at high or xhigh
   and preserve the mandatory independent-review gates. If no available model
   is adequate for the risk, pause and report the limitation.
2. For Sol-routed work, fall back to Astra at high, or to the strongest
   available implementation model at high when Astra is unavailable.
3. For Luna/Terra-routed work, use the other model at medium, then the closest
   available general implementation tier at medium.

Never silently claim or imply use of an unavailable model. In the phase notice
and any review artifact, record the actual fallback model and the reason. If the
runtime does not expose its model, write exactly `model not exposed by runtime`
rather than inferring it. If effort is not exposed, say `effort not exposed`.

## Required status commentary

At the start of every meaningful phase, report the role, exact model, reasoning
effort, and routing trigger. Report again whenever the role, model, or effort
changes. A meaningful phase includes framing/design, implementation, focused
verification, adversarial review, remediation after a failed review, and final
closure. Do not repeat the notice during routine progress updates when none of
those fields changed.

Use exactly this shape:

```text
Model routing: <role> → <exact model> (<effort>). Trigger: <brief reason>.
```

For a fallback, include it in the trigger, for example:

```text
Model routing: implementation builder → gpt-5.6-terra (high). Trigger: approved multi-file implementation; gpt-5.6-sol unavailable, closest implementation fallback.
```

Identify delegated builder and reviewer models in coordinator commentary. When
a delegated runtime does not expose its model, use the required unavailable
metadata wording rather than the requested model name.

## Review artifacts and closure

When known, every adversarial-review artifact must record:

- builder runtime identity, actual model, and effort;
- reviewer runtime identity, actual model, and effort;
- the routing trigger; and
- any fallback, unavailability, or unexposed runtime metadata.

Use a `## Model routing` section in each new design, implementation, remediation,
and closure-review artifact. Use a `## Model assignments` section in
`closure.md` to summarize the full run. These sections are the authoritative,
human-readable evidence locations; do not rely on task-local commentary or
model-selection requests as proof of the runtime used.

The independent closure reviewer must verify these sections against the phase
notices, returned runtime identities, and known delegation metadata. Missing,
inconsistent, inferred, or silently substituted model/effort evidence is a
closure blocker even if `validate-review-run.py` otherwise passes. Record
`model not exposed by runtime` or `effort not exposed` when applicable; that is
valid evidence of unavailable metadata, not permission to guess.

Do not rewrite historical attestations merely because model metadata was not
previously required. New review reports and closure evidence must be accurate
about what the runtime exposed. Final closure must summarize model assignments
for design, implementation, remediation, implementation review, and closure
review, including fallbacks.

For a review run already in progress when this policy is adopted, completed
reports are historical for this purpose even if they are still uncommitted. Do
not rewrite those immutable reports. Instead, bind this policy and the current
working tree into a fresh closure packet, summarize every known, unexposed, and
requested assignment in `closure.md`, and obtain a compliant independent
closure re-attestation before the files share a commit.

## Delegation mechanics

Use project subagents for bounded model-specific work when repository policy
and the active task permit delegation. Give each subagent one coherent role,
explicit scope, requested model and effort, and required evidence. Use the
repository's subagent mechanism so work remains attached to the current task;
do not create user-visible tasks merely to switch models.

The coordinator remains responsible for integrating results, checking actual
runtime metadata, preserving the working tree, and enforcing review gates.
