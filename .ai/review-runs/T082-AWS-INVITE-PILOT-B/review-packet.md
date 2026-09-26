# Review packet: T082-AWS-INVITE-PILOT-B

Stage: implementation
Generated: 2026-09-19T17:23:00+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `16eefcc2e01884c0855c5e4cb0db589e4c2970abbc5ed3bee878b5f2010af236`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: T082 AWS invite pilot — Package B

## Objective and authority

Implement the invite-only authentication, browser session boundary, and
tenant-safe observability/feedback family required before an AWS pilot can
accept external users.

This child run introduces no new design. Its normative authority is the
independently approved parent design:

- `../T082-AWS-INVITE-PILOT/decision.md` SHA-256
  `69c2cce98e90b2902e172ef067800ee6bfdbdaaef3f701b8fe492a694d977f71`;
- `../T082-AWS-INVITE-PILOT/design-remediation-1.md` SHA-256
  `2909b5b0e14af10e41eb6a7b762df28e47f3d91c16c35627db8064e375f31506`;
- `../T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md` SHA-256
  `78442e342fb36fb3732cc95d7e9e77f49842b3a5e35dffe49c920c6e2d496018`.

The design reviewer already closed the invitation, session/CSRF, role/type,
same-origin, observability, feedback, and revocation decisions before this
implementation began. The Package B design gate therefore asks only whether
the implementation stayed inside that approved authority; it must not reopen
or expand the design without a new finding.

## User-visible outcome

At most ten invited pilot users can paste a short-lived operator-generated
code, choose a password, receive a secure session, and use the existing product.
They cannot self-register or read another tenant's operational records.
Platform administrators retain a separate bounded cross-tenant view and
feedback-triage authority.

## Safety and correctness invariants

1. Only active platform administrators generate invitations. Codes are
   canonical versioned HMAC-SHA256 bearer credentials using a dedicated secret,
   random nonce, normalized email, maximum 24-hour lifetime, and at most five
   minutes of skew.
2. Only `owner`/`owner_admin` and
   `maintenance_shop`/`maintenance_admin` pairings can be signed or accepted;
   `platform_admin` can never be invited.
3. Successful acceptance atomically creates exactly one user, organization,
   active membership, session, and sanitized achievement event. Email
   uniqueness prevents successful replay; every acceptance failure is
   non-enumerating.
4. Pilot registration is unavailable. Pilot cookies are Secure, HttpOnly, and
   SameSite=Lax. Unsafe cookie-authenticated requests require the exact approved
   HTTPS Origin or same-origin Referer fallback.
5. Pilot browser API traffic uses direct same-origin `/api/v1/*`; the Next
   development proxy does not forward pilot requests.
6. Session invalidation is an audited database operator command and invalidates
   already-issued cookies.
7. Ordinary observability/feedback reads are current-aircraft scoped; personal
   fallback requires both organization and aircraft to be absent. Revocation
   removes aircraft-bound visibility even when the actor owns the row. Generic
   unresolved workflows remain administrator-only. Only platform admins change
   feedback status.
8. Package A's V4 release boundary remains green and its exact configuration
   target is amended and re-reviewed with Package B.

## Design and data behavior

Invitations remain stateless and add no database table or migration. Acceptance
uses existing users, organizations, memberships, sessions, and product events
in one transaction. The dedicated signing secret is runtime configuration and
is never returned except through a signed code, logged, or stored in event
properties. Global invitation revocation rotates that secret; per-code
revocation remains an explicit post-pilot limitation.

Tenant scope is computed from current active memberships, owner organizations,
and active aircraft assignments. Aircraft-bound product events and feedback use
that live scope. Only known workflow identities with a server-side path to a
visible aircraft are returned to ordinary users. Cross-tenant operations use a
separate platform-admin endpoint.

The frontend exposes `/invite`, hides pilot registration, and calls the backend
through the ALB's direct same-origin API path. Package C/E owns ALB routing, WAF,
Secrets Manager injection, images, tasks, and deployment evidence.

## Compatibility and rollback

Local/test self-registration and the development proxy remain available outside
pilot. No database migration or rewrite occurs. Rollback removes the new
routes/service/UI and restores the prior configuration target as one reviewed
change; existing users/sessions/events remain valid data. Emergency revocation
uses `python -m app.scripts.revoke_auth_sessions --user-id <id>` or `--all`.

## Test and review strategy

Use a bounded matrix: allowed and cross-domain roles, valid/tampered/expired/
future/replayed codes, atomic acceptance, startup settings, cookie flags,
Origin/Referer failures, session revocation, and a two-tenant visibility/
feedback scenario including membership revocation. Re-run the directly affected
auth/AD feedback tests, Package A boundary, and existing V4 API suite. Compile,
lint, type-check, and build the pilot frontend.

One independent Astra-xhigh-requested reviewer assesses design adherence and the
complete implementation family. It must inspect the actual dirty tree and
preserved T081/0030 scope, not only this packet.

## Expected file scope and exclusions

The exact implementation scope is recorded in
`../T082-AWS-INVITE-PILOT/package-b-implementation.md`. No T081 file,
`backend/app/models/core.py`, migration 0030, Terraform, AWS resource, Git index,
or commit belongs to Package B.

## Known uncertainty

- Runtime WAF/routing/secrets controls remain Package C/E acceptance evidence.
- Stateless invitations have global secret-rotation revocation only.
- The build needs network access for the repository's existing Google Fonts;
  lint and type-check remain local deterministic checks.

## Model routing

- Builder: `/root`; preferred GPT-5.6 Sol high, fallback used because the task
  subagent-thread limit prevented the Sol allocation. Actual model and effort
  are not exposed by runtime.
- Independent reviewer: `/root/t082_pilot_design_adversary`, GPT-6 Astra xhigh
  requested; actual model and effort must be reported if exposed.


## Current finding ledger

```json
[
  {
    "id": "T082-B-001",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "open",
    "invariant": "An authenticated pilot user reads only the observability records allowed by current authority, while cross-tenant reads and feedback triage remain platform-administrator-only.",
    "summary": "The ordinary-user Observability page unconditionally calls the administrator endpoint and receives 403.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "frontend/paprnav-frontend/src/lib/api.ts:listObservability",
      "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx"
    ],
    "impact": "Invited non-administrator users cannot see their authorized product/workflow events or feedback from the existing page.",
    "requiredClosure": "Separate ordinary and administrator readers, choose the reader from current membership, hide triage controls from ordinary users, and add an ordinary-user frontend regression.",
    "closureEvidence": []
  },
  {
    "id": "T082-B-002",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "open",
    "invariant": "The invitation-tamper regression always changes signed bytes and therefore deterministically exercises HMAC rejection.",
    "summary": "Changing the final base64url character can alter only unused encoding bits and leave decoded signature bytes unchanged.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "backend/tests/test_pilot_invite_tenant_boundary.py:test_invitation_verification_rejects_expired_future_and_tampered_codes"
    ],
    "impact": "The test has an approximately one-in-sixteen false failure and is not a reliable security oracle.",
    "requiredClosure": "Decode the signature, mutate a byte, re-encode it, and retain deterministic rejection evidence.",
    "closureEvidence": []
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT-B/decision.md`

size=6103; sha256=43f85c462fefa7a8a71f94d1bcf154d63f6a724512e8abd9a8b6ebd6b6775ca1

