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
