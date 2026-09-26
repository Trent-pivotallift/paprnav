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
