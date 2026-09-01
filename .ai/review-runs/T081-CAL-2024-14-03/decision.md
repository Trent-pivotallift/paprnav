# Decision packet: T081-CAL-2024-14-03

## Objective

Populate the fresh source-bound AD 2024-14-03 v3 review with a complete,
source-cited calibration proposal instead of an empty deterministic shell,
without approving, publishing, materializing, or suppressing unresolved source
and parser uncertainty.

## User-visible outcome

The linked admin review displays proposed applicability groups, the two
compliance requirements, effective/publication dates, and the AMOC provision
beside the retained source. Any unresolved serial-scope or table-extraction
issue is explicit and continues to block publication.

## Safety and correctness invariants

1. Staging never changes review/extraction/directive status from pending or
   needs-review and never creates applicability, requirements, matches, due
   state, AMOC, or released-catalog data.
2. Every exact field claimed as source-verified is tied to the retained
   document ID, page, and wording; visually identified OCR discrepancies remain
   explicit uncertainty and are not silently normalized.
3. The v3 JSON remains the complete top-level object. Requirements reference
   every applicability group they govern; AMOC authority is not a maintenance
   requirement; compatibility summaries remain derived.
4. An incomplete-draft staging mode may retain approval blockers for human
   calibration, but the normal strict staging mode and authenticated publish
   endpoint remain fail-closed.
5. Human approval is not performed in this slice.

## Current behavior

The deterministic source refresh correctly created review
`arv_94f8a23dd22a457faf007aa588601018` with two verified retained PDFs and ten
bounded pages, but its proposal contains empty applicability, requirements, and
AMOC arrays. The existing staging CLI describes itself as a non-approving draft
tool yet rejects every proposal having any approval blocker, so it cannot stage
an intentionally unresolved calibration packet. The table image on source
pages 3-4 visually resolves several model names that the retained text parser
misreads (for example 172I as 172T), which must remain blocked until parser or
source-text remediation.

## Proposed design

Create a complete calibration proposal artifact using the visually inspected
official PDF and the retained requirement draft. Preserve the Table 1 branches
as manufacturer/model applicability groups with the shared Garmin GFC 500,
GSA 28, STC, and drawing-list condition. Use explicit uncertainty for the
unstated serial-number scope and OCR-discrepant table cells.

The privileged staging CLI will require both the AD number and exact review ID,
lock that review with `SELECT ... FOR UPDATE`, and recheck that the review is
still `pending`, its extraction is still `needs_review`, and both belong to the
requested AD before writing. It will replace the complete proposed-output
object; no shallow merge with an older shell is allowed.

An explicit `--allow-incomplete` mode may retain only these typed calibration
blocker classes: `applicability_uncertainty`, `requirement_uncertainty`,
`amoc_uncertainty`, and `visual_ocr_model_cell_mismatch`. The OCR type is
narrowly limited to a `modelApplicability.models[].sourceDesignation` whose
citation resolves to an exact retained document/page but whose value is absent
from the parsed page text, whose group carries an explicit uncertainty reason
recording both the visual PDF transcription and conflicting parsed token. It
does not excuse manufacturer, action, timing, condition, date, AMOC, document,
page, or general citation mismatches. It remains fatal and unmodified in the
authenticated HTTP approval validator until the retained text itself is
remediated and reviewed.

Both modes reject every structural/schema error, empty required array,
AD-number mismatch, stale source-set hash, immutable-date mismatch,
missing document/page citation, source-boundary failure, non-model evidence
mismatch, or unclassified blocker. The implementation will classify blockers
from structured validation results, not substring-match arbitrary human
messages. Default behavior remains approval-ready-only.

Each committed change appends an `ADExtractionReviewDecision` row with
`event_type=proposal_staged`, `decision=proposal_staged`, the new complete
payload/hash in the existing decision-output columns, and the prior complete
payload/hash, allowed blocker codes, source-input hash, and target IDs in
metadata. This existing append-only review history—not mutable `raw_response`
or a truncated product event—is authoritative. The locked review row is the
serialization/uniqueness boundary: if its current proposal hash already equals
the requested new hash, the command is an idempotent no-op and appends neither
a history row nor event. Rollback supplies a prior decision row's complete
payload as a new staging input and therefore appends a new inverse snapshot;
historical rows are never updated or deleted.

