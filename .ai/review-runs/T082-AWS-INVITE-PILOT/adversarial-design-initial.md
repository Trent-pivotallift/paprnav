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
