# Package E E1A remediation 1

## Outcome

Remediated only E-IMPL-001. The focused `command = plan` Terraform run now
supplies plan-time values for every resource attribute that feeds the four
bootstrap `container_definitions`. The production expressions, direct
`aws_db_instance.postgres.address` / `.port` assertions, and fixed-command
assertion across all four phases are unchanged. No application or Terraform
source behavior changed.

This is builder evidence, not independent verification or finding closure. The
ledger remains unchanged for the coordinator and separate reviewer.

## Model routing

- Builder runtime identity: `/root/t082_package_e_e1a_remediation_1`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: first substantive failed implementation review; bounded remediation
  of a deterministic Terraform plan-time oracle gap.
- No fallback is claimed. Builder/reviewer separation remains required.

## Changed scope

- `infra/terraform/tests/package_c.tftest.hcl`
  - Replaced the apply-time RDS type mock with run-scoped
    `override_during = plan` overrides covering the complete resource-derived
    bootstrap JSON graph.
  - Added a plan-known valid `aws_iam_policy_document` data mock after the first
    real Terraform execution showed that targeted IAM role schema validation
    otherwise failed before reaching the container assertions.
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md`
  - Records the dependency audit, implementation, and verification evidence.

No other file was edited, staged, or committed by this builder. No AWS call,
secret access, network access, or provider operation occurred.

## Complete bootstrap container JSON dependency audit

The four `aws_ecs_task_definition.bootstrap` instances are `migration`,
`reference`, `runtime-role`, and `first-admin`.

| Consumer phases | Resource-derived JSON attribute | Exact plan mock |
| --- | --- | --- |
| all four | `aws_db_instance.postgres.address` | `paprnav-bootstrap-plan.invalid` |
| all four | `aws_db_instance.postgres.port` | `5432` |
| all four | `aws_db_instance.postgres.db_name` | `paprnav` |
| all four | `aws_db_instance.postgres.master_user_secret[0].secret_arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-package-c-plan` |
| all four | `aws_cloudwatch_log_group.bootstrap.name` | `/paprnav/package-c/bootstrap-plan` |
| `runtime-role` | `aws_secretsmanager_secret.database_url.arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/app-database-plan-000001` |
| `first-admin` | `aws_secretsmanager_secret.first_admin_password.arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/first-admin-plan-000001` |

The remaining JSON inputs are plan-known literals, variables, or `each.key`:
the image digest, container name, essential flag, fixed phase command, common
environment literals, AWS region, first-admin identity fields, empty secrets,
read-only root flag, init flag, log driver, and stream prefix. Task and execution
role ARNs are task-definition attributes outside `container_definitions`; they
cannot make the decoded JSON assertion unknown.

The host assertion still compares every rendered environment directly with
`aws_db_instance.postgres.address`; the port assertion still compares it with
`tostring(aws_db_instance.postgres.port)`. The command assertion still iterates
the same four-instance resource map and requires the sole command to equal each
phase key. No assertion was weakened and the run remains `command = plan`.

All mock identifiers are inert test values. The host uses the reserved
`.invalid` top-level domain and no secret value is represented.

## Focused verification

1. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py -k bootstrap_task_definitions --disable-warnings`
   - PASS: `1 passed, 26 deselected, 1 warning in 0.06s`.
2. `python3 -m json.tool .ai/review-runs/T082-AWS-INVITE-PILOT-E/findings.json >/dev/null`
   - PASS.
3. Balanced-delimiter and exact override-structure check over
   `infra/terraform/tests/package_c.tftest.hcl`.
   - PASS: braces, brackets, and parentheses balanced; four
     `override_during = plan` blocks and all four exact resource targets are
     present.
   - Pygments' `TerraformLexer` reports error tokens for existing Terraform
     test-language keywords and is not a usable full HCL parser here; no parser
     PASS is claimed.
4. `git diff --check --no-index /dev/null infra/terraform/tests/package_c.tftest.hcl`
   - PASS for whitespace (the expected diff exit for an untracked file is
     ignored only after `--check` reports no whitespace error).
5. `git diff --check --no-index /dev/null .ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md`
   - PASS for whitespace under the same untracked-file convention.

## Terraform execution evidence

The builder found no local Terraform/OpenTofu CLI. The coordinator then
downloaded Terraform 1.15.8 for Darwin arm64 into a temporary directory from
the official HashiCorp release host. The archive SHA-256
`f210110c5698b94d803a7a63cdb0251b5455c150841478808e2bbb343f95ed68`
matched the official 1.15.8 checksum file. Nothing was installed into the
repository or a system path.

The first sandboxed test reached provider startup but could not bind its local
Unix socket (`operation not permitted`); this was a sandbox failure, not a test
result. The first permitted local run then exposed a real mock dependency:
targeting the task definitions also plans their IAM roles, and the mocked
`aws_iam_policy_document.json` was not valid JSON. The coordinator added one
plan-known valid, empty policy-document mock. This changes test infrastructure
only and does not weaken the bootstrap assertions.

Final command:

`TF_IN_AUTOMATION=1 CHECKPOINT_DISABLE=1 AWS_EC2_METADATA_DISABLED=true /private/tmp/paprnav-terraform.UdPxeL/terraform -chdir=infra/terraform test -filter=tests/package_c.tftest.hcl -no-color`

- PASS: `13 passed, 0 failed`.
- `bootstrap_database_location_is_bound_to_rds` passed at plan time.
- Terraform emitted only expected targeting warnings from the pre-existing
  bounded test design.
- The mock provider made no AWS call and no credentials or secret values were
  supplied.

The coordinator reran the focused Python source oracle after the additional
mock: `1 passed, 26 deselected`. `git diff --check` also passed.

## Review handoff

The independent reviewer should reproduce or inspect the focused Terraform
result, confirm all four plan assertions resolve, inspect the actual working
tree, and disposition E-IMPL-001.

Coordinator extension model/effort: `model not exposed by runtime` / `effort
not exposed`. No AWS/provider/secret mutation, staging, or commit occurred.
