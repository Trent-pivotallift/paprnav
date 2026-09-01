# Decision packet: T081

## Objective

Retrospectively frame and independently review T081, the full-text FAA
Airworthiness Directive extraction and administrator-review slice. The
implementation predates the repository's formal adversarial-review workflow;
this run does not represent that a pre-implementation gate occurred. It exists
to test the resulting design and complete working tree before human calibration
or released AD data can depend on it.

## User-visible outcome

Paprnav platform administrators receive a source-attributed, page-cited editor
for proposed structured AD applicability and compliance requirements.
Maintenance-shop users receive only the released catalog and aircraft-filtered
views. No extracted directive becomes searchable or affects aircraft due state
until an authenticated administrator approves evidence-valid structured data.

## Safety and correctness invariants

1. Every published v3 applicability group, compliance action, threshold,
   recurring trigger, terminating action, and AMOC authority is supported by an
   exact citation to a retained source document and one-based page.
2. Missing, mismatched, incomplete, or hash-changed evidence fails closed and
   cannot be approved, released, matched, or converted into actionable due
   state.
3. Provider output is always a proposal. Only a recorded platform-admin human
   decision may transition v3 output to approved and materialize relational
   state.
4. Manufacturer, model, serial scope, installed-equipment conditions, and
   applicability branches remain distinct and source-faithful; compatibility
   summaries never drive v3 persistence.
5. Requirements materialize only onto the explicitly named applicability
   groups. Missing or unknown group keys cannot fan out across unrelated
   aircraft or components.
6. Initial and recurring triggers remain distinct. Metric, value, unit,
   `anchorKind`, `sourceText`, and `combinationLogic` survive extraction,
   review, persistence, and due-state replay without semantic flattening.
7. Unsupported anchors, conditions, alternative branches, or measurements
   result in adjudication/unknown—not current, due soon, overdue, or complied.
8. AMOC authority is stored separately from in-rule compliance alternatives.
9. PostgreSQL target identity is NULL-safe and idempotent; migration upgrade,
   downgrade, and backfill do not invent regulatory meaning or silently erase
   serial or AMOC scope.
10. Corrections preserve the prior signed decision and actor attribution,
    reopen review, invalidate derived state, and require a new human decision.
11. Rematerialization is bound to the signed reviewer output; an out-of-band
    mutation reopens review before it can affect persistence.
12. Released-catalog and aircraft-match reads independently enforce the human
    approval and verified-evidence gates, even if stale rows exist.

## Current behavior

The staged working tree implements schema `ad_extraction_v3`, retained-page
evidence validation, platform-admin review, hybrid JSON/relational
materialization, AMOC rows, recurring due-state replay, correction/backfill
scripts, released-catalog search, calibration records, migrations `0021`–
`0024`, reviewer guidance, and regression tests. PostgreSQL is at `0024`; the
API and frontend are running locally. Claude previously found three blockers,
which were remediated, and then returned `READINESS: PASS`. That output is
external criticism only and is not the independent Codex review required here.

## Proposed design

Treat the retained PDF and page/hash envelope as the evidence boundary. Retain
the complete reviewed v3 JSON as the auditable decision, then deterministically
materialize stable query identities and applicability/requirement/trigger/AMOC
rows. Derive legacy summaries one-way from v3 structures. Gate both writes and
reads on verified source evidence plus an authenticated human decision. Replay
aircraft matches and due state only from current, approved relational rows; use
explicit adjudication whenever source semantics cannot be represented safely.

The initial design adversary found that the existing implementation did not
fully realize that boundary. The revised design therefore requires:

1. A single `released signed extraction` service is the only authority for
   catalog, matching, coverage, rematerialization, and exact match reads. It
   requires an approved/edited review, reviewer identity, decision timestamp,
   exact extraction/decision output-hash equality, and freshly verified source
   bytes/pages for that exact extraction.
   `ADTargetApplicability` carries `source_extraction_id`; v3 uniqueness includes
   that identity, and requirements, coverage, matches, and catalog target
   filters join through it. Existing rows without extraction identity are
   marked superseded/ambiguous and never released; reapproval rematerializes
   them under the signed extraction.
