# IAM amendment implementation remediation 1

## Outcome

IAM-IMPL-001..003 are fixed pending independent verification. The implementation
adds one offline production authority, `scripts/pilot_iam_authority.py`, used by
the operator execution contract and by tests. It has no AWS SDK/client, mutation
mode, credential access, or apply command. No AWS or Git mutation occurred.

## Invariant closure evidence

- **IAM-IMPL-001:** `coverage()` expands 83 managed AWS instances, three AWS data
  instances and 12 explicitly local instances from the source-bound graph. Its
  pinned provider 5.100.0 catalog produces 751 action/resource/context decisions,
  including three `UpdateSecret` stops. Requirements use concrete IAM action
  names, not service wildcards. Terminal ARN scopes cover all AWS-assigned IDs;
  an exact fabricated example cannot satisfy the scope. `allowed()` evaluates
  the actual baseline/supplement, conditions and Deny precedence. Unsupported
  syntax and source drift stop. `runtime_boundary()` inspects actual HCL policy
  documents; source hashes bind role attachments, trust and task references.
- **IAM-IMPL-002:** `plan_gate()` requires the three exact secret addresses and
  current names, complete full graph and known authority inputs. It permits
  create and tag-only/no-op secret transitions, rejects description/KMS updates,
  unknown inputs, legacy ARN/name drift, omissions and mixed unsafe plans before
  any apply. Only provider-computed create outputs may be unknown. Parent E3/M6
  now requires the exact CLI gate and binds the JSON export to the saved plan.
- **IAM-IMPL-003:** `pages()`, `snapshot()` and `publication()` validate request
  marker chains for both entity usage filters, role attachments and versions;
  reject missing/later-page/shared/boundary/quota states; preserve baseline
  attachment; and derive absent/detached/attached publication steps. Recovery
  uses fresh observed state, verifies prior version hashes/policy identity,
  restores prior default/attachment and returns residual artifacts without
  deletion. Parent M1 invokes these same CLI functions after every ambiguous
  call, with serialized execution and fresh snapshots.

## Verification

- Full Package C: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_pilot_package_c.py -q --disable-warnings`
  → **85 passed, 2 skipped, 81 warnings**. Existing skips are the unavailable
  Terraform WAF mock-plan JSON and unset disposable PostgreSQL URL.
- Production-function mutations cover missing action, wrong resource/condition,
  deploy secret-value widening, runtime/source drift, secret plan changes and
  unknowns, both paginated consumer filters, all publication branches, quota
  failures, ambiguous create/version/default/attach and lost attachment recovery.
- Subprocess CLI checks cover all four commands, incomplete plan input and
  missing observed recovery state, including stop exit code 2 and JSON output.
- Python compile, matrix/baseline JSON parsing, and `git diff --check`: pass.
- Baseline file SHA-256 remains
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`.
  Generator and policy sizes remain unchanged. Git index remains empty.

The catalog is a bounded static oracle for reviewed source, not a general IAM
simulator or proof of live organization/session-policy effects. Provider calls
newly exposed by a live plan return through review. No live MFA, domain, updater,
M1, Access Analyzer, effective-policy simulation, plan or execution evidence is
claimed. Independent implementation/closure review remains mandatory.

Primary references checked: [provider secret lifecycle](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v5.100.0/internal/service/secretsmanager/secret.go),
[provider Scheduler lifecycle](https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v5.100.0/internal/service/scheduler/schedule.go),
[IAM entity pagination](https://docs.aws.amazon.com/IAM/latest/APIReference/API_ListEntitiesForPolicy.html),
[Budget IAM action mapping](https://docs.aws.amazon.com/service-authorization/latest/reference/list_budgets.html).

## Model routing

- Builder: `/root/t082_e_iam_amendment_remediation`.
- Actual model: `model not exposed by runtime`; effort: `effort not exposed`.
- Trigger: first substantive implementation failure in IAM authorization,
  missing shared oracle and ambiguous rollback; preferred Astra xhigh.
- Role phases: remediation builder and focused verifier. No independent review
  or closure is asserted by this builder; coordinator assigns the reviewer.
