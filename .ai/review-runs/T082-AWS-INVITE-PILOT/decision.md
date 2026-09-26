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

## Governing 30-day delivery objective

By **2026-10-19**, deploy an invite-only AWS pilot that lets at least one
external invited user sign in, manage an aircraft, upload and review a
logbook, use the existing decision-support workflow, submit feedback, and
generate attributable error, achievement, OCR-cost, and AWS-cost evidence.

This is the governing definition of completion for T082. The delivery rules,
scope filter, cadence, and review/test ceilings in
`delivery-objective-amendment.md` override any broader or more exhaustive
reading of this packet. Safety and release gates named there remain mandatory;
post-pilot completeness does not. The current daily gate status lives in
`delivery-scoreboard.md`.

The pilot release requires HTTPS invite-only accounts, tenant isolation and
secure sessions, private PostgreSQL with backups, the aircraft/logbook/upload/
OCR/existing-AD journey, feedback and attributable operational/cost evidence,
budget alerts and paid-operation ceilings, deployment and rollback procedures,
and one successful external invited-user run. Unfinished V4 functionality stays
disabled unless a concrete pilot gate proves it is required.

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

The package table is subordinate to the delivery amendment. Only one
critical-path package may be in progress. Each coherent family receives at most
one implementation review after its targeted evidence is complete; generated
artifacts, hashes, individual files, and marginal corrections are included in
that packet rather than reviewed separately. A failed mandatory gate stops and
reframes the family; the review budget never authorizes shipping through a
failed security, durability, provider, migration, or release gate.

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

The numbered cases below are requirements only when their dependency is changed
or when they protect a pilot-critical gate. The default package budget is one
targeted regression suite plus the applicable end-to-end pilot path, followed
by one independent family review. Broaden or repeat testing only after a
relevant failure or dependency change. No Cartesian corruption or exhaustive
schema matrix belongs in T082 unless it protects authorization, tenant
isolation, destructive data behavior, migration correctness, provider
idempotency/spend, or another explicit pilot release gate.

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
