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
