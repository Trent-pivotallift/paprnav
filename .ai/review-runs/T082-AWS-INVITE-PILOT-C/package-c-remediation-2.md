# Package C remediation 2 builder handoff

## Model routing

- Builder identity: `/root/t082_package_c_remediation_2`.
- Requested route: GPT-6 Astra xhigh, because the WAF/IAM finding family recurred
  after substantive implementation reviews and required invariant/oracle repair.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Roles: remediation builder and focused verification builder. Independent
  review, finding dispositions, and closure remain coordinator-owned.

## Result and remaining blocker

C-010 and C-014 have structural fixes and bounded evidence ready for independent
review. C-015 has a patched, built, and locally exercised standalone image.
C-012's ownership-mutation defect is fixed, but its initial-certificate
provisioning contract needs a design amendment before closure. This handoff is
not approval, a finding closure, or authorization to deploy.

The invitation rate rule now applies `URL_DECODE` to its URI predicate and
`NONE` to its exact POST predicate, matching login. The raw exact upload
exception is unchanged. The retained oracle consumes Terraform's actual
generated resource changes, resolves emitted regex ARNs, and evaluates emitted
field selections and transformations. It covers encoded/trailing-slash login,
invitation creation and acceptance; wrong methods and neighboring paths;
independent limits/priorities; disabled sampling; the managed body override;
and the raw multipart upload exception and 8192-byte boundary. Terraform also
asserts the auth field/transform structure directly. A mutation witness moves
the invitation transform back onto the method and is rejected by the same
oracle.

ACM tag-on-create and later tag-key lists are separate. Both later tag actions
require pre-existing `Project=paprnav`, exact account/region resources, and the
explicit non-ownership key allowlist. Adding, replacing, reasserting, or
removing `Project` is denied. The bounded IAM evaluator applies every condition
of every applicable generated statement, including IAM's absent-set semantics,
instead of checking strings. Positive/negative cases cover ownership, mixed
tag keys, requested tag values, domains, validation method, region, and account.
The remediation-1 ownership replacement is reconstructed and rejected by the
same assertions.

AWS's current [ACM authorization reference](https://docs.aws.amazon.com/service-authorization/latest/reference/list_acm.html)
maps the `RequestCertificate` API to both `acm:RequestCertificate` and
`acm:AddTagsToCertificate`. Our individual request-action allow is therefore
not proof that the API can create a tagged certificate: its dependent Project
tag operation is denied. The supported AddTags conditions do not establish a
safe distinction between initial ownership assignment and direct tagging of an
existing certificate. The code, policy matrix, and retained test expose this
gap; no undocumented condition or broader ownership-tag permission was added.

Minimal amendment options for the coordinator/design reviewer are (1) a
separately authorized operator provisions the owned certificate and supplies
its exact ARN for the deploy graph, or (2) separately reviewed provisioning
authority establishes initial ownership with an explicit resource/lifecycle
boundary. Either changes the current certificate-provisioning design and must
be reviewed before implementation. C-012 is not ready to close.

## Exact bounded checks

- `npm install --package-lock-only --ignore-scripts --no-audit --no-fund
  --cache /private/tmp/paprnav-c-remediation-2-npm-cache` from the frontend:
  successful exact `next=16.2.5` / `eslint-config-next=16.2.5` resolution.
- `npm run test:pilot` from the frontend: 1 passed. Native Node 24.13.0.
- Cached isolated Terraform 1.15.0 / AWS provider 5.100.0, with current `.tf`
  sources and no network: `terraform fmt -check -recursive`,
  `terraform validate -no-color`, and
  `terraform test -json -verbose -filter=tests/package_c.tftest.hcl` passed;
  5 mock-plan runs passed, including the new WAF run and three expected-negative
  execution gates. No live plan or apply was performed.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest
  backend/tests/test_pilot_package_c.py -q -k 'not first_admin and not waf_generated'`:
  9 passed, 2 deselected. Existing pytest old-temp cleanup warnings were emitted.
- `PAPRNAV_PACKAGE_C_TERRAFORM_TEST_JSON=/private/tmp/paprnav-t082-c-remediation-2.0ZcD3C/terraform-output.log
  PYTHONPATH=backend backend/.venv/bin/python -m pytest
  backend/tests/test_pilot_package_c.py -q -k waf_generated`:
  1 passed, 10 deselected, using the current generated plan.
- After adding the explicit ACM provisioning-gap assertion,
  `PYTHONPATH=backend backend/.venv/bin/python -m pytest
  backend/tests/test_pilot_package_c.py -q -k acm_policy
  --basetemp /private/tmp/paprnav-t082-c-remediation-2.0ZcD3C/pytest-acm-final`:
  1 passed, 10 deselected.
- Python compilation and `git diff --check`: passed. The main repository and
  disposable candidate have no staged changes.

The first-admin fixture is explicitly documented as synthetic transaction and
control evidence. It does not prove compatibility with the complete migrated
0029 schema. That unchanged fixture and the prior API/bootstrap images were
not rebuilt or retested; remediation-1 supplies their evidence. No broad suite
or new migrated-schema matrix was run.

The Python WAF test requires the generated JSON path above (and explicitly
skips without it); Terraform's retained structural assertions run independently
as part of its mock tests. Regenerate JSON from current sources when reviewing
or changing the WAF. Source hashes below match the isolated Terraform inputs.

## Frontend production evidence

The [maintainer advisory](https://github.com/vercel/next.js/security/advisories/GHSA-c4j6-fc7j-m34r)
identifies 16.2.5 as the patched Next 16 release for the WebSocket SSRF. Both Next
and its lint configuration are pinned exactly to 16.2.5 with registry integrity
entries in the generated lockfile. The resolver also refreshed two existing
development transitive packages and bundled-lock metadata; no unrelated audit
fix command was used.

A fresh disposable clone of the previous authority-valid candidate
`d6cccfd0deba8d3a06f5320cc8a23b2e0020e797` received only the two package-file
overlays. No new commit was created. The release builder performed the Package
A authority gate and produced a 64-file frontend context. All 64 files were
hash-compared to the current workspace frontend and matched. Re-running the
builder's `verify` action reproduced manifest SHA-256
`c893f4108500beb28a076518e1b10ff3e695766548cfc9278d834742aa107562`.
The existing overlay schema names these `reviewedInputs`; in this builder pass
the new package bytes are provisional evidence awaiting independent review.

The single production-image build command was:

```sh
docker build --platform linux/amd64 --pull=false \
  -t paprnav-package-c-frontend:remediation-2 \
  /private/tmp/paprnav-t082-c-remediation-2.0ZcD3C/frontend
