# Review packet: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

Stage: closure
Generated: 2026-09-19T19:48:48+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `d46390671b9d4925deedeb49f89ee159a71cba67fe32feaf46db2e18c4ad7a06`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

## Objective

Remove the unresolved ACM ownership bootstrap conflict from Package C without
granting the Terraform deploy principal authority to manufacture ownership on
an unrelated certificate. Preserve an HTTPS-ready invite pilot by treating the
certificate as an operator-provisioned, independently owned prerequisite that
Terraform verifies and consumes read-only.

## User-visible outcome

Invited users still reach the pilot over the canonical HTTPS hostname. The
deployment cannot create, retag, or delete certificates; it can only attach the
one already-issued Paprnav-owned certificate supplied for that hostname.

## Safety and correctness invariants

1. The Terraform deploy principal has no ACM mutation action, including
   `RequestCertificate`, `AddTagsToCertificate`, `RemoveTagsFromCertificate`,
   or `DeleteCertificate`.
2. An operator supplies one exact certificate ARN after provisioning and DNS
   validation through separately authorized administration.
3. Terraform fails before resource mutation unless the resolved certificate is
   issued, in the deployment region and account, covers the exact canonical
   pilot hostname, carries `Project=paprnav`, and resolves to the supplied ARN.
4. The HTTPS listener consumes that verified ARN; Terraform does not create
   ACM validation records or manage certificate lifecycle.
5. The deployment may still create the application Route53 alias after the
   existing hosted-zone identity gate passes.
6. Certificate provisioning evidence and identity are recorded as Package E
   execution inputs; they are not fabricated by local tests.

## Current behavior

Package C declares an `aws_acm_certificate`, DNS validation records, and an
`aws_acm_certificate_validation` resource. Immutable ownership correctly bars
the deploy principal from later changing the `Project` tag, but AWS maps tagged
`RequestCertificate` to the dependent `AddTagsToCertificate` authorization.
No documented condition safely distinguishes initial ownership assignment from
direct self-tagging of an existing unowned certificate. The strongest safe IAM
policy therefore blocks the current creation flow.

## Proposed design

- Remove the certificate and certificate-validation resources from Package C.
- Add required `pilot_certificate_arn` input and retain the canonical
  `pilot_hostname`, region, account, and public hosted-zone inputs.
- Resolve the unique issued Amazon certificate for the exact hostname with the
  AWS provider's read-only ACM data source, filtered by `Project=paprnav`.
  Add blocking preconditions that its returned ARN equals the supplied ARN and
  that the ARN encodes the configured region/account. The design reviewer must
  confirm the provider data source exposes enough status/domain/tag evidence;
  if not, implementation stops rather than weakening the invariant.
- Point the HTTPS listener directly at the verified supplied ARN.
- Replace generated ACM mutation permissions with only the read actions needed
  by that data lookup and plan. Retain explicit assertions that no ACM mutation
  action is emitted.
- Package E records the operator principal, certificate ARN, domain, status,
  ownership tag, and validation state before an authorized plan/apply.

## Alternatives considered

- **Grant tag-on-create authority to the deploy role:** rejected because the
  supported conditions do not prove that the same permission cannot directly
  assign ownership to an existing certificate.
- **Create a dedicated certificate-provisioning role/workflow:** defensible but
  unnecessary machinery for the invite-pilot MVP. It can be designed later if
  recurring automated certificate lifecycle becomes valuable.
- **Block WebSocket/TLS at another proxy or use an unverified certificate:**
  rejected; neither resolves ownership authority or provides the required
  public HTTPS boundary.

## Trust, authorization, and audit boundaries

The separately authorized operator is the sole certificate-provisioning and
initial-ownership authority. The Terraform deploy role receives read-only ACM
discovery/description authority and cannot create, tag, untag, or delete. The
reviewed hostname, zone, account, region, ownership tag, and exact ARN form the
handoff contract. Package E must retain the real AWS evidence and identity of
the operator; local mocks prove only fail-closed wiring.

## Read paths and consumers

- Terraform ACM data lookup reads the issued certificate metadata.
- Blocking preconditions consume certificate ARN, canonical hostname, region,
  account, status/type, and ownership tag evidence.
- The ALB HTTPS listener consumes only the verified ARN.
- Package E runbook and execution packet consume the operator evidence.

## Write paths and administrative paths

- Package C writes no ACM resource.
- The operator provisions and validates the certificate outside this Terraform
  deployment under separately authorized administration.
- Terraform retains its existing Route53 application-alias write after zone
  identity verification; it no longer writes certificate-validation records.

## Migration, compatibility, correction, and rollback

No Package C resources have been applied, so this is a pre-deployment contract
change with no Terraform state migration or cloud deletion. A wrong, missing,
unissued, differently tagged, cross-account, cross-region, or hostname-mismatched
certificate must stop planning. Correction is to supply or provision the right
certificate. Rollback to Terraform-managed certificate creation is forbidden
without a new reviewed ownership-authority design.

## Test strategy

- Retained Terraform mock plans: valid exact certificate; wrong ARN; wrong
  hostname/status/tag/account/region; ambiguous or absent lookup where the
  provider supports those fixtures.
- Retained IAM generator assertions: exact read actions needed by the data
  source and zero ACM mutation actions.
- Structural assertion: HTTPS listener uses the verified supplied ARN and no
  ACM certificate/validation or validation-record resource remains.
- Existing focused Package C WAF, secret, bootstrap, authority, image, and
  Next.js evidence remains valid unless a changed dependency can affect it.
- Package E supplies real read-only ACM/Route53 inventory and an authorized
  refreshing plan; mocks do not substitute for this evidence.

## Expected file scope

- `infra/terraform/load_balancer.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf` if certificate output semantics change
- `infra/terraform/tests/package_c.tftest.hcl`
- `scripts/generate_pilot_deploy_policy.py`
- `infra/aws-iam/pilot-policy-matrix.json`
- `backend/tests/test_pilot_package_c.py`
- Package C builder/review artifacts

No Package A sealed authority, T081 Slice 4B, 0030 artifact, application model,
or public API contract is in scope.

## Known uncertainty

The AWS provider data source's exact selection and exposed metadata must be
confirmed from the installed provider schema during implementation. Real AWS
certificate inventory remains unavailable to the current deploy principal and
is a Package E prerequisite. If exact read-only verification cannot be
expressed, the amendment returns to design review rather than granting
mutation authority.

## Model routing

- Coordinator: `/root`; actual model and effort are not exposed by runtime.
- Amendment designer: `/root`; actual model and effort are not exposed by
  runtime.
- Required independent reviewer: `/root/t082_pilot_design_adversary`, requested
  GPT-6 Astra xhigh.
- Trigger: ambiguous IAM/resource-ownership design discovered after a repeated
  high-risk implementation finding.


## Current finding ledger

```json
[
  {
    "id": "T082-C-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Final closure artifacts enumerate every meaningful phase, role, identity, requested route, and actual model and effort or runtime non-disclosure.",
    "summary": "The closure reports omitted a complete mandatory model-assignment summary.",
    "evidence": ["../T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md", ".ai/MODEL_ROUTING.md", "closure.md", "../T082-AWS-INVITE-PILOT-C/closure.md"],
    "impact": "The high-risk amendment cannot close without auditable model-routing evidence.",
    "requiredClosure": "Add complete Model assignments sections to both closure reports, preserving historical artifacts, and obtain documentation/integrity re-attestation.",
    "closureEvidence": ["closure.md", "../T082-AWS-INVITE-PILOT-C/closure.md", "../T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md"]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md`

size=7700; sha256=5530a6fc969d1133b7c638307ec43aa50861efb2bfd7d720dfd5d83ca0bae7c7

```text
# Decision packet: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

## Objective

Remove the unresolved ACM ownership bootstrap conflict from Package C without
granting the Terraform deploy principal authority to manufacture ownership on
an unrelated certificate. Preserve an HTTPS-ready invite pilot by treating the
certificate as an operator-provisioned, independently owned prerequisite that
Terraform verifies and consumes read-only.

## User-visible outcome

Invited users still reach the pilot over the canonical HTTPS hostname. The
deployment cannot create, retag, or delete certificates; it can only attach the
one already-issued Paprnav-owned certificate supplied for that hostname.

## Safety and correctness invariants

1. The Terraform deploy principal has no ACM mutation action, including
   `RequestCertificate`, `AddTagsToCertificate`, `RemoveTagsFromCertificate`,
   or `DeleteCertificate`.
2. An operator supplies one exact certificate ARN after provisioning and DNS
   validation through separately authorized administration.
3. Terraform fails before resource mutation unless the resolved certificate is
   issued, in the deployment region and account, covers the exact canonical
   pilot hostname, carries `Project=paprnav`, and resolves to the supplied ARN.
4. The HTTPS listener consumes that verified ARN; Terraform does not create
   ACM validation records or manage certificate lifecycle.
5. The deployment may still create the application Route53 alias after the
   existing hosted-zone identity gate passes.
6. Certificate provisioning evidence and identity are recorded as Package E
   execution inputs; they are not fabricated by local tests.

## Current behavior

Package C declares an `aws_acm_certificate`, DNS validation records, and an
`aws_acm_certificate_validation` resource. Immutable ownership correctly bars
the deploy principal from later changing the `Project` tag, but AWS maps tagged
`RequestCertificate` to the dependent `AddTagsToCertificate` authorization.
No documented condition safely distinguishes initial ownership assignment from
direct self-tagging of an existing unowned certificate. The strongest safe IAM
policy therefore blocks the current creation flow.

## Proposed design

- Remove the certificate and certificate-validation resources from Package C.
- Add required `pilot_certificate_arn` input and retain the canonical
  `pilot_hostname`, region, account, and public hosted-zone inputs.
- Resolve the unique issued Amazon certificate for the exact hostname with the
  AWS provider's read-only ACM data source, filtered by `Project=paprnav`.
  Add blocking preconditions that its returned ARN equals the supplied ARN and
  that the ARN encodes the configured region/account. The design reviewer must
  confirm the provider data source exposes enough status/domain/tag evidence;
  if not, implementation stops rather than weakening the invariant.
- Point the HTTPS listener directly at the verified supplied ARN.
- Replace generated ACM mutation permissions with only the read actions needed
  by that data lookup and plan. Retain explicit assertions that no ACM mutation
  action is emitted.
- Package E records the operator principal, certificate ARN, domain, status,
  ownership tag, and validation state before an authorized plan/apply.

## Alternatives considered

- **Grant tag-on-create authority to the deploy role:** rejected because the
  supported conditions do not prove that the same permission cannot directly
  assign ownership to an existing certificate.
- **Create a dedicated certificate-provisioning role/workflow:** defensible but
  unnecessary machinery for the invite-pilot MVP. It can be designed later if
  recurring automated certificate lifecycle becomes valuable.
- **Block WebSocket/TLS at another proxy or use an unverified certificate:**
  rejected; neither resolves ownership authority or provides the required
  public HTTPS boundary.

## Trust, authorization, and audit boundaries

The separately authorized operator is the sole certificate-provisioning and
initial-ownership authority. The Terraform deploy role receives read-only ACM
discovery/description authority and cannot create, tag, untag, or delete. The
reviewed hostname, zone, account, region, ownership tag, and exact ARN form the
handoff contract. Package E must retain the real AWS evidence and identity of
the operator; local mocks prove only fail-closed wiring.

## Read paths and consumers

- Terraform ACM data lookup reads the issued certificate metadata.
- Blocking preconditions consume certificate ARN, canonical hostname, region,
  account, status/type, and ownership tag evidence.
- The ALB HTTPS listener consumes only the verified ARN.
- Package E runbook and execution packet consume the operator evidence.

## Write paths and administrative paths

- Package C writes no ACM resource.
- The operator provisions and validates the certificate outside this Terraform
  deployment under separately authorized administration.
- Terraform retains its existing Route53 application-alias write after zone
  identity verification; it no longer writes certificate-validation records.

## Migration, compatibility, correction, and rollback

No Package C resources have been applied, so this is a pre-deployment contract
change with no Terraform state migration or cloud deletion. A wrong, missing,
unissued, differently tagged, cross-account, cross-region, or hostname-mismatched
certificate must stop planning. Correction is to supply or provision the right
certificate. Rollback to Terraform-managed certificate creation is forbidden
without a new reviewed ownership-authority design.

## Test strategy

- Retained Terraform mock plans: valid exact certificate; wrong ARN; wrong
  hostname/status/tag/account/region; ambiguous or absent lookup where the
  provider supports those fixtures.
- Retained IAM generator assertions: exact read actions needed by the data
  source and zero ACM mutation actions.
- Structural assertion: HTTPS listener uses the verified supplied ARN and no
  ACM certificate/validation or validation-record resource remains.
- Existing focused Package C WAF, secret, bootstrap, authority, image, and
  Next.js evidence remains valid unless a changed dependency can affect it.
- Package E supplies real read-only ACM/Route53 inventory and an authorized
  refreshing plan; mocks do not substitute for this evidence.

## Expected file scope

- `infra/terraform/load_balancer.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf` if certificate output semantics change
- `infra/terraform/tests/package_c.tftest.hcl`
- `scripts/generate_pilot_deploy_policy.py`
- `infra/aws-iam/pilot-policy-matrix.json`
- `backend/tests/test_pilot_package_c.py`
- Package C builder/review artifacts

No Package A sealed authority, T081 Slice 4B, 0030 artifact, application model,
or public API contract is in scope.

## Known uncertainty

The AWS provider data source's exact selection and exposed metadata must be
confirmed from the installed provider schema during implementation. Real AWS
certificate inventory remains unavailable to the current deploy principal and
is a Package E prerequisite. If exact read-only verification cannot be
expressed, the amendment returns to design review rather than granting
mutation authority.

## Model routing

- Coordinator: `/root`; actual model and effort are not exposed by runtime.
- Amendment designer: `/root`; actual model and effort are not exposed by
  runtime.
- Required independent reviewer: `/root/t082_pilot_design_adversary`, requested
  GPT-6 Astra xhigh.
- Trigger: ambiguous IAM/resource-ownership design discovered after a repeated
  high-risk implementation finding.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/findings.json`

size=998; sha256=cfd1abdfe8d2f39a050ac49ecad2c8b2a138069fb59f7910bfa793434b0a5eff

```text
[
  {
    "id": "T082-C-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Final closure artifacts enumerate every meaningful phase, role, identity, requested route, and actual model and effort or runtime non-disclosure.",
    "summary": "The closure reports omitted a complete mandatory model-assignment summary.",
    "evidence": ["../T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md", ".ai/MODEL_ROUTING.md", "closure.md", "../T082-AWS-INVITE-PILOT-C/closure.md"],
    "impact": "The high-risk amendment cannot close without auditable model-routing evidence.",
    "requiredClosure": "Add complete Model assignments sections to both closure reports, preserving historical artifacts, and obtain documentation/integrity re-attestation.",
    "closureEvidence": ["closure.md", "../T082-AWS-INVITE-PILOT-C/closure.md", "../T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md"]
  }
]

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md`

