# paprnav Terraform Pilot

This directory contains the first Terraform/OpenTofu slice for the paprnav AWS pilot.

Current scope:

- AWS provider configured for profile `paprnav-deploy`.
- Default tags for paprnav cost and ownership tracking.
- S3 bucket for volunteer uploads and OCR/AD artifacts.
- S3 backend for shared Terraform remote state and S3 lockfiles.
- ECR repositories for API and frontend images.
- CloudWatch log groups for API, frontend, and worker.
- ECS cluster foundation.
- Monthly AWS Budget with optional email notifications.
- Runtime skeleton for VPC, ALB, RDS, ECS task definitions/services, runtime IAM roles, and app secrets.

The runtime skeleton intentionally keeps ECS service desired counts at `0` until API/frontend images are built, pushed, secrets are populated, and migrations are ready.

## Applied Foundation

Applied on 2026-07-07 through the Dockerized HashiCorp Terraform CLI using profile `paprnav-deploy`.

Terraform provider lock:

- `hashicorp/aws v5.100.0`

Created resources:

- S3 artifacts bucket: `paprnav-pilot-artifacts-527257972989`
- S3 Terraform state bucket: `paprnav-pilot-terraform-state-527257972989`
- ECR API repository: `527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api`
- ECR frontend repository: `527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-frontend`
- ECS cluster: `paprnav-pilot`
- CloudWatch log groups:
  - `/paprnav/pilot/api`
  - `/paprnav/pilot/frontend`
  - `/paprnav/pilot/worker`
- AWS monthly budget: `paprnav-pilot-monthly`

Applied hardening on 2026-07-10:

- Migrated Terraform state to S3 backend with native S3 lockfile support.
- Updated app artifacts bucket lifecycle:
  - old object versions expire after 90 days
  - incomplete multipart uploads abort after 7 days
  - current `tmp/` artifacts expire after 30 days

Final verification:

```text
No changes. Your infrastructure matches the configuration.
```

Remote state:

- Backend bucket: `paprnav-pilot-terraform-state-527257972989`
- Backend key: `pilot/terraform.tfstate`
- Locking: S3 lockfile at `pilot/terraform.tfstate.tflock`

`terraform.tfstate`, `terraform.tfstate.backup`, and `.terraform/` remain local-only and ignored by git. After backend migration, Terraform uses the S3 state object.

## Runtime Skeleton Plan

Added in the current working tree:

- VPC `paprnav-pilot` with two public subnets and two private database subnets.
- Public HTTP ALB with frontend default target group and FastAPI path routing.
- ECS task definitions for API, frontend, and worker.
- ECS services for API and frontend with desired counts defaulting to `0`.
- Disabled EventBridge Scheduler schedule for the OCR worker Fargate task.
- Runtime IAM roles:
  - ECS execution role
  - API task role
  - frontend task role
  - worker task role with Textract permissions
- RDS PostgreSQL single instance with encrypted storage, AWS-managed master password, backups, and deletion protection enabled by default.
- Secrets Manager placeholders for `DATABASE_URL` and app session secret.

Validation:

```text
terraform validate -no-color
Success! The configuration is valid.
```

Plan result:

```text
Plan: 37 to add, 0 to change, 0 to destroy.
```

Container status:

- ECR repositories exist.
- `aws ecr describe-images` returned `[]` for both `paprnav/pilot-api` and `paprnav/pilot-frontend`.
- `backend/Dockerfile` exists.
- No frontend Dockerfile exists yet.
- Do not raise desired counts above `0` until images are built/pushed and runtime secrets are populated.
- Do not enable the worker schedule until images, secrets, and async/S3 Textract behavior are ready.
- The HTTP ALB is for initial runtime smoke only. Add ACM/HTTPS before external volunteers use the app.

Routing notes:

- The ALB forwards FastAPI-owned paths (`/api/v1/*`, `/health`, `/version`) to the API target group.
- Other paths go to the frontend target group, including the local-style Next proxy path `/api/backend/*`.
- `PAPRNAV_BACKEND_URL` is a runtime server-side frontend env var and points to the ALB root.
- `NEXT_PUBLIC_PAPRNAV_API_BASE_URL` is build-time for Next.js. The frontend Dockerfile must set it during `next build`; setting it only in the ECS task runtime environment will not change the browser bundle.

Secret runbook notes:

- RDS uses `manage_master_user_password = true`; AWS stores the DB password in the managed RDS master user secret.
- Terraform creates placeholder app secrets for `DATABASE_URL` and session secret but does not write secret values into state.
- Before starting ECS tasks, populate:
  - `/paprnav/pilot/database-url`
  - `/paprnav/pilot/session-secret`
- If the RDS managed password rotates, refresh the app `DATABASE_URL` secret or replace this placeholder approach with rotation-aware automation.

## Verify Identity

```bash
aws sts get-caller-identity --profile paprnav-deploy
```

Expected ARN shape:

```text
arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/...
```

## Plan

Terraform CLI version:

- Required: `>= 1.11.0`
- Reason: the S3 backend uses `use_lockfile = true` for native S3 state locking.

Terraform is not installed on the host. The current verified path uses Docker or the temporary CLI noted in `.ai/AWS_DEPLOYMENT_STATUS.md`:

```bash
cd infra/terraform
docker run --rm -v /Users/hostiletakeover/Projects/paprnav:/workspace -w /workspace/infra/terraform hashicorp/terraform:latest init -input=false
docker run --rm -v /Users/hostiletakeover/Projects/paprnav:/workspace -w /workspace/infra/terraform hashicorp/terraform:latest fmt -check
docker run --rm -v /Users/hostiletakeover/Projects/paprnav:/workspace -w /workspace/infra/terraform hashicorp/terraform:latest validate
docker run --rm -e AWS_PROFILE=paprnav-deploy -e AWS_SDK_LOAD_CONFIG=1 -v /Users/hostiletakeover/.aws:/root/.aws:ro -v /Users/hostiletakeover/Projects/paprnav:/workspace -w /workspace/infra/terraform hashicorp/terraform:latest plan -input=false -no-color
```

If local state exists and the backend is newly configured, migrate once:

```bash
docker run --rm -e AWS_PROFILE=paprnav-deploy -e AWS_SDK_LOAD_CONFIG=1 -v /Users/hostiletakeover/.aws:/root/.aws:ro -v /Users/hostiletakeover/Projects/paprnav:/workspace -w /workspace/infra/terraform hashicorp/terraform:latest init -migrate-state -input=false
```

To enable budget email notifications:

```bash
terraform plan -var='budget_notification_email=you@example.com'
```

The applied pilot budget currently has no notification subscribers when this value is left empty. Add a real notification email before inviting volunteers or running Textract at pilot scale.

Do not run `terraform apply` until the plan, expected monthly cost, tags, and teardown posture are reviewed.
