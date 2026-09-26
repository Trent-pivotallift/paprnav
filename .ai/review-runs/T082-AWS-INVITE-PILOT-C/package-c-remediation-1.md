# Package C remediation 1 builder handoff

## Outcome

This bounded builder pass implements T082-C-007 through T082-C-014 as one
remediation family. It is builder evidence for independent review, not an
approval or deployment authorization. No Terraform apply, ECR push, AWS secret
write, DNS/certificate mutation, AWS migration, service activation, or
staging/commit in the working repository was performed.

`backend/app/models/core.py`, the preserved T081 Slice 4B family, every 0030
artifact, and the sealed Package A authority were not edited by this builder.

## Model routing

- Builder runtime identity: `/root/t082_package_c_remediation_1`.
- Requested route: GPT-5.6 Sol at xhigh effort, because this is the first
  remediation after a substantive failed implementation review.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed by runtime`.
- Role: remediation builder only; no self-review or reviewer verdict was
  produced.

## Finding disposition implemented

- **T082-C-007:** API and worker now select the `DATABASE_URL` key from the
  JSON Secrets Manager value. The retained test resolves the resulting ECS
  reference and proves that exact URL reaches the application's
  `Settings.database_url` field.
- **T082-C-008:** generated database URLs retain ordinary percent-encoding for
  publication, while the migration subprocess alone doubles `%` at the
  ConfigParser/Alembic boundary. Bounded reserved characters are tested through
  both URL construction and the actual `run_migration` environment.
- **T082-C-009:** warning-only external-input/image checks were replaced by
  blocking lifecycle preconditions. The gate verifies exact ECR repository
  identity, real external inputs, and the actual public Route53 zone returned
  for the supplied zone ID. Retained mock-provider plans cover valid input,
  wrong API repository, wrong hosted-zone identity, and placeholder external
  input.
- **T082-C-010:** WAF login/invitation classification now URL-decodes routed
  paths and recognizes the routed trailing-slash/redirect form. The upload
  exception remains an exact undecoded `/api/v1/documents/upload` match.
- **T082-C-011:** WAF request sampling is disabled for every visibility config.
- **T082-C-012:** ACM request scope is the one canonical pilot hostname with
  DNS validation and required Paprnav request tag. Existing-certificate
  read/delete/tag mutation requires the pre-existing Paprnav resource tag;
  tag actions cannot add or remove the ownership key. Positive and negative
  generator assertions are retained.
- **T082-C-013:** the release builder invokes Package A's candidate/protected-
  blob verifier before context construction. Overlay schema v2 separates
  reviewed build inputs from explicitly preserved exclusions, requires their
  exact union to equal dirt, and bars overlay replacement of Package A
  authority paths. Positive/negative candidate and overlay tests are retained.
- **T082-C-014:** `backend/tests/test_pilot_package_c.py` and
  `infra/terraform/tests/package_c.tftest.hcl` provide one small retained
  regression family for configuration injection, reserved credentials,
  bootstrap rollback/concurrency/second-use behavior, context authority,
  IAM/ACM, WAF, Terraform gates, and static image inventory.

## Bounded verification evidence

- Python compile, JSON parse, and `git diff --check`: pass on the final builder
  files.
- Focused retained suite with disposable PostgreSQL 16.10:
  `11 passed, 1 warning in 0.63s`. It covered five injected first-admin rollback
  points, concurrent distinct callers (one success and one rejection),
  permanent second-use rejection, and the non-database Package C assertions.
- Isolated source-only Terraform 1.15.0 / AWS provider 5.100.0 validation:
  pass. Mock-provider gate tests: `4 passed, 0 failed`. Module formatting passed
  in the isolated run; after the test file's whitespace-only alignment fix, a
  final cached read-only container recheck could not read the host bind mount
  (`Cannot read directory infra/terraform`). It was not retried.
- A disposable authority-valid candidate clone passed Package A verification:
  exact 44 migration-authority blobs, protected model baseline, head 0029, and
  absence of excluded T081/0030 paths. The clone-only candidate commit was
  `d6cccfd0deba8d3a06f5320cc8a23b2e0020e797`; the working repository was not
  staged or committed.
- Clean contexts constructed from that candidate:

  | Context | Files | Manifest SHA-256 |
  | --- | ---: | --- |
  | API | 153 | `8ed8c2f2a23b4a2c8f05caf528c2a3cd03d82e334894d4103bbae0f4e98c2d79` |
  | frontend | 64 | `22adfe5addeba35408c07c0b096d5c906e40996e6a2d020e75fa50ad89eb3d29` |
  | bootstrap | 51 | `eeb0c9c8d674c69d81f1c626cfad6fd40c655e7b53aaa65614a67a7c0b1838e4` |

  Bootstrap's nested migration-manifest SHA-256 was
  `1c9152c3d46f50c42a536465160609d75469a38b1801254730ec2f5f6c3ad91b`.
- Local three-image construction completed before the interruption. A final
  read-only inventory confirmed all three retained tags are `linux/amd64` and
  use `10001:10001`:

  | Image | Local image ID |
  | --- | --- |
  | `paprnav-package-c-api:remediation-1` | `sha256:1dc8fa927c6cf33542ca4492d6e8daa9d0c3e4d6cb2b20aa3dc6aaad047912b5` |
  | `paprnav-package-c-frontend:remediation-1` | `sha256:62acb436c77b775f4e90cdccf2c812a2425035da970371ab0e600f592937a008` |
  | `paprnav-package-c-bootstrap:remediation-1` | `sha256:e1020ff24d182e8fa21de58e2e5573506d01d33e1b032c1ca25a55a70451f1b9` |

  Inventory assertions found the API release manifest and no tests/0030 path;
  the frontend server and no tests/workspace path; and only the reviewed
  bootstrap files plus the sealed 44-input migration context, with no
  application checkout or 0030 path. These local image IDs are not pushed ECR
  repository digests.

## Changed files and final hashes

| File | SHA-256 |
| --- | --- |
| `infra/bootstrap/bootstrap.py` | `11df37c395e8bb2955f8b6f828943119e73dee0ba7b16ff0db49e9f1718073d4` |
| `infra/terraform/ecs_runtime.tf` | `6f0c3e1296ff67269841d421fbf94f404036676a3ef36654f73240d794633891` |
| `infra/terraform/load_balancer.tf` | `fcd004de0baa0b5f9722dd62a126ba34a124c555d1cb861fee6b57c90ba48852` |
| `infra/terraform/main.tf` | `857e39d2e44c31ee55b62889bf13c468080f5f2b2883018612aa2b9572e6c3e9` |
| `infra/terraform/variables.tf` | `649152cd6480ab966752d63284e9ba1ed7a7e6b8e30bd9c82e0f530a148ae2e4` |
| `infra/terraform/tests/package_c.tftest.hcl` | `60a9ac84ce31b287c51880be3f56dc646ad8016dd7900e8060df55a175ca1a10` |
| `infra/aws-iam/pilot-policy-matrix.json` | `6005347422599660eaa5669319ebfc491daf3fb935f46c288da711fe45d673c6` |
| `scripts/build_pilot_release_context.py` | `7625442d2f4c4bf856c1daa5d91e948ba40b669e29a69c5f1e43f8dccb381b7d` |
| `scripts/generate_pilot_deploy_policy.py` | `4c18a26de9a61a6c40be86eb4983a182acc929cfbebc1846f9ead56e747a3cce` |
| `backend/tests/test_pilot_package_c.py` | `79ed949b42a5977ea5e559b32839ac3cc9215b5adff3a7a19a9b8de9c8090a79` |

This handoff artifact is the eleventh changed file and is intentionally not
self-hashed.

## Unresolved execution-only inputs and signals

Package E still requires the canonical hostname and matching Route53 zone
ID/name, real budget recipient, authorized policy-updater principal, resolved
Secrets Manager KMS key ARN, refreshed AWS inventory, Access Analyzer and
policy-simulation evidence, pushed ECR digests, and an independently authorized
refreshing Terraform plan. DNS/certificate mutation, secret writes, migrations,
and service activation remain unperformed.

The successful frontend `npm ci` emitted an audit summary of 12 dependency
findings (1 low, 2 moderate, 8 high, 1 critical). Dependency upgrades were not
part of this bounded remediation; this signal requires independent disposition
before deployment and is not hidden by the successful image build.