size=3803; sha256=43f945cba5a3ee21de96ea36100d3fae190c91ea4ed335e96da75a1a31deb7f2

```text
# Closure report: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

## Outcome

The ACM amendment is locally complete and independently implementation-
reviewed. Package C now consumes one operator-provisioned certificate through a
read-only, plan-time identity gate and grants no certificate mutation authority.
This closure does not authorize provisioning, planning, or applying in AWS.

## Invariants verified

- The deploy role has exactly four ACM read actions and no create, tag, untag,
  delete, export, or wildcard ACM authority.
- Lookup is pinned to provider 5.100.0 and filters the exact primary hostname,
  ISSUED status, AMAZON_ISSUED type, RSA_2048 key, and `Project=paprnav`, with
  ambiguity rejection.
- Blocking checks bind returned ARN, hostname, status, ownership tag, account,
  and region before the HTTPS listener can consume the certificate.
- Terraform does not manage a certificate, certificate validation, or DNS
  validation records; the application alias remains.
- Backend state and retained renewal records must be checked before execution.

## Findings disposition summary

The amendment design review produced no blocker or high finding. The parent
C-012 certificate-ownership finding is closed by the independently reviewed
implementation. The child ledger contains no open, accepted-risk, or deferred
finding.

## Verification performed

- Independent design review passed against pinned provider source and AWS
  authorization semantics.
- Provider offline schema confirmed required filters and returned fields.
- Terraform validation passed; twelve retained mocked plan runs passed.
- Focused structural/IAM tests passed and `git diff --check` passed.
- Independent combined implementation review passed, followed by current scoped
  packet and product-hash attestation.

## Final scope reviewed

Terraform provider/input/data/gate/listener/output and retained mock tests,
generated IAM policy and matrix, focused Package C structural tests, the parent
certificate consumers, and amendment decision/implementation evidence.

## Accepted risks and deferred work

None. Real inventory and execution evidence below are mandatory Package E
gates, not waived defects.

## Not verified

- Operator identity, real certificate ARN/metadata/tag, DNS validation records,
  and renewal behavior.
- Real backend state absence for removed ACM and validation resource addresses.
- Real zero/multiple-match lookup behavior and authorized refreshing plan.
- Cloud mutation or HTTPS listener activation.

## Model assignments

| Phase | Role and identity | Requested route | Actual runtime metadata |
| --- | --- | --- | --- |
| Amendment coordination and design | Coordinator/designer `/root` | High-risk IAM amendment; no exposed override | model not exposed by runtime; effort not exposed |
| Amendment design review | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| Amendment implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Combined parent/child implementation review and integrity attestations | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra high or stronger | model not exposed by runtime; effort not exposed |
| Initial closure review and documentation re-attestation | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |

The parent remediation builders were `/root/t082_package_c_remediation_1`
(requested GPT-5.6 Sol xhigh) and `/root/t082_package_c_remediation_2`
(requested GPT-6 Astra xhigh); both report `model not exposed by runtime` and
`effort not exposed`. Builder/reviewer separation was preserved.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md`

size=6004; sha256=be294c079ae5cdebfcc5afa59939c30a0ce8026c9a57da027718a5166643340e

```text
# Closure report: T082-AWS-INVITE-PILOT-C

## Outcome

Package C's local implementation is complete and independently implementation-
reviewed for the AWS invite-pilot boundary. It supplies deterministic and
authority-verified release contexts, sealed database bootstrap, three non-root
images, HTTPS/ALB/WAF/ECS/RDS Terraform with services fixed at zero, read-only
operator-provisioned certificate consumption, and least-privilege prerequisite
IAM. This closure does not authorize AWS mutation or claim deployed evidence.

## Invariants verified

- Release contexts fail closed on candidate/protected-authority drift and keep
  reviewed inputs distinct from explicitly preserved exclusions.
- API, frontend, and bootstrap images are digest-ready, non-root, and exclude
  the reviewed forbidden content; the bootstrap image contains no app checkout.
- Database bootstrap is idempotent, serializes permanent first-admin creation,
  survives bounded rollback points, publishes the app secret without reading
  it back, and grants only the exact runtime inventory.
- Terraform invalid inputs, zone/certificate identity, and image-repository
  mismatches block execution rather than warn.
- WAF classification covers encoded/redirect authentication routes, preserves
  the exact raw upload exception, and disables request sampling.
- The deploy role cannot create, tag, untag, delete, or export ACM
  certificates. The listener consumes one verified, issued, owned,
  operator-provisioned certificate.
- The production frontend uses patched Next.js 16.2.5; the reviewed standalone
  image contains no 16.1.6 package.
- API/frontend desired counts remain zero and the worker remains disabled until
  separately authorized activation.

## Findings disposition summary

T082-C-001 through T082-C-015 are closed with recorded design,
implementation, remediation, test, image, and amendment evidence. No blocker,
accepted risk, or deferred finding remains in this run.

## Verification performed

- Independent design review passed after two remediation rounds.
- Independent implementation review passed after two coherent remediation
  families and the independently approved ACM amendment.
- Focused retained Python/PostgreSQL evidence passed, including rollback,
  concurrency, permanent-use, secret/config, release-authority, IAM, WAF, and
  generated-structure cases.
- Terraform 1.15.0 with pinned AWS provider 5.100.0 validated; retained mocked
  plan gates passed, including the final twelve-run ACM family.
- API, frontend, and bootstrap images built locally as linux/amd64 non-root
  images; the patched frontend standalone image passed bounded smoke checks.
- Final scoped packets were current with unchanged product hashes; the parent
  and ACM child implementation PASS attestations are recorded.

## Final scope reviewed

`.ai/pilot-package-c-context-v1.json`, Package C release/IAM generators,
bootstrap image/program/manifests, API/frontend Docker inputs, focused Package C
tests, Terraform network/database/ECS/ALB/WAF/DNS/certificate-read inputs and
mock tests, frontend dependency lock, and the ACM amendment decision,
implementation, consumers, and review history. Preserved T081, 0030, Package B,
and unrelated application changes were excluded but inventoried.

## Accepted risks and deferred work

None in the Package C finding ledger. Remaining work below is an execution gate
owned by Package E, not an accepted implementation defect.

## Not verified

- Real hostname/zone/certificate/KMS/budget-recipient/updater inputs.
- Real backend state absence for removed certificate resource addresses.
- Live ACM/Route53/IAM inventory, Access Analyzer/policy simulation, and an
  authorized refreshing Terraform plan.
- Candidate commit and pushed ECR digests.
- AWS secret writes, migration/bootstrap execution, service activation, TLS,
  WAF, browser, database, observability, cost, and rollback proof.
- Remaining npm audit entries beyond the independently dispositioned production
  paths; their conditional exclusions must be revisited if features change.

## Model assignments

| Phase | Role and identity | Requested route | Actual runtime metadata |
| --- | --- | --- | --- |
| Coordination and initial design | Coordinator/designer `/root` | Repository risk policy; no override recorded | model not exposed by runtime; effort not exposed |
| Design adversary and design remediation closure | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| Initial implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Remediation 1 after first failed implementation review | Builder `/root/t082_package_c_remediation_1` | GPT-5.6 Sol xhigh | model not exposed by runtime; effort not exposed |
| Remediation 2 after repeated finding family | Builder `/root/t082_package_c_remediation_2` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| ACM amendment design | Designer `/root` | High-risk IAM amendment; no exposed override | model not exposed by runtime; effort not exposed |
| ACM amendment design review | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| ACM amendment implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Combined implementation review and integrity attestations | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra high or stronger | model not exposed by runtime; effort not exposed |
| Final closure review and documentation re-attestation | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |

Builder/reviewer separation was preserved for every review boundary. No
user-visible task was created merely to switch models.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md`

size=4173; sha256=b88979d7bd77c7f14edb5fcb2aaa45569897ed3473b57d77e002dfe9f307bad6

```text
# Package C and ACM amendment combined implementation review — PASS

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Parent remediation builder: `/root/t082_package_c_remediation_2`.
- ACM amendment builder: `/root/t082_package_c_implementation`.
- Requested reviewer capability: GPT-6 Astra, high or stronger.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.
- Trigger: complete-family re-review of recurrent WAF/IAM findings and the
  independently approved certificate-ownership amendment.

## Outcomes

- Parent `T082-AWS-INVITE-PILOT-C`: **PASS**.
- Child `T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT`: **PASS**.

No new implementation blocker or high finding remains.

## Finding dispositions

- **C-010 closed.** Both authentication rules apply `URL_DECODE` to URI
  matching and `NONE` to POST matching. Encoded and trailing-slash variants
  are covered; the raw multipart upload exception is unchanged.
- **C-012 closed through the child amendment.** Terraform no longer manages
  certificate creation, validation, or validation records. Generated ACM
  permissions contain exactly the four approved read actions and exclude all
  mutation and `ExportCertificate`.
- **C-014 closed.** The WAF oracle consumes generated Terraform structures and
  rejects the prior misplaced-transform mutation. IAM assertions bind actual
  generated actions, resources, and conditions. Earlier image/bootstrap
  evidence retains its stated limitations.
- **C-015 closed.** Source and lockfile pin Next.js and its lint configuration
  to 16.2.5. Reviewed build inputs and retained production evidence identify
  16.2.5 in the standalone image with the recorded non-root smoke checks.

Independent targeted verification passed: three tests passed with eight
deselected, covering Terraform structure, the generated WAF/mutation oracle,
and ACM policy. `git diff --check` passed. No broad suite or image rebuild was
performed by the reviewer.

## ACM amendment verification

The provider is pinned to 5.100.0. Terraform requires an exact certificate ARN
and performs a plan-time, ambiguity-rejecting lookup for the exact primary
domain, issued Amazon certificate, RSA_2048 key, and `Project=paprnav` tag.
Blocking gates bind returned ARN, domain, status, tag, account, and region.
The HTTPS listener consumes the verified lookup; the application alias remains;
certificate-management and validation-record resources are absent.

Generated ACM IAM is limited to `ListCertificates`, `DescribeCertificate`,
`ListTagsForCertificate`, and `GetCertificate`. The retained tests cover the
negative identity cases; the builder's twelve mock plans passed. Real
zero-match and ambiguity behavior is provided by pinned provider behavior and
remains subject to Package E's read-only real plan.

The handoff requires backend-state preflight before any plan, preservation of
renewal records, and operator/certificate evidence. If a removed resource
address exists in state, execution stops for a separately reviewed handoff.

## Packet integrity

The reviewer verified the explicit non-recursive scopes and confirmed no
product drift from the technical baseline.

- Parent packet SHA-256:
  `14876ad96b665382f6c60dc0abfef31d91881521ae954bb77e99fac7efd4eb18`;
  fingerprint
  `c164144dc793ed72a3d465d24cc2bd56e1a83a385d71339816b68c21ee2a9832`;
  35 product hashes checked.
- Child packet SHA-256 before this immutable report was added:
  `387df082c2a6148bbd5744d4e01c4dc19ca93f16387cb2e386553ced9a3666c1`;
  fingerprint
  `beaaaf9ef79b48d7bb8421ad8392e0721cc0ca105c0bcc852195990dcf6a3bf5`;
  12 product hashes checked. A mechanical child refresh binds the added report
  path without repeating technical review.

## Residual execution gates

Real operator inputs, backend-state inspection, certificate inventory and DNS
validation evidence, final committed candidate, pushed image digests,
refreshing plan, and Package E runtime/database/browser proofs remain required.
The remaining npm audit findings are not declared resolved. No review edit,
staging, commit, live plan, cloud action, broad suite, or image rebuild
occurred.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md`

size=2190; sha256=2449afbc8b37cb0d4631db14b53bd6a0f7f07d6dac44c677adeae00ce86e7c6e

```text
# Package C and ACM amendment closure review — FAIL

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: final infrastructure/IAM/bootstrap closure.

## Outcomes

- Parent Package C: **FAIL — closure documentation only**.
- ACM amendment child: **FAIL — closure documentation only**.

Implementation PASS outcomes remain valid; no source defect or product drift
was found.

## T082-C-CLOSURE-001 — Blocker — Incomplete final model assignments

The parent closure lists requested builder models but omits their explicit
actual/unexposed metadata. Both closure reports lack the mandatory
`## Model assignments` summary covering design, implementation, remediation,
implementation review, and closure review.

Close by adding complete phase and identity assignments to both reports,
distinguishing requested routing from actual metadata with
`model not exposed by runtime` and `effort not exposed`. Include the current
closure reviewer. Preserve immutable historical reports. Only documentation
and packet-integrity re-attestation are required.

## Otherwise verified

- C-001 through C-015 are closed and all closure evidence exists.
- The child ledger had no implementation finding; independent design and
  implementation attestations exist.
- Every recorded review artifact hash matched and builders differ from the
  reviewer.
- No product drift: parent 35 files and child 12 files.
- Git index is empty and HEAD unchanged. No reviewer write, test, rebuild, or
  cloud action occurred.
- Verified and unverified evidence and Package E boundaries are separated.

The parent packet fingerprint was
`63e26f02afec26448d7b3d1e3fd9ba7a51162c6495eb00a32cc59ddc32cf927b`;
the child fingerprint was
`3cae142d9d6ad213d25003b27f29bbf62e140c956c27fb6ca9d1e745d945f8b3`.

Package E still requires backend-state preflight, certificate/operator and
renewal evidence, approved candidate commit, pushed ECR digests, an authorized
refreshing plan, and bootstrap/deployment/TLS/WAF/browser/observability/cost/
rollback proofs before activation.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md`

size=1386; sha256=6cac47d08e19ce92461c10ca62e1406912d72971f0037d7a78f236446c57c83c

```text
# Package C and ACM amendment final closure review — PASS

## Outcomes

- Parent Package C: **FINAL CLOSURE PASS**.
- ACM amendment child: **FINAL CLOSURE PASS**.

T082-C-CLOSURE-001 is closed. Both `## Model assignments` sections cover the
required phases, identities, requested routes, and exact runtime non-disclosure
wording. No implementation finding was reopened.

## Integrity

The reviewed parent packet SHA-256 was
`a9dfc2cb8fac074f2da01126053b3fac9eabdd1f6f81f308c309d8ef6ef0f610`
with fingerprint
`54cd8f688bbbad7eafcec0ad99a51fcb14323df16582e9ad6a5e049e441483ba`.
The reviewed child packet SHA-256 was
`3b3177b643ab86bb4e55f682b57d1804eaddfccac3c269e6f794378da4a27f0c`
with fingerprint
`5235a8c6988da2142177885b72a27a511159fa5d105e5e6ec343f02603c7fc49`.
Declared out-of-scope inventories matched. Parent 35 and child 12 product
hashes were unchanged with zero drift.

No write, test, implementation re-review, staging, commit, or cloud action
occurred during the closure re-attestation. All Package E execution gates remain
required; closure does not authorize AWS activation.

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: final closure re-attestation after remediation of mandatory model-
  assignment evidence.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-2.md`

size=10792; sha256=989ddb4289e971bd4f92c8ee0e60ea3228269d81cec7b1a3b204af9e8325a4dd

```text
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

