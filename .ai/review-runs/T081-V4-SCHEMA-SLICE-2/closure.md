# Closure report: T081-V4-SCHEMA-SLICE-2

## Outcome

**READY FOR INDEPENDENT CLOSURE REVIEW — NOT CLOSED.**

The run remains in `implementation_reviewed`. The independent implementation
review recorded **PASS — 9 passed out of 9 implementation finding gates**.
This report assembles the reviewed implementation evidence for a separate
closure decision; it does not record closure or change review state.

Slice 2 produces immutable, evidence-bound `candidate_only` V4 proposals. It
does **not** publish an AD, make a human compliance decision, or authorize any
candidate for catalog, applicability, compliance, or due-state use.

## Invariants verified

1. V4 input crosses a raw-byte boundary before framework JSON decoding. The
   parser rejects duplicate keys, invalid/non-NFC strings, nulls, floats,
   non-finite numbers, excess bytes, depth, nodes, strings, arrays, evidence,
   AST nodes, and graph edges with stable errors; hostile deep JSON returns
   `resource_limit` / HTTP 413 rather than leaking recursion failure.
2. The checked-in V4 schema is closed at every object and array-item level.
   Semantic validation resolves typed namespaces and rejects dangling,
   mistyped, duplicate, or cyclic applicability, requirement, recurrence,
   correction, supersession, and candidate-relationship references.
3. Canonicalization is driven by schema set/sequence annotations. It rejects
   duplicate keyed and composite identities before sorting, preserves declared
   requirement sequence, uses fixed canonical/hash profiles, and produces a
   deterministic content identity independent of permissible set ordering.
4. Candidate evidence binds to exact immutable Slice-1 admitted fragment
   identities. The service deduplicates and locks the complete fragment set in
   lexical ID order before lifecycle validation. A candidate-store versus
   lifecycle-transition race cannot commit a proposal against stale evidence.
5. Content identity is separate from directive-local submission, origin,
   correction, and relationship provenance. Same-content idempotency is
   deterministic; different payloads cannot reuse an idempotency key; distinct
   origins remain distinct; immutable relationships reject self-links and
   cycles.
6. PostgreSQL independently binds canonical proposal, evidence-binding,
   submission, relationship, authorization-snapshot, and event envelopes to
   their relational rows and parents. Deferred checks require complete child
   sets, and all five V4 evidence/audit tables reject UPDATE and DELETE.
7. Only an active platform administrator with a captured membership and
   authorization-policy snapshot can create or inspect global candidates.
   Maintenance-shop identities cannot mutate global evidence. Audit list and
   detail APIs expose immutable submissions and relationships through bounded,
   independently paginated, integrity-checked results.
8. Every stored proposal remains `candidate_only`. No V3 review, publication,
   matching, materialization, catalog, compliance, coverage, or due-state read
   path consumes Slice-2 rows; V3 behavior remains isolated.
9. The portable five-AD calibration set is source-accounted to retained
   official bytes and exact clause selections. No calibration-specific AD truth
   was added to the production validator or store.

## Findings disposition summary

- Independent implementation review: **9 closed out of 9 findings**
  (`T081-V4-S2-IA-001` through `T081-V4-S2-IA-009`).
- Blocker findings closed: **5 out of 5**.
- High-severity findings closed: **4 out of 4**.
- No implementation blocker, accepted-risk disposition, or deferred finding
  remains in the current ledger. Deferred product capabilities are explicit
  later-slice scope, not exceptions to the Slice-2 invariants.

## Verification performed

- Independent focused host suite: **45 passed out of 45** in 6.42 seconds.
- Independent closure-1 counterexample replay: **4 passed out of 4** (deep
  JSON, supersession cycle, duplicate composite identity, and candidate
  relationship cycle).
- Independent representative retained-PDF → Slice-1 admission → V4 persistence
  path: **1 passed out of 1** in 9.96 seconds.
- Calibration retained-source integrity: **6 passed out of 6 PDFs**.
- Calibration claim integrity: **5 passed out of 5 AD packets**, comprising 67
  clause-narrow evidence fragments.
