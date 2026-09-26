# IAM amendment design review — initial

## Outcome

**FAIL.** The proposed Scheduler and WAF additions are sound, but the design is
not yet complete enough to authorize implementation or AWS mutation.

## Findings

### IAM-DESIGN-001 — High — secret lifecycle boundary is contradictory

The design promised complete CRUD coverage for every current Terraform
resource. The three `aws_secretsmanager_secret` resources carry descriptions,
but neither policy grants `secretsmanager:UpdateSecret` on
`/paprnav/pilot/*`. Provider 5.100.0 uses that action for description/KMS
changes. Granting it would also permit secret-value writes.

Required closure: choose and document either a metadata-update stop gate or
truthful value-mutation authority. Replace service-prefix presence checks with
resource/lifecycle/action coverage and negative tests.

### IAM-DESIGN-002 — High — DNS write authority exceeds the pilot alias

The generated `route53:ChangeResourceRecordSets` permission covers every record
in the selected zone. It can therefore alter unrelated records and ACM renewal
CNAMEs even though Terraform manages only the one pilot A alias.

Required closure: split read from write authority and constrain every record
name and type in a change batch to the canonical pilot hostname and A record,
including mixed-batch negative tests; otherwise record accountable acceptance
of zone-wide mutation authority.

### IAM-DESIGN-003 — Medium — existing-policy rollback loses pre-state

The rollback always detaches the supplement, even if it was attached before a
new version was published. Changing the default version also affects all policy
consumers before the design checks for unexpected attachments.

Required closure: preserve the original attachment state; inventory all policy
and permissions-boundary consumers before versioning; stop on any unexpected
consumer; and test absent, detached-existing, attached-existing, shared-policy,
and partial-failure cases.

### IAM-DESIGN-004 — High — M1 has no MFA-protected updater evidence

Live `iam:GetAccountSummary` evidence supplied after packet generation reports
`AccountMFAEnabled=0` and `MFADevicesInUse=0`. That does not prove whether an
external identity provider enforces MFA, but the design has no MFA/session
provenance for the candidate updater.

Required closure: record an accountable owner and require MFA-protected or
federated-session provenance for the exact updater before M1. Treat account
root MFA posture as a pilot security gate rather than broadening source
permissions.

## Verified conclusions

- Exact Scheduler CRUD on the declared schedule ARN and exact
  `iam:PassedToService=scheduler.amazonaws.com` are appropriate.
- No schedule-group mutation or Scheduler KMS permission is required.
- `wafv2:ListTagsForResource` is required by the pinned provider's tag reader.
- Runtime API, worker, frontend, execution, bootstrap, and Scheduler roles
  remain separated as described.
- Baseline SHA-256 is
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`.
- Existing compact policy sizes reproduce as 5,011 / 3,731 / 8,704.
- Focused policy tests: 2 passed, 25 deselected. Packet verification and
  `git diff --check` passed; the index was empty.

## Scope and identity

The reviewer inspected the complete dirty inventory and packet, amendment
decision, baseline, generator, matrix, every Terraform file and runtime policy,
focused tests, and relevant Package E design/rollback evidence. T081 and
unrelated application work were inventoried but not re-reviewed. No file, Git,
or AWS mutation occurred.

- Reviewer: `/root/t082_e_iam_amendment_design_review`
- Builder/coordinator: `/root`
- Requested reviewer model: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Trigger: IAM lifecycle completeness, least privilege, pass-role, and rollback
- Packet SHA-256:
  `a6d642bd3f761fca10800bdd935f4f0b3440d9f52e563d95a806d35230753799`

## References

- AWS provider 5.100.0 Secrets Manager implementation:
  <https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v5.100.0/internal/service/secretsmanager/secret.go>
- AWS `UpdateSecret` semantics:
  <https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_UpdateSecret.html>
- Route 53 IAM conditions:
  <https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/specifying-conditions-route53.html>
- IAM policy-consumer inventory:
  <https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListEntitiesForPolicy.html>
