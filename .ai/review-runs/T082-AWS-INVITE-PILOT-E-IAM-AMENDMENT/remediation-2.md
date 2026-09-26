# IAM amendment implementation remediation 2

## Complete pass invariant

The previous pass predicate proved positive samples without binding policy or
plan construction. It is replaced by one conjunctive invariant: pass requires
the exact reviewed policy construction and baseline, IAM-correct supported
matching, no possible forbidden secret grant, the entire reviewed Terraform
configuration embedded in the exact saved plan, agreement with that binary's
own JSON rendering, safe secret transitions, and internally consistent IAM
observations. Unsupported or contradictory evidence stops. No mutation mode
exists; pass is eligibility for the separately authorized operator review.

## Changes and dispositions

- **IAM-IMPL-001:** `policy_contract()` pins the generator source and baseline
  and regenerates the complete expected document from validated inputs. Any
  action/resource/operator/condition/metadata change stops. A product automaton
  proves IAM `*`/`?` inclusion and intersection; brackets remain literal.
  `forbidden_secret_overlap()` rejects every Allow that could overlap
  `/paprnav/pilot/*` for an excluded action, including exact suffixes and
  conditional grants. Deny does not excuse a forbidden grant. ForAllValues
  missing/null/empty context evaluates true for both effects. Unsupported
  condition operators and policy variables stop.
- **IAM-IMPL-002 dependency:** the source loader rejects all `.tf.json` and
  override inputs. `plan_gate()` requires the saved binary, checks every
  embedded configuration file and module against reviewed source, calls
  read-only `terraform show -json` on that same binary, and compares the JSON.
  It also rejects binary changes during verification. Pure transition checks
  return `checks-pass / saved-plan-binding-required`, never an approval pass.
  Parent E3/M6 and the matrix now require the exact extended command and hashes.
- **IAM-IMPL-003:** any non-null `getPolicyError` alongside policy success
  metadata stops both preflight and either recovery observation. This includes
  AccessDenied, NoSuchEntity, other errors and malformed false/empty error data.

All three implementation findings are fixed pending independent verification.
The independent reviewer must assess the whole predicate, not only regressions.

## Verification

- Full Package C: **115 passed, 2 skipped, 81 warnings** with
  `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_pilot_package_c.py -q --disable-warnings`.
- Exact reviewer counterexamples and their classes are production-function
  tests: `ZZZZZZ` secret suffix/conditional grants, Scheduler `*`, Route 53
  StringEquals weakening/removal, literal `[r]`, missing-context ForAllValues
  Deny, JSON/HCL overrides, widened inline-policy JSON mismatch, and all
  success/error preflight/recovery contradictions.
- CLI tests exercise all four commands. The positive plan CLI smoke test stubs
  only the external Terraform decoder; archive/configuration and JSON binding
  run in production. This is synthetic evidence, not a live pilot plan.
- A real local-only Terraform 1.15.8 `terraform_data` plan confirmed the archive
  layout and production `saved_configuration()` reader without any AWS provider,
  remote backend, apply, or resource mutation.
- Compile, JSON parsing and `git diff --check` pass; index remains empty.
  Generator and baseline file hashes remain respectively
  `008f8b5c3ae73b89c09337efb31e3919b4c22d968c36a820f2c85e61de5a9b33` and
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`.

No live MFA, domain, updater, M1, pilot Terraform plan, or execution evidence is
claimed. Trusted Terraform/AWS evidence readers, independent review and the
existing external authorization gates remain required.

## Model routing

- Builder/verifier: `/root/t082_e_iam_amendment_remediation`.
- Actual model: `model not exposed by runtime`; effort: `effort not exposed`.
- Trigger: second substantive implementation failure; whole-invariant repair
  under the mandatory Astra escalation policy, with independent review retained.
- No self-attestation of implementation review or closure.
