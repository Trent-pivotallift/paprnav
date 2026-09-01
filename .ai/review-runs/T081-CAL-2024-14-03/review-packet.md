# Review packet: T081-CAL-2024-14-03

Stage: closure
Generated: 2026-08-24T12:12:10+00:00
Base: `HEAD`
Head: `9e45397d24fd1e9e2e988a7decf42941d346929c`
Scope fingerprint: `b6b44d14b7dbd92bdafddd76c32acdca3002edb5789b3ad50057ec2f3f7ed55b`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

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


## Current finding ledger

```json
[
  {
    "id": "T081-CAL-DA-001",
    "stage": "design",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "Incomplete staging may retain only explicitly reviewable calibration uncertainty and may never bypass structural, identity, or evidence-integrity failures.",
    "summary": "The proposed allow-incomplete mode did not define a typed blocker taxonomy or complete-object replacement contract.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design.md", "backend/app/scripts/stage_ad_review_proposal.py"],
    "impact": "A broad bypass could persist malformed or wrong-record proposals and make the draft look more trustworthy than its evidence.",
    "requiredClosure": "Permit only enumerated unresolved semantic/evidence blockers after complete v3 structural and AD/source identity checks; replace the entire proposal object rather than shallow merging.",
    "closureEvidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design-closure-2.md", ".ai/review-runs/T081-CAL-2024-14-03/decision.md"]
  },
  {
    "id": "T081-CAL-DA-002",
    "stage": "design",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "Proposal staging cannot race an authenticated approval or mutate a terminal review.",
    "summary": "The staging path did not serialize on the same review row used by HTTP approval.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design.md", "backend/app/api/routes/ads.py:decide_extraction_review"],
    "impact": "A concurrent script could overwrite proposal/output after a reviewer decision.",
    "requiredClosure": "Lock the selected review row with FOR UPDATE and recheck pending/needs-review state inside the transaction.",
    "closureEvidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design-closure-2.md", ".ai/review-runs/T081-CAL-2024-14-03/decision.md"]
  },
  {
    "id": "T081-CAL-DA-003",
    "stage": "design",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "The calibration packet explicitly accounts for every operative or interpretive paragraph, not only the two headline actions.",
    "summary": "The proposal plan did not disposition paragraph (f) unless-already-done language, Note 1, or both AMOC paragraphs.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design.md", "2024-15529.pdf page 5"],
    "impact": "The proposed extraction could omit conditions, permitted methods, or required AMOC notification.",
    "requiredClosure": "Represent or explicitly disposition paragraph (f), Note 1, and the full AMOC authority/submission/notification text with citations.",
    "closureEvidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design-closure-2.md", ".ai/review-runs/T081-CAL-2024-14-03/decision.md"]
  },
  {
    "id": "T081-CAL-DA-004",
    "stage": "design",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "medium",
    "status": "closed",
    "invariant": "Repeated or rolled-back staging is attributable and reconstructable without losing the prior proposal.",
    "summary": "The plan lacked immutable prior/new proposal hashes and explicit idempotency behavior.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design.md", "backend/app/scripts/stage_ad_review_proposal.py"],
    "impact": "Operators cannot prove what a staging run replaced or reliably distinguish replay from a new draft.",
    "requiredClosure": "Record prior/new SHA-256 and payload snapshots, define same-hash replay behavior, and verify dry-run/commit/rollback.",
    "closureEvidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-design-closure-2.md", ".ai/review-runs/T081-CAL-2024-14-03/decision.md"]
  },
  {
    "id": "T081-CAL-IA-001",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "Staging and HTTP approval reject every schema-incomplete or schema-incongruent v3 object.",
    "summary": "The operational validator did not enforce all required fields or additionalProperties false.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "Partial or undeclared data could be presented or approved as complete v3.",
    "requiredClosure": "Enforce the exact recursive v3 schema at staging and approval with negative tests.",
    "closureEvidence": ["backend/app/services/ad_extraction.py:validate_extraction_json_schema", "backend/tests/test_ad_ingestion.py:test_operational_v3_schema_rejects_partial_extra_nested_and_nonfinite_values"]
  },
  {
    "id": "T081-CAL-IA-002",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "The visual OCR exception cannot authorize an unsupported canonical identity.",
    "summary": "The validation shadow replaced a non-null normalizedDesignation.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "Unsupported canonical model identity could be staged.",
    "requiredClosure": "Require normalizedDesignation null for every visual OCR exception.",
    "closureEvidence": ["backend/app/scripts/stage_ad_review_proposal.py:visual_ocr_validation_shadow", "backend/tests/test_ad_ingestion.py:test_visual_ocr_draft_exception_is_limited_to_an_exact_cited_model_cell"]
  },
  {
    "id": "T081-CAL-IA-003",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "high",
    "status": "closed",
    "invariant": "The GUI visibly distinguishes administrator-staged calibration from raw model output.",
    "summary": "The serializer read an obsolete raw-response provenance key.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "A human reviewer could misattribute hand-authored calibration data.",
    "requiredClosure": "Resolve the authoritative proposal_staged decision and show actor, time, mode, and decision ID.",
    "closureEvidence": ["backend/app/api/routes/ads.py:serialize_review", "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx", "backend/tests/test_ad_ingestion.py:test_staging_complete_proposal_is_audited_idempotent_and_reversible"]
  },
  {
    "id": "T081-CAL-IA-004",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "medium",
    "status": "closed",
    "invariant": "Allow-incomplete authorization uses stable blocker codes, not presentation strings.",
    "summary": "Allowed blockers were selected by matching English messages.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "Message edits could alter authorization behavior.",
    "requiredClosure": "Return and authorize stable structured blocker codes.",
    "closureEvidence": ["backend/app/services/ad_extraction.py:extraction_approval_blocker_details", "backend/app/scripts/stage_ad_review_proposal.py:stage_review_proposal"]
  },
  {
    "id": "T081-CAL-IA-005",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "medium",
    "status": "closed",
    "invariant": "Idempotency cannot preserve or conceal divergent review and extraction proposal copies.",
    "summary": "Replay compared only review.proposed_output.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "A divergent extraction copy could survive replay without audit evidence.",
    "requiredClosure": "Fail closed on divergence and snapshot both prior copies.",
    "closureEvidence": ["backend/app/scripts/stage_ad_review_proposal.py:stage_review_proposal", "backend/tests/test_ad_ingestion.py:test_staging_complete_proposal_is_audited_idempotent_and_reversible"]
  },
  {
    "id": "T081-CAL-IA-006",
    "stage": "implementation",
    "reviewer": "/root/t081_cal_2024_design",
    "severity": "medium",
    "status": "closed",
    "invariant": "Staging targeting, dry-run rollback, terminal conflict, and PostgreSQL serialization have executable proof.",
    "summary": "The negative, dry-run, and stage-versus-approval test matrix was incomplete.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/adversarial-implementation.md"],
    "impact": "A regression could race approval or persist a dry-run.",
    "requiredClosure": "Add focused negative/dry-run tests and a live PostgreSQL row-lock verifier.",
    "closureEvidence": ["backend/tests/test_ad_ingestion.py", "backend/app/scripts/verify_ad_staging_concurrency.py", "scripts/verify-t081-postgres-migrations.sh"]
  },
  {
    "id": "T081-CAL-2024-14-03-CC-001",
    "stage": "external_critic",
    "reviewer": "claude",
    "severity": "medium",
    "status": "closed",
    "invariant": "The full backend safety suite is green under the exact v3 schema.",
    "summary": "A recurring-AD fixture supplied dicts where complianceIntervals requires strings.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/claude-external-critic-20260824T042633Z.md"],
    "impact": "The recurring adjudication scenario could not execute.",
    "requiredClosure": "Normalize the fixture to schema-valid interval summaries and rerun the full suite.",
    "closureEvidence": ["backend/tests/test_full_product_readiness.py", "Full backend suite passed after remediation"]
  },
  {
    "id": "T081-CAL-2024-14-03-CC-002",
    "stage": "external_critic",
    "reviewer": "claude",
    "severity": "medium",
    "status": "closed",
    "invariant": "CLI dry-run and stage-versus-approval serialization are reproducibly tested.",
    "summary": "No automated PostgreSQL concurrency or CLI rollback proof existed.",
    "evidence": [".ai/review-runs/T081-CAL-2024-14-03/claude-external-critic-20260824T042633Z.md"],
    "impact": "Concurrency and rollback regressions would lack automated detection.",
    "requiredClosure": "Add and execute both proofs.",
    "closureEvidence": ["backend/app/scripts/verify_ad_staging_concurrency.py: 6 passed out of 6", "backend/tests/test_ad_ingestion.py:test_staging_complete_proposal_is_audited_idempotent_and_reversible"]
  }
]

```

## Changed-file manifest

```json
{
  "taskId": "T081-CAL-2024-14-03",
  "stage": "closure",
  "generatedAt": "2026-08-24T12:12:10+00:00",
  "baseRef": "HEAD",
  "head": "9e45397d24fd1e9e2e988a7decf42941d346929c",
  "scopePaths": [
    ".ai/ad-calibration",
    "backend/app/scripts/stage_ad_review_proposal.py",
    "backend/app/scripts/verify_ad_staging_concurrency.py",
    "backend/app/services/ad_extraction.py",
    "backend/app/api/routes/ads.py",
    "backend/app/schemas/ads.py",
    "backend/tests/test_ad_ingestion.py",
    "backend/tests/test_full_product_readiness.py",
    "scripts/verify-t081-postgres-migrations.sh",
    "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx",
    "frontend/paprnav-frontend/src/lib/api.ts",
    ".ai/review-runs/T081-CAL-2024-14-03"
  ],
  "scopeFingerprint": "b6b44d14b7dbd92bdafddd76c32acdca3002edb5789b3ad50057ec2f3f7ed55b",
  "files": [
    {
      "path": ".ai/ad-calibration/1998-17-11.requirements.json",
      "status": "A ",
      "size": 4467,
      "sha256": "6380048e8728390feb8be612ec44909fee3ccab8e39989f653d6032cfc91088d",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/2002-13-04.requirements.json",
      "status": "A ",
      "size": 3269,
      "sha256": "86c747eb7fc1e40e5d49bf67f234363823d94e5a746c30b0b737ef6390a7acac",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/2008-26-10.requirements.json",
      "status": "A ",
      "size": 9386,
      "sha256": "9f94f62789ab120da20b295b063deca1f996424c8802547abfdefe021f089a32",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/2011-10-09.requirements.json",
      "status": "A ",
      "size": 4190,
      "sha256": "7b6ae8b5b897b633c8feb728b5cd64a3647717c4235e30e4b7dce973d5111928",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/2024-14-03.requirements.json",
      "status": "A ",
      "size": 2199,
      "sha256": "bcc539a3016ded3f07797068eae7fa553949db9dc4182453b3e6e037c9d2fad5",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/2024-14-03.v3.proposal.json",
      "status": "??",
      "size": 43270,
      "sha256": "25a7cd3f7a7d16da76323ec5e2850c9f8d0aee370007647cd2d4800662cd2022",
      "readStatus": "readable"
    },
    {
      "path": ".ai/ad-calibration/README.md",
      "status": "AM",
      "size": 7901,
      "sha256": "16723a1915b4f89d9d66c4ff326bad7b0730402aaff464f7b3b1ebdc5bdbd9a5",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": "MM",
      "size": 47125,
      "sha256": "3d4d3d93acefb0280d1feec7250b350899a83e8b2b6274bc5d5f752da76962dd",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/schemas/ads.py",
      "status": "MM",
      "size": 6088,
      "sha256": "db193642fdbde4ab58c1adef4ccb45200f4b145103e33a9b397db37038c4b1d1",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/scripts/stage_ad_review_proposal.py",
      "status": "AM",
      "size": 16052,
      "sha256": "b968fdd0cdb2148cbd0d7dd3e1cf24b69f2739d8ba38df8b19254ed161de2e72",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/scripts/verify_ad_staging_concurrency.py",
      "status": "??",
      "size": 9866,
      "sha256": "2a4671f770b46b7b705b9001903f7bbfb075f95e47764749655f20ced4a7087e",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/ad_extraction.py",
      "status": "MM",
      "size": 92165,
      "sha256": "cf735b132056f01efba87ebaed39e8508d0c832778b75fdd09e3b6b86cfd5fcf",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_ingestion.py",
      "status": "MM",
      "size": 73391,
      "sha256": "813ffd03aa333590eec54e4e00a0702d28591053bd3da97c7e83f68404dddd56",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_full_product_readiness.py",
      "status": "MM",
      "size": 26489,
      "sha256": "c7f226d2b0e906159867af25a6e533f73488a0d05223acbfd51df80b64a48f14",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx",
      "status": "AM",
      "size": 18068,
      "sha256": "05016ef809630e8f478172a8ad8f915203d6020cc87bb4ad2aff1b84730fbf9b",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": "MM",
      "size": 23365,
      "sha256": "fb7bacef2623756502737cdba9ebb756c3dc3e48ad5d54eec9869bee9dcad232",
      "readStatus": "readable"
    },
    {
      "path": "scripts/verify-t081-postgres-migrations.sh",
      "status": "AM",
      "size": 11505,
      "sha256": "62529d44970ec8232c143e3d6e82a6f35e38a3842146716a05fa5843b730973a",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".agents/skills/adversarial-review/SKILL.md",
      "status": "A "
    },
    {
      "path": ".agents/skills/adversarial-review/agents/openai.yaml",
      "status": "A "
    },
    {
      "path": ".agents/skills/adversarial-review/references/checklists.md",
      "status": "A "
    },
    {
      "path": ".agents/skills/adversarial-review/references/severity.md",
      "status": "A "
    },
    {
      "path": ".ai/AD_APPLICABILITY_SCHEMA_REVIEW.md",
      "status": "A "
    },
    {
      "path": ".ai/AD_SOURCE_PROOF_2026-08-04.md",
      "status": "M "
    },
    {
      "path": ".ai/API_CONTRACT.md",
      "status": "M "
    },
    {
      "path": ".ai/CLAUDE_REVIEWER.md",
      "status": "M "
    },
    {
      "path": ".ai/DATA_MODEL.md",
      "status": "M "
    },
    {
      "path": ".ai/GOAL_TASKS.md",
      "status": "M "
    },
    {
      "path": ".ai/LOCAL_MVP_DEMO.md",
      "status": "M "
    },
    {
      "path": ".ai/PROVIDER_REFERENCES.md",
      "status": "M "
    },
    {
      "path": ".ai/REVIEW_PROCESS.md",
      "status": "A "
    },
    {
      "path": ".ai/agents/ADVERSARIAL_REVIEWER.md",
      "status": "A "
    },
    {
      "path": ".ai/agents/BUILDER.md",
      "status": "A "
    },
    {
      "path": ".ai/agents/CLAUDE_CRITIC.md",
      "status": "A "
    },
    {
      "path": ".ai/agents/COORDINATOR.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-closure-final.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-closure-staged.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-design-closure-1.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-design-final.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-design-initial.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-implementation-closure-1.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-implementation-final.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/adversarial-implementation-initial.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/claude-external-critic-20260823T163719Z.findings.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/claude-external-critic-20260823T163719Z.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/closure.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/decision.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/findings.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/latest",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/manifest.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/review-packet.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/reviews.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/T081/state.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-closure-attempt-1.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-closure-attempt-2.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-closure-attempt-3.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-closure-final.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-design.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-implementation-attempt-1.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-implementation-final.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/adversarial-implementation.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/claude-external-critic-20260823T003808Z.findings.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/claude-external-critic-20260823T003808Z.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/claude-findings-implementation-closure.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/closure.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/decision.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/findings.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/latest",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/manifest.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/review-packet.md",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/reviews.json",
      "status": "A "
    },
    {
      "path": ".ai/review-runs/review-infrastructure/state.json",
      "status": "A "
    },
    {
      "path": ".ai/review-templates/CLOSURE_REPORT.md",
      "status": "A "
    },
    {
      "path": ".ai/review-templates/DECISION_PACKET.md",
      "status": "A "
    },
    {
      "path": ".ai/review-templates/FINDINGS.json.schema",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-remediation-closure-20260822.md",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-reviewer-calibration-20260822.md",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-schema-data-20260822.md",
      "status": "A "
    },
    {
      "path": ".gitignore",
      "status": "M "
    },
    {
      "path": "AGENTS.md",
      "status": "A "
    },
    {
      "path": "backend/README.md",
      "status": "M "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0021_add_ad_applicability_v3.py",
      "status": "A "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0022_harden_ad_review_materialization.py",
      "status": "A "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0023_backfill_ad_v3_amoc_envelope.py",
      "status": "A "
    },
    {
      "path": "backend/app/db/migrations/versions/20260823_0024_bind_signed_ad_materialization.py",
      "status": "A "
    },
    {
      "path": "backend/app/models/core.py",
      "status": "M "
    },
    {
      "path": "backend/app/scripts/audit_ad_review_evidence.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/correct_approved_ad_review.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/prepare_ad_compliance_reviews.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/seed_dev.py",
      "status": "M "
    },
    {
      "path": "backend/app/scripts/verify_ad_correction_workflow.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/verify_ad_review_concurrency.py",
      "status": "A "
    },
    {
      "path": "backend/app/services/ad_applicability.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_compliance_population.py",
      "status": "A "
    },
    {
      "path": "backend/app/services/ad_coverage.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_matching.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_recurrence.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_release.py",
      "status": "A "
    },
    {
      "path": "backend/docker-compose.yml",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_coverage.py",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_recurrence.py",
      "status": "M "
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/logbook/[nNumber]/page.tsx",
      "status": "M "
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/page.tsx",
      "status": "M "
    },
    {
      "path": "scripts/advance-review-run.py",
      "status": "A "
    },
    {
      "path": "scripts/build-review-packet.py",
      "status": "A "
    },
    {
      "path": "scripts/claude-review.env.example",
      "status": "M "
    },
    {
      "path": "scripts/claude-review.sh",
      "status": "M "
    },
    {
      "path": "scripts/create-review-run.sh",
      "status": "A "
    },
    {
      "path": "scripts/extract-claude-findings.py",
      "status": "A "
    },
    {
      "path": "scripts/record-review.py",
      "status": "A "
    },
    {
      "path": "scripts/validate-review-run.py",
      "status": "A "
    },
    {
      "path": "scripts/verify-review-packet.py",
      "status": "A "
    }
  ],
  "outOfScopeReason": "The working tree includes the already-reviewed staged T081 implementation baseline; closure is limited to the AD 2024-14-03 controlled human-calibration slice and the listed implementation and review artifacts."
}
```

## Diff against base

