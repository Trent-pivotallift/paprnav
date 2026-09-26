# Package C read-only AWS preflight

Captured 2026-09-19 in `us-east-1`. No AWS mutation was attempted.

## Identity and existing foundation

- Caller: assumed role `paprnav-terraform-deploy` in account `527257972989`.
- ECR repositories `paprnav/pilot-api` and `paprnav/pilot-frontend` exist,
  currently allow mutable tags, scan on push, and contain zero images.
- ECS cluster `paprnav-pilot` is active with zero services, running tasks, or
  pending tasks.
- No RDS instance whose identifier begins with `paprnav-pilot` exists.

## Authority/prerequisite results

- `acm:ListCertificates`: denied by the current deploy policy.
- `wafv2:ListWebACLs`: denied by the current deploy policy.
- `route53:ListHostedZones`: denied by the current deploy policy.
- `AWSServiceRoleForRDS`: absent.
- `AWSServiceRoleForECS`: absent.
- `AWSServiceRoleForElasticLoadBalancing`: absent.
- The checked-in deploy policy does not grant
  `iam:CreateServiceLinkedRole`.

## Consequence

Package C may design, implement, validate, build locally, and produce a bounded
plan, but Package E may not apply until an independently reviewed least-
privilege policy prerequisite is applied by the bootstrap identity and the
inventory is refreshed. The pilot hostname/hosted-zone choice and real budget
recipient are also required before an execution-ready plan.
