# Adversarial implementation review — initial

Task: `T081-V4-SCHEMA-SLICE-3A`  
Reviewer runtime identity: `/root/v4_s3a_impl_adversary`  
Role: independent read-only implementation adversary  
Outcome: **FAIL — implementation gate blocked**

## Findings

### F1 — Blocker: implemented schema is not the approved typed relational design

Violated invariants: 5–7, 9, 11–18, 26–27; DA-001, DA-004, DA-005,
DA-008. Decision lines 663–924 require typed owner/value/scope/condition/
expression/rule/hint tables and deferred ownership/cardinality/cycle/evidence
checks. Migration 0027 lines 93–208 instead create broad semantic-node and
JSON-pointer datum tables. `_flatten` persists arbitrary shapes, while the
90-pair test proves only Python round trip and attribute absence.

Impact: direct SQL can commit malformed semantic shapes and references while
retaining valid-looking projection metadata; the implementation materially
deviates from the reviewed design.

Required closure: implement all approved typed tables and their discriminator,
ownership, cardinality, ordinal, reference, arity, and acyclicity constraints,
or return to design review and prove equivalent database enforcement for the
generic representation. Add PostgreSQL negative tests for every normative
typed constraint.

### F2 — Blocker: a projection root can commit with zero or partial children

Violated invariants: 4–7, 18–20, 27, especially invariant 5. Projection counts
are ordinary integers. `paprnav_v4_validate_app_projection` is a BEFORE INSERT
root trigger that validates copied bytes/envelope only; no deferred child-graph
constraint exists. The PostgreSQL forged-root test changes the root hash and
does not attempt a valid root with missing/extra/reordered/different children.

Impact: a direct writer can commit an incomplete immutable relational graph;
later application reconstruction is not database commit-time refusal.

Required closure: add deferred PostgreSQL validation that reconstructs the
complete typed representation, verifies counts/hashes/evidence/ownership, and
compares it to the exact candidate subtree. Add direct-SQL negative tests for
empty, missing, extra, reordered, differently-valued, and cross-reference
graphs.

### F3 — Blocker: supersession handling reopens DA-006

Violated invariants: 21–23 and DA-006. `projection_state` treats the first
relationship naming a proposal as predecessor as a stale cause without proving
successor canonical AD equality or unique predecessor resolution.
`_repair_stale_projection` writes `causing_dependency_id=None`; materialized
dependency rows remain unresolved with no target projection.

Impact: an untrusted candidate relation can stale a projection without the
approved evidence-bound resolution, and the event lacks exact causal identity.

Required closure: persist dependency resolution using successor-AD equality and
unique predecessor rules. Require stale events to reference the exact
same-projection dependency. Ambiguous/mismatched signals must remain unresolved.
Add positive and negative PostgreSQL/API tests.

### F4 — High: audit GET and list endpoints are write paths

Violated invariants: 21, 24 and CC-003. `projection_state` calls the mutating
repair helper; detail and list GET routes commit the resulting events.

Impact: audit reads become alternate writers and viewing a list can lock and
mutate multiple projections.

Required closure: make every GET/list/reconstruction path detection-only.
Invoke repair solely inside the authorized materialization POST transaction
with its request identity, locks, and both write gates. Prove GETs leave all
table/event counts unchanged.

### F5 — High: correction integrity and reconstruction are incomplete

Violated invariants: 3, 6–7 and DA-002. Correction rows are inserted, but no
exact correction reconstruction/verification exists. Expected child counts,
official-document identity, ordinals, owner slice, and evidence set are not
deferred database invariants. Verified reads ignore the correction foundation.

Impact: a projection can report verified with an absent, incomplete,
overcomplete, or disconnected shared correction foundation.

Required closure: reconstruct corrections exactly from their relational graph,
compare them to canonical proposal corrections, enforce completeness and
identity at commit, fail verified reads closed, and add direct-SQL negative
tests plus an exact 2008 fixture round trip.

## Verification accounting

- Packet digest verified as
  `34b8c671c36cf239a718bb03bbd521b02d2a719a930af319861bf039e8b61dd4`.
- All staged, unstaged, and untracked scope was inspected; nothing was staged.
- Callers/readers, migration, models, routes, schemas, services, fixtures, and
  tests were inspected. No released/customer consumer was found.
- A reviewer host-test attempt did not complete before its tool boundary and is
  not credited. PostgreSQL was not rerun by the reviewer and `paprnav_db` was
  never targeted.
- No files were edited by the reviewer.

Implementation review result: **FAIL; five findings remain open, including
three blockers.**
