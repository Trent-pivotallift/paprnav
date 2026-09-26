# ACM amendment implementation builder handoff

## Assignment and result

- Builder: `/root/t082_package_c_implementation`.
- Requested route: GPT-5.6 Sol, high effort.
- Actual model and effort: not exposed by the delegated runtime.
- Role: implementation builder only. Independent implementation review and
  approval remain coordinator-owned.

The bounded amendment is ready for independent review. Terraform no longer
declares or validates an ACM certificate or writes ACM validation records. A
required exact certificate ARN is bound to a plan-time, read-only lookup and
its returned ARN, primary domain, issued status, ownership tag, account, and
region before the HTTPS listener can consume it. The application Route53 alias
and its existing hosted-zone identity gate remain. Generated ACM IAM is exactly
`ListCertificates`, `DescribeCertificate`, `ListTagsForCertificate`, and
`GetCertificate`; it contains no wildcard ACM action, mutation action, or
`ExportCertificate`. This handoff is not an approval or deployment authority.

## Provider feasibility evidence

AWS provider 5.100.0 was checked before implementation from the installed
offline schema and the exact tagged provider source. The schema exposes the
required `domain`, `statuses`, `types`, `key_types`, `tags`, `most_recent`,
`arn`, and `status` fields. The tagged implementation performs exact-domain,
status, type, key, and tag filtering; with `most_recent=false` it errors on
multiple matches and also errors on no match. It calls `GetCertificate` for an
issued result. The configuration now pins `= 5.100.0` rather than a provider
range.

- `.terraform.lock.hcl` SHA-256:
  `a2ded1ea551540bbc25f53cd1a941cc1af985df90ab1d3eca2f8d6df467b1808`
- Installed Linux provider binary SHA-256:
  `6c0d4e10cf57e3fcaad0055f7149a32f66e24a63d75e78fe6c8e39013964bfb9`
- Extracted provider-schema JSON SHA-256:
  `a81108c4ed4baa5d7d936384ee6978f2bf8116831b3f171086273fb666227964`
- Tagged source:
  `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v5.100.0/internal/service/acm/certificate_data_source.go`

## Bounded checks

- Isolated source-only Terraform 1.15.0 with cached AWS provider 5.100.0,
  backend removed, network disabled, and no state copied or read:
  `terraform validate -no-color` passed.
- Retained mock plans:
  `terraform test -no-color -filter=tests/package_c.tftest.hcl` passed,
  12 runs. These cover the valid lookup; wrong exact ARN, returned domain,
  returned status, returned tag, account, and region; preserved WAF contract;
  and existing negative deployment gates. The valid run asserts the exact
  issued/Amazon-issued/RSA_2048/Project filters and `most_recent=false`.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest
  backend/tests/test_pilot_package_c.py -q -k 'terraform_gates or acm_policy'`:
  2 passed, 9 deselected; one existing Starlette deprecation warning.
- Python compilation and `git diff --check`: passed.
- No live Terraform plan, apply, AWS read, certificate/DNS mutation, image
  rebuild, staging, or commit was performed.

Mock-provider fixtures cannot exercise the provider's real zero-match or
multiple-match search result. Those cases remain fail-closed in the pinned
provider implementation and are made structurally mandatory by
`most_recent=false`; Package E must supply real read-only lookup/plan evidence.

## Changed files and hashes

| File | SHA-256 |
| --- | --- |
| `infra/terraform/versions.tf` | `eb83c7bbbee497ea0f928408b58d12fe7ac2120d08d41f427c091988ed03a6cf` |
| `infra/terraform/variables.tf` | `8ab402c401f0d394e0ae715654477c4ef2d914cdcb8614a2af4cc24a6442012f` |
| `infra/terraform/main.tf` | `cfb8cfe8890dafc421d462731bce87405baa3b0ae1c847ab70380c99b5b6f4ea` |
| `infra/terraform/load_balancer.tf` | `8ee9a4afc3f5c9330ce77283cb00a89e787ee1cab1c0f85d9a9536344d37a48f` |
| `infra/terraform/outputs.tf` | `6dd533bde5befa1f9540f537fffcc5f4ec3ee4ce979fb365c9c8a681a91a42d8` |
| `infra/terraform/tests/package_c.tftest.hcl` | `571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c` |
| `scripts/generate_pilot_deploy_policy.py` | `46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e` |
| `infra/aws-iam/pilot-policy-matrix.json` | `553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2` |
| `backend/tests/test_pilot_package_c.py` | `3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124` |

This evidence file is intentionally not self-hashed.

## Package E execution preflight and residual inputs

Before any authorized real plan or apply, Package E must record the operator
identity and timestamp and inspect the real backend with a read-only state
listing. If any of these removed addresses exist, stop before planning and
obtain a separately reviewed state handoff: `aws_acm_certificate.pilot`,
`aws_acm_certificate_validation.pilot`, or any
`aws_route53_record.certificate_validation` instance. Configuration removal
must not be allowed to schedule certificate or validation-record destruction.
Existing ACM DNS validation records must remain in Route53 for managed renewal.

Package E evidence must bind the operator principal, timestamp, exact
certificate ARN, primary domain, `ISSUED`/`AMAZON_ISSUED`/`RSA_2048` metadata,
`Project=paprnav`, DNS-validation record presence, state-listing output, and an
authorized refreshing plan. The real hostname/zone, certificate ARN, budget
recipient, updater identity, KMS input, and final ECR digests remain external
inputs and were not guessed. These are blockers to execution-ready evidence,
not blockers to local amendment review.

Package A authority, T081, 0030, `backend/app/models/core.py`, other Package C
remediations, and all reviewer ledgers/state were left untouched by this
amendment builder.