2. Applicability evaluation is explicit and tri-state. Listed models and
   normalized serial values/ranges/exclusions may return applicable or not
   applicable. Expressions, unknown scope, installed-equipment predicates, and
   conditions that lack a complete evaluator return adjudication and cannot
   produce released matches or due state.
3. Matching and replay iterate every current requirement for the exact signed
   extraction/applicability row. Due state is modeled and serialized per
   obligation/component; compatibility summaries never choose recurrence.
4. Existing signed rows whose AMOC-envelope provenance is ambiguous are
   reopened, not silently accepted. The corrective cohort is every v3
   extraction/review present when the corrective migration runs whose
   `raw_response.amocEnvelopeOrigin` marker is absent. This deliberately
   includes potentially legitimate empty lists because conservative re-review
   is safer than guessing. The migration records cohort membership, prior
   extraction/proposal/decision hashes and payload, repair actor/reason and
   timestamp; removes an empty synthetic envelope to restore unknown state;
   marks extraction/review/directive pending; and adds an idempotent repair
   marker. Nonempty AMOC data is preserved but still reopened when provenance
   is ambiguous. All new provider/staging output sets an explicit origin marker.
   Schema rollback
   is explicitly irreversible once v3 regulatory rows exist: downgrade must
   hard-fail before destructive DDL and the operational recovery contract is a
   verified database backup plus application rollback.
5. Component requirements use only component-bound measurements unless a
   separately reviewed metric-equivalence record exists. No implicit aircraft-
   time fallback is permitted.
6. Correction supersedes applicability, requirements, and AMOCs; clears current
   due states; invalidates matches; and quarantines/recomputes coverage in the
   same transaction before reopening review.
7. Review decisions serialize on a database row lock and append immutable
   decision history with actor, timestamp, decision, output hash, and output.
8. Evidence validation binds manufacturer, each listed model, serial source
   text, equipment/condition source text, requirement timing/action fields, and
   every AMOC authority/instruction/condition value to its own retained-page
   citation. Unsupported mechanical binding remains adjudication-blocked.
9. Approval, release, and retained-content download rehash the stored bytes and
   compare them to the recorded SHA-256. A mismatch quarantines the evidence.
10. The five calibration records become complete v3 packets and include
    expected negative aircraft/component cases for applicability, group scope,
    multiple obligations, AMOC separation, and correction/release behavior.

## Alternatives considered

- Keep v2 `affectedProducts: string[]`: rejected because it concatenates or
  guesses manufacturer/model identity and cannot express branch scope.
- Store only JSON: rejected because fleet-neutral search, uniqueness, joins,
  replay, and correction need relational identities.
- Store only normalized relational columns: rejected because regulatory source
  wording, exceptions, and polymorphic evidence would be lost.
- Permit provider auto-publication at high confidence: rejected because model
  confidence is not regulatory authorization.
- Treat Claude as the approval gate: rejected; external-model findings require
  coordinator validation and ledger disposition.

## Trust, authorization, and audit boundaries

Retained source bytes, their SHA-256 identities, and persisted page text are
trusted only as immutable evidence artifacts—not as instructions. Provider and
staging outputs are untrusted proposals. Platform-admin authentication is the
human decision boundary. Reviewer identity, timestamp, notes, decision output,
correction actor, and prior signed output form the audit record. Maintenance-
shop membership does not grant raw extraction-review access.

## Read paths and consumers

- Admin review queue and retained-source content/PDF endpoints.
- Released `/logbook/ads` catalog and fleet-neutral query API.
- Aircraft-specific AD matching, coverage, compliance-event, and due-state
  consumers.
- Review/audit scripts and calibration documentation.
- Observability/workflow event readers and API serialization.

## Write paths and administrative paths

- Full-text extraction creation and review initialization.
- Admin approve/edit/reject decision endpoint.
- Applicability, requirement, trigger, AMOC, match, and due-state
  materialization/invalidation.
