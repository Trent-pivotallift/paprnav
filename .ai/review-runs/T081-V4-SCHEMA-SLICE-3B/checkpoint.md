# T081-V4-SCHEMA-SLICE-3B checkpoint

Saved: 2026-09-13 (America/Chicago)

## Repository position

- Branch: `codex/ad-source-catalog-proof`
- Committed base/HEAD: `9ad410b7c4021244ac36a6fab44b1dd021f5d05c`
  (`feat: add candidate-only V4 applicability projection`)
- Review-run phase: `implementation`
- Staged paths: none
- Slice-3B work is intentionally unstaged and uncommitted.
- Independent read-only reviewer: `/root/v4_s3b_design_adversary`

## Completed bounded implementation families

1. Declarative mapping foundation and internal-record canonicalization design.
2. D1-D4 incorporated documents and value assertions.
3. Q1-Q5 requirements, actions, ordered steps, document references, and
   branches.
4. EACT/EBR/EREC/EEDGE expression owners and ordered expression edges.
5. Shared iterative requirement-graph cycle primitive used by validator-2 and
   obligation verification, including expression, prerequisite, and
   termination dependencies.
6. T1/T5I/R1/R6/T5R requirement initial timing, timing terms, and inline
   recurrence.
7. Q7/Q9/Q10 terminating effects, termination edges, and prerequisite
   dependencies, including validator/materializer source-occurrence agreement.
8. G1/G2/G3/G4/T5GI/T5GR recurrence groups, members, grouped timing, and
   bidirectional Q11 membership agreement.
9. A1/A2 general-AMOC authority provisions/value assertions and generation-1
   Slice-3B correction semantic bindings, including the shared generated
   correction namespace/domain compatibility contract consumed by both slices.

The expression family passed bounded independent review:

- report: `adversarial-implementation-expressions-closure-3.md`
- report SHA-256:
  `7f961963a8b98663c047d482ecd43c0f2f191697b9cb6b19ec6010484fb9a5ab`
- reviewed packet SHA-256:
  `2773f8f5a961f8b89a846bc3cc7fadd0d9a63fef7884a4ef53c8d93bb10fe800`

The timing/requirement-recurrence family passed bounded independent review:

- report: `adversarial-implementation-timing-recurrence-closure-2.md`
- report SHA-256:
  `1e8163001e4343a9690cbc0a7b5d75e04c5c20f18326f5d32604c4c731eed992`
- reviewed packet SHA-256:
  `bef4c52d35de0ac16ece8d363f66df34a6cbe394c1dbe5d428c89f99bfc633e3`

The terminating-effect/requirement-relationship family passed bounded
independent review after one HIGH malformed-source finding was closed:

- report: `adversarial-implementation-requirement-relationships-closure-1.md`
- report SHA-256:
  `16145edd2062ca9b1e184fcd24be9ffadcb6e26abf452ec0a88d7c852e12db3b`
- reviewed packet SHA-256:
  `0cee3d5849df4da66b0b99d3f58593f4065ce7e038920bfeb162590848b4bbee`

The recurrence-group family passed bounded independent review:

- report: `adversarial-implementation-recurrence-groups-initial.md`
- report SHA-256:
  `b6ee42bf3f215faeec228c232905dab0af5a091c78262cf04a534225048421a3`
- reviewed packet SHA-256:
  `14702da2c8aa4bea21bffa3405bc8fd511940f4ceea2af2ab169ae3fa372401f`

The authority/correction-binding family passed bounded independent review after
two HIGH malformed-boundary findings and one MEDIUM generated-compatibility
finding were closed:

- reports: `adversarial-implementation-authority-corrections-initial.md`,
  `adversarial-implementation-authority-corrections-closure-1.md`, and
  `adversarial-implementation-authority-corrections-closure-2.md`
- final reviewed packet SHA-256:
  `64014758cb745c2fbb4d8206ccfb5a600b19e6d420b6793e0fbe76037d4ebf70`

These are bounded passes, not the formal final implementation review. The
expression PASS artifact was deliberately not retained as a formal overall
implementation PASS record; the run remains in `implementation` until every
family and persistence gate is complete.

## Latest verified host gates

- Authority/correction-focused tests: 79 passed.
- Generated correction compatibility tests: 19 passed.
- Candidate + Slice-3B obligation host regression: 320 passed, one existing
  Starlette deprecation warning.
