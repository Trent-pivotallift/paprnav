# IAM amendment implementation review — remediation 1

## Outcome

**FAIL.** IAM-IMPL-001 and IAM-IMPL-003 remain open. IAM-IMPL-002's direct
secret transition checks pass, but its source/coverage dependency is not yet a
sound authority. No AWS mutation is authorized.

## Findings

### IAM-IMPL-001 — still open

The evaluator permits four counterexample classes:

1. Excluded secret actions are sampled at one ARN suffix and a whole-wildcard
   check is incorrectly used as proof that no overlapping grant exists.
2. Scheduler `Resource="*"` and weakened Route 53 conditions satisfy positive
   coverage even though they violate least privilege.
3. Python shell matching accepts bracket character classes that IAM does not,
   and missing-context `ForAllValues` handling is incorrect for Deny statements.
4. Terraform `.tf.json` overrides are neither bound nor rejected; an override
   can widen a runtime inline policy while coverage and the secret-focused plan
   gate still pass.

Required closure: bind the exact reviewed policy construction and every
Terraform configuration input; use IAM-specific wildcard and effect-correct
condition semantics or stop on unsupported syntax; prove forbidden-domain
non-overlap; reject scope/condition widening; and bind each plan to the reviewed
configuration.

### IAM-IMPL-003 — still open

Publication accepts successful existing-policy metadata together with
`getPolicyError=AccessDenied` or `NoSuchEntity`, then proposes a new version.
Stale success plus contradictory failure evidence must never pass.

Required closure: require mutually exclusive success/error states in preflight
and recovery and reject every contradictory observation.

## Verified positives

- Current generator scopes remain sound and the baseline digest is unchanged.
- Ordinary Deny precedence, direct secret transition rejection,
  pagination/marker validation, consumer/boundary/quota rejection, and observed
  rollback without deletion work for the tested inputs.
- Parent M1/E3/M6 commands invoke the production functions.
- Full Package C: 85 passed, 2 skipped; `git diff --check` and packet freshness
  passed.

## Scope and model routing

The reviewer inspected the dirty inventory, amendment and parent execution
artifacts, full evaluator/generator/matrix, Terraform/runtime IAM files, tests,
and callers. The override proof was confined to a temporary directory. No
repository, Git, or AWS mutation occurred.

- Reviewer: `/root/t082_e_iam_amendment_impl_review_2`
- Builder: `/root/t082_e_iam_amendment_remediation`
- Requested reviewer model: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Packet SHA-256:
  `b130818fffba9e7dc0dbbc7fc372d487b22d33f11d0c233827e31dc80693b33b`
