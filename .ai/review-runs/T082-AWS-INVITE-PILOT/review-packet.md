# Review packet: T082-AWS-INVITE-PILOT

Stage: implementation
Generated: 2026-09-19T16:51:09+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `90dfb6565e1cf4c2fddc249b2956f8f069b5c02e14eaa8350dd5cb217611f48d`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: T082-AWS-INVITE-PILOT

## Objective

Launch a deliberately bounded, invite-only paprnav pilot on AWS so a small
external cohort can exercise the existing aircraft/logbook/OCR/AD
decision-support workflow while the operator can observe failures, successful
milestones, and attributable cost. This run optimizes time to validated product
learning while retaining minimum external-user security, privacy, durability,
and cost controls.

This run does not close, weaken, or absorb `T081-V4-SCHEMA-SLICE-4B`. Its open
findings and uncommitted working tree remain intact. The pilot release excludes
the unreviewed 0030 candidate-acceptance migration and keeps every unfinished V4
write/read/review feature gate disabled.

Pilot scale is at most ten invited users/aircraft in one AWS `pilot`
environment. Paprnav remains decision support and must not claim official
airworthiness or regulatory compliance.

## User-visible outcome

- An operator can generate a short-lived invitation for a named email and an
  allowed pilot role without enabling public account creation.
- An invitee can accept the invitation, set a password, sign in over HTTPS,
  create or access only authorized aircraft, upload a logbook, review OCR,
  create structured entries, and view conservative AD decision-support output.
- A user can submit feedback with a request/workflow reference without exposing
  another tenant's events or feedback.
- The operator can see sanitized operational errors, the agreed product
  milestones, OCR/provider usage, estimated variable cost, and aggregate AWS
  budget state.
- Deployment, migration, rollback, and data recovery have a short operator
  runbook and one bounded acceptance packet.

## Safety and correctness invariants

1. **Invite-only identity.** In `pilot`, public self-registration is unavailable.
   Only a valid, unexpired, correctly signed invitation may create a user and
   membership. Invitation payloads cannot grant `platform_admin`; replay cannot
   create a second user or additional membership.
2. **Tenant isolation.** A non-platform user may read events, workflows,
   feedback, uploads, entries, and aircraft only when the existing membership
   and aircraft visibility rules authorize them. Client-provided `userId`,
   `organizationId`, `aircraftId`, or subject identifiers never widen access.
3. **Administrative authority.** Cross-tenant pilot reporting, invitation
   generation, feedback disposition, and cost summaries require a fresh active
   `platform_admin` membership. A separately audited deployment role may only
   bootstrap the first platform administrator on an empty deployment and may
   not generate user invitations; possession of an ordinary application
   session is insufficient.
