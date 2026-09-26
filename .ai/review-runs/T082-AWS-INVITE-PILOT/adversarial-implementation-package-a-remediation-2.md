# T082 Package A remediation-2 implementation review

## Outcome

**FAIL.** `T082-A-001` remains closed. `T082-A-002` remains high in the
repeated release-authority/oracle family.

Reviewed packet SHA-256:
`513971f42c6a1828b9e98865cd2525082947f87f6d499a4b649008d127337b76`.
All 18 manifest-bound input hashes matched.

## T082-A-002 residual counterexample

A passing candidate must not introduce repository code executed by the
reviewed migration invocation outside the approved authority. The current
import allowlist omits `psycopg`, while `backend/alembic.ini` prepends the
backend directory and SQLAlchemy's `postgresql+psycopg` dialect imports that
DBAPI during `engine_from_config`.

An in-memory candidate preserving all 44 approved hashes plus either
`backend/psycopg.py` or `backend/psycopg/__init__.py` passed without errors. A
read-only normal-`FileFinder` execution probe confirmed that
`engine_from_config` selects the candidate module and executes its sentinel
before connecting to a database.

This is repository import substitution, not an external dependency-version
change. Unreviewed code can execute with migration credentials despite a
release-boundary pass. Adding only the observed module name is insufficient.

Required closure: restate the executable-import boundary and either prevent
repository shadowing or comprehensively bind eligible repository import inputs.
Add an execution-backed candidate regression oracle.

This is the third substantive failure in this family. Implementation must
pause until the missing invariant, architecture boundary, and shared oracle are
recorded and independently reviewed.

## Verified evidence

- `T082-A-001` remained closed under an independent 441-case raw-ASGI matrix;
  every request returned generic 404 with zero authentication or body reads.
- 124 targeted tests passed.
- All 132 content/removal/rename mutations over the 44 authority files and nine
  invalid policy-scope changes were rejected.
- `HEAD` failed exactly the approved config target mismatch; the working-config
  candidate passed; `HEAD^` failed ancestry.
- No other blocker/high finding was found.
- No repository edit, staging, commit, PostgreSQL execution, image, or cloud
  mutation was performed by the reviewer.

## Model routing

- Remediation builder: `/root/t082_package_a_migration_authority`; requested
  GPT-6 Astra xhigh; actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Reviewer: `/root/t082_pilot_design_adversary`; requested GPT-6 Astra xhigh;
  actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Trigger: repeated high-severity release-authority/oracle finding at the third
  review loop.
