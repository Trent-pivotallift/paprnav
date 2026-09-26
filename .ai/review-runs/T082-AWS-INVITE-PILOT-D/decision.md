# Decision packet: T082-AWS-INVITE-PILOT-D

## Objective

Implement the approved Package D learning loop for the invite-only AWS pilot:
six server-owned achievements, sanitized correlation/error evidence, and a
platform-admin operational/cost summary. Reuse the committed `ProductEvent`,
workflow/feedback, `OCRRun`, and AWS Budget structures; add no migration and do
not enable a paid worker or AWS service.

## User-visible outcome

- Invited users see their authorized workflow and feedback evidence without
  cross-tenant disclosure.
- A platform administrator sees versioned achievement counts/recent records,
  bounded workflow failures/feedback, and OCR usage/cost split into priced,
  unpriced, attributed, unattributed, failed, and reconciliation-required
  categories.
- Every HTTP response has a safe correlation ID that can link a user report to
  sanitized server logs without exposing request bodies, OCR text, files,
  passwords, tokens, invitations, cookies, or maintenance prose.
- Terraform continues to require a real budget subscriber before external
  execution; no provider call, customer charge, or cost allocation is enabled.

## Safety and correctness invariants

1. The only version-1 achievements are `invite_accepted`, `aircraft_created`,
   `upload_received`, `page_review_completed`, `logbook_entry_created`, and
   `ad_review_completed`, each with taxonomy `pilot-achievement-v1`.
2. Achievement actor, organization, aircraft, subject type, and subject ID are
   server-derived and written in the same transaction as the defined success
   point. Failed requests and client assertions cannot create success.
3. Reports deduplicate by `(taxonomyVersion, eventType, subjectType, subjectId)`
   without rewriting or deleting existing event rows.
4. Event properties use a fixed allowlist per achievement. Free text, filenames,
   OCR/logbook content, invitation/auth material, and arbitrary client metadata
   never enter achievement properties or error logs.
5. Incoming correlation IDs are accepted only under a fixed ASCII format and
   length; otherwise a new opaque ID is generated. The value is returned in a
   response header and attached to sanitized logs/server events only.
6. Unexpected exceptions log route template, method, status, release,
   correlation ID, and authenticated server-derived identifiers when available,
   but never headers, cookies, query strings, request/response bodies, exception
   messages, or stack-local values. The client receives a generic error plus
   correlation ID. Database failure remains diagnosable without a DB insert.
7. Ordinary observability remains actor/current-aircraft scoped. Cross-tenant
   achievement, failure, feedback, or cost summaries require a fresh active
   `platform_admin` membership.
8. OCR summaries are explicitly **recorded-run projections**, not complete
   paid-attempt inventories. They never convert a missing row, price, amount, or
   attribution to zero. Known partial estimates remain distinct from unknown
   amounts; lifecycle status, pricing status, historical billing attribution,
   and billing classification are independent dimensions. Completed priced
   totals remain distinct from failed, pending, reconciliation-required,
   unpriced, and unattributed recorded runs. Historical billing tags are not
   reassigned to a current owner. Shared AD/AWS costs remain separate from
   user-variable OCR estimates. Coverage/reconciliation completeness remains
   unavailable until Package E's durable pre-call attempt protocol exists.
9. Package D does not invoke Textract, retry a provider request, enable the
   worker, mutate AWS, or claim actual invoice/customer billing accuracy.
10. The existing budget resource requires a real subscriber in external mode;
    Package D reports that execution prerequisite rather than fabricating an AWS
    budget status from local data.

## Current behavior

Package B already provides tenant-scoped and administrator observability reads,
feedback authorization, and invite acceptance. Several workflow endpoints
write `ProductEvent` rows, but names/properties are inconsistent with the six
approved achievements and no canonical funnel projection exists. The app has no
request-correlation/error middleware. The administrator OCR billing endpoint
reports completed runs and an excluded count, which hides why runs were
excluded and does not present unknown price/attribution as first-class pilot
evidence. Terraform now blocks placeholder budget recipients but AWS budget
state is unavailable until Package E.

