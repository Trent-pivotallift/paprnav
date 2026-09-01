# T081-CAL-2024-14-03 design closure review 2

Reviewer: `/root/t081_cal_2024_design`

Outcome: **PASS**

The revised decision closes all four design findings without weakening the
authenticated human-decision or signed-release boundaries. It defines a useful
but non-publishable calibration tier, serializes it with approval, retains exact
source uncertainty, and makes every committed proposal mutation reconstructable.

No product code was edited during this review. This PASS authorizes
implementation; it does not assert that the current staging script implements
the revised design.

## Finding disposition

### T081-CAL-DA-001 — High — DESIGN CLOSED

The input is now an exact complete-object replacement, not a patch. Structural,
identity, source-set, immutable-date, document/page, source-boundary,
non-model-evidence, and unclassified failures remain fatal in both modes.

The only evidence exception is the typed
`visual_ocr_model_cell_mismatch`, narrowly scoped to
`modelApplicability.models[].sourceDesignation`. It requires an admitted exact
document/page and a cell-specific uncertainty reason containing both visual and
parsed tokens. It cannot excuse manufacturer, action, timing, condition, date,
AMOC, document, page, or general citation failures. Crucially, this mismatch is
not removed from the normal validator and remains fatal at authenticated HTTP
approval until retained text is remediated and reviewed.

Implementation review must prove the classifier is structural rather than
message-substring based and cannot be widened by a crafted uncertainty string.

### T081-CAL-DA-002 — High — DESIGN CLOSED

The CLI requires both exact review ID and AD number, takes `SELECT ... FOR
UPDATE` on the same review row used by authenticated approval, and rechecks
review `pending`, extraction `needs_review`, and record identity before the
write. Complete replacement, snapshot, proposal mutation, and audit event occur
inside that serialized operation. The test plan includes terminal-state conflict
and exact targeting.

Implementation review must run both PostgreSQL orderings: approve-first rejects
staging without mutation; stage-first commits an incomplete proposal that the
subsequent HTTP decision still independently rejects.

### T081-CAL-DA-003 — High — DESIGN CLOSED

The design now accounts for the regulatory content omitted by the initial
packet: paragraph (f)'s exact “unless already done” qualification belongs to the
one-time update; Note 1 is retained as a permitted non-mandatory method rather
than invented as a third obligation; and the AMOC envelope contains approving
authority, submission route, and paragraph (i)(2)'s pre-use notification. Any
meaning that cannot fit the v3 structure without distortion adds uncertainty
and remains unapprovable.

Implementation review must compare the proposal against a paragraph-by-
paragraph source coverage artifact, all Table 1 branches, exact page citations,
and the two retained document identities.

### T081-CAL-DA-004 — Medium — DESIGN CLOSED

The authoritative store is now explicitly an append-only
`ADExtractionReviewDecision` row with `event_type=proposal_staged`. Existing
full JSON and metadata columns contain the new payload/hash, prior payload/hash,
actor, source-input hash, exact target IDs, and allowed blocker codes. Mutable
`raw_response` is only a convenience pointer and product-event truncation is not
relied upon.

The locked current review is the idempotency boundary: identical current hashes
append nothing. Rollback is an inverse staging operation sourced from a prior
immutable row and itself appends a new row; earlier history is never updated or
deleted. This is representable in the existing schema, so no migration is
required.

Implementation review must verify complete payload equality and hashes,
same-hash no-op under concurrent sessions, failed-transaction rollback, event
actor attribution, and A-to-B-to-A inverse history.

## Non-blocking clarification

The write-path section says both that staging appends
`ADExtractionReviewDecision` history and that “no ... decision history is
written.” Implementation documentation should clarify the latter as “no
terminal human `review_decision` is written”; the authoritative
`proposal_staged` history is intentionally written. The surrounding design is
unambiguous enough that this wording issue does not block implementation.

## Gate result

No design blocker remains. The incomplete packet cannot become released state:
it preserves pending/needs-review status, materializes nothing, retains typed
uncertainty, and remains subject to the unchanged strict HTTP approval and
signed-release checks.

**DESIGN OUTCOME: PASS**
