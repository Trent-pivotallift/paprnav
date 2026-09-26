# Package C implementation handoff

## Outcome

The bounded local Package C family is ready for independent implementation
review. No Terraform apply, ECR push, secret value write, DNS/certificate
mutation, AWS migration, service activation, staging, or commit was performed.
API and frontend desired counts are fixed at zero and the worker schedule is
fixed `DISABLED`.

## Model routing

- Builder runtime identity: `/root/t082_package_c_implementation`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: approved coherent multi-file implementation with IAM,
  authorization, concurrency, migration, and public-ingress invariants.
- Role: builder only; no self-review or reviewer verdict was produced.

## Implemented scope

- Deterministic explicit-ref API/frontend/bootstrap context policy and builder:
  `.ai/pilot-package-c-context-v1.json` and
  `scripts/build_pilot_release_context.py`.
- Digest-pinned, non-root API/frontend images with hash-pinned Python/npm
  inputs: `backend/Dockerfile`, `backend/requirements.lock`,
  `frontend/paprnav-frontend/{Dockerfile,.dockerignore,next.config.ts}`.
- Dedicated sealed bootstrap image/program and manifests:
  `infra/bootstrap/{Dockerfile,bootstrap.py,requirements.in,requirements.lock,grant-manifest.json,reference-data.json}`.
  Its fixed phases are `migration`, `runtime-role`, `reference`, and
  `first-admin`; it contains no application checkout path.
- HTTPS ACM/Route53/ALB routing, regional WAF managed-common policy with the
  reviewed multipart exception and independent login/invitation rate rules,
  split security groups, digest-only task inputs, split execution/task roles,
  app/admin secret boundaries, zero services, and disabled worker:
  `infra/terraform/{database.tf,ecs_runtime.tf,load_balancer.tf,main.tf,network.tf,outputs.tf,variables.tf}`.
- Explicit prerequisite matrix and generator:
  `infra/aws-iam/pilot-policy-matrix.json` and
  `scripts/generate_pilot_deploy_policy.py`. The generated deploy supplement
  omits application secret-value read/write; the updater policy is bound to
  the one existing deploy-policy ARN.

`backend/app/models/core.py`, every preserved T081 Slice 4B artifact, and every
0030 artifact were not edited by this builder.

## Verification performed

- Python compile and JSON parsing: pass for all new scripts/manifests.
- Terraform 1.15.0 isolated `init -backend=false` and `validate` with locked
  AWS provider 5.100.0: pass. Formatting was applied and rechecked during the
  same isolated source-only workflow; no state file was copied or read.
- Disposable PostgreSQL 16.10: migrations 0001 through exact head
  `20260913_0029` passed. The resulting reviewed grant inventory contains 113
  app tables, explicitly excludes `alembic_version`, and contains zero public
  sequences.
- Bootstrap integration: pass for exact inventory/grants, idempotent three-row
  reference bootstrap, five injected first-admin rollback boundaries,
  permanent second-use and post-revocation rejection, app denial for DDL,
  role escalation, `alembic_version`, and `pilot_control`, and fresh
  same-password app connection proof. Fake Secrets Manager evidence recorded
  zero `GetSecretValue` calls for the app database secret.
- IAM fixture generation/assertions: pass (16 supplement statements; no app
  secret `GetSecretValue`/`PutSecretValue`; exact deploy-policy updater ARN).
- Dirty-tree release negative: pass; context construction failed closed before
  output because no reviewed overlay manifest covered the current dirty tree.
- Existing frontend pilot boundary test: 1 passed.

## Bound artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `.ai/pilot-package-c-context-v1.json` | `b13c07ce5831eba17221363d07fa3db23ed4a1187b16b47b9e6fe9b020756e41` |
| `infra/bootstrap/Dockerfile` | `6b2daf14fa8768d436cad4ecffcf4f81af040834dbcc40a4ff2fd51e697f3262` |
| `infra/bootstrap/bootstrap.py` | `2412fab7deb9cd1579ebd2659e8299c19df0f58da3249d4d9e795d6bf453f2b2` |
| `infra/bootstrap/grant-manifest.json` | `8bb97bb77a72452eb20b2404ce0ad2139bb763ad2917c31833f13ff99aa43fac` |
| `infra/bootstrap/requirements.lock` | `221371094f52ace94027bef0da5b06fd8f37827ccfe71cdbeced10f5c2263cc5` |
| `backend/requirements.lock` | `729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d` |
| `frontend/paprnav-frontend/Dockerfile` | `3f4e91bd8de248533293750490a4fb7346255a59fd9756965173944cbafab418` |
| `infra/aws-iam/pilot-policy-matrix.json` | `26daa18cd54b00bfa1b711ad5c7d2ceef7ada624d37d77f299d1cac0bd572c79` |
| `scripts/build_pilot_release_context.py` | `0f42caef0db9630cc5bb638d5e86349fa3e3bcbada37efacbc109a9c4115d83a` |
| `scripts/generate_pilot_deploy_policy.py` | `7c85de8875ccbcffaf3fbd312925cb061476d5097850566a76b3820e0a6d6b89` |

## Execution-gate inputs and unverified evidence

The local implementation is not blocked, but an execution-ready plan and image
evidence remain blocked on operator-owned inputs: canonical pilot hostname,
matching Route53 zone ID/name, real budget recipient, authorized deploy-policy
updater principal, resolved Secrets Manager KMS key ARN, and final pushed ECR
digests for API/frontend/bootstrap. These were not guessed. Consequently no
refreshing Terraform plan, candidate-commit context hash, container build/image
inventory, Access Analyzer result, or cloud execution is claimed here. Package
E must supply those inputs, regenerate the policies/contexts from the reviewed
candidate commit, and obtain independent authorization before mutation.
