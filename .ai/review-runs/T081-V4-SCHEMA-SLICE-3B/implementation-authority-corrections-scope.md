# Authority and correction-binding implementation review scope

This is a bounded pre-persistence implementation review for A1/A2 general-AMOC
authority owners and the Slice-3B portion of CB correction semantic bindings.
It claims the pure construction and verified-read oracle for these families. It
does not claim PostgreSQL enforcement, ORM integration, API integration, or
overall IA-001 closure.

## Normative authority

This review is explicitly bound to
`.ai/review-runs/T081-V4-SCHEMA-SLICE-3B/normative-mapping-matrix.md`, the generated
mapping manifest, and the approved Slice-3B decision. This scope does not replace
or narrow those authorities.

## In-scope claims

- A1 is a root `amoc_provision` semantic owner keyed by exact
  `provisionKey`, ordered by canonical provision-key order, with one A2 child at
  fixed slot 0 and own one-or-more `amoc_authority_clause` evidence.
- A2 is the shared `value_assertion` owner with field code
  `approving_authority`. It preserves the complete closed known, unknown, and
  not-applicable union, including exact value or reason, all five temporal-scope
  kinds where applicable, and independent one-or-more
  `amoc_authority_clause` evidence.
- Authority source boundaries require exact JSON dictionary/list/scalar types
  before canonicalization or discriminator/set membership. Extra application,
  aircraft, method, timing, authenticity, or AMOC-use fields fail closed.
- A1/A2 evidence mappings must yield exact string candidate-binding IDs before
  link construction. The pure interface treats those strings as opaque;
  same-proposal row existence and lifecycle validity remain mandatory
  persistence/read-verification checks.
- Authority verified read reconstructs and compares the entire A family without
  sorting supplied rows. Missing, extra, reordered, cross-parent, differently
  valued, differently evidenced, wrongly typed, or foreign-projection rows fail.
- The neutral correction-reference snapshot recomputes every Slice-3A `avc_`
  correction ID and `avf_` reference ID/hash from validator-2 canonical
  corrections using the unchanged applicability row domain. It derives
  `owner_slice` solely from the closed namespace map and compares the complete
  supplied snapshot before selecting Slice-3B references.
- CB recognizes exactly the Slice-3B root namespaces `requirements`,
  `recurrenceGroups`, and `amocAuthorityProvisions`, resolving by namespace,
  typed owner, exact key, proposal, and obligation projection. Equal keys in
  different namespaces remain distinct. Multiple corrections may target one
  semantic node, but each distinct correction reference receives exactly one
  binding.
- Every new CB row uses only the obligation projection/node pair; the legacy
  applicability pair is null. `binding_slice` is exactly `slice_3b`, generation
  is exact integer 1, and identity/hash use the new `avk_` / `correction-binding`
  obligation row domain over `{refId, semanticId}`.
- The binding-set record is an exact closed object, sorted by correction ref,
  slice, and target semantic ID, serialized by the obligation internal-record
  canonicalizer, and hashed with the dedicated correction-binding-set domain.
- Correction verified read reverifies the complete D/Q/E/timing/G and A
  dependencies supplied by the caller, the entire neutral reference snapshot,
  every selected binding, and the binding-set bytes/hash. Missing, extra,
  reordered, relabeled, cross-projection, cross-node, legacy-pair, generation,
  identity, hash, or numeric-type drift fails closed.
- Runtime contract gates pin A1/A2 descriptors, the exact A1 owner shape, the
  shared assertion owner, the CB relationship identity/table contract, every
  correction namespace classification/target type, and the legacy-versus-
  obligation row-domain selection consumed by both Slice 3A and Slice 3B.

## Neutral correction-foundation boundary

The pure helper accepts canonical corrections only after the candidate-level
closed grammar and resource validation succeeds, then independently recomputes
and compares the complete correction-reference identity surface. It does not
load or independently verify persisted correction roots, correction evidence,
or incorporated-document ownership. Those remain Slice-3A/persistence
dependencies and must be reverified by the ORM/PostgreSQL/API integration before
IA-001 can close. This boundary is explicit review scope, not an exclusion from
the final invariant.

## Builder evidence

- Authority/correction-focused tests: 79 passed.
- Generated correction-compatibility parity and mutation tests: 19 passed.
- Candidate + obligation host regression: 301 passed.
- Existing Slice-3A applicability regression: 15 passed.
- Python compilation and `git diff --check` passed.
- Positive coverage includes empty A/CB sets, every authority union, every
  temporal-scope kind, exact 512-character not-applicable reason, independent
  A1/A2 evidence, canonical reordering, mixed 3A/3B correction namespaces,
  same-key cross-namespace resolution, multiple corrections targeting one
  semantic node, and exact A1/A2/avc/avf/avk/binding-set golden identities and
  hashes. The generated manifest is reproducible at SHA-256
  `e229c6008f323cb6622e96b286b6ecb93ec7f2be47a5e4dd48bec294af51465d`.
- Negative coverage includes unsupported mappings, unhashable discriminators,
  extra fields, invalid/duplicate keys and references, 513-character reason,
  incomplete/duplicate/relabeled foundation refs, unresolved targets,
  missing/extra/reordered owners and bindings, parent/type/value/evidence drift,
  legacy/obligation column-pair drift, bool generation, foreign projection/node,
  identity/hash/bytes drift, and physical dataclass-contract mismatch.
  Hostile-row coverage includes null/mapping containers and dict/string/
  UserDict elements before any field access. Evidence coverage rejects list,
  dict, integer, boolean, and non-mapping binding sources. Compatibility
  mutation coverage exercises all eight namespace classifications, all six
  bindable target types, and all four correction identity-domain roles in both
  consumers.

## Explicitly out of scope

- ORM models and all database persistence;
- Alembic migration and downgrade;
- PostgreSQL commit-time validation, triggers, exact global owner union, and
  internal-record serializer/goldens;
- API materialization, authorization/capabilities, requests/events,
  reconstruction, repeatable-read verification, stale detection, and audit;
- calibration packets, disposable PostgreSQL gates, whole-tree implementation
  review, selected external critic, closure review, staging, or commit.

These remain mandatory Slice-3B gates. `T081-V4-S3B-DOC-001` remains open until
the PostgreSQL canonical serializer and cross-language golden vectors pass
independent review. A pass here is not a final Slice-3B implementation pass and
must not be recorded as one.
