# IAM plan-authority architecture pause

## Missing invariant

A reviewed Terraform configuration and a rendered saved plan are independent
representations. Matching the plan archive's embedded configuration to source
does not prove that the compiled planned IAM values were produced from that
configuration.

## Recommended MVP authority

Retain the exact generator/baseline contract, IAM semantics, publication state
machine and secret transition checks that passed review. Replace the claim that
configuration binding proves runtime IAM safety with a bounded semantic
validator over the actual `terraform show -json` planned values.

The validator should cover only pilot-critical authorization outputs:

- every `aws_iam_role_policy` JSON document;
- every managed-policy attachment and execution/task/scheduler role reference;
- every task definition's execution/task role pairing;
- the Scheduler target role, cluster and task definition;
- the exact Route 53 A alias and hosted zone;
- the three secret resources and their transition actions;
- absence of wildcard runtime policies, unreviewed principals, and deferred
  service permissions; and
- exact generated supplement hash/structure outside Terraform.

Unknown planned values stop. Tests must use real `terraform show -json` output
with contradictory embedded configuration and widened planned policies. This is
a narrow release gate, not a general Terraform or IAM simulator.

## Alternative not recommended

Protected external plan provenance could establish who created an immutable
plan, but it introduces CI/signing infrastructure not currently on the 30-day
pilot critical path. It may be added after the invite-only pilot.

## Resume gate

Implementation resumes only after independent Astra design review approves the
bounded planned-value semantic authority. A third local patch to the current
configuration-binding claim is prohibited.

## Model routing

- Coordinator/architecture author: `/root`
- Actual model: `model not exposed by runtime`; effort: `effort not exposed`
- Trigger: third unsuccessful IAM oracle loop; implementation paused for an
  explicit invariant and architecture decision.
