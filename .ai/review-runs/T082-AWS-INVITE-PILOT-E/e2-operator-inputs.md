# Package E2 operator inputs

Updated: 2026-09-20. This file records only non-secret identity and authority
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
| Canonical pilot hostname | **required** | certificate identity, image/runtime config, Terraform plan |
| Public hosted-zone ID and exact zone name | **required** | DNS identity and Terraform plan |
| Issued ACM certificate ARN | **required** | TLS listener plan |
| Certificate/DNS owner principal | **required** | certificate/renewal authority evidence |
| Budget notification recipient | **required; do not commit the address if private** | foundation plan and invitations |
| Accountable cost/incident operator | **required** | foundation plan and invitations |
| IAM supplement updater principal and exact session ARN | **required** | supplement proof and M1 authorization; do not infer from bootstrap-user identity |
| IAM updater accountable human owner | **required** | M1 authorization and rollback ownership |
| IAM updater MFA or federated strong-authentication provenance | **required** | M1; current account-summary evidence does not prove this |
| Root MFA or centralized root-credential-removal evidence | **required** | external pilot release; never compensate with broader updater/deploy authority |
| First administrator email/display name/platform organization | **required; use restricted handoff for private values** | bootstrap task definition |
| Clean candidate commit authorization | **required** | staging/commit construction |
| Restore, session-revocation, service-stop, and invitation operators | later activation input | E4/E5 |
| Initial cohort identities and consent channel | later pre-invite input | E5 |
| Provider/mode/rate/page/dollar ceilings | deferred behind paid-OCR gate | E6 |

Missing values stop at the no-mutation packet. They do not authorize identity
creation, policy attachment, ECR mutation/push, Terraform lock/plan/apply,
secret population, database migration, service activation, or invitations.

The deploy role is denied `route53:ListHostedZones` and
`acm:ListCertificates`. Those denials mean the zone/certificate are unknown,
not absent. Their owner must provide the exact values or perform the inventory
with a separately authorized read-only identity.

For an existing supplement, M1 also requires fully paginated
`ListEntitiesForPolicy` evidence for both permissions-policy and
permissions-boundary use, the prior default version/document hash, and the
exact prior deploy-role attachment state. Shared use, any boundary use, quota
exhaustion, or an incomplete/ambiguous inventory stops before versioning.