```

It completed `npm ci --ignore-scripts`, Next 16.2.5 production compilation,
TypeScript, all 13 static pages, and standalone image export. The local image
ID is `sha256:69c3795b1a8bcd6e98cfab957b43eea7c827f8d4875c1bed4633c4b8ac5671fb`;
the Linux image manifest is
`sha256:9325c3ce4946bc35da2b87d2313f42e9f19f3dd565543977b8ccca80d1d35f95`.
These are local identifiers, not pushed ECR digests.

Inventory inside that image confirmed `linux/amd64`, UID 10001, and precisely
the production Next-family manifests `/app/node_modules/next/package.json`
and `/app/node_modules/@next/env/package.json`, both version 16.2.5. No Next
16.1.6 package, `/workspace`, or `/app/tests` was found.

A non-root, read-only container with no network or published ports and a `/tmp`
tmpfs started its real `server.js`. With `PAPRNAV_ENV=pilot` matching
`aws_ecs_task_definition.frontend`, `/` and `/invite` returned 200;
`/api/backend/auth/login` and `/api/v1/ads/v4` returned 404. The first smoke
harness omitted that ECS environment variable and consequently exercised the
local proxy, returning 500 with no backend. The corrected harness passed on
the same image; no rebuild or dependency retry was needed. An initial native
test invocation used the repository root rather than the frontend directory,
and the first Terraform formatting check required whitespace normalization;
both invocation/formatting issues were corrected before the passing checks.

`npm ci` still reports 12 aggregate audit findings (1 low, 2 moderate, 8 high,
1 critical). This handoff proves the identified Next SSRF version is removed,
not that every dependency finding is resolved. Prior feature/platform-specific
audit dispositions remain subject to independent review.

## Changed files and hashes

| File | SHA-256 |
| --- | --- |
| `infra/terraform/load_balancer.tf` | `4262284e6047de8bf2063c96369f08f8d12e30cb5774e5b429290cb25ba86818` |
| `scripts/generate_pilot_deploy_policy.py` | `3d79da4ead52496f2262ecf9f8da40d63179a4eab881c08257f5784a793127c0` |
| `infra/aws-iam/pilot-policy-matrix.json` | `b0c21e772c850b55e9cd6d34bfa9a0c45148a246804b52690b99cb975502a470` |
| `backend/tests/test_pilot_package_c.py` | `f1ce2a22e8858e23e52c1fc779c44bdbac3291a81b950be44cf754e893dd4b0d` |
| `infra/terraform/tests/package_c.tftest.hcl` | `2436cdb89eeb0ccde1d3a2a3a8e15bb47477d3f6ae9512644d438cf6dcafe943` |
| `frontend/paprnav-frontend/package.json` | `838f7488e4eeca4f619cc3811191a5b31f025c8e84f76eb39ffe4913ccbcfa99` |
| `frontend/paprnav-frontend/package-lock.json` | `3f4b0a0cce3719c8434611f1133ab78f1ef45971a06b99e2f1f9473b1aa1710a` |

This handoff is the eighth changed file and is not self-hashed. Local retained
logs under `/private/tmp/paprnav-t082-c-remediation-2.0ZcD3C/` are:

- `frontend-build.log`: `e2d0523cdb9766dc55562a2bf0912550bdc4f77ad10ccedd2f39960a984c1664`.
- `terraform-output.log`: `f863dd0045716d2a016fffc8c45de2700c96898385d3ae75543e89fb117a2f8d`.

## Preserved scope and residual gates

No edits were made to Package A sealed authority, T081 Slice 4B, 0030 artifacts,
or `backend/app/models/core.py`. Findings/reviews/state and reviewer artifacts
were not edited. No staging, commit, Terraform apply, push, AWS/secrets/DNS/
certificate mutation, AWS migration, or service activation occurred.

The ACM provisioning amendment is a design blocker, not merely missing live
execution evidence. Beyond that amendment and independent implementation/
closure review, Package E retains operator identities and real hostname/zone/
budget/KMS inputs, refreshed AWS inventory and policy evidence, an approved
committed candidate, pushed ECR digests, an authorized refreshing plan, and the
deployed TLS/WAF/bootstrap/database/browser proofs.
