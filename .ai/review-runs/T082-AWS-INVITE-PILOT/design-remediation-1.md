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