```text
# Decision packet: T082 AWS invite pilot — Package B

## Objective and authority

Implement the invite-only authentication, browser session boundary, and
tenant-safe observability/feedback family required before an AWS pilot can
accept external users.

This child run introduces no new design. Its normative authority is the
independently approved parent design:

- `../T082-AWS-INVITE-PILOT/decision.md` SHA-256
  `69c2cce98e90b2902e172ef067800ee6bfdbdaaef3f701b8fe492a694d977f71`;
- `../T082-AWS-INVITE-PILOT/design-remediation-1.md` SHA-256
  `2909b5b0e14af10e41eb6a7b762df28e47f3d91c16c35627db8064e375f31506`;
- `../T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md` SHA-256
  `78442e342fb36fb3732cc95d7e9e77f49842b3a5e35dffe49c920c6e2d496018`.

The design reviewer already closed the invitation, session/CSRF, role/type,
same-origin, observability, feedback, and revocation decisions before this
implementation began. The Package B design gate therefore asks only whether
the implementation stayed inside that approved authority; it must not reopen
or expand the design without a new finding.

## User-visible outcome

At most ten invited pilot users can paste a short-lived operator-generated
code, choose a password, receive a secure session, and use the existing product.
They cannot self-register or read another tenant's operational records.
Platform administrators retain a separate bounded cross-tenant view and
feedback-triage authority.

## Safety and correctness invariants

1. Only active platform administrators generate invitations. Codes are
   canonical versioned HMAC-SHA256 bearer credentials using a dedicated secret,
   random nonce, normalized email, maximum 24-hour lifetime, and at most five
   minutes of skew.
2. Only `owner`/`owner_admin` and
   `maintenance_shop`/`maintenance_admin` pairings can be signed or accepted;
   `platform_admin` can never be invited.
3. Successful acceptance atomically creates exactly one user, organization,
   active membership, session, and sanitized achievement event. Email
   uniqueness prevents successful replay; every acceptance failure is
   non-enumerating.
4. Pilot registration is unavailable. Pilot cookies are Secure, HttpOnly, and
   SameSite=Lax. Unsafe cookie-authenticated requests require the exact approved
   HTTPS Origin or same-origin Referer fallback.
5. Pilot browser API traffic uses direct same-origin `/api/v1/*`; the Next
   development proxy does not forward pilot requests.
6. Session invalidation is an audited database operator command and invalidates
   already-issued cookies.
7. Ordinary observability/feedback reads are current-aircraft scoped; personal
   fallback requires both organization and aircraft to be absent. Revocation
   removes aircraft-bound visibility even when the actor owns the row. Generic
   unresolved workflows remain administrator-only. Only platform admins change
   feedback status.
8. Package A's V4 release boundary remains green and its exact configuration
   target is amended and re-reviewed with Package B.

## Design and data behavior

Invitations remain stateless and add no database table or migration. Acceptance
uses existing users, organizations, memberships, sessions, and product events
in one transaction. The dedicated signing secret is runtime configuration and
is never returned except through a signed code, logged, or stored in event
properties. Global invitation revocation rotates that secret; per-code
revocation remains an explicit post-pilot limitation.

Tenant scope is computed from current active memberships, owner organizations,
and active aircraft assignments. Aircraft-bound product events and feedback use
that live scope. Only known workflow identities with a server-side path to a
visible aircraft are returned to ordinary users. Cross-tenant operations use a
separate platform-admin endpoint.

The frontend exposes `/invite`, hides pilot registration, and calls the backend
through the ALB's direct same-origin API path. Package C/E owns ALB routing, WAF,
Secrets Manager injection, images, tasks, and deployment evidence.

## Compatibility and rollback

Local/test self-registration and the development proxy remain available outside
pilot. No database migration or rewrite occurs. Rollback removes the new
routes/service/UI and restores the prior configuration target as one reviewed
change; existing users/sessions/events remain valid data. Emergency revocation
uses `python -m app.scripts.revoke_auth_sessions --user-id <id>` or `--all`.

## Test and review strategy

Use a bounded matrix: allowed and cross-domain roles, valid/tampered/expired/
future/replayed codes, atomic acceptance, startup settings, cookie flags,
Origin/Referer failures, session revocation, and a two-tenant visibility/
feedback scenario including membership revocation. Re-run the directly affected
auth/AD feedback tests, Package A boundary, and existing V4 API suite. Compile,
lint, type-check, and build the pilot frontend.

One independent Astra-xhigh-requested reviewer assesses design adherence and the
complete implementation family. It must inspect the actual dirty tree and
preserved T081/0030 scope, not only this packet.

## Expected file scope and exclusions

The exact implementation scope is recorded in
`../T082-AWS-INVITE-PILOT/package-b-implementation.md`. No T081 file,
`backend/app/models/core.py`, migration 0030, Terraform, AWS resource, Git index,
or commit belongs to Package B.

## Known uncertainty

- Runtime WAF/routing/secrets controls remain Package C/E acceptance evidence.
- Stateless invitations have global secret-rotation revocation only.
- The build needs network access for the repository's existing Google Fonts;
  lint and type-check remain local deterministic checks.

## Model routing

- Builder: `/root`; preferred GPT-5.6 Sol high, fallback used because the task
  subagent-thread limit prevented the Sol allocation. Actual model and effort
  are not exposed by runtime.
- Independent reviewer: `/root/t082_pilot_design_adversary`, GPT-6 Astra xhigh
  requested; actual model and effort must be reported if exposed.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-B/findings.json`

size=2059; sha256=4133a6e8e938a7c67526489459aba05d6ed1473404573bbdbb5d2bac706a7fdc

```text
[
  {
    "id": "T082-B-001",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "open",
    "invariant": "An authenticated pilot user reads only the observability records allowed by current authority, while cross-tenant reads and feedback triage remain platform-administrator-only.",
    "summary": "The ordinary-user Observability page unconditionally calls the administrator endpoint and receives 403.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "frontend/paprnav-frontend/src/lib/api.ts:listObservability",
      "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx"
    ],
    "impact": "Invited non-administrator users cannot see their authorized product/workflow events or feedback from the existing page.",
    "requiredClosure": "Separate ordinary and administrator readers, choose the reader from current membership, hide triage controls from ordinary users, and add an ordinary-user frontend regression.",
    "closureEvidence": []
  },
  {
    "id": "T082-B-002",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "open",
    "invariant": "The invitation-tamper regression always changes signed bytes and therefore deterministically exercises HMAC rejection.",
    "summary": "Changing the final base64url character can alter only unused encoding bits and leave decoded signature bytes unchanged.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "backend/tests/test_pilot_invite_tenant_boundary.py:test_invitation_verification_rejects_expired_future_and_tampered_codes"
    ],
    "impact": "The test has an approximately one-in-sixteen false failure and is not a reliable security oracle.",
    "requiredClosure": "Decode the signature, mutate a byte, re-encode it, and retain deterministic rejection evidence.",
    "closureEvidence": []
  }
]

```
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
### `.ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md`

size=5971; sha256=2673d43606dde214046f93912574060840539302bb74ada2025cb6ad4fc1d669

```text
# Package B implementation: invitation and tenant isolation

## Scope

This package implements the approved invite-only authentication and tenant-safe
observability family without a schema migration, AWS mutation, mail provider,
or invitation table. It preserves the T081/0030 working tree.

Implementation scope:

- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/observability.py`
- `backend/app/schemas/auth.py`
- `backend/app/services/invitations.py`
- `backend/app/services/session_revocation.py`
- `backend/app/scripts/revoke_auth_sessions.py`
- `backend/.env.example`
- `backend/tests/test_pilot_invite_tenant_boundary.py`
- `backend/tests/test_pilot_release_boundary.py`
- `backend/tests/test_ad_matching.py`
- `.ai/pilot-release-boundary-v1.json`
- `.ai/PILOT_RELEASE_BOUNDARY.md`
- `frontend/paprnav-frontend/.env.example`
- `frontend/paprnav-frontend/package.json`
- `frontend/paprnav-frontend/src/lib/api.ts`
- `frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx`
- `frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts`
- `frontend/paprnav-frontend/src/app/(auth)/page.tsx`
- `frontend/paprnav-frontend/src/app/(auth)/register/page.tsx`
- `frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx`
- `frontend/paprnav-frontend/tests/pilot-observability.test.mjs`

## Implemented invariants

1. An active platform administrator can generate a canonical, versioned,
   HMAC-SHA256 invitation with a random nonce and at most 24 hours of lifetime.
   Only `owner`/`owner_admin` and
   `maintenance_shop`/`maintenance_admin` pairings can be signed or accepted.
2. Acceptance verifies canonical bytes, signature, normalized email, timestamps,
   five-minute skew, nonce shape, role/type pairing, and expiry. It atomically
   creates the user, organization, active membership, session, and sanitized
   `invite_accepted` event. Email uniqueness provides successful-use replay
   prevention; invalid, expired, tampered, replayed, and already-registered
   codes share one response.
3. Pilot startup requires the dedicated invitation secret, exactly one
   canonical HTTPS browser origin, secure cookies, and all Package A V4 gates
   disabled. Public registration returns a generic 404 in pilot. Local/test
   registration remains compatible.
4. Pilot session cookies are Secure, HttpOnly, and SameSite=Lax. Unsafe
   cookie-authenticated requests require the exact allowed Origin or its exact
   same-origin Referer fallback before endpoint authentication or body use.
5. The pilot frontend calls `/api/v1/*` directly on the same origin, hides
   self-registration, presents a fixed invitation-code form, and disables the
   Next development proxy in pilot.
6. The audited operator CLI revokes one user's or all database sessions and
   records only the target/count in a server-side event.
7. Ordinary observability reads include aircraft-bound rows only while the
   actor can currently see that aircraft, plus personal rows with neither
   organization nor aircraft. Actor identity cannot preserve aircraft access
   after membership/assignment revocation. Only resolvable aircraft workflows
   are visible. A distinct platform-admin endpoint owns cross-tenant reads, and
   only platform admins may update feedback status.
8. The shared Observability page selects the ordinary or administrator reader
   from the authenticated user's current memberships. Ordinary users never call
   the cross-tenant endpoint and never receive feedback-triage controls.

## Bounded verification

- Package B plus directly affected regressions: **13 passed**. This is 11
  focused invitation/startup/cookie/CSRF/revocation/two-tenant cases and two
  existing auth/AD-feedback cases.
- Package A release boundary after the configuration amendment: **292 passed**.
- Existing V4 API regression: **16 passed**.
- Total distinct backend checks in this evidence set: **321 passed**.
- Frontend ESLint: pass with one pre-existing `no-img-element` warning.
- Frontend TypeScript `--noEmit`: pass.
- Frontend pilot scope regression: **1 passed**, proving ordinary and
  administrator users call distinct endpoints.
- Pilot webpack production build: pass; the first sandboxed attempt failed only
  because the existing `next/font` dependency could not reach Google Fonts.
- Python compilation and `git diff --check`: pass.

These tests intentionally use representative negative and two-tenant cases
rather than a combinatorial token or database state space.

After independent review, the two bounded remediations passed **18** focused
backend/regression tests plus the frontend pilot regression, lint, TypeScript,
and `git diff --check`. The HMAC tamper case now flips a decoded signature byte
before canonical re-encoding, so it cannot mutate only unused base64 bits.

## Remaining gates and deviations

- AWS WAF rate rules, the same-origin ALB routing, Secrets Manager injection,
  and immutable images/task definitions belong to Package C/E and are not
  claimed here.
- Per-invitation revocation, email delivery, password recovery, MFA, and a
  durable invitation ledger remain explicit post-pilot work.
- The release policy's exact `config.py` target hash now includes both Package A
  V4 gates and Package B trust-boundary settings. It requires independent
  Package B review and eventual candidate-commit verification.
- No deployment, Git staging, commit, or AWS mutation occurred.

## Model routing

- Builder identity: `/root`.
- Preferred route: GPT-5.6 Sol high under the approved design.
- The Sol subagent allocation was unavailable because the task had reached its
  subagent-thread limit. The coordinator implemented as the documented
  fallback.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Required independent reviewer: separate GPT-6 Astra xhigh at this complete
  invitation plus observability boundary.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md`

size=2685; sha256=cd7fc858bfcf9a7299fe26abe3dee9d7ae9b777655d334fb70740e0203df1884

```text
# Package A remediation-3 independent implementation review

## Verdict

**PASS.** No blocker or high-severity finding remains within Package A's
independently approved sealed-context boundary.

Reviewed packet SHA-256:
`9713a30067dd988b369eda8328e9ad12445e7e841d0e8709d92a85322bb78452`.
All 24 manifest-bound scope files and review inputs matched.

## Finding dispositions

- **T082-A-001: closed.** Router-authoritative path classification,
  encoded-delimiter rejection, mounted-path handling, pre-authentication/body
  rejection, and pilot startup gates remain intact.
- **T082-A-002: closed for Package A.** The migration-context builder pins the
  resolved commit, validates the approved source inventory, hashes, and modes,
  and constructs only the mapped 44 files plus the canonical manifest.
  Arbitrary checkout modules no longer enter privileged context construction.

## Verification

- 308 focused tests passed: 292 release-boundary cases and 16 existing V4 API
  cases.
- Both vulnerable `psycopg` module and package controls executed their
  sentinels. Sealed controls loaded the real installed driver through actual
  Alembic `env.py` and SQLAlchemy engine construction.
- Source/output mutation, path, mode, symlink, inventory, and secret-handling
  controls passed.
- Independent probes confirmed commit pinning and rejection of an otherwise
  byte-identical output file with an external hard link.
- Pre-Package-A `HEAD` still fails the intentional configuration-target
  mismatch and constructs no context. Verification of the eventual candidate
  commit remains mandatory.
- `git diff --check` passed. Dependency and older pytest-cleanup warnings did
  not cause failures.

## Explicit limits

Local `0444`/`0555` permissions and before/after verification do not protect
against hostile same-owner or root modification between verification and
execution. Package E must establish runtime immutability, absent checkout and
mount overrides, trusted installed dependencies and startup hooks, the
migration-only secret, and a fresh PostgreSQL upgrade. The documentation
assigns these controls correctly. This review does not approve deployment or
use of the local wrapper as the production entrypoint.

The reviewer inspected all eight Package A files, bound review inputs,
staged/unstaged/untracked state, relevant routing/configuration consumers, and
migration/import consumers. No repository file was edited, staged, or
committed; T081 was preserved.

## Model routing

- Reviewer identity: `/root/t082_pilot_design_adversary`.
- Requested model and effort: GPT-6 Astra xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-design-inheritance.md`

size=949; sha256=95afd08c2e7a33173fdc0cdcec6fdee4e84d930b1999945213b0aef6cd2dd7a1

```text
# Package B design-inheritance review

**PASS — design inheritance and applicability.**

Package B introduces no new architecture. Stateless signed invitations, exact
role/type mappings, database sessions/revocation, same-origin browser requests,
and current-aircraft telemetry authorization remain within the independently
approved parent design.

The inherited design remains applicable. The implementation issues in the
initial implementation review require local corrections and dispositions, not
a design expansion. Full implementation adherence must not be claimed until
they are dispositioned.

Package A's configuration-hash amendment is explicit. T081/0030 remains
excluded. WAF, runtime secrets, ALB routing, and immutable deployment evidence
remain later gates.

- Reviewer: `/root/t082_pilot_design_adversary`
- Requested routing: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`


```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md`

size=2484; sha256=c0f781e0293f7ee3f922886bfe3abc1991813c9ad944266311d46eb6e639cec1

```text
# Package B initial implementation review

**PASS at the blocker/high gate.** No blocker/high finding was found. The two
medium findings below require explicit disposition before implementation
closure.

## T082-B-001 — Medium: ordinary users' Observability page calls the administrator endpoint

The shared frontend reader in `frontend/paprnav-frontend/src/lib/api.ts`
unconditionally requests `/observability/admin`. Its existing page consumer in
`frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx`
remains linked for ordinary users. Independent verification confirms those
users receive 403 despite having authorized personal or aircraft records.

Required disposition: separate ordinary/admin readers, select the appropriate
scope, restrict triage controls to administrators, and add one ordinary-user
frontend regression.

## T082-B-002 — Medium: invitation tamper test is nondeterministic

The test in `backend/tests/test_pilot_invite_tenant_boundary.py` changes the
final base64 character to `A`, or `A` to `B`. For a signature ending in `A`,
the latter can change only unused encoding bits; decoded signature bytes remain
identical and verification correctly accepts them. This produces approximately
a 1-in-16 false test failure.

Required disposition: mutate a decoded signature byte and re-encode. If
canonical transport encoding is required, enforce round-trip encoding
separately. Accepted encoding aliases do not bypass HMAC or email-uniqueness
replay protection.

## Verification and limits

327 dependency-relevant backend tests passed. Additional probes confirmed
rollback/no cookie after post-session acceptance failure; assignment revocation
removes actor-owned aircraft events; revoked platform administrators cannot
issue invitations; and all four exported pilot proxy methods return generic
404 without accessing request bodies or upstream fetch. Package A regressions
remain green.

Packet SHA-256:
`87b70986a24d560d2d13c735e6d6c6291d05aa2520ae4737d94286fb4b720008`.
All 29 bound files and inputs matched. The reviewer inspected all 20 scoped
files, relevant producers/consumers, and dirty-tree exclusions without editing
or staging files.

PostgreSQL concurrency, deployed browser routing/WAF, and runtime operator
identity remain deployment evidence and are not established by these local
checks.

- Reviewer: `/root/t082_pilot_design_adversary`
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`


```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-B/package-b-remediation-1.md`

size=1838; sha256=0d21b34b766bc120c0c8b70a86e1844f7a6fec7f74f3a74084557083731c79bc

```text
# Package B remediation 1

## Findings addressed

### T082-B-001

- `listObservability` now calls the ordinary scoped endpoint.
- `listAdminObservability` owns the explicit cross-tenant endpoint.
- `listVisibleObservability` selects between them from the current user's
  platform-administrator membership, and the page uses that selector.
- Feedback triage controls render only for platform administrators.
- `tests/pilot-observability.test.mjs` executes both branches and asserts the
  exact ordinary and administrator request paths.

### T082-B-002

The tamper case decodes the HMAC signature, flips the high bit of its first
byte, and base64url-encodes the changed bytes. The assertion that the resulting
code differs from the original is retained before verification rejection.

## Proportionate verification

- `PYTHONPATH=. .venv/bin/pytest -q tests/test_pilot_invite_tenant_boundary.py tests/test_ad_matching.py`:
  **18 passed**.
- `npm run test:pilot`: **1 passed**.
- `npm run lint`: pass with the one pre-existing `no-img-element` warning.
- `npx tsc --noEmit`: pass.
- `git diff --check`: pass.

The already-green 292-case Package A boundary, 16-case V4 API regression, and
pilot production build were not repeated: neither remediation changed their
configuration, backend route boundary, V4 behavior, proxy, invitation page, or
build configuration. The new page/API behavior is covered by the executable
frontend regression, lint, and TypeScript checks.

No file was staged or committed and no AWS resource was mutated.

## Routing

- Builder: `/root`; preferred GPT-5.6 Sol high.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Independent reviewer: `/root/t082_pilot_design_adversary`; GPT-6 Astra xhigh
  requested, actual model and effort not exposed by runtime.

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
  "taskId": "T082-AWS-INVITE-PILOT-B",
  "stage": "implementation",
  "generatedAt": "2026-09-19T17:23:00+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    "backend/.env.example",
    "backend/app/core/config.py",
    "backend/app/main.py",
    "backend/app/api/routes/auth.py",
    "backend/app/api/routes/observability.py",
    "backend/app/schemas/auth.py",
    "backend/app/services/invitations.py",
    "backend/app/services/session_revocation.py",
    "backend/app/scripts/revoke_auth_sessions.py",
    "backend/tests/test_pilot_invite_tenant_boundary.py",
    "backend/tests/test_pilot_release_boundary.py",
    "backend/tests/test_ad_matching.py",
    ".ai/pilot-release-boundary-v1.json",
    ".ai/PILOT_RELEASE_BOUNDARY.md",
    "frontend/paprnav-frontend/.env.example",
    "frontend/paprnav-frontend/package.json",
    "frontend/paprnav-frontend/src/lib/api.ts",
    "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
    "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
    "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
    "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
    "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
    "frontend/paprnav-frontend/tests/pilot-observability.test.mjs"
  ],
  "scopeFingerprint": "16eefcc2e01884c0855c5e4cb0db589e4c2970abbc5ed3bee878b5f2010af236",
  "files": [
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "??",
      "size": 6653,
      "sha256": "41e01eda7ad31da31a74d920c1b1b6b267f2ca25d34a5acc69bf3d8ca437dad3",
      "readStatus": "readable"
    },
    {
      "path": ".ai/pilot-release-boundary-v1.json",
      "status": "??",
      "size": 8074,
      "sha256": "0eb014c2329e3dcfb9f388a7029e5d8a67eb1df4675106ee45bd6f32a3e458a8",
      "readStatus": "readable"
    },
    {
      "path": "backend/.env.example",
      "status": " M",
      "size": 2212,
      "sha256": "9d624bceccbeaaf1d49a889d3854060080ca92d5659ab6d574fe347bc3d5d71a",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/api/routes/auth.py",
      "status": " M",
      "size": 9323,
      "sha256": "7c60a4e7818db8349d91431e53d6362f665e2a89c2ae3e25b86cbfef175a171a",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/api/routes/observability.py",
      "status": " M",
      "size": 11751,
      "sha256": "39014b4d22b9defb9fdba1416532221cb8ddec28f065c03b99f86f7ea20ee762",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M",
      "size": 10801,
      "sha256": "a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/main.py",
      "status": " M",
      "size": 2160,
      "sha256": "d82af05027a5be5e7395fe85eb6d5dc183ccc32a14c924dc18453e691819016e",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/schemas/auth.py",
      "status": " M",
      "size": 1360,
      "sha256": "81ce14129ba709d36e031069ca5e4eb3e7af3c6cd86b21290ead742ff8b413ed",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/scripts/revoke_auth_sessions.py",
      "status": "??",
      "size": 779,
      "sha256": "65b73178e5f855f515c5dba15d9c9b76f58be5f590431f4f82100a6358293fe7",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/invitations.py",
      "status": "??",
      "size": 6308,
      "sha256": "b81a153085587c0a7b64961c043e2d13ab0ed54f93f2d31f624270097a0bf819",
      "readStatus": "readable"
    },
    {
      "path": "backend/app/services/session_revocation.py",
      "status": "??",
      "size": 918,
      "sha256": "d7c4a36fb880d74d2a390711b30ec0d19dd858205cb768a6cb11344e9996145f",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": " M",
      "size": 23550,
      "sha256": "51c8ad49fae7d3ff6b3c21fea7c692a437a4645aca63768fee59dbc9866e0303",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_invite_tenant_boundary.py",
      "status": "??",
      "size": 15496,
      "sha256": "4481bc1e88bfaac5f0e7a9e3c05acc2cb070dd7131d6a4756a19b6a981227bc6",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??",
      "size": 36863,
      "sha256": "ad8538a9dc7292e4f5cb273b424cdabd64740fdd6b50fffa914574b56fde45a6",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/.env.example",
      "status": " M",
      "size": 261,
      "sha256": "330af5f1958cc928f047f1c07b5db547361c865f3fb2ccb4b94f8048600611d3",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/package.json",
      "status": " M",
      "size": 1202,
      "sha256": "4a320871cb8e65506a8f9cc38006b9702e28cf93a14392088ad317d616581a6d",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
      "status": "??",
      "size": 3488,
      "sha256": "20e1ba41c07086e00a981e09577e966f27fa2311931f933c8baa40ed2d73f295",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
      "status": " M",
      "size": 5097,
      "sha256": "f076a27dc99d7da98b007502bf7a9ec78db8ba6a88a8ccbea96fbfd8bd1e2297",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
      "status": " M",
      "size": 5612,
      "sha256": "1d2338ac38759343a8babea48efd0719821671d2a81c7b8facd584367c052736",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
      "status": " M",
      "size": 7963,
      "sha256": "ab363fbce7a06211f7508ea2407d62c24498516f44f40c8eea248bcdac01f35f",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
      "status": " M",
      "size": 1780,
      "sha256": "aa0dcb3c035b5180420d0ec5d9912625fde68f3d72d818c2fecc4daf33dcdad2",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": " M",
      "size": 24483,
      "sha256": "6feaa2e9ccdbaefd2e1f2785ce1f5f999e531d7da6e1857f4e57752873c71ba8",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/tests/pilot-observability.test.mjs",
      "status": "??",
      "size": 940,
      "sha256": "4b05f4297d57a0f63b5de11e6b2a0786c72f4d258f467fd0085fefe76cb31a2c",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/decision.md",
      "status": "review_input",
      "size": 6103,
      "sha256": "43f85c462fefa7a8a71f94d1bcf154d63f6a724512e8abd9a8b6ebd6b6775ca1",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/findings.json",
      "status": "review_input",
      "size": 2059,
      "sha256": "4133a6e8e938a7c67526489459aba05d6ed1473404573bbdbb5d2bac706a7fdc",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "review_input",
      "size": 36292,
      "sha256": "69c2cce98e90b2902e172ef067800ee6bfdbdaaef3f701b8fe492a694d977f71",
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
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md",
      "status": "review_input",
      "size": 5971,
      "sha256": "2673d43606dde214046f93912574060840539302bb74ada2025cb6ad4fc1d669",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md",
      "status": "review_input",
      "size": 2685,
      "sha256": "cd7fc858bfcf9a7299fe26abe3dee9d7ae9b777655d334fb70740e0203df1884",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-design-inheritance.md",
      "status": "review_input",
      "size": 949,
      "sha256": "95afd08c2e7a33173fdc0cdcec6fdee4e84d930b1999945213b0aef6cd2dd7a1",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "status": "review_input",
      "size": 2484,
      "sha256": "c0f781e0293f7ee3f922886bfe3abc1991813c9ad944266311d46eb6e639cec1",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/package-b-remediation-1.md",
      "status": "review_input",
      "size": 1838,
      "sha256": "0d21b34b766bc120c0c8b70a86e1844f7a6fec7f74f3a74084557083731c79bc",
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
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/state.json",
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
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??"
    },
    {
      "path": "scripts/generate-ad-v4-acceptance-persistence.py",
      "status": "??"
    },
    {
      "path": "scripts/verify_pilot_release_boundary.py",
      "status": "??"
    }
  ],
  "outOfScopeReason": "Preserved T081 Slice 4B artifacts, migration 0030, backend/app/models/core.py edits, Package A source outside shared config/main/test/policy dependencies, and the pre-existing model-routing policy edit are not Package B implementation. No Terraform, AWS, Git staging, or commit is in scope."
}
```

## Diff against base

```diff
diff --git a/backend/.env.example b/backend/.env.example
index 3b782c6..6c493ca 100644
--- a/backend/.env.example
+++ b/backend/.env.example
@@ -3,6 +3,9 @@ PAPRNAV_APP_VERSION=0.1.0
 PAPRNAV_ENV=local
 DATABASE_URL=postgresql+psycopg://paprnav_user:paprnav_password@localhost:5432/paprnav_db
 PAPRNAV_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
+PAPRNAV_SESSION_COOKIE_SECURE=false
+# Pilot only: dedicated secret of at least 32 bytes. Do not reuse database or session values.
+PAPRNAV_INVITE_SIGNING_SECRET=
 PAPRNAV_LOCAL_STORAGE_PATH=.data
 PAPRNAV_STORAGE_BACKEND=local
 PAPRNAV_S3_UPLOAD_BUCKET=
@@ -40,3 +43,12 @@ PAPRNAV_OPENAI_API_KEY=
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
diff --git a/backend/app/api/routes/auth.py b/backend/app/api/routes/auth.py
index c11d5ef..31834ae 100644
--- a/backend/app/api/routes/auth.py
+++ b/backend/app/api/routes/auth.py
@@ -3,21 +3,28 @@ from typing import Optional
 
 from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
 from sqlalchemy import select
+from sqlalchemy.exc import IntegrityError
 from sqlalchemy.orm import Session
 
 from app.api.deps import SESSION_COOKIE_NAME, get_current_user
+from app.api.routes.admin import ensure_platform_admin
+from app.core.config import get_settings
 from app.core.security import create_session_token, hash_password, hash_session_token, verify_password
 from app.db.session import get_db
-from app.models.core import AuthSession, User
+from app.models.core import AuthSession, Organization, OrganizationMembership, User
 from app.schemas.auth import (
     AuthResponse,
     CurrentUserResponse,
+    InvitationAcceptRequest,
+    InvitationCreateRequest,
+    InvitationCreateResponse,
     LoginRequest,
     MembershipResponse,
     OkResponse,
     ProfileUpdateRequest,
     RegisterRequest,
 )
+from app.services.invitations import InvitationError, create_invitation, verify_invitation
 from app.services.observability import record_product_event
 
 router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
@@ -58,13 +65,15 @@ def create_session(db: Session, user: User, request: Request, response: Response
         value=token,
         httponly=True,
         samesite="lax",
-        secure=False,
+        secure=get_settings().session_cookie_secure,
         max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
     )
 
 
 @router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
 def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
+    if get_settings().environment == "pilot":
+        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
     email = normalize_email(payload.email)
     existing_user = db.scalar(select(User).where(User.email == email))
     if existing_user:
@@ -80,6 +89,118 @@ def register(payload: RegisterRequest, request: Request, response: Response, db:
     return AuthResponse(user=serialize_user(user))
 
 
+@router.post("/invitations", response_model=InvitationCreateResponse)
+def generate_invitation(
+    payload: InvitationCreateRequest,
+    response: Response,
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> InvitationCreateResponse:
+    ensure_platform_admin(current_user)
+    settings = get_settings()
+    if not settings.invite_signing_secret:
+        raise HTTPException(
+            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
+            detail="Invitation service is unavailable",
+        )
+    try:
+        code, expires_at = create_invitation(
+            secret=settings.invite_signing_secret,
+            email=payload.email,
+            name=payload.name,
+            organization_name=payload.organizationName,
+            organization_type=payload.organizationType,
+            role=payload.role,
+            ttl=timedelta(hours=payload.expiresInHours),
+        )
+    except InvitationError as exc:
+        raise HTTPException(
+            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
+            detail="Invalid invitation request",
+        ) from exc
+    record_product_event(
+        db,
+        event_type="invite_generated",
+        subject_type="invitation",
+        actor=current_user,
+        properties={
+            "organizationType": payload.organizationType,
+            "role": payload.role,
+            "expiresAt": expires_at.isoformat(),
+        },
+    )
+    db.commit()
+    response.headers["Cache-Control"] = "no-store"
+    return InvitationCreateResponse(invitationCode=code, expiresAt=expires_at)
+
+
+@router.post(
+    "/invitations/accept",
+    response_model=AuthResponse,
+    status_code=status.HTTP_201_CREATED,
+)
+def accept_invitation(
+    payload: InvitationAcceptRequest,
+    request: Request,
+    response: Response,
+    db: Session = Depends(get_db),
+) -> AuthResponse:
+    settings = get_settings()
+    if not settings.invite_signing_secret:
+        raise HTTPException(
+            status_code=status.HTTP_404_NOT_FOUND,
+            detail="Invitation could not be accepted",
+        )
+    try:
+        claims = verify_invitation(
+            payload.invitationCode,
+            secret=settings.invite_signing_secret,
+        )
+        if db.scalar(select(User.id).where(User.email == claims.email)) is not None:
+            raise InvitationError("invitation already used")
+        user = User(
+            email=claims.email,
+            name=claims.name,
+            password_hash=hash_password(payload.password),
+            status="active",
+        )
+        organization = Organization(
+            name=claims.organization_name,
+            type=claims.organization_type,
+        )
+        db.add_all([user, organization])
+        db.flush()
+        db.add(
+            OrganizationMembership(
+                organization_id=organization.id,
+                user_id=user.id,
+                role=claims.role,
+                status="active",
+            )
+        )
+        db.flush()
+        create_session(db, user, request, response)
+        record_product_event(
+            db,
+            event_type="invite_accepted",
+            subject_type="user",
+            subject_id=user.id,
+            actor=user,
+            organization_id=organization.id,
+            properties={"taxonomyVersion": "pilot-achievement-v1"},
+        )
+        db.commit()
+        db.refresh(user)
+    except (InvitationError, IntegrityError, ValueError):
+        db.rollback()
+        raise HTTPException(
+            status_code=status.HTTP_404_NOT_FOUND,
+            detail="Invitation could not be accepted",
+        ) from None
+    response.headers["Cache-Control"] = "no-store"
+    return AuthResponse(user=serialize_user(user))
+
+
 @router.post("/login", response_model=AuthResponse)
 def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
     email = normalize_email(payload.email)
@@ -132,5 +253,10 @@ def logout(
             auth_session.revoked_at = datetime.now(timezone.utc)
             db.commit()
 
-    response.delete_cookie(SESSION_COOKIE_NAME)
+    response.delete_cookie(
+        SESSION_COOKIE_NAME,
+        secure=get_settings().session_cookie_secure,
+        httponly=True,
+        samesite="lax",
+    )
     return OkResponse(ok=True)
diff --git a/backend/app/api/routes/observability.py b/backend/app/api/routes/observability.py
index f3bb8db..51d094f 100644
--- a/backend/app/api/routes/observability.py
+++ b/backend/app/api/routes/observability.py
@@ -1,13 +1,24 @@
 from typing import Optional
 
 from fastapi import APIRouter, Depends, HTTPException, Query, status
-from sqlalchemy import select
+from sqlalchemy import and_, or_, select
 from sqlalchemy.orm import Session
 
 from app.api.deps import get_current_user
-from app.api.routes.aircraft import get_visible_aircraft_or_404
+from app.api.routes.admin import ensure_platform_admin
+from app.api.routes.aircraft import get_visible_aircraft_or_404, visible_aircraft_statement
 from app.db.session import get_db
-from app.models.core import ProductEvent, User, UserFeedback, WorkflowStatusEvent
+from app.models.core import (
+    ADMatchAdjudication,
+    ADMatchResult,
+    Aircraft,
+    AircraftAssignment,
+    IngestionJob,
+    ProductEvent,
+    User,
+    UserFeedback,
+    WorkflowStatusEvent,
+)
 from app.schemas.observability import (
     ObservabilityListResponse,
     ProductEventResponse,
@@ -35,8 +46,79 @@ def list_observability(
 ) -> ObservabilityListResponse:
     if aircraft_id:
         get_visible_aircraft_or_404(db, current_user, aircraft_id)
+    if user_id and user_id != current_user.id:
+        raise HTTPException(
+            status_code=status.HTTP_403_FORBIDDEN,
+            detail="Cannot widen observability scope",
+        )
+    return _list_observability(
+        db,
+        current_user=current_user,
+        admin_scope=False,
+        aircraft_id=aircraft_id,
+        user_id=user_id,
+        event_type=event_type,
+        subject_type=subject_type,
+        status_filter=status_filter,
+        workflow_id=workflow_id,
+    )
+
+
+@router.get("/admin", response_model=ObservabilityListResponse)
+def list_observability_admin(
+    aircraft_id: Optional[str] = Query(default=None),
+    user_id: Optional[str] = Query(default=None),
+    event_type: Optional[str] = Query(default=None),
+    subject_type: Optional[str] = Query(default=None),
+    status_filter: Optional[str] = Query(default=None, alias="status"),
+    workflow_id: Optional[str] = Query(default=None),
+    current_user: User = Depends(get_current_user),
+    db: Session = Depends(get_db),
+) -> ObservabilityListResponse:
+    ensure_platform_admin(current_user)
+    return _list_observability(
+        db,
+        current_user=current_user,
+        admin_scope=True,
+        aircraft_id=aircraft_id,
+        user_id=user_id,
+        event_type=event_type,
+        subject_type=subject_type,
+        status_filter=status_filter,
+        workflow_id=workflow_id,
+    )
+
+
+def _list_observability(
+    db: Session,
+    *,
+    current_user: User,
+    admin_scope: bool,
+    aircraft_id: Optional[str],
+    user_id: Optional[str],
+    event_type: Optional[str],
+    subject_type: Optional[str],
+    status_filter: Optional[str],
+    workflow_id: Optional[str],
+) -> ObservabilityListResponse:
+    visible_aircraft_ids = (
+        visible_aircraft_statement(current_user)
+        .with_only_columns(Aircraft.id)
+        .order_by(None)
+    )
 
     event_statement = select(ProductEvent).order_by(ProductEvent.event_time.desc()).limit(100)
+    if not admin_scope:
+        event_statement = event_statement.where(
+            or_(
+                ProductEvent.aircraft_id.in_(visible_aircraft_ids),
+                and_(
+                    ProductEvent.aircraft_id.is_(None),
+                    ProductEvent.organization_id.is_(None),
+                    ProductEvent.actor_user_id == current_user.id,
+                ),
+            )
+        )
     if aircraft_id:
         event_statement = event_statement.where(ProductEvent.aircraft_id == aircraft_id)
     if user_id:
@@ -47,6 +129,33 @@ def list_observability(
         event_statement = event_statement.where(ProductEvent.subject_type == subject_type)
 
     workflow_statement = select(WorkflowStatusEvent).order_by(WorkflowStatusEvent.created_at.desc()).limit(100)
+    if not admin_scope:
+        visible_job_ids = select(IngestionJob.id).where(
+            IngestionJob.aircraft_id.in_(visible_aircraft_ids)
+        )
+        visible_adjudication_ids = (
+            select(ADMatchAdjudication.id)
+            .join(ADMatchResult, ADMatchAdjudication.match_result_id == ADMatchResult.id)
+            .where(ADMatchResult.aircraft_id.in_(visible_aircraft_ids))
+        )
+        workflow_statement = workflow_statement.where(
+            or_(
+                and_(
+                    WorkflowStatusEvent.workflow_type.in_(
+                        {"upload_ingestion", "page_verification", "ocr_correction"}
+                    ),
+                    WorkflowStatusEvent.workflow_id.in_(visible_job_ids),
+                ),
+                and_(
+                    WorkflowStatusEvent.workflow_type == "ad_matching",
+                    WorkflowStatusEvent.workflow_id.in_(visible_aircraft_ids),
+                ),
+                and_(
+                    WorkflowStatusEvent.workflow_type == "hitl_adjudication",
+                    WorkflowStatusEvent.workflow_id.in_(visible_adjudication_ids),
+                ),
+            )
+        )
     if workflow_id:
         workflow_statement = workflow_statement.where(WorkflowStatusEvent.workflow_id == workflow_id)
     if status_filter:
@@ -55,6 +164,17 @@ def list_observability(
         workflow_statement = workflow_statement.where(WorkflowStatusEvent.actor_user_id == user_id)
 
     feedback_statement = select(UserFeedback).order_by(UserFeedback.created_at.desc()).limit(50)
+    if not admin_scope:
+        feedback_statement = feedback_statement.where(
+            or_(
+                UserFeedback.aircraft_id.in_(visible_aircraft_ids),
+                and_(
+                    UserFeedback.aircraft_id.is_(None),
+                    UserFeedback.organization_id.is_(None),
+                    UserFeedback.submitted_by_user_id == current_user.id,
+                ),
+            )
+        )
     if aircraft_id:
         feedback_statement = feedback_statement.where(UserFeedback.aircraft_id == aircraft_id)
     if status_filter:
@@ -75,9 +195,24 @@ def create_feedback(
     current_user: User = Depends(get_current_user),
     db: Session = Depends(get_db),
 ) -> UserFeedbackCreateResponse:
+    organization_id = None
     if payload.aircraftId:
-        get_visible_aircraft_or_404(db, current_user, payload.aircraftId)
-    organization_id = current_user.memberships[0].organization_id if current_user.memberships else None
+        aircraft = get_visible_aircraft_or_404(db, current_user, payload.aircraftId)
+        active_organization_ids = {
+            membership.organization_id
+            for membership in current_user.memberships
+            if membership.status == "active"
+        }
+        if aircraft.owner_organization_id in active_organization_ids:
+            organization_id = aircraft.owner_organization_id
+        else:
+            organization_id = db.scalar(
+                select(AircraftAssignment.organization_id).where(
+                    AircraftAssignment.aircraft_id == aircraft.id,
+                    AircraftAssignment.organization_id.in_(active_organization_ids),
+                    AircraftAssignment.status == "active",
+                )
+            )
     feedback = UserFeedback(
         submitted_by_user_id=current_user.id,
         organization_id=organization_id,
@@ -113,11 +248,10 @@ def update_feedback(
     current_user: User = Depends(get_current_user),
     db: Session = Depends(get_db),
 ) -> UserFeedbackCreateResponse:
+    ensure_platform_admin(current_user)
     feedback = db.get(UserFeedback, feedback_id)
     if not feedback:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
-    if feedback.aircraft_id:
-        get_visible_aircraft_or_404(db, current_user, feedback.aircraft_id)
     feedback.status = payload.status
     record_product_event(
         db,
diff --git a/backend/app/core/config.py b/backend/app/core/config.py
index 256c3cd..1b9b196 100644
--- a/backend/app/core/config.py
+++ b/backend/app/core/config.py
@@ -3,6 +3,7 @@ from dataclasses import dataclass
 from functools import lru_cache
 from pathlib import Path
 from typing import Optional
+from urllib.parse import urlsplit
 
 
 DEFAULT_CORS_ORIGINS = (
@@ -81,7 +82,10 @@ class Settings:
     ad_extraction_timeout_seconds: float
     govinfo_api_key: Optional[str]
     govinfo_base_url: str
+    session_cookie_secure: bool
+    invite_signing_secret: Optional[str]
     drs_max_snapshot_age_days: int = 7
+    ad_v4_routes_enabled: bool = True
     ad_v4_validator2_writes_enabled: bool = False
     ad_v4_slice3a_routes_enabled: bool = False
     ad_v4_slice3b_routes_enabled: bool = False
@@ -99,10 +103,11 @@ def parse_bool(value: Optional[str], default: bool = False) -> bool:
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
@@ -179,9 +184,18 @@ def get_settings() -> Settings:
         ad_extraction_timeout_seconds=float(os.getenv("PAPRNAV_AD_EXTRACTION_TIMEOUT_SECONDS", "30")),
         govinfo_api_key=os.getenv("GOVINFO_API_KEY") or None,
         govinfo_base_url=os.getenv("PAPRNAV_GOVINFO_BASE_URL", "https://api.govinfo.gov").rstrip("/"),
+        session_cookie_secure=parse_bool(
+            os.getenv("PAPRNAV_SESSION_COOKIE_SECURE"),
+            default=environment == "pilot",
+        ),
+        invite_signing_secret=os.getenv("PAPRNAV_INVITE_SIGNING_SECRET") or None,
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
@@ -201,3 +215,44 @@ def get_settings() -> Settings:
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
+    """Fail closed when required invite-pilot trust boundaries are absent."""
+
+    if settings.environment != "pilot":
+        return
+    enabled = [name for name in PILOT_FORBIDDEN_V4_SETTINGS if getattr(settings, name)]
+    if enabled:
+        raise RuntimeError(
+            "Pilot startup refused because V4 capability settings are enabled: "
+            + ", ".join(enabled)
+        )
+    if not settings.session_cookie_secure:
+        raise RuntimeError("Pilot startup requires secure session cookies")
+    if not settings.invite_signing_secret or len(settings.invite_signing_secret.encode("utf-8")) < 32:
+        raise RuntimeError("Pilot startup requires a dedicated invitation signing secret of at least 32 bytes")
+    if len(settings.cors_origins) != 1:
+        raise RuntimeError("Pilot startup requires exactly one CORS origin")
+    origin = settings.cors_origins[0]
+    parsed = urlsplit(origin)
+    canonical_origin = f"{parsed.scheme}://{parsed.netloc}"
+    if (
+        parsed.scheme != "https"
+        or not parsed.hostname
+        or origin != canonical_origin
+        or parsed.username
+        or parsed.password
+    ):
+        raise RuntimeError("Pilot startup requires one canonical HTTPS browser origin")
diff --git a/backend/app/main.py b/backend/app/main.py
index 910f197..246775b 100644
--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -1,12 +1,39 @@
-from fastapi import FastAPI
+from fastapi import FastAPI, Request
 from fastapi.middleware.cors import CORSMiddleware
+from fastapi.responses import JSONResponse
+from starlette._utils import get_route_path
+from urllib.parse import urlsplit
 
+from app.api.deps import SESSION_COOKIE_NAME
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
+
+
+def request_origin(request: Request) -> str | None:
+    origin = request.headers.get("origin")
+    if origin:
+        return origin
+    referer = request.headers.get("referer")
+    if not referer:
+        return None
+    parsed = urlsplit(referer)
+    if not parsed.scheme or not parsed.netloc:
+        return None
+    return f"{parsed.scheme}://{parsed.netloc}"
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
+    validate_runtime_settings(settings)
     app = FastAPI(title=settings.app_name, version=settings.app_version)
 
     app.add_middleware(
@@ -17,6 +44,24 @@ def create_app() -> FastAPI:
         allow_headers=["*"],
     )
 
+    @app.middleware("http")
+    async def enforce_pilot_release_boundary(request: Request, call_next):
+        if not settings.ad_v4_routes_enabled and is_ad_v4_path(
+            get_route_path(request.scope)
+        ):
+            return JSONResponse(status_code=404, content={"detail": "Not Found"})
+        if (
+            settings.environment == "pilot"
+            and request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
+            and request.cookies.get(SESSION_COOKIE_NAME)
+            and request_origin(request) != settings.cors_origins[0]
+        ):
+            return JSONResponse(
+                status_code=403,
+                content={"detail": "Cross-origin request rejected"},
+            )
+        return await call_next(request)
+
     app.include_router(api_router)
 
     return app
diff --git a/backend/app/schemas/auth.py b/backend/app/schemas/auth.py
index 068f958..23d8493 100644
--- a/backend/app/schemas/auth.py
+++ b/backend/app/schemas/auth.py
@@ -1,3 +1,6 @@
+from datetime import datetime
+from typing import Literal
+
 from pydantic import BaseModel, Field
 
 
@@ -12,6 +15,25 @@ class LoginRequest(BaseModel):
     password: str
 
 
+class InvitationCreateRequest(BaseModel):
+    email: str = Field(min_length=3, max_length=255)
+    name: str = Field(min_length=1, max_length=255)
+    organizationName: str = Field(min_length=1, max_length=255)
+    organizationType: Literal["owner", "maintenance_shop"]
+    role: Literal["owner_admin", "maintenance_admin"]
+    expiresInHours: int = Field(default=24, ge=1, le=24)
+
+
+class InvitationCreateResponse(BaseModel):
+    invitationCode: str
+    expiresAt: datetime
+
+
+class InvitationAcceptRequest(BaseModel):
+    invitationCode: str = Field(min_length=1, max_length=4096)
+    password: str = Field(min_length=8, max_length=1024)
+
+
 class MembershipResponse(BaseModel):
     organizationId: str
     organizationName: str
diff --git a/backend/tests/test_ad_matching.py b/backend/tests/test_ad_matching.py
index 4dc10a7..556f1d1 100644
--- a/backend/tests/test_ad_matching.py
+++ b/backend/tests/test_ad_matching.py
@@ -314,8 +314,8 @@ def test_ad_matching_creates_evidence_and_unresolved_review_tasks(
     assert feedback_response.status_code == 201
     feedback_id = feedback_response.json()["feedback"]["id"]
     triage_response = client.patch(f"/api/v1/observability/feedback/{feedback_id}", json={"status": "triaged"})
-    assert triage_response.status_code == 200
-    assert db_session.get(UserFeedback, feedback_id).status == "triaged"
+    assert triage_response.status_code == 403
+    assert db_session.get(UserFeedback, feedback_id).status == "open"
 
     observability_response = client.get("/api/v1/observability")
     assert observability_response.status_code == 200
diff --git a/frontend/paprnav-frontend/.env.example b/frontend/paprnav-frontend/.env.example
index 1147ada..24975bf 100644
--- a/frontend/paprnav-frontend/.env.example
+++ b/frontend/paprnav-frontend/.env.example
@@ -1,5 +1,7 @@
 PAPRNAV_BACKEND_URL=http://127.0.0.1:8000
 NEXT_PUBLIC_PAPRNAV_API_BASE_URL=/api/backend
+NEXT_PUBLIC_PAPRNAV_ENV=local
+PAPRNAV_ENV=local
 PAPRNAV_FRONTEND_URL=http://localhost:3000
 PAPRNAV_SMOKE_EMAIL=owner.demo@paprnav.local
 PAPRNAV_SMOKE_PASSWORD=demo-password
diff --git a/frontend/paprnav-frontend/package.json b/frontend/paprnav-frontend/package.json
index 4f45000..6dcda30 100644
--- a/frontend/paprnav-frontend/package.json
+++ b/frontend/paprnav-frontend/package.json
@@ -7,7 +7,8 @@
     "build": "next build",
     "start": "next start",
     "lint": "eslint",
-    "smoke": "node scripts/smoke.mjs"
+    "smoke": "node scripts/smoke.mjs",
+    "test:pilot": "NEXT_PUBLIC_PAPRNAV_ENV=pilot node --test tests/pilot-observability.test.mjs"
   },
   "dependencies": {
     "@radix-ui/react-avatar": "^1.1.11",
diff --git a/frontend/paprnav-frontend/src/app/(auth)/page.tsx b/frontend/paprnav-frontend/src/app/(auth)/page.tsx
index fb3ccfd..d3bccb7 100644
--- a/frontend/paprnav-frontend/src/app/(auth)/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(auth)/page.tsx
@@ -24,6 +24,7 @@ function LoginForm() {
   const [password, setPassword] = useState("demo-password");
   const [error, setError] = useState<string | null>(null);
   const [isSubmitting, setIsSubmitting] = useState(false);
+  const isPilot = process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot";
 
   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
     event.preventDefault();
@@ -126,16 +127,21 @@ function LoginForm() {
           </CardContent>
         </Card>
 
-        {/* Register link */}
-        <p className="text-center text-sm text-muted-foreground">
-          Don&apos;t have an account?{" "}
-          <Link
-            href="/register"
-            className="font-medium text-primary hover:text-primary/80"
-          >
-            Create one
-          </Link>
-        </p>
+        {isPilot ? (
+          <p className="text-center text-sm text-muted-foreground">
+            Have an invitation?{" "}
+            <Link href="/invite" className="font-medium text-primary hover:text-primary/80">
+              Accept it
+            </Link>
+          </p>
+        ) : (
+          <p className="text-center text-sm text-muted-foreground">
+            Don&apos;t have an account?{" "}
+            <Link href="/register" className="font-medium text-primary hover:text-primary/80">
+              Create one
+            </Link>
+          </p>
+        )}
       </div>
     </div>
   );