```diff
diff --git a/.ai/ad-calibration/1998-17-11.requirements.json b/.ai/ad-calibration/1998-17-11.requirements.json
new file mode 100644
index 0000000..790a637
--- /dev/null
+++ b/.ai/ad-calibration/1998-17-11.requirements.json
@@ -0,0 +1,84 @@
+[
+  {
+    "requirementKey": "a-applicability-determination",
+    "requirementType": "conditional",
+    "actionText": "Within 10 hours time in service after the effective date of this AD, determine if this AD applies, as follows:",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 10,
+        "unit": "hours",
+        "anchorKind": "effective_date",
+        "sourceText": "Within 10 hours time in service after the effective date of this AD"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "Engine repair required crankshaft removal between February 1, 1995 and December 31, 1997.",
+      "If the crankshaft repairer cannot be determined, compliance is required."
+    ],
+    "terminatingAction": "No further action is required if the engine was not repaired in the specified period or the crankshaft was not repaired by Nelson Balancing Service.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_9e7cba005b4c4529a699537f4c64940c",
+        "pageNumber": 22,
+        "text": "Within 10 hours time in service after the effective date of this AD, determine if this AD applies, as follows:"
+      }
+    ],
+    "confidence": 0.88,
+    "uncertaintyReasons": [
+      "Confirm whether applicability determinations should remain requirements or be represented only as applicability predicates."
+    ]
+  },
+  {
+    "requirementKey": "b-inspect-or-remove-crankshaft",
+    "requirementType": "alternative",
+    "actionText": "Perform a visual inspection as defined in paragraph (b)(2) of this AD, magnetic particle inspection, and a dimensional check of the crankshaft journals, or remove from service affected crankshafts and replace with serviceable parts.",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 10,
+        "unit": "hours",
+        "anchorKind": "effective_date",
+        "sourceText": "Within 10 hours time in service after the effective date of this AD"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "alternative",
+    "conditions": [
+      "The applicability determination does not establish that no further action is required."
+    ],
+    "terminatingAction": "Removal from service and replacement with a serviceable crankshaft satisfies this alternative obligation.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_9e7cba005b4c4529a699537f4c64940c",
+        "pageNumber": 22,
+        "text": "Perform a visual inspection as defined in paragraph (b)(2) of this AD, magnetic particle inspection, and a dimensional check of the crankshaft journals, or remove from service affected crankshafts and replace with serviceable parts."
+      }
+    ],
+    "confidence": 0.94,
+    "uncertaintyReasons": []
+  },
+  {
+    "requirementKey": "b-3-failed-inspection-correction",
+    "requirementType": "alternative",
+    "actionText": "Replace any crankshaft that fails the visual inspection, magnetic particle inspection, or the dimensional check with a serviceable crankshaft, unless the crankshaft can be reworked to bring it in compliance with: (i) All the overhaul requirements of the appropriate TCM or LYC Overhaul/Maintenance Manuals; or (ii) All of the FAA-approved requirements for any repair station which currently has approval for limits other than those in the appropriate TCM or LYC Overhaul/Maintenance Manuals.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "alternative",
+    "conditions": [
+      "The crankshaft fails the visual inspection, magnetic-particle inspection, or dimensional check."
+    ],
+    "terminatingAction": "Replacement with a serviceable crankshaft or qualifying rework resolves the failed-inspection condition.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_9e7cba005b4c4529a699537f4c64940c",
+        "pageNumber": 22,
+        "text": "Replace any crankshaft that fails the visual inspection, magnetic particle inspection, or the dimensional check with a serviceable crankshaft, unless the crankshaft can be reworked to bring it in compliance with: (i) All the overhaul requirements of the appropriate TCM or LYC Overhaul/Maintenance Manuals; or (ii) All of the FAA-approved requirements for any repair station which currently has approval for limits other than those in the appropriate TCM or LYC Overhaul/Maintenance Manuals."
+      }
+    ],
+    "confidence": 0.92,
+    "uncertaintyReasons": []
+  }
+]
diff --git a/.ai/ad-calibration/2002-13-04.requirements.json b/.ai/ad-calibration/2002-13-04.requirements.json
new file mode 100644
index 0000000..1c75dbe
--- /dev/null
+++ b/.ai/ad-calibration/2002-13-04.requirements.json
@@ -0,0 +1,76 @@
+[
+  {
+    "requirementKey": "a-magneto-replacement",
+    "requirementType": "one_time",
+    "actionText": "Replace any magneto that has a SN of 99110001 through 99129999, inclusive, with a magneto that does not have a serial number in that range.",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 10,
+        "unit": "hours",
+        "anchorKind": "effective_date",
+        "sourceText": "Compliance with this AD is required within 10 flight hours after the effective date of this AD"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "Installed magneto serial number is 99110001 through 99129999 inclusive."
+    ],
+    "terminatingAction": "Replacement with a magneto outside the affected serial-number range satisfies the replacement obligation, subject to the separate installation prohibition.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_2c509af5b8df4eb2aa1cbc2f2563d54d",
+        "pageNumber": 2,
+        "text": "Replace any magneto that has a SN of 99110001 through 99129999, inclusive, with a magneto that does not have a serial number in that range."
+      }
+    ],
+    "confidence": 0.9,
+    "uncertaintyReasons": [
+      "Confirm whether flight hours should map to total-time or tach-hours in the normalized due-state model."
+    ]
+  },
+  {
+    "requirementKey": "b-missing-stop-pin-engine-inspection",
+    "requirementType": "conditional",
+    "actionText": "Inspect each removed magneto to verify that the impulse coupling stop pin is present. If the pin is missing, do the following:",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "The impulse-coupling stop pin is missing.",
+      "Follow paragraph (b)(1) for C-125, C145, O-300, IO-360, and TSIO-360 series engines or paragraph (b)(2) for LTSIO-520-AE series engines."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_2c509af5b8df4eb2aa1cbc2f2563d54d",
+        "pageNumber": 2,
+        "text": "Inspect each removed magneto to verify that the impulse coupling stop pin is present. If the pin is missing, do the following:"
+      }
+    ],
+    "confidence": 0.82,
+    "uncertaintyReasons": [
+      "Determine whether the two engine-family branches need separate requirement objects for applicability and materialization."
+    ]
+  },
+  {
+    "requirementKey": "c-installation-prohibition",
+    "requirementType": "installation_prohibition",
+    "actionText": "After the effective date of this AD, do not install any Unison Industries magnetos, model 6314, 6324, or 6364 that have a SN of 99110001 through 99129999 inclusive, on any engine.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_2c509af5b8df4eb2aa1cbc2f2563d54d",
+        "pageNumber": 2,
+        "text": "After the effective date of this AD, do not install any Unison Industries magnetos, model 6314, 6324, or 6364 that have a SN of 99110001 through 99129999 inclusive, on any engine."
+      }
+    ],
+    "confidence": 0.96,
+    "uncertaintyReasons": []
+  }
+]
diff --git a/.ai/ad-calibration/2008-26-10.requirements.json b/.ai/ad-calibration/2008-26-10.requirements.json
new file mode 100644
index 0000000..b7f6f42
--- /dev/null
+++ b/.ai/ad-calibration/2008-26-10.requirements.json
@@ -0,0 +1,205 @@
+[
+  {
+    "requirementKey": "e-1-non-ifr-inspection",
+    "requirementType": "one_time",
+    "actionText": "For all affected airplanes that are not equipped for flight under instrument flight rules (IFR): Inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port.",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 100,
+        "unit": "hours",
+        "anchorKind": "effective_date",
+        "sourceText": "Within the next 100 hours time-in-service after January 5, 2009"
+      },
+      {
+        "metric": "calendar",
+        "value": 4,
+        "unit": "months",
+        "anchorKind": "effective_date",
+        "sourceText": "or within the next 4 months after January 5, 2009, whichever occurs first"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "whichever_first",
+    "conditions": [
+      "Affected airplane is not equipped for IFR flight."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 4,
+        "text": "For all affected airplanes that are not equipped for flight under instrument flight rules (IFR): Inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port."
+      }
+    ],
+    "confidence": 0.92,
+    "uncertaintyReasons": [
+      "Confirm how a usage-hour allowance anchored to a calendar effective date should map into the current threshold model."
+    ]
+  },
+  {
+    "requirementKey": "e-2-ifr-immediate-alternative",
+    "requirementType": "alternative",
+    "actionText": "Inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port; or fabricate a placard that incorporates the following words (using at least 1/8-inch letters) and install this placard on the instrument panel within the pilot's clear view: ‘IFR OPERATION IS PROHIBITED’ and ‘USE OF THE ALTERNATE STATIC AIR SOURCE IS PROHIBITED.’",
+    "initialThresholds": [
+      {
+        "metric": "calendar",
+        "value": 10,
+        "unit": "days",
+        "anchorKind": "effective_date",
+        "sourceText": "Inspect within the next 10 days after January 5, 2009; or install placards before further flight"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "alternative",
+    "conditions": [
+      "Affected airplane is equipped for IFR flight."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 4,
+        "text": "Inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port; or"
+      },
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 4,
+        "text": "Fabricate a placard that incorporates the following words (using at least 1/8-inch letters) and install this placard on the instrument panel within the pilot's clear view: ‘IFR OPERATION IS PROHIBITED’ and ‘USE OF THE ALTERNATE STATIC AIR SOURCE IS PROHIBITED.’"
+      }
+    ],
+    "confidence": 0.78,
+    "uncertaintyReasons": [
+      "The current schema cannot bind a distinct deadline to each branch of one alternative requirement; decide whether alternative groups need first-class branch objects."
+    ]
+  },
+  {
+    "requirementKey": "e-3-temporary-placard-follow-up",
+    "requirementType": "conditional",
+    "actionText": "For all affected airplanes that are equipped for flight under instrument flight rules (IFR): If placards were installed in accordance with paragraph (e)(2)(ii) of this AD, inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port.",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 100,
+        "unit": "hours",
+        "anchorKind": "effective_date",
+        "sourceText": "Within the next 100 hours TIS after January 5, 2009"
+      },
+      {
+        "metric": "calendar",
+        "value": 4,
+        "unit": "months",
+        "anchorKind": "effective_date",
+        "sourceText": "or within the next 4 months after January 5, 2009, whichever occurs first"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "whichever_first",
+    "conditions": [
+      "Placards were installed under paragraph (e)(2)(ii)."
+    ],
+    "terminatingAction": "Complete the inspection and remove the temporary placards before further flight.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 4,
+        "text": "For all affected airplanes that are equipped for flight under instrument flight rules (IFR): If placards were installed in accordance with paragraph (e)(2)(ii) of this AD, inspect the alternate static air source selector valve to assure that the part number identification placard is not obstructing the port."
+      }
+    ],
+    "confidence": 0.88,
+    "uncertaintyReasons": []
+  },
+  {
+    "requirementKey": "e-4-obstructed-port-correction",
+    "requirementType": "conditional",
+    "actionText": "For all affected airplanes: If the alternate static air source selector valve port is found obstructed by the part number identification placard during the inspection required in paragraphs (e)(1), (e)(2)(i), and (e)(3) of this AD, remove the placard from the valve body, discard the placard, and assure that the port is open and unobstructed.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "The selector-valve port is obstructed by the part-number identification placard."
+    ],
+    "terminatingAction": "Removal of the obstructing placard and verification of an open port resolves this finding.",
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 4,
+        "text": "For all affected airplanes: If the alternate static air source selector valve port is found obstructed by the part number identification placard during the inspection required in paragraphs (e)(1), (e)(2)(i), and (e)(3) of this AD, remove the placard from the valve body, discard the placard, and assure that the port is open and unobstructed."
+      }
+    ],
+    "confidence": 0.96,
+    "uncertaintyReasons": []
+  },
+  {
+    "requirementKey": "e-5-replacement-valve-installation",
+    "requirementType": "installation_prohibition",
+    "actionText": "For all affected airplanes: When a replacement valve is needed, only install a P/N 2013142-18 alternate static air source selector valve that has been inspected and the port is found free from obstruction.",
+    "initialThresholds": [
+      {
+        "metric": "calendar",
+        "value": 10,
+        "unit": "days",
+        "anchorKind": "effective_date",
+        "sourceText": "As of 10 days after January 5, 2009"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "A replacement alternate static-air-source selector valve is needed."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 5,
+        "text": "For all affected airplanes: When a replacement valve is needed, only install a P/N 2013142-18 alternate static air source selector valve that has been inspected and the port is found free from obstruction."
+      }
+    ],
+    "confidence": 0.94,
+    "uncertaintyReasons": []
+  },
+  {
+    "requirementKey": "f-obstruction-report",
+    "requirementType": "conditional",
+    "actionText": "Report to the FAA the results of the inspection required by this AD where an obstruction was found.",
+    "initialThresholds": [
+      {
+        "metric": "calendar",
+        "value": 10,
+        "unit": "days",
+        "anchorKind": "last_compliance",
+        "sourceText": "Within 10 days after the inspection or 10 days after the effective date of this AD, whichever occurs later"
+      },
+      {
+        "metric": "calendar",
+        "value": 10,
+        "unit": "days",
+        "anchorKind": "effective_date",
+        "sourceText": "Within 10 days after the inspection or 10 days after the effective date of this AD, whichever occurs later"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "whichever_later",
+    "conditions": [
+      "An inspection required by the AD found an obstruction."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_37922ee632e24a23a5f0ecd1aa4809fe",
+        "pageNumber": 5,
+        "text": "Report to the FAA the results of the inspection required by this AD where an obstruction was found."
+      },
+      {
+        "sourceDocumentId": "asd_3c7aa0ef184646e2b32b1171e44b4f7a",
+        "pageNumber": 2,
+        "text": "On page 78943, in the second column, in paragraph (f)(2), on line 3, change 1804 to 1801."
+      }
+    ],
+    "confidence": 0.86,
+    "uncertaintyReasons": [
+      "Confirm whether a reporting deadline belongs in aircraft due-state materialization or in a separate administrative-obligation class."
+    ]
+  }
+]
diff --git a/.ai/ad-calibration/2011-10-09.requirements.json b/.ai/ad-calibration/2011-10-09.requirements.json
new file mode 100644
index 0000000..946ab7a
--- /dev/null
+++ b/.ai/ad-calibration/2011-10-09.requirements.json
@@ -0,0 +1,79 @@
+[
+  {
+    "requirementKey": "g-recurring-seat-system-inspection",
+    "requirementType": "recurring",
+    "actionText": "For all airplanes, to address the unsafe condition described in paragraph (e) of this AD, you must do the following actions on the seat rails; seat rollers, washers, and axle bolts or bushings; seat roller housings and the tangs; and lock pin springs, unless already done, initially within the next 100 hours time-in-service (TIS) after the last inspection done following AD 87-20-03 R2 or within the next 12 calendar months after the effective date of this AD, whichever occurs first. Repetitively thereafter do the actions at intervals not to exceed every 100 hours TIS or every 12 months, whichever occurs first:",
+    "initialThresholds": [
+      {
+        "metric": "total_time_hours",
+        "value": 100,
+        "unit": "hours",
+        "anchorKind": "last_compliance",
+        "sourceText": "Initially within the next 100 hours time-in-service after the last inspection done following AD 87-20-03 R2"
+      },
+      {
+        "metric": "calendar",
+        "value": 12,
+        "unit": "months",
+        "anchorKind": "effective_date",
+        "sourceText": "or within the next 12 calendar months after the effective date of this AD, whichever occurs first"
+      }
+    ],
+    "recurringTriggers": [
+      {
+        "metric": "total_time_hours",
+        "value": 100,
+        "unit": "hours",
+        "anchorKind": "last_compliance",
+        "sourceText": "at intervals not to exceed every 100 hours TIS"
+      },
+      {
+        "metric": "calendar",
+        "value": 12,
+        "unit": "months",
+        "anchorKind": "last_compliance",
+        "sourceText": "or every 12 months, whichever occurs first"
+      }
+    ],
+    "combinationLogic": "whichever_first",
+    "conditions": [],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_dca1a807cdab483bbb876bfac5af99b7",
+        "pageNumber": 5,
+        "text": "For all airplanes, to address the unsafe condition described in paragraph (e) of this AD, you must do the following actions on the seat rails; seat rollers, washers, and axle bolts or bushings; seat roller housings and the tangs; and lock pin springs, unless already done, initially within the next 100 hours time-in-service (TIS) after the last inspection done following AD 87-20-03 R2 or within the next 12 calendar months after the effective date of this AD, whichever occurs first. Repetitively thereafter do the actions at intervals not to exceed every 100 hours TIS or every 12 months, whichever occurs first:"
+      }
+    ],
+    "confidence": 0.9,
+    "uncertaintyReasons": [
+      "Confirm whether each paragraph (g)(1) through (g)(10) corrective branch should materialize as a separate conditional requirement."
+    ]
+  },
+  {
+    "requirementKey": "g-10-locking-pin-correction",
+    "requirementType": "conditional",
+    "actionText": "If engagement of any of the seat locking pins measures less than 0.15 of an inch, before further flight, replace or repair any seat components necessary to achieve a seat pin engagement of a minimum of 0.15 of an inch. Repair or replacement of necessary seat components does not terminate the repetitive actions required in paragraph (g) of this AD.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [
+      "Any seat locking pin engagement measures less than 0.15 inch."
+    ],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_dca1a807cdab483bbb876bfac5af99b7",
+        "pageNumber": 8,
+        "text": "If engagement of any of the seat locking pins measures less than 0.15 of an inch, before further flight, replace or repair any seat components necessary to achieve a seat pin engagement of a minimum of 0.15 of an inch."
+      },
+      {
+        "sourceDocumentId": "asd_dca1a807cdab483bbb876bfac5af99b7",
+        "pageNumber": 8,
+        "text": "Repair or replacement of necessary seat components does not terminate the repetitive actions required in paragraph (g) of this AD."
+      }
+    ],
+    "confidence": 0.94,
+    "uncertaintyReasons": []
+  }
+]
diff --git a/.ai/ad-calibration/2024-14-03.requirements.json b/.ai/ad-calibration/2024-14-03.requirements.json
new file mode 100644
index 0000000..9ab7e0a
--- /dev/null
+++ b/.ai/ad-calibration/2024-14-03.requirements.json
@@ -0,0 +1,48 @@
+[
+  {
+    "requirementKey": "g-software-update",
+    "requirementType": "one_time",
+    "actionText": "Within 12 months after the effective date of this AD, update the Garmin GFC 500 Autopilot System software applicable to your airplane to a version that is not 8.01 or earlier for the G5, not version 9.01 or earlier for the G3X Touch, and not version 2.59 or earlier for the GI 275.",
+    "initialThresholds": [
+      {
+        "metric": "calendar",
+        "value": 12,
+        "unit": "months",
+        "anchorKind": "effective_date",
+        "sourceText": "Within 12 months after the effective date of this AD"
+      }
+    ],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0",
+        "pageNumber": 5,
+        "text": "Within 12 months after the effective date of this AD, update the Garmin GFC 500 Autopilot System software applicable to your airplane to a version that is not 8.01 or earlier for the G5, not version 9.01 or earlier for the G3X Touch, and not version 2.59 or earlier for the GI 275."
+      }
+    ],
+    "confidence": 0.98,
+    "uncertaintyReasons": []
+  },
+  {
+    "requirementKey": "h-installation-prohibition",
+    "requirementType": "installation_prohibition",
+    "actionText": "As of the effective date of this AD, do not install Garmin GFC 500 Autopilot System Software that is version 8.01 or earlier for the G5, version 9.01 or earlier for the G3X Touch, or version 2.59 or earlier for the GI 275, on any airplane.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": [],
+    "terminatingAction": null,
+    "citations": [
+      {
+        "sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0",
+        "pageNumber": 5,
+        "text": "As of the effective date of this AD, do not install Garmin GFC 500 Autopilot System Software that is version 8.01 or earlier for the G5, version 9.01 or earlier for the G3X Touch, or version 2.59 or earlier for the GI 275, on any airplane."
+      }
+    ],
+    "confidence": 0.98,
+    "uncertaintyReasons": []
+  }
+]
diff --git a/.ai/ad-calibration/README.md b/.ai/ad-calibration/README.md
new file mode 100644
index 0000000..75de9de
--- /dev/null
+++ b/.ai/ad-calibration/README.md
@@ -0,0 +1,115 @@
+# AD Compliance Extraction Calibration Set
+
+Status: the linked records are new pending v3 reviews. The
+`*.requirements.json` files are retained v2 requirement calibration evidence;
+they cannot publish by themselves. AD 2024-14-03's earlier approval is
+quarantined because its v2 applicability was materialized as disconnected
+manufacturer/model strings. The remaining four were never completed.
+
+The shortlist deliberately covers five different compliance structures from the
+14 source-verified reviews. The requirement arrays remain useful source-faithful
+drafts, but a publishable v3 review must also contain complete
+`applicabilityGroups` and every requirement must add
+`applicabilityGroupKeys`. The linked source-bound v3 reviews are already staged;
+open the relevant link and edit the complete JSON object in the GUI. The GUI remains the authoritative place to
+validate and publish a complete extraction. See
+[`AD_APPLICABILITY_SCHEMA_REVIEW.md`](../AD_APPLICABILITY_SCHEMA_REVIEW.md) for
+the field rules and PostgreSQL mapping.
+
+## Shortlist
+
+| Pattern | Current v3 review | Complete v3 proposal | Requirement calibration draft |
+| --- | --- | --- | --- |
+| One-time calendar action plus installation prohibition | [AD 2024-14-03 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_94f8a23dd22a457faf007aa588601018) | [2024-14-03.v3.proposal.json](2024-14-03.v3.proposal.json) — populated in GUI; unresolved OCR, serial-scope, and Note 1 method-schema issues intentionally block approval | [2024-14-03.requirements.json](2024-14-03.requirements.json) |
+| Recurring 100-hour/12-month whichever-first inspection; corrective work does not terminate recurrence | [AD 2011-10-09 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_89e2c6f1798743a49fb249c407895620) | Not yet built | [2011-10-09.requirements.json](2011-10-09.requirements.json) |
+| Conditional engine-family branches plus installation prohibition | [AD 2002-13-04 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_d8feca4a3f4a4ceab3974cea332a27f5) | Not yet built | [2002-13-04.requirements.json](2002-13-04.requirements.json) |
+| Applicability determination, inspect-or-remove alternative, and repair-or-replace branch | [AD 98-17-11 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_c317487e391740dcade16e4451cf4ae4) | Not yet built | [1998-17-11.requirements.json](1998-17-11.requirements.json) |
+| Different IFR/non-IFR paths, whichever-first/later thresholds, temporary placarding, corrective action, installation control, and reporting | [AD 2008-26-10 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_d75c981204fa4795a5f3b15e5ea8394e) | Not yet built | [2008-26-10.requirements.json](2008-26-10.requirements.json) |
+
+## Retained source PDFs
+
+Use **Open in browser** while the local API is running and you are signed in as
+a Paprnav administrator. **Open local file** opens the same retained artifact
+directly from the workspace.
+
+### AD 2024-14-03
+
+- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_63da3892cf8b4124b49e4066c57858a0/content)
+- [Open local file: 2024-15529.pdf](../../backend/.data/ad-sources/federal_register/c7/c7be1903331497057fb55faf9ed5994e61774d8acd287cbbc1cb0da5df423b89/2024-15529.pdf)
+- Source document: `asd_63da3892cf8b4124b49e4066c57858a0`
+- SHA-256: `c7be1903331497057fb55faf9ed5994e61774d8acd287cbbc1cb0da5df423b89`
+
+### AD 2011-10-09
+
+- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_dca1a807cdab483bbb876bfac5af99b7/content)
+- [Open local file: 2011-10988.pdf](../../backend/.data/ad-sources/federal_register/cd/cdcf75940451488e47858bd49c40615803325652ef3143d0df4178a95fe577fe/2011-10988.pdf)
+- Source document: `asd_dca1a807cdab483bbb876bfac5af99b7`
+- SHA-256: `cdcf75940451488e47858bd49c40615803325652ef3143d0df4178a95fe577fe`
+
+### AD 2002-13-04
+
+- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_2c509af5b8df4eb2aa1cbc2f2563d54d/content)
+- [Open local file: 02-16174.pdf](../../backend/.data/ad-sources/federal_register/6a/6abbb7724df98bf571ab84e9d58b18f5ef87a0e89aa29817670c17f4461714b7/02-16174.pdf)
+- Source document: `asd_2c509af5b8df4eb2aa1cbc2f2563d54d`
+- SHA-256: `6abbb7724df98bf571ab84e9d58b18f5ef87a0e89aa29817670c17f4461714b7`
+
+### AD 98-17-11
+
+- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_9e7cba005b4c4529a699537f4c64940c/content)
+- [Open local file: FR-1998-08-20.pdf](../../backend/.data/ad-sources/govinfo/e8/e86e204d59ad3464f31aac3945b73b03ad60adff6989ec3702a99f2d2fa06374/FR-1998-08-20.pdf)
+- Source document: `asd_9e7cba005b4c4529a699537f4c64940c`
+- SHA-256: `e86e204d59ad3464f31aac3945b73b03ad60adff6989ec3702a99f2d2fa06374`
+
+### AD 2008-26-10
+
+Original final rule:
+
+- [Open original in browser](http://localhost:8000/api/v1/ads/source-documents/asd_37922ee632e24a23a5f0ecd1aa4809fe/content)
+- [Open local original: E8-30465.pdf](../../backend/.data/ad-sources/federal_register/17/177c3ed17897931c0dcb902e2e867fdc7348526441d2885f26f80974402e201f/E8-30465.pdf)
+- Source document: `asd_37922ee632e24a23a5f0ecd1aa4809fe`
+- SHA-256: `177c3ed17897931c0dcb902e2e867fdc7348526441d2885f26f80974402e201f`
+
+2010 correction:
+
+- [Open correction in browser](http://localhost:8000/api/v1/ads/source-documents/asd_3c7aa0ef184646e2b32b1171e44b4f7a/content)
+- [Open local correction: 2010-28579.pdf](../../backend/.data/ad-sources/federal_register/67/676a282adba0fea1ef7ddb87787ce85746ea8eb08b43ac28cf059f7ccff39db2/2010-28579.pdf)
+- Source document: `asd_3c7aa0ef184646e2b32b1171e44b4f7a`
+- SHA-256: `676a282adba0fea1ef7ddb87787ce85746ea8eb08b43ac28cf059f7ccff39db2`
+
+## Review method
+
+1. Open the retained source or stable review link.
+2. Create source-cited `applicabilityGroups`. Keep official manufacturer and
+   model wording in separate fields; preserve model/serial scope, installed-
+   equipment conditions, exceptions, and uncertainty. Add each group key to
+   the requirements it governs.
+3. Compare every draft `actionText`, condition, threshold, trigger, combination
+   rule, terminating-action statement, and citation with the displayed source.
+   Preserve the regulatory wording in `actionText`; put normalized meaning in
+   the other structured fields rather than paraphrasing the action.
+   Treat every existing draft as untrusted calibration input: timing clauses,
+   values, requirement types, and citations must be rechecked against the PDF.
+   Copy the exact timing clause into `sourceText` and preserve its `anchorKind`.
+   Capture the AD's AMOC paragraph in `amocProvisions` rather than an alternative
+   maintenance requirement.
+4. Edit the requirement draft. Do not remove an `uncertaintyReasons` entry until
+   the ambiguity is resolved in the source or the schema/methodology is changed.
+5. Replace the full extraction object's `requirements` value with the reviewed
+   array; never paste a requirements array as the top-level JSON value. The server
+   derives `affectedProducts` and `complianceActions`; do not edit those fields
+   as authoritative data.
+6. Use **Edit, validate & publish** only after the entire directive—not merely
+   the representative calibration passages—has been accounted for.
+
+The first pass should focus on whether the schema can faithfully represent the
+source. It should not be treated as a production approval quota.
+
+Any remaining `uncertaintyReasons` now blocks **Approve & publish**. The record
+remains editable in the GUI so the calibration question can be resolved without
+publishing a partially modeled directive.
+
+AD 2008-26-10 is intentionally reviewed as a two-document source packet. The
+2010 correction removes model 188, corrects the Unsafe Condition paragraph
+label, and changes the reporting address; the original rule contains the full
+compliance table. The review page now retains both bounded sections rather than
+silently choosing one document.
diff --git a/backend/app/api/routes/ads.py b/backend/app/api/routes/ads.py
index 28b4578..e8c0749 100644
--- a/backend/app/api/routes/ads.py
+++ b/backend/app/api/routes/ads.py
@@ -1,9 +1,12 @@
 from __future__ import annotations
 
 from datetime import datetime, timezone
+from pathlib import Path
+from urllib.parse import quote
 
-from fastapi import APIRouter, Depends, HTTPException, status
-from sqlalchemy import select
+from fastapi import APIRouter, Depends, HTTPException, Query, status
+from fastapi.responses import Response
+from sqlalchemy import or_, select, update
 from sqlalchemy.orm import Session, selectinload
 
 from app.api.deps import get_current_user
@@ -12,6 +15,7 @@ from app.api.routes.aircraft import (
     ensure_maintenance_review_access,
     get_visible_aircraft_or_404,
 )
+from app.core.config import get_settings
 from app.db.session import get_db
 from app.models.core import (
     ADDiscoveryRecord,
@@ -19,11 +23,17 @@ from app.models.core import (
     ADCoverageSubscription,
     ADExtraction,
     ADExtractionReview,
+    ADExtractionReviewDecision,
+    ADPublication,
+    ADSourceDocument,
     ADMatchAdjudication,
+    ADMatchDueStateLink,
     ADMatchEvidence,
     ADMatchResult,
     ADTargetApplicability,
+    AircraftADDueState,
     AirworthinessDirective,
+    ApplicabilityTarget,
     LogbookEntry,
     ProductEvent,
     User,
@@ -33,6 +43,8 @@ from app.schemas.ads import (
     ADExtractionResponse,
     ADExtractionReviewListResponse,
     ADExtractionReviewResponse,
+    ADProposalProvenanceResponse,
+    ADSourceDocumentResponse,
     ADMatchAdjudicationResponse,
     ADMatchAdjudicationDecisionRequest,
     ADMatchAdjudicationDecisionResponse,
@@ -46,9 +58,22 @@ from app.schemas.ads import (
     ADDueStateResponse,
     ADReviewDecisionRequest,
     ADReviewDecisionResponse,
+    ADDirectiveApplicabilityTargetResponse,
     AirworthinessDirectiveResponse,
 )
-from app.services.ad_extraction import validate_extraction_output
+from app.services.ad_extraction import (
+    bounded_source_document_pages,
+    derive_compliance_action_summaries,
+    ensure_persisted_source_pages,
+    extraction_approval_blockers,
+    extraction_input_hash,
+    official_ad_number,
+    persisted_source_pages,
+    source_evidence_status,
+    structured_output_hash,
+    retained_document_bytes_match,
+    verified_retained_document_bytes,
+)
 from app.services.ad_applicability import populate_applicability_from_extraction
 from app.services.ad_coverage import summarize_aircraft_coverage_status
 from app.services.ad_coverage import resolve_aircraft_ad_coverage
@@ -58,13 +83,62 @@ from app.services.ad_matching import (
     invalidate_aircraft_match_results,
 )
 from app.services.ad_recurrence import materialize_requirements_from_extraction
+from app.services.ad_release import (
+    extraction_has_signed_release,
+    released_extraction_for_directive,
+    released_signed_extractions,
+)
+from app.services.ad_extraction import full_text_pages_for_extraction
 from app.services.ad_recurrence import due_state_payload
 from app.services.installed_components import component_display_name
 from app.services.observability import record_product_event, record_workflow_status
+from app.services.storage import safe_filename
 
 router = APIRouter(prefix="/api/v1/ads", tags=["airworthiness-directives"])
 
 
+def ensure_ad_extraction_reviewer(user: User) -> None:
+    ensure_platform_admin(user)
+
+
+def is_platform_admin(user: User) -> bool:
+    return any(
+        membership.status == "active" and membership.role == "platform_admin"
+        for membership in user.memberships
+    )
+
+
+@router.get("/source-documents/{source_document_id}/content")
+def open_retained_source_document(
+    source_document_id: str,
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+):
+    ensure_ad_extraction_reviewer(current_user)
+    document = db.scalar(
+        select(ADSourceDocument).where(ADSourceDocument.id == source_document_id)
+    )
+    if document is None:
+        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found")
+    filename = safe_filename(Path(document.storage_key).name or f"{document.id}.pdf")
+    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}
+    settings = get_settings()
+    try:
+        payload = verified_retained_document_bytes(document, settings=settings)
+    except ValueError as exc:
+        raise HTTPException(
+            status_code=status.HTTP_409_CONFLICT,
+            detail="Retained AD source document hash mismatch",
+        ) from exc
+    except Exception as exc:
+        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retained AD source document not found") from exc
+    return Response(
+        content=payload,
+        media_type=document.media_type or "application/octet-stream",
+        headers=headers,
+    )
+
+
 @router.get("/discovery-records", response_model=list[ADDiscoveryRecordResponse])
 def list_discovery_records(
     current_user: User = Depends(get_current_user),
@@ -77,34 +151,232 @@ def list_discovery_records(
 
 @router.get("/directives", response_model=list[AirworthinessDirectiveResponse])
 def list_directives(
+    q: str | None = Query(default=None, max_length=200),
+    ad_number: str | None = Query(default=None, max_length=64),
+    directive_status: str | None = Query(default=None, alias="status", max_length=64),
+    product_type: str | None = Query(default=None, alias="productType", max_length=64),
+    manufacturer: str | None = Query(default=None, max_length=255),
+    model: str | None = Query(default=None, max_length=255),
+    include_unreviewed: bool = Query(default=False, alias="includeUnreviewed"),
+    limit: int = Query(default=200, ge=1, le=500),
     current_user: User = Depends(get_current_user),
     db: Session = Depends(get_db),
 ) -> list[AirworthinessDirectiveResponse]:
-    _ = current_user
-    directives = db.scalars(
-        select(AirworthinessDirective)
-        .options(selectinload(AirworthinessDirective.discovery_record))
-        .order_by(AirworthinessDirective.created_at.desc())
-    ).all()
+    if include_unreviewed and not is_platform_admin(current_user):
+        raise HTTPException(
+            status_code=status.HTTP_403_FORBIDDEN,
+            detail="Paprnav administrator access required for unreleased directives",
+        )
+    statement = select(AirworthinessDirective).options(
+        selectinload(AirworthinessDirective.discovery_record),
+        selectinload(AirworthinessDirective.extractions)
+        .selectinload(ADExtraction.reviews)
+        .selectinload(ADExtractionReview.reviewer)
+        .selectinload(User.memberships),
+        selectinload(AirworthinessDirective.publications).selectinload(
+            ADPublication.source_document
+        ),
+        selectinload(AirworthinessDirective.target_applicabilities).selectinload(
+            ADTargetApplicability.target
+        ),
+    )
+    if not include_unreviewed:
+        statement = statement.where(AirworthinessDirective.review_status == "approved")
+    if q and include_unreviewed:
+        term = f"%{q.strip()}%"
+        statement = statement.where(
+            or_(
+                AirworthinessDirective.title.ilike(term),
+                AirworthinessDirective.ad_number.ilike(term),
+                current_target_exists(search_term=term),
+            )
+        )
+    if ad_number:
+        normalized_number = ad_number.upper().removeprefix("AD ").strip()
+        statement = statement.where(AirworthinessDirective.ad_number.ilike(f"%{normalized_number}%"))
+    if directive_status:
+        statement = statement.where(AirworthinessDirective.status == directive_status)
+    if (product_type or manufacturer or model) and include_unreviewed:
+        statement = statement.where(current_target_exists(
+            product_type=product_type,
+            manufacturer=manufacturer,
+            model=model,
+        ))
+    ordered = statement.order_by(
+        AirworthinessDirective.ad_number.desc(),
+        AirworthinessDirective.created_at.desc(),
+    )
+    if include_unreviewed:
+        ordered = ordered.limit(limit)
+    directives = db.scalars(ordered).all()
+    if not include_unreviewed:
+        released_by_directive = {
+            extraction.directive_id: extraction
+            for extraction in released_signed_extractions(db)
+        }
+        directives = [
+            directive for directive in directives
+            if directive.id in released_by_directive
+        ]
+        directives = [
+            directive
+            for directive in directives
+            if directive_has_verified_release_evidence(directive)
+            and released_directive_matches_query(
+                directive,
+                q=q,
+                product_type=product_type,
+                manufacturer=manufacturer,
+                model=model,
+            )
+        ][:limit]
     return [serialize_directive(directive) for directive in directives]
 
 
+def current_target_exists(
+    *,
+    search_term: str | None = None,
+    product_type: str | None = None,
+    manufacturer: str | None = None,
+    model: str | None = None,
+):
+    target_query = (
+        select(ADTargetApplicability.id)
+        .join(
+            ApplicabilityTarget,
+            ApplicabilityTarget.id == ADTargetApplicability.target_id,
+        )
+        .where(
+            ADTargetApplicability.directive_id == AirworthinessDirective.id,
+            ADTargetApplicability.status == "current",
+        )
+    )
+    if search_term:
+        target_query = target_query.where(or_(
+            ApplicabilityTarget.make.ilike(search_term),
+            ApplicabilityTarget.model.ilike(search_term),
+            ApplicabilityTarget.product_type.ilike(search_term),
+            ApplicabilityTarget.product_subtype.ilike(search_term),
+        ))
+    if product_type:
+        target_query = target_query.where(ApplicabilityTarget.product_type.ilike(product_type.strip()))
+    if manufacturer:
+        target_query = target_query.where(ApplicabilityTarget.make.ilike(f"%{manufacturer.strip()}%"))
+    if model:
+        target_query = target_query.where(ApplicabilityTarget.model.ilike(f"%{model.strip()}%"))
+    return target_query.exists()
+
+
+def directive_has_verified_release_evidence(directive: AirworthinessDirective) -> bool:
+    return released_extraction_for_directive(directive) is not None
+
+
+def released_directive_matches_query(
+    directive: AirworthinessDirective,
+    *,
+    q: str | None,
+    product_type: str | None,
+    manufacturer: str | None,
+    model: str | None,
+) -> bool:
+    extraction = released_extraction_for_directive(directive)
+    if extraction is None:
+        return False
+    targets = [
+        item.target
+        for item in directive.target_applicabilities
+        if item.status == "current"
+        and item.source_extraction_id == extraction.id
+        and item.target is not None
+    ]
+    if q:
+        needle = q.strip().lower()
+        searchable = [directive.title, directive.ad_number]
+        searchable.extend(
+            value
+            for target in targets
+            for value in (
+                target.make,
+                target.model,
+                target.product_type,
+                target.product_subtype,
+            )
+        )
+        if not any(needle in str(value or "").lower() for value in searchable):
+            return False
+    if product_type and not any(
+        target.product_type.lower() == product_type.strip().lower()
+        for target in targets
+    ):
+        return False
+    if manufacturer and not any(
+        manufacturer.strip().lower() in str(target.make or "").lower()
+        for target in targets
+    ):
+        return False
+    if model and not any(
+        model.strip().lower() in str(target.model or "").lower()
+        for target in targets
+    ):
+        return False
+    return True
+
+
 @router.get("/extraction-reviews", response_model=ADExtractionReviewListResponse)
 def list_extraction_reviews(
+    offset: int = Query(default=0, ge=0),
+    limit: int = Query(default=1, ge=1, le=20),
+    review_id: str | None = Query(default=None, alias="reviewId", max_length=64),
     current_user: User = Depends(get_current_user),
     db: Session = Depends(get_db),
 ) -> ADExtractionReviewListResponse:
-    ensure_platform_admin(current_user)
-    reviews = db.scalars(
+    ensure_ad_extraction_reviewer(current_user)
+    all_reviews = db.scalars(
         select(ADExtractionReview)
         .options(
             selectinload(ADExtractionReview.extraction)
             .selectinload(ADExtraction.directive)
-            .selectinload(AirworthinessDirective.discovery_record)
+            .selectinload(AirworthinessDirective.discovery_record),
+            selectinload(ADExtractionReview.extraction)
+            .selectinload(ADExtraction.directive)
+            .selectinload(AirworthinessDirective.publications)
+            .selectinload(ADPublication.source_document),
         )
-        .order_by(ADExtractionReview.created_at.desc())
+        .order_by(ADExtractionReview.created_at.desc(), ADExtractionReview.id)
     ).all()
-    return ADExtractionReviewListResponse(reviews=[serialize_review(review) for review in reviews])
+    review_statuses = [review.status for review in all_reviews]
+    current_offset = offset
+    if review_id:
+        matching_index = next(
+            (index for index, review in enumerate(all_reviews) if review.id == review_id),
+            None,
+        )
+        selected_models = (
+            [all_reviews[matching_index]]
+            if matching_index is not None
+            else []
+        )
+        current_offset = matching_index or 0
+    else:
+        selected_models = all_reviews[offset:offset + limit]
+    # Exact retained-byte/text verification is intentionally limited to the
+    # selected page. Re-parsing every retained Federal Register PDF just to
+    # render queue counters made the reviewer UI unavailable. Aggregate counts
+    # are triage hints derived from the persisted source cache; the selected
+    # review, approval action, and release gate all re-derive exact source text.
+    selected_reviews = [serialize_review(review) for review in selected_models]
+    aggregate_states = [review_queue_candidate_state(review) for review in all_reviews]
+    verified_count = sum(state[0] for state in aggregate_states)
+    return ADExtractionReviewListResponse(
+        reviews=selected_reviews,
+        currentOffset=current_offset,
+        totalCount=len(review_statuses),
+        pendingCount=sum(review_status == "pending" for review_status in review_statuses),
+        reviewedCount=sum(review_status != "pending" for review_status in review_statuses),
+        verifiedCount=verified_count,
+        quarantinedCount=len(all_reviews) - verified_count,
+        approvalReadyCount=sum(state[1] for state in aggregate_states),
+    )
 
 
 @router.get("/aircraft/{aircraft_id}/matches", response_model=ADMatchResultListResponse)
@@ -126,15 +398,31 @@ def list_aircraft_matches(
             selectinload(ADMatchResult.aircraft),
             selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.discovery_record),
             selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.publications),
+            selectinload(ADMatchResult.directive).selectinload(AirworthinessDirective.extractions),
+            selectinload(ADMatchResult.extraction)
+            .selectinload(ADExtraction.reviews)
+            .selectinload(ADExtractionReview.reviewer)
+            .selectinload(User.memberships),
+            selectinload(ADMatchResult.directive)
+            .selectinload(AirworthinessDirective.publications)
+            .selectinload(ADPublication.source_document),
             selectinload(ADMatchResult.installed_component),
             selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.target),
             selectinload(ADMatchResult.target_applicability).selectinload(ADTargetApplicability.source_publication),
-            selectinload(ADMatchResult.due_state),
+            selectinload(ADMatchResult.due_state).selectinload(AircraftADDueState.requirement),
+            selectinload(ADMatchResult.due_state_links)
+            .selectinload(ADMatchDueStateLink.due_state)
+            .selectinload(AircraftADDueState.requirement),
             selectinload(ADMatchResult.evidence_links).selectinload(ADMatchEvidence.logbook_entry).selectinload(LogbookEntry.logbook_section),
             selectinload(ADMatchResult.adjudication),
         )
         .order_by(ADMatchResult.status.desc(), ADMatchResult.confidence.desc(), ADMatchResult.created_at.desc())
     ).all()
+    matches = [
+        match for match in matches
+        if extraction_has_signed_release(match.extraction)
+        and match_has_signed_materialization_chain(match)
+    ]
     latest_matching_event = db.scalar(
         select(ProductEvent)
         .where(
@@ -190,6 +478,37 @@ def list_aircraft_matches(
     )
 
 
+def match_has_signed_materialization_chain(match: ADMatchResult) -> bool:
+    applicability = match.target_applicability
+    if (
+        applicability is None
+        or applicability.status != "current"
+        or applicability.source_extraction_id != match.extraction_id
+    ):
+        return False
+    due_states = [
+        link.due_state for link in match.due_state_links
+        if link.due_state is not None
+    ]
+    if match.due_state is not None and all(
+        state.id != match.due_state.id for state in due_states
+    ):
+        due_states.append(match.due_state)
+    for state in due_states:
+        requirement = state.requirement
+        if (
+            not state.is_current
+            or state.aircraft_id != match.aircraft_id
+            or state.installed_component_id != match.installed_component_id
+            or requirement is None
+            or requirement.status != "current"
+            or requirement.source_extraction_id != match.extraction_id
+            or requirement.target_applicability_id != applicability.id
+        ):
+            return False
+    return True
+
+
 @router.post("/matches/{match_id}/adjudication", response_model=ADMatchAdjudicationDecisionResponse)
 def decide_match_adjudication(
     match_id: str,
@@ -284,24 +603,54 @@ def decide_extraction_review(
     current_user: User = Depends(get_current_user),
     db: Session = Depends(get_db),
 ) -> ADReviewDecisionResponse:
-    ensure_platform_admin(current_user)
+    ensure_ad_extraction_reviewer(current_user)
     review = db.scalar(
         select(ADExtractionReview)
         .where(ADExtractionReview.id == review_id)
+        .with_for_update()
         .options(
             selectinload(ADExtractionReview.extraction)
             .selectinload(ADExtraction.directive)
-            .selectinload(AirworthinessDirective.discovery_record)
+            .selectinload(AirworthinessDirective.discovery_record),
+            selectinload(ADExtractionReview.extraction)
+            .selectinload(ADExtraction.directive)
+            .selectinload(AirworthinessDirective.publications)
+            .selectinload(ADPublication.source_document),
         )
     )
     if review is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AD extraction review not found")
     if review.status != "pending":
-        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review has already been decided")
+        attempted_output = derive_compliance_action_summaries(
+            payload.output if payload.output is not None else review.proposed_output
+        )
+        db.add(ADExtractionReviewDecision(
+            review_id=review.id,
+            extraction_id=review.extraction_id,
+            decision=payload.decision,
+            output_hash=structured_output_hash(attempted_output),
+            decision_output=attempted_output,
+            actor_user_id=current_user.id,
+            decided_at=datetime.now(timezone.utc),
+            notes=payload.notes,
+            event_type="decision_conflict",
+            metadata_json={
+                "directiveId": review.extraction.directive_id,
+                "terminalStatusObserved": review.status,
+                "terminalReviewerUserId": review.reviewer_user_id,
+            },
+        ))
+        db.commit()
+        raise HTTPException(
+            status_code=status.HTTP_409_CONFLICT,
+            detail="Review has already been decided; the conflicting attempt was recorded",
+        )
     if payload.decision not in {"approved", "edited", "rejected"}:
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported review decision")
 
-    decision_output = payload.output if payload.output is not None else review.proposed_output
+    decision_output = derive_compliance_action_summaries(
+        payload.output if payload.output is not None else review.proposed_output
+    )
     affected_aircraft_ids = set(
         db.scalars(
             select(ADMatchResult.aircraft_id)
@@ -314,14 +663,43 @@ def decide_extraction_review(
         .all()
     )
     if payload.decision in {"approved", "edited"}:
-        try:
-            validate_extraction_output(decision_output)
-        except ValueError as exc:
+        source_pages = bounded_source_document_pages(
+            ensure_persisted_source_pages(
+                review.extraction.directive,
+                review.extraction,
+            ),
+            ad_number=review.extraction.directive.ad_number,
+            title=review.extraction.directive.title,
+        )
+        evidence_status, evidence_message = source_evidence_status(
+            review.extraction.directive.ad_number,
+            source_pages,
+        )
+        if evidence_status != "verified":
+            raise HTTPException(
+                status_code=status.HTTP_409_CONFLICT,
+                detail=evidence_message,
+            )
+        approval_blockers = extraction_approval_blockers(
+            review.extraction,
+            decision_output,
+            source_pages,
+        )
+        if approval_blockers:
             raise HTTPException(
                 status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
-                detail=str(exc),
-            ) from exc
+                detail=" ".join(approval_blockers),
+            )
         review.extraction.output = decision_output
+        db.execute(
+            update(ADExtraction)
+            .where(
+                ADExtraction.directive_id == review.extraction.directive_id,
+                ADExtraction.id != review.extraction.id,
+                ADExtraction.status == "approved",
+            )
+            .values(status="superseded")
+        )
         review.extraction.status = "approved"
         review.extraction.directive.extraction_status = "complete"
         review.extraction.directive.review_status = "approved"
@@ -333,7 +711,9 @@ def decide_extraction_review(
             select(ADTargetApplicability.target_id)
             .where(
                 ADTargetApplicability.directive_id
-                == review.extraction.directive_id
+                == review.extraction.directive_id,
+                ADTargetApplicability.status == "current",
+                ADTargetApplicability.source_extraction_id == review.extraction.id,
             )
             .distinct()
         ).all()
@@ -357,12 +737,25 @@ def decide_extraction_review(
         review.extraction.status = "rejected"
         review.extraction.directive.review_status = "rejected"
 
+    decision_time = datetime.now(timezone.utc)
+    db.add(ADExtractionReviewDecision(
+        review_id=review.id,
+        extraction_id=review.extraction_id,
+        decision=payload.decision,
+        output_hash=structured_output_hash(decision_output),
+        decision_output=decision_output,
+        actor_user_id=current_user.id,
+        decided_at=decision_time,
+        notes=payload.notes,
+        event_type="review_decision",
+        metadata_json={"directiveId": review.extraction.directive_id},
+    ))
     review.status = payload.decision
     review.decision = payload.decision
     review.decision_output = decision_output
     review.reviewer_user_id = current_user.id
     review.notes = payload.notes
-    review.reviewed_at = datetime.now(timezone.utc)
+    review.reviewed_at = decision_time
     for aircraft_id in affected_aircraft_ids:
         resolve_aircraft_ad_coverage(db, aircraft_id)
         invalidate_aircraft_match_results(
@@ -419,6 +812,7 @@ def serialize_directive(directive: AirworthinessDirective) -> AirworthinessDirec
         id=directive.id,
         discoveryRecordId=directive.discovery_record_id,
         adNumber=directive.ad_number,
+        officialAdNumber=official_ad_number(directive.ad_number),
         title=directive.title,
         status=directive.status,
         extractionStatus=directive.extraction_status,
@@ -427,9 +821,49 @@ def serialize_directive(directive: AirworthinessDirective) -> AirworthinessDirec
         publicationDate=record.publication_date if record else first_publication_date(directive),
         htmlUrl=record.html_url if record else first_publication_url(directive, "html_url"),
         pdfUrl=record.pdf_url if record else first_publication_url(directive, "pdf_url"),
+        applicabilityTargets=serialize_directive_applicability_targets(directive),
     )
 
 
+def serialize_directive_applicability_targets(
+    directive: AirworthinessDirective,
+) -> list[ADDirectiveApplicabilityTargetResponse]:
+    released_extraction = released_extraction_for_directive(directive)
+    released_extraction_id = released_extraction.id if released_extraction else None
+    rows: list[ADDirectiveApplicabilityTargetResponse] = []
+    seen: set[tuple[str | None, str, str | None, str | None]] = set()
+    for applicability in directive.target_applicabilities:
+        if (
+            applicability.status != "current"
+            or applicability.target is None
+            or applicability.source_extraction_id != released_extraction_id
+        ):
+            continue
+        target = applicability.target
+        identity = applicability.source_identity or {}
+        source_manufacturer = identity.get("manufacturer") or {}
+        source_model = identity.get("model") or {}
+        key = (
+            applicability.applicability_group_key,
+            target.product_type,
+            target.make,
+            target.model,
+        )
+        if key in seen:
+            continue
+        seen.add(key)
+        rows.append(ADDirectiveApplicabilityTargetResponse(
+            groupKey=applicability.applicability_group_key,
+            productType=target.product_type,
+            productSubtype=target.product_subtype,
+            manufacturer=target.make,
+            model=target.model,
+            sourceManufacturer=source_manufacturer.get("sourceName"),
+            sourceModel=source_model.get("sourceDesignation"),
+        ))
+    return rows
+
+
 def serialize_extraction(extraction: ADExtraction) -> ADExtractionResponse:
     return ADExtractionResponse(
         id=extraction.id,
@@ -445,23 +879,172 @@ def serialize_extraction(extraction: ADExtraction) -> ADExtractionResponse:
     )
 
 
+def review_queue_candidate_state(
+    review: ADExtractionReview,
+) -> tuple[bool, bool]:
+    """Return cheap triage counts without asserting a release decision.
+
+    The selected review is always serialized through ``persisted_source_pages``
+    and therefore re-derived from verified bytes. These aggregate values only
+    keep the queue responsive; they never authorize approval or publication.
+    """
+
+    raw_response = review.extraction.raw_response or {}
+    cached_pages = raw_response.get("retainedSourcePages")
+    if (
+        not raw_response.get("retainedSourcePagesCached")
+        or not isinstance(cached_pages, list)
+        or review.extraction.input_content_hash
+        != extraction_input_hash(review.extraction.directive)
+    ):
+        return False, False
+    source_pages = bounded_source_document_pages(
+        cached_pages,
+        ad_number=review.extraction.directive.ad_number,
+        title=review.extraction.directive.title,
+    )
+    evidence_status, _ = source_evidence_status(
+        review.extraction.directive.ad_number,
+        source_pages,
+    )
+    source_candidate = evidence_status == "verified"
+    if not source_candidate:
+        return False, False
+    proposed_output = derive_compliance_action_summaries(
+        review.decision_output
+        if review.decision_output is not None
+        else review.proposed_output
+    )
+    blockers = extraction_approval_blockers(
+        review.extraction,
+        proposed_output,
+        source_pages,
+    )
+    return True, review.status == "pending" and not blockers
+
+
 def serialize_review(review: ADExtractionReview) -> ADExtractionReviewResponse:
-    record = review.extraction.directive.discovery_record
-    source_text = "\n\n".join(filter(None, [record.title, record.abstract, record.excerpts])) if record else review.extraction.directive.title
+    source_pages = bounded_source_document_pages(
+        full_text_pages_for_extraction(review.extraction),
+        ad_number=review.extraction.directive.ad_number,
+        title=review.extraction.directive.title,
+    )
+    evidence_status, evidence_message = source_evidence_status(
+        review.extraction.directive.ad_number,
+        source_pages,
+    )
+    proposed_output = derive_compliance_action_summaries(review.proposed_output)
+    decision_output = (
+        derive_compliance_action_summaries(review.decision_output)
+        if review.decision_output is not None
+        else None
+    )
+    output = decision_output or proposed_output
+    requirements = output.get("requirements") or []
+    approval_blockers = extraction_approval_blockers(
+        review.extraction,
+        output,
+        source_pages,
+    )
+    source_document_ids = {
+        str(page.get("sourceDocumentId"))
+        for page in source_pages
+        if page.get("sourceDocumentId")
+    }
+    source_documents: list[ADSourceDocumentResponse] = []
+    seen_document_ids: set[str] = set()
+    for publication in review.extraction.directive.publications:
+        document = publication.source_document
+        if (
+            document is None
+            or document.id not in source_document_ids
+            or document.id in seen_document_ids
+        ):
+            continue
+        seen_document_ids.add(document.id)
+        source_documents.append(serialize_source_document(document))
+    provenance = None
+    staging_decision_id = (review.extraction.raw_response or {}).get(
+        "latestProposalStagingDecisionId"
+    )
+    if staging_decision_id:
+        staging_decision = next(
+            (
+                decision
+                for decision in review.decision_history
+                if decision.id == staging_decision_id
+                and decision.event_type == "proposal_staged"
+                and decision.decision == "proposal_staged"
+            ),
+            None,
+        )
+        if staging_decision is not None:
+            metadata = staging_decision.metadata_json or {}
+            provenance = ADProposalProvenanceResponse(
+                stagingDecisionId=staging_decision.id,
+                actorUserId=staging_decision.actor_user_id,
+                stagedAt=staging_decision.decided_at,
+                stagingMode=(
+                    "allow_incomplete"
+                    if metadata.get("allowIncomplete")
+                    else "strict"
+                ),
+            )
     return ADExtractionReviewResponse(
         id=review.id,
         status=review.status,
-        proposedOutput=review.proposed_output,
-        decisionOutput=review.decision_output,
+        proposedOutput=proposed_output,
+        decisionOutput=decision_output,
         decision=review.decision,
         notes=review.notes,
         extraction=serialize_extraction(review.extraction),
         directive=serialize_directive(review.extraction.directive),
-        sourceText=source_text,
+        sourceText="\n\n".join(page["text"] for page in source_pages),
+        sourcePages=source_pages,
+        sourceDocuments=source_documents,
+        requirementCount=len(requirements),
+        unresolvedRequirementCount=(
+            sum(bool(item.get("uncertaintyReasons")) for item in requirements)
+            + sum(
+                bool(item.get("uncertaintyReasons"))
+                for item in output.get("applicabilityGroups") or []
+            )
+        ),
+        evidenceStatus=evidence_status,
+        evidenceMessage=evidence_message,
+        canApprove=review.status == "pending" and not approval_blockers,
+        approvalBlockers=approval_blockers,
+        proposalProvenance=provenance,
+    )
+
+
+def serialize_source_document(document: ADSourceDocument) -> ADSourceDocumentResponse:
+    return ADSourceDocumentResponse(
+        id=document.id,
+        sourceSystem=document.source_system,
+        sourceType=document.source_type,
+        sourceIdentifier=document.source_identifier,
+        parentSourceIdentifier=document.parent_source_identifier,
+        sourceUrl=document.source_url,
+        contentUrl=f"/api/v1/ads/source-documents/{document.id}/content",
+        mediaType=document.media_type,
+        contentHash=document.content_hash,
+        storageBytes=document.storage_bytes,
+        capturedAt=document.captured_at,
+        publicationDate=document.publication_date,
+        parserName=document.parser_name,
+        parserVersion=document.parser_version,
     )
 
 
 def serialize_match_result(match: ADMatchResult) -> ADMatchResultResponse:
+    due_states = [
+        link.due_state
+        for link in match.due_state_links
+        if link.due_state is not None
+    ]
+    if not due_states and match.due_state is not None:
+        due_states = [match.due_state]
     return ADMatchResultResponse(
         id=match.id,
         aircraftId=match.aircraft_id,
@@ -483,10 +1066,14 @@ def serialize_match_result(match: ADMatchResult) -> ADMatchResultResponse:
         unresolvedReasons=match.unresolved_reasons or [],
         applicability=serialize_match_applicability(match),
         dueState=(
-            ADDueStateResponse(**due_state_payload(match.due_state))
-            if match.due_state
+            ADDueStateResponse(**due_state_payload(due_states[0]))
+            if len(due_states) == 1
             else None
         ),
+        dueStates=[
+            ADDueStateResponse(**due_state_payload(state))
+            for state in due_states
+        ],
         algorithmName=match.algorithm_name,
         algorithmVersion=match.algorithm_version,
         inputHash=match.input_hash,
diff --git a/backend/app/schemas/ads.py b/backend/app/schemas/ads.py
index 7fe8a2a..ed64f11 100644
--- a/backend/app/schemas/ads.py
+++ b/backend/app/schemas/ads.py
@@ -1,4 +1,4 @@
-from datetime import date
+from datetime import date, datetime
 from typing import Any, Optional
 
 from pydantic import BaseModel
@@ -18,10 +18,21 @@ class ADDiscoveryRecordResponse(BaseModel):
     contentHash: str
 
 
+class ADDirectiveApplicabilityTargetResponse(BaseModel):
+    groupKey: Optional[str]
+    productType: str
+    productSubtype: Optional[str]
+    manufacturer: Optional[str]
+    model: Optional[str]
+    sourceManufacturer: Optional[str]
+    sourceModel: Optional[str]
+
+
 class AirworthinessDirectiveResponse(BaseModel):
     id: str
     discoveryRecordId: Optional[str]
     adNumber: Optional[str]
+    officialAdNumber: Optional[str]
     title: str
     status: str
     extractionStatus: str
@@ -30,6 +41,7 @@ class AirworthinessDirectiveResponse(BaseModel):
     publicationDate: Optional[date]
     htmlUrl: Optional[str]
     pdfUrl: Optional[str]
+    applicabilityTargets: list[ADDirectiveApplicabilityTargetResponse] = []
 
 
 class ADExtractionResponse(BaseModel):
@@ -45,6 +57,30 @@ class ADExtractionResponse(BaseModel):
     citations: list[dict[str, Any]]
 
 
+class ADSourceDocumentResponse(BaseModel):
+    id: str
+    sourceSystem: str
+    sourceType: str
+    sourceIdentifier: str
+    parentSourceIdentifier: Optional[str]
+    sourceUrl: Optional[str]
+    contentUrl: str
+    mediaType: Optional[str]
+    contentHash: str
+    storageBytes: int
+    capturedAt: datetime
+    publicationDate: Optional[date]
+    parserName: Optional[str]
+    parserVersion: Optional[str]
+
+
+class ADProposalProvenanceResponse(BaseModel):
+    stagingDecisionId: str
+    actorUserId: Optional[str]
+    stagedAt: datetime
+    stagingMode: str
+
+
 class ADExtractionReviewResponse(BaseModel):
     id: str
     status: str
@@ -55,10 +91,26 @@ class ADExtractionReviewResponse(BaseModel):
     extraction: ADExtractionResponse
     directive: AirworthinessDirectiveResponse
     sourceText: str
+    sourcePages: list[dict[str, Any]]
+    sourceDocuments: list[ADSourceDocumentResponse]
+    requirementCount: int
+    unresolvedRequirementCount: int
+    evidenceStatus: str
+    evidenceMessage: str
+    canApprove: bool
+    approvalBlockers: list[str]
+    proposalProvenance: Optional[ADProposalProvenanceResponse]
 
 
 class ADExtractionReviewListResponse(BaseModel):
     reviews: list[ADExtractionReviewResponse]
+    currentOffset: int
+    totalCount: int
+    pendingCount: int
+    reviewedCount: int
+    verifiedCount: int
+    quarantinedCount: int
+    approvalReadyCount: int
 
 
 class ADReviewDecisionRequest(BaseModel):
@@ -156,6 +208,7 @@ class ADMatchResultResponse(BaseModel):
     unresolvedReasons: list[str]
     applicability: Optional[ADMatchApplicabilityResponse]
     dueState: Optional[ADDueStateResponse]
+    dueStates: list[ADDueStateResponse]
     algorithmName: str
     algorithmVersion: str
     inputHash: str
diff --git a/backend/app/scripts/stage_ad_review_proposal.py b/backend/app/scripts/stage_ad_review_proposal.py
new file mode 100644
index 0000000..970be69
--- /dev/null
+++ b/backend/app/scripts/stage_ad_review_proposal.py
@@ -0,0 +1,420 @@
+from __future__ import annotations
+
+import argparse
+import copy
+import json
+import re
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+
+from sqlalchemy import select
+from sqlalchemy.orm import Session, selectinload
+
+from app.db.session import SessionLocal
+from app.models.core import (
+    ADExtraction,
+    ADExtractionReview,
+    ADExtractionReviewDecision,
+    ADPublication,
+    AirworthinessDirective,
+    User,
+)
+from app.services.ad_extraction import (
+    SCHEMA_VERSION,
+    bounded_source_document_pages,
+    derive_compliance_action_summaries,
+    ensure_persisted_source_pages,
+    extraction_approval_blocker_details,
+    extraction_approval_blockers,
+    normalize_regulatory_text,
+    structured_output_hash,
+    validate_extraction_json_schema,
+    validate_extraction_output,
+    validate_requirement_evidence,
+)
+from app.services.observability import record_product_event, record_workflow_status
+
+
+VISUAL_OCR_REASON_PATTERN = re.compile(
+    r"^visual_ocr_model_cell_mismatch"
+    r"\|modelIndex=(?P<model_index>\d+)"
+    r"\|visual=(?P<visual>[^|]+)"
+    r"\|parsed=(?P<parsed>[^|]+)"
+    r"\|sourceDocumentId=(?P<document_id>[^|]+)"
+    r"\|pageNumber=(?P<page_number>\d+)$"
+)
+
+
+def contains_normalized_phrase(haystack: str, needle: str) -> bool:
+    return f" {needle} " in f" {haystack} "
+
+
+def visual_ocr_validation_shadow(
+    proposal: dict[str, Any],
+    source_pages: list[dict[str, Any]],
+) -> tuple[dict[str, Any], list[dict[str, Any]]]:
+    """Substitute only explicitly recorded visual-vs-parser model cells for draft validation.
+
+    The returned shadow is never persisted. Authenticated approval validates the
+    unmodified proposal, so every visual correction remains fail-closed until
+    retained source text is remediated and reviewed.
+    """
+
+    shadow = copy.deepcopy(proposal)
+    page_index = {
+        (str(page["sourceDocumentId"]), int(page["pageNumber"])):
+        normalize_regulatory_text(page["text"])
+        for page in source_pages
+    }
+    records: list[dict[str, Any]] = []
+    for group_index, (group, shadow_group) in enumerate(zip(
+        proposal.get("applicabilityGroups") or [],
+        shadow.get("applicabilityGroups") or [],
+        strict=True,
+    )):
+        for reason in group.get("uncertaintyReasons") or []:
+            match = VISUAL_OCR_REASON_PATTERN.fullmatch(str(reason).strip())
+            if match is None:
+                continue
+            model_index = int(match.group("model_index"))
+            visual = match.group("visual").strip()
+            parsed = match.group("parsed").strip()
+            document_id = match.group("document_id").strip()
+            page_number = int(match.group("page_number"))
+            models = group.get("modelApplicability", {}).get("models") or []
+            shadow_models = shadow_group.get("modelApplicability", {}).get("models") or []
+            if model_index >= len(models) or model_index >= len(shadow_models):
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR model index is out of range"
+                )
+            model = models[model_index]
+            shadow_model = shadow_models[model_index]
+            if str(model.get("sourceDesignation") or "").strip() != visual:
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR record does not match sourceDesignation"
+                )
+            if model.get("normalizedDesignation") is not None:
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR model normalizedDesignation must be null"
+                )
+            cited_keys = {
+                (str(citation.get("sourceDocumentId")), int(citation.get("pageNumber")))
+                for citation in group.get("citations") or []
+                if citation.get("sourceDocumentId") and citation.get("pageNumber")
+            }
+            page_key = (document_id, page_number)
+            if page_key not in cited_keys or page_key not in page_index:
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR record must identify an admitted cited page"
+                )
+            parsed_text = page_index[page_key]
+            if not contains_normalized_phrase(
+                parsed_text, normalize_regulatory_text(parsed)
+            ):
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR parsed token is not present on the cited page"
+                )
+            if contains_normalized_phrase(
+                parsed_text, normalize_regulatory_text(visual)
+            ):
+                raise ValueError(
+                    f"AD applicability group {group_index} visual OCR correction is already present in retained text"
+                )
+            shadow_model["sourceDesignation"] = parsed
+            records.append({
+                "groupIndex": group_index,
+                "modelIndex": model_index,
+                "visual": visual,
+                "parsed": parsed,
+                "sourceDocumentId": document_id,
+                "pageNumber": page_number,
+            })
+    return shadow, records
+
+
+def allowed_incomplete_blockers(
+    proposal: dict[str, Any],
+    source_pages: list[dict[str, Any]],
+) -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
+    """Validate a complete draft and return its narrowly typed allowed blockers."""
+
+    validate_extraction_json_schema(proposal)
+    validate_extraction_output(
+        proposal,
+        require_v2_requirements=True,
+        require_nonempty_requirements=True,
+        require_nonempty_applicability=True,
+    )
+    shadow, visual_records = visual_ocr_validation_shadow(proposal, source_pages)
+    validate_requirement_evidence(shadow, source_pages)
+    codes: list[str] = []
+    applicability_count = sum(
+        len(group.get("uncertaintyReasons") or [])
+        for group in proposal.get("applicabilityGroups") or []
+    )
+    requirement_count = sum(
+        len(requirement.get("uncertaintyReasons") or [])
+        for requirement in proposal.get("requirements") or []
+    )
+    amoc_count = sum(
+        len(provision.get("uncertaintyReasons") or [])
+        for provision in proposal.get("amocProvisions") or []
+    )
+    if applicability_count:
+        codes.append("applicability_uncertainty")
+    if requirement_count:
+        codes.append("requirement_uncertainty")
+    if amoc_count:
+        codes.append("amoc_uncertainty")
+    if visual_records:
+        codes.append("visual_ocr_model_cell_mismatch")
+    return shadow, codes, visual_records
+
+
+def stage_review_proposal(
+    db: Session,
+    *,
+    ad_number: str,
+    review_id: str,
+    actor_user_id: str,
+    loaded_proposal: dict[str, Any],
+    allow_incomplete: bool,
+) -> dict[str, Any]:
+    if not isinstance(loaded_proposal, dict):
+        raise ValueError("Proposal input must be a complete v3 JSON object")
+    actor = db.scalar(
+        select(User)
+        .where(User.id == actor_user_id)
+        .options(selectinload(User.memberships))
+    )
+    if actor is None or actor.status != "active" or not any(
+        membership.status == "active" and membership.role == "platform_admin"
+        for membership in actor.memberships
+    ):
+        raise ValueError("An active Paprnav platform administrator actor is required")
+    review = db.scalar(
+        select(ADExtractionReview)
+        .where(ADExtractionReview.id == review_id)
+        .with_for_update()
+        .options(
+            selectinload(ADExtractionReview.extraction)
+            .selectinload(ADExtraction.directive)
+            .selectinload(AirworthinessDirective.discovery_record),
+            selectinload(ADExtractionReview.extraction)
+            .selectinload(ADExtraction.directive)
+            .selectinload(AirworthinessDirective.publications)
+            .selectinload(ADPublication.source_document),
+        )
+    )
+    if review is None:
+        raise ValueError(f"AD extraction review {review_id} was not found")
+    directive = review.extraction.directive
+    if directive.ad_number != ad_number:
+        raise ValueError(
+            f"Review {review_id} belongs to AD {directive.ad_number}, not {ad_number}"
+        )
+    if review.extraction.schema_version != SCHEMA_VERSION:
+        raise ValueError(f"Review {review_id} is not a {SCHEMA_VERSION} extraction")
+    if review.status != "pending" or review.extraction.status != "needs_review":
+        raise ValueError(
+            f"Review {review_id} is terminal or its extraction is not awaiting review"
+        )
+
+    proposal = derive_compliance_action_summaries(copy.deepcopy(loaded_proposal))
+    pages = bounded_source_document_pages(
+        ensure_persisted_source_pages(directive, review.extraction),
+        ad_number=directive.ad_number,
+        title=directive.title,
+    )
+    visual_records: list[dict[str, Any]] = []
+    blocker_codes: list[str] = []
+    if allow_incomplete:
+        validation_output, blocker_codes, visual_records = allowed_incomplete_blockers(
+            proposal, pages,
+        )
+        approval_blocker_details = extraction_approval_blocker_details(
+            review.extraction, validation_output, pages,
+        )
+        allowed_codes = {
+            "applicability_uncertainty",
+            "requirement_uncertainty",
+            "amoc_uncertainty",
+        }
+        fatal_blockers = [
+            blocker["message"]
+            for blocker in approval_blocker_details
+            if blocker["code"] not in allowed_codes
+        ]
+        if fatal_blockers:
+            raise ValueError(" ".join(fatal_blockers))
+    else:
+        validate_extraction_json_schema(proposal)
+        validate_extraction_output(
+            proposal,
+            require_v2_requirements=True,
+            require_nonempty_requirements=True,
+            require_nonempty_applicability=True,
+        )
+        validate_requirement_evidence(proposal, pages)
+        approval_blockers = extraction_approval_blockers(
+            review.extraction, proposal, pages,
+        )
+        if approval_blockers:
+            raise ValueError(" ".join(approval_blockers))
+
+    prior_output = copy.deepcopy(review.proposed_output)
+    prior_extraction_output = copy.deepcopy(review.extraction.output)
+    if structured_output_hash(prior_output) != structured_output_hash(prior_extraction_output):
+        raise ValueError(
+            "Review proposed output and extraction output diverge; use the audited correction workflow before staging"
+        )
+    prior_hash = structured_output_hash(prior_output)
+    new_hash = structured_output_hash(proposal)
+    if prior_hash == new_hash:
+        return {
+            "review": review,
+            "actor": actor,
+            "proposal": proposal,
+            "pages": pages,
+            "blockerCodes": blocker_codes,
+            "visualOcrRecords": visual_records,
+            "stagingDecisionId": None,
+            "idempotent": True,
+        }
+
+    staged_at = datetime.now(timezone.utc)
+    staging_decision = ADExtractionReviewDecision(
+        review_id=review.id,
+        extraction_id=review.extraction_id,
+        decision="proposal_staged",
+        output_hash=new_hash,
+        decision_output=proposal,
+        actor_user_id=actor.id,
+        decided_at=staged_at,
+        notes="Complete cited v3 proposal staged for human review; no approval performed.",
+        event_type="proposal_staged",
+        metadata_json={
+            "directiveId": review.extraction.directive_id,
+            "adNumber": ad_number,
+            "reviewId": review.id,
+            "extractionId": review.extraction_id,
+            "priorOutputHash": prior_hash,
+            "priorOutput": prior_output,
+            "priorExtractionOutputHash": structured_output_hash(prior_extraction_output),
+            "priorExtractionOutput": prior_extraction_output,
+            "newOutputHash": new_hash,
+            "sourceInputHash": review.extraction.input_content_hash,
+            "allowIncomplete": allow_incomplete,
+            "allowedBlockerCodes": blocker_codes,
+            "visualOcrRecords": visual_records,
+        },
+    )
+    db.add(staging_decision)
+    db.flush()
+    review.proposed_output = proposal
+    review.extraction.output = proposal
+    review.extraction.confidence = float(
+        proposal.get("confidence", review.extraction.confidence)
+    )
+    review.extraction.raw_response = {
+        **(review.extraction.raw_response or {}),
+        "latestProposalStagingDecisionId": staging_decision.id,
+    }
+    record_product_event(
+        db,
+        event_type="ad_extraction_proposal_staged",
+        subject_type="ad_review",
+        subject_id=review.id,
+        actor=actor,
+        properties={
+            "directiveId": review.extraction.directive_id,
+            "adNumber": ad_number,
+            "stagingDecisionId": staging_decision.id,
+            "priorOutputHash": prior_hash,
+            "newOutputHash": new_hash,
+            "requirementCount": len(proposal["requirements"]),
+            "allowedBlockerCodes": blocker_codes,
+        },
+    )
+    record_workflow_status(
+        db,
+        workflow_type="ad_extraction",
+        workflow_id=review.extraction_id,
+        previous_status="needs_review",
+        new_status="needs_review",
+        reason="cited_proposal_staged_for_human_review",
+        actor_type="reviewer",
+        actor=actor,
+    )
+    return {
+        "review": review,
+        "actor": actor,
+        "proposal": proposal,
+        "pages": pages,
+        "blockerCodes": blocker_codes,
+        "visualOcrRecords": visual_records,
+        "stagingDecisionId": staging_decision.id,
+        "idempotent": False,
+    }
+
+
+def main() -> None:
+    parser = argparse.ArgumentParser(
+        description="Stage a complete cited AD extraction proposal for human review without approving it"
+    )
+    parser.add_argument("--ad-number", required=True)
+    parser.add_argument("--review-id", required=True)
+    parser.add_argument("--actor-user-id", required=True)
+    parser.add_argument("--input", required=True)
+    parser.add_argument("--allow-incomplete", action="store_true")
+    parser.add_argument("--commit", action="store_true")
+    args = parser.parse_args()
+
+    loaded_proposal = json.loads(Path(args.input).read_text(encoding="utf-8"))
+    try:
+        with SessionLocal() as db:
+            result = stage_review_proposal(
+                db,
+                ad_number=args.ad_number,
+                review_id=args.review_id,
+                actor_user_id=args.actor_user_id,
+                loaded_proposal=loaded_proposal,
+                allow_incomplete=args.allow_incomplete,
+            )
+            checks = [
+                ("exact_pending_review_locked", result["review"].status == "pending"),
+                ("requirements_staged", len(result["proposal"]["requirements"]) > 0),
+                ("retained_pages_available", len(result["pages"]) > 0),
+                (
+                    "no_approval_or_materialization",
+                    result["review"].extraction.status == "needs_review",
+                ),
+            ]
+            if args.commit:
+                db.commit()
+            else:
+                db.rollback()
+    except ValueError as exc:
+        raise SystemExit(str(exc)) from exc
+
+    passed = sum(value for _, value in checks)
+    print(json.dumps({
+        "adNumber": args.ad_number,
+        "reviewId": args.review_id,
+        "actorUserId": args.actor_user_id,
+        "allowIncomplete": args.allow_incomplete,
+        "blockerCodes": result["blockerCodes"],
+        "visualOcrRecords": result["visualOcrRecords"],
+        "stagingDecisionId": result["stagingDecisionId"],
+        "idempotent": result["idempotent"],
+        "committed": args.commit,
+        "checks": dict(checks),
+    }, sort_keys=True))
+    print(f"{passed} passed out of {len(checks)}")
+    if passed != len(checks):
+        raise SystemExit(1)
+
+
+if __name__ == "__main__":
+    main()
diff --git a/backend/app/services/ad_extraction.py b/backend/app/services/ad_extraction.py
index c10a345..a9543fc 100644
--- a/backend/app/services/ad_extraction.py
+++ b/backend/app/services/ad_extraction.py
@@ -1,9 +1,12 @@
 from __future__ import annotations
 
 import hashlib
+import io
 import json
+import math
 import re
-from datetime import datetime, timezone
+from datetime import date, datetime, timezone
+from decimal import Decimal, InvalidOperation
 from typing import Any, Protocol
 
 import httpx
@@ -11,7 +14,17 @@ from sqlalchemy import select
 from sqlalchemy.orm import Session, selectinload
 
 from app.core.config import get_settings
-from app.models.core import ADExtraction, ADExtractionReview, AirworthinessDirective
+from pypdf import PdfReader
+
+from app.models.core import (
+    ADExtraction,
+    ADExtractionReview,
+    ADPublication,
+    ADTargetApplicability,
+    AirworthinessDirective,
+    ApplicabilityTarget,
+)
+from app.services.storage import read_stored_file_bytes
 from app.services.ad_applicability import populate_applicability_from_extraction
 from app.services.ad_discovery import extract_ad_number
 from app.services.observability import record_product_event, record_workflow_status
@@ -19,15 +32,158 @@ from app.services.observability import record_product_event, record_workflow_sta
 PROVIDER_NAME = "deterministic_ad_extractor"
 PROVIDER_VERSION = "0.1.0"
 OPENAI_PROVIDER_NAME = "openai_responses_ad_extractor"
-OPENAI_PROMPT_VERSION = "ad_extraction_prompt_v1"
-SCHEMA_VERSION = "ad_extraction_v1"
+OPENAI_PROMPT_VERSION = "ad_full_text_compliance_prompt_v3"
+SCHEMA_VERSION = "ad_extraction_v3"
 REVIEW_THRESHOLD = 0.86
 LLM_REVIEW_THRESHOLD = 0.80
 AD_NUMBER_PATTERN = re.compile(r"\b(?:AD\s*)?(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
 AD_EXTRACTION_SYSTEM_PROMPT = """Extract structured FAA Airworthiness Directive data for paprnav.
 Return only facts supported by the supplied source text. Use null or empty lists when the source does not support a field.
 Confidence is your 0.0-1.0 estimate that the extracted fields are complete and source-supported.
-Set uncertaintyReasons when applicability, compliance, dates, or supersession data are missing or ambiguous."""
+Create source-faithful applicabilityGroups. Keep manufacturer sourceName separate from every model sourceDesignation.
+Do not concatenate manufacturer and model, and do not emit manufacturer and model as unrelated sibling values.
+Use normalizedName/normalizedDesignation only when a conservative canonical identity is supported; otherwise use null.
+Preserve serial scope, installed-equipment conditions, applicability conditions, and page citations in each group.
+Create a separate requirement for each compliance action or alternative. Keep initial thresholds separate from recurring triggers.
+Every requirement must list the applicabilityGroupKeys it governs.
+Set complianceActions to the ordered actionText values from requirements; requirements are the authoritative compliance structure.
+Capture the AD's alternative-method-of-compliance paragraph in amocProvisions. Do not treat an AMOC provision as an in-rule alternative requirement.
+Every requirement citation must use the source-document ID and page number printed in the supplied source text.
+Set uncertaintyReasons when applicability, compliance, dates, trigger logic, conditions, or supersession data are missing or ambiguous."""
+AD_THRESHOLD_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": ["metric", "value", "unit", "anchorKind", "sourceText"],
+    "properties": {
+        "metric": {"type": "string", "enum": ["calendar", "tach_hours", "hobbs_hours", "total_time_hours", "cycles"]},
+        "value": {"type": "number", "exclusiveMinimum": 0},
+        "unit": {"type": "string", "enum": ["days", "months", "hours", "cycles"]},
+        "anchorKind": {"type": "string", "enum": ["effective_date", "last_compliance", "installation", "manufacture", "unknown"]},
+        "sourceText": {"type": "string"},
+    },
+}
+AD_PAGE_CITATION_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": ["sourceDocumentId", "pageNumber", "text"],
+    "properties": {
+        "sourceDocumentId": {"type": "string"},
+        "pageNumber": {"type": "integer", "minimum": 1},
+        "text": {"type": "string"},
+    },
+}
+AD_MANUFACTURER_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": ["sourceName", "normalizedName"],
+    "properties": {
+        "sourceName": {"type": "string"},
+        "normalizedName": {"type": ["string", "null"]},
+    },
+}
+AD_MODEL_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": ["sourceDesignation", "normalizedDesignation", "aliases"],
+    "properties": {
+        "sourceDesignation": {"type": "string"},
+        "normalizedDesignation": {"type": ["string", "null"]},
+        "aliases": {"type": "array", "items": {"type": "string"}},
+    },
+}
+AD_SERIAL_APPLICABILITY_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": ["kind", "values", "ranges", "excludedValues", "sourceText"],
+    "properties": {
+        "kind": {"type": "string", "enum": ["all", "values", "ranges", "expression", "unknown"]},
+        "values": {"type": "array", "items": {"type": "string"}},
+        "ranges": {
+            "type": "array",
+            "items": {
+                "type": "object",
+                "additionalProperties": False,
+                "required": ["start", "end"],
+                "properties": {
+                    "start": {"type": ["string", "null"]},
+                    "end": {"type": ["string", "null"]},
+                },
+            },
+        },
+        "excludedValues": {"type": "array", "items": {"type": "string"}},
+        "sourceText": {"type": ["string", "null"]},
+    },
+}
+AD_EQUIPMENT_CONDITION_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": [
+        "conditionKey", "productType", "manufacturer", "model", "softwareVersions",
+        "conditionText", "citations",
+    ],
+    "properties": {
+        "conditionKey": {"type": "string"},
+        "productType": {"type": "string"},
+        "manufacturer": AD_MANUFACTURER_SCHEMA,
+        "model": {"anyOf": [AD_MODEL_SCHEMA, {"type": "null"}]},
+        "softwareVersions": {"type": "array", "items": {"type": "string"}},
+        "conditionText": {"type": "string"},
+        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
+    },
+}
+AD_APPLICABILITY_GROUP_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": [
+        "groupKey", "productType", "productSubtype", "manufacturer", "modelApplicability",
+        "serialNumberApplicability", "equipmentCombinationLogic", "equipmentConditions", "conditions",
+        "citations", "confidence", "uncertaintyReasons",
+    ],
+    "properties": {
+        "groupKey": {"type": "string"},
+        "productType": {
+            "type": "string",
+            "enum": ["aircraft", "rotorcraft", "engine", "propeller", "appliance", "equipment", "other"],
+        },
+        "productSubtype": {"type": ["string", "null"]},
+        "manufacturer": AD_MANUFACTURER_SCHEMA,
+        "modelApplicability": {
+            "type": "object",
+            "additionalProperties": False,
+            "required": ["kind", "models", "sourceText"],
+            "properties": {
+                "kind": {"type": "string", "enum": ["listed", "all", "expression", "unknown"]},
+                "models": {"type": "array", "items": AD_MODEL_SCHEMA},
+                "sourceText": {"type": ["string", "null"]},
+            },
+        },
+        "serialNumberApplicability": AD_SERIAL_APPLICABILITY_SCHEMA,
+        "equipmentCombinationLogic": {"type": "string", "enum": ["all", "any"]},
+        "equipmentConditions": {"type": "array", "items": AD_EQUIPMENT_CONDITION_SCHEMA},
+        "conditions": {"type": "array", "items": {"type": "string"}},
+        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
+        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
+        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
+    },
+}
+AD_AMOC_PROVISION_SCHEMA: dict[str, Any] = {
+    "type": "object",
+    "additionalProperties": False,
+    "required": [
+        "provisionKey", "authorityText", "approvingAuthority", "submissionInstructions",
+        "conditions", "citations", "confidence", "uncertaintyReasons",
+    ],
+    "properties": {
+        "provisionKey": {"type": "string"},
+        "authorityText": {"type": "string"},
+        "approvingAuthority": {"type": ["string", "null"]},
+        "submissionInstructions": {"type": ["string", "null"]},
+        "conditions": {"type": "array", "items": {"type": "string"}},
+        "citations": {"type": "array", "items": AD_PAGE_CITATION_SCHEMA},
+        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
+        "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
+    },
+}
 AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
     "type": "object",
     "additionalProperties": False,
@@ -36,6 +192,7 @@ AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
         "title",
         "effectiveDate",
         "publicationDate",
+        "applicabilityGroups",
         "affectedProducts",
         "complianceActions",
         "complianceIntervals",
@@ -44,12 +201,16 @@ AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
         "confidence",
         "citations",
         "uncertaintyReasons",
+        "requirements",
+        "amocProvisions",
     ],
     "properties": {
         "adNumber": {"type": ["string", "null"]},
         "title": {"type": ["string", "null"]},
         "effectiveDate": {"type": ["string", "null"]},
         "publicationDate": {"type": ["string", "null"]},
+        "applicabilityGroups": {"type": "array", "items": AD_APPLICABILITY_GROUP_SCHEMA},
+        # Legacy compatibility summary. Applicability groups remain authoritative.
         "affectedProducts": {"type": "array", "items": {"type": "string"}},
         "complianceActions": {"type": "array", "items": {"type": "string"}},
         "complianceIntervals": {"type": "array", "items": {"type": "string"}},
@@ -79,10 +240,118 @@ AD_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
             },
         },
         "uncertaintyReasons": {"type": "array", "items": {"type": "string"}},
+        "requirements": {
+            "type": "array",
+            "items": {
+                "type": "object",
+                "additionalProperties": False,
+                "required": [
+                    "requirementKey", "applicabilityGroupKeys", "requirementType", "actionText", "initialThresholds",
+                    "recurringTriggers", "combinationLogic", "conditions", "terminatingAction",
+                    "citations", "confidence", "uncertaintyReasons"
+                ],
+                "properties": {
+                    "requirementKey": {"type": "string"},
+                    "applicabilityGroupKeys": {"type": "array", "items": {"type": "string"}},
+                    "requirementType": {"type": "string", "enum": ["one_time", "recurring", "alternative", "conditional", "installation_prohibition"]},
+                    "actionText": {"type": "string"},
+                    "initialThresholds": {"type": "array", "items": AD_THRESHOLD_SCHEMA},
+                    "recurringTriggers": {"type": "array", "items": AD_THRESHOLD_SCHEMA},
+                    "combinationLogic": {"type": "string", "enum": ["all", "whichever_first", "whichever_later", "alternative"]},
+                    "conditions": {"type": "array", "items": {"type": "string"}},
+                    "terminatingAction": {"type": ["string", "null"]},
+                    "citations": {
+                        "type": "array",
+                        "items": {
+                            **AD_PAGE_CITATION_SCHEMA,
+                        }
+                    },
+                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
+                    "uncertaintyReasons": {"type": "array", "items": {"type": "string"}}
+                }
+            }
+        },
+        "amocProvisions": {"type": "array", "items": AD_AMOC_PROVISION_SCHEMA},
     },
 }
 
 
+def validate_extraction_json_schema(output: Any) -> None:
+    """Validate an extraction against the exact provider/reviewer v3 contract.
+
+    This intentionally implements the small JSON-Schema subset used by
+    ``AD_EXTRACTION_JSON_SCHEMA`` so approval does not depend on an optional
+    runtime package. It rejects unknown properties and non-finite JSON numbers.
+    """
+
+    def fail(path: str, message: str) -> None:
+        raise ValueError(f"AD extraction schema error at {path}: {message}")
+
+    def matches_type(value: Any, expected: str) -> bool:
+        if expected == "null":
+            return value is None
+        if expected == "object":
+            return isinstance(value, dict)
+        if expected == "array":
+            return isinstance(value, list)
+        if expected == "string":
+            return isinstance(value, str)
+        if expected == "integer":
+            return isinstance(value, int) and not isinstance(value, bool)
+        if expected == "number":
+            return (
+                isinstance(value, (int, float))
+                and not isinstance(value, bool)
+                and math.isfinite(float(value))
+            )
+        return False
+
+    def validate(value: Any, schema: dict[str, Any], path: str) -> None:
+        alternatives = schema.get("anyOf")
+        if alternatives:
+            for alternative in alternatives:
+                try:
+                    validate(value, alternative, path)
+                except ValueError:
+                    continue
+                return
+            fail(path, "does not match any permitted shape")
+
+        expected = schema.get("type")
+        expected_types = expected if isinstance(expected, list) else [expected]
+        if expected and not any(matches_type(value, item) for item in expected_types):
+            fail(path, f"must be {' or '.join(expected_types)}")
+        if value is None:
+            return
+        if "enum" in schema and value not in schema["enum"]:
+            fail(path, f"must be one of {schema['enum']}")
+        if isinstance(value, (int, float)) and not isinstance(value, bool):
+            if "minimum" in schema and value < schema["minimum"]:
+                fail(path, f"must be at least {schema['minimum']}")
+            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
+                fail(path, f"must be greater than {schema['exclusiveMinimum']}")
+            if "maximum" in schema and value > schema["maximum"]:
+                fail(path, f"must be at most {schema['maximum']}")
+        if isinstance(value, dict):
+            required = set(schema.get("required") or [])
+            missing = required.difference(value)
+            if missing:
+                fail(path, f"is missing required properties: {', '.join(sorted(missing))}")
+            properties = schema.get("properties") or {}
+            if schema.get("additionalProperties") is False:
+                extras = set(value).difference(properties)
+                if extras:
+                    fail(path, f"contains unsupported properties: {', '.join(sorted(extras))}")
+            for key, child in value.items():
+                if key in properties:
+                    validate(child, properties[key], f"{path}.{key}")
+        if isinstance(value, list) and "items" in schema:
+            for index, child in enumerate(value):
+                validate(child, schema["items"], f"{path}[{index}]")
+
+    validate(output, AD_EXTRACTION_JSON_SCHEMA, "$")
+
+
 class ADExtractionProvider(Protocol):
     provider_name: str
     provider_version: str
@@ -99,7 +368,11 @@ def process_pending_ad_extractions(
     directives = db.scalars(
         select(AirworthinessDirective)
         .where(AirworthinessDirective.extraction_status.in_(["not_started", "needs_review"]))
-        .options(selectinload(AirworthinessDirective.discovery_record), selectinload(AirworthinessDirective.extractions))
+        .options(
+            selectinload(AirworthinessDirective.discovery_record),
+            selectinload(AirworthinessDirective.extractions),
+            selectinload(AirworthinessDirective.publications).selectinload(ADPublication.source_document),
+        )
         .limit(limit)
     ).all()
     stats = {"seen": 0, "extracted": 0, "review_queued": 0, "approved": 0}
@@ -154,35 +427,52 @@ def extract_with_deterministic_provider(
     existing = db.scalar(
         select(ADExtraction).where(
             ADExtraction.directive_id == directive.id,
-            ADExtraction.input_content_hash == directive.source_content_hash,
+            ADExtraction.input_content_hash == extraction_input_hash(directive),
             ADExtraction.provider_name == PROVIDER_NAME,
             ADExtraction.provider_version == PROVIDER_VERSION,
             ADExtraction.schema_version == SCHEMA_VERSION,
         )
     )
     if existing:
+        ensure_persisted_source_pages(directive, existing)
         if fallback_reason and existing.raw_response:
             existing.raw_response = {**existing.raw_response, "latestFallbackReason": fallback_reason}
         ensure_review_for_extraction(db, directive, existing)
         return existing
 
     output, confidence, citations = build_extraction_output(directive)
+    if not output.get("affectedProducts"):
+        output["affectedProducts"] = affected_products_from_applicability(
+            db,
+            directive.id,
+        )
     validate_extraction_output(output)
-    status = "approved" if confidence >= REVIEW_THRESHOLD else "needs_review"
+    # The deterministic provider can classify metadata, but it cannot approve
+    # regulatory meaning from a retained full-text publication.
+    status = (
+        "approved"
+        if confidence >= REVIEW_THRESHOLD and not retained_pdf_documents(directive)
+        else "needs_review"
+    )
+    source_pages = full_text_pages_for_directive(directive)
     extraction = ADExtraction(
         directive_id=directive.id,
         provider_name=PROVIDER_NAME,
         provider_version=PROVIDER_VERSION,
         schema_version=SCHEMA_VERSION,
-        input_content_hash=directive.source_content_hash,
+        input_content_hash=extraction_input_hash(directive),
         status=status,
         confidence=confidence,
         output=output,
         citations=citations,
         raw_response={
             "mode": "deterministic",
+            "amocEnvelopeOrigin": "deterministic_provider",
             "schemaVersion": SCHEMA_VERSION,
             "fallbackReason": fallback_reason,
+            "retainedSourcePagesCached": True,
+            "retainedSourcePages": source_pages,
+            "sourcePageParser": "pypdf-native-text-v1",
         },
     )
     db.add(extraction)
@@ -199,13 +489,14 @@ def extract_with_llm_provider(
     existing = db.scalar(
         select(ADExtraction).where(
             ADExtraction.directive_id == directive.id,
-            ADExtraction.input_content_hash == directive.source_content_hash,
+            ADExtraction.input_content_hash == extraction_input_hash(directive),
             ADExtraction.provider_name == provider.provider_name,
             ADExtraction.provider_version == provider.provider_version,
             ADExtraction.schema_version == SCHEMA_VERSION,
         )
     )
     if existing:
+        ensure_persisted_source_pages(directive, existing)
         ensure_review_for_extraction(db, directive, existing)
         return existing
 
@@ -218,13 +509,26 @@ def extract_with_llm_provider(
         return extract_with_deterministic_provider(db, directive, fallback_reason=f"{type(exc).__name__}: {exc}")
 
     review_reasons = review_reasons_for_provider_output(output, confidence, raw_provider, deterministic_output)
-    status = "needs_review" if review_reasons else "approved"
+    source_pages = full_text_pages_for_directive(directive)
+    if retained_pdf_documents(directive) and not source_pages:
+        review_reasons.append("retained_pdf_text_unavailable")
+    if source_pages and not output.get("requirements"):
+        review_reasons.append("missing_full_text_requirements")
+    try:
+        validate_requirement_evidence(output, source_pages)
+    except ValueError:
+        review_reasons.append("invalid_requirement_evidence")
+    # Full-text regulatory meaning is never machine-published. Even a complete,
+    # high-confidence provider result must pass the authenticated admin review.
+    review_reasons.append("human_full_text_review_required")
+    review_reasons = sorted(set(review_reasons))
+    status = "needs_review"
     extraction = ADExtraction(
         directive_id=directive.id,
         provider_name=provider.provider_name,
         provider_version=provider.provider_version,
         schema_version=SCHEMA_VERSION,
-        input_content_hash=directive.source_content_hash,
+        input_content_hash=extraction_input_hash(directive),
         status=status,
         confidence=confidence,
         output=output,
@@ -232,8 +536,12 @@ def extract_with_llm_provider(
         raw_response={
             **raw_provider,
             "mode": "llm",
+            "amocEnvelopeOrigin": "llm_provider",
             "schemaVersion": SCHEMA_VERSION,
             "reviewReasons": review_reasons,
+            "retainedSourcePagesCached": True,
+            "retainedSourcePages": source_pages,
+            "sourcePageParser": "pypdf-native-text-v1",
         },
     )
     db.add(extraction)
@@ -327,7 +635,54 @@ def normalize_provider_payload(payload: dict[str, Any]) -> tuple[dict[str, Any],
     if not isinstance(uncertainty_reasons, list):
         raise ValueError("AD provider output uncertaintyReasons must be a list")
     raw_provider["uncertaintyReasons"] = uncertainty_reasons
-    return provider_output, float(confidence), citations, raw_provider
+    return derive_compliance_action_summaries(provider_output), float(confidence), citations, raw_provider
+
+
+def derive_compliance_action_summaries(output: dict[str, Any]) -> dict[str, Any]:
+    """Synchronize compatibility summaries with authoritative v3 structures."""
+    normalized = dict(output)
+    requirements = normalized.get("requirements")
+    if isinstance(requirements, list):
+        actions: list[str] = []
+        for requirement in requirements:
+            if not isinstance(requirement, dict):
+                continue
+            action = str(requirement.get("actionText") or "").strip()
+            if action and action not in actions:
+                actions.append(action)
+        if actions:
+            normalized["complianceActions"] = actions
+    groups = normalized.get("applicabilityGroups")
+    if isinstance(groups, list):
+        normalized["affectedProducts"] = affected_product_labels(groups)
+    return normalized
+
+
+def affected_product_labels(groups: list[Any]) -> list[str]:
+    """Derive human-readable legacy labels without parsing them back into data."""
+    labels: list[str] = []
+    for group in groups:
+        if not isinstance(group, dict):
+            continue
+        manufacturer = group.get("manufacturer") or {}
+        make = clean_schema_text(
+            manufacturer.get("normalizedName") or manufacturer.get("sourceName")
+        ) if isinstance(manufacturer, dict) else None
+        model_scope = group.get("modelApplicability") or {}
+        models = model_scope.get("models") or [] if isinstance(model_scope, dict) else []
+        if models:
+            for model in models:
+                if not isinstance(model, dict):
+                    continue
+                designation = clean_schema_text(
+                    model.get("normalizedDesignation") or model.get("sourceDesignation")
+                )
+                label = " ".join(value for value in (make, designation) if value)
+                if label and label not in labels:
+                    labels.append(label)
+        elif make and make not in labels:
+            labels.append(make)
+    return labels
 
 
 def review_reasons_for_provider_output(
@@ -339,8 +694,8 @@ def review_reasons_for_provider_output(
     reasons: list[str] = []
     if confidence < LLM_REVIEW_THRESHOLD:
         reasons.append("low_confidence")
-    if not output.get("affectedProducts"):
-        reasons.append("missing_affected_products")
+    if not output.get("applicabilityGroups"):
+        reasons.append("missing_applicability_groups")
     if not output.get("complianceActions"):
         reasons.append("missing_compliance_actions")
     if raw_provider.get("uncertaintyReasons"):
@@ -349,20 +704,53 @@ def review_reasons_for_provider_output(
         reasons.append("ad_number_disagreement")
     if normalize_list(output.get("supersedesAdNumbers")) != normalize_list(deterministic_output.get("supersedesAdNumbers")):
         reasons.append("supersession_disagreement")
-    if deterministic_output.get("affectedProducts") and normalize_list(output.get("affectedProducts")) != normalize_list(
-        deterministic_output.get("affectedProducts")
-    ):
-        reasons.append("applicability_disagreement")
     return sorted(set(reasons))
 
 
 def ensure_review_for_extraction(db: Session, directive: AirworthinessDirective, extraction: ADExtraction) -> None:
     if extraction.status == "approved":
-        directive.extraction_status = "complete"
-        directive.review_status = "approved"
-        directive.approved_at = directive.approved_at or datetime.now(timezone.utc)
-        populate_applicability_from_extraction(db, extraction)
-        return
+        decided_review = db.scalar(
+            select(ADExtractionReview).where(
+                ADExtractionReview.extraction_id == extraction.id,
+                ADExtractionReview.status.in_({"approved", "edited"}),
+            )
+        )
+        if extraction.schema_version == SCHEMA_VERSION and decided_review is None:
+            # Existing/provider-created v3 rows are not allowed to materialize
+            # without an authenticated human decision.
+            extraction.status = "needs_review"
+        elif (
+            extraction.schema_version == SCHEMA_VERSION
+            and decided_review is not None
+            and structured_output_hash(extraction.output)
+            != structured_output_hash(decided_review.decision_output)
+        ):
+            raw_response = dict(extraction.raw_response or {})
+            mismatch_history = list(raw_response.get("reviewIntegrityMismatches") or [])
+            mismatch_history.append({
+                "detectedAt": datetime.now(timezone.utc).isoformat(),
+                "reviewId": decided_review.id,
+                "reviewedOutputHash": structured_output_hash(decided_review.decision_output),
+                "extractionOutputHash": structured_output_hash(extraction.output),
+            })
+            raw_response["reviewIntegrityMismatches"] = mismatch_history
+            extraction.raw_response = raw_response
+            extraction.status = "needs_review"
+            decided_review.status = "pending"
+            decided_review.proposed_output = extraction.output
+            decided_review.decision = None
+            decided_review.decision_output = None
+            decided_review.reviewer_user_id = None
+            decided_review.reviewed_at = None
+        else:
+            directive.extraction_status = "complete"
+            directive.review_status = "approved"
+            directive.approved_at = directive.approved_at or datetime.now(timezone.utc)
+            populate_applicability_from_extraction(db, extraction)
+            from app.services.ad_recurrence import materialize_requirements_from_extraction
+
+            materialize_requirements_from_extraction(db, extraction)
+            return
 
     directive.extraction_status = "needs_review"
     directive.review_status = "pending"
@@ -379,6 +767,16 @@ def ensure_review_for_extraction(db: Session, directive: AirworthinessDirective,
     db.flush()
 
 
+def structured_output_hash(output: dict[str, Any] | None) -> str:
+    normalized = json.dumps(
+        output or {},
+        sort_keys=True,
+        separators=(",", ":"),
+        default=str,
+    )
+    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
+
+
 def build_extraction_output(directive: AirworthinessDirective) -> tuple[dict[str, Any], float, list[dict[str, str]]]:
     record = directive.discovery_record
     source_text = "\n".join(filter(None, [record.title, record.abstract, record.excerpts])) if record else directive.title
@@ -400,10 +798,13 @@ def build_extraction_output(directive: AirworthinessDirective) -> tuple[dict[str
         "title": title,
         "effectiveDate": record.effective_date.isoformat() if record and record.effective_date else None,
         "publicationDate": record.publication_date.isoformat() if record and record.publication_date else None,
+        "applicabilityGroups": [],
         "affectedProducts": [title_subject] if title_subject else [],
         "complianceActions": [],
         "complianceIntervals": [],
         "supersedesAdNumbers": superseded_numbers,
+        "requirements": [],
+        "amocProvisions": [],
         "sourceUrls": {
             "html": record.html_url if record else None,
             "pdf": record.pdf_url if record else None,
@@ -423,35 +824,671 @@ def build_extraction_output(directive: AirworthinessDirective) -> tuple[dict[str
     return output, confidence, citations
 
 
-def validate_extraction_output(output: dict[str, Any]) -> None:
+def validate_extraction_output(
+    output: dict[str, Any],
+    *,
+    require_v2_requirements: bool = True,
+    require_nonempty_requirements: bool = False,
+    require_nonempty_applicability: bool = False,
+) -> None:
     required_keys = {
         "adNumber",
         "title",
         "effectiveDate",
         "publicationDate",
-        "affectedProducts",
+        "applicabilityGroups",
         "complianceActions",
         "complianceIntervals",
         "supersedesAdNumbers",
         "sourceUrls",
+        "amocProvisions",
     }
+    if require_v2_requirements:
+        required_keys.add("requirements")
     missing = required_keys.difference(output)
     if missing:
         raise ValueError(f"AD extraction output is missing required keys: {', '.join(sorted(missing))}")
-    for list_key in ["affectedProducts", "complianceActions", "complianceIntervals", "supersedesAdNumbers"]:
+    for list_key in ["applicabilityGroups", "complianceActions", "complianceIntervals", "supersedesAdNumbers", "amocProvisions"]:
         if not isinstance(output[list_key], list):
             raise ValueError(f"AD extraction field {list_key} must be a list")
-    affected_products = [
-        str(item).strip()
-        for item in output["affectedProducts"]
-        if str(item).strip()
-    ]
-    if not affected_products:
-        raise ValueError(
-            "AD extraction field affectedProducts must contain at least one attributable product"
-        )
+    validate_applicability_groups(
+        output["applicabilityGroups"],
+        require_nonempty=require_nonempty_applicability,
+    )
     if not isinstance(output["sourceUrls"], dict):
         raise ValueError("AD extraction field sourceUrls must be an object")
+    if "requirements" not in output:
+        return
+    if not isinstance(output["requirements"], list):
+        raise ValueError("AD extraction field requirements must be a list")
+    if require_nonempty_requirements and not output["requirements"]:
+        raise ValueError("AD extraction v3 must include at least one compliance requirement")
+    group_keys = {
+        clean_schema_text(group.get("groupKey"))
+        for group in output["applicabilityGroups"]
+        if isinstance(group, dict)
+    }
+    for index, requirement in enumerate(output["requirements"]):
+        validate_requirement(requirement, index, group_keys=group_keys)
+    for index, provision in enumerate(output["amocProvisions"]):
+        validate_amoc_provision(provision, index)
+
+
+def validate_applicability_groups(groups: Any, *, require_nonempty: bool) -> None:
+    if not isinstance(groups, list):
+        raise ValueError("AD extraction field applicabilityGroups must be a list")
+    if require_nonempty and not groups:
+        raise ValueError("AD extraction v3 must include at least one applicability group")
+    seen_keys: set[str] = set()
+    for index, group in enumerate(groups):
+        if not isinstance(group, dict):
+            raise ValueError(f"AD applicability group {index} must be an object")
+        required = {
+            "groupKey", "productType", "productSubtype", "manufacturer", "modelApplicability",
+            "serialNumberApplicability", "equipmentCombinationLogic", "equipmentConditions", "conditions",
+            "citations", "confidence", "uncertaintyReasons",
+        }
+        missing = required.difference(group)
+        if missing:
+            raise ValueError(f"AD applicability group {index} is missing: {', '.join(sorted(missing))}")
+        group_key = clean_schema_text(group.get("groupKey"))
+        if not group_key:
+            raise ValueError(f"AD applicability group {index} must include groupKey")
+        if group_key in seen_keys:
+            raise ValueError(f"AD applicability group key {group_key} is duplicated")
+        seen_keys.add(group_key)
+        if group.get("productType") not in {
+            "aircraft", "rotorcraft", "engine", "propeller", "appliance", "equipment", "other",
+        }:
+            raise ValueError(f"AD applicability group {index} has an unsupported productType")
+        manufacturer = group.get("manufacturer")
+        if not isinstance(manufacturer, dict) or not clean_schema_text(manufacturer.get("sourceName")):
+            raise ValueError(f"AD applicability group {index} must include manufacturer.sourceName")
+        model_scope = group.get("modelApplicability")
+        if not isinstance(model_scope, dict):
+            raise ValueError(f"AD applicability group {index} modelApplicability must be an object")
+        if model_scope.get("kind") not in {"listed", "all", "expression", "unknown"}:
+            raise ValueError(f"AD applicability group {index} has unsupported model applicability")
+        models = model_scope.get("models")
+        if not isinstance(models, list):
+            raise ValueError(f"AD applicability group {index} models must be a list")
+        if model_scope.get("kind") == "listed" and not models:
+            raise ValueError(f"AD applicability group {index} with listed models must include a model")
+        for model_index, model in enumerate(models):
+            if not isinstance(model, dict) or not clean_schema_text(model.get("sourceDesignation")):
+                raise ValueError(
+                    f"AD applicability group {index} model {model_index} must include sourceDesignation"
+                )
+            if not isinstance(model.get("aliases"), list):
+                raise ValueError(f"AD applicability group {index} model {model_index} aliases must be a list")
+        serial_scope = group.get("serialNumberApplicability")
+        if not isinstance(serial_scope, dict) or serial_scope.get("kind") not in {
+            "all", "values", "ranges", "expression", "unknown",
+        }:
+            raise ValueError(f"AD applicability group {index} has invalid serialNumberApplicability")
+        for field in ("values", "ranges", "excludedValues"):
+            if not isinstance(serial_scope.get(field), list):
+                raise ValueError(f"AD applicability group {index} serial field {field} must be a list")
+        for field in ("equipmentConditions", "conditions", "citations", "uncertaintyReasons"):
+            if not isinstance(group.get(field), list):
+                raise ValueError(f"AD applicability group {index} field {field} must be a list")
+        validate_page_citations(group.get("citations"), f"AD applicability group {index}")
+        for condition_index, condition in enumerate(group.get("equipmentConditions") or []):
+            if not isinstance(condition, dict):
+                raise ValueError(
+                    f"AD applicability group {index} equipment condition {condition_index} must be an object"
+                )
+            condition_manufacturer = condition.get("manufacturer")
+            if not isinstance(condition_manufacturer, dict) or not clean_schema_text(condition_manufacturer.get("sourceName")):
+                raise ValueError(
+                    f"AD applicability group {index} equipment condition {condition_index} must include manufacturer.sourceName"
+                )
+            validate_page_citations(
+                condition.get("citations"),
+                f"AD applicability group {index} equipment condition {condition_index}",
+            )
+
+
+def affected_products_from_applicability(db: Session, directive_id: str) -> list[str]:
+    targets = db.scalars(
+        select(ApplicabilityTarget)
+        .join(
+            ADTargetApplicability,
+            ADTargetApplicability.target_id == ApplicabilityTarget.id,
+        )
+        .where(
+            ADTargetApplicability.directive_id == directive_id,
+            ADTargetApplicability.status.in_({"current", "active", "unknown", "historical"}),
+        )
+        .distinct()
+    ).all()
+    products = []
+    for target in targets:
+        identity = " ".join(
+            value.strip()
+            for value in (target.make, target.model)
+            if value and value.strip()
+        )
+        label = identity or target.product_subtype or target.product_type
+        if label and label not in products:
+            products.append(label)
+    return sorted(products)
+
+
+def validate_requirement(requirement: Any, index: int, *, group_keys: set[str] | None = None) -> None:
+    if not isinstance(requirement, dict):
+        raise ValueError(f"AD extraction requirement {index} must be an object")
+    required = {
+        "requirementKey", "applicabilityGroupKeys", "requirementType", "actionText", "initialThresholds",
+        "recurringTriggers", "combinationLogic", "conditions", "terminatingAction",
+        "citations", "confidence", "uncertaintyReasons",
+    }
+    missing = required.difference(requirement)
+    if missing:
+        raise ValueError(f"AD extraction requirement {index} is missing: {', '.join(sorted(missing))}")
+    if not str(requirement["actionText"]).strip():
+        raise ValueError(f"AD extraction requirement {index} must include actionText")
+    if requirement["requirementType"] not in {
+        "one_time", "recurring", "alternative", "conditional", "installation_prohibition"
+    }:
+        raise ValueError(f"AD extraction requirement {index} has an unsupported requirementType")
+    if requirement["combinationLogic"] not in {"all", "whichever_first", "whichever_later", "alternative"}:
+        raise ValueError(f"AD extraction requirement {index} has unsupported combinationLogic")
+    for field in ("initialThresholds", "recurringTriggers", "conditions", "uncertaintyReasons"):
+        if not isinstance(requirement[field], list):
+            raise ValueError(f"AD extraction requirement {index} field {field} must be a list")
+    for threshold in requirement["initialThresholds"] + requirement["recurringTriggers"]:
+        if not isinstance(threshold, dict) or not all(
+            key in threshold for key in ("metric", "value", "unit", "anchorKind", "sourceText")
+        ):
+            raise ValueError(f"AD extraction requirement {index} has an invalid threshold or trigger")
+    applicability_group_keys = requirement.get("applicabilityGroupKeys")
+    if not isinstance(applicability_group_keys, list) or not applicability_group_keys:
+        raise ValueError(f"AD extraction requirement {index} must include applicabilityGroupKeys")
+    referenced_keys = {
+        clean_schema_text(key) for key in applicability_group_keys if clean_schema_text(key)
+    }
+    unknown_keys = referenced_keys.difference(group_keys or set())
+    if unknown_keys:
+        raise ValueError(
+            f"AD extraction requirement {index} references unknown applicability group(s): {', '.join(sorted(unknown_keys))}"
+        )
+    validate_page_citations(requirement.get("citations"), f"AD extraction requirement {index}")
+
+
+def validate_page_citations(citations: Any, label: str) -> None:
+    if not isinstance(citations, list) or not citations:
+        raise ValueError(f"{label} must include page citations")
+    for citation in citations:
+        if not isinstance(citation, dict) or not citation.get("sourceDocumentId") or not citation.get("pageNumber") or not citation.get("text"):
+            raise ValueError(f"{label} has an invalid page citation")
+
+
+def validate_amoc_provision(provision: Any, index: int) -> None:
+    if not isinstance(provision, dict):
+        raise ValueError(f"AD AMOC provision {index} must be an object")
+    required = {
+        "provisionKey", "authorityText", "approvingAuthority", "submissionInstructions",
+        "conditions", "citations", "confidence", "uncertaintyReasons",
+    }
+    missing = required.difference(provision)
+    if missing:
+        raise ValueError(
+            f"AD AMOC provision {index} is missing: {', '.join(sorted(missing))}"
+        )
+    if not clean_schema_text(provision.get("provisionKey")):
+        raise ValueError(f"AD AMOC provision {index} must include provisionKey")
+    if not clean_schema_text(provision.get("authorityText")):
+        raise ValueError(f"AD AMOC provision {index} must include authorityText")
+    for field in ("conditions", "uncertaintyReasons"):
+        if not isinstance(provision.get(field), list):
+            raise ValueError(f"AD AMOC provision {index} field {field} must be a list")
+    validate_page_citations(provision.get("citations"), f"AD AMOC provision {index}")
+
+
+def clean_schema_text(value: Any) -> str | None:
+    text = " ".join(str(value or "").strip().split())
+    return text or None
+
+
+def validate_requirement_evidence(output: dict[str, Any], source_pages: list[dict[str, Any]]) -> None:
+    page_index = {
+        (page["sourceDocumentId"], page["pageNumber"]): normalize_regulatory_text(page["text"])
+        for page in source_pages
+    }
+    validate_top_level_date_evidence(output, source_pages)
+    for index, group in enumerate(output.get("applicabilityGroups") or []):
+        group_citations = validate_citations_against_pages(
+            group.get("citations") or [],
+            page_index,
+            f"AD applicability group {index}",
+        )
+        validate_applicability_evidence(group, group_citations, index)
+        for condition_index, condition in enumerate(group.get("equipmentConditions") or []):
+            condition_citations = validate_citations_against_pages(
+                condition.get("citations") or [],
+                page_index,
+                f"AD applicability group {index} equipment condition {condition_index}",
+            )
+            validate_equipment_condition_evidence(
+                condition,
+                condition_citations,
+                f"AD applicability group {index} equipment condition {condition_index}",
+            )
+    for index, requirement in enumerate(output.get("requirements") or []):
+        normalized_citations: list[str] = []
+        normalized_citations.extend(validate_citations_against_pages(
+            requirement.get("citations") or [],
+            page_index,
+            f"AD extraction requirement {index}",
+        ))
+        action_text = normalize_regulatory_text(requirement.get("actionText"))
+        combined_citations = " ".join(normalized_citations)
+        if action_text and not (
+            any(action_text in citation for citation in normalized_citations)
+            or action_text in combined_citations
+        ):
+            raise ValueError(
+                f"AD extraction requirement {index} actionText must preserve wording from a page citation"
+            )
+        timings = [
+            ("initial", timing)
+            for timing in requirement.get("initialThresholds") or []
+        ] + [
+            ("recurring", timing)
+            for timing in requirement.get("recurringTriggers") or []
+        ]
+        for timing_index, (trigger_kind, timing) in enumerate(timings):
+            validate_timing_evidence(
+                timing,
+                normalized_citations,
+                f"AD extraction requirement {index} timing {timing_index}",
+                trigger_kind=trigger_kind,
+            )
+        validate_requirement_semantics(
+            requirement,
+            combined_citations,
+            f"AD extraction requirement {index}",
+        )
+        for condition_index, condition in enumerate(requirement.get("conditions") or []):
+            require_cited_wording(
+                condition,
+                normalized_citations,
+                f"AD extraction requirement {index} condition {condition_index}",
+            )
+        terminating_action = normalize_regulatory_text(requirement.get("terminatingAction"))
+        if terminating_action and not (
+            any(terminating_action in citation for citation in normalized_citations)
+            or terminating_action in combined_citations
+        ):
+            raise ValueError(
+                f"AD extraction requirement {index} terminatingAction must preserve wording from a page citation"
+            )
+    for index, provision in enumerate(output.get("amocProvisions") or []):
+        normalized_citations = validate_citations_against_pages(
+            provision.get("citations") or [],
+            page_index,
+            f"AD AMOC provision {index}",
+        )
+        authority_text = normalize_regulatory_text(provision.get("authorityText"))
+        if not authority_text or not any(
+            authority_text in citation for citation in normalized_citations
+        ):
+            raise ValueError(
+                f"AD AMOC provision {index} authorityText must preserve wording from a page citation"
+            )
+        for field in ("approvingAuthority", "submissionInstructions"):
+            require_cited_wording(
+                provision.get(field),
+                normalized_citations,
+                f"AD AMOC provision {index} {field}",
+                allow_empty=True,
+            )
+        for condition_index, condition in enumerate(provision.get("conditions") or []):
+            require_cited_wording(
+                condition,
+                normalized_citations,
+                f"AD AMOC provision {index} condition {condition_index}",
+            )
+
+
+def validate_applicability_evidence(
+    group: dict[str, Any],
+    citations: list[str],
+    index: int,
+) -> None:
+    label = f"AD applicability group {index}"
+    validate_product_type_semantics(group, citations, label)
+    manufacturer = group.get("manufacturer") or {}
+    require_cited_wording(
+        manufacturer.get("sourceName"),
+        citations,
+        f"{label} manufacturer.sourceName",
+    )
+    require_source_identity_or_null(
+        manufacturer.get("sourceName"),
+        manufacturer.get("normalizedName"),
+        f"{label} manufacturer.normalizedName",
+    )
+    model_scope = group.get("modelApplicability") or {}
+    validate_model_scope_semantics(model_scope, group, label)
+    require_cited_wording(
+        model_scope.get("sourceText"),
+        citations,
+        f"{label} modelApplicability.sourceText",
+    )
+    for model_index, model in enumerate(model_scope.get("models") or []):
+        require_cited_wording(
+            model.get("sourceDesignation") if isinstance(model, dict) else None,
+            citations,
+            f"{label} model {model_index} sourceDesignation",
+        )
+        if isinstance(model, dict):
+            require_source_identity_or_null(
+                model.get("sourceDesignation"),
+                model.get("normalizedDesignation"),
+                f"{label} model {model_index} normalizedDesignation",
+            )
+    serial_scope = group.get("serialNumberApplicability") or {}
+    validate_serial_scope_semantics(serial_scope, group, label)
+    serial_source = normalize_regulatory_text(serial_scope.get("sourceText"))
+    require_cited_wording(
+        serial_scope.get("sourceText"),
+        citations,
+        f"{label} serialNumberApplicability.sourceText",
+    )
+    for value in serial_scope.get("values") or []:
+        if normalize_regulatory_text(value) not in serial_source:
+            raise ValueError(f"{label} serial value is not present in serial sourceText")
+    for serial_range in serial_scope.get("ranges") or []:
+        for endpoint in (serial_range.get("start"), serial_range.get("end")):
+            if endpoint and normalize_regulatory_text(endpoint) not in serial_source:
+                raise ValueError(f"{label} serial range endpoint is not present in serial sourceText")
+    for value in serial_scope.get("excludedValues") or []:
+        if normalize_regulatory_text(value) not in serial_source:
+            raise ValueError(f"{label} excluded serial is not present in serial sourceText")
+    for condition_index, condition in enumerate(group.get("conditions") or []):
+        require_cited_wording(
+            condition,
+            citations,
+            f"{label} condition {condition_index}",
+        )
+
+
+def validate_equipment_condition_evidence(
+    condition: dict[str, Any],
+    citations: list[str],
+    label: str,
+) -> None:
+    manufacturer = condition.get("manufacturer") or {}
+    require_cited_wording(
+        manufacturer.get("sourceName"),
+        citations,
+        f"{label} manufacturer.sourceName",
+    )
+    require_source_identity_or_null(
+        manufacturer.get("sourceName"),
+        manufacturer.get("normalizedName"),
+        f"{label} manufacturer.normalizedName",
+    )
+    model = condition.get("model") or {}
+    if model:
+        require_cited_wording(
+            model.get("sourceDesignation"),
+            citations,
+            f"{label} model.sourceDesignation",
+        )
+        require_source_identity_or_null(
+            model.get("sourceDesignation"),
+            model.get("normalizedDesignation"),
+            f"{label} model.normalizedDesignation",
+        )
+    require_cited_wording(
+        condition.get("conditionText"),
+        citations,
+        f"{label} conditionText",
+    )
+    for version in condition.get("softwareVersions") or []:
+        require_cited_wording(version, citations, f"{label} softwareVersion")
+
+
+def validate_product_type_semantics(
+    group: dict[str, Any],
+    citations: list[str],
+    label: str,
+) -> None:
+    product_type = normalize_regulatory_text(group.get("productType"))
+    combined = " ".join(citations)
+    supported_terms = {
+        "aircraft": ("aircraft", "airplane"),
+        "airplane": ("aircraft", "airplane"),
+        "rotorcraft": ("rotorcraft", "helicopter"),
+        "engine": ("engine",),
+        "propeller": ("propeller",),
+        "appliance": ("appliance", "equipment"),
+    }
+    terms = supported_terms.get(product_type)
+    if terms and not any(term in combined for term in terms):
+        raise ValueError(f"{label} productType is not supported by cited text")
+    subtype = normalize_regulatory_text(group.get("productSubtype"))
+    if subtype and subtype not in combined:
+        raise ValueError(f"{label} productSubtype is not supported by cited text")
+
+
+def require_cited_wording(
+    value: Any,
+    citations: list[str],
+    label: str,
+    *,
+    allow_empty: bool = False,
+) -> None:
+    normalized = normalize_regulatory_text(value)
+    if not normalized:
+        if allow_empty:
+            return
+        raise ValueError(f"{label} must preserve wording from a page citation")
+    combined = " ".join(citations)
+    if normalized not in combined:
+        raise ValueError(f"{label} must preserve wording from a page citation")
+
+
+def require_source_identity_or_null(
+    source_value: Any,
+    normalized_value: Any,
+    label: str,
+) -> None:
+    """Do not let an unreviewed canonicalization replace source identity."""
+
+    normalized = normalize_regulatory_text(normalized_value)
+    if not normalized:
+        return
+    source = normalize_regulatory_text(source_value)
+    if normalized != source:
+        raise ValueError(
+            f"{label} must be null or equal the cited source identity until a reviewed canonical identity mapping exists"
+        )
+
+
+def validate_timing_evidence(
+    timing: dict[str, Any],
+    normalized_citations: list[str],
+    label: str,
+    *,
+    trigger_kind: str,
+) -> None:
+    source_text = normalize_regulatory_text(timing.get("sourceText"))
+    combined_citations = " ".join(normalized_citations)
+    if not source_text or source_text not in combined_citations:
+        raise ValueError(f"{label} sourceText must preserve wording from a page citation")
+    try:
+        decimal_value = Decimal(str(timing.get("value")))
+        value_text = format(decimal_value.normalize(), "f")
+    except (InvalidOperation, TypeError, ValueError):
+        raise ValueError(f"{label} value must be numeric") from None
+    if value_text and value_text not in source_text.split():
+        raise ValueError(f"{label} value is not present in its sourceText")
+    unit = str(timing.get("unit") or "").lower()
+    unit_stems = {
+        "days": ("day",),
+        "months": ("month", "year"),
+        "hours": ("hour",),
+        "cycles": ("cycle",),
+    }
+    if unit in unit_stems and not any(stem in source_text for stem in unit_stems[unit]):
+        raise ValueError(f"{label} unit is not present in its sourceText")
+    anchor_kind = str(timing.get("anchorKind") or "")
+    anchor_terms = {
+        "effective_date": ("effective date",),
+        "installation": ("install",),
+        "manufacture": ("manufactur",),
+        "last_compliance": (
+            "last compliance",
+            "last inspection",
+            "time since last",
+            "thereafter",
+            "repetitively",
+            "interval",
+            "every",
+        ),
+    }
+    if anchor_kind == "unknown":
+        raise ValueError(f"{label} anchorKind unknown requires adjudication")
+    if anchor_kind not in anchor_terms:
+        raise ValueError(f"{label} has unsupported anchorKind")
+    if not any(term in source_text for term in anchor_terms[anchor_kind]):
+        raise ValueError(f"{label} anchorKind is not supported by its sourceText")
+    if trigger_kind == "initial" and anchor_kind == "last_compliance" and not any(
+        term in source_text for term in ("last compliance", "last inspection")
+    ):
+        raise ValueError(f"{label} initial last_compliance anchor is not explicit")
+
+
+def validate_model_scope_semantics(
+    model_scope: dict[str, Any],
+    group: dict[str, Any],
+    label: str,
+) -> None:
+    kind = str(model_scope.get("kind") or "")
+    models = model_scope.get("models") or []
+    source_text = normalize_regulatory_text(model_scope.get("sourceText"))
+    uncertainty = group.get("uncertaintyReasons") or []
+    if kind == "listed" and not models:
+        raise ValueError(f"{label} listed model scope must include cited models")
+    if kind == "all":
+        if models:
+            raise ValueError(f"{label} all-model scope cannot also list selected models")
+        if "all" not in source_text or not any(
+            term in source_text
+            for term in ("model", "airplane", "aircraft", "engine", "propeller")
+        ):
+            raise ValueError(f"{label} all-model scope is not explicit in sourceText")
+    if kind in {"expression", "unknown"} and not uncertainty:
+        raise ValueError(f"{label} unresolved model scope requires uncertaintyReasons")
+
+
+def validate_serial_scope_semantics(
+    serial_scope: dict[str, Any],
+    group: dict[str, Any],
+    label: str,
+) -> None:
+    kind = str(serial_scope.get("kind") or "")
+    values = serial_scope.get("values") or []
+    ranges = serial_scope.get("ranges") or []
+    source_text = normalize_regulatory_text(serial_scope.get("sourceText"))
+    uncertainty = group.get("uncertaintyReasons") or []
+    if kind == "all":
+        if values or ranges:
+            raise ValueError(f"{label} all-serial scope cannot also list selected serials")
+        if "all" not in source_text or not any(
+            term in source_text for term in ("serial", "s n")
+        ):
+            raise ValueError(f"{label} all-serial scope is not explicit in sourceText")
+    elif kind == "values" and not values:
+        raise ValueError(f"{label} values serial scope must include cited values")
+    elif kind == "ranges" and not ranges:
+        raise ValueError(f"{label} ranges serial scope must include cited ranges")
+    elif kind in {"expression", "unknown"} and not uncertainty:
+        raise ValueError(f"{label} unresolved serial scope requires uncertaintyReasons")
+
+
+def validate_requirement_semantics(
+    requirement: dict[str, Any],
+    cited_text: str,
+    label: str,
+) -> None:
+    requirement_type = str(requirement.get("requirementType") or "")
+    recurring = requirement.get("recurringTriggers") or []
+    conditions = requirement.get("conditions") or []
+    action_text = normalize_regulatory_text(requirement.get("actionText"))
+    if requirement_type == "recurring" and not recurring:
+        raise ValueError(f"{label} recurring type requires a recurring trigger")
+    if requirement_type == "one_time" and recurring:
+        raise ValueError(f"{label} one_time type cannot contain recurring triggers")
+    if requirement_type == "installation_prohibition" and not any(
+        phrase in action_text for phrase in ("do not install", "must not install", "may not install")
+    ):
+        raise ValueError(f"{label} installation_prohibition is not explicit in actionText")
+    if requirement_type == "conditional" and not conditions:
+        raise ValueError(f"{label} conditional type requires cited conditions")
+
+    logic = str(requirement.get("combinationLogic") or "")
+    if logic == "whichever_first" and "whichever occurs first" not in cited_text:
+        raise ValueError(f"{label} whichever_first logic is not explicit in cited text")
+    if logic == "whichever_later" and "whichever occurs later" not in cited_text:
+        raise ValueError(f"{label} whichever_later logic is not explicit in cited text")
+    if logic == "alternative" and " or " not in f" {cited_text} ":
+        raise ValueError(f"{label} alternative logic is not explicit in cited text")
+
+
+def validate_top_level_date_evidence(
+    output: dict[str, Any],
+    source_pages: list[dict[str, Any]],
+) -> None:
+    """Bind reviewed date fields to the retained official text.
+
+    Effective date drives calendar due-state anchors. Publication date is also
+    retained here so both reviewed dates share one provenance rule.
+    """
+
+    source_text = normalize_regulatory_text(
+        " ".join(str(page.get("text") or "") for page in source_pages)
+    )
+    for field in ("effectiveDate",):
+        raw_value = output.get(field)
+        if raw_value in (None, ""):
+            continue
+        try:
+            parsed = date.fromisoformat(str(raw_value))
+        except ValueError:
+            raise ValueError(f"AD extraction {field} must be an ISO date") from None
+        month_name = parsed.strftime("%B")
+        variants = {
+            str(raw_value),
+            f"{month_name} {parsed.day}, {parsed.year}",
+            f"{month_name} {parsed.day} {parsed.year}",
+            f"{parsed.month}/{parsed.day}/{parsed.year}",
+        }
+        if not any(normalize_regulatory_text(value) in source_text for value in variants):
+            raise ValueError(
+                f"AD extraction {field} must be present in retained official source text"
+            )
+
+
+def validate_citations_against_pages(
+    citations: list[dict[str, Any]],
+    page_index: dict[tuple[Any, Any], str],
+    label: str,
+) -> list[str]:
+    normalized_citations: list[str] = []
+    for citation in citations:
+        page_text = page_index.get((citation.get("sourceDocumentId"), citation.get("pageNumber")))
+        cited_text = normalize_regulatory_text(citation.get("text"))
+        if page_text is None:
+            raise ValueError(f"{label} cites a page outside retained evidence")
+        if not cited_text or cited_text not in page_text:
+            raise ValueError(f"{label} citation text is not present on the retained page")
+        normalized_citations.append(cited_text)
+    return normalized_citations
 
 
 def subject_from_title(title: str | None) -> str | None:
@@ -463,6 +1500,18 @@ def subject_from_title(title: str | None) -> str | None:
 
 
 def source_text_for_directive(directive: AirworthinessDirective) -> str:
+    pages = full_text_pages_for_directive(directive)
+    if pages:
+        return "\n\n".join(
+            f"[Source document {page['sourceDocumentId']}, page {page['pageNumber']}]\n{page['text']}"
+            for page in pages
+        )
+    documents = retained_pdf_documents(directive)
+    if documents:
+        return "\n".join(
+            f"[Retained PDF {document.id} could not produce reliable native text; extraction requires adjudication.]"
+            for document in documents
+        )
     record = directive.discovery_record
     if record:
         fields = [
@@ -480,6 +1529,586 @@ def source_text_for_directive(directive: AirworthinessDirective) -> str:
     return directive.title
 
 
+def full_text_pages_for_directive(directive: AirworthinessDirective) -> list[dict[str, Any]]:
+    """Read retained primary PDFs and preserve page boundaries for extraction/review."""
+    for extraction in reversed(getattr(directive, "extractions", []) or []):
+        cached, pages = persisted_source_pages(directive, extraction)
+        if cached:
+            return pages
+    return extract_full_text_pages(directive)
+
+
+def full_text_pages_for_extraction(extraction: ADExtraction) -> list[dict[str, Any]]:
+    cached, pages = persisted_source_pages(extraction.directive, extraction)
+    if cached:
+        return pages
+    return extract_full_text_pages(extraction.directive)
+
+
+def ensure_persisted_source_pages(
+    directive: AirworthinessDirective,
+    extraction: ADExtraction,
+) -> list[dict[str, Any]]:
+    cached, pages = persisted_source_pages(directive, extraction)
+    if cached:
+        return pages
+    pages = extract_full_text_pages(directive)
+    extraction.raw_response = {
+        **(extraction.raw_response or {}),
+        "retainedSourcePagesCached": True,
+        "retainedSourcePages": pages,
+        "sourcePageParser": "pypdf-native-text-v1",
+    }
+    return pages
+
+
+def persisted_source_pages(
+    directive: AirworthinessDirective,
+    extraction: ADExtraction,
+) -> tuple[bool, list[dict[str, Any]]]:
+    raw_response = extraction.raw_response or {}
+    if not raw_response.get("retainedSourcePagesCached"):
+        return False, []
+    pages = raw_response.get("retainedSourcePages")
+    if not isinstance(pages, list):
+        return False, []
+    documents = {document.id: document for document in retained_pdf_documents(directive)}
+    document_hashes = {document_id: document.content_hash for document_id, document in documents.items()}
+    derived_text: dict[tuple[str, int], str] = {}
+    try:
+        for document in documents.values():
+            payload = verified_retained_document_bytes(document)
+            reader = PdfReader(io.BytesIO(payload))
+            document_pages = []
+            for page_number, page in enumerate(reader.pages, start=1):
+                text = (page.extract_text() or "").strip()
+                if text:
+                    document_pages.append({
+                        "sourceDocumentId": document.id,
+                        "pageNumber": page_number,
+                        "text": text,
+                    })
+            if getattr(document, "source_type", None) == "issue_pdf":
+                document_pages = bounded_issue_pages(
+                    document_pages,
+                    ad_number=getattr(directive, "ad_number", None),
+                    title=getattr(directive, "title", None),
+                )
+            derived_text.update({
+                (page["sourceDocumentId"], page["pageNumber"]): page["text"]
+                for page in document_pages
+            })
+    except Exception:
+        return False, []
+    validated: list[dict[str, Any]] = []
+    for page in pages:
+        if not isinstance(page, dict):
+            return False, []
+        document_id = page.get("sourceDocumentId")
+        if document_id not in document_hashes or page.get("contentHash") != document_hashes[document_id]:
+            return False, []
+        if not isinstance(page.get("pageNumber"), int) or not isinstance(page.get("text"), str):
+            return False, []
+        if page["text"] != derived_text.get((document_id, page["pageNumber"])):
+            return False, []
+        validated.append(page)
+    if documents and {
+        (page["sourceDocumentId"], page["pageNumber"])
+        for page in validated
+    } != set(derived_text):
+        return False, []
+    return True, validated
+
+
+def extract_full_text_pages(directive: AirworthinessDirective) -> list[dict[str, Any]]:
+    """Perform the expensive retained-PDF read used during preparation only."""
+    settings = get_settings()
+    pages: list[dict[str, Any]] = []
+    seen: set[str] = set()
+    for document in retained_pdf_documents(directive):
+        if document.id in seen:
+            continue
+        seen.add(document.id)
+        try:
+            payload = verified_retained_document_bytes(document, settings=settings)
+            actual_hash = hashlib.sha256(payload).hexdigest()
+            reader = PdfReader(io.BytesIO(payload))
+            document_pages: list[dict[str, Any]] = []
+            for page_number, page in enumerate(reader.pages, start=1):
+                text = (page.extract_text() or "").strip()
+                if text:
+                    document_pages.append({
+                        "sourceDocumentId": document.id,
+                        "contentHash": actual_hash,
+                        "pageNumber": page_number,
+                        "text": text,
+                    })
+            if getattr(document, "source_type", None) == "issue_pdf":
+                document_pages = bounded_issue_pages(
+                    document_pages,
+                    ad_number=getattr(directive, "ad_number", None),
+                    title=getattr(directive, "title", None),
+                )
+            pages.extend(document_pages)
+        except Exception:
+            # Retention and reconciliation remain authoritative; unreadable source
+            # documents must route the extraction to review, not disappear.
+            continue
+    return pages
+
+
+def verified_retained_document_bytes(document: Any, *, settings: Any | None = None) -> bytes:
+    """Read once and return only the exact retained bytes whose identity verifies."""
+
+    payload = read_stored_file_bytes(
+        settings=settings or get_settings(),
+        storage_backend=document.storage_backend,
+        storage_key=document.storage_key,
+    )
+    if (
+        hashlib.sha256(payload).hexdigest() != document.content_hash
+        or len(payload) != document.storage_bytes
+    ):
+        raise ValueError("Retained AD source document hash or size mismatch")
+    return payload
+
+
+def retained_document_bytes_match(document: Any) -> bool:
+    try:
+        verified_retained_document_bytes(document)
+    except Exception:
+        return False
+    return True
+
+
+def retained_pdf_documents(directive: AirworthinessDirective) -> list[Any]:
+    documents: list[Any] = []
+    seen: set[str] = set()
+    for publication in getattr(directive, "publications", []) or []:
+        document = publication.source_document
+        if document is None or document.id in seen or document.media_type != "application/pdf":
+            continue
+        seen.add(document.id)
+        documents.append(document)
+    return documents
+
+
+def bounded_issue_pages(
+    pages: list[dict[str, Any]],
+    *,
+    ad_number: str | None,
+    title: str | None = None,
+    context_pages: int = 0,
+) -> list[dict[str, Any]]:
+    """Keep only one AD section from a complete Federal Register issue.
+
+    Federal Register pages routinely contain the end of one rule and the start
+    of another. Returning whole neighboring pages therefore creates false
+    evidence. This function slices the page text from the target Part 39
+    heading through that rule's FR Doc footer and preserves page provenance.
+    ``context_pages`` remains in the signature for backwards compatibility but
+    is intentionally ignored.
+    """
+    _ = context_pages
+    if not ad_number:
+        return []
+    normalized = ad_number.upper().removeprefix("AD ").strip()
+    parts = normalized.split("-")
+    if len(parts) != 3:
+        return []
+    year, sequence, item = (re.escape(part) for part in parts)
+    short_year = re.escape(parts[0][2:]) if len(parts[0]) == 4 else year
+    separator = r"[\s\-‐‑‒–—±]*"
+    identifier_expression = rf"(?:{year}|{short_year}){separator}{sequence}{separator}{item}"
+    identifier_pattern = re.compile(
+        rf"\b(?:AD\s*)?{identifier_expression}\b",
+        re.IGNORECASE,
+    )
+    if not pages:
+        return []
+
+    separator_token = "\n\n<<<PAPRNAV_PAGE_BREAK>>>\n\n"
+    page_offsets: list[tuple[int, int]] = []
+    chunks: list[str] = []
+    cursor = 0
+    for page in pages:
+        text = page.get("text", "")
+        chunks.append(text)
+        page_offsets.append((cursor, cursor + len(text)))
+        cursor += len(text) + len(separator_token)
+    combined = separator_token.join(chunks)
+
+    formal_matches = [
+        match
+        for pattern in formal_ad_identity_patterns(identifier_expression)
+        if (match := pattern.search(combined)) is not None
+    ]
+    identifier_match = min(formal_matches, key=lambda match: match.start()) if formal_matches else identifier_pattern.search(combined)
+    anchor_start = identifier_match.start() if identifier_match else None
+    if anchor_start is None and title:
+        title_terms = {
+            term.lower()
+            for term in re.findall(r"[A-Za-z0-9]+", title)
+            if len(term) >= 5
+            and term.lower() not in {"airworthiness", "directive", "directives"}
+        }
+        required_hits = max(1, min(2, len(title_terms)))
+        if title_terms:
+            lowered = combined.lower()
+            candidate_offsets = [lowered.find(term) for term in title_terms]
+            candidate_offsets = [offset for offset in candidate_offsets if offset >= 0]
+            if len(candidate_offsets) >= required_hits:
+                anchor_start = min(candidate_offsets)
+    if anchor_start is None:
+        return []
+
+    heading_patterns = (
+        re.compile(r"14\s+CFR\s+Part\s+39", re.IGNORECASE),
+        re.compile(r"PART\s+39\s*[\-‐‑‒–—]+\s*AIRWORTHINESS\s+DIRECTIVES", re.IGNORECASE),
+        re.compile(r"\[Docket\s+No\.[^\]]+\]", re.IGNORECASE),
+    )
+    section_start = anchor_start
+    search_floor = max(0, anchor_start - 5000)
+    prior_footers = list(
+        re.finditer(r"\[(?:FR|PR)\s+Doc\.[^\]]+\]", combined[search_floor:anchor_start], re.IGNORECASE)
+    )
+    if prior_footers:
+        search_floor += prior_footers[-1].end()
+    prefix = combined[search_floor:anchor_start]
+    heading_offsets = [
+        search_floor + match.start()
+        for pattern in heading_patterns
+        for match in pattern.finditer(prefix)
+    ]
+    if heading_offsets:
+        section_start = min(heading_offsets)
+
+    footer = re.search(
+        r"\[(?:FR|PR)\s+Doc\.[^\]]+\]",
+        combined[anchor_start:],
+        re.IGNORECASE,
+    )
+    if footer is None:
+        # A missing/mangled footer is not permission to admit the remainder of
+        # a Federal Register issue. The tail can contain an unrelated AD whose
+        # genuine wording would otherwise become citation-eligible.
+        return []
+    footer_start = anchor_start + footer.start()
+    intervening_text = combined[anchor_start + 1:footer_start]
+    intervening_agency_boundary = re.search(
+        r"(?:^|\n)\s*(?:"
+        r"DEPARTMENT\s+OF\s+[A-Z][A-Z &-]+"
+        r"|[A-Z][A-Z &-]+\s+(?:AGENCY|ADMINISTRATION|COMMISSION|BOARD|OFFICE)"
+        r")\s*(?:\n|$)",
+        intervening_text,
+    )
+    later_part39_numbers = [
+        "-".join(match.groups())
+        for match in re.finditer(
+            r"(?:^|\n)\s*14\s+CFR\s+Part\s+39\b[\s\S]{0,500}?"
+            r"(?:^|\n)\s*(?:AD\s*)?(\d{2,4})[\s\-‐‑‒–—±]+(\d{2})[\s\-‐‑‒–—±]+(\d{2})\b",
+            intervening_text,
+            re.IGNORECASE | re.MULTILINE,
+        )
+    ]
+    target_numbers = {normalized}
+    if len(parts[0]) == 4:
+        target_numbers.add(f"{parts[0][2:]}-{parts[1]}-{parts[2]}")
+    has_different_later_ad = any(
+        number.upper() not in target_numbers for number in later_part39_numbers
+    )
+    if intervening_agency_boundary is not None or has_different_later_ad:
+        # A recognizable later-document header or closing billing marker before
+        # the first valid footer means that footer cannot be attributed to the
+        # target rule. This also rejects a non-Part-39 neighbor after an
+        # OCR-corrupted target footer.
+        return []
+    section_end = anchor_start + footer.end()
+
+    selected: list[dict[str, Any]] = []
+    for page, (page_start, page_end) in zip(pages, page_offsets, strict=True):
+        overlap_start = max(section_start, page_start)
+        overlap_end = min(section_end, page_end)
+        if overlap_start >= overlap_end:
+            continue
+        scoped_text = combined[overlap_start:overlap_end].strip()
+        if scoped_text:
+            selected.append({**page, "text": scoped_text})
+    return selected
+
+
+def bounded_source_document_pages(
+    pages: list[dict[str, Any]],
+    *,
+    ad_number: str | None,
+    title: str | None = None,
+) -> list[dict[str, Any]]:
+    """Bound each retained document independently and combine its AD sections.
+
+    A directive can have an original final rule plus a later correction. Bounding
+    concatenated documents stops at the first matching FR Doc footer and can hide
+    the other authoritative document from a reviewer.
+    """
+    grouped: dict[str, list[dict[str, Any]]] = {}
+    order: list[str] = []
+    for index, page in enumerate(pages):
+        document_id = str(page.get("sourceDocumentId") or f"__document_{index}")
+        if document_id not in grouped:
+            grouped[document_id] = []
+            order.append(document_id)
+        grouped[document_id].append(page)
+    bounded_by_document: dict[str, list[dict[str, Any]]] = {
+        document_id: bounded_issue_pages(
+            grouped[document_id],
+            ad_number=ad_number,
+            title=title,
+        )
+        for document_id in order
+    }
+    statuses = {
+        document_id: source_evidence_status(ad_number, document_pages)[0]
+        for document_id, document_pages in bounded_by_document.items()
+    }
+    has_primary_rule = any(status == "verified" for status in statuses.values())
+    admitted: list[dict[str, Any]] = []
+    for document_id in order:
+        document_pages = bounded_by_document[document_id]
+        status = statuses[document_id]
+        if status == "verified" or (
+            has_primary_rule
+            and status == "identity_unverified"
+            and correction_document_mentions_ad(document_pages, ad_number)
+        ):
+            admitted.extend(document_pages)
+    return admitted
+
+
+def correction_document_mentions_ad(
+    pages: list[dict[str, Any]],
+    ad_number: str | None,
+) -> bool:
+    official_number = official_ad_number(ad_number)
+    if not pages or not official_number:
+        return False
+    text = "\n".join(str(page.get("text") or "") for page in pages)
+    parts = official_number.split("-")
+    if len(parts) != 3:
+        return False
+    separator = r"[\s\-‐‑‒–—±]*"
+    identifier = separator.join(re.escape(part) for part in parts)
+    return bool(
+        re.search(rf"\b(?:AD\s*)?{identifier}\b", text, re.IGNORECASE)
+        and re.search(r"\b(?:correction|correcting|technical\s+amendment)\b", text, re.IGNORECASE)
+        and re.search(r"(?:14\s+CFR\s+Part\s+39|AIRWORTHINESS\s+DIRECTIVES)", text, re.IGNORECASE)
+    )
+
+
+def official_ad_number(ad_number: str | None) -> str | None:
+    """Return the FAA source designation while retaining normalized IDs in storage."""
+    if not ad_number:
+        return None
+    normalized = ad_number.upper().removeprefix("AD ").strip()
+    parts = normalized.split("-")
+    if len(parts) != 3:
+        return normalized
+    try:
+        year = int(parts[0])
+    except ValueError:
+        return normalized
+    if len(parts[0]) == 4 and year < 2000:
+        return f"{parts[0][2:]}-{parts[1]}-{parts[2]}"
+    return normalized
+
+
+def source_evidence_status(
+    ad_number: str | None,
+    pages: list[dict[str, Any]],
+) -> tuple[str, str]:
+    """Classify whether retained text proves the directive identity."""
+    if not pages:
+        return "missing", "No retained source section is available. Approval is blocked."
+    official_number = official_ad_number(ad_number)
+    if not official_number:
+        return "unverified", "The directive has no AD number to verify against the source."
+    parts = official_number.split("-")
+    if len(parts) != 3:
+        return "unverified", "The directive identifier is not in a recognized FAA AD format."
+    separator = r"[\s\-‐‑‒–—±]*"
+    identifier_expression = rf"{re.escape(parts[0])}{separator}{re.escape(parts[1])}{separator}{re.escape(parts[2])}"
+    identifier_pattern = re.compile(
+        rf"\b(?:AD\s*)?{identifier_expression}\b",
+        re.IGNORECASE,
+    )
+    source_text = "\n".join(page.get("text", "") for page in pages)
+    if not identifier_pattern.search(source_text):
+        return (
+            "identity_unverified",
+            f"Retained text does not contain official designation AD {official_number}. Approval is blocked.",
+        )
+    if not re.search(r"(?:14\s+CFR\s+Part\s+39|AIRWORTHINESS\s+DIRECTIVES)", source_text, re.IGNORECASE):
+        return "unverified", "The retained section does not include a Part 39 / Airworthiness Directives heading."
+    formal_identity_patterns = formal_ad_identity_patterns(identifier_expression)
+    if not any(pattern.search(source_text) for pattern in formal_identity_patterns):
+        formal_heading = re.search(
+            r"adding\s+the\s+following\s+new\s+airworthiness\s+directive\s*:\s*(?:AD\s*)?(\d{2,4})[\s\-‐‑‒–—±]+(\d{2})[\s\-‐‑‒–—±]+(\d{2})\b",
+            source_text,
+            re.IGNORECASE,
+        )
+        if formal_heading:
+            found = "-".join(formal_heading.groups())
+            return (
+                "identity_mismatch",
+                f"The retained Part 39 section is AD {found}, not AD {official_number}. Approval is blocked.",
+            )
+        return (
+            "identity_unverified",
+            f"AD {official_number} appears only as a reference, not as the retained Part 39 directive heading. Approval is blocked.",
+        )
+    return "verified", f"Retained source section contains official designation AD {official_number}."
+
+
+def formal_ad_identity_patterns(identifier_expression: str) -> tuple[re.Pattern[str], ...]:
+    """Patterns that identify an AD as the rule body, not as a cross-reference."""
+    return (
+        re.compile(
+            rf"(?:adding|adds)\s+(?:the\s+following\s+)?(?:new\s+)?(?:airworthiness\s+directive|AD)(?:\s+to\s+read\s+as\s+follows)?\s*:\s*(?:AD\s*)?{identifier_expression}\b",
+            re.IGNORECASE,
+        ),
+        re.compile(
+            rf"\[[^\]]{{0,300}}(?:Amendment[^\]]{{0,120}})?\bAD\s*{identifier_expression}\b[^\]]*\]",
+            re.IGNORECASE,
+        ),
+        re.compile(
+            rf"(?:^|\n)\s*(?:AD\s*)?{identifier_expression}\s+[^\n]{{0,180}}?\bAmendment\b",
+            re.IGNORECASE,
+        ),
+    )
+
+
+def extraction_approval_blocker_details(
+    extraction: ADExtraction,
+    output: dict[str, Any],
+    source_pages: list[dict[str, Any]],
+) -> list[dict[str, str]]:
+    """Return stable codes plus messages for fail-closed approval reasons."""
+    blockers: list[dict[str, str]] = []
+
+    def add(code: str, message: str) -> None:
+        blockers.append({"code": code, "message": message})
+
+    evidence_status, evidence_message = source_evidence_status(
+        extraction.directive.ad_number,
+        source_pages,
+    )
+    if evidence_status != "verified":
+        add("source_evidence_unverified", evidence_message)
+    if extraction.schema_version != SCHEMA_VERSION:
+        add(
+            "schema_version_mismatch",
+            f"Extraction schema {extraction.schema_version} is audit-only; {SCHEMA_VERSION} is required for approval."
+        )
+    proposed_number = str(output.get("adNumber") or "").upper().removeprefix("AD ").strip()
+    expected_number = (extraction.directive.ad_number or "").upper().removeprefix("AD ").strip()
+    if proposed_number != expected_number:
+        add(
+            "ad_number_mismatch",
+            f"Proposed AD number {proposed_number or 'missing'} does not match normalized directive {expected_number or 'missing'}."
+        )
+    if (
+        getattr(extraction, "input_content_hash", None) is not None
+        and extraction.input_content_hash != extraction_input_hash(extraction.directive)
+    ):
+        add(
+            "source_set_changed",
+            "Retained source document set changed after extraction; generate and review a new extraction."
+        )
+    publication_date = getattr(
+        getattr(extraction.directive, "discovery_record", None),
+        "publication_date",
+        None,
+    )
+    proposed_publication_date = output.get("publicationDate")
+    if publication_date is not None and proposed_publication_date != publication_date.isoformat():
+        add(
+            "publication_date_mismatch",
+            "Proposed publicationDate does not match immutable discovery metadata."
+        )
+    if extraction.schema_version == SCHEMA_VERSION:
+        try:
+            validate_extraction_json_schema(output)
+            validate_extraction_output(
+                output,
+                require_v2_requirements=True,
+                require_nonempty_requirements=True,
+                require_nonempty_applicability=True,
+            )
+            validate_requirement_evidence(output, source_pages)
+        except ValueError as exc:
+            add("schema_or_evidence_invalid", str(exc))
+        unresolved = [
+            str(reason).strip()
+            for requirement in output.get("requirements") or []
+            for reason in requirement.get("uncertaintyReasons") or []
+            if str(reason).strip()
+        ]
+        if unresolved:
+            add(
+                "requirement_uncertainty",
+                f"Resolve {len(unresolved)} requirement uncertainty reason(s) before approval."
+            )
+        applicability_unresolved = [
+            str(reason).strip()
+            for group in output.get("applicabilityGroups") or []
+            for reason in group.get("uncertaintyReasons") or []
+            if str(reason).strip()
+        ]
+        if applicability_unresolved:
+            add(
+                "applicability_uncertainty",
+                f"Resolve {len(applicability_unresolved)} applicability uncertainty reason(s) before approval."
+            )
+        amoc_unresolved = [
+            str(reason).strip()
+            for provision in output.get("amocProvisions") or []
+            for reason in provision.get("uncertaintyReasons") or []
+            if str(reason).strip()
+        ]
+        if amoc_unresolved:
+            add(
+                "amoc_uncertainty",
+                f"Resolve {len(amoc_unresolved)} AMOC uncertainty reason(s) before approval."
+            )
+    return blockers
+
+
+def extraction_approval_blockers(
+    extraction: ADExtraction,
+    output: dict[str, Any],
+    source_pages: list[dict[str, Any]],
+) -> list[str]:
+    """Return presentation messages for fail-closed approval reasons."""
+    return [
+        blocker["message"]
+        for blocker in extraction_approval_blocker_details(
+            extraction,
+            output,
+            source_pages,
+        )
+    ]
+
+
+def extraction_input_hash(directive: AirworthinessDirective) -> str:
+    documents = retained_pdf_documents(directive)
+    if not documents:
+        return directive.source_content_hash
+    material = {
+        "directiveHash": directive.source_content_hash,
+        "documents": sorted((document.id, document.content_hash) for document in documents),
+        "schemaVersion": SCHEMA_VERSION,
+    }
+    return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
+
+
 def response_output_text(payload: dict[str, Any]) -> str:
     for output_item in payload.get("output", []) or []:
         for content_item in output_item.get("content", []) or []:
@@ -504,6 +2133,21 @@ def normalize_scalar(value: Any) -> str:
     return " ".join(str(value or "").strip().lower().split())
 
 
+def normalize_regulatory_text(value: Any) -> str:
+    """Compare regulatory wording while ignoring layout-only punctuation.
+
+    Federal Register PDF extraction inserts line-wrap hyphens and typography
+    variants. Token comparison preserves the word sequence while preventing a
+    paraphrase from passing as a verbatim action.
+    """
+    def join_wrapped_token(match: re.Match[str]) -> str:
+        left, right = match.groups()
+        return f"{left}{right}" if left.isalpha() and right.isalpha() else f"{left} {right}"
+
+    text = re.sub(r"(\w)-\s*\n\s*(\w)", join_wrapped_token, str(value or ""))
+    return " ".join(re.findall(r"\w+", text.casefold()))
+
+
 def normalize_list(value: Any) -> list[str]:
     if not isinstance(value, list):
         return []
diff --git a/backend/tests/test_ad_ingestion.py b/backend/tests/test_ad_ingestion.py
index ce9f781..eafac3e 100644
--- a/backend/tests/test_ad_ingestion.py
+++ b/backend/tests/test_ad_ingestion.py
@@ -1,9 +1,16 @@
 from __future__ import annotations
 
+import hashlib
+import json
+from datetime import datetime, timezone
+from pathlib import Path
 from typing import Any
+from types import SimpleNamespace
 
+import pytest
 from fastapi.testclient import TestClient
 from sqlalchemy import select
+from sqlalchemy.dialects import postgresql
 from sqlalchemy.orm import Session
 
 from app.models.core import (
@@ -12,13 +19,41 @@ from app.models.core import (
     ADDiscoveryRecord,
     ADExtraction,
     ADExtractionReview,
+    ADExtractionReviewDecision,
     ADTargetApplicability,
     AirworthinessDirective,
     ProductEvent,
+    ADPublication,
+    ADSourceDocument,
 )
+from app.core.config import get_settings
 from app.services.ad_discovery import FederalRegisterSearchResult, discover_federal_register_ads
-from app.services.ad_extraction import process_pending_ad_extractions
+from app.services.ad_extraction import AD_EXTRACTION_JSON_SCHEMA, process_pending_ad_extractions
+from app.services.ad_extraction import derive_compliance_action_summaries
+from app.services.ad_extraction import validate_extraction_output
+from app.services.ad_extraction import (
+    bounded_issue_pages,
+    bounded_source_document_pages,
+    extraction_approval_blockers,
+    extraction_input_hash,
+    full_text_pages_for_directive,
+    full_text_pages_for_extraction,
+    official_ad_number,
+    persisted_source_pages,
+    retained_pdf_documents,
+    source_evidence_status,
+    validate_extraction_json_schema,
+    validate_requirement_evidence,
+    verified_retained_document_bytes,
+)
+from app.api.routes.ads import match_has_signed_materialization_chain, serialize_review
 from app.services.ad_matching import match_aircraft_ads
+from app.scripts.correct_approved_ad_review import supersede_amoc_provisions_statement
+from app.scripts.stage_ad_review_proposal import (
+    main as stage_review_proposal_main,
+    stage_review_proposal,
+    visual_ocr_validation_shadow,
+)
 from tests.conftest import (
     add_membership,
     create_organization,
@@ -47,6 +82,953 @@ class FakeFederalRegisterClient:
         )
 
 
+def test_v3_schema_requires_page_citations_for_each_requirement() -> None:
+    output = provider_output()
+    output.pop("confidence")
+    output.pop("citations")
+    output.pop("uncertaintyReasons")
+    output["requirements"] = [{
+        "requirementKey": "inspection",
+        "applicabilityGroupKeys": ["airbus-as350"],
+        "requirementType": "recurring",
+        "actionText": "Inspect the affected part.",
+        "initialThresholds": [],
+        "recurringTriggers": [{"metric": "tach_hours", "value": 100, "unit": "hours", "anchorKind": "last_compliance", "sourceText": "every 100 hours"}],
+        "combinationLogic": "all",
+        "conditions": [],
+        "terminatingAction": None,
+        "citations": [],
+        "confidence": 0.9,
+        "uncertaintyReasons": [],
+    }]
+
+    try:
+        validate_extraction_output(output)
+    except ValueError as exc:
+        assert "page citations" in str(exc)
+    else:
+        raise AssertionError("uncited v2 requirement was accepted")
+
+
+def test_v3_schema_accepts_installation_prohibition_requirement() -> None:
+    output = provider_output()
+    output["requirements"] = [{
+        "requirementKey": "replacement-part-installation",
+        "applicabilityGroupKeys": ["airbus-as350"],
+        "requirementType": "installation_prohibition",
+        "actionText": "Install only a replacement part that passed inspection.",
+        "initialThresholds": [],
+        "recurringTriggers": [],
+        "combinationLogic": "all",
+        "conditions": ["A replacement part is installed."],
+        "terminatingAction": None,
+        "citations": [{
+            "sourceDocumentId": "asd_example",
+            "pageNumber": 2,
+            "text": "Only install a replacement part that passed inspection.",
+        }],
+        "confidence": 0.95,
+        "uncertaintyReasons": [],
+    }]
+
+    validate_extraction_output(output, require_v2_requirements=True)
+
+
+def test_v2_compliance_actions_are_derived_from_requirement_objects() -> None:
+    output = provider_output()
+    output["complianceActions"] = []
+    output["requirements"] = [
+        {"actionText": "Inspect the impulse coupling stop pin."},
+        {"actionText": "Replace a missing stop pin."},
+        {"actionText": "Inspect the impulse coupling stop pin."},
+    ]
+
+    normalized = derive_compliance_action_summaries(output)
+
+    assert normalized["complianceActions"] == [
+        "Inspect the impulse coupling stop pin.",
+        "Replace a missing stop pin.",
+    ]
+    assert output["complianceActions"] == []
+
+
+def test_requirement_evidence_rejects_paraphrased_action_text() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 5,
+        "text": "Within 12 months, update the software to a version that is not 8.01 or earlier.",
+    }]
+    output = {"requirements": [{
+        "actionText": "Install a software version later than 8.01.",
+        "citations": [{
+            "sourceDocumentId": "asd_source",
+            "pageNumber": 5,
+            "text": "Within 12 months, update the software to a version that is not 8.01 or earlier.",
+        }],
+    }]}
+
+    try:
+        validate_requirement_evidence(output, source_pages)
+    except ValueError as exc:
+        assert "preserve wording" in str(exc)
+    else:
+        raise AssertionError("paraphrased actionText was accepted")
+
+
+def test_requirement_evidence_accepts_source_wording_with_pdf_typography_changes() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 5,
+        "text": "Do not install auto-\npilot software in the pilot’s airplane.",
+    }]
+    action = "Do not install autopilot software in the pilot's airplane."
+
+    validate_requirement_evidence(
+        {"requirements": [{
+            "actionText": action,
+            "citations": [{
+                "sourceDocumentId": "asd_source",
+                "pageNumber": 5,
+                "text": action,
+            }],
+        }]},
+        source_pages,
+    )
+
+
+def test_requirement_evidence_accepts_source_wording_assembled_from_ordered_citations() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 8,
+        "text": "(i) Replace the worn component. (ii) Continue the repetitive inspections.",
+    }]
+
+    validate_requirement_evidence(
+        {"requirements": [{
+            "actionText": "Replace the worn component. Continue the repetitive inspections.",
+            "citations": [{
+                "sourceDocumentId": "asd_source",
+                "pageNumber": 8,
+                "text": "Replace the worn component.",
+            }, {
+                "sourceDocumentId": "asd_source",
+                "pageNumber": 8,
+                "text": "Continue the repetitive inspections.",
+            }],
+        }]},
+        source_pages,
+    )
+
+
+def test_requirement_evidence_rejects_hallucinated_threshold_value() -> None:
+    source_text = "Inspect the part within 10 hours after the effective date."
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 3,
+        "text": source_text,
+    }]
+    output = {"requirements": [{
+        "actionText": source_text,
+        "initialThresholds": [{
+            "metric": "total_time_hours",
+            "value": 100,
+            "unit": "hours",
+            "anchorKind": "effective_date",
+            "sourceText": source_text,
+        }],
+        "recurringTriggers": [],
+        "terminatingAction": None,
+        "citations": [{
+            "sourceDocumentId": "asd_source",
+            "pageNumber": 3,
+            "text": source_text,
+        }],
+    }]}
+
+    try:
+        validate_requirement_evidence(output, source_pages)
+    except ValueError as exc:
+        assert "value is not present" in str(exc)
+    else:
+        raise AssertionError("unsupported threshold value was accepted")
+
+
+def test_amoc_authority_text_must_be_source_cited() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 9,
+        "text": "The Manager, New York ACO Branch, FAA, has the authority to approve AMOCs for this AD.",
+    }]
+    output = {
+        "requirements": [],
+        "amocProvisions": [{
+            "authorityText": "Any mechanic may approve an AMOC.",
+            "citations": [{
+                "sourceDocumentId": "asd_source",
+                "pageNumber": 9,
+                "text": source_pages[0]["text"],
+            }],
+        }],
+    }
+
+    try:
+        validate_requirement_evidence(output, source_pages)
+    except ValueError as exc:
+        assert "authorityText must preserve wording" in str(exc)
+    else:
+        raise AssertionError("uncited AMOC authority was accepted")
+
+
+def test_applicability_identity_and_serial_scope_must_be_source_cited() -> None:
+    cited = "This AD applies to Cessna Model 172R airplanes, serial numbers 17280001 through 17280099."
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 1,
+        "text": cited,
+    }]
+    group = v3_applicability_group(
+        source_document_id="asd_source",
+        citation_text=cited,
+        manufacturer="Cessna",
+        model="172R",
+        group_key="cessna-172r",
+    )
+    group["serialNumberApplicability"] = {
+        "kind": "ranges",
+        "values": [],
+        "ranges": [{"start": "17280001", "end": "17280999"}],
+        "excludedValues": [],
+        "sourceText": cited,
+    }
+
+    try:
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+    except ValueError as exc:
+        assert "serial range endpoint" in str(exc)
+    else:
+        raise AssertionError("hallucinated serial endpoint was accepted")
+
+
+def test_applicability_rejects_unreviewed_normalized_identity_override() -> None:
+    cited = "This AD applies to Lycoming Model O-320 engines, all serial numbers."
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 1,
+        "text": cited,
+    }]
+    group = v3_applicability_group(
+        source_document_id="asd_source",
+        citation_text=cited,
+        manufacturer="Lycoming",
+        model="O-320",
+        group_key="lycoming-o-320",
+    )
+    group["productType"] = "engine"
+    group["manufacturer"]["normalizedName"] = "Continental Motors"
+
+    with pytest.raises(ValueError, match="reviewed canonical identity mapping"):
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+    group["manufacturer"]["normalizedName"] = "Lycoming"
+    group["modelApplicability"]["models"][0]["normalizedDesignation"] = "IO-360"
+    with pytest.raises(ValueError, match="normalizedDesignation"):
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+
+
+def test_applicability_scope_kind_cannot_broaden_cited_scope() -> None:
+    cited = "This AD applies to Cessna Model 172R airplanes, serial numbers 1 through 10."
+    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
+    group = v3_applicability_group(
+        source_document_id="asd_source",
+        citation_text=cited,
+        manufacturer="Cessna",
+        model="172R",
+        group_key="cessna-172r",
+    )
+    group["modelApplicability"] = {
+        "kind": "all", "models": [], "sourceText": "Cessna Model 172R airplanes",
+    }
+    with pytest.raises(ValueError, match="all-model scope"):
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+
+    group["modelApplicability"] = {
+        "kind": "listed",
+        "models": [{"sourceDesignation": "172R", "normalizedDesignation": None, "aliases": []}],
+        "sourceText": "Cessna Model 172R airplanes",
+    }
+    group["serialNumberApplicability"] = {
+        "kind": "all", "values": [], "ranges": [], "excludedValues": [],
+        "sourceText": "serial numbers 1 through 10",
+    }
+    with pytest.raises(ValueError, match="all-serial scope"):
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+
+
+def test_requirement_timing_and_combination_semantics_are_source_bound() -> None:
+    cited = "Inspect within 10 hours after installation, whichever occurs first."
+    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
+    requirement = {
+        "requirementType": "one_time",
+        "actionText": cited,
+        "initialThresholds": [{
+            "metric": "total_time_hours", "value": 10, "unit": "hours",
+            "anchorKind": "effective_date", "sourceText": cited,
+        }],
+        "recurringTriggers": [], "combinationLogic": "whichever_first",
+        "conditions": [], "terminatingAction": None,
+        "citations": [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}],
+    }
+    with pytest.raises(ValueError, match="anchorKind"):
+        validate_requirement_evidence(
+            {"requirements": [requirement], "amocProvisions": []}, source_pages,
+        )
+    requirement["initialThresholds"][0]["anchorKind"] = "installation"
+    requirement["combinationLogic"] = "whichever_later"
+    with pytest.raises(ValueError, match="whichever_later"):
+        validate_requirement_evidence(
+            {"requirements": [requirement], "amocProvisions": []}, source_pages,
+        )
+
+
+def test_requirement_condition_and_product_type_are_source_bound() -> None:
+    cited = "This AD applies to Cessna Model 172R airplanes. Inspect the seat rail."
+    source_pages = [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}]
+    group = v3_applicability_group(
+        source_document_id="asd_source", citation_text=cited,
+        manufacturer="Cessna", model="172R", group_key="cessna-172r",
+    )
+    group["productType"] = "engine"
+    with pytest.raises(ValueError, match="productType"):
+        validate_requirement_evidence(
+            {"applicabilityGroups": [group], "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+
+    requirement = {
+        "requirementType": "conditional", "actionText": "Inspect the seat rail.",
+        "initialThresholds": [], "recurringTriggers": [], "combinationLogic": "all",
+        "conditions": ["Only when floats are installed."], "terminatingAction": None,
+        "citations": [{"sourceDocumentId": "asd_source", "pageNumber": 1, "text": cited}],
+    }
+    with pytest.raises(ValueError, match="condition 0"):
+        validate_requirement_evidence(
+            {"requirements": [requirement], "amocProvisions": []}, source_pages,
+        )
+
+def test_reviewed_dates_must_be_present_in_retained_source() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_source", "pageNumber": 1,
+        "text": "This amendment becomes effective on August 30, 2026.",
+    }]
+    with pytest.raises(ValueError, match="effectiveDate"):
+        validate_requirement_evidence(
+            {"effectiveDate": "2026-09-30", "requirements": [], "amocProvisions": []},
+            source_pages,
+        )
+    validate_requirement_evidence(
+        {"effectiveDate": "2026-08-30", "requirements": [], "amocProvisions": []},
+        source_pages,
+    )
+
+def test_amoc_authority_details_and_conditions_must_be_source_cited() -> None:
+    cited = "The Manager, New York ACO Branch, may approve AMOCs submitted through the principal inspector."
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 9,
+        "text": cited,
+    }]
+    provision = {
+        "authorityText": cited,
+        "approvingAuthority": "New York ACO Branch",
+        "submissionInstructions": "Submit through an unrelated office.",
+        "conditions": [],
+        "citations": [{
+            "sourceDocumentId": "asd_source",
+            "pageNumber": 9,
+            "text": cited,
+        }],
+    }
+
+    try:
+        validate_requirement_evidence(
+            {"requirements": [], "amocProvisions": [provision]},
+            source_pages,
+        )
+    except ValueError as exc:
+        assert "submissionInstructions" in str(exc)
+    else:
+        raise AssertionError("uncited AMOC submission instruction was accepted")
+
+
+def test_requirement_uncertainty_blocks_approval() -> None:
+    extraction = SimpleNamespace(
+        schema_version="ad_extraction_v3",
+        directive=SimpleNamespace(ad_number="2026-12-01", title="Example AD"),
+    )
+    source_pages = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 1,
+        "text": (
+            "Federal Register, June 16, 2026.\n14 CFR Part 39\n"
+            "Section 39.13 is amended by adding the following new "
+            "airworthiness directive: AD 2026-12-01. This AD applies to Airbus "
+            "Helicopters Model AS350, all serial numbers. Inspect the seat rail."
+        ),
+    }]
+    output = provider_output()
+    output["applicabilityGroups"][0]["citations"] = [{
+        "sourceDocumentId": "asd_source",
+        "pageNumber": 1,
+        "text": "This AD applies to Airbus Helicopters Model AS350, all serial numbers.",
+    }]
+    output["requirements"] = [{
+        "requirementKey": "g-inspection",
+        "applicabilityGroupKeys": ["airbus-as350"],
+        "requirementType": "one_time",
+        "actionText": "Inspect the seat rail.",
+        "initialThresholds": [],
+        "recurringTriggers": [],
+        "combinationLogic": "all",
+        "conditions": [],
+        "terminatingAction": None,
+        "citations": [{
+            "sourceDocumentId": "asd_source",
+            "pageNumber": 1,
+            "text": "Inspect the seat rail.",
+        }],
+        "confidence": 0.8,
+        "uncertaintyReasons": ["Confirm whether paragraph (g)(2) is a separate requirement."],
+    }]
+
+    blockers = extraction_approval_blockers(extraction, output, source_pages)
+
+    assert blockers == ["Resolve 1 requirement uncertainty reason(s) before approval."]
+
+
+def test_v3_provider_schema_closes_and_requires_every_object_field() -> None:
+    def assert_strict_objects(node: Any) -> None:
+        if isinstance(node, dict):
+            if node.get("type") == "object":
+                assert node.get("additionalProperties") is False
+                assert set(node.get("required") or []) == set((node.get("properties") or {}).keys())
+            for value in node.values():
+                assert_strict_objects(value)
+        elif isinstance(node, list):
+            for value in node:
+                assert_strict_objects(value)
+
+    assert_strict_objects(AD_EXTRACTION_JSON_SCHEMA)
+
+
+def test_operational_v3_schema_rejects_partial_extra_nested_and_nonfinite_values() -> None:
+    output = provider_output()
+    validate_extraction_json_schema(output)
+
+    missing = dict(output)
+    missing.pop("confidence")
+    with pytest.raises(ValueError, match="missing required properties: confidence"):
+        validate_extraction_json_schema(missing)
+
+    extra = dict(output)
+    extra["unsupported"] = True
+    with pytest.raises(ValueError, match="unsupported properties: unsupported"):
+        validate_extraction_json_schema(extra)
+
+    nested = provider_output()
+    nested["applicabilityGroups"][0]["manufacturer"]["unsupported"] = "value"
+    with pytest.raises(ValueError, match="unsupported properties: unsupported"):
+        validate_extraction_json_schema(nested)
+
+    invalid_confidence = provider_output()
+    invalid_confidence["confidence"] = 2
+    with pytest.raises(ValueError, match="must be at most 1"):
+        validate_extraction_json_schema(invalid_confidence)
+
+    nonfinite = provider_output()
+    nonfinite["confidence"] = float("nan")
+    with pytest.raises(ValueError, match="must be number"):
+        validate_extraction_json_schema(nonfinite)
+
+
+def test_retained_pdf_text_preserves_document_and_page_identity(tmp_path, monkeypatch) -> None:
+    from reportlab.pdfgen import canvas
+
+    pdf_path = tmp_path / "source.pdf"
+    writer = canvas.Canvas(str(pdf_path))
+    writer.drawString(72, 720, "Compliance: inspect within 100 hours.")
+    writer.showPage()
+    writer.drawString(72, 720, "Thereafter inspect every 50 hours.")
+    writer.save()
+    pdf_bytes = pdf_path.read_bytes()
+    document = SimpleNamespace(
+        id="asd_retained",
+        media_type="application/pdf",
+        storage_backend="local",
+        storage_key="source.pdf",
+        content_hash=hashlib.sha256(pdf_bytes).hexdigest(),
+        storage_bytes=len(pdf_bytes),
+    )
+    directive = SimpleNamespace(
+        publications=[SimpleNamespace(source_document=document)],
+        source_content_hash="b" * 64,
+    )
+    monkeypatch.setattr(
+        "app.services.ad_extraction.get_settings",
+        lambda: SimpleNamespace(
+            local_storage_path=str(tmp_path),
+            storage_backend="local",
+            ad_extraction_provider="deterministic",
+            openai_api_key=None,
+        ),
+    )
+
+    pages = full_text_pages_for_directive(directive)
+
+    assert [(page["sourceDocumentId"], page["pageNumber"]) for page in pages] == [
+        ("asd_retained", 1),
+        ("asd_retained", 2),
+    ]
+    assert "inspect within 100 hours" in pages[0]["text"]
+    assert extraction_input_hash(directive) != directive.source_content_hash
+
+
+def test_cached_source_pages_are_rejected_after_retained_bytes_change(
+    tmp_path,
+    monkeypatch,
+) -> None:
+    from reportlab.pdfgen import canvas
+
+    source_path = tmp_path / "source.pdf"
+    writer = canvas.Canvas(str(source_path))
+    writer.drawString(72, 720, "original retained evidence")
+    writer.showPage()
+    writer.drawString(72, 720, "later compliance exception")
+    writer.save()
+    original = source_path.read_bytes()
+    content_hash = hashlib.sha256(original).hexdigest()
+    document = SimpleNamespace(
+        id="asd_retained",
+        media_type="application/pdf",
+        source_system="federal_register",
+        source_type="rule_pdf",
+        storage_backend="local",
+        storage_key="source.pdf",
+        content_hash=content_hash,
+        storage_bytes=len(original),
+    )
+    directive = SimpleNamespace(
+        publications=[SimpleNamespace(source_document=document)],
+    )
+    extraction = SimpleNamespace(raw_response={
+        "retainedSourcePagesCached": True,
+        "retainedSourcePages": [{
+            "sourceDocumentId": document.id,
+            "contentHash": content_hash,
+            "pageNumber": 1,
+            "text": "original retained evidence",
+        }, {
+            "sourceDocumentId": document.id,
+            "contentHash": content_hash,
+            "pageNumber": 2,
+            "text": "later compliance exception",
+        }],
+    })
+    monkeypatch.setattr(
+        "app.services.ad_extraction.get_settings",
+        lambda: SimpleNamespace(local_storage_path=str(tmp_path)),
+    )
+
+    assert persisted_source_pages(directive, extraction)[0] is True
+    omitted_page = extraction.raw_response["retainedSourcePages"].pop()
+    assert persisted_source_pages(directive, extraction) == (False, [])
+    extraction.raw_response["retainedSourcePages"].append(omitted_page)
+    extraction.raw_response["retainedSourcePages"][0]["text"] = "invented retained evidence"
+    assert persisted_source_pages(directive, extraction) == (False, [])
+    extraction.raw_response["retainedSourcePages"][0]["text"] = "original retained evidence"
+    source_path.write_bytes(b"%PDF-1.4\ntampered retained evidence\n%%EOF\n")
+    assert persisted_source_pages(directive, extraction) == (False, [])
+
+
+def test_retained_source_set_includes_individual_and_issue_pdfs() -> None:
+    def document(document_id: str, source_type: str) -> SimpleNamespace:
+        return SimpleNamespace(
+            id=document_id, media_type="application/pdf",
+            source_system="federal_register", source_type=source_type,
+        )
+
+    original = document("asd_original", "document_pdf")
+    correction = document("asd_correction_issue", "issue_pdf")
+    directive = SimpleNamespace(publications=[
+        SimpleNamespace(source_document=original),
+        SimpleNamespace(source_document=correction),
+    ])
+    assert [item.id for item in retained_pdf_documents(directive)] == [
+        "asd_original", "asd_correction_issue",
+    ]
+
+
+def test_match_due_state_chain_rejects_cross_extraction_or_stale_state() -> None:
+    applicability = SimpleNamespace(
+        id="ata_expected", status="current", source_extraction_id="adx_expected",
+    )
+    requirement = SimpleNamespace(
+        status="current", source_extraction_id="adx_other",
+        target_applicability_id="ata_expected",
+    )
+    state = SimpleNamespace(
+        id="adu_fixture", is_current=True, aircraft_id="air_fixture",
+        installed_component_id="cmp_fixture", requirement=requirement,
+    )
+    match = SimpleNamespace(
+        target_applicability=applicability, extraction_id="adx_expected",
+        aircraft_id="air_fixture", installed_component_id="cmp_fixture",
+        due_state_links=[SimpleNamespace(due_state=state)], due_state=None,
+    )
+    assert match_has_signed_materialization_chain(match) is False
+    requirement.source_extraction_id = "adx_expected"
+    assert match_has_signed_materialization_chain(match) is True
+    state.is_current = False
+    assert match_has_signed_materialization_chain(match) is False
+
+
+def test_deterministic_full_text_extraction_always_requires_review(
+    db_session: Session,
+    tmp_path,
+    monkeypatch,
+) -> None:
+    from datetime import datetime, timezone
+    from reportlab.pdfgen import canvas
+
+    discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
+    directive = db_session.scalar(select(AirworthinessDirective))
+    pdf_path = tmp_path / "retained.pdf"
+    writer = canvas.Canvas(str(pdf_path))
+    writer.drawString(72, 720, "Compliance: inspect the affected part every 100 hours.")
+    writer.save()
+    retained_bytes = pdf_path.read_bytes()
+    document = ADSourceDocument(
+        source_system="federal_register",
+        source_type="rule_pdf",
+        source_identifier="fixture-retained-pdf",
+        storage_backend="local",
+        storage_key="retained.pdf",
+        media_type="application/pdf",
+        content_hash=hashlib.sha256(retained_bytes).hexdigest(),
+        storage_bytes=pdf_path.stat().st_size,
+        captured_at=datetime.now(timezone.utc),
+        status="retained",
+    )
+    db_session.add(document)
+    db_session.flush()
+    db_session.add(ADPublication(
+        directive_id=directive.id,
+        source_document_id=document.id,
+        source_system="federal_register",
+        source_type="rule_pdf",
+        source_identifier="fixture-retained-publication",
+        content_hash=document.content_hash,
+        status="retained",
+    ))
+    db_session.flush()
+    monkeypatch.setattr(
+        "app.services.ad_extraction.get_settings",
+        lambda: SimpleNamespace(
+            local_storage_path=str(tmp_path),
+            storage_backend="local",
+            ad_extraction_provider="deterministic",
+            openai_api_key=None,
+        ),
+    )
+
+    stats = process_pending_ad_extractions(db_session)
+
+    extraction = db_session.scalar(select(ADExtraction))
+    assert stats["review_queued"] == 1
+    assert extraction.schema_version == "ad_extraction_v3"
+    assert extraction.status == "needs_review"
+    assert extraction.raw_response["retainedSourcePagesCached"] is True
+    assert len(extraction.raw_response["retainedSourcePages"]) == 1
+    byte_reads = 0
+
+    def verified_read(**_) -> bytes:
+        nonlocal byte_reads
+        byte_reads += 1
+        return retained_bytes
+
+    monkeypatch.setattr(
+        "app.services.ad_extraction.read_stored_file_bytes",
+        verified_read,
+    )
+    assert len(full_text_pages_for_extraction(extraction)) == 1
+    assert byte_reads == 1
+    document.content_hash = "b" * 64
+    db_session.flush()
+    assert persisted_source_pages(directive, extraction) == (False, [])
+    assert db_session.scalar(select(ADExtractionReview)) is not None
+
+
+def test_retained_document_verification_never_accepts_a_second_read(
+    monkeypatch,
+) -> None:
+    expected = b"official retained bytes"
+    document = SimpleNamespace(
+        storage_backend="local",
+        storage_key="retained.pdf",
+        content_hash=hashlib.sha256(expected).hexdigest(),
+        storage_bytes=len(expected),
+    )
+    payloads = iter([b"tampered first read", expected])
+    reads = 0
+
+    def alternating_read(**_) -> bytes:
+        nonlocal reads
+        reads += 1
+        return next(payloads)
+
+    monkeypatch.setattr(
+        "app.services.ad_extraction.read_stored_file_bytes",
+        alternating_read,
+    )
+
+    with pytest.raises(ValueError, match="hash or size mismatch"):
+        verified_retained_document_bytes(document, settings=SimpleNamespace())
+    assert reads == 1
+
+
+def test_approved_correction_amoc_revocation_compiles_for_postgresql() -> None:
+    statement = supersede_amoc_provisions_statement("adx_fixture")
+
+    compiled = str(statement.compile(dialect=postgresql.dialect()))
+
+    assert "UPDATE ad_amoc_provisions SET status=" in compiled
+    assert "review_status" not in compiled
+
+
+def test_complete_issue_text_is_bounded_to_ad_section() -> None:
+    pages = [
+        {"pageNumber": 1, "text": "Unrelated FAA rule. [FR Doc. 2026-10000]"},
+        {"pageNumber": 2, "text": "14 CFR Part 39\n[Docket No. FAA-2026-1]\nAirworthiness Directive AD 2026-12-01 begins."},
+        {"pageNumber": 3, "text": "Compliance actions continue here."},
+        {"pageNumber": 4, "text": "Issued in Washington. [FR Doc. 2026-12052]\nAnother unrelated rule."},
+        {"pageNumber": 5, "text": "Unrelated appendix."},
+    ]
+
+    selected = bounded_issue_pages(pages, ad_number="2026-12-01", title="Affected Part")
+
+    assert [page["pageNumber"] for page in selected] == [2, 3, 4]
+    assert "Another unrelated rule" not in selected[-1]["text"]
+    assert bounded_issue_pages(pages, ad_number="1999-99-99") == []
+    title_selected = bounded_issue_pages(
+        pages,
+        ad_number="1999-99-99",
+        title="Compliance Actions",
+    )
+    assert [page["pageNumber"] for page in title_selected] == [2, 3, 4]
+
+
+def test_issue_bounding_fails_closed_without_a_footer() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.",
+    }]
+
+    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []
+
+
+def test_issue_bounding_fails_closed_with_an_ocr_corrupted_footer() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": (
+            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
+            "[F8 D0c 2026-12052 Filed 6-15-26]"
+        ),
+    }]
+
+    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []
+
+
+def test_issue_bounding_rejects_a_later_rules_footer() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": (
+            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
+            "14 CFR Part 39\nAD 2026-12-02\nReplace another part.\n"
+            "[FR Doc. 2026-12053 Filed 6-15-26]"
+        ),
+    }]
+
+    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []
+
+
+def test_issue_bounding_rejects_a_non_part_39_neighbors_footer() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": (
+            "14 CFR Part 39\nAD 2026-12-01\nInspect the affected part.\n"
+            "[F8 D0c 2026-12052 Filed 6-15-26]\n"
+            "DEPARTMENT OF AGRICULTURE\nForest Service\n"
+            "NeighborCo model N-1 grazing notice.\n"
+            "[FR Doc. 2026-12054 Filed 6-15-26]"
+        ),
+    }]
+
+    assert bounded_issue_pages(pages, ad_number="2026-12-01") == []
+
+
+def test_issue_bounding_allows_internal_billing_code_before_table() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": (
+            "14 CFR Part 39\n[Docket No. FAA-2026-1; AD 2026-12-01]\n"
+            "This AD applies to the listed airplanes.\n"
+            "BILLING CODE 4910-13-P\n"
+            "Table 1—Applicable Airplane Models\n"
+            "Comply within 12 months.\n"
+            "[FR Doc. 2026-12052 Filed 6-15-26]"
+        ),
+    }]
+
+    selected = bounded_issue_pages(pages, ad_number="2026-12-01")
+
+    assert len(selected) == 1
+    assert "Table 1—Applicable Airplane Models" in selected[0]["text"]
+
+
+def test_issue_bounding_allows_target_part_39_amendment_after_preamble() -> None:
+    pages = [{
+        "pageNumber": 1,
+        "text": (
+            "14 CFR Part 39\n"
+            "[Docket No. FAA-2026-1; Amendment 39-1; AD 2026-12-01]\n"
+            "The FAA proposed to amend 14 CFR part 39 by adding an AD.\n"
+            "PART 39—AIRWORTHINESS DIRECTIVES\n"
+            "2026-12-01 Example Aircraft: Amendment 39-1.\n"
+            "Inspect the affected part.\n"
+            "BILLING CODE 4910-13-P\n"
+            "[FR Doc. 2026-12052 Filed 6-15-26]"
+        ),
+    }]
+
+    selected = bounded_issue_pages(pages, ad_number="2026-12-01")
+
+    assert len(selected) == 1
+    assert "Inspect the affected part" in selected[0]["text"]
+
+
+def test_formal_target_heading_wins_over_earlier_cross_reference() -> None:
+    pages = [
+        {
+            "sourceDocumentId": "superseding-rule",
+            "pageNumber": 1,
+            "text": "14 CFR Part 39\nAD 2023-17-04 supersedes AD 2022-04-04.\n[FR Doc. 2023-10000]",
+        },
+        {
+            "sourceDocumentId": "target-rule",
+            "pageNumber": 1,
+            "text": "14 CFR Part 39\nThe FAA amends section 39.13 by adding the following new AD: 2022-04-04 Continental Motors.",
+        },
+        {
+            "sourceDocumentId": "target-rule",
+            "pageNumber": 2,
+            "text": "Compliance is required.\n[FR Doc. 2022-10000]",
+        },
+    ]
+
+    selected = bounded_issue_pages(pages, ad_number="2022-04-04")
+
+    assert {page["sourceDocumentId"] for page in selected} == {"target-rule"}
+    assert [page["pageNumber"] for page in selected] == [1, 2]
+    assert "supersedes" not in selected[0]["text"]
+
+
+def test_document_bounding_retains_original_rule_and_correction() -> None:
+    pages = [
+        {
+            "sourceDocumentId": "original",
+            "pageNumber": 1,
+            "text": (
+                "14 CFR Part 39\n[AD 2008-26-10]\nCompliance\n"
+                "Inspect the valve.\n[FR Doc. E8-30465 Filed 12-23-08]"
+            ),
+        },
+        {
+            "sourceDocumentId": "correction",
+            "pageNumber": 1,
+            "text": (
+                "14 CFR Part 39\nAirworthiness Directive 2008-26-10\n"
+                "Correction of Regulatory Text\nChange paragraph (e) to (d).\n"
+                "[FR Doc. 2010-28579 Filed 11-15-10]"
+            ),
+        },
+    ]
+
+    selected = bounded_source_document_pages(pages, ad_number="2008-26-10")
+
+    assert [page["sourceDocumentId"] for page in selected] == ["original", "correction"]
+    assert "Inspect the valve" in selected[0]["text"]
+    assert "Change paragraph" in selected[1]["text"]
+
+
+def test_document_bounding_rejects_foreign_rule_that_only_references_target_ad() -> None:
+    pages = [
+        {
+            "sourceDocumentId": "target",
+            "pageNumber": 1,
+            "text": (
+                "Federal Register, June 16, 2026.\n14 CFR Part 39\n"
+                "Section 39.13 is amended by adding the following new "
+                "airworthiness directive: AD 2011-10-09. Inspect the seat rail.\n"
+                "[FR Doc. 2011-10988]"
+            ),
+        },
+        {
+            "sourceDocumentId": "foreign",
+            "pageNumber": 1,
+            "text": (
+                "14 CFR Part 39\nSection 39.13 is amended by adding the following new "
+                "airworthiness directive: AD 2020-21-22. A commenter referred to AD 2011-10-09.\n"
+                "[FR Doc. 2020-24046]"
+            ),
+        },
+    ]
+
+    selected = bounded_source_document_pages(pages, ad_number="2011-10-09")
+
+    assert {page["sourceDocumentId"] for page in selected} == {"target"}
+
+
+def test_source_evidence_requires_official_identifier_and_part_39_heading() -> None:
+    assert official_ad_number("1995-21-15") == "95-21-15"
+    assert official_ad_number("2024-14-03") == "2024-14-03"
+    status, _ = source_evidence_status(
+        "1995-21-15",
+        [{"text": "14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\n95±21±15 Teledyne Continental Motors"}],
+    )
+    assert status == "verified"
+    mismatch_status, mismatch_message = source_evidence_status(
+        "2000-06-01",
+        [{"text": "14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\n2005-05-09 EMBRAER.\nThis AD references Brazilian airworthiness directive 2000-06-01."}],
+    )
+    assert mismatch_status == "identity_mismatch"
+    assert "AD 2005-05-09" in mismatch_message
+    missing_status, _ = source_evidence_status("1994-14-12", [])
+    assert missing_status == "missing"
+
+
 class FakeProviderBackedExtractor:
     provider_name = "openai_responses_ad_extractor"
     provider_version = "gpt-test:ad_extraction_prompt_v1:testhash"
@@ -95,6 +1077,7 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     client: TestClient,
     db_session: Session,
     demo_data: dict[str, object],
+    monkeypatch,
 ) -> None:
     discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
 
@@ -106,7 +1089,107 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     assert review is not None
     assert review.status == "pending"
     assert review.extraction.provider_name == "deterministic_ad_extractor"
-    assert review.extraction.schema_version == "ad_extraction_v1"
+    assert review.extraction.schema_version == "ad_extraction_v3"
+    retained_pdf = b"%PDF-1.4\nretained AD test source\n%%EOF\n"
+    storage_key = "ad-sources/test/retained-ad.pdf"
+    retained_path = Path(get_settings().local_storage_path) / storage_key
+    retained_path.parent.mkdir(parents=True, exist_ok=True)
+    retained_path.write_bytes(retained_pdf)
+    source_document = ADSourceDocument(
+        source_system="federal_register",
+        source_type="document_pdf",
+        source_identifier="2026-12052",
+        source_url="https://www.govinfo.gov/content/pkg/FR-2026-06-16/pdf/2026-12052.pdf",
+        storage_backend="local",
+        storage_key=storage_key,
+        media_type="application/pdf",
+        content_hash=hashlib.sha256(retained_pdf).hexdigest(),
+        storage_bytes=len(retained_pdf),
+        captured_at=datetime.now(timezone.utc),
+        status="retained",
+        parser_name="test-parser",
+        parser_version="1",
+        metadata_json={},
+    )
+    db_session.add(source_document)
+    db_session.flush()
+    publication = db_session.scalar(
+        select(ADPublication).where(
+            ADPublication.directive_id == review.extraction.directive_id
+        )
+    )
+    if publication is None:
+        publication = ADPublication(
+            directive_id=review.extraction.directive_id,
+            source_system="federal_register",
+            source_type="document_pdf",
+            source_identifier="2026-12052",
+            title=review.extraction.directive.title,
+            pdf_url=source_document.source_url,
+            status="retained",
+            content_hash=source_document.content_hash,
+        )
+        db_session.add(publication)
+    publication.source_document = source_document
+    verified_source_pages = [{
+        "sourceDocumentId": source_document.id,
+        "contentHash": source_document.content_hash,
+        "pageNumber": 1,
+        "text": "Federal Register, June 16, 2026\n14 CFR Part 39\nSection 39.13 is amended by adding the following new airworthiness directive:\nAD 2026-12-01.\nThis AD applies to Cessna Model 172R airplanes, all serial numbers.\nReview the required corrective action.\n[FR Doc. 2026-12052]",
+    }]
+    review_ready_output = {
+        **review.proposed_output,
+        "confidence": 0.9,
+        "citations": [],
+        "uncertaintyReasons": [],
+        "applicabilityGroups": [v3_applicability_group(
+            source_document_id=source_document.id,
+            citation_text="This AD applies to Cessna Model 172R airplanes, all serial numbers.",
+            manufacturer="Cessna",
+            model="172R",
+            group_key="cessna-172r",
+        )],
+        "requirements": [{
+            "requirementKey": "source-review",
+            "applicabilityGroupKeys": ["cessna-172r"],
+            "requirementType": "one_time",
+            "actionText": "Review the required corrective action.",
+            "initialThresholds": [],
+            "recurringTriggers": [],
+            "combinationLogic": "all",
+            "conditions": [],
+            "terminatingAction": None,
+            "citations": [{
+                "sourceDocumentId": source_document.id,
+                "pageNumber": 1,
+                "text": "Review the required corrective action.",
+            }],
+            "confidence": 0.9,
+            "uncertaintyReasons": [],
+        }],
+    }
+    review.proposed_output = review_ready_output
+    review.extraction.output = review_ready_output
+    db_session.flush()
+    db_session.expire(review.extraction.directive, ["publications"])
+    review.extraction.input_content_hash = extraction_input_hash(
+        review.extraction.directive
+    )
+    review.extraction.raw_response = {
+        **(review.extraction.raw_response or {}),
+        "retainedSourcePagesCached": True,
+        "retainedSourcePages": verified_source_pages,
+        "sourcePageParser": "test-parser",
+    }
+    db_session.flush()
+    monkeypatch.setattr(
+        "app.api.routes.ads.full_text_pages_for_extraction",
+        lambda _: verified_source_pages,
+    )
+    monkeypatch.setattr(
+        "app.api.routes.ads.ensure_persisted_source_pages",
+        lambda *_: verified_source_pages,
+    )
 
     aircraft = demo_data["aircraft"]
     initial_stats = match_aircraft_ads(db_session, aircraft.id)
@@ -115,6 +1198,11 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     login(client, "owner.test@paprnav.local")
     assert client.get("/api/v1/ads/extraction-reviews").status_code == 403
 
+    login(client, "shop.test@paprnav.local")
+    shop_list_response = client.get("/api/v1/ads/extraction-reviews")
+    assert shop_list_response.status_code == 403
+    assert client.get(f"/api/v1/ads/source-documents/{source_document.id}/content").status_code == 403
+
     admin = create_user(
         db_session,
         "ad.admin@paprnav.local",
@@ -130,14 +1218,31 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     login(client, "ad.admin@paprnav.local")
     list_response = client.get("/api/v1/ads/extraction-reviews")
     assert list_response.status_code == 200
+    assert list_response.json()["currentOffset"] == 0
     reviews = list_response.json()["reviews"]
     assert len(reviews) == 1
+    assert list_response.json()["verifiedCount"] == 1
+    assert list_response.json()["quarantinedCount"] == 0
+    assert list_response.json()["approvalReadyCount"] == 1, reviews[0]["approvalBlockers"]
     assert reviews[0]["directive"]["federalRegisterDocumentNumber"] == "2026-12052"
     assert reviews[0]["extraction"]["inputContentHash"] == review.extraction.input_content_hash
-    assert "Airworthiness Directives" in reviews[0]["sourceText"]
+    assert "14 CFR Part 39" in reviews[0]["sourceText"]
+    assert reviews[0]["canApprove"] is True
+    assert reviews[0]["directive"]["officialAdNumber"] == "2026-12-01"
+    assert reviews[0]["sourceDocuments"][0]["sourceIdentifier"] == "2026-12052"
+    retained_response = client.get(reviews[0]["sourceDocuments"][0]["contentUrl"])
+    assert retained_response.status_code == 200
+    assert retained_response.content == retained_pdf
+    assert retained_response.headers["content-type"] == "application/pdf"
+    direct_review_response = client.get(
+        f"/api/v1/ads/extraction-reviews?reviewId={reviews[0]['id']}"
+    )
+    assert direct_review_response.status_code == 200
+    assert direct_review_response.json()["currentOffset"] == 0
+    assert direct_review_response.json()["reviews"][0]["id"] == reviews[0]["id"]
 
     edited_output: dict[str, Any] = reviews[0]["proposedOutput"]
-    edited_output["affectedProducts"] = []
+    edited_output["applicabilityGroups"] = []
     empty_applicability = client.post(
         f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
         json={
@@ -147,9 +1252,9 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
         },
     )
     assert empty_applicability.status_code == 422
-    assert "at least one attributable product" in empty_applicability.json()["detail"]
+    assert "at least one applicability group" in empty_applicability.json()["detail"]
 
-    edited_output["affectedProducts"] = ["Cessna 172R"]
+    edited_output["applicabilityGroups"] = review_ready_output["applicabilityGroups"]
     decision_response = client.post(
         f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
         json={"decision": "edited", "output": edited_output, "notes": "Confirmed from source PDF."},
@@ -158,6 +1263,51 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     decided = decision_response.json()["review"]
     assert decided["status"] == "edited"
     assert decided["decisionOutput"]["affectedProducts"] == ["Cessna 172R"]
+    decision_history = db_session.scalar(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id
+        )
+    )
+    assert decision_history is not None
+    assert decision_history.actor_user_id == admin.id
+    assert decision_history.decision == "edited"
+    assert decision_history.decision_output == review.extraction.output
+    second_admin = create_user(
+        db_session,
+        "second.ad.admin@paprnav.local",
+        "Second AD Platform Admin",
+    )
+    second_admin_org = create_organization(
+        db_session,
+        "Second Paprnav AD Operations",
+        "platform",
+    )
+    add_membership(db_session, second_admin_org, second_admin, "platform_admin")
+    db_session.commit()
+    login(client, "second.ad.admin@paprnav.local")
+    conflicting_response = client.post(
+        f"/api/v1/ads/extraction-reviews/{reviews[0]['id']}/decision",
+        json={
+            "decision": "rejected",
+            "notes": "Concurrent reviewer reached a different conclusion.",
+        },
+    )
+    assert conflicting_response.status_code == 409
+    conflict = db_session.scalar(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "decision_conflict",
+        )
+    )
+    assert conflict is not None
+    assert conflict.actor_user_id == second_admin.id
+    assert conflict.metadata_json["terminalReviewerUserId"] == admin.id
+    retained_path.write_bytes(b"%PDF-1.4\ntampered source\n%%EOF\n")
+    tampered_response = client.get(
+        f"/api/v1/ads/source-documents/{source_document.id}/content"
+    )
+    assert tampered_response.status_code == 409
+    retained_path.write_bytes(retained_pdf)
     target_ids = db_session.scalars(
         select(ADTargetApplicability.target_id).where(
             ADTargetApplicability.directive_id == review.extraction.directive_id
@@ -195,6 +1345,85 @@ def test_ad_extraction_routes_low_confidence_output_to_review(
     assert review.extraction.directive.review_status == "approved"
     assert review.extraction.directive.extraction_status == "complete"
 
+    login(client, "shop.test@paprnav.local")
+    monkeypatch.setattr(
+        "app.services.ad_release.persisted_source_pages",
+        lambda *_: (False, []),
+    )
+    assert client.get("/api/v1/ads/directives").json() == []
+    monkeypatch.setattr(
+        "app.services.ad_release.persisted_source_pages",
+        lambda *_: (True, verified_source_pages),
+    )
+    assert review.extraction.input_content_hash == extraction_input_hash(
+        review.extraction.directive
+    ), (
+        review.extraction.input_content_hash,
+        extraction_input_hash(review.extraction.directive),
+    )
+    released = client.get("/api/v1/ads/directives")
+    assert released.status_code == 200
+    assert [item["officialAdNumber"] for item in released.json()] == ["2026-12-01"]
+    structured = client.get(
+        "/api/v1/ads/directives?productType=aircraft&manufacturer=Cessna&model=172R"
+    )
+    assert structured.status_code == 200
+    assert [item["officialAdNumber"] for item in structured.json()] == ["2026-12-01"]
+    assert structured.json()[0]["applicabilityTargets"] == [{
+        "groupKey": "cessna-172r",
+        "productType": "aircraft",
+        "productSubtype": None,
+        "manufacturer": "Cessna",
+        "model": "172R",
+        "sourceManufacturer": "Cessna",
+        "sourceModel": "172R",
+    }]
+    assert client.get("/api/v1/ads/directives?manufacturer=Piper").json() == []
+    assert [item["officialAdNumber"] for item in client.get("/api/v1/ads/directives?q=172R").json()] == [
+        "2026-12-01"
+    ]
+    applicability = db_session.scalar(
+        select(ADTargetApplicability).where(
+            ADTargetApplicability.source_extraction_id == review.extraction_id,
+            ADTargetApplicability.status == "current",
+        )
+    )
+    applicability.target.make = "Piper"
+    db_session.flush()
+    assert client.get("/api/v1/ads/directives?manufacturer=Piper").json() == []
+    assert len(client.get("/api/v1/ads/directives?manufacturer=Cessna").json()) == 1
+    correction_bytes = b"%PDF-1.4\nlater correction\n%%EOF\n"
+    correction_document = ADSourceDocument(
+        source_system="federal_register",
+        source_type="document_pdf",
+        source_identifier="2026-12052-correction",
+        storage_backend="local",
+        storage_key="ad-sources/test/later-correction.pdf",
+        media_type="application/pdf",
+        content_hash=hashlib.sha256(correction_bytes).hexdigest(),
+        storage_bytes=len(correction_bytes),
+        captured_at=datetime.now(timezone.utc),
+        status="retained",
+    )
+    db_session.add(correction_document)
+    db_session.flush()
+    db_session.add(ADPublication(
+        directive_id=review.extraction.directive_id,
+        source_document_id=correction_document.id,
+        source_system="federal_register",
+        source_type="document_pdf",
+        source_identifier="2026-12052-correction",
+        content_hash=correction_document.content_hash,
+        status="retained",
+    ))
+    db_session.flush()
+    db_session.expire(review.extraction.directive, ["publications"])
+    blockers = extraction_approval_blockers(
+        review.extraction, review.extraction.output, verified_source_pages,
+    )
+    assert any("source document set changed" in blocker for blocker in blockers)
+    assert client.get("/api/v1/ads/directives").json() == []
+
 
 def test_provider_backed_extraction_uses_cache_and_routes_disagreement_to_review(db_session: Session) -> None:
     discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
@@ -218,27 +1447,28 @@ def test_provider_backed_extraction_uses_cache_and_routes_disagreement_to_review
     assert extraction is not None
     assert extraction.provider_version == provider.provider_version
     assert extraction.status == "needs_review"
-    assert "applicability_disagreement" in extraction.raw_response["reviewReasons"]
+    assert "invalid_requirement_evidence" in extraction.raw_response["reviewReasons"]
     assert "provider_uncertainty" in extraction.raw_response["reviewReasons"]
     assert db_session.scalar(select(ADExtractionReview)) is not None
     assert db_session.scalars(select(ADTargetApplicability)).all() == []
 
 
-def test_provider_backed_extraction_can_approve_valid_consistent_output(db_session: Session) -> None:
+def test_provider_backed_extraction_without_retained_pages_requires_review(db_session: Session) -> None:
     discover_federal_register_ads(db_session, client=FakeFederalRegisterClient())
     provider = FakeProviderBackedExtractor(output=provider_output())
 
     stats = process_pending_ad_extractions(db_session, llm_provider=provider)
 
     assert stats["seen"] == 1
-    assert stats["approved"] == 1
+    assert stats["approved"] == 0
+    assert stats["review_queued"] == 1
     extraction = db_session.scalar(select(ADExtraction).where(ADExtraction.provider_name == provider.provider_name))
     assert extraction is not None
-    assert extraction.status == "approved"
-    assert extraction.raw_response["reviewReasons"] == []
-    assert db_session.scalar(select(ADExtractionReview)) is None
+    assert extraction.status == "needs_review"
+    assert "invalid_requirement_evidence" in extraction.raw_response["reviewReasons"]
+    assert db_session.scalar(select(ADExtractionReview)) is not None
     applicabilities = db_session.scalars(select(ADTargetApplicability)).all()
-    assert len(applicabilities) == 1
+    assert applicabilities == []
 
 
 def test_provider_backed_extraction_falls_back_to_deterministic_on_provider_error(db_session: Session) -> None:
@@ -291,12 +1521,52 @@ def provider_output(
     confidence: float = 0.92,
     uncertainty_reasons: list[str] | None = None,
 ) -> dict[str, Any]:
+    product = (affected_products or ["Airbus Helicopters AS350"])[0]
+    if product == "Cessna 172R":
+        manufacturer, model, group_key = "Cessna", "172R", "cessna-172r"
+    else:
+        manufacturer, model, group_key = "Airbus Helicopters", "AS350", "airbus-as350"
     return {
         "adNumber": "2026-12-01",
         "title": "Airworthiness Directives; Airbus Helicopters",
         "effectiveDate": None,
         "publicationDate": "2026-06-16",
         "affectedProducts": affected_products if affected_products is not None else ["Airbus Helicopters"],
+        "applicabilityGroups": [{
+            "groupKey": group_key,
+            "productType": "rotorcraft",
+            "productSubtype": None,
+            "manufacturer": {
+                "sourceName": manufacturer,
+                "normalizedName": None,
+            },
+            "modelApplicability": {
+                "kind": "listed",
+                "models": [{
+                    "sourceDesignation": model,
+                    "normalizedDesignation": None,
+                    "aliases": [],
+                }],
+                "sourceText": f"{manufacturer} Model {model}",
+            },
+            "serialNumberApplicability": {
+                "kind": "all",
+                "values": [],
+                "ranges": [],
+                "excludedValues": [],
+                "sourceText": "all serial numbers",
+            },
+            "equipmentCombinationLogic": "all",
+            "equipmentConditions": [],
+            "conditions": [],
+            "citations": [{
+                "sourceDocumentId": "asd_example",
+                "pageNumber": 1,
+                "text": f"{manufacturer} Model {model}",
+            }],
+            "confidence": 0.95,
+            "uncertaintyReasons": [],
+        }],
         "complianceActions": ["Review source document for required corrective actions."],
         "complianceIntervals": [],
         "supersedesAdNumbers": [],
@@ -308,4 +1578,339 @@ def provider_output(
         "confidence": confidence,
         "citations": [{"field": "title", "source": "federal_register", "text": "Airworthiness Directives; Airbus Helicopters"}],
         "uncertaintyReasons": uncertainty_reasons or [],
+        "requirements": [],
+        "amocProvisions": [],
     }
+
+
+def v3_applicability_group(
+    *,
+    source_document_id: str,
+    citation_text: str,
+    manufacturer: str,
+    model: str,
+    group_key: str,
+) -> dict[str, Any]:
+    return {
+        "groupKey": group_key,
+        "productType": "aircraft",
+        "productSubtype": None,
+        "manufacturer": {"sourceName": manufacturer, "normalizedName": None},
+        "modelApplicability": {
+            "kind": "listed",
+            "models": [{
+                "sourceDesignation": model,
+                "normalizedDesignation": None,
+                "aliases": [],
+            }],
+            "sourceText": citation_text,
+        },
+        "serialNumberApplicability": {
+            "kind": "all",
+            "values": [],
+            "ranges": [],
+            "excludedValues": [],
+            "sourceText": "all serial numbers",
+        },
+        "equipmentCombinationLogic": "all",
+        "equipmentConditions": [],
+        "conditions": [],
+        "citations": [{
+            "sourceDocumentId": source_document_id,
+            "pageNumber": 1,
+            "text": citation_text,
+        }],
+        "confidence": 0.95,
+        "uncertaintyReasons": [],
+    }
+
+
+def test_visual_ocr_draft_exception_is_limited_to_an_exact_cited_model_cell() -> None:
+    source_pages = [{
+        "sourceDocumentId": "asd_table",
+        "pageNumber": 4,
+        "text": "Textron Aviation Tnc. 172D, 172T, 172K",
+    }]
+    proposal = {"applicabilityGroups": [{
+        "modelApplicability": {
+            "models": [{
+                "sourceDesignation": "172I",
+                "normalizedDesignation": None,
+                "aliases": [],
+            }],
+        },
+        "citations": [{
+            "sourceDocumentId": "asd_table",
+            "pageNumber": 4,
+            "text": "Textron Aviation Tnc. 172D, 172T, 172K",
+        }],
+        "uncertaintyReasons": [
+            "visual_ocr_model_cell_mismatch|modelIndex=0|visual=172I|parsed=172T|sourceDocumentId=asd_table|pageNumber=4"
+        ],
+    }]}
+
+    shadow, records = visual_ocr_validation_shadow(proposal, source_pages)
+
+    assert proposal["applicabilityGroups"][0]["modelApplicability"]["models"][0]["sourceDesignation"] == "172I"
+    assert shadow["applicabilityGroups"][0]["modelApplicability"]["models"][0]["sourceDesignation"] == "172T"
+    assert records == [{
+        "groupIndex": 0,
+        "modelIndex": 0,
+        "visual": "172I",
+        "parsed": "172T",
+        "sourceDocumentId": "asd_table",
+        "pageNumber": 4,
+    }]
+
+    proposal["applicabilityGroups"][0]["citations"][0]["sourceDocumentId"] = "asd_other"
+    with pytest.raises(ValueError, match="admitted cited page"):
+        visual_ocr_validation_shadow(proposal, source_pages)
+
+    proposal["applicabilityGroups"][0]["citations"][0]["sourceDocumentId"] = "asd_table"
+    proposal["applicabilityGroups"][0]["modelApplicability"]["models"][0][
+        "normalizedDesignation"
+    ] = "UNSUPPORTED-CANONICAL"
+    with pytest.raises(ValueError, match="normalizedDesignation must be null"):
+        visual_ocr_validation_shadow(proposal, source_pages)
+
+
+def test_staging_complete_proposal_is_audited_idempotent_and_reversible(
+    db_session: Session,
+    monkeypatch: pytest.MonkeyPatch,
+    tmp_path: Path,
+) -> None:
+    actor = create_user(db_session, "proposal.admin@paprnav.local", "Proposal Admin")
+    organization = create_organization(db_session, "Proposal Operations", "platform")
+    add_membership(db_session, organization, actor, "platform_admin")
+    directive = AirworthinessDirective(
+        ad_number="2026-12-01",
+        title="Airworthiness Directives; Airbus Helicopters",
+        status="candidate",
+        source_content_hash="source-hash",
+        extraction_status="needs_review",
+        review_status="pending",
+    )
+    db_session.add(directive)
+    db_session.flush()
+    source_text = (
+        "14 CFR Part 39 [Docket No. FAA-2026-1; Amendment 39-1; AD 2026-12-01] "
+        "Airworthiness Directives; Airbus Helicopters Model AS350 all serial numbers. "
+        "Inspect the rotorcraft."
+    )
+    source_pages = [{
+        "sourceDocumentId": "asd_example",
+        "pageNumber": 1,
+        "text": source_text,
+    }]
+
+    def complete_proposal(title: str) -> dict[str, Any]:
+        output = provider_output()
+        output["title"] = title
+        group = output["applicabilityGroups"][0]
+        group["modelApplicability"]["sourceText"] = "Airbus Helicopters Model AS350"
+        group["serialNumberApplicability"]["sourceText"] = "all serial numbers"
+        group["citations"] = [{
+            "sourceDocumentId": "asd_example",
+            "pageNumber": 1,
+            "text": "Airbus Helicopters Model AS350 all serial numbers",
+        }]
+        group["uncertaintyReasons"] = ["Human confirmation of applicability is pending."]
+        output["requirements"] = [{
+            "requirementKey": "inspection",
+            "applicabilityGroupKeys": ["airbus-as350"],
+            "requirementType": "one_time",
+            "actionText": "Inspect the rotorcraft.",
+            "initialThresholds": [],
+            "recurringTriggers": [],
+            "combinationLogic": "all",
+            "conditions": [],
+            "terminatingAction": None,
+            "citations": [{
+                "sourceDocumentId": "asd_example",
+                "pageNumber": 1,
+                "text": "Inspect the rotorcraft.",
+            }],
+            "confidence": 0.9,
+            "uncertaintyReasons": [],
+        }]
+        return output
+
+    prior = complete_proposal("Prior complete proposal")
+    extraction = ADExtraction(
+        directive_id=directive.id,
+        provider_name="test",
+        provider_version="1",
+        schema_version="ad_extraction_v3",
+        input_content_hash="source-hash",
+        status="needs_review",
+        confidence=0.8,
+        output=prior,
+        citations=[],
+        raw_response={},
+    )
+    db_session.add(extraction)
+    db_session.flush()
+    review = ADExtractionReview(
+        extraction_id=extraction.id,
+        status="pending",
+        proposed_output=prior,
+    )
+    db_session.add(review)
+    db_session.flush()
+    monkeypatch.setattr(
+        "app.scripts.stage_ad_review_proposal.ensure_persisted_source_pages",
+        lambda *_: source_pages,
+    )
+    monkeypatch.setattr(
+        "app.scripts.stage_ad_review_proposal.bounded_source_document_pages",
+        lambda pages, **_: pages,
+    )
+    proposed = complete_proposal("New complete proposal")
+
+    with pytest.raises(ValueError, match="applicability uncertainty"):
+        stage_review_proposal(
+            db_session,
+            ad_number=directive.ad_number,
+            review_id=review.id,
+            actor_user_id=actor.id,
+            loaded_proposal=proposed,
+            allow_incomplete=False,
+        )
+
+    first = stage_review_proposal(
+        db_session,
+        ad_number=directive.ad_number,
+        review_id=review.id,
+        actor_user_id=actor.id,
+        loaded_proposal=proposed,
+        allow_incomplete=True,
+    )
+    assert first["idempotent"] is False
+    assert review.status == "pending"
+    assert extraction.status == "needs_review"
+    history = db_session.scalars(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "proposal_staged",
+        )
+    ).all()
+    assert len(history) == 1
+    assert history[0].metadata_json["priorOutput"] == prior
+    assert history[0].metadata_json["priorExtractionOutput"] == prior
+    assert history[0].decision_output == review.proposed_output
+
+    monkeypatch.setattr(
+        "app.api.routes.ads.full_text_pages_for_extraction",
+        lambda *_: source_pages,
+    )
+    serialized = serialize_review(review)
+    assert serialized.proposalProvenance is not None
+    assert serialized.proposalProvenance.stagingDecisionId == history[0].id
+    assert serialized.proposalProvenance.actorUserId == actor.id
+    assert serialized.proposalProvenance.stagingMode == "allow_incomplete"
+
+    replay = stage_review_proposal(
+        db_session,
+        ad_number=directive.ad_number,
+        review_id=review.id,
+        actor_user_id=actor.id,
+        loaded_proposal=proposed,
+        allow_incomplete=True,
+    )
+    assert replay["idempotent"] is True
+    assert len(db_session.scalars(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "proposal_staged",
+        )
+    ).all()) == 1
+
+    dry_run = complete_proposal("Dry-run proposal")
+    dry_run_path = tmp_path / "dry-run-proposal.json"
+    dry_run_path.write_text(json.dumps(dry_run), encoding="utf-8")
+    connection = db_session.connection()
+    monkeypatch.setattr(
+        "app.scripts.stage_ad_review_proposal.SessionLocal",
+        lambda: Session(bind=connection, join_transaction_mode="create_savepoint"),
+    )
+    monkeypatch.setattr(
+        "sys.argv",
+        [
+            "stage_ad_review_proposal",
+            "--ad-number", directive.ad_number,
+            "--review-id", review.id,
+            "--actor-user-id", actor.id,
+            "--input", str(dry_run_path),
+            "--allow-incomplete",
+        ],
+    )
+    before_history_count = len(db_session.scalars(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "proposal_staged",
+        )
+    ).all())
+    stage_review_proposal_main()
+    db_session.expire_all()
+    review = db_session.get(ADExtractionReview, review.id)
+    extraction = db_session.get(ADExtraction, extraction.id)
+    assert review is not None and review.proposed_output["title"] == "New complete proposal"
+    assert extraction is not None and extraction.output["title"] == "New complete proposal"
+    assert len(db_session.scalars(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "proposal_staged",
+        )
+    ).all()) == before_history_count
+
+    extraction.output = prior
+    with pytest.raises(ValueError, match="output diverge"):
+        stage_review_proposal(
+            db_session,
+            ad_number=directive.ad_number,
+            review_id=review.id,
+            actor_user_id=actor.id,
+            loaded_proposal=proposed,
+            allow_incomplete=True,
+        )
+    extraction.output = dict(review.proposed_output)
+
+    with pytest.raises(ValueError, match="belongs to AD"):
+        stage_review_proposal(
+            db_session,
+            ad_number="2026-99-99",
+            review_id=review.id,
+            actor_user_id=actor.id,
+            loaded_proposal=proposed,
+            allow_incomplete=True,
+        )
+
+    rollback = stage_review_proposal(
+        db_session,
+        ad_number=directive.ad_number,
+        review_id=review.id,
+        actor_user_id=actor.id,
+        loaded_proposal=prior,
+        allow_incomplete=True,
+    )
+    assert rollback["idempotent"] is False
+    assert review.proposed_output["title"] == "Prior complete proposal"
+    history = db_session.scalars(
+        select(ADExtractionReviewDecision).where(
+            ADExtractionReviewDecision.review_id == review.id,
+            ADExtractionReviewDecision.event_type == "proposal_staged",
+        ).order_by(ADExtractionReviewDecision.decided_at)
+    ).all()
+    assert len(history) == 2
+    assert history[-1].metadata_json["priorOutput"]["title"] == "New complete proposal"
+
+    review.status = "approved"
+    with pytest.raises(ValueError, match="terminal"):
+        stage_review_proposal(
+            db_session,
+            ad_number=directive.ad_number,
+            review_id=review.id,
+            actor_user_id=actor.id,
+            loaded_proposal=prior,
+            allow_incomplete=True,
+        )
diff --git a/backend/tests/test_full_product_readiness.py b/backend/tests/test_full_product_readiness.py
index 329ca1c..05201d6 100644
--- a/backend/tests/test_full_product_readiness.py
+++ b/backend/tests/test_full_product_readiness.py
@@ -1,12 +1,14 @@
 from __future__ import annotations
 
 from datetime import date, datetime, timezone
+import hashlib
 from io import BytesIO
 from pathlib import Path
 
 from fastapi.testclient import TestClient
 from sqlalchemy import func, select
 from sqlalchemy.orm import Session
+from reportlab.pdfgen import canvas
 
 from app.models.core import (
     ADCostLedgerEntry,
@@ -14,6 +16,9 @@ from app.models.core import (
     ADCoverageSubscription,
     ADMatchAdjudication,
     ADMatchResult,
+    ADExtractionReview,
+    ADPublication,
+    ADSourceDocument,
     ADSourceSnapshot,
     ADSupersession,
     IngestionJob,
@@ -23,7 +28,11 @@ from app.models.core import (
     OCRRun,
 )
 from app.services.ad_coverage import resolve_aircraft_ad_coverage
+from app.services.ad_applicability import populate_applicability_from_extraction
+from app.core.config import get_settings
+from app.services.ad_extraction import extraction_input_hash, persisted_source_pages
 from app.services.ad_matching import match_aircraft_ads
+from app.services.ad_release import extraction_has_signed_release
 from app.services.drs_bulk_import import import_drs_bulk_rows, upsert_snapshot
 from app.services.ingestion import process_ingestion_job
 from tests.conftest import (
@@ -175,7 +184,7 @@ def _approved_ad(
     action: str,
     intervals: list[dict] | None = None,
 ):
-    return create_approved_extraction(
+    extraction = create_approved_extraction(
         db,
         title=f"Airworthiness Directives; {product}",
         document_number=f"fixture-{ad_number}",
@@ -184,6 +193,171 @@ def _approved_ad(
         compliance_actions=[action],
         compliance_intervals=intervals or [],
     )
+    product_parts = product.split()
+    manufacturer = product_parts[0]
+    model = product_parts[1]
+    product_type = (
+        "engine" if product.lower().endswith("engines")
+        else "propeller" if product.lower().endswith("propellers")
+        else "aircraft"
+    )
+    product_noun = {
+        "aircraft": "airplanes",
+        "engine": "engines",
+        "propeller": "propellers",
+    }[product_type]
+    applicability_text = (
+        f"This AD applies to {manufacturer} Model {model} {product_noun}, all serial numbers."
+    )
+    source_text = (
+        "14 CFR Part 39\nSection 39.13 is amended by adding the following new "
+        f"airworthiness directive: AD {ad_number}.\n{applicability_text}\n"
+        f"{action}\n[FR Doc. fixture-{ad_number}]"
+    )
+    storage_key = f"ad-sources/readiness/{ad_number}.pdf"
+    retained_path = Path(get_settings().local_storage_path) / storage_key
+    retained_path.parent.mkdir(parents=True, exist_ok=True)
+    writer = canvas.Canvas(str(retained_path))
+    y = 740
+    for line in source_text.splitlines():
+        writer.drawString(72, y, line)
+        y -= 20
+    writer.save()
+    retained_bytes = retained_path.read_bytes()
+    document = ADSourceDocument(
+        source_system="federal_register",
+        source_type="document_pdf",
+        source_identifier=f"fixture-{ad_number}",
+        source_url=extraction.output["sourceUrls"]["pdf"],
+        storage_backend="local",
+        storage_key=storage_key,
+        media_type="application/pdf",
+        content_hash=hashlib.sha256(retained_bytes).hexdigest(),
+        storage_bytes=len(retained_bytes),
+        captured_at=datetime.now(timezone.utc),
+        status="retained",
+    )
+    db.add(document)
+    db.flush()
+    db.add(ADPublication(
+        directive_id=extraction.directive_id,
+        source_document_id=document.id,
+        source_system="federal_register",
+        source_type="document_pdf",
+        source_identifier=f"fixture-{ad_number}",
+        title=extraction.directive.title,
+        pdf_url=document.source_url,
+        content_hash=document.content_hash,
+        status="retained",
+    ))
+    db.flush()
+    db.expire(extraction.directive, ["publications"])
+    extraction.input_content_hash = extraction_input_hash(extraction.directive)
+    recurring_triggers = []
+    for interval in intervals or []:
+        if interval.get("type") == "tach_hours":
+            recurring_triggers.append({
+                "metric": "tach_hours",
+                "value": interval["intervalHours"],
+                "unit": "hours",
+                "anchorKind": "last_compliance",
+                "sourceText": action,
+            })
+    output = {
+        **extraction.output,
+        "complianceIntervals": [
+            f"Every {interval['intervalHours']} tach hours"
+            for interval in (intervals or [])
+            if interval.get("type") == "tach_hours"
+        ],
+        "applicabilityGroups": [{
+            "groupKey": f"{manufacturer.lower()}-{model.lower()}",
+            "productType": product_type,
+            "productSubtype": None,
+            "manufacturer": {"sourceName": manufacturer, "normalizedName": None},
+            "modelApplicability": {
+                "kind": "listed",
+                "models": [{
+                    "sourceDesignation": model,
+                    "normalizedDesignation": None,
+                    "aliases": [],
+                }],
+                "sourceText": applicability_text,
+            },
+            "serialNumberApplicability": {
+                "kind": "all",
+                "values": [],
+                "ranges": [],
+                "excludedValues": [],
+                "sourceText": "all serial numbers",
+            },
+            "equipmentCombinationLogic": "all",
+            "equipmentConditions": [],
+            "conditions": [],
+            "citations": [{
+                "sourceDocumentId": document.id,
+                "pageNumber": 1,
+                "text": applicability_text,
+            }],
+            "confidence": 0.99,
+            "uncertaintyReasons": [],
+        }],
+        "requirements": [{
+            "requirementKey": "primary-action",
+            "applicabilityGroupKeys": [f"{manufacturer.lower()}-{model.lower()}"],
+            "requirementType": "recurring" if recurring_triggers else "one_time",
+            "actionText": action,
+            "initialThresholds": [],
+            "recurringTriggers": recurring_triggers,
+            "combinationLogic": "all",
+            "conditions": [],
+            "terminatingAction": None,
+            "citations": [{
+                "sourceDocumentId": document.id,
+                "pageNumber": 1,
+                "text": action,
+            }],
+            "confidence": 0.99,
+            "uncertaintyReasons": [],
+        }],
+        "amocProvisions": [],
+        "confidence": 0.99,
+        "citations": [],
+        "uncertaintyReasons": [],
+    }
+    extraction.schema_version = "ad_extraction_v3"
+    extraction.output = output
+    extraction.raw_response = {
+        "retainedSourcePagesCached": True,
+        "retainedSourcePages": [{
+            "sourceDocumentId": document.id,
+            "contentHash": document.content_hash,
+            "pageNumber": 1,
+            "text": source_text,
+        }],
+        "amocEnvelopeOrigin": "readiness_fixture",
+    }
+    admin = create_user(db, f"admin-{ad_number}@paprnav.local", "Fixture AD Admin")
+    admin_org = create_organization(db, f"AD Operations {ad_number}", "platform")
+    add_membership(db, admin_org, admin, "platform_admin")
+    db.add(ADExtractionReview(
+        extraction_id=extraction.id,
+        status="approved",
+        proposed_output=output,
+        decision_output=output,
+        decision="approved",
+        reviewer_user_id=admin.id,
+        reviewed_at=datetime.now(timezone.utc),
+    ))
+    extraction.directive.review_status = "approved"
+    extraction.directive.extraction_status = "complete"
+    extraction.directive.approved_at = datetime.now(timezone.utc)
+    populate_applicability_from_extraction(db, extraction)
+    db.flush()
+    assert extraction.input_content_hash == extraction_input_hash(extraction.directive)
+    assert persisted_source_pages(extraction.directive, extraction)[0] is True
+    assert extraction_has_signed_release(extraction) is True
+    return extraction
 
 
 def _import_drs_row(
@@ -256,12 +430,6 @@ def test_scenario_02_airframe_ad_uses_verified_page_evidence(
         db_session,
         aircraft_id=aircraft.id,
     )
-    _approved_ad(
-        db_session,
-        ad_number="2020-01-02",
-        product="Cessna 172R Airplanes",
-        action="Inspect the affected airframe.",
-    )
     _import_drs_row(
         db_session,
         ad_number="2020-01-02",
@@ -269,10 +437,16 @@ def test_scenario_02_airframe_ad_uses_verified_page_evidence(
         make="Cessna",
         model="172R",
     )
+    _approved_ad(
+        db_session,
+        ad_number="2020-01-02",
+        product="Cessna 172R Airplanes",
+        action="Inspect the affected airframe.",
+    )
     db_session.commit()
 
     stats = match_aircraft_ads(db_session, aircraft.id)
-    assert stats["matched"] == 1
+    assert stats["matched"] == 1, stats
     result = db_session.scalar(
         select(ADMatchResult).where(ADMatchResult.status == "candidate_satisfied")
     )
@@ -297,12 +471,6 @@ def test_scenario_03_engine_applicability_remains_component_specific(
         entry_date=date(2026, 1, 3),
         text="Complied with AD 2026-03-01 by inspecting the Lycoming engine.",
     )
-    _approved_ad(
-        db_session,
-        ad_number="2026-03-01",
-        product="Lycoming IO-360-L2A Engines",
-        action="Inspect the engine.",
-    )
     _import_drs_row(
         db_session,
         ad_number="2026-03-01",
@@ -310,6 +478,12 @@ def test_scenario_03_engine_applicability_remains_component_specific(
         make="Lycoming",
         model="IO-360-L2A",
     )
+    _approved_ad(
+        db_session,
+        ad_number="2026-03-01",
+        product="Lycoming IO-360-L2A Engines",
+        action="Inspect the engine.",
+    )
     db_session.commit()
 
     match_aircraft_ads(db_session, aircraft.id)
@@ -318,7 +492,7 @@ def test_scenario_03_engine_applicability_remains_component_specific(
     )
     assert result is not None
     assert result.installed_component.role == "engine"
-    assert result.target_applicability.target.product_type == "Engine"
+    assert result.target_applicability.target.product_type.lower() == "engine"
 
 
 def test_scenario_04_propeller_applicability_remains_component_specific(
@@ -334,12 +508,6 @@ def test_scenario_04_propeller_applicability_remains_component_specific(
         entry_date=date(2026, 1, 4),
         text="Complied with AD 2026-04-01 by inspecting the McCauley propeller.",
     )
-    _approved_ad(
-        db_session,
-        ad_number="2026-04-01",
-        product="McCauley 1A170 Propellers",
-        action="Inspect the propeller.",
-    )
     _import_drs_row(
         db_session,
         ad_number="2026-04-01",
@@ -347,6 +515,12 @@ def test_scenario_04_propeller_applicability_remains_component_specific(
         make="McCauley",
         model="1A170",
     )
+    _approved_ad(
+        db_session,
+        ad_number="2026-04-01",
+        product="McCauley 1A170 Propellers",
+        action="Inspect the propeller.",
+    )
     db_session.commit()
 
     match_aircraft_ads(db_session, aircraft.id)
@@ -355,7 +529,7 @@ def test_scenario_04_propeller_applicability_remains_component_specific(
     )
     assert result is not None
     assert result.installed_component.role == "propeller"
-    assert result.target_applicability.target.product_type == "Propeller"
+    assert result.target_applicability.target.product_type.lower() == "propeller"
 
 
 def test_scenario_05_recurring_ad_requires_adjudication(
@@ -384,7 +558,10 @@ def test_scenario_05_recurring_ad_requires_adjudication(
     result = db_session.scalar(select(ADMatchResult))
     assert result is not None
     assert result.status == "needs_adjudication"
-    assert "recurring_due_status_unknown" in result.unresolved_reasons
+    assert any(
+        reason.endswith("due_status_unknown")
+        for reason in result.unresolved_reasons
+    )
     assert result.adjudication.status == "pending"
 
 
diff --git a/frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx b/frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx
new file mode 100644
index 0000000..e987bb2
--- /dev/null
+++ b/frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx
@@ -0,0 +1,201 @@
+"use client";
+
+import Link from "next/link";
+import { FormEvent, useCallback, useEffect, useState } from "react";
+import { AlertTriangle, ArrowLeft, CheckCircle2, ExternalLink, FileWarning, RefreshCw, ShieldAlert, XCircle } from "lucide-react";
+import { useAuth } from "@/components/AuthProvider";
+import { PageHeader } from "@/components/PageHeader";
+import { Button } from "@/components/ui/button";
+import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
+import { Textarea } from "@/components/ui/textarea";
+import { ADExtractionReview, adSourceDocumentContentUrl, decideAdExtractionReview, listAdExtractionReviews } from "@/lib/api";
+
+function prettyJson(value: Record<string, unknown>) { return JSON.stringify(value, null, 2); }
+
+export default function ADExtractionReviewsPage() {
+  const { user } = useAuth();
+  const isAdmin = user?.memberships.some((membership) => membership.role === "platform_admin") ?? false;
+  const [reviews, setReviews] = useState<ADExtractionReview[]>([]);
+  const [drafts, setDrafts] = useState<Record<string, string>>({});
+  const [notes, setNotes] = useState<Record<string, string>>({});
+  const [message, setMessage] = useState<string | null>(null);
+  const [error, setError] = useState<string | null>(null);
+  const [isSaving, setIsSaving] = useState(false);
+  const [progress, setProgress] = useState({ total: 0, pending: 0, reviewed: 0, verified: 0, quarantined: 0, approvalReady: 0 });
+  const [reviewOffset, setReviewOffset] = useState(0);
+  const [targetReviewId, setTargetReviewId] = useState<string | null>(null);
+  const [queryReady, setQueryReady] = useState(false);
+  const [isLoading, setIsLoading] = useState(true);
+
+  useEffect(() => {
+    setTargetReviewId(new URLSearchParams(window.location.search).get("reviewId"));
+    setQueryReady(true);
+  }, []);
+
+  const loadReviews = useCallback(async () => {
+    if (!isAdmin || !queryReady) return;
+    setIsLoading(true);
+    setError(null);
+    try {
+      const response = await listAdExtractionReviews(reviewOffset, 1, targetReviewId);
+      setReviews(response.reviews);
+      setReviewOffset(response.currentOffset);
+      setProgress({ total: response.totalCount, pending: response.pendingCount, reviewed: response.reviewedCount, verified: response.verifiedCount, quarantined: response.quarantinedCount, approvalReady: response.approvalReadyCount });
+      setDrafts(response.reviews.reduce<Record<string, string>>((current, review) => {
+        current[review.id] = prettyJson(review.decisionOutput ?? review.proposedOutput);
+        return current;
+      }, {}));
+    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to load AD extraction reviews."); }
+    finally { setIsLoading(false); }
+  }, [isAdmin, queryReady, reviewOffset, targetReviewId]);
+
+  useEffect(() => { void loadReviews(); }, [loadReviews]);
+
+  async function submitDecision(review: ADExtractionReview, decision: "approved" | "edited" | "rejected") {
+    setIsSaving(true); setError(null); setMessage(null);
+    try {
+      const output = decision === "rejected" ? undefined : JSON.parse(drafts[review.id] || prettyJson(review.proposedOutput)) as Record<string, unknown>;
+      const response = await decideAdExtractionReview(review.id, { decision, output, notes: notes[review.id] || null });
+      setMessage(`Review ${response.review.status}.`);
+      await loadReviews();
+    } catch (caught) { setError(caught instanceof Error ? caught.message : "Unable to save AD review decision."); }
+    finally { setIsSaving(false); }
+  }
+
+  function handleSubmit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); }
+
+  function moveToReview(offset: number) {
+    setTargetReviewId(null);
+    window.history.replaceState({}, "", "/logbook/ads/reviews");
+    setReviewOffset(offset);
+  }
+
+  if (!isAdmin) {
+    return <div className="container mx-auto px-4 py-8"><PageHeader title="Admin extraction review" description="Downloaded source and machine extraction review is restricted to Paprnav administrators." /><Card className="mt-6"><CardContent className="py-10 text-center"><ShieldAlert className="mx-auto h-8 w-8 text-muted-foreground" /><p className="mt-3 font-medium">Administrator access required</p><p className="mt-1 text-sm text-muted-foreground">Maintenance shops use the released AD catalog and aircraft-specific compliance views.</p><Button asChild className="mt-4"><Link href="/logbook/ads">Return to AD research</Link></Button></CardContent></Card></div>;
+  }
+
+  return (
+    <div className="container mx-auto px-4 py-8">
+      <Button asChild variant="ghost" className="mb-3 -ml-3"><Link href="/logbook/ads"><ArrowLeft className="mr-2 h-4 w-4" />AD currency & research</Link></Button>
+      <PageHeader title="Admin extraction review" description={isLoading ? "Loading and re-verifying the selected review's retained source…" : `${progress.verified} source-indexed out of ${progress.total} · ${progress.approvalReady} approval candidates · ${progress.quarantined} source-quarantined · ${progress.pending} decisions pending`} />
+      <p className="mt-2 max-w-3xl text-sm text-muted-foreground">Compare the bounded official source section with the proposed structure. Queue totals use cached provenance for triage; opening a record re-verifies its exact PDF bytes and extracted text. Missing or identity-unverified evidence is quarantined and cannot be approved.</p>
+
+      <div className="mt-4 flex items-center justify-between gap-3">
+        <Button type="button" variant="outline" onClick={() => moveToReview(Math.max(0, reviewOffset - 1))} disabled={reviewOffset === 0 || isSaving}>Previous review</Button>
+        <span className="text-sm text-muted-foreground">{progress.total ? reviewOffset + 1 : 0} of {progress.total}</span>
+        <Button type="button" variant="outline" onClick={() => moveToReview(Math.min(progress.total - 1, reviewOffset + 1))} disabled={reviewOffset >= progress.total - 1 || isSaving}>Next review</Button>
+      </div>
+
+      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
+      {message ? <p className="mt-6 flex items-center gap-2 rounded-md border bg-card p-3 text-sm text-green-700 dark:text-green-400"><CheckCircle2 className="h-4 w-4" />{message}</p> : null}
+
+      <div className="mt-8 space-y-6">
+        {reviews.map((review) => (
+          <Card key={review.id}>
+            <CardHeader>
+              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
+                <div>
+                  <CardTitle className="text-lg">AD {review.directive.officialAdNumber ?? "Unnumbered"} · {review.directive.title}</CardTitle>
+                  <p className="mt-1 text-sm text-muted-foreground">{review.directive.adNumber !== review.directive.officialAdNumber ? `Normalized ID ${review.directive.adNumber} · ` : ""}confidence {(review.extraction.confidence * 100).toFixed(0)}% · {review.status}</p>
+                  <p className="mt-1 text-xs text-muted-foreground">{review.requirementCount} requirements · {review.unresolvedRequirementCount} unresolved · {review.sourcePages.length} bounded source pages</p>
+                </div>
+                <div className="flex flex-wrap gap-2">
+                  {review.directive.htmlUrl ? <Button asChild size="sm" variant="outline"><a href={review.directive.htmlUrl} target="_blank" rel="noreferrer"><ExternalLink className="mr-2 h-4 w-4" />Publisher HTML</a></Button> : null}
+                  {review.sourceDocuments.map((source) => <Button asChild key={source.id} size="sm" variant="outline"><a href={adSourceDocumentContentUrl(source.id)} target="_blank" rel="noreferrer"><FileWarning className="mr-2 h-4 w-4" />PDF {source.sourceIdentifier}</a></Button>)}
+                </div>
+              </div>
+            </CardHeader>
+            <CardContent>
+              {review.proposalProvenance ? <div className="mb-4 rounded-md border border-blue-600/30 bg-blue-600/10 p-3 text-sm text-blue-900 dark:text-blue-200"><p className="font-medium">Administrator-staged calibration draft</p><p>This is not raw model output. It was staged in {review.proposalProvenance.stagingMode.replaceAll("_", " ")} mode by administrator {review.proposalProvenance.actorUserId ?? "unknown"} at {new Date(review.proposalProvenance.stagedAt).toLocaleString()} (audit decision {review.proposalProvenance.stagingDecisionId}). Review every field against the retained source before publishing.</p></div> : null}
+              <div className={`mb-4 flex gap-3 rounded-md border p-3 text-sm ${review.canApprove ? "border-green-600/30 bg-green-600/10 text-green-800 dark:text-green-300" : "border-amber-600/30 bg-amber-600/10 text-amber-900 dark:text-amber-200"}`}>
+                {review.canApprove ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />}<div><p className="font-medium">{review.canApprove ? "Ready for admin decision" : review.evidenceStatus === "verified" ? "Extraction incomplete — approval blocked" : "Source evidence quarantined — approval blocked"}</p>{review.approvalBlockers.length ? <ul className="mt-1 list-disc space-y-1 pl-5">{review.approvalBlockers.map((blocker) => <li key={blocker}>{blocker}</li>)}</ul> : <p>{review.evidenceMessage}</p>}</div>
+              </div>
+              <form className="space-y-4" onSubmit={handleSubmit}>
+                <div className="rounded-md border bg-muted/20 p-3 text-sm">
+                  <p className="font-medium">Source attribution</p>
+                  {review.sourceDocuments.length ? <div className="mt-2 space-y-2">{review.sourceDocuments.map((source) => <div key={source.id}><p>{source.sourceSystem.replaceAll("_", " ")} · {source.sourceType.replaceAll("_", " ")} · {source.sourceIdentifier}</p><p className="text-xs text-muted-foreground">Retained {new Date(source.capturedAt).toLocaleString()} · SHA-256 {source.contentHash.slice(0, 16)}… · {(source.storageBytes / 1024 / 1024).toFixed(1)} MB{source.parserName ? ` · ${source.parserName} ${source.parserVersion ?? ""}` : ""}</p></div>)}</div> : <p className="mt-1 text-muted-foreground">No retained evidence document is attributable to this extraction.</p>}
+                </div>
+                <details className="rounded-md border p-3 text-sm">
+                  <summary className="cursor-pointer font-medium">How to complete the structured JSON</summary>
+                  <div className="mt-2 space-y-2 text-muted-foreground">
+                    <p><code>applicabilityGroups</code> is the authoritative applicability structure. Keep the official manufacturer in <code>sourceName</code> and each model in a separate <code>sourceDesignation</code>. Never combine manufacturer and model in one string or list them as unrelated sibling values.</p>
+                    <p>Use <code>normalizedName</code> and <code>normalizedDesignation</code> only for a conservative canonical identity; otherwise use <code>null</code>. Preserve serial scope, installed-equipment conditions, exceptions, and a page citation in the group.</p>
+                    <p>Every safety-relevant value must be visible verbatim in its cited excerpt: manufacturer, model, serial values and range endpoints, equipment or applicability conditions, compliance action, timing, terminating action, and AMOC authority or submission instructions. Do not infer or paraphrase a value that the retained page does not state.</p>
+                    <p><code>requirements</code> is a JSON list. Add one object for each independently testable one-time, recurring, conditional, or alternative obligation.</p>
+                    <p>Put the source-faithful instruction—not a paraphrase—in each requirement&apos;s <code>actionText</code>. List the exact <code>applicabilityGroupKeys</code> it governs. The server derives <code>affectedProducts</code> and <code>complianceActions</code>; do not use those compatibility summaries as source data.</p>
+                    <p>Every requirement needs at least one citation using the exact retained <code>sourceDocumentId</code>, one-based <code>pageNumber</code>, and a supporting excerpt displayed on the left.</p>
+                    <p>Each threshold or trigger must repeat its exact timing clause in <code>sourceText</code>. Preserve <code>anchorKind</code>: effective date, last compliance, installation, or manufacture are not interchangeable.</p>
+                    <p>Choose <code>combinationLogic</code> from the rule text: <code>whichever_first</code> uses the earliest limit, <code>whichever_later</code> uses the latest limit, and <code>alternative</code> remains blocked for explicit adjudication instead of being flattened to <code>all</code>.</p>
+                    <p>Use <code>amocProvisions</code> for the AD&apos;s alternative-method-of-compliance paragraph and approving authority. Do not encode that paragraph as an <code>alternative</code> compliance requirement.</p>
+                    <p>Keep each independently due obligation as a separate requirement object even when two obligations apply to the same applicability group. The matcher calculates and retains one due state per requirement.</p>
+                    <pre className="overflow-x-auto rounded bg-background p-3 text-xs text-foreground">{`"applicabilityGroups": [{
+  "groupKey": "paragraph-c-cessna-150a",
+  "productType": "aircraft",
+  "productSubtype": "small_airplane",
+  "manufacturer": {
+    "sourceName": "Cessna Aircraft Company",
+    "normalizedName": "Textron Aviation Inc."
+  },
+  "modelApplicability": {
+    "kind": "listed",
+    "models": [{
+      "sourceDesignation": "150A",
+      "normalizedDesignation": "150A",
+      "aliases": []
+    }],
+    "sourceText": "Model 150A airplanes"
+  },
+  "serialNumberApplicability": {
+    "kind": "all", "values": [], "ranges": [],
+    "excludedValues": [], "sourceText": "all serial numbers"
+  },
+  "equipmentCombinationLogic": "all",
+  "equipmentConditions": [],
+  "conditions": [],
+  "citations": [{
+    "sourceDocumentId": "copy from the page heading",
+    "pageNumber": 1,
+    "text": "copy the applicability source excerpt"
+  }],
+  "confidence": 0.9,
+  "uncertaintyReasons": []
+}],
+"requirements": [
+  {
+    "requirementKey": "paragraph-g-inspection",
+    "applicabilityGroupKeys": ["paragraph-c-cessna-150a"],
+    "requirementType": "conditional",
+    "actionText": "Copy the complete regulatory instruction from the cited source.",
+    "initialThresholds": [],
+    "recurringTriggers": [],
+    "combinationLogic": "all",
+    "conditions": ["Use the source's exact applicability condition."],
+    "terminatingAction": null,
+    "citations": [{
+      "sourceDocumentId": "copy from the page heading",
+      "pageNumber": 1,
+      "text": "copy the supporting source excerpt"
+    }],
+    "confidence": 0.9,
+    "uncertaintyReasons": []
+  }
+]`}</pre>
+                  </div>
+                </details>
+                <div className="grid gap-4 lg:grid-cols-2">
+                  <div className="space-y-2"><p className="text-sm font-medium">Bounded official source section</p><div className="max-h-[32rem] space-y-4 overflow-auto rounded-md border bg-muted/30 p-3 text-sm">{review.sourcePages.length ? review.sourcePages.map((page) => <section key={`${page.sourceDocumentId}-${page.pageNumber}`}><p className="mb-1 text-xs font-semibold text-muted-foreground">Page {page.pageNumber} · {page.sourceDocumentId}</p><p className="whitespace-pre-wrap">{page.text}</p></section>) : <p className="text-muted-foreground">No retained source section. The record is visible for remediation only and is not reviewable.</p>}</div></div>
+                  <div className="space-y-2"><p className="text-sm font-medium">Proposed structured extraction</p><Textarea className="min-h-[32rem] font-mono text-xs" value={drafts[review.id] ?? ""} onChange={(event) => setDrafts((current) => ({ ...current, [review.id]: event.target.value }))} disabled={review.status !== "pending" || review.evidenceStatus !== "verified" || review.extraction.schemaVersion !== "ad_extraction_v3"} /></div>
+                </div>
+                <Textarea placeholder="Review notes or source-remediation reason" value={notes[review.id] ?? ""} onChange={(event) => setNotes((current) => ({ ...current, [review.id]: event.target.value }))} disabled={review.status !== "pending"} />
+                <p className="text-xs text-muted-foreground">Approval records your identity, publishes the reviewed directive, materializes supported requirements, and replays affected aircraft compliance state.</p>
+                <div className="flex flex-wrap gap-2"><Button type="button" onClick={() => submitDecision(review, "approved")} disabled={isSaving || !review.canApprove}><CheckCircle2 className="mr-2 h-4 w-4" />Approve &amp; publish</Button><Button type="button" variant="outline" onClick={() => submitDecision(review, "edited")} disabled={isSaving || review.status !== "pending" || review.evidenceStatus !== "verified" || review.extraction.schemaVersion !== "ad_extraction_v3"}><RefreshCw className="mr-2 h-4 w-4" />Edit, validate &amp; publish</Button><Button type="button" variant="destructive" onClick={() => submitDecision(review, "rejected")} disabled={isSaving || review.status !== "pending"}><XCircle className="mr-2 h-4 w-4" />Reject / send to remediation</Button></div>
+              </form>
+            </CardContent>
+          </Card>
+        ))}
+        {isLoading && !reviews.length ? <Card><CardContent className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground"><RefreshCw className="h-4 w-4 animate-spin" />Re-verifying retained PDF bytes and source text…</CardContent></Card> : null}
+        {!isLoading && !reviews.length ? <Card><CardContent className="py-10 text-center text-sm text-muted-foreground">{targetReviewId ? `Review ${targetReviewId} was not found in the current queue.` : "No AD extraction reviews are queued."}</CardContent></Card> : null}
+      </div>
+    </div>
+  );
+}
diff --git a/frontend/paprnav-frontend/src/lib/api.ts b/frontend/paprnav-frontend/src/lib/api.ts
index 66272fb..a10d6e0 100644
--- a/frontend/paprnav-frontend/src/lib/api.ts
+++ b/frontend/paprnav-frontend/src/lib/api.ts
@@ -303,6 +303,7 @@ export interface AirworthinessDirective {
   id: string;
   discoveryRecordId: string | null;
   adNumber: string | null;
+  officialAdNumber: string | null;
   title: string;
   status: string;
   extractionStatus: string;
@@ -311,6 +312,15 @@ export interface AirworthinessDirective {
   publicationDate: string | null;
   htmlUrl: string | null;
   pdfUrl: string | null;
+  applicabilityTargets: Array<{
+    groupKey: string | null;
+    productType: string;
+    productSubtype: string | null;
+    manufacturer: string | null;
+    model: string | null;
+    sourceManufacturer: string | null;
+    sourceModel: string | null;
+  }>;
 }
 
 export interface ADExtraction {
@@ -336,10 +346,51 @@ export interface ADExtractionReview {
   extraction: ADExtraction;
   directive: AirworthinessDirective;
   sourceText: string;
+  sourcePages: Array<{
+    sourceDocumentId: string;
+    contentHash: string;
+    pageNumber: number;
+    text: string;
+  }>;
+  sourceDocuments: Array<{
+    id: string;
+    sourceSystem: string;
+    sourceType: string;
+    sourceIdentifier: string;
+    parentSourceIdentifier: string | null;
+    sourceUrl: string | null;
+    contentUrl: string;
+    mediaType: string | null;
+    contentHash: string;
+    storageBytes: number;
+    capturedAt: string;
+    publicationDate: string | null;
+    parserName: string | null;
+    parserVersion: string | null;
+  }>;
+  requirementCount: number;
+  unresolvedRequirementCount: number;
+  evidenceStatus: "verified" | "missing" | "identity_unverified" | "identity_mismatch" | "unverified";
+  evidenceMessage: string;
+  canApprove: boolean;
+  approvalBlockers: string[];
+  proposalProvenance: {
+    stagingDecisionId: string;
+    actorUserId: string | null;
+    stagedAt: string;
+    stagingMode: "strict" | "allow_incomplete";
+  } | null;
 }
 
 export interface ADExtractionReviewListResponse {
   reviews: ADExtractionReview[];
+  currentOffset: number;
+  totalCount: number;
+  pendingCount: number;
+  reviewedCount: number;
+  verifiedCount: number;
+  quarantinedCount: number;
+  approvalReadyCount: number;
 }
 
 export interface ADMatchEvidence {
@@ -427,6 +478,7 @@ export interface ADMatchResult {
   unresolvedReasons: string[];
   applicability: ADMatchApplicability | null;
   dueState: ADDueState | null;
+  dueStates: ADDueState[];
   algorithmName: string;
   algorithmVersion: string;
   inputHash: string;
@@ -732,8 +784,35 @@ export function extractLogbookEntries(jobId: string) {
   });
 }
 
-export function listAdExtractionReviews() {
-  return apiFetch<ADExtractionReviewListResponse>("/api/v1/ads/extraction-reviews");
+export function listAdExtractionReviews(offset = 0, limit = 1, reviewId?: string | null) {
+  const query = new URLSearchParams({ offset: String(offset), limit: String(limit) });
+  if (reviewId) query.set("reviewId", reviewId);
+  return apiFetch<ADExtractionReviewListResponse>(`/api/v1/ads/extraction-reviews?${query.toString()}`);
+}
+
+export function adSourceDocumentContentUrl(sourceDocumentId: string) {
+  return `${API_BASE_URL}/api/v1/ads/source-documents/${encodeURIComponent(sourceDocumentId)}/content`;
+}
+
+export function listAirworthinessDirectives(params: {
+  q?: string;
+  adNumber?: string;
+  status?: string;
+  productType?: string;
+  manufacturer?: string;
+  model?: string;
+  includeUnreviewed?: boolean;
+} = {}) {
+  const query = new URLSearchParams();
+  if (params.q) query.set("q", params.q);
+  if (params.adNumber) query.set("ad_number", params.adNumber);
+  if (params.status) query.set("status", params.status);
+  if (params.productType) query.set("productType", params.productType);
+  if (params.manufacturer) query.set("manufacturer", params.manufacturer);
+  if (params.model) query.set("model", params.model);
+  if (params.includeUnreviewed) query.set("includeUnreviewed", "true");
+  const suffix = query.toString() ? `?${query.toString()}` : "";
+  return apiFetch<AirworthinessDirective[]>(`/api/v1/ads/directives${suffix}`);
 }
 
 export function decideAdExtractionReview(
diff --git a/scripts/verify-t081-postgres-migrations.sh b/scripts/verify-t081-postgres-migrations.sh
new file mode 100755
index 0000000..8985fcc
--- /dev/null
+++ b/scripts/verify-t081-postgres-migrations.sh
@@ -0,0 +1,210 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
+backend_dir="$repo_root/backend"
+verify_db="paprnav_t081_verify_$$"
+database_url="postgresql+psycopg://paprnav_user:paprnav_password@db:5432/$verify_db"
+
+if [[ ! "$verify_db" =~ ^paprnav_t081_verify_[0-9]+$ ]]; then
+  printf 'Refusing unvalidated verification database name: %s\n' "$verify_db" >&2
+  exit 1
+fi
+
+cleanup() {
+  docker compose exec -T db dropdb --if-exists -U paprnav_user "$verify_db" >/dev/null
+}
+trap cleanup EXIT
+
+cd "$backend_dir"
+docker compose exec -T db createdb -U paprnav_user "$verify_db"
+
+run_alembic() {
+  docker compose exec -T -e DATABASE_URL="$database_url" api alembic "$@"
+}
+
+run_alembic upgrade head
+run_alembic downgrade 20260822_0023
+
+# A terminal/attributed v3 review with a null decision_output must still retain
+# an immutable pre-repair snapshot when 0024 conservatively reopens it.
+docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
+INSERT INTO ad_discovery_records (
+  id, federal_register_document_number, title, api_snapshot, content_hash,
+  classification, classification_confidence, classification_reason,
+  classifier_name, classifier_version
+) VALUES (
+  'adr_t081_null_decision', 'T081-NULL-DECISION', 'T081 migration fixture',
+  '{}'::json, repeat('a', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
+), (
+  'adr_t081_nonempty', 'T081-NONEMPTY', 'T081 nonempty AMOC fixture',
+  '{}'::json, repeat('c', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
+), (
+  'adr_t081_partial', 'T081-PARTIAL', 'T081 partial envelope fixture',
+  '{}'::json, repeat('d', 64), 'ad_candidate', 1.0, 'fixture', 'fixture', '1'
+);
+INSERT INTO airworthiness_directives (
+  id, discovery_record_id, ad_number, title, status, source_content_hash,
+  extraction_status, review_status
+) VALUES (
+  'ad_t081_null_decision', 'adr_t081_null_decision', '2026-81-01',
+  'T081 migration fixture', 'candidate', repeat('a', 64), 'complete', 'approved'
+), (
+  'ad_t081_nonempty', 'adr_t081_nonempty', '2026-81-02',
+  'T081 nonempty AMOC fixture', 'candidate', repeat('c', 64), 'complete', 'approved'
+), (
+  'ad_t081_partial', 'adr_t081_partial', '2026-81-03',
+  'T081 partial envelope fixture', 'candidate', repeat('d', 64), 'complete', 'approved'
+);
+INSERT INTO ad_extractions (
+  id, directive_id, provider_name, provider_version, schema_version,
+  input_content_hash, status, confidence, output, citations, raw_response
+) VALUES (
+  'adx_t081_null_decision', 'ad_t081_null_decision', 'fixture', '1',
+  'ad_extraction_v3', repeat('b', 64), 'approved', 1.0,
+  '{"adNumber":"2026-81-01","requirements":[],"applicabilityGroups":[]}'::json,
+  '[]'::json, '{}'::json
+), (
+  'adx_t081_nonempty', 'ad_t081_nonempty', 'fixture', '1',
+  'ad_extraction_v3', repeat('c', 64), 'approved', 1.0,
+  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
+  '[]'::json, '{}'::json
+), (
+  'adx_t081_partial', 'ad_t081_partial', 'fixture', '1',
+  'ad_extraction_v3', repeat('d', 64), 'approved', 1.0,
+  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[],"amocProvisions":[]}'::json,
+  '[]'::json, '{}'::json
+);
+INSERT INTO ad_extraction_reviews (
+  id, extraction_id, status, proposed_output, decision_output, decision,
+  reviewer_user_id, notes, reviewed_at
+) VALUES (
+  'arv_t081_null_decision', 'adx_t081_null_decision', 'approved',
+  '{"adNumber":"2026-81-01","requirements":[],"applicabilityGroups":[]}'::json,
+  NULL, 'approved', NULL, 'legacy terminal review', now()
+), (
+  'arv_t081_nonempty', 'adx_t081_nonempty', 'approved',
+  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
+  '{"adNumber":"2026-81-02","requirements":[],"applicabilityGroups":[],"amocProvisions":[{"authority":"FAA","method":"existing approved AMOC"}]}'::json,
+  'approved', NULL, 'preserve nonempty AMOC', now()
+), (
+  'arv_t081_partial', 'adx_t081_partial', 'edited',
+  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[]}'::json,
+  '{"adNumber":"2026-81-03","requirements":[],"applicabilityGroups":[],"amocProvisions":[]}'::json,
+  'edited', NULL, 'partial envelope state', now()
+);
+SQL
+run_alembic upgrade 20260823_0024
+
+repair_snapshot="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select count(*) || ':' || coalesce(max(metadata_json::jsonb ->> 'repairActor'), '') || ':' || coalesce(bool_and(decision_output is null), false) from ad_extraction_review_decisions where review_id = 'arv_t081_null_decision' and event_type = 'migration_repair_snapshot';"
+} | tr -d '[:space:]')"
+if [[ "$repair_snapshot" != "1:alembic:20260823_0024:true" ]]; then
+  printf 'Null-decision repair snapshot was not preserved: %s\n' "$repair_snapshot" >&2
+  exit 1
+fi
+review_reopened="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select status || ':' || coalesce(decision, 'null') || ':' || coalesce(reviewed_at::text, 'null') from ad_extraction_reviews where id = 'arv_t081_null_decision';"
+} | tr -d '[:space:]')"
+if [[ "$review_reopened" != "pending:null:null" ]]; then
+  printf 'Fixture review was not conservatively reopened: %s\n' "$review_reopened" >&2
+  exit 1
+fi
+cohort_result="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select count(*) || ':' || count(*) filter (where review.status = 'pending' and review.decision is null and review.reviewed_at is null) || ':' || count(*) filter (where extraction.status = 'needs_review' and extraction.raw_response::jsonb ->> 'amocEnvelopeOrigin' = 'migration_repair_pending') from ad_extraction_reviews review join ad_extractions extraction on extraction.id = review.extraction_id where extraction.id in ('adx_t081_null_decision','adx_t081_nonempty','adx_t081_partial');"
+} | tr -d '[:space:]')"
+if [[ "$cohort_result" != "3:3:3" ]]; then
+  printf 'Full ambiguous cohort was not conservatively reopened: %s\n' "$cohort_result" >&2
+  exit 1
+fi
+payload_result="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select (not (empty_extraction.output::jsonb ? 'amocProvisions'))::text || ':' || (not (partial_review.proposed_output::jsonb ? 'amocProvisions'))::text || ':' || (nonempty_extraction.output::jsonb #>> '{amocProvisions,0,method}') || ':' || (nonempty_review.proposed_output::jsonb #>> '{amocProvisions,0,method}') from ad_extractions empty_extraction cross join ad_extractions nonempty_extraction cross join ad_extraction_reviews nonempty_review cross join ad_extraction_reviews partial_review where empty_extraction.id = 'adx_t081_partial' and nonempty_extraction.id = 'adx_t081_nonempty' and nonempty_review.id = 'arv_t081_nonempty' and partial_review.id = 'arv_t081_partial';"
+} | tr -d '[:space:]')"
+if [[ "$payload_result" != "true:true:existingapprovedAMOC:existingapprovedAMOC" ]]; then
+  printf 'Empty/nonempty/partial AMOC payload repair was incorrect: %s\n' "$payload_result" >&2
+  exit 1
+fi
+snapshot_result="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select count(*) || ':' || count(*) filter (where decision_output is null) || ':' || count(*) filter (where decision_output::jsonb #>> '{amocProvisions,0,method}' = 'existing approved AMOC') || ':' || count(*) filter (where decision_output::jsonb -> 'amocProvisions' = '[]'::jsonb) from ad_extraction_review_decisions where review_id in ('arv_t081_null_decision','arv_t081_nonempty','arv_t081_partial') and event_type = 'migration_repair_snapshot';"
+} | tr -d '[:space:]')"
+if [[ "$snapshot_result" != "3:1:1:1" ]]; then
+  printf 'Partial/nonempty/null decision snapshots were not preserved: %s\n' "$snapshot_result" >&2
+  exit 1
+fi
+run_alembic upgrade 20260823_0024
+rerun_result="$({
+  docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" -Atc \
+    "select count(*) || ':' || count(*) filter (where event_type = 'migration_repair_snapshot') from ad_extraction_review_decisions where review_id in ('arv_t081_null_decision','arv_t081_nonempty','arv_t081_partial');"
+} | tr -d '[:space:]')"
+if [[ "$rerun_result" != "3:3" ]]; then
+  printf 'Repair rerun was not idempotent: %s\n' "$rerun_result" >&2
+  exit 1
+fi
+if run_alembic downgrade 20260822_0021 >/dev/null 2>&1; then
+  printf '0024 downgrade unexpectedly accepted live immutable decision history\n' >&2
+  exit 1
+fi
+still_at_head="$(run_alembic current | tr -d '\r')"
+if [[ "$still_at_head" != *"20260823_0024"* ]]; then
+  printf 'Guarded downgrade changed revision unexpectedly: %s\n' "$still_at_head" >&2
+  exit 1
+fi
+docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
+DELETE FROM ad_extraction_review_decisions WHERE review_id = 'arv_t081_null_decision';
+DELETE FROM ad_extraction_review_decisions WHERE review_id IN ('arv_t081_nonempty', 'arv_t081_partial');
+DELETE FROM ad_extraction_reviews WHERE id IN ('arv_t081_null_decision', 'arv_t081_nonempty', 'arv_t081_partial');
+UPDATE ad_extractions
+SET raw_response = '{"amocEnvelopeOrigin":"llm_provider"}'::json
+WHERE id IN ('adx_t081_null_decision', 'adx_t081_nonempty', 'adx_t081_partial');
+SQL
+if run_alembic downgrade 20260822_0021 >/dev/null 2>&1; then
+  printf '0024 downgrade unexpectedly accepted origin-marked v3 extraction\n' >&2
+  exit 1
+fi
+still_at_head="$(run_alembic current | tr -d '\r')"
+if [[ "$still_at_head" != *"20260823_0024"* ]]; then
+  printf 'V3 guard changed revision unexpectedly: %s\n' "$still_at_head" >&2
+  exit 1
+fi
+docker compose exec -T db psql -v ON_ERROR_STOP=1 -U paprnav_user -d "$verify_db" <<'SQL'
+DELETE FROM ad_extractions WHERE id IN ('adx_t081_null_decision', 'adx_t081_nonempty', 'adx_t081_partial');
+DELETE FROM airworthiness_directives WHERE id IN ('ad_t081_null_decision', 'ad_t081_nonempty', 'ad_t081_partial');
+DELETE FROM ad_discovery_records WHERE id IN ('adr_t081_null_decision', 'adr_t081_nonempty', 'adr_t081_partial');
+SQL
+run_alembic downgrade 20260822_0021
+
+parent_index="$({
+  docker compose exec -T db psql -U paprnav_user -d "$verify_db" -Atc \
+    "select indexdef from pg_indexes where indexname = 'uq_ad_target_applicability';"
+} | tr -d '[:space:]')"
+for column in directive_id target_id source_publication_id applicability_basis applicability_group_key; do
+  if [[ "$parent_index" != *"$column"* ]]; then
+    printf 'Missing %s from reconstructed 0021 applicability identity: %s\n' "$column" "$parent_index" >&2
+    exit 1
+  fi
+done
+if [[ "$parent_index" == *"source_extraction_id"* ]]; then
+  printf '0021 parent constraint unexpectedly contains source_extraction_id: %s\n' "$parent_index" >&2
+  exit 1
+fi
+
+run_alembic downgrade 20260809_0020
+run_alembic upgrade head
+docker compose exec -T -e DATABASE_URL="$database_url" api \
+  python -m app.scripts.verify_ad_review_concurrency
+docker compose exec -T -e DATABASE_URL="$database_url" api \
+  python -m app.scripts.verify_ad_staging_concurrency
+docker compose exec -T -e DATABASE_URL="$database_url" api \
+  python -m app.scripts.verify_ad_correction_workflow
+current_revision="$(run_alembic current | tr -d '\r')"
+if [[ "$current_revision" != *"20260823_0024"* ]]; then
+  printf 'Unexpected final migration revision: %s\n' "$current_revision" >&2
+  exit 1
+fi
+
+printf '12 passed out of 12\n'

```

