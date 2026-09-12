# Independent external-critic closure review: T081-V4-SCHEMA-SLICE-3A

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Boundary: Claude external-critic dispositions  
Outcome: **PASS**

## Gate result

**13 passed out of 13 finding gates.** Claude findings CC-001 through CC-003
are independently closed, and the ten previously closed Codex design findings
remain closed with no regression. There are zero open blockers, highs,
mediums, or lows. The existing design PASS remains authoritative; this artifact
does not create a second design attestation.

## Claude finding dispositions

### CC-001 — concrete rollout gates

The revision defines two independent application flags and two independent
database gates, all default-off. Migration 0027 cannot enable them. The
deployment role alone can change database gates through an audited procedure;
the application role can only read them. Fixed compiled capability declarations
and the 0027 capability function are checked at startup and again in the write
transaction after the proposal lock.

Validator-2 candidate POST requires its application flag and database gate.
The 3A materialization POST requires both application flags, both database
gates, and both compiled capabilities. Audit GET requires only the 3A/read gate
and cannot materialize a missing projection. The four-state matrix explicitly
uses a preexisting v2 candidate: `v2-off/3A-on` permits audit of an existing
projection but rejects materialization with zero request, projection,
dependency, correction, or event rows. Proposal-before-gate locking plus
`FOR SHARE`/audited `FOR UPDATE` gate access gives deterministic concurrent
disable outcomes. Compatibility-release, mixed-instance, drain, rollback, and
database-capability mismatch cases are mandatory implementation tests; no flag
claims to prove fleet-wide rollout.

### CC-002 — correction-foundation scope

The Objective, invariant 3, detailed design, and Expected file scope now agree.
Slice 3A explicitly owns the shared proposal-scoped correction foundation and
its four named tables. It may read and verify canonical
`authoritativeCorrections` and referenced `officialDocuments` identity/evidence
fields only, reconstructing corrections separately from the four-field
applicability subtree. Complete ordered references into future Slice-3B
namespaces are retained to preserve one identity, while requirements,
recurrence, AMOC, incorporated-document, and service-bulletin semantics remain
deferred.

### CC-003 — inline repair only

The stale-event repair helper runs only opportunistically inside the existing,
authorized materialization POST transaction. It uses the same capability and
membership checks, total lock order, deterministic cause identity, and
idempotent event identity. Audit GET invokes detection-only behavior and is
side-effect-free. The design explicitly forbids a cron process, worker, queue
consumer, scheduler, CLI, startup sweep, repair endpoint, or other operational
writer.

## Prior-finding regression check

- DA-001 through DA-010 remain `closed` with their prior independent evidence.
- Added database gate rows preserve DA-010's proposal-first global lock order:
  writers take the proposal boundary before a gate lock, and downgrade takes
  the proposal table before the feature-gate table and all child/3A tables.
- The new scope wording preserves DA-002's single shared correction identity
  and does not add Slice-3B materialization.
- The repair clarification preserves DA-006's deterministic causal dependency,
  DA-007's exact-membership authorization, and append-only audit behavior.
- Candidate-only isolation, v1/v2 hash semantics, exact unknown handling,
  source-faithful series expressions, and absence of released readers or
  matching indexes are unchanged.

## Verification accounting

- Incoming external-critic packet freshness: **1 passed out of 1** at
  fingerprint
  `a3664385537c5f5492f53616b7d9b229f446af77e79256879ec9b06bc7eab70b`.
- Incoming packet SHA-256: 
  `2c473fbca1572cb0f7d46a47dd2aed251017652c6bc1a9334bb35b4c53a008a1`.
- Explicit bound inputs: **36 inspected out of 36**, including the successful
  Claude markdown and structured findings sidecar.
- Claude finding closures: **3 passed out of 3**.
- Preserved Codex design closures: **10 passed out of 10**.
- Total finding gate: **13 passed out of 13**.
- Packet/source scope: design-only; no implementation runtime result is claimed.

Implementation may advance under the existing design PASS, but the feature
gates, capability checks, four-state matrix, concurrent-disable behavior,
correction-foundation boundary, and inline repair semantics remain mandatory
implementation-review gates.
