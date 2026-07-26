# paprnav AWS Pilot Terraform Planning Loop

Last updated: 2026-06-28

Purpose: plan a controlled AWS volunteer pilot for 10 user-provided aircraft logbook PDF sets, derive the paprnav-specific AWS role/permission boundary needed for Terraform, and avoid applying cloud changes before review.

This is a planning artifact only. Do not treat it as approved infrastructure. Do not run `terraform apply` or AWS write commands from this document without an explicit approval step.

## Inputs From Product Discussion

- Pilot data: PDFs from volunteers or potential customers.
- Pilot offer: 2 months free in exchange for product refinement feedback.
- Data storage assumption: storing logbooks in AWS is acceptable when the owner gives permission.
- Default AWS region: `us-east-1`.
- IaC tool: Terraform.
- Runtime preference: ECS/Fargate for control and production-shaped learning.
- Frontend must be hosted for volunteer access.
- OCR provider: AWS Textract.
- AD ingestion/data parsing is already valuable locally; cloud pilot should focus on real logbook ingestion, OCR, hosted access, and operational learning.
- Payment is not required for the 10-aircraft pilot, but trial entitlement and later conversion should be modeled enough to avoid rewrites.

## Planning Loop Rules

For this pilot, large plans should iterate before implementation:

1. Draft the plan.
2. Critique it against product risk, cost, security, data/privacy, implementation complexity, and what it fails to prove.
3. Revise the plan.
4. Repeat for at least three passes.
5. Produce an implementation checklist only after the third pass.
6. Ask for approval before editing Terraform files, creating AWS resources, or running cloud write commands.

## Current Official Reference Notes

- AWS IAM guidance favors temporary credentials for humans and workloads, MFA, least privilege, regular credential cleanup, policy conditions, and IAM Access Analyzer.
- Terraform S3 backend stores state in S3 and recommends bucket versioning for recovery. The current Terraform S3 backend supports S3 lockfiles; DynamoDB locking is documented as deprecated for future removal.
- ECS task execution role is separate from task IAM role. Execution role lets ECS/Fargate pull images, publish logs, and read referenced secrets; application AWS access belongs in task roles.

References:

- https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- https://developer.hashicorp.com/terraform/language/backend/s3
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html

## Pass 1: Broad Draft

Initial architecture:

- Hosted Next.js frontend on ECS/Fargate behind an ALB.
- FastAPI backend on ECS/Fargate behind the same ALB.
- Worker task definition for OCR/logbook ingestion, run on demand at first.
- S3 bucket for volunteer PDF uploads and derived OCR artifacts.
- RDS PostgreSQL for application state.
- Secrets Manager or SSM Parameter Store for database URL, session secret, OCR/provider settings, and future LLM keys.
- CloudWatch log groups for frontend, backend, and worker containers.
- ECR repositories for frontend and backend images.
- Textract permissions for OCR worker only.
- AWS Budgets and alerts for pilot cost ceiling.
- Terraform remote state in S3 with locking.

Initial identity model:

- Do not use `marketer-pipeline-agent` for paprnav.
- Create a paprnav-specific bootstrap identity to establish state storage and deploy role.
- Use a `paprnav-terraform-deploy` role for Terraform plan/apply.
- Use ECS task execution role for image pulls/logs/secrets.
- Use distinct ECS task roles for backend and worker application permissions.

Critique:

- This plan is too broad to permission safely without sharper resource boundaries.
- Creating VPC, ECS, RDS, IAM, ECR, S3, ALB, logs, secrets, budgets, and Textract permissions requires broad AWS actions.
- A single deploy role can drift toward admin if not constrained by naming, tags, and account/region guardrails.
- NAT Gateway can quietly dominate pilot costs.
- A custom domain and certificate are useful but not necessary for the first volunteer ingestion learning.
- Payment should not block the pilot, but trial entitlement and consent should be represented in product state.
- The first pilot does not need HA/multi-region claims.

