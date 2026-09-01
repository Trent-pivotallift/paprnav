# Decision packet: T081-V4-SCHEMA

## Objective

Design, but do not implement, a candidate `ad_extraction_v4` contract that
conforms to `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1. The design must
stop treating one large editable JSON document as the official source, the
query model, the aircraft record, and the resulting assessment. It must also
remove the repeated source-document IDs and source text observed in the V3
2024-14-03 calibration proposal.

This review run is a pre-implementation design gate. Approval of this packet
does not authorize a migration, application change, V3 data rewrite, or AD
publication.

The initial calibration gate covers the five retained AD packets plus the
structural and negative behavior of separately administered supporting
evidence. It must prove that absent or unverified incorporated service
bulletins and aircraft-specific AMOC-use evidence fail closed, and that an
authorized immutable retention/review workflow exists. It does not require a
real retained bulletin or actual aircraft-specific AMOC-use record to already
exist. Lawfully obtained real examples become regression fixtures when
available.

## User-visible outcome

Platform administrators review a compact, form-based AD decision against the
complete retained official document. Exact source clauses are highlighted and
stored once, then selected by evidence key from applicability, obligation,
timing, branch, and AMOC forms. Reusable installed-equipment or modification
conditions are entered once and may govern multiple manufacturer/model scopes.

Maintenance-shop and aircraft users continue to see customer-facing candidate
applicability, evidence-sufficiency, and due-state assessments. Those views are
derived from four independently versioned inputs: a signed structured AD
decision, aircraft configuration, aircraft maintenance/compliance evidence,
and any signed aircraft-specific determination. The complete PDF remains
available as retained evidence and is opened at its relevant page range.

## Safety and correctness invariants

1. A complete official AD or authoritative correction is retained as immutable
   bytes with a verified hash. V4 structured data never replaces or embeds the
   complete document.
2. An exact source clause is stored once as an immutable evidence fragment
   mechanically selected from an immutable source-hash-bound page rendition
   and text/coordinate version.
   Safety-relevant V4 values reference fragment keys and hashes; they do not
   repeat document IDs, page numbers, or clause text per model or requirement.
3. Official evidence, structured AD decisions, aircraft configuration,
   aircraft compliance evidence, and derived Paprnav assessments have separate
   tables, ownership, versioning, and authorization paths.
4. `null` never represents regulatory or configuration uncertainty. A
   safety-relevant value is known, explicitly not applicable, or explicitly
   unknown with reason, evidence scope, and temporal scope. Safety-relevant
   `not_applicable` assertions also require evidence, reason, and scope.
5. Product manufacturer, model/series, serial/part-number scope, product role,
   installed-equipment predicates, modifications, exclusions, and effective
   periods remain separately queryable. No combined display string drives
   matching.
6. A shared condition is authored once. Applicability rules reference condition
   keys and may reference multiple product scopes without copying the condition
   or its evidence.
7. Each independently actionable obligation is authored once and has an
   explicit recursive activation expression over applicability rules.
   Relational persistence does not duplicate the
   obligation once per model or applicability target.
8. Exact action, timing, exception, branch, and terminating-action wording is
   reachable through evidence keys. Normalized action and timing values never
   overwrite or silently paraphrase the source clause.
9. An unresolved predicate or value may create a candidate or
   human-determination state, but it cannot produce affirmative applicability,
   compliance, terminating-action credit, or an authoritative due value.
10. A general AD AMOC provision is separate from an aircraft-specific AMOC
    approval. Unverified aircraft evidence is customer-facing as **Possible
    AMOC—unverified** and receives no compliance credit.
11. Referenced service bulletins have an identity and access/retention state.
    If unseen content is necessary to support a conclusion, that conclusion
    remains explicitly unknown until an administrator adds and verifies the
    document.
    Retention requires authorized administrator ingestion of immutable original
    bytes, verified hash, source attribution, and human admission review before
    any dependent semantics become actionable.
12. STC identity, revision, installation/removal evidence, affected
    configuration, and effective period are preserved when supported. Detected
    but incomplete STC information remains explicit unknown, never inferred.
13. Provider output remains an unsigned proposal. Only an attributable
    platform-administrator decision may publish a V4 structured AD version.
14. A recurring next-due date, time, or cycle is authoritative only after the
    required attributable human review. Recalculation from unchanged signed
    inputs is deterministic and needs no new review.
    The same rule applies after bulletin/AMOC evidence admission: changed signed
    input requires invalidation/review; identical signed-input replay does not.
15. Derived summaries, compatibility labels, search indexes, candidate ranks,
    and cache rows are reproducible projections and cannot be accepted as
    authoritative write input.
16. Corrections and supersession append versions, retain the prior signed
    decision, invalidate affected projections/assessments, and fail closed
    during reevaluation.
17. V3 audit records remain byte-for-byte immutable. No mechanical V3-to-V4
    transformation may publish or claim human review.
18. Rollback cannot silently restore a V3 decision known to have been corrected
    by V4; such a directive is quarantined until an eligible signed decision is
    selected.

## Current behavior

The current system retains source bytes in `ad_source_documents`, relates them
to directives through `ad_publications`, and stores provider/reviewer JSON in
`ad_extractions.output` and `ad_extraction_reviews.decision_output`. V3
applicability is represented by `applicabilityGroups`; requirements point to
`applicabilityGroupKeys`; general AMOC language is in `amocProvisions`.

V3 improved the V2 manufacturer/model flattening problem, but it still repeats
evidence objects (`sourceDocumentId`, `pageNumber`, and `text`) on every group,
equipment condition, requirement, trigger, and AMOC provision. The
administrator edits raw JSON. The 2024-14-03 proposal expands 182 product
labels and repeats the same Garmin installed-equipment condition across five
manufacturer groups.

Materialization also duplicates each requirement for every current
`ADTargetApplicability` row because `ad_compliance_requirements` requires a
single `target_applicability_id`. `ADTargetApplicability` retains copied source
payload, citations, conditions, compatibility actions, and intervals. These
rows are useful projections for existing readers but are not a minimal
authoritative representation.

Aircraft configuration is currently split between columns on `aircraft` and
`installed_components`. It lacks a general explicit-unknown representation,
part-number/STC relationships, complete evidence bindings, and configuration
validity periods expressed by date/time/cycles. `ad_compliance_events` and
`aircraft_ad_due_states` model useful downstream events and calculations, but
do not by themselves preserve the required separation between source record,
machine candidate, reviewed values, signed determination, and customer-facing
assessment.

The review page currently exposes a raw JSON textarea and opens each retained
PDF at its first page. The full Federal Register issue for 2024-14-03 is valid
evidence, but opening a 333-page issue at page 1 rather than the bounded AD
pages makes correct evidence appear unrelated.

## Proposed design

Adopt the candidate detailed in `codex-schema-proposal.md` after independent
design review. Its central decisions are:

1. Keep retained documents and immutable evidence fragments outside the signed
   structured decision. The V4 decision contains a compact evidence-binding
   map from local evidence keys to immutable fragment IDs and hashes.
2. Replace V3 applicability groups with normalized product scopes, reusable
   condition definitions, and applicability rules. One rule may apply a shared
   condition expression to many manufacturer/model scopes. All scope,
   applicability, and branch logic uses a typed recursive T/F/unknown AST with
   normative truth tables, explicit `All`/`Any`/`Not`, evaluator versioning,
   traces, and acyclic references.
3. Store one requirement per signed decision and relate it to applicability
   through one explicit activation-expression FK. Thresholds, alternatives, prerequisites, and
   terminating effects are independently addressable rows.
4. Use strict discriminated known/not-applicable/unknown values where absence
   has safety meaning. Optional omission is permitted only when the schema says
   the concept is structurally inapplicable.
5. Keep service-bulletin references and general AMOC provisions in the
   structured AD domain. Keep actual aircraft-specific AMOC use, logbook work,
   return-to-service evidence, and next-due signoff in the aircraft compliance
   evidence domain. Supporting bulletin and AMOC-use records enter only through
   the authorized immutable-byte/hash/source-attribution workflow and remain
   candidate-only until human verification.
6. Treat existing target/applicability and flattened catalog fields as
   disposable compatibility/search projections during transition. They are
   generated from the current signed decision and never accepted as V4 input.
7. Replace the raw JSON review editor with source-linked forms, menus, product
   tables, a shared-condition library, requirement/timing forms, and explicit
   unknown-reason controls. Raw canonical JSON is downloadable as read-only
   audit/debug output.
8. Introduce additive immutable V4 decision/lifecycle/relationship tables and a
   compare-and-swap operational selection pointer. Freeze all new V3 approvals
   at V4 deployment; existing signed V3 remains read-only transitional
   authority. No directive mixes V3 and V4 rows, and a corrected V4 directive
   can never fall back to V3. V3 translation produces pending proposals only.
9. Persist every three-valued field losslessly using typed value assertions,
   typed temporal/STC/series/identifier/predicate tables, value-level evidence,
   strict CHECK/FK/unique constraints, and canonical JSON round-trip equality.
10. Bind each signoff to immutable membership and aircraft-assignment authority
    snapshots. Provisionally require an independent signer for human-authored
    proposal revisions while the domain owner considers broader dual control.

## Alternatives considered

### Continue refining the V3 JSON

Rejected. It would be the fourth set of semantics forced into structures that
copy evidence into every consumer and materialize requirements per model. The
problem is not cosmetic JSON formatting; it is domain ownership and relational
cardinality.

### Store a top-level evidence-text dictionary inside the V4 decision

Rejected as the authoritative model. It reduces JSON size but still makes the
structured decision a second source repository and complicates correction or
hash verification. V4 stores only immutable fragment references and hashes in
the decision. The review API may join fragment text for display.

### Keep one applicability group per manufacturer and share only citations

Rejected. It removes some source repetition but still repeats identical
installed-equipment predicates and requirement relationships across groups.

### Store only normalized PostgreSQL rows

Rejected. A signed canonical decision envelope is needed for review replay,
hashing, export, correction comparison, and audit. Polymorphic rule structure
also cannot be losslessly reduced to a handful of nullable columns.

### Store only canonical JSON and query it directly

Rejected. Indexed manufacturer/model/role/serial/part queries, graph integrity,
correction scope, and deterministic materialization require relational keys and
foreign-key enforcement.

### Automatically convert and publish existing V3 decisions

Rejected. Deduplication and grouping require semantic judgment. A translator
may produce a candidate, but only a source-comparison review can publish it.

### Treat candidate-only packets as released directives

Rejected. V4 distinguishes `candidate_only` from `released_actionable` and
never exposes candidate-only semantics as released catalog/compliance/due-state
authority. The domain owner permits a reviewed explicit unknown to be retained
candidate-only for administrator and aircraft-specific discovery as
`Uncertain—human determination required`. It cannot establish affirmative
applicability, compliance, terminating-action credit, a next-due value, or
coverage. Missing source identity, retained evidence, minimum applicability,
or minimum obligation data remains remediation-only.

## Trust, authorization, and audit boundaries

- Source ingestion may add immutable retained documents and candidate evidence
  fragments. It cannot publish structured decisions.
- Extraction providers may create V4 proposals and confidence metadata. Model
  confidence is not an approval input and is not materialized as truth.
- A platform administrator may admit a new immutable evidence fragment/version, add a
  lawfully obtained service bulletin, edit structured AD forms, and sign a V4
  publish/reject/remediation decision. Adding a document and approving a
  decision are distinct audit events.
- A maintenance-shop or aircraft administrator may review aircraft-specific
  configuration/evidence discrepancies and sign recurring next-due values
  within an authorized organization. That role cannot alter the global AD
  decision.
- Aircraft owners/users see customer-facing assessments but cannot mutate
  official evidence or global structured AD semantics through assessment UI.
- Evidence fragments are immutable and content-addressed. A correction creates
  a new fragment/version; it never edits the source clause referenced by an old
  signed decision.
- Signed decisions include actor, organization/role, timestamp, schema version,
  canonical content hash, evidence-binding hash, and predecessor/correction
  identity. Audit history is append-only.
- The API re-verifies source bytes and fragment hashes at approval and release.
  Authorization checks are server-side; hiding controls in the GUI is not an
  authorization boundary.

## Read paths and consumers

The implementation review must trace at least:

- admin extraction-review list/detail and retained-document content APIs;
- released AD catalog search and detail;
- aircraft-specific candidate generation and component matching;
- coverage reconciliation and subscription rebuilds;
- requirement and recurring due-state replay;
- AD match evidence/adjudication APIs and worklists;
- source audit, review staging, correction, and remediation scripts;
- data exports, observability, cost attribution, and API documentation;
- all current readers of `ad_target_applicability`,
  `ad_compliance_requirements`, `ad_compliance_triggers`,
  `ad_amoc_provisions`, `ADExtraction.output`, and reviewer decision JSON;
- frontend `api.ts`, AD research, review, and aircraft compliance pages; and
- any tests/fixtures that synthesize `ad_extraction_v3`.

V4 readers select exactly one eligible signed decision version per directive.
They do not union V3 and V4 semantics. Joined review responses may include
fragment text and derived summaries, but those fields are explicitly marked
non-authoritative and cannot be posted back as decision input.

## Write paths and administrative paths

Expected future write paths are:

1. source retention creates an immutable source document;
2. evidence indexing creates immutable fragment rows and document-reference
   identities;
3. provider extraction creates a pending V4 proposal referencing fragments;
4. platform-admin form review creates an append-only signed decision event;
5. one transaction selects the current decision and materializes normalized
   V4 rows plus version-bound disposable projections;
6. candidate matching reads signed AD rows plus versioned aircraft
   configuration facts;
7. aircraft-record extraction creates candidate compliance-evidence claims;
8. authorized aircraft/shop review signs aircraft-specific determinations and
   recurring due values when required; and
9. deterministic assessment calculation writes an input-hashed, stale-aware
   projection.

Correction, service-bulletin addition, STC evidence completion, AMOC
verification, and supersession always append versions and invalidate affected
derived state. Administrative scripts must call the same services and gates as
the API; direct JSON or table mutation is unsupported.

## Migration, compatibility, correction, and rollback

The migration is additive. Existing V1/V2/V3 extraction, review, and derived
rows remain immutable. New V4 tables and a current-decision selector are added
without dropping V3 columns or changing their meaning.

A deterministic V3 translator may deduplicate identical citation tuples into
candidate evidence bindings, identify repeated conditions, create product
scopes, and link requirements. It must ignore `affectedProducts`,
`complianceActions`, and `complianceIntervals` as authoritative inputs. Every
translated packet is `pending_review`; provenance records source V3 decision
and translator version. No translated value is released automatically.

At V4 deployment, new V3 approval/correction freezes. During transition, a
directive uses either its selected signed V4 decision or its already signed,
read-only V3 decision. V4 selection uses immutable lifecycle and relationship
events plus a generation-CAS pointer in the same serializable transaction that
validates a complete projection. Correction creates a new V4 version and
explicit correction/invalidation edges; prior versions remain immutable.

Application rollback disables V4 writes. A directive ever corrected or
superseded by selected V4 can never fall back to V3 and is quarantined if a V4
reader is unavailable. An untouched directive may retain only its already
selected, source-verified V3 predecessor; no new V3 decision is allowed.
Database downgrade does
not delete V4 regulatory/audit rows; destructive downgrade is prohibited once
V4 data exists. Operational rollback uses application rollback plus verified
backup/restore if schema removal is required.

## Test strategy

### Contract and schema tests

- strict object schemas, no unknown properties, no JSON `null` in canonical V4;
- known/not-applicable/unknown discriminators and required unknown reasons;
- unique key namespaces and complete cross-reference resolution;
- evidence fragment/document hashes and exact locator validation;
- no derived-summary fields accepted in canonical input;
- no orphan scope, condition, rule, requirement, branch, document, or evidence
  references;
- full T/F/unknown AST truth-table and predicate tests;
- canonical JSON -> constrained rows -> identical canonical JSON/hash;
- database-negative CHECK/FK/unique, evidence-minimum, graph-cycle, temporal,
  identifier, series, and STC tests.

### Calibration tests

- 2024-14-03 broad manufacturer/model table: one shared installed-equipment
  condition, five manufacturer scopes, no repeated evidence text, and exact
  relevant PDF page navigation;
- listed serial/part ranges with inclusions and exclusions;
- engine, propeller, appliance, installed-part, and STC applicability;
- one-time plus recurring multi-metric timing, whichever-first/later logic;
- conditional/alternative obligations, terminating action, and installation
  prohibition;
- referenced-but-absent and retained-but-unverified service-bulletin paths,
  authorized immutable retention/review, and candidate-only enforcement;
- general AMOC provision versus **possible AMOC—unverified**, including no
  compliance/timing/termination credit before human verification;
- correction and supersession with stale-state invalidation.

Each positive calibration has negative aircraft/component cases and an expected
`applicable`, `not_applicable`, or `human_determination_required` result. No test
uses a flattened label parser.

The initial five-packet gate does not require retained service-bulletin bytes or
an actual aircraft-specific approved AMOC-use record. It requires source-
complete AD semantics plus deterministic structural tests of authorized
ingestion, immutable bytes/hash/source attribution, human verification,
candidate-only/fail-closed absence and unverified states, and unchanged-signed-
input replay. Future lawfully obtained real examples are added as regression
fixtures.

### Persistence, authorization, and rollback tests

- one requirement row remains one row regardless of model count;
- shared fragments/conditions are not duplicated by materialization;
- concurrent reviews serialize and only one signed version becomes current;
- failure injection at event/projection/CAS/outbox/replay boundaries preserves
  one complete selected generation and idempotent recovery;
- non-platform administrators cannot publish global decisions or add official
  documents;
- aircraft/shop administrators cannot edit global V4 semantics;
- signoffs preserve exact membership/assignment/policy snapshots and reject
  inactive, wrong-scope, stale-role, and prohibited self-review submissions;
- V3 translation never publishes, V3 remains byte-identical, and mixed-version
  reads are rejected;
- correction/rollback never resurrects invalidated data;
- changing any signed input stales affected assessments and recurring due
  signoff; unchanged deterministic replay is idempotent.

Verification reporting must use `x passed out of x` and identify skipped or
unexecuted classes separately.

## Expected file scope

This design-only slice changes:

- `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md`
- `.ai/review-runs/T081-V4-SCHEMA/decision.md`
- `.ai/review-runs/T081-V4-SCHEMA/codex-schema-proposal.md`
- `.ai/review-runs/T081-V4-SCHEMA/calibration/*.md`
- `scripts/build-review-packet.py`
- `scripts/verify-review-packet.py`

No application code, migrations, tests, calibration JSON, API contract, or
existing T081 artifacts are in scope before the independent design review
passes.

## Recorded decisions and residual calibration gaps

The design records candidate-only exposure, separate governed identity
normalization, typed non-calendar observations, access-controlled service
bulletins, one independent authorized signer, a platform-wide V3 approval
freeze at V4 deployment, quarantine rather than V3 fallback after V4
correction, and a versioned database authority for customer-facing assessment
codes.

The retained shortlist does not contain an actual aircraft-specific approved
AMOC use or a retained incorporated service bulletin. Under domain contract
1.1, these are administrator-ingested supporting-evidence types rather than
required initial AD packet artifacts. Initial calibration must prove their
absent/unverified fail-closed behavior and complete structural admin workflow;
it must not claim positive real-artifact coverage. A real retained and reviewed
example becomes a regression fixture when available.
