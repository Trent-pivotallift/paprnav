# Bounded adversarial implementation review — A1/A2 + CB

- Reviewer runtime: `/root/v4_s3b_design_adversary`
- Packet SHA-256: `b93a0bede8f1d53a5f05f37f26fe391bdc74c746d395b020b2ad9e52e90a3060`
- Packet currentness: verified
- Review mode: read-only; no files edited
- Verdict: **FAIL**

No blocker was found. Two high findings and one medium finding remain.

## T081-V4-S3B-A-CB-IMPL-001 — High — malformed snapshot/read rows escape the integrity boundary

Violated invariant: malformed or wrongly typed reference-snapshot and
verified-read rows must fail through `ObligationIntegrityError`.

Evidence:

- `ad_v4_obligations.py:3553` dereferences `ref.canonical_ordinal` before
  checking each `foundation_refs` element's type.
- `ad_v4_obligations.py:3715` similarly dereferences `binding.generation`.
- `ad_v4_obligations.py:3399` dereferences ordinal fields from authority family
  collections without row-shape validation.
- Independent public-boundary reproductions found raw `TypeError` for
  `foundation_refs=None`; raw `AttributeError` for mapping containers and
  dict/string/UserDict elements; and the same uncontrolled failures for corrupt
  binding or authority row elements.

Impact: corrupt reconstructed rows or an integration assembly defect bypasses
the controlled integrity-error contract and becomes an availability/error-
handling failure.

Required closure:

- Validate collection and element types before field access for
  `foundation_refs`, CB bindings, and A-family ordinal-bearing rows.
- Normalize every rejection to `ObligationIntegrityError`.
- Add `None`, dict-container, dict/string/UserDict-element probes at
  materialization and verified-read boundaries.

## T081-V4-S3B-A-IMPL-002 — High — invalid evidence-binding targets become accepted expected output

Violated invariant: every A1/A2 evidence link must bind to an exact typed Slice-2
candidate binding; construction must not emit values incompatible with
`candidate_binding_id: str`.

Evidence:

- `_evidence_links` treats every non-`None` `evidence_bindings.get()` result as
  valid and stores it without type validation.
- A1 materialization independently accepted `[]`, `{}`, `0`, and `True` as
  `candidate_binding_id`.
- Verification accepts the resulting family when rebuilt against the same
  malformed mapping.

Impact: the pure constructor and oracle can agree on an impossible typed
evidence graph. Later ORM/FK rejection does not satisfy the bounded pure-
construction claim.

Required closure:

- Require each selected evidence-binding target to be an exact string before
  constructing a link.
- Retain same-proposal/existence verification as a later persistence dependency
  if the pure interface intentionally trusts opaque string IDs.
- Add malformed target-value tests for both A1 and A2 evidence at materialize
  and verified-read reconstruction.

## T081-V4-S3B-A-CB-IMPL-003 — Medium — correction compatibility facts remain outside the generated contract

Violated invariant: the declarative mapping should cover rules whose duplication
can cause Python/Slice-3A/SQL drift.

Evidence:

- The namespace-to-owner-slice map is handwritten in `ad_v4_obligations.py`,
  separately in `ad_v4_applicability.py`, and again in migration SQL.
- The legacy applicability row domain is another handwritten compatibility
  constant.
- The generated manifest's CB descriptor pins table, identity, ordering, and
  cardinality, but contains neither the closed namespace ownership map nor the
  legacy-domain rule.
- `_validate_correction_binding_contract()` therefore cannot detect drift in
  either compatibility fact.

Impact: drift currently fails safely when the complete supplied snapshot
disagrees, but can unnecessarily disable CB materialization; coordinated
duplicate changes could also evade generated-contract parity.

Required closure:

- Put the closed correction namespace ownership map and legacy-domain selection
  rule in the declarative manifest, or establish an equivalent shared
  authoritative contract.
- Generate or parity-check both Slice-3A and Slice-3B expectations from it.
- Add mutation coverage for every namespace classification and both binding
  domains.

## Passing evidence

- Authority/correction focused tests: **50 passed**
- Candidate + obligation regression: **254 passed**
- Generator check passed; digest
  `4bad42e983c765994ab042673a3a8413aa1b4346a18f1ede9af04d024ae135fe`
- Python compilation passed.
- `git diff --check` passed.
- Packet remained at the exact reviewed SHA after testing.

The explicit neutral correction-foundation boundary is otherwise coherent.
Absence of independent persisted correction-root/document/evidence verification
was not treated as a bounded defect because the packet expressly defers it to
ORM/PostgreSQL/API integration. `T081-V4-S3B-DOC-001`, persistence, API, and
whole-Slice closure remain open.
