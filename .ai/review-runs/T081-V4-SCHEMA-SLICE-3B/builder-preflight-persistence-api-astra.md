# Slice 3B persistence/API — Astra builder preflight

Reviewer: `/root/v4_s3b_q7_edges_preflight` (Astra, builder-side preflight only)

Scope: the unstaged Slice-3B persistence service and API, migration `0028`
including its generated/hand-written SQL, Slice-3A compatibility readers,
direct-SQL PostgreSQL tests, and relevant callers. The reviewer was read-only
and made no edits. This report is review input, not an independent
implementation or closure verdict.

## Result

**FAIL — seven HIGH findings and one MEDIUM finding.** The preflight correctly
prevented a premature implementation-review packet. The builder has implemented
responses for all eight findings; every disposition remains
`fixed_pending_verification` until the independent reviewer reproduces the
evidence against a current exact packet.

## Findings and builder dispositions

1. **High — false stale causes.** A root applicability materialization event
   and the root evidence admission event could be cited as invalidating causes.
   The shared Python lifecycle verifier and both applicability/obligation event
   readers now require an exact dense hash chain and only admitted invalidating
   event types; SQL independently recomputes and validates the cited cause.
2. **High — forward child identity was not exact.** Equal-valued action payloads
   could exchange Q1 `action_node_id` references. SQL now resolves every
   forward child pointer to the exact semantic node/type/key/parent/ordinal,
   with an equal-payload swap regression.
3. **High — direct request gate/actor enforcement was incomplete.** A direct
   request could be inserted with validator-2 or Slice-3A disabled, or by an
   inactive actor. The complete validator now requires all three gates and an
   active actor; a BEFORE INSERT request guard validates and locks the actor,
   membership, idempotency key, proposal, gates, evidence, both projections,
   and related correction state in the normative order.
4. **High — recursive SQL graph walk amplified paths exponentially.** The
   validator now uses deduplicating `UNION` reachability over `(origin,current)`
   pairs and enforces the raw edge resource limit before traversal. A 52-node,
   100-edge layered DAG completes within the bounded regression threshold.
5. **High — stale repair was unreachable.** Materialization rejected stale
   parents before finding the existing projection and could not append P4
   events. Existing projections now reconstruct structurally, repair the parent,
   derive verified causes, append each deterministic cause once, and reserve
   freshness failure for normal GET reconstruction.
6. **High — direct request lock inversion.** A request foreign key could lock
   the 3B root before the proposal while POST took the proposal first. The
   BEFORE INSERT guard acquires the normative prefix before FK acquisition; a
   forced two-connection interleaving verifies that the writer waits before the
   root/proposal cycle can form.
7. **High — expected database failures escaped as 500.** The POST boundary now
   rolls back and maps known integrity and retryable transaction SQLSTATEs to
   stable 409 responses while re-raising unknown database failures. Endpoint
   tests cover `P0001` and `40P01`.
8. **Medium — Slice-3A SQL compatibility skipped structural 3B binding checks.**
   The replacement Slice-3A validator now requires the exact Slice-3B root,
   proposal, semantic node, owner generation/type/key, deterministic binding
   identity, and hash. A restamped/misclassified binding fails through the
   shared database boundary.

## Builder evidence produced before independent verification

- Expanded disposable PostgreSQL suite: 19 direct-SQL, concurrency, catalog,
  stale-event, correction-compatibility, anchor-coalescing, and verified-read
  tests passed in 6.13 seconds.
- Complete non-PostgreSQL V4 host set: 382 passed, one PostgreSQL-only test
  skipped.
- Five real packets passed the fresh PostgreSQL deferred round trip exactly in
  54.86 seconds after the commit-time validation performance fix.
- Mapping digest remains
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
- Fresh databases migrated through `0028`; downgrade/re-upgrade and current
  full PostgreSQL evidence are recorded in `checkpoint.md`.

## Required next boundary

Regenerate and verify the exact implementation packet only after the complete
host, fresh-migration, downgrade/re-upgrade, serializer, and PostgreSQL gates
are green. Then assign the existing independent reviewer read-only scope over
the entire persistence/API family. No finding in this report is closed solely
by builder evidence.
