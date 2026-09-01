# T081-CAL-2024-14-03 design closure review 1

Reviewer: `/root/t081_cal_2024_design`

Outcome: **FAIL**

The revised packet materially improves the design. Exact review targeting,
same-row locking, complete-object replacement, strict/default behavior, and the
expanded source coverage are sound. Two prior findings remain open because the
written design is internally contradictory at the precise failure modes this
slice is intended to handle.

No product code was edited during this review.

## Finding disposition

### T081-CAL-DA-001 — High — OPEN — OCR discrepancy cannot pass the proposed staging tier

The packet correctly requires a complete replacement object and rejects
structural, identity, stale-source, date, boundary, and unclassified failures.
That closes the broad-bypass portion of the finding. It does not close the OCR
portion.

The design says Table 1 contains visually resolved values that differ from
retained parsed text (`decision.md:35-43`) and requires those corrected cells in
the proposal with explicit uncertainty (`decision.md:47-51`). Yet incomplete
mode permits only `applicability_uncertainty`, `requirement_uncertainty`, and
`amoc_uncertainty`, while every missing or incorrect citation is fatal
(`decision.md:59-66`). Current evidence validation requires each model source
designation and citation transcription to occur in the retained parsed page
text (`ad_extraction.py:974-986,1093-1105`). A visually correct `172I` therefore
fails as an incorrect citation/model-evidence mismatch when the parser retained
`172T`; merely adding an uncertainty reason does not change that failure class.

This leaves only unsafe or nonfunctional choices: stage the known-wrong OCR
value, silently omit the affected model, or reject the very proposal this change
exists to stage.

**Required design closure:** Add a narrowly typed
`visual_ocr_evidence_mismatch` staging blocker. Permit it only when the retained
document hash and bounded page are verified, the proposed visual transcription
is attached to that exact document/page, the affected group carries a
cell-specific uncertainty reason containing parsed-versus-visual values, and no
normalized identity claims more than the unresolved source transcription.
Every other citation/document/page mismatch remains fatal. The authenticated
approval path must continue treating this class as a blocker. Tests must cover
an allowed known cell mismatch and reject wrong page, wrong document, missing
cell-specific uncertainty, and arbitrary uncited model changes.

### T081-CAL-DA-002 — High — DESIGN CLOSED; implementation proof required

The revised design requires AD number plus exact review ID, locks the same review
row as authenticated approval, rechecks pending/needs-review state under the
lock, and replaces the entire proposal (`decision.md:53-57`). The test plan now
includes terminal conflict behavior (`decision.md:122-124`). This resolves the
design race.

Implementation review must still prove both PostgreSQL orderings and reject
inconsistent terminal evidence (`decision_output`, decision/reviewer/timestamp,
or approved/complete directive state) without mutation.

### T081-CAL-DA-003 — High — DESIGN CLOSED; implementation coverage required

The revised design now binds paragraph (f)'s “unless already done” text to the
one-time requirement, classifies Note 1 as a non-mandatory permitted method
rather than inventing an obligation, and includes AMOC approval, submission,
and pre-use notification (`decision.md:145-153`). It expressly keeps the record
unapprovable if the v3 schema cannot hold that meaning without distortion.

Implementation review must inspect a paragraph-by-paragraph coverage artifact
and verify exact retained citations; prose intent alone is not source evidence.

### T081-CAL-DA-004 — Medium — OPEN — No defined immutable snapshot store

The revised design specifies the correct snapshot contents, same-hash no-op, and
actor-attributed rollback (`decision.md:68-73,108-124`). It simultaneously says
that snapshots live in `extraction.output/raw_response` append-only history,
that no decision history is written, and that no migration is required
(`decision.md:101-114`). Those constraints do not identify an enforceable
immutable store:

- `ADExtraction.output` and `raw_response` are mutable JSON columns.
- `ProductEvent.properties_json` truncates lists to 20 elements and strings to
  256 characters, so it cannot retain both complete payloads.
- `ADExtractionReviewDecision` is the existing append-only row capable of
  holding an output payload and metadata, but the packet explicitly excludes
  decision-history writes.
- No dedicated staging-history table or external durable store is in scope.

Consequently, exact reconstruction and rollback remain aspirations rather than
a persistence design.

**Required design closure:** Name the authoritative append-only store and its
write/read contract. Either use `ADExtractionReviewDecision` with a distinct
non-decision `event_type` and explicit prior/new payload placement, or add a
dedicated staging-history table/migration. Do not call a list inside mutable
`raw_response` immutable. Define uniqueness/idempotency keys and show how an
operator selects a recorded prior snapshot for rollback without trusting a
mutable current row.

## Gate result

The authenticated HTTP publication and signed-release boundaries remain
unchanged and fail closed. Design implementation should not begin until
T081-CAL-DA-001 and T081-CAL-DA-004 are revised and independently rechecked.

**DESIGN OUTCOME: FAIL**
