# T081-CAL-2024-14-03 independent design adversary

Reviewer: `/root/t081_cal_2024_design`

Outcome: **FAIL**

The retained-byte approval and release boundaries provide a sound fail-closed
foundation: the authenticated decision endpoint locks the review, re-bounds the
retained source, reruns all approval blockers, and materializes only after those
checks pass. An incomplete proposal can therefore remain non-released. The
proposed staging design is not yet safe enough to implement, however, because it
does not define which blockers may be bypassed, does not serialize staging with
approval, and does not account for all regulatory text represented by the
calibration packet.

No product code was edited during this review.

## Findings

### T081-CAL-DA-001 — High — `--allow-incomplete` has no bounded blocker taxonomy

**Violated invariant:** An incomplete calibration draft may retain explicit
source/parser uncertainty, but it must remain a complete v3 object bound to the
correct directive and unchanged retained source.

**Evidence:** The design says the new mode records "the current approval
blockers" and permits staging despite them, without distinguishing tolerated
calibration uncertainty from identity and integrity failures
(`decision.md:45-55`). `extraction_approval_blockers` currently returns one flat
list containing wrong AD number, changed retained source set, wrong publication
date, missing source identity, malformed structure, evidence mismatch, and
unresolved uncertainty. The current CLI also merges the input over the stored
proposal (`stage_ad_review_proposal.py:40-44,75`) even though both its error text
and the design claim a complete object. The manual validator does not enforce
the full provider schema or reject extra/omitted top-level review fields
(`ad_extraction.py:747-794`).

**Impact:** A likely implementation that simply ignores nonempty blockers could
stage a partial, wrong-directive, stale-source, or structurally invalid packet
under the same trusted-looking provenance as the intended OCR/serial calibration
draft. Publication would still fail closed, but the human-review evidence and
audit attribution would be misleading and rollback/replay would not identify
what class of defect was intentionally accepted for staging.

**Required closure:** Define two explicit validation tiers. In incomplete mode,
require an exact complete-object replacement, schema/shape and referential
integrity, matching AD number, matching immutable discovery date, current
`input_content_hash`, verified bounded source identity, nonempty requirements and
applicability, and citations that refer only to admitted document/page pairs.
Only enumerated evidence mismatches caused by the recorded OCR-cell discrepancies
and nonempty uncertainty reasons may remain. Prefer typed blocker codes rather
than classifying human-readable strings. Add negative tests for partial input,
wrong AD, changed source set/hash, wrong document/page, malformed group links,
and an unrecognized blocker.

### T081-CAL-DA-002 — High — Staging is not serialized with approval or terminal review state

**Violated invariant:** Staging must modify only a pending/needs-review record
and must never overwrite an approved extraction or its signed output.

**Evidence:** The authenticated decision path locks `ADExtractionReview` with
`FOR UPDATE` before checking terminal state (`ads.py:606-646`). The current
staging path filters for `pending` when it first reads the review but takes no row
lock and later writes both `review.proposed_output` and `extraction.output`
(`stage_ad_review_proposal.py:56-75,92-96`). The proposed design and test plan do
not mention concurrent stage-versus-approve behavior (`decision.md:83-104`).

**Impact:** An administrator can approve while a CLI invocation is validating.
The CLI may then commit its incomplete proposal over the newly approved
extraction. The signed-release equality check should quarantine that extraction,
so this is fail-closed for safety, but it silently revokes availability, mutates
a terminal regulatory artifact, and destroys the claimed clean human-decision
boundary.

**Required closure:** Acquire the same review row lock used by the decision
endpoint, and after the lock assert exact preconditions: review `pending`,
extraction `needs_review`, directive not approved/complete, unchanged source
hash, and no decision output/history indicating a terminal decision. Keep the
read, validation, event writes, and proposal update in one transaction. Add a
real two-session PostgreSQL test proving approve-first makes stage fail without
mutation and stage-first leaves approval to revalidate the staged packet.

### T081-CAL-DA-003 — High — The claimed complete proposal omits regulatory clauses that affect interpretation