## Untracked text files

### `.ai/ad-calibration/2024-14-03.v3.proposal.json`

size=43270; sha256=25a7cd3f7a7d16da76323ec5e2850c9f8d0aee370007647cd2d4800662cd2022; truncated=false

```text
{
  "adNumber": "2024-14-03",
  "title": "Autopilot System",
  "effectiveDate": "2024-08-20",
  "publicationDate": "2024-07-16",
  "applicabilityGroups": [
    {
      "groupKey": "commander-aircraft-table-1",
      "productType": "aircraft",
      "productSubtype": "airplane",
      "manufacturer": {"sourceName": "Commander Aircraft", "normalizedName": null},
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {"sourceDesignation": "112B", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "112TC", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "112TCA", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "114", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "114A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "114B", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "114TC", "normalizedDesignation": null, "aliases": []}
        ],
        "sourceText": "Table 1 to Paragraph (c)—Applicable Airplane Models"
      },
      "serialNumberApplicability": {
        "kind": "unknown", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [
        {
          "conditionKey": "garmin-gfc-500",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GFC 500", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "having a Garmin GFC 500 Autopilot System",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "having a Garmin GFC 500 Autopilot System"}]
        },
        {
          "conditionKey": "garmin-gsa-28-stc",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GSA 28", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76"}]
        }
      ],
      "conditions": ["certificated in any category"],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD, certificated in any category, having a Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Table 1 to Paragraph (c)—Applicable Airplane Models"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Commander Aircraft 112B, 112TC, 112TCA, 114, 114A, 114B, and 114TC Corporation"}
      ],
      "confidence": 0.82,
      "uncertaintyReasons": [
        "Serial-number scope is not stated separately in paragraph (c); retain unknown until the methodology explicitly resolves omission semantics.",
        "The retained table parser separates the final word Corporation from Commander Aircraft; sourceName preserves only the contiguous parsed identity pending table remediation."
      ]
    },
    {
      "groupKey": "daher-aerospace-table-1",
      "productType": "aircraft",
      "productSubtype": "airplane",
      "manufacturer": {"sourceName": "DAHER AEROSPACE", "normalizedName": null},
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {"sourceDesignation": "TB 20", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TB 21", "normalizedDesignation": null, "aliases": []}
        ],
        "sourceText": "Table 1 to Paragraph (c)—Applicable Airplane Models"
      },
      "serialNumberApplicability": {
        "kind": "unknown", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [
        {
          "conditionKey": "garmin-gfc-500",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GFC 500", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "having a Garmin GFC 500 Autopilot System",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "having a Garmin GFC 500 Autopilot System"}]
        },
        {
          "conditionKey": "garmin-gsa-28-stc",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GSA 28", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76"}]
        }
      ],
      "conditions": ["certificated in any category"],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD, certificated in any category, having a Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Table 1 to Paragraph (c)—Applicable Airplane Models"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "DAHER AEROSPACE TB 20 and TB 21"}
      ],
      "confidence": 0.9,
      "uncertaintyReasons": ["Serial-number scope is not stated separately in paragraph (c); retain unknown until the methodology explicitly resolves omission semantics."]
    },
    {
      "groupKey": "mooney-international-table-1",
      "productType": "aircraft",
      "productSubtype": "airplane",
      "manufacturer": {"sourceName": "Mooney International", "normalizedName": null},
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {"sourceDesignation": "M20C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20J", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M20S", "normalizedDesignation": null, "aliases": []}
        ],
        "sourceText": "Table 1 to Paragraph (c)—Applicable Airplane Models"
      },
      "serialNumberApplicability": {
        "kind": "unknown", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [
        {
          "conditionKey": "garmin-gfc-500",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GFC 500", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "having a Garmin GFC 500 Autopilot System",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "having a Garmin GFC 500 Autopilot System"}]
        },
        {
          "conditionKey": "garmin-gsa-28-stc",
          "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GSA 28", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76"}]
        }
      ],
      "conditions": ["certificated in any category"],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD, certificated in any category, having a Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Table 1 to Paragraph (c)—Applicable Airplane Models"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Mooney International M20C, M20D, M20E, M20F, M20G, M20J, M20K, M20M, Corporation M20R, and M20S"}
      ],
      "confidence": 0.82,
      "uncertaintyReasons": [
        "Serial-number scope is not stated separately in paragraph (c); retain unknown until the methodology explicitly resolves omission semantics.",
        "The retained table parser separates the final word Corporation from Mooney International; sourceName preserves only the contiguous parsed identity pending table remediation."
      ]
    },
    {
      "groupKey": "piper-aircraft-table-1",
      "productType": "aircraft",
      "productSubtype": "airplane",
      "manufacturer": {"sourceName": "Piper Aircraft, Inc.", "normalizedName": null},
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {"sourceDesignation": "PA-24", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-24-250", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-24-260", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-140", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-150", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-151", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-160", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-161", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-180", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-181", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-201T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-235", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28-236", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28R-180", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28R-200", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28R-201", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28R-201T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28RT-201", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-28RT-201T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-30", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-39", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-260", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-300", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-301", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-301FT", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-301T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32-301XTC", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32R-300", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32RT-300", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32RT-300T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32R-301 (HP)", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32R-301 (SP)", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "PA-32R-301T", "normalizedDesignation": null, "aliases": []}
        ],
        "sourceText": "Table 1 to Paragraph (c)—Applicable Airplane Models"
      },
      "serialNumberApplicability": {
        "kind": "unknown", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [
        {
          "conditionKey": "garmin-gfc-500", "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GFC 500", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [], "conditionText": "having a Garmin GFC 500 Autopilot System",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "having a Garmin GFC 500 Autopilot System"}]
        },
        {
          "conditionKey": "garmin-gsa-28-stc", "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GSA 28", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76"}]
        }
      ],
      "conditions": ["certificated in any category"],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD, certificated in any category, having a Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Table 1 to Paragraph (c)—Applicable Airplane Models"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Piper Aircraft, Inc. PA-24, PA-24-250, and PA-24-260 Piper Aircraft, Inc. PA-28-140, PA-28-150, PA-28-151, PA-28-160, PA-28-161, PA-28-180, PA-28-181, PA-28-201T, PA-28-235, PA-28-236, PA-28R-180, PA-28R-200, PA-28R-201, PA-28R-201T, PA-28RT-201, and PA-28RT-201 T Piper Aircraft, Inc. PA-30 and PA-39 Piper Aircraft, Inc. PA-32-260, PA-32-300, PA-32-301, PA-32-301FT, PA-32-301T, PA-32-301XTC, PA-32R-300, PA-32RT-300, PA-32RT-300T, PA-32R-301 (HP), PA-32R-301 (SP), and PA-32R-301 T"}
      ],
      "confidence": 0.78,
      "uncertaintyReasons": [
        "Serial-number scope is not stated separately in paragraph (c); retain unknown until the methodology explicitly resolves omission semantics.",
        "visual_ocr_model_cell_mismatch|modelIndex=18|visual=PA-28RT-201T|parsed=PA-28RT-201 T|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=3",
        "visual_ocr_model_cell_mismatch|modelIndex=32|visual=PA-32R-301T|parsed=PA-32R-301 T|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=3"
      ]
    },
    {
      "groupKey": "textron-aviation-table-1",
      "productType": "aircraft",
      "productSubtype": "airplane",
      "manufacturer": {"sourceName": "Textron Aviation Inc.", "normalizedName": null},
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {"sourceDesignation": "19A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "B19", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M19A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A23A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A23-19", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A23-24", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "B23", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "C23", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A24", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A24R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "B24R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "C24R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "C35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "D35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "E35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "G35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "35-33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "35-A33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "35-B33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "35-C33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "35-C33A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "36", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A36", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "A36TC", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "B36TC", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "E33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "E33A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "E33C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F33A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F33C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "G33", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "H35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "J35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "K35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "M35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "N35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "P35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "S35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "V35", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "V35A", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "V35B", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172I", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172L", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172N", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172P", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172Q", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172S", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172L", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172N", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F172P", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "172RG", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "P172D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "R172K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "FR172K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "177B", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "177RG", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F177RG", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182J", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182L", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182N", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182P", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182Q", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182R", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182S", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "182T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F182P", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "F182Q", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "FR182", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "R182", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T182", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T182T", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TR182", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "206H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "P206C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "P206D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "P206E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T206H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TP206C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TP206D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TP206E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TU206C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TU206D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TU206E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TU206F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "TU206G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "U206C", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "U206D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "U206E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "U206F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "U206G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210D", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210E", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210J", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210L", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "210N", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210F", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210G", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210H", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210J", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210K", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210L", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210M", "normalizedDesignation": null, "aliases": []},
          {"sourceDesignation": "T210N", "normalizedDesignation": null, "aliases": []}
        ],
        "sourceText": "Table 1 to Paragraph (c)—Applicable Airplane Models"
      },
      "serialNumberApplicability": {
        "kind": "unknown", "values": [], "ranges": [], "excludedValues": [],
        "sourceText": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [
        {
          "conditionKey": "garmin-gfc-500", "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GFC 500", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [], "conditionText": "having a Garmin GFC 500 Autopilot System",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "having a Garmin GFC 500 Autopilot System"}]
        },
        {
          "conditionKey": "garmin-gsa-28-stc", "productType": "equipment",
          "manufacturer": {"sourceName": "Garmin", "normalizedName": null},
          "model": {"sourceDesignation": "GSA 28", "normalizedDesignation": null, "aliases": []},
          "softwareVersions": [],
          "conditionText": "includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76",
          "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76"}]
        }
      ],
      "conditions": ["certificated in any category"],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "This AD applies to all airplane models specified in Table 1 to paragraph (c) of this AD, certificated in any category, having a Garmin GFC 500 Autopilot System that includes an optional GSA 28 pitch trim servo installed per Supplemental Type Certificate No. SA01866WI using Master Drawing List 005–01264–00, Revisions 1 through 76."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Table 1 to Paragraph (c)—Applicable Airplane Models"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 3, "text": "Textron Aviation Inc. 19A, B19, M19A, A23A, A23-19, A23-24, B23, C23, A24, ( type certificate A24R, B24R, and C24R previously held by Beech Aircraft Corporation, Raytheon Aircraft Company, Hawker Beechcraft Corporation, and Beechcraft Corporation) Textron Aviation Inc. C35, D35, E35, F35, and G35 ( type certificate previously held by Beech Aircraft Corporation, Raytheon Aircraft Company, Hawker Beechcraft Corporation, and Beechcraft Corporation) Textron Aviation Inc. 35-33, 35-A33, 35-B33, 35-C33, 35-C33A, 36, A36, A36TC, (type certificate B36TC, E33, E33A, E33C, F33, F33A, F33C, G33, H35, J35, previously held by Beech K35, M35, N35, P35, S35, V35, V35A, and V35B"},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 4, "text": "Type certificate holder Airplane model Aircraft Corporation, Raytheon Aircraft Company, Hawker Beechcraft Corporation, and Beechcraft Corporation) Textron Aviation Tnc. 172D, 172E, 172F, 172G, 172H, 172T, 172K, 172L, 172M, 172N, ( type certificate 172P, 172Q, 172R, and 172S previously held by Cessna Aircraft Company) Textron Aviation Inc. Fl 72E, Fl 72F, Fl 72G, Fl 72H, Fl 72K, Fl 72L, Fl 72M, Fl 72N, ( type certificate F172P previously held by Cessna Aircraft Company) Textron Aviation Inc. 172RG, Pl 72D, and Rl 72K ( type certificate previously held by Cessna Aircraft Company) Textron Aviation Inc. FR172K (type certificate previously held by Cessna Aircraft Company) Textron Aviation Inc. 177B (type certificate previously held by Cessna Aircraft Company) Textron Aviation Inc. 177RG (type certificate previously held by Cessna Aircraft Company) Textron Aviation Inc. F177RG ( type certificate previously held by Cessna Aircraft Company) Textron Aviation Inc. 182E, 182F, 182G, 182H, 182J, 182K, 182L, 182M, 182N, 182P, ( type certificate 182Q, 182R, 182S, 182T, F182P, F182Q, FR182, R182, T182, previously held by Cessna T182T, and TR182 Aircraft Company) Textron Aviation Inc. 206H,P206C,P206D,P206E, T206H,TP206C, TP206D, ( type certificate TP206E, TU206C, TU206D, TU206E, TU206F, TU206G, previously held by Cessna U206C, U206D, U206E, U206F, and U206G Aircraft Company) Textron Aviation Inc. 210D, 210E, 210F, 2100, 210H, 210J, 210K, 210L, 210M, 210N, (type certificate T210F, T210G, T210H, T210J, T210K, T210L, T210M, and previously held by Cessna T210N Aircraft Company)"}
      ],
      "confidence": 0.72,
      "uncertaintyReasons": [
        "Serial-number scope is not stated separately in paragraph (c); retain unknown until the methodology explicitly resolves omission semantics.",
        "visual_ocr_model_cell_mismatch|modelIndex=48|visual=172I|parsed=172T|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=57|visual=F172E|parsed=Fl 72E|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=58|visual=F172F|parsed=Fl 72F|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=59|visual=F172G|parsed=Fl 72G|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=60|visual=F172H|parsed=Fl 72H|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=61|visual=F172K|parsed=Fl 72K|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=62|visual=F172L|parsed=Fl 72L|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=63|visual=F172M|parsed=Fl 72M|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=64|visual=F172N|parsed=Fl 72N|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=67|visual=P172D|parsed=Pl 72D|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=68|visual=R172K|parsed=Rl 72K|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4",
        "visual_ocr_model_cell_mismatch|modelIndex=115|visual=210G|parsed=2100|sourceDocumentId=asd_63da3892cf8b4124b49e4066c57858a0|pageNumber=4"
      ]
    }
  ],
  "affectedProducts": [],
  "complianceActions": [],
  "complianceIntervals": ["Within 12 months after the effective date of this AD"],
  "supersedesAdNumbers": [],
  "requirements": [
    {
      "requirementKey": "g-software-update",
      "applicabilityGroupKeys": ["commander-aircraft-table-1", "daher-aerospace-table-1", "mooney-international-table-1", "piper-aircraft-table-1", "textron-aviation-table-1"],
      "requirementType": "one_time",
      "actionText": "Within 12 months after the effective date of this AD, update the Garmin GFC 500 Autopilot System software applicable to your airplane to a version that is not 8.01 or earlier for the G5, not version 9.01 or earlier for the G3X Touch, and not version 2.59 or earlier for the GI 275.",
      "initialThresholds": [{"metric": "calendar", "value": 12, "unit": "months", "anchorKind": "effective_date", "sourceText": "Within 12 months after the effective date of this AD"}],
      "recurringTriggers": [],
      "combinationLogic": "all",
      "conditions": ["unless already done"],
      "terminatingAction": null,
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "Comply with this AD within the compliance times specified, unless already done."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "Within 12 months after the effective date of this AD, update the Garmin GFC 500 Autopilot System software applicable to your airplane to a version that is not 8.01 or earlier for the G5, not version 9.01 or earlier for the G3X Touch, and not version 2.59 or earlier for the GI 275."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "Note 1 to paragraph (g): The software update can be done using Garmin Mandatory STC Service Bulletin 22123, Rev A, dated January 3, 2023. This AD also allows the installation of versions other than those listed in Garmin Mandatory STC Service Bulletin 22123, Rev A, dated January 3, 2023, provided those versions are not listed in paragraph (g) of this AD."}
      ],
      "confidence": 0.88,
      "uncertaintyReasons": ["Schema gap: Note 1 is a non-mandatory compliance method and permitted alternative, not a separate obligation; v3 has no dedicated method/reference object, so the exact cited note is retained here pending schema expansion."]
    },
    {
      "requirementKey": "h-installation-prohibition",
      "applicabilityGroupKeys": ["commander-aircraft-table-1", "daher-aerospace-table-1", "mooney-international-table-1", "piper-aircraft-table-1", "textron-aviation-table-1"],
      "requirementType": "installation_prohibition",
      "actionText": "As of the effective date of this AD, do not install Garmin GFC 500 Autopilot System Software that is version 8.01 or earlier for the G5, version 9.01 or earlier for the G3X Touch, or version 2.59 or earlier for the GI 275, on any airplane.",
      "initialThresholds": [],
      "recurringTriggers": [],
      "combinationLogic": "all",
      "conditions": [],
      "terminatingAction": null,
      "citations": [{"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "As of the effective date of this AD, do not install Garmin GFC 500 Autopilot System Software that is version 8.01 or earlier for the G5, version 9.01 or earlier for the G3X Touch, or version 2.59 or earlier for the GI 275, on any airplane."}],
      "confidence": 0.98,
      "uncertaintyReasons": []
    }
  ],
  "amocProvisions": [
    {
      "provisionKey": "i-amoc",
      "authorityText": "The Manager, Central Certification Branch, FAA, has the authority to approve AMOCs for this AD, if requested using the procedures found in 14 CFR 39.19.",
      "approvingAuthority": "The Manager, Central Certification Branch, FAA",
      "submissionInstructions": "In accordance with 14 CFR 39.19, send your request to your principal inspector or local Flight Standards District Office, as appropriate. If sending information directly to the manager of the Central Certification Branch, send it to the attention of the person identified in paragraph (j)(1) of this AD. Information may be emailed to wichita-cos@faa.gov.",
      "conditions": ["Before using any approved AMOC, notify your appropriate principal inspector, or lacking a principal inspector, the manager of the local flight standards district office/certificate holding district office."],
      "citations": [
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "The Manager, Central Certification Branch, FAA, has the authority to approve AMOCs for this AD, if requested using the procedures found in 14 CFR 39.19. In accordance with 14 CFR 39.19, send your request to your principal inspector or local Flight Standards District Office, as appropriate. If sending information directly to the manager of the Central Certification Branch, send it to the attention of the person identified in paragraph (j)(1) of this AD. Information may be emailed to wichita-cos@faa.gov."},
        {"sourceDocumentId": "asd_63da3892cf8b4124b49e4066c57858a0", "pageNumber": 5, "text": "Before using any approved AMOC, notify your appropriate principal inspector, or lacking a principal inspector, the manager of the local flight standards district office/certificate holding district office."}
      ],
      "confidence": 0.98,
      "uncertaintyReasons": []
    }
  ],
  "sourceUrls": {
    "html": "https://www.govinfo.gov/content/pkg/FR-2024-07-16/html/2024-15529.htm",
    "pdf": "https://www.govinfo.gov/content/pkg/FR-2024-07-16/pdf/2024-15529.pdf",
    "publicInspectionPdf": null
  },
  "confidence": 0.76,
  "citations": [
    {"field": "effectiveDate", "source": "federal_register_document_pdf_page_1", "text": "DATES: This AD is effective August 20, 2024."},
    {"field": "publicationDate", "source": "federal_register_document_pdf_header", "text": "Tuesday, July 16, 2024"}
  ],
  "uncertaintyReasons": [
    "Human calibration draft only: table-image OCR discrepancies and absent explicit serial-number wording remain unresolved.",
    "No approval, publication, applicability materialization, matching, or due-state computation is authorized from this draft."
  ]
}

```
### `backend/app/scripts/verify_ad_staging_concurrency.py`

