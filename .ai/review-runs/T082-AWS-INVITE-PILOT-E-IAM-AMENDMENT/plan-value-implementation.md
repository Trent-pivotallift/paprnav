# IAM plan-value semantic implementation

## Outcome

The no-mutation plan gate now treats rendered `terraform show -json` values as
the authority for the pilot-critical runtime boundary. Configuration/archive
binding remains a drift check, but cannot substitute for the planned values.
This implementation does not publish IAM, plan/apply Terraform, populate
secrets, mutate DNS, or authorize M1/M6.

## Bound semantics

- Plan inputs are exact for `pilot.paprnav.com`, Squarespace zone
  `paprnav.com`, the operator-verified ACM certificate, external mode, account,
  region, and the generated candidate's updater principal. The stale
  `route53_zone_id` input and every planned Route 53 resource are rejected.
- Every ECS/Scheduler assume-role policy, runtime inline policy, ECS managed
  execution-policy attachment, task execution/task role, and Scheduler
  cluster/task/role reference is checked from the planned values. Unknown
  documents/references, wildcard actions, wildcard runtime resources other
  than the reviewed Textract APIs, and unreviewed principals stop.
- The ACM lookup must resolve the exact issued certificate and lookup
  constraints; the HTTPS listener must use that ARN. The external output must
  be the exact Squarespace CNAME handoff with a known ALB DNS value and must
  agree with `planned_values.outputs`.
- The existing three-secret create/tag-only and metadata transition checks,
  saved-plan/JSON identity checks, deferred-change rejection, generator/baseline
  contract, publication state machine, and `mutationAuthorized: false` results
  are retained.
- The executable-authority catalog was refreshed for the current reviewed
  Terraform sources and no longer lists removed Route 53 Terraform types.
- Remediation aligned the generated v5 contract with that boundary: its inputs
  name Squarespace and `paprnav.com`, and its supplement contains no Route 53
  permissions while retaining all four required ACM read actions.

## Focused evidence

Focused tests cover the valid known-value plan plus stale Route 53 input,
certificate drift, unknown/wildcard inline policy, wildcard trust principal,
task-role drift, Scheduler-role drift, unknown DNS output, deferred changes,
and all retained secret-transition negatives. Full verification is recorded in
the task handoff; no live AWS evidence is claimed.

## Model routing

- Builder: `/root/pilot_aws_permissions_sol_audit`
- Model: `gpt-5.6-sol`; effort: `high`
- Trigger: user-requested bounded implementation of an approved IAM
  plan-value invariant with deterministic focused tests.
- No independent review or closure attestation is claimed, per the explicit
  no-adversarial-loop task constraint.
