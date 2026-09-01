# T081-V4-SCHEMA slice 1 — formal closure review

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: closure  
Decision: **FAIL**  
Packet fingerprint reviewed: `6c63fa80c0ab7c14a2aa25cfabdc26c20c43a006aa0af9ff19251b7a275c16dd`

## Closure checks

- Closure-stage packet freshness: **1 passed out of 1** with
  `scripts/verify-review-packet.py`.
- Design findings: **8 closed out of 8**.
- Implementation findings: **8 closed out of 8**.
- Latest independent implementation review: **PASS**, separate reviewer and
  builder identities, fingerprint-bound artifact present and hash-valid.
- Closure report scope: accurate. It closes slice 1 only and explicitly defers
  canonical V4 semantics/persistence, decision binding, reviewer forms,
  publication/cutover, OCR/coordinates/cross-page evidence, supporting-document
  ingestion, aircraft matching, compliance, and due-state work.
- Hidden scope expansion: none identified. Existing V3 release behavior remains
  outside the implemented evidence slice and no slice-1 path makes a candidate
  actionable.
- Temporary-database evidence: coordinator records **0** databases matching
  `paprnav_t081_v4_%` after explicit cleanup; `paprnav_db` was not targeted.
- Pre-closure state is correctly `implementation_reviewed`; a supported closure
  PASS would transition directly to `closed`.

## Blocking finding

### T081-V4-CA-001 — final validator cannot reproduce the packet fingerprint

`scripts/build-review-packet.py` computes the packet fingerprint over ordinary
scope files **plus explicit review inputs**. `scripts/verify-review-packet.py`
rehashes those review inputs and accepts the current packet. In contrast,
`scripts/validate-review-run.py::current_fingerprint` hashes only changed
inventory files and omits `manifest.reviewInputs`.

The contradiction was reproduced before any closure artifact or ledger change:

- packet verifier: current, fingerprint
  `6c63fa80c0ab7c14a2aa25cfabdc26c20c43a006aa0af9ff19251b7a275c16dd`;
- final validator: `working tree changed after packet generation`.

The validator also reported the expected pre-attestation conditions—no closure
PASS and phase `implementation_reviewed`—but the fingerprint error is
independent of those expected conditions. Recording PASS now would move the
state to `closed` while leaving the required validation path unable to accept
the run.

## Required closure

Update the validator to include current explicit review-input metadata in the
same ordered fingerprint payload used by build and verify, add a regression
test, rebuild the packet, and repeat independent closure review. Product code
does not require a change for this finding.

Formal result: **0 passed closure attestations out of 1 required**. The review
run must remain `implementation_reviewed`.
