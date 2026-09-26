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
