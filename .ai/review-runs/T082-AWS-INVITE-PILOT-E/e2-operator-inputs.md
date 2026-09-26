# Package E2 operator inputs

Updated: 2026-09-25. This file records only non-secret identity and authority
metadata. Passwords, tokens, invitation secrets, private keys, and database
URLs must never be added.

| Input | Current value/status | Required before |
| --- | --- | --- |
| Product/page display name | `Paprnav` | user-facing branding; distinct from DNS hostname |
| AWS account | `527257972989` (verified by STS on 2026-09-20) | candidate/plan identity binding |
| AWS region | `us-east-1` (profile configuration) | candidate/plan identity binding |
| Deploy profile | `paprnav-deploy`; source profile `paprnav-bootstrap` | operator execution identity |
| Deploy role | `arn:aws:iam::527257972989:role/paprnav-terraform-deploy` (STS verified) | read-only plan and later authorized apply |
| Deploy role metadata | one-hour maximum session; tags `Project=paprnav`, `Environment=pilot`, `Managedby=codex`; no permissions boundary | authority review |
| Secrets Manager KMS key | `arn:aws:kms:us-east-1:527257972989:key/ea9571ad-3bc5-4ed5-96d9-070bcad47d60` (AWS-managed; final effective-policy check pending) | final policy generation |
| Canonical pilot hostname | `pilot.paprnav.com` (operator confirmed; ACM read-only lookup verified 2026-09-25) | certificate identity, image/runtime config, Terraform plan |
| External DNS provider and zone | Squarespace-managed `paprnav.com`; Terraform does not read or mutate the zone and no Route 53 hosted-zone ID is required | DNS handoff and Terraform plan |
| Issued ACM certificate ARN | `arn:aws:acm:us-east-1:527257972989:certificate/f2f3ca73-7168-485b-b283-933cdb9915dd`; `ISSUED`, DNS validation `SUCCESS`, tags `Project=paprnav`, `Environment=pilot` verified 2026-09-25 | TLS listener plan |
| Certificate/DNS owner principal | Operator controls Squarespace DNS; exact accountable human/AWS certificate creator remains to be recorded | certificate/renewal authority evidence |
| Budget notification recipient | **required; do not commit the address if private** | foundation plan and invitations |
| Accountable cost/incident operator | **required** | foundation plan and invitations |
| IAM supplement updater principal and exact session ARN | Operator approved existing project role `arn:aws:iam::527257972989:role/paprnav-terraform-deploy`; execution used `arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/botocore-session-1790386879` | v2 supplement update executed 2026-09-25 America/Chicago |
| IAM updater accountable human owner | Repository operator approved the existing deploy role; exact accountable human identity remains to be recorded before external invitations | rollback ownership |
| IAM updater MFA or federated strong-authentication provenance | **required before external invitations**; the assumed-role session was verified, but its upstream strong-authentication provenance was not exposed | release gate |
| Root MFA or centralized root-credential-removal evidence | AWS account summary on 2026-09-25 reports `AccountMFAEnabled=0`, `AccountAccessKeysPresent=0`, and `AccountSigningCertificatesPresent=0`; root MFA/removal evidence remains a release blocker | external pilot release; never compensate with broader updater/deploy authority |
| First administrator email/display name/platform organization | **required; use restricted handoff for private values** | bootstrap task definition |
| Clean candidate commit authorization | Explicitly authorized and constructed as `e1e4c3cdcf135d6039c8b763e1a4cc251d558259`; release-boundary verifier passed and branch `codex/aws-invite-pilot` was published 2026-09-25 | immutable image/context construction |
| Restore, session-revocation, service-stop, and invitation operators | later activation input | E4/E5 |
| Initial cohort identities and consent channel | later pre-invite input | E5 |
| Provider/mode/rate/page/dollar ceilings | deferred behind paid-OCR gate | E6 |

Missing values stop at the no-mutation packet. They do not authorize identity
creation, policy attachment, ECR mutation/push, Terraform lock/plan/apply,
secret population, database migration, service activation, or invitations.

The deploy role does not need Route 53 discovery or mutation because the zone
is Squarespace-managed. Exact certificate read authority is available and the
operator-provided ARN has been verified directly. The final deployment output
must provide the ALB CNAME target for the operator to enter in Squarespace.

For an existing supplement, M1 also requires fully paginated
`ListEntitiesForPolicy` evidence for both permissions-policy and
permissions-boundary use, the prior default version/document hash, and the
exact prior deploy-role attachment state. Shared use, any boundary use, quota
exhaustion, or an incomplete/ambiguous inventory stops before versioning.