4. **HTTPS session boundary.** External browser traffic is HTTPS only. Pilot
   session cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`; secrets and
   invitation codes never enter logs, product-event properties, URLs, browser
   history, referrers, or client analytics. Unsafe cookie-authenticated methods
   reject absent or unapproved Origin/Referer context in pilot.
5. **Closed regulatory boundary.** A pilot-wide V4 route gate is false and all
   unfinished V4 service gates are false in `pilot`; startup fails closed if
   configuration attempts to enable any of them. Candidate-only or unreviewed data cannot become a pilot-facing
   compliance statement. Existing AD output retains degraded-coverage and
   needs-review states and is labelled decision support.
6. **Error evidence without source-data leakage.** Each request has a correlation
   ID. Expected workflow failures persist bounded codes/status on their owning
   record; unexpected failures produce structured CloudWatch logs containing
   route, status, release, and authorized actor/account identifiers, but no
   passwords, tokens, file bytes, raw logbook text, OCR text, or free-form
   maintenance content.
7. **Meaningful achievements.** The first taxonomy is versioned and limited to
   `invite_accepted`, `aircraft_created`, `upload_received`,
   `page_review_completed`, `logbook_entry_created`, and
   `ad_review_completed`. Events bind to the authenticated actor and server-owned
   organization/aircraft/workflow identifiers. Client requests cannot assert
   successful completion of a server workflow.
8. **Cost attribution.** Every paid OCR invocation records provider/mode,
   billable units, configured unit rate, estimated USD, billing status,
   organization/account, aircraft, upload/job, and the initiating user through
   the owning ingestion job. Unknown price or attribution remains visibly
   unknown; it is never converted to zero-cost or allocated customer charges.
   Shared AWS spend remains separate from per-user variable cost.
9. **Bounded spend.** A real budget notification recipient is configured before
   paid OCR or invited-user traffic. Expensive workers are disabled until their
   image, secret, provider mode, per-page ceiling, durable idempotent attempt,
   single-claim behavior, ambiguous-outcome reconciliation, and operator
   enablement are verified. No customer billing or automated charging occurs
   in this run.
10. **Durable, recoverable data.** RDS is private and encrypted with automated
    backups; uploaded source files use the existing encrypted/versioned S3
    bucket. A restore check proves the operator can recover pilot records. No
    destroy path may silently remove volunteer data.
11. **Least privilege by function.** Runtime API/worker credentials do not use
    the RDS master identity or migration authority. A one-off migration/bootstrap
    task has separately scoped secret access and no public listener. ECS tasks
    accept inbound traffic only from the ALB security group.
12. **Reproducible release and rollback.** ECS task definitions use an immutable
    release tag or digest, migrations are completed before service counts rise,
    and rollback identifies the prior image plus schema compatibility. `latest`
    is not release evidence.
13. **Preserved review history.** No T081 file, finding, review result, or
    untracked implementation artifact is deleted, rewritten, staged, committed,
    or represented as pilot closure. The pilot release manifest explicitly
    excludes the unreviewed 0030 artifacts.
14. **Cloud mutation gate.** Terraform apply, image push, secret population,
    DNS/certificate changes, migrations against AWS, and service-count changes
    require an approved reviewed plan and explicit execution authorization.
15. **Fresh-database operability.** A committed, idempotent pilot bootstrap
    creates required non-secret reference rows, including the airframe, engine,
    and propeller logbook sections, without running `seed_dev.py` or creating
    demo users/passwords. Manual and OCR-derived entry creation work on a fresh
    migrated/bootstrap database.

## Current behavior

- The local application already supplies API-backed auth, organizations,
  aircraft, maintenance assignments, logbook CRUD, upload/download, OCR review,
  structured extraction, AD ingestion/matching/HITL review, product events,
  feedback, and admin cost summaries.
- The repository contains 479 backend test functions and a frontend smoke
  script, but this run has not yet established a clean pilot-baseline result.
- Public `/api/v1/auth/register` is enabled and immediately creates an active
  user. The browser session cookie is currently written with `secure=False`.
- The observability list begins with global product-event, workflow-event, and
  feedback queries; an authenticated caller may supply an arbitrary `user_id`.
  Feedback status updates require aircraft visibility only when the feedback
  has an aircraft, rather than requiring platform administration.
- Product-event values are sanitized and ingestion jobs/OCR runs already retain
  useful error, actor, provider, unit, pricing, and attribution data.
- The applied AWS foundation contains S3, remote Terraform state, ECR
  repositories, an ECS cluster, CloudWatch log groups, and a budget. The runtime
  VPC/ALB/RDS/ECS skeleton is checked in and was previously validated/planned,
  but it is not applied; ECR is empty, frontend has no Dockerfile, secrets are
  placeholders, services are at zero, and the ALB is HTTP-only.
- The runtime task definitions reference `:latest`, run API/worker with one
  application database secret, and do not define the separate migration
  authority required by this design.
- The active T081 4B run has open PostgreSQL/RDS/ACL/oracle findings. The
  unfinished 0030 artifacts are untracked or modified and are not pilot inputs.

## Proposed design

### 0. Release boundary and feature exposure

- Define one pilot release manifest at a reviewed Git commit. The manifest lists
  included Alembic head, image digests, enabled routes/providers, expected
  environment variables, and explicitly excluded T081/0030 artifacts.
- Add one route-family gate that makes every `/api/v1/ads/**/v4/**` operation
  unavailable in `pilot`, including the committed validator-v1 candidate route
  which currently has no application feature gate. Keep all existing V4
  service defaults false. Add a pilot startup assertion that rejects an enabled
  V4 route, write, projection, review, or acceptance gate. The established non-V4 AD worklist remains available with decision-
  support language and existing uncertainty/degraded states.
- Do not copy, reset, or delete the dirty T081 working tree. Implementation must
  either avoid overlapping files or isolate pilot release construction after a
  reviewed handoff; no commit may accidentally include T081 artifacts.

### 1. Invite-only access and tenant-safe telemetry

- Retain the application session model for this pilot; do not migrate to a new
  identity provider in the critical path.
- Use a stateless, HMAC-SHA256 signed invitation with a dedicated Secrets
  Manager signing secret. Its canonical versioned payload contains a random
  nonce, normalized email, display name, organization name/type, allowed role,
  issued-at, and expiry. Allowed mappings are exactly `owner_admin` in an
  `owner` organization and `maintenance_admin` in a `maintenance_shop`
  organization; every other role/type pair, including `platform_admin`, is
  rejected by both signing and acceptance.
- An authenticated platform-admin endpoint generates a bearer invitation code;
  it signs server-side so the operator never reads the signing secret. The
  response is `no-store`, bounded, and not copied into product-event properties.
  No mail provider is required initially; the operator delivers the code out of
  band and the user pastes it into a fixed invitation page whose URL contains no
  credential. Codes have a maximum 24-hour lifetime, canonical UTC timestamps,
  one normalization version, and at most five minutes of clock-skew tolerance.
  Acceptance verifies signature and expiry, creates user,
  organization, and membership atomically, records `invite_accepted`, and fails
  generically if the email already exists. Email uniqueness makes successful
  acceptance non-replayable. Revocation before expiry is by rotating the
  dedicated invite secret; per-invite revocation is a documented pilot
  limitation.
- Local/test environments may retain self-registration. `pilot` returns a
  non-enumerating not-found/disabled response from public registration, hides
  the registration link, and exposes an invitation-acceptance page instead.
- Pilot cookies derive `Secure` from an explicit setting which must be true at
  startup in `pilot`. Login and invite endpoints receive bounded AWS WAF
  rate-based protection; failure responses do not disclose whether an email is
  registered or invited. Pilot CORS uses an exact HTTPS origin, and unsafe
  cookie-authenticated requests require an exact allowed Origin (or a same-origin
  Referer fallback where browser behavior requires it); wildcard origins and
  cross-origin credentialed mutations are rejected.
- The browser calls the ALB's same-origin `/api/v1/*` route directly in pilot.
  The Next `/api/backend/*` development proxy is disabled in pilot and tests
  prove it cannot forward cookies or mutations there. Local development may
  retain the proxy. This gives WAF, CSRF/origin enforcement, correlation IDs,
  route metrics, and authorization one public API path.
- Ordinary observability reads are restricted to the current actor plus records
  attached to aircraft currently visible to that actor; they cannot accept a
  widening `user_id`. Actor ownership never preserves access to an
  aircraft-bound event or feedback row after membership/assignment revocation.
  Actor-only fallback applies only to personal rows with no organization or
  aircraft. Generic workflow events are admin-only unless a server-side join
  resolves the referenced workflow to a currently visible aircraft. A distinct
  platform-admin endpoint provides bounded cross-tenant operational reporting.
  Only platform admins may change feedback status.

### 2. Pilot instrumentation

- Add request-correlation middleware. Honor an incoming correlation ID only
  after format/length validation; otherwise generate one. Return it in the
  response and include it in sanitized structured logs and server-originated
  product/workflow events.
- Record the six server-owned achievement events named in invariant 7. Reuse
  `ProductEvent`; add a shared constant/validation module and query/reporting
  projection rather than a new analytics schema. Existing event types remain
  valid but do not count toward the pilot funnel unless mapped explicitly.
- Version-1 achievement success and identity are closed as follows:

  | Event | Success point | Subject and report deduplication key |
  | --- | --- | --- |
  | `invite_accepted` | user, organization, membership, session, and event commit atomically | `user:<new-user-id>` |
  | `aircraft_created` | aircraft and its server-derived owner/cost identifiers commit | `aircraft:<aircraft-id>` |
  | `upload_received` | consented upload plus ingestion job commit | `upload:<upload-id>` |
  | `page_review_completed` | first commit where OCR is complete and the latest page verification confirms both order and completeness; it does not claim all low-confidence corrections are complete | `ingestion_job:<job-id>` |
  | `logbook_entry_created` | manual or extracted entry plus its owning aircraft and evidence links commit | `logbook_entry:<entry-id>` |
  | `ad_review_completed` | a human extraction-review decision or aircraft-match adjudication commits | `ad_extraction_review:<review-id>` or `ad_match_adjudication:<adjudication-id>` |

  Every event has taxonomy version `pilot-achievement-v1`, server-derived actor,
  organization, aircraft, subject type, and subject ID and is written in the
  same transaction as its success point. The reporting identity is
  `(taxonomy-version, event-type, subject-type, subject-id)` and counts each
  identity once even if legacy/retry behavior produced duplicate rows. A status
  field, client assertion, or frontend navigation alone is never success.
- CloudWatch is the source for unexpected runtime exceptions and ECS health;
  PostgreSQL is the source for workflow failures, feedback, achievements, and
  per-operation attribution. A database outage therefore remains diagnosable
  from logs rather than relying on an error insert into the failed database.
- Platform-admin reporting returns counts and bounded recent records, not raw
  documents or OCR text. Existing property sanitization remains defense in
  depth and gains direct tests for invitation, authorization, and exception
  fields.

### 3. Cost recording and controls

- Reuse `OCRRun` as the per-invocation source of truth and join through
  `IngestionJob.created_by_user_id`, upload, aircraft, and organization. Report
  unattributed, unpriced, failed, and reconciliation-required runs explicitly by
  user/account/aircraft/provider; completed-only billing totals remain a
  separate view.
- Reuse `ADCostLedgerEntry` for AD/shared-source work. Do not mix estimated OCR
  chargeback, actual provider invoices, and shared infrastructure allocation.
- Configure the existing AWS Budget with a real subscriber. Use project and
  environment resource tags for aggregate AWS reporting. Cost Explorer/CUR
  reconciliation is an operator cadence after launch and is not required to
  block the first invite, provided budget alerts and app-side paid-operation
  attribution are active.
- Set a conservative per-upload page ceiling and keep paid Textract opt-in until
  its async S3 mode, rate, timeout, and attempt protocol are verified.
  Deterministic OCR remains available for the infrastructure smoke path.
- Before a paid provider call, acquire a per-job PostgreSQL claim/advisory lock
  and commit one `OCRRun` intent containing a stable provider idempotency token,
  upload hash, provider/config identity, page ceiling, initiator, and attribution
  metadata. The intent freezes the complete Start request, including API mode,
  feature types, exact S3 bucket/key/version for either the original or derived
  routed object, object/content hash, and every parameter that affects AWS's
  idempotency comparison. Textract async Start uses a token derived from that
  immutable intent. Persist and commit the returned JobId before polling; after
  a crash, resume/poll that JobId or repeat Start with the identical token and
  parameters only within six days of intent creation. This deadline is
  deliberately inside Textract's seven-day idempotency and result-retention
  windows. Store intent/JobId in the existing bounded metadata JSON for this
  pilot unless review proves a schema column is required.
- `failed` or timed-out paid attempts are not automatically resubmitted. An
  unknown Start/poll outcome becomes `reconciliation_required`, retains its
  estimated maximum exposure, and requires an operator reconciliation action.
  Any recovery at/after the six-day deadline, or with unknown intent age or
  parameters, remains `reconciliation_required` and never calls Start. A
  missing JobId within the window may repeat only the identical frozen Start
  after operator reconciliation. A later new paid attempt requires an explicit
  operator disposition linking it to the old attempt and retaining both cost
  exposures.
  The worker claims one queued job transactionally and cannot overlap a second
  worker for the same job. A definite pre-provider validation failure may be
  retried without billable-attempt semantics.

### 4. Deployable AWS runtime

- Build API and frontend images from the reviewed release commit and push an
  immutable release tag/digest to the existing repositories. Add a multi-stage
  frontend Dockerfile whose build receives the public same-origin API base.
- Retain the cost-controlled public-subnet Fargate design for the first pilot:
  the public ALB is the only inbound source to task security groups; RDS remains
  private. Record public task IPs as a pilot-only outbound-cost compromise.
- Add ACM HTTPS with HTTP redirect and a user-owned DNS name. No external invite
  is sent until certificate and browser-cookie behavior are verified.
- Separate database identities:
  - RDS-managed `paprnav_admin` is bootstrap/migration authority;
  - a one-off ECS migration task can read only the RDS admin secret and execute
    the reviewed committed migration head;
  - API/worker read only an application `DATABASE_URL` secret for a
    `paprnav_app` login with runtime DML privileges and no schema/role authority.
  The bootstrap procedure creates/grants the runtime role and writes the app
  secret without exposing values in Terraform output or logs.
- The same one-off bootstrap authority creates the first platform organization,
  user, and active `platform_admin` membership only when no active platform
  administrator exists. Email/name are explicit inputs and the password is
  interactively supplied or read from a one-use secret; no demo identity or
  fixed password is allowed. Subsequent platform-admin creation follows a
  reviewed admin path, not `seed_dev.py`.
- A separate idempotent reference-data step creates the canonical `airframe`,
  `engine`, and `propeller` logbook sections with reviewed display/sort values.
  It creates no user, organization, aircraft, or sample record. The migration
  task runs schema migration, reference-data bootstrap, runtime grants, and
  first-admin bootstrap as explicit individually logged phases; rerunning the
  reference phase is safe, while first-admin bootstrap fails closed once an
  active platform administrator exists.
- Existing sessions are opaque random bearer tokens whose hashes live in
  PostgreSQL; `PAPRNAV_SESSION_SECRET` is currently unused and is removed from
  the pilot task/secret contract rather than treated as a revocation control.
  Add an audited operator command to revoke all sessions or all sessions for one
  user in the database. Invite-secret rotation affects only outstanding invite
  codes.
- Resolve service-linked-role and `rds!db-*` permission preflight before apply.
  Apply network/RDS/runtime definitions with service desired counts at zero,
  run bootstrap/migrations, then raise API/frontend counts. Enable the worker
  only after its provider and cost gate pass.
- Replace `:latest` references with variables bound to reviewed immutable image
  identifiers. Document health checks, prior-task rollback, migration
  compatibility, secret rotation, and RDS restore.

### 5. Review and release cadence

| Package | Dependencies | Risk / complexity / centrality / uncertainty (1-5) | Builder | Independent review boundary | Exit evidence |
| --- | --- | --- | --- | --- | --- |
| A. Release boundary and route gates | approved design | 5 / 2 / 5 / 2 | Sol high | Astra high after complete gate family | all V4 HTTP methods return unavailable in pilot; startup fails for every V4 enablement; release manifest excludes 0030 |
| B. Invite and tenant isolation | A | 5 / 4 / 5 / 3 | Sol high | Astra xhigh after invite + observability family | token negative matrix, role/tenant matrix, secure-cookie proof, WAF plan |
| C. Images, RDS identities, migration path, HTTPS | A, reviewed IAM preflight | 5 / 4 / 5 / 4 | Sol high for coherent implementation; Terra/Sol medium for mechanical generated artifacts | Astra xhigh after complete infrastructure family | validate/plan, policy simulation/live read-only preflight, clean RDS migration, image builds, no cloud mutation yet |
| D. Achievements, errors, and cost view | B; existing event/cost models | 3 / 3 / 4 / 2 | Sol high | Astra high once for complete telemetry/cost family | sanitization negatives, milestone oracle, attribution/unpriced cases, budget plan |
| E. AWS execution and pilot acceptance | B-D, explicit apply authorization, DNS and alert recipient | 5 / 3 / 5 / 3 | coordinator/operator with reviewed runbook | Astra xhigh closure after deployment evidence | HTTPS smoke, tenant isolation, one bounded OCR flow, logs/events/cost, backup/restore, rollback |

Mechanical artifacts, hashes, container builds, and Terraform plan changes are
verified deterministically and included in their family packet; they do not
receive standalone reviewer turns. Expected remaining cadence after design is
four coherent builder passes, four family reviews, and one closure review,
with remediation only for substantive findings.

## Alternatives considered

1. **Continue T081 until every V4 invariant closes before deploying.** Rejected
   for the pilot: it delays product learning and solves a stronger publication
   problem than this non-attestation cohort requires. T081 remains valid future
   hardening work.
2. **Deploy the current tree unchanged.** Rejected: public registration,
   insecure cookies, global observability queries, HTTP-only ingress, empty
   images, and unapplied runtime resources make it neither deployable nor safe
   for unrelated external users.
3. **Adopt Cognito before the pilot.** Deferred. Managed invitations, recovery,
   and MFA are valuable, but replacing the established app session boundary
   adds migration and authorization risk before product learning. Reassess after
   the first cohort.
4. **Store invitation rows in a new database table.** Deferred because the
   active dirty tree already contains an unreviewed 0030 migration and the
   pilot needs only a small cohort. Short-lived signed, role-restricted tokens
   avoid migration collision. Persistent revocation and resend history become
   a post-pilot identity story.
5. **Use public registration plus an email allowlist.** Rejected because email
   ownership is not verified and an attacker who knows an invited address could
   claim it first.
6. **Use the RDS master credential in API and worker tasks.** Rejected because
   an application compromise would gain schema/role authority and because it
   conflates runtime, migration, and candidate-acceptance concerns.
7. **Add a full analytics/error SaaS immediately.** Deferred. Structured
   CloudWatch logs plus existing PostgreSQL events/feedback answer the initial
   learning questions without adding a new processor or data export boundary.
8. **Private Fargate plus NAT gateways.** Deferred for pilot cost. Public task
   IPs with ALB-only inbound security groups retain a smaller fixed-cost shape;
   revisit after measured traffic and risk.

## Trust, authorization, and audit boundaries

- Browser users trust the HTTPS frontend/API origin and hold only an opaque
  session cookie. Invitation codes are short-lived bearer credentials and are
  not sessions after acceptance.
- FastAPI is the authorization boundary for user, organization, aircraft,
  observability, feedback, and admin operations. Server-owned joins determine
  tenant scope.
- Active platform-admin membership is the boundary for invitation generation,
  cross-tenant reporting, feedback disposition, and cost administration.
- ALB/WAF is the public network and coarse abuse-control boundary; ECS security
  groups accept only ALB traffic; RDS accepts only approved task groups.
- Secrets Manager owns invite, admin-database, application-database, and
  one-use bootstrap secrets. The current opaque database-session mechanism has
  no signing secret. Terraform state and logs may contain ARNs/configuration but
  no secret values.
- CloudWatch owns runtime diagnostics; PostgreSQL owns users, memberships,
  workflow state, achievements, feedback, and usage/cost attribution; S3 owns
  original uploaded evidence.
- Product events are audit/learning evidence, not an authorization source and
  not a billing invoice.

## Read paths and consumers

- Login, current-user, aircraft, logbook, ingestion, AD worklist, profile, and
  feedback frontend pages.
- Ordinary user's scoped observability response and platform-admin pilot
  operations/cost response.
- Operator CloudWatch logs, ECS health, AWS Budget notifications, and RDS/S3
  recovery evidence.
- OCR billing and AD cost summaries; pilot funnel summary derived from the six
  canonical events.
- Release/runbook consumers: builder, independent reviewers, and the operator
  executing a reviewed Terraform/migration/deployment sequence.

## Write paths and administrative paths

- A platform-admin endpoint signs but does not persist bearer codes. Invite
  acceptance atomically creates user, organization, membership, session, and a
  sanitized acceptance event. One separately audited bootstrap command creates
  only the first platform administrator on an empty deployment.
- Existing authenticated aircraft, upload, ingestion, logbook, feedback, and
  AD adjudication endpoints continue to write their current domain records.
- Achievement recording occurs only after the owning server transaction reaches
  the defined success point; failed requests do not create success events.
- Platform admins update feedback state and read global operational/cost views;
  ordinary users submit and read only authorized feedback.
- A one-off migration/bootstrap task performs database role/schema changes.
  Runtime tasks cannot perform DDL or role administration.
- Terraform/apply, image push, secret writes, DNS/certificate changes, service
  count changes, and AWS migrations remain separately authorized external
  mutations and are not implied by design approval.

## Migration, compatibility, correction, and rollback

- The invite design intentionally adds no application table and therefore does
  not consume or depend on the unreviewed 0030 revision. Any required pilot
  database change must first resolve revision ownership and receive its own
  reviewed migration plan.
- The reviewed pilot database head is the committed migration head selected in
  the release manifest, never the filesystem's untracked newest-looking file.
- Local/test self-registration remains backward compatible; pilot behavior is
  controlled by an explicit environment mode and startup assertions.
- Event taxonomy is additive. Existing event rows remain readable and are not
  rewritten. Funnel reports count only explicitly mapped version-1 events.
- Authorization corrections tighten reads/updates; no data rewrite is required.
  Previously globally readable observability data becomes admin-only or tenant
  scoped.
- Infrastructure is applied at zero service count. If bootstrap or migration
  fails, do not start services. Application rollback uses the previous immutable
  image only when its schema compatibility is documented; otherwise restore a
  pre-migration snapshot into a new RDS instance and repoint secrets.
- Invitation-secret rotation invalidates all outstanding invitations, not
  existing sessions. Emergency session invalidation uses the audited database
  revocation command; rotating an unused/configuration secret is not accepted
  as evidence of logout.
- Pilot data deletion is not part of rollback. RDS deletion protection, final
  snapshots, S3 versioning, and `force_destroy=false` remain in effect.

## Test strategy

Use a small invariant-driven acceptance matrix rather than exhaustive V4
enumeration.

1. **Release gate:** pilot startup accepts the documented safe configuration,
   rejects each V4 route/service gate individually and in combinations, and a
   route inventory proves every V4 HTTP method unavailable in pilot.
2. **Invitation:** valid, expired, altered, wrong-signature, unsupported role,
   platform-admin, invalid role/org mapping, duplicate/replay, malformed, and
   concurrent acceptance. Prove non-admin signing is forbidden and first-admin
   bootstrap refuses a nonempty authority state.
   Prove no partial user/org/membership remains on failure and no code appears
   in URL/history/referrer/logs/events.
3. **Auth/session:** pilot public registration disabled, local registration
  retained, generic login failures, secure cookie in pilot, inactive user and
  revoked session rejected, and unsafe cookie-authenticated requests reject
  missing/wrong origins without breaking approved same-origin requests. The
  Next development proxy returns unavailable in pilot, and bulk/per-user
  session revocation invalidates already-issued sessions.
4. **Tenant ACL:** two unrelated organizations plus platform admin exercise
   aircraft, uploads, workflows, feedback, product events, user filters, and
   status updates. Direct identifiers from the other tenant always fail closed;
   revoking membership/assignment immediately removes aircraft-bound telemetry
   even when the caller originally authored it.
5. **Telemetry:** one success and one failure for each canonical workflow;
   exact achievement counts and duplicate-event report deduplication;
   correlation ID propagation; malicious properties
   cannot persist secrets, raw text, or oversized content; DB outage still logs
   an error.
6. **Cost:** multiple users/accounts/aircraft/providers and billing statuses;
   priced, unpriced, attributed, unattributed, failed, retry, native bypass, and
   Textract cases. Inject crashes before Start, after Start/before JobId commit,
   after JobId commit, during poll, and after provider completion/before final
   domain commit. Prove stable provider idempotency, one claim, recovery by
   JobId, no automatic ambiguous retry/double-charge, and no unknown-to-zero
   conversion.
7. **Build/IaC:** frontend/backend container builds, deterministic release tag,
   Terraform formatting/validation/plan, IAM policy checks, and no secret value
   in plan/output/logs.
8. **Disposable PostgreSQL:** fresh committed-head migration plus idempotent
   reference bootstrap, first-admin bootstrap, manual entry, OCR-derived entry,
   and app-role privilege negatives. `seed_dev.py` is never invoked and T081
   0030 is absent. Runtime role cannot DDL or manage roles; migration role can
   complete and rerun the supported reference path, while repeated first-admin
   bootstrap fails closed.
9. **AWS acceptance:** HTTPS login/invite, two-tenant isolation, one bounded
   upload/OCR/review/entry flow, feedback, achievement visibility, cost record,
   CloudWatch error correlation, budget subscriber, health checks, backup
   restore, and previous-image rollback.

Only tests whose changed dependencies can invalidate the pilot evidence are
repeated. Full T081 semantic-oracle and Cartesian mutation suites are explicitly
outside this run.

## Expected file scope

- `.ai/review-runs/T082-AWS-INVITE-PILOT/**`
- pilot target/release/runbook documentation under `.ai/`
- backend configuration, auth routes/schemas/security, authorization helpers,
  observability/event/cost services and their targeted tests
- frontend login/register/invitation, observability, and admin pilot views plus
  frontend Docker/build configuration and smoke coverage
- Terraform variables, ALB/ACM/WAF, ECS task/service, RDS/secret/migration-role,
  IAM, outputs, and deployment documentation
- image/deployment scripts that are non-secret and deterministically bind the
  reviewed release

Explicitly excluded: existing modified/untracked T081 4B files, the unreviewed
0030 candidate-acceptance migration/SQL/contract/generator/tests, broad V4
semantic oracle expansion, customer billing/charging, Cognito migration,
multi-region/HA, and unrelated cleanup.

## Known uncertainty

- No DNS name, Route 53 zone, ACM certificate, or certificate owner is recorded
  in the repository. HTTPS infrastructure cannot be finalized or applied until
  the operator supplies the domain/zone decision.
- The real AWS budget notification recipient is intentionally not stored in
  Git; it must be supplied at reviewed apply time.
- Live AWS state was not refreshed for this framing pass. Service-linked-role,
  deploy-role, RDS quota, VPC/Fargate quota, ECR, and secret preflight evidence
  must be refreshed read-only before the infrastructure design is approved.
- The committed migration head must be proven on the selected RDS PostgreSQL
  version without importing the untracked 0030 work. Existing advanced V4
  migrations may impose RDS privilege assumptions even when feature-gated.
- Stateless invitations cannot revoke one outstanding token without rotating
  the shared invite secret and cannot add an existing user to a second
  organization. Those are accepted only as bounded pilot limitations subject
  to independent review.
- AWS WAF, ALB, RDS, Fargate, logs, backups, and OCR have fixed/variable costs;
  the reviewed Terraform plan and current pricing estimate must stay below the
  pilot budget before apply.
- Frontend documentation is stale about implemented AD pages; user-facing scope
  must be verified from the built release rather than those statements.

## Model routing

- Framing/coordinator: model not exposed by runtime (effort not exposed).
  Trigger: authorization, IAM, external-user privacy, billing telemetry, and
  regulatory feature-boundary design.
- Design adversary: GPT-6 Astra xhigh requested. Trigger: new invite trust
  boundary, tenant ACL, AWS database authority, and separation from repeatedly
  failed T081 invariant work.
- Planned family builders/reviewers are recorded in the package table above;
  actual runtime model/effort and fallbacks must replace requests in each new
  review artifact when known.


## Current finding ledger

```json
[
  {
    "id": "T082-DESIGN-001",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Paid provider attempts are durable, single-claim, replay-safe, and cost-visible across crashes and ambiguous outcomes.",
    "summary": "The current OCR transaction can lose a billable Textract Start and automatically submit another paid attempt.",
    "evidence": [
      "backend/app/services/ingestion.py:90-120,238 flushes but does not commit the attempt before the provider call.",
      "backend/app/services/ocr_provider.py:353-362 starts Textract without a stable idempotency token and keeps JobId only in memory.",
      "backend/app/workers/ocr.py:10-15 automatically selects failed jobs; backend/app/services/ocr_billing.py:42-44 excludes failed attempts."
    ],
    "impact": "A crash or timeout can create duplicate AWS spend while local cost evidence omits or undercounts the first attempt.",
    "requiredClosure": "Define durable pre-call identity, serialized claim, stable provider token, retained JobId, ambiguous reconciliation, and failed/unknown cost visibility; later prove crash and competing-worker cases.",
    "closureEvidence": [
      "decision.md defines committed OCRRun intent, frozen Start parameters/S3 version, stable Textract token, retained JobId, six-day recovery ceiling, single claim, and reconciliation_required.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-002",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "A fresh pilot database becomes usable without development users or fixed credentials.",
    "summary": "Required logbook-section rows and the first platform administrator previously existed only through seed_dev.py.",
    "evidence": [
      "backend/app/db/migrations/versions/20260617_0001_initial_schema.py:45-53 creates the table but not required rows.",
      "backend/app/api/routes/logbook_entries.py:41-44,235 and backend/app/services/ingestion.py:308-311 require those rows.",
      "backend/app/scripts/seed_dev.py:19-35,209-224 also creates public demo credentials."
    ],
    "impact": "A clean AWS database cannot complete manual/OCR entry workflows, while using the development seed exposes a known administrator password.",
    "requiredClosure": "Specify idempotent non-demo reference data, a secure first-admin bootstrap, prohibition of seed_dev, and clean-database acceptance evidence.",
    "closureEvidence": [
      "decision.md:269-281 defines separate first-admin and idempotent reference-data bootstrap phases without seed_dev.py.",
      "decision.md test strategy requires fresh migration/bootstrap, manual and OCR-derived entry, and rerun behavior.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-003",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Historical authorship never restores access removed by current membership or aircraft-assignment revocation.",
    "summary": "An actor branch could have exposed aircraft-bound events or feedback after the actor lost tenant access.",
    "evidence": [
      "backend/app/api/routes/aircraft.py:51-70 removes aircraft visibility with inactive membership or assignment.",
      "backend/app/api/routes/observability.py:80-108 stores aircraft-linked user feedback."
    ],
    "impact": "A former tenant participant could retain access to aircraft-linked operational or user-authored data.",
    "requiredClosure": "Require current aircraft/organization authority for tenant-bound records, actor-only fallback for personal unbound rows, authoritative workflow joins, and revocation tests.",
    "closureEvidence": [
      "decision.md:192-200 defines current-visibility scoping, limited personal fallback, and fail-closed workflow resolution.",
      "decision.md tenant ACL tests require membership and assignment revocation coverage.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-004",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Invitation roles map exactly to existing organization and membership authorization domains.",
    "summary": "Initial owner/maintenance token roles did not match owner_admin/maintenance_admin application checks.",
    "evidence": [
      "frontend owner and maintenance checks use owner_ and maintenance_ role prefixes.",
      "backend/app/scripts/seed_dev.py:214-219 uses owner_admin and maintenance_admin with owner and maintenance_shop organization types."
    ],
    "impact": "A valid invite could create a user unable to perform the intended pilot workflow or with an ambiguous authority domain.",
    "requiredClosure": "Close the exact owner_admin/owner and maintenance_admin/maintenance_shop mapping and reject all other pairs.",
    "closureEvidence": [
      "decision.md specifies the exact allowed mappings and fail-closed behavior.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-005",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Pilot browser mutations traverse one origin/CSRF/WAF/correlation boundary.",
    "summary": "The Next development proxy forwarded cookies/body while dropping security and correlation context.",
    "evidence": [
      "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts:18-44 forwards cookie and body but not Origin, Referer, or correlation headers."
    ],
    "impact": "The alternate proxy path could bypass the proposed request controls and fragment evidence.",
    "requiredClosure": "Disable the proxy in pilot and use one direct same-origin API path; retain implementation proof.",
    "closureEvidence": [
      "decision.md:180-191 requires exact origin enforcement, direct /api/v1 calls, and pilot-unavailable /api/backend proxy.",
      "adversarial-design-initial.md records independent acceptance of the corrected design."
    ]
  },
  {
    "id": "T082-DESIGN-006",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Emergency session invalidation revokes already-issued opaque database sessions.",
    "summary": "The original design incorrectly claimed rotation of an unused session secret would invalidate sessions.",
    "evidence": [
      "backend/app/core/security.py:38-43 creates random tokens and unsalted SHA256 hashes without the configured secret.",
      "backend/app/api/deps.py:22-35 relies on database revocation and expiry."
    ],
    "impact": "An operator could believe sessions were revoked while existing cookies remained valid.",
    "requiredClosure": "Use audited per-user/global database revocation and remove the unused secret from the pilot contract; retain implementation proof.",
    "closureEvidence": [
      "decision.md:282-287 and 416-419 define database revocation and reject secret rotation as evidence.",
      "adversarial-design-initial.md records independent acceptance of the corrected design."
    ]
  },
  {
    "id": "T082-DESIGN-007",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Achievement names and success predicates state only what the current authoritative workflow has actually completed.",
    "summary": "The proposed ocr_review_completed milestone fired after page order/completeness verification even when mandatory low-confidence corrections remained.",
    "evidence": [
      "backend/app/api/routes/ingestion.py:390-399 sets verification_status verified but may leave job.status awaiting_ocr_corrections."
    ],
    "impact": "Pilot reporting could count OCR review as complete while the user still had required correction work.",
    "requiredClosure": "Either require all mandatory corrections or name the milestone as page review only and state that it does not prove correction completion.",
    "closureEvidence": [
      "decision.md version-1 achievement table uses page_review_completed and explicitly disclaims completion of low-confidence corrections.",
      "design-remediation-1.md records the semantic correction without adding a new workflow.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-A-001",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every pilot V4 route-family request is rejected before authentication, request-body parsing, or CORS handling using the same decoded path authority as the router.",
    "summary": "Reparsing request.url.path truncates decoded question-mark and fragment characters, allowing encoded delimiter requests to reach V4 authentication.",
    "evidence": [
      "GET /api/v1/ads/directives/id%3Fquery/v4/candidate-proposals reached an injected authentication sentinel.",
      "The %23fragment variant also reached authentication, while the ordinary path returned the generic 404."
    ],
    "impact": "A pilot request can enter unfinished V4 authentication or validation despite the claimed release boundary.",
    "requiredClosure": "Use the decoded ASGI scope path with deliberate root-path handling and independently verify encoded-delimiter, authentication-sentinel, body-read-sentinel, and preflight cases.",
    "closureEvidence": [
      "backend/app/main.py classifies starlette._utils.get_route_path(request.scope), matching router decoding and root-path handling.",
      "backend/tests/test_pilot_release_boundary.py covers %3F/%23 authentication sentinels, preflight, mounted decoded paths, and a body-read sentinel.",
      "package-a-remediation-1.md records 23 focused passing tests.",
      "adversarial-implementation-package-a-remediation-1.md records an independent 378-case raw-ASGI matrix with zero authentication or body reads."
    ]
  },
  {
    "id": "T082-A-002",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "fixed_pending_verification",
    "invariant": "The release verifier proves the exact executed, complete, acyclic migration graph approved for the pilot candidate.",
    "summary": "First-assignment parsing and head set subtraction accept later metadata overrides and disconnected migration cycles.",
    "evidence": [
      "Appending a second revision assignment to the committed 0029 migration still produced a passing 0029 head.",
      "A disconnected two-revision cycle beside the expected head also preserved the expected head and passed."
    ],
    "impact": "An unreviewed executed migration identity or invalid graph can receive a false release-boundary pass.",
    "requiredClosure": "Independently verify the approved sealed-context builder, exact Git/mode/hash/output manifest, and execution-backed import oracle; retain candidate-commit and Package E immutable-image/task acceptance gates.",
    "closureEvidence": [
      ".ai/pilot-release-boundary-v1.json binds the exact 29 approved migration source paths and blob hashes.",
      "scripts/verify_pilot_release_boundary.py rejects inventory/blob drift, duplicate metadata, missing predecessors, duplicate predecessors, and graph cycles.",
      "backend/tests/test_pilot_release_boundary.py mutates actual 0029 content and constructs a disconnected cycle; both fail.",
      "package-a-remediation-1.md records 23 focused passing tests and an explicit HEAD check with all 29 revision blobs matched.",
      "adversarial-implementation-package-a-remediation-1.md shows the remaining unbound SQL/configuration and Git-quoted path gaps; the finding is not closed.",
      "package-a-remediation-2.md binds 44 authority inputs including the whole migration directory, Alembic configuration, and env.py repository import closure; the exact Package A config target amendment is recorded.",
      "The verifier now compares raw NUL-delimited Git names as bytes and requires all four graph metadata declarations, a complete acyclic single-root graph, the separate head, and protected model checks.",
      "Remediation 2: 124 dependency-relevant tests pass, including candidate authority addition/removal/rename/content drift and quoted/tab/newline/UTF-8/non-UTF-8 names under migration and excluded T081 prefixes; Python compilation and diff checks pass.",
      "HEAD correctly fails only for the intentionally target-bound config.py; the mocked target candidate passes. Eventual reviewed candidate-commit verification and independent finding verification remain required.",
      "adversarial-implementation-package-a-remediation-2.md proves backend/psycopg.py and backend/psycopg/__init__.py can execute through engine_from_config while the 44-file verifier passes; implementation paused after the third loop.",
      "package-a-authority-architecture-amendment.md replaces import-name enumeration with a sealed context assembled only from reviewed Git blobs.",
      "adversarial-authority-architecture-amendment.md independently passes the architecture and records the required implementation evidence; implementation may resume but the finding remains open.",
      "package-a-remediation-3.md records the sealed 44-file context plus deterministic manifest, exact commit/blob/mode checks, exclusive no-symlink creation, read-only integrity verification, and simplified source-verifier responsibility.",
      "Actual Alembic env.py and SQLAlchemy engine_from_config select injected psycopg module/package sentinels in vulnerable controls, while sealed controls load canonical installed psycopg with no checkout source on sys.path and no database connection.",
      "Remediation 3 evidence: 292 boundary cases and 16 existing V4 API cases pass; compilation and diff checks pass. Runtime database configuration is required, dotenv/bytecode disabled, and child secret output suppressed. Independent implementation verification and later candidate/image/task gates remain required."
    ]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT/decision.md`

size=36292; sha256=69c2cce98e90b2902e172ef067800ee6bfdbdaaef3f701b8fe492a694d977f71

```text
# Decision packet: T082-AWS-INVITE-PILOT

## Objective

Launch a deliberately bounded, invite-only paprnav pilot on AWS so a small
external cohort can exercise the existing aircraft/logbook/OCR/AD
decision-support workflow while the operator can observe failures, successful
milestones, and attributable cost. This run optimizes time to validated product
learning while retaining minimum external-user security, privacy, durability,
and cost controls.

This run does not close, weaken, or absorb `T081-V4-SCHEMA-SLICE-4B`. Its open
findings and uncommitted working tree remain intact. The pilot release excludes
the unreviewed 0030 candidate-acceptance migration and keeps every unfinished V4
write/read/review feature gate disabled.

Pilot scale is at most ten invited users/aircraft in one AWS `pilot`
environment. Paprnav remains decision support and must not claim official
airworthiness or regulatory compliance.

## User-visible outcome

- An operator can generate a short-lived invitation for a named email and an
  allowed pilot role without enabling public account creation.
- An invitee can accept the invitation, set a password, sign in over HTTPS,
  create or access only authorized aircraft, upload a logbook, review OCR,
  create structured entries, and view conservative AD decision-support output.
- A user can submit feedback with a request/workflow reference without exposing
  another tenant's events or feedback.
- The operator can see sanitized operational errors, the agreed product
  milestones, OCR/provider usage, estimated variable cost, and aggregate AWS
  budget state.
- Deployment, migration, rollback, and data recovery have a short operator
  runbook and one bounded acceptance packet.

## Safety and correctness invariants

1. **Invite-only identity.** In `pilot`, public self-registration is unavailable.
   Only a valid, unexpired, correctly signed invitation may create a user and
   membership. Invitation payloads cannot grant `platform_admin`; replay cannot
   create a second user or additional membership.
2. **Tenant isolation.** A non-platform user may read events, workflows,
   feedback, uploads, entries, and aircraft only when the existing membership
   and aircraft visibility rules authorize them. Client-provided `userId`,
   `organizationId`, `aircraftId`, or subject identifiers never widen access.
3. **Administrative authority.** Cross-tenant pilot reporting, invitation
   generation, feedback disposition, and cost summaries require a fresh active
   `platform_admin` membership. A separately audited deployment role may only
   bootstrap the first platform administrator on an empty deployment and may
   not generate user invitations; possession of an ordinary application
   session is insufficient.
4. **HTTPS session boundary.** External browser traffic is HTTPS only. Pilot
   session cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`; secrets and
   invitation codes never enter logs, product-event properties, URLs, browser
   history, referrers, or client analytics. Unsafe cookie-authenticated methods
   reject absent or unapproved Origin/Referer context in pilot.
5. **Closed regulatory boundary.** A pilot-wide V4 route gate is false and all
   unfinished V4 service gates are false in `pilot`; startup fails closed if
   configuration attempts to enable any of them. Candidate-only or unreviewed data cannot become a pilot-facing
   compliance statement. Existing AD output retains degraded-coverage and
   needs-review states and is labelled decision support.
6. **Error evidence without source-data leakage.** Each request has a correlation
   ID. Expected workflow failures persist bounded codes/status on their owning
   record; unexpected failures produce structured CloudWatch logs containing
   route, status, release, and authorized actor/account identifiers, but no
   passwords, tokens, file bytes, raw logbook text, OCR text, or free-form
   maintenance content.
7. **Meaningful achievements.** The first taxonomy is versioned and limited to
   `invite_accepted`, `aircraft_created`, `upload_received`,
   `page_review_completed`, `logbook_entry_created`, and
   `ad_review_completed`. Events bind to the authenticated actor and server-owned
   organization/aircraft/workflow identifiers. Client requests cannot assert
   successful completion of a server workflow.
8. **Cost attribution.** Every paid OCR invocation records provider/mode,
   billable units, configured unit rate, estimated USD, billing status,
   organization/account, aircraft, upload/job, and the initiating user through
   the owning ingestion job. Unknown price or attribution remains visibly
   unknown; it is never converted to zero-cost or allocated customer charges.
   Shared AWS spend remains separate from per-user variable cost.
9. **Bounded spend.** A real budget notification recipient is configured before
   paid OCR or invited-user traffic. Expensive workers are disabled until their
   image, secret, provider mode, per-page ceiling, durable idempotent attempt,
   single-claim behavior, ambiguous-outcome reconciliation, and operator
   enablement are verified. No customer billing or automated charging occurs
   in this run.
10. **Durable, recoverable data.** RDS is private and encrypted with automated
    backups; uploaded source files use the existing encrypted/versioned S3
    bucket. A restore check proves the operator can recover pilot records. No
    destroy path may silently remove volunteer data.
11. **Least privilege by function.** Runtime API/worker credentials do not use
    the RDS master identity or migration authority. A one-off migration/bootstrap
    task has separately scoped secret access and no public listener. ECS tasks
    accept inbound traffic only from the ALB security group.
12. **Reproducible release and rollback.** ECS task definitions use an immutable
    release tag or digest, migrations are completed before service counts rise,
    and rollback identifies the prior image plus schema compatibility. `latest`
    is not release evidence.
13. **Preserved review history.** No T081 file, finding, review result, or
    untracked implementation artifact is deleted, rewritten, staged, committed,
    or represented as pilot closure. The pilot release manifest explicitly
    excludes the unreviewed 0030 artifacts.
14. **Cloud mutation gate.** Terraform apply, image push, secret population,
    DNS/certificate changes, migrations against AWS, and service-count changes
    require an approved reviewed plan and explicit execution authorization.
15. **Fresh-database operability.** A committed, idempotent pilot bootstrap
    creates required non-secret reference rows, including the airframe, engine,
    and propeller logbook sections, without running `seed_dev.py` or creating
    demo users/passwords. Manual and OCR-derived entry creation work on a fresh
    migrated/bootstrap database.

## Current behavior

- The local application already supplies API-backed auth, organizations,
  aircraft, maintenance assignments, logbook CRUD, upload/download, OCR review,
  structured extraction, AD ingestion/matching/HITL review, product events,
  feedback, and admin cost summaries.
- The repository contains 479 backend test functions and a frontend smoke
  script, but this run has not yet established a clean pilot-baseline result.
- Public `/api/v1/auth/register` is enabled and immediately creates an active
  user. The browser session cookie is currently written with `secure=False`.
- The observability list begins with global product-event, workflow-event, and
  feedback queries; an authenticated caller may supply an arbitrary `user_id`.
  Feedback status updates require aircraft visibility only when the feedback
  has an aircraft, rather than requiring platform administration.
- Product-event values are sanitized and ingestion jobs/OCR runs already retain
  useful error, actor, provider, unit, pricing, and attribution data.
- The applied AWS foundation contains S3, remote Terraform state, ECR
  repositories, an ECS cluster, CloudWatch log groups, and a budget. The runtime
  VPC/ALB/RDS/ECS skeleton is checked in and was previously validated/planned,
  but it is not applied; ECR is empty, frontend has no Dockerfile, secrets are
  placeholders, services are at zero, and the ALB is HTTP-only.
- The runtime task definitions reference `:latest`, run API/worker with one
  application database secret, and do not define the separate migration
  authority required by this design.
- The active T081 4B run has open PostgreSQL/RDS/ACL/oracle findings. The
  unfinished 0030 artifacts are untracked or modified and are not pilot inputs.

## Proposed design

### 0. Release boundary and feature exposure

- Define one pilot release manifest at a reviewed Git commit. The manifest lists
  included Alembic head, image digests, enabled routes/providers, expected
  environment variables, and explicitly excluded T081/0030 artifacts.
- Add one route-family gate that makes every `/api/v1/ads/**/v4/**` operation
  unavailable in `pilot`, including the committed validator-v1 candidate route
  which currently has no application feature gate. Keep all existing V4
  service defaults false. Add a pilot startup assertion that rejects an enabled
  V4 route, write, projection, review, or acceptance gate. The established non-V4 AD worklist remains available with decision-
  support language and existing uncertainty/degraded states.
- Do not copy, reset, or delete the dirty T081 working tree. Implementation must
  either avoid overlapping files or isolate pilot release construction after a
  reviewed handoff; no commit may accidentally include T081 artifacts.

### 1. Invite-only access and tenant-safe telemetry

- Retain the application session model for this pilot; do not migrate to a new
  identity provider in the critical path.
- Use a stateless, HMAC-SHA256 signed invitation with a dedicated Secrets
  Manager signing secret. Its canonical versioned payload contains a random
  nonce, normalized email, display name, organization name/type, allowed role,
  issued-at, and expiry. Allowed mappings are exactly `owner_admin` in an
  `owner` organization and `maintenance_admin` in a `maintenance_shop`
  organization; every other role/type pair, including `platform_admin`, is
  rejected by both signing and acceptance.
- An authenticated platform-admin endpoint generates a bearer invitation code;
  it signs server-side so the operator never reads the signing secret. The
  response is `no-store`, bounded, and not copied into product-event properties.
  No mail provider is required initially; the operator delivers the code out of
  band and the user pastes it into a fixed invitation page whose URL contains no
  credential. Codes have a maximum 24-hour lifetime, canonical UTC timestamps,
  one normalization version, and at most five minutes of clock-skew tolerance.
  Acceptance verifies signature and expiry, creates user,
  organization, and membership atomically, records `invite_accepted`, and fails
  generically if the email already exists. Email uniqueness makes successful
  acceptance non-replayable. Revocation before expiry is by rotating the
  dedicated invite secret; per-invite revocation is a documented pilot
  limitation.
- Local/test environments may retain self-registration. `pilot` returns a
  non-enumerating not-found/disabled response from public registration, hides
  the registration link, and exposes an invitation-acceptance page instead.
- Pilot cookies derive `Secure` from an explicit setting which must be true at
  startup in `pilot`. Login and invite endpoints receive bounded AWS WAF
  rate-based protection; failure responses do not disclose whether an email is
  registered or invited. Pilot CORS uses an exact HTTPS origin, and unsafe
  cookie-authenticated requests require an exact allowed Origin (or a same-origin
  Referer fallback where browser behavior requires it); wildcard origins and
  cross-origin credentialed mutations are rejected.
- The browser calls the ALB's same-origin `/api/v1/*` route directly in pilot.
  The Next `/api/backend/*` development proxy is disabled in pilot and tests
  prove it cannot forward cookies or mutations there. Local development may
  retain the proxy. This gives WAF, CSRF/origin enforcement, correlation IDs,
  route metrics, and authorization one public API path.
- Ordinary observability reads are restricted to the current actor plus records
  attached to aircraft currently visible to that actor; they cannot accept a
  widening `user_id`. Actor ownership never preserves access to an
  aircraft-bound event or feedback row after membership/assignment revocation.
  Actor-only fallback applies only to personal rows with no organization or
  aircraft. Generic workflow events are admin-only unless a server-side join
  resolves the referenced workflow to a currently visible aircraft. A distinct
  platform-admin endpoint provides bounded cross-tenant operational reporting.
  Only platform admins may change feedback status.

### 2. Pilot instrumentation

- Add request-correlation middleware. Honor an incoming correlation ID only
  after format/length validation; otherwise generate one. Return it in the
  response and include it in sanitized structured logs and server-originated
  product/workflow events.
- Record the six server-owned achievement events named in invariant 7. Reuse
  `ProductEvent`; add a shared constant/validation module and query/reporting
  projection rather than a new analytics schema. Existing event types remain
  valid but do not count toward the pilot funnel unless mapped explicitly.
- Version-1 achievement success and identity are closed as follows:

  | Event | Success point | Subject and report deduplication key |
  | --- | --- | --- |
  | `invite_accepted` | user, organization, membership, session, and event commit atomically | `user:<new-user-id>` |
  | `aircraft_created` | aircraft and its server-derived owner/cost identifiers commit | `aircraft:<aircraft-id>` |
  | `upload_received` | consented upload plus ingestion job commit | `upload:<upload-id>` |
  | `page_review_completed` | first commit where OCR is complete and the latest page verification confirms both order and completeness; it does not claim all low-confidence corrections are complete | `ingestion_job:<job-id>` |
  | `logbook_entry_created` | manual or extracted entry plus its owning aircraft and evidence links commit | `logbook_entry:<entry-id>` |
  | `ad_review_completed` | a human extraction-review decision or aircraft-match adjudication commits | `ad_extraction_review:<review-id>` or `ad_match_adjudication:<adjudication-id>` |

  Every event has taxonomy version `pilot-achievement-v1`, server-derived actor,
  organization, aircraft, subject type, and subject ID and is written in the
  same transaction as its success point. The reporting identity is
  `(taxonomy-version, event-type, subject-type, subject-id)` and counts each
  identity once even if legacy/retry behavior produced duplicate rows. A status
  field, client assertion, or frontend navigation alone is never success.
- CloudWatch is the source for unexpected runtime exceptions and ECS health;
  PostgreSQL is the source for workflow failures, feedback, achievements, and
  per-operation attribution. A database outage therefore remains diagnosable
  from logs rather than relying on an error insert into the failed database.
- Platform-admin reporting returns counts and bounded recent records, not raw
  documents or OCR text. Existing property sanitization remains defense in
  depth and gains direct tests for invitation, authorization, and exception
  fields.

### 3. Cost recording and controls

- Reuse `OCRRun` as the per-invocation source of truth and join through
  `IngestionJob.created_by_user_id`, upload, aircraft, and organization. Report
  unattributed, unpriced, failed, and reconciliation-required runs explicitly by
  user/account/aircraft/provider; completed-only billing totals remain a
  separate view.
- Reuse `ADCostLedgerEntry` for AD/shared-source work. Do not mix estimated OCR
  chargeback, actual provider invoices, and shared infrastructure allocation.
- Configure the existing AWS Budget with a real subscriber. Use project and
  environment resource tags for aggregate AWS reporting. Cost Explorer/CUR
  reconciliation is an operator cadence after launch and is not required to
  block the first invite, provided budget alerts and app-side paid-operation
  attribution are active.
- Set a conservative per-upload page ceiling and keep paid Textract opt-in until
  its async S3 mode, rate, timeout, and attempt protocol are verified.
  Deterministic OCR remains available for the infrastructure smoke path.
- Before a paid provider call, acquire a per-job PostgreSQL claim/advisory lock
  and commit one `OCRRun` intent containing a stable provider idempotency token,
  upload hash, provider/config identity, page ceiling, initiator, and attribution
  metadata. The intent freezes the complete Start request, including API mode,
  feature types, exact S3 bucket/key/version for either the original or derived
  routed object, object/content hash, and every parameter that affects AWS's
  idempotency comparison. Textract async Start uses a token derived from that
  immutable intent. Persist and commit the returned JobId before polling; after
  a crash, resume/poll that JobId or repeat Start with the identical token and
  parameters only within six days of intent creation. This deadline is
  deliberately inside Textract's seven-day idempotency and result-retention
  windows. Store intent/JobId in the existing bounded metadata JSON for this
  pilot unless review proves a schema column is required.
- `failed` or timed-out paid attempts are not automatically resubmitted. An
  unknown Start/poll outcome becomes `reconciliation_required`, retains its
  estimated maximum exposure, and requires an operator reconciliation action.
  Any recovery at/after the six-day deadline, or with unknown intent age or
  parameters, remains `reconciliation_required` and never calls Start. A
  missing JobId within the window may repeat only the identical frozen Start
  after operator reconciliation. A later new paid attempt requires an explicit
  operator disposition linking it to the old attempt and retaining both cost
  exposures.
  The worker claims one queued job transactionally and cannot overlap a second
  worker for the same job. A definite pre-provider validation failure may be
  retried without billable-attempt semantics.

### 4. Deployable AWS runtime

- Build API and frontend images from the reviewed release commit and push an
  immutable release tag/digest to the existing repositories. Add a multi-stage
  frontend Dockerfile whose build receives the public same-origin API base.
- Retain the cost-controlled public-subnet Fargate design for the first pilot:
  the public ALB is the only inbound source to task security groups; RDS remains
  private. Record public task IPs as a pilot-only outbound-cost compromise.
- Add ACM HTTPS with HTTP redirect and a user-owned DNS name. No external invite
  is sent until certificate and browser-cookie behavior are verified.
- Separate database identities:
  - RDS-managed `paprnav_admin` is bootstrap/migration authority;
  - a one-off ECS migration task can read only the RDS admin secret and execute
    the reviewed committed migration head;
  - API/worker read only an application `DATABASE_URL` secret for a
    `paprnav_app` login with runtime DML privileges and no schema/role authority.
  The bootstrap procedure creates/grants the runtime role and writes the app
  secret without exposing values in Terraform output or logs.
- The same one-off bootstrap authority creates the first platform organization,
  user, and active `platform_admin` membership only when no active platform
  administrator exists. Email/name are explicit inputs and the password is
  interactively supplied or read from a one-use secret; no demo identity or
  fixed password is allowed. Subsequent platform-admin creation follows a
  reviewed admin path, not `seed_dev.py`.
- A separate idempotent reference-data step creates the canonical `airframe`,
  `engine`, and `propeller` logbook sections with reviewed display/sort values.
  It creates no user, organization, aircraft, or sample record. The migration
  task runs schema migration, reference-data bootstrap, runtime grants, and
  first-admin bootstrap as explicit individually logged phases; rerunning the
  reference phase is safe, while first-admin bootstrap fails closed once an
  active platform administrator exists.
- Existing sessions are opaque random bearer tokens whose hashes live in
  PostgreSQL; `PAPRNAV_SESSION_SECRET` is currently unused and is removed from
  the pilot task/secret contract rather than treated as a revocation control.
  Add an audited operator command to revoke all sessions or all sessions for one
  user in the database. Invite-secret rotation affects only outstanding invite
  codes.
- Resolve service-linked-role and `rds!db-*` permission preflight before apply.
  Apply network/RDS/runtime definitions with service desired counts at zero,
  run bootstrap/migrations, then raise API/frontend counts. Enable the worker
  only after its provider and cost gate pass.
- Replace `:latest` references with variables bound to reviewed immutable image
  identifiers. Document health checks, prior-task rollback, migration
  compatibility, secret rotation, and RDS restore.

### 5. Review and release cadence

| Package | Dependencies | Risk / complexity / centrality / uncertainty (1-5) | Builder | Independent review boundary | Exit evidence |
| --- | --- | --- | --- | --- | --- |
| A. Release boundary and route gates | approved design | 5 / 2 / 5 / 2 | Sol high | Astra high after complete gate family | all V4 HTTP methods return unavailable in pilot; startup fails for every V4 enablement; release manifest excludes 0030 |
| B. Invite and tenant isolation | A | 5 / 4 / 5 / 3 | Sol high | Astra xhigh after invite + observability family | token negative matrix, role/tenant matrix, secure-cookie proof, WAF plan |
| C. Images, RDS identities, migration path, HTTPS | A, reviewed IAM preflight | 5 / 4 / 5 / 4 | Sol high for coherent implementation; Terra/Sol medium for mechanical generated artifacts | Astra xhigh after complete infrastructure family | validate/plan, policy simulation/live read-only preflight, clean RDS migration, image builds, no cloud mutation yet |
| D. Achievements, errors, and cost view | B; existing event/cost models | 3 / 3 / 4 / 2 | Sol high | Astra high once for complete telemetry/cost family | sanitization negatives, milestone oracle, attribution/unpriced cases, budget plan |
| E. AWS execution and pilot acceptance | B-D, explicit apply authorization, DNS and alert recipient | 5 / 3 / 5 / 3 | coordinator/operator with reviewed runbook | Astra xhigh closure after deployment evidence | HTTPS smoke, tenant isolation, one bounded OCR flow, logs/events/cost, backup/restore, rollback |

Mechanical artifacts, hashes, container builds, and Terraform plan changes are
verified deterministically and included in their family packet; they do not
receive standalone reviewer turns. Expected remaining cadence after design is
four coherent builder passes, four family reviews, and one closure review,
with remediation only for substantive findings.

## Alternatives considered

1. **Continue T081 until every V4 invariant closes before deploying.** Rejected
   for the pilot: it delays product learning and solves a stronger publication
   problem than this non-attestation cohort requires. T081 remains valid future
   hardening work.
2. **Deploy the current tree unchanged.** Rejected: public registration,
   insecure cookies, global observability queries, HTTP-only ingress, empty
   images, and unapplied runtime resources make it neither deployable nor safe
   for unrelated external users.
3. **Adopt Cognito before the pilot.** Deferred. Managed invitations, recovery,
   and MFA are valuable, but replacing the established app session boundary
   adds migration and authorization risk before product learning. Reassess after
   the first cohort.
4. **Store invitation rows in a new database table.** Deferred because the
   active dirty tree already contains an unreviewed 0030 migration and the
   pilot needs only a small cohort. Short-lived signed, role-restricted tokens
   avoid migration collision. Persistent revocation and resend history become
   a post-pilot identity story.
5. **Use public registration plus an email allowlist.** Rejected because email
   ownership is not verified and an attacker who knows an invited address could
   claim it first.
6. **Use the RDS master credential in API and worker tasks.** Rejected because
   an application compromise would gain schema/role authority and because it
   conflates runtime, migration, and candidate-acceptance concerns.
7. **Add a full analytics/error SaaS immediately.** Deferred. Structured
   CloudWatch logs plus existing PostgreSQL events/feedback answer the initial
   learning questions without adding a new processor or data export boundary.
8. **Private Fargate plus NAT gateways.** Deferred for pilot cost. Public task
   IPs with ALB-only inbound security groups retain a smaller fixed-cost shape;
   revisit after measured traffic and risk.

## Trust, authorization, and audit boundaries

- Browser users trust the HTTPS frontend/API origin and hold only an opaque
  session cookie. Invitation codes are short-lived bearer credentials and are
  not sessions after acceptance.
- FastAPI is the authorization boundary for user, organization, aircraft,
  observability, feedback, and admin operations. Server-owned joins determine
  tenant scope.
- Active platform-admin membership is the boundary for invitation generation,
  cross-tenant reporting, feedback disposition, and cost administration.
- ALB/WAF is the public network and coarse abuse-control boundary; ECS security
  groups accept only ALB traffic; RDS accepts only approved task groups.
- Secrets Manager owns invite, admin-database, application-database, and
  one-use bootstrap secrets. The current opaque database-session mechanism has
  no signing secret. Terraform state and logs may contain ARNs/configuration but
  no secret values.
- CloudWatch owns runtime diagnostics; PostgreSQL owns users, memberships,
  workflow state, achievements, feedback, and usage/cost attribution; S3 owns
  original uploaded evidence.
- Product events are audit/learning evidence, not an authorization source and
  not a billing invoice.

## Read paths and consumers

- Login, current-user, aircraft, logbook, ingestion, AD worklist, profile, and
  feedback frontend pages.
- Ordinary user's scoped observability response and platform-admin pilot
  operations/cost response.
- Operator CloudWatch logs, ECS health, AWS Budget notifications, and RDS/S3
  recovery evidence.
- OCR billing and AD cost summaries; pilot funnel summary derived from the six
  canonical events.
- Release/runbook consumers: builder, independent reviewers, and the operator
  executing a reviewed Terraform/migration/deployment sequence.

## Write paths and administrative paths

- A platform-admin endpoint signs but does not persist bearer codes. Invite
  acceptance atomically creates user, organization, membership, session, and a
  sanitized acceptance event. One separately audited bootstrap command creates
  only the first platform administrator on an empty deployment.
- Existing authenticated aircraft, upload, ingestion, logbook, feedback, and
  AD adjudication endpoints continue to write their current domain records.
- Achievement recording occurs only after the owning server transaction reaches
  the defined success point; failed requests do not create success events.
- Platform admins update feedback state and read global operational/cost views;
  ordinary users submit and read only authorized feedback.
- A one-off migration/bootstrap task performs database role/schema changes.
  Runtime tasks cannot perform DDL or role administration.
- Terraform/apply, image push, secret writes, DNS/certificate changes, service
  count changes, and AWS migrations remain separately authorized external
  mutations and are not implied by design approval.

## Migration, compatibility, correction, and rollback

- The invite design intentionally adds no application table and therefore does
  not consume or depend on the unreviewed 0030 revision. Any required pilot
  database change must first resolve revision ownership and receive its own
  reviewed migration plan.
- The reviewed pilot database head is the committed migration head selected in
  the release manifest, never the filesystem's untracked newest-looking file.
- Local/test self-registration remains backward compatible; pilot behavior is
  controlled by an explicit environment mode and startup assertions.
- Event taxonomy is additive. Existing event rows remain readable and are not
  rewritten. Funnel reports count only explicitly mapped version-1 events.
- Authorization corrections tighten reads/updates; no data rewrite is required.
  Previously globally readable observability data becomes admin-only or tenant
  scoped.
- Infrastructure is applied at zero service count. If bootstrap or migration
  fails, do not start services. Application rollback uses the previous immutable
  image only when its schema compatibility is documented; otherwise restore a
  pre-migration snapshot into a new RDS instance and repoint secrets.
- Invitation-secret rotation invalidates all outstanding invitations, not
  existing sessions. Emergency session invalidation uses the audited database
  revocation command; rotating an unused/configuration secret is not accepted
  as evidence of logout.
- Pilot data deletion is not part of rollback. RDS deletion protection, final
  snapshots, S3 versioning, and `force_destroy=false` remain in effect.

## Test strategy

Use a small invariant-driven acceptance matrix rather than exhaustive V4
enumeration.

1. **Release gate:** pilot startup accepts the documented safe configuration,
   rejects each V4 route/service gate individually and in combinations, and a
   route inventory proves every V4 HTTP method unavailable in pilot.
2. **Invitation:** valid, expired, altered, wrong-signature, unsupported role,
   platform-admin, invalid role/org mapping, duplicate/replay, malformed, and
   concurrent acceptance. Prove non-admin signing is forbidden and first-admin
   bootstrap refuses a nonempty authority state.
   Prove no partial user/org/membership remains on failure and no code appears
   in URL/history/referrer/logs/events.
3. **Auth/session:** pilot public registration disabled, local registration
  retained, generic login failures, secure cookie in pilot, inactive user and
  revoked session rejected, and unsafe cookie-authenticated requests reject
  missing/wrong origins without breaking approved same-origin requests. The
  Next development proxy returns unavailable in pilot, and bulk/per-user
  session revocation invalidates already-issued sessions.
4. **Tenant ACL:** two unrelated organizations plus platform admin exercise
   aircraft, uploads, workflows, feedback, product events, user filters, and
   status updates. Direct identifiers from the other tenant always fail closed;
   revoking membership/assignment immediately removes aircraft-bound telemetry
   even when the caller originally authored it.
5. **Telemetry:** one success and one failure for each canonical workflow;
   exact achievement counts and duplicate-event report deduplication;
   correlation ID propagation; malicious properties
   cannot persist secrets, raw text, or oversized content; DB outage still logs
   an error.
6. **Cost:** multiple users/accounts/aircraft/providers and billing statuses;
   priced, unpriced, attributed, unattributed, failed, retry, native bypass, and
   Textract cases. Inject crashes before Start, after Start/before JobId commit,
   after JobId commit, during poll, and after provider completion/before final
   domain commit. Prove stable provider idempotency, one claim, recovery by
   JobId, no automatic ambiguous retry/double-charge, and no unknown-to-zero
   conversion.
7. **Build/IaC:** frontend/backend container builds, deterministic release tag,
   Terraform formatting/validation/plan, IAM policy checks, and no secret value
   in plan/output/logs.
8. **Disposable PostgreSQL:** fresh committed-head migration plus idempotent
   reference bootstrap, first-admin bootstrap, manual entry, OCR-derived entry,
   and app-role privilege negatives. `seed_dev.py` is never invoked and T081
   0030 is absent. Runtime role cannot DDL or manage roles; migration role can
   complete and rerun the supported reference path, while repeated first-admin
   bootstrap fails closed.
9. **AWS acceptance:** HTTPS login/invite, two-tenant isolation, one bounded
   upload/OCR/review/entry flow, feedback, achievement visibility, cost record,
   CloudWatch error correlation, budget subscriber, health checks, backup
   restore, and previous-image rollback.

Only tests whose changed dependencies can invalidate the pilot evidence are
repeated. Full T081 semantic-oracle and Cartesian mutation suites are explicitly
outside this run.

## Expected file scope

- `.ai/review-runs/T082-AWS-INVITE-PILOT/**`
- pilot target/release/runbook documentation under `.ai/`
- backend configuration, auth routes/schemas/security, authorization helpers,
  observability/event/cost services and their targeted tests
- frontend login/register/invitation, observability, and admin pilot views plus
  frontend Docker/build configuration and smoke coverage
- Terraform variables, ALB/ACM/WAF, ECS task/service, RDS/secret/migration-role,
  IAM, outputs, and deployment documentation
- image/deployment scripts that are non-secret and deterministically bind the
  reviewed release

Explicitly excluded: existing modified/untracked T081 4B files, the unreviewed
0030 candidate-acceptance migration/SQL/contract/generator/tests, broad V4
semantic oracle expansion, customer billing/charging, Cognito migration,
multi-region/HA, and unrelated cleanup.

## Known uncertainty

- No DNS name, Route 53 zone, ACM certificate, or certificate owner is recorded
  in the repository. HTTPS infrastructure cannot be finalized or applied until
  the operator supplies the domain/zone decision.
- The real AWS budget notification recipient is intentionally not stored in
  Git; it must be supplied at reviewed apply time.
- Live AWS state was not refreshed for this framing pass. Service-linked-role,
  deploy-role, RDS quota, VPC/Fargate quota, ECR, and secret preflight evidence
  must be refreshed read-only before the infrastructure design is approved.
- The committed migration head must be proven on the selected RDS PostgreSQL
  version without importing the untracked 0030 work. Existing advanced V4
  migrations may impose RDS privilege assumptions even when feature-gated.
- Stateless invitations cannot revoke one outstanding token without rotating
  the shared invite secret and cannot add an existing user to a second
  organization. Those are accepted only as bounded pilot limitations subject
  to independent review.
- AWS WAF, ALB, RDS, Fargate, logs, backups, and OCR have fixed/variable costs;
  the reviewed Terraform plan and current pricing estimate must stay below the
  pilot budget before apply.
- Frontend documentation is stale about implemented AD pages; user-facing scope
  must be verified from the built release rather than those statements.

## Model routing

- Framing/coordinator: model not exposed by runtime (effort not exposed).
  Trigger: authorization, IAM, external-user privacy, billing telemetry, and
  regulatory feature-boundary design.
- Design adversary: GPT-6 Astra xhigh requested. Trigger: new invite trust
  boundary, tenant ACL, AWS database authority, and separation from repeatedly
  failed T081 invariant work.
- Planned family builders/reviewers are recorded in the package table above;
  actual runtime model/effort and fallbacks must replace requests in each new
  review artifact when known.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/findings.json`

size=14534; sha256=09965b0d059bf502df2438ad9dd225351e32fac4fef453c6c787ffa945280a73

```text
[
  {
    "id": "T082-DESIGN-001",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Paid provider attempts are durable, single-claim, replay-safe, and cost-visible across crashes and ambiguous outcomes.",
    "summary": "The current OCR transaction can lose a billable Textract Start and automatically submit another paid attempt.",
    "evidence": [
      "backend/app/services/ingestion.py:90-120,238 flushes but does not commit the attempt before the provider call.",
      "backend/app/services/ocr_provider.py:353-362 starts Textract without a stable idempotency token and keeps JobId only in memory.",
      "backend/app/workers/ocr.py:10-15 automatically selects failed jobs; backend/app/services/ocr_billing.py:42-44 excludes failed attempts."
    ],
    "impact": "A crash or timeout can create duplicate AWS spend while local cost evidence omits or undercounts the first attempt.",
    "requiredClosure": "Define durable pre-call identity, serialized claim, stable provider token, retained JobId, ambiguous reconciliation, and failed/unknown cost visibility; later prove crash and competing-worker cases.",
    "closureEvidence": [
      "decision.md defines committed OCRRun intent, frozen Start parameters/S3 version, stable Textract token, retained JobId, six-day recovery ceiling, single claim, and reconciliation_required.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-002",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "A fresh pilot database becomes usable without development users or fixed credentials.",
    "summary": "Required logbook-section rows and the first platform administrator previously existed only through seed_dev.py.",
    "evidence": [
      "backend/app/db/migrations/versions/20260617_0001_initial_schema.py:45-53 creates the table but not required rows.",
      "backend/app/api/routes/logbook_entries.py:41-44,235 and backend/app/services/ingestion.py:308-311 require those rows.",
      "backend/app/scripts/seed_dev.py:19-35,209-224 also creates public demo credentials."
    ],
    "impact": "A clean AWS database cannot complete manual/OCR entry workflows, while using the development seed exposes a known administrator password.",
    "requiredClosure": "Specify idempotent non-demo reference data, a secure first-admin bootstrap, prohibition of seed_dev, and clean-database acceptance evidence.",
    "closureEvidence": [
      "decision.md:269-281 defines separate first-admin and idempotent reference-data bootstrap phases without seed_dev.py.",
      "decision.md test strategy requires fresh migration/bootstrap, manual and OCR-derived entry, and rerun behavior.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-003",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Historical authorship never restores access removed by current membership or aircraft-assignment revocation.",
    "summary": "An actor branch could have exposed aircraft-bound events or feedback after the actor lost tenant access.",
    "evidence": [
      "backend/app/api/routes/aircraft.py:51-70 removes aircraft visibility with inactive membership or assignment.",
      "backend/app/api/routes/observability.py:80-108 stores aircraft-linked user feedback."
    ],
    "impact": "A former tenant participant could retain access to aircraft-linked operational or user-authored data.",
    "requiredClosure": "Require current aircraft/organization authority for tenant-bound records, actor-only fallback for personal unbound rows, authoritative workflow joins, and revocation tests.",
    "closureEvidence": [
      "decision.md:192-200 defines current-visibility scoping, limited personal fallback, and fail-closed workflow resolution.",
      "decision.md tenant ACL tests require membership and assignment revocation coverage.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-004",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Invitation roles map exactly to existing organization and membership authorization domains.",
    "summary": "Initial owner/maintenance token roles did not match owner_admin/maintenance_admin application checks.",
    "evidence": [
      "frontend owner and maintenance checks use owner_ and maintenance_ role prefixes.",
      "backend/app/scripts/seed_dev.py:214-219 uses owner_admin and maintenance_admin with owner and maintenance_shop organization types."
    ],
    "impact": "A valid invite could create a user unable to perform the intended pilot workflow or with an ambiguous authority domain.",
    "requiredClosure": "Close the exact owner_admin/owner and maintenance_admin/maintenance_shop mapping and reject all other pairs.",
    "closureEvidence": [
      "decision.md specifies the exact allowed mappings and fail-closed behavior.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-DESIGN-005",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Pilot browser mutations traverse one origin/CSRF/WAF/correlation boundary.",
    "summary": "The Next development proxy forwarded cookies/body while dropping security and correlation context.",
    "evidence": [
      "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts:18-44 forwards cookie and body but not Origin, Referer, or correlation headers."
    ],
    "impact": "The alternate proxy path could bypass the proposed request controls and fragment evidence.",
    "requiredClosure": "Disable the proxy in pilot and use one direct same-origin API path; retain implementation proof.",
    "closureEvidence": [
      "decision.md:180-191 requires exact origin enforcement, direct /api/v1 calls, and pilot-unavailable /api/backend proxy.",
      "adversarial-design-initial.md records independent acceptance of the corrected design."
    ]
  },
  {
    "id": "T082-DESIGN-006",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Emergency session invalidation revokes already-issued opaque database sessions.",
    "summary": "The original design incorrectly claimed rotation of an unused session secret would invalidate sessions.",
    "evidence": [
      "backend/app/core/security.py:38-43 creates random tokens and unsalted SHA256 hashes without the configured secret.",
      "backend/app/api/deps.py:22-35 relies on database revocation and expiry."
    ],
    "impact": "An operator could believe sessions were revoked while existing cookies remained valid.",
    "requiredClosure": "Use audited per-user/global database revocation and remove the unused secret from the pilot contract; retain implementation proof.",
    "closureEvidence": [
      "decision.md:282-287 and 416-419 define database revocation and reject secret rotation as evidence.",
      "adversarial-design-initial.md records independent acceptance of the corrected design."
    ]
  },
  {
    "id": "T082-DESIGN-007",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Achievement names and success predicates state only what the current authoritative workflow has actually completed.",
    "summary": "The proposed ocr_review_completed milestone fired after page order/completeness verification even when mandatory low-confidence corrections remained.",
    "evidence": [
      "backend/app/api/routes/ingestion.py:390-399 sets verification_status verified but may leave job.status awaiting_ocr_corrections."
    ],
    "impact": "Pilot reporting could count OCR review as complete while the user still had required correction work.",
    "requiredClosure": "Either require all mandatory corrections or name the milestone as page review only and state that it does not prove correction completion.",
    "closureEvidence": [
      "decision.md version-1 achievement table uses page_review_completed and explicitly disclaims completion of low-confidence corrections.",
      "design-remediation-1.md records the semantic correction without adding a new workflow.",
      "adversarial-design-closure-1.md independently verifies design closure."
    ]
  },
  {
    "id": "T082-A-001",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every pilot V4 route-family request is rejected before authentication, request-body parsing, or CORS handling using the same decoded path authority as the router.",
    "summary": "Reparsing request.url.path truncates decoded question-mark and fragment characters, allowing encoded delimiter requests to reach V4 authentication.",
    "evidence": [
      "GET /api/v1/ads/directives/id%3Fquery/v4/candidate-proposals reached an injected authentication sentinel.",
      "The %23fragment variant also reached authentication, while the ordinary path returned the generic 404."
    ],
    "impact": "A pilot request can enter unfinished V4 authentication or validation despite the claimed release boundary.",
    "requiredClosure": "Use the decoded ASGI scope path with deliberate root-path handling and independently verify encoded-delimiter, authentication-sentinel, body-read-sentinel, and preflight cases.",
    "closureEvidence": [
      "backend/app/main.py classifies starlette._utils.get_route_path(request.scope), matching router decoding and root-path handling.",
      "backend/tests/test_pilot_release_boundary.py covers %3F/%23 authentication sentinels, preflight, mounted decoded paths, and a body-read sentinel.",
      "package-a-remediation-1.md records 23 focused passing tests.",
      "adversarial-implementation-package-a-remediation-1.md records an independent 378-case raw-ASGI matrix with zero authentication or body reads."
    ]
  },
  {
    "id": "T082-A-002",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "fixed_pending_verification",
    "invariant": "The release verifier proves the exact executed, complete, acyclic migration graph approved for the pilot candidate.",
    "summary": "First-assignment parsing and head set subtraction accept later metadata overrides and disconnected migration cycles.",
    "evidence": [
      "Appending a second revision assignment to the committed 0029 migration still produced a passing 0029 head.",
      "A disconnected two-revision cycle beside the expected head also preserved the expected head and passed."
    ],
    "impact": "An unreviewed executed migration identity or invalid graph can receive a false release-boundary pass.",
    "requiredClosure": "Independently verify the approved sealed-context builder, exact Git/mode/hash/output manifest, and execution-backed import oracle; retain candidate-commit and Package E immutable-image/task acceptance gates.",
    "closureEvidence": [
      ".ai/pilot-release-boundary-v1.json binds the exact 29 approved migration source paths and blob hashes.",
      "scripts/verify_pilot_release_boundary.py rejects inventory/blob drift, duplicate metadata, missing predecessors, duplicate predecessors, and graph cycles.",
      "backend/tests/test_pilot_release_boundary.py mutates actual 0029 content and constructs a disconnected cycle; both fail.",
      "package-a-remediation-1.md records 23 focused passing tests and an explicit HEAD check with all 29 revision blobs matched.",
      "adversarial-implementation-package-a-remediation-1.md shows the remaining unbound SQL/configuration and Git-quoted path gaps; the finding is not closed.",
      "package-a-remediation-2.md binds 44 authority inputs including the whole migration directory, Alembic configuration, and env.py repository import closure; the exact Package A config target amendment is recorded.",
      "The verifier now compares raw NUL-delimited Git names as bytes and requires all four graph metadata declarations, a complete acyclic single-root graph, the separate head, and protected model checks.",
      "Remediation 2: 124 dependency-relevant tests pass, including candidate authority addition/removal/rename/content drift and quoted/tab/newline/UTF-8/non-UTF-8 names under migration and excluded T081 prefixes; Python compilation and diff checks pass.",
      "HEAD correctly fails only for the intentionally target-bound config.py; the mocked target candidate passes. Eventual reviewed candidate-commit verification and independent finding verification remain required.",
      "adversarial-implementation-package-a-remediation-2.md proves backend/psycopg.py and backend/psycopg/__init__.py can execute through engine_from_config while the 44-file verifier passes; implementation paused after the third loop.",
      "package-a-authority-architecture-amendment.md replaces import-name enumeration with a sealed context assembled only from reviewed Git blobs.",
      "adversarial-authority-architecture-amendment.md independently passes the architecture and records the required implementation evidence; implementation may resume but the finding remains open.",
      "package-a-remediation-3.md records the sealed 44-file context plus deterministic manifest, exact commit/blob/mode checks, exclusive no-symlink creation, read-only integrity verification, and simplified source-verifier responsibility.",
      "Actual Alembic env.py and SQLAlchemy engine_from_config select injected psycopg module/package sentinels in vulnerable controls, while sealed controls load canonical installed psycopg with no checkout source on sys.path and no database connection.",
      "Remediation 3 evidence: 292 boundary cases and 16 existing V4 API cases pass; compilation and diff checks pass. Runtime database configuration is required, dotenv/bytecode disabled, and child secret output suppressed. Independent implementation verification and later candidate/image/task gates remain required."
    ]
  }
]

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md`

size=5778; sha256=a34e97448b435bda1e6e5f5b3f78f2e734d8c270a2fbb62839a70ef35753f315

```text
# T082 AWS invite pilot — independent design review

Outcome: **FAIL — changes required**

The pilot boundary is viable, but the initial design did not yet close paid OCR
attempt durability, fresh-database initialization, or revocation-safe telemetry.
Implementation must not begin until the amended design is independently
verified.

## Findings

### T082-DESIGN-001 — High — paid OCR attempts are not durable or replay-safe

The current ingestion transaction flushes an OCR attempt without committing it
before calling the provider, Textract Start has no stable idempotency token, the
JobId exists only in memory during polling, and the worker automatically selects
failed jobs. A crash or timeout after AWS accepts work can therefore create a
second paid submission while losing the first local cost record. Failed attempts
are also excluded from the current billing summary.

Required closure: specify and later prove durable pre-call attempt identity,
serialized claiming, stable provider idempotency, retained JobId, explicit
ambiguous-outcome reconciliation, and operational cost visibility for
failed/unknown attempts. A serialized operator path is acceptable for the pilot;
a full billing platform is not required.

Evidence:

- `backend/app/services/ingestion.py:90-120,238`
- `backend/app/services/ocr_provider.py:353-362`
- `backend/app/workers/ocr.py:10-15`
- `backend/app/services/ocr_billing.py:42-44`
- `backend/tests/test_ocr_billing.py:305-358`

### T082-DESIGN-002 — High — fresh-database initialization is incomplete

The initial migration creates the logbook-section table but not the required
airframe/engine/propeller rows. Manual and OCR-derived entry paths require those
rows. The only current population path is the development seed, which also
creates a platform administrator with a public demo password. The invitation
design intentionally cannot create the first platform administrator.

Required closure: define an idempotent non-demo reference bootstrap and a
separate auditable first-platform-admin bootstrap with securely supplied
credentials. Prohibit `seed_dev.py` in pilot and prove the full workflow on a
fresh migrated database.

Evidence:

- `backend/app/db/migrations/versions/20260617_0001_initial_schema.py:45-53`
- `backend/app/api/routes/logbook_entries.py:41-44,235`
- `backend/app/services/ingestion.py:308-311`
- `backend/app/scripts/seed_dev.py:19-35,209-224`

### T082-DESIGN-003 — High — actor-based telemetry can survive tenant revocation

Authorship cannot restore access to an aircraft-bound event or feedback record
after the user's organization membership or aircraft assignment becomes
inactive. Generic workflow identifiers also need an authoritative parent join;
unknown workflow types must fail closed.

Required closure: require current aircraft visibility for aircraft-bound rows,
current organization authority for organization-bound rows, and allow actor-only
fallback solely for personal rows without a tenant subject. Add membership and
assignment revocation cases.

Evidence:

- `backend/app/api/routes/aircraft.py:51-70`
- `backend/app/api/routes/observability.py:80-108`

### T082-DESIGN-004 — Medium — invitation role mapping was not aligned to existing roles

The original `owner`/`maintenance` invite-role names did not match frontend and
backend authorization conventions. The accepted mapping must be exact:
`owner_admin` in an `owner` organization and `maintenance_admin` in a
`maintenance_shop` organization; all other pairs fail closed.

Evidence:

- `frontend/paprnav-frontend/src/app/(authenticated)/logbook/[nNumber]/page.tsx:98-100`
- `frontend/paprnav-frontend/src/app/(authenticated)/logbook/page.tsx:69-73`
- `backend/app/scripts/seed_dev.py:214-219`

### T082-DESIGN-005 — High — public Next proxy bypassed the proposed request boundary

The development proxy forwards cookies and request bodies but drops
Origin/Referer and correlation headers. The amended design closes the design gap
by disabling `/api/backend/*` in pilot and using one direct same-origin
`/api/v1/*` public API path. Implementation proof remains required.

Evidence: `frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts:18-44`.

### T082-DESIGN-006 — High — session-secret rotation did not revoke sessions

Current sessions use random bearer tokens hashed in PostgreSQL; the configured
session secret is not part of creation or verification. The amended design
correctly replaces the false rotation claim with audited per-user/global
database revocation and removes the unused secret from the pilot contract.
Implementation proof remains required.

Evidence:

- `backend/app/core/security.py:38-43`
- `backend/app/api/deps.py:22-35`

## Bounded limitations and prerequisites

- Stateless invitations are proportionate for ten users when lifetime,
  normalization, atomic acceptance, delivery, and signing-key rotation are
  explicit. Per-invite revocation, Cognito, self-service recovery, HA, private
  task NAT, and a full billing platform need not block the pilot.
- The release must take committed migration head `20260913_0029` and exclude the
  untracked 0030 migration together with the modified T081 model work.
- Live AWS prerequisites, DNS/certificate ownership, budget recipient,
  application-role grants, and restore/rollback remain release gates.
- Achievement success predicates and deduplication identities must be explicit
  before implementation.

## Model routing

- Reviewer runtime identity: `/root/t082_pilot_design_adversary`
- Model: model not exposed by runtime
- Effort: effort not exposed
- Trigger: authorization, deployment authority, paid-provider retries, and
  rollback design.

The reviewer made no repository edits and performed no cloud mutation.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md`

size=4092; sha256=2909b5b0e14af10e41eb6a7b762df28e47f3d91c16c35627db8064e375f31506

```text
# T082 design remediation 1

This amendment responds to the failed independent design review in
`adversarial-design-initial.md`. It changes design only; no product,
infrastructure, migration, or cloud state has been implemented.

## Finding dispositions

### T082-DESIGN-001 — fixed pending independent verification

The design now commits a single OCR attempt intent before a paid provider call,
uses a stable provider idempotency token, serializes the job claim, records the
Textract JobId before polling, resumes rather than resubmits, and sends unknown
outcomes to explicit reconciliation. Failed/unknown attempts remain visible to
operational cost reporting. Crash points and competing-worker cases are in the
test boundary. This is a bounded durable-attempt protocol, not a general billing
platform.

### T082-DESIGN-002 — fixed pending independent verification

Fresh deployment now has separate idempotent reference-data and first-platform-
admin bootstrap phases. Reference bootstrap creates only the canonical
airframe/engine/propeller sections. First-admin bootstrap accepts explicit
identity and securely supplied password, fails once an active platform admin
exists, and never invokes `seed_dev.py`.

### T082-DESIGN-003 — fixed pending independent verification

Aircraft-bound telemetry always requires current aircraft visibility, including
for the author. Organization-bound rows require current organization authority.
Actor fallback is limited to personal rows with neither aircraft nor
organization. Generic workflow rows are admin-only until an authoritative
parent resolver proves current aircraft visibility. Revocation is an explicit
negative test.

### T082-DESIGN-004 — fixed pending independent verification

The invitation domain is exactly `owner_admin` + `owner` or
`maintenance_admin` + `maintenance_shop`. Signing and acceptance reject every
other role/type pair. The acceptance packet covers owner assignment and
maintenance access.

### T082-DESIGN-005 — design closed; implementation proof retained

Pilot browsers use direct same-origin `/api/v1/*`. The Next development proxy
is unavailable in pilot, leaving one WAF/origin/correlation boundary. The
implementation family must prove both sides.

### T082-DESIGN-006 — design closed; implementation proof retained

The unused session-secret claim was removed. Emergency invalidation is an
audited database operation updating existing opaque sessions per user or
globally. The implementation family must prove an already-issued cookie fails
after revocation.

## Additional reviewer question resolved

Achievement version 1 now defines six exact server-side success points and a
reporting identity `(taxonomy-version, event-type, subject-type, subject-id)`.
Events are written in the same transaction as their successful domain object;
reports count each identity once. Client assertions, navigation, and status
labels alone are not achievements. The page-verification milestone is named
`page_review_completed`, not `ocr_review_completed`, because current page
verification may correctly leave a job awaiting mandatory OCR corrections.

The provider remediation also freezes the entire Start request, including the
exact S3 object version, and permits idempotent Start recovery only for six days
from intent creation after operator reconciliation and only with identical
frozen parameters. At or after that conservative deadline, or when intent age
or parameters are unknown, provider state remains reconciliation-required and
cannot call Start as recovery.

## Scope discipline

The remediation does not add Cognito, a mail provider, a general analytics
platform, persistent invitation history, customer charging, high availability,
or the T081 0030 acceptance work. It preserves the dirty T081 tree and the cloud
mutation gate.

## Model routing

- Remediation coordinator: model not exposed by runtime (effort not exposed).
- Trigger: first substantive design-review failure involving paid-provider
  idempotency, bootstrap authority, tenant revocation, and alternate public
  request paths.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md`

size=2888; sha256=78442e342fb36fb3732cc95d7e9e77f49842b3a5e35dffe49c920c6e2d496018

```text
# T082 AWS invite pilot — independent design closure 1

Outcome: **PASS**

No unresolved design blocker, high, or medium finding remains. All seven design
findings are closed at the design stage; implementation and deployment evidence
remain mandatory.

The reviewer verified the held packet with scope fingerprint
`2baf9dad894d45e401a2db84afe312e23e05fccdf35e330e491aa995be19a3c9`.
The authoritative local manifest records generation at
`2026-09-19T15:38:26+00:00`, and local packet verification returned
`review packet is current`.

## Finding closure

- **T082-DESIGN-001 — PASS.** The design requires committed intent, serialized
  claim, frozen complete provider request/S3 object version, retained JobId,
  failed/unknown exposure reporting, and explicit reconciliation. Same-token
  recovery is operator-authorized and stops before Textract's seven-day
  idempotency/result window.
- **T082-DESIGN-002 — PASS.** Separate first-admin and idempotent reference-data
  bootstrap closes the missing-section and development-seed credential hazards;
  fresh-database acceptance covers manual/OCR entry creation and reruns.
- **T082-DESIGN-003 — PASS.** Current aircraft/organization authority governs
  tenant rows, personal fallback is narrow, unresolved workflow parents fail
  closed, and revocation cases are explicit.
- **T082-DESIGN-004 — PASS.** Invitation mappings are exactly
  `owner_admin`/`owner` and `maintenance_admin`/`maintenance_shop`.
- **T082-DESIGN-005 — PASS.** Pilot traffic uses direct same-origin API routing
  and the Next development proxy is unavailable, yielding one public WAF,
  origin, correlation, and authorization path.
- **T082-DESIGN-006 — PASS.** Database session revocation replaces the invalid
  session-secret rotation claim and retains existing-cookie rejection as an
  implementation oracle.
- **T082-DESIGN-007 — PASS.** `page_review_completed` accurately describes page
  order/completeness without claiming OCR-correction completion, and all six
  achievements have transactional success/deduplication identities.

Stateless invitations, manual out-of-band code delivery, public-subnet Fargate
with ALB-only inbound access, and deferred Cognito/HA/full billing remain bounded
pilot decisions rather than missing design closure.

This pass does not authorize cloud execution. Live AWS prerequisites,
DNS/certificate selection, budget recipient, RDS migration/app-role checks,
secure-cookie behavior, restore/rollback, paid-provider crash tests, and tenant
authorization tests remain release gates.

## Model routing

- Reviewer runtime identity: `/root/t082_pilot_design_adversary`
- Model: model not exposed by runtime
- Effort: effort not exposed
- Trigger: independent closure after substantive authorization,
  provider-retry, and deployment findings.

The reviewer made no repository edits and performed no cloud mutation.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md`

size=4889; sha256=083b635357b9e0e3f79eed2e407216907459f504aef7ba2c1946dbed8381bcf4

```text
# Package A implementation: pilot release boundary and V4 route gate

## Scope

This package implements only the approved Package A boundary. It does not
implement invitations, session/CSRF changes, telemetry authorization, pilot
instrumentation, paid OCR, AWS runtime changes, or deployment. It preserves
the active T081 working tree and excludes its unreviewed 0030 artifacts from a
pilot release commit.

Changed scope:

- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/.env.example`
- `backend/tests/test_pilot_release_boundary.py`
- `.ai/pilot-release-boundary-v1.json`
- `.ai/PILOT_RELEASE_BOUNDARY.md`
- `scripts/verify_pilot_release_boundary.py`
- `scripts/build_pilot_migration_context.py`

## Implemented invariants

1. `PAPRNAV_ENV=pilot` defaults the pilot-wide V4 route gate to false.
2. Pilot startup rejects the route gate or any existing V4 capability flag
   when enabled.
3. Every path in the `/api/v1/ads/**/v4/**` family returns the same generic 404
   before routing, authentication, or body parsing when the gate is false.
   The boundary is outside CORS, so preflight requests cannot bypass it.
4. Local/test behavior remains unchanged by default.
5. The release verifier inspects an explicit Git commit tree, not the dirty
   working directory. It checks baseline ancestry, the complete reviewed
   44-file migration authority, the single reviewed migration head, the
   reviewed `core.py` blob hash, and excluded 0030/T081 paths.
6. The migration-context builder copies only those exact reviewed Git blobs
   into a sealed, read-only context, verifies its complete inventory and bytes,
   and launches Alembic locally with an isolated interpreter and explicit
   database selection.
7. Neither tool writes Git state, mutates AWS, grants deployment authorization,
   or claims the later image/task controls.

## Deterministic evidence

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_release_boundary.py`
  - 292 passed after remediation 3.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_ad_v4_api.py`
  - 16 passed.
- `python3 scripts/verify_pilot_release_boundary.py --ref HEAD`
  - expected fail with exactly the target-bound Package A `config.py` mismatch;
    the old `HEAD` predates Package A. All other 43 authority hashes, migration
    head `20260913_0029`, protected model hash, and exclusions passed. A mocked
    target candidate passed all 44 hashes.
- Python compilation of all changed Python files passed.
- `git diff --check` passed.

The focused route test binds the expected OpenAPI inventory of 18 V4 method and
path pairs, exercises every pair with malformed JSON and no authentication,
checks ordinary and encoded-delimiter CORS preflight, uses authentication and
body-read sentinels against decoded and mounted paths, checks every forbidden
setting independently, and proves `/health` remains available. Negative
release checks cover protected-blob drift, candidate migration-content drift,
migration-head drift, duplicate metadata, disconnected cycles, and exact/prefix
exclusions. The exact 44-file authority covers the full migration tree,
Alembic configuration, and `env.py` repository import closure, with raw
NUL-delimited byte-safe Git path handling. The execution oracle proves that
checkout-level `psycopg.py` and `psycopg/__init__.py` sentinels execute in the
vulnerable control but cannot enter the sealed context; the sealed run loads
the installed driver through actual Alembic and SQLAlchemy import paths without
connecting to a database.

## Residual limits and next gate

- `HEAD` is still the pre-Package-A baseline because the task commit gate is
  closed. The verifier must be rerun against the eventual reviewed candidate
  commit before image construction.
- Image digests, enabled providers, and the full deployment manifest belong to
  the later AWS execution package; this boundary is necessary but not
  sufficient release evidence.
- No claim is made that T081 or migration 0030 is complete.
- Package B must not start until an independent implementation adversary passes
  this complete family and all findings are dispositioned.

## Model routing

- Builder runtime identity: `/root`.
- Builder model: `model not exposed by runtime`.
- Builder effort: `effort not exposed`.
- Preferred routing was GPT-5.6 Sol high because this is coherent multi-file
  implementation under an approved design. A bounded Sol subagent allocation
  was attempted, but the repository subagent thread limit prevented it. The
  coordinator acted as the closest available implementation fallback.
- Required implementation reviewer: separate read-only GPT-6 Astra high
  subagent at the complete Package A boundary. Actual model and effort must be
  recorded from the returned runtime metadata; if unavailable, record the
  mandated unexposed wording.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md`

size=3670; sha256=e49b39910551c7199ff4f2b61e75de0bf018205c022ea4da2c70eeca2eab35a8

```text
# T082 Package A independent implementation review

## Outcome

**FAIL.** Existing tests pass, but independent counterexamples disprove the
route and migration-verifier guarantees. Two high-severity findings remain
open.

## Findings

### T082-A-001 — High: reconstructed URL parsing bypasses the V4 boundary

`backend/app/main.py` checks `request.url.path`, while routing uses the decoded
ASGI scope path. Requests to
`/api/v1/ads/directives/id%3Fquery/v4/candidate-proposals` and the `%23fragment`
variant reached an injected authentication sentinel. Both returned
`500 / AUTH_REACHED`; the ordinary path returned the generic 404 without
invoking authentication.

An encoded `?` or `#` becomes part of the decoded identifier, then URL
reconstruction/reparsing truncates the path before `/v4/`. The router still
sees the decoded segment. Pilot requests can therefore enter authentication or
validation despite the route boundary.

Required remediation: classify the router's decoded scope path, handle
`root_path` deliberately, and add encoded-delimiter negative tests using
authentication and body-read sentinels, including preflight.

Finding family: canonicalization mismatch at the route-authority boundary and
a missing negative oracle.

### T082-A-002 — High: migration verification does not establish the executed graph

`scripts/verify_pilot_release_boundary.py` accepts the first literal metadata
assignment and calculates heads using set subtraction without detecting cycles.
An in-memory committed 0029 migration blob with an appended
`revision = "unreviewed_revision"` still passed as head `20260913_0029`, even
though Python executes the later assignment. A disconnected two-revision cycle
beside the expected head also returned the expected head.

A candidate with different executed metadata or an invalid migration graph can
therefore receive a release-boundary pass.

Required remediation: bind the complete migration inventory and blob hashes to
the approved baseline, requiring an explicit policy amendment for migrations,
or implement strict single-assignment metadata validation plus complete
acyclic-graph validation. Add candidate-content negative tests; changing only
the expected policy value is insufficient.

Finding family: release-authority/oracle mismatch.

## Verification and inspected scope

- Focused boundary plus existing V4 API tests: 34 passed.
- Current packet verifier and explicit `HEAD` verification passed for the
  baseline.
- `HEAD^` correctly failed ancestry, model-blob, and migration-head checks.
- `git diff --check` passed.
- Independent encoded-path/auth-sentinel and migration-metadata probes produced
  the counterexamples above.

The reviewer inspected all seven Package A files, the implementation artifact,
packet and bound inputs, staged/unstaged/untracked inventory, API router and V4
handlers, configuration consumers and service gates, database session/test
setup, committed migration metadata, and preserved T081 differences. No files
were edited or staged.

The documentation correctly says `HEAD` predates Package A and that verification
must run against the eventual reviewed candidate. Passing this check is
explicitly insufficient for deployment approval.

## Model routing

- Builder runtime identity: `/root`.
- Builder model: `model not exposed by runtime`.
- Builder effort: `effort not exposed`.
- Reviewer runtime identity: `/root/t082_pilot_design_adversary`.
- Reviewer model: `model not exposed by runtime`.
- Reviewer effort: `effort not exposed`.
- Routing trigger: independent implementation review of feature isolation and
  release/migration authority; GPT-6 Astra high was requested.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md`

size=2538; sha256=6ca96fdc41f658ec35d7170daa3fe2f1a832bfa35159046a6ba01a679b497a25

```text
# Package A remediation 1

## Finding classes

The first implementation review failed on two high-severity missing-oracle
classes, not isolated counterexamples:

- `T082-A-001`: canonicalization mismatch at the route-authority boundary.
- `T082-A-002`: release-authority and migration-oracle mismatch.

## Remediation

The route boundary now classifies `starlette._utils.get_route_path(scope)`, the
same decoded ASGI path authority used by the Starlette router. This avoids
reconstructing and reparsing a URL after percent decoding and deliberately
accounts for mounted `root_path`. The boundary remains outside CORS.

The negative oracle now covers both `%3F` and `%23` path delimiters, CORS
preflight, an injected authentication sentinel, and a raw ASGI request whose
receive callable fails if any code reads the body. A mounted decoded path is
included.

The release verifier now binds the exact 29-file migration source inventory and
SHA-256 of every approved migration blob. Any source addition, removal, rename,
or byte change requires a reviewed policy amendment. Independently of the hash
binding, metadata must have exactly one module-scope assignment, predecessor
references must exist, duplicate predecessors are rejected, and a full graph
walk rejects cycles even when they are disconnected from the expected head.

The negative oracle modifies the actual 0029 candidate content in memory by
appending a second executed revision assignment and proves both blob drift and
duplicate metadata fail. A separate synthetic disconnected cycle must also
fail.

## Verification

- Package A boundary tests: 23 passed.
- Existing V4 API tests: 16 passed.
- Explicit `HEAD` verifier: pass, 29 migration blobs matched, head
  `20260913_0029`, protected model blob matched, no excluded committed paths.
- Changed Python compilation: pass.
- `git diff --check`: pass.

The verifier still evaluates the pre-Package-A `HEAD` until the task's commit
gate opens. It must be rerun against the eventual reviewed candidate commit;
the documentation retains that limitation.

## Model routing

- Remediation builder runtime identity: `/root`.
- Builder model: `model not exposed by runtime`.
- Builder effort: `effort not exposed`.
- Trigger: first substantive implementation-review failure; reasoning was
  escalated and each finding was reframed as an invariant/oracle class.
- Required verifier: `/root/t082_pilot_design_adversary`, requested GPT-6 Astra
  high, read-only. Actual model and effort must be recorded as exposed by that
  runtime.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md`

size=3043; sha256=acb6475c569a5314f30ecd8901795488d53695125f6d2fd7c5b60d6c5f3f23c3

```text
# T082 Package A remediation-1 implementation review

## Outcome

**FAIL.** `T082-A-001` is independently verified closed. `T082-A-002`
remains high because the release-authority inventory is incomplete and Git path
parsing can omit authority inputs.

The reviewed packet SHA-256 was
`eb9eaac17d3c9c8225b876762fc7a8ed8dcb45afee9b86a4616b8bf79f5f92da`;
packet verification passed.

## T082-A-001 disposition

**Closed.** The middleware and the installed Starlette/FastAPI router use the
same `get_route_path(scope)` authority. An independent 378-case raw-ASGI matrix
covered methods, decoded delimiters, mounted and unmounted root paths, CORS,
authentication sentinels, and a receive callable that fails on body access.
Every gated request returned the generic 404 with zero authentication or body
reads.

## T082-A-002 residual finding

**High — migration authority inventory remains incomplete and path parsing can
omit files.**

- The 29 bound files cover only `versions/*.py`. Migration 0029 reads and
  executes `backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql`;
  0028 executes two further SQL sidecars. Changes to the 0029 SQL,
  `backend/app/db/migrations/env.py`, and `backend/alembic.ini` all passed because
  they are outside the current inventory.
- `tree_paths()` consumes newline-delimited, Git-quoted names without decoding.
  Synthetic quoted names containing a tab under the migrations and excluded
  T081 prefixes both passed because the leading quote defeated prefix matching.

Required closure: define and bind the complete migration authority set,
including executable sources/sidecars and Alembic invocation configuration;
enumerate tree names with NUL-delimited raw output; test addition, removal,
rename, content drift, and escaped/non-ASCII names across the complete set.

This is the second substantive failure in the release-authority/oracle family.
Repository routing policy therefore requires an Astra xhigh remediation pass
and prohibits counterexample-by-counterexample patching.

## Verification and limits

- Package A plus existing V4 API tests: 39 passed.
- Revision content drift, duplicate/nested metadata, revision
  addition/removal/rename, malformed/duplicate/missing predecessors, and cycles
  were rejected.
- All Package A files, review inputs, working-tree inventory, routing
  implementation, migration consumers, and Alembic configuration were
  inspected.
- `HEAD` remains the pre-Package-A baseline; later candidate verification and
  deployment gates are still required.
- No files were edited, staged, committed, or deployed by the reviewer.

## Model routing

- Builder identity: `/root`; model `model not exposed by runtime`; effort
  `effort not exposed`.
- Reviewer identity: `/root/t082_pilot_design_adversary`; model
  `model not exposed by runtime`; effort `effort not exposed`.
- GPT-6 Astra high was requested for the remediation verification.
- Trigger: independent review of route canonicalization and migration
  authority after a prior substantive failure.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md`

size=5758; sha256=41827e83574a0c82cbc3d6fa5360b9e7c1498242018f7099bd80ae13fb2cd7f6

```text
# Package A remediation 2: complete migration authority

## Invariant and scope

`T082-A-002` is a release-authority/oracle gap. A candidate can pass only when
its complete repository migration authority inventory and bytes equal the
reviewed target, its entire revision graph is valid, and its separately bound
head/model/exclusion checks pass. This remediation closes that family together;
it does not change the already-closed route behavior.

Changed files are the release verifier, its JSON policy and operator document,
the focused boundary tests, this artifact, and the T082 findings ledger.
No T081 file, model source, migration source, Git index/commit, or cloud resource
was edited by this builder.

## Authority and provenance

The policy now binds exactly 44 files: every committed file beneath
`backend/app/db/migrations/` (including 29 revisions, three executable SQL
sidecars, environment, template, README, and placeholder), `backend/alembic.ini`,
and the complete repository import closure executed by `env.py`:
`app/core/config.py`, `app/db/base.py`, `app/models/core.py`, and four package
initializers. This closure was traced through the committed environment,
revision imports/read calls, configuration loader, and model imports. The
directory inventory deliberately has no extension filter, so new SQL, JSON,
templates, configuration, bytecode, or unknown sidecars require review.

All hashes are read from baseline commit
`19fe8e2e170687ed65deed78cb1af99d60f601e9` except the exact Package A target
configuration bytes, SHA-256
`482af947a0fe1cd31a9974b634435dccf7041b50903ae365e365c20507a07f0d`.
The coordinator explicitly directed this target amendment because `env.py`
imports the configuration containing the already implemented pilot gate. The
policy records the amendment; it remains subject to the independent Package A
implementation pass. It is not an exemption for arbitrary configuration drift.

New dotenv input, replacements for direct-import modules/packages, and
imported-package bytecode are also classified as authority and rejected as
unapproved additions. External Python package contents and deployment/container
execution configuration remain the later immutable-image/migration-task
boundary; no site-package dependency crawl is claimed. The operator document
states the reviewed invocation and forbids treating this source check as proof
of the packaged/runtime environment.

Git inventory uses `git ls-tree -rz --name-only`. Names remain bytes for all
authority/exclusion comparisons and blob lookup. JSON-facing names use
`surrogateescape`; ASCII-escaped JSON preserves tabs, newlines, quotes,
backslashes, UTF-8, and non-UTF-8 bytes without lossy decoding.

The graph independently requires one literal module-level assignment for each
of `revision`, `down_revision`, `branch_labels`, and `depends_on`. The approved
graph has no branch aliases or dependency edges, so non-null values fail
explicitly. Duplicate revisions/predecessors, malformed or missing
predecessors, empty predecessor sequences, cycles in any component, and
multiple roots fail. The separate expected head remains `20260913_0029`, and
`core.py` retains its separate protected-blob comparison.

## Verification

- `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_release_boundary.py backend/tests/test_ad_v4_api.py`:
  **124 passed** (108 boundary cases and 16 existing V4 API cases).
- The positive mocked candidate uses real committed baseline blobs plus the
  actual Package A configuration bytes and passes all 44 authority hashes.
- Candidate-content negatives cover removal, rename, and executable byte drift
  for Alembic configuration/environment/template, all SQL sidecars, a revision,
  configuration/base/model imports, and every loaded package initializer.
- Candidate-tree additions cover revisions, SQL, JSON, unknown sidecars,
  configuration/templates, dotenv, import replacement packages/modules, and
  bytecode. Raw Git output negatives cover quotes, backslashes, tabs, newlines,
  UTF-8 and non-UTF-8 names beneath both migration authority and excluded T081
  prefixes; JSON round trips remain valid.
- Synthetic candidate revision sources exercise 16 graph/metadata corruption
  cases, retaining the disconnected-cycle and duplicate/nested-assignment
  regressions from remediation 1.
- `python3 scripts/verify_pilot_release_boundary.py --ref HEAD`: expected
  **fail**, exit 1, with exactly one error for the old committed
  `app/core/config.py`; all 43 remaining hashes, the graph/head, protected model,
  and exclusions pass. This supersedes the historical HEAD-pass evidence in
  remediation 1. The eventual reviewed candidate commit must pass before image
  construction; no candidate commit was created here.
- Changed verifier/test Python compilation: pass. `git diff --check`: pass.

Existing FastAPI/Starlette deprecation and dirty-tree ORM teardown warnings
remain; no new test failure occurred. `T082-A-002` is
`fixed_pending_verification`, not closed. Independent verification belongs to
`/root/t082_pilot_design_adversary`.

## Model routing

- Builder runtime identity: `/root/t082_package_a_migration_authority`.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Trigger: second substantive failed review in the release-authority/oracle
  family; complete invariant remediation and focused verification. Repository
  policy requests GPT-6 Astra xhigh for this phase; the runtime does not expose
  actual model/effort metadata, so none is inferred.
- Independent reviewer assignment retained by coordinator:
  `/root/t082_pilot_design_adversary`; this builder performed no independent
  review or closure attestation.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md`

size=2715; sha256=852c434b41b2c6630dd1a5888ac0211d66933f1c5be0e9a40a135de7ac984b48

```text
# T082 Package A remediation-2 implementation review

## Outcome

**FAIL.** `T082-A-001` remains closed. `T082-A-002` remains high in the
repeated release-authority/oracle family.

Reviewed packet SHA-256:
`513971f42c6a1828b9e98865cd2525082947f87f6d499a4b649008d127337b76`.
All 18 manifest-bound input hashes matched.

## T082-A-002 residual counterexample

A passing candidate must not introduce repository code executed by the
reviewed migration invocation outside the approved authority. The current
import allowlist omits `psycopg`, while `backend/alembic.ini` prepends the
backend directory and SQLAlchemy's `postgresql+psycopg` dialect imports that
DBAPI during `engine_from_config`.

An in-memory candidate preserving all 44 approved hashes plus either
`backend/psycopg.py` or `backend/psycopg/__init__.py` passed without errors. A
read-only normal-`FileFinder` execution probe confirmed that
`engine_from_config` selects the candidate module and executes its sentinel
before connecting to a database.

This is repository import substitution, not an external dependency-version
change. Unreviewed code can execute with migration credentials despite a
release-boundary pass. Adding only the observed module name is insufficient.

Required closure: restate the executable-import boundary and either prevent
repository shadowing or comprehensively bind eligible repository import inputs.
Add an execution-backed candidate regression oracle.

This is the third substantive failure in this family. Implementation must
pause until the missing invariant, architecture boundary, and shared oracle are
recorded and independently reviewed.

## Verified evidence

- `T082-A-001` remained closed under an independent 441-case raw-ASGI matrix;
  every request returned generic 404 with zero authentication or body reads.
- 124 targeted tests passed.
- All 132 content/removal/rename mutations over the 44 authority files and nine
  invalid policy-scope changes were rejected.
- `HEAD` failed exactly the approved config target mismatch; the working-config
  candidate passed; `HEAD^` failed ancestry.
- No other blocker/high finding was found.
- No repository edit, staging, commit, PostgreSQL execution, image, or cloud
  mutation was performed by the reviewer.

## Model routing

- Remediation builder: `/root/t082_package_a_migration_authority`; requested
  GPT-6 Astra xhigh; actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Reviewer: `/root/t082_pilot_design_adversary`; requested GPT-6 Astra xhigh;
  actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Trigger: repeated high-severity release-authority/oracle finding at the third
  review loop.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md`

size=6926; sha256=eb675256176e509132834eb673d3bf7b494e1229d97e32788fa4220416482f51

```text
# Package A architecture amendment: sealed migration execution context

## Why implementation is paused

`T082-A-002` failed three implementation reviews in the same
release-authority/oracle family. The missing invariant is broader than a list
of known imports:

> Code running with migration credentials may execute repository bytes only
> from a sealed, reviewed migration context. No other file from the application
> checkout may be present on its import path or in its filesystem view.

Enumerating names such as `sqlalchemy`, `alembic`, and `psycopg` cannot prove
that invariant because dependencies may add or change transitive imports. No
further implementation is authorized until this amendment is independently
approved.

## Decision

Build and run migrations from a separate sealed context assembled from an
explicit manifest at the exact reviewed Git commit. The context contains only:

- `backend/alembic.ini` with the reviewed `script_location` and
  `prepend_sys_path` behavior;
- every reviewed file beneath `backend/app/db/migrations/`;
- the minimal repository package/import closure required by `env.py`:
  `app/core/config.py`, `app/db/base.py`, `app/models/core.py`, and the required
  package initializers; and
- a generated manifest recording source commit, path, Git mode, byte length,
  and SHA-256 for every context file.

The builder reads blobs from the named Git commit, never from the working tree.
It rejects symlinks, submodules, non-regular modes, duplicate or non-UTF-8
manifest paths, path traversal, and any source/manifest mismatch. The output
directory is newly created and must contain exactly the manifest plus the
listed files. Arbitrary repository files—including `backend/psycopg.py`, any
future driver name, `.env`, bytecode, tests, scripts, and T081/0030 artifacts—
are excluded by construction rather than discovered by import-name rules.

The migration task receives only this context and installed third-party
packages. It runs from the sealed directory with `PAPRNAV_DISABLE_DOTENV=1`, a
database URL supplied at runtime from the separately scoped migration secret,
and an explicit command equivalent to:

```text
python -I -m alembic -c /migration/alembic.ini upgrade 20260913_0029
```

Alembic may add the sealed directory to `sys.path`; that directory cannot
contain an unapproved top-level replacement module. The application checkout
is not copied or mounted into the migration task. The image records the source
commit and context-manifest digest as labels and uses an immutable image digest.

## Boundary by package

Package A resumes only to implement the deterministic context builder,
manifest verifier, and local execution-backed oracle. Package A does not push
an image, contact AWS, or run an AWS migration. Its implementation review must
bind the builder, manifest, policy, tests, and current Package A route gate.

The later AWS/image package must:

- create a dedicated migration image/stage containing the sealed context and
  pinned installed dependencies, but no application checkout;
- prove the image file inventory and labels match the reviewed context manifest
  and exact Git commit;
- run the image by immutable digest with the migration-only database identity;
- prove a fresh disposable PostgreSQL upgrade to `20260913_0029`; and
- record the image digest before any AWS database migration is authorized.

External Python package bytes are owned by that immutable-image boundary, not
by Package A's repository manifest. The source verifier must stop claiming it
proves the complete transitive import closure; it proves the inputs to the
sealed context and the migration graph. The context and later image digest
together prove the execution boundary.

## Shared oracle and exit evidence

One execution-backed oracle governs construction and review:

1. Build twice from the same explicit commit; manifests and file bytes are
   identical.
2. Add arbitrary top-level replacement modules/packages to a synthetic
   candidate tree, including randomized names and known DBAPI/import names.
   Build the context and prove none appears in its inventory or import path.
3. Run a subprocess from the sealed context with the reviewed Alembic config.
   Instrument imports and `engine_from_config`; prove repository sentinels never
   execute and DBAPI/Alembic/SQLAlchemy resolve outside the context.
4. Mutate, remove, rename, add, symlink, or mode-change every manifest class;
   construction or verification fails closed.
5. Prove the migration graph/head, SQL sidecar hashes, protected model hash,
   T081/0030 exclusions, and V4 route/startup gates still pass their existing
   focused oracles.
6. Before image construction, run the release verifier and context builder
   against the exact reviewed candidate commit; a pre-Package-A `HEAD` is not
   release evidence.

The oracle remains bounded by the number of manifest files and mutation
classes. It does not generate combinatorial database rows or broad application
test matrices.

## Alternatives rejected

- **Continue adding import names:** rejected because every new transitive import
  creates another bypass and another review loop.
- **Bind the full repository only:** exact commit identity is necessary release
  provenance, but copying the full checkout still places unrelated modules on
  the privileged import path and creates avoidable review/rework coupling.
- **Install the full application package and remove repository paths:** viable
  later, but the repository has no closed packaging contract today and the full
  application is a larger migration credential surface than the minimal sealed
  context.
- **Rely on `python -I` alone:** insufficient because Alembic's reviewed config
  deliberately adds its script root to `sys.path`; isolation must also control
  the directory contents.

## Failure, rollback, and residual limits

Any manifest, context, commit, graph, image-label, or digest mismatch blocks the
migration task. Rollback selects the prior reviewed image digest only when its
schema compatibility is explicit; this design does not authorize automatic
downgrade. A failed migration leaves ECS service counts at zero until the
operator dispositions it.

This boundary does not authenticate repository reviewers, secure third-party
package provenance by itself, authorize an AWS apply, or close T081. Those
remain review-process and later image/deployment gates.

## Model routing

- Architecture author: `/root`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Requested routing: GPT-6 Astra xhigh after the third unsuccessful invariant
  loop. A new Astra subagent turn was attempted but rejected by the runtime
  thread limit, so no unavailable model is claimed.
- Required reviewer: independent `/root/t082_pilot_design_adversary`, GPT-6
  Astra xhigh requested; implementation remains paused until a pass is recorded.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md`

size=2249; sha256=96e9c47d801d64ed5ca56daa4e2e740c89ec260a2096fad3e82fa6ddb9e83c08

```text
# Independent review: sealed migration authority architecture

## Outcome

**PASS — architecture only.** The amendment replaces the incomplete import-name
blacklist with a sound boundary: arbitrary checkout files never enter the
privileged execution context. Unknown future DBAPI or dependency names cannot
gain authority through repository shadowing.

Reviewed amendment SHA-256:
`eb675256176e509132834eb673d3bf7b494e1229d97e32788fa4220416482f51`.

No architecture blocker/high remains. Implementation is not approved;
`T082-A-002` remains open pending implementation and execution evidence.

## Required implementation evidence

- Define exact source-to-destination mapping, especially
  `backend/alembic.ini` to `/migration/alembic.ini`, while preserving package
  and SQL-relative paths.
- Validate raw Git names, modes, hashes, and exact output inventory without
  following symlinks or reusing an existing destination.
- Include positive controls proving injected modules execute under the
  vulnerable invocation but not the sealed invocation. Preserve actual DBAPI
  loading and check canonical import origins, not only sentinel output.
- Require the migration secret at launch; missing configuration may not fall
  back to development credentials. Secrets stay out of manifests, image layers,
  and diagnostics.
- Preserve context integrity during execution with a read-only context and
  explicit bytecode suppression; `python -I` alone is insufficient.
- The later AWS/image owner must bind interpreter, installed dependencies,
  startup hooks, context, and command to the immutable image/task definition;
  mounts, editable installs, or overrides cannot reintroduce checkout files.

Package A's local oracle proves construction and import isolation, not container
filesystem isolation or PostgreSQL success. Those remain later gates.

## Model routing

- Architecture author: `/root`; actual model `model not exposed by runtime`;
  actual effort `effort not exposed`.
- Reviewer: `/root/t082_pilot_design_adversary`; GPT-6 Astra xhigh requested;
  actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Trigger: independent architecture review after the third repeated
  release-authority/oracle failure.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md`

size=4699; sha256=7b9e87c5e504f19e2b63739c632602876cfebc6447e93cb40da2a43d9e9a2986

```text
# Package A remediation 3: sealed migration context

## Outcome and scope

Implemented the independently approved authority architecture in
`scripts/build_pilot_migration_context.py`, with matching source-verifier,
policy, documentation, and focused-test updates. `T082-A-002` is
`fixed_pending_verification`; this is builder evidence, not independent closure.
No migration/model/T081 source, cloud resource, Git index, or commit was changed.

## Implemented boundary

The builder resolves one exact commit and reads only its Git blobs/modes for
the reviewed 44 inputs. Mapping is exact: `backend/alembic.ini` becomes
`alembic.ini`; approved `backend/app/...` files become `app/...`. Arbitrary
checkout files are excluded by construction. The incomplete import-name
blacklist was removed from the source verifier, which now claims only source
inventory/hash/graph correctness.

Construction rejects missing/hash-drifted inputs, modes other than regular
`100644` blobs, unsafe/non-UTF-8 manifest paths, duplicate names/keys, reused
destinations, and symlink traversal. Exclusive descriptor-based creation writes
44 files plus a canonical manifest with source commit, source/destination paths,
Git mode, byte length, SHA-256, and deterministic manifest digest. Files are
`0444`; directories are `0555`. Verification compares every output byte and the
complete file/directory inventory to the commit/policy, rejecting added,
removed, renamed, mutable, linked, or tampered output.

The local launcher requires nonempty runtime `DATABASE_URL`, forces dotenv
off and bytecode suppression, supplies a minimal environment, and launches
`python -I -B -m alembic` from the verified context with its absolute config and
head `20260913_0029`. Credentials are absent from manifests/arguments, and child
output is suppressed because driver errors may expose URLs. The local wrapper
is not the production task entrypoint.

## Execution-backed oracle

The subprocess executes actual committed `env.py` through Alembic and actual
SQLAlchemy `engine_from_config`. Both a candidate `backend/psycopg.py` and
`backend/psycopg/__init__.py` sentinel execute under the vulnerable checkout
control. Both sealed controls load real installed `psycopg`; canonical driver,
Alembic, and SQLAlchemy origins are inside the interpreter's site-packages and
outside the context. No checkout source/editable path is on `sys.path`.

The installed local environment is under ignored `backend/.venv`; the oracle
allows only its exact canonical site-packages root there. An initial overly
broad path assertion was corrected to express that distinction. The oracle
stops after driver loading, before any database connection, verifies explicit
database selection and disabled dotenv, and leaves the read-only context
unchanged with no bytecode.

## Verification

- Focused boundary suite: **292 passed**. Existing V4 API cases: **16 passed**.
  All 308 distinct final focused cases are green in coordinator verification.
- Matrix includes reproducible double builds, randomized/known replacement
  modules, dotenv/bytecode exclusion, source/output inventory and byte
  mutations, source symlink/submodule/executable/tree modes, output symlinks and
  mode drift, unsafe paths, duplicates, and existing-destination preservation.
- Real baseline Git mode reads pass. Source verifier and context builder reject
  pre-Package-A `HEAD` solely for the intentionally target-bound config blob;
  construction creates no output. Mocked target candidates pass. Exact reviewed
  candidate-commit verification remains mandatory before image construction.
- Changed Python compilation and `git diff --check`: pass. The test finalizer
  now restores permissions on deliberately read-only temporary contexts before
  pytest teardown. Existing FastAPI, Starlette, and SQLAlchemy dependency
  warnings remain; stale cleanup warnings from the earlier interrupted run do
  not represent current test failures.

Package E must prove the immutable image/task, installed dependencies and
startup hooks, read-only mount, absent checkout/mount overrides, runtime secret,
and fresh PostgreSQL upgrade. No container isolation or migration success is
claimed here.

## Model routing

- Builder identity: `/root/t082_package_a_migration_authority`.
- Actual model: `model not exposed by runtime`; actual effort:
  `effort not exposed`.
- Requested routing: GPT-6 Astra xhigh; trigger: implementation and focused
  verification after independent approval of the architecture amendment
  required by the third repeated authority finding.
- Independent reviewer remains `/root/t082_pilot_design_adversary`; no
  independent review or closure was performed by this builder.

```
### `AGENTS.md`

size=2214; sha256=2295cae2d1394c07fe3573d4d790985eb1b85c9a6514a94d851d55337f3fc0cb

```text
# Paprnav agent workflow

## Mandatory model routing

Route every meaningful phase by risk, complexity, and review history according
to [`.ai/MODEL_ROUTING.md`](.ai/MODEL_ROUTING.md). At phase start and whenever
role, model, or effort changes, emit the required model-routing notice. Preserve
builder/reviewer separation, record known assignments in review artifacts, and
apply the documented escalation and fallback rules without silently claiming
an unavailable model.

Use the adversarial review process for changes involving regulatory or safety
semantics, schemas or migrations, authorization, audit evidence, destructive
data operations, provider/billing decisions, infrastructure/IAM, or public API
contracts. Read `.ai/REVIEW_PROCESS.md` and use the repository-local
`adversarial-review` skill.

For qualifying work:

1. Create a review run and write the decision packet before implementation.
2. Use a separate Codex subagent for design review. The builder may not review
   its own work.
3. Resolve design blockers before migrations, contracts, or implementation.
4. Implement one coherent vertical slice at a time.
5. Use a separate Codex subagent to adversarially review every high-risk slice.
6. Use Claude only as an external critic at selected decision boundaries, after
   the Codex adversarial loop has produced a complete review packet.
7. Record every finding and disposition. Do not declare completion while a
   blocker remains open or closure evidence is absent.

The coordinating Codex runtime must create the reviewer assignment and record
the returned reviewer identity; repository scripts cannot authenticate runtime
identity and are not a security boundary. The adversarial reviewer is read-only
unless the coordinator explicitly assigns a later fix task. Reviewers must
inspect staged, unstaged, and untracked files,
plus callers, readers, migrations, administrative scripts, tests, and relevant
contracts. A scope omission is a review finding, not an implicit exclusion.

Claude output is review input rather than authority. The coordinating Codex
agent validates and dispositions each finding as fixed, rejected with evidence,
accepted risk with an owner, or deferred with rationale.

```
### `.ai/MODEL_ROUTING.md`

size=10194; sha256=043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261

```text
# Paprnav model-routing policy

This policy is mandatory for every Codex task in this repository. Route each
meaningful phase independently; do not choose one model for an entire task when
later phases have different risk or review needs.

## Routing tiers

Choose the highest tier triggered by the work. Complexity, safety impact, and
review history override convenience or expected speed.

| Work | Preferred routing |
| --- | --- |
| Mechanical, localized, low-risk edits with an obvious oracle and limited blast radius | GPT-5.6 Luna (`gpt-5.6-luna`) or GPT-5.6 Terra (`gpt-5.6-terra`), medium |
| Coherent multi-file implementation whose design is already approved | GPT-5.6 Sol (`gpt-5.6-sol`), high |
| Schema or migration design; authorization; regulatory or safety semantics; invariant synthesis; adversarial review; closure review | GPT-6 Astra (`gpt-6-astra`), high or xhigh |

Use xhigh for interacting invariants, ambiguous trust boundaries, concurrency or
rollback reasoning, closure after substantive findings, or when high effort has
not resolved the review class. Use high for a well-framed problem with explicit
invariants and a strong test oracle.

Low-risk routing applies only when all of these are true:

- the change is localized and mechanically checkable;
- failure cannot alter authorization, regulatory meaning, safety behavior,
  persisted schema, audit evidence, billing/provider choice, or a public
  contract;
- rollback is straightforward; and
- no review-history escalation below applies.

When a phase mixes tiers, use the highest triggered tier or split it into
bounded phases with explicit handoffs. An approved design is required before
routing coherent high-risk implementation to Sol; design and invariant work
remain Astra work.

## Risk-adjusted planning and review cadence

For multi-phase work, score each remaining package independently from 1 (low)
to 5 (high) on risk, technical complexity, dependency centrality, and
uncertainty. Record dependencies, downstream consumers, reversibility, the
strength of deterministic oracles, design-approval state, and relevant review
history. File count and apparent edit size are not risk scores: a one-line ACL
or migration change can be high-risk, while a large generated rewrite can be
mechanical.

Optimize expected total effort, including likely rework and review cost. Route
to Astra earlier when ambiguity, centrality, or repeated findings make a Sol
pass likely to require another implementation/review loop. Conversely, use
Terra medium or Sol medium for deterministic work mechanically derived from an
approved authority, even when it touches many generated files.

Review once at each meaningful invariant-bearing family boundary:

- review a coherent design together with its generated contracts, manifests,
  hashes, counts, and deterministic validator results;
- do not create standalone reviewer turns for each generated artifact or for
  mechanical implementation that stays within the approved design;
- request one implementation review after the coherent family and its full
  positive/negative evidence are complete;
- repeat a review or broad test only when changed dependencies can invalidate
  prior evidence; and
- retain independent design, implementation, and closure review for high-risk
  schema, migration, authorization, regulatory, IAM, or invariant work.

If an agent has completed the technical analysis but continues expanding prose,
direct it to publish a compact reviewable artifact and return. Drafting length
is not additional verification.

## Review-history escalation

Count substantive failures within the current finding family or review loop.
Formatting-only feedback and infrastructure/transient failures do not count.

1. After the first substantive failed review, increase reasoning effort for the
   next pass and reassess whether the issue is a local defect, a missing
   invariant, a design error, an oracle gap, or a scope omission.
2. After the second failed review, or whenever the same finding family recurs,
   route the next pass to GPT-6 Astra and stop counterexample-by-counterexample
   patching. Restate the complete invariant and close the coherent family with
   its positive and negative matrix.
3. After the third unsuccessful loop, pause implementation. Identify and record
   the missing invariant, architecture decision, or shared test oracle before
   further code changes. Resume only after that gap is resolved and, for work
   governed by the adversarial-review process, independently reviewed.

Examples:

- A first concurrency-review failure moves the next pass to higher effort and
  reclassifies the issue as lock ordering, transaction isolation, or test
  coverage before editing.
- A second malformed-row counterexample in the same schema family moves the
  work to Astra and replaces one-off trigger patches with a complete union and
  corruption matrix.
- A third reconstruction mismatch stops implementation until the canonical
  mapping invariant and shared oracle are explicit.

Escalation never authorizes broader product scope or bypasses an approval gate.

## Builder and reviewer separation

Builder/reviewer separation is mandatory regardless of model. A model upgrade
does not make self-review independent. Qualifying work must still follow
`AGENTS.md`, `.ai/REVIEW_PROCESS.md`, and the repository-local
`adversarial-review` skill.

- Assign design, implementation, and closure adversaries as separate read-only
  project subagents unless the coordinator explicitly assigns a later fix task.
- Do not let the builder attest its own review stage, even when builder and
  reviewer would use the same model family.
- Record the actual runtime reviewer identity; a model name is not an identity.

## Dynamic availability and fallbacks

Use the preferred model when it is available. Otherwise choose the closest
available capability tier that can safely perform the phase:

1. For Astra-routed work, prefer the strongest available model at high or xhigh
   and preserve the mandatory independent-review gates. If no available model
   is adequate for the risk, pause and report the limitation.
2. For Sol-routed work, fall back to Astra at high, or to the strongest
   available implementation model at high when Astra is unavailable.
3. For Luna/Terra-routed work, use the other model at medium, then the closest
   available general implementation tier at medium.

Never silently claim or imply use of an unavailable model. In the phase notice
and any review artifact, record the actual fallback model and the reason. If the
runtime does not expose its model, write exactly `model not exposed by runtime`
rather than inferring it. If effort is not exposed, say `effort not exposed`.

## Required status commentary

At the start of every meaningful phase, report the role, exact model, reasoning
effort, and routing trigger. Report again whenever the role, model, or effort
changes. A meaningful phase includes framing/design, implementation, focused
verification, adversarial review, remediation after a failed review, and final
closure. Do not repeat the notice during routine progress updates when none of
those fields changed.

Use exactly this shape:

```text
Model routing: <role> → <exact model> (<effort>). Trigger: <brief reason>.
```

For a fallback, include it in the trigger, for example:

```text
Model routing: implementation builder → gpt-5.6-terra (high). Trigger: approved multi-file implementation; gpt-5.6-sol unavailable, closest implementation fallback.
```

Identify delegated builder and reviewer models in coordinator commentary. When
a delegated runtime does not expose its model, use the required unavailable
metadata wording rather than the requested model name.

## Review artifacts and closure

When known, every adversarial-review artifact must record:

- builder runtime identity, actual model, and effort;
- reviewer runtime identity, actual model, and effort;
- the routing trigger; and
- any fallback, unavailability, or unexposed runtime metadata.

Use a `## Model routing` section in each new design, implementation, remediation,
and closure-review artifact. Use a `## Model assignments` section in
`closure.md` to summarize the full run. These sections are the authoritative,
human-readable evidence locations; do not rely on task-local commentary or
model-selection requests as proof of the runtime used.

The independent closure reviewer must verify these sections against the phase
notices, returned runtime identities, and known delegation metadata. Missing,
inconsistent, inferred, or silently substituted model/effort evidence is a
closure blocker even if `validate-review-run.py` otherwise passes. Record
`model not exposed by runtime` or `effort not exposed` when applicable; that is
valid evidence of unavailable metadata, not permission to guess.

Do not rewrite historical attestations merely because model metadata was not
previously required. New review reports and closure evidence must be accurate
about what the runtime exposed. Final closure must summarize model assignments
for design, implementation, remediation, implementation review, and closure
review, including fallbacks.

For a review run already in progress when this policy is adopted, completed
reports are historical for this purpose even if they are still uncommitted. Do
not rewrite those immutable reports. Instead, bind this policy and the current
working tree into a fresh closure packet, summarize every known, unexposed, and
requested assignment in `closure.md`, and obtain a compliant independent
closure re-attestation before the files share a commit.

## Delegation mechanics

Use project subagents for bounded model-specific work when repository policy
and the active task permit delegation. Give each subagent one coherent role,
explicit scope, requested model and effort, and required evidence. Use the
repository's subagent mechanism so work remains attached to the current task;
do not create user-visible tasks merely to switch models.

The coordinator remains responsible for integrating results, checking actual
runtime metadata, preserving the working tree, and enforcing review gates.

```

## Changed-file manifest

```json
{
  "taskId": "T082-AWS-INVITE-PILOT",
  "stage": "implementation",
  "generatedAt": "2026-09-19T16:51:09+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    "backend/app/core/config.py",
    "backend/app/main.py",
    "backend/.env.example",
    "backend/tests/test_pilot_release_boundary.py",
    ".ai/pilot-release-boundary-v1.json",
    ".ai/PILOT_RELEASE_BOUNDARY.md",
    "scripts/verify_pilot_release_boundary.py",
    "scripts/build_pilot_migration_context.py"
  ],
  "scopeFingerprint": "90dfb6565e1cf4c2fddc249b2956f8f069b5c02e14eaa8350dd5cb217611f48d",
  "files": [
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "??",
      "size": 6594,
      "sha256": "e630583812eb35383b72097f9c5fc61960aac18ba5f9ac7f6d1a218e8373d6de",
      "readStatus": "readable"
    },
    {
      "path": ".ai/pilot-release-boundary-v1.json",
      "status": "??",
      "size": 8053,
      "sha256": "178c94eab65eb38c77b49afeb9f1494fa52bc433dc7d97bca1204555b6382ba9",
      "readStatus": "readable"
    },
    {
      "path": "backend/.env.example",
      "status": " M",
      "size": 2051,
      "sha256": "78171cf0089c0951ac52f0fa9dc078c9c36516c137e269dfe50fd3f10367dbc9",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M",
      "size": 9625,
      "sha256": "482af947a0fe1cd31a9974b634435dccf7041b50903ae365e365c20507a07f0d",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/main.py",
      "status": " M",
      "size": 1297,
      "sha256": "6f5e93cce90ef1b52ceafbb371951e264762e74a2885be7eadbfd9b1e122a42a",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??",
      "size": 36590,
      "sha256": "3d3bc5ff0b946812555d21f511ffc0a4ea0625bf0982361ef403b9f431cb2d47",
      "readStatus": "readable"
    },
    {
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??",
      "size": 12566,
      "sha256": "8f0f8a24cd6aaf6bb5583bcae4f05abdd47b2553ebe7efb4c366fe01ba7d637e",
      "readStatus": "readable"
    },
    {
      "path": "scripts/verify_pilot_release_boundary.py",
      "status": "??",
      "size": 11997,
      "sha256": "0021bff593434e97eebd5f143aa876c160c35b1650224cd9580946cc441fe8cf",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "review_input",
      "size": 36292,
      "sha256": "69c2cce98e90b2902e172ef067800ee6bfdbdaaef3f701b8fe492a694d977f71",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/findings.json",
      "status": "review_input",
      "size": 14534,
      "sha256": "09965b0d059bf502df2438ad9dd225351e32fac4fef453c6c787ffa945280a73",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md",
      "status": "review_input",
      "size": 5778,
      "sha256": "a34e97448b435bda1e6e5f5b3f78f2e734d8c270a2fbb62839a70ef35753f315",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md",
      "status": "review_input",
      "size": 4092,
      "sha256": "2909b5b0e14af10e41eb6a7b762df28e47f3d91c16c35627db8064e375f31506",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md",
      "status": "review_input",
      "size": 2888,
      "sha256": "78442e342fb36fb3732cc95d7e9e77f49842b3a5e35dffe49c920c6e2d496018",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md",
      "status": "review_input",
      "size": 4889,
      "sha256": "083b635357b9e0e3f79eed2e407216907459f504aef7ba2c1946dbed8381bcf4",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md",
      "status": "review_input",
      "size": 3670,
      "sha256": "e49b39910551c7199ff4f2b61e75de0bf018205c022ea4da2c70eeca2eab35a8",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md",
      "status": "review_input",
      "size": 2538,
      "sha256": "6ca96fdc41f658ec35d7170daa3fe2f1a832bfa35159046a6ba01a679b497a25",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md",
      "status": "review_input",
      "size": 3043,
      "sha256": "acb6475c569a5314f30ecd8901795488d53695125f6d2fd7c5b60d6c5f3f23c3",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md",
      "status": "review_input",
      "size": 5758,
      "sha256": "41827e83574a0c82cbc3d6fa5360b9e7c1498242018f7099bd80ae13fb2cd7f6",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md",
      "status": "review_input",
      "size": 2715,
      "sha256": "852c434b41b2c6630dd1a5888ac0211d66933f1c5be0e9a40a135de7ac984b48",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md",
      "status": "review_input",
      "size": 6926,
      "sha256": "eb675256176e509132834eb673d3bf7b494e1229d97e32788fa4220416482f51",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md",
      "status": "review_input",
      "size": 2249,
      "sha256": "96e9c47d801d64ed5ca56daa4e2e740c89ec260a2096fad3e82fa6ddb9e83c08",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md",
      "status": "review_input",
      "size": 4699,
      "sha256": "7b9e87c5e504f19e2b63739c632602876cfebc6447e93cb40da2a43d9e9a2986",
      "readStatus": "readable"
    },
    {
      "path": "AGENTS.md",
      "status": "review_input",
      "size": 2214,
      "sha256": "2295cae2d1394c07fe3573d4d790985eb1b85c9a6514a94d851d55337f3fc0cb",
      "readStatus": "readable"
    },
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": "review_input",
      "size": 10194,
      "sha256": "043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": " M"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-executor.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-schema-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-reference-program-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-calibration-goldens.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-fixtures-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-goldens-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-interpreter.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-mutations-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-schema-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-architecture-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-bootstrap.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-inputs.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-integration-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-5.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-6.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-mapping-reconstruction.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-dag-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-resource-rebinding.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/architecture-oracle-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-integration-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/independent-acceptance-enumerator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-cases-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-oracle-results-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-registry-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_harness.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_kernel.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/normative-acceptance-matrix.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary.tar.gz",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle-v2.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-execution-manifest.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-prerequisite-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-contract-builder.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/risk-adjusted-routing-audit.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/run-trusted-sentinel.sh",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/sql-topology-benchmark.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-harness.sql",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-output.txt",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
      "status": "??"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M"
    },
    {
      "path": "backend/app/services/ad_v4_acceptance_persistence_contract.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority_postgres.py",
      "status": "??"
    },
    {
      "path": "scripts/generate-ad-v4-acceptance-persistence.py",
      "status": "??"
    }
  ],
  "outOfScopeReason": "Preserved pre-existing T081 Slice 4B work, its unreviewed 0030 migration/service/tests/generator, backend/app/models/core.py edits, and the pre-existing model-routing policy edit are not Package A implementation and must not be changed, staged, committed, or treated as pilot closure."
}
```

## Diff against base

```diff
diff --git a/backend/.env.example b/backend/.env.example
index 3b782c6..f4e93af 100644
--- a/backend/.env.example
+++ b/backend/.env.example
@@ -40,3 +40,12 @@ PAPRNAV_OPENAI_API_KEY=
 PAPRNAV_OPENAI_BASE_URL=https://api.openai.com/v1
 PAPRNAV_AD_EXTRACTION_MODEL=gpt-5.5
 PAPRNAV_AD_EXTRACTION_TIMEOUT_SECONDS=30
+# V4 routes remain available by default outside pilot. Pilot startup requires
+# this and every narrower V4 capability flag to be false.
+PAPRNAV_AD_V4_ROUTES_ENABLED=true
+PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED=false
+PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED=false
+PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED=false
+PAPRNAV_AD_V4_SLICE4_READS_ENABLED=false
+PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED=false
+PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED=false
diff --git a/backend/app/core/config.py b/backend/app/core/config.py
index 256c3cd..b427e1d 100644
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -82,6 +82,7 @@ class Settings:
     govinfo_api_key: Optional[str]
     govinfo_base_url: str
     drs_max_snapshot_age_days: int = 7
+    ad_v4_routes_enabled: bool = True
     ad_v4_validator2_writes_enabled: bool = False
     ad_v4_slice3a_routes_enabled: bool = False
     ad_v4_slice3b_routes_enabled: bool = False
@@ -99,10 +100,11 @@ def parse_bool(value: Optional[str], default: bool = False) -> bool:
 @lru_cache
 def get_settings() -> Settings:
     load_local_env_file()
+    environment = os.getenv("PAPRNAV_ENV", "local").strip().lower()
     return Settings(
         app_name=os.getenv("PAPRNAV_APP_NAME", "paprnav"),
         app_version=os.getenv("PAPRNAV_APP_VERSION", "0.1.0"),
-        environment=os.getenv("PAPRNAV_ENV", "local"),
+        environment=environment,
         database_url=os.getenv(
             "DATABASE_URL",
             "postgresql+psycopg://paprnav_user:paprnav_password@localhost:5432/paprnav_db",
@@ -182,6 +184,10 @@ def get_settings() -> Settings:
         drs_max_snapshot_age_days=int(
             os.getenv("PAPRNAV_DRS_MAX_SNAPSHOT_AGE_DAYS", "7")
         ),
+        ad_v4_routes_enabled=parse_bool(
+            os.getenv("PAPRNAV_AD_V4_ROUTES_ENABLED"),
+            default=environment != "pilot",
+        ),
         ad_v4_validator2_writes_enabled=parse_bool(
             os.getenv("PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED")
         ),
@@ -201,3 +207,27 @@ def get_settings() -> Settings:
             os.getenv("PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED")
         ),
     )
+
+
+PILOT_FORBIDDEN_V4_SETTINGS = (
+    "ad_v4_routes_enabled",
+    "ad_v4_validator2_writes_enabled",
+    "ad_v4_slice3a_routes_enabled",
+    "ad_v4_slice3b_routes_enabled",
+    "ad_v4_slice4_reads_enabled",
+    "ad_v4_slice4_drafts_enabled",
+    "ad_v4_slice4_decisions_enabled",
+)
+
+
+def validate_runtime_settings(settings: Settings) -> None:
+    """Fail closed when the invite pilot attempts to expose unfinished V4 work."""
+
+    if settings.environment != "pilot":
+        return
+    enabled = [name for name in PILOT_FORBIDDEN_V4_SETTINGS if getattr(settings, name)]
+    if enabled:
+        raise RuntimeError(
+            "Pilot startup refused because V4 capability settings are enabled: "
+            + ", ".join(enabled)
+        )
diff --git a/backend/app/main.py b/backend/app/main.py
index 910f197..24cd7b9 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -1,12 +1,24 @@
-from fastapi import FastAPI
+from fastapi import FastAPI, Request
 from fastapi.middleware.cors import CORSMiddleware
+from fastapi.responses import JSONResponse
+from starlette._utils import get_route_path
 
 from app.api.router import api_router
-from app.core.config import get_settings
+from app.core.config import get_settings, validate_runtime_settings
+
+
+def is_ad_v4_path(path: str) -> bool:
+    segments = [segment for segment in path.split("/") if segment]
+    return (
+        len(segments) >= 4
+        and segments[:3] == ["api", "v1", "ads"]
+        and "v4" in segments[3:]
+    )
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
+    validate_runtime_settings(settings)
     app = FastAPI(title=settings.app_name, version=settings.app_version)
 
     app.add_middleware(
@@ -17,6 +29,14 @@ def create_app() -> FastAPI:
         allow_headers=["*"],
     )
 
+    @app.middleware("http")
+    async def enforce_pilot_release_boundary(request: Request, call_next):
+        if not settings.ad_v4_routes_enabled and is_ad_v4_path(
+            get_route_path(request.scope)
+        ):
+            return JSONResponse(status_code=404, content={"detail": "Not Found"})
+        return await call_next(request)
+
     app.include_router(api_router)
 
     return app

```

## Untracked text files

### `.ai/PILOT_RELEASE_BOUNDARY.md`

size=6594; sha256=e630583812eb35383b72097f9c5fc61960aac18ba5f9ac7f6d1a218e8373d6de; truncated=false

```text
# Pilot release boundary

The invite-only AWS pilot is built from an explicit reviewed Git commit. It is
not built from the current working directory. Before packaging a candidate,
run:

```bash
python3 scripts/verify_pilot_release_boundary.py --ref <commit>
```

The verifier reads the commit tree named by `--ref`, applies
`.ai/pilot-release-boundary-v1.json`, and fails unless:

- the approved pilot baseline is an ancestor;
- the migration graph has the single reviewed head `20260913_0029`;
- the exact 44-file migration authority inventory and every SHA-256 match the
  reviewed policy, with no duplicate metadata, missing predecessor, graph cycle,
  extra root, or unsupported dependency/branch metadata;
- the reviewed `backend/app/models/core.py` blob is unchanged; and
- no T081 Slice 4B or unreviewed 0030 artifact is present.

The authority inventory includes every committed file under
`backend/app/db/migrations/`, regardless of extension: all 29 revision sources,
all three SQL sidecars executed by 0028/0029, `env.py`, `script.py.mako`, and the
directory's remaining files. It also includes `backend/alembic.ini` and the
minimal repository support modules used by `env.py`: `app/core/config.py`,
`app/db/base.py`, `app/models/core.py`, and their package `__init__.py` files.
The separate expected-head and protected-model checks remain mandatory.

All inventory names and hashes come from baseline commit
`19fe8e2e170687ed65deed78cb1af99d60f601e9`, except the explicitly recorded
Package A `app/core/config.py` target amendment. Its exact SHA-256 is
`482af947a0fe1cd31a9974b634435dccf7041b50903ae365e365c20507a07f0d` and must
receive independent Package A approval. The pre-Package-A baseline therefore
fails with exactly that configuration difference. A mocked candidate containing
the approved target bytes passes; this is not evidence that a release commit
already exists. Run the verifier on the eventual reviewed candidate commit
before image construction.

Additions, removals, renames, and content changes in these source inputs require
an explicit reviewed policy amendment. This verifier proves source inventory,
hashes, and graph correctness. A source pass does not prove import isolation
when running from the full checkout.
Git names are enumerated as raw NUL-delimited bytes, compared as bytes, and
decoded with `surrogateescape` only for ASCII-escaped JSON output. Quoted,
tab/newline, non-ASCII, and non-UTF-8 names cannot bypass the authority or T081
prefix checks.

Build the migration execution context separately:

```bash
backend/.venv/bin/python scripts/build_pilot_migration_context.py build --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
backend/.venv/bin/python scripts/build_pilot_migration_context.py verify --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
```

The destination and every ancestor must be real directories with no symlink
traversal; the destination itself must not exist. The builder resolves the ref
once, reads Git blobs and modes at that commit, validates all inputs before
creation, and maps `backend/alembic.ini` to `alembic.ini` and each approved
`backend/app/...` source to `app/...`. It copies no arbitrary checkout input,
regardless of current or future driver/import name. In particular, `.env`,
bytecode, tests, and unapproved replacement modules never enter the context.

The exact output is 44 regular files plus `migration-context.json`. Each entry
records source/destination paths, Git mode, byte length, and SHA-256. The
manifest records the exact source commit and a deterministic SHA-256 over
canonical JSON without the digest field. Source mode must be `100644`; context
files are `0444` and directories `0555`. Verification compares the manifest and
every file byte back to the reviewed commit/policy and rejects extra/missing
files or directories, symlinks, hard links, and mode drift. Unsafe, duplicate,
or non-UTF-8 manifest paths fail. A failed write leaves an incomplete directory
for inspection; it cannot be reused or pass verification.

The script's local `run` mode requires an explicit nonempty `DATABASE_URL`,
verifies the context before/after execution, forces `PAPRNAV_DISABLE_DOTENV=1`
and `PYTHONDONTWRITEBYTECODE=1`, and launches `python -I -B -m alembic` from the
context with its absolute configuration path and fixed head `20260913_0029`.
`-B` is explicit because `-I` ignores Python environment variables. Runtime
credentials are never recorded in the context/manifest or passed as command
arguments; child output is suppressed because driver errors may contain URLs.
The local wrapper needs repository access for verification and is not the
production task entrypoint.

Package A's execution oracle runs the actual committed `env.py` through Alembic
and actual SQLAlchemy `engine_from_config`, stopping after driver loading and
before any database connection. Both `psycopg.py` and `psycopg/__init__.py`
sentinels execute in the vulnerable checkout control. In the sealed control,
the real installed psycopg, Alembic, and SQLAlchemy resolve to the interpreter's
canonical site-packages, and no checkout source directory is on `sys.path`.
The local virtual environment is located beneath the repository; only its
exact installed site-packages root is allowed, never application/editable
source paths. Output remains unchanged and contains no bytecode after execution.

Package E must bind the dedicated migration image, interpreter, installed
dependencies/startup hooks, read-only context, command/environment, image labels,
and task definition to an immutable image digest. It must prove the application
checkout is absent from the task filesystem/import path and cannot reenter via
mounts or overrides, require the migration-only runtime secret, and prove a fresh
PostgreSQL upgrade. These local tests do not establish container isolation,
package provenance, database migration success, or AWS execution readiness.

`PAPRNAV_ENV=pilot` defaults the pilot-wide V4 route gate off. Startup also
fails if that gate or any narrower V4 write, projection, draft, or decision
gate is enabled. Every `/api/v1/ads/**/v4/**` request then receives a generic
404 before authentication or request-body parsing. Local and test environments
retain their existing V4 behavior unless the route gate is explicitly false.

Passing this check is necessary release evidence, not authorization to deploy.
It does not validate an image digest, modify AWS, migrate a database, or close
the preserved T081 review run. Those remain later reviewed pilot gates.

```
### `.ai/pilot-release-boundary-v1.json`

size=8053; sha256=178c94eab65eb38c77b49afeb9f1494fa52bc433dc7d97bca1204555b6382ba9; truncated=false

```text
{
  "version": "paprnav-pilot-release-boundary-v1",
  "approvedBaselineCommit": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "expectedMigrationHeads": [
    "20260913_0029"
  ],
  "migrationAuthorityProvenance": {
    "baselineCommit": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
    "scope": "Reviewed inputs to the sealed migration context: all committed migration-directory files, Alembic configuration, and the minimal env.py repository support modules. This source inventory alone does not prove transitive import isolation.",
    "targetAmendments": {
      "backend/app/core/config.py": "Package A pilot V4 gate configuration; exact target bytes are bound below and require independent Package A implementation approval before release."
    }
  },
  "migrationContext": {
    "version": "paprnav-sealed-migration-context-v1",
    "manifestName": "migration-context.json",
    "sourceGitMode": "100644",
    "sourceToDestination": {
      "backend/alembic.ini": "alembic.ini",
      "backend/app/": "app/"
    }
  },
  "approvedMigrationAuthoritySha256": {
    "backend/alembic.ini": "b08cc331288d26bc4d717908115f3107393c714512b8d6da072fe4260f92d3b7",
    "backend/app/__init__.py": "119575f3fe80c33bbf4ff5a79decfeaf5e26296258e61fb1f07a8a8c5ff36945",
    "backend/app/core/__init__.py": "cdeae4c1b7a55869627de430e66b776b6784584e8cf5d0f2aea86acfacfd8868",
    "backend/app/core/config.py": "482af947a0fe1cd31a9974b634435dccf7041b50903ae365e365c20507a07f0d",
    "backend/app/db/__init__.py": "718944411bc53dcb4233ba8cded164b5ec32d4e0ab6f554f51fc9bf2e9225eff",
    "backend/app/db/base.py": "7bc9d3f954177acda9b00457d7844ae640c15d77fcf25bb6022ded809f548b35",
    "backend/app/db/migrations/README.md": "565479aaab47141f517fa167e49cca4d810c55705cb0d0d11109801b5cdf7f18",
    "backend/app/db/migrations/env.py": "4e43a1a90bd81a036384fb82997aa0863185f2cf90a02c7347f0ff43b830aca1",
    "backend/app/db/migrations/script.py.mako": "a1ba0945f4421247989ffaa31a92c0d83ed7822ca2fd9e3aa586af8fb97e62a7",
    "backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql": "c8d1f6508b2708ae0a0c7c64ca9cefe7aa144e5d268e1d1118aee3bda25432b7",
    "backend/app/db/migrations/sql/20260911_0028_obligation_integrity.sql": "d2db777166d1785d179d5bff5d572a95131b2a570df0b2c2a04dab4edd6d879e",
    "backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql": "92cc8cb8c73356f8194fe2e995c1ca7ba9892d88d07e17f4cea67cc34d39cf7e",
    "backend/app/db/migrations/versions/.gitkeep": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
    "backend/app/db/migrations/versions/20260617_0001_initial_schema.py": "4e2e9800d88efe949d3c10256ea82ae1c57a07fd8a463d6fc63c9793d6cfcce2",
    "backend/app/db/migrations/versions/20260617_0002_add_auth_sessions.py": "295d960a5838a9160d5a5feea2bbe9e5aa2e1617545bd7aab628a1f1fe35896c",
    "backend/app/db/migrations/versions/20260618_0003_add_ocr_ingestion.py": "6bec108a7a7dae047c8cca500f0622a6240c9ae4ae5ca572fe2a5a1ae8008eb3",
    "backend/app/db/migrations/versions/20260618_0004_add_ad_ingestion.py": "22bb8021278526b25ca0cadb1b7d5f0031445176732740e8b7352faa9e7586cc",
    "backend/app/db/migrations/versions/20260618_0005_add_ad_matching.py": "78c28259824e185c9649e79862b04d356dd596996cc14e1979b25adfeddb9a9b",
    "backend/app/db/migrations/versions/20260619_0006_add_observability_and_adjudication.py": "e0cce3b4e68246b576a32f85c7def6c5ca5ded3a0ca1013198a5723c44fdcaf0",
    "backend/app/db/migrations/versions/20260620_0007_add_component_applicability.py": "416ff71ff6e86c4935fcc7b98c4d3492f894677465476d0d5ee3fab91af5d2a0",
    "backend/app/db/migrations/versions/20260708_0008_add_pilot_cost_tags.py": "96a07bf6456a456e51c9060d32a489cb0c6659376661e7785d59d8df8a27a26e",
    "backend/app/db/migrations/versions/20260710_0009_add_ocr_correction_order.py": "d9a889a8a531e775c69c40f9edadf0e45b4813efb96bbccd768a1801220b9fdb",
    "backend/app/db/migrations/versions/20260722_0010_add_ocr_review_audit.py": "53d283189605a449016a527ad86fc70dd8125b3dc433a91764329f58f667128a",
    "backend/app/db/migrations/versions/20260725_0011_add_ocr_usage_metering.py": "4ff94f4ab0d2b8116631db42d7aaeba3bb9920fad9c84942436f4b4e19258549",
    "backend/app/db/migrations/versions/20260725_0012_use_fixed_precision_ocr_costs.py": "30ae5ed52fc8bf26a0904e304f7d4bc1eefffae07468756683ea71f8fdd74f21",
    "backend/app/db/migrations/versions/20260725_0013_add_pdf_inspection.py": "202dc0551bdca8ac282943a475925f64d30588d3edaf6a1160c7b920051b3fab",
    "backend/app/db/migrations/versions/20260726_0014_add_page_extraction_plans.py": "426ec2bb9e51f0a2557cea9d30a870c591e3db3c2312875972bfa705a6a54fd9",
    "backend/app/db/migrations/versions/20260726_0015_add_candidate_validation.py": "624a23cbe229320254780001ed4fd77f2974c8f2a5e412939befe3bb8903362a",
    "backend/app/db/migrations/versions/20260726_0016_add_ad_coverage_cost_attribution.py": "7bc2125efe7013fa374d7a9fb446fd3e7e72b0cd071e39068e7898498f7f13eb",
    "backend/app/db/migrations/versions/20260730_0017_add_review_attestation_and_current_matches.py": "9ed542afbddb8adcaace34fc4499ec3060c344021f319b8098233a024a33fa24",
    "backend/app/db/migrations/versions/20260804_0018_add_ad_source_documents.py": "f530b964880888e172ce6a3720ce53b489879c411aed85848cf3309bdfd483ab",
    "backend/app/db/migrations/versions/20260806_0019_expand_applicability_product_subtype.py": "d856fb08e3fb5286d0a5f4a8546bcb5342eec7665abd712dbdadd35c213d86df",
    "backend/app/db/migrations/versions/20260809_0020_add_ad_recurrence.py": "20ff264a9ea43557f50f99aa6e221e6c071f2fded46cb38c14a1657b44c42d83",
    "backend/app/db/migrations/versions/20260822_0021_add_ad_applicability_v3.py": "922164309f78fbe6bfbfe9801443fbbd70e18d146f6af35e02a93d1ee119252c",
    "backend/app/db/migrations/versions/20260822_0022_harden_ad_review_materialization.py": "110edf1e31f5833e80a3fbb6d7188135a63525dfc3ba3b7eedabfcac0d6ed0e1",
    "backend/app/db/migrations/versions/20260822_0023_backfill_ad_v3_amoc_envelope.py": "7c74737f8e332973a14c307525b470ea19a050758f0006f751294f24a0a7fd23",
    "backend/app/db/migrations/versions/20260823_0024_bind_signed_ad_materialization.py": "c0f461d4fa7ffa5c02217990be9c72c444d23c9c1d2a276fe5326212503e8d29",
    "backend/app/db/migrations/versions/20260830_0025_add_ad_evidence_fragments.py": "5f0c3bc1b4597e87cca56c28b726b62f8f1329795d716eaa5bd75feac5bd90a2",
    "backend/app/db/migrations/versions/20260901_0026_add_ad_v4_candidates.py": "811efe67991359f70cd853444a00c9dd741407469a99634bc8ee4e8eee886633",
    "backend/app/db/migrations/versions/20260907_0027_add_ad_v4_applicability.py": "6338c193516ebdf016fe5e80c6af1d443de1cc40bd911c8012bff41f3f107405",
    "backend/app/db/migrations/versions/20260911_0028_add_ad_v4_obligations.py": "754c86b18ff6901cf14b17c28562b45511107a3b78acdb4b646d6b2deefcff8c",
    "backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py": "325277f7ffb8c9e100028c6f32e39263b0a336591b88634f641ed24737041a8f",
    "backend/app/models/__init__.py": "da84cc35897dece40a86bf6cebbc661a8398570559d5f195d8d430f5af879311",
    "backend/app/models/core.py": "be50bfb1009cd24b1787cf2ceeff1377e92a82c2825aaa74023dec74852ae7ac"
  },
  "protectedBlobSha256": {
    "backend/app/models/core.py": "be50bfb1009cd24b1787cf2ceeff1377e92a82c2825aaa74023dec74852ae7ac"
  },
  "excludedTreePaths": [
    "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
    "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
    "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
    "backend/app/services/ad_v4_acceptance_persistence_contract.py",
    "backend/tests/test_ad_v4_acceptance_persistence.py",
    "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
    "backend/tests/test_ad_v4_model_source_authority.py",
    "backend/tests/test_ad_v4_model_source_authority_postgres.py",
    "scripts/generate-ad-v4-acceptance-persistence.py"
  ],
  "excludedTreePrefixes": [
    ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/"
  ]
}

```
### `backend/tests/test_pilot_release_boundary.py`

size=36590; sha256=3d3bc5ff0b946812555d21f511ffc0a4ea0625bf0982361ef403b9f431cb2d47; truncated=false

```text
from __future__ import annotations

import asyncio
import copy
import importlib.util
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import PILOT_FORBIDDEN_V4_SETTINGS, get_settings
from app.main import create_app, is_ad_v4_path


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / ".ai" / "pilot-release-boundary-v1.json"
V4_ENV_BY_SETTING = {
    "ad_v4_routes_enabled": "PAPRNAV_AD_V4_ROUTES_ENABLED",
    "ad_v4_validator2_writes_enabled": "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED",
    "ad_v4_slice3a_routes_enabled": "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED",
    "ad_v4_slice3b_routes_enabled": "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED",
    "ad_v4_slice4_reads_enabled": "PAPRNAV_AD_V4_SLICE4_READS_ENABLED",
    "ad_v4_slice4_drafts_enabled": "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED",
    "ad_v4_slice4_decisions_enabled": "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED",
}
EXPECTED_V4_OPERATIONS = {
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/applicability-projections"),
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals"),
    ("POST", "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals"),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/applicability-projection/reconstruction",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/obligation-projection/reconstruction",
    ),
    (
        "GET",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-observation",
    ),
    (
        "POST",
        "/api/v1/ads/directives/{directive_id}/v4/candidate-proposals/{proposal_id}/review-cases",
    ),
    ("GET", "/api/v1/ads/directives/{directive_id}/v4/obligation-projections"),
    ("GET", "/api/v1/ads/v4/candidate-proposals/{proposal_id}"),
    ("GET", "/api/v1/ads/v4/review-cases"),
    ("GET", "/api/v1/ads/v4/review-cases/{case_id}"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/drafts"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/rejection"),
    ("POST", "/api/v1/ads/v4/review-cases/{case_id}/review-request"),
}


@pytest.fixture(autouse=True)
def restore_temporary_context_permissions(tmp_path: Path):
    """Let pytest remove contexts deliberately made read-only by the tests."""

    yield
    for current, directories, files in os.walk(tmp_path, topdown=False):
        for name in [*directories, *files]:
            path = Path(current) / name
            if not path.is_symlink():
                path.chmod(0o700)
        Path(current).chmod(0o700)


def load_release_verifier() -> ModuleType:
    path = REPO_ROOT / "scripts" / "verify_pilot_release_boundary.py"
    spec = importlib.util.spec_from_file_location("verify_pilot_release_boundary", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure_pilot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    for env_name in V4_ENV_BY_SETTING.values():
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()


def concrete_path(path: str) -> str:
    return re.sub(r"\{[^}/]+\}", "00000000-0000-0000-0000-000000000000", path)


def v4_operations(app) -> list[tuple[str, str]]:
    operations: list[tuple[str, str]] = []
    for path, path_item in app.openapi()["paths"].items():
        if is_ad_v4_path(path):
            operations.extend(
                (method.upper(), path)
                for method in path_item
                if method.lower() in {"get", "post", "put", "patch", "delete"}
            )
    return sorted(operations)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/api/v1/ads/v4", True),
        ("/api/v1/ads/directives/id/v4/candidate-proposals", True),
        ("//api//v1//ads//v4//review-cases", True),
        ("/api/v1/ads/v4ish/candidate-proposals", False),
        ("/api/v1/aircraft/v4", False),
        ("/api/v2/ads/v4", False),
    ],
)
def test_v4_path_family_matcher(path: str, expected: bool) -> None:
    assert is_ad_v4_path(path) is expected


def test_safe_pilot_configuration_disables_all_v4_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_pilot(monkeypatch)

    settings = get_settings()
    assert settings.environment == "pilot"
    assert all(not getattr(settings, name) for name in PILOT_FORBIDDEN_V4_SETTINGS)

    app = create_app()
    operations = v4_operations(app)
    assert set(operations) == EXPECTED_V4_OPERATIONS

    with TestClient(app) as client:
        for method, path in operations:
            response = client.request(
                method,
                concrete_path(path),
                content=b"{not-json",
                headers={"Origin": "https://untrusted.example"},
            )
            assert response.status_code == 404, (method, path, response.text)
            assert response.json() == {"detail": "Not Found"}

        preflight = client.options(
            concrete_path(operations[0][1]),
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert preflight.status_code == 404
        assert preflight.json() == {"detail": "Not Found"}
        assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("encoded_delimiter", ["%3Fquery", "%23fragment"])
def test_encoded_path_delimiters_cannot_reach_authentication(
    monkeypatch: pytest.MonkeyPatch,
    encoded_delimiter: str,
) -> None:
    configure_pilot(monkeypatch)
    app = create_app()
    auth_reached = False

    def authentication_sentinel():
        nonlocal auth_reached
        auth_reached = True
        raise AssertionError("authentication boundary was reached")

    app.dependency_overrides[get_current_user] = authentication_sentinel
    path = (
        f"/api/v1/ads/directives/id{encoded_delimiter}/v4/candidate-proposals"
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(path)
        preflight = client.options(
            path,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert preflight.status_code == 404
    assert preflight.json() == {"detail": "Not Found"}
    assert auth_reached is False


def test_decoded_scope_path_and_root_path_gate_without_reading_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_pilot(monkeypatch)
    app = create_app()
    handler_reached = False

    @app.post("/api/v1/ads/{identifier}/v4/body-sentinel")
    async def body_sentinel(identifier: str, request: Request):
        nonlocal handler_reached
        handler_reached = True
        await request.body()
        return {"identifier": identifier}

    messages: list[dict] = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mount/api/v1/ads/id?query/v4/body-sentinel",
        "raw_path": b"/mount/api/v1/ads/id%3Fquery/v4/body-sentinel",
        "root_path": "/mount",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }

    async def body_read_sentinel():
        raise AssertionError("request body was read")

    async def send(message: dict) -> None:
        messages.append(message)

    asyncio.run(app(scope, body_read_sentinel, send))

    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    assert start["status"] == 404
    assert json.loads(body) == {"detail": "Not Found"}
    assert handler_reached is False


@pytest.mark.parametrize("setting_name", PILOT_FORBIDDEN_V4_SETTINGS)
def test_pilot_startup_rejects_each_v4_capability(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
) -> None:
    configure_pilot(monkeypatch)
    monkeypatch.setenv(V4_ENV_BY_SETTING[setting_name], "true")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match=setting_name):
        create_app()


def test_local_environment_retains_v4_route_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "local")
    for env_name in V4_ENV_BY_SETTING.values():
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()

    assert get_settings().ad_v4_routes_enabled is True
    assert set(v4_operations(create_app())) == EXPECTED_V4_OPERATIONS


def test_pre_package_a_commit_fails_only_for_target_configuration() -> None:
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    result = verifier.verify_release(REPO_ROOT, policy["approvedBaselineCommit"], policy)

    assert result["status"] == "fail"
    assert result["errors"] == [
        "migration authority blob differs: backend/app/core/config.py"
    ]
    assert result["migrationHeads"] == ["20260913_0029"]
    assert result["excludedPathsPresent"] == []
    protected = result["protectedBlobs"]["backend/app/models/core.py"]
    assert protected["actualSha256"] == protected["expectedSha256"]


@pytest.fixture(scope="module")
def approved_candidate_tree() -> dict[bytes, bytes]:
    """Real baseline blobs plus the reviewed Package A config target bytes."""
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    baseline = policy["approvedBaselineCommit"]
    paths = verifier.migration_authority_paths(verifier.tree_paths(REPO_ROOT, baseline))
    tree = {
        path: verifier.blob_bytes(REPO_ROOT, baseline, path)
        for path in paths
    }
    tree[b"backend/app/core/config.py"] = (REPO_ROOT / "backend/app/core/config.py").read_bytes()
    return tree


@pytest.fixture
def candidate_verifier(approved_candidate_tree, monkeypatch):
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    tree = dict(approved_candidate_tree)
    verifier.candidate_modes = {}
    commit = "a" * 40

    def candidate_git(repo, *args, check=True):
        if args[:3] == ("ls-tree", "-rz", "--name-only") and args[-1] in {"candidate", commit}:
            # Exercise the raw Git output parser, including every unusual byte
            # name supplied by the negative cases below.
            return subprocess.CompletedProcess(args, 0, b"\0".join(sorted(tree)) + b"\0", b"")
        if args == ("ls-tree", "-rz", commit):
            records = []
            for path in sorted(tree):
                mode, kind = verifier.candidate_modes.get(path, (b"100644", b"blob"))
                records.append(mode + b" " + kind + b" " + b"0" * 40 + b"\t" + path)
            return subprocess.CompletedProcess(args, 0, b"\0".join(records) + b"\0", b"")
        if args == ("merge-base", "--is-ancestor", policy["approvedBaselineCommit"], commit):
            return subprocess.CompletedProcess(args, 0, b"", b"")
        if args[0] == "show":
            path = args[1].split(b":", 1)[1]
            if path not in tree:
                raise RuntimeError(f"missing tree path: {path!r}")
            return subprocess.CompletedProcess(args, 0, tree[path], b"")
        raise AssertionError(f"unexpected Git command: {args}")

    monkeypatch.setattr(verifier, "git", candidate_git)
    monkeypatch.setattr(verifier, "resolve_commit", lambda repo, ref: commit)
    return verifier, policy, tree


def test_approved_target_candidate_passes_complete_authority(candidate_verifier) -> None:
    verifier, policy, _ = candidate_verifier
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "pass", result["errors"]
    assert result["migrationHeads"] == ["20260913_0029"]
    assert result["excludedPathsPresent"] == []
    assert len(result["migrationAuthorityBlobs"]) == 44
    assert set(result["migrationAuthorityBlobs"]) == set(policy["approvedMigrationAuthoritySha256"])
    assert all(item["actualSha256"] == item["expectedSha256"]
               for item in result["migrationAuthorityBlobs"].values())
    assert json.loads(json.dumps(result, sort_keys=True)) == result


def test_release_verifier_fails_for_protected_blob_or_head_policy_drift(candidate_verifier) -> None:
    verifier, policy, _ = candidate_verifier
    wrong_blob = copy.deepcopy(policy)
    wrong_blob["protectedBlobSha256"]["backend/app/models/core.py"] = "0" * 64
    blob_result = verifier.verify_release(REPO_ROOT, "candidate", wrong_blob)
    assert blob_result["status"] == "fail"
    assert "protected release blob differs: backend/app/models/core.py" in blob_result[
        "errors"
    ]

    wrong_head = copy.deepcopy(policy)
    wrong_head["expectedMigrationHeads"] = ["not-the-reviewed-head"]
    head_result = verifier.verify_release(REPO_ROOT, "candidate", wrong_head)
    assert head_result["status"] == "fail"
    assert any(error.startswith("migration heads differ:") for error in head_result["errors"])


def test_release_verifier_recognizes_exact_and_prefix_exclusions() -> None:
    verifier = load_release_verifier()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    paths = [
        policy["excludedTreePaths"][0].encode(),
        policy["excludedTreePrefixes"][0].encode() + b"decision.md",
        b"backend/app/main.py",
    ]

    assert verifier.excluded_paths(paths, policy) == sorted(paths[:2])


def test_release_verifier_rejects_changed_migration_content(candidate_verifier) -> None:
    verifier, policy, tree = candidate_verifier
    target = b"backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py"
    tree[target] += b'\nrevision = "unreviewed_revision"\n'
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)

    assert result["status"] == "fail"
    assert f"migration authority blob differs: {target.decode()}" in result["errors"]
    assert any(
        "revision exactly once at module scope; found 2 assignments" in error
        for error in result["errors"]
    )


AUTHORITY_MUTATION_TARGETS = [
    "backend/alembic.ini",
    "backend/app/db/migrations/env.py",
    "backend/app/db/migrations/script.py.mako",
    "backend/app/db/migrations/sql/20260911_0028_obligation_expectations.sql",
    "backend/app/db/migrations/sql/20260911_0028_obligation_integrity.sql",
    "backend/app/db/migrations/sql/20260913_0029_review_case_integrity.sql",
    "backend/app/db/migrations/versions/20260913_0029_add_ad_v4_review_cases.py",
    "backend/app/core/config.py",
    "backend/app/db/base.py",
    "backend/app/models/core.py",
    "backend/app/__init__.py",
    "backend/app/core/__init__.py",
    "backend/app/db/__init__.py",
    "backend/app/models/__init__.py",
]


@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
@pytest.mark.parametrize("mutation", ["remove", "rename", "content"])
def test_complete_authority_rejects_candidate_drift(candidate_verifier, target, mutation) -> None:
    verifier, policy, tree = candidate_verifier
    path = target.encode()
    if mutation == "remove":
        del tree[path]
    elif mutation == "rename":
        tree[path + b".renamed"] = tree.pop(path)
    else:
        if path.endswith(b".sql"):
            tree[path] += b"\nDROP TABLE users;\n"
        elif path.endswith(b".ini"):
            tree[path] = tree[path].replace(b"script_location = app/db/migrations", b"script_location = unreviewed")
        elif path.endswith(b".mako"):
            tree[path] += b"\n${unreviewed_template_input}\n"
        else:
            tree[path] += b'\nraise RuntimeError("unreviewed execution")\n'
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    expected = "migration authority blob differs:" if mutation == "content" else "migration authority inventory differs:"
    assert any(error.startswith(expected) for error in result["errors"])
    if target == "backend/app/models/core.py" and mutation == "content":
        assert "protected release blob differs: backend/app/models/core.py" in result["errors"]


@pytest.mark.parametrize("path", [
    b"backend/app/db/migrations/versions/new.py",
    b"backend/app/db/migrations/sql/new.sql",
    b"backend/app/db/migrations/sql/new.json",
    b"backend/app/db/migrations/other-sidecar.bin",
    b"backend/app/db/migrations/new.ini",
    b"backend/app/db/migrations/new.mako",
])
def test_complete_authority_rejects_candidate_additions(candidate_verifier, path) -> None:
    verifier, policy, tree = candidate_verifier
    tree[path] = b"unapproved migration input"
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    assert any(error.startswith("migration authority inventory differs:") for error in result["errors"])


@pytest.mark.parametrize("suffix", [
    b'quote".json', b"back\\slash.json", b"tab\t.json", b"line\nbreak.json",
    "non-ascii-é.json".encode(), b"non-utf8-\xff.json",
])
@pytest.mark.parametrize("prefix", [
    b"backend/app/db/migrations/sql/",
    b".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/",
])
def test_raw_git_path_bytes_cannot_evade_boundaries(candidate_verifier, suffix, prefix) -> None:
    verifier, policy, tree = candidate_verifier
    path = prefix + suffix
    tree[path] = b"unreviewed"
    assert path in verifier.tree_paths(REPO_ROOT, "candidate")
    result = verifier.verify_release(REPO_ROOT, "candidate", policy)
    assert result["status"] == "fail"
    if prefix.startswith(b".ai/"):
        assert result["excludedPathsPresent"] == [path.decode("utf-8", "surrogateescape")]
    else:
        assert any(error.startswith("migration authority inventory differs:") for error in result["errors"])
    rendered = json.dumps(result, sort_keys=True, ensure_ascii=True)
    assert json.loads(rendered) == result
    assert rendered.encode("ascii")


def migration_source(revision, predecessor, extra=b"") -> bytes:
    return (f"revision = {revision!r}\ndown_revision = {predecessor!r}\n"
            "branch_labels = None\ndepends_on = None\n").encode() + extra


@pytest.mark.parametrize(("sources", "error"), [
    ([migration_source("root", None), migration_source("cycle_a", "cycle_b"), migration_source("cycle_b", "cycle_a")], "contains a cycle"),
    ([migration_source("root", None), migration_source("other", "missing")], "predecessors are missing"),
    ([migration_source("root", None), migration_source("root", None)], "duplicate migration revision"),
    ([migration_source("root", None), migration_source("other", ["root", "root"])], "duplicate down_revision"),
    ([migration_source("root", None), migration_source("other", [1])], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", "")], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", [])], "invalid down_revision"),
    ([migration_source("root", None), migration_source("other", None)], "exactly one root"),
    ([migration_source("root", "root")], "contains a cycle"),
    ([migration_source("root", None, b'\nrevision = "override"\n')], "revision exactly once"),
    ([migration_source("root", None, b'\ndef mutate():\n    revision = "override"\n')], "revision exactly once"),
    ([migration_source("root", None, b'\ndown_revision = "override"\n')], "down_revision exactly once"),
    ([migration_source("root", None, b'\nbranch_labels = None\n')], "branch_labels exactly once"),
    ([migration_source("root", None, b'\ndepends_on = None\n')], "depends_on exactly once"),
    ([migration_source("root", None).replace(b"depends_on = None", b'depends_on = "missing"')], "unsupported migration depends_on"),
    ([migration_source("root", None).replace(b"branch_labels = None", b'branch_labels = "alias"')], "unsupported migration branch_labels"),
])
def test_complete_graph_rejects_invalid_candidate_metadata(sources, error) -> None:
    verifier = load_release_verifier()
    tree = {f"backend/app/db/migrations/versions/{i}.py".encode(): source
            for i, source in enumerate(sources)}
    verifier.blob_bytes = lambda repo, commit, path: tree[path]
    with pytest.raises(ValueError, match=error):
        verifier.migration_heads(REPO_ROOT, "candidate", sorted(tree))


@pytest.fixture
def context_builder(candidate_verifier, monkeypatch):
    verifier, policy, tree = candidate_verifier
    monkeypatch.setitem(sys.modules, "verify_pilot_release_boundary", verifier)
    spec = importlib.util.spec_from_file_location(
        "build_pilot_migration_context", REPO_ROOT / "scripts/build_pilot_migration_context.py"
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder, verifier, policy, tree


def test_sealed_context_reproducible_and_excludes_arbitrary_checkout_inputs(context_builder, tmp_path):
    builder, _, policy, tree = context_builder
    for name in ("psycopg", "sqlalchemy", "alembic", "sitecustomize", "random_" + uuid.uuid4().hex):
        tree[f"backend/{name}.py".encode()] = b'raise RuntimeError("checkout sentinel")\n'
        tree[f"backend/{name}/__init__.py".encode()] = b'raise RuntimeError("checkout sentinel")\n'
    tree[b"backend/.env"] = b"DATABASE_URL=must-never-enter-the-context\n"
    tree[b"backend/app/core/config/__init__.py"] = b'raise RuntimeError("checkout sentinel")\n'
    tree[b"backend/app/__pycache__/__init__.cpython-312.pyc"] = b"unreviewed bytecode"
    first, second = tmp_path / "first", tmp_path / "second"
    first_manifest = builder.build_context(REPO_ROOT, "candidate", policy, first)
    second_manifest = builder.build_context(REPO_ROOT, "candidate", policy, second)
    assert first_manifest == second_manifest
    assert builder.verify_context(REPO_ROOT, "candidate", policy, first) == first_manifest
    body = {key: value for key, value in first_manifest.items() if key != "manifestSha256"}
    assert hashlib.sha256(builder.canonical_json(body)).hexdigest() == first_manifest["manifestSha256"]
    expected = {source.removeprefix("backend/") for source in policy["approvedMigrationAuthoritySha256"]}
    expected.add("migration-context.json")
    assert {str(path.relative_to(first)) for path in first.rglob("*") if path.is_file()} == expected
    for entry in first_manifest["files"]:
        assert entry["destinationPath"] == entry["sourcePath"].removeprefix("backend/")
        assert entry["gitMode"] == "100644"
        assert entry["sizeBytes"] == len(tree[entry["sourcePath"].encode()])
    for relative in expected:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()
        assert stat.S_IMODE((first / relative).stat().st_mode) == 0o444
    assert stat.S_IMODE(first.stat().st_mode) == 0o555
    assert b"must-never-enter" not in (first / "migration-context.json").read_bytes()


@pytest.mark.parametrize("mode_kind", [(b"120000", b"blob"), (b"160000", b"commit"), (b"100755", b"blob"), (b"040000", b"tree")])
@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
def test_builder_rejects_changed_source_modes_before_output(context_builder, tmp_path, mode_kind, target):
    builder, verifier, policy, _ = context_builder
    verifier.candidate_modes[target.encode()] = mode_kind
    destination = tmp_path / "context"
    with pytest.raises(builder.ContextError, match="unapproved Git mode/type"):
        builder.build_context(REPO_ROOT, "candidate", policy, destination)
    assert not destination.exists()


@pytest.mark.parametrize("mutation", ["remove", "rename", "content"])
@pytest.mark.parametrize("target", AUTHORITY_MUTATION_TARGETS)
def test_builder_rejects_changed_source_inventory_and_bytes(context_builder, tmp_path, mutation, target):
    builder, _, policy, tree = context_builder
    path = target.encode()
    if mutation == "remove":
        del tree[path]
    elif mutation == "rename":
        tree[path + b".renamed"] = tree.pop(path)
    else:
        tree[path] += b"\n# candidate mutation\n"
    with pytest.raises(builder.ContextError, match="release source check failed"):
        builder.build_context(REPO_ROOT, "candidate", policy, tmp_path / "context")
    assert not (tmp_path / "context").exists()


@pytest.mark.parametrize("path", [b"/absolute", b"backend/../alembic.ini", b"backend//alembic.ini", b"backend/./alembic.ini", b"backend/invalid-\xff.py", b"backend\\alembic.ini"])
def test_context_paths_reject_noncanonical_or_non_utf8_names(context_builder, path):
    builder, _, _, _ = context_builder
    with pytest.raises(builder.ContextError):
        builder.destination_path(path)


def test_context_rejects_duplicate_git_names_and_json_keys(context_builder, monkeypatch):
    builder, verifier, _, _ = context_builder
    record = b"100644 blob " + b"0" * 40 + b"\tbackend/alembic.ini\0"
    monkeypatch.setattr(verifier, "git", lambda *args: subprocess.CompletedProcess(args, 0, record + record, b""))
    with pytest.raises(builder.ContextError, match="duplicate Git tree path"):
        builder.tree_records(REPO_ROOT, "a" * 40)
    with pytest.raises(ValueError, match="duplicate JSON object key"):
        json.loads('{"sourcePath":"first","sourcePath":"second"}', object_pairs_hook=verifier.unique_json_object)


def test_real_git_modes_and_pre_package_a_builder_fail_closed(context_builder, tmp_path, monkeypatch):
    builder, _, policy, _ = context_builder
    monkeypatch.setattr(builder, "boundary", load_release_verifier())
    baseline = policy["approvedBaselineCommit"]
    records = builder.tree_records(REPO_ROOT, baseline)
    assert all(records[path.encode()] == (b"100644", b"blob")
               for path in policy["approvedMigrationAuthoritySha256"])
    with pytest.raises(builder.ContextError, match="migration authority blob differs: backend/app/core/config.py"):
        builder.build_context(REPO_ROOT, baseline, policy, tmp_path / "context")
    assert not (tmp_path / "context").exists()


@pytest.mark.parametrize("existing_kind", ["directory", "file", "symlink", "parent_symlink"])
def test_context_never_reuses_or_follows_existing_destinations(context_builder, tmp_path, existing_kind):
    builder, _, policy, _ = context_builder
    existing = tmp_path / "existing"
    if existing_kind == "directory":
        existing.mkdir()
    elif existing_kind == "file":
        existing.write_text("preserve me")
    else:
        target = tmp_path / "target"
        target.mkdir()
        existing.symlink_to(target, target_is_directory=True)
    destination = existing / "child" if existing_kind == "parent_symlink" else existing
    with pytest.raises(OSError):
        builder.build_context(REPO_ROOT, "candidate", policy, destination)
    if existing_kind == "file":
        assert existing.read_text() == "preserve me"
    if existing_kind in {"symlink", "parent_symlink"}:
        assert not list((tmp_path / "target").iterdir())


@pytest.mark.parametrize("target", [source.removeprefix("backend/") for source in AUTHORITY_MUTATION_TARGETS] + ["migration-context.json"])
@pytest.mark.parametrize("mutation", ["remove", "rename", "content", "symlink", "mode"])
def test_context_verification_rejects_tampering_in_every_manifest_class(context_builder, tmp_path, target, mutation):
    builder, _, policy, _ = context_builder
    context = tmp_path / "context"
    builder.build_context(REPO_ROOT, "candidate", policy, context)
    path = context / target
    path.parent.chmod(0o755)
    if mutation == "remove":
        path.unlink()
    elif mutation == "rename":
        path.rename(path.with_name(path.name + ".renamed"))
    elif mutation == "content":
        path.chmod(0o644)
        path.write_bytes(path.read_bytes() + b"\nmutated\n")
        path.chmod(0o444)
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to(tmp_path / "outside-context")
    else:
        path.chmod(0o644)
    path.parent.chmod(0o555)
    with pytest.raises(builder.ContextError):
        builder.verify_context(REPO_ROOT, "candidate", policy, context)


@pytest.mark.parametrize("extra", [".env", "psycopg.py", "app/__pycache__/injected.pyc", "empty-directory/"])
def test_context_verification_rejects_extra_files_or_directories(context_builder, tmp_path, extra):
    builder, _, policy, _ = context_builder
    context = tmp_path / "context"
    builder.build_context(REPO_ROOT, "candidate", policy, context)
    for parent in [context, context / "app"]:
        parent.chmod(0o755)
    target = context / extra.rstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    if extra.endswith("/"):
        target.mkdir(mode=0o555)
    else:
        target.write_bytes(b"unapproved")
        target.chmod(0o444)
    for parent in [target.parent, context / "app", context]:
        parent.chmod(0o555)
    with pytest.raises(builder.ContextError):
        builder.verify_context(REPO_ROOT, "candidate", policy, context)


IMPORT_BOUNDARY_ORACLE = r'''
import json, os, sys, sysconfig
from pathlib import Path
import alembic, sqlalchemy
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

class DriverLoaded(Exception):
    pass

report = {"engineCalled": False, "sentinel": False, "driverOrigin": None, "driverName": None}
original_engine_from_config = sqlalchemy.engine_from_config
def observed_engine_from_config(*args, **kwargs):
    report["engineCalled"] = True
    engine = original_engine_from_config(*args, **kwargs)
    report["driverOrigin"] = str(Path(engine.dialect.dbapi.__file__).resolve())
    report["driverName"] = engine.dialect.dbapi.__name__
    raise DriverLoaded()
sqlalchemy.engine_from_config = observed_engine_from_config
config = Config(str(Path.cwd() / "alembic.ini"))
scripts = ScriptDirectory.from_config(config)
try:
    with EnvironmentContext(config, scripts):
        scripts.run_env()
except DriverLoaded:
    pass
except RuntimeError as exc:
    if str(exc) != "CHECKOUT_PSYCOPG_SENTINEL":
        raise
    report["sentinel"] = True
report["imports"] = {"alembic": str(Path(alembic.__file__).resolve()),
                     "sqlalchemy": str(Path(sqlalchemy.__file__).resolve())}
report["sitePackages"] = sorted({str(Path(sysconfig.get_path(name)).resolve()) for name in ("purelib", "platlib")})
report["sysPath"] = [str(Path(path or ".").resolve()) for path in sys.path]
report["bytecodeDisabled"] = sys.dont_write_bytecode
from app.core.config import get_settings
report["explicitDatabaseSelected"] = get_settings().database_url == os.environ["DATABASE_URL"]
report["dotenvDisabled"] = os.environ["PAPRNAV_DISABLE_DOTENV"] == "1"
report["dotenvNotLoaded"] = get_settings().storage_backend != "dotenv-sentinel"
print(json.dumps(report, sort_keys=True))
'''


@pytest.mark.parametrize("sentinel_path", [b"backend/psycopg.py", b"backend/psycopg/__init__.py"])
def test_real_alembic_engine_imports_checkout_sentinel_only_in_vulnerable_control(context_builder, tmp_path, sentinel_path):
    builder, _, policy, tree = context_builder
    tree[sentinel_path] = b'raise RuntimeError("CHECKOUT_PSYCOPG_SENTINEL")\n'
    tree[b"backend/.env"] = b"PAPRNAV_STORAGE_BACKEND=dotenv-sentinel\nDATABASE_URL=forbidden-fallback\n"
    candidate = tmp_path / "candidate"
    for source, content in tree.items():
        target = candidate / source.decode()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    sealed = tmp_path / "sealed"
    builder.build_context(REPO_ROOT, "candidate", policy, sealed)
    database_url = "postgresql+psycopg://oracle:never-connect@127.0.0.1:1/oracle"
    environment = builder.launch_environment({"DATABASE_URL": database_url, "PAPRNAV_DISABLE_DOTENV": "0", "PYTHONPATH": str(REPO_ROOT / "backend")})
    reports = []
    for cwd in [candidate / "backend", sealed]:
        process = subprocess.run([sys.executable, "-I", "-B", "-c", IMPORT_BOUNDARY_ORACLE],
                                 cwd=cwd, env=environment, capture_output=True, text=True)
        assert process.returncode == 0, process.stderr
        assert database_url not in process.stdout + process.stderr
        reports.append(json.loads(process.stdout))
    vulnerable, protected = reports
    assert vulnerable["engineCalled"] and vulnerable["sentinel"]
    assert vulnerable["driverOrigin"] is None
    assert str(candidate / "backend") in vulnerable["sysPath"]
    assert protected["engineCalled"] and not protected["sentinel"]
    assert protected["driverOrigin"] is not None
    assert protected["driverName"] == "psycopg"
    for origin in [protected["driverOrigin"], *protected["imports"].values()]:
        assert any(Path(origin).is_relative_to(site) for site in protected["sitePackages"])
        assert not Path(origin).is_relative_to(sealed)
    for entry in protected["sysPath"]:
        assert not Path(entry).is_relative_to(candidate)
        # This project's interpreter is in an ignored backend/.venv directory.
        # Only its exact canonical installed-package root is allowed there;
        # no checkout source directory or editable-install path may be present.
        if Path(entry).is_relative_to(REPO_ROOT):
            assert entry in protected["sitePackages"]
    assert protected["bytecodeDisabled"] and protected["dotenvDisabled"] and protected["explicitDatabaseSelected"]
    assert vulnerable["dotenvNotLoaded"] and protected["dotenvNotLoaded"]
    assert not list(sealed.rglob("__pycache__"))
    assert builder.verify_context(REPO_ROOT, "candidate", policy, sealed)


def test_launcher_requires_database_and_suppresses_child_secret_output(context_builder, tmp_path, monkeypatch):
    builder, _, policy, _ = context_builder
    for env in ({}, {"DATABASE_URL": ""}, {"DATABASE_URL": "  "}):
        with pytest.raises(builder.ContextError, match="DATABASE_URL must be supplied"):
            builder.run_context(REPO_ROOT, "candidate", policy, tmp_path / "absent", env)
    secret_url = "postgresql+psycopg://operator:runtime-secret@db/pilot"
    environment = builder.launch_environment({"DATABASE_URL": secret_url, "PAPRNAV_DISABLE_DOTENV": "0", "PYTHONPATH": "untrusted"})
    assert environment == {"DATABASE_URL": secret_url, "PAPRNAV_DISABLE_DOTENV": "1", "PYTHONDONTWRITEBYTECODE": "1", "PAPRNAV_ENV": "pilot"}
    context = tmp_path / "sealed"
    manifest = builder.build_context(REPO_ROOT, "candidate", policy, context)
    assert secret_url not in json.dumps(manifest)

    def failing_child(command, **kwargs):
        assert command == builder.launch_command(context, policy, sys.executable)
        assert command[1:5] == ["-I", "-B", "-m", "alembic"]
        assert command[-2:] == ["upgrade", "20260913_0029"]
        assert kwargs["cwd"] == context
        assert kwargs["env"] == environment
        assert kwargs["capture_output"] is True
        return subprocess.CompletedProcess(command, 1, secret_url.encode(), secret_url.encode())

    monkeypatch.setattr(builder.subprocess, "run", failing_child)
    with pytest.raises(builder.ContextError, match="child output suppressed") as failure:
        builder.run_context(REPO_ROOT, "candidate", policy, context, environment)
    assert secret_url not in str(failure.value)

```
### `scripts/build_pilot_migration_context.py`

size=12566; sha256=8f0f8a24cd6aaf6bb5583bcae4f05abdd47b2553ebe7efb4c366fe01ba7d637e; truncated=false

```text
#!/usr/bin/env python3
"""Build, verify, or launch a sealed context from reviewed Git commit blobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

import verify_pilot_release_boundary as boundary


CONTEXT_POLICY = {
    "version": "paprnav-sealed-migration-context-v1",
    "manifestName": "migration-context.json",
    "sourceGitMode": "100644",
    "sourceToDestination": {
        "backend/alembic.ini": "alembic.ini",
        "backend/app/": "app/",
    },
}
MANIFEST_NAME = CONTEXT_POLICY["manifestName"]
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


class ContextError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def safe_path(raw: bytes) -> str:
    try:
        value = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContextError("context path is not UTF-8") from exc
    if not value or "\\" in value or "\0" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ContextError("context path is not a canonical relative path")
    return value


def destination_path(source: bytes) -> str:
    source_text = safe_path(source)
    if source_text == "backend/alembic.ini":
        return "alembic.ini"
    if source_text.startswith("backend/app/"):
        return safe_path(source[len(b"backend/"):])
    raise ContextError("source has no approved context destination")


def tree_records(repo: Path, commit: str) -> dict[bytes, tuple[bytes, bytes]]:
    raw = boundary.git(repo, "ls-tree", "-rz", commit).stdout
    if not raw or not raw.endswith(b"\0"):
        raise ContextError("invalid NUL-delimited Git tree records")
    records: dict[bytes, tuple[bytes, bytes]] = {}
    for record in raw[:-1].split(b"\0"):
        try:
            header, path = record.split(b"\t", 1)
            mode, kind, object_id = header.split(b" ")
        except ValueError as exc:
            raise ContextError("invalid Git tree record") from exc
        if path in records:
            raise ContextError("duplicate Git tree path")
        if not re.fullmatch(b"[0-9a-f]{40}|[0-9a-f]{64}", object_id):
            raise ContextError("invalid Git object identity")
        records[path] = (mode, kind)
    return records


def context_spec(repo: Path, ref: str, policy: dict[str, Any]) -> tuple[dict, dict[str, bytes]]:
    if policy.get("migrationContext") != CONTEXT_POLICY:
        raise ContextError("migration context policy differs from the reviewed mapping/modes")
    # Resolve once; every subsequent read uses the immutable commit identity.
    commit = boundary.resolve_commit(repo, ref)
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ContextError("release ref did not resolve to an exact commit")
    source_paths = policy.get("approvedMigrationAuthoritySha256", {})
    destinations: set[str] = set()
    for source in source_paths:
        try:
            destination = destination_path(source.encode("utf-8", "strict"))
        except UnicodeEncodeError as exc:
            raise ContextError("context path is not UTF-8") from exc
        if destination in destinations or destination == MANIFEST_NAME:
            raise ContextError("duplicate context destination")
        destinations.add(destination)
    release = boundary.verify_release(repo, commit, policy)
    if release["status"] != "pass":
        raise ContextError("release source check failed: " + "; ".join(release["errors"]))
    records = tree_records(repo, commit)
    if set(records) != set(boundary.tree_paths(repo, commit)):
        raise ContextError("Git name and mode inventories differ")
    files: dict[str, bytes] = {}
    entries: list[dict] = []
    for source, expected_hash in sorted(source_paths.items()):
        raw_source = source.encode("utf-8")
        destination = destination_path(raw_source)
        if records.get(raw_source) != (b"100644", b"blob"):
            raise ContextError("context source is missing or has an unapproved Git mode/type")
        content = boundary.blob_bytes(repo, commit, raw_source)
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise ContextError("context source hash differs")
        files[destination] = content
        entries.append({"sourcePath": source, "destinationPath": destination,
                        "gitMode": "100644", "sizeBytes": len(content), "sha256": expected_hash})
    body = {"version": CONTEXT_POLICY["version"], "sourceCommit": commit, "files": entries}
    manifest = {**body, "manifestSha256": hashlib.sha256(canonical_json(body)).hexdigest()}
    files[MANIFEST_NAME] = canonical_json(manifest)
    return manifest, files


def open_directory(path: Path) -> int:
    """Walk from / using descriptors, refusing symlink ancestors as well."""
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise ContextError("destination traversal is forbidden")
    fd = os.open(absolute.anchor, DIRECTORY_FLAGS)
    try:
        for part in absolute.parts[1:]:
            next_fd = os.open(part, DIRECTORY_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def file_directories(files: dict[str, bytes]) -> set[str]:
    return {"/".join(path.split("/")[:i]) for path in files for i in range(1, len(path.split("/")))}


def build_context(repo: Path, ref: str, policy: dict, destination: Path) -> dict:
    manifest, files = context_spec(repo, ref, policy)
    destination = destination.absolute()
    if destination.name in {"", ".", ".."}:
        raise ContextError("a new context directory is required")
    parent_fd = open_directory(destination.parent)
    try:
        # No overwrite, merge, reuse, or symlink following is permitted.
        os.mkdir(destination.name, mode=0o700, dir_fd=parent_fd)
        root_fd = os.open(destination.name, DIRECTORY_FLAGS, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)
    directories = {"": root_fd}
    try:
        for path in sorted(file_directories(files), key=lambda item: (item.count("/"), item)):
            parent, _, name = path.rpartition("/")
            os.mkdir(name, mode=0o700, dir_fd=directories[parent])
            directories[path] = os.open(name, DIRECTORY_FLAGS, dir_fd=directories[parent])
        for path, content in sorted(files.items()):
            parent, _, name = path.rpartition("/")
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directories[parent])
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fchmod(output.fileno(), 0o444)
        for path in sorted(directories, key=lambda item: (item.count("/"), item), reverse=True):
            os.fchmod(directories[path], 0o555)
    finally:
        # On an I/O failure an incomplete directory is left for inspection. It
        # cannot be reused and cannot pass exact verification.
        for fd in directories.values():
            os.close(fd)
    verify_files(destination, files)
    return manifest


def verify_files(destination: Path, expected_files: dict[str, bytes]) -> None:
    seen_files: set[str] = set()
    seen_dirs: set[str] = set()

    def walk(fd: int, prefix: str) -> None:
        if stat.S_IMODE(os.fstat(fd).st_mode) != 0o555:
            raise ContextError("context directory is not read-only")
        for name in sorted(os.listdir(fd)):
            relative = prefix + name
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                seen_dirs.add(relative)
                child = os.open(name, DIRECTORY_FLAGS, dir_fd=fd)
                try:
                    walk(child, relative + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                if relative not in expected_files:
                    raise ContextError("context contains an unlisted file")
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                with os.fdopen(child, "rb") as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o444 or info.st_nlink != 1:
                        raise ContextError("context file has an unapproved type/mode/link count")
                    if source.read() != expected_files[relative]:
                        raise ContextError("context file or manifest bytes differ")
                seen_files.add(relative)
            else:
                raise ContextError("context contains a symlink or non-regular file")

    root = open_directory(destination)
    try:
        walk(root, "")
    finally:
        os.close(root)
    if seen_files != set(expected_files) or seen_dirs != file_directories(expected_files):
        raise ContextError("context inventory differs")


def verify_context(repo: Path, ref: str, policy: dict, destination: Path) -> dict:
    manifest, files = context_spec(repo, ref, policy)
    verify_files(destination, files)
    return manifest


def launch_environment(runtime_environment: dict[str, str]) -> dict[str, str]:
    database_url = runtime_environment.get("DATABASE_URL", "")
    if not database_url.strip():
        raise ContextError("DATABASE_URL must be supplied at launch; development fallback is forbidden")
    return {"DATABASE_URL": database_url, "PAPRNAV_DISABLE_DOTENV": "1",
            "PYTHONDONTWRITEBYTECODE": "1", "PAPRNAV_ENV": "pilot"}


def launch_command(destination: Path, policy: dict, interpreter: str) -> list[str]:
    # -I ignores PYTHON* environment variables, so -B is required as well as
    # PYTHONDONTWRITEBYTECODE for explicit bytecode suppression.
    return [str(Path(interpreter).absolute()), "-I", "-B", "-m", "alembic", "-c",
            str(destination.absolute() / "alembic.ini"), "upgrade", policy["expectedMigrationHeads"][0]]


def run_context(repo: Path, ref: str, policy: dict, destination: Path,
                runtime_environment: dict[str, str], interpreter: str = sys.executable) -> dict:
    environment = launch_environment(runtime_environment)
    manifest = verify_context(repo, ref, policy, destination)
    result = subprocess.run(launch_command(destination, policy, interpreter),
                            cwd=destination, env=environment, capture_output=True)
    # Never forward child output: driver/configuration exceptions can contain
    # the runtime URL. The source manifest never records runtime credentials.
    if result.returncode:
        raise ContextError("migration process failed; child output suppressed")
    verify_context(repo, ref, policy, destination)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify", "run"))
    parser.add_argument("--ref", required=True)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--policy", default=boundary.DEFAULT_POLICY_PATH)
    args = parser.parse_args()
    try:
        repo = Path(boundary.path_text(boundary.git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.rstrip(b"\n")))
        policy_path = (repo / args.policy).resolve()
        policy_path.relative_to(repo)
        policy = json.loads(policy_path.read_text(encoding="utf-8"), object_pairs_hook=boundary.unique_json_object)
        if args.action == "build":
            manifest = build_context(repo, args.ref, policy, args.destination)
        elif args.action == "verify":
            manifest = verify_context(repo, args.ref, policy, args.destination)
        else:
            manifest = run_context(repo, args.ref, policy, args.destination, dict(os.environ))
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps({"status": "pass", "sourceCommit": manifest["sourceCommit"],
                      "manifestSha256": manifest["manifestSha256"], "fileCount": len(manifest["files"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `scripts/verify_pilot_release_boundary.py`

size=11997; sha256=0021bff593434e97eebd5f143aa876c160c35b1650224cd9580946cc441fe8cf; truncated=false

```text
#!/usr/bin/env python3
"""Verify an explicit Git commit, not the working tree, as a pilot release input."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


DEFAULT_POLICY_PATH = ".ai/pilot-release-boundary-v1.json"
MIGRATION_TREE_PREFIX = b"backend/app/db/migrations/"
MIGRATION_PREFIX = MIGRATION_TREE_PREFIX + b"versions/"
# Reviewed repository inputs to the sealed migration context. This source
# verifier does not establish isolation of a full application's import path.
MIGRATION_SUPPORT_PATHS = frozenset({
    b"backend/alembic.ini",
    b"backend/app/__init__.py",
    b"backend/app/core/__init__.py",
    b"backend/app/core/config.py",
    b"backend/app/db/__init__.py",
    b"backend/app/db/base.py",
    b"backend/app/models/__init__.py",
    b"backend/app/models/core.py",
})


def path_text(path: bytes) -> str:
    """Lossless JSON-facing name; json.dumps escapes controls and surrogates."""
    return path.decode("utf-8", errors="surrogateescape")


def git(repo: Path, *args: str | bytes, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result


def resolve_commit(repo: Path, ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ValueError("release ref must be an explicit non-option Git ref")
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def tree_paths(repo: Path, commit: str) -> list[bytes]:
    raw = git(repo, "ls-tree", "-rz", "--name-only", commit).stdout
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise ValueError("Git tree inventory is not NUL terminated")
    paths = raw[:-1].split(b"\0")
    if any(not path for path in paths) or len(paths) != len(set(paths)):
        raise ValueError("Git tree inventory has empty or duplicate paths")
    return sorted(paths)


def blob_bytes(repo: Path, commit: str, path: bytes) -> bytes:
    return git(repo, "show", commit.encode("ascii") + b":" + path).stdout


def excluded_paths(paths: list[bytes], policy: dict[str, Any]) -> list[bytes]:
    exact = {path.encode("utf-8", "surrogateescape") for path in policy.get("excludedTreePaths", [])}
    prefixes = tuple(path.encode("utf-8", "surrogateescape") for path in policy.get("excludedTreePrefixes", []))
    return sorted(path for path in paths if path in exact or path.startswith(prefixes))


def assignment_value(tree: ast.Module, name: str) -> Any:
    stores = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Store)
        and node.id == name
    ]
    assignments: list[ast.expr] = []
    for node in tree.body:
        target_name = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            target_name = target.id if isinstance(target, ast.Name) else None
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target_name = node.target.id if isinstance(node.target, ast.Name) else None
            value = node.value
        if target_name == name and value is not None:
            assignments.append(value)
    if len(stores) != 1 or len(assignments) != 1:
        raise ValueError(
            f"migration must declare {name} exactly once at module scope; "
            f"found {len(stores)} assignments"
        )
    return ast.literal_eval(assignments[0])


def migration_heads(repo: Path, commit: str, paths: list[bytes]) -> list[str]:
    revisions: set[str] = set()
    predecessors: set[str] = set()
    graph: dict[str, tuple[str, ...]] = {}
    for path in paths:
        if not path.startswith(MIGRATION_PREFIX) or not path.endswith(b".py"):
            continue
        tree = ast.parse(blob_bytes(repo, commit, path).decode("utf-8"), filename=path_text(path))
        revision = assignment_value(tree, "revision")
        down_revision = assignment_value(tree, "down_revision")
        # The approved graph has no branch aliases or dependency edges. Reject
        # them explicitly rather than silently deriving a partial graph.
        for name in ("branch_labels", "depends_on"):
            if assignment_value(tree, name) is not None:
                raise ValueError(f"unsupported migration {name} in {path_text(path)}")
        if not isinstance(revision, str) or not revision:
            raise ValueError(f"invalid migration revision in {path}")
        if revision in revisions:
            raise ValueError(f"duplicate migration revision: {revision}")
        revisions.add(revision)
        if isinstance(down_revision, str):
            if not down_revision:
                raise ValueError(f"invalid down_revision in {path_text(path)}")
            predecessors.add(down_revision)
            graph[revision] = (down_revision,)
        elif isinstance(down_revision, (tuple, list)):
            if not down_revision or not all(isinstance(item, str) and item for item in down_revision):
                raise ValueError(f"invalid down_revision in {path}")
            if len(set(down_revision)) != len(down_revision):
                raise ValueError(f"duplicate down_revision in {path}")
            graph[revision] = tuple(down_revision)
            predecessors.update(down_revision)
        elif down_revision is None:
            graph[revision] = ()
        elif down_revision is not None:
            raise ValueError(f"invalid down_revision in {path}")
    if not revisions:
        raise ValueError("release tree has no Alembic revisions")
    missing = sorted(predecessors - revisions)
    if missing:
        raise ValueError(f"migration predecessors are missing: {missing}")

    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(revision: str) -> None:
        if revision in visiting:
            raise ValueError(f"migration graph contains a cycle at {revision}")
        if revision in visited:
            return
        visiting.add(revision)
        for predecessor in graph[revision]:
            visit(predecessor)
        visiting.remove(revision)
        visited.add(revision)

    for revision in sorted(revisions):
        visit(revision)
    roots = sorted(revision for revision, parents in graph.items() if not parents)
    if len(roots) != 1:
        raise ValueError(f"migration graph must have exactly one root: {roots}")
    return sorted(revisions - predecessors)


def migration_authority_paths(paths: list[bytes]) -> list[bytes]:
    return sorted(path for path in paths if path.startswith(MIGRATION_TREE_PREFIX)
                  or path in MIGRATION_SUPPORT_PATHS)


def unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def verify_migration_inventory(
    repo: Path,
    commit: str,
    paths: list[bytes],
    policy: dict[str, Any],
) -> tuple[dict[str, dict[str, str]], list[str]]:
    expected = policy.get("approvedMigrationAuthoritySha256", {})
    if not isinstance(expected, dict) or not expected:
        return {}, ["approved migration authority inventory is missing"]
    expected = {path.encode("utf-8", "surrogateescape"): value for path, value in expected.items()}
    actual_paths = migration_authority_paths(paths)
    expected_paths = sorted(expected)
    errors: list[str] = []
    if not MIGRATION_SUPPORT_PATHS.issubset(expected) or migration_authority_paths(expected_paths) != expected_paths:
        errors.append("approved migration authority inventory has an invalid scope")
    if actual_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(actual_paths))
        unapproved = sorted(set(actual_paths) - set(expected_paths))
        errors.append(
            f"migration authority inventory differs: missing {missing}, unapproved {unapproved}"
        )

    results: dict[str, dict[str, str]] = {}
    for path in sorted(set(actual_paths) & set(expected_paths)):
        expected_hash = expected[path]
        actual_hash = hashlib.sha256(blob_bytes(repo, commit, path)).hexdigest()
        results[path_text(path)] = {
            "expectedSha256": expected_hash,
            "actualSha256": actual_hash,
        }
        if actual_hash != expected_hash:
            errors.append(f"migration authority blob differs: {path_text(path)}")
    return results, errors


def verify_release(repo: Path, ref: str, policy: dict[str, Any]) -> dict[str, Any]:
    commit = resolve_commit(repo, ref)
    baseline = str(policy["approvedBaselineCommit"])
    ancestor = git(repo, "merge-base", "--is-ancestor", baseline, commit, check=False)
    errors: list[str] = []
    if ancestor.returncode:
        errors.append(f"approved baseline {baseline} is not an ancestor of {commit}")

    paths = tree_paths(repo, commit)
    found_excluded = excluded_paths(paths, policy)
    if found_excluded:
        errors.append(f"release tree contains excluded paths: {found_excluded}")

    protected_results: dict[str, dict[str, str]] = {}
    for path, expected_hash in sorted(policy.get("protectedBlobSha256", {}).items()):
        try:
            actual_hash = hashlib.sha256(blob_bytes(repo, commit, path.encode("utf-8", "surrogateescape"))).hexdigest()
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        protected_results[path] = {"expectedSha256": expected_hash, "actualSha256": actual_hash}
        if actual_hash != expected_hash:
            errors.append(f"protected release blob differs: {path}")

    try:
        migration_blobs, migration_blob_errors = verify_migration_inventory(
            repo, commit, paths, policy
        )
        errors.extend(migration_blob_errors)
    except RuntimeError as exc:
        migration_blobs = {}
        errors.append(str(exc))

    try:
        heads = migration_heads(repo, commit, paths)
    except (SyntaxError, UnicodeDecodeError, ValueError, RuntimeError) as exc:
        heads = []
        errors.append(str(exc))
    expected_heads = sorted(policy.get("expectedMigrationHeads", []))
    if heads != expected_heads:
        errors.append(f"migration heads differ: expected {expected_heads}, got {heads}")

    return {
        "version": policy["version"],
        "status": "pass" if not errors else "fail",
        "commit": commit,
        "approvedBaselineCommit": baseline,
        "migrationHeads": heads,
        "expectedMigrationHeads": expected_heads,
        "migrationAuthorityBlobs": migration_blobs,
        "excludedPathsPresent": [path_text(path) for path in found_excluded],
        "protectedBlobs": protected_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True, help="Explicit Git commit or ref to inspect")
    parser.add_argument("--policy", default=DEFAULT_POLICY_PATH)
    args = parser.parse_args()

    repo = Path(path_text(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.rstrip(b"\n")))
    policy_path = (repo / args.policy).resolve()
    try:
        policy_path.relative_to(repo)
    except ValueError as exc:
        raise SystemExit("policy path must remain inside the repository") from exc
    policy = json.loads(policy_path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_object)
    result = verify_release(repo, args.ref, policy)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

```
