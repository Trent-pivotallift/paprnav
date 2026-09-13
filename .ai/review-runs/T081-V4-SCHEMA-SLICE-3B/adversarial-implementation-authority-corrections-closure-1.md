# Bounded A1/A2/CB closure review 1

- Reviewer runtime: `/root/v4_s3b_design_adversary`
- Packet SHA-256: `6f66446b900233bce7eb896586768d77d7c17fb2d3c048911ca1ce6118b34efa`
- Packet currentness: verified
- Review mode: read-only; no files edited
- Verdict: **PARTIAL PASS — two findings closed, one Medium remains**

## T081-V4-S3B-A-CB-IMPL-001 — CLOSED

The authority and correction boundaries now validate exact family, collection,
and row types before dereferencing fields. Independent probes confirmed
controlled `ObligationIntegrityError` for null/dict/MappingProxyType/UserDict
families or collections, hostile authority elements in every collection, the
same correction reference inputs at both public boundaries, and malformed
correction families/bindings. No raw TypeError or AttributeError remained.

## T081-V4-S3B-A-IMPL-002 — CLOSED

`_evidence_links()` now requires a mapping and exact string binding targets.
Independent probes replaced both A1 and A2 targets with list, dictionary,
integer, and boolean values; every case failed through
`ObligationIntegrityError` at materialize and verified-read reconstruction.
Non-mapping collections also failed cleanly. Same-proposal existence/lifecycle
verification remains correctly deferred to persistence/read verification.

## T081-V4-S3B-A-CB-IMPL-003 — REMAINS OPEN, Medium

The generated artifacts now contain all eight owner classifications, all six
bindable target node types, all four domain roles, and the legacy row domain.
Both consumers use the metadata, and both reject all domain-role mutations.

Slice 3A, however, validates only domain roles. The reviewer independently
mutated all eight `_CORRECTION_OWNER_BY_NAMESPACE` entries and all six
`_CORRECTION_TARGET_TYPE_BY_NAMESPACE` entries; every mutation was accepted by
the Slice-3A validator. Slice 3B rejected equivalent owner-map drift.

Required closure: make the Slice-3A compatibility validator compare both
derived maps against the generated contract and add per-entry Slice-3A mutation
tests, while retaining the domain-role tests.

## Test evidence

- A/CB-focused selection: **84 passed**
- Candidate + obligation gate: **295 passed**
- Existing Slice-3A applicability suite: **15 passed**
- Generator digest:
  `8ffe13312a10b91cecdeed54707ebfa30fe2863296273ed599363d37c0f4a4db`
- Python compilation and `git diff --check` passed.
- Packet SHA remained unchanged after review.

This is only a bounded-family verdict. Persistence, API integration,
`T081-V4-S3B-DOC-001`, and whole-Slice closure remain open.
