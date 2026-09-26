# Package E E1A implementation evidence

## Outcome

Implemented the approved pre-execution bootstrap connection and separate IAM
supplement family. No AWS/provider call, secret-value access, remote image
build/push, Git staging, or commit occurred. This is builder evidence only;
E-DESIGN-001 and E-DESIGN-002 remain `fixed_pending_verification` until the
coordinator obtains an independent implementation review.

## Model routing

- Builder runtime identity: `/root/t082_package_e_e1a_implementation`.
- Approved/requested route: GPT-5.6 Sol high for the coherent, approved
  multi-file implementation.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: authorization-sensitive IAM publication plus the privileged sealed
  bootstrap database trust boundary, with approved design and deterministic
  negative/size oracles.
- No fallback is claimed. The coordinator must record the separately assigned
  implementation reviewer identity and its exposed model/effort.

## Changed scope

- `infra/bootstrap/bootstrap.py`
  - Reads only `username` and `password` from the managed-secret document.
  - Requires `PAPRNAV_DATABASE_HOST` and `PAPRNAV_DATABASE_PORT`, validates a
    sane DNS-style host and an integer port in `1..65535`, and ignores secret
    host/port/database fields.
- `infra/terraform/ecs_runtime.tf`
  - Binds the common environment of all four fixed-phase bootstrap task
    definitions directly to `aws_db_instance.postgres.address` and `.port`.
- `scripts/generate_pilot_deploy_policy.py`
  - Keeps the baseline ARN distinct, emits the exact separately named pilot
    supplement, scopes updater lifecycle actions to that supplement, and
    scopes role attach/detach to the exact deploy role with
    `iam:PolicyARN`.
  - Emits destructive deletion authority in a separate proof policy and
    records publication quota preconditions.
- `infra/aws-iam/pilot-policy-matrix.json`
  - Mirrors separate supplement/updater/deletion authorities and states that
    the broad unchanged baseline remains effective.
- `backend/tests/test_pilot_package_c.py`
  - Adds realistic credential-only managed-secret tests, host/port negative
    and boundary cases, secret override resistance, exact Terraform source
    bindings, policy scope, quota, count, and unchanged-baseline assertions.
- `infra/terraform/tests/package_c.tftest.hcl`
  - Adds mocked RDS address/port and plan assertions for all four fixed-phase
    task definitions.
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-implementation.md`
  - This builder evidence.

No file outside the declared scope was edited. Existing Package A-D, T081/0030,
and `backend/app/models/core.py` work was preserved.

## Deterministic policy evidence

Stable fixture inputs:

- hosted zone: `Z123456789ABC`
- hostname: `pilot.example.com`
- updater: `arn:aws:iam::527257972989:role/paprnav-policy-updater`
- KMS key: `arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555`

Results:

- unchanged baseline compact characters: `5011`
- supplement compact characters: `3731`
- invalid merged compact characters: `8704`
- per-policy character limit: `6144`
- baseline file SHA-256:
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`
- supplement compact SHA-256:
  `11885bca4559c55e7dc81181ea5b59ab167903b5ef72a0571d28a6541e6cd11e`

The generator and matrix require one available role-attachment slot and, when
versioning an existing supplement, one available policy-version slot under the
five-version limit. These are publication preconditions, not claims about live
quota state. Deletion of exact non-default versions or the exact detached
supplement is separately authorized and requires a zero-unexpected-attachment
operator check; ordinary updater authority contains no delete action.

## Focused verification

1. `.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py`
   - Not run: exit `127`; the repository-root `.venv` does not exist.
2. `python3 -m pytest -q backend/tests/test_pilot_package_c.py`
   - Not run: exit `1`; system Python has no `pytest` module.
3. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py`
   - PASS: `25 passed, 2 skipped, 81 warnings in 0.17s`.
   - Skips were the existing optional Terraform-plan JSON oracle and disposable
     PostgreSQL test because their opt-in environment inputs were absent.
4. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py -k 'admin_connection or bootstrap_task_definitions or generated_supplement' --disable-warnings`
   - PASS: `16 passed, 11 deselected, 1 warning in 0.07s`.
5. `backend/.venv/bin/python -m py_compile infra/bootstrap/bootstrap.py scripts/generate_pilot_deploy_policy.py backend/tests/test_pilot_package_c.py`
   - PASS.
6. `python3 -m json.tool infra/aws-iam/pilot-policy-matrix.json >/dev/null`
   - PASS.
7. `python3 scripts/generate_pilot_deploy_policy.py --hosted-zone-id Z123456789ABC --pilot-hostname pilot.example.com --operator-updater-principal-arn arn:aws:iam::527257972989:role/paprnav-policy-updater --secrets-manager-kms-key-arn arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555 --output /private/tmp/t082-e1a-policy-fixture.json`
   - PASS: `statementCount=15`, status `pass`.
8. Compact JSON count/hash Python fixture over the unchanged baseline and the
   generated supplement.
   - PASS: `5011 / 3731 / 8704` and hashes recorded above.
9. `git diff --check`
   - PASS.

## Deviations and unavailable checks

- `terraform test` was not run because neither `terraform` nor `tofu` is
  installed and no local executable was available. The Terraform mock test was
  added for the coordinator/reviewer to run where the existing pinned tooling
  is available. The focused Python source oracle passed and binds the literal
  RDS expressions; no substitute Terraform PASS is claimed.
- Python `hcl2` parsing was unavailable (`No module named 'hcl2'`); no HCL parse
  PASS is claimed.
- The optional disposable PostgreSQL test did not run because
  `PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL` was absent. The non-database bootstrap
  connection contract tests passed.
- No refreshed image was built or remote task definition inspected in this
  bounded source implementation. Those candidate/image checks remain after
  independent implementation review and under their later authorization gate.
- No design deviation or newly discovered source consumer required expanding
  the declared scope.

## Review handoff

The independent reviewer should inspect staged, unstaged, and untracked files;
verify the managed-secret/environment provenance through every bootstrap phase;
run the Terraform mock test with pinned local tooling; reproduce the compact
counts and baseline hash; and verify exact updater, attachment, rollback, and
deletion scope. The builder does not close either finding or attest review.