```

## Changed-file manifest

```json
{
  "taskId": "T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT",
  "stage": "closure",
  "generatedAt": "2026-09-19T19:48:48+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    "backend/tests/test_pilot_package_c.py",
    "infra/aws-iam/pilot-policy-matrix.json",
    "infra/terraform",
    "scripts/generate_pilot_deploy_policy.py"
  ],
  "scopeFingerprint": "d46390671b9d4925deedeb49f89ee159a71cba67fe32feaf46db2e18c4ad7a06",
  "files": [
    {
      "path": "backend/tests/test_pilot_package_c.py",
      "status": "??",
      "size": 27366,
      "sha256": "3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124",
      "readStatus": "readable"
    },
    {
      "path": "infra/aws-iam/pilot-policy-matrix.json",
      "status": "??",
      "size": 2898,
      "sha256": "553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/database.tf",
      "status": " M",
      "size": 2023,
      "sha256": "47370debfe1e71b803ddc821afe70819e44c3d2fd572e2b4f69ca54b6aaa6dcd",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/ecs_runtime.tf",
      "status": " M",
      "size": 15832,
      "sha256": "6f0c3e1296ff67269841d421fbf94f404036676a3ef36654f73240d794633891",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/load_balancer.tf",
      "status": " M",
      "size": 9126,
      "sha256": "8ee9a4afc3f5c9330ce77283cb00a89e787ee1cab1c0f85d9a9536344d37a48f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/main.tf",
      "status": " M",
      "size": 8829,
      "sha256": "cfb8cfe8890dafc421d462731bce87405baa3b0ae1c847ab70380c99b5b6f4ea",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/network.tf",
      "status": " M",
      "size": 4837,
      "sha256": "4ef5f37229962dc3b90da425193a74491a7c23afef7c159f038e9ae075f6aa0f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/outputs.tf",
      "status": " M",
      "size": 3405,
      "sha256": "6dd533bde5befa1f9540f537fffcc5f4ec3ee4ce979fb365c9c8a681a91a42d8",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/tests/package_c.tftest.hcl",
      "status": "??",
      "size": 8979,
      "sha256": "571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/variables.tf",
      "status": " M",
      "size": 5754,
      "sha256": "8ab402c401f0d394e0ae715654477c4ef2d914cdcb8614a2af4cc24a6442012f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/versions.tf",
      "status": " M",
      "size": 571,
      "sha256": "eb83c7bbbee497ea0f928408b58d12fe7ac2120d08d41f427c091988ed03a6cf",
      "readStatus": "readable"
    },
    {
      "path": "scripts/generate_pilot_deploy_policy.py",
      "status": "??",
      "size": 7082,
      "sha256": "46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md",
      "status": "review_input",
      "size": 7700,
      "sha256": "5530a6fc969d1133b7c638307ec43aa50861efb2bfd7d720dfd5d83ca0bae7c7",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/findings.json",
      "status": "review_input",
      "size": 998,
      "sha256": "cfd1abdfe8d2f39a050ac49ecad2c8b2a138069fb59f7910bfa793434b0a5eff",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md",
      "status": "review_input",
      "size": 3803,
      "sha256": "43f945cba5a3ee21de96ea36100d3fae190c91ea4ed335e96da75a1a31deb7f2",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md",
      "status": "review_input",
      "size": 6004,
      "sha256": "be294c079ae5cdebfcc5afa59939c30a0ce8026c9a57da027718a5166643340e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md",
      "status": "review_input",
      "size": 4173,
      "sha256": "b88979d7bd77c7f14edb5fcb2aaa45569897ed3473b57d77e002dfe9f307bad6",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md",
      "status": "review_input",
      "size": 2190,
      "sha256": "2449afbc8b37cb0d4631db14b53bd6a0f7f07d6dac44c677adeae00ce86e7c6e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md",
      "status": "review_input",
      "size": 1386,
      "sha256": "6cac47d08e19ce92461c10ca62e1406912d72971f0037d7a78f236446c57c83c",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-2.md",
      "status": "review_input",
      "size": 10792,
      "sha256": "989ddb4289e971bd4f92c8ee0e60ea3228269d81cec7b1a3b204af9e8325a4dd",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": " M"
    },
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "??"
    },
    {
      "path": ".ai/pilot-package-c-context-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/pilot-release-boundary-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-executor.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-schema-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-reference-program-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-calibration-goldens.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-fixtures-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-goldens-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-interpreter.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-mutations-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-schema-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-architecture-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-bootstrap.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-inputs.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-integration-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-5.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-6.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-mapping-reconstruction.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-dag-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-resource-rebinding.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/architecture-oracle-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-integration-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/independent-acceptance-enumerator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-cases-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-oracle-results-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-registry-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_harness.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_kernel.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/normative-acceptance-matrix.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary.tar.gz",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle-v2.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-execution-manifest.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-prerequisite-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-contract-builder.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/risk-adjusted-routing-audit.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/run-trusted-sentinel.sh",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/sql-topology-benchmark.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-harness.sql",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-output.txt",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-design-inheritance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/package-b-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/aws-readonly-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/state.json",
      "status": "??"
    },
    {
      "path": "backend/.env.example",
      "status": " M"
    },
    {
      "path": "backend/Dockerfile",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
      "status": "??"
    },
    {
      "path": "backend/app/main.py",
      "status": " M"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M"
    },
    {
      "path": "backend/app/schemas/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/scripts/revoke_auth_sessions.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/ad_v4_acceptance_persistence_contract.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/invitations.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/session_revocation.py",
      "status": "??"
    },
    {
      "path": "backend/requirements.lock",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": " M"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_invite_tenant_boundary.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.dockerignore",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.env.example",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/Dockerfile",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/next.config.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package-lock.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/tests/pilot-observability.test.mjs",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/Dockerfile",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/bootstrap.py",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/grant-manifest.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/reference-data.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.in",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.lock",
      "status": "??"
    },
    {
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??"
    },
    {
      "path": "scripts/build_pilot_release_context.py",
      "status": "??"
    },
    {
      "path": "scripts/generate-ad-v4-acceptance-persistence.py",
      "status": "??"
    },
    {
      "path": "scripts/verify_pilot_release_boundary.py",
      "status": "??"
    }
  ],
  "outOfScopeReason": "Parent Package C, preserved T081, 0030, Package B, policy, and sibling review metadata are outside the narrow ACM amendment closure boundary; parent review and closure evidence are hash-bound."
}
```

## Diff against base

```diff
diff --git a/infra/terraform/database.tf b/infra/terraform/database.tf
index 4cc2d7a..f3741be 100644
--- a/infra/terraform/database.tf
+++ b/infra/terraform/database.tf
@@ -20,7 +20,7 @@ resource "aws_db_instance" "postgres" {
   storage_type          = "gp3"
 
   db_name                     = "paprnav"
-  username                    = "paprnav_app"
+  username                    = "paprnav_admin"
   manage_master_user_password = true
 
   db_subnet_group_name   = aws_db_subnet_group.main.name
@@ -50,7 +50,14 @@ resource "aws_secretsmanager_secret" "database_url" {
   description = "SQLAlchemy DATABASE_URL for the paprnav pilot API and worker. Populate after RDS creation."
 }
 
-resource "aws_secretsmanager_secret" "session_secret" {
-  name        = "/${var.project}/${var.environment}/session-secret"
-  description = "Application session secret for the paprnav pilot runtime. Populate before starting ECS tasks."
+resource "aws_secretsmanager_secret" "invitation_signing" {
+  name                    = "/${var.project}/${var.environment}/invitation-signing"
+  description             = "Dedicated pilot invitation HMAC secret. Populate only at the Package E gate."
+  recovery_window_in_days = 30
+}
+
+resource "aws_secretsmanager_secret" "first_admin_password" {
+  name                    = "/${var.project}/${var.environment}/first-admin-password"
+  description             = "One-use first administrator password. Populate only at the Package E gate."
+  recovery_window_in_days = 30
 }
diff --git a/infra/terraform/ecs_runtime.tf b/infra/terraform/ecs_runtime.tf
index 03a8b85..7dfc44f 100644
--- a/infra/terraform/ecs_runtime.tf
+++ b/infra/terraform/ecs_runtime.tf
@@ -1,7 +1,6 @@
 data "aws_iam_policy_document" "ecs_task_assume_role" {
   statement {
     actions = ["sts:AssumeRole"]
-
     principals {
       type        = "Service"
       identifiers = ["ecs-tasks.amazonaws.com"]
@@ -9,33 +8,81 @@ data "aws_iam_policy_document" "ecs_task_assume_role" {
   }
 }
 
+locals {
+  execution_role_names = toset(["api", "frontend", "worker", "bootstrap"])
+  app_environment_base = [
+    { name = "PAPRNAV_ENV", value = "pilot" },
+    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
+    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
+    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
+    { name = "PAPRNAV_CORS_ORIGINS", value = "https://${var.pilot_hostname}" },
+    { name = "PAPRNAV_SESSION_COOKIE_SECURE", value = "true" },
+    { name = "PAPRNAV_AD_V4_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_READS_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", value = "false" },
+    { name = "AWS_REGION", value = var.aws_region },
+  ]
+  api_environment = concat(local.app_environment_base, [
+    { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
+  ])
+  worker_environment = concat(local.app_environment_base, [
+    { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
+  ])
+  api_secrets = [
+    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
+    { name = "PAPRNAV_INVITE_SIGNING_SECRET", valueFrom = aws_secretsmanager_secret.invitation_signing.arn },
+  ]
+  worker_secrets = [
+    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
+  ]
+  bootstrap_common_environment = [
+    { name = "PAPRNAV_ENV", value = "pilot" },
+    { name = "PAPRNAV_ADMIN_SECRET_ARN", value = aws_db_instance.postgres.master_user_secret[0].secret_arn },
+    { name = "PAPRNAV_DATABASE_NAME", value = aws_db_instance.postgres.db_name },
+    { name = "AWS_REGION", value = var.aws_region },
+  ]
+}
+
 resource "aws_iam_role" "ecs_execution" {
-  name               = "${local.name_prefix}-ecs-execution-role"
+  for_each           = local.execution_role_names
+  name               = "${local.name_prefix}-${each.key}-execution-role"
   assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
 }
 
 resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
-  role       = aws_iam_role.ecs_execution.name
+  for_each   = local.execution_role_names
+  role       = aws_iam_role.ecs_execution[each.key].name
   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
 }
 
-data "aws_iam_policy_document" "ecs_execution_secrets" {
+data "aws_iam_policy_document" "api_execution_secrets" {
   statement {
-    actions = [
-      "secretsmanager:GetSecretValue",
-    ]
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn, aws_secretsmanager_secret.invitation_signing.arn]
+  }
+}
 
-    resources = [
-      aws_secretsmanager_secret.database_url.arn,
-      aws_secretsmanager_secret.session_secret.arn,
-    ]
+resource "aws_iam_role_policy" "api_execution_secrets" {
+  name   = "${local.name_prefix}-api-execution-secrets"
+  role   = aws_iam_role.ecs_execution["api"].id
+  policy = data.aws_iam_policy_document.api_execution_secrets.json
+}
+
+data "aws_iam_policy_document" "worker_execution_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn]
   }
 }
 
-resource "aws_iam_role_policy" "ecs_execution_secrets" {
-  name   = "${local.name_prefix}-ecs-execution-secrets"
-  role   = aws_iam_role.ecs_execution.id
-  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
+resource "aws_iam_role_policy" "worker_execution_secrets" {
+  name   = "${local.name_prefix}-worker-execution-secrets"
+  role   = aws_iam_role.ecs_execution["worker"].id
+  policy = data.aws_iam_policy_document.worker_execution_secrets.json
 }
 
 resource "aws_iam_role" "api_task" {
@@ -53,29 +100,29 @@ resource "aws_iam_role" "worker_task" {
   assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
 }
 
+resource "aws_iam_role" "migration_reference_task" {
+  name               = "${local.name_prefix}-migration-reference-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
+resource "aws_iam_role" "runtime_role_task" {
+  name               = "${local.name_prefix}-runtime-role-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
+resource "aws_iam_role" "first_admin_task" {
+  name               = "${local.name_prefix}-first-admin-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
 data "aws_iam_policy_document" "api_task" {
   statement {
-    actions = [
-      "s3:GetObject",
-      "s3:PutObject",
-      "s3:DeleteObject",
-      "s3:GetObjectTagging",
-      "s3:PutObjectTagging",
-    ]
-
-    resources = [
-      "${aws_s3_bucket.app_artifacts.arn}/*",
-    ]
+    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
+    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
   }
-
   statement {
-    actions = [
-      "s3:ListBucket",
-    ]
-
-    resources = [
-      aws_s3_bucket.app_artifacts.arn,
-    ]
+    actions   = ["s3:ListBucket"]
+    resources = [aws_s3_bucket.app_artifacts.arn]
   }
 }
 
@@ -87,36 +134,15 @@ resource "aws_iam_role_policy" "api_task" {
 
 data "aws_iam_policy_document" "worker_task" {
   statement {
-    actions = [
-      "s3:GetObject",
-      "s3:PutObject",
-      "s3:DeleteObject",
-      "s3:GetObjectTagging",
-      "s3:PutObjectTagging",
-    ]
-
-    resources = [
-      "${aws_s3_bucket.app_artifacts.arn}/*",
-    ]
+    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
+    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
   }
-
   statement {
-    actions = [
-      "s3:ListBucket",
-    ]
-
-    resources = [
-      aws_s3_bucket.app_artifacts.arn,
-    ]
+    actions   = ["s3:ListBucket"]
+    resources = [aws_s3_bucket.app_artifacts.arn]
   }
-
   statement {
-    actions = [
-      "textract:DetectDocumentText",
-      "textract:StartDocumentTextDetection",
-      "textract:GetDocumentTextDetection",
-    ]
-
+    actions   = ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"]
     resources = ["*"]
   }
 }
@@ -127,33 +153,50 @@ resource "aws_iam_role_policy" "worker_task" {
   policy = data.aws_iam_policy_document.worker_task.json
 }
 
-locals {
-  app_environment_base = [
-    { name = "PAPRNAV_ENV", value = var.environment },
-    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
-    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
-    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
-    { name = "AWS_REGION", value = var.aws_region },
-  ]
+data "aws_iam_policy_document" "migration_reference_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
+  }
+}
 
-  api_environment = concat(
-    local.app_environment_base,
-    [
-      { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
-    ]
-  )
+resource "aws_iam_role_policy" "migration_reference_secrets" {
+  name   = "${local.name_prefix}-migration-reference-secrets"
+  role   = aws_iam_role.migration_reference_task.id
+  policy = data.aws_iam_policy_document.migration_reference_secrets.json
+}
+
+data "aws_iam_policy_document" "runtime_role_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
+  }
+  statement {
+    actions   = ["secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn]
+  }
+}
+
+resource "aws_iam_role_policy" "runtime_role_secrets" {
+  name   = "${local.name_prefix}-runtime-role-secrets"
+  role   = aws_iam_role.runtime_role_task.id
+  policy = data.aws_iam_policy_document.runtime_role_secrets.json
+}
 
-  worker_environment = concat(
-    local.app_environment_base,
-    [
-      { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
+data "aws_iam_policy_document" "first_admin_secrets" {
+  statement {
+    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [
+      aws_db_instance.postgres.master_user_secret[0].secret_arn,
+      aws_secretsmanager_secret.first_admin_password.arn,
     ]
-  )
+  }
+}
 
-  api_secrets = [
-    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
-    { name = "PAPRNAV_SESSION_SECRET", valueFrom = aws_secretsmanager_secret.session_secret.arn },
-  ]
+resource "aws_iam_role_policy" "first_admin_secrets" {
+  name   = "${local.name_prefix}-first-admin-secrets"
+  role   = aws_iam_role.first_admin_task.id
+  policy = data.aws_iam_policy_document.first_admin_secrets.json
 }
 
 resource "aws_ecs_task_definition" "api" {
@@ -162,36 +205,23 @@ resource "aws_ecs_task_definition" "api" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["api"].arn
   task_role_arn            = aws_iam_role.api_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "api"
-      image     = "${aws_ecr_repository.api.repository_url}:latest"
-      essential = true
-
-      portMappings = [
-        {
-          containerPort = var.api_container_port
-          hostPort      = var.api_container_port
-          protocol      = "tcp"
-        }
-      ]
-
-      environment = local.api_environment
-      secrets     = local.api_secrets
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.api.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "api"
-        }
+  container_definitions = jsonencode([{
+    name         = "api"
+    image        = var.api_image
+    essential    = true
+    portMappings = [{ containerPort = var.api_container_port, hostPort = var.api_container_port, protocol = "tcp" }]
+    environment  = local.api_environment
+    secrets      = local.api_secrets
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.api.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "api"
       }
     }
-  ])
+  }])
 }
 
 resource "aws_ecs_task_definition" "frontend" {
@@ -200,38 +230,23 @@ resource "aws_ecs_task_definition" "frontend" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["frontend"].arn
   task_role_arn            = aws_iam_role.frontend_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "frontend"
-      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
-      essential = true
-
-      portMappings = [
-        {
-          containerPort = var.frontend_container_port
-          hostPort      = var.frontend_container_port
-          protocol      = "tcp"
-        }
-      ]
-
-      environment = [
-        { name = "PAPRNAV_ENV", value = var.environment },
-        { name = "PAPRNAV_BACKEND_URL", value = "http://${aws_lb.main.dns_name}" },
-      ]
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.frontend.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "frontend"
-        }
+  container_definitions = jsonencode([{
+    name         = "frontend"
+    image        = var.frontend_image
+    essential    = true
+    portMappings = [{ containerPort = var.frontend_container_port, hostPort = var.frontend_container_port, protocol = "tcp" }]
+    environment  = [{ name = "PAPRNAV_ENV", value = "pilot" }]
+    secrets      = []
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.frontend.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "frontend"
       }
     }
-  ])
+  }])
 }
 
 resource "aws_ecs_task_definition" "worker" {
@@ -240,79 +255,125 @@ resource "aws_ecs_task_definition" "worker" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["worker"].arn
   task_role_arn            = aws_iam_role.worker_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "worker"
-      image     = "${aws_ecr_repository.api.repository_url}:latest"
-      essential = true
-      command   = ["python", "-m", "app.workers.ocr"]
-
-      environment = local.worker_environment
-      secrets     = local.api_secrets
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.worker.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "worker"
-        }
+  container_definitions = jsonencode([{
+    name        = "worker", image = var.api_image, essential = true, command = ["python", "-m", "app.workers.ocr"]
+    environment = local.worker_environment
+    secrets     = local.worker_secrets
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.worker.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "worker"
       }
     }
-  ])
+  }])
+}
+
+locals {
+  bootstrap_tasks = {
+    migration = {
+      command     = ["migration"]
+      role        = aws_iam_role.migration_reference_task.arn
+      environment = local.bootstrap_common_environment
+    }
+    reference = {
+      command     = ["reference"]
+      role        = aws_iam_role.migration_reference_task.arn
+      environment = local.bootstrap_common_environment
+    }
+    runtime-role = {
+      command = ["runtime-role"]
+      role    = aws_iam_role.runtime_role_task.arn
+      environment = concat(local.bootstrap_common_environment, [
+        { name = "PAPRNAV_APP_DATABASE_SECRET_ARN", value = aws_secretsmanager_secret.database_url.arn },
+      ])
+    }
+    first-admin = {
+      command = ["first-admin"]
+      role    = aws_iam_role.first_admin_task.arn
+      environment = concat(local.bootstrap_common_environment, [
+        { name = "PAPRNAV_FIRST_ADMIN_SECRET_ARN", value = aws_secretsmanager_secret.first_admin_password.arn },
+        { name = "PAPRNAV_FIRST_ADMIN_EMAIL", value = var.first_admin_email },
+        { name = "PAPRNAV_FIRST_ADMIN_NAME", value = var.first_admin_name },
+        { name = "PAPRNAV_FIRST_ADMIN_ORGANIZATION", value = var.first_admin_organization },
+      ])
+    }
+  }
+}
+
+resource "aws_ecs_task_definition" "bootstrap" {
+  for_each                 = local.bootstrap_tasks
+  family                   = "${local.name_prefix}-bootstrap-${each.key}"
+  requires_compatibilities = ["FARGATE"]
+  network_mode             = "awsvpc"
+  cpu                      = var.ecs_task_cpu
+  memory                   = var.ecs_task_memory
+  execution_role_arn       = aws_iam_role.ecs_execution["bootstrap"].arn
+  task_role_arn            = each.value.role
+
+  container_definitions = jsonencode([{
+    name                   = "bootstrap"
+    image                  = var.bootstrap_image
+    essential              = true
+    command                = each.value.command
+    environment            = each.value.environment
+    secrets                = []
+    readonlyRootFilesystem = true
+    linuxParameters        = { initProcessEnabled = true }
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.bootstrap.name, awslogs-region = var.aws_region, awslogs-stream-prefix = each.key
+      }
+    }
+  }])
 }
 
 resource "aws_ecs_service" "api" {
   name            = "${local.name_prefix}-api"
   cluster         = aws_ecs_cluster.main.id
   task_definition = aws_ecs_task_definition.api.arn
-  desired_count   = var.api_desired_count
+  desired_count   = 0
   launch_type     = "FARGATE"
 
   network_configuration {
     subnets          = aws_subnet.public[*].id
-    security_groups  = [aws_security_group.ecs_tasks.id]
+    security_groups  = [aws_security_group.api.id]
     assign_public_ip = true
   }
-
   load_balancer {
     target_group_arn = aws_lb_target_group.api.arn
     container_name   = "api"
     container_port   = var.api_container_port
   }
-
-  depends_on = [aws_lb_listener.http]
+  depends_on = [aws_lb_listener.https]
 }
 
 resource "aws_ecs_service" "frontend" {
   name            = "${local.name_prefix}-frontend"
   cluster         = aws_ecs_cluster.main.id
   task_definition = aws_ecs_task_definition.frontend.arn
-  desired_count   = var.frontend_desired_count
+  desired_count   = 0
   launch_type     = "FARGATE"
 
   network_configuration {
     subnets          = aws_subnet.public[*].id
-    security_groups  = [aws_security_group.ecs_tasks.id]
+    security_groups  = [aws_security_group.frontend.id]
     assign_public_ip = true
   }
-
   load_balancer {
     target_group_arn = aws_lb_target_group.frontend.arn
     container_name   = "frontend"
     container_port   = var.frontend_container_port
   }
-
-  depends_on = [aws_lb_listener.http]
+  depends_on = [aws_lb_listener.https]
 }
 
 data "aws_iam_policy_document" "scheduler_assume_role" {
   statement {
     actions = ["sts:AssumeRole"]
-
     principals {
       type        = "Service"
       identifiers = ["scheduler.amazonaws.com"]
@@ -327,27 +388,17 @@ resource "aws_iam_role" "worker_scheduler" {
 
 data "aws_iam_policy_document" "worker_scheduler" {
   statement {
-    actions = ["ecs:RunTask"]
-
-    resources = [
-      aws_ecs_task_definition.worker.arn,
-    ]
-
+    actions   = ["ecs:RunTask"]
+    resources = [aws_ecs_task_definition.worker.arn]
     condition {
       test     = "ArnEquals"
       variable = "ecs:cluster"
       values   = [aws_ecs_cluster.main.arn]
     }
   }
-
   statement {
-    actions = ["iam:PassRole"]
-
-    resources = [
-      aws_iam_role.ecs_execution.arn,
-      aws_iam_role.worker_task.arn,
-    ]
-
+    actions   = ["iam:PassRole"]
+    resources = [aws_iam_role.ecs_execution["worker"].arn, aws_iam_role.worker_task.arn]
     condition {
       test     = "StringEquals"
       variable = "iam:PassedToService"
@@ -363,27 +414,21 @@ resource "aws_iam_role_policy" "worker_scheduler" {
 }
 
 resource "aws_scheduler_schedule" "worker" {
-  name       = "${local.name_prefix}-worker"
-  group_name = "default"
-  state      = var.worker_schedule_state
-
-  flexible_time_window {
-    mode = "OFF"
-  }
-
-  schedule_expression = var.worker_schedule_expression
+  name                = "${local.name_prefix}-worker"
+  group_name          = "default"
+  state               = "DISABLED"
+  schedule_expression = "rate(15 minutes)"
+  flexible_time_window { mode = "OFF" }
 
   target {
     arn      = aws_ecs_cluster.main.arn
     role_arn = aws_iam_role.worker_scheduler.arn
-
     ecs_parameters {
       launch_type         = "FARGATE"
       task_definition_arn = aws_ecs_task_definition.worker.arn
-
       network_configuration {
         subnets          = aws_subnet.public[*].id
-        security_groups  = [aws_security_group.ecs_tasks.id]
+        security_groups  = [aws_security_group.worker.id]
         assign_public_ip = true
       }
     }
diff --git a/infra/terraform/load_balancer.tf b/infra/terraform/load_balancer.tf
index 29baae0..6ccad49 100644
--- a/infra/terraform/load_balancer.tf
+++ b/infra/terraform/load_balancer.tf
@@ -4,9 +4,18 @@ resource "aws_lb" "main" {
   internal           = false
   security_groups    = [aws_security_group.alb.id]
   subnets            = aws_subnet.public[*].id
+  tags               = { Name = local.name_prefix }
+}
+
+resource "aws_route53_record" "pilot" {
+  zone_id = data.aws_route53_zone.pilot.zone_id
+  name    = var.pilot_hostname
+  type    = "A"
 
-  tags = {
-    Name = local.name_prefix
+  alias {
+    name                   = aws_lb.main.dns_name
+    zone_id                = aws_lb.main.zone_id
+    evaluate_target_health = true
   }
 }
 
@@ -27,10 +36,7 @@ resource "aws_lb_target_group" "frontend" {
     timeout             = 5
     unhealthy_threshold = 3
   }
-
-  tags = {
-    Name = "${local.name_prefix}-frontend"
-  }
+  tags = { Name = "${local.name_prefix}-frontend" }
 }
 
 resource "aws_lb_target_group" "api" {
@@ -50,10 +56,7 @@ resource "aws_lb_target_group" "api" {
     timeout             = 5
     unhealthy_threshold = 3
   }
-
-  tags = {
-    Name = "${local.name_prefix}-api"
-  }
+  tags = { Name = "${local.name_prefix}-api" }
 }
 
 resource "aws_lb_listener" "http" {
@@ -61,24 +64,284 @@ resource "aws_lb_listener" "http" {
   port              = 80
   protocol          = "HTTP"
 
+  default_action {
+    type = "redirect"
+    redirect {
+      port        = "443"
+      protocol    = "HTTPS"
+      status_code = "HTTP_301"
+    }
+  }
+}
+
+resource "aws_lb_listener" "https" {
+  load_balancer_arn = aws_lb.main.arn
+  port              = 443
+  protocol          = "HTTPS"
+  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
+  certificate_arn   = data.aws_acm_certificate.pilot.arn
+
   default_action {
     type             = "forward"
     target_group_arn = aws_lb_target_group.frontend.arn
   }
+
+  depends_on = [terraform_data.certificate_input_gate]
 }
 
 resource "aws_lb_listener_rule" "api" {
-  listener_arn = aws_lb_listener.http.arn
+  listener_arn = aws_lb_listener.https.arn
   priority     = 100
 
   action {
     type             = "forward"
     target_group_arn = aws_lb_target_group.api.arn
   }
-
   condition {
     path_pattern {
       values = ["/api/v1/*", "/health", "/version"]
     }
   }
 }
+
+resource "aws_wafv2_regex_pattern_set" "upload_path" {
+  name  = "${local.name_prefix}-upload-path"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/aircraft/[^/]+/uploads$"
+  }
+}
+
+resource "aws_wafv2_regex_pattern_set" "invitation_paths" {
+  name  = "${local.name_prefix}-invitation-paths"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/auth/invitations(?:/accept)?/?$"
+  }
+}
+
+resource "aws_wafv2_regex_pattern_set" "login_path" {
+  name  = "${local.name_prefix}-login-path"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/auth/login/?$"
+  }
+}
+
+resource "aws_wafv2_web_acl" "pilot" {
+  name  = "${local.name_prefix}-web-acl"
+  scope = "REGIONAL"
+
+  default_action {
+    allow {}
+  }
+
+  rule {
+    name     = "aws-managed-common"
+    priority = 10
+    override_action {
+      none {}
+    }
+    statement {
+      managed_rule_group_statement {
+        name        = "AWSManagedRulesCommonRuleSet"
+        vendor_name = "AWS"
+        rule_action_override {
+          name = "SizeRestrictions_BODY"
+          action_to_use {
+            count {}
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-managed-common"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "block-oversize-body-except-reviewed-upload"
+    priority = 20
+    action {
+      block {}
+    }
+    statement {
+      and_statement {
+        statement {
+          size_constraint_statement {
+            comparison_operator = "GT"
+            size                = 8192
+            field_to_match {
+              body { oversize_handling = "MATCH" }
+            }
+            text_transformation {
+              priority = 0
+              type     = "NONE"
+            }
+          }
+        }
+        statement {
+          not_statement {
+            statement {
+              and_statement {
+                statement {
+                  byte_match_statement {
+                    positional_constraint = "EXACTLY"
+                    search_string         = "POST"
+                    field_to_match {
+                      method {}
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "NONE"
+                    }
+                  }
+                }
+                statement {
+                  regex_pattern_set_reference_statement {
+                    arn = aws_wafv2_regex_pattern_set.upload_path.arn
+                    field_to_match {
+                      uri_path {}
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "NONE"
+                    }
+                  }
+                }
+                statement {
+                  byte_match_statement {
+                    positional_constraint = "STARTS_WITH"
+                    search_string         = "multipart/form-data"
+                    field_to_match {
+                      single_header { name = "content-type" }
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "LOWERCASE"
+                    }
+                  }
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-oversize-body"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "login-rate-limit"
+    priority = 30
+    action {
+      block {}
+    }
+    statement {
+      rate_based_statement {
+        aggregate_key_type = "IP"
+        limit              = var.login_rate_limit
+        scope_down_statement {
+          and_statement {
+            statement {
+              byte_match_statement {
+                positional_constraint = "EXACTLY"
+                search_string         = "POST"
+                field_to_match {
+                  method {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "NONE"
+                }
+              }
+            }
+            statement {
+              regex_pattern_set_reference_statement {
+                arn = aws_wafv2_regex_pattern_set.login_path.arn
+                field_to_match {
+                  uri_path {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "URL_DECODE"
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-login-rate"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "invitation-rate-limit"
+    priority = 40
+    action {
+      block {}
+    }
+    statement {
+      rate_based_statement {
+        aggregate_key_type = "IP"
+        limit              = var.invitation_rate_limit
+        scope_down_statement {
+          and_statement {
+            statement {
+              byte_match_statement {
+                positional_constraint = "EXACTLY"
+                search_string         = "POST"
+                field_to_match {
+                  method {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "NONE"
+                }
+              }
+            }
+            statement {
+              regex_pattern_set_reference_statement {
+                arn = aws_wafv2_regex_pattern_set.invitation_paths.arn
+                field_to_match {
+                  uri_path {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "URL_DECODE"
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-invitation-rate"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  visibility_config {
+    cloudwatch_metrics_enabled = true
+    metric_name                = "${local.name_prefix}-waf"
+    sampled_requests_enabled   = false
+  }
+  tags = { Name = "${local.name_prefix}-web-acl" }
+}
+
+resource "aws_wafv2_web_acl_association" "pilot" {
+  resource_arn = aws_lb.main.arn
+  web_acl_arn  = aws_wafv2_web_acl.pilot.arn
+}
diff --git a/infra/terraform/main.tf b/infra/terraform/main.tf
index e2cec01..867307e 100644
--- a/infra/terraform/main.tf
+++ b/infra/terraform/main.tf
@@ -1,6 +1,10 @@
 locals {
   name_prefix = "${var.project}-${var.environment}"
 
+  expected_api_image_prefix       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-api@sha256:"
+  expected_frontend_image_prefix  = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-frontend@sha256:"
+  expected_bootstrap_image_prefix = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-bootstrap@sha256:"
+
   common_tags = {
     Project     = var.project
     Environment = var.environment
@@ -12,6 +16,100 @@ locals {
   }
 }
 
+data "aws_route53_zone" "pilot" {
+  zone_id      = var.route53_zone_id
+  private_zone = false
+}
+
+data "aws_acm_certificate" "pilot" {
+  domain      = var.pilot_hostname
+  statuses    = ["ISSUED"]
+  types       = ["AMAZON_ISSUED"]
+  key_types   = ["RSA_2048"]
+  tags        = { Project = "paprnav" }
+  most_recent = false
+}
+
+resource "terraform_data" "certificate_input_gate" {
+  input = {
+    requested_arn = var.pilot_certificate_arn
+    resolved_arn  = data.aws_acm_certificate.pilot.arn
+    domain        = data.aws_acm_certificate.pilot.domain
+    status        = data.aws_acm_certificate.pilot.status
+    project_tag   = lookup(data.aws_acm_certificate.pilot.tags, "Project", "")
+  }
+
+  lifecycle {
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn
+      error_message = "The resolved ACM certificate ARN must equal pilot_certificate_arn."
+    }
+
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.domain == var.pilot_hostname
+      error_message = "The resolved ACM certificate primary domain must equal pilot_hostname."
+    }
+
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.status == "ISSUED"
+      error_message = "The resolved ACM certificate must be ISSUED."
+    }
+
+    precondition {
+      condition     = lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
+      error_message = "The resolved ACM certificate must carry Project=paprnav."
+    }
+
+    precondition {
+      condition = startswith(
+        data.aws_acm_certificate.pilot.arn,
+        "arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"
+      )
+      error_message = "The resolved ACM certificate ARN must belong to the configured AWS account and region."
+    }
+  }
+}
+
+resource "terraform_data" "deployment_input_gate" {
+  input = {
+    hosted_zone_id   = data.aws_route53_zone.pilot.zone_id
+    hosted_zone_name = data.aws_route53_zone.pilot.name
+    pilot_hostname   = var.pilot_hostname
+  }
+
+  lifecycle {
+    precondition {
+      condition = (
+        startswith(var.api_image, local.expected_api_image_prefix) &&
+        startswith(var.frontend_image, local.expected_frontend_image_prefix) &&
+        startswith(var.bootstrap_image, local.expected_bootstrap_image_prefix)
+      )
+      error_message = "All image digests must reference the exact pilot ECR repository for their task family."
+    }
+
+    precondition {
+      condition = !var.external_mode || (
+        !endswith(var.pilot_hostname, ".invalid") &&
+        can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.budget_notification_email)) &&
+        !endswith(var.budget_notification_email, ".invalid") &&
+        can(regex("^arn:aws:iam::[0-9]{12}:(user|role)/.+$", var.policy_updater_principal_arn))
+      )
+      error_message = "External mode requires a real hostname, budget recipient, and explicit IAM policy-updater principal."
+    }
+
+    precondition {
+      condition = (
+        lower(trimsuffix(data.aws_route53_zone.pilot.name, ".")) == lower(trimsuffix(var.route53_zone_name, ".")) &&
+        (
+          var.pilot_hostname == lower(trimsuffix(data.aws_route53_zone.pilot.name, ".")) ||
+          endswith(var.pilot_hostname, ".${lower(trimsuffix(data.aws_route53_zone.pilot.name, "."))}")
+        )
+      )
+      error_message = "The actual Route53 hosted-zone identity must match route53_zone_name and contain pilot_hostname."
+    }
+  }
+}
+
 resource "aws_s3_bucket" "app_artifacts" {
   bucket        = "${local.name_prefix}-artifacts-${var.aws_account_id}"
   force_destroy = var.force_destroy_buckets
@@ -112,7 +210,7 @@ resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state"
 
 resource "aws_ecr_repository" "api" {
   name                 = "${var.project}/${var.environment}-api"
-  image_tag_mutability = "MUTABLE"
+  image_tag_mutability = "IMMUTABLE"
 
   image_scanning_configuration {
     scan_on_push = true
@@ -121,7 +219,16 @@ resource "aws_ecr_repository" "api" {
 
 resource "aws_ecr_repository" "frontend" {
   name                 = "${var.project}/${var.environment}-frontend"
-  image_tag_mutability = "MUTABLE"
+  image_tag_mutability = "IMMUTABLE"
+
+  image_scanning_configuration {
+    scan_on_push = true
+  }
+}
+
+resource "aws_ecr_repository" "bootstrap" {
+  name                 = "${var.project}/${var.environment}-bootstrap"
+  image_tag_mutability = "IMMUTABLE"
 
   image_scanning_configuration {
     scan_on_push = true
@@ -143,6 +250,11 @@ resource "aws_cloudwatch_log_group" "worker" {
   retention_in_days = var.log_retention_days
 }
 
+resource "aws_cloudwatch_log_group" "bootstrap" {
+  name              = "/paprnav/${var.environment}/bootstrap"
+  retention_in_days = var.log_retention_days
+}
+
 resource "aws_ecs_cluster" "main" {
   name = local.name_prefix
 
@@ -166,39 +278,27 @@ resource "aws_budgets_budget" "monthly_pilot" {
     ]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 50
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "ACTUAL"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 50
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "ACTUAL"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 80
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "ACTUAL"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 80
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "ACTUAL"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 100
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "FORECASTED"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 100
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "FORECASTED"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 }
diff --git a/infra/terraform/network.tf b/infra/terraform/network.tf
index 7ae4938..e4d8909 100644
--- a/infra/terraform/network.tf
+++ b/infra/terraform/network.tf
@@ -7,17 +7,12 @@ resource "aws_vpc" "main" {
   enable_dns_hostnames = true
   enable_dns_support   = true
 
-  tags = {
-    Name = local.name_prefix
-  }
+  tags = { Name = local.name_prefix }
 }
 
 resource "aws_internet_gateway" "main" {
   vpc_id = aws_vpc.main.id
-
-  tags = {
-    Name = "${local.name_prefix}-igw"
-  }
+  tags   = { Name = "${local.name_prefix}-igw" }
 }
 
 resource "aws_subnet" "public" {
@@ -27,7 +22,6 @@ resource "aws_subnet" "public" {
   cidr_block              = var.public_subnet_cidrs[count.index]
   availability_zone       = data.aws_availability_zones.available.names[count.index]
   map_public_ip_on_launch = true
-
   tags = {
     Name = "${local.name_prefix}-public-${count.index + 1}"
     Tier = "public"
@@ -40,7 +34,6 @@ resource "aws_subnet" "private" {
   vpc_id            = aws_vpc.main.id
   cidr_block        = var.private_subnet_cidrs[count.index]
   availability_zone = data.aws_availability_zones.available.names[count.index]
-
   tags = {
     Name = "${local.name_prefix}-private-${count.index + 1}"
     Tier = "private"
@@ -49,53 +42,73 @@ resource "aws_subnet" "private" {
 
 resource "aws_route_table" "public" {
   vpc_id = aws_vpc.main.id
-
   route {
     cidr_block = "0.0.0.0/0"
     gateway_id = aws_internet_gateway.main.id
   }
-
-  tags = {
-    Name = "${local.name_prefix}-public"
-  }
+  tags = { Name = "${local.name_prefix}-public" }
 }
 
 resource "aws_route_table_association" "public" {
-  count = length(aws_subnet.public)
-
+  count          = length(aws_subnet.public)
   subnet_id      = aws_subnet.public[count.index].id
   route_table_id = aws_route_table.public.id
 }
 
 resource "aws_security_group" "alb" {
   name        = "${local.name_prefix}-alb"
-  description = "Allow public HTTP access to the pilot ALB."
+  description = "Public HTTPS entry point; HTTP exists only for redirect."
   vpc_id      = aws_vpc.main.id
 
   ingress {
-    description = "HTTP from internet"
+    description = "HTTP redirect from internet"
     from_port   = 80
     to_port     = 80
     protocol    = "tcp"
     cidr_blocks = ["0.0.0.0/0"]
   }
-
+  ingress {
+    description = "HTTPS from internet"
+    from_port   = 443
+    to_port     = 443
+    protocol    = "tcp"
+    cidr_blocks = ["0.0.0.0/0"]
+  }
   egress {
-    description = "ALB to ECS targets"
+    description = "ALB to named API/frontend groups"
     from_port   = 0
     to_port     = 0
     protocol    = "-1"
     cidr_blocks = [var.vpc_cidr]
   }
+  tags = { Name = "${local.name_prefix}-alb" }
+}
 
-  tags = {
-    Name = "${local.name_prefix}-alb"
+resource "aws_security_group" "api" {
+  name        = "${local.name_prefix}-api"
+  description = "API ingress only from the ALB."
+  vpc_id      = aws_vpc.main.id
+
+  ingress {
+    description     = "API from ALB"
+    from_port       = var.api_container_port
+    to_port         = var.api_container_port
+    protocol        = "tcp"
+    security_groups = [aws_security_group.alb.id]
+  }
+  egress {
+    description = "Pilot public-task outbound compromise"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-api" }
 }
 
-resource "aws_security_group" "ecs_tasks" {
-  name        = "${local.name_prefix}-ecs-tasks"
-  description = "Allow ALB access to ECS tasks."
+resource "aws_security_group" "frontend" {
+  name        = "${local.name_prefix}-frontend"
+  description = "Frontend ingress only from the ALB; no database ingress grant."
   vpc_id      = aws_vpc.main.id
 
   ingress {
@@ -105,42 +118,61 @@ resource "aws_security_group" "ecs_tasks" {
     protocol        = "tcp"
     security_groups = [aws_security_group.alb.id]
   }
-
-  ingress {
-    description     = "API from ALB"
-    from_port       = var.api_container_port
-    to_port         = var.api_container_port
-    protocol        = "tcp"
-    security_groups = [aws_security_group.alb.id]
+  egress {
+    description = "Pilot public-task outbound compromise"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-frontend" }
+}
+
+resource "aws_security_group" "worker" {
+  name        = "${local.name_prefix}-worker"
+  description = "Non-listening worker tasks."
+  vpc_id      = aws_vpc.main.id
 
   egress {
-    description = "Outbound for AWS APIs and package/runtime access"
+    description = "Pilot public-task outbound compromise"
     from_port   = 0
     to_port     = 0
     protocol    = "-1"
     cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-worker" }
+}
 
-  tags = {
-    Name = "${local.name_prefix}-ecs-tasks"
+resource "aws_security_group" "bootstrap" {
+  name        = "${local.name_prefix}-bootstrap"
+  description = "Non-listening one-off migration/bootstrap tasks."
+  vpc_id      = aws_vpc.main.id
+
+  egress {
+    description = "Secrets Manager, ECR, logs, and RDS access"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-bootstrap" }
 }
 
 resource "aws_security_group" "rds" {
   name        = "${local.name_prefix}-rds"
-  description = "Allow PostgreSQL from ECS tasks."
+  description = "PostgreSQL from API, disabled worker, and one-off bootstrap tasks only."
   vpc_id      = aws_vpc.main.id
 
   ingress {
-    description     = "PostgreSQL from ECS tasks"
-    from_port       = 5432
-    to_port         = 5432
-    protocol        = "tcp"
-    security_groups = [aws_security_group.ecs_tasks.id]
-  }
-
-  tags = {
-    Name = "${local.name_prefix}-rds"
+    description = "PostgreSQL from API runtime"
+    from_port   = 5432
+    to_port     = 5432
+    protocol    = "tcp"
+    security_groups = [
+      aws_security_group.api.id,
+      aws_security_group.worker.id,
+      aws_security_group.bootstrap.id,
+    ]
   }
+  tags = { Name = "${local.name_prefix}-rds" }
 }
diff --git a/infra/terraform/outputs.tf b/infra/terraform/outputs.tf
index c81a15e..eeebcad 100644
--- a/infra/terraform/outputs.tf
+++ b/infra/terraform/outputs.tf
@@ -18,6 +18,11 @@ output "frontend_ecr_repository_url" {
   value       = aws_ecr_repository.frontend.repository_url
 }
 
+output "bootstrap_ecr_repository_url" {
+  description = "ECR repository URL for the sealed migration/bootstrap image."
+  value       = aws_ecr_repository.bootstrap.repository_url
+}
+
 output "ecs_cluster_name" {
   description = "ECS cluster name for paprnav pilot services."
   value       = aws_ecs_cluster.main.name
@@ -29,10 +34,20 @@ output "vpc_id" {
 }
 
 output "alb_dns_name" {
-  description = "Public ALB DNS name for the HTTP pilot runtime skeleton."
+  description = "Public ALB DNS name behind the canonical HTTPS pilot record."
   value       = aws_lb.main.dns_name
 }
 
+output "pilot_https_url" {
+  description = "Canonical HTTPS URL."
+  value       = "https://${var.pilot_hostname}"
+}
+
+output "pilot_certificate_arn" {
+  description = "Verified operator-provisioned ACM certificate attached to the HTTPS listener."
+  value       = data.aws_acm_certificate.pilot.arn
+}
+
 output "api_service_name" {
   description = "ECS API service name."
   value       = aws_ecs_service.api.name
@@ -73,12 +88,22 @@ output "database_url_secret_arn" {
   value       = aws_secretsmanager_secret.database_url.arn
 }
 
-output "session_secret_arn" {
-  description = "Secret ARN for the app session secret. Populate before starting ECS tasks."
-  value       = aws_secretsmanager_secret.session_secret.arn
+output "invitation_signing_secret_arn" {
+  description = "Secret ARN for the dedicated invitation-signing secret."
+  value       = aws_secretsmanager_secret.invitation_signing.arn
+}
+
+output "first_admin_password_secret_arn" {
+  description = "One-use first-administrator password secret ARN."
+  value       = aws_secretsmanager_secret.first_admin_password.arn
 }
 
 output "worker_schedule_name" {
   description = "EventBridge Scheduler schedule for the OCR worker task."
   value       = aws_scheduler_schedule.worker.name
 }
+
+output "bootstrap_task_definition_arns" {
+  description = "Fixed one-off task definitions; running them remains a Package E gate."
+  value       = { for phase, task in aws_ecs_task_definition.bootstrap : phase => task.arn }
+}
diff --git a/infra/terraform/variables.tf b/infra/terraform/variables.tf
index 707eb5f..93a89ca 100644
--- a/infra/terraform/variables.tf
+++ b/infra/terraform/variables.tf
@@ -17,138 +17,210 @@ variable "aws_profile" {
 }
 
 variable "project" {
-  description = "Project tag and resource prefix."
-  type        = string
-  default     = "paprnav"
+  type    = string
+  default = "paprnav"
 }
 
 variable "environment" {
-  description = "Deployment environment."
+  type    = string
+  default = "pilot"
+}
+
+variable "external_mode" {
+  description = "Enable execution-ready input checks. Package C fixture plans keep this false."
+  type        = bool
+  default     = false
+}
+
+variable "pilot_hostname" {
+  description = "Operator-owned canonical hostname; no default is permitted."
   type        = string
-  default     = "pilot"
+
+  validation {
+    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$", var.pilot_hostname))
+    error_message = "pilot_hostname must be one canonical lower-case DNS hostname."
+  }
 }
 
-variable "budget_limit_usd" {
-  description = "Monthly pilot budget limit in USD."
+variable "pilot_certificate_arn" {
+  description = "Exact ARN of the operator-provisioned, issued ACM certificate for pilot_hostname."
   type        = string
-  default     = "300"
+
+  validation {
+    condition     = can(regex("^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[0-9a-f-]+$", var.pilot_certificate_arn))
+    error_message = "pilot_certificate_arn must be one exact ACM certificate ARN."
+  }
+}
+
+variable "route53_zone_id" {
+  description = "Exact operator-supplied Route53 hosted-zone ID."
+  type        = string
+
+  validation {
+    condition     = can(regex("^Z[A-Z0-9]{8,32}$", var.route53_zone_id))
+    error_message = "route53_zone_id must be an explicit Route53 hosted-zone ID."
+  }
+}
+
+variable "route53_zone_name" {
+  description = "Expected canonical DNS name; Terraform verifies it against the hosted-zone ID returned by Route53."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+\\.?$", var.route53_zone_name))
+    error_message = "route53_zone_name must be one canonical lower-case DNS zone name."
+  }
 }
 
 variable "budget_notification_email" {
-  description = "Email address for AWS budget notifications. Empty disables budget notifications and should only be used for local planning."
+  description = "Real AWS Budget recipient in external mode; no repository default."
+  type        = string
+}
+
+variable "policy_updater_principal_arn" {
+  description = "Operator-admin principal authorized to version only paprnav-terraform-deploy."
+  type        = string
+}
+
+variable "api_image" {
+  description = "Immutable API image reference."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.api_image))
+    error_message = "api_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "frontend_image" {
+  description = "Immutable frontend image reference."
   type        = string
-  default     = ""
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.frontend_image))
+    error_message = "frontend_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "bootstrap_image" {
+  description = "Immutable dedicated migration/bootstrap image reference."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.bootstrap_image))
+    error_message = "bootstrap_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "first_admin_email" {
+  description = "First administrator identity; the password remains only in Secrets Manager."
+  type        = string
+}
+
+variable "first_admin_name" {
+  description = "First administrator display name."
+  type        = string
+}
+
+variable "first_admin_organization" {
+  description = "Permanent platform organization name created during first-admin bootstrap."
+  type        = string
+}
+
+variable "budget_limit_usd" {
+  type    = string
+  default = "300"
 }
 
 variable "log_retention_days" {
-  description = "CloudWatch log retention for pilot services."
-  type        = number
-  default     = 30
+  type    = number
+  default = 30
 }
 
 variable "force_destroy_buckets" {
-  description = "Allow Terraform to destroy non-empty pilot buckets. Keep false for volunteer data safety."
+  description = "Must remain false for volunteer-data safety."
   type        = bool
   default     = false
+
+  validation {
+    condition     = !var.force_destroy_buckets
+    error_message = "pilot buckets may not use force_destroy."
+  }
 }
 
 variable "vpc_cidr" {
-  description = "CIDR block for the paprnav pilot VPC."
-  type        = string
-  default     = "10.42.0.0/16"
+  type    = string
+  default = "10.42.0.0/16"
 }
 
 variable "public_subnet_cidrs" {
-  description = "CIDR blocks for public ALB/ECS subnets."
-  type        = list(string)
-  default     = ["10.42.0.0/24", "10.42.1.0/24"]
+  type    = list(string)
+  default = ["10.42.0.0/24", "10.42.1.0/24"]
 }
 
 variable "private_subnet_cidrs" {
-  description = "CIDR blocks for private database subnets."
-  type        = list(string)
-  default     = ["10.42.10.0/24", "10.42.11.0/24"]
+  type    = list(string)
+  default = ["10.42.10.0/24", "10.42.11.0/24"]
 }
 
 variable "api_container_port" {
-  description = "Container port for the FastAPI service."
-  type        = number
-  default     = 8000
+  type    = number
+  default = 8000
 }
 
 variable "frontend_container_port" {
-  description = "Container port for the Next.js frontend service."
-  type        = number
-  default     = 3000
-}
-
-variable "api_desired_count" {
-  description = "Desired ECS task count for the API service. Keep 0 until the API image is pushed."
-  type        = number
-  default     = 0
-}
-
-variable "frontend_desired_count" {
-  description = "Desired ECS task count for the frontend service. Keep 0 until the frontend image is pushed."
-  type        = number
-  default     = 0
+  type    = number
+  default = 3000
 }
 
 variable "ecs_task_cpu" {
-  description = "Default Fargate task CPU units for pilot API/frontend tasks."
-  type        = number
-  default     = 512
+  type    = number
+  default = 512
 }
 
 variable "ecs_task_memory" {
-  description = "Default Fargate task memory in MiB for pilot API/frontend tasks."
-  type        = number
-  default     = 1024
+  type    = number
+  default = 1024
 }
 
 variable "db_instance_class" {
-  description = "RDS PostgreSQL instance class for the pilot."
-  type        = string
-  default     = "db.t4g.micro"
+  type    = string
+  default = "db.t4g.micro"
 }
 
 variable "db_allocated_storage_gb" {
-  description = "Allocated RDS PostgreSQL storage in GiB."
-  type        = number
-  default     = 20
+  type    = number
+  default = 20
 }
 
 variable "db_engine_version" {
-  description = "RDS PostgreSQL engine version."
-  type        = string
-  default     = "16.3"
+  type    = string
+  default = "16.3"
 }
 
 variable "db_backup_retention_days" {
-  description = "RDS automated backup retention in days."
-  type        = number
-  default     = 7
+  type    = number
+  default = 7
 }
 
 variable "rds_deletion_protection" {
-  description = "Enable deletion protection for the pilot RDS instance."
-  type        = bool
-  default     = true
-}
+  type    = bool
+  default = true
 
-variable "worker_schedule_expression" {
-  description = "EventBridge Scheduler expression for the OCR worker task."
-  type        = string
-  default     = "rate(15 minutes)"
+  validation {
+    condition     = var.rds_deletion_protection
+    error_message = "pilot RDS deletion protection must remain enabled."
+  }
 }
 
-variable "worker_schedule_state" {
-  description = "EventBridge Scheduler state for the OCR worker task. Keep DISABLED until images and secrets are ready."
-  type        = string
-  default     = "DISABLED"
+variable "login_rate_limit" {
+  description = "Five-minute per-IP login request threshold."
+  type        = number
+  default     = 100
+}
 
-  validation {
-    condition     = contains(["ENABLED", "DISABLED"], var.worker_schedule_state)
-    error_message = "worker_schedule_state must be ENABLED or DISABLED."
-  }
+variable "invitation_rate_limit" {
+  description = "Five-minute per-IP invitation create/accept threshold."
+  type        = number
+  default     = 50
 }
diff --git a/infra/terraform/versions.tf b/infra/terraform/versions.tf
index 1b67d5d..c76bf06 100644
--- a/infra/terraform/versions.tf
+++ b/infra/terraform/versions.tf
@@ -13,7 +13,7 @@ terraform {
   required_providers {
     aws = {
       source  = "hashicorp/aws"
-      version = "~> 5.0"
+      version = "= 5.100.0"
     }
   }
 }

```

## Untracked text files

### `backend/tests/test_pilot_package_c.py`

size=27366; sha256=3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124; truncated=false

```text
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
from types import ModuleType, SimpleNamespace
from typing import Any
from urllib.parse import unquote

from alembic.config import Config
import psycopg
import pytest
from sqlalchemy.engine import make_url

from app.core.config import get_settings


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bootstrap() -> ModuleType:
    return load_module("paprnav_package_c_bootstrap", REPO_ROOT / "infra/bootstrap/bootstrap.py")


@pytest.fixture(scope="module")
def release_builder() -> ModuleType:
    return load_module("paprnav_package_c_release_builder", REPO_ROOT / "scripts/build_pilot_release_context.py")


def test_ecs_json_key_becomes_the_actual_application_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    terraform = (REPO_ROOT / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    selector = '${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::'
    assert terraform.count(selector) == 2
    assert 'name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn' not in terraform

    published = json.dumps(
        {"DATABASE_URL": "postgresql+psycopg://paprnav_app:p%40ss@db.internal:5432/paprnav"}
    )
    injected = json.loads(published)["DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", injected)
    get_settings.cache_clear()
    assert get_settings().database_url == injected


@pytest.mark.parametrize(
    "password",
    [
        "admin@%reserved",
        "colon:/question?#brackets[]percent%at@",
    ],
)
def test_admin_credentials_survive_url_and_configparser(
    bootstrap: ModuleType,
    password: str,
) -> None:
    connection = {
        "host": "db.internal",
        "port": 5432,
        "dbname": "paprnav",
        "user": "paprnav_admin",
        "password": password,
        "sslmode": "require",
    }
    environment_url = bootstrap.alembic_environment_url(connection)
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", environment_url)
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.username == "paprnav_admin"
    assert parsed.password == password
    assert parsed.host == "db.internal"


def test_migration_passes_only_configparser_safe_url(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "admin@%reserved"

    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {
                "SecretString": json.dumps(
                    {
                        "username": "paprnav_admin",
                        "password": password,
                        "host": "db.internal",
                        "port": 5432,
                    }
                )
            }

    captured: dict[str, str] = {}

    def run(*_: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs["env"])  # type: ignore[arg-type]
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    bootstrap.run_migration(Secrets())
    assert "%%" in captured["DATABASE_URL"]
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", captured["DATABASE_URL"])
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.password == password


def test_terraform_gates_are_blocking_and_bind_actual_zone_identity() -> None:
    variables = (REPO_ROOT / "infra/terraform/variables.tf").read_text(encoding="utf-8")
    main = (REPO_ROOT / "infra/terraform/main.tf").read_text(encoding="utf-8")
    load_balancer = (REPO_ROOT / "infra/terraform/load_balancer.tf").read_text(encoding="utf-8")
    versions = (REPO_ROOT / "infra/terraform/versions.tf").read_text(encoding="utf-8")
    assert 'check "external_inputs"' not in variables
    assert 'check "image_repositories"' not in main
    assert 'resource "terraform_data" "deployment_input_gate"' in main
    assert 'resource "terraform_data" "certificate_input_gate"' in main
    assert main.count("precondition {") >= 8
    assert 'data "aws_route53_zone" "pilot"' in main
    assert "data.aws_route53_zone.pilot.name" in main
    assert "private_zone = false" in main
    assert load_balancer.count("data.aws_route53_zone.pilot.zone_id") == 1

    assert 'variable "pilot_certificate_arn"' in variables
    assert 'data "aws_acm_certificate" "pilot"' in main
    for exact_filter in (
        'domain      = var.pilot_hostname',
        'statuses    = ["ISSUED"]',
        'types       = ["AMAZON_ISSUED"]',
        'key_types   = ["RSA_2048"]',
        'tags        = { Project = "paprnav" }',
        'most_recent = false',
    ):
        assert exact_filter in main
    for bound_value in (
        "data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn",
        "data.aws_acm_certificate.pilot.domain == var.pilot_hostname",
        'data.aws_acm_certificate.pilot.status == "ISSUED"',
        'lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"',
        '"arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"',
    ):
        assert bound_value in main
    assert 'resource "aws_acm_certificate"' not in load_balancer
    assert 'resource "aws_acm_certificate_validation"' not in load_balancer
    assert 'resource "aws_route53_record" "certificate_validation"' not in load_balancer
    assert "certificate_arn   = data.aws_acm_certificate.pilot.arn" in load_balancer
    assert "depends_on = [terraform_data.certificate_input_gate]" in load_balancer
    assert 'version = "= 5.100.0"' in versions

    expected = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:"
    good = expected + "a" * 64
    wrong_repository = "527257972989.dkr.ecr.us-east-1.amazonaws.com/other/api@sha256:" + "a" * 64
    mutable = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api:latest"
    assert good.startswith(expected)
    assert not wrong_repository.startswith(expected)
    assert not mutable.startswith(expected)


def one(values: list[Any]) -> Any:
    assert len(values) == 1
    return values[0]


@pytest.fixture(scope="module")
def waf_plan() -> dict[str, Any]:
    # Supply the actual output of `terraform test -json -verbose` from an
    # isolated, current-source module. No handwritten HCL parser or substitute
    # regex/normalization table is used. Terraform also asserts the field and
    # transformation structure directly in package_c.tftest.hcl.
    path = os.getenv("PAPRNAV_PACKAGE_C_TERRAFORM_TEST_JSON")
    if not path:
        pytest.skip("generate the current Package C Terraform mock-plan JSON to run the WAF oracle")
    records = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.startswith("{"):
                continue  # `terraform validate` may precede the JSON stream.
            item = json.loads(line)
            if item.get("type") == "test_plan":
                # Provider schemas are large and are not part of this oracle.
                item["test_plan"].pop("provider_schemas", None)
            if item.get("type") in ("test_plan", "test_summary"):
                records.append(item)
    assert one([item["test_summary"] for item in records if item.get("type") == "test_summary"])["status"] == "pass"
    plan = one([
        item["test_plan"] for item in records
        if item.get("type") == "test_plan" and item.get("@testrun") == "waf_auth_and_upload_contract"
    ])
    return {item["address"]: item["change"]["after"] for item in plan["resource_changes"]}


def active_block(block: dict[str, Any]) -> tuple[str, Any]:
    return one([(key, value) for key, value in block.items() if value not in (None, [], {})])


def waf_matches(statement: dict[str, Any], patterns: dict[str, list[str]], request: dict[str, Any]) -> bool:
    """Evaluate only the emitted WAF subset; unknown constructs fail the test."""
    kind, values = active_block(statement)
    clause = one(values)
    if kind == "and_statement":
        return all(waf_matches(child, patterns, request) for child in clause["statement"])
    if kind == "not_statement":
        return not waf_matches(one(clause["statement"]), patterns, request)
    if kind == "rate_based_statement":
        return waf_matches(one(clause["scope_down_statement"]), patterns, request)
    field, selection = active_block(one(clause["field_to_match"]))
    if field == "method":
        value = request["method"]
    elif field == "uri_path":
        value = request["path"]
    elif field == "single_header":
        value = request["headers"].get(one(selection)["name"], "")
    elif field == "body":
        assert one(selection)["oversize_handling"] == "MATCH"
        value = request["body"]
    else:
        raise AssertionError(f"unsupported WAF field: {field}")
    for transform in sorted(clause["text_transformation"], key=lambda item: item["priority"]):
        operation = transform["type"]
        if operation == "URL_DECODE":
            value = unquote(value)
        elif operation == "LOWERCASE":
            value = value.lower()
        else:
            assert operation == "NONE", f"unsupported WAF transform: {operation}"
    if kind == "regex_pattern_set_reference_statement":
        return any(re.search(pattern, value) is not None for pattern in patterns[clause["arn"]])
    if kind == "byte_match_statement":
        if clause["positional_constraint"] == "EXACTLY":
            return value == clause["search_string"]
        assert clause["positional_constraint"] == "STARTS_WITH"
        return value.startswith(clause["search_string"])
    assert kind == "size_constraint_statement"
    assert clause["comparison_operator"] == "GT"
    return len(value) > clause["size"]


def assert_waf_contract(plan: dict[str, Any]) -> None:
    acl = plan["aws_wafv2_web_acl.pilot"]
    rules = {rule["name"]: rule for rule in acl["rule"]}
    patterns = {
        value["arn"]: [item["regex_string"] for item in value["regular_expression"]]
        for address, value in plan.items() if address.startswith("aws_wafv2_regex_pattern_set.")
    }
    assert len(rules) == 4 and len(patterns) == 3
    assert not one(acl["visibility_config"])["sampled_requests_enabled"]
    assert all(not one(rule["visibility_config"])["sampled_requests_enabled"] for rule in rules.values())
    request = {"method": "POST", "path": "", "headers": {}, "body": b"x" * 8193}
    auth_cases = {
        "login-rate-limit": (30, 100, [
            "/api/v1/auth/login", "/api/v1/auth/login/", "/api/v1/auth/%6cogin",
            "/api/v1/auth/%6Cogin/", "/api/v1/auth%2flogin%2f",
        ]),
        "invitation-rate-limit": (40, 50, [
            "/api/v1/auth/invitations", "/api/v1/auth/invitations/",
            "/api/v1/auth/%69nvitations", "/api/v1/auth/invitations/accept",
            "/api/v1/auth/invitations/accept/", "/api/v1/auth/invitations/%61ccept",
            "/api/v1/auth/invitations/%61ccept/", "/api/v1/auth/invitations%2Faccept%2F",
        ]),
    }
    for name, (priority, limit, paths) in auth_cases.items():
        rule = rules[name]
        assert rule["priority"] == priority and active_block(one(rule["action"]))[0] == "block"
        statement = one(rule["statement"])
        rate = one(statement["rate_based_statement"])
        assert rate["aggregate_key_type"] == "IP" and rate["limit"] == limit
        predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
        assert len(predicates) == 2
        for predicate in predicates:
            kind, values = active_block(predicate)
            value = one(values)
            expected_field, expected_transform = (
                ("method", "NONE") if kind == "byte_match_statement" else ("uri_path", "URL_DECODE")
            )
            assert active_block(one(value["field_to_match"]))[0] == expected_field
            assert value["text_transformation"] == [{"priority": 0, "type": expected_transform}]
        for path in paths:
            assert waf_matches(statement, patterns, {**request, "path": path}), path
            assert not waf_matches(statement, patterns, {**request, "method": "GET", "path": path}), path
        assert not waf_matches(statement, patterns, {**request, "path": paths[0] + "-extra"})
        assert not waf_matches(statement, patterns, {**request, "method": "%50OST", "path": paths[0]})
        other = "/api/v1/auth/invitations/accept" if name == "login-rate-limit" else "/api/v1/auth/login"
        assert not waf_matches(statement, patterns, {**request, "path": other})

    # Bind the raw upload exception AND its body-size/managed-rule context.
    managed = rules["aws-managed-common"]
    assert managed["priority"] == 10
    common = one(one(managed["statement"])["managed_rule_group_statement"])
    assert common["name"] == "AWSManagedRulesCommonRuleSet" and common["vendor_name"] == "AWS"
    override = one(common["rule_action_override"])
    assert override["name"] == "SizeRestrictions_BODY"
    assert active_block(one(override["action_to_use"]))[0] == "count"
    oversize = rules["block-oversize-body-except-reviewed-upload"]
    assert oversize["priority"] == 20 and active_block(one(oversize["action"]))[0] == "block"
    statement = one(oversize["statement"])
    predicates = one(statement["and_statement"])["statement"]
    assert one(predicates[0]["size_constraint_statement"])["size"] == 8192
    exception = one(one(predicates[1]["not_statement"])["statement"])
    upload_predicates = one(exception["and_statement"])["statement"]
    assert len(upload_predicates) == 3
    uri = one(upload_predicates[1]["regex_pattern_set_reference_statement"])
    assert active_block(one(uri["field_to_match"]))[0] == "uri_path"
    assert uri["text_transformation"] == [{"priority": 0, "type": "NONE"}]
    assert patterns[uri["arn"]] == [r"^/api/v1/aircraft/[^/]+/uploads$"]
    upload = {**request, "path": "/api/v1/aircraft/plane/uploads", "headers": {"content-type": "multipart/form-data; boundary=pilot"}}
    assert not waf_matches(statement, patterns, upload)
    for change in (
        {"method": "GET"}, {"path": upload["path"] + "/"},
        {"path": "/api/v1/aircraft/plane/%75ploads"},
        {"path": "/api/v1/aircraft/plane%2Fuploads"},
        {"path": "/api/v1/aircraft/plane/uploads-extra"},
        {"headers": {"content-type": "application/json"}},
        {"path": "/api/v1/auth/invitations/accept"},
    ):
        assert waf_matches(statement, patterns, {**upload, **change}), change
    assert not waf_matches(statement, patterns, {**request, "body": b"x" * 8192})
    assert waf_matches(statement, patterns, request)


def test_waf_generated_auth_normalization_and_raw_upload_exception(waf_plan: dict[str, Any]) -> None:
    assert_waf_contract(waf_plan)
    # The exact remediation-1 defect must be rejected by this same oracle.
    old = deepcopy(waf_plan)
    invitation = next(rule for rule in old["aws_wafv2_web_acl.pilot"]["rule"] if rule["name"] == "invitation-rate-limit")
    rate = one(one(invitation["statement"])["rate_based_statement"])
    predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
    one(predicates[0]["byte_match_statement"])["text_transformation"][0]["type"] = "URL_DECODE"
    one(predicates[1]["regex_pattern_set_reference_statement"])["text_transformation"][0]["type"] = "NONE"
    with pytest.raises(AssertionError):
        assert_waf_contract(old)


def test_acm_policy_is_exactly_read_only_and_account_region_bounded() -> None:
    generator = load_module(
        "paprnav_package_c_policy_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    hostname = "pilot.example.com"
    policy = generator.generate(
        "Z123456789",
        hostname,
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555",
    )
    statements = policy["deployPolicySupplement"]["Statement"]
    acm_statements = [item for item in statements if any(action.lower().startswith("acm:") for action in item["Action"])]
    actions = {action for item in acm_statements for action in item["Action"]}
    assert actions == {
        "acm:ListCertificates",
        "acm:DescribeCertificate",
        "acm:ListTagsForCertificate",
        "acm:GetCertificate",
    }
    assert all("*" not in action for action in actions)
    assert all("ExportCertificate" not in action for action in actions)

    inventory = one([item for item in acm_statements if item["Action"] == ["acm:ListCertificates"]])
    metadata = one([item for item in acm_statements if "acm:DescribeCertificate" in item["Action"]])
    assert inventory["Resource"] == "*"
    assert metadata["Resource"] == "arn:aws:acm:us-east-1:527257972989:certificate/*"
    for item in (inventory, metadata):
        assert item["Condition"] == {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    matrix_acm = one([row for row in matrix["rows"] if any(action.startswith("acm:") for action in row["actions"])])
    assert set(matrix_acm["actions"]) == actions
    assert "mutation" not in matrix_acm["condition"].lower()


def test_release_builder_candidate_gate_and_preserved_dirt_separation(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_policy = {
        "approvedMigrationAuthoritySha256": {"backend/app/core/config.py": "0" * 64},
        "protectedBlobSha256": {"backend/app/models/core.py": "1" * 64},
    }
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    reviewed_path = "backend/Dockerfile"
    preserved_path = "backend/app/models/core.py"
    absolute = tmp_path / reviewed_path
    absolute.parent.mkdir(parents=True)
    absolute.write_text("FROM scratch\n", encoding="utf-8")
    manifest = tmp_path / "overlay.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "paprnav-reviewed-overlay-v2",
                "sourceCommit": "a" * 40,
                "reviewedInputs": [
                    {"path": reviewed_path, "sha256": release_builder.hashlib.sha256(absolute.read_bytes()).hexdigest()}
                ],
                "preservedExclusions": [preserved_path],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release_builder, "dirty_paths", lambda: {reviewed_path, preserved_path})
    reviewed, preserved = release_builder.overlay_files(
        manifest,
        "a" * 40,
        {"forbiddenPaths": [], "forbiddenPrefixes": []},
        boundary_policy,
    )
    assert reviewed == {reviewed_path: b"FROM scratch\n"}
    assert preserved == [preserved_path]

    protected_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    protected_manifest["reviewedInputs"] = [
        {"path": preserved_path, "sha256": "1" * 64}
    ]
    protected_manifest["preservedExclusions"] = [reviewed_path]
    manifest.write_text(json.dumps(protected_manifest), encoding="utf-8")
    with pytest.raises(release_builder.ContextError, match="protected authority"):
        release_builder.overlay_files(
            manifest,
            "a" * 40,
            {"forbiddenPaths": [], "forbiddenPrefixes": []},
            boundary_policy,
        )


def test_release_builder_blocks_failed_package_a_authority(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = load_module(
        "verify_pilot_release_boundary",
        REPO_ROOT / "scripts/verify_pilot_release_boundary.py",
    )
    monkeypatch.setitem(sys.modules, "verify_pilot_release_boundary", boundary)

    policy_path = tmp_path / "boundary.json"
    policy_path.write_text('{"version":"test"}\n', encoding="utf-8")
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(release_builder, "BOUNDARY_POLICY", policy_path)
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {"status": "pass", "errors": []})
    assert release_builder.candidate_authority("a" * 40) == {"version": "test"}
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {
        "status": "fail",
        "errors": ["protected release blob differs"],
    })
    with pytest.raises(release_builder.ContextError, match="protected release blob differs"):
        release_builder.candidate_authority("a" * 40)


def postgres_connection_args() -> dict[str, object]:
    raw = os.getenv("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL", "")
    if not raw:
        pytest.skip("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL is not set")
    parsed = make_url(raw)
    if not parsed.database or not parsed.database.startswith("paprnav_package_c_"):
        pytest.fail("Package C PostgreSQL tests require a disposable paprnav_package_c_* database")
    return {
        "host": parsed.host,
        "port": parsed.port or 5432,
        "dbname": parsed.database,
        "user": parsed.username,
        "password": parsed.password,
        "sslmode": "disable",
    }


def prepare_first_admin_database(connection_args: dict[str, object], bootstrap: ModuleType) -> None:
    # Synthetic transaction/control fixture only. It does not establish that
    # first-admin succeeds against the full sealed 0029 migrated schema.
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS pilot_control CASCADE")
            cursor.execute("DROP TABLE IF EXISTS product_events, organization_memberships, organizations, users CASCADE")
            cursor.execute(
                "CREATE TABLE users (id varchar(36) PRIMARY KEY, email text NOT NULL, name text NOT NULL, "
                "password_hash text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organizations (id varchar(36) PRIMARY KEY, name text NOT NULL, type text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organization_memberships (id varchar(36) PRIMARY KEY, organization_id varchar(36) NOT NULL, "
                "user_id varchar(36) NOT NULL, role text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE product_events (id varchar(36) PRIMARY KEY, actor_user_id varchar(36), "
                "organization_id varchar(36), event_type text, event_source text, subject_type text, "
                "subject_id varchar(36), properties_json json)"
            )
            bootstrap.install_control_schema(cursor)
        connection.commit()


def relation_counts(connection_args: dict[str, object]) -> list[int]:
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            result = []
            for relation in (
                "users",
                "organizations",
                "organization_memberships",
                "product_events",
                "pilot_control.bootstrap_consumptions",
            ):
                cursor.execute(f"SELECT count(*) FROM {relation}")
                result.append(cursor.fetchone()[0])
            return result


def test_first_admin_failure_boundaries_and_concurrency(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_args = postgres_connection_args()
    prepare_first_admin_database(connection_args, bootstrap)

    class Secrets:
        def get_secret_value(self, *, SecretId: str) -> dict[str, str]:
            if SecretId == "admin":
                return {"SecretString": json.dumps({
                    "username": "paprnav_admin",
                    "password": connection_args["password"],
                    "host": connection_args["host"],
                    "port": connection_args["port"],
                    "dbname": connection_args["dbname"],
                })}
            assert SecretId == "first-admin"
            return {"SecretString": json.dumps({"password": "first-admin-password"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin")
    monkeypatch.setenv("PAPRNAV_FIRST_ADMIN_SECRET_ARN", "first-admin")
    monkeypatch.setenv("PAPRNAV_DATABASE_SSLMODE", "disable")
    identity = {"email": "first@example.com", "name": "First Admin", "organization": "Paprnav"}
    for point in ("user", "organization", "membership", "audit", "consumption"):
        monkeypatch.setenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER", point)
        with pytest.raises(bootstrap.BootstrapError, match="injected failure"):
            bootstrap.run_first_admin(Secrets(), identity=identity)
        assert relation_counts(connection_args) == [0, 0, 0, 0, 0]
    monkeypatch.delenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER")

    barrier = threading.Barrier(2)

    def synchronized_connect(**kwargs: object) -> psycopg.Connection:
        barrier.wait(timeout=10)
        return psycopg.connect(**kwargs)

    identities = (
        identity,
        {"email": "other@example.com", "name": "Other Admin", "organization": "Other"},
    )

    def attempt(value: dict[str, str]) -> str:
        try:
            bootstrap.run_first_admin(Secrets(), connect=synchronized_connect, identity=value)
            return "success"
        except bootstrap.BootstrapError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(attempt, identities))
    assert outcomes == ["rejected", "success"]
    assert relation_counts(connection_args) == [1, 1, 1, 1, 1]

    with pytest.raises(bootstrap.BootstrapError, match="permanently unavailable"):
        bootstrap.run_first_admin(Secrets(), identity=identity)


def test_three_dockerfiles_are_pinned_non_root_and_bootstrap_inventory_is_sealed() -> None:
    api = (REPO_ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    frontend = (REPO_ROOT / "frontend/paprnav-frontend/Dockerfile").read_text(encoding="utf-8")
    bootstrap = (REPO_ROOT / "infra/bootstrap/Dockerfile").read_text(encoding="utf-8")
    assert "@sha256:" in api and "USER 10001:10001" in api
    assert "@sha256:" in frontend and "USER 10001:10001" in frontend
    assert "@sha256:" in bootstrap and "USER 10001:10001" in bootstrap
    assert "COPY --chown=root:root migration/ /migration/" in bootstrap
    assert "backend/" not in bootstrap and "frontend/" not in bootstrap
    context_policy = json.loads((REPO_ROOT / ".ai/pilot-package-c-context-v1.json").read_text(encoding="utf-8"))
    assert all("0030" in path for path in context_policy["forbiddenPaths"][:3])

```
### `infra/aws-iam/pilot-policy-matrix.json`

size=2898; sha256=553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2; truncated=false

```text
{
  "version": "paprnav-pilot-policy-matrix-v1",
  "accountId": "527257972989",
  "region": "us-east-1",
  "deployPolicyArn": "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy",
  "rows": [
    {
      "principal": "operator-admin prerequisite",
      "actions": ["iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"],
      "resourceTemplate": "${DEPLOY_POLICY_ARN}"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["acm:ListCertificates", "acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
      "resourceTemplate": "arn:aws:acm:${REGION}:${ACCOUNT}:certificate/*",
      "condition": "Read-only lookup only: ListCertificates uses Resource=* and all ACM actions are restricted to the configured region; certificate metadata reads are additionally account/region bounded by the certificate ARN. Certificate provisioning, validation, tagging, deletion, export, and renewal-record ownership remain outside the Terraform deploy role."
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["wafv2:CreateWebACL", "wafv2:GetWebACL", "wafv2:UpdateWebACL", "wafv2:DeleteWebACL", "wafv2:CreateRegexPatternSet", "wafv2:GetRegexPatternSet", "wafv2:UpdateRegexPatternSet", "wafv2:DeleteRegexPatternSet", "wafv2:AssociateWebACL", "wafv2:DisassociateWebACL", "wafv2:List*", "wafv2:TagResource", "wafv2:UntagResource"],
      "resourceTemplate": "arn:aws:wafv2:${REGION}:${ACCOUNT}:regional/*/paprnav-*/*"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets", "route53:GetChange", "route53:ListTagsForResource"],
      "resourceTemplate": "arn:aws:route53:::hostedzone/${HOSTED_ZONE_ID}"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["iam:CreateServiceLinkedRole"],
      "resourceTemplate": "exact RDS, ECS, and ELB service-linked-role ARNs",
      "condition": "matching iam:AWSServiceName"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret", "secretsmanager:PutResourcePolicy", "secretsmanager:GetResourcePolicy", "secretsmanager:DeleteResourcePolicy"],
      "resourceTemplate": "arn:aws:secretsmanager:${REGION}:${ACCOUNT}:secret:/paprnav/pilot/*",
      "excludes": ["secretsmanager:GetSecretValue", "secretsmanager:PutSecretValue"]
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["secretsmanager:CreateSecret", "secretsmanager:TagResource", "kms:DescribeKey"],
      "resourceTemplate": "RDS-managed rds!db-* names and exact aws/secretsmanager KMS key"
    }
  ]
}

```
### `infra/terraform/tests/package_c.tftest.hcl`

size=8979; sha256=571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c; truncated=false

```text
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  mock_data "aws_route53_zone" {
    defaults = {
      zone_id      = "Z123456789"
      name         = "example.com."
      private_zone = false
    }
  }

  mock_resource "aws_db_instance" {
    defaults = {
      db_name = "paprnav"
      master_user_secret = [{
        secret_arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-test"
      }]
    }
  }

  mock_data "aws_acm_certificate" {
    defaults = {
      arn    = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
      domain = "pilot.example.com"
      status = "ISSUED"
      tags   = { Project = "paprnav" }
    }
  }
}

variables {
  pilot_hostname               = "pilot.example.com"
  pilot_certificate_arn        = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  route53_zone_id              = "Z123456789"
  route53_zone_name            = "example.com"
  budget_notification_email    = "pilot-owner@example.com"
  policy_updater_principal_arn = "arn:aws:iam::527257972989:role/paprnav-policy-updater"
  api_image                    = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  frontend_image               = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-frontend@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  bootstrap_image              = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-bootstrap@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  first_admin_email            = "first-admin@example.com"
  first_admin_name             = "First Admin"
  first_admin_organization     = "Paprnav"
}

run "valid_gate_inputs" {
  command = plan

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }
}

run "valid_certificate_gate" {
  command = plan

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  assert {
    condition = (
      data.aws_acm_certificate.pilot.domain == var.pilot_hostname &&
      data.aws_acm_certificate.pilot.most_recent == false &&
      length(data.aws_acm_certificate.pilot.statuses) == 1 &&
      data.aws_acm_certificate.pilot.statuses[0] == "ISSUED" &&
      length(data.aws_acm_certificate.pilot.types) == 1 &&
      data.aws_acm_certificate.pilot.types[0] == "AMAZON_ISSUED" &&
      length(data.aws_acm_certificate.pilot.key_types) == 1 &&
      contains(data.aws_acm_certificate.pilot.key_types, "RSA_2048") &&
      length(data.aws_acm_certificate.pilot.tags) == 1 &&
      lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
    )
    error_message = "The ACM lookup must remain exact, issued, Amazon-issued, RSA_2048, Project-owned, and ambiguity rejecting."
  }
}

run "wrong_certificate_arn_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:527257972989:certificate/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_domain_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { domain = "unrelated.example.net" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_status_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { status = "PENDING_VALIDATION" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_tag_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { tags = { Project = "other" } }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_account_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_region_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

# Export this plan with `terraform test -json -verbose` for the bounded Python
# request oracle in test_pilot_package_c.py. Only computed ARNs are mocked; the
# WAF statements, field selectors, transformations and regexes are real config.
run "waf_auth_and_upload_contract" {
  command = plan

  override_resource {
    target          = aws_wafv2_regex_pattern_set.login_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-login/11111111-1111-1111-1111-111111111111"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.invitation_paths
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-invitation/22222222-2222-2222-2222-222222222222"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.upload_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-upload/33333333-3333-3333-3333-333333333333"
    }
  }

  plan_options {
    target = [aws_wafv2_web_acl.pilot]
  }

  assert {
    condition = length([
      for rule in aws_wafv2_web_acl.pilot.rule : rule
      if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
      ]) == 2 && alltrue(flatten([
        for rule in aws_wafv2_web_acl.pilot.rule : [
          for predicate in one(one(rule.statement).rate_based_statement).scope_down_statement[0].and_statement[0].statement : (
            length(predicate.byte_match_statement) == 1 ? (
              one(predicate.byte_match_statement).search_string == "POST" &&
              one(predicate.byte_match_statement).positional_constraint == "EXACTLY" &&
              length(one(predicate.byte_match_statement).field_to_match[0].method) == 1 &&
              one(one(predicate.byte_match_statement).text_transformation).type == "NONE"
              ) : (
              length(one(predicate.regex_pattern_set_reference_statement).field_to_match[0].uri_path) == 1 &&
              one(one(predicate.regex_pattern_set_reference_statement).text_transformation).type == "URL_DECODE"
            )
          )
        ] if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
    ]))
    error_message = "Both auth rules must match raw POST methods and URL_DECODE the URI predicate itself."
  }

  assert {
    condition = alltrue(concat(
      [for visibility in aws_wafv2_web_acl.pilot.visibility_config : !visibility.sampled_requests_enabled],
      flatten([for rule in aws_wafv2_web_acl.pilot.rule : [
        for visibility in rule.visibility_config : !visibility.sampled_requests_enabled
      ]])
    ))
    error_message = "No WAF sampling may retain session-bearing requests."
  }
}

run "wrong_api_repository_is_blocked" {
  command = plan

  variables {
    api_image = "527257972989.dkr.ecr.us-east-1.amazonaws.com/unrelated/api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "wrong_hosted_zone_identity_is_blocked" {
  command = plan

  variables {
    route53_zone_name = "unrelated.example.net"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "placeholder_external_input_is_blocked" {
  command = plan

  variables {
    external_mode             = true
    budget_notification_email = "owner@example.invalid"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

```
### `scripts/generate_pilot_deploy_policy.py`

size=7082; sha256=46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e; truncated=false

```text
#!/usr/bin/env python3
"""Generate bounded pilot prerequisite IAM documents from explicit inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ACCOUNT = "527257972989"
REGION = "us-east-1"
DEPLOY_POLICY_ARN = f"arn:aws:iam::{ACCOUNT}:policy/paprnav-terraform-deploy"
ZONE_RE = re.compile(r"^Z[A-Z0-9]{8,32}$")
PRINCIPAL_RE = re.compile(rf"^arn:aws:iam::{ACCOUNT}:(?:user|role)/[^\s]+$")
KMS_RE = re.compile(rf"^arn:aws:kms:{REGION}:{ACCOUNT}:key/[0-9a-f-]+$")
HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")


def statement(sid: str, actions: list[str], resource: str | list[str], condition: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"Sid": sid, "Effect": "Allow", "Action": actions, "Resource": resource}
    if condition:
        result["Condition"] = condition
    return result


def generate(zone_id: str, pilot_hostname: str, updater_principal: str, kms_key_arn: str) -> dict[str, Any]:
    if ZONE_RE.fullmatch(zone_id) is None:
        raise ValueError("invalid Route53 zone ID")
    if HOSTNAME_RE.fullmatch(pilot_hostname) is None:
        raise ValueError("pilot hostname must be one canonical lower-case DNS hostname")
    if PRINCIPAL_RE.fullmatch(updater_principal) is None:
        raise ValueError("updater principal must be an exact account IAM user or role ARN")
    if KMS_RE.fullmatch(kms_key_arn) is None:
        raise ValueError("Secrets Manager KMS key must be one exact account/region key ARN")
    service_roles = {
        "rds.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/rds.amazonaws.com/AWSServiceRoleForRDS",
        "ecs.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
        "elasticloadbalancing.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing",
    }
    deploy_statements = [
        statement(
            "AcmListCertificates",
            ["acm:ListCertificates"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "AcmReadCertificateMetadata",
            ["acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
            f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement("WafInventory", ["wafv2:ListWebACLs", "wafv2:ListRegexPatternSets", "wafv2:GetWebACLForResource"], "*"),
        statement(
            "WafCreateTaggedPilotResources",
            ["wafv2:CreateWebACL", "wafv2:CreateRegexPatternSet"],
            "*",
            {"StringEquals": {"aws:RequestTag/Project": "paprnav", "aws:RequestedRegion": REGION}},
        ),
        statement(
            "WafManagePilotResources",
            ["wafv2:GetWebACL", "wafv2:UpdateWebACL", "wafv2:DeleteWebACL", "wafv2:GetRegexPatternSet", "wafv2:UpdateRegexPatternSet", "wafv2:DeleteRegexPatternSet", "wafv2:TagResource", "wafv2:UntagResource"],
            [
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*",
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/regexpatternset/paprnav-*/*",
            ],
        ),
        statement(
            "WafAssociatePilotAlb",
            ["wafv2:AssociateWebACL", "wafv2:DisassociateWebACL"],
            [f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*", f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/app/paprnav-*/*"],
        ),
        statement("Route53Inventory", ["route53:ListHostedZones", "route53:GetChange"], "*"),
        statement(
            "Route53ExactPilotZone",
            ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets", "route53:ListTagsForResource"],
            f"arn:aws:route53:::hostedzone/{zone_id}",
        ),
        statement(
            "PilotSecretLifecycleWithoutValues",
            ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret", "secretsmanager:PutResourcePolicy", "secretsmanager:GetResourcePolicy", "secretsmanager:DeleteResourcePolicy"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:/paprnav/pilot/*",
        ),
        statement(
            "RdsManagedSecretCreation",
            ["secretsmanager:CreateSecret"],
            "*",
            {"StringLike": {"secretsmanager:Name": "rds!db-*"}, "StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "RdsManagedSecretTagging",
            ["secretsmanager:TagResource"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:rds!db-*",
        ),
        statement("RdsManagedSecretKmsDescribe", ["kms:DescribeKey"], kms_key_arn),
    ]
    for index, (service_name, role_arn) in enumerate(service_roles.items(), start=1):
        deploy_statements.append(statement(
            f"CreateServiceLinkedRole{index}",
            ["iam:CreateServiceLinkedRole"],
            role_arn,
            {"StringEquals": {"iam:AWSServiceName": service_name}},
        ))
    operator = {
        "Version": "2012-10-17",
        "Statement": [statement(
            "VersionOnlyPaprnNavDeployPolicy",
            ["iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"],
            DEPLOY_POLICY_ARN,
        )],
    }
    return {
        "version": "paprnav-pilot-generated-prerequisites-v1",
        "inputs": {"hostedZoneId": zone_id, "pilotHostname": pilot_hostname, "operatorUpdaterPrincipalArn": updater_principal, "secretsManagerKmsKeyArn": kms_key_arn},
        "deployPolicySupplement": {"Version": "2012-10-17", "Statement": deploy_statements},
        "operatorUpdaterProofPolicy": operator,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hosted-zone-id", required=True)
    parser.add_argument("--pilot-hostname", required=True)
    parser.add_argument("--operator-updater-principal-arn", required=True)
    parser.add_argument("--secrets-manager-kms-key-arn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        generated = generate(
            args.hosted_zone_id,
            args.pilot_hostname,
            args.operator_updater_principal_arn,
            args.secrets_manager_kms_key_arn,
        )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "output": str(args.output), "statementCount": len(generated["deployPolicySupplement"]["Statement"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