Pass 1 revision target:

- Keep production-shaped services where they answer pilot questions.
- Strip anything that does not help 1 -> 3 -> 10 aircraft ingestion learning.
- Derive identity in phases: bootstrap, plan/apply, runtime.

## Pass 2: Tighter Pilot Scope

Revised architecture:

- One AWS account, one region: `us-east-1`.
- One environment name: `pilot`.
- ALB DNS name for access; no Route 53, custom domain, or ACM certificate in the first Terraform pass.
- One VPC for paprnav pilot, with two AZs.
- Public ALB.
- ECS/Fargate frontend service.
- ECS/Fargate backend service.
- ECS/Fargate worker task definition, manually triggered or run by an operator command at first.
- RDS PostgreSQL single instance, no Multi-AZ for the first pilot unless risk tolerance changes.
- S3 bucket with server-side encryption, block public access, versioning enabled, and lifecycle rules drafted.
- ECR repositories for images.
- Secrets Manager for session secret and database credentials.
- CloudWatch log groups with retention configured.
- Textract permissions only on the worker task role.
- AWS Budget at hard planning ceiling.

Budget guardrails:

- Comfort target: `$100-$150/month`.
- Hard planning ceiling: `$300/month`.
- Initial page cap: 2,000 total pages across all volunteers.
- Alerts: 50%, 80%, 100% of monthly budget.
- Rollout gate: 1 aircraft first, then 3, then 10.

Critique:

- A new VPC is cleaner and safer to delete, but requires broader EC2 permissions than default VPC use.
- Running both frontend and backend as always-on ECS services plus ALB and RDS may exceed comfort budget before Textract does.
- Without NAT Gateway, private ECS tasks have harder image/secrets access unless VPC endpoints are added. With NAT Gateway, costs rise.
- Public ECS tasks are simpler but less production-shaped and need careful security groups.
- RDS database credentials and application migrations need a clear operational story.
- Terraform state bootstrapping still needs a write identity before the deploy role exists.

Pass 2 revision target:

- Choose network shape explicitly.
- Separate plan-time permissions from apply-time permissions.
- Identify which permissions can be delayed until the second Terraform phase.

## Pass 3: Final Planning Position

Recommended pilot architecture:

- New `paprnav-pilot` VPC in `us-east-1`.
- Two public subnets for ALB.
- Two private subnets for backend/frontend/worker ECS tasks and RDS if budget allows NAT or required VPC endpoints.
- If cost ceiling is tight, defer NAT Gateway and use a simpler public-subnet ECS pilot with locked-down security groups, then record that as a pilot-only compromise.
- Public ALB serving:
  - frontend listener/rule to Next.js service
  - backend listener/rule or path routing to FastAPI service
- ECS/Fargate services:
  - `paprnav-pilot-frontend`
  - `paprnav-pilot-api`
- ECS/Fargate task definition, not always-on service:
  - `paprnav-pilot-worker`
- ECR:
  - `paprnav/pilot-frontend`
  - `paprnav/pilot-api`
- RDS PostgreSQL:
  - single instance
  - deletion protection disabled only if teardown speed is more important than data safety; otherwise enabled and documented
  - automated backups enabled for pilot data
- S3:
  - encrypted bucket for volunteer PDFs, original uploads, OCR artifacts, and AD source artifacts
  - block public access
  - versioning enabled
  - lifecycle rules for temporary derived artifacts
- Secrets Manager:
  - database credentials
  - session secret
  - future provider API keys
- CloudWatch:
  - frontend/backend/worker log groups
  - retention set explicitly
- AWS Budget:
  - monthly cost budget with alerts at 50/80/100 percent
- Textract:
  - worker task role can call Textract APIs needed by selected OCR mode
  - no Textract permission in frontend or backend task roles unless a backend route starts jobs directly

Cost attribution note:

- S3 object tags should be treated as paprnav metadata/reconciliation tags, not as per-customer AWS Cost Explorer dimensions.
- Textract OCR spend is not attributable per customer through AWS request tags. The pilot billing model must use paprnav application records (`OCRRun.billable_page_count`, billable account tag, aircraft tag, and billing status) for customer/account OCR chargeback.
- Onboarding OCR measurement must be implemented as a product-metering/reporting feature before enabling real volunteer Textract at pilot scale.
- The minimum billing report should group by customer account tag and aircraft tag, then show upload count, OCR run count, billable page count, provider, billing status, estimated OCR cost, and date range.
- The first estimate can use a configured Textract per-page unit price for `DetectDocumentText` or async text detection. Persist the provider/API mode used so later AnalyzeDocument or feature-specific pricing does not get mixed into the same bucket.
- AWS Budget remains the overall account/project guardrail; paprnav billing summaries are the customer/account attribution source of truth.

What this proves:

- Volunteers can reach a hosted frontend.
- User-provided PDFs can be uploaded and retained in S3.
- Real Textract output can drive the existing OCR/logbook ingestion loop.
- Worker sizing, PDF/page constraints, OCR confidence, review burden, and per-aircraft cost can be measured.
- Per-customer onboarding OCR work can be measured from app-side billing records before asking AWS Cost Explorer for aggregate project cost.
- The product can gather learnings across 1, then 3, then 10 aircraft.

What this does not prove:

- Full production compliance posture.
- Payment/conversion workflow.
- Enterprise identity or fine-grained admin workflows.
- Multi-region/high-availability behavior.
- Complete AD historical coverage.
- Fully automated CI/CD deployment.
- Long-term least-privilege IAM refinement.

## Identity And Role Boundary

Do not use:

- `arn:aws:iam::527257972989:user/marketer-pipeline-agent`

Recommended identities:

### Bootstrap Identity

Name: `paprnav-terraform-bootstrap`

Purpose:

- Initial setup only.
- Create Terraform state bucket and lockfile/state access path.
- Create the deploy role and initial policies.
- Ideally disabled or removed after deploy role/OIDC is working.

Preferred shape:

- IAM Identity Center permission set or human-assumed role.
- If a temporary IAM user is used for speed, require MFA, rotate/delete keys after bootstrap, and restrict use to `us-east-1` where possible.

Bootstrap write scope:

- IAM role/policy creation for paprnav deploy and runtime roles.
- S3 state bucket creation/configuration.
- Optional KMS key if customer-managed encryption is selected.
- No application runtime resources unless the first Terraform pass deliberately combines bootstrap and app resources.

### Terraform Deploy Role

Name: `paprnav-terraform-deploy`

Purpose:

- Run `terraform plan` and, after explicit approval, `terraform apply` for paprnav pilot resources.

Trust:

- Initially assumable by the paprnav bootstrap/human operator.
- Later assumable by GitHub OIDC for a protected branch/environment.

Plan-time read scope:

- STS caller identity and account metadata.
- IAM read for paprnav roles/policies.
- EC2/VPC/Subnet/SecurityGroup read.
- ECS/ECR/ELBv2/RDS/S3/Secrets Manager/CloudWatch Logs/Budgets read.
- Textract read is minimal; service capability is mostly needed at runtime.
- S3 state access: list bucket, get/put state object, get/put/delete lockfile if using S3 locking.

Apply-time write scope:

- Create/update/delete paprnav-prefixed/tagged VPC, subnets, route tables, internet gateway, security groups, ALB, target groups, listeners.
- Create/update/delete paprnav ECR repos, ECS clusters, task definitions, services, and log groups.
- Create/update/delete paprnav RDS subnet group, instance, parameter/security group attachments.
- Create/update/delete paprnav S3 app bucket and object lifecycle/encryption/public-access settings.
- Create/update/delete paprnav Secrets Manager secrets and secret versions as needed.
- Create/update/delete paprnav IAM roles and policies for ECS task execution, backend task, worker task, and future GitHub OIDC.
- Create/update/delete paprnav AWS Budget alerts.