- Calibration real admission and candidate persistence: **5 passed out of 5**.
- Calibration schema-valid composed negatives: **5 passed out of 5**, each
  rejected with `calibration_semantic_mismatch`.
- Calibration structural validator negatives: **5 passed out of 5**.
- Deterministic calibration rebuild: checked-in fragment manifest identity
  reproduced exactly.
- Fresh isolated PostgreSQL matrix on `paprnav_v4_slice2_closure3`: **5 passed
  out of 5** in 3.72 seconds, with one deprecation warning. It covered fresh
  upgrade, empty round trip, occupied downgrade refusal/preservation and lock
  race, idempotent and conflicting concurrent submissions, sorted overlapping
  fragment locks, correction origins and cycles, direct-SQL envelope/child/
  authorization forgery, all-table immutability, concurrent lifecycle
  successors, and candidate binding versus lifecycle transition.
- PostgreSQL cleanup: the exact disposable database and container were removed;
  a read-only wildcard check confirmed no Slice-2 closure/final-proof databases
  remained. The default `paprnav_db` was not used.
- Independent implementation gate: **9 passed out of 9**.

## Final scope reviewed

The reviewed vertical slice consists of:

- strict V4 JSON Schema, raw-byte parser, semantic/reference validator,
  schema-driven canonicalization, and versioned hash envelopes;
- additive immutable candidate proposal, evidence binding, submission,
  relationship, authorization snapshot, and lifecycle event persistence;
- platform-admin candidate POST and bounded audit GET/list APIs;
- Slice-1 admitted-fragment validation, deterministic lock ordering, and
  candidate/lifecycle concurrency controls;
- additive migration `20260901_0026_add_ad_v4_candidates.py`, including
  database-level transitive integrity, immutability, and downgrade guards;
- focused service/API/PostgreSQL/V3-isolation tests; and
- five source-accounted calibration proposals, retained-source and fragment
  manifests, deterministic rebuild tooling, and positive/negative integration
  gates.

The closure packet also binds the governing domain contract, Slice-2 decision
and finding history, implementation evidence and final implementation PASS,
and the closed Slice-1 predecessor design, implementation, calibration, review,
state, and packet-integrity inputs.

## Accepted risks and deferred work

No risk was accepted to weaken a Slice-2 safety invariant. The following are
deliberately deferred to separately designed and adversarially reviewed later
slices:

- normalized relational materialization of V4 product scopes, predicates,
  requirements, branches, timing, STCs, service bulletins, and AMOCs;
- reviewer GUI/forms, human recurring-date review, signoff, approval,
  rejection, publication, and current-decision selection;
- released catalog, aircraft applicability/matching, coverage, compliance,
  terminating-action, and due-state consumers;
- V3 mutation, translation, backfill, fallback, replacement, or mixed reads;
- supporting-document upload/admission, cross-page evidence fragments, OCR,
  and aircraft-specific AMOC-use evidence; and
- provider-job and CLI candidate writers.

Application rollback disables the V4 candidate route/service while preserving
all immutable candidate and audit rows. Migration downgrade from 0026 to 0025
acquires `ACCESS EXCLUSIVE` locks and succeeds only when all five Slice-2 tables
are empty. If occupied, downgrade refuses before DDL and preserves the rows;
physical rollback then requires retaining 0026 or restoring a verified
pre-0026 backup. No downgrade deletes, translates, or republishes data.

## Not verified

- No publication, release, human approval, or regulatory compliance decision
  is claimed or enabled by this closure report.
- No customer-facing search, aircraft applicability, coverage, compliance, or
  due-date behavior is verified because those readers are outside Slice 2.
- No normalized V4 semantic materialization or reviewer GUI exists in this
  slice.
- Real supporting service-bulletin, STC, or aircraft-specific AMOC admission is
  not verified; supporting-document references remain fail-closed/unknown-only
  at this boundary.
- Production deployment, production data migration, load testing, and broad
  end-to-end UI behavior were not performed.
- Independent closure review and a closure state transition have not yet
  occurred. The current phase must remain `implementation_reviewed` until a
  separate reviewer records the closure outcome.
