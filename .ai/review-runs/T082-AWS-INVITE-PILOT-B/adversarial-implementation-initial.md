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