size=9866; sha256=2a4671f770b46b7b705b9001903f7bbfb075f95e47764749655f20ced4a7087e; truncated=false

```text
from __future__ import annotations

import threading

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.core import (
    ADExtraction,
    ADExtractionReview,
    ADExtractionReviewDecision,
    AirworthinessDirective,
    Organization,
    OrganizationMembership,
    User,
)
from app.scripts import stage_ad_review_proposal as staging


REVIEW_ID = "arv_t081_stage_concurrency"
EXTRACTION_ID = "adx_t081_stage_concurrency"
DIRECTIVE_ID = "ad_t081_stage_concurrency"
ADMIN_ID = "usr_t081_stage_admin"
APPROVER_ID = "usr_t081_stage_approver"
SOURCE_TEXT = (
    "14 CFR Part 39 [Docket No. FAA-2099-1; Amendment 39-1; AD 2099-00-82] "
    "Airworthiness Directives; Example Aircraft Model E-1, all serial numbers. "
    "Inspect the aircraft."
)
SOURCE_PAGES = [{
    "sourceDocumentId": "asd_t081_stage",
    "pageNumber": 1,
    "text": SOURCE_TEXT,
}]


def proposal(title: str) -> dict:
    citation = {
        "sourceDocumentId": "asd_t081_stage",
        "pageNumber": 1,
        "text": "Example Aircraft Model E-1, all serial numbers",
    }
    return {
        "adNumber": "2099-00-82",
        "title": title,
        "effectiveDate": None,
        "publicationDate": None,
        "applicabilityGroups": [{
            "groupKey": "example-e1",
            "productType": "aircraft",
            "productSubtype": "airplane",
            "manufacturer": {"sourceName": "Example Aircraft", "normalizedName": None},
            "modelApplicability": {
                "kind": "listed",
                "models": [{
                    "sourceDesignation": "E-1",
                    "normalizedDesignation": None,
                    "aliases": [],
                }],
                "sourceText": "Example Aircraft Model E-1",
            },
            "serialNumberApplicability": {
                "kind": "all",
                "values": [],
                "ranges": [],
                "excludedValues": [],
                "sourceText": "all serial numbers",
            },
            "equipmentCombinationLogic": "all",
            "equipmentConditions": [],
            "conditions": [],
            "citations": [citation],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "affectedProducts": [],
        "complianceActions": ["Inspect the aircraft."],
        "complianceIntervals": [],
        "supersedesAdNumbers": [],
        "sourceUrls": {"html": None, "pdf": None, "publicInspectionPdf": None},
        "confidence": 1.0,
        "citations": [],
        "uncertaintyReasons": [],
        "requirements": [{
            "requirementKey": "inspect",
            "applicabilityGroupKeys": ["example-e1"],
            "requirementType": "one_time",
            "actionText": "Inspect the aircraft.",
            "initialThresholds": [],
            "recurringTriggers": [],
            "combinationLogic": "all",
            "conditions": [],
            "terminatingAction": None,
            "citations": [{
                "sourceDocumentId": "asd_t081_stage",
                "pageNumber": 1,
                "text": "Inspect the aircraft.",
            }],
            "confidence": 1.0,
            "uncertaintyReasons": [],
        }],
        "amocProvisions": [],
    }


def seed() -> None:
    initial = proposal("Initial proposal")
    with SessionLocal() as db:
        db.execute(delete(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == REVIEW_ID
        ))
        review = db.get(ADExtractionReview, REVIEW_ID)
        if review is None:
            admin = User(
                id=ADMIN_ID,
                email="t081-stage-admin@example.invalid",
                name="T081 Stage Admin",
                password_hash="not-a-login-credential",
                status="active",
            )
            approver = User(
                id=APPROVER_ID,
                email="t081-stage-approver@example.invalid",
                name="T081 Stage Approver",
                password_hash="not-a-login-credential",
                status="active",
            )
            organization = Organization(
                id="org_t081_stage_concurrency",
                name="T081 Stage Verification",
                type="platform",
            )
            db.add_all([admin, approver, organization])
            db.flush()
            db.add_all([
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=ADMIN_ID,
                    role="platform_admin",
                    status="active",
                ),
                OrganizationMembership(
                    organization_id=organization.id,
                    user_id=APPROVER_ID,
                    role="platform_admin",
                    status="active",
                ),
            ])
            directive = AirworthinessDirective(
                id=DIRECTIVE_ID,
                ad_number="2099-00-82",
                title="T081 staging concurrency verification",
                status="candidate",
                source_content_hash="8" * 64,
                extraction_status="needs_review",
                review_status="pending",
            )
            extraction = ADExtraction(
                id=EXTRACTION_ID,
                directive=directive,
                provider_name="t081-verifier",
                provider_version="1",
                schema_version="ad_extraction_v3",
                input_content_hash="8" * 64,
                status="needs_review",
                confidence=1.0,
                output=initial,
                citations=[],
                raw_response={"verification": True},
            )
            review = ADExtractionReview(
                id=REVIEW_ID,
                extraction=extraction,
                status="pending",
                proposed_output=initial,
            )
            db.add(review)
        else:
            review.status = "pending"
            review.decision = None
            review.decision_output = None
            review.reviewer_user_id = None
            review.reviewed_at = None
            review.proposed_output = initial
            review.extraction.status = "needs_review"
            review.extraction.output = initial
            review.extraction.raw_response = {"verification": True}
            review.extraction.directive.review_status = "pending"
            review.extraction.directive.extraction_status = "needs_review"
        db.commit()


def main() -> None:
    seed()
    staging.ensure_persisted_source_pages = lambda *_: SOURCE_PAGES
    staging.bounded_source_document_pages = lambda pages, **_: pages

    approval_locked = threading.Event()
    stage_attempting = threading.Event()
    release_approval = threading.Event()
    stage_finished = threading.Event()
    outcomes: list[str] = []

    def approval_wins() -> None:
        with SessionLocal() as db:
            review = db.scalar(select(ADExtractionReview).where(
                ADExtractionReview.id == REVIEW_ID
            ).with_for_update())
            approval_locked.set()
            if not release_approval.wait(timeout=5):
                outcomes.append("approval_timeout")
                return
            review.status = "approved"
            review.decision = "approved"
            review.extraction.status = "approved"
            review.reviewer_user_id = APPROVER_ID
            db.commit()
            outcomes.append("approved")

    def stage_loses() -> None:
        with SessionLocal() as db:
            stage_attempting.set()
            try:
                staging.stage_review_proposal(
                    db,
                    ad_number="2099-00-82",
                    review_id=REVIEW_ID,
                    actor_user_id=ADMIN_ID,
                    loaded_proposal=proposal("Concurrent staged proposal"),
                    allow_incomplete=False,
                )
            except ValueError as exc:
                outcomes.append("stage_terminal" if "terminal" in str(exc) else str(exc))
            else:
                outcomes.append("stage_unexpected")
            finally:
                stage_finished.set()

    approval_thread = threading.Thread(target=approval_wins)
    stage_thread = threading.Thread(target=stage_loses)
    approval_thread.start()
    if not approval_locked.wait(timeout=5):
        raise SystemExit("Approval verifier did not lock the review row")
    stage_thread.start()
    if not stage_attempting.wait(timeout=5):
        raise SystemExit("Staging verifier did not attempt the row lock")
    stage_blocked = not stage_finished.wait(timeout=0.25)
    release_approval.set()
    approval_thread.join(timeout=5)
    stage_thread.join(timeout=5)

    with SessionLocal() as db:
        review = db.get(ADExtractionReview, REVIEW_ID)
        stage_decisions = db.scalars(select(ADExtractionReviewDecision).where(
            ADExtractionReviewDecision.review_id == REVIEW_ID,
            ADExtractionReviewDecision.event_type == "proposal_staged",
        )).all()
    checks = {
        "staging_blocked_on_approval_row_lock": stage_blocked,
        "approval_terminal_transition_committed": outcomes.count("approved") == 1,
        "staging_rechecked_terminal_state": outcomes.count("stage_terminal") == 1,
        "no_losing_staging_history_survived": not stage_decisions,
        "terminal_review_preserved": review is not None and review.status == "approved",
        "original_proposal_preserved": review is not None and review.proposed_output["title"] == "Initial proposal",
    }
    passed = sum(checks.values())
    print(f"{passed} passed out of {len(checks)}")
    if passed != len(checks):
        raise SystemExit(str(checks))


if __name__ == "__main__":
    main()

```
