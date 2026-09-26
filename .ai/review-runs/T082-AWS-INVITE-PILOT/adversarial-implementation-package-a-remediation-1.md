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
