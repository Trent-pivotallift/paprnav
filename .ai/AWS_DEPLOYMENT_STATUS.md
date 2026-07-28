# paprnav AWS Deployment Status

Last updated: 2026-07-10

## Verified Identity

Local deploy profile:

```text
paprnav-deploy
```

Verified identity:

```text
arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/...
```

## Foundation Applied

Terraform foundation under `infra/terraform` was applied with Dockerized Terraform.

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

Current budget caveat:

- The budget exists, but `budget_notification_email` is empty, so no AWS Budget alert subscribers are configured yet.
- Add a real alert email before inviting volunteers or enabling Textract for pilot-scale OCR.

Final Terraform verification after S3 backend migration:

```text
No changes. Your infrastructure matches the configuration.
```

## Terraform Remote State

Terraform state has been migrated from local state into the S3 backend.

Backend:

```text
s3://paprnav-pilot-terraform-state-527257972989/pilot/terraform.tfstate
```

Verification:

- `terraform init -migrate-state -force-copy -input=false` completed successfully with Terraform `1.15.8`.
- `aws s3api head-object` found the state object at `2026-07-10T00:43:06+00:00`, encrypted with `AES256`.
- Post-migration `terraform plan -input=false -no-color` returned no changes.
- Terraform now requires CLI `>= 1.11.0` because the S3 backend uses `use_lockfile = true`.

## IAM Updates During Apply

The initial deploy policy was missing S3 read actions required by the Terraform AWS provider while refreshing S3 bucket state.

Added to `infra/aws-iam/paprnav-terraform-deploy-policy.json` and applied to the AWS managed policy:

- `s3:GetAccelerateConfiguration`
- `s3:GetReplicationConfiguration`

Current managed policy default version after the initial Terraform loop:

```text
v3
```

Claude review on 2026-07-10 flagged the KMS statement in the deploy policy as too broad because destructive KMS actions were granted on `Resource="*"`. The policy in `infra/aws-iam/paprnav-terraform-deploy-policy.json` was split so KMS key mutation/deletion requires paprnav resource tags or paprnav aliases. IAM Access Analyzer returned one S3 wildcard suggestion and no blocking findings.

Live managed policy updates:

```text
arn:aws:iam::527257972989:policy/paprnav-terraform-deploy
DefaultVersionId=v4
DefaultVersionId=v5
```

Version `v5` additionally removes the unconditional `iam:PassRole` from the general IAM management statement so role passing is only allowed by the service-conditioned statement.

## OCR Tooling

Textract OCR adapter added behind the existing OCR provider abstraction.

Environment gate:

```text
PAPRNAV_OCR_PROVIDER=textract
```

Default remains deterministic OCR for local demo and CI.

Current Textract mode:

- Uses `DetectDocumentText`.
- Maps Textract `LINE` and `WORD` Blocks into paprnav OCR spans.
- Preserves confidence, ratio bounding boxes, provider block IDs, and relationships.
- Supports local-file input for the current local storage path and S3-object references for future S3-backed uploads.

Important limitation:

- Production volunteer PDF ingestion should move to S3-backed asynchronous Textract `StartDocumentTextDetection` before broad use.

## S3 Upload Storage

The backend now supports env-gated S3 upload storage.

```text
PAPRNAV_STORAGE_BACKEND=s3
PAPRNAV_S3_UPLOAD_BUCKET=paprnav-pilot-artifacts-527257972989
PAPRNAV_S3_UPLOAD_PREFIX=uploads
```

Behavior:

- Local storage remains the default for development and CI.
- S3 upload objects are written with `AES256` server-side encryption.
- S3 upload objects receive the existing non-sensitive paprnav metadata/reconciliation tags: project, environment, application, customer account, aircraft, upload, billable account, and billing stage.
- S3 download support streams the object back through the authenticated download endpoint.
- Uploads require server-side pilot consent before storage and ingestion are created.

Billing note:

- S3 object tags are retained for paprnav metadata/reconciliation, not as a per-customer AWS Cost Explorer dimension.
- Textract API charges are not tagged per request by AWS; per-customer OCR billing must use paprnav's app-side `OCRRun.billable_page_count`, billable account tag, aircraft tag, and billing status.
- Customer onboarding OCR measurement is implemented at
  `GET /api/v1/admin/ocr-billing` from app-side OCR run records. It groups by
  billable account and aircraft tags; separates chargeable and non-billable
  pages and estimated cost; and reports upload/run counts, provider/API mode,
  and filterable date ranges. AWS Budget remains the aggregate project
  guardrail.

## S3 Lifecycle Hardening

Applied on 2026-07-10:

- Added lifecycle rule `retain-current-uploads-expire-old-versions` to expire noncurrent versions after 90 days across the artifacts bucket.
- Added incomplete multipart upload abort after 7 days.
- Preserved `tmp/` current-object expiration after 30 days.

Terraform apply result:

```text
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

Post-apply verification:

```text
No changes. Your infrastructure matches the configuration.
```

## Next Deployment Loop

Runtime skeleton has been added to the Terraform working tree but not applied.

Plan verification:

```text
terraform validate -no-color
Success! The configuration is valid.

terraform plan -input=false -no-color
Plan: 37 to add, 0 to change, 0 to destroy.
```

Runtime skeleton includes:

- VPC with two public subnets and two private database subnets.
- Public HTTP ALB with frontend default target group and FastAPI route forwarding for `/api/v1/*`, `/health`, and `/version`.
- RDS PostgreSQL single instance with encrypted storage, AWS-managed master password, backups, and deletion protection enabled by default.
- Secrets Manager placeholders for app `DATABASE_URL` and session secret.
- ECS task definitions for API, frontend, and worker.
- ECS API/frontend services with desired counts defaulting to `0`.
- Disabled EventBridge Scheduler schedule for the worker Fargate task.
- ECS execution, API task, frontend task, and worker task roles.
- Worker task role has Textract permissions.

Container status:

- Existing ECR repositories are empty:
  - `paprnav/pilot-api`: `[]`
  - `paprnav/pilot-frontend`: `[]`
- Backend has `backend/Dockerfile`.
- Frontend has no Dockerfile yet.
- Desired ECS counts should stay `0` until images are built/pushed, secrets are populated, and migrations are ready.
- The worker schedule should stay `DISABLED` until images, secrets, and OCR mode are ready.
- The HTTP ALB is for first runtime smoke only; add ACM/HTTPS before external volunteers use the app.
- `NEXT_PUBLIC_PAPRNAV_API_BASE_URL` must be set at frontend image build time, not only in ECS runtime environment.
- Terraform creates app secret placeholders, but a human or automation still must populate `/paprnav/pilot/database-url` and `/paprnav/pilot/session-secret`.

Recommended next slice:

1. Review the runtime skeleton plan and expected monthly cost before apply.
2. Add a frontend Dockerfile and image build path.
3. Build and push API/frontend images to ECR.
4. Populate runtime Secrets Manager values and run migrations.
5. Apply or re-plan runtime skeleton with desired counts still at `0`, then raise counts after images/secrets are ready.
6. Add AWS Budget notification email and apply the alert subscribers.
7. Move Textract PDF processing to async S3 mode with provider/API mode persisted for pricing.