## Proposed design

- Add one declarative achievement specification/service containing the six
  event names, success subject types, fixed property keys, taxonomy version,
  recorder, and deduplicating projection. Existing noncanonical events remain
  readable. Where an endpoint already writes the canonical name, route it
  through the helper; otherwise retain legacy evidence only when a known
  consumer requires it and add the canonical event in the same transaction.
- Instrument the exact parent-approved success points: invite commit, aircraft
  with cost identifiers, consented upload plus ingestion job, first complete
  order/completeness page verification, each manual/extracted entry creation,
  and human AD extraction/match decision. The extracted-entry service owns the
  transaction: it receives an explicit authenticated actor for pilot HTTP work,
  writes one canonical event for each newly created entry before its commit,
  and writes none when returning existing entries on retry. The non-HTTP
  feasibility caller supplies no pilot actor and preserves its existing commit
  behavior without minting achievement evidence.
- Add correlation/error middleware with a context-local correlation value,
  strict input validation, response header, structured JSON logger payload,
  and generic 500 response. Do not log exception text or request content.
- Add one platform-admin `pilot-summary` endpoint and response schema. It
  returns bounded canonical achievement counts/recent rows, bounded workflow
  failure/feedback summaries, and an OCR cost/exposure projection using
  server-owned joins from `OCRRun` through ingestion/upload/aircraft/
  organization/user. The projection is labeled `recordedRunsOnly=true` and
  `paidAttemptCoverageComplete=false`; it exposes missing-row/ambiguous-attempt
  completeness as unavailable rather than deriving it from `OCRRun`. Filters
  are bounded server inputs and never authorize.
- Canonical event identity is `(taxonomyVersion, eventType, subjectType,
  subjectId)`. The projection first selects the deterministic earliest
  `(event_time, id)` successful row for every identity, then applies date/actor
  grouping and recent-row limits. Aggregate identity counts are computed before
  and independently of display limits.
- Extend the administrator observability page with compact achievement,
  failure, and OCR cost cards; ordinary users keep their existing scoped view.
- Retain the existing AWS Budget resource and blocking subscriber input.
  Package D may expose `budgetConfigured=true` only from reviewed configuration,
  not live spend. Live alert subscription/aggregate spend proof remains
  Package E.
- Add one small retained oracle for the taxonomy/success-point mapping,
  duplicate projection, sanitization/correlation negatives, tenant/admin
  authorization, priced/unpriced/attributed/unattributed/failed/reconciliation
  summaries, and the budget plan gate.

## Alternatives considered

- External analytics/error SaaS: deferred; it adds a data processor and export
  boundary before pilot learning justifies it.
- A new achievement/cost schema: rejected because committed event and OCR rows
  can represent the MVP without colliding with unreviewed migration 0030.
- Store every exception in PostgreSQL: rejected because database failure is a
  primary case and sensitive exception text is hard to sanitize reliably.
- Implement/enable paid Textract idempotency now: deferred to Package E's
  separately reviewed provider/worker activation gate; Package D reports
  existing attempts and unknown exposure without making new calls.
- Treat excluded OCR runs as zero cost: rejected because it hides risk and
  produces misleading pilot economics.

## Trust, authorization, and audit boundaries

FastAPI authorization and server-owned joins define user/admin scope.
PostgreSQL owns achievements, workflow failures, feedback, and OCR attribution;
CloudWatch structured logs own unexpected runtime errors; AWS Budget owns
aggregate alerting after deployment. Product events are learning/audit evidence,
not authorization or invoices. Platform-admin membership is checked on each
admin request and cannot be inferred from event properties.

## Read paths and consumers

