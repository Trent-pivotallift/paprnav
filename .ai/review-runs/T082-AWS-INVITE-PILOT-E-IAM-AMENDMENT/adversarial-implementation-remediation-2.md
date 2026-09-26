# IAM amendment implementation review — remediation 2

## Outcome

**FAIL — mandatory third-loop pause.** IAM-IMPL-001 remains open and
IAM-IMPL-002's source-binding dependency is unresolved. IAM-IMPL-003 is
verified. No AWS mutation is authorized.

## Architecture gap

The saved-plan gate proves that embedded Terraform configuration matches the
reviewed files and that supplied JSON matches `terraform show -json`. It does
not prove that the compiled planned values follow the embedded configuration.
Terraform stores those representations separately.

The reviewer proved this twice:

- Real Terraform 1.15.8 accepted a plan archive whose compiled value was
  `widened-planned-value` after only the embedded configuration was replaced
  with `reviewed-safe-value`; production configuration checks and real
  `terraform show -json` both succeeded.
- In the complete pilot fixture, a planned API inline role policy with
  `Action="*"`, `Resource="*"` still returned
  `pass / eligible-for-M6-review` when the decoder returned that same widened
  plan.

Repeating archive/JSON hashes cannot prove the missing configuration-to-plan
relationship. Implementation must pause until a new independently reviewed
plan-provenance or semantic-binding design is approved.

## Required design decision

Choose one independently reviewed authority:

1. bind trusted plan creation to protected external provenance; or
2. validate the actual planned IAM policies, attachments, role references,
   scopes, conditions, DNS alias and secret transitions from the rendered plan
   against the approved authority.

The coordinator recommends option 2 for the MVP because it checks the security
properties actually crossing the AWS boundary without extending the current
general-purpose simulator.

## Verified closures and positives

- IAM-IMPL-003 success/error contradiction handling passes in preflight and
  both recovery observations.
- Exact generator/baseline binding, forbidden secret-domain overlap,
  Scheduler/Route 53 widening rejection, source override/nested-module stops,
  pagination, quotas, and recovery without deletion pass.
- Direct secret-transition checks pass.
- Bounded IAM wildcard differential: 7,744 pattern pairs; missing/null/empty
  `ForAllValues` checked for both effects.
- Full Package C: 115 passed, 2 skipped; packet freshness and
  `git diff --check` pass; index empty.

## Scope and model routing

The reviewer inspected the full authority, generator, baseline, matrix,
Terraform/runtime policies, tests, callers, amendment and parent execution
evidence. Temporary reproductions stayed under `/private/tmp`; no repository,
Git, Terraform apply, or AWS mutation occurred.

- Reviewer: `/root/t082_e_iam_amendment_impl_review_3`
- Builder: `/root/t082_e_iam_amendment_remediation`
- Requested reviewer model: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Packet SHA-256:
  `9782b2e9a09d5637fd2f9b89e1ebf4f207a4b2b8689ba04ce63734a8cde2c68e`
