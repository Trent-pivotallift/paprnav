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
