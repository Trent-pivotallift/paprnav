# paprnav AWS IAM Bootstrap

This directory contains the IAM artifacts used to create the first paprnav-specific deployment role.

## Role

- Account: `527257972989`
- Role: `paprnav-terraform-deploy`
- Initial trusted principal: `arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap`
- Intended use: Terraform/OpenTofu plan/apply for the paprnav pilot stack in `us-east-1`.

## Policy Shape

`paprnav-terraform-deploy-policy.json` intentionally grants one comprehensive deployment role rather than staged partial roles. It covers the planned pilot stack:

- VPC/networking
- ECS/Fargate frontend, API, and worker
- ECR image repositories
- ALB/listeners/target groups
- RDS PostgreSQL
- S3 application and Terraform state buckets
- Secrets Manager and SSM parameters
- CloudWatch logs/metrics
- AWS Budgets
- Textract
- paprnav-prefixed IAM roles, policies, instance profiles, and GitHub OIDC provider

Guardrails:

- Regional service writes are constrained to `us-east-1`.
- S3 write scope is constrained to `paprnav-*` buckets.
- Secrets/parameters are constrained to `paprnav-*`/`/paprnav/*`.
- KMS destructive and policy-mutating actions require paprnav resource tags or paprnav aliases.
- IAM mutation is constrained to `paprnav-*` roles, policies, instance profiles, and the GitHub Actions OIDC provider.
- `iam:PassRole` is constrained to `paprnav-*` roles and expected AWS services.

This role is still powerful. Validate policy changes with IAM Access Analyzer and review Terraform plans before apply.

## Create Or Update Commands

Run these with an AWS principal that can create/update IAM roles and policies in account `527257972989`:

```bash
aws accessanalyzer validate-policy \
  --region us-east-1 \
  --policy-document file://infra/aws-iam/paprnav-terraform-deploy-policy.json \
  --policy-type IDENTITY_POLICY

aws iam create-role \
  --role-name paprnav-terraform-deploy \
  --assume-role-policy-document file://infra/aws-iam/paprnav-terraform-deploy-trust.json \
  --description "paprnav Terraform deployment role for pilot AWS infrastructure" \
  --tags Key=Project,Value=paprnav Key=Environment,Value=pilot Key=ManagedBy,Value=codex \
  --max-session-duration 43200

aws iam put-role-policy \
  --role-name paprnav-terraform-deploy \
  --policy-name paprnav-terraform-deploy \
  --policy-document file://infra/aws-iam/paprnav-terraform-deploy-policy.json
```

If using the managed policy created during the 2026-07-07 console bootstrap, update it with:

```bash
aws iam create-policy-version \
  --policy-arn arn:aws:iam::527257972989:policy/paprnav-terraform-deploy \
  --policy-document file://infra/aws-iam/paprnav-terraform-deploy-policy.json \
  --set-as-default
```

If the role already exists, replace `create-role` with:

```bash
aws iam update-assume-role-policy \
  --role-name paprnav-terraform-deploy \
  --policy-document file://infra/aws-iam/paprnav-terraform-deploy-trust.json
```

## 2026-07-02 Bootstrap Attempt

The local AWS CLI is currently authenticated as:

```text
arn:aws:iam::527257972989:user/marketer-pipeline-agent
```

That user could read STS identity, but could not create the role:

```text
AccessDenied: not authorized to perform iam:CreateRole on arn:aws:iam::527257972989:role/paprnav-terraform-deploy
```

It also could not validate the policy:

```text
AccessDeniedException: not authorized to perform access-analyzer:ValidatePolicy
```

## Tagging Standard

Every paprnav-managed AWS resource should be tagged when the AWS service supports tags.

Required tags:

```text
Project=paprnav
Environment=pilot
ManagedBy=terraform
```

Recommended additional tags:

```text
Application=paprnav
Owner=paprnav
CostCenter=paprnav
DataClass=volunteer-logbook-pilot
```

Terraform should set these centrally with provider `default_tags` where supported, then add resource-specific tags only when a service requires them. IAM policy enforcement for tag-on-create should be added carefully after the first plan because some AWS APIs either do not support tag-on-create or require separate follow-up tag calls.

## Bootstrap Separation

Do not leave `paprnav-terraform-deploy` trusted to `marketer-pipeline-agent`.

Recommended temporary bootstrap identity:

```text
arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap
```

Attach only this policy to that bootstrap user:

```text
infra/aws-iam/paprnav-terraform-bootstrap-assume-policy.json
```

Then update the `paprnav-terraform-deploy` role trust policy to:

```text
infra/aws-iam/paprnav-terraform-deploy-trust.json
```

After GitHub OIDC or IAM Identity Center access is configured, remove or disable the temporary bootstrap user.

## Local AWS CLI Profiles

After creating an access key for `paprnav-terraform-bootstrap`, configure it as a dedicated local profile. Do not paste access keys into chat or commit them to the repo.

```bash
aws configure --profile paprnav-bootstrap
```

Use:

```text
AWS Access Key ID: <paprnav-terraform-bootstrap access key>
AWS Secret Access Key: <paprnav-terraform-bootstrap secret key>
Default region name: us-east-1
Default output format: json
```

Verify the bootstrap profile:

```bash
aws sts get-caller-identity --profile paprnav-bootstrap
```

Expected ARN:

```text
arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap
```

Then verify role assumption:

```bash
aws sts assume-role \
  --profile paprnav-bootstrap \
  --role-arn arn:aws:iam::527257972989:role/paprnav-terraform-deploy \
  --role-session-name paprnav-terraform-test
```

For normal Terraform usage, add this profile to `~/.aws/config`:

```ini
[profile paprnav-deploy]
role_arn = arn:aws:iam::527257972989:role/paprnav-terraform-deploy
source_profile = paprnav-bootstrap
region = us-east-1
output = json
```

Then verify:

```bash
aws sts get-caller-identity --profile paprnav-deploy
```

Expected ARN shape:

```text
arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/...
```

## 2026-07-07 Verification

Manual console setup completed:

- Created `paprnav-terraform-deploy` managed policy.
- Created `paprnav-terraform-deploy` role.
- Created `paprnav-terraform-bootstrap` IAM user.
- Attached inline policy `paprnav-terraform-bootstrap-assume-deploy` to the bootstrap user.
- Updated deploy role trust to `arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap`.
- Configured local AWS profile `paprnav-bootstrap`.
- Verified `aws sts get-caller-identity --profile paprnav-bootstrap` returns account `527257972989`.
- Verified `aws sts assume-role --profile paprnav-bootstrap --role-arn arn:aws:iam::527257972989:role/paprnav-terraform-deploy --role-session-name paprnav-terraform-test` returns the expected assumed-role ARN.

## 2026-07-10 Policy Hardening

Claude reviewer flagged broad KMS permissions in the deploy policy. The policy now scopes KMS destructive and policy-mutating actions to paprnav-tagged keys or paprnav aliases. IAM Access Analyzer returned only a non-blocking S3 wildcard suggestion.

Live managed policy:

```text
arn:aws:iam::527257972989:policy/paprnav-terraform-deploy
DefaultVersionId=v5
```

Version `v5` additionally removes the unconditional `iam:PassRole` from the general IAM management statement so the service condition on `iam:PassedToService` is effective.