diff --git a/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx b/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
index 2f251f6..750d35c 100644
--- a/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
@@ -18,6 +18,24 @@ export default function RegisterPage() {
   const [error, setError] = useState<string | null>(null);
   const [isSubmitting, setIsSubmitting] = useState(false);
 
+  if (process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot") {
+    return (
+      <div className="min-h-screen flex items-center justify-center px-4">
+        <Card className="w-full max-w-md">
+          <CardHeader>
+            <CardTitle>Invitation required</CardTitle>
+            <CardDescription>The pilot is available only to invited users.</CardDescription>
+          </CardHeader>
+          <CardContent>
+            <Link href="/invite" className="font-medium text-primary hover:text-primary/80">
+              Accept an invitation
+            </Link>
+          </CardContent>
+        </Card>
+      </div>
+    );
+  }
+
   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
     event.preventDefault();
     setError(null);
diff --git a/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx b/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
index 7c567a5..dc5c66b 100644
--- a/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
@@ -8,14 +8,17 @@ import { Input } from "@/components/ui/input";
 import { Label } from "@/components/ui/label";
 import { Textarea } from "@/components/ui/textarea";
 import { PageHeader } from "@/components/PageHeader";
+import { useAuth } from "@/components/AuthProvider";
 import {
   createFeedback,
-  listObservability,
+  listVisibleObservability,
   ObservabilityListResponse,
   updateFeedbackStatus,
 } from "@/lib/api";
 
 export default function ObservabilityPage() {
+  const { user } = useAuth();
+  const isPlatformAdmin = user?.memberships.some((membership) => membership.role === "platform_admin") ?? false;
   const [data, setData] = useState<ObservabilityListResponse>({ events: [], workflowEvents: [], feedback: [] });
   const [filters, setFilters] = useState({ aircraftId: "", eventType: "", subjectType: "", status: "" });
   const [feedbackMessage, setFeedbackMessage] = useState("");
@@ -26,13 +29,13 @@ export default function ObservabilityPage() {
   const loadData = useCallback(async () => {
     try {
       const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim()));
-      const response = await listObservability(params);
+      const response = await listVisibleObservability(isPlatformAdmin, params);
       setData(response);
       setError(null);
     } catch (caught) {
       setError(caught instanceof Error ? caught.message : "Unable to load product observability.");
     }
-  }, [filters]);
+  }, [filters, isPlatformAdmin]);
 
   useEffect(() => {
     const timeoutId = window.setTimeout(() => {
@@ -151,10 +154,12 @@ export default function ObservabilityPage() {
                   <p>{item.message}</p>
                   <p className="text-muted-foreground">{item.subjectType} {item.subjectId ?? ""}</p>
                 </div>
-                <div className="flex gap-2">
-                  <Button type="button" size="sm" variant="outline" onClick={() => triageFeedback(item.id, "triaged")}>Triaged</Button>
-                  <Button type="button" size="sm" variant="ghost" onClick={() => triageFeedback(item.id, "closed")}>Closed</Button>
-                </div>
+                {isPlatformAdmin ? (
+                  <div className="flex gap-2">
+                    <Button type="button" size="sm" variant="outline" onClick={() => triageFeedback(item.id, "triaged")}>Triaged</Button>
+                    <Button type="button" size="sm" variant="ghost" onClick={() => triageFeedback(item.id, "closed")}>Closed</Button>
+                  </div>
+                ) : null}
               </div>
             </div>
           )) : <p className="text-sm text-muted-foreground">No feedback yet.</p>}
diff --git a/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts b/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
index d7301ba..1eafe0f 100644
--- a/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
+++ b/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
@@ -16,6 +16,9 @@ type RouteContext = {
 };
 
 async function proxyRequest(request: NextRequest, context: RouteContext) {
+  if (process.env.PAPRNAV_ENV === "pilot") {
+    return NextResponse.json({ detail: "Not Found" }, { status: 404 });
+  }
   const { path } = await context.params;
   const backendPath = path.join("/");
   const upstreamUrl = new URL(`${BACKEND_URL.replace(/\/$/, "")}/${backendPath}`);
diff --git a/frontend/paprnav-frontend/src/lib/api.ts b/frontend/paprnav-frontend/src/lib/api.ts
index a87a5fe..32b07a1 100644
--- a/frontend/paprnav-frontend/src/lib/api.ts
+++ b/frontend/paprnav-frontend/src/lib/api.ts
@@ -1,4 +1,6 @@
-const API_BASE_URL = process.env.NEXT_PUBLIC_PAPRNAV_API_BASE_URL ?? "/api/backend";
+const API_BASE_URL = process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot"
+  ? ""
+  : process.env.NEXT_PUBLIC_PAPRNAV_API_BASE_URL ?? "/api/backend";
 
 export interface Membership {
   organizationId: string;
@@ -17,6 +19,11 @@ export interface AuthResponse {
   user: CurrentUser;
 }
 
+export interface InvitationAcceptRequest {
+  invitationCode: string;
+  password: string;
+}
+
 export interface ProfileUpdateRequest {
   name: string;
 }
@@ -664,6 +671,13 @@ export function register(name: string, email: string, password: string) {
   });
 }
 
+export function acceptInvitation(payload: InvitationAcceptRequest) {
+  return apiFetch<AuthResponse>("/api/v1/auth/invitations/accept", {
+    method: "POST",
+    body: JSON.stringify(payload),
+  });
+}
+
 export function getCurrentUser() {
   return apiFetch<AuthResponse>("/api/v1/auth/me");
 }
@@ -859,6 +873,19 @@ export function listObservability(params: Record<string, string> = {}) {
   return apiFetch<ObservabilityListResponse>(`/api/v1/observability${suffix}`);
 }
 
+export function listAdminObservability(params: Record<string, string> = {}) {
+  const query = new URLSearchParams(params);
+  const suffix = query.toString() ? `?${query.toString()}` : "";
+  return apiFetch<ObservabilityListResponse>(`/api/v1/observability/admin${suffix}`);
+}
+
+export function listVisibleObservability(
+  isPlatformAdmin: boolean,
+  params: Record<string, string> = {},
+) {
+  return isPlatformAdmin ? listAdminObservability(params) : listObservability(params);
+}
+
 export function getADCostAdminSummary() {
   return apiFetch<ADCostAdminSummary>("/api/v1/admin/ad-costs");
 }

```

## Untracked text files

### `.ai/PILOT_RELEASE_BOUNDARY.md`

size=6653; sha256=41e01eda7ad31da31a74d920c1b1b6b267f2ca25d34a5acc69bf3d8ca437dad3; truncated=false

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
`app/core/config.py` target amendment containing the Package A V4 gates and
Package B pilot trust-boundary settings. Its exact SHA-256 is
`a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4` and must
receive independent implementation approval. The baseline therefore fails with
exactly that configuration difference. A mocked candidate containing the
approved target bytes passes; this is not evidence that a release commit
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

size=8074; sha256=0eb014c2329e3dcfb9f388a7029e5d8a67eb1df4675106ee45bd6f32a3e458a8; truncated=false

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
      "backend/app/core/config.py": "Package A V4 gates plus Package B pilot trust-boundary configuration; exact target bytes are bound below and require independent implementation approval before release."
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
    "backend/app/core/config.py": "a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4",
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
### `backend/app/scripts/revoke_auth_sessions.py`

size=779; sha256=65b73178e5f855f515c5dba15d9c9b76f58be5f590431f4f82100a6358293fe7; truncated=false

```text
from __future__ import annotations

import argparse

from app.db.session import SessionLocal
from app.services.session_revocation import revoke_auth_sessions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Revoke active paprnav sessions and write an operator audit event.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--user-id")
    target.add_argument("--all", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        count = revoke_auth_sessions(
            db,
            user_id=None if args.all else args.user_id,
        )
        db.commit()
    print(f"revoked_sessions={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `backend/app/services/invitations.py`

size=6308; sha256=b81a153085587c0a7b64961c043e2d13ab0ed54f93f2d31f624270097a0bf819; truncated=false

```text
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


INVITATION_VERSION = 1
MAX_INVITATION_TTL = timedelta(hours=24)
INVITATION_CLOCK_SKEW = timedelta(minutes=5)
ALLOWED_ROLE_TYPES = {
    ("owner", "owner_admin"),
    ("maintenance_shop", "maintenance_admin"),
}
INVITATION_KEYS = {
    "email",
    "exp",
    "iat",
    "name",
    "nonce",
    "organizationName",
    "organizationType",
    "role",
    "version",
}


class InvitationError(ValueError):
    pass


@dataclass(frozen=True)
class InvitationClaims:
    email: str
    name: str
    organization_name: str
    organization_type: str
    role: str
    nonce: str
    issued_at: datetime
    expires_at: datetime


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    if not value or any(character.isspace() for character in value):
        raise InvitationError("invalid invitation")
    try:
        return base64.b64decode(
            value.encode("ascii") + b"=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (UnicodeEncodeError, ValueError) as exc:
        raise InvitationError("invalid invitation") from exc


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def create_invitation(
    *,
    secret: str,
    email: str,
    name: str,
    organization_name: str,
    organization_type: str,
    role: str,
    now: datetime | None = None,
    ttl: timedelta = MAX_INVITATION_TTL,
) -> tuple[str, datetime]:
    normalized_email = normalize_email(email)
    clean_name = name.strip()
    clean_organization_name = organization_name.strip()
    if not normalized_email or not clean_name or not clean_organization_name:
        raise InvitationError("invalid invitation fields")
    if (organization_type, role) not in ALLOWED_ROLE_TYPES:
        raise InvitationError("invalid invitation role")
    if ttl <= timedelta(0) or ttl > MAX_INVITATION_TTL:
        raise InvitationError("invalid invitation lifetime")
    issued_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    expires_at = issued_at + ttl
    payload = {
        "email": normalized_email,
        "exp": int(expires_at.timestamp()),
        "iat": int(issued_at.timestamp()),
        "name": clean_name,
        "nonce": secrets.token_urlsafe(24),
        "organizationName": clean_organization_name,
        "organizationType": organization_type,
        "role": role,
        "version": INVITATION_VERSION,
    }
    payload_bytes = _canonical_payload(payload)
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_encode(payload_bytes)}.{_encode(signature)}", expires_at


def verify_invitation(
    token: str,
    *,
    secret: str,
    now: datetime | None = None,
) -> InvitationClaims:
    try:
        payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise InvitationError("invalid invitation") from exc
    payload_bytes = _decode(payload_part)
    signature = _decode(signature_part)
    expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise InvitationError("invalid invitation")
    try:
        payload = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvitationError("invalid invitation") from exc
    if not isinstance(payload, dict) or set(payload) != INVITATION_KEYS:
        raise InvitationError("invalid invitation")
    if _canonical_payload(payload) != payload_bytes:
        raise InvitationError("invalid invitation")
    if type(payload.get("version")) is not int or payload["version"] != INVITATION_VERSION:
        raise InvitationError("invalid invitation")
    string_keys = INVITATION_KEYS - {"version", "iat", "exp"}
    if any(not isinstance(payload.get(key), str) or not payload[key] for key in string_keys):
        raise InvitationError("invalid invitation")
    if type(payload.get("iat")) is not int or type(payload.get("exp")) is not int:
        raise InvitationError("invalid invitation")
    if normalize_email(payload["email"]) != payload["email"]:
        raise InvitationError("invalid invitation")
    try:
        nonce = _decode(payload["nonce"])
    except InvitationError as exc:
        raise InvitationError("invalid invitation") from exc
    if len(nonce) != 24 or _encode(nonce) != payload["nonce"]:
        raise InvitationError("invalid invitation")
    if payload["name"].strip() != payload["name"] or payload["organizationName"].strip() != payload["organizationName"]:
        raise InvitationError("invalid invitation")
    if (payload["organizationType"], payload["role"]) not in ALLOWED_ROLE_TYPES:
        raise InvitationError("invalid invitation")
    try:
        issued_at = datetime.fromtimestamp(payload["iat"], timezone.utc)
        expires_at = datetime.fromtimestamp(payload["exp"], timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise InvitationError("invalid invitation") from exc
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if issued_at > current + INVITATION_CLOCK_SKEW:
        raise InvitationError("invalid invitation")
    if expires_at <= current - INVITATION_CLOCK_SKEW:
        raise InvitationError("invalid invitation")
    if expires_at <= issued_at or expires_at - issued_at > MAX_INVITATION_TTL:
        raise InvitationError("invalid invitation")
    return InvitationClaims(
        email=payload["email"],
        name=payload["name"],
        organization_name=payload["organizationName"],
        organization_type=payload["organizationType"],
        role=payload["role"],
        nonce=payload["nonce"],
        issued_at=issued_at,
        expires_at=expires_at,
    )

```
### `backend/app/services/session_revocation.py`

size=918; sha256=d7c4a36fb880d74d2a390711b30ec0d19dd858205cb768a6cb11344e9996145f; truncated=false

```text
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.core import AuthSession
from app.services.observability import record_product_event


def revoke_auth_sessions(db: Session, *, user_id: str | None) -> int:
    statement = update(AuthSession).where(AuthSession.revoked_at.is_(None))
    if user_id is not None:
        statement = statement.where(AuthSession.user_id == user_id)
    result = db.execute(statement.values(revoked_at=datetime.now(timezone.utc)))
    revoked_count = result.rowcount or 0
    record_product_event(
        db,
        event_type="operator_sessions_revoked",
        subject_type="user" if user_id else "session_population",
        subject_id=user_id or "all",
        event_source="operator_cli",
        properties={"revokedCount": revoked_count},
    )
    return revoked_count

```
### `backend/tests/test_pilot_invite_tenant_boundary.py`

size=15496; sha256=4481bc1e88bfaac5f0e7a9e3c05acc2cb070dd7131d6a4756a19b6a981227bc6; truncated=false

```text
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.core import (
    AuthSession,
    OrganizationMembership,
    ProductEvent,
    User,
    UserFeedback,
    WorkflowStatusEvent,
)
from app.services.invitations import InvitationError, create_invitation, verify_invitation
from app.services.observability import record_product_event
from app.services.session_revocation import revoke_auth_sessions
from tests.conftest import (
    TEST_PASSWORD,
    add_membership,
    create_aircraft,
    create_organization,
    create_user,
    login,
)


PILOT_ORIGIN = "https://pilot.example.test"
INVITE_SECRET = "pilot-invitation-secret-that-is-at-least-32-bytes"
V4_SETTINGS = (
    "PAPRNAV_AD_V4_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED",
    "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_READS_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED",
    "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED",
)


@pytest.fixture()
def pilot_client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", PILOT_ORIGIN)
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    for name in V4_SETTINGS:
        monkeypatch.setenv(name, "false")
    get_settings.cache_clear()

    def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url=PILOT_ORIGIN) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def make_platform_admin(db: Session, email: str = "pilot.admin@example.test") -> User:
    user = create_user(db, email, "Pilot Administrator")
    organization = create_organization(db, "Pilot Operations", "platform")
    add_membership(db, organization, user, "platform_admin")
    db.commit()
    return user


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("PAPRNAV_SESSION_COOKIE_SECURE", "false"),
        ("PAPRNAV_INVITE_SIGNING_SECRET", "short"),
        ("PAPRNAV_CORS_ORIGINS", "http://pilot.example.test"),
        ("PAPRNAV_CORS_ORIGINS", f"{PILOT_ORIGIN},https://second.example.test"),
    ),
)
def test_pilot_startup_rejects_missing_trust_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv("PAPRNAV_ENV", "pilot")
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", PILOT_ORIGIN)
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("PAPRNAV_INVITE_SIGNING_SECRET", INVITE_SECRET)
    for setting in V4_SETTINGS:
        monkeypatch.setenv(setting, "false")
    monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        create_app()


def issue_invitation(client: TestClient, *, role: str = "owner_admin", organization_type: str = "owner") -> str:
    response = client.post(
        "/api/v1/auth/invitations",
        headers={"Origin": PILOT_ORIGIN},
        json={
            "email": "Invitee@Example.Test ",
            "name": "Invited Owner",
            "organizationName": "Invited Hangar",
            "organizationType": organization_type,
            "role": role,
            "expiresInHours": 24,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()["invitationCode"]


def test_pilot_invitation_acceptance_is_atomic_and_non_replayable(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    admin = make_platform_admin(db_session)
    login_response = pilot_client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    assert "Secure" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert "SameSite=lax" in login_response.headers["set-cookie"]

    code = issue_invitation(pilot_client)
    accepted = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": code, "password": "invited-password"},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.headers["cache-control"] == "no-store"
    assert accepted.json()["user"]["email"] == "invitee@example.test"
    assert accepted.json()["user"]["memberships"][0]["role"] == "owner_admin"

    user = db_session.scalar(select(User).where(User.email == "invitee@example.test"))
    membership = db_session.scalar(
        select(OrganizationMembership).where(OrganizationMembership.user_id == user.id)
    )
    assert membership.organization.type == "owner"
    assert db_session.scalar(
        select(ProductEvent).where(
            ProductEvent.event_type == "invite_accepted",
            ProductEvent.subject_id == user.id,
        )
    )
    assert db_session.scalar(select(AuthSession).where(AuthSession.user_id == user.id))

    replay = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": code, "password": "invited-password"},
    )
    invalid = pilot_client.post(
        "/api/v1/auth/invitations/accept",
        headers={"Origin": PILOT_ORIGIN},
        json={"invitationCode": "invalid", "password": "invited-password"},
    )
    assert (replay.status_code, replay.json()) == (invalid.status_code, invalid.json())


@pytest.mark.parametrize(
    ("organization_type", "role"),
    (("owner", "maintenance_admin"), ("maintenance_shop", "owner_admin")),
)
def test_invitation_generation_rejects_cross_domain_roles(
    pilot_client: TestClient,
    db_session: Session,
    organization_type: str,
    role: str,
) -> None:
    admin = make_platform_admin(db_session)
    assert pilot_client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": TEST_PASSWORD},
    ).status_code == 200
    response = pilot_client.post(
        "/api/v1/auth/invitations",
        headers={"Origin": PILOT_ORIGIN},
        json={
            "email": "invitee@example.test",
            "name": "Invitee",
            "organizationName": "Invited Organization",
            "organizationType": organization_type,
            "role": role,
        },
    )
    assert response.status_code == 422


def test_invitation_verification_rejects_expired_future_and_tampered_codes() -> None:
    now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    expired, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now - timedelta(days=2),
        ttl=timedelta(hours=1),
    )
    future, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now + timedelta(minutes=6),
        ttl=timedelta(hours=1),
    )
    valid, _ = create_invitation(
        secret=INVITE_SECRET,
        email="invitee@example.test",
        name="Invitee",
        organization_name="Hangar",
        organization_type="owner",
        role="owner_admin",
        now=now,
        ttl=timedelta(hours=1),
    )
    payload, encoded_signature = valid.split(".", maxsplit=1)
    signature = bytearray(base64.urlsafe_b64decode(encoded_signature + "=" * (-len(encoded_signature) % 4)))
    signature[0] ^= 0x01
    tampered_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    tampered = f"{payload}.{tampered_signature}"
    assert tampered != valid

    for code in (expired, future, tampered):
        with pytest.raises(InvitationError):
            verify_invitation(code, secret=INVITE_SECRET, now=now)


def test_pilot_registration_and_cookie_authenticated_cross_origin_mutations_fail_closed(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, "pilot.user@example.test", "Pilot User")
    db_session.commit()
    assert pilot_client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.test", "name": "New", "password": "new-password"},
    ).status_code == 404
    assert pilot_client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": TEST_PASSWORD},
    ).status_code == 200

    payload = {"name": "Updated Pilot"}
    assert pilot_client.patch("/api/v1/auth/profile", json=payload).status_code == 403
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Origin": "https://evil.example"},
        json=payload,
    ).status_code == 403
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Origin": PILOT_ORIGIN},
        json=payload,
    ).status_code == 200
    assert pilot_client.patch(
        "/api/v1/auth/profile",
        headers={"Referer": f"{PILOT_ORIGIN}/profile"},
        json=payload,
    ).status_code == 200


def test_session_revocation_invalidates_existing_cookie(
    pilot_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, "revoke.me@example.test", "Revoke Me")
    db_session.commit()
    with TestClient(pilot_client.app, base_url=PILOT_ORIGIN) as user_client:
        assert user_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": TEST_PASSWORD},
        ).status_code == 200
        assert user_client.get("/api/v1/auth/me").status_code == 200
        assert revoke_auth_sessions(db_session, user_id=user.id) == 1
        db_session.commit()
        assert user_client.get("/api/v1/auth/me").status_code == 401
        assert db_session.scalar(
            select(ProductEvent).where(
                ProductEvent.event_type == "operator_sessions_revoked",
                ProductEvent.subject_id == user.id,
            )
        )


def test_observability_is_tenant_scoped_and_feedback_updates_are_admin_only(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(db_session, "scope.owner@example.test", "Scope Owner")
    stranger = create_user(db_session, "scope.stranger@example.test", "Scope Stranger")
    admin = create_user(db_session, "scope.admin@example.test", "Scope Admin")
    owner_org = create_organization(db_session, "Scope Hangar", "owner")
    stranger_org = create_organization(db_session, "Other Hangar", "owner")
    platform_org = create_organization(db_session, "Pilot Operations", "platform")
    owner_membership = add_membership(db_session, owner_org, owner, "owner_admin")
    add_membership(db_session, stranger_org, stranger, "owner_admin")
    add_membership(db_session, platform_org, admin, "platform_admin")
    aircraft = create_aircraft(db_session, owner_org, owner, "N321ZZ")
    other_aircraft = create_aircraft(db_session, stranger_org, stranger, "N654YY")
    record_product_event(
        db_session,
        event_type="visible_aircraft_event",
        subject_type="aircraft",
        subject_id=aircraft.id,
        actor=owner,
        aircraft_id=aircraft.id,
        organization_id=owner_org.id,
    )
    record_product_event(
        db_session,
        event_type="other_aircraft_event",
        subject_type="aircraft",
        subject_id=other_aircraft.id,
        actor=stranger,
        aircraft_id=other_aircraft.id,
        organization_id=stranger_org.id,
    )
    record_product_event(
        db_session,
        event_type="personal_event",
        subject_type="profile",
        subject_id=owner.id,
        actor=owner,
    )
    record_product_event(
        db_session,
        event_type="org_only_event",
        subject_type="organization",
        subject_id=owner_org.id,
        actor=owner,
        organization_id=owner_org.id,
    )
    db_session.add_all(
        [
            WorkflowStatusEvent(
                workflow_type="ad_matching",
                workflow_id=aircraft.id,
                new_status="complete",
                actor_type="worker",
            ),
            WorkflowStatusEvent(
                workflow_type="ad_ingestion",
                workflow_id="global",
                new_status="complete",
                actor_type="worker",
            ),
            UserFeedback(
                submitted_by_user_id=owner.id,
                organization_id=owner_org.id,
                aircraft_id=aircraft.id,
                subject_type="aircraft",
                subject_id=aircraft.id,
                feedback_type="demo_note",
                message="Visible feedback",
                severity="medium",
                status="open",
            ),
            UserFeedback(
                submitted_by_user_id=stranger.id,
                organization_id=stranger_org.id,
                aircraft_id=other_aircraft.id,
                subject_type="aircraft",
                subject_id=other_aircraft.id,
                feedback_type="demo_note",
                message="Other feedback",
                severity="medium",
                status="open",
            ),
        ]
    )
    db_session.commit()

    login(client, owner.email)
    response = client.get("/api/v1/observability")
    assert response.status_code == 200
    payload = response.json()
    event_types = {event["eventType"] for event in payload["events"]}
    assert {"visible_aircraft_event", "personal_event", "auth_login"} <= event_types
    assert {"other_aircraft_event", "org_only_event"}.isdisjoint(event_types)
    assert [event["workflowType"] for event in payload["workflowEvents"]] == ["ad_matching"]
    assert [item["message"] for item in payload["feedback"]] == ["Visible feedback"]
    feedback_id = payload["feedback"][0]["id"]
    assert client.get(
        "/api/v1/observability",
        params={"user_id": stranger.id},
    ).status_code == 403
    assert client.patch(
        f"/api/v1/observability/feedback/{feedback_id}",
        json={"status": "triaged"},
    ).status_code == 403

    owner_membership.status = "revoked"
    db_session.commit()
    revoked_payload = client.get("/api/v1/observability").json()
    revoked_event_types = {event["eventType"] for event in revoked_payload["events"]}
    assert {"personal_event", "auth_login"} <= revoked_event_types
    assert "visible_aircraft_event" not in revoked_event_types
    assert revoked_payload["workflowEvents"] == []
    assert revoked_payload["feedback"] == []

    client.post("/api/v1/auth/logout")
    login(client, admin.email)
    admin_payload = client.get("/api/v1/observability/admin").json()
    assert {event["eventType"] for event in admin_payload["events"]} >= {
        "visible_aircraft_event",
        "other_aircraft_event",
    }
    assert client.patch(
        f"/api/v1/observability/feedback/{feedback_id}",
        json={"status": "triaged"},
    ).status_code == 200

```
### `backend/tests/test_pilot_release_boundary.py`

size=36863; sha256=ad8538a9dc7292e4f5cb273b424cdabd64740fdd6b50fffa914574b56fde45a6; truncated=false

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
    monkeypatch.setenv("PAPRNAV_CORS_ORIGINS", "https://pilot.example.test")
    monkeypatch.setenv("PAPRNAV_SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv(
        "PAPRNAV_INVITE_SIGNING_SECRET",
        "pilot-invitation-secret-that-is-at-least-32-bytes",
    )
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
### `frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx`

size=3488; sha256=20e1ba41c07086e00a981e09577e966f27fa2311931f933c8baa40ed2d73f295; truncated=false

```text
"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { acceptInvitation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function InvitationPage() {
  const router = useRouter();
  const [invitationCode, setInvitationCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsSubmitting(true);
    try {
      await acceptInvitation({ invitationCode, password });
      router.push("/logbook");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Invitation could not be accepted.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Accept invitation</CardTitle>
          <CardDescription>Paste the invitation code sent to you by the pilot operator.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="invitation-code">Invitation code</Label>
              <Input
                id="invitation-code"
                value={invitationCode}
                onChange={(event) => setInvitationCode(event.target.value)}
                autoComplete="off"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Accepting..." : "Accept invitation"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            <Link href="/" className="font-medium text-primary hover:text-primary/80">
              Back to sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

```
### `frontend/paprnav-frontend/tests/pilot-observability.test.mjs`

size=940; sha256=4b05f4297d57a0f63b5de11e6b2a0786c72f4d258f467fd0085fefe76cb31a2c; truncated=false

```text
import assert from "node:assert/strict";
import test from "node:test";

import { listVisibleObservability } from "../src/lib/api.ts";

const EMPTY_OBSERVABILITY = {
  events: [],
  workflowEvents: [],
  feedback: [],
};

test("ordinary and platform-admin observability readers use distinct scopes", async () => {
  const requestedPaths = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    requestedPaths.push(String(input));
    return new Response(JSON.stringify(EMPTY_OBSERVABILITY), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  try {
    await listVisibleObservability(false, { status: "open" });
    await listVisibleObservability(true, { status: "open" });
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.deepEqual(requestedPaths, [
    "/api/v1/observability?status=open",
    "/api/v1/observability/admin?status=open",
  ]);
});

```
