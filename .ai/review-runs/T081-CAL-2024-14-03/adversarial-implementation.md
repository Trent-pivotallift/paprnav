# Adversarial implementation review: T081-CAL-2024-14-03

Reviewer: `/root/t081_cal_2024_design`
Stage: implementation
Outcome: **FAIL**
Reviewed packet: `.ai/review-runs/T081-CAL-2024-14-03/review-packet.md` (`0520c00fc3dc80f1506132aa409b40cd9a11e1632d6b4aeb1dab5df94b930891`)

The implementation does not yet close the design obligations. The retained
2024-14-03 proposal itself is materially complete and the committed staging
operation remains pending and non-materialized, but three high-severity trust
boundary defects and three medium-severity audit/test defects remain open.

## Findings

### T081-CAL-IA-001 — High — Open

**Invariant:** Both strict and allow-incomplete staging reject every structural
or schema error, and the staged input is a complete v3 object.

**Finding:** The operational validator is not the declared v3 JSON schema.
`AD_EXTRACTION_JSON_SCHEMA` requires `confidence`, `citations`, and
`uncertaintyReasons` and rejects additional properties, but
`validate_extraction_output` does neither. The allow-incomplete path calls only
that weaker validator before staging.

**Evidence:**

- `backend/app/services/ad_extraction.py:186-272` declares the complete schema,
  including `additionalProperties: false` and the three required top-level
  fields.
- `backend/app/services/ad_extraction.py:747-794` omits those fields and has no
  additional-property check.
- `backend/app/scripts/stage_ad_review_proposal.py:132-145` relies on the weaker
  validator.
- Executable counterexamples against the retained 2024-14-03 proposal and exact
  PDF pages produced:
  - `partial_top_level=ACCEPTED` after removing all three required fields.
  - `additional_property=ACCEPTED` after adding an undeclared top-level field.

**Impact:** A partial or schema-incongruent object can be actor-attributed and
shown as a complete v3 proposal. Because authenticated approval also calls the
same weaker validator through `extraction_approval_blockers`, this is not
confined to the administrative staging CLI.

**Required closure:** Validate the full object and all nested objects against
the authoritative v3 schema (or implement an exactly equivalent strict
validator) before either staging mode or HTTP approval can proceed. Add
negative tests for missing required fields, extra fields, invalid nested
shapes, invalid confidence values, and non-JSON numeric values.

### T081-CAL-IA-002 — High — Open

**Invariant:** The visual OCR exception applies only to the cited
`sourceDesignation`; it cannot excuse or rewrite an unsupported canonical
identity.

**Finding:** The validation shadow overwrites a non-null
`normalizedDesignation` with the parsed OCR token before evidence validation.
That removes the unsupported canonical value from the object being validated,
even though the original unsupported value is what gets staged.

**Evidence:**

- `backend/app/scripts/stage_ad_review_proposal.py:118-120` rewrites both
  `sourceDesignation` and any non-empty `normalizedDesignation` in the shadow.
- `backend/app/services/ad_extraction.py:1215-1229` would otherwise reject a
  normalized identity that is neither null nor equal to source identity.
- An executable counterexample set the visually cited `172I` model's
  `normalizedDesignation` to `UNSUPPORTED-CANONICAL`. Incomplete validation
  accepted it because the shadow became
  `{"sourceDesignation":"172T","normalizedDesignation":"172T"}` while the
  staged proposal retained the unsupported value.
- `backend/tests/test_ad_ingestion.py:1591-1630` tests only a null normalized
  designation and therefore does not cover this path.

**Impact:** The narrow model-cell exception can stage a canonical model claim
that neither the visual PDF nor retained text supports. This weakens the
identity boundary the exception was designed to preserve.

**Required closure:** Require `normalizedDesignation` to remain null for an OCR
exception (or validate it independently against an already reviewed canonical
mapping); never mutate it in the validation shadow. Add a negative regression
test using a non-null conflicting value.

### T081-CAL-IA-003 — High — Open

**Invariant:** A human reviewer can distinguish an administrator-authored
calibration proposal from raw model output using authoritative staging
provenance.

**Finding:** The GUI's provenance banner is unreachable for the newly staged
record. Staging writes only `latestProposalStagingDecisionId`, while review
serialization still reads the removed `proposalStagingMode` raw-response key.
The append-only decision row is present but is not consulted by this read path.

**Evidence:**

- `backend/app/scripts/stage_ad_review_proposal.py:293-327` appends the
  authoritative `proposal_staged` row and stores only its ID as a convenience
  pointer.
- `backend/app/api/routes/ads.py:925-990` sets `proposalProvenance` only from
  `raw_response["proposalStagingMode"]`.
- `frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx:108-110`
  shows the warning only when `proposalProvenance` is non-null.
- Live PostgreSQL inspection of review
  `arv_94f8a23dd22a457faf007aa588601018` found a valid pointer to
  `ard_25ded7d89273493aa0f29a79eaadabff` but a null UI provenance value.

**Impact:** The admin review page presents a hand-authored calibration proposal
under “Proposed structured extraction” without the intended warning that it is
not raw model output. That can contaminate human calibration and audit
interpretation.

**Required closure:** Resolve the latest pointer to the authoritative
append-only `proposal_staged` row and serialize staged-by, staged-at, decision
ID, and staging mode from that row. The UI must display the provenance before
the proposal can be reviewed; mutable raw response must not become the audit
authority again.

