# Closure report: T081-V4-SCHEMA-SLICE-4

## Outcome

**Ready for independent closure review.** The implemented Slice-4 vertical is
the frozen rejection-only workflow: immutable review cases and annotation
drafts, frozen review requests, and graph-free rejecting signoffs. The design
and implementation review stages passed with all 17 findings closed. Nothing is
staged or committed.

This outcome does not claim the complete feature set originally explored in the
decision packet. Candidate-only acceptance and every release/publication path
remain intentionally unavailable and require separately reviewed later slices.

## Model assignments

This review run began before `.ai/MODEL_ROUTING.md` was adopted. Completed
reports remain immutable; the assignments below record the metadata available
to the coordinator without retroactively inventing missing runtime fields.

| Phase and role | Runtime identity | Actual runtime metadata | Routing evidence |
| --- | --- | --- | --- |
| Slice-4 design, implementation, and first closure adversary | `/root/v4_s4_design_adversary` | model not exposed by runtime; effort not exposed | The coordinator checkpoint described an Astra assignment for schema, authorization, invariant, adversarial, and closure work, but the reviewer later confirmed that neither actual model nor effort was exposed; no exact actual-model claim is made. |
| Slice-4 builder/coordinator and remediation | `/root` | model not exposed by runtime; effort not exposed | Builder role and runtime identity are recorded throughout the run; no exact model is inferred. |
| Model-policy builder/coordinator | `/root` | model not exposed by runtime; effort not exposed | Localized policy edit; active runtime did not expose model metadata. |
| First model-policy verifier | `/root/model_routing_policy_verifier` | model not exposed by runtime; effort not exposed | Requested `gpt-5.6-terra` medium for mechanical policy verification; the reviewer closed most requirements and identified missing durable closure evidence. |
| Escalated model-policy verifier | `/root/model_routing_policy_closure` | model not exposed by runtime; effort not exposed | Requested `gpt-5.6-terra` high after the first substantive failure; it identified active-run packet integration as the remaining family. |
| Final closure re-attestation reviewer | `/root/model_policy_astra_closure` | model not exposed by runtime; effort not exposed | Requested `gpt-6-astra` xhigh after the second unsuccessful loop; the runtime accepted the assignment but did not expose actual model or effort to the reviewer. |

No fallback is claimed. Requested routing is recorded separately from actual
runtime metadata whenever the delegated runtime did not expose the latter.

## Invariants verified

- Slice-4 writes are additive V4 review history only and cannot publish, select,
  release, or mutate V1/V2/V3 authority.
- Each case, draft, request, rejection, signoff, and lifecycle event has exact
  immutable ownership, state, predecessor, request identity, authorization
  snapshot, canonical bytes, and domain-separated hashes.
- The stable input CAS excludes observation time; the timestamped observation
  envelope preserves the exact verified/missing/stale/integrity/unsupported
  branch and its closed key set.
- Requests freeze one exact immutable draft. Rejection binds the frozen and
  current observation and creates no acceptance decision-node graph.
- Server authorization is repeated under lock; active platform-admin identity,
  membership, organization, policy, action, claims, and result are retained.
- Idempotency, event order, terminal uniqueness, case succession, and lock
  ordering are enforced in both service logic and deferred PostgreSQL checks.
- Detail and queue reads use repeatable-read, reverify hashes and lifecycle
  structure, and return controlled nonverification for source or projection
  integrity failures.
- History, source verification, projection reconstruction, lifecycle, and
  returned pagination work are bounded before large payloads are loaded.
- Phase-aware 16 MiB draft, 28 MiB requested, and 40 MiB terminal limits retain
  enough capacity for request, rejection, and successor creation.
- Application and database rollout gates default off; downgrade is exact only
  while both gates are off and the six review tables are empty.

## Findings disposition summary

The ledger contains 17 findings: 4 blockers, 8 high, and 5 medium. All are
closed with evidence. There are no accepted risks, deferred findings, rejected
findings, or open/fix-pending findings.

Four design review passes and six implementation review passes were recorded.
The final implementation adversary closed M-001 against packet
`b531efdaba8866893e8c0dcdb4d60f19922c87bfab95371892e455551ba9647a`
after independently reproducing both count and byte parent-projection overflow
through case detail and queue reads.

## Verification performed

- Static: `git diff --check`, JSON validation, and Python compilation over all
  changed implementation, migration, and test modules passed.
- Host V4/API/service/reconstruction/calibration gate: **532 passed, 1 skipped**
  in 191.41 seconds.
- Focused review/service/storage gate: **93 passed** in 8.49 seconds; the
  independent reviewer repeated the same 93-test gate successfully.
- Fresh empty database `paprnav_s4_closure7` migrated through 0001-0029 and the
  migration/lock-order/review-service gate passed **86 tests** in 36.66 seconds;
  the independent reviewer repeated the same 86-test gate successfully.
- Independent populated parent-count and parent-byte probes passed for both
  detail and queue with zero projection request/event payload-byte selections.
- Dedicated rollback database `paprnav_s4_rollout4`: **4 passed**, including
  exact inherited-function restoration, helper removal, independent gate
  refusal, and occupied-history refusal.
- Isolated prior-slice PostgreSQL regressions passed: candidate 5,
  applicability 24, obligation 68, and old-reader rollout 1.

## Final scope reviewed

- Migration 0029 SQL/Alembic upgrade and downgrade, six immutable review tables,
  closed checks, deferred validators, history protection, and rollout gates.
- Review ORM models, API schemas/routes, service construction and verification,
  storage error normalization/bounds, and the bounded lock-order changes in
  candidate, applicability, and obligation services.
- Review-case migration, rollback, concurrency, service, API, bounds,
  authorization, corruption, calibration regression, and direct-SQL tests.
- The decision packet, normative matrix, rollout contract, complete working
  tree, staged/unstaged/untracked files, and relevant surrounding consumers.
- The repository-root model-routing directive and detailed persistent policy,
  added after the first closure PASS and bound into the fresh closure
  re-attestation packet before any shared commit.
- Every stable active-run review artifact is an explicit hash-bound input to
  the final re-attestation packet. Generated packet/manifest files and
  append-only final attestation bookkeeping follow the narrowly documented
  self-reference exception and repository validator path in
  `model-routing-policy-integration.md`.

## Accepted risks and deferred work

There are no accepted-risk ledger entries in this vertical.

The following work is intentionally deferred outside this rejection-only
closure and requires new decision packets and adversarial review:

- candidate-only acceptance, decision-node gates/dependencies, and actionable
  classification;
- executable evaluator and supporting-document admission contracts;
- reviewer UI and complete form/control projection;
- release/publication/current selection, V3 freeze, search, matching, coverage,
  compliance, terminating-credit, and due-state consumers.

`signature_hash` is an internal integrity digest, not PKI, a user-held-key
signature, or legal non-repudiation proof.

## Not verified

- No production rollout, gate enablement, or live-data migration was performed.
- No acceptance, publication, current-selection, or release-authority behavior
  exists in this implementation and none is approved by this closure.
- Frontend reviewer UI behavior is absent and was not tested.
- The five calibration packets were reverified through the unchanged candidate,
  Slice-3A, and Slice-3B reconstruction layers, not through deferred acceptance
  UI/signoff paths.