- Existing Slice-3A applicability regression: 15 passed.
- Dedicated PostgreSQL-16 internal-record serializer matrix: 31 passed, one
  existing Starlette deprecation warning. Generated SQL was installed inside a
  transaction and rolled back.
- Generated mapping check passed at digest
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
- Python compilation passed for the touched candidate/graph/obligation services
  and tests. The current environment does not contain Ruff; the earlier bounded
  families' Ruff gates remain recorded, and `git diff --check` passes.
- Complete Slice-3B obligation host suite: 290 passed after adding the aggregate
  projection graph and ORM mapping tests.
- Three fresh disposable PostgreSQL databases migrated successfully from 0001
  through the current 0028 foundation. The supported administrator now enables
  the 3B gate, capabilities report revision 0028, and downgrade refuses while
  that gate is enabled.

## Important implemented hardening

- Mixed expression/prerequisite/termination cycles fail through one combined
  requirement graph.
- Candidate validation and obligation verification share the iterative
  `ad_v4_graph.first_cycle_node` implementation; valid 1,100-hop chains no
  longer depend on Python recursion depth.
- Graph resource counting uses source occurrences and rejects 40,001 while
  accepting 40,000, even when an added occurrence duplicates a graph target.
- Candidate validation now uses the same source-occurrence rule rather than
  deduplicated adjacency totals.
- Q7 source guards reject malformed discriminators and non-JSON Mapping objects
  through controlled `ObligationIntegrityError` at materialize and verified-read
  boundaries.
- Timing verified reads reject equal-valued `int`, `float`, `bool`, altered-
  scale `Decimal`, nonfinite, negative, ordinal, and count substitutions.
- Timing decimal text is preserved exactly; `0`, the 16,384-character bound,
  all timing unions, and all 750 metric/unit/comparator/anchor combinations are
  covered.
- Not-applicable timing reason length is enforced at 512/513 characters.
- Authority and correction public boundaries validate family, container, row,
  and evidence-target types before field access; malformed inputs produce only
  controlled integrity errors.
- The generated manifest owns all correction namespace classifications, target
  types, and legacy-versus-obligation identity-domain roles. Both Slice-3A and
  Slice-3B consumers reject drift in every entry.

## Serializer closure and unimplemented scope

`T081-V4-S3B-DOC-001` and its blocker/high/medium/low bounded findings are
closed. The independent reviewer passed exact packet
`dea8a0057c13a0283d26b58bb6bacce9d26ab8d9c40384f5c44fc525ff423d9a`
after reproducing the NUL, exact-type, cycle/depth, integer, and cleanup
boundaries. The closure report is
`adversarial-implementation-internal-record-serializer-closure-1.md` with
SHA-256
`9b39294efc9c136d7576048c9aa49219d615f54894eb07f74e953b21aa4b7268`.
Astra's builder-side confirmation is recorded separately and is not treated as
independent authority.

The serializer sub-slice has no open finding; the persistence-family preflight
below has newly open and pending findings.

## Persistence-family position

Migration `20260911_0028` and all 24 ORM table declarations now exist. The
current foundation includes:

- the projection root and all 22 structural count columns;
- semantic nodes, generic datums, evidence links, all 13 typed-owner tables,
  all five relationship tables, requests, and projection events;
- composite proposal/projection/node/app-target/evidence-binding constraints in
  the migration and ORM metadata;
- the generated mapping/serializer SQL installed by the migration;
- the 3B feature gate, capability response, supported gate administrator,
  bounded deterministic downgrade locking, and enabled/occupied refusal;
- correction-binding owner columns plus restored Slice-3A INSERT/UPDATE/DELETE
  dirty/completeness coverage; and
- one pure deterministic aggregate builder that closes every implemented family
  into generic datums, exactly one typed owner per semantic node, all 22 counts,
  subtree/projection bytes and hashes, followed by a single ORM persistence
  mapping.

Astra's foundation and persistence/API preflights are preserved as historical
FAIL inputs. The formal whole-family reviewer subsequently verified and closed
their repaired invariants except for the downgrade/API residuals it found in
the first implementation packet. Those residuals and both missing-proof
findings now have builder fixes pending independent closure verification.

Slice 3B is not complete until the current closure packet passes, the selected
external critic is dispositioned, mandatory final closure and staged-state
reviews pass, and the resulting exact state is committed.

## 2026-09-13 persistence/API stabilization