- Ordinary `/api/v1/observability` and the existing observability page.
- New platform-admin pilot summary and administrator page cards.
- Operator CloudWatch correlation search and Package E acceptance evidence.
- Existing OCR billing/admin consumers remain compatible or are explicitly
  adapted to the richer projection.

## Write paths and administrative paths

- Existing invite, aircraft, upload, page verification, manual-entry, and AD
  decision transactions write canonical achievement events. Extracted-entry
  events are written inside `app.services.ingestion.extract_entries_from_job`
  before its existing commit, only for entries created during that invocation,
  with an explicit authenticated actor supplied by the HTTP caller. The
  feasibility caller remains actorless and produces no pilot achievement.
- Correlation/error middleware writes only structured application logs.
- Feedback status remains platform-admin-only under Package B.
- No migration, AWS API write, provider call, worker activation, customer
  charge, or automated reconciliation action is introduced.

## Migration, compatibility, correction, and rollback

No database migration or data rewrite is permitted. Existing event types remain
readable; only canonical version-1 events count. Duplicate legacy/retry rows are
deduplicated in projection. Rollback removes the new projection/UI and helper
wiring while leaving append-only evidence rows readable. Any need for a unique
constraint or durable paid-attempt state stops for a separate reviewed schema
decision rather than consuming 0030.

## Test strategy

- One transaction-oriented success/failure case per achievement, plus duplicate
  report rows proving one identity count.
- Direct sanitization cases for nested secrets, tokens, invitation values, raw
  text, filenames, oversized strings/lists, and unexpected exception text.
- Valid/invalid incoming correlation IDs, generated IDs, response propagation,
  generic 500 behavior, DB-outage log path, and no sensitive log fields.
- Two unrelated tenants plus platform admin for summary/event/failure/cost
  reads; revoked access immediately fails closed.
- OCR cases covering provider/mode, billable units/rate/estimate, billing
  status, priced/unpriced, attributed/unattributed, failed/pending/
  reconciliation-required, historical tag/current-owner disagreement, known
  partial estimate versus unknown amount, explicit recorded-run incompleteness,
  and no missing-row/unknown-to-zero conversion.
- Existing Terraform mock gate proves external mode rejects a placeholder/missing
  budget subscriber. No live AWS budget query is claimed.
- Focused backend/frontend tests only; no T081 oracle, broad repository suite,
  paid provider call, or image rebuild unless a changed dependency requires it.

## Expected file scope

- Backend correlation/error middleware and configuration-safe logging helper.
- Achievement specification/service plus exact existing route/service success
  points.
- `backend/app/services/ingestion.py`, its HTTP caller, and
  `backend/app/scripts/run_ocr_feasibility.py` for extracted-entry transaction
  and actor semantics.
- Administrator pilot summary schemas/service/route and focused tests.
- Existing OCR billing projection only where needed for explicit unknown and
  failure categories.
- Frontend API types/client and observability administrator cards/tests.
- Package D review artifacts.

Explicitly excluded: migrations/models, T081/0030, paid-provider protocol,
worker activation, customer billing, live AWS queries, unrelated UI cleanup,
and Package E deployment/runbook execution.

## Known uncertainty

Both AD human-decision consumers must be traced before wiring to avoid duplicate
or premature achievements. Existing `OCRRun` rows are known to be incomplete
for pre-commit crashes and lack future Textract idempotency fields; D reports
only recorded evidence, labels completeness unavailable, and leaves activation
disabled. CloudWatch log ingestion/redaction and real Budget notification are
Package E evidence.

## Model routing

- Coordinator/designer: `/root`; actual model and effort are not exposed by
  runtime.
- Inherited authority: independently approved parent T082 design.
- Required inheritance reviewer: `/root/t082_pilot_design_adversary`, requested
  GPT-6 Astra high.
- Planned builder after approval: GPT-5.6 Sol high.
- Planned implementation reviewer: GPT-6 Astra high at the complete telemetry/
  cost family boundary.