Guardrails:

- Region guardrail: `us-east-1`.
- Naming/tag guardrail: resources must be named or tagged with `Project=paprnav` and `Environment=pilot`.
- Avoid wildcard IAM permissions without a documented reason.
- Validate policy with IAM Access Analyzer before broadening permissions.
- Store Terraform state in S3 with versioning and S3 lockfile support; do not put credentials in backend config or plan files.

### ECS Runtime Roles

Execution role:

- Name: `paprnav-pilot-ecs-execution-role`.
- Used by ECS/Fargate agent for pulling ECR images, writing CloudWatch logs, and resolving referenced secrets.
- Application code should not depend on this role for AWS service calls.

Backend task role:

- Name: `paprnav-pilot-api-task-role`.
- Minimal app access:
  - read required secrets/parameters
  - read/write app S3 objects only if backend handles uploads/downloads directly
  - no Textract unless backend initiates Textract jobs directly

Worker task role:

- Name: `paprnav-pilot-worker-task-role`.
- Minimal worker access:
  - read/write pilot S3 artifacts
  - call selected Textract APIs
  - read required secrets/parameters
  - no IAM mutation, no Terraform/state access

Frontend task role:

- Name: `paprnav-pilot-frontend-task-role`.
- Usually no AWS data-plane permissions beyond reading required runtime configuration/secrets if needed.

## Implementation Checklist After Approval

Do not start this checklist until the planning loop is approved.

1. Create `infra/terraform` skeleton.
2. Add provider/backend placeholders with `allowed_account_ids = ["527257972989"]`.
3. Add variables for region, environment, project, cost ceiling, page cap, and image tags.
4. Add tags/locals enforcing `Project=paprnav`, `Environment=pilot`.
5. Add state bootstrap notes or separate bootstrap module.
6. Add VPC/network module.
7. Add S3 app bucket module.
8. Add ECR module.
9. Add Secrets Manager module.
10. Add RDS module.
11. Add ECS cluster/task/service module.
12. Add ALB module.
13. Add CloudWatch logs module.
14. Add budget module.
15. Add IAM roles/policies with explicit runtime separation.
16. Run `terraform fmt`.
17. Run `terraform validate`.
18. Run `terraform plan`.
19. Review plan, estimated cost, IAM policy breadth, and teardown path.
20. Ask for explicit approval before `terraform apply`.

## Open Questions Before Terraform Files

- Should first pilot use private ECS tasks with NAT/VPC endpoints, or public ECS tasks with tighter security groups to keep cost down?
- Should RDS deletion protection be enabled for volunteer data even in pilot?
- Should uploaded volunteer PDFs use S3 Object Lock, or is versioning plus backups enough for the pilot?
- Should the frontend/backend use one ALB with path routing or separate listeners/services?
- Should we host a custom domain in the first pilot, or use the ALB DNS name until ingestion learning proves value?
- Should Textract use plain text detection first, or AnalyzeDocument features where useful despite higher cost?
- What is the maximum page count per volunteer aircraft before manual approval?
- What exact consent language is required before upload?
- Should payment remain deferred, or should trial entitlement fields be added before volunteer onboarding?
- What email should receive AWS Budget notifications before volunteers or real Textract usage begin?
- What Textract unit price should the pilot use for app-side OCR cost estimates in `us-east-1`?

## Recommended Next Goal

After review:

```text
Implement the paprnav OCR billing summary slice before enabling real volunteer Textract at pilot scale. Use existing Upload and OCRRun billing fields as the source of truth, add a backend summary endpoint grouped by customer account and aircraft, include estimated OCR cost from configured provider/API unit pricing, document that AWS Cost Explorer is aggregate-only for Textract, and test the summary with multiple customers/aircraft/statuses. Then add the AWS Budget notification email and proceed to async S3-backed Textract.
```
