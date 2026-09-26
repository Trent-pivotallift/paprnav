# Package C implementation review — FAIL

## Model routing

- Builder runtime identity: `/root/t082_package_c_implementation`.
- Reviewer runtime identity: `/root/t082_pilot_design_adversary`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual builder/reviewer model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: complete infrastructure/IAM/bootstrap implementation review after
  design findings.

## Scope and packet

The reviewer inspected the current changed and untracked Package C
infrastructure, bootstrap, release-context builders, manifests, consumers,
inherited Package A/B evidence, and preserved dirty tree. The reviewed packet
SHA-256 was
`e057acd59751a3e4ab9f9dbfe07e33933f788b6cb3d1bb2fe8e6f81ce08cf295`;
packet-current verification passed for scope fingerprint
`7c8472e1d0b34b3c7ff955e4547e28696f0c5627651765d780548dc2202125c7`.
No repository edit, staging, commit, or cloud mutation occurred during review.

## Findings

### T082-C-007 — High — App-secret producer/consumer mismatch

`infra/bootstrap/bootstrap.py` publishes JSON, but API and worker ECS
configuration in `infra/terraform/ecs_runtime.tf` selects the whole secret
rather than its `DATABASE_URL` key. Passing that JSON to SQLAlchemy reproduced
an `ArgumentError`.

Close by aligning every consumer with the publication format and testing the
actual injected value through application configuration.

### T082-C-008 — High — Valid administrator passwords can prevent migration

`infra/bootstrap/bootstrap.py` percent-encodes reserved characters when
constructing the URL, while `backend/app/db/migrations/env.py` passes that URL
through ConfigParser interpolation without escaping. A password containing
`@` and `%` reproduced `ValueError` before connection.

Close by preserving credentials through this boundary, with bounded
reserved-character regression cases and any necessary reviewed Package A
authority update.

### T082-C-009 — High — Execution gates are warnings, not fail-closed checks

The external-input checks in `infra/terraform/variables.tf` and repository
checks in `infra/terraform/main.tf` use Terraform `check` blocks. Failed check
blocks warn but do not prevent plan or apply.

Close by using blocking validation or preconditions, verifying actual hosted
zone identity, and proving invalid external inputs and wrong image
repositories fail.

### T082-C-010 — High — Encoded auth paths bypass endpoint rate matching

Login and invitation WAF statements in `infra/terraform/load_balancer.tf`
inspect raw paths with transformation `NONE`. FastAPI accepted
`/api/v1/auth/%6cogin` and `/api/v1/auth/invitations/%61ccept`, but neither
matched the corresponding WAF predicate.

Close by aligning edge classification with routed-path semantics, including
encoded and redirect variants, without weakening the upload exception.

### T082-C-011 — High — WAF sampling retains session-bearing headers

WAF sampling is enabled without data protection. Sampled requests retain
header values, including cookies, and ordinary logging redaction does not
protect sampled requests.

Close by disabling sampling or proving effective sensitive-header protection
for every enabled sampling configuration.

### T082-C-012 — High — ACM mutation exceeds approved resource ownership

The generated certificate-management permissions allow tagging and deleting
any certificate in the account and region without the approved resource-tag
restriction.

Close by constraining mutation to reviewed ownership, preventing unrestricted
tagging from manufacturing that ownership, and retaining positive and
negative policy assertions.

### T082-C-013 — High — Release-context authority is incomplete

The API context construction does not invoke Package A's commit/protected-blob
verifier. An in-memory Git-source probe accepted an unrelated commit identifier
and altered protected model/config bytes. Overlay validation also requires
every dirty path while forbidding preserved T081/0030 paths, making the
approved preserved-tree workflow impossible.

Close by enforcing one candidate authority gate, distinguishing explicitly
preserved exclusions from reviewed build inputs, and retaining executable
positive and negative tests.

### T082-C-014 — High — Required local closure evidence is absent

No retained bounded Package C regression suite exercises the new components.
The implementation handoff also defers local image construction and inventory
evidence to operator inputs that are unnecessary for local builds.

Close by retaining bounded bootstrap/concurrency/failure, context, IAM, and
WAF tests and producing the approved three-image local evidence. Live
deployment evidence may remain Package E-owned.

## Disposition and residual gates

C-001, C-003, C-004, and C-005 are not implementation-closed because of the
findings above. C-002's serialized permanent-control implementation appears
consistent, but its reproducible tests are not retained. C-006 routing evidence
is present.

The hostname/zone, budget recipient, authorized updater, KMS identity,
refreshed AWS inventory, and pushed digests remain legitimate execution gates.
The administrator-secret fixture must also establish whether host and port are
supplied by the managed secret or separately by Terraform.

An inadvertently broad Package A test completed before cancellation (292
passed with cleanup warnings). It is incidental diagnostic evidence, not
Package C closure evidence. No command remained running when the reviewer
returned.