## Alternatives considered

- Ask the reviewer to author the packet from a blank shell: rejected because it
  defeats machine-assisted calibration and makes omissions likely.
- Guess all serial numbers and silently correct OCR table cells: rejected
  because the current evidence validator cannot mechanically prove those
  values from retained parsed text.
- Publish an incomplete packet: rejected; uncertainty and evidence mismatches
  must continue to block approval.
- Directly update PostgreSQL: rejected in favor of an actor-attributed,
  dry-run-by-default operational staging path.

## Trust, authorization, and audit boundaries

The retained PDF bytes are authoritative evidence. Rendered visual inspection
is review input, not automatic authorization. The calibration JSON is an
untrusted proposal. The direct-database CLI remains restricted to trusted
operators, requires an active platform-admin actor for attribution, and cannot
approve. Only the authenticated HTTP human decision path can publish.

## Read paths and consumers

- Admin extraction review page and exact retained-source endpoint.
- Calibration README shortlist and proposal artifact.
- Approval blocker serialization; no released reader may consume the draft.

## Write paths and administrative paths

- `stage_ad_review_proposal` updates only the locked pending review proposal,
  needs-review extraction output, append-only `ADExtractionReviewDecision`
  staging history, and audit events. Mutable `raw_response` may contain only a
  convenience pointer to the latest staging decision ID; it is not audit
  evidence. Input is a complete replacement object, never a partial patch.
- No relational materialization or terminal human `review_decision` history is
  written by staging; append-only `proposal_staged` audit rows are intentional.

## Migration, compatibility, correction, and rollback

No schema migration is required. Omitting `--allow-incomplete` preserves the
strict existing CLI contract. A recorded snapshot supplies the exact prior
payload and hashes needed for replay or rollback; restoring it is another
actor-attributed staging operation. No released regulatory state needs reversal
because this slice performs no approval.

## Test strategy

- Unit-test incomplete mode stages a complete cited packet while preserving
  pending/needs-review state and recording typed allowed blockers; strict mode
  rejects it. Include a positive model-cell OCR mismatch and negative cases for
  manufacturer, action, timing, date, AMOC, missing document/page, and unknown
  citation mismatches. Structural, identity, source-hash, date, non-model
  evidence, and unknown blockers remain fatal in both modes.
- Test exact-review targeting, same-row locking/terminal-state conflict,
  complete-object replacement, immutable prior/new snapshots, identical replay
  idempotency, and exact rollback replay.
- Validate the proposal structure and report its approval blockers against the
  exact retained pages.
- Dry-run then commit staging; verify review ID, actor attribution, requirement
  count, retained pages, and zero approval/materialization.
- Frontend lint/build and focused backend tests.

## Expected file scope

- `.ai/ad-calibration/2024-14-03.v3.proposal.json` and calibration README.
- `backend/app/scripts/stage_ad_review_proposal.py` and focused tests.
- Frontend review-page loading/empty-state handling.
- Review artifacts under `.ai/review-runs/T081-CAL-2024-14-03/`.

## Known uncertainty

The AD does not state an explicit serial-number clause, while current v3
evidence rules require serial wording to prove `kind: all`. The table is an
image and retained text has several OCR substitutions on page 4. Both remain
explicit blockers for methodology/parser remediation and human resolution.

The proposal must account for every operative paragraph rather than presenting
only paragraphs (g) and (h): paragraph (f)'s exact “unless already done” rule is
bound to the one-time update requirement; Note 1 is retained verbatim as a
non-mandatory method/alternative and explicitly marked as not a separate
obligation because v3 has no dedicated method-reference object; and paragraph
(i) is captured as one AMOC provision containing the approving authority,
submission route, and required pre-use notification. If these meanings cannot
be represented without distortion, the proposal carries a typed uncertainty
and stays unapprovable.