### T081-CAL-IA-004 — Medium — Open

**Invariant:** Allow-incomplete classification is typed and cannot depend on
arbitrary human-readable blocker strings.

**Finding:** Although blocker codes are calculated, the actual fatal/allowed
decision is still made by exact comparison with dynamically reconstructed
English messages.

**Evidence:** `backend/app/scripts/stage_ad_review_proposal.py:227-263` builds
`allowed_messages` from uncertainty counts and filters the string list returned
by `extraction_approval_blockers`. This directly contradicts the decision
packet's structured-classification requirement.

**Impact:** The safety contract is coupled to message wording and count
formatting. A harmless message edit can make a permitted draft fail, and a
future colliding message can be misclassified. The current comparisons are
exact rather than substring-based, so no present non-uncertainty bypass was
demonstrated, but the promised typed boundary is absent.

**Required closure:** Return stable structured blocker objects/codes from the
approval validator and permit only the enumerated codes. Human strings should
be presentation fields, not authorization inputs.

### T081-CAL-IA-005 — Medium — Open

**Invariant:** Append-only history reconstructs every mutable proposal state,
and same-hash replay is safe and idempotent.

**Finding:** The prior snapshot and idempotency boundary consider only
`review.proposed_output`, even though staging mutates both that field and
`extraction.output`. No equality invariant is checked before the early return.

**Evidence:** `backend/app/scripts/stage_ad_review_proposal.py:278-321` hashes
and records only the prior review proposal, returns immediately when its hash
matches the requested proposal, and otherwise overwrites both mutable copies.
`backend/tests/test_ad_ingestion.py:1693-1789` initializes the two copies equal
and never exercises divergence.

**Impact:** If the two mutable copies are already inconsistent, same-hash replay
can report an idempotent no-op while leaving `extraction.output` divergent, and
a new stage can erase its prior value without recording that value. The history
would not be authoritative for the complete mutable pre-state.

**Required closure:** Enforce and test equality of the review and extraction
payload/hash under the locked row before staging, or record both prior
snapshots and include both in idempotency. Divergence must fail closed and be
remediated through an auditable path.

### T081-CAL-IA-006 — Medium — Open

**Invariant:** The high-risk slice has executable proof for targeting,
serialization, terminal races, negative exception classes, rollback, and the
unchanged strict HTTP boundary.

**Finding:** The implementation adds only two focused tests. They do not cover
the decision packet's negative matrix, exact AD/review mismatch, terminal
state, a real PostgreSQL stage-vs-approval race, strict HTTP rejection of the
staged artifact, failed/dry-run transaction behavior, or divergent mutable
copies. The repository concurrency verifier tests two terminal decisions, not
staging against approval.

**Evidence:** The only staging-specific tests are
`backend/tests/test_ad_ingestion.py:1591-1630` and `:1633-1789`.
`backend/app/scripts/verify_ad_review_concurrency.py` never invokes
`stage_review_proposal`.

**Impact:** The same-row `FOR UPDATE` implementation and pending/needs-review
checks are plausible and align with the HTTP row lock, but their cross-path
ordering remains unproved. Most fatal exception classes can regress without a
focused failure.

**Required closure:** Implement the negative matrix from `decision.md`, plus a
two-session PostgreSQL stage-vs-approval test that proves the second actor sees
terminal state after acquiring the exact same row lock. Verify no staging
history or mutable write survives every rejected or dry-run transaction.

## Positive verification

- The implementation packet hashes matched the current files during review.
- The retained Federal Register PDF was rendered and visually inspected on
  pages 3-5. Table 1 contains the proposed five manufacturer groups with model
  counts `[7, 2, 10, 33, 130]`; the visual/OCR conflict records correspond to
  actual table cells.
- Fourteen proposal obligations passed: identity, group/model coverage, shared
  requirement scope, paragraph (f), paragraph (g), Note 1, paragraph (h), both
  AMOC paragraphs, dates, OCR record count, and v3 proposal shape.
- The current strict HTTP blocker computation returns three blockers and does
  not permit approval of the staged artifact.
- Live PostgreSQL state remains `pending` / `needs_review`; directive approval
  is unset; the proposal has five groups, two requirements, and one AMOC; the
  one staging row has an actor plus full prior/new snapshots and matching new
  hash; applicability, requirement, AMOC, and match materialization counts are
  all zero.
- The source-page cache re-verifies exact retained PDF bytes, page text,
  document hashes, and complete page-set equality before use
  (`backend/app/services/ad_extraction.py:1468-1534`). No source-boundary bypass
  was found.
- The same pending review row is selected with `FOR UPDATE` by both staging and
  HTTP approval, and both recheck terminal state after lock acquisition. The
  missing cross-path test remains finding IA-006 rather than a demonstrated
  race.

## Verification summary

**67 passed out of 71.**

- Backend AD-ingestion suite: **42 passed out of 42**.
- Proposal/source obligation checks: **14 passed out of 14**.
- Frontend lint and production build: **2 passed out of 2** (one unrelated
  existing lint warning).
- Live PostgreSQL state/audit/materialization checks: **9 passed out of 10**;
  GUI provenance resolution failed.
- Adversarial rejection checks: **0 passed out of 3**; incomplete top-level,
  additional-property, and conflicting-normalized-identity inputs were all
  accepted when each should have been rejected.

No product code was edited by this reviewer. Closure requires fixes and a new
independent implementation re-review; this artifact is not a release approval.