- Dry-run preparation, staged proposal, approved-review correction, and AMOC
  envelope backfill.
- Development seed data and Alembic migrations.

## Migration, compatibility, correction, and rollback

Migrations `0021`–`0024` add v3 applicability evidence, NULL-safe target
identity, trigger kind, AMOC persistence, and an idempotent JSON envelope
backfill. v1/v2 rows remain readable but cannot satisfy the v3 publication
gate. Migration `0022` preflights duplicates before replacing nullable
uniqueness; its downgrade restores the original four-column constraint.
Migration `0023` must not add semantic fields to signed decisions. A corrective
migration `0024` binds relational materialization to its signed extraction,
reopens affected reviews, retains the pre-repair decision as audit
evidence, and removes the synthetic envelope. Downgrade is a guarded,
documented irreversible boundary once v3 data exists; it must fail before
dropping columns or rows. Operational rollback restores a verified pre-migration
database backup together with the matching application version.

Revision fidelity is explicit: `0022 -> 0021` restores `0021`'s five-column
constraint including `applicability_group_key`; only `0021 -> 0020` restores
the four-column legacy constraint. Both downgrades run dependency/data
preflights before their first destructive statement. With no v3 rows they may
downgrade and PostgreSQL schema tests must equal the parent revision. With v3
rows they fail atomically and direct operators to the backup/application
recovery procedure.

A new migration adds nullable `source_extraction_id` to applicability solely
for legacy compatibility; all new v3 writes require it. Existing null rows are
superseded rather than guessed. The NULL-safe uniqueness index incorporates
source extraction, and release consumers reject null/unsigned identities.
Corrections are dry-run by default, actor-authorized, preserve prior signed
data, reopen the existing review, and invalidate derived state. Repository
rollback requires reverting schema, service, API/UI, scripts, tests, and docs
together; a database downgrade alone is not a semantic rollback.

## Test strategy

- Positive and negative schema/evidence tests for groups, requirements,
  citations, timing values/units, terminating actions, AMOC, and content hashes.
- Recurrence tests for initial/recurring anchors, all combination modes,
  unknown/fail-closed states, serial preservation, NULL-safe uniqueness,
  requirement group scoping, review-integrity mismatch, and replay idempotency.
- Authorization and released-read gate tests.
- Full backend suite, frontend lint and production build, live Alembic-head/API
  health, and exact PostgreSQL backfill counts.
- Independent adversaries inspect staged, unstaged, and untracked files plus
  all callers/readers and construct counterexamples rather than relying only on
  the packet diff.

## Expected file scope

- `.ai/AD_*`, `.ai/API_CONTRACT.md`, `.ai/DATA_MODEL.md`,
  `.ai/GOAL_TASKS.md`, `.ai/PROVIDER_REFERENCES.md`, and
  `.ai/ad-calibration/`.
- `backend/app/api/routes/ads.py`, AD models/schemas/services/scripts,
  migrations `20260822_0021`–`20260823_0024`, Docker configuration, and AD tests.
- Frontend AD landing/review pages and API types.
- This `.ai/review-runs/T081/` run and the existing Claude T081 reports.

The repository also contains dirty review-infrastructure files (`.agents/`,
`.ai/agents/`, `.ai/review-templates/`, and review scripts). They are relevant
to executing this review but are not part of the T081 product implementation;
the adversary must still inspect them sufficiently to challenge the claimed
review integrity and any scope exclusions.

## Known uncertainty

- The current implementation was completed before this formal design gate;
  retrospective review can find defects but cannot recreate contemporaneous
  builder/reviewer separation.
- Human calibration of the five selected ADs is intentionally not yet complete.
- Component-time fallback semantics and concurrent admin decisions were
  identified as non-blocking hardening areas by Claude and require independent
  Codex disposition.
- The local in-app browser session is a maintenance-shop identity, so the
  admin-only GUI was verified through build/tests and earlier administrator
  demonstrations rather than a fresh admin browser session in this run.