**Violated invariant:** The calibration proposal must account for the entire
directive and preserve safety-bearing qualifications, not merely populate two
headline actions.

**Evidence:** The packet commits to exactly two requirements
(`decision.md:10-15`), and the retained draft has empty `conditions` for both
(`2024-14-03.requirements.json:3-27,30-47`). The official rule also contains
paragraph (f), "unless already done," and Note 1 to paragraph (g), which states
an optional service-bulletin path and expressly permits later software versions
not listed in the bulletin. Neither clause is dispositioned in the decision or
draft. The packet also lacks a paragraph-by-paragraph coverage matrix proving
that (a)-(k), Table 1, and the AMOC notification condition were represented or
intentionally classified as non-material.

**Impact:** Calling this a complete machine-assisted proposal can lead the human
reviewer to approve an extraction that loses an existing-compliance exception or
misstates which software-update methods/versions satisfy the rule. This defeats
the calibration set's purpose even though publication remains technically
blocked today by serial/OCR uncertainty.

**Required closure:** Add a source coverage matrix for every operative paragraph
and Table 1. Represent paragraph (f) and Note 1 source-faithfully in the existing
schema (as cited requirement conditions/context, or document why another field
is authoritative), include paragraph (i)(2)'s pre-use notification condition in
the AMOC envelope, and test that each retained clause is present in or explicitly
dispositioned by the proposal. Do not invent a third mandatory action merely to
store explanatory Note 1.

### T081-CAL-DA-004 — Medium — Audit replay and rollback are underspecified

**Violated invariant:** Every privileged proposal mutation must be attributable,
replayable, and reversibly distinguishable from the prior proposal.

**Evidence:** The design promises actor and blocker recording and says rollback
"restores the prior proposal shell" (`decision.md:69-75,89-94`) but defines no
immutable proposal history, previous-output snapshot, rollback command, or
idempotency behavior. Current events record actor, directive, AD number, and
requirement count only, while mutable `raw_response` keeps only the latest
staging metadata (`stage_ad_review_proposal.py:97-125`). Generic product-event
properties truncate lists and strings, so they cannot be assumed to retain a
large table-cell blocker inventory.

**Impact:** Repeated or mistaken staging cannot be reconstructed or mechanically
reverted from database evidence, and later reviewers cannot prove which exact
proposal/source/blocker set an administrator staged.

**Required closure:** Define an append-only staging record containing actor,
timestamp, mode, review/extraction IDs, source-input hash, previous and new
structured-output hashes, complete blocker codes (or a hash plus immutable full
payload), and the prior/new proposal needed for restoration. Define duplicate
input behavior and an explicit rollback/re-stage procedure. Test dry-run
nonmutation, committed history, duplicate replay, failed transaction rollback,
and restoration of the exact prior proposal without changing decision or
materialized state.

## Source/OCR and serial-scope assessment

- `serialNumberApplicability.kind = "unknown"` with no invented serial text and
  a nonempty uncertainty reason is the correct fail-closed draft for this AD;
  `kind = "all"` is not source-supported.
- Each visually corrected Table 1 cell must carry its own discrepancy reason and
  exact PDF document/page attribution. A generic table-level warning is not
  enough to identify which model designations are unverified by parsed text.
- `normalizedName` and `normalizedDesignation` must remain null or identical to
  cited source identity; they cannot be used to smuggle a visual OCR correction
  past evidence validation.
- Requirements must reference every applicability group to which they apply, and
  the shared Garmin/GSA 28/STC/drawing-list predicate must be preserved as an
  all-of condition for every Table 1 branch.

## Required verification additions

In addition to the packet's proposed positive test, implementation review must
see: wrong-source/identity negatives; malformed and partial-object negatives;
per-cell OCR discrepancy assertions; unknown serial scope remaining an approval
blocker; strict mode rejecting the identical proposal; authenticated HTTP
approval rejecting it; zero applicability, requirement, AMOC, match, due-state,
coverage, or released-catalog rows/readers; two-session stage/approve ordering;
audit replay/idempotency; and exact rollback restoration.

**DESIGN OUTCOME: FAIL**
