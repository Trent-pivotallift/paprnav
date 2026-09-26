# Package E independent design review

## Outcome

**FAIL.** Two high-severity prerequisite gaps require explicit remediation
before Package E execution.

## Findings

### E-DESIGN-001 — High — Bootstrap cannot consume the configured RDS-managed secret

E4 must bootstrap the actual RDS deployment through the sealed, fixed-phase
task. `infra/bootstrap/bootstrap.py:83-95` requires `username`, `password`,
`host`, and `port` inside the secret. `infra/terraform/ecs_runtime.tf:42-47`
supplies the RDS-managed secret ARN and database name, but no endpoint or port.
AWS documents that RDS-managed secrets do not include the database endpoint and
port. Invoking `admin_connection` with a realistic `{username,password}` secret
therefore raises `RDS administrator secret is missing required fields`.
Existing tests manufacture host and port inside their fake secret.

Impact: all four bootstrap phases fail before connecting, so the manual cohort
cannot launch. Prior Package C local evidence does not cover this production
contract.

Required closure: add an explicit prelaunch bootstrap/IaC amendment that binds
non-secret endpoint and port to the exact RDS resource while obtaining
credentials only from its managed secret. Add realistic positive and
missing/mismatched-input tests, independent implementation review, and refreshed
image/task evidence. Do not manually rewrite the managed secret or permit
arbitrary overrides.

### E-DESIGN-002 — High — M1 has no viable policy publication path

The IAM prerequisite must be executable within its named updater authority and
accurately describe effective permissions. The decision proposes merging the
baseline and generated supplement, then versioning one existing managed policy.
A compact-JSON calculation using valid placeholder inputs gives 5,011 characters
for the baseline, 3,731 for the supplement, and 8,704 for the merge. AWS limits
each customer-managed policy to 6,144 non-whitespace characters.

Impact: the existing quota gate correctly stops execution, but this is a known
dependency rather than uncertain live evidence. Splitting policies requires
create/attach authority outside the stated version-only updater grant. The
additive merge also retains broad regional `Resource=*` permissions, so it
cannot prove general unrelated-resource denials.

Required closure: choose and independently review a feasible policy layout—a
bounded reduction or separately named supplement attachment—with exact updater
actions and rollback. Retain character counts and effective allow/deny evidence,
and distinguish IAM-enforced restrictions from operator authorization limits.
Wholesale IAM redesign is unnecessary.

## Accepted limitations and boundary

The manual-first milestone is reasonable: inspected upload/API paths enqueue
work without invoking OCR, while the worker remains disabled. Durable
paid-attempt engineering may remain a separate gate. Clean candidate
construction, narrow ECR bootstrap, explicit state-lock authority, zero-first
deployment, live privacy/tenant checks, intentional service-count drift, budget
delivery, isolated restore/S3-version evidence, and session/invite rollback
gates are appropriate.

A/B closure templates remain unresolved release evidence as the decision
acknowledges. Current `HEAD` fails the release verifier solely on the expected
pilot configuration authority change; its working-tree configuration matches
the approved hash. A clean candidate remains mandatory.

Review covered staged, unstaged, and untracked inventory, relevant
infrastructure/IAM/bootstrap, release generators, launchers,
API/worker/storage/auth consumers, tests, and A-D attestations. C/D final
closure artifact hashes verified. No files, Git state, AWS resources, secrets,
or providers were mutated. This was design review, not candidate approval or
deployed-readiness certification.

## Review identity and packet

- Reviewer: `/root/t082_package_e_design_review`
- Role: independent read-only design adversary
- Requested route: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Builder: `/root/t082_package_e_execution_design`
- Builder actual model: `model not exposed by runtime`
- Builder actual effort: `effort not exposed`
- Packet SHA-256:
  `4afc0faaf858a379ce086bac7112bbb492c2c12a9fb58e3008fcee9acc09a4b3`
- All 11 bound review-input hashes matched.