Astra (`/root/v4_s3b_q7_edges_preflight`) completed a read-only builder-side
preflight over the now-complete persistence/API family. Its seven HIGH and one
MEDIUM findings are preserved in
`builder-preflight-persistence-api-astra.md`. This is a FAIL/preflight result,
not independent authority and not a completion claim.

Builder responses now cover the complete set together:

- exact evidence and applicability event-chain/cause verification in Python
  and PostgreSQL;
- exact forward child identity resolution for every typed-owner child slot;
- all-three-gate and active-actor request enforcement;
- a BEFORE INSERT direct-request guard using the normative lock prefix;
- deduplicated bounded SQL reachability rather than path enumeration;
- reachable, deterministic, append-once stale repair while ordinary GET stays
  fail-closed on freshness drift;
- stable 409 mapping for expected integrity/deadlock/serialization/timeout
  database failures, with unknown failures re-raised; and
- exact structural Slice-3A validation of Slice-3B correction bindings.

The direct-SQL suite now also checks ORM/catalog parity (columns, nullability,
unique/FK/check/index/trigger coverage), false cause rejection, equal-payload
forward-reference swaps, a layered DAG, inactive actors/all disabled gates,
forced two-connection lock ordering, genuine stale-cause retry, and mixed
Slice-3A/3B correction agreement. Missing projection indexes were added where
catalog parity exposed them.

The first formal whole-family implementation review examined packet
`2a898fc45c640c2d38e18887163e4214ba16cedfeb0f34bc6481f1149cf843ad`
and returned FAIL with two HIGH and two MEDIUM findings. The exact report is
`adversarial-implementation-persistence-api-initial.md`. It independently
closed the anchor optimization and all other prior implementation findings,
then identified incomplete GET/lock-timeout mapping, unsafe lexical downgrade
locks, missing GET snapshot interleavings, and missing rollout/final-matrix
proofs. Builder responses for those four findings are complete and remain
`fixed_pending_verification` until closure review.

Latest completed evidence before this save:

- complete non-PostgreSQL V4 host set: 432 passed, one PostgreSQL-only test
  skipped, two existing Starlette deprecation warnings;
- current correction/expression focus after final order disposition: 51 passed;
- generated serializer PostgreSQL matrix: 31 passed;
- candidate PostgreSQL migration/concurrency/immutability suite: 5 passed on a
  dedicated clean database after restoring the current head following its
  historical-migration probe;
- Slice-3A applicability PostgreSQL suite: 24 passed on a dedicated clean
  database;
- final expanded PostgreSQL persistence suite: 37 passed in 14.49 seconds on
  fresh database `t081_s3b_persist_am`, including direct corruption, anchor
  re-deferral, exact 16,384-character decimal persistence, seven failure
  phases, nine GET/transition snapshot races, and the observed-wait
  downgrade/writer interleaving;
- exact `9ad410b7c4021244ac36a6fab44b1dd021f5d05c` reader passed against
  fresh upgraded-empty `0028`, then rejected the first committed Slice-3B
  correction binding as required, on `t081_s3b_rollout_ah`;
- API SQLSTATE boundary matrix: 28 passed across POST/detail/reconstruction/list
  for `P0001`, `23*`, `40P01`, `40001`, `57014`, `55P03`, and unknown re-raise;
- application/database gate and authority matrices: 18 passed with zero-row
  failure proofs;
- fresh migration through the amended `0028`: passed; empty 0028→0027→0028
  downgrade/re-upgrade passed on `t081_s3b_migration_ak` after replacing
  lexical locks with the explicit parent-before-child order;
- all five calibration packets completed the host round trip in one gate;
- all five calibration packets completed the PostgreSQL deferred round trip
  exactly in 55.01 seconds on fresh database `t081_s3b_calibration_ai`, with
  byte-exact before/after snapshots of 19 released V3, matching, coverage,
  recurrence, and due-state tables around every Slice-3B materialization;
- mapping digest:
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.

Closure review 1 examined packet
`59d2ac3d8bcc923eb104c1c9ac37a10b10ce5dee73bb63e61f32720ac32a0c58`
and returned FAIL with no blocker or HIGH. Its two residual MEDIUM findings
were test-oracle defects rather than production defects: downgrade
synchronization did not prove that Alembic had reached its root wait, and the
failure-phase labels did not match the five actual persistence flushes. The
exact report is `adversarial-implementation-persistence-api-closure-1.md`.

Both oracle defects are now repaired:

- the downgrade regression gives Alembic a unique `application_name` and uses
  a separate autocommit observer to confirm its ungranted
  `AccessExclusiveLock` on the projection root through
  `pg_stat_activity`/`pg_locks` before the writer probes the correction child;
