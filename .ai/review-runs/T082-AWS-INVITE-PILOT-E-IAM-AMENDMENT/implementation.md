# IAM amendment implementation

## Outcome

Implemented the independently approved static IAM amendment without changing
the baseline policy, Terraform resources, Git state, or AWS state. M1 remains
unauthorized and blocked on live identity, strong-authentication, domain, and
policy-consumer evidence.

## Implemented scope

- The generated supplement now grants regional Scheduler inventory, exact
  CRUD/read on `default/paprnav-pilot-worker`, and pass-role of only
  `paprnav-pilot-worker-scheduler-role` to `scheduler.amazonaws.com`.
- WAF reconciliation includes `wafv2:ListTagsForResource` only on the existing
  Paprnav web-ACL and regex-pattern-set ARN patterns.
- Route 53 reads and writes are separate. The exact-zone write statement uses
  `ForAllValues:StringEquals` for normalized `pilot.example.com` fixture names,
  type `A`, and actions `CREATE`, `UPSERT`, and `DELETE`; production generation
  substitutes the validated canonical hostname input.
- Updater proof includes `iam:ListEntitiesForPolicy` on only the supplement.
- `UpdateSecret`, `GetSecretValue`, and `PutSecretValue` remain outside deploy
  authority. The matrix binds `UpdateSecret` to an explicit pre-apply stop gate
  for all three declared secret resources and records separated runtime value
  principals.
- The matrix now covers every declared Terraform AWS resource/data-source type,
  lifecycle actions/authority source, runtime principal separation, quota
  preconditions, and absent/detached/attached/shared/boundary/quota/ambiguous
  publication states.
- Parent Package E now preserves the exact prior attachment/default state,
  requires fully paginated policy and permissions-boundary inventory before
  versioning, and requests accountable-owner plus MFA/federation evidence.
  Its pre-amendment candidate digest is explicitly marked historical.

## Changed files

- `scripts/generate_pilot_deploy_policy.py`
- `infra/aws-iam/pilot-policy-matrix.json`
- `backend/tests/test_pilot_package_c.py`
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md`
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e2-operator-inputs.md`
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e2-preparation.md`
- this artifact

`infra/aws-iam/paprnav-terraform-deploy-policy.json` remains byte-for-byte
unchanged with SHA-256
`da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`.

## Deterministic evidence

Representative compact documents using the reviewed fixture inputs:

| Document | Characters | SHA-256 |
| --- | ---: | --- |
| baseline | 5,011 | `dc7e543afbd7b42f459118591499e9d11f7b5b1be29f8a93e2bf22a8f722083d` |
| supplement | 4,796 | `10d188f490d0f2ec0e66e7da584d775ad6c47116bd00612a3163167726e6d802` |
| invalid merged document | 9,769 | `0c85f79046fc427770c8d14a40e2b65355764871220eaa6196e63f13b15813d7` |

Both separately published policies fit the 6,144-character limit; the merged
document does not. One attachment slot and, for an existing policy, one version
slot remain hard preconditions.

Verification:

- Generator CLI with fixture inputs: pass, 19 supplement statements; generated
  document JSON parse: pass.
- JSON parse of the matrix and unchanged baseline policy: pass.
- Python compile of generator and focused test: pass.
- IAM-focused selection: `7 passed, 25 deselected, 1 warning in 0.07s`.
- Full `test_pilot_package_c.py`: `30 passed, 2 skipped, 81 warnings in 0.09s`.
  The skips were the unavailable current Terraform mock-plan JSON WAF oracle
  and unset disposable PostgreSQL URL; neither covers the amended IAM tests.
- The first attempted pytest path `.venv/bin/pytest` did not exist; the recorded
  results use the repository environment `backend/.venv/bin/pytest` with
  `PYTHONPATH=backend`.
- Repository `git diff --check`: pass. The Git index was not changed.

## Remaining live gates

- canonical hostname, hosted-zone ID/name, issued ACM ARN, and certificate/DNS
  owner remain unavailable;
- exact updater principal/session, accountable owner, and MFA/federation
  provenance remain unavailable;
- root MFA or centralized root-credential-removal evidence remains unavailable;
- supplement existence, versions/default/hash, exact attachment pre-state,
  fully paginated permissions-policy and permissions-boundary consumers, and
  attachment/version quotas require fresh live proof;
- KMS effective use, Access Analyzer validation, effective-policy simulation,
  SCP/session-policy effects, and post-attachment service inventory remain
  unverified; and
- explicit M1 authorization has not been given. No updater call, attachment,
  policy version, deletion, Terraform action, or AWS mutation is authorized by
  this implementation.

## Model routing

- Builder runtime identity: `/root/t082_e_iam_amendment_impl`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: independently approved coherent multi-file IAM implementation with
  deterministic positive/negative oracles; preferred route is GPT-5.6 Sol high.
- Independent implementation and closure reviewer: not assigned by this
  builder; the coordinator must record the actual returned reviewer identity
  and exposed model/effort in new immutable review artifacts.
