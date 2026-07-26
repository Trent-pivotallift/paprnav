# paprnav AWS CLI Profiles

Last updated: 2026-07-07

This note records local AWS profile names and role assumptions for paprnav deployment work. Do not store access keys, secret keys, session tokens, or copied STS credentials in this repo.

## Profiles

Bootstrap profile:

```text
paprnav-bootstrap
```

Expected identity:

```text
arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap
```

Deploy profile:

```text
paprnav-deploy
```

Expected assumed-role identity shape:

```text
arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/...
```

Deploy role ARN:

```text
arn:aws:iam::527257972989:role/paprnav-terraform-deploy
```

## Local Config Shape

`~/.aws/config` should include:

```ini
[profile paprnav-bootstrap]
region = us-east-1
output = json

[profile paprnav-deploy]
role_arn = arn:aws:iam::527257972989:role/paprnav-terraform-deploy
source_profile = paprnav-bootstrap
region = us-east-1
output = json
```

`~/.aws/credentials` should include the `paprnav-bootstrap` access key only:

```ini
[paprnav-bootstrap]
aws_access_key_id = <local secret, do not commit>
aws_secret_access_key = <local secret, do not commit>
```

## Verification Commands

```bash
aws sts get-caller-identity --profile paprnav-bootstrap
aws sts get-caller-identity --profile paprnav-deploy
```

Use `paprnav-deploy` for future Terraform/OpenTofu plan and apply commands:

```bash
AWS_PROFILE=paprnav-deploy terraform plan
```

Do not use `marketer-pipeline-agent` for paprnav deployment work.