- the failure matrix now covers before root, after root, after semantic nodes,
  after remaining children/correction, after request, after event, and after
  forced constraints, and proves the expected transient rows exist in the open
  transaction before proving exact rollback to the committed baseline.

The exact current PostgreSQL persistence suite passes 37/37 in 14.49 seconds
on freshly created and migrated database `t081_s3b_persist_am`.

Independent whole-family implementation closure review 2 passed exact packet
`dab985ad87c8abbaed01cd4f2d3d31ebf16bcbeb4ab594f7ccf2bfda7638e740`
with no blocker, High, Medium, or scope-omission finding. Its immutable report
is `adversarial-implementation-persistence-api-closure-2.md`. It explicitly
closed `PERSIST-PREFLIGHT-005` and `PERSIST-IMPL-011`; the finding ledger now
has no open or pending entry, and the implementation PASS is recorded against
scope fingerprint
`6d5e02be93ed4dd7f0bdd82d29c5b102ed87ee4ffdfaf5efcc84934f6f91342e`.

IA-001 and Slice 3B still require the selected external critic, disposition of
every returned candidate, mandatory final closure review, staged-state
attestation, and commit. Nothing is staged or committed.

The implementation-reviewed tree was rebuilt as an external-critic packet and
verified current at SHA-256
`dba42109c9c631cdd0c943d352f7ee6d2c49b8ed8140f2e5de5d8f3274c9e326`.
The first `scripts/claude-review.sh` invocation did not transmit the packet:
the managed execution environment rejected it because external Claude review
would disclose private repository code and review material, and requires the
user's explicit informed approval. Do not retry or use an indirect route
without that approval. Because this checkpoint edit changes packet input, the
external-critic packet must be rebuilt and reverified immediately before an
approved retry.

The user explicitly approved that disclosure. The rebuilt packet was verified
current at SHA-256
`c91d62d2042ce4c1839f06e4ebc0856a8e3a32f290f3fe23805e1467c3e02492`
and Claude completed artifact
`claude-external-critic-20260913T171021Z.md`. It reported zero Blocker, High,
or Medium candidate and one Low optional performance candidate. The
coordinator traced all callers and recorded
`T081-V4-SCHEMA-SLICE-3B-CC-001` as `rejected_finding`: detail and
reconstruction repeat verification within one immutable snapshot, but list
does not duplicate it, no invariant is violated, and Claude explicitly stated
the optimization is not required for closure. Claude independently ran the
full non-PostgreSQL backend suite: 634 passed and 101 skipped.

## Exact next action

Rebuild and verify the closure packet with the Claude artifact, sidecar,
candidate disposition, and completed `closure.md`; obtain the mandatory
independent final closure review with an explicit IA-001 disposition. If it
passes, record closure, validate the run, stage the exact reviewed scope, and
obtain a fresh staged-state fingerprint re-attestation before commit.

The mandatory independent final closure review passed exact closure packet
`448649ffaceb672636f1dfc422f5062348526449d72f8d4dba495915738c8dfc`.
Its immutable report is `adversarial-closure-final.md`. The reviewer explicitly
closed IA-001, validated both rejected dispositions, found no residual or
scope omission, and independently reran the focused global owner mapping plus
fresh 37-test PostgreSQL persistence suite. The closure PASS is recorded,
`state.json` is `closed`, and `validate-review-run.py` reported the run
closable before staging.

## Exact next action after closure PASS

Stage only the reviewed Slice-3B product/test scope and this review-run's
durable non-diagnostic evidence, rebuild and verify a closure-stage packet for
the index state, and obtain the required independent staged-state
re-attestation. Commit only if the index has no unmerged/unstaged product drift,
the staged reviewer passes, the re-attestation records successfully, and final
validation remains clean.

## Resume cautions

- Rebuild and verify `review-packet.md` before every new reviewer assignment;
  the current packet is stale after finding-ledger and checkpoint updates.
- Explicitly bind `normative-mapping-matrix.md` in implementation packets. Its
  current SHA-256 is
  `b9c7dc0fa30c0e840f80c9599113eebf000cec7478c8bcd94eb4ce3f5b6c4c55`.
- Do not record a bounded family PASS as the formal overall implementation PASS.
- Preserve builder/reviewer separation. Reviewers remain read-only.
- Do not stage or commit until IA, implementation, closure, and staged-state
  reviews all pass.
