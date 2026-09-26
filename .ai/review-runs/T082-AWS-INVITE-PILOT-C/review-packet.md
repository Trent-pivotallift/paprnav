# Review packet: T082-AWS-INVITE-PILOT-C

Stage: closure
Generated: 2026-09-19T19:48:48+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `0cd3490a90f5d119bf5dd4ebebc0363858fec8cdda64d8d0264055c55f5ff224`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: T082-AWS-INVITE-PILOT-C

## Objective

Implement the local, reviewable deployment family for the invite-only AWS
pilot: deterministic API/frontend image contexts, immutable task image
references, HTTPS/ALB/WAF infrastructure, separate runtime and migration
database authority, and a clean-database bootstrap path. This package ends at
validated source, local container/database evidence, and a reviewed Terraform
plan. It does not apply Terraform, push images, populate secrets, issue DNS or
certificate changes, run an AWS migration, or start a service.

Normative authority is the independently approved parent
`T082-AWS-INVITE-PILOT` design. Packages A and B are implementation-reviewed.
This child must resolve Package C details without weakening their route,
invitation, session, or tenant boundaries.

## User-visible outcome

After the later execution gate, invited users reach one HTTPS hostname, paste
an invitation on `/invite`, and use the existing product. The browser calls
same-origin `/api/v1/*`; HTTP redirects to HTTPS; unfinished V4 routes remain
unavailable; ordinary users remain tenant-scoped. Package C itself changes no
live user-visible service.

## Safety and correctness invariants

1. Every task definition names an immutable `repository@sha256:<digest>` image.
   No `latest`, mutable release tag, or dirty/unreviewed 0030 artifact can enter
   a pilot image context.
2. Public traffic has one path: HTTP redirects to HTTPS; HTTPS routes
   `/api/v1/*`, `/health`, and `/version` to the API and other paths to the
   frontend. Only the ALB reaches service ports. A regional WAF protects the
   HTTPS listener with AWS managed common protections plus endpoint-scoped
   rate limits for login and invitation creation/acceptance.
3. External-mode planning fails unless a canonical HTTPS hostname, matching
   Route53 zone, ACM validation path, real budget recipient, and digest-pinned
   API/frontend images are supplied. These values are inputs, not invented.
4. The RDS-managed `paprnav_admin` login is bootstrap/migration authority only.
   API and worker use a distinct `paprnav_app` login with DML/sequence access
   and no role, schema, DDL, extension, or database administration authority.
5. Secret access is task- and phase-specific. API execution may read only the
   app database and invitation secrets; worker execution may read only the app
   database secret; frontend reads none. Migration/reference, runtime-role,
   and first-admin tasks have distinct roles described below.
   No secret value appears in Terraform state, plan output, logs, or command
   arguments.
6. The reviewed database head is Package A's committed 0029 context. The
   untracked 0030 files are absent from image/migration contexts and cannot be
   selected by filesystem discovery.
7. Bootstrap phases are explicit and separately logged: migration to reviewed
   head, runtime role/grants, idempotent reference rows, and first admin.
   Reference bootstrap may rerun. First-admin bootstrap is permanently
   first-use-only on an empty identity/authority state, serializes competing
   callers, and atomically creates its consumption record, user, organization,
   membership, and audit event. It never invokes `seed_dev.py` or creates demo
   data.
8. Package C plans with API/frontend desired counts zero and worker scheduling
   disabled. Service activation and paid OCR remain Package E/D gates.
9. Deletion protection, final-snapshot behavior, S3 versioning, and
   `force_destroy=false` remain intact. No plan may destroy or replace an
   existing durable resource without a new reviewed decision.
10. Cloud mutation remains separately authorized. A valid plan is evidence,
    not permission to apply, push, populate, migrate, or activate.

## Current behavior

- The applied foundation has two empty ECR repositories and an active ECS
  cluster with zero services/tasks. No pilot RDS instance exists.
- Terraform source proposes an HTTP-only ALB, mutable ECR tags, `:latest` task
  images, shared task/execution authority, an RDS master named `paprnav_app`,
  and an unused session-secret placeholder. The frontend has no Dockerfile.
- The checked-in deploy policy has no ACM, WAF, or Route53 permissions. Live
  read-only calls confirmed all three inventories are denied.
- Required AWS service-linked roles for RDS, ECS, and Elastic Load Balancing do
  not exist; the deploy role lacks `iam:CreateServiceLinkedRole`.
- The user-owned pilot hostname/hosted zone and the real AWS Budget notification
  address are not repository inputs and must not be guessed or committed.

## Proposed design

### Deterministic release contexts and images

Add one allowlist-and-hash release-context builder derived from tracked `HEAD`
plus only independently reviewed T082 overlay files. It rejects unlisted dirty
files, symlinks escaping the context, hash drift, and every 0030 path. The
manifest binds source commit, overlay hashes, Dockerfiles, lockfiles,
Package-A migration context, build arguments, and expected image platforms.
The eventual candidate commit must reproduce the context before push.

Use the ordinary backend image only for API and worker. Build a third,
digest-pinned migration/bootstrap image from Package A's sealed migration
context plus a separately manifested minimal `/bootstrap` program and
hash-pinned third-party wheels. The program uses direct PostgreSQL and AWS SDK
calls and stdlib password hashing; it imports no application package. The
image contains no application checkout, arbitrary mount, dotenv file, shell
override, or unmanifested import root. Its base image is digest pinned, its
root filesystem is read-only at execution, and its fixed entry point accepts
only the four reviewed phase names. Package C explicitly extends Package A's
manifest with the bootstrap files and dependency hashes; Package A's migration
context remains byte-for-byte unchanged.

Add a multi-stage, non-root Next.js standalone frontend image with the pilot
same-origin API setting fixed at build time. Add container health checks and
run all three images locally. Terraform accepts API/frontend/bootstrap image
references only in digest form; ECR repositories reject mutable tag overwrite
for future releases. Image-inventory tests prove that 0030, the workspace,
unlisted mounts, and application-only modules are absent from the privileged
image.

### HTTPS, routing, WAF, and network authority

Terraform manages an ACM certificate and DNS validation records in a supplied
Route53 zone, an alias record for the supplied pilot hostname, an HTTP redirect
listener, and an HTTPS forwarding listener. WAF associates only with the ALB.
It uses AWS managed common protections with `SizeRestrictions_BODY` overridden
to Count, followed by a custom 8 KiB oversize-body block for every route except
an exact `POST ^/api/v1/aircraft/[^/]+/uploads$` multipart request. The upload
path still receives every other managed-common rule; WAF inspects its available
8 KiB prefix and the application streaming boundary remains authoritative for
content type and the 100 MiB maximum. A `Content-Length` over 100 MiB is an
early block optimization, not the sole size control. Separate endpoint-scoped
rate rules protect login and invitation creation/acceptance regardless of body
size. Exact thresholds, regex, overrides, and priorities are declared once and
asserted from the plan.

Separate security groups for public API/frontend services and non-listening
worker/bootstrap tasks. ALB ingress reaches only API/frontend ports; RDS ingress
accepts only the named runtime and bootstrap task groups. Public task IPs remain
the reviewed pilot-only outbound-cost compromise.

### Database identities, secrets, and bootstrap

Change the RDS master username to `paprnav_admin`. Create distinct execution
roles so frontend has no secret access, API can retrieve only the app database
and invitation secrets, and worker can retrieve only the app database secret.
Bootstrap secrets are fetched in process by distinct task roles rather than
injected into environment variables: migration/reference can get only the
RDS-managed admin secret; runtime-role setup can get that admin secret and put
only the app database secret; first-admin can get the admin secret and the
exact one-use first-admin password secret. None may list or read unrelated
secrets.

The runtime-role phase constructs credentials in memory, creates/rotates the
`paprnav_app` login, revokes public schema creation, and compares the exact
post-0029 public table/sequence inventory to a reviewed manifest. It grants
connect, schema usage, table DML, and sequence usage/select only for the matched
allowlist, explicitly excluding `alembic_version` and the admin-owned
`pilot_control` schema. It grants no default privileges: every future migration
must refresh a reviewed grant manifest. Because initial services remain zero,
a failure after database-password change but before secret publication is
recovered only by rerunning this phase. The task commits the generated database
password, calls `PutSecretValue` with a fresh client request token, retains the
returned VersionId, uses `DescribeSecret` to require that exact VersionId at
`AWSCURRENT`, and opens a fresh `paprnav_app` connection with the same generated
bytes before reporting success. It never needs `GetSecretValue` and never logs
the token or password. A crash at any boundary is recoverable by a new
zero-service run that installs and publishes a new value.

The migration phase runs only the sealed 0001-through-0029 context. The
reference phase inserts only canonical airframe/engine/propeller rows
idempotently. Admin-owned SQL creates
`pilot_control.bootstrap_consumptions`, inaccessible to `paprnav_app`. The
first-admin transaction takes one fixed transaction-level advisory lock,
requires no consumption row and zero rows across `users`, `organizations`, and
`organization_memberships`, and then inserts the permanent consumption row,
user, platform organization, active `platform_admin` membership, and sanitized
audit event together. A rollback leaves none of them. Revocation never removes
the consumption row, so it cannot reopen bootstrap. Identity fields are
explicit arguments; the password comes only from the one-use secret. Logs
contain phase, status, and non-secret identifiers only.

Runtime configuration supplies the Package A/B pilot gates, exact HTTPS CORS
origin, Secure cookie setting, storage bucket, and invitation secret. The
unused session-secret resource and task injection are removed. The worker stays
disabled until Package D closes paid-attempt/cost behavior.

### AWS prerequisite authority

Generate the deploy-policy prerequisite from a reviewed action/resource matrix
and the operator-supplied hosted-zone ID. It covers the actual
`/paprnav/pilot/*` application/invitation secret ARNs, RDS-managed `rds!db-*`
creation/tagging prerequisites, ACM, WAF, Route53, and service-linked roles.
`CreateServiceLinkedRole` is constrained by exact role ARN and
`iam:AWSServiceName` for RDS, ECS, and Elastic Load Balancing; Route53 mutation
is constrained to the supplied hosted zone; certificate/WAF resources are
region/account and paprnav-name/tag constrained where supported. The complete
matrix is in `design-remediation-1.md`.

The existing bootstrap user is only authorized to assume the deploy role and
is not a policy updater. Package E therefore has a separate operator-admin
prerequisite: record an exact principal ARN and prove it can create/set a new
version of only `paprnav-terraform-deploy`. Neither that principal nor its
authorization is invented here, and no policy update occurs until explicit
authorization.

## Alternatives considered

- Reusing `paprnav_app` as RDS master was rejected because an API compromise
  would inherit schema/role authority.
- Building from the current workspace was rejected because preserved T081/0030
  files would contaminate the release context.
- `:latest` or a mutable release tag was rejected because neither proves which
  bytes ECS executes.
- Keeping HTTP for a small cohort was rejected because invitation codes,
  passwords, sessions, and volunteer records cross the browser boundary.
- Using the Next development proxy in AWS was rejected by Package B; it would
  create a second auth/origin path.
- A NAT-gateway/private-task redesign remains deferred for pilot cost; the ALB
  security-group boundary and public task IP compromise are explicit.

## Trust, authorization, and audit boundaries

Terraform source and the reviewed plan define infrastructure intent; only the
operator may authorize mutation. ACM/Route53 establish hostname control, ALB/WAF
own public ingress, ECS roles own workload AWS calls, PostgreSQL roles own data
authority, Secrets Manager owns credential delivery, and CloudWatch receives
sanitized runtime logs. Neither Terraform state nor product events are an
authorization source.

## Read paths and consumers

- Browser HTTPS frontend and direct same-origin API routes.
- ECS image pulls, health checks, CloudWatch log delivery, S3 upload access,
  Secrets Manager retrieval, RDS connections, and later Textract calls.
- Operator Terraform validate/plan, release manifest, bootstrap phase output,
  and rollback/restore runbook.

## Write paths and administrative paths

- Local source generation, image builds, disposable PostgreSQL bootstrap, and
  Terraform plan are Package C writes/evidence.
- Later Package E paths include deploy-policy prerequisite, Terraform apply,
  ECR push, secret population, one-off bootstrap task, DNS/certificate
  validation, and service activation. None is authorized here.

## Migration, compatibility, correction, and rollback

The infrastructure plan is created with zero services and no worker schedule.
Database bootstrap targets sealed 0029. If a local migration/bootstrap phase
fails, discard the disposable database/context and fix the reviewed source; no
live correction occurs. After future apply, failure before service activation
leaves services at zero. A runtime-role publication failure is recovered by a
new zero-service phase run and connection proof, not by guessing or exposing a
password. A first-admin failure rolls back its permanent sentinel and all
identity/audit rows together. Application rollback uses a prior digest only with
documented schema compatibility; database recovery restores a pre-migration
snapshot into a new instance. Pilot data is never deleted as rollback.

## Test strategy

1. Deterministically rebuild release contexts twice; compare manifests; prove
   unlisted dirty files, symlink escape, hash drift, and every 0030 inclusion
   fail closed. Inspect the privileged image and attempt application-checkout,
   mount, import-root, entry-point, and dependency-hash bypasses.
2. Build API/frontend images locally, inspect non-root user/platform/digests,
   run API health/version and frontend/invite smoke requests, and prove pilot
   proxy/V4 boundaries remain unavailable.
3. Terraform fmt/validate plus a refreshed zero-count plan; assert HTTPS-only
   public access, exact routing/WAF rules including the upload override and auth
   rate rules, digest images, task-specific secret policies, disabled worker,
   deletion controls, and no destroy/replacement. Exercise a representative
   multipart upload through a local WAF-policy oracle; deployed acceptance
   remains Package E.
   Scan plan/output for secret values and forbidden mutable tags.
4. Validate the IAM policy with deterministic assertions and AWS Access
   Analyzer; retain the live read-only preflight and re-run it only if policy or
   target account dependencies change.
5. On disposable PostgreSQL 16, execute the sealed migration/bootstrap path
   from empty state, rerun reference bootstrap, reject a second first-admin,
   populated identity state, revoked prior administrator, and two concurrent
   distinct first-admin attempts; inject failure after each identity/audit
   insert and prove atomic rollback. Verify exact grants after migration,
   simulate password-publication failure/recovery, create manual and
   OCR-derived entries, and prove the app role cannot DDL, manage roles, access
   `pilot_control`, mutate `alembic_version`, read admin secrets, or advance
   migrations.
6. Include prior Package A/B review evidence by reference. Repeat their tests
   only when a changed dependency could invalidate them.

## Expected file scope

- `infra/terraform/**` except ignored state/cache
- `infra/aws-iam/paprnav-terraform-deploy-policy.json` and its README
- backend/frontend Dockerfiles and `.dockerignore` files
- bounded backend bootstrap scripts/services/tests; no ORM model or migration
  change
- deterministic release-context/build/plan verification scripts
- `.ai/review-runs/T082-AWS-INVITE-PILOT-C/**` and bounded deployment docs

Preserved T081 Slice 4B artifacts, `backend/app/models/core.py`, every 0030
artifact, unrelated application behavior, Git index/commit, cloud mutation, and
paid OCR activation are excluded.

## Known uncertainty

- The user-owned pilot hostname/Route53 zone and real budget notification
  recipient remain operator inputs. Implementation may parameterize and test
  them but cannot produce an execution-ready plan without them.
- The exact operator-admin principal authorized to update the deploy policy is
  also an explicit Package E input. The existing bootstrap user is not assumed
  to have that authority.
- Live ACM/WAF/Route53 state is unknown because the current deploy role is
  denied read access. The reviewed policy prerequisite must land before final
  plan/apply evidence.
- Required service-linked roles are absent. Their constrained creation is a
  prerequisite, not an apply-time surprise.
- Local image digests are not ECR digests. Package E must bind pushed digests
  and prove ECS uses those exact values.
- Runtime cost, certificate issuance time, DNS propagation, RDS restore, and
  deployed browser behavior cannot be proven by Package C.

## Model routing

- Design builder: `/root`.
- Preferred route: GPT-6 Astra xhigh because Package C defines IAM, migration
  authority, secret delivery, HTTPS/WAF, and immutable release boundaries.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Independent reviewer: `/root/t082_pilot_design_adversary`; GPT-6 Astra xhigh
  requested, actual model and effort not exposed by runtime.


## Current finding ledger

```json
[
  {
    "id": "T082-C-001",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The credential-bearing migration/bootstrap execution path contains only explicitly reviewed sealed authority files and dependencies.",
    "summary": "Reusing the backend application image exposes the entire application checkout to migration credentials.",
    "evidence": ["adversarial-design-initial.md", "backend/Dockerfile", "../T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md"],
    "impact": "Unreviewed application or dirty-tree code could execute with RDS administrator and secret-publication authority.",
    "requiredClosure": "Use a dedicated digest-pinned sealed bootstrap image and prove the full execution path excludes application checkout files, mounts, and import overrides.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-002",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Deployment bootstrap can create platform administration exactly once on an empty authority state, atomically and under serialization.",
    "summary": "The no-active-admin guard can reopen after revocation and has no concurrent first-use semantics.",
    "evidence": ["adversarial-design-initial.md", "decision.md", "../T082-AWS-INVITE-PILOT/decision.md"],
    "impact": "A later or racing bootstrap could create an unauthorized platform administrator.",
    "requiredClosure": "Define a permanent first-use sentinel and serialized atomic creation with populated, revoked-prior, concurrent, and rollback tests.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-003",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every AWS prerequisite action is granted only to an identified authorized principal and matches the exact resource names used by Terraform/runtime.",
    "summary": "Secret resource patterns and policy-updater authority do not match the proposed infrastructure.",
    "evidence": ["adversarial-design-initial.md", "infra/aws-iam/paprnav-terraform-deploy-policy.json", "infra/aws-iam/paprnav-terraform-bootstrap-assume-policy.json", "infra/terraform/database.tf"],
    "impact": "Planning/apply can fail late or require an undocumented privilege escalation.",
    "requiredClosure": "Add an exact action/resource/principal matrix for secrets and prerequisites and identify an explicit operator-admin update gate.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-004",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "The runtime database role cannot mutate migration control state and credential rotation cannot strand runtime access.",
    "summary": "Broad default grants could include alembic_version and password/secret publication lacks recovery semantics.",
    "evidence": ["adversarial-design-initial.md", "decision.md"],
    "impact": "Runtime could advance migration metadata or a partial rotation could make the application secret unusable.",
    "requiredClosure": "Freeze explicit post-migration grants excluding control tables and a recoverable password-publication protocol.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md", "adversarial-design-closure-2.md"]
  },
  {
    "id": "T082-C-005",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "WAF protections preserve the reviewed authenticated multipart upload workflow without weakening public auth controls.",
    "summary": "Managed common body-size protection is incompatible with the application's 100 MiB multipart upload boundary unless scoped.",
    "evidence": ["adversarial-design-initial.md", "backend/app/api/routes/uploads.py", "backend/app/core/config.py"],
    "impact": "Valid pilot uploads could be blocked at the public edge.",
    "requiredClosure": "Define path-scoped body-size handling and multipart acceptance evidence while retaining auth rate limits.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-006",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every meaningful design/review phase records builder and reviewer identity, exact model or runtime non-disclosure, effort or runtime non-disclosure, and routing trigger.",
    "summary": "The reviewed Package C decision and remediation artifact omitted mandatory model-routing sections.",
    "evidence": ["adversarial-design-closure-1.md", ".ai/MODEL_ROUTING.md"],
    "impact": "The design cannot close under repository policy without auditable routing evidence.",
    "requiredClosure": "Add accurate routing sections without rewriting immutable review artifacts and obtain independent verification from a regenerated packet.",
    "closureEvidence": ["decision.md#model-routing", "design-remediation-1.md#model-routing", "adversarial-design-closure-2.md"]
  },
  {
    "id": "T082-C-007",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every runtime database-secret consumer receives the published DATABASE_URL value rather than the enclosing JSON document.",
    "summary": "ECS injects the whole JSON application secret into DATABASE_URL.",
    "evidence": ["adversarial-implementation-initial.md", "infra/bootstrap/bootstrap.py", "infra/terraform/ecs_runtime.tf"],
    "impact": "The API and worker fail database configuration at startup.",
    "requiredClosure": "Select the DATABASE_URL JSON key for all consumers and retain a configuration-level regression test.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/ecs_runtime.tf", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-008",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "All valid generated database credentials survive migration URL construction and Alembic configuration parsing unchanged.",
    "summary": "Reserved password characters can trigger ConfigParser interpolation failure before migration connects.",
    "evidence": ["adversarial-implementation-initial.md", "infra/bootstrap/bootstrap.py", "backend/app/db/migrations/env.py"],
    "impact": "A valid managed administrator password can make fresh-database bootstrap fail.",
    "requiredClosure": "Remove or correctly escape the interpolation boundary and retain reserved-character cases.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/bootstrap/bootstrap.py", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-009",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Invalid external deployment inputs and mismatched immutable image repositories prevent plan or apply.",
    "summary": "Terraform check blocks warn instead of enforcing execution gates.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/variables.tf", "infra/terraform/main.tf"],
    "impact": "A malformed or wrong-target pilot configuration can proceed to mutation.",
    "requiredClosure": "Use blocking validation/preconditions, verify hosted-zone identity, and retain negative assertions.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/main.tf", "infra/terraform/variables.tf", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-010",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every routed login and invitation-accept variant is subject to its reviewed edge rate limit.",
    "summary": "Encoded auth paths accepted by FastAPI bypass raw WAF path predicates.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/load_balancer.tf"],
    "impact": "Attackers can bypass endpoint-specific public authentication throttles.",
    "requiredClosure": "Align WAF classification with routed-path semantics for encoded and redirect variants without weakening uploads.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "infra/terraform/load_balancer.tf", "backend/tests/test_pilot_package_c.py", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-011",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "WAF observability does not retain session-bearing request-header values.",
    "summary": "Enabled WAF request sampling can retain Cookie values.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/load_balancer.tf"],
    "impact": "Session credentials can be exposed through sampled-request access.",
    "requiredClosure": "Disable sampling or prove effective sensitive-header protection for every enabled sampling configuration.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/load_balancer.tf", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-012",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Certificate mutations are limited to reviewed Paprnav-owned resources and ownership cannot be self-manufactured.",
    "summary": "Generated ACM permissions permit tagging and deleting any regional account certificate.",
    "evidence": ["adversarial-implementation-initial.md", "scripts/generate_pilot_deploy_policy.py"],
    "impact": "The deploy role could alter or delete unrelated certificates.",
    "requiredClosure": "Constrain mutation by ownership without granting unrestricted ownership tagging and retain policy assertions.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md", "scripts/generate_pilot_deploy_policy.py", "infra/aws-iam/pilot-policy-matrix.json", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-013",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Release contexts are derived only from the approved candidate commit and protected authority blobs while unrelated preserved dirt is excluded explicitly.",
    "summary": "The release builder omits Package A authority verification and cannot represent the approved preserved dirty-tree workflow.",
    "evidence": ["adversarial-implementation-initial.md", "scripts/build_pilot_release_context.py", ".ai/pilot-package-c-context-v1.json"],
    "impact": "Unreviewed protected bytes could enter images or valid pilot builds could be impossible from the preserved tree.",
    "requiredClosure": "Enforce one candidate authority gate, model preserved exclusions separately, and retain positive and negative tests.",
    "closureEvidence": ["package-c-remediation-1.md", "scripts/build_pilot_release_context.py", ".ai/pilot-package-c-context-v1.json", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-014",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Package C has retained bounded regression evidence and locally constructible evidence for all three reviewed images.",
    "summary": "New Package C components lack a retained regression suite and local three-image evidence.",
    "evidence": ["adversarial-implementation-initial.md", "package-c-implementation.md"],
    "impact": "The implementation cannot be reproduced or protected from immediate regression before deployment inputs exist.",
    "requiredClosure": "Retain bounded bootstrap, context, IAM, and WAF tests and produce local three-image evidence while leaving live inputs to Package E.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md", "backend/tests/test_pilot_package_c.py", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-015",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The internet-facing frontend does not expose a known unauthenticated WebSocket SSRF path in its production server.",
    "summary": "The production image contains vulnerable Next.js 16.1.6 and the edge does not block WebSocket upgrades.",
    "evidence": ["adversarial-implementation-remediation-1.md", "frontend/paprnav-frontend/package.json", "frontend/paprnav-frontend/package-lock.json"],
    "impact": "An unauthenticated client could induce server-side requests from the public frontend process.",
    "requiredClosure": "Upgrade to a maintainer-patched Next.js release and rebuild/revalidate, or prove the maintainer's upgrade-blocking mitigation before exposure.",
    "closureEvidence": ["package-c-remediation-2.md", "adversarial-implementation-remediation-2.md", "frontend/paprnav-frontend/package.json", "frontend/paprnav-frontend/package-lock.json", "frontend/paprnav-frontend/Dockerfile"]
  },
  {
    "id": "T082-C-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Final closure artifacts enumerate every meaningful phase, role, identity, requested route, and actual model and effort or runtime non-disclosure.",
    "summary": "The closure reports omitted a complete mandatory model-assignment summary.",
    "evidence": ["adversarial-closure-initial.md", ".ai/MODEL_ROUTING.md", "closure.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md"],
    "impact": "The high-risk package cannot close without auditable model-routing evidence.",
    "requiredClosure": "Add complete Model assignments sections to both closure reports, preserving historical artifacts, and obtain documentation/integrity re-attestation.",
    "closureEvidence": ["closure.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md", "adversarial-closure-final.md"]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/decision.md`

size=18482; sha256=9fcfe44934b68499c8be7cf6ac9a8ae68947fc23aac806a9bc092677f5319768

```text
# Decision packet: T082-AWS-INVITE-PILOT-C

## Objective

Implement the local, reviewable deployment family for the invite-only AWS
pilot: deterministic API/frontend image contexts, immutable task image
references, HTTPS/ALB/WAF infrastructure, separate runtime and migration
database authority, and a clean-database bootstrap path. This package ends at
validated source, local container/database evidence, and a reviewed Terraform
plan. It does not apply Terraform, push images, populate secrets, issue DNS or
certificate changes, run an AWS migration, or start a service.

Normative authority is the independently approved parent
`T082-AWS-INVITE-PILOT` design. Packages A and B are implementation-reviewed.
This child must resolve Package C details without weakening their route,
invitation, session, or tenant boundaries.

## User-visible outcome

After the later execution gate, invited users reach one HTTPS hostname, paste
an invitation on `/invite`, and use the existing product. The browser calls
same-origin `/api/v1/*`; HTTP redirects to HTTPS; unfinished V4 routes remain
unavailable; ordinary users remain tenant-scoped. Package C itself changes no
live user-visible service.

## Safety and correctness invariants

1. Every task definition names an immutable `repository@sha256:<digest>` image.
   No `latest`, mutable release tag, or dirty/unreviewed 0030 artifact can enter
   a pilot image context.
2. Public traffic has one path: HTTP redirects to HTTPS; HTTPS routes
   `/api/v1/*`, `/health`, and `/version` to the API and other paths to the
   frontend. Only the ALB reaches service ports. A regional WAF protects the
   HTTPS listener with AWS managed common protections plus endpoint-scoped
   rate limits for login and invitation creation/acceptance.
3. External-mode planning fails unless a canonical HTTPS hostname, matching
   Route53 zone, ACM validation path, real budget recipient, and digest-pinned
   API/frontend images are supplied. These values are inputs, not invented.
4. The RDS-managed `paprnav_admin` login is bootstrap/migration authority only.
   API and worker use a distinct `paprnav_app` login with DML/sequence access
   and no role, schema, DDL, extension, or database administration authority.
5. Secret access is task- and phase-specific. API execution may read only the
   app database and invitation secrets; worker execution may read only the app
   database secret; frontend reads none. Migration/reference, runtime-role,
   and first-admin tasks have distinct roles described below.
   No secret value appears in Terraform state, plan output, logs, or command
   arguments.
6. The reviewed database head is Package A's committed 0029 context. The
   untracked 0030 files are absent from image/migration contexts and cannot be
   selected by filesystem discovery.
7. Bootstrap phases are explicit and separately logged: migration to reviewed
   head, runtime role/grants, idempotent reference rows, and first admin.
   Reference bootstrap may rerun. First-admin bootstrap is permanently
   first-use-only on an empty identity/authority state, serializes competing
   callers, and atomically creates its consumption record, user, organization,
   membership, and audit event. It never invokes `seed_dev.py` or creates demo
   data.
8. Package C plans with API/frontend desired counts zero and worker scheduling
   disabled. Service activation and paid OCR remain Package E/D gates.
9. Deletion protection, final-snapshot behavior, S3 versioning, and
   `force_destroy=false` remain intact. No plan may destroy or replace an
   existing durable resource without a new reviewed decision.
10. Cloud mutation remains separately authorized. A valid plan is evidence,
    not permission to apply, push, populate, migrate, or activate.

## Current behavior

- The applied foundation has two empty ECR repositories and an active ECS
  cluster with zero services/tasks. No pilot RDS instance exists.
- Terraform source proposes an HTTP-only ALB, mutable ECR tags, `:latest` task
  images, shared task/execution authority, an RDS master named `paprnav_app`,
  and an unused session-secret placeholder. The frontend has no Dockerfile.
- The checked-in deploy policy has no ACM, WAF, or Route53 permissions. Live
  read-only calls confirmed all three inventories are denied.
- Required AWS service-linked roles for RDS, ECS, and Elastic Load Balancing do
  not exist; the deploy role lacks `iam:CreateServiceLinkedRole`.
- The user-owned pilot hostname/hosted zone and the real AWS Budget notification
  address are not repository inputs and must not be guessed or committed.

## Proposed design

### Deterministic release contexts and images

Add one allowlist-and-hash release-context builder derived from tracked `HEAD`
plus only independently reviewed T082 overlay files. It rejects unlisted dirty
files, symlinks escaping the context, hash drift, and every 0030 path. The
manifest binds source commit, overlay hashes, Dockerfiles, lockfiles,
Package-A migration context, build arguments, and expected image platforms.
The eventual candidate commit must reproduce the context before push.

Use the ordinary backend image only for API and worker. Build a third,
digest-pinned migration/bootstrap image from Package A's sealed migration
context plus a separately manifested minimal `/bootstrap` program and
hash-pinned third-party wheels. The program uses direct PostgreSQL and AWS SDK
calls and stdlib password hashing; it imports no application package. The
image contains no application checkout, arbitrary mount, dotenv file, shell
override, or unmanifested import root. Its base image is digest pinned, its
root filesystem is read-only at execution, and its fixed entry point accepts
only the four reviewed phase names. Package C explicitly extends Package A's
manifest with the bootstrap files and dependency hashes; Package A's migration
context remains byte-for-byte unchanged.

Add a multi-stage, non-root Next.js standalone frontend image with the pilot
same-origin API setting fixed at build time. Add container health checks and
run all three images locally. Terraform accepts API/frontend/bootstrap image
references only in digest form; ECR repositories reject mutable tag overwrite
for future releases. Image-inventory tests prove that 0030, the workspace,
unlisted mounts, and application-only modules are absent from the privileged
image.

### HTTPS, routing, WAF, and network authority

Terraform manages an ACM certificate and DNS validation records in a supplied
Route53 zone, an alias record for the supplied pilot hostname, an HTTP redirect
listener, and an HTTPS forwarding listener. WAF associates only with the ALB.
It uses AWS managed common protections with `SizeRestrictions_BODY` overridden
to Count, followed by a custom 8 KiB oversize-body block for every route except
an exact `POST ^/api/v1/aircraft/[^/]+/uploads$` multipart request. The upload
path still receives every other managed-common rule; WAF inspects its available
8 KiB prefix and the application streaming boundary remains authoritative for
content type and the 100 MiB maximum. A `Content-Length` over 100 MiB is an
early block optimization, not the sole size control. Separate endpoint-scoped
rate rules protect login and invitation creation/acceptance regardless of body
size. Exact thresholds, regex, overrides, and priorities are declared once and
asserted from the plan.

Separate security groups for public API/frontend services and non-listening
worker/bootstrap tasks. ALB ingress reaches only API/frontend ports; RDS ingress
accepts only the named runtime and bootstrap task groups. Public task IPs remain
the reviewed pilot-only outbound-cost compromise.

### Database identities, secrets, and bootstrap

Change the RDS master username to `paprnav_admin`. Create distinct execution
roles so frontend has no secret access, API can retrieve only the app database
and invitation secrets, and worker can retrieve only the app database secret.
Bootstrap secrets are fetched in process by distinct task roles rather than
injected into environment variables: migration/reference can get only the
RDS-managed admin secret; runtime-role setup can get that admin secret and put
only the app database secret; first-admin can get the admin secret and the
exact one-use first-admin password secret. None may list or read unrelated
secrets.

The runtime-role phase constructs credentials in memory, creates/rotates the
`paprnav_app` login, revokes public schema creation, and compares the exact
post-0029 public table/sequence inventory to a reviewed manifest. It grants
connect, schema usage, table DML, and sequence usage/select only for the matched
allowlist, explicitly excluding `alembic_version` and the admin-owned
`pilot_control` schema. It grants no default privileges: every future migration
must refresh a reviewed grant manifest. Because initial services remain zero,
a failure after database-password change but before secret publication is
recovered only by rerunning this phase. The task commits the generated database
password, calls `PutSecretValue` with a fresh client request token, retains the
returned VersionId, uses `DescribeSecret` to require that exact VersionId at
`AWSCURRENT`, and opens a fresh `paprnav_app` connection with the same generated
bytes before reporting success. It never needs `GetSecretValue` and never logs
the token or password. A crash at any boundary is recoverable by a new
zero-service run that installs and publishes a new value.

The migration phase runs only the sealed 0001-through-0029 context. The
reference phase inserts only canonical airframe/engine/propeller rows
idempotently. Admin-owned SQL creates
`pilot_control.bootstrap_consumptions`, inaccessible to `paprnav_app`. The
first-admin transaction takes one fixed transaction-level advisory lock,
requires no consumption row and zero rows across `users`, `organizations`, and
`organization_memberships`, and then inserts the permanent consumption row,
user, platform organization, active `platform_admin` membership, and sanitized
audit event together. A rollback leaves none of them. Revocation never removes
the consumption row, so it cannot reopen bootstrap. Identity fields are
explicit arguments; the password comes only from the one-use secret. Logs
contain phase, status, and non-secret identifiers only.

Runtime configuration supplies the Package A/B pilot gates, exact HTTPS CORS
origin, Secure cookie setting, storage bucket, and invitation secret. The
unused session-secret resource and task injection are removed. The worker stays
disabled until Package D closes paid-attempt/cost behavior.

### AWS prerequisite authority

Generate the deploy-policy prerequisite from a reviewed action/resource matrix
and the operator-supplied hosted-zone ID. It covers the actual
`/paprnav/pilot/*` application/invitation secret ARNs, RDS-managed `rds!db-*`
creation/tagging prerequisites, ACM, WAF, Route53, and service-linked roles.
`CreateServiceLinkedRole` is constrained by exact role ARN and
`iam:AWSServiceName` for RDS, ECS, and Elastic Load Balancing; Route53 mutation
is constrained to the supplied hosted zone; certificate/WAF resources are
region/account and paprnav-name/tag constrained where supported. The complete
matrix is in `design-remediation-1.md`.

The existing bootstrap user is only authorized to assume the deploy role and
is not a policy updater. Package E therefore has a separate operator-admin
prerequisite: record an exact principal ARN and prove it can create/set a new
version of only `paprnav-terraform-deploy`. Neither that principal nor its
authorization is invented here, and no policy update occurs until explicit
authorization.

## Alternatives considered

- Reusing `paprnav_app` as RDS master was rejected because an API compromise
  would inherit schema/role authority.
- Building from the current workspace was rejected because preserved T081/0030
  files would contaminate the release context.
- `:latest` or a mutable release tag was rejected because neither proves which
  bytes ECS executes.
- Keeping HTTP for a small cohort was rejected because invitation codes,
  passwords, sessions, and volunteer records cross the browser boundary.
- Using the Next development proxy in AWS was rejected by Package B; it would
  create a second auth/origin path.
- A NAT-gateway/private-task redesign remains deferred for pilot cost; the ALB
  security-group boundary and public task IP compromise are explicit.

## Trust, authorization, and audit boundaries

Terraform source and the reviewed plan define infrastructure intent; only the
operator may authorize mutation. ACM/Route53 establish hostname control, ALB/WAF
own public ingress, ECS roles own workload AWS calls, PostgreSQL roles own data
authority, Secrets Manager owns credential delivery, and CloudWatch receives
sanitized runtime logs. Neither Terraform state nor product events are an
authorization source.

## Read paths and consumers

- Browser HTTPS frontend and direct same-origin API routes.
- ECS image pulls, health checks, CloudWatch log delivery, S3 upload access,
  Secrets Manager retrieval, RDS connections, and later Textract calls.
- Operator Terraform validate/plan, release manifest, bootstrap phase output,
  and rollback/restore runbook.

## Write paths and administrative paths

- Local source generation, image builds, disposable PostgreSQL bootstrap, and
  Terraform plan are Package C writes/evidence.
- Later Package E paths include deploy-policy prerequisite, Terraform apply,
  ECR push, secret population, one-off bootstrap task, DNS/certificate
  validation, and service activation. None is authorized here.

## Migration, compatibility, correction, and rollback

The infrastructure plan is created with zero services and no worker schedule.
Database bootstrap targets sealed 0029. If a local migration/bootstrap phase
fails, discard the disposable database/context and fix the reviewed source; no
live correction occurs. After future apply, failure before service activation
leaves services at zero. A runtime-role publication failure is recovered by a
new zero-service phase run and connection proof, not by guessing or exposing a
password. A first-admin failure rolls back its permanent sentinel and all
identity/audit rows together. Application rollback uses a prior digest only with
documented schema compatibility; database recovery restores a pre-migration
snapshot into a new instance. Pilot data is never deleted as rollback.

## Test strategy

1. Deterministically rebuild release contexts twice; compare manifests; prove
   unlisted dirty files, symlink escape, hash drift, and every 0030 inclusion
   fail closed. Inspect the privileged image and attempt application-checkout,
   mount, import-root, entry-point, and dependency-hash bypasses.
2. Build API/frontend images locally, inspect non-root user/platform/digests,
   run API health/version and frontend/invite smoke requests, and prove pilot
   proxy/V4 boundaries remain unavailable.
3. Terraform fmt/validate plus a refreshed zero-count plan; assert HTTPS-only
   public access, exact routing/WAF rules including the upload override and auth
   rate rules, digest images, task-specific secret policies, disabled worker,
   deletion controls, and no destroy/replacement. Exercise a representative
   multipart upload through a local WAF-policy oracle; deployed acceptance
   remains Package E.
   Scan plan/output for secret values and forbidden mutable tags.
4. Validate the IAM policy with deterministic assertions and AWS Access
   Analyzer; retain the live read-only preflight and re-run it only if policy or
   target account dependencies change.
5. On disposable PostgreSQL 16, execute the sealed migration/bootstrap path
   from empty state, rerun reference bootstrap, reject a second first-admin,
   populated identity state, revoked prior administrator, and two concurrent
   distinct first-admin attempts; inject failure after each identity/audit
   insert and prove atomic rollback. Verify exact grants after migration,
   simulate password-publication failure/recovery, create manual and
   OCR-derived entries, and prove the app role cannot DDL, manage roles, access
   `pilot_control`, mutate `alembic_version`, read admin secrets, or advance
   migrations.
6. Include prior Package A/B review evidence by reference. Repeat their tests
   only when a changed dependency could invalidate them.

## Expected file scope

- `infra/terraform/**` except ignored state/cache
- `infra/aws-iam/paprnav-terraform-deploy-policy.json` and its README
- backend/frontend Dockerfiles and `.dockerignore` files
- bounded backend bootstrap scripts/services/tests; no ORM model or migration
  change
- deterministic release-context/build/plan verification scripts
- `.ai/review-runs/T082-AWS-INVITE-PILOT-C/**` and bounded deployment docs

Preserved T081 Slice 4B artifacts, `backend/app/models/core.py`, every 0030
artifact, unrelated application behavior, Git index/commit, cloud mutation, and
paid OCR activation are excluded.

## Known uncertainty

- The user-owned pilot hostname/Route53 zone and real budget notification
  recipient remain operator inputs. Implementation may parameterize and test
  them but cannot produce an execution-ready plan without them.
- The exact operator-admin principal authorized to update the deploy policy is
  also an explicit Package E input. The existing bootstrap user is not assumed
  to have that authority.
- Live ACM/WAF/Route53 state is unknown because the current deploy role is
  denied read access. The reviewed policy prerequisite must land before final
  plan/apply evidence.
- Required service-linked roles are absent. Their constrained creation is a
  prerequisite, not an apply-time surprise.
- Local image digests are not ECR digests. Package E must bind pushed digests
  and prove ECS uses those exact values.
- Runtime cost, certificate issuance time, DNS propagation, RDS restore, and
  deployed browser behavior cannot be proven by Package C.

## Model routing

- Design builder: `/root`.
- Preferred route: GPT-6 Astra xhigh because Package C defines IAM, migration
  authority, secret delivery, HTTPS/WAF, and immutable release boundaries.
- Actual builder model: `model not exposed by runtime`.
- Actual builder effort: `effort not exposed`.
- Independent reviewer: `/root/t082_pilot_design_adversary`; GPT-6 Astra xhigh
  requested, actual model and effort not exposed by runtime.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/findings.json`

size=15020; sha256=5f87531f4e8d7ddd28474175d48dfb6229d607e90ac96217ed2d991d08c217c5

```text
[
  {
    "id": "T082-C-001",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The credential-bearing migration/bootstrap execution path contains only explicitly reviewed sealed authority files and dependencies.",
    "summary": "Reusing the backend application image exposes the entire application checkout to migration credentials.",
    "evidence": ["adversarial-design-initial.md", "backend/Dockerfile", "../T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md"],
    "impact": "Unreviewed application or dirty-tree code could execute with RDS administrator and secret-publication authority.",
    "requiredClosure": "Use a dedicated digest-pinned sealed bootstrap image and prove the full execution path excludes application checkout files, mounts, and import overrides.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-002",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Deployment bootstrap can create platform administration exactly once on an empty authority state, atomically and under serialization.",
    "summary": "The no-active-admin guard can reopen after revocation and has no concurrent first-use semantics.",
    "evidence": ["adversarial-design-initial.md", "decision.md", "../T082-AWS-INVITE-PILOT/decision.md"],
    "impact": "A later or racing bootstrap could create an unauthorized platform administrator.",
    "requiredClosure": "Define a permanent first-use sentinel and serialized atomic creation with populated, revoked-prior, concurrent, and rollback tests.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-003",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every AWS prerequisite action is granted only to an identified authorized principal and matches the exact resource names used by Terraform/runtime.",
    "summary": "Secret resource patterns and policy-updater authority do not match the proposed infrastructure.",
    "evidence": ["adversarial-design-initial.md", "infra/aws-iam/paprnav-terraform-deploy-policy.json", "infra/aws-iam/paprnav-terraform-bootstrap-assume-policy.json", "infra/terraform/database.tf"],
    "impact": "Planning/apply can fail late or require an undocumented privilege escalation.",
    "requiredClosure": "Add an exact action/resource/principal matrix for secrets and prerequisites and identify an explicit operator-admin update gate.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-004",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "The runtime database role cannot mutate migration control state and credential rotation cannot strand runtime access.",
    "summary": "Broad default grants could include alembic_version and password/secret publication lacks recovery semantics.",
    "evidence": ["adversarial-design-initial.md", "decision.md"],
    "impact": "Runtime could advance migration metadata or a partial rotation could make the application secret unusable.",
    "requiredClosure": "Freeze explicit post-migration grants excluding control tables and a recoverable password-publication protocol.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md", "adversarial-design-closure-2.md"]
  },
  {
    "id": "T082-C-005",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "WAF protections preserve the reviewed authenticated multipart upload workflow without weakening public auth controls.",
    "summary": "Managed common body-size protection is incompatible with the application's 100 MiB multipart upload boundary unless scoped.",
    "evidence": ["adversarial-design-initial.md", "backend/app/api/routes/uploads.py", "backend/app/core/config.py"],
    "impact": "Valid pilot uploads could be blocked at the public edge.",
    "requiredClosure": "Define path-scoped body-size handling and multipart acceptance evidence while retaining auth rate limits.",
    "closureEvidence": ["design-remediation-1.md", "adversarial-design-closure-1.md"]
  },
  {
    "id": "T082-C-006",
    "stage": "design",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Every meaningful design/review phase records builder and reviewer identity, exact model or runtime non-disclosure, effort or runtime non-disclosure, and routing trigger.",
    "summary": "The reviewed Package C decision and remediation artifact omitted mandatory model-routing sections.",
    "evidence": ["adversarial-design-closure-1.md", ".ai/MODEL_ROUTING.md"],
    "impact": "The design cannot close under repository policy without auditable routing evidence.",
    "requiredClosure": "Add accurate routing sections without rewriting immutable review artifacts and obtain independent verification from a regenerated packet.",
    "closureEvidence": ["decision.md#model-routing", "design-remediation-1.md#model-routing", "adversarial-design-closure-2.md"]
  },
  {
    "id": "T082-C-007",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every runtime database-secret consumer receives the published DATABASE_URL value rather than the enclosing JSON document.",
    "summary": "ECS injects the whole JSON application secret into DATABASE_URL.",
    "evidence": ["adversarial-implementation-initial.md", "infra/bootstrap/bootstrap.py", "infra/terraform/ecs_runtime.tf"],
    "impact": "The API and worker fail database configuration at startup.",
    "requiredClosure": "Select the DATABASE_URL JSON key for all consumers and retain a configuration-level regression test.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/ecs_runtime.tf", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-008",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "All valid generated database credentials survive migration URL construction and Alembic configuration parsing unchanged.",
    "summary": "Reserved password characters can trigger ConfigParser interpolation failure before migration connects.",
    "evidence": ["adversarial-implementation-initial.md", "infra/bootstrap/bootstrap.py", "backend/app/db/migrations/env.py"],
    "impact": "A valid managed administrator password can make fresh-database bootstrap fail.",
    "requiredClosure": "Remove or correctly escape the interpolation boundary and retain reserved-character cases.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/bootstrap/bootstrap.py", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-009",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Invalid external deployment inputs and mismatched immutable image repositories prevent plan or apply.",
    "summary": "Terraform check blocks warn instead of enforcing execution gates.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/variables.tf", "infra/terraform/main.tf"],
    "impact": "A malformed or wrong-target pilot configuration can proceed to mutation.",
    "requiredClosure": "Use blocking validation/preconditions, verify hosted-zone identity, and retain negative assertions.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/main.tf", "infra/terraform/variables.tf", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-010",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Every routed login and invitation-accept variant is subject to its reviewed edge rate limit.",
    "summary": "Encoded auth paths accepted by FastAPI bypass raw WAF path predicates.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/load_balancer.tf"],
    "impact": "Attackers can bypass endpoint-specific public authentication throttles.",
    "requiredClosure": "Align WAF classification with routed-path semantics for encoded and redirect variants without weakening uploads.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "infra/terraform/load_balancer.tf", "backend/tests/test_pilot_package_c.py", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-011",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "WAF observability does not retain session-bearing request-header values.",
    "summary": "Enabled WAF request sampling can retain Cookie values.",
    "evidence": ["adversarial-implementation-initial.md", "infra/terraform/load_balancer.tf"],
    "impact": "Session credentials can be exposed through sampled-request access.",
    "requiredClosure": "Disable sampling or prove effective sensitive-header protection for every enabled sampling configuration.",
    "closureEvidence": ["package-c-remediation-1.md", "infra/terraform/load_balancer.tf", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-012",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Certificate mutations are limited to reviewed Paprnav-owned resources and ownership cannot be self-manufactured.",
    "summary": "Generated ACM permissions permit tagging and deleting any regional account certificate.",
    "evidence": ["adversarial-implementation-initial.md", "scripts/generate_pilot_deploy_policy.py"],
    "impact": "The deploy role could alter or delete unrelated certificates.",
    "requiredClosure": "Constrain mutation by ownership without granting unrestricted ownership tagging and retain policy assertions.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md", "scripts/generate_pilot_deploy_policy.py", "infra/aws-iam/pilot-policy-matrix.json", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-013",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Release contexts are derived only from the approved candidate commit and protected authority blobs while unrelated preserved dirt is excluded explicitly.",
    "summary": "The release builder omits Package A authority verification and cannot represent the approved preserved dirty-tree workflow.",
    "evidence": ["adversarial-implementation-initial.md", "scripts/build_pilot_release_context.py", ".ai/pilot-package-c-context-v1.json"],
    "impact": "Unreviewed protected bytes could enter images or valid pilot builds could be impossible from the preserved tree.",
    "requiredClosure": "Enforce one candidate authority gate, model preserved exclusions separately, and retain positive and negative tests.",
    "closureEvidence": ["package-c-remediation-1.md", "scripts/build_pilot_release_context.py", ".ai/pilot-package-c-context-v1.json", "backend/tests/test_pilot_package_c.py"]
  },
  {
    "id": "T082-C-014",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Package C has retained bounded regression evidence and locally constructible evidence for all three reviewed images.",
    "summary": "New Package C components lack a retained regression suite and local three-image evidence.",
    "evidence": ["adversarial-implementation-initial.md", "package-c-implementation.md"],
    "impact": "The implementation cannot be reproduced or protected from immediate regression before deployment inputs exist.",
    "requiredClosure": "Retain bounded bootstrap, context, IAM, and WAF tests and produce local three-image evidence while leaving live inputs to Package E.",
    "closureEvidence": ["package-c-remediation-1.md", "package-c-remediation-2.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md", "backend/tests/test_pilot_package_c.py", "infra/terraform/tests/package_c.tftest.hcl"]
  },
  {
    "id": "T082-C-015",
    "stage": "implementation",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The internet-facing frontend does not expose a known unauthenticated WebSocket SSRF path in its production server.",
    "summary": "The production image contains vulnerable Next.js 16.1.6 and the edge does not block WebSocket upgrades.",
    "evidence": ["adversarial-implementation-remediation-1.md", "frontend/paprnav-frontend/package.json", "frontend/paprnav-frontend/package-lock.json"],
    "impact": "An unauthenticated client could induce server-side requests from the public frontend process.",
    "requiredClosure": "Upgrade to a maintainer-patched Next.js release and rebuild/revalidate, or prove the maintainer's upgrade-blocking mitigation before exposure.",
    "closureEvidence": ["package-c-remediation-2.md", "adversarial-implementation-remediation-2.md", "frontend/paprnav-frontend/package.json", "frontend/paprnav-frontend/package-lock.json", "frontend/paprnav-frontend/Dockerfile"]
  },
  {
    "id": "T082-C-CLOSURE-001",
    "stage": "closure",
    "reviewer": "/root/t082_pilot_design_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Final closure artifacts enumerate every meaningful phase, role, identity, requested route, and actual model and effort or runtime non-disclosure.",
    "summary": "The closure reports omitted a complete mandatory model-assignment summary.",
    "evidence": ["adversarial-closure-initial.md", ".ai/MODEL_ROUTING.md", "closure.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md"],
    "impact": "The high-risk package cannot close without auditable model-routing evidence.",
    "requiredClosure": "Add complete Model assignments sections to both closure reports, preserving historical artifacts, and obtain documentation/integrity re-attestation.",
    "closureEvidence": ["closure.md", "../T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md", "adversarial-closure-final.md"]
  }
]

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md`

size=6004; sha256=be294c079ae5cdebfcc5afa59939c30a0ce8026c9a57da027718a5166643340e

```text
# Closure report: T082-AWS-INVITE-PILOT-C

## Outcome

Package C's local implementation is complete and independently implementation-
reviewed for the AWS invite-pilot boundary. It supplies deterministic and
authority-verified release contexts, sealed database bootstrap, three non-root
images, HTTPS/ALB/WAF/ECS/RDS Terraform with services fixed at zero, read-only
operator-provisioned certificate consumption, and least-privilege prerequisite
IAM. This closure does not authorize AWS mutation or claim deployed evidence.

## Invariants verified

- Release contexts fail closed on candidate/protected-authority drift and keep
  reviewed inputs distinct from explicitly preserved exclusions.
- API, frontend, and bootstrap images are digest-ready, non-root, and exclude
  the reviewed forbidden content; the bootstrap image contains no app checkout.
- Database bootstrap is idempotent, serializes permanent first-admin creation,
  survives bounded rollback points, publishes the app secret without reading
  it back, and grants only the exact runtime inventory.
- Terraform invalid inputs, zone/certificate identity, and image-repository
  mismatches block execution rather than warn.
- WAF classification covers encoded/redirect authentication routes, preserves
  the exact raw upload exception, and disables request sampling.
- The deploy role cannot create, tag, untag, delete, or export ACM
  certificates. The listener consumes one verified, issued, owned,
  operator-provisioned certificate.
- The production frontend uses patched Next.js 16.2.5; the reviewed standalone
  image contains no 16.1.6 package.
- API/frontend desired counts remain zero and the worker remains disabled until
  separately authorized activation.

## Findings disposition summary

T082-C-001 through T082-C-015 are closed with recorded design,
implementation, remediation, test, image, and amendment evidence. No blocker,
accepted risk, or deferred finding remains in this run.

## Verification performed

- Independent design review passed after two remediation rounds.
- Independent implementation review passed after two coherent remediation
  families and the independently approved ACM amendment.
- Focused retained Python/PostgreSQL evidence passed, including rollback,
  concurrency, permanent-use, secret/config, release-authority, IAM, WAF, and
  generated-structure cases.
- Terraform 1.15.0 with pinned AWS provider 5.100.0 validated; retained mocked
  plan gates passed, including the final twelve-run ACM family.
- API, frontend, and bootstrap images built locally as linux/amd64 non-root
  images; the patched frontend standalone image passed bounded smoke checks.
- Final scoped packets were current with unchanged product hashes; the parent
  and ACM child implementation PASS attestations are recorded.

## Final scope reviewed

`.ai/pilot-package-c-context-v1.json`, Package C release/IAM generators,
bootstrap image/program/manifests, API/frontend Docker inputs, focused Package C
tests, Terraform network/database/ECS/ALB/WAF/DNS/certificate-read inputs and
mock tests, frontend dependency lock, and the ACM amendment decision,
implementation, consumers, and review history. Preserved T081, 0030, Package B,
and unrelated application changes were excluded but inventoried.

## Accepted risks and deferred work

None in the Package C finding ledger. Remaining work below is an execution gate
owned by Package E, not an accepted implementation defect.

## Not verified

- Real hostname/zone/certificate/KMS/budget-recipient/updater inputs.
- Real backend state absence for removed certificate resource addresses.
- Live ACM/Route53/IAM inventory, Access Analyzer/policy simulation, and an
  authorized refreshing Terraform plan.
- Candidate commit and pushed ECR digests.
- AWS secret writes, migration/bootstrap execution, service activation, TLS,
  WAF, browser, database, observability, cost, and rollback proof.
- Remaining npm audit entries beyond the independently dispositioned production
  paths; their conditional exclusions must be revisited if features change.

## Model assignments

| Phase | Role and identity | Requested route | Actual runtime metadata |
| --- | --- | --- | --- |
| Coordination and initial design | Coordinator/designer `/root` | Repository risk policy; no override recorded | model not exposed by runtime; effort not exposed |
| Design adversary and design remediation closure | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| Initial implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Remediation 1 after first failed implementation review | Builder `/root/t082_package_c_remediation_1` | GPT-5.6 Sol xhigh | model not exposed by runtime; effort not exposed |
| Remediation 2 after repeated finding family | Builder `/root/t082_package_c_remediation_2` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| ACM amendment design | Designer `/root` | High-risk IAM amendment; no exposed override | model not exposed by runtime; effort not exposed |
| ACM amendment design review | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| ACM amendment implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Combined implementation review and integrity attestations | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra high or stronger | model not exposed by runtime; effort not exposed |
| Final closure review and documentation re-attestation | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |

Builder/reviewer separation was preserved for every review boundary. No
user-visible task was created merely to switch models.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md`

size=4173; sha256=b88979d7bd77c7f14edb5fcb2aaa45569897ed3473b57d77e002dfe9f307bad6

```text
# Package C and ACM amendment combined implementation review — PASS

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Parent remediation builder: `/root/t082_package_c_remediation_2`.
- ACM amendment builder: `/root/t082_package_c_implementation`.
- Requested reviewer capability: GPT-6 Astra, high or stronger.
- Actual reviewer model: `model not exposed by runtime`.
- Actual reviewer effort: `effort not exposed`.
- Trigger: complete-family re-review of recurrent WAF/IAM findings and the
  independently approved certificate-ownership amendment.

## Outcomes

- Parent `T082-AWS-INVITE-PILOT-C`: **PASS**.
- Child `T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT`: **PASS**.

No new implementation blocker or high finding remains.

## Finding dispositions

- **C-010 closed.** Both authentication rules apply `URL_DECODE` to URI
  matching and `NONE` to POST matching. Encoded and trailing-slash variants
  are covered; the raw multipart upload exception is unchanged.
- **C-012 closed through the child amendment.** Terraform no longer manages
  certificate creation, validation, or validation records. Generated ACM
  permissions contain exactly the four approved read actions and exclude all
  mutation and `ExportCertificate`.
- **C-014 closed.** The WAF oracle consumes generated Terraform structures and
  rejects the prior misplaced-transform mutation. IAM assertions bind actual
  generated actions, resources, and conditions. Earlier image/bootstrap
  evidence retains its stated limitations.
- **C-015 closed.** Source and lockfile pin Next.js and its lint configuration
  to 16.2.5. Reviewed build inputs and retained production evidence identify
  16.2.5 in the standalone image with the recorded non-root smoke checks.

Independent targeted verification passed: three tests passed with eight
deselected, covering Terraform structure, the generated WAF/mutation oracle,
and ACM policy. `git diff --check` passed. No broad suite or image rebuild was
performed by the reviewer.

## ACM amendment verification

The provider is pinned to 5.100.0. Terraform requires an exact certificate ARN
and performs a plan-time, ambiguity-rejecting lookup for the exact primary
domain, issued Amazon certificate, RSA_2048 key, and `Project=paprnav` tag.
Blocking gates bind returned ARN, domain, status, tag, account, and region.
The HTTPS listener consumes the verified lookup; the application alias remains;
certificate-management and validation-record resources are absent.

Generated ACM IAM is limited to `ListCertificates`, `DescribeCertificate`,
`ListTagsForCertificate`, and `GetCertificate`. The retained tests cover the
negative identity cases; the builder's twelve mock plans passed. Real
zero-match and ambiguity behavior is provided by pinned provider behavior and
remains subject to Package E's read-only real plan.

The handoff requires backend-state preflight before any plan, preservation of
renewal records, and operator/certificate evidence. If a removed resource
address exists in state, execution stops for a separately reviewed handoff.

## Packet integrity

The reviewer verified the explicit non-recursive scopes and confirmed no
product drift from the technical baseline.

- Parent packet SHA-256:
  `14876ad96b665382f6c60dc0abfef31d91881521ae954bb77e99fac7efd4eb18`;
  fingerprint
  `c164144dc793ed72a3d465d24cc2bd56e1a83a385d71339816b68c21ee2a9832`;
  35 product hashes checked.
- Child packet SHA-256 before this immutable report was added:
  `387df082c2a6148bbd5744d4e01c4dc19ca93f16387cb2e386553ced9a3666c1`;
  fingerprint
  `beaaaf9ef79b48d7bb8421ad8392e0721cc0ca105c0bcc852195990dcf6a3bf5`;
  12 product hashes checked. A mechanical child refresh binds the added report
  path without repeating technical review.

## Residual execution gates

Real operator inputs, backend-state inspection, certificate inventory and DNS
validation evidence, final committed candidate, pushed image digests,
refreshing plan, and Package E runtime/database/browser proofs remain required.
The remaining npm audit findings are not declared resolved. No review edit,
staging, commit, live plan, cloud action, broad suite, or image rebuild
occurred.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md`

size=2190; sha256=2449afbc8b37cb0d4631db14b53bd6a0f7f07d6dac44c677adeae00ce86e7c6e

```text
# Package C and ACM amendment closure review — FAIL

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: final infrastructure/IAM/bootstrap closure.

## Outcomes

- Parent Package C: **FAIL — closure documentation only**.
- ACM amendment child: **FAIL — closure documentation only**.

Implementation PASS outcomes remain valid; no source defect or product drift
was found.

## T082-C-CLOSURE-001 — Blocker — Incomplete final model assignments

The parent closure lists requested builder models but omits their explicit
actual/unexposed metadata. Both closure reports lack the mandatory
`## Model assignments` summary covering design, implementation, remediation,
implementation review, and closure review.

Close by adding complete phase and identity assignments to both reports,
distinguishing requested routing from actual metadata with
`model not exposed by runtime` and `effort not exposed`. Include the current
closure reviewer. Preserve immutable historical reports. Only documentation
and packet-integrity re-attestation are required.

## Otherwise verified

- C-001 through C-015 are closed and all closure evidence exists.
- The child ledger had no implementation finding; independent design and
  implementation attestations exist.
- Every recorded review artifact hash matched and builders differ from the
  reviewer.
- No product drift: parent 35 files and child 12 files.
- Git index is empty and HEAD unchanged. No reviewer write, test, rebuild, or
  cloud action occurred.
- Verified and unverified evidence and Package E boundaries are separated.

The parent packet fingerprint was
`63e26f02afec26448d7b3d1e3fd9ba7a51162c6495eb00a32cc59ddc32cf927b`;
the child fingerprint was
`3cae142d9d6ad213d25003b27f29bbf62e140c956c27fb6ca9d1e745d945f8b3`.

Package E still requires backend-state preflight, certificate/operator and
renewal evidence, approved candidate commit, pushed ECR digests, an authorized
refreshing plan, and bootstrap/deployment/TLS/WAF/browser/observability/cost/
rollback proofs before activation.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md`

size=1386; sha256=6cac47d08e19ce92461c10ca62e1406912d72971f0037d7a78f236446c57c83c

```text
# Package C and ACM amendment final closure review — PASS

## Outcomes

- Parent Package C: **FINAL CLOSURE PASS**.
- ACM amendment child: **FINAL CLOSURE PASS**.

T082-C-CLOSURE-001 is closed. Both `## Model assignments` sections cover the
required phases, identities, requested routes, and exact runtime non-disclosure
wording. No implementation finding was reopened.

## Integrity

The reviewed parent packet SHA-256 was
`a9dfc2cb8fac074f2da01126053b3fac9eabdd1f6f81f308c309d8ef6ef0f610`
with fingerprint
`54cd8f688bbbad7eafcec0ad99a51fcb14323df16582e9ad6a5e049e441483ba`.
The reviewed child packet SHA-256 was
`3b3177b643ab86bb4e55f682b57d1804eaddfccac3c269e6f794378da4a27f0c`
with fingerprint
`5235a8c6988da2142177885b72a27a511159fa5d105e5e6ec343f02603c7fc49`.
Declared out-of-scope inventories matched. Parent 35 and child 12 product
hashes were unchanged with zero drift.

No write, test, implementation re-review, staging, commit, or cloud action
occurred during the closure re-attestation. All Package E execution gates remain
required; closure does not authorize AWS activation.

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: final closure re-attestation after remediation of mandatory model-
  assignment evidence.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md`

size=7700; sha256=5530a6fc969d1133b7c638307ec43aa50861efb2bfd7d720dfd5d83ca0bae7c7

```text
# Decision packet: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

## Objective

Remove the unresolved ACM ownership bootstrap conflict from Package C without
granting the Terraform deploy principal authority to manufacture ownership on
an unrelated certificate. Preserve an HTTPS-ready invite pilot by treating the
certificate as an operator-provisioned, independently owned prerequisite that
Terraform verifies and consumes read-only.

## User-visible outcome

Invited users still reach the pilot over the canonical HTTPS hostname. The
deployment cannot create, retag, or delete certificates; it can only attach the
one already-issued Paprnav-owned certificate supplied for that hostname.

## Safety and correctness invariants

1. The Terraform deploy principal has no ACM mutation action, including
   `RequestCertificate`, `AddTagsToCertificate`, `RemoveTagsFromCertificate`,
   or `DeleteCertificate`.
2. An operator supplies one exact certificate ARN after provisioning and DNS
   validation through separately authorized administration.
3. Terraform fails before resource mutation unless the resolved certificate is
   issued, in the deployment region and account, covers the exact canonical
   pilot hostname, carries `Project=paprnav`, and resolves to the supplied ARN.
4. The HTTPS listener consumes that verified ARN; Terraform does not create
   ACM validation records or manage certificate lifecycle.
5. The deployment may still create the application Route53 alias after the
   existing hosted-zone identity gate passes.
6. Certificate provisioning evidence and identity are recorded as Package E
   execution inputs; they are not fabricated by local tests.

## Current behavior

Package C declares an `aws_acm_certificate`, DNS validation records, and an
`aws_acm_certificate_validation` resource. Immutable ownership correctly bars
the deploy principal from later changing the `Project` tag, but AWS maps tagged
`RequestCertificate` to the dependent `AddTagsToCertificate` authorization.
No documented condition safely distinguishes initial ownership assignment from
direct self-tagging of an existing unowned certificate. The strongest safe IAM
policy therefore blocks the current creation flow.

## Proposed design

- Remove the certificate and certificate-validation resources from Package C.
- Add required `pilot_certificate_arn` input and retain the canonical
  `pilot_hostname`, region, account, and public hosted-zone inputs.
- Resolve the unique issued Amazon certificate for the exact hostname with the
  AWS provider's read-only ACM data source, filtered by `Project=paprnav`.
  Add blocking preconditions that its returned ARN equals the supplied ARN and
  that the ARN encodes the configured region/account. The design reviewer must
  confirm the provider data source exposes enough status/domain/tag evidence;
  if not, implementation stops rather than weakening the invariant.
- Point the HTTPS listener directly at the verified supplied ARN.
- Replace generated ACM mutation permissions with only the read actions needed
  by that data lookup and plan. Retain explicit assertions that no ACM mutation
  action is emitted.
- Package E records the operator principal, certificate ARN, domain, status,
  ownership tag, and validation state before an authorized plan/apply.

## Alternatives considered

- **Grant tag-on-create authority to the deploy role:** rejected because the
  supported conditions do not prove that the same permission cannot directly
  assign ownership to an existing certificate.
- **Create a dedicated certificate-provisioning role/workflow:** defensible but
  unnecessary machinery for the invite-pilot MVP. It can be designed later if
  recurring automated certificate lifecycle becomes valuable.
- **Block WebSocket/TLS at another proxy or use an unverified certificate:**
  rejected; neither resolves ownership authority or provides the required
  public HTTPS boundary.

## Trust, authorization, and audit boundaries

The separately authorized operator is the sole certificate-provisioning and
initial-ownership authority. The Terraform deploy role receives read-only ACM
discovery/description authority and cannot create, tag, untag, or delete. The
reviewed hostname, zone, account, region, ownership tag, and exact ARN form the
handoff contract. Package E must retain the real AWS evidence and identity of
the operator; local mocks prove only fail-closed wiring.

## Read paths and consumers

- Terraform ACM data lookup reads the issued certificate metadata.
- Blocking preconditions consume certificate ARN, canonical hostname, region,
  account, status/type, and ownership tag evidence.
- The ALB HTTPS listener consumes only the verified ARN.
- Package E runbook and execution packet consume the operator evidence.

## Write paths and administrative paths

- Package C writes no ACM resource.
- The operator provisions and validates the certificate outside this Terraform
  deployment under separately authorized administration.
- Terraform retains its existing Route53 application-alias write after zone
  identity verification; it no longer writes certificate-validation records.

## Migration, compatibility, correction, and rollback

No Package C resources have been applied, so this is a pre-deployment contract
change with no Terraform state migration or cloud deletion. A wrong, missing,
unissued, differently tagged, cross-account, cross-region, or hostname-mismatched
certificate must stop planning. Correction is to supply or provision the right
certificate. Rollback to Terraform-managed certificate creation is forbidden
without a new reviewed ownership-authority design.

## Test strategy

- Retained Terraform mock plans: valid exact certificate; wrong ARN; wrong
  hostname/status/tag/account/region; ambiguous or absent lookup where the
  provider supports those fixtures.
- Retained IAM generator assertions: exact read actions needed by the data
  source and zero ACM mutation actions.
- Structural assertion: HTTPS listener uses the verified supplied ARN and no
  ACM certificate/validation or validation-record resource remains.
- Existing focused Package C WAF, secret, bootstrap, authority, image, and
  Next.js evidence remains valid unless a changed dependency can affect it.
- Package E supplies real read-only ACM/Route53 inventory and an authorized
  refreshing plan; mocks do not substitute for this evidence.

## Expected file scope

- `infra/terraform/load_balancer.tf`
- `infra/terraform/variables.tf`
- `infra/terraform/outputs.tf` if certificate output semantics change
- `infra/terraform/tests/package_c.tftest.hcl`
- `scripts/generate_pilot_deploy_policy.py`
- `infra/aws-iam/pilot-policy-matrix.json`
- `backend/tests/test_pilot_package_c.py`
- Package C builder/review artifacts

No Package A sealed authority, T081 Slice 4B, 0030 artifact, application model,
or public API contract is in scope.

## Known uncertainty

The AWS provider data source's exact selection and exposed metadata must be
confirmed from the installed provider schema during implementation. Real AWS
certificate inventory remains unavailable to the current deploy principal and
is a Package E prerequisite. If exact read-only verification cannot be
expressed, the amendment returns to design review rather than granting
mutation authority.

## Model routing

- Coordinator: `/root`; actual model and effort are not exposed by runtime.
- Amendment designer: `/root`; actual model and effort are not exposed by
  runtime.
- Required independent reviewer: `/root/t082_pilot_design_adversary`, requested
  GPT-6 Astra xhigh.
- Trigger: ambiguous IAM/resource-ownership design discovered after a repeated
  high-risk implementation finding.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md`

size=3204; sha256=7686652eeab60357e05ed088b81565aa58e08b547ceba7a53ad2fc38989d73b0

```text
# ACM amendment design review — PASS

## Model routing

- Designer: `/root`.
- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: ambiguous certificate ownership authority discovered after a
  repeated high-risk implementation finding.

## Outcome

No blocker or high finding. Operator-provisioned ACM ownership is a simpler,
viable invite-pilot boundary. This approves design only, not implementation or
deployment.

## Provider and authorization contract

Pinned AWS provider 5.100.0 supports exact primary-domain lookup with
`statuses = ["ISSUED"]`, `types = ["AMAZON_ISSUED"]`,
`tags = { Project = "paprnav" }`, and `most_recent = false`, which rejects
ambiguous matches. It returns ARN, domain, status, and tags. Certificate type
is established by the fixed selection filter because there is no singular
returned `type` attribute. The operator contract and lookup must also select a
supported key algorithm; RSA_2048 is sufficient for this pilot.

Blocking checks must bind returned metadata to the exact supplied ARN, account,
region, and primary hostname. The lookup must remain plan-time with known
inputs, and the HTTPS listener must consume its verified result.

The complete read-only lookup requires exactly:

- `acm:ListCertificates`
- `acm:DescribeCertificate`
- `acm:ListTagsForCertificate`
- `acm:GetCertificate`

`GetCertificate` returns the public certificate and chain, not the private key.
No ACM mutation or `ExportCertificate` permission is required. Candidate
discovery occurs before tag filtering, so account/region-bounded certificate
metadata reads are acceptable and do not manufacture ownership.

## Handoff, correction, and state

Removing certificate, validation, and validation-record resources is coherent;
the application alias and HTTPS listener remain the intended consumers.
Package E must verify actual backend/state before execution. If any removed
resource address exists, execution stops for a separately reviewed state
handoff because configuration removal could otherwise schedule destruction.

Operator evidence must retain certificate identity, issuance/type, primary
hostname, ownership, DNS-validation evidence, principal, and timestamp.
Validation records remain in place for renewal. Replacement preserves the
currently serving certificate until the new attachment is verified. Multiple
matching owned certificates intentionally block planning; no automatic delete
or retag resolution is allowed.

## Verification and scope

Packet SHA-256 matched
`b6783d36b68c063dc820e50160e406fc7742f556ffce0a81dca9cc7f8eeb7ea6`.
Packet-current verification passed with fingerprint
`31841c31563b1ab64932fe9d4933ef5b0e8ea90dafac620bf34b687615639cf2`.
The reviewer inspected the amendment, parent design/review/remediation history,
current Terraform/IAM generator/tests and consumers, committed baseline, and
dirty inventory. Provider schema extraction was blocked by uninitialized
backend configuration, so conclusions use the exact pinned provider source.
No files changed, tests ran, or cloud actions occurred during review.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md`

size=5755; sha256=d0b59236477d6e1cd30cba5ae54750b76226bebb5f97f29d4625e670ef40c4d1

```text
# ACM amendment implementation builder handoff

## Assignment and result

- Builder: `/root/t082_package_c_implementation`.
- Requested route: GPT-5.6 Sol, high effort.
- Actual model and effort: not exposed by the delegated runtime.
- Role: implementation builder only. Independent implementation review and
  approval remain coordinator-owned.

The bounded amendment is ready for independent review. Terraform no longer
declares or validates an ACM certificate or writes ACM validation records. A
required exact certificate ARN is bound to a plan-time, read-only lookup and
its returned ARN, primary domain, issued status, ownership tag, account, and
region before the HTTPS listener can consume it. The application Route53 alias
and its existing hosted-zone identity gate remain. Generated ACM IAM is exactly
`ListCertificates`, `DescribeCertificate`, `ListTagsForCertificate`, and
`GetCertificate`; it contains no wildcard ACM action, mutation action, or
`ExportCertificate`. This handoff is not an approval or deployment authority.

## Provider feasibility evidence

AWS provider 5.100.0 was checked before implementation from the installed
offline schema and the exact tagged provider source. The schema exposes the
required `domain`, `statuses`, `types`, `key_types`, `tags`, `most_recent`,
`arn`, and `status` fields. The tagged implementation performs exact-domain,
status, type, key, and tag filtering; with `most_recent=false` it errors on
multiple matches and also errors on no match. It calls `GetCertificate` for an
issued result. The configuration now pins `= 5.100.0` rather than a provider
range.

- `.terraform.lock.hcl` SHA-256:
  `a2ded1ea551540bbc25f53cd1a941cc1af985df90ab1d3eca2f8d6df467b1808`
- Installed Linux provider binary SHA-256:
  `6c0d4e10cf57e3fcaad0055f7149a32f66e24a63d75e78fe6c8e39013964bfb9`
- Extracted provider-schema JSON SHA-256:
  `a81108c4ed4baa5d7d936384ee6978f2bf8116831b3f171086273fb666227964`
- Tagged source:
  `https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/v5.100.0/internal/service/acm/certificate_data_source.go`

## Bounded checks

- Isolated source-only Terraform 1.15.0 with cached AWS provider 5.100.0,
  backend removed, network disabled, and no state copied or read:
  `terraform validate -no-color` passed.
- Retained mock plans:
  `terraform test -no-color -filter=tests/package_c.tftest.hcl` passed,
  12 runs. These cover the valid lookup; wrong exact ARN, returned domain,
  returned status, returned tag, account, and region; preserved WAF contract;
  and existing negative deployment gates. The valid run asserts the exact
  issued/Amazon-issued/RSA_2048/Project filters and `most_recent=false`.
- `PYTHONPATH=backend backend/.venv/bin/python -m pytest
  backend/tests/test_pilot_package_c.py -q -k 'terraform_gates or acm_policy'`:
  2 passed, 9 deselected; one existing Starlette deprecation warning.
- Python compilation and `git diff --check`: passed.
- No live Terraform plan, apply, AWS read, certificate/DNS mutation, image
  rebuild, staging, or commit was performed.

Mock-provider fixtures cannot exercise the provider's real zero-match or
multiple-match search result. Those cases remain fail-closed in the pinned
provider implementation and are made structurally mandatory by
`most_recent=false`; Package E must supply real read-only lookup/plan evidence.

## Changed files and hashes

| File | SHA-256 |
| --- | --- |
| `infra/terraform/versions.tf` | `eb83c7bbbee497ea0f928408b58d12fe7ac2120d08d41f427c091988ed03a6cf` |
| `infra/terraform/variables.tf` | `8ab402c401f0d394e0ae715654477c4ef2d914cdcb8614a2af4cc24a6442012f` |
| `infra/terraform/main.tf` | `cfb8cfe8890dafc421d462731bce87405baa3b0ae1c847ab70380c99b5b6f4ea` |
| `infra/terraform/load_balancer.tf` | `8ee9a4afc3f5c9330ce77283cb00a89e787ee1cab1c0f85d9a9536344d37a48f` |
| `infra/terraform/outputs.tf` | `6dd533bde5befa1f9540f537fffcc5f4ec3ee4ce979fb365c9c8a681a91a42d8` |
| `infra/terraform/tests/package_c.tftest.hcl` | `571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c` |
| `scripts/generate_pilot_deploy_policy.py` | `46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e` |
| `infra/aws-iam/pilot-policy-matrix.json` | `553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2` |
| `backend/tests/test_pilot_package_c.py` | `3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124` |

This evidence file is intentionally not self-hashed.

## Package E execution preflight and residual inputs

Before any authorized real plan or apply, Package E must record the operator
identity and timestamp and inspect the real backend with a read-only state
listing. If any of these removed addresses exist, stop before planning and
obtain a separately reviewed state handoff: `aws_acm_certificate.pilot`,
`aws_acm_certificate_validation.pilot`, or any
`aws_route53_record.certificate_validation` instance. Configuration removal
must not be allowed to schedule certificate or validation-record destruction.
Existing ACM DNS validation records must remain in Route53 for managed renewal.

Package E evidence must bind the operator principal, timestamp, exact
certificate ARN, primary domain, `ISSUED`/`AMAZON_ISSUED`/`RSA_2048` metadata,
`Project=paprnav`, DNS-validation record presence, state-listing output, and an
authorized refreshing plan. The real hostname/zone, certificate ARN, budget
recipient, updater identity, KMS input, and final ECR digests remain external
inputs and were not guessed. These are blockers to execution-ready evidence,
not blockers to local amendment review.

Package A authority, T081, 0030, `backend/app/models/core.py`, other Package C
remediations, and all reviewer ledgers/state were left untouched by this
amendment builder.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md`

size=3803; sha256=43f945cba5a3ee21de96ea36100d3fae190c91ea4ed335e96da75a1a31deb7f2

```text
# Closure report: T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT

## Outcome

The ACM amendment is locally complete and independently implementation-
reviewed. Package C now consumes one operator-provisioned certificate through a
read-only, plan-time identity gate and grants no certificate mutation authority.
This closure does not authorize provisioning, planning, or applying in AWS.

## Invariants verified

- The deploy role has exactly four ACM read actions and no create, tag, untag,
  delete, export, or wildcard ACM authority.
- Lookup is pinned to provider 5.100.0 and filters the exact primary hostname,
  ISSUED status, AMAZON_ISSUED type, RSA_2048 key, and `Project=paprnav`, with
  ambiguity rejection.
- Blocking checks bind returned ARN, hostname, status, ownership tag, account,
  and region before the HTTPS listener can consume the certificate.
- Terraform does not manage a certificate, certificate validation, or DNS
  validation records; the application alias remains.
- Backend state and retained renewal records must be checked before execution.

## Findings disposition summary

The amendment design review produced no blocker or high finding. The parent
C-012 certificate-ownership finding is closed by the independently reviewed
implementation. The child ledger contains no open, accepted-risk, or deferred
finding.

## Verification performed

- Independent design review passed against pinned provider source and AWS
  authorization semantics.
- Provider offline schema confirmed required filters and returned fields.
- Terraform validation passed; twelve retained mocked plan runs passed.
- Focused structural/IAM tests passed and `git diff --check` passed.
- Independent combined implementation review passed, followed by current scoped
  packet and product-hash attestation.

## Final scope reviewed

Terraform provider/input/data/gate/listener/output and retained mock tests,
generated IAM policy and matrix, focused Package C structural tests, the parent
certificate consumers, and amendment decision/implementation evidence.

## Accepted risks and deferred work

None. Real inventory and execution evidence below are mandatory Package E
gates, not waived defects.

## Not verified

- Operator identity, real certificate ARN/metadata/tag, DNS validation records,
  and renewal behavior.
- Real backend state absence for removed ACM and validation resource addresses.
- Real zero/multiple-match lookup behavior and authorized refreshing plan.
- Cloud mutation or HTTPS listener activation.

## Model assignments

| Phase | Role and identity | Requested route | Actual runtime metadata |
| --- | --- | --- | --- |
| Amendment coordination and design | Coordinator/designer `/root` | High-risk IAM amendment; no exposed override | model not exposed by runtime; effort not exposed |
| Amendment design review | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |
| Amendment implementation | Builder `/root/t082_package_c_implementation` | GPT-5.6 Sol high | model not exposed by runtime; effort not exposed |
| Combined parent/child implementation review and integrity attestations | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra high or stronger | model not exposed by runtime; effort not exposed |
| Initial closure review and documentation re-attestation | Independent reviewer `/root/t082_pilot_design_adversary` | GPT-6 Astra xhigh | model not exposed by runtime; effort not exposed |

The parent remediation builders were `/root/t082_package_c_remediation_1`
(requested GPT-5.6 Sol xhigh) and `/root/t082_package_c_remediation_2`
(requested GPT-6 Astra xhigh); both report `model not exposed by runtime` and
`effort not exposed`. Builder/reviewer separation was preserved.

```

## Changed-file manifest

```json
{
  "taskId": "T082-AWS-INVITE-PILOT-C",
  "stage": "closure",
  "generatedAt": "2026-09-19T19:48:48+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    ".ai/pilot-package-c-context-v1.json",
    "backend/Dockerfile",
    "backend/requirements.lock",
    "backend/tests/test_pilot_package_c.py",
    "frontend/paprnav-frontend",
    "infra/aws-iam/pilot-policy-matrix.json",
    "infra/bootstrap",
    "infra/terraform",
    "scripts/build_pilot_release_context.py",
    "scripts/generate_pilot_deploy_policy.py"
  ],
  "scopeFingerprint": "0cd3490a90f5d119bf5dd4ebebc0363858fec8cdda64d8d0264055c55f5ff224",
  "files": [
    {
      "path": ".ai/pilot-package-c-context-v1.json",
      "status": "??",
      "size": 2637,
      "sha256": "b13c07ce5831eba17221363d07fa3db23ed4a1187b16b47b9e6fe9b020756e41",
      "readStatus": "readable"
    },
    {
      "path": "backend/Dockerfile",
      "status": " M",
      "size": 917,
      "sha256": "e778b77b4cf56b2b9b4a66ddb570fafa0ad3849ef9ad086e0597e3e501b1f6bf",
      "readStatus": "readable"
    },
    {
      "path": "backend/requirements.lock",
      "status": "??",
      "size": 64899,
      "sha256": "729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d",
      "readStatus": "readable"
    },
    {
      "path": "backend/tests/test_pilot_package_c.py",
      "status": "??",
      "size": 27366,
      "sha256": "3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/.dockerignore",
      "status": "??",
      "size": 72,
      "sha256": "eb7532f74421b9e785d8c0e03711f19e80d52ef4b0ebb31f4b9ca20149787606",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/.env.example",
      "status": " M",
      "size": 261,
      "sha256": "330af5f1958cc928f047f1c07b5db547361c865f3fb2ccb4b94f8048600611d3",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/Dockerfile",
      "status": "??",
      "size": 1180,
      "sha256": "3f4e91bd8de248533293750490a4fb7346255a59fd9756965173944cbafab418",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/next.config.ts",
      "status": " M",
      "size": 152,
      "sha256": "fd75d99b0f5a866732b84f4b034bdcd54c22ab03b09654c9b195ada176419f47",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/package-lock.json",
      "status": " M",
      "size": 287312,
      "sha256": "3f4b0a0cce3719c8434611f1133ab78f1ef45971a06b99e2f1f9473b1aa1710a",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/package.json",
      "status": " M",
      "size": 1202,
      "sha256": "838f7488e4eeca4f619cc3811191a5b31f025c8e84f76eb39ffe4913ccbcfa99",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
      "status": "??",
      "size": 3488,
      "sha256": "20e1ba41c07086e00a981e09577e966f27fa2311931f933c8baa40ed2d73f295",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
      "status": " M",
      "size": 5097,
      "sha256": "f076a27dc99d7da98b007502bf7a9ec78db8ba6a88a8ccbea96fbfd8bd1e2297",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
      "status": " M",
      "size": 5612,
      "sha256": "1d2338ac38759343a8babea48efd0719821671d2a81c7b8facd584367c052736",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
      "status": " M",
      "size": 7963,
      "sha256": "ab363fbce7a06211f7508ea2407d62c24498516f44f40c8eea248bcdac01f35f",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
      "status": " M",
      "size": 1780,
      "sha256": "aa0dcb3c035b5180420d0ec5d9912625fde68f3d72d818c2fecc4daf33dcdad2",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": " M",
      "size": 24483,
      "sha256": "6feaa2e9ccdbaefd2e1f2785ce1f5f999e531d7da6e1857f4e57752873c71ba8",
      "readStatus": "readable"
    },
    {
      "path": "frontend/paprnav-frontend/tests/pilot-observability.test.mjs",
      "status": "??",
      "size": 940,
      "sha256": "4b05f4297d57a0f63b5de11e6b2a0786c72f4d258f467fd0085fefe76cb31a2c",
      "readStatus": "readable"
    },
    {
      "path": "infra/aws-iam/pilot-policy-matrix.json",
      "status": "??",
      "size": 2898,
      "sha256": "553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/Dockerfile",
      "status": "??",
      "size": 1238,
      "sha256": "6b2daf14fa8768d436cad4ecffcf4f81af040834dbcc40a4ff2fd51e697f3262",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/bootstrap.py",
      "status": "??",
      "size": 18877,
      "sha256": "11df37c395e8bb2955f8b6f828943119e73dee0ba7b16ff0db49e9f1718073d4",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/grant-manifest.json",
      "status": "??",
      "size": 4295,
      "sha256": "8bb97bb77a72452eb20b2404ce0ad2139bb763ad2917c31833f13ff99aa43fac",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/reference-data.json",
      "status": "??",
      "size": 413,
      "sha256": "9b6c3cdaae15ba1adc968c5bccb2d337e5b36cd875cc45525131b0205dd5728b",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/requirements.in",
      "status": "??",
      "size": 55,
      "sha256": "9824b776ee52fb1c295f9c58daffa783f4adf3bc58f7593cb01899b23a8d8b7f",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/requirements.lock",
      "status": "??",
      "size": 26705,
      "sha256": "221371094f52ace94027bef0da5b06fd8f37827ccfe71cdbeced10f5c2263cc5",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/database.tf",
      "status": " M",
      "size": 2023,
      "sha256": "47370debfe1e71b803ddc821afe70819e44c3d2fd572e2b4f69ca54b6aaa6dcd",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/ecs_runtime.tf",
      "status": " M",
      "size": 15832,
      "sha256": "6f0c3e1296ff67269841d421fbf94f404036676a3ef36654f73240d794633891",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/load_balancer.tf",
      "status": " M",
      "size": 9126,
      "sha256": "8ee9a4afc3f5c9330ce77283cb00a89e787ee1cab1c0f85d9a9536344d37a48f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/main.tf",
      "status": " M",
      "size": 8829,
      "sha256": "cfb8cfe8890dafc421d462731bce87405baa3b0ae1c847ab70380c99b5b6f4ea",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/network.tf",
      "status": " M",
      "size": 4837,
      "sha256": "4ef5f37229962dc3b90da425193a74491a7c23afef7c159f038e9ae075f6aa0f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/outputs.tf",
      "status": " M",
      "size": 3405,
      "sha256": "6dd533bde5befa1f9540f537fffcc5f4ec3ee4ce979fb365c9c8a681a91a42d8",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/tests/package_c.tftest.hcl",
      "status": "??",
      "size": 8979,
      "sha256": "571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/variables.tf",
      "status": " M",
      "size": 5754,
      "sha256": "8ab402c401f0d394e0ae715654477c4ef2d914cdcb8614a2af4cc24a6442012f",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/versions.tf",
      "status": " M",
      "size": 571,
      "sha256": "eb83c7bbbee497ea0f928408b58d12fe7ac2120d08d41f427c091988ed03a6cf",
      "readStatus": "readable"
    },
    {
      "path": "scripts/build_pilot_release_context.py",
      "status": "??",
      "size": 13259,
      "sha256": "7625442d2f4c4bf856c1daa5d91e948ba40b669e29a69c5f1e43f8dccb381b7d",
      "readStatus": "readable"
    },
    {
      "path": "scripts/generate_pilot_deploy_policy.py",
      "status": "??",
      "size": 7082,
      "sha256": "46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/decision.md",
      "status": "review_input",
      "size": 18482,
      "sha256": "9fcfe44934b68499c8be7cf6ac9a8ae68947fc23aac806a9bc092677f5319768",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/findings.json",
      "status": "review_input",
      "size": 15020,
      "sha256": "5f87531f4e8d7ddd28474175d48dfb6229d607e90ac96217ed2d991d08c217c5",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md",
      "status": "review_input",
      "size": 6004,
      "sha256": "be294c079ae5cdebfcc5afa59939c30a0ce8026c9a57da027718a5166643340e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md",
      "status": "review_input",
      "size": 4173,
      "sha256": "b88979d7bd77c7f14edb5fcb2aaa45569897ed3473b57d77e002dfe9f307bad6",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md",
      "status": "review_input",
      "size": 2190,
      "sha256": "2449afbc8b37cb0d4631db14b53bd6a0f7f07d6dac44c677adeae00ce86e7c6e",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md",
      "status": "review_input",
      "size": 1386,
      "sha256": "6cac47d08e19ce92461c10ca62e1406912d72971f0037d7a78f236446c57c83c",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md",
      "status": "review_input",
      "size": 7700,
      "sha256": "5530a6fc969d1133b7c638307ec43aa50861efb2bfd7d720dfd5d83ca0bae7c7",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md",
      "status": "review_input",
      "size": 3204,
      "sha256": "7686652eeab60357e05ed088b81565aa58e08b547ceba7a53ad2fc38989d73b0",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md",
      "status": "review_input",
      "size": 5755,
      "sha256": "d0b59236477d6e1cd30cba5ae54750b76226bebb5f97f29d4625e670ef40c4d1",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md",
      "status": "review_input",
      "size": 3803,
      "sha256": "43f945cba5a3ee21de96ea36100d3fae190c91ea4ed335e96da75a1a31deb7f2",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": " M"
    },
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "??"
    },
    {
      "path": ".ai/pilot-release-boundary-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-executor.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-ast-schema-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-bootstrap-reference-program-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-calibration-goldens.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-design-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-mapping.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-bootstrap-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-requirements-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-persistence.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-fixtures-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-goldens-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-interpreter.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-mutations-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-semantic-oracle-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-catalog.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-schema-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-source-validator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/acceptance-synthetic-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-architecture-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag-closure-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-dag.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-bootstrap.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-bootstrap-inputs.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-design-integration-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-kernel.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-5.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design-remediation-6.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-mapping-reconstruction.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-dag-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-local-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-platform-runtime-authority-rds-prerequisite.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/adversarial-resource-rebinding.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/architecture-oracle-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-dag-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/acceptance-persistence-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-history/decision-authority-map-v1/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/authority-versioning-remediation-4.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision-authority-map.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-integration-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/design-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/independent-acceptance-enumerator.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-cloud-partition-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/entry-fence.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-cases-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-oracle-results-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/predicate-registry-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_harness.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-kernel/semantic_kernel.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/local-semantic-predicate-oracle-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/normative-acceptance-matrix.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/oracle-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/orm-source-authority-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-canonicalization-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-acl-rollback-blocker.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/persistence-runtime-authority-reassessment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-0029-binary.tar.gz",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle-v2.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-local-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-oracle-plan.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v1.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile-v2.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-profile.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-execution-manifest.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-preflight.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-rds-prerequisite-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-oracle.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/platform-runtime-authority-relationship-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-results.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-v2.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting-vectors.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-accounting.schema.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-contract-builder.py",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/resource-reconstruction-provenance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/risk-adjusted-routing-audit.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/run-trusted-sentinel.sh",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/sql-topology-benchmark.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-harness.sql",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/trusted-sentinel-output.txt",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-design-inheritance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/package-b-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-B/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/adversarial-design.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/adversarial-implementation-package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-authority-architecture-amendment.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-a-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/package-b-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT/state.json",
      "status": "??"
    },
    {
      "path": "backend/.env.example",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
      "status": "??"
    },
    {
      "path": "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
      "status": "??"
    },
    {
      "path": "backend/app/main.py",
      "status": " M"
    },
    {
      "path": "backend/app/models/core.py",
      "status": " M"
    },
    {
      "path": "backend/app/schemas/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/scripts/revoke_auth_sessions.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/ad_v4_acceptance_persistence_contract.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/invitations.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/session_revocation.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": " M"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_ad_v4_model_source_authority_postgres.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_invite_tenant_boundary.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??"
    },
    {
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??"
    },
    {
      "path": "scripts/generate-ad-v4-acceptance-persistence.py",
      "status": "??"
    },
    {
      "path": "scripts/verify_pilot_release_boundary.py",
      "status": "??"
    }
  ],
  "outOfScopeReason": "Preserved T081, 0030, Package B, policy, and sibling review metadata are outside this Package C closure boundary; all relevant cross-run authority and closure inputs are hash-bound."
}
```

## Diff against base

```diff
diff --git a/backend/Dockerfile b/backend/Dockerfile
index 1411be0..009fa97 100644
--- a/backend/Dockerfile
+++ b/backend/Dockerfile
@@ -1,4 +1,5 @@
-FROM python:3.12-slim
+ARG PYTHON_BASE=python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
+FROM ${PYTHON_BASE}
 
 ENV PYTHONDONTWRITEBYTECODE=1
 ENV PYTHONUNBUFFERED=1
@@ -9,13 +10,18 @@ RUN apt-get update \
     && apt-get install --no-install-recommends --yes mdbtools poppler-utils \
     && rm -rf /var/lib/apt/lists/*
 
-RUN python -m pip install --upgrade pip
-
-COPY requirements.txt .
-RUN pip install --no-cache-dir -r requirements.txt
+COPY requirements.lock .
+RUN pip install --no-cache-dir --require-hashes -r requirements.lock
 
 COPY . .
 
+RUN addgroup --system --gid 10001 paprnav \
+    && adduser --system --uid 10001 --ingroup paprnav --home /nonexistent --no-create-home paprnav \
+    && chown -R 10001:10001 /app
+
 EXPOSE 8000
 
+USER 10001:10001
+HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
+  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]
 CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
diff --git a/frontend/paprnav-frontend/.env.example b/frontend/paprnav-frontend/.env.example
index 1147ada..24975bf 100644
--- a/frontend/paprnav-frontend/.env.example
+++ b/frontend/paprnav-frontend/.env.example
@@ -1,5 +1,7 @@
 PAPRNAV_BACKEND_URL=http://127.0.0.1:8000
 NEXT_PUBLIC_PAPRNAV_API_BASE_URL=/api/backend
+NEXT_PUBLIC_PAPRNAV_ENV=local
+PAPRNAV_ENV=local
 PAPRNAV_FRONTEND_URL=http://localhost:3000
 PAPRNAV_SMOKE_EMAIL=owner.demo@paprnav.local
 PAPRNAV_SMOKE_PASSWORD=demo-password
diff --git a/frontend/paprnav-frontend/next.config.ts b/frontend/paprnav-frontend/next.config.ts
index 66e1566..fdfc499 100644
--- a/frontend/paprnav-frontend/next.config.ts
+++ b/frontend/paprnav-frontend/next.config.ts
@@ -1,7 +1,7 @@
 import type { NextConfig } from "next";
 
 const nextConfig: NextConfig = {
-  /* config options here */
+  output: "standalone",
   reactCompiler: true,
 };
 
diff --git a/frontend/paprnav-frontend/package-lock.json b/frontend/paprnav-frontend/package-lock.json
index 680db11..7d28fc3 100644
--- a/frontend/paprnav-frontend/package-lock.json
+++ b/frontend/paprnav-frontend/package-lock.json
@@ -18,7 +18,7 @@
         "class-variance-authority": "^0.7.1",
         "clsx": "^2.1.1",
         "lucide-react": "^0.576.0",
-        "next": "16.1.6",
+        "next": "16.2.5",
         "next-themes": "^0.4.6",
         "react": "19.2.3",
         "react-dom": "19.2.3",
@@ -32,7 +32,7 @@
         "@types/react-dom": "^19",
         "babel-plugin-react-compiler": "1.0.0",
         "eslint": "^9",
-        "eslint-config-next": "16.1.6",
+        "eslint-config-next": "16.2.5",
         "tailwindcss": "^4",
         "typescript": "^5"
       }
@@ -1088,15 +1088,15 @@
       }
     },
     "node_modules/@next/env": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/env/-/env-16.1.6.tgz",
-      "integrity": "sha512-N1ySLuZjnAtN3kFnwhAwPvZah8RJxKasD7x1f8shFqhncnWZn4JMfg37diLNuoHsLAlrDfM3g4mawVdtAG8XLQ==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/env/-/env-16.2.5.tgz",
+      "integrity": "sha512-Lb9ElHD2klcyeVD25vW+siPFqz9QMzDUSgvFZNO+dZEKoMHex4viJhVuzBhrXKqb+UKnih7mVYbt50/7KLsSCA==",
       "license": "MIT"
     },
     "node_modules/@next/eslint-plugin-next": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/eslint-plugin-next/-/eslint-plugin-next-16.1.6.tgz",
-      "integrity": "sha512-/Qq3PTagA6+nYVfryAtQ7/9FEr/6YVyvOtl6rZnGsbReGLf0jZU6gkpr1FuChAQpvV46a78p4cmHOVP8mbfSMQ==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/eslint-plugin-next/-/eslint-plugin-next-16.2.5.tgz",
+      "integrity": "sha512-PyILm/cw2u5gEG5xOjqFbALUAl/erAqtM47iZtP9lXiSzin+eOIf3KRi+CBC/mFG9j7Iz3JDqCOY94nFLUCccg==",
       "dev": true,
       "license": "MIT",
       "dependencies": {
@@ -1104,9 +1104,9 @@
       }
     },
     "node_modules/@next/swc-darwin-arm64": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-darwin-arm64/-/swc-darwin-arm64-16.1.6.tgz",
-      "integrity": "sha512-wTzYulosJr/6nFnqGW7FrG3jfUUlEf8UjGA0/pyypJl42ExdVgC6xJgcXQ+V8QFn6niSG2Pb8+MIG1mZr2vczw==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-darwin-arm64/-/swc-darwin-arm64-16.2.5.tgz",
+      "integrity": "sha512-BW+8PGVmsruomXHsitD8JG6gny9lEdobctjBwvtPF8AKtxGDR7nR35FOl/oK9UAPXBOBm+vx0k8qtpeHOXQMGQ==",
       "cpu": [
         "arm64"
       ],
@@ -1120,9 +1120,9 @@
       }
     },
     "node_modules/@next/swc-darwin-x64": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-darwin-x64/-/swc-darwin-x64-16.1.6.tgz",
-      "integrity": "sha512-BLFPYPDO+MNJsiDWbeVzqvYd4NyuRrEYVB5k2N3JfWncuHAy2IVwMAOlVQDFjj+krkWzhY2apvmekMkfQR0CUQ==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-darwin-x64/-/swc-darwin-x64-16.2.5.tgz",
+      "integrity": "sha512-ZoCGnCl9LlQJWmqXrZAUlNxvuNmclvE+7zUif+nDydkkehl9FKxHJ+wxSQMj+C37BYFerKiEdX9s9o02ir975Q==",
       "cpu": [
         "x64"
       ],
@@ -1136,9 +1136,9 @@
       }
     },
     "node_modules/@next/swc-linux-arm64-gnu": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-linux-arm64-gnu/-/swc-linux-arm64-gnu-16.1.6.tgz",
-      "integrity": "sha512-OJYkCd5pj/QloBvoEcJ2XiMnlJkRv9idWA/j0ugSuA34gMT6f5b7vOiCQHVRpvStoZUknhl6/UxOXL4OwtdaBw==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-linux-arm64-gnu/-/swc-linux-arm64-gnu-16.2.5.tgz",
+      "integrity": "sha512-AwcZzMChaWkOTZt3vu+2ZMIj8g4dYQY+B8VUVhlFSQ2JtvyZpefyYHTe00D6b6L7BysYw7vl3zsvs9jix8tl5Q==",
       "cpu": [
         "arm64"
       ],
@@ -1152,9 +1152,9 @@
       }
     },
     "node_modules/@next/swc-linux-arm64-musl": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-linux-arm64-musl/-/swc-linux-arm64-musl-16.1.6.tgz",
-      "integrity": "sha512-S4J2v+8tT3NIO9u2q+S0G5KdvNDjXfAv06OhfOzNDaBn5rw84DGXWndOEB7d5/x852A20sW1M56vhC/tRVbccQ==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-linux-arm64-musl/-/swc-linux-arm64-musl-16.2.5.tgz",
+      "integrity": "sha512-QqMgqWbCBFsfiQ7BF3dUlW8HJy1LWhpcqbTpoHMWA9IV+TnWwDKozQJA5NdIAHjQ00yX2Q7AUkLr/XK4n77q8A==",
       "cpu": [
         "arm64"
       ],
@@ -1168,9 +1168,9 @@
       }
     },
     "node_modules/@next/swc-linux-x64-gnu": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-linux-x64-gnu/-/swc-linux-x64-gnu-16.1.6.tgz",
-      "integrity": "sha512-2eEBDkFlMMNQnkTyPBhQOAyn2qMxyG2eE7GPH2WIDGEpEILcBPI/jdSv4t6xupSP+ot/jkfrCShLAa7+ZUPcJQ==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-linux-x64-gnu/-/swc-linux-x64-gnu-16.2.5.tgz",
+      "integrity": "sha512-3hzeiFGZtyATVx9pCeuzTshXmh50vHZitqaeZiyJZaUmjQyrfjsVUgS8apOj1vEJCIpKJM/55F45yPAV2kpjsA==",
       "cpu": [
         "x64"
       ],
@@ -1184,9 +1184,9 @@
       }
     },
     "node_modules/@next/swc-linux-x64-musl": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-linux-x64-musl/-/swc-linux-x64-musl-16.1.6.tgz",
-      "integrity": "sha512-oicJwRlyOoZXVlxmIMaTq7f8pN9QNbdes0q2FXfRsPhfCi8n8JmOZJm5oo1pwDaFbnnD421rVU409M3evFbIqg==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-linux-x64-musl/-/swc-linux-x64-musl-16.2.5.tgz",
+      "integrity": "sha512-0mzZV/mAt7Qj2tYNdTB6AqrS8dwng/AQLSYC5Z1YLpZdi2wxqKDPK7RY2RvjB1fXyJfOfdA3l/yTF5yLi+WfuQ==",
       "cpu": [
         "x64"
       ],
@@ -1200,9 +1200,9 @@
       }
     },
     "node_modules/@next/swc-win32-arm64-msvc": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-win32-arm64-msvc/-/swc-win32-arm64-msvc-16.1.6.tgz",
-      "integrity": "sha512-gQmm8izDTPgs+DCWH22kcDmuUp7NyiJgEl18bcr8irXA5N2m2O+JQIr6f3ct42GOs9c0h8QF3L5SzIxcYAAXXw==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-win32-arm64-msvc/-/swc-win32-arm64-msvc-16.2.5.tgz",
+      "integrity": "sha512-f/H4nZ2zJBvA8/+HpsB9mNonF9zfQoAU6D0WxJrfzhJDvJLfngVN85oqxUyrDVK99DIFfFYhLpGa5K+c5uotSw==",
       "cpu": [
         "arm64"
       ],
@@ -1216,9 +1216,9 @@
       }
     },
     "node_modules/@next/swc-win32-x64-msvc": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/@next/swc-win32-x64-msvc/-/swc-win32-x64-msvc-16.1.6.tgz",
-      "integrity": "sha512-NRfO39AIrzBnixKbjuo2YiYhB6o9d8v/ymU9m/Xk8cyVk+k7XylniXkHwjs4s70wedVffc6bQNbufk5v0xEm0A==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/@next/swc-win32-x64-msvc/-/swc-win32-x64-msvc-16.2.5.tgz",
+      "integrity": "sha512-nuP7DHs4koAojsIxVPkihNgKiRUKtCU65j5X6DAbSy8VBrfT/o90bCLLHPf51JEdOZwZMFzM6e0NiGWfIWjVAg==",
       "cpu": [
         "x64"
       ],
@@ -2764,6 +2764,70 @@
         "node": ">=14.0.0"
       }
     },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/core": {
+      "version": "1.8.1",
+      "dev": true,
+      "inBundle": true,
+      "license": "MIT",
+      "optional": true,
+      "dependencies": {
+        "@emnapi/wasi-threads": "1.1.0",
+        "tslib": "^2.4.0"
+      }
+    },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/runtime": {
+      "version": "1.8.1",
+      "dev": true,
+      "inBundle": true,
+      "license": "MIT",
+      "optional": true,
+      "dependencies": {
+        "tslib": "^2.4.0"
+      }
+    },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@emnapi/wasi-threads": {
+      "version": "1.1.0",
+      "dev": true,
+      "inBundle": true,
+      "license": "MIT",
+      "optional": true,
+      "dependencies": {
+        "tslib": "^2.4.0"
+      }
+    },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@napi-rs/wasm-runtime": {
+      "version": "1.1.1",
+      "dev": true,
+      "inBundle": true,
+      "license": "MIT",
+      "optional": true,
+      "dependencies": {
+        "@emnapi/core": "^1.7.1",
+        "@emnapi/runtime": "^1.7.1",
+        "@tybys/wasm-util": "^0.10.1"
+      },
+      "funding": {
+        "type": "github",
+        "url": "https://github.com/sponsors/Brooooooklyn"
+      }
+    },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/@tybys/wasm-util": {
+      "version": "0.10.1",
+      "dev": true,
+      "inBundle": true,
+      "license": "MIT",
+      "optional": true,
+      "dependencies": {
+        "tslib": "^2.4.0"
+      }
+    },
+    "node_modules/@tailwindcss/oxide-wasm32-wasi/node_modules/tslib": {
+      "version": "2.8.1",
+      "dev": true,
+      "inBundle": true,
+      "license": "0BSD",
+      "optional": true
+    },
     "node_modules/@tailwindcss/oxide-win32-arm64-msvc": {
       "version": "4.2.1",
       "resolved": "https://registry.npmjs.org/@tailwindcss/oxide-win32-arm64-msvc/-/oxide-win32-arm64-msvc-4.2.1.tgz",
@@ -4465,13 +4529,13 @@
       }
     },
     "node_modules/eslint-config-next": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/eslint-config-next/-/eslint-config-next-16.1.6.tgz",
-      "integrity": "sha512-vKq40io2B0XtkkNDYyleATwblNt8xuh3FWp8SpSz3pt7P01OkBFlKsJZ2mWt5WsCySlDQLckb1zMY9yE9Qy0LA==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/eslint-config-next/-/eslint-config-next-16.2.5.tgz",
+      "integrity": "sha512-fXEkugikngux1FBJ/Vop+52SLAMFjXZFXjyl/+HjGHngnXf8iIfqe3qdjcwN+40RBpSsCVhI04j0/ngEWL5Qng==",
       "dev": true,
       "license": "MIT",
       "dependencies": {
-        "@next/eslint-plugin-next": "16.1.6",
+        "@next/eslint-plugin-next": "16.2.5",
         "eslint-import-resolver-node": "^0.3.6",
         "eslint-import-resolver-typescript": "^3.5.2",
         "eslint-plugin-import": "^2.32.0",
@@ -4595,7 +4659,6 @@
       "integrity": "sha512-whOE1HFo/qJDyX4SnXzP4N6zOWn79WhnCUY/iDR0mPfQZO8wcYE4JClzI2oZrhBnnMUCBCHZhO6VQyoBU95mZA==",
       "dev": true,
       "license": "MIT",
-      "peer": true,
       "dependencies": {
         "@rtsao/scc": "^1.1.0",
         "array-includes": "^3.1.9",
@@ -4887,9 +4950,9 @@
       "license": "MIT"
     },
     "node_modules/fastq": {
-      "version": "1.20.1",
-      "resolved": "https://registry.npmjs.org/fastq/-/fastq-1.20.1.tgz",
-      "integrity": "sha512-GGToxJ/w1x32s/D2EKND7kTil4n8OVk/9mycTc4VDza13lOvpUZTGX3mFSCtV9ksdGBVzvsyAVLM6mHFThxXxw==",
+      "version": "1.20.3",
+      "resolved": "https://registry.npmjs.org/fastq/-/fastq-1.20.3.tgz",
+      "integrity": "sha512-XKv5nnLs6nLF71NgiKJLIZFLkPyIEuOselLG7ujZnGrRfQK8HpvY+WqKhAJUAdLomwVHErVS4LfxFlPq0/FTAw==",
       "dev": true,
       "license": "ISC",
       "dependencies": {
@@ -6358,14 +6421,14 @@
       "license": "MIT"
     },
     "node_modules/next": {
-      "version": "16.1.6",
-      "resolved": "https://registry.npmjs.org/next/-/next-16.1.6.tgz",
-      "integrity": "sha512-hkyRkcu5x/41KoqnROkfTm2pZVbKxvbZRuNvKXLRXxs3VfyO0WhY50TQS40EuKO9SW3rBj/sF3WbVwDACeMZyw==",
+      "version": "16.2.5",
+      "resolved": "https://registry.npmjs.org/next/-/next-16.2.5.tgz",
+      "integrity": "sha512-TkVTm9F2WEulkgGljm4wPwNgvCCWCVw6StUHsZb8WZpHFRjepoUWg3d7L4IMg7IyjcJ4Co9eVhpro8e8O+KarQ==",
       "license": "MIT",
       "dependencies": {
-        "@next/env": "16.1.6",
+        "@next/env": "16.2.5",
         "@swc/helpers": "0.5.15",
-        "baseline-browser-mapping": "^2.8.3",
+        "baseline-browser-mapping": "^2.9.19",
         "caniuse-lite": "^1.0.30001579",
         "postcss": "8.4.31",
         "styled-jsx": "5.1.6"
@@ -6377,15 +6440,15 @@
         "node": ">=20.9.0"
       },
       "optionalDependencies": {
-        "@next/swc-darwin-arm64": "16.1.6",
-        "@next/swc-darwin-x64": "16.1.6",
-        "@next/swc-linux-arm64-gnu": "16.1.6",
-        "@next/swc-linux-arm64-musl": "16.1.6",
-        "@next/swc-linux-x64-gnu": "16.1.6",
-        "@next/swc-linux-x64-musl": "16.1.6",
-        "@next/swc-win32-arm64-msvc": "16.1.6",
-        "@next/swc-win32-x64-msvc": "16.1.6",
-        "sharp": "^0.34.4"
+        "@next/swc-darwin-arm64": "16.2.5",
+        "@next/swc-darwin-x64": "16.2.5",
+        "@next/swc-linux-arm64-gnu": "16.2.5",
+        "@next/swc-linux-arm64-musl": "16.2.5",
+        "@next/swc-linux-x64-gnu": "16.2.5",
+        "@next/swc-linux-x64-musl": "16.2.5",
+        "@next/swc-win32-arm64-msvc": "16.2.5",
+        "@next/swc-win32-x64-msvc": "16.2.5",
+        "sharp": "^0.34.5"
       },
       "peerDependencies": {
         "@opentelemetry/api": "^1.1.0",
@@ -6712,9 +6775,9 @@
       "license": "ISC"
     },
     "node_modules/picomatch": {
-      "version": "2.3.1",
-      "resolved": "https://registry.npmjs.org/picomatch/-/picomatch-2.3.1.tgz",
-      "integrity": "sha512-JU3teHTNjmE2VCGFzuY8EXzCDVwEqB2a8fsIvwaStHhAWJEeVd1o1QD80CU6+ZdEXXSLbSsuLwJjkCBWqRQUVA==",
+      "version": "2.3.2",
+      "resolved": "https://registry.npmjs.org/picomatch/-/picomatch-2.3.2.tgz",
+      "integrity": "sha512-V7+vQEJ06Z+c5tSye8S+nHUfI51xoXIXjHQ99cQtKUkQqqO1kO/KCJUfZXuB47h/YBlDhah2H3hdUGXn8ie0oA==",
       "dev": true,
       "license": "MIT",
       "engines": {
diff --git a/frontend/paprnav-frontend/package.json b/frontend/paprnav-frontend/package.json
index 4f45000..9a26993 100644
--- a/frontend/paprnav-frontend/package.json
+++ b/frontend/paprnav-frontend/package.json
@@ -7,7 +7,8 @@
     "build": "next build",
     "start": "next start",
     "lint": "eslint",
-    "smoke": "node scripts/smoke.mjs"
+    "smoke": "node scripts/smoke.mjs",
+    "test:pilot": "NEXT_PUBLIC_PAPRNAV_ENV=pilot node --test tests/pilot-observability.test.mjs"
   },
   "dependencies": {
     "@radix-ui/react-avatar": "^1.1.11",
@@ -20,7 +21,7 @@
     "class-variance-authority": "^0.7.1",
     "clsx": "^2.1.1",
     "lucide-react": "^0.576.0",
-    "next": "16.1.6",
+    "next": "16.2.5",
     "next-themes": "^0.4.6",
     "react": "19.2.3",
     "react-dom": "19.2.3",
@@ -34,7 +35,7 @@
     "@types/react-dom": "^19",
     "babel-plugin-react-compiler": "1.0.0",
     "eslint": "^9",
-    "eslint-config-next": "16.1.6",
+    "eslint-config-next": "16.2.5",
     "tailwindcss": "^4",
     "typescript": "^5"
   }
diff --git a/frontend/paprnav-frontend/src/app/(auth)/page.tsx b/frontend/paprnav-frontend/src/app/(auth)/page.tsx
index fb3ccfd..d3bccb7 100644
--- a/frontend/paprnav-frontend/src/app/(auth)/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(auth)/page.tsx
@@ -24,6 +24,7 @@ function LoginForm() {
   const [password, setPassword] = useState("demo-password");
   const [error, setError] = useState<string | null>(null);
   const [isSubmitting, setIsSubmitting] = useState(false);
+  const isPilot = process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot";
 
   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
     event.preventDefault();
@@ -126,16 +127,21 @@ function LoginForm() {
           </CardContent>
         </Card>
 
-        {/* Register link */}
-        <p className="text-center text-sm text-muted-foreground">
-          Don&apos;t have an account?{" "}
-          <Link
-            href="/register"
-            className="font-medium text-primary hover:text-primary/80"
-          >
-            Create one
-          </Link>
-        </p>
+        {isPilot ? (
+          <p className="text-center text-sm text-muted-foreground">
+            Have an invitation?{" "}
+            <Link href="/invite" className="font-medium text-primary hover:text-primary/80">
+              Accept it
+            </Link>
+          </p>
+        ) : (
+          <p className="text-center text-sm text-muted-foreground">
+            Don&apos;t have an account?{" "}
+            <Link href="/register" className="font-medium text-primary hover:text-primary/80">
+              Create one
+            </Link>
+          </p>
+        )}
       </div>
     </div>
   );
diff --git a/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx b/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
index 2f251f6..750d35c 100644
--- a/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
@@ -18,6 +18,24 @@ export default function RegisterPage() {
   const [error, setError] = useState<string | null>(null);
   const [isSubmitting, setIsSubmitting] = useState(false);
 
+  if (process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot") {
+    return (
+      <div className="min-h-screen flex items-center justify-center px-4">
+        <Card className="w-full max-w-md">
+          <CardHeader>
+            <CardTitle>Invitation required</CardTitle>
+            <CardDescription>The pilot is available only to invited users.</CardDescription>
+          </CardHeader>
+          <CardContent>
+            <Link href="/invite" className="font-medium text-primary hover:text-primary/80">
+              Accept an invitation
+            </Link>
+          </CardContent>
+        </Card>
+      </div>
+    );
+  }
+
   async function handleSubmit(event: FormEvent<HTMLFormElement>) {
     event.preventDefault();
     setError(null);
diff --git a/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx b/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
index 7c567a5..dc5c66b 100644
--- a/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
+++ b/frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
@@ -8,14 +8,17 @@ import { Input } from "@/components/ui/input";
 import { Label } from "@/components/ui/label";
 import { Textarea } from "@/components/ui/textarea";
 import { PageHeader } from "@/components/PageHeader";
+import { useAuth } from "@/components/AuthProvider";
 import {
   createFeedback,
-  listObservability,
+  listVisibleObservability,
   ObservabilityListResponse,
   updateFeedbackStatus,
 } from "@/lib/api";
 
 export default function ObservabilityPage() {
+  const { user } = useAuth();
+  const isPlatformAdmin = user?.memberships.some((membership) => membership.role === "platform_admin") ?? false;
   const [data, setData] = useState<ObservabilityListResponse>({ events: [], workflowEvents: [], feedback: [] });
   const [filters, setFilters] = useState({ aircraftId: "", eventType: "", subjectType: "", status: "" });
   const [feedbackMessage, setFeedbackMessage] = useState("");
@@ -26,13 +29,13 @@ export default function ObservabilityPage() {
   const loadData = useCallback(async () => {
     try {
       const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value.trim()));
-      const response = await listObservability(params);
+      const response = await listVisibleObservability(isPlatformAdmin, params);
       setData(response);
       setError(null);
     } catch (caught) {
       setError(caught instanceof Error ? caught.message : "Unable to load product observability.");
     }
-  }, [filters]);
+  }, [filters, isPlatformAdmin]);
 
   useEffect(() => {
     const timeoutId = window.setTimeout(() => {
@@ -151,10 +154,12 @@ export default function ObservabilityPage() {
                   <p>{item.message}</p>
                   <p className="text-muted-foreground">{item.subjectType} {item.subjectId ?? ""}</p>
                 </div>
-                <div className="flex gap-2">
-                  <Button type="button" size="sm" variant="outline" onClick={() => triageFeedback(item.id, "triaged")}>Triaged</Button>
-                  <Button type="button" size="sm" variant="ghost" onClick={() => triageFeedback(item.id, "closed")}>Closed</Button>
-                </div>
+                {isPlatformAdmin ? (
+                  <div className="flex gap-2">
+                    <Button type="button" size="sm" variant="outline" onClick={() => triageFeedback(item.id, "triaged")}>Triaged</Button>
+                    <Button type="button" size="sm" variant="ghost" onClick={() => triageFeedback(item.id, "closed")}>Closed</Button>
+                  </div>
+                ) : null}
               </div>
             </div>
           )) : <p className="text-sm text-muted-foreground">No feedback yet.</p>}
diff --git a/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts b/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
index d7301ba..1eafe0f 100644
--- a/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
+++ b/frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
@@ -16,6 +16,9 @@ type RouteContext = {
 };
 
 async function proxyRequest(request: NextRequest, context: RouteContext) {
+  if (process.env.PAPRNAV_ENV === "pilot") {
+    return NextResponse.json({ detail: "Not Found" }, { status: 404 });
+  }
   const { path } = await context.params;
   const backendPath = path.join("/");
   const upstreamUrl = new URL(`${BACKEND_URL.replace(/\/$/, "")}/${backendPath}`);
diff --git a/frontend/paprnav-frontend/src/lib/api.ts b/frontend/paprnav-frontend/src/lib/api.ts
index a87a5fe..32b07a1 100644
--- a/frontend/paprnav-frontend/src/lib/api.ts
+++ b/frontend/paprnav-frontend/src/lib/api.ts
@@ -1,4 +1,6 @@
-const API_BASE_URL = process.env.NEXT_PUBLIC_PAPRNAV_API_BASE_URL ?? "/api/backend";
+const API_BASE_URL = process.env.NEXT_PUBLIC_PAPRNAV_ENV === "pilot"
+  ? ""
+  : process.env.NEXT_PUBLIC_PAPRNAV_API_BASE_URL ?? "/api/backend";
 
 export interface Membership {
   organizationId: string;
@@ -17,6 +19,11 @@ export interface AuthResponse {
   user: CurrentUser;
 }
 
+export interface InvitationAcceptRequest {
+  invitationCode: string;
+  password: string;
+}
+
 export interface ProfileUpdateRequest {
   name: string;
 }
@@ -664,6 +671,13 @@ export function register(name: string, email: string, password: string) {
   });
 }
 
+export function acceptInvitation(payload: InvitationAcceptRequest) {
+  return apiFetch<AuthResponse>("/api/v1/auth/invitations/accept", {
+    method: "POST",
+    body: JSON.stringify(payload),
+  });
+}
+
 export function getCurrentUser() {
   return apiFetch<AuthResponse>("/api/v1/auth/me");
 }
@@ -859,6 +873,19 @@ export function listObservability(params: Record<string, string> = {}) {
   return apiFetch<ObservabilityListResponse>(`/api/v1/observability${suffix}`);
 }
 
+export function listAdminObservability(params: Record<string, string> = {}) {
+  const query = new URLSearchParams(params);
+  const suffix = query.toString() ? `?${query.toString()}` : "";
+  return apiFetch<ObservabilityListResponse>(`/api/v1/observability/admin${suffix}`);
+}
+
+export function listVisibleObservability(
+  isPlatformAdmin: boolean,
+  params: Record<string, string> = {},
+) {
+  return isPlatformAdmin ? listAdminObservability(params) : listObservability(params);
+}
+
 export function getADCostAdminSummary() {
   return apiFetch<ADCostAdminSummary>("/api/v1/admin/ad-costs");
 }
diff --git a/infra/terraform/database.tf b/infra/terraform/database.tf
index 4cc2d7a..f3741be 100644
--- a/infra/terraform/database.tf
+++ b/infra/terraform/database.tf
@@ -20,7 +20,7 @@ resource "aws_db_instance" "postgres" {
   storage_type          = "gp3"
 
   db_name                     = "paprnav"
-  username                    = "paprnav_app"
+  username                    = "paprnav_admin"
   manage_master_user_password = true
 
   db_subnet_group_name   = aws_db_subnet_group.main.name
@@ -50,7 +50,14 @@ resource "aws_secretsmanager_secret" "database_url" {
   description = "SQLAlchemy DATABASE_URL for the paprnav pilot API and worker. Populate after RDS creation."
 }
 
-resource "aws_secretsmanager_secret" "session_secret" {
-  name        = "/${var.project}/${var.environment}/session-secret"
-  description = "Application session secret for the paprnav pilot runtime. Populate before starting ECS tasks."
+resource "aws_secretsmanager_secret" "invitation_signing" {
+  name                    = "/${var.project}/${var.environment}/invitation-signing"
+  description             = "Dedicated pilot invitation HMAC secret. Populate only at the Package E gate."
+  recovery_window_in_days = 30
+}
+
+resource "aws_secretsmanager_secret" "first_admin_password" {
+  name                    = "/${var.project}/${var.environment}/first-admin-password"
+  description             = "One-use first administrator password. Populate only at the Package E gate."
+  recovery_window_in_days = 30
 }
diff --git a/infra/terraform/ecs_runtime.tf b/infra/terraform/ecs_runtime.tf
index 03a8b85..7dfc44f 100644
--- a/infra/terraform/ecs_runtime.tf
+++ b/infra/terraform/ecs_runtime.tf
@@ -1,7 +1,6 @@
 data "aws_iam_policy_document" "ecs_task_assume_role" {
   statement {
     actions = ["sts:AssumeRole"]
-
     principals {
       type        = "Service"
       identifiers = ["ecs-tasks.amazonaws.com"]
@@ -9,33 +8,81 @@ data "aws_iam_policy_document" "ecs_task_assume_role" {
   }
 }
 
+locals {
+  execution_role_names = toset(["api", "frontend", "worker", "bootstrap"])
+  app_environment_base = [
+    { name = "PAPRNAV_ENV", value = "pilot" },
+    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
+    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
+    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
+    { name = "PAPRNAV_CORS_ORIGINS", value = "https://${var.pilot_hostname}" },
+    { name = "PAPRNAV_SESSION_COOKIE_SECURE", value = "true" },
+    { name = "PAPRNAV_AD_V4_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_VALIDATOR2_WRITES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE3A_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE3B_ROUTES_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_READS_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED", value = "false" },
+    { name = "PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED", value = "false" },
+    { name = "AWS_REGION", value = var.aws_region },
+  ]
+  api_environment = concat(local.app_environment_base, [
+    { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
+  ])
+  worker_environment = concat(local.app_environment_base, [
+    { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
+  ])
+  api_secrets = [
+    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
+    { name = "PAPRNAV_INVITE_SIGNING_SECRET", valueFrom = aws_secretsmanager_secret.invitation_signing.arn },
+  ]
+  worker_secrets = [
+    { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::" },
+  ]
+  bootstrap_common_environment = [
+    { name = "PAPRNAV_ENV", value = "pilot" },
+    { name = "PAPRNAV_ADMIN_SECRET_ARN", value = aws_db_instance.postgres.master_user_secret[0].secret_arn },
+    { name = "PAPRNAV_DATABASE_NAME", value = aws_db_instance.postgres.db_name },
+    { name = "AWS_REGION", value = var.aws_region },
+  ]
+}
+
 resource "aws_iam_role" "ecs_execution" {
-  name               = "${local.name_prefix}-ecs-execution-role"
+  for_each           = local.execution_role_names
+  name               = "${local.name_prefix}-${each.key}-execution-role"
   assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
 }
 
 resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
-  role       = aws_iam_role.ecs_execution.name
+  for_each   = local.execution_role_names
+  role       = aws_iam_role.ecs_execution[each.key].name
   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
 }
 
-data "aws_iam_policy_document" "ecs_execution_secrets" {
+data "aws_iam_policy_document" "api_execution_secrets" {
   statement {
-    actions = [
-      "secretsmanager:GetSecretValue",
-    ]
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn, aws_secretsmanager_secret.invitation_signing.arn]
+  }
+}
 
-    resources = [
-      aws_secretsmanager_secret.database_url.arn,
-      aws_secretsmanager_secret.session_secret.arn,
-    ]
+resource "aws_iam_role_policy" "api_execution_secrets" {
+  name   = "${local.name_prefix}-api-execution-secrets"
+  role   = aws_iam_role.ecs_execution["api"].id
+  policy = data.aws_iam_policy_document.api_execution_secrets.json
+}
+
+data "aws_iam_policy_document" "worker_execution_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn]
   }
 }
 
-resource "aws_iam_role_policy" "ecs_execution_secrets" {
-  name   = "${local.name_prefix}-ecs-execution-secrets"
-  role   = aws_iam_role.ecs_execution.id
-  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
+resource "aws_iam_role_policy" "worker_execution_secrets" {
+  name   = "${local.name_prefix}-worker-execution-secrets"
+  role   = aws_iam_role.ecs_execution["worker"].id
+  policy = data.aws_iam_policy_document.worker_execution_secrets.json
 }
 
 resource "aws_iam_role" "api_task" {
@@ -53,29 +100,29 @@ resource "aws_iam_role" "worker_task" {
   assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
 }
 
+resource "aws_iam_role" "migration_reference_task" {
+  name               = "${local.name_prefix}-migration-reference-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
+resource "aws_iam_role" "runtime_role_task" {
+  name               = "${local.name_prefix}-runtime-role-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
+resource "aws_iam_role" "first_admin_task" {
+  name               = "${local.name_prefix}-first-admin-task-role"
+  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
+}
+
 data "aws_iam_policy_document" "api_task" {
   statement {
-    actions = [
-      "s3:GetObject",
-      "s3:PutObject",
-      "s3:DeleteObject",
-      "s3:GetObjectTagging",
-      "s3:PutObjectTagging",
-    ]
-
-    resources = [
-      "${aws_s3_bucket.app_artifacts.arn}/*",
-    ]
+    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
+    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
   }
-
   statement {
-    actions = [
-      "s3:ListBucket",
-    ]
-
-    resources = [
-      aws_s3_bucket.app_artifacts.arn,
-    ]
+    actions   = ["s3:ListBucket"]
+    resources = [aws_s3_bucket.app_artifacts.arn]
   }
 }
 
@@ -87,36 +134,15 @@ resource "aws_iam_role_policy" "api_task" {
 
 data "aws_iam_policy_document" "worker_task" {
   statement {
-    actions = [
-      "s3:GetObject",
-      "s3:PutObject",
-      "s3:DeleteObject",
-      "s3:GetObjectTagging",
-      "s3:PutObjectTagging",
-    ]
-
-    resources = [
-      "${aws_s3_bucket.app_artifacts.arn}/*",
-    ]
+    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:GetObjectTagging", "s3:PutObjectTagging"]
+    resources = ["${aws_s3_bucket.app_artifacts.arn}/*"]
   }
-
   statement {
-    actions = [
-      "s3:ListBucket",
-    ]
-
-    resources = [
-      aws_s3_bucket.app_artifacts.arn,
-    ]
+    actions   = ["s3:ListBucket"]
+    resources = [aws_s3_bucket.app_artifacts.arn]
   }
-
   statement {
-    actions = [
-      "textract:DetectDocumentText",
-      "textract:StartDocumentTextDetection",
-      "textract:GetDocumentTextDetection",
-    ]
-
+    actions   = ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"]
     resources = ["*"]
   }
 }
@@ -127,33 +153,50 @@ resource "aws_iam_role_policy" "worker_task" {
   policy = data.aws_iam_policy_document.worker_task.json
 }
 
-locals {
-  app_environment_base = [
-    { name = "PAPRNAV_ENV", value = var.environment },
-    { name = "PAPRNAV_STORAGE_BACKEND", value = "s3" },
-    { name = "PAPRNAV_S3_UPLOAD_BUCKET", value = aws_s3_bucket.app_artifacts.bucket },
-    { name = "PAPRNAV_S3_UPLOAD_PREFIX", value = "uploads" },
-    { name = "AWS_REGION", value = var.aws_region },
-  ]
+data "aws_iam_policy_document" "migration_reference_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
+  }
+}
 
-  api_environment = concat(
-    local.app_environment_base,
-    [
-      { name = "PAPRNAV_OCR_PROVIDER", value = "deterministic" },
-    ]
-  )
+resource "aws_iam_role_policy" "migration_reference_secrets" {
+  name   = "${local.name_prefix}-migration-reference-secrets"
+  role   = aws_iam_role.migration_reference_task.id
+  policy = data.aws_iam_policy_document.migration_reference_secrets.json
+}
+
+data "aws_iam_policy_document" "runtime_role_secrets" {
+  statement {
+    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_db_instance.postgres.master_user_secret[0].secret_arn]
+  }
+  statement {
+    actions   = ["secretsmanager:PutSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [aws_secretsmanager_secret.database_url.arn]
+  }
+}
+
+resource "aws_iam_role_policy" "runtime_role_secrets" {
+  name   = "${local.name_prefix}-runtime-role-secrets"
+  role   = aws_iam_role.runtime_role_task.id
+  policy = data.aws_iam_policy_document.runtime_role_secrets.json
+}
 
-  worker_environment = concat(
-    local.app_environment_base,
-    [
-      { name = "PAPRNAV_OCR_PROVIDER", value = "textract" },
+data "aws_iam_policy_document" "first_admin_secrets" {
+  statement {
+    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
+    resources = [
+      aws_db_instance.postgres.master_user_secret[0].secret_arn,
+      aws_secretsmanager_secret.first_admin_password.arn,
     ]
-  )
+  }
+}
 
-  api_secrets = [
-    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
-    { name = "PAPRNAV_SESSION_SECRET", valueFrom = aws_secretsmanager_secret.session_secret.arn },
-  ]
+resource "aws_iam_role_policy" "first_admin_secrets" {
+  name   = "${local.name_prefix}-first-admin-secrets"
+  role   = aws_iam_role.first_admin_task.id
+  policy = data.aws_iam_policy_document.first_admin_secrets.json
 }
 
 resource "aws_ecs_task_definition" "api" {
@@ -162,36 +205,23 @@ resource "aws_ecs_task_definition" "api" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["api"].arn
   task_role_arn            = aws_iam_role.api_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "api"
-      image     = "${aws_ecr_repository.api.repository_url}:latest"
-      essential = true
-
-      portMappings = [
-        {
-          containerPort = var.api_container_port
-          hostPort      = var.api_container_port
-          protocol      = "tcp"
-        }
-      ]
-
-      environment = local.api_environment
-      secrets     = local.api_secrets
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.api.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "api"
-        }
+  container_definitions = jsonencode([{
+    name         = "api"
+    image        = var.api_image
+    essential    = true
+    portMappings = [{ containerPort = var.api_container_port, hostPort = var.api_container_port, protocol = "tcp" }]
+    environment  = local.api_environment
+    secrets      = local.api_secrets
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.api.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "api"
       }
     }
-  ])
+  }])
 }
 
 resource "aws_ecs_task_definition" "frontend" {
@@ -200,38 +230,23 @@ resource "aws_ecs_task_definition" "frontend" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["frontend"].arn
   task_role_arn            = aws_iam_role.frontend_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "frontend"
-      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
-      essential = true
-
-      portMappings = [
-        {
-          containerPort = var.frontend_container_port
-          hostPort      = var.frontend_container_port
-          protocol      = "tcp"
-        }
-      ]
-
-      environment = [
-        { name = "PAPRNAV_ENV", value = var.environment },
-        { name = "PAPRNAV_BACKEND_URL", value = "http://${aws_lb.main.dns_name}" },
-      ]
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.frontend.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "frontend"
-        }
+  container_definitions = jsonencode([{
+    name         = "frontend"
+    image        = var.frontend_image
+    essential    = true
+    portMappings = [{ containerPort = var.frontend_container_port, hostPort = var.frontend_container_port, protocol = "tcp" }]
+    environment  = [{ name = "PAPRNAV_ENV", value = "pilot" }]
+    secrets      = []
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.frontend.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "frontend"
       }
     }
-  ])
+  }])
 }
 
 resource "aws_ecs_task_definition" "worker" {
@@ -240,79 +255,125 @@ resource "aws_ecs_task_definition" "worker" {
   network_mode             = "awsvpc"
   cpu                      = var.ecs_task_cpu
   memory                   = var.ecs_task_memory
-  execution_role_arn       = aws_iam_role.ecs_execution.arn
+  execution_role_arn       = aws_iam_role.ecs_execution["worker"].arn
   task_role_arn            = aws_iam_role.worker_task.arn
 
-  container_definitions = jsonencode([
-    {
-      name      = "worker"
-      image     = "${aws_ecr_repository.api.repository_url}:latest"
-      essential = true
-      command   = ["python", "-m", "app.workers.ocr"]
-
-      environment = local.worker_environment
-      secrets     = local.api_secrets
-
-      logConfiguration = {
-        logDriver = "awslogs"
-        options = {
-          awslogs-group         = aws_cloudwatch_log_group.worker.name
-          awslogs-region        = var.aws_region
-          awslogs-stream-prefix = "worker"
-        }
+  container_definitions = jsonencode([{
+    name        = "worker", image = var.api_image, essential = true, command = ["python", "-m", "app.workers.ocr"]
+    environment = local.worker_environment
+    secrets     = local.worker_secrets
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.worker.name, awslogs-region = var.aws_region, awslogs-stream-prefix = "worker"
       }
     }
-  ])
+  }])
+}
+
+locals {
+  bootstrap_tasks = {
+    migration = {
+      command     = ["migration"]
+      role        = aws_iam_role.migration_reference_task.arn
+      environment = local.bootstrap_common_environment
+    }
+    reference = {
+      command     = ["reference"]
+      role        = aws_iam_role.migration_reference_task.arn
+      environment = local.bootstrap_common_environment
+    }
+    runtime-role = {
+      command = ["runtime-role"]
+      role    = aws_iam_role.runtime_role_task.arn
+      environment = concat(local.bootstrap_common_environment, [
+        { name = "PAPRNAV_APP_DATABASE_SECRET_ARN", value = aws_secretsmanager_secret.database_url.arn },
+      ])
+    }
+    first-admin = {
+      command = ["first-admin"]
+      role    = aws_iam_role.first_admin_task.arn
+      environment = concat(local.bootstrap_common_environment, [
+        { name = "PAPRNAV_FIRST_ADMIN_SECRET_ARN", value = aws_secretsmanager_secret.first_admin_password.arn },
+        { name = "PAPRNAV_FIRST_ADMIN_EMAIL", value = var.first_admin_email },
+        { name = "PAPRNAV_FIRST_ADMIN_NAME", value = var.first_admin_name },
+        { name = "PAPRNAV_FIRST_ADMIN_ORGANIZATION", value = var.first_admin_organization },
+      ])
+    }
+  }
+}
+
+resource "aws_ecs_task_definition" "bootstrap" {
+  for_each                 = local.bootstrap_tasks
+  family                   = "${local.name_prefix}-bootstrap-${each.key}"
+  requires_compatibilities = ["FARGATE"]
+  network_mode             = "awsvpc"
+  cpu                      = var.ecs_task_cpu
+  memory                   = var.ecs_task_memory
+  execution_role_arn       = aws_iam_role.ecs_execution["bootstrap"].arn
+  task_role_arn            = each.value.role
+
+  container_definitions = jsonencode([{
+    name                   = "bootstrap"
+    image                  = var.bootstrap_image
+    essential              = true
+    command                = each.value.command
+    environment            = each.value.environment
+    secrets                = []
+    readonlyRootFilesystem = true
+    linuxParameters        = { initProcessEnabled = true }
+    logConfiguration = {
+      logDriver = "awslogs"
+      options = {
+        awslogs-group = aws_cloudwatch_log_group.bootstrap.name, awslogs-region = var.aws_region, awslogs-stream-prefix = each.key
+      }
+    }
+  }])
 }
 
 resource "aws_ecs_service" "api" {
   name            = "${local.name_prefix}-api"
   cluster         = aws_ecs_cluster.main.id
   task_definition = aws_ecs_task_definition.api.arn
-  desired_count   = var.api_desired_count
+  desired_count   = 0
   launch_type     = "FARGATE"
 
   network_configuration {
     subnets          = aws_subnet.public[*].id
-    security_groups  = [aws_security_group.ecs_tasks.id]
+    security_groups  = [aws_security_group.api.id]
     assign_public_ip = true
   }
-
   load_balancer {
     target_group_arn = aws_lb_target_group.api.arn
     container_name   = "api"
     container_port   = var.api_container_port
   }
-
-  depends_on = [aws_lb_listener.http]
+  depends_on = [aws_lb_listener.https]
 }
 
 resource "aws_ecs_service" "frontend" {
   name            = "${local.name_prefix}-frontend"
   cluster         = aws_ecs_cluster.main.id
   task_definition = aws_ecs_task_definition.frontend.arn
-  desired_count   = var.frontend_desired_count
+  desired_count   = 0
   launch_type     = "FARGATE"
 
   network_configuration {
     subnets          = aws_subnet.public[*].id
-    security_groups  = [aws_security_group.ecs_tasks.id]
+    security_groups  = [aws_security_group.frontend.id]
     assign_public_ip = true
   }
-
   load_balancer {
     target_group_arn = aws_lb_target_group.frontend.arn
     container_name   = "frontend"
     container_port   = var.frontend_container_port
   }
-
-  depends_on = [aws_lb_listener.http]
+  depends_on = [aws_lb_listener.https]
 }
 
 data "aws_iam_policy_document" "scheduler_assume_role" {
   statement {
     actions = ["sts:AssumeRole"]
-
     principals {
       type        = "Service"
       identifiers = ["scheduler.amazonaws.com"]
@@ -327,27 +388,17 @@ resource "aws_iam_role" "worker_scheduler" {
 
 data "aws_iam_policy_document" "worker_scheduler" {
   statement {
-    actions = ["ecs:RunTask"]
-
-    resources = [
-      aws_ecs_task_definition.worker.arn,
-    ]
-
+    actions   = ["ecs:RunTask"]
+    resources = [aws_ecs_task_definition.worker.arn]
     condition {
       test     = "ArnEquals"
       variable = "ecs:cluster"
       values   = [aws_ecs_cluster.main.arn]
     }
   }
-
   statement {
-    actions = ["iam:PassRole"]
-
-    resources = [
-      aws_iam_role.ecs_execution.arn,
-      aws_iam_role.worker_task.arn,
-    ]
-
+    actions   = ["iam:PassRole"]
+    resources = [aws_iam_role.ecs_execution["worker"].arn, aws_iam_role.worker_task.arn]
     condition {
       test     = "StringEquals"
       variable = "iam:PassedToService"
@@ -363,27 +414,21 @@ resource "aws_iam_role_policy" "worker_scheduler" {
 }
 
 resource "aws_scheduler_schedule" "worker" {
-  name       = "${local.name_prefix}-worker"
-  group_name = "default"
-  state      = var.worker_schedule_state
-
-  flexible_time_window {
-    mode = "OFF"
-  }
-
-  schedule_expression = var.worker_schedule_expression
+  name                = "${local.name_prefix}-worker"
+  group_name          = "default"
+  state               = "DISABLED"
+  schedule_expression = "rate(15 minutes)"
+  flexible_time_window { mode = "OFF" }
 
   target {
     arn      = aws_ecs_cluster.main.arn
     role_arn = aws_iam_role.worker_scheduler.arn
-
     ecs_parameters {
       launch_type         = "FARGATE"
       task_definition_arn = aws_ecs_task_definition.worker.arn
-
       network_configuration {
         subnets          = aws_subnet.public[*].id
-        security_groups  = [aws_security_group.ecs_tasks.id]
+        security_groups  = [aws_security_group.worker.id]
         assign_public_ip = true
       }
     }
diff --git a/infra/terraform/load_balancer.tf b/infra/terraform/load_balancer.tf
index 29baae0..6ccad49 100644
--- a/infra/terraform/load_balancer.tf
+++ b/infra/terraform/load_balancer.tf
@@ -4,9 +4,18 @@ resource "aws_lb" "main" {
   internal           = false
   security_groups    = [aws_security_group.alb.id]
   subnets            = aws_subnet.public[*].id
+  tags               = { Name = local.name_prefix }
+}
+
+resource "aws_route53_record" "pilot" {
+  zone_id = data.aws_route53_zone.pilot.zone_id
+  name    = var.pilot_hostname
+  type    = "A"
 
-  tags = {
-    Name = local.name_prefix
+  alias {
+    name                   = aws_lb.main.dns_name
+    zone_id                = aws_lb.main.zone_id
+    evaluate_target_health = true
   }
 }
 
@@ -27,10 +36,7 @@ resource "aws_lb_target_group" "frontend" {
     timeout             = 5
     unhealthy_threshold = 3
   }
-
-  tags = {
-    Name = "${local.name_prefix}-frontend"
-  }
+  tags = { Name = "${local.name_prefix}-frontend" }
 }
 
 resource "aws_lb_target_group" "api" {
@@ -50,10 +56,7 @@ resource "aws_lb_target_group" "api" {
     timeout             = 5
     unhealthy_threshold = 3
   }
-
-  tags = {
-    Name = "${local.name_prefix}-api"
-  }
+  tags = { Name = "${local.name_prefix}-api" }
 }
 
 resource "aws_lb_listener" "http" {
@@ -61,24 +64,284 @@ resource "aws_lb_listener" "http" {
   port              = 80
   protocol          = "HTTP"
 
+  default_action {
+    type = "redirect"
+    redirect {
+      port        = "443"
+      protocol    = "HTTPS"
+      status_code = "HTTP_301"
+    }
+  }
+}
+
+resource "aws_lb_listener" "https" {
+  load_balancer_arn = aws_lb.main.arn
+  port              = 443
+  protocol          = "HTTPS"
+  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
+  certificate_arn   = data.aws_acm_certificate.pilot.arn
+
   default_action {
     type             = "forward"
     target_group_arn = aws_lb_target_group.frontend.arn
   }
+
+  depends_on = [terraform_data.certificate_input_gate]
 }
 
 resource "aws_lb_listener_rule" "api" {
-  listener_arn = aws_lb_listener.http.arn
+  listener_arn = aws_lb_listener.https.arn
   priority     = 100
 
   action {
     type             = "forward"
     target_group_arn = aws_lb_target_group.api.arn
   }
-
   condition {
     path_pattern {
       values = ["/api/v1/*", "/health", "/version"]
     }
   }
 }
+
+resource "aws_wafv2_regex_pattern_set" "upload_path" {
+  name  = "${local.name_prefix}-upload-path"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/aircraft/[^/]+/uploads$"
+  }
+}
+
+resource "aws_wafv2_regex_pattern_set" "invitation_paths" {
+  name  = "${local.name_prefix}-invitation-paths"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/auth/invitations(?:/accept)?/?$"
+  }
+}
+
+resource "aws_wafv2_regex_pattern_set" "login_path" {
+  name  = "${local.name_prefix}-login-path"
+  scope = "REGIONAL"
+  regular_expression {
+    regex_string = "^/api/v1/auth/login/?$"
+  }
+}
+
+resource "aws_wafv2_web_acl" "pilot" {
+  name  = "${local.name_prefix}-web-acl"
+  scope = "REGIONAL"
+
+  default_action {
+    allow {}
+  }
+
+  rule {
+    name     = "aws-managed-common"
+    priority = 10
+    override_action {
+      none {}
+    }
+    statement {
+      managed_rule_group_statement {
+        name        = "AWSManagedRulesCommonRuleSet"
+        vendor_name = "AWS"
+        rule_action_override {
+          name = "SizeRestrictions_BODY"
+          action_to_use {
+            count {}
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-managed-common"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "block-oversize-body-except-reviewed-upload"
+    priority = 20
+    action {
+      block {}
+    }
+    statement {
+      and_statement {
+        statement {
+          size_constraint_statement {
+            comparison_operator = "GT"
+            size                = 8192
+            field_to_match {
+              body { oversize_handling = "MATCH" }
+            }
+            text_transformation {
+              priority = 0
+              type     = "NONE"
+            }
+          }
+        }
+        statement {
+          not_statement {
+            statement {
+              and_statement {
+                statement {
+                  byte_match_statement {
+                    positional_constraint = "EXACTLY"
+                    search_string         = "POST"
+                    field_to_match {
+                      method {}
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "NONE"
+                    }
+                  }
+                }
+                statement {
+                  regex_pattern_set_reference_statement {
+                    arn = aws_wafv2_regex_pattern_set.upload_path.arn
+                    field_to_match {
+                      uri_path {}
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "NONE"
+                    }
+                  }
+                }
+                statement {
+                  byte_match_statement {
+                    positional_constraint = "STARTS_WITH"
+                    search_string         = "multipart/form-data"
+                    field_to_match {
+                      single_header { name = "content-type" }
+                    }
+                    text_transformation {
+                      priority = 0
+                      type     = "LOWERCASE"
+                    }
+                  }
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-oversize-body"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "login-rate-limit"
+    priority = 30
+    action {
+      block {}
+    }
+    statement {
+      rate_based_statement {
+        aggregate_key_type = "IP"
+        limit              = var.login_rate_limit
+        scope_down_statement {
+          and_statement {
+            statement {
+              byte_match_statement {
+                positional_constraint = "EXACTLY"
+                search_string         = "POST"
+                field_to_match {
+                  method {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "NONE"
+                }
+              }
+            }
+            statement {
+              regex_pattern_set_reference_statement {
+                arn = aws_wafv2_regex_pattern_set.login_path.arn
+                field_to_match {
+                  uri_path {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "URL_DECODE"
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-login-rate"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  rule {
+    name     = "invitation-rate-limit"
+    priority = 40
+    action {
+      block {}
+    }
+    statement {
+      rate_based_statement {
+        aggregate_key_type = "IP"
+        limit              = var.invitation_rate_limit
+        scope_down_statement {
+          and_statement {
+            statement {
+              byte_match_statement {
+                positional_constraint = "EXACTLY"
+                search_string         = "POST"
+                field_to_match {
+                  method {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "NONE"
+                }
+              }
+            }
+            statement {
+              regex_pattern_set_reference_statement {
+                arn = aws_wafv2_regex_pattern_set.invitation_paths.arn
+                field_to_match {
+                  uri_path {}
+                }
+                text_transformation {
+                  priority = 0
+                  type     = "URL_DECODE"
+                }
+              }
+            }
+          }
+        }
+      }
+    }
+    visibility_config {
+      cloudwatch_metrics_enabled = true
+      metric_name                = "${local.name_prefix}-invitation-rate"
+      sampled_requests_enabled   = false
+    }
+  }
+
+  visibility_config {
+    cloudwatch_metrics_enabled = true
+    metric_name                = "${local.name_prefix}-waf"
+    sampled_requests_enabled   = false
+  }
+  tags = { Name = "${local.name_prefix}-web-acl" }
+}
+
+resource "aws_wafv2_web_acl_association" "pilot" {
+  resource_arn = aws_lb.main.arn
+  web_acl_arn  = aws_wafv2_web_acl.pilot.arn
+}
diff --git a/infra/terraform/main.tf b/infra/terraform/main.tf
index e2cec01..867307e 100644
--- a/infra/terraform/main.tf
+++ b/infra/terraform/main.tf
@@ -1,6 +1,10 @@
 locals {
   name_prefix = "${var.project}-${var.environment}"
 
+  expected_api_image_prefix       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-api@sha256:"
+  expected_frontend_image_prefix  = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-frontend@sha256:"
+  expected_bootstrap_image_prefix = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project}/${var.environment}-bootstrap@sha256:"
+
   common_tags = {
     Project     = var.project
     Environment = var.environment
@@ -12,6 +16,100 @@ locals {
   }
 }
 
+data "aws_route53_zone" "pilot" {
+  zone_id      = var.route53_zone_id
+  private_zone = false
+}
+
+data "aws_acm_certificate" "pilot" {
+  domain      = var.pilot_hostname
+  statuses    = ["ISSUED"]
+  types       = ["AMAZON_ISSUED"]
+  key_types   = ["RSA_2048"]
+  tags        = { Project = "paprnav" }
+  most_recent = false
+}
+
+resource "terraform_data" "certificate_input_gate" {
+  input = {
+    requested_arn = var.pilot_certificate_arn
+    resolved_arn  = data.aws_acm_certificate.pilot.arn
+    domain        = data.aws_acm_certificate.pilot.domain
+    status        = data.aws_acm_certificate.pilot.status
+    project_tag   = lookup(data.aws_acm_certificate.pilot.tags, "Project", "")
+  }
+
+  lifecycle {
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn
+      error_message = "The resolved ACM certificate ARN must equal pilot_certificate_arn."
+    }
+
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.domain == var.pilot_hostname
+      error_message = "The resolved ACM certificate primary domain must equal pilot_hostname."
+    }
+
+    precondition {
+      condition     = data.aws_acm_certificate.pilot.status == "ISSUED"
+      error_message = "The resolved ACM certificate must be ISSUED."
+    }
+
+    precondition {
+      condition     = lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
+      error_message = "The resolved ACM certificate must carry Project=paprnav."
+    }
+
+    precondition {
+      condition = startswith(
+        data.aws_acm_certificate.pilot.arn,
+        "arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"
+      )
+      error_message = "The resolved ACM certificate ARN must belong to the configured AWS account and region."
+    }
+  }
+}
+
+resource "terraform_data" "deployment_input_gate" {
+  input = {
+    hosted_zone_id   = data.aws_route53_zone.pilot.zone_id
+    hosted_zone_name = data.aws_route53_zone.pilot.name
+    pilot_hostname   = var.pilot_hostname
+  }
+
+  lifecycle {
+    precondition {
+      condition = (
+        startswith(var.api_image, local.expected_api_image_prefix) &&
+        startswith(var.frontend_image, local.expected_frontend_image_prefix) &&
+        startswith(var.bootstrap_image, local.expected_bootstrap_image_prefix)
+      )
+      error_message = "All image digests must reference the exact pilot ECR repository for their task family."
+    }
+
+    precondition {
+      condition = !var.external_mode || (
+        !endswith(var.pilot_hostname, ".invalid") &&
+        can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.budget_notification_email)) &&
+        !endswith(var.budget_notification_email, ".invalid") &&
+        can(regex("^arn:aws:iam::[0-9]{12}:(user|role)/.+$", var.policy_updater_principal_arn))
+      )
+      error_message = "External mode requires a real hostname, budget recipient, and explicit IAM policy-updater principal."
+    }
+
+    precondition {
+      condition = (
+        lower(trimsuffix(data.aws_route53_zone.pilot.name, ".")) == lower(trimsuffix(var.route53_zone_name, ".")) &&
+        (
+          var.pilot_hostname == lower(trimsuffix(data.aws_route53_zone.pilot.name, ".")) ||
+          endswith(var.pilot_hostname, ".${lower(trimsuffix(data.aws_route53_zone.pilot.name, "."))}")
+        )
+      )
+      error_message = "The actual Route53 hosted-zone identity must match route53_zone_name and contain pilot_hostname."
+    }
+  }
+}
+
 resource "aws_s3_bucket" "app_artifacts" {
   bucket        = "${local.name_prefix}-artifacts-${var.aws_account_id}"
   force_destroy = var.force_destroy_buckets
@@ -112,7 +210,7 @@ resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state"
 
 resource "aws_ecr_repository" "api" {
   name                 = "${var.project}/${var.environment}-api"
-  image_tag_mutability = "MUTABLE"
+  image_tag_mutability = "IMMUTABLE"
 
   image_scanning_configuration {
     scan_on_push = true
@@ -121,7 +219,16 @@ resource "aws_ecr_repository" "api" {
 
 resource "aws_ecr_repository" "frontend" {
   name                 = "${var.project}/${var.environment}-frontend"
-  image_tag_mutability = "MUTABLE"
+  image_tag_mutability = "IMMUTABLE"
+
+  image_scanning_configuration {
+    scan_on_push = true
+  }
+}
+
+resource "aws_ecr_repository" "bootstrap" {
+  name                 = "${var.project}/${var.environment}-bootstrap"
+  image_tag_mutability = "IMMUTABLE"
 
   image_scanning_configuration {
     scan_on_push = true
@@ -143,6 +250,11 @@ resource "aws_cloudwatch_log_group" "worker" {
   retention_in_days = var.log_retention_days
 }
 
+resource "aws_cloudwatch_log_group" "bootstrap" {
+  name              = "/paprnav/${var.environment}/bootstrap"
+  retention_in_days = var.log_retention_days
+}
+
 resource "aws_ecs_cluster" "main" {
   name = local.name_prefix
 
@@ -166,39 +278,27 @@ resource "aws_budgets_budget" "monthly_pilot" {
     ]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 50
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "ACTUAL"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 50
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "ACTUAL"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 80
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "ACTUAL"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 80
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "ACTUAL"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 
-  dynamic "notification" {
-    for_each = var.budget_notification_email == "" ? [] : [var.budget_notification_email]
-
-    content {
-      comparison_operator        = "GREATER_THAN"
-      threshold                  = 100
-      threshold_type             = "PERCENTAGE"
-      notification_type          = "FORECASTED"
-      subscriber_email_addresses = [notification.value]
-    }
+  notification {
+    comparison_operator        = "GREATER_THAN"
+    threshold                  = 100
+    threshold_type             = "PERCENTAGE"
+    notification_type          = "FORECASTED"
+    subscriber_email_addresses = [var.budget_notification_email]
   }
 }
diff --git a/infra/terraform/network.tf b/infra/terraform/network.tf
index 7ae4938..e4d8909 100644
--- a/infra/terraform/network.tf
+++ b/infra/terraform/network.tf
@@ -7,17 +7,12 @@ resource "aws_vpc" "main" {
   enable_dns_hostnames = true
   enable_dns_support   = true
 
-  tags = {
-    Name = local.name_prefix
-  }
+  tags = { Name = local.name_prefix }
 }
 
 resource "aws_internet_gateway" "main" {
   vpc_id = aws_vpc.main.id
-
-  tags = {
-    Name = "${local.name_prefix}-igw"
-  }
+  tags   = { Name = "${local.name_prefix}-igw" }
 }
 
 resource "aws_subnet" "public" {
@@ -27,7 +22,6 @@ resource "aws_subnet" "public" {
   cidr_block              = var.public_subnet_cidrs[count.index]
   availability_zone       = data.aws_availability_zones.available.names[count.index]
   map_public_ip_on_launch = true
-
   tags = {
     Name = "${local.name_prefix}-public-${count.index + 1}"
     Tier = "public"
@@ -40,7 +34,6 @@ resource "aws_subnet" "private" {
   vpc_id            = aws_vpc.main.id
   cidr_block        = var.private_subnet_cidrs[count.index]
   availability_zone = data.aws_availability_zones.available.names[count.index]
-
   tags = {
     Name = "${local.name_prefix}-private-${count.index + 1}"
     Tier = "private"
@@ -49,53 +42,73 @@ resource "aws_subnet" "private" {
 
 resource "aws_route_table" "public" {
   vpc_id = aws_vpc.main.id
-
   route {
     cidr_block = "0.0.0.0/0"
     gateway_id = aws_internet_gateway.main.id
   }
-
-  tags = {
-    Name = "${local.name_prefix}-public"
-  }
+  tags = { Name = "${local.name_prefix}-public" }
 }
 
 resource "aws_route_table_association" "public" {
-  count = length(aws_subnet.public)
-
+  count          = length(aws_subnet.public)
   subnet_id      = aws_subnet.public[count.index].id
   route_table_id = aws_route_table.public.id
 }
 
 resource "aws_security_group" "alb" {
   name        = "${local.name_prefix}-alb"
-  description = "Allow public HTTP access to the pilot ALB."
+  description = "Public HTTPS entry point; HTTP exists only for redirect."
   vpc_id      = aws_vpc.main.id
 
   ingress {
-    description = "HTTP from internet"
+    description = "HTTP redirect from internet"
     from_port   = 80
     to_port     = 80
     protocol    = "tcp"
     cidr_blocks = ["0.0.0.0/0"]
   }
-
+  ingress {
+    description = "HTTPS from internet"
+    from_port   = 443
+    to_port     = 443
+    protocol    = "tcp"
+    cidr_blocks = ["0.0.0.0/0"]
+  }
   egress {
-    description = "ALB to ECS targets"
+    description = "ALB to named API/frontend groups"
     from_port   = 0
     to_port     = 0
     protocol    = "-1"
     cidr_blocks = [var.vpc_cidr]
   }
+  tags = { Name = "${local.name_prefix}-alb" }
+}
 
-  tags = {
-    Name = "${local.name_prefix}-alb"
+resource "aws_security_group" "api" {
+  name        = "${local.name_prefix}-api"
+  description = "API ingress only from the ALB."
+  vpc_id      = aws_vpc.main.id
+
+  ingress {
+    description     = "API from ALB"
+    from_port       = var.api_container_port
+    to_port         = var.api_container_port
+    protocol        = "tcp"
+    security_groups = [aws_security_group.alb.id]
+  }
+  egress {
+    description = "Pilot public-task outbound compromise"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-api" }
 }
 
-resource "aws_security_group" "ecs_tasks" {
-  name        = "${local.name_prefix}-ecs-tasks"
-  description = "Allow ALB access to ECS tasks."
+resource "aws_security_group" "frontend" {
+  name        = "${local.name_prefix}-frontend"
+  description = "Frontend ingress only from the ALB; no database ingress grant."
   vpc_id      = aws_vpc.main.id
 
   ingress {
@@ -105,42 +118,61 @@ resource "aws_security_group" "ecs_tasks" {
     protocol        = "tcp"
     security_groups = [aws_security_group.alb.id]
   }
-
-  ingress {
-    description     = "API from ALB"
-    from_port       = var.api_container_port
-    to_port         = var.api_container_port
-    protocol        = "tcp"
-    security_groups = [aws_security_group.alb.id]
+  egress {
+    description = "Pilot public-task outbound compromise"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-frontend" }
+}
+
+resource "aws_security_group" "worker" {
+  name        = "${local.name_prefix}-worker"
+  description = "Non-listening worker tasks."
+  vpc_id      = aws_vpc.main.id
 
   egress {
-    description = "Outbound for AWS APIs and package/runtime access"
+    description = "Pilot public-task outbound compromise"
     from_port   = 0
     to_port     = 0
     protocol    = "-1"
     cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-worker" }
+}
 
-  tags = {
-    Name = "${local.name_prefix}-ecs-tasks"
+resource "aws_security_group" "bootstrap" {
+  name        = "${local.name_prefix}-bootstrap"
+  description = "Non-listening one-off migration/bootstrap tasks."
+  vpc_id      = aws_vpc.main.id
+
+  egress {
+    description = "Secrets Manager, ECR, logs, and RDS access"
+    from_port   = 0
+    to_port     = 0
+    protocol    = "-1"
+    cidr_blocks = ["0.0.0.0/0"]
   }
+  tags = { Name = "${local.name_prefix}-bootstrap" }
 }
 
 resource "aws_security_group" "rds" {
   name        = "${local.name_prefix}-rds"
-  description = "Allow PostgreSQL from ECS tasks."
+  description = "PostgreSQL from API, disabled worker, and one-off bootstrap tasks only."
   vpc_id      = aws_vpc.main.id
 
   ingress {
-    description     = "PostgreSQL from ECS tasks"
-    from_port       = 5432
-    to_port         = 5432
-    protocol        = "tcp"
-    security_groups = [aws_security_group.ecs_tasks.id]
-  }
-
-  tags = {
-    Name = "${local.name_prefix}-rds"
+    description = "PostgreSQL from API runtime"
+    from_port   = 5432
+    to_port     = 5432
+    protocol    = "tcp"
+    security_groups = [
+      aws_security_group.api.id,
+      aws_security_group.worker.id,
+      aws_security_group.bootstrap.id,
+    ]
   }
+  tags = { Name = "${local.name_prefix}-rds" }
 }
diff --git a/infra/terraform/outputs.tf b/infra/terraform/outputs.tf
index c81a15e..eeebcad 100644
--- a/infra/terraform/outputs.tf
+++ b/infra/terraform/outputs.tf
@@ -18,6 +18,11 @@ output "frontend_ecr_repository_url" {
   value       = aws_ecr_repository.frontend.repository_url
 }
 
+output "bootstrap_ecr_repository_url" {
+  description = "ECR repository URL for the sealed migration/bootstrap image."
+  value       = aws_ecr_repository.bootstrap.repository_url
+}
+
 output "ecs_cluster_name" {
   description = "ECS cluster name for paprnav pilot services."
   value       = aws_ecs_cluster.main.name
@@ -29,10 +34,20 @@ output "vpc_id" {
 }
 
 output "alb_dns_name" {
-  description = "Public ALB DNS name for the HTTP pilot runtime skeleton."
+  description = "Public ALB DNS name behind the canonical HTTPS pilot record."
   value       = aws_lb.main.dns_name
 }
 
+output "pilot_https_url" {
+  description = "Canonical HTTPS URL."
+  value       = "https://${var.pilot_hostname}"
+}
+
+output "pilot_certificate_arn" {
+  description = "Verified operator-provisioned ACM certificate attached to the HTTPS listener."
+  value       = data.aws_acm_certificate.pilot.arn
+}
+
 output "api_service_name" {
   description = "ECS API service name."
   value       = aws_ecs_service.api.name
@@ -73,12 +88,22 @@ output "database_url_secret_arn" {
   value       = aws_secretsmanager_secret.database_url.arn
 }
 
-output "session_secret_arn" {
-  description = "Secret ARN for the app session secret. Populate before starting ECS tasks."
-  value       = aws_secretsmanager_secret.session_secret.arn
+output "invitation_signing_secret_arn" {
+  description = "Secret ARN for the dedicated invitation-signing secret."
+  value       = aws_secretsmanager_secret.invitation_signing.arn
+}
+
+output "first_admin_password_secret_arn" {
+  description = "One-use first-administrator password secret ARN."
+  value       = aws_secretsmanager_secret.first_admin_password.arn
 }
 
 output "worker_schedule_name" {
   description = "EventBridge Scheduler schedule for the OCR worker task."
   value       = aws_scheduler_schedule.worker.name
 }
+
+output "bootstrap_task_definition_arns" {
+  description = "Fixed one-off task definitions; running them remains a Package E gate."
+  value       = { for phase, task in aws_ecs_task_definition.bootstrap : phase => task.arn }
+}
diff --git a/infra/terraform/variables.tf b/infra/terraform/variables.tf
index 707eb5f..93a89ca 100644
--- a/infra/terraform/variables.tf
+++ b/infra/terraform/variables.tf
@@ -17,138 +17,210 @@ variable "aws_profile" {
 }
 
 variable "project" {
-  description = "Project tag and resource prefix."
-  type        = string
-  default     = "paprnav"
+  type    = string
+  default = "paprnav"
 }
 
 variable "environment" {
-  description = "Deployment environment."
+  type    = string
+  default = "pilot"
+}
+
+variable "external_mode" {
+  description = "Enable execution-ready input checks. Package C fixture plans keep this false."
+  type        = bool
+  default     = false
+}
+
+variable "pilot_hostname" {
+  description = "Operator-owned canonical hostname; no default is permitted."
   type        = string
-  default     = "pilot"
+
+  validation {
+    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$", var.pilot_hostname))
+    error_message = "pilot_hostname must be one canonical lower-case DNS hostname."
+  }
 }
 
-variable "budget_limit_usd" {
-  description = "Monthly pilot budget limit in USD."
+variable "pilot_certificate_arn" {
+  description = "Exact ARN of the operator-provisioned, issued ACM certificate for pilot_hostname."
   type        = string
-  default     = "300"
+
+  validation {
+    condition     = can(regex("^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[0-9a-f-]+$", var.pilot_certificate_arn))
+    error_message = "pilot_certificate_arn must be one exact ACM certificate ARN."
+  }
+}
+
+variable "route53_zone_id" {
+  description = "Exact operator-supplied Route53 hosted-zone ID."
+  type        = string
+
+  validation {
+    condition     = can(regex("^Z[A-Z0-9]{8,32}$", var.route53_zone_id))
+    error_message = "route53_zone_id must be an explicit Route53 hosted-zone ID."
+  }
+}
+
+variable "route53_zone_name" {
+  description = "Expected canonical DNS name; Terraform verifies it against the hosted-zone ID returned by Route53."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+\\.?$", var.route53_zone_name))
+    error_message = "route53_zone_name must be one canonical lower-case DNS zone name."
+  }
 }
 
 variable "budget_notification_email" {
-  description = "Email address for AWS budget notifications. Empty disables budget notifications and should only be used for local planning."
+  description = "Real AWS Budget recipient in external mode; no repository default."
+  type        = string
+}
+
+variable "policy_updater_principal_arn" {
+  description = "Operator-admin principal authorized to version only paprnav-terraform-deploy."
+  type        = string
+}
+
+variable "api_image" {
+  description = "Immutable API image reference."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.api_image))
+    error_message = "api_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "frontend_image" {
+  description = "Immutable frontend image reference."
   type        = string
-  default     = ""
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.frontend_image))
+    error_message = "frontend_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "bootstrap_image" {
+  description = "Immutable dedicated migration/bootstrap image reference."
+  type        = string
+
+  validation {
+    condition     = can(regex("^[^:@[:space:]]+(?::[0-9]+)?/[^:@[:space:]]+@sha256:[0-9a-f]{64}$", var.bootstrap_image))
+    error_message = "bootstrap_image must be a repository@sha256:<64 lowercase hex> reference."
+  }
+}
+
+variable "first_admin_email" {
+  description = "First administrator identity; the password remains only in Secrets Manager."
+  type        = string
+}
+
+variable "first_admin_name" {
+  description = "First administrator display name."
+  type        = string
+}
+
+variable "first_admin_organization" {
+  description = "Permanent platform organization name created during first-admin bootstrap."
+  type        = string
+}
+
+variable "budget_limit_usd" {
+  type    = string
+  default = "300"
 }
 
 variable "log_retention_days" {
-  description = "CloudWatch log retention for pilot services."
-  type        = number
-  default     = 30
+  type    = number
+  default = 30
 }
 
 variable "force_destroy_buckets" {
-  description = "Allow Terraform to destroy non-empty pilot buckets. Keep false for volunteer data safety."
+  description = "Must remain false for volunteer-data safety."
   type        = bool
   default     = false
+
+  validation {
+    condition     = !var.force_destroy_buckets
+    error_message = "pilot buckets may not use force_destroy."
+  }
 }
 
 variable "vpc_cidr" {
-  description = "CIDR block for the paprnav pilot VPC."
-  type        = string
-  default     = "10.42.0.0/16"
+  type    = string
+  default = "10.42.0.0/16"
 }
 
 variable "public_subnet_cidrs" {
-  description = "CIDR blocks for public ALB/ECS subnets."
-  type        = list(string)
-  default     = ["10.42.0.0/24", "10.42.1.0/24"]
+  type    = list(string)
+  default = ["10.42.0.0/24", "10.42.1.0/24"]
 }
 
 variable "private_subnet_cidrs" {
-  description = "CIDR blocks for private database subnets."
-  type        = list(string)
-  default     = ["10.42.10.0/24", "10.42.11.0/24"]
+  type    = list(string)
+  default = ["10.42.10.0/24", "10.42.11.0/24"]
 }
 
 variable "api_container_port" {
-  description = "Container port for the FastAPI service."
-  type        = number
-  default     = 8000
+  type    = number
+  default = 8000
 }
 
 variable "frontend_container_port" {
-  description = "Container port for the Next.js frontend service."
-  type        = number
-  default     = 3000
-}
-
-variable "api_desired_count" {
-  description = "Desired ECS task count for the API service. Keep 0 until the API image is pushed."
-  type        = number
-  default     = 0
-}
-
-variable "frontend_desired_count" {
-  description = "Desired ECS task count for the frontend service. Keep 0 until the frontend image is pushed."
-  type        = number
-  default     = 0
+  type    = number
+  default = 3000
 }
 
 variable "ecs_task_cpu" {
-  description = "Default Fargate task CPU units for pilot API/frontend tasks."
-  type        = number
-  default     = 512
+  type    = number
+  default = 512
 }
 
 variable "ecs_task_memory" {
-  description = "Default Fargate task memory in MiB for pilot API/frontend tasks."
-  type        = number
-  default     = 1024
+  type    = number
+  default = 1024
 }
 
 variable "db_instance_class" {
-  description = "RDS PostgreSQL instance class for the pilot."
-  type        = string
-  default     = "db.t4g.micro"
+  type    = string
+  default = "db.t4g.micro"
 }
 
 variable "db_allocated_storage_gb" {
-  description = "Allocated RDS PostgreSQL storage in GiB."
-  type        = number
-  default     = 20
+  type    = number
+  default = 20
 }
 
 variable "db_engine_version" {
-  description = "RDS PostgreSQL engine version."
-  type        = string
-  default     = "16.3"
+  type    = string
+  default = "16.3"
 }
 
 variable "db_backup_retention_days" {
-  description = "RDS automated backup retention in days."
-  type        = number
-  default     = 7
+  type    = number
+  default = 7
 }
 
 variable "rds_deletion_protection" {
-  description = "Enable deletion protection for the pilot RDS instance."
-  type        = bool
-  default     = true
-}
+  type    = bool
+  default = true
 
-variable "worker_schedule_expression" {
-  description = "EventBridge Scheduler expression for the OCR worker task."
-  type        = string
-  default     = "rate(15 minutes)"
+  validation {
+    condition     = var.rds_deletion_protection
+    error_message = "pilot RDS deletion protection must remain enabled."
+  }
 }
 
-variable "worker_schedule_state" {
-  description = "EventBridge Scheduler state for the OCR worker task. Keep DISABLED until images and secrets are ready."
-  type        = string
-  default     = "DISABLED"
+variable "login_rate_limit" {
+  description = "Five-minute per-IP login request threshold."
+  type        = number
+  default     = 100
+}
 
-  validation {
-    condition     = contains(["ENABLED", "DISABLED"], var.worker_schedule_state)
-    error_message = "worker_schedule_state must be ENABLED or DISABLED."
-  }
+variable "invitation_rate_limit" {
+  description = "Five-minute per-IP invitation create/accept threshold."
+  type        = number
+  default     = 50
 }
diff --git a/infra/terraform/versions.tf b/infra/terraform/versions.tf
index 1b67d5d..c76bf06 100644
--- a/infra/terraform/versions.tf
+++ b/infra/terraform/versions.tf
@@ -13,7 +13,7 @@ terraform {
   required_providers {
     aws = {
       source  = "hashicorp/aws"
-      version = "~> 5.0"
+      version = "= 5.100.0"
     }
   }
 }

```

## Untracked text files

### `.ai/pilot-package-c-context-v1.json`

size=2637; sha256=b13c07ce5831eba17221363d07fa3db23ed4a1187b16b47b9e6fe9b020756e41; truncated=false

```text
{
  "version": "paprnav-pilot-package-c-context-v1",
  "expectedPlatforms": [
    "linux/amd64"
  ],
  "forbiddenPaths": [
    "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json",
    "backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql",
    "backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py",
    "backend/app/services/ad_v4_acceptance_persistence_contract.py",
    "backend/tests/test_ad_v4_acceptance_persistence.py",
    "backend/tests/test_ad_v4_acceptance_persistence_postgres.py",
    "backend/tests/test_ad_v4_model_source_authority.py",
    "backend/tests/test_ad_v4_model_source_authority_postgres.py",
    "scripts/generate-ad-v4-acceptance-persistence.py"
  ],
  "forbiddenPrefixes": [
    ".ai/review-runs/T081-V4-SCHEMA-SLICE-4B/"
  ],
  "contexts": {
    "api": {
      "sourcePrefix": "backend/",
      "excludePrefixes": [
        "backend/.data/",
        "backend/.pytest_cache/",
        "backend/.venv/",
        "backend/tests/"
      ],
      "excludeNames": [
        ".DS_Store",
        ".env"
      ],
      "requiredPaths": [
        "backend/Dockerfile",
        "backend/requirements.lock",
        "backend/main.py"
      ],
      "buildArgs": {
        "PYTHON_BASE": "python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7"
      }
    },
    "frontend": {
      "sourcePrefix": "frontend/paprnav-frontend/",
      "excludePrefixes": [
        "frontend/paprnav-frontend/.next/",
        "frontend/paprnav-frontend/node_modules/",
        "frontend/paprnav-frontend/tests/"
      ],
      "excludeNames": [
        ".DS_Store",
        ".env"
      ],
      "requiredPaths": [
        "frontend/paprnav-frontend/Dockerfile",
        "frontend/paprnav-frontend/package-lock.json",
        "frontend/paprnav-frontend/next.config.ts"
      ],
      "buildArgs": {
        "NODE_BASE": "node:24.13.0-alpine3.23@sha256:cd6fb7efa6490f039f3471a189214d5f548c11df1ff9e5b181aa49e22c14383e"
      }
    },
    "bootstrap": {
      "sourcePrefix": "infra/bootstrap/",
      "excludePrefixes": [],
      "excludeNames": [],
      "requiredPaths": [
        "infra/bootstrap/Dockerfile",
        "infra/bootstrap/bootstrap.py",
        "infra/bootstrap/grant-manifest.json",
        "infra/bootstrap/reference-data.json",
        "infra/bootstrap/requirements.lock"
      ],
      "buildArgs": {
        "PYTHON_BASE": "python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7"
      },
      "sealedMigrationContext": true
    }
  }
}


```
### `backend/requirements.lock`

size=64899; sha256=729a4a4316e863db493204ecc103c41943162cb7986af3fe5669a10e8d66462d; truncated=false

```text
# This file was autogenerated by uv via the following command:
#    uv pip compile backend/requirements.txt --generate-hashes --python-version 3.12 --python-platform x86_64-manylinux_2_28 -o backend/requirements.lock
alembic==1.20.0 \
    --hash=sha256:77eb101048d95f982c0353e9233404889dcd7a6fc244c107836c0e2fc9cf7d9d \
    --hash=sha256:db505480647bc60386c5369402f4a57a506b7539c9e9ef5e270d45cbbe4939bf
    # via -r backend/requirements.txt
annotated-doc==0.0.5 \
    --hash=sha256:117bac03a25ede5df5440e855b32d556049ca169ead221505badf432fed4b101 \
    --hash=sha256:c7e58ce09192557605d8bbd92836d7e1d520ac9580096042c0bfd197efacf1bb
    # via fastapi
annotated-types==0.8.0 \
    --hash=sha256:13b2beaad985e05e2d6407ee4c4f35590b11f8d693a258a561055cac8f64cab7 \
    --hash=sha256:f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0
    # via pydantic
anyio==4.15.1 \
    --hash=sha256:6152fdbbf9a77fdec97731721bebf7c4c44f7c29b424b0065826173efc7ed101 \
    --hash=sha256:9f28306018cbd6d329e64a36d58256edff76dd996fe423bc957326e578b82a94
    # via
    #   httpx
    #   starlette
boto3==1.43.98 \
    --hash=sha256:1ec732e023fb29c12dc8520f925b5bbbed29eeb36b5764b5a5c26052d7c721f7 \
    --hash=sha256:7454f666a9e852a56db0a7fa23be33a899f64e27828930eac43c3edba7b34e17
    # via -r backend/requirements.txt
botocore==1.43.98 \
    --hash=sha256:6135dd639ea6d1b3b49381bc253c8a139d61f7d44cb5f7dae8e7cd1791758572 \
    --hash=sha256:84b35b10402c2fc0c265f634fbf86336eecc6489ee23f55074b329924b2cfd6f
    # via
    #   boto3
    #   s3transfer
certifi==2026.7.22 \
    --hash=sha256:62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775 \
    --hash=sha256:741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55
    # via
    #   httpcore
    #   httpx
charset-normalizer==3.5.1 \
    --hash=sha256:00668ebb0609751758682eb0b5857e7c35b9f00e84dfdef062e103244ec94d45 \
    --hash=sha256:012a22b88a77ca2e59b98ac5889b0deb604147666032f45e6d6e217634d2550d \
    --hash=sha256:01e93745f7f219b703b60ba7afead36cfc4242782be5af484673fc500df12da5 \
    --hash=sha256:04368edf83514385ffc3e1cfd4546e595f4f1272dd23ba437a93a9cc3741d47b \
    --hash=sha256:0722590aabf9dc6a6c0343d523c05458fa2b5047dbe6302fd526bb570600753f \
    --hash=sha256:07ffd07412fc5d5e84cd8952acf9ff7e4ed7a708e69d1bada19d8ba91711353f \
    --hash=sha256:09a7bba9f739468c8e78c36a75c33768e53cb1959fc638f510454c14683f00d5 \
    --hash=sha256:0b2b1b3fa5670c127b246df1d0c059defd41f689a868a3b9d79df9b1cac42d22 \
    --hash=sha256:0c6dfb5ca6723eeed15aa8e564a014d69fcb8812f94eef11fe3631e0508199f5 \
    --hash=sha256:0d929fc574b4d6fd9e7c0f5c2ede8716a41911923aa7fa5fce38e0818aa4a1ac \
    --hash=sha256:13e3afe97712e8887cd516e960c63f0b93122971e5b5e4b2622fe7701771e838 \
    --hash=sha256:15f024313246a4ed976c60f440bb8d257815513a681d212ff74fd46f7d715a90 \
    --hash=sha256:195ce897c6153c0700078142cf8efe3e6454ca4cf4357499e4078dfd83396626 \
    --hash=sha256:19a3dd5aa73cef1c99687c4fc57db016a9c17104ae1185da88ba566a5d3bebe4 \
    --hash=sha256:1d1c7a53a6c2103925cdd6d7229f8c567379f211c869793df679f2e9f738c369 \
    --hash=sha256:1f5883d77fd409a261abb5dc8ccbe335720d798b1de4abb3b1d47ccbbc76b53b \
    --hash=sha256:21b82d8082f6f5e7f456ef0bd16323d08de1266efbfeb476e64b2a91d1471a4e \
    --hash=sha256:252d099029bcbea642f2a06c4ed5046bdf8b5a8150b64afa5e027e88b106e5ee \
    --hash=sha256:256dd4d85d9e4dc595e2bc983c980e73f62ddeb3165c58b4c3dfe78c5c8548c1 \
    --hash=sha256:26422d45fd13551cf564c58932f7d72b4f58b93b0fcf18c35ba6be12b46bb102 \
    --hash=sha256:2679de311c7946dde5d3b6f44941844133ff5c7cb86099c0061ab1e8901c20a8 \
    --hash=sha256:29880d17a8eb0b5cfdfd8944b468322928059aa35f1f5fa8ff22b149ec0b42f8 \
    --hash=sha256:2bced4061f000f7187254a02ad3433ae17eaf991747ceea2f478422590a5bba9 \
    --hash=sha256:2e9cf9253119d8e5d111f05d71626786fd3d6193817316eab1ca088cdb8593cf \
    --hash=sha256:2f06b7eae9dbe77fe1d644ca244dad508de8d302870a43f3c559b521270938a0 \
    --hash=sha256:2f293479cce755c75f1697e87c409b7ae4c555c7dfecb6e988ad13abba943031 \
    --hash=sha256:329fc3ccb63ad22d867d84c2adea759a64079a37ba4a343433b02c7a2816871e \
    --hash=sha256:343fb4f2821043bd87095f7b08a1a181febc8e36ac64212143bbfd0a0e1bc235 \
    --hash=sha256:3588e376b3ea2eea84976f67273d679f229e24c66dce7b82ae45aef04ff6e072 \
    --hash=sha256:35aea775dc2bd5f54cd84a1cd2696cc3207c479cb9cf0bd346f0d343e4300ddb \
    --hash=sha256:35fe081843b35aad20ffeccec3eeffbe637b15d14f3fb22cc1b59cd8ec17e93c \
    --hash=sha256:36047af20e17097c3bb9476c2b7655f2f7aa51322c0ba58c07695bedf755a950 \
    --hash=sha256:3617ac3cfd8b9888f145ad89dd6e692285834b0201c6074a5eeaad3fd4d668c2 \
    --hash=sha256:366ec70f5547c640d3ce1985722490f23faf4eb5216a7eeba78277490e78dacb \
    --hash=sha256:394fea06235c8543390050ed5f529187074b029fb027213f6c46ac11ab5d950e \
    --hash=sha256:3d27167433c0d5f18dc850f07d0b3816221984fecdc405d6c157a6f0b8f8e9e6 \
    --hash=sha256:3e5e1224c0a6a90e05843e07adfec669edebec17801c67072f51e59561d63c0b \
    --hash=sha256:41876ee62a3dddf48ff1121ad8f0798032aa03f2fd35f21f34a4cab14f18d8d2 \
    --hash=sha256:433c5a81eade63b47e522303bad236f59dba55ea6951746f5558355eeed8c75d \
    --hash=sha256:4582c27e8c889d64811987b5967fbd3ae0c823fe1fd933b543d55ac20bb475fa \
    --hash=sha256:485a0d363cafefcd2538a73c7c838daa2035f09b2c9f9b5e3133f80c6aeb84c2 \
    --hash=sha256:494b70049a4d69aec6e8137c13af4cf8db8c9f9820a1392ac293b0dd2987a818 \
    --hash=sha256:496846868fea80e479324862fa877f02411f2fd0f83b79ccee2607aa68b2a032 \
    --hash=sha256:4abdc5f9ad448c1ecbfae2974b820535d6bc6e7eef63babbab3d81cf46968c71 \
    --hash=sha256:4b599739b93b2cbeded49645ae3c8d1405c29ddfbceac1545c87a3f9580a9e96 \
    --hash=sha256:4bea7f8ebe90bbd7f0e4a2de42ca6924ba23e3e76418c408ff82f1d46fabd687 \
    --hash=sha256:4c4fb141a727957c93edfe5c32a26ceb6b5f6461d67146e2d39f51e16170bea8 \
    --hash=sha256:4c9548dc78002099910abaebc0a72ac58b7d30931869e0351c09b507dff4ece3 \
    --hash=sha256:4d26f14f041e83dd8edfd61f4cd4fa7285d31798b5bf1f28e70c367ba6c41d61 \
    --hash=sha256:4f298bdadb8f0b9e5672877f647d1be9373ef5320c9e2f049795e26cad28b6a9 \
    --hash=sha256:52ec005752a56ae79547a05c0139ca2501a0c866390b6115008456b9f0e7cde1 \
    --hash=sha256:55261ac0d2941c42f196dd576f543d87a8ee03cd6f5e30dfb4d807b2e3b9121a \
    --hash=sha256:56490c595a28b1bb27dfc583e816152a9767721ef58b2c03b13f954d2f707420 \
    --hash=sha256:58d3e12c88e0950bca850ae1f7c256055c097639c2edb9eb123af9807d8b15e4 \
    --hash=sha256:58d4aa13a59c969dbfdf9e6a9560e242cbfd9e8a8f50c2747714df1a423adf65 \
    --hash=sha256:59171c6e45bf07d0d5cab3b0bf81d945035530f6873398b3b531c31184d46663 \
    --hash=sha256:5b6d1386bf0096d26d3a863dc0a487a5b4eb9aa93cf5ba69683d29dde6b9d60f \
    --hash=sha256:5c0ea61a470e070686aa30892fed79e297d2c8d0ab46b8bcdf027d38c51da591 \
    --hash=sha256:5c84bec0ab5ae0c64bfe73a7d2adcb5ce73b467523fc27fd6a28ab2aa6cbe35a \
    --hash=sha256:5ca0555312ae2fe82715cada7fac375530c2f3349e1eaa1bcb33d0283ac79a18 \
    --hash=sha256:5d8531a6569d025f68e2321e7638fb7978f23db58e5f69f56913837aae03816e \
    --hash=sha256:5e2d0e146dcb57034f8b97dc58d2d512cb90aba253960ce449f695fec6a82c6f \
    --hash=sha256:5fc45d653ea8c9a20479167e11d4a0f8cb2fa3470737ab6f9c827532313187b7 \
    --hash=sha256:6117b84ea48435e5356dc737f5121485c30920ba43375fa7b434fd753df0eac3 \
    --hash=sha256:6199d5606e2bbf2b096cf64d03f8b6790c91081d5ac866b8e7bb6422738cc60c \
    --hash=sha256:62b55f6722735a6c472f88361cde6640608773d9443cebdbb51abf436a1fcdd3 \
    --hash=sha256:687c9ca3035544b113bea2055e180af96fb63c0c476e22a9180f51925186e7b7 \
    --hash=sha256:6b7430cf5728e68f6c462254009a6ef4086e1bea43cf2f57aa9c55fb4f50ff96 \
    --hash=sha256:6ba32c4d2abf1d2fe7cf27d280f4cca5664233b0f885549c7761719eb977f486 \
    --hash=sha256:6c9cdde8becb25a7fde49924511aa2644d6f8081cc8df8e9452724303348d8e3 \
    --hash=sha256:6df0ec430f9a831772c23ca5a224cba36517a58a84bb32c32bb59a9fa67c47f6 \
    --hash=sha256:6e2912d4babbc65196ac13c2f53468dc57fb8b9c25ef913e8c59ddf7c6dc0e1b \
    --hash=sha256:6e5e4d73d588ca5ed09df1b7dcd1b203d1df3c542e3f50d126c947d432b10731 \
    --hash=sha256:70055ff39b97c99e7ae40ea3e393fb62aa2e44dbd9b29f8d14f42fb0025c3959 \
    --hash=sha256:706bfd38730a5ac7a365793269a00f4e988178cec121391f4248d84ad8c972e9 \
    --hash=sha256:7235dc28fc6dd9d832ac7c7bce95367dedb85929f17368a0c2bee1e080b9acbf \
    --hash=sha256:774d157f112367ff4abd29019f38f023c24e00e56edc7829c20e358a5a913ad8 \
    --hash=sha256:77efcff2b23071c349402ac1066667a3d011f62398d81408c9b88ad991747c9e \
    --hash=sha256:789b8982559ae28dad2356519f841655756cdcd96616410590ae0b17454ee64f \
    --hash=sha256:7ac76cf9afd34929d76eb7fcb63be476a4853d8a96f0dcf2d0db68a0cbdf9885 \
    --hash=sha256:7c0c10730342b0c9b35dd1d619beb8214e520bd96a1f870f452680b238aab3e0 \
    --hash=sha256:823f82903d189af463d7df250ef1f7f696f3cee08cc8d91deb565e8d425f6506 \
    --hash=sha256:838648accb3a7fd9803fd45c87bce8509648eb0c11bc34e216141300977244f2 \
    --hash=sha256:854066be00447fa8de2ccbbe893e2ffc4b123ef16d897af794c1e18bd4a714b0 \
    --hash=sha256:85d5855daafc240cc045c026d7a15fd198a09b0fc8ff6f5ecbb5297b509cb11e \
    --hash=sha256:85de3134b5379856e323ba37c19c9256d39425f7b76a63af52b09fb4664c2e8f \
    --hash=sha256:87e4f41d375c0b9be2fb5251aee4b8a689169e134535aed81bf085c3b647451e \
    --hash=sha256:88ca277405c2d3b71c4e1c2ee0e7966e807bcba86a69d11e19ba199d18ae4491 \
    --hash=sha256:88e85ab89cb822c1e635f51d6d32e488f94e002e70e2f492bdb8b945543f345a \
    --hash=sha256:8ac8c94b6539074e0f40899301273ac8402b9b3e01c7b7ba269ff30340aaaf20 \
    --hash=sha256:8fe532b3c966d1fb794e0698e4589d0444017ae77fc0b31edea13c0e35bcc449 \
    --hash=sha256:9085f87b0e38a2b92b8923059b4e8789fe40d9279712d15dcc670048d77079af \
    --hash=sha256:90b7481fb62fbe172c558bc6fd1c4c98d82004a54a7551f20e11ac9bf0b8708c \
    --hash=sha256:92caef967d287a407085d61176fce4012b1dd62daed4eb6d5ceb26d3d2538712 \
    --hash=sha256:9362dd90aa7dab48c0054a21187791ccf05473f7dba5d92b8033ae62164675e7 \
    --hash=sha256:94d78ecec2605a8d0398b0f365d5f12a63248438516f5dac536a5eff7337df4a \
    --hash=sha256:94fbf1c0c6cc0d3d5e50f9a9313a8cdca90dd696d34b381cd1704f8c9e939f20 \
    --hash=sha256:950f23cb393f85543777b0433f082cddd25b51ab398eac7971146495679efe5f \
    --hash=sha256:96eefc178f8636b9c760c5829345307fd81cfae9ab1e80997dbddeb0f54ee9a3 \
    --hash=sha256:96fef3e886d6a9874b14f27fc193fbdc69d5d8035783d86aa4e1cea594e695f9 \
    --hash=sha256:977cdbd483a9cff38179bea4fd754289a6f2195c7abd414aba85410b3e66cc5e \
    --hash=sha256:978eab16f55b4ab2c2a745be9a0a840bf8f09a7f227d9c76eb30214d078865a5 \
    --hash=sha256:994e883d17c559cdfd38c84003c8b27d25424a1077272a17e7cd27bfe0bf57b2 \
    --hash=sha256:9ac4444d8d4fd4c4bd08bf451ed3167aa9e7ec6cdb41b648794f1d1103652e36 \
    --hash=sha256:9b5db6052055d34d41230fb78d7c439c23dc536a9896f6cb039e8dd92cfc1263 \
    --hash=sha256:9d9a0dc7cbe9bec24c3f767c9122c41fe5a1bc43f47cd099d00d393e09769de4 \
    --hash=sha256:9dbdd9205662134957cf0c324f639bdc5031c0ca056e2369e238db75187c0f11 \
    --hash=sha256:9eea3ab2597a5e65fe65296e2d6a84570845a6b55532d90333d740d48bbc850a \
    --hash=sha256:a2028475ba855475b8b4d3cfeb4994269c967aea8b9892dfba907f4263a863a3 \
    --hash=sha256:a3a370082ce34d0612f421e15fe011c53bb1feff21a26d06ad4fb244dab5a375 \
    --hash=sha256:a545775cfe815855ea32d7c27731d79da358ef2055b4a25830231b1622dd18aa \
    --hash=sha256:a5cbd90ecf0fc62e64726917ad083b73001f0563657a87ec3c0b504e277dc90d \
    --hash=sha256:a6d095662e73e74f0a49988e0593373e243e3a52e27bfeea0a859e88acf4a0f5 \
    --hash=sha256:a6dac12ff6b846103483683f60c5f8fee205121adc58ffd87e90a90a3af69e99 \
    --hash=sha256:a951ad59cad9145664a730d3036b40b844e74d2d3683da40111463cd3a83845d \
    --hash=sha256:aa1099b956fb795e686d073568f6dc002a0bb89765ea6d5b055dd7d9bf1b116c \
    --hash=sha256:aa2bb0b37202dca27175591f761108b5d34096ade1191ffe4808bdf6b1571488 \
    --hash=sha256:aae2ee51122d3ae968a3837d97dc24a0aeebb0dea23694422cd172bd30017cd6 \
    --hash=sha256:ab743e9bc90c1f73552ec33e10e3331315acd2c397b36065b591b0181de533cc \
    --hash=sha256:ac00177c4831ffa650f8609e4bdddd5fe09c03b1c0c47acece7e6ea20421598b \
    --hash=sha256:ac13b004224fb341e1e25a1ed5e19d32f57cdb2a403e01f003b46f051a550f6f \
    --hash=sha256:acaf604462bf330b0d07e7a07c1d6e4adac79e5fb13e9c5140590542cafacc00 \
    --hash=sha256:ae31a1a1db2ee6cc2942fccaf695c934bc7f3db9f2133a3fef1f367cf1a4ab10 \
    --hash=sha256:ae4a097991662cd4fff0ddc74e0fe7874f82e00042fa0ea00855645ed0c79598 \
    --hash=sha256:aea996a6aba25260827c9ea511d1addfde2da9eb686ac961838509086188b7e6 \
    --hash=sha256:b39b69b347e5e47a3b5b8cfc005c68c1ba347474e3960236c4944a8ecd174962 \
    --hash=sha256:b54e7e13267d49ffbfe68e25b3cbd774dab38fa37238f71265e91b36146eb21c \
    --hash=sha256:b9af956078716df40d985fb0dfeb2c2120c5ca92ba4ff4b388acfd01cdc14d08 \
    --hash=sha256:ba2f37ee79e6338845261a3c5b1784e5d1acdff2c0785b284f1b633033d136ab \
    --hash=sha256:ba501e667c17d8411f98e67a022d9604ef179aff0e459b7e292c796837c13573 \
    --hash=sha256:baf3775a2635e5a11fbd5e4e64ee69c7e86875d224a5c72aca4c141064589a90 \
    --hash=sha256:bb57753e36e4855b8ca375069482250a6246372331a3e4f3407eaebb007443f5 \
    --hash=sha256:bd6c173f04743d483881bffa1478d5a4624475b8cd1d2194956a75548e191c18 \
    --hash=sha256:be47f99644b208bff7766314013f9acf57b056b04191d570d68ad14022cf5b1d \
    --hash=sha256:c010f5581d9c612804cc59fcf7b524b707fbcb72828551237ab545bb5c7034af \
    --hash=sha256:c1dcc36dcb96abc02236e182d17e0f71430152a6c2c7447421da2d2dc144edea \
    --hash=sha256:c428c6c31eb5f4277d7f8eccaf767fbd548ddd5ce3c8b4f4cbbfab3d96b5904c \
    --hash=sha256:c658c50ac0c98cd755a2dd50b7977d3bca7df401dcc47fbdfa87db53ef7d4e8b \
    --hash=sha256:c71fb0d56c920c269cd3e2e3fe7c610e3f1fdb21a6ce60efa6430ff63676cea6 \
    --hash=sha256:c7b742bf31c88566b4bb6335a7f393bb322e580b6bb98df7bd0c25e6e3519ce8 \
    --hash=sha256:cc0329df4caaceb950d2f580b5ac716a377f7059624a0bafaeaf8a218c6ed774 \
    --hash=sha256:cc5d36d96478aa9c60654bd932525bf32964c62a7281eafdf16d85003a8d6004 \
    --hash=sha256:ce854f5f478050ade5a238731c4ca985a7d3b3cb53ff600a9b5c3b689b5f0a7a \
    --hash=sha256:ced3fdd71aaa83ce593746c2edb42b7a59cb4c19c8b5c407781c72e493aae55a \
    --hash=sha256:cee5dd7c6fb5dd52a0fe2a740f9bc6e3593f5f8b1788bde49de02086f30182b2 \
    --hash=sha256:cfa1c0cc3a8f9f53f1243a5a99ac36fd003880199383b37672e86ddda9cb07e2 \
    --hash=sha256:d1ee1e296209fdce05b81b663250eefa02213a2da7b41bf26f7829b8ba3545aa \
    --hash=sha256:d59b75732e9b6f27388e10c14b0259cc5f2e48c78627d185e6a177b58ad3cffe \
    --hash=sha256:d63600d620ad0064c3a748b950ac5ea38a80190e5498532efefa4b7b3f1da1f3 \
    --hash=sha256:dd732602a7009217f658d5863d12d79d373a4de0eebc111094bcdd3bb8e0a6cc \
    --hash=sha256:e06efa066f7dbadbc84ebc126a97c452a6451dfcf589d89d788484949e1cf795 \
    --hash=sha256:e199fb99720074809a7720f1c0b4d919eea8b87e88713e0f8f602f7bef543d9d \
    --hash=sha256:e4b018dc5a0eee4676e38fe84a47a427816c590b93b55d9025274ec4d6ffc2dc \
    --hash=sha256:e6621fb2a4988d6e53eedc455e5903e2679f3967b8acb3d639f1b63c14a2e893 \
    --hash=sha256:e71c909f353863b2b89c83de2ebed71ea6d0df8a6ef65a128193c5e650766bef \
    --hash=sha256:e90251c0c7bdd54a100a0dce3c07b7e637278c93af29dbf78ebb89a58c4bac7d \
    --hash=sha256:e9fbdce1e47394b09bc9f26ab117dfc8d6491977a11d86f592bb42c779db2fda \
    --hash=sha256:eb12fb2ba69ffa05f8695f61c69e591dc4b4a12ac3757ac8af8adb259bf56d17 \
    --hash=sha256:eda059b6bc8bc0812d626fd91a7ce01bf583df0a61296eff390fd94141a34e30 \
    --hash=sha256:f03ac127268b43ef4fe9e6ab6794a6794b49485a0cc0c1db79876d2f33f75bc7 \
    --hash=sha256:f298e218441525d3794428b4c8b8fb8662c6d3ea79925d4807ee6b9a96a3bca5 \
    --hash=sha256:f5542f9b941279d82d41eb0aa9f98eba36fe4df5c7086c651df7944935b37182 \
    --hash=sha256:f6f7deae3feb4edfa2efaf7c574fe88cbf055038a6abdb40188e4fff66d5699f \
    --hash=sha256:f9b1e28d0e8dbfa858abdba91d6b547beaf2df1a59bec6da6faae7b96a4991a9 \
    --hash=sha256:f9f8405c2c758532c74fed975dbee57be1f31a6e865c031870c79a6ed3212ada \
    --hash=sha256:fa48b1b63d639f9483e0633e092f5851e2348c352f1f9bb6c8182f87884ef876 \
    --hash=sha256:fb78f6e7fcd8ad785d28cd577168bc1aaee827b25bb8755638f694794ea98f0a \
    --hash=sha256:fbc597639158fd7c14d55e808718848319540f51b0e6746e3eefa59723a4a348 \
    --hash=sha256:fce8cbd4997efeb450bd298b54f755dcdff18d496f7a5ddbb4867c6d7c88fdc3 \
    --hash=sha256:fd0350afdc3aabd5576f60ea109228bd5538139713c7b094c5cd27c73a98bc6f \
    --hash=sha256:fd0a274c0e5f9a21565cd9d3dd749b61f96b7aa1e20a93aa1ba4029518f2e5c0 \
    --hash=sha256:fdb8a068947befafba9952162645dc2fecaeb400e64584829ed5e9b2fbe21a7f
    # via reportlab
click==8.5.0 \
    --hash=sha256:255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360 \
    --hash=sha256:ba0d2089de75ea0310e2dde03160e6ca10009947fb95a182f9b54021bb272e34
    # via uvicorn
fastapi==0.141.1 \
    --hash=sha256:bfb91aa2d334c61cb35ba9a116fc123b3d3df31640b801cf57a7a78ec3f603b3 \
    --hash=sha256:e8822fc40db1e1858054d7a949a888695bc9bdce70139178e33bd2871a453ca1
    # via -r backend/requirements.txt
greenlet==3.5.6 \
    --hash=sha256:0616b8f878098c5681fd8f0dc92d887551717402342a70f0abcbfea5f5ad8a44 \
    --hash=sha256:06c0e933290fba8ffe53ead4ae1b8044b0e9754b75cebf381aa2bc3e50d82fac \
    --hash=sha256:128813fc29f2336a21b4d06eedd5e16bcc7ea46f59e9ff1cb30ea70e48195d88 \
    --hash=sha256:188bf333769b7145e2b0b4a7f09615ec550ed44d3a2a8395fb7b36f0e9901e13 \
    --hash=sha256:1c20ea32a73d17b9b60e3371240e17b0068120c98a5ec01a224a7dd8c89733ba \
    --hash=sha256:2ab5f42ac6c238eb71770715e6e909ad9a1a92b6c681ccb64cd5a0f07edb953f \
    --hash=sha256:301102a49120b095e72a7838792b41233975fc1c155daec6d98f81c00c9280e0 \
    --hash=sha256:311018b46472fb26ee85870847fb89eb64cc8aaddb617400789d87076f7cfeec \
    --hash=sha256:3ac3494c381dab876cad7d0b22f3a722f3e0c8deb3a65b9e7f35ad7f58b8fcb3 \
    --hash=sha256:3c6dede9133e1da41d561bc3fb14e92b47e2ce39ae60edefaad145658ea7c5e2 \
    --hash=sha256:3dbb4596a6a4e5d47121a33ff20533a81e60f302d9e67b69909a8bc21a43f0a7 \
    --hash=sha256:3deccbb57a481e3a408fe61cdfd5c13e0678fc0a30fdd09597917ca87b4be877 \
    --hash=sha256:45663c01a4de48b9a64a2ee1509d92d1dfd3afb02b2ccfc9333029d11aef996a \
    --hash=sha256:45bfd2b51e38aaa5f9849f114d9c7c1d75f69187c849b3549cd64c465283abfa \
    --hash=sha256:460e70b033aba8ed47e2ac9b5d0d2157b05a34fbfa30a241400aef4118902cdc \
    --hash=sha256:4fb8e59f68845d56c23c031dcd79c329f345e4a9d2ffac91c3d1ab366bdc457b \
    --hash=sha256:520648db8fb92eef7b3e6013f5a6f901cdf0d6685f639c2f7a245879f865bef7 \
    --hash=sha256:5599b380c1f28efeb724e81569eac80cd92f99a85bd9775456caaf3225d40b11 \
    --hash=sha256:59deccd347735a7774223b05a93773fddbb298aba3cea21be4337fb4752dbe32 \
    --hash=sha256:5a0b2791239c99992a86c1b635b787fe2a877d9eaaa26f8891ce943832b585ae \
    --hash=sha256:5adcbbfe78bdc242c71740a02e0991cc1b2f34d33c8bb15ca45eee8fd1140942 \
    --hash=sha256:5b602b4201b965a8354d74e232364a66ff243dd142e350d035f46169bb36e13d \
    --hash=sha256:5bbda3c70dd35d60671bc33b01916802707a052130d9e50cdb871d34594d35cb \
    --hash=sha256:602024dae6d77e161f4b89491b62ca1d4f19949d79d47b2db057e476d21179d6 \
    --hash=sha256:61a61b4a95a4f97922c3a6f5606d3e360851584bd47e500a5161373c53810e3d \
    --hash=sha256:63aff70fe5aac59c72215f42ec39fcb59ff46774fa966e717f8ecb6ee2273577 \
    --hash=sha256:71890d5247020c25c21a6b65202782bfc281d4e6e244842419d30e3492bb6dcc \
    --hash=sha256:73a29b5ba642e35433166a03a3e02935e7238c4b3467fbd77523b99edea23e5b \
    --hash=sha256:7969bffa322c097bd46ae595ada6a931cefda613f18ba64587e9cff4cb320756 \
    --hash=sha256:7ac4abb3877c43af320392c664774eef6fa2cc063c79a55fc02d844a3cbe7395 \
    --hash=sha256:7f731ebac68ea06d628658295cb2d217b10186329fcf9a3b6a149045059bf92e \
    --hash=sha256:7f924a5a9d5890649566f2f6682e0d8ad8ca23028bacffbbac36dbd7fd680176 \
    --hash=sha256:874cea8bb1ec1ddccbacbd027856f6bf496f6bc18aba97a918c20e067edab236 \
    --hash=sha256:876077e7ebb8c84ed068e2b23d4c62ebb010d60df84b9591af1be2f39010ffb2 \
    --hash=sha256:886bcf1870af74c32bc310fd00a6b803445e17e51b7d5a107c7b35c0f362cc16 \
    --hash=sha256:8b27df301f56e3b3d2298095c8f7d6b68f2521f6b1693e901fa039bdbae34424 \
    --hash=sha256:8b7c73d1cef3d9ae963e9ff03f6222df43efbb9054ffd2f1969c935b7fc84c02 \
    --hash=sha256:8cda13494d86a4f12429641117cb6ac4bbbc9c30a33f711f7d3a2e5fbe4b0b7e \
    --hash=sha256:8cddea1b8339451c2fb3388e138347b6126744f33b611bdb55b7357361cfef46 \
    --hash=sha256:8dba0129b93e7091dfefaf4cf7000172741bff7f47bf6326fcf17f32fbb54d6b \
    --hash=sha256:8e67c43bdfc88d5fee6db0d3e40175b362fc95fb85f0412d233b9b203c53a575 \
    --hash=sha256:9133d68624b1f2e89ec2f554d56aea8a5b0d7168cd9320200ba58d4d794845a4 \
    --hash=sha256:916f92f2a8db10508f739d0b5e00b83defe5d1115a997c54532a6d7cf8c95404 \
    --hash=sha256:9297fb9c39b9a2c039dbcd306c410bd6906b95244dec3bba4318d36c718c164c \
    --hash=sha256:95e7c44d072db623a1aab04ce488cf9533294a77ed9d072cd503a3596f4106ac \
    --hash=sha256:975736b002ed080d124cf81a79cb7e05cb26d6b3f5c7a7b651c0fcce70353aa1 \
    --hash=sha256:97c5a53e8c1754df58e73f047a99e287d4da1bdfe64b0072fb25c87000897951 \
    --hash=sha256:9a09d59bef1db94f384b5bcc2d523694d338f3df6b757aeeaf7baca5d0c0be88 \
    --hash=sha256:a364c1ea75dc51b83a17f52fe0c79cf8bc4ddf740403bebd4581c7666eea017d \
    --hash=sha256:a3b4a01c6da07ef9f80d4fe8933b994bc99747bcea3eab0330a9c34d3c12655b \
    --hash=sha256:a5876d0a60355af98d535c47f6cd6eb0f8a432396dab26845d380b92f8412422 \
    --hash=sha256:a6a4b98a9132e0f45c9fc245a63894cfd8c45fb7a0d6bffc5eab3ec327cf7324 \
    --hash=sha256:a6b4ff33f7e011bbaa148238d131c4fd4f8afbab3c104ddfbdb2b12b74ff7016 \
    --hash=sha256:a93ee7c6e8fd0f8a83525a51bd777be57ee17787e91d805bd8d6faf9dcada18e \
    --hash=sha256:b374e79ffa7511afc11773aef40a4ccea6191fba1c856ea2f9c56738dca69d7a \
    --hash=sha256:b7d501d5eb5d4f67207df364752ad697465b834268744be7581c18d81d35d41d \
    --hash=sha256:c59acfa8eb73a1e0d484392dc002bdf001fd4ce73394e0132df3d1ab6093d7cb \
    --hash=sha256:c75116c9de79949de23006e2d9b35ee82874c594fcf5c0311b439acaa14b8441 \
    --hash=sha256:ca80a49b53ed1d22f7282da7255f7bb2fd1935fd0f623d8613fda38745f18961 \
    --hash=sha256:cad5782f93f7f738b62c6527b6f32a60694d924029f299a8b524758cfa53d815 \
    --hash=sha256:ccadce0130fd813ec86ebfe969a6c58b42acc1d0fe55a47525375b740e07b605 \
    --hash=sha256:d701eab36200c36224833d07dbdb709adb7fd4253429548ddb5e547b8ed40586 \
    --hash=sha256:dad3d233d441a022c1f7155f0fb9d5aff7b97c1ea8c7dfa02cce586b16ab2d0b \
    --hash=sha256:dd0b83bed3405b586a3133629f1d1a5bc7bfd64822a3b7ab342bdc68e6dbc61b \
    --hash=sha256:de3de000d459402cda015068fd135aa50c0bf6f2477a80d4da1e646f123b4e78 \
    --hash=sha256:de9923832f2d8c1a5ecd8d7260465a6ca5a86888a0d129e3bd5cf0406d2fc5bf \
    --hash=sha256:df19e2d0b1620039af5102563fbd96e8938c7f5c3f5828528d641d9fc585525e \
    --hash=sha256:e85880b538e59a59f55117b81f208a6660ad5ac328aad9305f812d9b8bc67a0f \
    --hash=sha256:ee7d9da3bf493909cf811a3f038840cb34fab5ae2956b8a263919f6e289ab188 \
    --hash=sha256:eed88b64a5e5da72d6a71cdc5aaeefaa5ced9b748f8d19f89800b339961dad39 \
    --hash=sha256:f0ba7c2a329d650628f4c8572fd1db29f0a59dd70a3e3e0710dcf18a35cce9d8 \
    --hash=sha256:f8e63209c3e1e828ee6a457529b4a6d8b05d050fe0ae03a7ae49e967c5d312e0 \
    --hash=sha256:f8f0bd690e1a41294ac87905e8121c81a3761ec2583c768f13467428606c8c7a \
    --hash=sha256:f96f0e30b5a95c7631b12bfe214cbc90ec8fe8cfa36920596c10514a65743519 \
    --hash=sha256:f98e8215e172f567ce80eeaed9107fb4d32b6c44f26983d9b8334658136a205a \
    --hash=sha256:f9fe868463ec7e1363733af77e38a5fda3e9b63940337048c945d69e0c80ff24 \
    --hash=sha256:fdacf26402389bdd89857ad3c045a26fe8f3314f9a8b28226f82f88463a65b77 \
    --hash=sha256:fe3170a69fe039b18ad18171e66faa9a75f6fe9d78f968fd9b54e09fbd714d81 \
    --hash=sha256:fea4427d1ffdb3b523d7daa6712038428a4c16c450b9777bdd1221cfee0eab49
    # via sqlalchemy
h11==0.16.0 \
    --hash=sha256:4e35b956cf45792e4caa5885e69fba00bdbc6ffafbfa020300e549b208ee5ff1 \
    --hash=sha256:63cf8bbe7522de3bf65932fda1d9c2772064ffb3dae62d55932da54b31cb6c86
    # via
    #   httpcore
    #   uvicorn
httpcore==1.0.9 \
    --hash=sha256:2d400746a40668fc9dec9810239072b40b4484b640a8c38fd654a024c7a1bf55 \
    --hash=sha256:6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8
    # via httpx
httpx==0.28.1 \
    --hash=sha256:75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc \
    --hash=sha256:d909fcccc110f8c7faf814ca82a9a4d816bc5a6dbfea25d6591d6985b8ba59ad
    # via -r backend/requirements.txt
idna==3.20 \
    --hash=sha256:a7db850025b95ded1eae8a46181a1a6c56c92c96f0e2b005d9ff8dc0210cab44 \
    --hash=sha256:ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c
    # via
    #   anyio
    #   httpx
iniconfig==2.3.0 \
    --hash=sha256:c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730 \
    --hash=sha256:f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
    # via pytest
jmespath==1.1.0 \
    --hash=sha256:472c87d80f36026ae83c6ddd0f1d05d4e510134ed462851fd5f754c8c3cbb88d \
    --hash=sha256:a5663118de4908c91729bea0acadca56526eb2698e83de10cd116ae0f4e97c64
    # via
    #   boto3
    #   botocore
mako==1.4.1 \
    --hash=sha256:a359d9a94a541213958742b2698d0a7757bb83551767bc468a74b9905aba9617 \
    --hash=sha256:d7904710b662996425a21627710c4777c45053146942cf8a7aebf757c92b8c27
    # via alembic
markupsafe==3.0.3 \
    --hash=sha256:0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f \
    --hash=sha256:068f375c472b3e7acbe2d5318dea141359e6900156b5b2ba06a30b169086b91a \
    --hash=sha256:0bf2a864d67e76e5c9a34dc26ec616a66b9888e25e7b9460e1c76d3293bd9dbf \
    --hash=sha256:0db14f5dafddbb6d9208827849fad01f1a2609380add406671a26386cdf15a19 \
    --hash=sha256:0eb9ff8191e8498cca014656ae6b8d61f39da5f95b488805da4bb029cccbfbaf \
    --hash=sha256:0f4b68347f8c5eab4a13419215bdfd7f8c9b19f2b25520968adfad23eb0ce60c \
    --hash=sha256:1085e7fbddd3be5f89cc898938f42c0b3c711fdcb37d75221de2666af647c175 \
    --hash=sha256:116bb52f642a37c115f517494ea5feb03889e04df47eeff5b130b1808ce7c219 \
    --hash=sha256:12c63dfb4a98206f045aa9563db46507995f7ef6d83b2f68eda65c307c6829eb \
    --hash=sha256:133a43e73a802c5562be9bbcd03d090aa5a1fe899db609c29e8c8d815c5f6de6 \
    --hash=sha256:1353ef0c1b138e1907ae78e2f6c63ff67501122006b0f9abad68fda5f4ffc6ab \
    --hash=sha256:15d939a21d546304880945ca1ecb8a039db6b4dc49b2c5a400387cdae6a62e26 \
    --hash=sha256:177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1 \
    --hash=sha256:1872df69a4de6aead3491198eaf13810b565bdbeec3ae2dc8780f14458ec73ce \
    --hash=sha256:1b4b79e8ebf6b55351f0d91fe80f893b4743f104bff22e90697db1590e47a218 \
    --hash=sha256:1b52b4fb9df4eb9ae465f8d0c228a00624de2334f216f178a995ccdcf82c4634 \
    --hash=sha256:1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695 \
    --hash=sha256:1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad \
    --hash=sha256:218551f6df4868a8d527e3062d0fb968682fe92054e89978594c28e642c43a73 \
    --hash=sha256:26a5784ded40c9e318cfc2bdb30fe164bdb8665ded9cd64d500a34fb42067b1c \
    --hash=sha256:2713baf880df847f2bece4230d4d094280f4e67b1e813eec43b4c0e144a34ffe \
    --hash=sha256:2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa \
    --hash=sha256:2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559 \
    --hash=sha256:32001d6a8fc98c8cb5c947787c5d08b0a50663d139f1305bac5885d98d9b40fa \
    --hash=sha256:3524b778fe5cfb3452a09d31e7b5adefeea8c5be1d43c4f810ba09f2ceb29d37 \
    --hash=sha256:3537e01efc9d4dccdf77221fb1cb3b8e1a38d5428920e0657ce299b20324d758 \
    --hash=sha256:35add3b638a5d900e807944a078b51922212fb3dedb01633a8defc4b01a3c85f \
    --hash=sha256:38664109c14ffc9e7437e86b4dceb442b0096dfe3541d7864d9cbe1da4cf36c8 \
    --hash=sha256:3a7e8ae81ae39e62a41ec302f972ba6ae23a5c5396c8e60113e9066ef893da0d \
    --hash=sha256:3b562dd9e9ea93f13d53989d23a7e775fdfd1066c33494ff43f5418bc8c58a5c \
    --hash=sha256:457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97 \
    --hash=sha256:4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a \
    --hash=sha256:4e885a3d1efa2eadc93c894a21770e4bc67899e3543680313b09f139e149ab19 \
    --hash=sha256:4faffd047e07c38848ce017e8725090413cd80cbc23d86e55c587bf979e579c9 \
    --hash=sha256:509fa21c6deb7a7a273d629cf5ec029bc209d1a51178615ddf718f5918992ab9 \
    --hash=sha256:5678211cb9333a6468fb8d8be0305520aa073f50d17f089b5b4b477ea6e67fdc \
    --hash=sha256:591ae9f2a647529ca990bc681daebdd52c8791ff06c2bfa05b65163e28102ef2 \
    --hash=sha256:5a7d5dc5140555cf21a6fefbdbf8723f06fcd2f63ef108f2854de715e4422cb4 \
    --hash=sha256:69c0b73548bc525c8cb9a251cddf1931d1db4d2258e9599c28c07ef3580ef354 \
    --hash=sha256:6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50 \
    --hash=sha256:722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698 \
    --hash=sha256:729586769a26dbceff69f7a7dbbf59ab6572b99d94576a5592625d5b411576b9 \
    --hash=sha256:77f0643abe7495da77fb436f50f8dab76dbc6e5fd25d39589a0f1fe6548bfa2b \
    --hash=sha256:795e7751525cae078558e679d646ae45574b47ed6e7771863fcc079a6171a0fc \
    --hash=sha256:7be7b61bb172e1ed687f1754f8e7484f1c8019780f6f6b0786e76bb01c2ae115 \
    --hash=sha256:7c3fb7d25180895632e5d3148dbdc29ea38ccb7fd210aa27acbd1201a1902c6e \
    --hash=sha256:7e68f88e5b8799aa49c85cd116c932a1ac15caaa3f5db09087854d218359e485 \
    --hash=sha256:83891d0e9fb81a825d9a6d61e3f07550ca70a076484292a70fde82c4b807286f \
    --hash=sha256:8485f406a96febb5140bfeca44a73e3ce5116b2501ac54fe953e488fb1d03b12 \
    --hash=sha256:8709b08f4a89aa7586de0aadc8da56180242ee0ada3999749b183aa23df95025 \
    --hash=sha256:8f71bc33915be5186016f675cd83a1e08523649b0e33efdb898db577ef5bb009 \
    --hash=sha256:915c04ba3851909ce68ccc2b8e2cd691618c4dc4c4232fb7982bca3f41fd8c3d \
    --hash=sha256:949b8d66bc381ee8b007cd945914c721d9aba8e27f71959d750a46f7c282b20b \
    --hash=sha256:94c6f0bb423f739146aec64595853541634bde58b2135f27f61c1ffd1cd4d16a \
    --hash=sha256:9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5 \
    --hash=sha256:9b79b7a16f7fedff2495d684f2b59b0457c3b493778c9eed31111be64d58279f \
    --hash=sha256:a320721ab5a1aba0a233739394eb907f8c8da5c98c9181d1161e77a0c8e36f2d \
    --hash=sha256:a4afe79fb3de0b7097d81da19090f4df4f8d3a2b3adaa8764138aac2e44f3af1 \
    --hash=sha256:ad2cf8aa28b8c020ab2fc8287b0f823d0a7d8630784c31e9ee5edea20f406287 \
    --hash=sha256:b8512a91625c9b3da6f127803b166b629725e68af71f8184ae7e7d54686a56d6 \
    --hash=sha256:bc51efed119bc9cfdf792cdeaa4d67e8f6fcccab66ed4bfdd6bde3e59bfcbb2f \
    --hash=sha256:bdc919ead48f234740ad807933cdf545180bfbe9342c2bb451556db2ed958581 \
    --hash=sha256:bdd37121970bfd8be76c5fb069c7751683bdf373db1ed6c010162b2a130248ed \
    --hash=sha256:be8813b57049a7dc738189df53d69395eba14fb99345e0a5994914a3864c8a4b \
    --hash=sha256:c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c \
    --hash=sha256:c47a551199eb8eb2121d4f0f15ae0f923d31350ab9280078d1e5f12b249e0026 \
    --hash=sha256:c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8 \
    --hash=sha256:ccfcd093f13f0f0b7fdd0f198b90053bf7b2f02a3927a30e63f3ccc9df56b676 \
    --hash=sha256:d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6 \
    --hash=sha256:d53197da72cc091b024dd97249dfc7794d6a56530370992a5e1a08983ad9230e \
    --hash=sha256:d6dd0be5b5b189d31db7cda48b91d7e0a9795f31430b7f271219ab30f1d3ac9d \
    --hash=sha256:d88b440e37a16e651bda4c7c2b930eb586fd15ca7406cb39e211fcff3bf3017d \
    --hash=sha256:de8a88e63464af587c950061a5e6a67d3632e36df62b986892331d4620a35c01 \
    --hash=sha256:df2449253ef108a379b8b5d6b43f4b1a8e81a061d6537becd5582fba5f9196d7 \
    --hash=sha256:e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419 \
    --hash=sha256:e1cf1972137e83c5d4c136c43ced9ac51d0e124706ee1c8aa8532c1287fa8795 \
    --hash=sha256:e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1 \
    --hash=sha256:e56b7d45a839a697b5eb268c82a71bd8c7f6c94d6fd50c3d577fa39a9f1409f5 \
    --hash=sha256:e8afc3f2ccfa24215f8cb28dcf43f0113ac3c37c2f0f0806d8c70e4228c5cf4d \
    --hash=sha256:e8fc20152abba6b83724d7ff268c249fa196d8259ff481f3b1476383f8f24e42 \
    --hash=sha256:eaa9599de571d72e2daf60164784109f19978b327a3910d3e9de8c97b5b70cfe \
    --hash=sha256:ec15a59cf5af7be74194f7ab02d0f59a62bdcf1a537677ce67a2537c9b87fcda \
    --hash=sha256:f190daf01f13c72eac4efd5c430a8de82489d9cff23c364c3ea822545032993e \
    --hash=sha256:f34c41761022dd093b4b6896d4810782ffbabe30f2d443ff5f083e0cbbb8c737 \
    --hash=sha256:f3e98bb3798ead92273dc0e5fd0f31ade220f59a266ffd8a4f6065e0a3ce0523 \
    --hash=sha256:f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591 \
    --hash=sha256:f71a396b3bf33ecaa1626c255855702aca4d3d9fea5e051b41ac59a9c1c41edc \
    --hash=sha256:f9e130248f4462aaa8e2552d547f36ddadbeaa573879158d721bbd33dfe4743a \
    --hash=sha256:fed51ac40f757d41b7c48425901843666a6677e3e8eb0abcff09e4ba6e664f50
    # via mako
packaging==26.3 \
    --hash=sha256:94edc256424af38762eb31306eed28beb9f0efc50a8837492c9d6fd6004aed79 \
    --hash=sha256:d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c
    # via pytest
pillow==12.3.0 \
    --hash=sha256:00808c5e14ef63ac5161091d242999076604ff74b883423a11e5d7bbb38bf756 \
    --hash=sha256:04f01d28a6aaff387bf842a13be313df23ba0597a44f1a976c9feb3c6ff4711a \
    --hash=sha256:06ff022112bc9cbf83b60f8e028d94ad87b60621706487e65f673de61610ab59 \
    --hash=sha256:0740a512dc522224c77d9aa5a8d70d8b7d73fb91f2c21125d8d025d3b8990e45 \
    --hash=sha256:0847a763afefb695bc912d7c131e7e0632d4edc1d8698f58ddabec8e46b8b6d3 \
    --hash=sha256:0dd2064cbc55aaec028ef5fbb60fa47bb6c3e7918e07ff17935284b227a9d2df \
    --hash=sha256:0feb2e9d6ad6c9e3c06effe9d00f3f1e618a6643273576b016f591e9315a7139 \
    --hash=sha256:10e41f0fbf1eec8cfd234b8fe17a4caac7c9d0db4c204d3c173a8f9f6ef3232b \
    --hash=sha256:1182d52bc2d5e5d7d0949503aa7e36d12f42205dc287e4883f407b1988820d39 \
    --hash=sha256:164b31cd1a0490ab6efae01aa5df49da7061be0af1b30e035b6e9a1bfe34ee6e \
    --hash=sha256:1657923d2d45afb66526e5b933e5b3052e6bdea196c90d3abb2424e18c77dae8 \
    --hash=sha256:186941b6aef820ad110fb01fb06eb925374dc3a21b17e37ec9a53b250c6fe2d1 \
    --hash=sha256:1cca606cd25738df4ed873d5ad46bbdb3d83b5cbca291f6b4ff13a4df6b0bbe8 \
    --hash=sha256:21900ce7ba264168cd50defae43cd75d25c833ad4ad6e73ffc5596d12e25ac89 \
    --hash=sha256:236ff70b9312fb68943c703aa842ca6a758abfa45ac187a5e7c1452e96ef72b5 \
    --hash=sha256:23aceaa007d6172b02c277f0cd359c79492bbb14f7072b4ede9fbcaf20648130 \
    --hash=sha256:23d27a3e0307ec2244cc51e7287b919aa68d097504ebe19df4e76a98a3eea5bd \
    --hash=sha256:24870b09b224f7ae3c39ed07d10e819d06f8720bc551847b1d623832b5b0e28d \
    --hash=sha256:251bf95b67017e27b13d82f5b326234ca62d70f9cf4c2b9032de2358a3b12c7b \
    --hash=sha256:25b9b82bb22e6e2b3cd07b39c68b7b862001226cb3dff7130d1cb914121b39ed \
    --hash=sha256:28ce87c5ab450a9dd970b52e5aca5fe63ed432d18a2eaddd1979a00a1ba24ace \
    --hash=sha256:300557495eb45ebb8aec96c2da9c4be642fbf7cd937278b4013ba894ea8eb0eb \
    --hash=sha256:30f2aa603c41533cc25c05acd0da21636e84a315768feb631c937177db558931 \
    --hash=sha256:331b624368d4f1d069149002f25f44bc61c8919ce8ddb3c45bdad8f6e2d89510 \
    --hash=sha256:37d6d0a00072fd2948eb22bce7e1475f34569d90c87c59f7a2ec59541b77f7a6 \
    --hash=sha256:37dc8f7bbb66efe481bb60defacef820c950c24713fb44962ed6aa2a50966de1 \
    --hash=sha256:3b8182a766685eaa002637e28b4ec8d6b18819a0c71f579bf0dbaa5830297cce \
    --hash=sha256:3edce1d53195db527e0191f84b71d02022de0540bf43a16ed734ed7537b07385 \
    --hash=sha256:446c34dcc4324b084a53b705127dc15717b22c5e140ae0a3c38349d4efec071e \
    --hash=sha256:4998562bf62a445225f22e07c896bb04b35b1b1f2eb6d760584c9c51d7a5f78c \
    --hash=sha256:4b0a7fe987b14c31ebda6083f74f22b561fd3739bc0ac51e019622e3d72668c7 \
    --hash=sha256:4e8c2a84d977f50b9daed6eeaf3baef67d00d5d74d932288f02cb94518ee3ace \
    --hash=sha256:4f883547d4b7f0495ebe7056b0cc2aea76094e7a4abc8e933540f3271df27d9c \
    --hash=sha256:514435a37670e3e5e08f3945b68718b6ed329bb84367777e16f9f4dfe1e61a0f \
    --hash=sha256:53aa02d20d10c3d814d536aa4e5ac9b84ca0ff5a88377963b085ad6822f93e64 \
    --hash=sha256:5594fc43d548a7ed94949d139aa1341b270f1863f11cfd37f5a6c8b778a6b67f \
    --hash=sha256:571b9fcb07b97ef3a492028fb3d2dc0993ca23a06138b0315286566d29ef718a \
    --hash=sha256:57b3d78c95ba9059768b10e28b813002261d3f3dfc55cc48b0c988f625175827 \
    --hash=sha256:5afb51d599ea772b8365ae807ae557f18bccfe46ab261fd1c2a9ed700fc6eb17 \
    --hash=sha256:6b02afb9b97f65fbca5f31db6a2a3ba21aa93030225f150fa3f249717e938fb4 \
    --hash=sha256:6c0016e7b354317c4e9e525b937ac8596c38d2d232b419529b9cd7a1cd46e39a \
    --hash=sha256:71d6097b330eea8fd15097780c8e89cb1a8ce7838669f48c5bacd6f663dd4701 \
    --hash=sha256:756c768d0c9c2955feb7a56c37ea24aea2e369f8d36a88da270b6a9f19e62b5e \
    --hash=sha256:78cb2c6865a35ab8ff8b75fd122f6033b92a62c82801110e48ddd6c936a45d91 \
    --hash=sha256:7a743ff716f746fc19a9557f60dab1600d4613255f8a7aeb3cdde4db7eb15a66 \
    --hash=sha256:85f998ea1848bc6757289e739cfbdda3a04adfd58b02fc018ce54d754a5ce468 \
    --hash=sha256:8728f216dcdb6e6d555cf971cb34076139ad74b31fc2c14da4fafc741c5f6217 \
    --hash=sha256:877c3f311ff35410f690861c4409e7ccbf0cd2f878e50628a28e5a0bb689e658 \
    --hash=sha256:8cd2f7bdda092d99c9fc2fb7391354f306d01443d22785d0cbfafa2e2c8bb418 \
    --hash=sha256:8e95e1385e4998ae9694eeaa4730ba5457ff61185b3a55e2e7bea0880aef452a \
    --hash=sha256:962864dc93511324d51ddbb5b9f8731bf71675b93ca612a07441896f4688fb8c \
    --hash=sha256:9cf95fe4d0f84c82d282745d9bb08ad9f926efa00be4697e767b814ce40d4330 \
    --hash=sha256:9e881fca225083806662a5c43d627d215f258ff43c890f831966c7d7ba9c7402 \
    --hash=sha256:a2b55dd6b2a4c4b7d87ffa56bdb33fdc5fdb9a462173861a7bc097f17d91cb09 \
    --hash=sha256:a45650e8ce7fafffd731db8550230db6b0d306d181a90b67d3e6bca2f1990930 \
    --hash=sha256:a876864214e136f0eb367788dbd7df045f4806801518e2cfe9e13229cfe06d8f \
    --hash=sha256:ae26d61dfa7a47befdc7572b521024e8745f3d809bd95ca9505a7bba9ef849ec \
    --hash=sha256:af8d94b0db561cf68b88a267c5c44b49e134f525d0dc2cb7ed413a66bc23559a \
    --hash=sha256:b343699e8308bdc51978310e1c959c584e7869cc8c40780058c87da7781a1e94 \
    --hash=sha256:b3c777e849237620b022f7f297dd67705f9f5cf1685f09f02e46f93e92725468 \
    --hash=sha256:b629de27fda84b42cde7edef0d85f13b958b47f6e9bbcbba9b673c562a89bd8b \
    --hash=sha256:ba09209fbe443b4acccebe845d8a138b89a8f4fbaeedd44953490b5315d5e965 \
    --hash=sha256:ba54cfebe86920a559a7c4d6b9050791c20513650a1952ebe3368c7dc70306f8 \
    --hash=sha256:bcb46e2f9feff8d06323983bd83ed00c201fdcab3d74973e7072a889b3979fcd \
    --hash=sha256:bcc33feacfaefce60c12fd500a277533bdc02b10a19f7f6d348763d8140bbba7 \
    --hash=sha256:bf16ba1b4d0b6b7c8e534936632270cf70eb00dbe09005bc345b2677b726855c \
    --hash=sha256:cf1845d02ad822a369a49f2bb9345b1614744267682e7a03527dc3bf6eea1777 \
    --hash=sha256:d69141514cc30b774ceea5e3ed3a6635c8d8a96edf664689b890f4089111fb35 \
    --hash=sha256:d9c7f76c0673154f044e9d78c8655fb4213f6ca31a836df48b40fe5d187717b9 \
    --hash=sha256:dbce0b29841537a2fa4a214c2bbf14de3587c9680caa9b4e217568472490b28f \
    --hash=sha256:dc624f6bc473dacdf7ef7eb8678d0d08edf15cd94fad6ae5c7d6cc67a4e4902f \
    --hash=sha256:e158cb00350dc278f3b91551101aa7d12415a66ebf2c91d8d5ac14e56ddd3ad0 \
    --hash=sha256:e491916b378fba47242221bb9ead245211b70d504f495d105d17b14a24b4907c \
    --hash=sha256:e795b7eb908249c4e43c7c99fac7c2c75dab0c43566e37db472a355f63693d71 \
    --hash=sha256:e7e480451b9fa137494bccd3a7d69adbe8ac65a87d97be61e11f1b1050a5bac3 \
    --hash=sha256:e91206ee562682b51b98ef4b26a6ef48fd84e15fd4c4bc5ec768eb641d206838 \
    --hash=sha256:e9871b1ffbfa9656b60aeee92ed5136a5742696006fa322b29ea3d8da0ecc9cf \
    --hash=sha256:e9aeb04d6aef139de265b29683e119b638208f88cf73cdd1658aa07221165321 \
    --hash=sha256:ebaea975e03d3141d9d3a507df75c9b3ec90fa9d2ffd07567b3a978d9d790b26 \
    --hash=sha256:f0606c8bf2cdefea14a43530f7657cbbb7ecf1c4222512492ef4a4434a9501ec \
    --hash=sha256:f13c32a3abd6079a66d9526e18dad9b6d280384d49d7c54040cd57b6424041d9 \
    --hash=sha256:f7401aebd7f581d7f83a439d87d474999317ee099218e5ad25d125290990ba65 \
    --hash=sha256:fa4ecea169a355be7a3ade2c783e2ed12f0e40d2c5621cda8b3297faf7fbb9f5 \
    --hash=sha256:fbd139c8447d25dd750ab79ee274cc5e1fe80fc56340ab10b18a195e1b6eca3e \
    --hash=sha256:fdafc9cce40277e0f7a0feabce0ee50dd2fa1800f3b38015e51296b5e814048d \
    --hash=sha256:fe3cca2e4e8a592be0f269a1ca4835c25199d9f3ce815c8491048f785b0a0198 \
    --hash=sha256:ffd0c5368496f41b0944be820fcb7a838aa6e623d250b01acf2643939c3f99d7
    # via
    #   -r backend/requirements.txt
    #   reportlab
pluggy==1.6.0 \
    --hash=sha256:7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3 \
    --hash=sha256:e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
    # via pytest
psycopg==3.3.6 \
    --hash=sha256:a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631 \
    --hash=sha256:c081f2250df751a943036e42db6df4571c66cd0aabe8291a7a506512b12007d2
    # via -r backend/requirements.txt
psycopg-binary==3.3.6 \
    --hash=sha256:05a83ac9fd52b9bca7cb5ab04b3691163170bd16f53defa27216ea3aa07ee781 \
    --hash=sha256:0a52991594ac4db888c7d39bccef331797e30cb31a95cae02cf2607f83a42dc2 \
    --hash=sha256:0bf08b749cc144f33b44a91b78e3f71c60eb07963746a0df5a100b36ce3d7475 \
    --hash=sha256:0ebfad5d131de9f892ae9e70cc7616207768b6714b66a52d4612b8ceaf78b372 \
    --hash=sha256:1679a1cb93fbe5a6d1fd58d82cbddcc6fcb8c61446ba7cae6eb2a7b19bc585de \
    --hash=sha256:198a48e68cc99ccac03ba95ac857e73aa66f3bf6be77019fafb0832a05f7ad03 \
    --hash=sha256:1fbd30e537dab22cafdf080608f10148fe2a5f3a61294ddb5113caac8a623840 \
    --hash=sha256:289aadd6a00e151203c081f708348ec89f1e483c9b510ef4ac3981f847f01f79 \
    --hash=sha256:2f122603f36050937982abf9668d8bc4769a79f7c93a65013b1c49f1cab7b56b \
    --hash=sha256:303732e798fe6729f8e12021b9c96107df8e95ecec4dd487c67b98ec2a59435e \
    --hash=sha256:31cd942c23f613276b81a6e6598cefa12960058b0f46e1e874b540c793f6aca5 \
    --hash=sha256:366db6e97e66b37211475f20c4c1324a2dc0dd825e46d4e87f9d599304d276f9 \
    --hash=sha256:373704aea331d3f3e3402c125a1543f5875e2986ebb54f97d1647942161f803f \
    --hash=sha256:37d40450659401600e6d043ff586c89a71a69f33cbb8bcdba6cdb2569beecdbe \
    --hash=sha256:37e517c146b185f9c0c6e8d0a0ebbdeeeb67896af28466e032bc810d0c7dc7a7 \
    --hash=sha256:3af90f92769d8cc10f94515ee7a0aef36ea85ca733a0ce22858f6e0953f41138 \
    --hash=sha256:3c9e663b2e800e3218994cf948c11bcc2844e6491b34aa80d089baf6531827bf \
    --hash=sha256:3f84dab25e0385692ee13274c68678377e0b1a70ab9d14e56264cbf61f60c62d \
    --hash=sha256:4690cf67738f0e0e49a32aeec99bf0e4595cc2b4f1af984a4345394b1dcff91a \
    --hash=sha256:566dd827f17728efdf7d88a5b066f815170f6fdad13967ae952842d90e6aaa9f \
    --hash=sha256:5927b7ba63153cd8e9862987290a2b783a5c590daf2a4ef981700cc3569166d4 \
    --hash=sha256:5ad8f35e67cc16d1fad1fa8c88972dc9b3a3141ea67897399904edab96a301b6 \
    --hash=sha256:5ea8beeb5541780b4b50b462eeacbc4f594ce3b911dc20c81c75f267876f71d2 \
    --hash=sha256:5f598f19fa9a91540b5cee17932ffd227b7b53a481605bcc4573c0eafa647300 \
    --hash=sha256:612382ac3ed13651c7fa44b5fee9fbf7baaa2ddbc6f500391672682c5f1df9e0 \
    --hash=sha256:6ff05561e4a067d35507dc5c90f1deb2ec1c9703ac5cccc1bc26e08a197f9c5a \
    --hash=sha256:7308c93cf0b19bbaf8e6ff0a6ad50d3c442385739245fe15a8d593bf841734a6 \
    --hash=sha256:79a2a1c3449f6c3409427078ed1cec10de79f3023cb5f2504f0597d350ad46c7 \
    --hash=sha256:7beb3e41c9a1e509f3ed85263386588cbe3e975aa67be21f79f44fd35ffaeefc \
    --hash=sha256:86147cb5d140341c3363fb5bacce31f8d5543902a46699d3c536b101bbceaf9e \
    --hash=sha256:889e42acec10450185e0cdfb396f375e2c1a8d7737c114830a7fde4654f59e30 \
    --hash=sha256:910ace140e3e7b7596898d083f37a8fe90c5c40684252ad4e682364b2cd3deba \
    --hash=sha256:955e3dd94da361e052d2e49acf591017158dc8f8ed2c8a42c2e3943403c39dc2 \
    --hash=sha256:9892188bb15e5803beb51afe8a25add6b56be391a53058e8bca03b74e1e6bf22 \
    --hash=sha256:98c02090d88f2ebc0ec1e8da538f77d225ce0fffecf372aa39262e62a1b054ef \
    --hash=sha256:9b2f11794e017ce340934e35de46181c46ef71ec75ea3d85dd75cd836761c01e \
    --hash=sha256:a2e44a342d2aee40508e28a563d8961c39d9bbd8cae36d8578f0a3c6658aab0f \
    --hash=sha256:a4ee3bdd5468a725f2a4d9aab8a74b6d0279f768c8b5d3aeb102c5307ff3d59c \
    --hash=sha256:a5165300324efd5a772c48a88ab3a928513ab3979fca76553e62ee815f7b2b9c \
    --hash=sha256:a9348c5b43a3bb5ef8c2e89d5237c9c87eeafb01d338c84a7aebbc5cd0313299 \
    --hash=sha256:aa73160077345ec21b3f51e8e24b3de2e99586217e497629326eb9b2ea88c52e \
    --hash=sha256:ad1c785e784cfd87e8436c6b7702f2d321fc39601bbaf29bc63a41a867091638 \
    --hash=sha256:b3f75dee0f9afafabe4edc52c4842f1e1878ed2069bd05b22d6fe961e97e4dba \
    --hash=sha256:b599defe9190b17e9907c8b4d114c181e702c87efcd1b8a0ad40971cdcc4634a \
    --hash=sha256:b82491019b884d62318b5f30706c3d7e6d4e5a6cb7eabcb3edc0c1b0fdaceae9 \
    --hash=sha256:b8ece331509f7a975b90501f41e83ad905e4141753fedf3f2711b2bc70a8efbc \
    --hash=sha256:b979a42815410432420275412633960807178b1ce26591a16ce06e78a5bd4bb2 \
    --hash=sha256:be4f9b3c9338ac5dd217c5847e21521b396c8117f78dc420d495a5c49bbef874 \
    --hash=sha256:bf8c8481d026b85dd70c5fa7dde85b2333aed0b32a2602bcd38a900cbd78a49c \
    --hash=sha256:c61617eaae0112ca154da87ffb99b73af2c74067acac28dfb9a4455b019dff2e \
    --hash=sha256:c6d19cb4999d03231e8730a5f66c8f5068bc3b532677eb39dab0f600bff3e312 \
    --hash=sha256:c7753871eb57e6a5f4646f6168590c6653073dea5e9e720b201c8875332df4c8 \
    --hash=sha256:c7f92daa0d2a1c76f07264abddf8cbabd30152a2f09c3270e50f0c7efdf5dcac \
    --hash=sha256:cbd5f73073ed19c378d4c35499db1e3e703a5b1a324e521204065967bfaa7a18 \
    --hash=sha256:cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269 \
    --hash=sha256:d636338c8f21b0df2f84657b00bc34f9313f826ef93f1155bc743607e4a0c5eb \
    --hash=sha256:dc75da5a20951049f7b773145f998f69d181adad9c58a0ff36e0cf1d73c10e10 \
    --hash=sha256:e23a66a763fbe83fcc210bc77c27e5a5ea380ebf091c06f34d8561b695e5a40f \
    --hash=sha256:e8cbb54454dbf1bbf2ff08dd7693e8d94ac94b1a20f70f4b3b813d52ecb5cbc1 \
    --hash=sha256:ee2c4728c691245e24501fcd7a97b5b381236b9985bc445bba88cdce7d1b5784 \
    --hash=sha256:f0535693ce476a722b718b002d5d2c27d47e71ca945276ac194409c98e74c492 \
    --hash=sha256:f19cc87343eaa55255e76b31259a570072ac95d6ae82c92dd34b97691f5e49dc \
    --hash=sha256:f21d057f3e5f5491067e5b292498073b73847d48799b099803fef100775fcc52 \
    --hash=sha256:f87dbdc42e78ee0f7ea180c03f8c78e80a949e373066629bd90fefff10552dff \
    --hash=sha256:fa34eb47969297471db7b7f193622c7e3ee839ec05abd05f1fe104d5b1b1dcf4 \
    --hash=sha256:fdccb3a0e184b03e9baa673b15a809cf36c339c85dbda0ebc25a698846dfbee8
    # via psycopg
pydantic==2.13.5 \
    --hash=sha256:346a034f080da3755d8e9cb5e00e8b07de1d39e4f6e2c87d8ab7cafa0b269a73 \
    --hash=sha256:51a9c5f7b2f8e636f04c6cada605d9b6a3bf1348fdf945a3d8869b19bba0ee08
    # via fastapi
pydantic-core==2.46.5 \
    --hash=sha256:013d6f3483d81e02e7c328831808f336c8596ee33b4bd4026b9ffb1e960b8942 \
    --hash=sha256:03b9666e41e35d8909852ba191a0607520f81b74eaf12ccf8737005dbb313821 \
    --hash=sha256:045ab3b6d308439e32b81cc173bba5b9018bc6ed896afd0c65b3b009b1699af5 \
    --hash=sha256:0bddb4020d8f04175865ccd17eff3040874fc11fb593f424edb452653b4b947c \
    --hash=sha256:0cdbada856a1c69a7624a64d3d9aefe79300bd6ef827b43a4f265010b9b55184 \
    --hash=sha256:0fc5be0abd4a407e200d844b404e33639a554e7bd0d448e7b9ae181be4789ac2 \
    --hash=sha256:10416c15b8839ecc4ef4d0885da76da6fd0f67333a0eb8aff6d93c4b8f2910fc \
    --hash=sha256:15f4a94963c95accac15b7b657bb177d3ad82bb90b0d0526d9a9b85079925db5 \
    --hash=sha256:18a09e1e1011b462f2e32774f25859ef1223d5c2b0546a633cf56654710721e0 \
    --hash=sha256:193375f3548919d3f0b60936ca113ada3e38f264f91b9b8e0508efaad57be931 \
    --hash=sha256:1a353f84de772f423b5ffb11d7ae352fbbef0f446f3c0b0af0f8236d7233606e \
    --hash=sha256:1e449def1945a462c464331254e5a44fca7c3b4f9aedf59ec2f50f8066dd8e25 \
    --hash=sha256:1e5aad1220a1192c42341c8fd4a8686657e73ab2a920c970bdc4de334fe3193d \
    --hash=sha256:200aa3dc9f8d54f0754f43247c0bad0999fdcfbfd2488384dd44f37279271fe6 \
    --hash=sha256:2471fd51c61c610e1dcf7de44d7299283661654d11264ab4802b303368d69c47 \
    --hash=sha256:24922243639cbdac66c75fcb6fd6495a9cb52b213d62f9a0d16f0310b1ff8038 \
    --hash=sha256:28a6a556cd3b6066bea827857f9d9cce027c96f776e512f544a581f9e42161f8 \
    --hash=sha256:2bc9419666990c06d7397831f2126a1ecc3594aaa3ff7de5bf2d066802f4e07b \
    --hash=sha256:2cbd9a5eff05e51c447c34dfa4632145b26b09120cf04bd0c871e44c1a5e1c9a \
    --hash=sha256:2d330aaba8621b1edcec8ae2c4050f63b84ccf6d98723a8f212e9684713abf0e \
    --hash=sha256:2d5d76654becf5efd62c9e51c3756c67b49498b0c9a40884934c40807adbd074 \
    --hash=sha256:337639ba62a11acde6ef3aeb08c8ea755f8ef1fe5e513356c0f36a2b0d7568b0 \
    --hash=sha256:347ec774390c87326a2e4929d58d3f7e8763a104d5d35f4cd595a4c952366433 \
    --hash=sha256:356c8368cbc321050b169595683a2e1d63413b1e0e2868b330af9fc14c616d3f \
    --hash=sha256:37ae34309d7bd8c0d61ab839668058f2a7962ea1fc51d105d2db228fe0618034 \
    --hash=sha256:37ea7b83c935e5b0d68c9449b82651accf78a10828b2c02b2f2d9e9496446c21 \
    --hash=sha256:3a3e26b6a8274211bddee2d0e4d0d42778f17a34510f49d2ec44b58abfc41736 \
    --hash=sha256:3aa166e99c4f2985407fb8714aebede877ecb5455cf321b606adca926d30d5a0 \
    --hash=sha256:3d2652072b2d774947ba5cf78a9e59644ac62ee572daf6dd2e1dfe905e15b2b7 \
    --hash=sha256:40375c2d05acec10323e45dfe2077ac44bc74659008614af5069034e2cfc781c \
    --hash=sha256:413a717a410d0c817ef5b786a059415550b3794e1d0c2abffd9efb93a3d9f7b4 \
    --hash=sha256:46c25dda9d092a06c08db76ffe0a197107904d0dfac653f7d5306bbcd6d6119c \
    --hash=sha256:49776eab08766a08dfff7012f8b422dcd7e25e43b316eedf0477c24fcfa84b7c \
    --hash=sha256:4d44cf99ddebf875f9b68cc267aa684c99b7b44fe63ee1cac4ec163807290069 \
    --hash=sha256:4dedce55295becb61921e386b99d4f2706045306e7fa52249a33004c837379fb \
    --hash=sha256:4f8507560a9284e1370bb048ed4282012fbef4e8d109875b95e884d228552061 \
    --hash=sha256:4fdc8b93a41521988916eeaa271173fcca7fa0803d62f87675aac8dcec1c8e29 \
    --hash=sha256:5086029a57366b8cf81b130a43908738095c270c21a8d7f0e8bdfdb89718e2f3 \
    --hash=sha256:52e24eacdb536cade636aa90fb851835222becff8484b7001fdc78cb0290f2aa \
    --hash=sha256:53feb344243bb9510a9dec7bf3cf1b64d88a98af5dc7872a5160465f8b198c8e \
    --hash=sha256:545f26c504b27c3758439a5e6d9349931f0a04f855668d5fe323c89e82300a38 \
    --hash=sha256:54d510bac3ee52247af28ed4bb18a1e799f040ac60fd2bf5ccd4c92f1fbe786f \
    --hash=sha256:5cb482e9e84c851f4e623fe4acc1ced89168cf1fe18f7089db4548c8f5bbb65b \
    --hash=sha256:5e81740c09e310f5aa5cbd3e434a01c154d4bef93241c7877b39f211d2b78ba8 \
    --hash=sha256:5ee239d575f80b08eca11f6e20f90c4c695de7825c67eefe6091fbf20dda648e \
    --hash=sha256:5f194189415698233dd1114a093a9b56e61e2c57e11b469be3b0506f46f0771c \
    --hash=sha256:5f93c5fe914d75fbec9a49209b00da5f08e9e467d69da2b1510c81940cfd10be \
    --hash=sha256:657b40d6240c0a7b6a64b30f22d1e3aa631c7e846c621b0c0f6d1d75e2e15ea6 \
    --hash=sha256:6d30e1a4f138b8951063e9a394752a9179b51da288ffa507b1e659222f4c1793 \
    --hash=sha256:6f7b393a8b3da82f5c1fc0751e6d01ac6c55b93c18226a60bdfba4a724efafd1 \
    --hash=sha256:701b2e04b560eeb4bddf7a25ab8ca476176e34fdbd9a0e18196f0d12d4685f0b \
    --hash=sha256:771cf63ae0b1b50dd22e5f3e3549fab5f3f4ff1635d352a9e1a97fe01c7b2e64 \
    --hash=sha256:79bdfa52f843137045b2d081cc05c120ba6665d29b7559c2c47690906f39279f \
    --hash=sha256:7ac031912d54f3d83ef3b3eb98dfabc1608802e2202263d25957eeed40b94761 \
    --hash=sha256:7b0fc826b16c55e561e5d2a0c5c77b051ba1d92808118c4e4b5390f5e0cf191d \
    --hash=sha256:7c6be839a5a8312626b32029a415644a0846b420bc8b52b95b28cd92da162168 \
    --hash=sha256:816ff0a6550ffc06c098ccd2e0698600f9aa7da192a79eaa6f9af504a35db869 \
    --hash=sha256:82a36973cf8a2ef5406f4fe2edbf8ed0c99629535d959e0b100c76a32535a111 \
    --hash=sha256:837b396ca3d7b74091ca623f6cbd8351bd42d670a79c2683e79fb089f06a2de5 \
    --hash=sha256:850a08d167dde16db8702c274f320c7be9d7da6f6dff2b58b18f9e815bd94f5b \
    --hash=sha256:8816f3d218beb4b787de5c9759c259b8fa61f9dec42dc7811f320a33771778b7 \
    --hash=sha256:892a881d5f68c2b9ea304b7a6c2c60d9343df578a311b0f86b94bc8f1ffe8129 \
    --hash=sha256:895395f8918627b04efb1ad2a4cf605387143300ba03304cd1dfa6d03f5e095e \
    --hash=sha256:8b10e3e8fd7ddc2bd915848a2768e44c15b22936f1cc54c462ad1164deb02655 \
    --hash=sha256:8e24d8f05fa2d28513d94e877e9c75ad66175376209b3977f916e240e623193c \
    --hash=sha256:8feeac04b5794e513e710af2f9c87d49f31a6dc47967bb264a1fed61a8989bec \
    --hash=sha256:9432f3598db432cb51c5b37fdbf29a60fcccc79e30d37a05022776a6bc4ab689 \
    --hash=sha256:976e1128455aa595ea04c79ccfedff1aaeab96ee013fcc916bed120c4f0ad94f \
    --hash=sha256:978e7b97d4824b5be09c69fb70507cbde3b0323fc147332ca40a94d9a6a0ebbf \
    --hash=sha256:97bf8de4d541598c94a59344eeb988a94c08ff76b5723c41f6567ec18c7892ea \
    --hash=sha256:97cf3eb53a8cccacf9d46686a0926186c9bfb5574f2ed66d3639d5fe117cd3a9 \
    --hash=sha256:9b68938dd5b0c783d88ff8e2dcc69451b5eb936fe212d516b21b9d5567f6d464 \
    --hash=sha256:9c4b71f10dd532fb7a5cbc8f58707779e64f03a258c2bf8bfbaecfcd9970b519 \
    --hash=sha256:9f47b8a949e60f027f0aa0a6f6c7b7e9c55cbf4380d10b344e282fa4e7ab1e1b \
    --hash=sha256:a1dee1b804ff4d11c663636cf15d2ea47e9f79cd56c033fb1cbf08924842a48f \
    --hash=sha256:a2468d93d181667a7abd66e1b64bb9f76f361b0fef8faddf687456453576f5ee \
    --hash=sha256:a2a5e1d0ff29adddc9f6d6821a66302e4493f8ca898b715b6b1182c2c201ea0a \
    --hash=sha256:a39ac25a9a2fa4072efdb429833c4a4c8009a51ff9eea3eeae131713cd27991e \
    --hash=sha256:a445486499897b88a7d6c310c88ed64dd37b1b59bfd7ae9107490bbb362f47d6 \
    --hash=sha256:a91c17edf6eea2402cb5457b4c89e99bc5ed1004aa34c4adf1d4258c1a5c22c2 \
    --hash=sha256:ab4b66edffb32d9e951efb3814bd104b8367a7501b81b955cacb5726d897389f \
    --hash=sha256:aca6c767f552b21b10f774aeac128e828eafb796adfa1b666a18bf6321453c3a \
    --hash=sha256:acf8a67ba51f4ca9ddbd0e6b3000a65ac51ab734661778b3e7ba64d99a710f2f \
    --hash=sha256:b10ec717381bdbfafef34607824db4c91de69ff085e4fca3b2af91b4fa17e68a \
    --hash=sha256:b49924c73a235e969511bf2aabdff3beebf9820931f646c80274d5d780010c47 \
    --hash=sha256:b6acfb46a814762367fb7ba0828b0a17d441b92ce249a0e007474c9072662dda \
    --hash=sha256:b7ca9034437b6022f941f4857459562ee00a560b97e7cce8a0ec5a74fc6766e0 \
    --hash=sha256:b98134087d9de723658d17a42c7d0da8d6e2ef08015dee7dc93889047315f5e4 \
    --hash=sha256:b9fe6fb92520e3fd61f2e49000b6911b188824f089b75973ea06d6267f0b476d \
    --hash=sha256:bce57638e08ac148e5778cce7feb968307a727d66f8e2274a543d0cf0c9ad6a3 \
    --hash=sha256:c14ad3bdc85ee7f318742c457ca3968a92126d144b15721c759033bfb06296c2 \
    --hash=sha256:c1c43ad4339643d70ebb8124e1305a7dab423001eff58bb41a0f731adbc98355 \
    --hash=sha256:c3471e5c4a949c26ec00a77f01df59096aa9495877de76fd60a980f8ee6be461 \
    --hash=sha256:c583b927a8838dab890706a6fa7573fbb8b70e24000ef9f7238e2d6f6435a5ed \
    --hash=sha256:c76fe65e607be28c7fd4d56fc3c42b1583aa058ce3408b7ad0fd540171d31f9f \
    --hash=sha256:c7ea57fc63aa7da93a1bd2d644e6577befae10c52c4e36377635eea1056a74f5 \
    --hash=sha256:cd5214352ae68f3b5e9af7768bdc5253695ee069675db3480518420b3be881f2 \
    --hash=sha256:cdbb78909f52b981d3b2d56b97328d71eb0b974c36bd77c920123a7ebb192829 \
    --hash=sha256:cdc8b74ecc48c0cb1e9607a05ec4e9e88db60a19ffcc9a1d5f9088ede40c8dc0 \
    --hash=sha256:d0a24b40877af2de4950252be9d21eaf7fb07660f3c2cae1f56c6b599ada5266 \
    --hash=sha256:d22a945598fb91236b4dd793a6e42e4f3dd7740bb5aace5ebd7d4c08d13bb575 \
    --hash=sha256:d2f9fc07a8042a8f95925b35c4f04f469707c981fc33245b6ca187cf5d2dd290 \
    --hash=sha256:d625a186a65201c23a9e3b8ed9c47e90a026e03256608cc91851c6709096844f \
    --hash=sha256:d925f3d9afd05a8c0fb3a1031463a8d59ebe5e2afad297e29c78be19e13b4e62 \
    --hash=sha256:e64e88d5585bea9ce95861079de72006c7fa6d3df4e3a3b65ba31eb979c15c9f \
    --hash=sha256:e652ab17569c94bff5475520f907b7148b8c24036a8ebbe5cf7cf7493d28579a \
    --hash=sha256:e7b891faeedeafba41b2983e5001a81b6a915b69544c7e7570d1989ce1c36ac7 \
    --hash=sha256:e80675d75ae2cd14372cb65cad5400d9347a3d3f6c13000183f22dfd027283ed \
    --hash=sha256:e9c134bb666dd54b778b9fc0d2b50cbb7f979b9e3716f26a88c9ab3b6fc1dd0f \
    --hash=sha256:eb7d8d0e5886a89a55d2eef490e272fa965a9d57c6b29a5b5088a7997ec2cad1 \
    --hash=sha256:ecb42011e12ee19cafbc312887cbf3546959fe02fbad44f272d4be5baa997615 \
    --hash=sha256:ef3fbbf161dc9351a2fe0422e51b129f9e97e42385bd0320b309c15f7d287dd8 \
    --hash=sha256:efd62a42486f1bda5d24cb4f63d15a3c7768375fe83d36f9417b4ad7a2fb20b3 \
    --hash=sha256:f077d0b97ab11fa7dcc633fca53515f290bca8a8a633e966d5b6d1879d9ed01a \
    --hash=sha256:f332f0e72a5a0400141f830744e141bf9f97917878dbe968669e8a7fefea78ff \
    --hash=sha256:f7b0ec93a2893de856652154d73b7ba622f26fa97726487dcac373de5f4c6084 \
    --hash=sha256:fa10ef4112775900e7a0661068635eb67b2ab824fbde764de6e0e21982a93db0 \
    --hash=sha256:fc5d783bd4a2387e97b8a2d5ec781cfb92b3d893bf82370548e99db5915935d3 \
    --hash=sha256:fc8515076c11f3cfdf4fb142dcca0fe384b1230a3b5415458ac84f3e0903ec13 \
    --hash=sha256:ff218293c9c806138dca139765e3b067621be52bcd93cdc14c7711be7ddc90a9
    # via pydantic
pygments==2.21.0 \
    --hash=sha256:2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9 \
    --hash=sha256:610ca751c9bc2492b38eb9a38a7fbc93edbbb2d7182edaf34e66ae493dee5c8c
    # via pytest
pypdf==6.19.0 \
    --hash=sha256:7e5d6e730e7dae87d560a2cee218b852f6498c8be61966f3cd02ead971e48d14 \
    --hash=sha256:bbc43aca292369ccc6cbc8a921991ecf2538a3587ab5a116eff06c321d647155
    # via -r backend/requirements.txt
pytest==9.1.1 \
    --hash=sha256:1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313 \
    --hash=sha256:37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c
    # via -r backend/requirements.txt
python-dateutil==2.9.0.post0 \
    --hash=sha256:37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3 \
    --hash=sha256:a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427
    # via botocore
python-multipart==0.0.32 \
    --hash=sha256:be54b7f3fa167bb83e4fcd936b887b708f4e57fe75911c02aebf53efaf8d938e \
    --hash=sha256:ff6d3f776f16878c894e52e107296ffc890e913c611b1a4ec6c44e2821fe2e23
    # via -r backend/requirements.txt
reportlab==5.0.1 \
    --hash=sha256:1c36e6bb0e71780c72331eba60da7f602e8d4389a8723825af71342e49d791e8 \
    --hash=sha256:ebd13154be1c8515e665de70bd2d303ae9ddc3ef47e44afd5116441ca0283a26
    # via -r backend/requirements.txt
s3transfer==0.19.2 \
    --hash=sha256:ba0309fd86be3c27dbf78cdd813c13c5e1df16e5874b99d2535ebbdfb9892993 \
    --hash=sha256:d8168eccca828cbb2cd573675333f3bddd254313a9c42494b84c76b539e8ba25
    # via boto3
six==1.17.0 \
    --hash=sha256:4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274 \
    --hash=sha256:ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81
    # via python-dateutil
sqlalchemy==2.0.54 \
    --hash=sha256:03cbf8d9a67da618bd65500a5eb3ddac89caf4c61e99b2f03fa4a1952a0725a9 \
    --hash=sha256:0e7a76d5dce712ce50435d0f97181eb955ec27d138c004176f01282e063bac52 \
    --hash=sha256:1019abef05a4b5eafc8eae6fb483167fa28a4dbe5f518d577b744f31a5276a37 \
    --hash=sha256:18a8b6417cbb7b735cf91c2b59453c2a554cefa0a8d7bd15aa35740739410d77 \
    --hash=sha256:1d887fbd5d248e250807bd801e697fc73e3b44866ce5f093dbc90512e75bde25 \
    --hash=sha256:24ae093dec196ba37fc2beb0316de53e7871d3d246a50faecbbb53034e41ded2 \
    --hash=sha256:264460333ed0b177cbb1956355d0ee4e0cab83fb415c934ce12a25db2e7be39c \
    --hash=sha256:279bde5bfedb0f3e0f1bdbcffa2daa39c6c54d90f9408ef3b1802001597199f0 \
    --hash=sha256:2f61a70b3b82e2ec7ad6a4f2301422b9ca93ff06917983e41317bcae878bddf6 \
    --hash=sha256:31d5458672a6f72db2c087f4a5098b3c8503ea0254186ff29205d63afa9401a4 \
    --hash=sha256:32de6deded25e8b9b11d07428d496ff24dfbc882b8e990c177266948cb5f3d9e \
    --hash=sha256:330d35f9ce815d35cb1daab038d4d7ec0e907f4d7ed0fc8bcb2411d1f23d0b50 \
    --hash=sha256:34e10af7d274a5c4b7cd0fced5e7361008c5e07d97dd48a93852d5b2f1142a1c \
    --hash=sha256:3de32cc6721eb42c3aad35bcfb244bb7a18f66c00f3582aae6281d6287a339b5 \
    --hash=sha256:415239eb2ddbbc508ba4cac97affb91c0f210548fd1731edda6e529b0bb93015 \
    --hash=sha256:48611087a75d26d798003645c688c7d3cfc26b89dbe4a2c568d6b378d330deae \
    --hash=sha256:4e55a0b96a1577a1e108c91ccdeeb9cd92768f28ce206597311c3bf6d6423abd \
    --hash=sha256:4e8a4afcc7d714cc3c8a57facdff4c3529f5f93d71e54b7da1e03e022c9089c9 \
    --hash=sha256:5417322b3c025dd82918725d3bf09ec105fac95efc195722b8b06e1d9c381139 \
    --hash=sha256:5800ddea045c2c860ef1d359a07a3066c7c0c426f45e3abc3874e116cb3c6937 \
    --hash=sha256:63cae7210fea9899e0bf35c1f1ae55d3ddd9c6d47cae8b6b43d945afa79dd65b \
    --hash=sha256:68d994e9b0d0423a02a20039631fa6fcbb7fa829a992f7605025774940305d19 \
    --hash=sha256:69cab115c40fd02c5a22c68e4ee630fa6ef9a1650f1de944419aab1f7096fc4f \
    --hash=sha256:6b6d4e601c4f6d85e99bb3416107cc9418c5603ca73d4ee0f5f8d79c2a1ed9e8 \
    --hash=sha256:6f84099e4b04a5c2d44500a2a8302eee5af4bc6fee63e8c6e9cf6786e747280e \
    --hash=sha256:7108f410f596c5ac22fe43ba467e864d27c4e1477ae89e90c6c87120b2c1be23 \
    --hash=sha256:744fb219a390561a57dbbd59cd69a22b5b5b2facfde794c1f79236dd847fa67a \
    --hash=sha256:762cfe4d340c56368256d936a98b620a9a5650e49c1c84eba51d6edd17ffefb2 \
    --hash=sha256:7b973e4facc2f80e42f5a27b841feb7e202661881a6320580abbe597a28a007f \
    --hash=sha256:7d03084f3352dd92048cb19c71d90f116d076c9c7937e0ebc7752c4685de6d38 \
    --hash=sha256:7e33a631ab1474f8fe6b910bd1a07b7b8009c4c78cdd3fb18001b03e3bc2e1d2 \
    --hash=sha256:842540e4382472f23c79589995752648d14696a8200d0807ed8c5c59c92ade44 \
    --hash=sha256:87ba8834318b0d8dc94fc6f405d071b5c08be32a6c3fd68107fd6952ee949615 \
    --hash=sha256:92622fbbda1b1fe1632f3402a6e516a93c0e41d9158839c6b3dfb12117f26b72 \
    --hash=sha256:a0956dc754d3884da7fe60097110ec7a8a105d26afa2f0844468f4b1598c6912 \
    --hash=sha256:abd6b21bc58e91c1932eb5d6d7f1bd44a551dfec7b6a7f517c3638ccd67233a0 \
    --hash=sha256:b374e3bc91e246a942592a98ba6a23be76fff21358b00546ac8c0ebc0fd0e00b \
    --hash=sha256:b67749f7da3985a529cefbb1474783cb91ef44371cb9713630bade3de908760d \
    --hash=sha256:b67c1744e453af833667fc1b84de07adb4a64f3536ef52a8ec5ac2b941d43970 \
    --hash=sha256:b6c419c83a87fd901f0b1b5338ffcb82471c3ac32a86bb8883688c18f8eb85d3 \
    --hash=sha256:b9086b8ad48280ef6a7ba68262d5e44f7db1c4cb1973e8cdae8a9f467ae66f51 \
    --hash=sha256:baa8521e8ee9f24e75dfc7aaabc08020e551ef0d48d7c3e3536f5cddf277586b \
    --hash=sha256:c1a3455a88f66e4851792bedb098ed942912253d31caed1dbc58afbfa9e875cd \
    --hash=sha256:ca05f4e7852cf48083b0cf157e4f9504b7068780422a50fa82f45353b8c5e14a \
    --hash=sha256:cad78d04254967bdbcccbed5e631d88fe4868530946ab0929aa45e9032849518 \
    --hash=sha256:cf89e92bf0d4204a6afcc17af27b9271ed9c7e34e17d6f80c085d431ea4a1747 \
    --hash=sha256:d31a2bc06a854ee52dd86b455be4df7c750b28817e2d1b884e31fff126c4fd7b \
    --hash=sha256:d566099d60cded87d175d4171dc899b9613d2e3b663573364565ca1b27ccd241 \
    --hash=sha256:d65f8ca742ef1e1e14bc417ef59dc2ddf207a7b66b30cfdc6152447314e030cf \
    --hash=sha256:d6adf80277372a89910a0f3ccfe960b846d279dc55b366dd5c5ec07f41c84758 \
    --hash=sha256:deeab253fe01a770f634c7007c73702df2324c868a79ae756507a9a1a76294fe \
    --hash=sha256:e08397c6c42f53b2488acde9108b8bfefd52d7afd1bf2f03d2ffcab7a204aceb \
    --hash=sha256:e1f455db400289f77ba2f7b62fffafe8875153812d0e3777aa4ff2b34a0fc1f7 \
    --hash=sha256:f3ea33bcf0aa599c1511fe5c9fb126f45aa450419084c4823f786155fe4c79f1 \
    --hash=sha256:f4e8f955d13af83fb4e35c3472e5377ee22d3445eada1e5e48199588edb69835 \
    --hash=sha256:f5c09090b1a7c4d389d1431f820931e8df318f82caafc53f9a72c872fef467c5 \
    --hash=sha256:f8cc6532f930c27974e9239e5ce5abebe7600ba9807cea4fcf42f1b6cab18fe7 \
    --hash=sha256:ffba7eb2d67c7505e82a0902aa854d8824b74c28a183820d6a8bd3cfd0f812c2
    # via
    #   -r backend/requirements.txt
    #   alembic
starlette==1.6.0 \
    --hash=sha256:a86dd39d14bb45f85a3d18525215a9ef0cfd1f192ac793220e72598c90335f0c \
    --hash=sha256:d4e3ac5e546444960c710297a3c9fc3f7ebae1b7e963f3d36173b49da535be9b
    # via fastapi
typing-extensions==4.16.0 \
    --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8 \
    --hash=sha256:dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5
    # via
    #   alembic
    #   anyio
    #   fastapi
    #   psycopg
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   starlette
    #   typing-inspection
typing-inspection==0.4.4 \
    --hash=sha256:547274fa6b0a561ccf549cc9524b999a578e737d015d8709d021f9d0d13bea47 \
    --hash=sha256:65b8397ba37ccbce054456aaccddfc91e6e3083c92824df348d96ca832f3f147
    # via
    #   fastapi
    #   pydantic
urllib3==2.8.0 \
    --hash=sha256:0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3 \
    --hash=sha256:63bf2ead4c879426ebf22ef2a781eeb4aa3b4ae798a0435506f8687fd5bb9b63
    # via botocore
uvicorn==0.53.0 \
    --hash=sha256:a9356f0cb89b3b8621529c5d5eebd69bfe154f4c3f68b4cf2de47e45fa855c2e \
    --hash=sha256:e8dca71ec86dce5f04e333f0d56cdedf942446e6643b9cea1af0d6d3a02cb03e
    # via -r backend/requirements.txt

```
### `backend/tests/test_pilot_package_c.py`

size=27366; sha256=3b617978b1c99ada475622e12ef96c77d6cc683ed14395346b0d264afad09124; truncated=false

```text
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import threading
from types import ModuleType, SimpleNamespace
from typing import Any
from urllib.parse import unquote

from alembic.config import Config
import psycopg
import pytest
from sqlalchemy.engine import make_url

from app.core.config import get_settings


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bootstrap() -> ModuleType:
    return load_module("paprnav_package_c_bootstrap", REPO_ROOT / "infra/bootstrap/bootstrap.py")


@pytest.fixture(scope="module")
def release_builder() -> ModuleType:
    return load_module("paprnav_package_c_release_builder", REPO_ROOT / "scripts/build_pilot_release_context.py")


def test_ecs_json_key_becomes_the_actual_application_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    terraform = (REPO_ROOT / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    selector = '${aws_secretsmanager_secret.database_url.arn}:DATABASE_URL::'
    assert terraform.count(selector) == 2
    assert 'name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn' not in terraform

    published = json.dumps(
        {"DATABASE_URL": "postgresql+psycopg://paprnav_app:p%40ss@db.internal:5432/paprnav"}
    )
    injected = json.loads(published)["DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", injected)
    get_settings.cache_clear()
    assert get_settings().database_url == injected


@pytest.mark.parametrize(
    "password",
    [
        "admin@%reserved",
        "colon:/question?#brackets[]percent%at@",
    ],
)
def test_admin_credentials_survive_url_and_configparser(
    bootstrap: ModuleType,
    password: str,
) -> None:
    connection = {
        "host": "db.internal",
        "port": 5432,
        "dbname": "paprnav",
        "user": "paprnav_admin",
        "password": password,
        "sslmode": "require",
    }
    environment_url = bootstrap.alembic_environment_url(connection)
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", environment_url)
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.username == "paprnav_admin"
    assert parsed.password == password
    assert parsed.host == "db.internal"


def test_migration_passes_only_configparser_safe_url(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "admin@%reserved"

    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {
                "SecretString": json.dumps(
                    {
                        "username": "paprnav_admin",
                        "password": password,
                        "host": "db.internal",
                        "port": 5432,
                    }
                )
            }

    captured: dict[str, str] = {}

    def run(*_: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs["env"])  # type: ignore[arg-type]
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    bootstrap.run_migration(Secrets())
    assert "%%" in captured["DATABASE_URL"]
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", captured["DATABASE_URL"])
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.password == password


def test_terraform_gates_are_blocking_and_bind_actual_zone_identity() -> None:
    variables = (REPO_ROOT / "infra/terraform/variables.tf").read_text(encoding="utf-8")
    main = (REPO_ROOT / "infra/terraform/main.tf").read_text(encoding="utf-8")
    load_balancer = (REPO_ROOT / "infra/terraform/load_balancer.tf").read_text(encoding="utf-8")
    versions = (REPO_ROOT / "infra/terraform/versions.tf").read_text(encoding="utf-8")
    assert 'check "external_inputs"' not in variables
    assert 'check "image_repositories"' not in main
    assert 'resource "terraform_data" "deployment_input_gate"' in main
    assert 'resource "terraform_data" "certificate_input_gate"' in main
    assert main.count("precondition {") >= 8
    assert 'data "aws_route53_zone" "pilot"' in main
    assert "data.aws_route53_zone.pilot.name" in main
    assert "private_zone = false" in main
    assert load_balancer.count("data.aws_route53_zone.pilot.zone_id") == 1

    assert 'variable "pilot_certificate_arn"' in variables
    assert 'data "aws_acm_certificate" "pilot"' in main
    for exact_filter in (
        'domain      = var.pilot_hostname',
        'statuses    = ["ISSUED"]',
        'types       = ["AMAZON_ISSUED"]',
        'key_types   = ["RSA_2048"]',
        'tags        = { Project = "paprnav" }',
        'most_recent = false',
    ):
        assert exact_filter in main
    for bound_value in (
        "data.aws_acm_certificate.pilot.arn == var.pilot_certificate_arn",
        "data.aws_acm_certificate.pilot.domain == var.pilot_hostname",
        'data.aws_acm_certificate.pilot.status == "ISSUED"',
        'lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"',
        '"arn:aws:acm:${var.aws_region}:${var.aws_account_id}:certificate/"',
    ):
        assert bound_value in main
    assert 'resource "aws_acm_certificate"' not in load_balancer
    assert 'resource "aws_acm_certificate_validation"' not in load_balancer
    assert 'resource "aws_route53_record" "certificate_validation"' not in load_balancer
    assert "certificate_arn   = data.aws_acm_certificate.pilot.arn" in load_balancer
    assert "depends_on = [terraform_data.certificate_input_gate]" in load_balancer
    assert 'version = "= 5.100.0"' in versions

    expected = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:"
    good = expected + "a" * 64
    wrong_repository = "527257972989.dkr.ecr.us-east-1.amazonaws.com/other/api@sha256:" + "a" * 64
    mutable = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api:latest"
    assert good.startswith(expected)
    assert not wrong_repository.startswith(expected)
    assert not mutable.startswith(expected)


def one(values: list[Any]) -> Any:
    assert len(values) == 1
    return values[0]


@pytest.fixture(scope="module")
def waf_plan() -> dict[str, Any]:
    # Supply the actual output of `terraform test -json -verbose` from an
    # isolated, current-source module. No handwritten HCL parser or substitute
    # regex/normalization table is used. Terraform also asserts the field and
    # transformation structure directly in package_c.tftest.hcl.
    path = os.getenv("PAPRNAV_PACKAGE_C_TERRAFORM_TEST_JSON")
    if not path:
        pytest.skip("generate the current Package C Terraform mock-plan JSON to run the WAF oracle")
    records = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.startswith("{"):
                continue  # `terraform validate` may precede the JSON stream.
            item = json.loads(line)
            if item.get("type") == "test_plan":
                # Provider schemas are large and are not part of this oracle.
                item["test_plan"].pop("provider_schemas", None)
            if item.get("type") in ("test_plan", "test_summary"):
                records.append(item)
    assert one([item["test_summary"] for item in records if item.get("type") == "test_summary"])["status"] == "pass"
    plan = one([
        item["test_plan"] for item in records
        if item.get("type") == "test_plan" and item.get("@testrun") == "waf_auth_and_upload_contract"
    ])
    return {item["address"]: item["change"]["after"] for item in plan["resource_changes"]}


def active_block(block: dict[str, Any]) -> tuple[str, Any]:
    return one([(key, value) for key, value in block.items() if value not in (None, [], {})])


def waf_matches(statement: dict[str, Any], patterns: dict[str, list[str]], request: dict[str, Any]) -> bool:
    """Evaluate only the emitted WAF subset; unknown constructs fail the test."""
    kind, values = active_block(statement)
    clause = one(values)
    if kind == "and_statement":
        return all(waf_matches(child, patterns, request) for child in clause["statement"])
    if kind == "not_statement":
        return not waf_matches(one(clause["statement"]), patterns, request)
    if kind == "rate_based_statement":
        return waf_matches(one(clause["scope_down_statement"]), patterns, request)
    field, selection = active_block(one(clause["field_to_match"]))
    if field == "method":
        value = request["method"]
    elif field == "uri_path":
        value = request["path"]
    elif field == "single_header":
        value = request["headers"].get(one(selection)["name"], "")
    elif field == "body":
        assert one(selection)["oversize_handling"] == "MATCH"
        value = request["body"]
    else:
        raise AssertionError(f"unsupported WAF field: {field}")
    for transform in sorted(clause["text_transformation"], key=lambda item: item["priority"]):
        operation = transform["type"]
        if operation == "URL_DECODE":
            value = unquote(value)
        elif operation == "LOWERCASE":
            value = value.lower()
        else:
            assert operation == "NONE", f"unsupported WAF transform: {operation}"
    if kind == "regex_pattern_set_reference_statement":
        return any(re.search(pattern, value) is not None for pattern in patterns[clause["arn"]])
    if kind == "byte_match_statement":
        if clause["positional_constraint"] == "EXACTLY":
            return value == clause["search_string"]
        assert clause["positional_constraint"] == "STARTS_WITH"
        return value.startswith(clause["search_string"])
    assert kind == "size_constraint_statement"
    assert clause["comparison_operator"] == "GT"
    return len(value) > clause["size"]


def assert_waf_contract(plan: dict[str, Any]) -> None:
    acl = plan["aws_wafv2_web_acl.pilot"]
    rules = {rule["name"]: rule for rule in acl["rule"]}
    patterns = {
        value["arn"]: [item["regex_string"] for item in value["regular_expression"]]
        for address, value in plan.items() if address.startswith("aws_wafv2_regex_pattern_set.")
    }
    assert len(rules) == 4 and len(patterns) == 3
    assert not one(acl["visibility_config"])["sampled_requests_enabled"]
    assert all(not one(rule["visibility_config"])["sampled_requests_enabled"] for rule in rules.values())
    request = {"method": "POST", "path": "", "headers": {}, "body": b"x" * 8193}
    auth_cases = {
        "login-rate-limit": (30, 100, [
            "/api/v1/auth/login", "/api/v1/auth/login/", "/api/v1/auth/%6cogin",
            "/api/v1/auth/%6Cogin/", "/api/v1/auth%2flogin%2f",
        ]),
        "invitation-rate-limit": (40, 50, [
            "/api/v1/auth/invitations", "/api/v1/auth/invitations/",
            "/api/v1/auth/%69nvitations", "/api/v1/auth/invitations/accept",
            "/api/v1/auth/invitations/accept/", "/api/v1/auth/invitations/%61ccept",
            "/api/v1/auth/invitations/%61ccept/", "/api/v1/auth/invitations%2Faccept%2F",
        ]),
    }
    for name, (priority, limit, paths) in auth_cases.items():
        rule = rules[name]
        assert rule["priority"] == priority and active_block(one(rule["action"]))[0] == "block"
        statement = one(rule["statement"])
        rate = one(statement["rate_based_statement"])
        assert rate["aggregate_key_type"] == "IP" and rate["limit"] == limit
        predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
        assert len(predicates) == 2
        for predicate in predicates:
            kind, values = active_block(predicate)
            value = one(values)
            expected_field, expected_transform = (
                ("method", "NONE") if kind == "byte_match_statement" else ("uri_path", "URL_DECODE")
            )
            assert active_block(one(value["field_to_match"]))[0] == expected_field
            assert value["text_transformation"] == [{"priority": 0, "type": expected_transform}]
        for path in paths:
            assert waf_matches(statement, patterns, {**request, "path": path}), path
            assert not waf_matches(statement, patterns, {**request, "method": "GET", "path": path}), path
        assert not waf_matches(statement, patterns, {**request, "path": paths[0] + "-extra"})
        assert not waf_matches(statement, patterns, {**request, "method": "%50OST", "path": paths[0]})
        other = "/api/v1/auth/invitations/accept" if name == "login-rate-limit" else "/api/v1/auth/login"
        assert not waf_matches(statement, patterns, {**request, "path": other})

    # Bind the raw upload exception AND its body-size/managed-rule context.
    managed = rules["aws-managed-common"]
    assert managed["priority"] == 10
    common = one(one(managed["statement"])["managed_rule_group_statement"])
    assert common["name"] == "AWSManagedRulesCommonRuleSet" and common["vendor_name"] == "AWS"
    override = one(common["rule_action_override"])
    assert override["name"] == "SizeRestrictions_BODY"
    assert active_block(one(override["action_to_use"]))[0] == "count"
    oversize = rules["block-oversize-body-except-reviewed-upload"]
    assert oversize["priority"] == 20 and active_block(one(oversize["action"]))[0] == "block"
    statement = one(oversize["statement"])
    predicates = one(statement["and_statement"])["statement"]
    assert one(predicates[0]["size_constraint_statement"])["size"] == 8192
    exception = one(one(predicates[1]["not_statement"])["statement"])
    upload_predicates = one(exception["and_statement"])["statement"]
    assert len(upload_predicates) == 3
    uri = one(upload_predicates[1]["regex_pattern_set_reference_statement"])
    assert active_block(one(uri["field_to_match"]))[0] == "uri_path"
    assert uri["text_transformation"] == [{"priority": 0, "type": "NONE"}]
    assert patterns[uri["arn"]] == [r"^/api/v1/aircraft/[^/]+/uploads$"]
    upload = {**request, "path": "/api/v1/aircraft/plane/uploads", "headers": {"content-type": "multipart/form-data; boundary=pilot"}}
    assert not waf_matches(statement, patterns, upload)
    for change in (
        {"method": "GET"}, {"path": upload["path"] + "/"},
        {"path": "/api/v1/aircraft/plane/%75ploads"},
        {"path": "/api/v1/aircraft/plane%2Fuploads"},
        {"path": "/api/v1/aircraft/plane/uploads-extra"},
        {"headers": {"content-type": "application/json"}},
        {"path": "/api/v1/auth/invitations/accept"},
    ):
        assert waf_matches(statement, patterns, {**upload, **change}), change
    assert not waf_matches(statement, patterns, {**request, "body": b"x" * 8192})
    assert waf_matches(statement, patterns, request)


def test_waf_generated_auth_normalization_and_raw_upload_exception(waf_plan: dict[str, Any]) -> None:
    assert_waf_contract(waf_plan)
    # The exact remediation-1 defect must be rejected by this same oracle.
    old = deepcopy(waf_plan)
    invitation = next(rule for rule in old["aws_wafv2_web_acl.pilot"]["rule"] if rule["name"] == "invitation-rate-limit")
    rate = one(one(invitation["statement"])["rate_based_statement"])
    predicates = one(one(rate["scope_down_statement"])["and_statement"])["statement"]
    one(predicates[0]["byte_match_statement"])["text_transformation"][0]["type"] = "URL_DECODE"
    one(predicates[1]["regex_pattern_set_reference_statement"])["text_transformation"][0]["type"] = "NONE"
    with pytest.raises(AssertionError):
        assert_waf_contract(old)


def test_acm_policy_is_exactly_read_only_and_account_region_bounded() -> None:
    generator = load_module(
        "paprnav_package_c_policy_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    hostname = "pilot.example.com"
    policy = generator.generate(
        "Z123456789",
        hostname,
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555",
    )
    statements = policy["deployPolicySupplement"]["Statement"]
    acm_statements = [item for item in statements if any(action.lower().startswith("acm:") for action in item["Action"])]
    actions = {action for item in acm_statements for action in item["Action"]}
    assert actions == {
        "acm:ListCertificates",
        "acm:DescribeCertificate",
        "acm:ListTagsForCertificate",
        "acm:GetCertificate",
    }
    assert all("*" not in action for action in actions)
    assert all("ExportCertificate" not in action for action in actions)

    inventory = one([item for item in acm_statements if item["Action"] == ["acm:ListCertificates"]])
    metadata = one([item for item in acm_statements if "acm:DescribeCertificate" in item["Action"]])
    assert inventory["Resource"] == "*"
    assert metadata["Resource"] == "arn:aws:acm:us-east-1:527257972989:certificate/*"
    for item in (inventory, metadata):
        assert item["Condition"] == {"StringEquals": {"aws:RequestedRegion": "us-east-1"}}

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    matrix_acm = one([row for row in matrix["rows"] if any(action.startswith("acm:") for action in row["actions"])])
    assert set(matrix_acm["actions"]) == actions
    assert "mutation" not in matrix_acm["condition"].lower()


def test_release_builder_candidate_gate_and_preserved_dirt_separation(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_policy = {
        "approvedMigrationAuthoritySha256": {"backend/app/core/config.py": "0" * 64},
        "protectedBlobSha256": {"backend/app/models/core.py": "1" * 64},
    }
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    reviewed_path = "backend/Dockerfile"
    preserved_path = "backend/app/models/core.py"
    absolute = tmp_path / reviewed_path
    absolute.parent.mkdir(parents=True)
    absolute.write_text("FROM scratch\n", encoding="utf-8")
    manifest = tmp_path / "overlay.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "paprnav-reviewed-overlay-v2",
                "sourceCommit": "a" * 40,
                "reviewedInputs": [
                    {"path": reviewed_path, "sha256": release_builder.hashlib.sha256(absolute.read_bytes()).hexdigest()}
                ],
                "preservedExclusions": [preserved_path],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(release_builder, "dirty_paths", lambda: {reviewed_path, preserved_path})
    reviewed, preserved = release_builder.overlay_files(
        manifest,
        "a" * 40,
        {"forbiddenPaths": [], "forbiddenPrefixes": []},
        boundary_policy,
    )
    assert reviewed == {reviewed_path: b"FROM scratch\n"}
    assert preserved == [preserved_path]

    protected_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    protected_manifest["reviewedInputs"] = [
        {"path": preserved_path, "sha256": "1" * 64}
    ]
    protected_manifest["preservedExclusions"] = [reviewed_path]
    manifest.write_text(json.dumps(protected_manifest), encoding="utf-8")
    with pytest.raises(release_builder.ContextError, match="protected authority"):
        release_builder.overlay_files(
            manifest,
            "a" * 40,
            {"forbiddenPaths": [], "forbiddenPrefixes": []},
            boundary_policy,
        )


def test_release_builder_blocks_failed_package_a_authority(
    release_builder: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = load_module(
        "verify_pilot_release_boundary",
        REPO_ROOT / "scripts/verify_pilot_release_boundary.py",
    )
    monkeypatch.setitem(sys.modules, "verify_pilot_release_boundary", boundary)

    policy_path = tmp_path / "boundary.json"
    policy_path.write_text('{"version":"test"}\n', encoding="utf-8")
    monkeypatch.setattr(release_builder, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(release_builder, "BOUNDARY_POLICY", policy_path)
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {"status": "pass", "errors": []})
    assert release_builder.candidate_authority("a" * 40) == {"version": "test"}
    monkeypatch.setattr(boundary, "verify_release", lambda *_: {
        "status": "fail",
        "errors": ["protected release blob differs"],
    })
    with pytest.raises(release_builder.ContextError, match="protected release blob differs"):
        release_builder.candidate_authority("a" * 40)


def postgres_connection_args() -> dict[str, object]:
    raw = os.getenv("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL", "")
    if not raw:
        pytest.skip("PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL is not set")
    parsed = make_url(raw)
    if not parsed.database or not parsed.database.startswith("paprnav_package_c_"):
        pytest.fail("Package C PostgreSQL tests require a disposable paprnav_package_c_* database")
    return {
        "host": parsed.host,
        "port": parsed.port or 5432,
        "dbname": parsed.database,
        "user": parsed.username,
        "password": parsed.password,
        "sslmode": "disable",
    }


def prepare_first_admin_database(connection_args: dict[str, object], bootstrap: ModuleType) -> None:
    # Synthetic transaction/control fixture only. It does not establish that
    # first-admin succeeds against the full sealed 0029 migrated schema.
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS pilot_control CASCADE")
            cursor.execute("DROP TABLE IF EXISTS product_events, organization_memberships, organizations, users CASCADE")
            cursor.execute(
                "CREATE TABLE users (id varchar(36) PRIMARY KEY, email text NOT NULL, name text NOT NULL, "
                "password_hash text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organizations (id varchar(36) PRIMARY KEY, name text NOT NULL, type text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE organization_memberships (id varchar(36) PRIMARY KEY, organization_id varchar(36) NOT NULL, "
                "user_id varchar(36) NOT NULL, role text NOT NULL, status text NOT NULL)"
            )
            cursor.execute(
                "CREATE TABLE product_events (id varchar(36) PRIMARY KEY, actor_user_id varchar(36), "
                "organization_id varchar(36), event_type text, event_source text, subject_type text, "
                "subject_id varchar(36), properties_json json)"
            )
            bootstrap.install_control_schema(cursor)
        connection.commit()


def relation_counts(connection_args: dict[str, object]) -> list[int]:
    with psycopg.connect(**connection_args) as connection:
        with connection.cursor() as cursor:
            result = []
            for relation in (
                "users",
                "organizations",
                "organization_memberships",
                "product_events",
                "pilot_control.bootstrap_consumptions",
            ):
                cursor.execute(f"SELECT count(*) FROM {relation}")
                result.append(cursor.fetchone()[0])
            return result


def test_first_admin_failure_boundaries_and_concurrency(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_args = postgres_connection_args()
    prepare_first_admin_database(connection_args, bootstrap)

    class Secrets:
        def get_secret_value(self, *, SecretId: str) -> dict[str, str]:
            if SecretId == "admin":
                return {"SecretString": json.dumps({
                    "username": "paprnav_admin",
                    "password": connection_args["password"],
                    "host": connection_args["host"],
                    "port": connection_args["port"],
                    "dbname": connection_args["dbname"],
                })}
            assert SecretId == "first-admin"
            return {"SecretString": json.dumps({"password": "first-admin-password"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin")
    monkeypatch.setenv("PAPRNAV_FIRST_ADMIN_SECRET_ARN", "first-admin")
    monkeypatch.setenv("PAPRNAV_DATABASE_SSLMODE", "disable")
    identity = {"email": "first@example.com", "name": "First Admin", "organization": "Paprnav"}
    for point in ("user", "organization", "membership", "audit", "consumption"):
        monkeypatch.setenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER", point)
        with pytest.raises(bootstrap.BootstrapError, match="injected failure"):
            bootstrap.run_first_admin(Secrets(), identity=identity)
        assert relation_counts(connection_args) == [0, 0, 0, 0, 0]
    monkeypatch.delenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER")

    barrier = threading.Barrier(2)

    def synchronized_connect(**kwargs: object) -> psycopg.Connection:
        barrier.wait(timeout=10)
        return psycopg.connect(**kwargs)

    identities = (
        identity,
        {"email": "other@example.com", "name": "Other Admin", "organization": "Other"},
    )

    def attempt(value: dict[str, str]) -> str:
        try:
            bootstrap.run_first_admin(Secrets(), connect=synchronized_connect, identity=value)
            return "success"
        except bootstrap.BootstrapError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = sorted(executor.map(attempt, identities))
    assert outcomes == ["rejected", "success"]
    assert relation_counts(connection_args) == [1, 1, 1, 1, 1]

    with pytest.raises(bootstrap.BootstrapError, match="permanently unavailable"):
        bootstrap.run_first_admin(Secrets(), identity=identity)


def test_three_dockerfiles_are_pinned_non_root_and_bootstrap_inventory_is_sealed() -> None:
    api = (REPO_ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    frontend = (REPO_ROOT / "frontend/paprnav-frontend/Dockerfile").read_text(encoding="utf-8")
    bootstrap = (REPO_ROOT / "infra/bootstrap/Dockerfile").read_text(encoding="utf-8")
    assert "@sha256:" in api and "USER 10001:10001" in api
    assert "@sha256:" in frontend and "USER 10001:10001" in frontend
    assert "@sha256:" in bootstrap and "USER 10001:10001" in bootstrap
    assert "COPY --chown=root:root migration/ /migration/" in bootstrap
    assert "backend/" not in bootstrap and "frontend/" not in bootstrap
    context_policy = json.loads((REPO_ROOT / ".ai/pilot-package-c-context-v1.json").read_text(encoding="utf-8"))
    assert all("0030" in path for path in context_policy["forbiddenPaths"][:3])

```
### `frontend/paprnav-frontend/.dockerignore`

size=72; sha256=eb7532f74421b9e785d8c0e03711f19e80d52ef4b0ebb31f4b9ca20149787606; truncated=false

```text
.git
.next
node_modules
npm-debug.log*
.env
.env.*
!.env.example
tests


```
### `frontend/paprnav-frontend/Dockerfile`

size=1180; sha256=3f4e91bd8de248533293750490a4fb7346255a59fd9756965173944cbafab418; truncated=false

```text
ARG NODE_BASE=node:24.13.0-alpine3.23@sha256:cd6fb7efa6490f039f3471a189214d5f548c11df1ff9e5b181aa49e22c14383e
FROM ${NODE_BASE} AS dependencies
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

FROM ${NODE_BASE} AS builder
WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_PAPRNAV_ENV=pilot \
    NEXT_PUBLIC_PAPRNAV_API_BASE_URL=""
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE_BASE} AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_PAPRNAV_ENV=pilot \
    NEXT_PUBLIC_PAPRNAV_API_BASE_URL="" \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup -S -g 10001 paprnav && adduser -S -D -H -u 10001 -G paprnav paprnav
COPY --from=builder --chown=10001:10001 /workspace/public ./public
COPY --from=builder --chown=10001:10001 /workspace/.next/standalone ./
COPY --from=builder --chown=10001:10001 /workspace/.next/static ./.next/static
USER 10001:10001
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1
CMD ["node", "server.js"]

```
### `frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx`

size=3488; sha256=20e1ba41c07086e00a981e09577e966f27fa2311931f933c8baa40ed2d73f295; truncated=false

```text
"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { acceptInvitation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function InvitationPage() {
  const router = useRouter();
  const [invitationCode, setInvitationCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setIsSubmitting(true);
    try {
      await acceptInvitation({ invitationCode, password });
      router.push("/logbook");
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Invitation could not be accepted.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Accept invitation</CardTitle>
          <CardDescription>Paste the invitation code sent to you by the pilot operator.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="invitation-code">Invitation code</Label>
              <Input
                id="invitation-code"
                value={invitationCode}
                onChange={(event) => setInvitationCode(event.target.value)}
                autoComplete="off"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Accepting..." : "Accept invitation"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            <Link href="/" className="font-medium text-primary hover:text-primary/80">
              Back to sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

```
### `frontend/paprnav-frontend/tests/pilot-observability.test.mjs`

size=940; sha256=4b05f4297d57a0f63b5de11e6b2a0786c72f4d258f467fd0085fefe76cb31a2c; truncated=false

```text
import assert from "node:assert/strict";
import test from "node:test";

import { listVisibleObservability } from "../src/lib/api.ts";

const EMPTY_OBSERVABILITY = {
  events: [],
  workflowEvents: [],
  feedback: [],
};

test("ordinary and platform-admin observability readers use distinct scopes", async () => {
  const requestedPaths = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    requestedPaths.push(String(input));
    return new Response(JSON.stringify(EMPTY_OBSERVABILITY), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  try {
    await listVisibleObservability(false, { status: "open" });
    await listVisibleObservability(true, { status: "open" });
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.deepEqual(requestedPaths, [
    "/api/v1/observability?status=open",
    "/api/v1/observability/admin?status=open",
  ]);
});

```
### `infra/aws-iam/pilot-policy-matrix.json`

size=2898; sha256=553ba411b90fef2cdf0577d07c44d85ffc3514c06f33c1284f1bf67cca1a3db2; truncated=false

```text
{
  "version": "paprnav-pilot-policy-matrix-v1",
  "accountId": "527257972989",
  "region": "us-east-1",
  "deployPolicyArn": "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy",
  "rows": [
    {
      "principal": "operator-admin prerequisite",
      "actions": ["iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"],
      "resourceTemplate": "${DEPLOY_POLICY_ARN}"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["acm:ListCertificates", "acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
      "resourceTemplate": "arn:aws:acm:${REGION}:${ACCOUNT}:certificate/*",
      "condition": "Read-only lookup only: ListCertificates uses Resource=* and all ACM actions are restricted to the configured region; certificate metadata reads are additionally account/region bounded by the certificate ARN. Certificate provisioning, validation, tagging, deletion, export, and renewal-record ownership remain outside the Terraform deploy role."
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["wafv2:CreateWebACL", "wafv2:GetWebACL", "wafv2:UpdateWebACL", "wafv2:DeleteWebACL", "wafv2:CreateRegexPatternSet", "wafv2:GetRegexPatternSet", "wafv2:UpdateRegexPatternSet", "wafv2:DeleteRegexPatternSet", "wafv2:AssociateWebACL", "wafv2:DisassociateWebACL", "wafv2:List*", "wafv2:TagResource", "wafv2:UntagResource"],
      "resourceTemplate": "arn:aws:wafv2:${REGION}:${ACCOUNT}:regional/*/paprnav-*/*"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets", "route53:GetChange", "route53:ListTagsForResource"],
      "resourceTemplate": "arn:aws:route53:::hostedzone/${HOSTED_ZONE_ID}"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["iam:CreateServiceLinkedRole"],
      "resourceTemplate": "exact RDS, ECS, and ELB service-linked-role ARNs",
      "condition": "matching iam:AWSServiceName"
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret", "secretsmanager:PutResourcePolicy", "secretsmanager:GetResourcePolicy", "secretsmanager:DeleteResourcePolicy"],
      "resourceTemplate": "arn:aws:secretsmanager:${REGION}:${ACCOUNT}:secret:/paprnav/pilot/*",
      "excludes": ["secretsmanager:GetSecretValue", "secretsmanager:PutSecretValue"]
    },
    {
      "principal": "Terraform deploy role",
      "actions": ["secretsmanager:CreateSecret", "secretsmanager:TagResource", "kms:DescribeKey"],
      "resourceTemplate": "RDS-managed rds!db-* names and exact aws/secretsmanager KMS key"
    }
  ]
}

```
### `infra/bootstrap/Dockerfile`

size=1238; sha256=6b2daf14fa8768d436cad4ecffcf4f81af040834dbcc40a4ff2fd51e697f3262; truncated=false

```text
ARG PYTHON_BASE=python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7
FROM ${PYTHON_BASE}

ARG PAPRNAV_SOURCE_COMMIT
ARG PAPRNAV_MIGRATION_MANIFEST_SHA256
ARG PAPRNAV_BOOTSTRAP_MANIFEST_SHA256

LABEL org.opencontainers.image.revision="${PAPRNAV_SOURCE_COMMIT}" \
      io.paprnav.migration-manifest-sha256="${PAPRNAV_MIGRATION_MANIFEST_SHA256}" \
      io.paprnav.bootstrap-manifest-sha256="${PAPRNAV_BOOTSTRAP_MANIFEST_SHA256}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PAPRNAV_DISABLE_DOTENV=1 \
    PAPRNAV_MIGRATION_ROOT=/migration

RUN addgroup --system --gid 10001 paprnav \
    && adduser --system --uid 10001 --ingroup paprnav --home /nonexistent --no-create-home paprnav

WORKDIR /bootstrap
COPY bootstrap/requirements.lock /bootstrap/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r /bootstrap/requirements.lock \
    && rm -rf /root/.cache /tmp/*

COPY --chown=root:root migration/ /migration/
COPY --chown=root:root bootstrap/bootstrap.py bootstrap/grant-manifest.json bootstrap/reference-data.json /bootstrap/
RUN chmod -R a-w /migration /bootstrap

USER 10001:10001
ENTRYPOINT ["python", "-I", "-B", "/bootstrap/bootstrap.py"]

```
### `infra/bootstrap/bootstrap.py`

size=18877; sha256=11df37c395e8bb2955f8b6f828943119e73dee0ba7b16ff0db49e9f1718073d4; truncated=false

```text
#!/usr/bin/env python3
"""Fixed-phase bootstrap for the sealed Paprnav pilot image.

This module deliberately has no import from ``app``. Production credentials are
read in-process from task-scoped Secrets Manager ARNs and are never accepted as
command-line values or printed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from typing import Any, Callable, Mapping
from urllib.parse import quote
import uuid

import psycopg
from psycopg import sql


APP_ROLE = "paprnav_app"
CONTROL_SCHEMA = "pilot_control"
ADVISORY_LOCK_KEY = 824082
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000
PHASES = ("migration", "runtime-role", "reference", "first-admin")
BOOTSTRAP_ROOT = Path(__file__).resolve().parent
MIGRATION_ROOT = Path(os.getenv("PAPRNAV_MIGRATION_ROOT", "/migration"))
GRANT_MANIFEST = BOOTSTRAP_ROOT / "grant-manifest.json"
REFERENCE_DATA = BOOTSTRAP_ROOT / "reference-data.json"
SAFE_IDENTITY = re.compile(r"^[^\x00-\x1f\x7f]+$")


class BootstrapError(RuntimeError):
    """A sanitized, operator-actionable bootstrap failure."""


def emit(phase: str, status: str, **identifiers: str) -> None:
    payload = {"phase": phase, "status": status, **identifiers}
    print(json.dumps(payload, sort_keys=True), flush=True)


def require_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise BootstrapError(f"required environment input is absent: {name}")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootstrapError(f"invalid sealed JSON input: {path.name}") from exc
    if not isinstance(value, dict):
        raise BootstrapError(f"sealed JSON input is not an object: {path.name}")
    return value


def secret_json(client: Any, arn: str, *, exact_keys: set[str] | None = None) -> dict[str, Any]:
    response = client.get_secret_value(SecretId=arn)
    value = response.get("SecretString")
    if not isinstance(value, str):
        raise BootstrapError("required secret is not a SecretString")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise BootstrapError("required secret is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise BootstrapError("required secret JSON is not an object")
    if exact_keys is not None and set(parsed) != exact_keys:
        raise BootstrapError("required secret has an unexpected schema")
    return parsed


def admin_connection(secret_client: Any) -> dict[str, Any]:
    value = secret_json(secret_client, require_env("PAPRNAV_ADMIN_SECRET_ARN"))
    required = {"username", "password", "host", "port"}
    if not required.issubset(value):
        raise BootstrapError("RDS administrator secret is missing required fields")
    if value["username"] != "paprnav_admin":
        raise BootstrapError("RDS administrator secret has the wrong username")
    return {
        "host": value["host"],
        "port": int(value["port"]),
        "dbname": value.get("dbname") or os.getenv("PAPRNAV_DATABASE_NAME", "paprnav"),
        "user": value["username"],
        "password": value["password"],
        "sslmode": os.getenv("PAPRNAV_DATABASE_SSLMODE", "require"),
    }


def sqlalchemy_url(connection: Mapping[str, Any]) -> str:
    return (
        "postgresql+psycopg://"
        f"{quote(str(connection['user']), safe='')}:{quote(str(connection['password']), safe='')}"
        f"@{connection['host']}:{connection['port']}/{quote(str(connection['dbname']), safe='')}"
        f"?sslmode={quote(str(connection['sslmode']), safe='')}"
    )


def alembic_environment_url(connection: Mapping[str, Any]) -> str:
    """Return a URL that survives Alembic's ConfigParser interpolation.

    ``env.py`` copies ``DATABASE_URL`` into Alembic's Config object.  Percent
    escapes in a valid SQLAlchemy URL therefore need ConfigParser's literal
    percent spelling.  This escaping belongs only at the migration-process
    boundary; the application secret retains the ordinary URL.
    """

    return sqlalchemy_url(connection).replace("%", "%%")


def run_migration(secret_client: Any) -> None:
    connection = admin_connection(secret_client)
    command = [
        sys.executable,
        "-I",
        "-B",
        "-m",
        "alembic",
        "-c",
        str(MIGRATION_ROOT / "alembic.ini"),
        "upgrade",
        "20260913_0029",
    ]
    environment = {
        "DATABASE_URL": alembic_environment_url(connection),
        "PAPRNAV_DISABLE_DOTENV": "1",
        "PAPRNAV_ENV": "pilot",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PATH": os.environ.get("PATH", ""),
    }
    result = subprocess.run(
        command,
        cwd=MIGRATION_ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        raise BootstrapError("sealed migration failed; child output suppressed")


def relation_inventory(cursor: Any, relation_kind: str) -> list[str]:
    if relation_kind == "tables":
        cursor.execute(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname='public' ORDER BY tablename"
        )
    elif relation_kind == "sequences":
        cursor.execute(
            "SELECT sequencename FROM pg_catalog.pg_sequences "
            "WHERE schemaname='public' ORDER BY sequencename"
        )
    else:  # pragma: no cover - internal programming guard
        raise AssertionError(relation_kind)
    return [row[0] for row in cursor.fetchall()]


def exact_grant_inventory(cursor: Any, manifest: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    cursor.execute("SELECT version_num FROM public.alembic_version")
    rows = cursor.fetchall()
    if rows != [(manifest["expectedHead"],)]:
        raise BootstrapError("database is not at the sealed migration head")
    actual_tables = relation_inventory(cursor, "tables")
    actual_sequences = relation_inventory(cursor, "sequences")
    expected_tables = sorted([*manifest["publicTables"], *manifest["excludedTables"]])
    expected_sequences = sorted(manifest["publicSequences"])
    if actual_tables != expected_tables or actual_sequences != expected_sequences:
        raise BootstrapError("post-migration relation inventory differs from the reviewed grant manifest")
    return sorted(manifest["publicTables"]), expected_sequences


def install_control_schema(cursor: Any) -> None:
    cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION CURRENT_USER").format(
        sql.Identifier(CONTROL_SCHEMA)
    ))
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pilot_control.bootstrap_consumptions (
          bootstrap_key text PRIMARY KEY CHECK (bootstrap_key = 'first-admin'),
          consumed_at timestamptz NOT NULL DEFAULT now(),
          user_id varchar(36) NOT NULL,
          organization_id varchar(36) NOT NULL,
          identity_sha256 char(64) NOT NULL
        )
        """
    )
    cursor.execute("REVOKE ALL ON SCHEMA pilot_control FROM PUBLIC")


def ensure_app_role(cursor: Any, password: str) -> None:
    cursor.execute("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=%s", (APP_ROLE,))
    if cursor.fetchone() is None:
        cursor.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(
            sql.Identifier(APP_ROLE)
        ))
    cursor.execute(
        sql.SQL("ALTER ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}").format(
            sql.Identifier(APP_ROLE), sql.Literal(password)
        )
    )


def apply_exact_grants(cursor: Any, tables: list[str], sequences: list[str], database_name: str) -> None:
    cursor.execute(sql.SQL("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
    cursor.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
        sql.Identifier(database_name), sql.Identifier(APP_ROLE)
    ))
    cursor.execute(sql.SQL("REVOKE ALL ON SCHEMA pilot_control FROM {}").format(sql.Identifier(APP_ROLE)))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES REVOKE ALL ON TABLES FROM {}").format(
        sql.Identifier(APP_ROLE)
    ))
    cursor.execute(sql.SQL("ALTER DEFAULT PRIVILEGES REVOKE ALL ON SEQUENCES FROM {}").format(
        sql.Identifier(APP_ROLE)
    ))
    for table in tables:
        identifier = sql.Identifier("public", table)
        cursor.execute(sql.SQL("REVOKE ALL ON TABLE {} FROM {}").format(identifier, sql.Identifier(APP_ROLE)))
        cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {} TO {}").format(
            identifier, sql.Identifier(APP_ROLE)
        ))
    for sequence in sequences:
        identifier = sql.Identifier("public", sequence)
        cursor.execute(sql.SQL("REVOKE ALL ON SEQUENCE {} FROM {}").format(identifier, sql.Identifier(APP_ROLE)))
        cursor.execute(sql.SQL("GRANT USAGE, SELECT ON SEQUENCE {} TO {}").format(
            identifier, sql.Identifier(APP_ROLE)
        ))


def app_connection(admin: Mapping[str, Any], password: str) -> dict[str, Any]:
    return {**admin, "user": APP_ROLE, "password": password}


def run_runtime_role(secret_client: Any, connect: Callable[..., Any] = psycopg.connect) -> None:
    admin = admin_connection(secret_client)
    manifest = load_json(GRANT_MANIFEST)
    generated_password = secrets.token_urlsafe(48)
    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            tables, sequences = exact_grant_inventory(cursor, manifest)
            install_control_schema(cursor)
            ensure_app_role(cursor, generated_password)
            apply_exact_grants(cursor, tables, sequences, str(admin["dbname"]))
        connection.commit()

    app_secret_arn = require_env("PAPRNAV_APP_DATABASE_SECRET_ARN")
    token = str(uuid.uuid4())
    payload = json.dumps(
        {"DATABASE_URL": sqlalchemy_url(app_connection(admin, generated_password))},
        sort_keys=True,
        separators=(",", ":"),
    )
    publication = secret_client.put_secret_value(
        SecretId=app_secret_arn,
        SecretString=payload,
        ClientRequestToken=token,
        VersionStages=["AWSCURRENT"],
    )
    version_id = publication.get("VersionId")
    if not isinstance(version_id, str) or not version_id:
        raise BootstrapError("app database secret publication returned no VersionId")
    metadata = secret_client.describe_secret(SecretId=app_secret_arn)
    stages = metadata.get("VersionIdsToStages", {}).get(version_id, [])
    if "AWSCURRENT" not in stages:
        raise BootstrapError("published app database secret version is not AWSCURRENT")
    with connect(**app_connection(admin, generated_password)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user")
            if cursor.fetchone() != (APP_ROLE,):
                raise BootstrapError("fresh runtime-role connection proof failed")


def run_reference(secret_client: Any, connect: Callable[..., Any] = psycopg.connect) -> None:
    data = load_json(REFERENCE_DATA)
    rows = data.get("logbookSections")
    if not isinstance(rows, list) or not rows:
        raise BootstrapError("reference manifest has no logbook sections")
    admin = admin_connection(secret_client)
    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            for row in rows:
                if set(row) != {"id", "key", "name", "sortOrder"}:
                    raise BootstrapError("reference row has an unexpected schema")
                cursor.execute(
                    """
                    INSERT INTO public.logbook_sections (id, key, name, sort_order)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET name=EXCLUDED.name, sort_order=EXCLUDED.sort_order
                    """,
                    (row["id"], row["key"], row["name"], row["sortOrder"]),
                )
        connection.commit()


def clean_identity(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 255 or SAFE_IDENTITY.fullmatch(normalized) is None:
        raise BootstrapError(f"invalid first-admin identity input: {name}")
    return normalized


def password_hash(password: str) -> str:
    if len(password.encode("utf-8")) < 12:
        raise BootstrapError("first-admin password does not meet the minimum length")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join((PASSWORD_ALGORITHM, str(PASSWORD_ITERATIONS), salt.hex(), digest.hex()))


def maybe_fail(point: str) -> None:
    if os.getenv("PAPRNAV_BOOTSTRAP_FAIL_AFTER") == point:
        raise BootstrapError(f"injected failure after {point}")


def run_first_admin(
    secret_client: Any,
    connect: Callable[..., Any] = psycopg.connect,
    identity: Mapping[str, str] | None = None,
) -> dict[str, str]:
    admin = admin_connection(secret_client)
    password_value = secret_json(
        secret_client,
        require_env("PAPRNAV_FIRST_ADMIN_SECRET_ARN"),
        exact_keys={"password"},
    )
    password = password_value["password"]
    if not isinstance(password, str):
        raise BootstrapError("first-admin password secret has the wrong type")
    supplied_identity = identity or {
        "email": require_env("PAPRNAV_FIRST_ADMIN_EMAIL"),
        "name": require_env("PAPRNAV_FIRST_ADMIN_NAME"),
        "organization": require_env("PAPRNAV_FIRST_ADMIN_ORGANIZATION"),
    }
    if set(supplied_identity) != {"email", "name", "organization"}:
        raise BootstrapError("first-admin identity has an unexpected schema")
    email = clean_identity("email", supplied_identity["email"]).lower()
    name = clean_identity("name", supplied_identity["name"])
    organization_name = clean_identity("organization", supplied_identity["organization"])
    identity_sha256 = hashlib.sha256(email.encode("utf-8")).hexdigest()
    user_id = f"usr_{uuid.uuid4().hex}"
    organization_id = f"org_{uuid.uuid4().hex}"
    membership_id = f"mem_{uuid.uuid4().hex}"
    event_id = f"pev_{uuid.uuid4().hex}"

    with connect(**admin) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (ADVISORY_LOCK_KEY,))
            cursor.execute("SELECT to_regclass('pilot_control.bootstrap_consumptions')")
            if cursor.fetchone() != ("pilot_control.bootstrap_consumptions",):
                raise BootstrapError("bootstrap control schema is absent; run runtime-role first")
            cursor.execute("SELECT count(*) FROM pilot_control.bootstrap_consumptions")
            consumed = cursor.fetchone()[0]
            counts: list[int] = []
            for table in ("users", "organizations", "organization_memberships"):
                cursor.execute(sql.SQL("SELECT count(*) FROM public.{}").format(sql.Identifier(table)))
                counts.append(cursor.fetchone()[0])
            if consumed != 0 or counts != [0, 0, 0]:
                raise BootstrapError("first-admin bootstrap is permanently unavailable")

            cursor.execute(
                "INSERT INTO public.users (id,email,name,password_hash,status) VALUES (%s,%s,%s,%s,'active')",
                (user_id, email, name, password_hash(password)),
            )
            maybe_fail("user")
            cursor.execute(
                "INSERT INTO public.organizations (id,name,type) VALUES (%s,%s,'platform')",
                (organization_id, organization_name),
            )
            maybe_fail("organization")
            cursor.execute(
                """
                INSERT INTO public.organization_memberships
                  (id,organization_id,user_id,role,status)
                VALUES (%s,%s,%s,'platform_admin','active')
                """,
                (membership_id, organization_id, user_id),
            )
            maybe_fail("membership")
            cursor.execute(
                """
                INSERT INTO public.product_events
                  (id,actor_user_id,organization_id,event_type,event_source,subject_type,subject_id,properties_json)
                VALUES (%s,%s,%s,'pilot_first_admin_created','bootstrap','user',%s,%s::json)
                """,
                (
                    event_id,
                    user_id,
                    organization_id,
                    user_id,
                    json.dumps({"identitySha256": identity_sha256}, separators=(",", ":")),
                ),
            )
            maybe_fail("audit")
            cursor.execute(
                """
                INSERT INTO pilot_control.bootstrap_consumptions
                  (bootstrap_key,user_id,organization_id,identity_sha256)
                VALUES ('first-admin',%s,%s,%s)
                """,
                (user_id, organization_id, identity_sha256),
            )
            maybe_fail("consumption")
        connection.commit()
    return {"userId": user_id, "organizationId": organization_id}


def secrets_client() -> Any:
    # Keep the AWS SDK import inside the production boundary; unit tests inject
    # a fake client without importing an application package.
    import boto3

    return boto3.client("secretsmanager", region_name=require_env("AWS_REGION"))


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    phase = args.phase
    try:
        client = secrets_client()
        if phase == "migration":
            run_migration(client)
            result: dict[str, str] = {}
        elif phase == "runtime-role":
            run_runtime_role(client)
            result = {}
        elif phase == "reference":
            run_reference(client)
            result = {}
        else:
            result = run_first_admin(client)
        emit(phase, "success", **result)
        return 0
    except (BootstrapError, psycopg.Error, OSError, ValueError) as exc:
        # Messages are written by this module and never include secret values or
        # connection strings. Driver exceptions are intentionally suppressed.
        message = str(exc) if isinstance(exc, BootstrapError) else "phase failed; sensitive detail suppressed"
        emit(phase, "failure", reason=message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

```
### `infra/bootstrap/grant-manifest.json`

size=4295; sha256=8bb97bb77a72452eb20b2404ce0ad2139bb763ad2917c31833f13ff99aa43fac; truncated=false

```text
{
  "version": "paprnav-post-0029-runtime-grants-v1",
  "expectedHead": "20260913_0029",
  "excludedTables": [
    "alembic_version"
  ],
  "publicSequences": [],
  "publicTables": [
    "ad_amoc_provisions",
    "ad_compliance_events",
    "ad_compliance_requirements",
    "ad_compliance_triggers",
    "ad_cost_ledger_entries",
    "ad_coverage_sets",
    "ad_coverage_subscriptions",
    "ad_discovery_records",
    "ad_evidence_fragment_lifecycle_events",
    "ad_evidence_fragments",
    "ad_extraction_review_decisions",
    "ad_extraction_reviews",
    "ad_extractions",
    "ad_match_adjudications",
    "ad_match_due_state_links",
    "ad_match_evidence",
    "ad_match_results",
    "ad_publications",
    "ad_reconciliation_issues",
    "ad_source_documents",
    "ad_source_page_renditions",
    "ad_source_page_text_versions",
    "ad_source_snapshots",
    "ad_supersessions",
    "ad_target_applicability",
    "ad_v4_candidate_app_change_dependencies",
    "ad_v4_candidate_app_conditions",
    "ad_v4_candidate_app_data",
    "ad_v4_candidate_app_designation_group_members",
    "ad_v4_candidate_app_designation_groups",
    "ad_v4_candidate_app_designation_ranges",
    "ad_v4_candidate_app_designation_scopes",
    "ad_v4_candidate_app_designation_values",
    "ad_v4_candidate_app_evidence_links",
    "ad_v4_candidate_app_expression_edges",
    "ad_v4_candidate_app_expressions",
    "ad_v4_candidate_app_identity_mappings",
    "ad_v4_candidate_app_materialization_requests",
    "ad_v4_candidate_app_product_scopes",
    "ad_v4_candidate_app_projection_events",
    "ad_v4_candidate_app_projections",
    "ad_v4_candidate_app_rule_exclusions",
    "ad_v4_candidate_app_rules",
    "ad_v4_candidate_app_search_hint_groups",
    "ad_v4_candidate_app_search_hint_members",
    "ad_v4_candidate_app_search_hints",
    "ad_v4_candidate_app_semantic_nodes",
    "ad_v4_candidate_app_value_assertions",
    "ad_v4_candidate_correction_evidence_links",
    "ad_v4_candidate_correction_refs",
    "ad_v4_candidate_correction_semantic_bindings",
    "ad_v4_candidate_corrections",
    "ad_v4_candidate_evidence_bindings",
    "ad_v4_candidate_obligation_action_document_refs",
    "ad_v4_candidate_obligation_action_steps",
    "ad_v4_candidate_obligation_actions",
    "ad_v4_candidate_obligation_amoc_provisions",
    "ad_v4_candidate_obligation_branches",
    "ad_v4_candidate_obligation_data",
    "ad_v4_candidate_obligation_documents",
    "ad_v4_candidate_obligation_evidence_links",
    "ad_v4_candidate_obligation_expression_edges",
    "ad_v4_candidate_obligation_expressions",
    "ad_v4_candidate_obligation_materialization_requests",
    "ad_v4_candidate_obligation_projection_events",
    "ad_v4_candidate_obligation_projections",
    "ad_v4_candidate_obligation_recurrence_group_members",
    "ad_v4_candidate_obligation_recurrence_groups",
    "ad_v4_candidate_obligation_recurrences",
    "ad_v4_candidate_obligation_requirement_dependencies",
    "ad_v4_candidate_obligation_requirements",
    "ad_v4_candidate_obligation_semantic_nodes",
    "ad_v4_candidate_obligation_terminating_effects",
    "ad_v4_candidate_obligation_termination_edges",
    "ad_v4_candidate_obligation_timing_groups",
    "ad_v4_candidate_obligation_timing_terms",
    "ad_v4_candidate_obligation_value_assertions",
    "ad_v4_candidate_proposal_events",
    "ad_v4_candidate_proposals",
    "ad_v4_candidate_submission_relationships",
    "ad_v4_candidate_submissions",
    "ad_v4_feature_gates",
    "ad_v4_review_case_events",
    "ad_v4_review_cases",
    "ad_v4_review_draft_revisions",
    "ad_v4_review_rejections",
    "ad_v4_review_requests",
    "ad_v4_signoff_events",
    "aircraft",
    "aircraft_ad_due_states",
    "aircraft_assignments",
    "aircraft_time_states",
    "airworthiness_directives",
    "applicability_targets",
    "auth_sessions",
    "ingestion_jobs",
    "ingestion_pages",
    "installed_components",
    "logbook_entries",
    "logbook_entry_evidence",
    "logbook_sections",
    "logical_page_regions",
    "ocr_corrections",
    "ocr_runs",
    "ocr_text_spans",
    "organization_memberships",
    "organizations",
    "page_verifications",
    "product_events",
    "uploads",
    "user_feedback",
    "users",
    "workflow_status_events"
  ]
}

```
### `infra/bootstrap/reference-data.json`

size=413; sha256=9b6c3cdaae15ba1adc968c5bccb2d337e5b36cd875cc45525131b0205dd5728b; truncated=false

```text
{
  "version": "paprnav-pilot-reference-v1",
  "logbookSections": [
    {
      "id": "lbs_airframe",
      "key": "airframe",
      "name": "Airframe",
      "sortOrder": 10
    },
    {
      "id": "lbs_engine",
      "key": "engine",
      "name": "Engine",
      "sortOrder": 20
    },
    {
      "id": "lbs_propeller",
      "key": "propeller",
      "name": "Propeller",
      "sortOrder": 30
    }
  ]
}


```
### `infra/bootstrap/requirements.in`

size=55; sha256=9824b776ee52fb1c295f9c58daffa783f4adf3bc58f7593cb01899b23a8d8b7f; truncated=false

```text
alembic==1.19.1
boto3==1.43.70
psycopg[binary]==3.3.4


```
### `infra/bootstrap/requirements.lock`

size=26705; sha256=221371094f52ace94027bef0da5b06fd8f37827ccfe71cdbeced10f5c2263cc5; truncated=false

```text
# This file was autogenerated by uv via the following command:
#    uv pip compile infra/bootstrap/requirements.in --generate-hashes --python-version 3.12 --python-platform x86_64-manylinux_2_28 -o infra/bootstrap/requirements.lock
alembic==1.19.1 \
    --hash=sha256:b39018cb3d9413a19cbd54cf3c02ad33998641f0538eb77413a488a21c3e14be \
    --hash=sha256:e0fca0518118c78acc493e31bcb5402f190057aaf6df8b5b95ce94c4789cf648
    # via -r infra/bootstrap/requirements.in
boto3==1.43.70 \
    --hash=sha256:4f1e16b9eebbad3f312bb6fbf7685d40abdd52a691485cb9f09e7df60d912b41 \
    --hash=sha256:b9399cce51bec9552e61a6b85015c42dea68752e79c00a7005d84eaf7ee15fef
    # via -r infra/bootstrap/requirements.in
botocore==1.43.98 \
    --hash=sha256:6135dd639ea6d1b3b49381bc253c8a139d61f7d44cb5f7dae8e7cd1791758572 \
    --hash=sha256:84b35b10402c2fc0c265f634fbf86336eecc6489ee23f55074b329924b2cfd6f
    # via
    #   boto3
    #   s3transfer
greenlet==3.5.6 \
    --hash=sha256:0616b8f878098c5681fd8f0dc92d887551717402342a70f0abcbfea5f5ad8a44 \
    --hash=sha256:06c0e933290fba8ffe53ead4ae1b8044b0e9754b75cebf381aa2bc3e50d82fac \
    --hash=sha256:128813fc29f2336a21b4d06eedd5e16bcc7ea46f59e9ff1cb30ea70e48195d88 \
    --hash=sha256:188bf333769b7145e2b0b4a7f09615ec550ed44d3a2a8395fb7b36f0e9901e13 \
    --hash=sha256:1c20ea32a73d17b9b60e3371240e17b0068120c98a5ec01a224a7dd8c89733ba \
    --hash=sha256:2ab5f42ac6c238eb71770715e6e909ad9a1a92b6c681ccb64cd5a0f07edb953f \
    --hash=sha256:301102a49120b095e72a7838792b41233975fc1c155daec6d98f81c00c9280e0 \
    --hash=sha256:311018b46472fb26ee85870847fb89eb64cc8aaddb617400789d87076f7cfeec \
    --hash=sha256:3ac3494c381dab876cad7d0b22f3a722f3e0c8deb3a65b9e7f35ad7f58b8fcb3 \
    --hash=sha256:3c6dede9133e1da41d561bc3fb14e92b47e2ce39ae60edefaad145658ea7c5e2 \
    --hash=sha256:3dbb4596a6a4e5d47121a33ff20533a81e60f302d9e67b69909a8bc21a43f0a7 \
    --hash=sha256:3deccbb57a481e3a408fe61cdfd5c13e0678fc0a30fdd09597917ca87b4be877 \
    --hash=sha256:45663c01a4de48b9a64a2ee1509d92d1dfd3afb02b2ccfc9333029d11aef996a \
    --hash=sha256:45bfd2b51e38aaa5f9849f114d9c7c1d75f69187c849b3549cd64c465283abfa \
    --hash=sha256:460e70b033aba8ed47e2ac9b5d0d2157b05a34fbfa30a241400aef4118902cdc \
    --hash=sha256:4fb8e59f68845d56c23c031dcd79c329f345e4a9d2ffac91c3d1ab366bdc457b \
    --hash=sha256:520648db8fb92eef7b3e6013f5a6f901cdf0d6685f639c2f7a245879f865bef7 \
    --hash=sha256:5599b380c1f28efeb724e81569eac80cd92f99a85bd9775456caaf3225d40b11 \
    --hash=sha256:59deccd347735a7774223b05a93773fddbb298aba3cea21be4337fb4752dbe32 \
    --hash=sha256:5a0b2791239c99992a86c1b635b787fe2a877d9eaaa26f8891ce943832b585ae \
    --hash=sha256:5adcbbfe78bdc242c71740a02e0991cc1b2f34d33c8bb15ca45eee8fd1140942 \
    --hash=sha256:5b602b4201b965a8354d74e232364a66ff243dd142e350d035f46169bb36e13d \
    --hash=sha256:5bbda3c70dd35d60671bc33b01916802707a052130d9e50cdb871d34594d35cb \
    --hash=sha256:602024dae6d77e161f4b89491b62ca1d4f19949d79d47b2db057e476d21179d6 \
    --hash=sha256:61a61b4a95a4f97922c3a6f5606d3e360851584bd47e500a5161373c53810e3d \
    --hash=sha256:63aff70fe5aac59c72215f42ec39fcb59ff46774fa966e717f8ecb6ee2273577 \
    --hash=sha256:71890d5247020c25c21a6b65202782bfc281d4e6e244842419d30e3492bb6dcc \
    --hash=sha256:73a29b5ba642e35433166a03a3e02935e7238c4b3467fbd77523b99edea23e5b \
    --hash=sha256:7969bffa322c097bd46ae595ada6a931cefda613f18ba64587e9cff4cb320756 \
    --hash=sha256:7ac4abb3877c43af320392c664774eef6fa2cc063c79a55fc02d844a3cbe7395 \
    --hash=sha256:7f731ebac68ea06d628658295cb2d217b10186329fcf9a3b6a149045059bf92e \
    --hash=sha256:7f924a5a9d5890649566f2f6682e0d8ad8ca23028bacffbbac36dbd7fd680176 \
    --hash=sha256:874cea8bb1ec1ddccbacbd027856f6bf496f6bc18aba97a918c20e067edab236 \
    --hash=sha256:876077e7ebb8c84ed068e2b23d4c62ebb010d60df84b9591af1be2f39010ffb2 \
    --hash=sha256:886bcf1870af74c32bc310fd00a6b803445e17e51b7d5a107c7b35c0f362cc16 \
    --hash=sha256:8b27df301f56e3b3d2298095c8f7d6b68f2521f6b1693e901fa039bdbae34424 \
    --hash=sha256:8b7c73d1cef3d9ae963e9ff03f6222df43efbb9054ffd2f1969c935b7fc84c02 \
    --hash=sha256:8cda13494d86a4f12429641117cb6ac4bbbc9c30a33f711f7d3a2e5fbe4b0b7e \
    --hash=sha256:8cddea1b8339451c2fb3388e138347b6126744f33b611bdb55b7357361cfef46 \
    --hash=sha256:8dba0129b93e7091dfefaf4cf7000172741bff7f47bf6326fcf17f32fbb54d6b \
    --hash=sha256:8e67c43bdfc88d5fee6db0d3e40175b362fc95fb85f0412d233b9b203c53a575 \
    --hash=sha256:9133d68624b1f2e89ec2f554d56aea8a5b0d7168cd9320200ba58d4d794845a4 \
    --hash=sha256:916f92f2a8db10508f739d0b5e00b83defe5d1115a997c54532a6d7cf8c95404 \
    --hash=sha256:9297fb9c39b9a2c039dbcd306c410bd6906b95244dec3bba4318d36c718c164c \
    --hash=sha256:95e7c44d072db623a1aab04ce488cf9533294a77ed9d072cd503a3596f4106ac \
    --hash=sha256:975736b002ed080d124cf81a79cb7e05cb26d6b3f5c7a7b651c0fcce70353aa1 \
    --hash=sha256:97c5a53e8c1754df58e73f047a99e287d4da1bdfe64b0072fb25c87000897951 \
    --hash=sha256:9a09d59bef1db94f384b5bcc2d523694d338f3df6b757aeeaf7baca5d0c0be88 \
    --hash=sha256:a364c1ea75dc51b83a17f52fe0c79cf8bc4ddf740403bebd4581c7666eea017d \
    --hash=sha256:a3b4a01c6da07ef9f80d4fe8933b994bc99747bcea3eab0330a9c34d3c12655b \
    --hash=sha256:a5876d0a60355af98d535c47f6cd6eb0f8a432396dab26845d380b92f8412422 \
    --hash=sha256:a6a4b98a9132e0f45c9fc245a63894cfd8c45fb7a0d6bffc5eab3ec327cf7324 \
    --hash=sha256:a6b4ff33f7e011bbaa148238d131c4fd4f8afbab3c104ddfbdb2b12b74ff7016 \
    --hash=sha256:a93ee7c6e8fd0f8a83525a51bd777be57ee17787e91d805bd8d6faf9dcada18e \
    --hash=sha256:b374e79ffa7511afc11773aef40a4ccea6191fba1c856ea2f9c56738dca69d7a \
    --hash=sha256:b7d501d5eb5d4f67207df364752ad697465b834268744be7581c18d81d35d41d \
    --hash=sha256:c59acfa8eb73a1e0d484392dc002bdf001fd4ce73394e0132df3d1ab6093d7cb \
    --hash=sha256:c75116c9de79949de23006e2d9b35ee82874c594fcf5c0311b439acaa14b8441 \
    --hash=sha256:ca80a49b53ed1d22f7282da7255f7bb2fd1935fd0f623d8613fda38745f18961 \
    --hash=sha256:cad5782f93f7f738b62c6527b6f32a60694d924029f299a8b524758cfa53d815 \
    --hash=sha256:ccadce0130fd813ec86ebfe969a6c58b42acc1d0fe55a47525375b740e07b605 \
    --hash=sha256:d701eab36200c36224833d07dbdb709adb7fd4253429548ddb5e547b8ed40586 \
    --hash=sha256:dad3d233d441a022c1f7155f0fb9d5aff7b97c1ea8c7dfa02cce586b16ab2d0b \
    --hash=sha256:dd0b83bed3405b586a3133629f1d1a5bc7bfd64822a3b7ab342bdc68e6dbc61b \
    --hash=sha256:de3de000d459402cda015068fd135aa50c0bf6f2477a80d4da1e646f123b4e78 \
    --hash=sha256:de9923832f2d8c1a5ecd8d7260465a6ca5a86888a0d129e3bd5cf0406d2fc5bf \
    --hash=sha256:df19e2d0b1620039af5102563fbd96e8938c7f5c3f5828528d641d9fc585525e \
    --hash=sha256:e85880b538e59a59f55117b81f208a6660ad5ac328aad9305f812d9b8bc67a0f \
    --hash=sha256:ee7d9da3bf493909cf811a3f038840cb34fab5ae2956b8a263919f6e289ab188 \
    --hash=sha256:eed88b64a5e5da72d6a71cdc5aaeefaa5ced9b748f8d19f89800b339961dad39 \
    --hash=sha256:f0ba7c2a329d650628f4c8572fd1db29f0a59dd70a3e3e0710dcf18a35cce9d8 \
    --hash=sha256:f8e63209c3e1e828ee6a457529b4a6d8b05d050fe0ae03a7ae49e967c5d312e0 \
    --hash=sha256:f8f0bd690e1a41294ac87905e8121c81a3761ec2583c768f13467428606c8c7a \
    --hash=sha256:f96f0e30b5a95c7631b12bfe214cbc90ec8fe8cfa36920596c10514a65743519 \
    --hash=sha256:f98e8215e172f567ce80eeaed9107fb4d32b6c44f26983d9b8334658136a205a \
    --hash=sha256:f9fe868463ec7e1363733af77e38a5fda3e9b63940337048c945d69e0c80ff24 \
    --hash=sha256:fdacf26402389bdd89857ad3c045a26fe8f3314f9a8b28226f82f88463a65b77 \
    --hash=sha256:fe3170a69fe039b18ad18171e66faa9a75f6fe9d78f968fd9b54e09fbd714d81 \
    --hash=sha256:fea4427d1ffdb3b523d7daa6712038428a4c16c450b9777bdd1221cfee0eab49
    # via sqlalchemy
jmespath==1.1.0 \
    --hash=sha256:472c87d80f36026ae83c6ddd0f1d05d4e510134ed462851fd5f754c8c3cbb88d \
    --hash=sha256:a5663118de4908c91729bea0acadca56526eb2698e83de10cd116ae0f4e97c64
    # via
    #   boto3
    #   botocore
mako==1.4.1 \
    --hash=sha256:a359d9a94a541213958742b2698d0a7757bb83551767bc468a74b9905aba9617 \
    --hash=sha256:d7904710b662996425a21627710c4777c45053146942cf8a7aebf757c92b8c27
    # via alembic
markupsafe==3.0.3 \
    --hash=sha256:0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f \
    --hash=sha256:068f375c472b3e7acbe2d5318dea141359e6900156b5b2ba06a30b169086b91a \
    --hash=sha256:0bf2a864d67e76e5c9a34dc26ec616a66b9888e25e7b9460e1c76d3293bd9dbf \
    --hash=sha256:0db14f5dafddbb6d9208827849fad01f1a2609380add406671a26386cdf15a19 \
    --hash=sha256:0eb9ff8191e8498cca014656ae6b8d61f39da5f95b488805da4bb029cccbfbaf \
    --hash=sha256:0f4b68347f8c5eab4a13419215bdfd7f8c9b19f2b25520968adfad23eb0ce60c \
    --hash=sha256:1085e7fbddd3be5f89cc898938f42c0b3c711fdcb37d75221de2666af647c175 \
    --hash=sha256:116bb52f642a37c115f517494ea5feb03889e04df47eeff5b130b1808ce7c219 \
    --hash=sha256:12c63dfb4a98206f045aa9563db46507995f7ef6d83b2f68eda65c307c6829eb \
    --hash=sha256:133a43e73a802c5562be9bbcd03d090aa5a1fe899db609c29e8c8d815c5f6de6 \
    --hash=sha256:1353ef0c1b138e1907ae78e2f6c63ff67501122006b0f9abad68fda5f4ffc6ab \
    --hash=sha256:15d939a21d546304880945ca1ecb8a039db6b4dc49b2c5a400387cdae6a62e26 \
    --hash=sha256:177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1 \
    --hash=sha256:1872df69a4de6aead3491198eaf13810b565bdbeec3ae2dc8780f14458ec73ce \
    --hash=sha256:1b4b79e8ebf6b55351f0d91fe80f893b4743f104bff22e90697db1590e47a218 \
    --hash=sha256:1b52b4fb9df4eb9ae465f8d0c228a00624de2334f216f178a995ccdcf82c4634 \
    --hash=sha256:1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695 \
    --hash=sha256:1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad \
    --hash=sha256:218551f6df4868a8d527e3062d0fb968682fe92054e89978594c28e642c43a73 \
    --hash=sha256:26a5784ded40c9e318cfc2bdb30fe164bdb8665ded9cd64d500a34fb42067b1c \
    --hash=sha256:2713baf880df847f2bece4230d4d094280f4e67b1e813eec43b4c0e144a34ffe \
    --hash=sha256:2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa \
    --hash=sha256:2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559 \
    --hash=sha256:32001d6a8fc98c8cb5c947787c5d08b0a50663d139f1305bac5885d98d9b40fa \
    --hash=sha256:3524b778fe5cfb3452a09d31e7b5adefeea8c5be1d43c4f810ba09f2ceb29d37 \
    --hash=sha256:3537e01efc9d4dccdf77221fb1cb3b8e1a38d5428920e0657ce299b20324d758 \
    --hash=sha256:35add3b638a5d900e807944a078b51922212fb3dedb01633a8defc4b01a3c85f \
    --hash=sha256:38664109c14ffc9e7437e86b4dceb442b0096dfe3541d7864d9cbe1da4cf36c8 \
    --hash=sha256:3a7e8ae81ae39e62a41ec302f972ba6ae23a5c5396c8e60113e9066ef893da0d \
    --hash=sha256:3b562dd9e9ea93f13d53989d23a7e775fdfd1066c33494ff43f5418bc8c58a5c \
    --hash=sha256:457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97 \
    --hash=sha256:4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a \
    --hash=sha256:4e885a3d1efa2eadc93c894a21770e4bc67899e3543680313b09f139e149ab19 \
    --hash=sha256:4faffd047e07c38848ce017e8725090413cd80cbc23d86e55c587bf979e579c9 \
    --hash=sha256:509fa21c6deb7a7a273d629cf5ec029bc209d1a51178615ddf718f5918992ab9 \
    --hash=sha256:5678211cb9333a6468fb8d8be0305520aa073f50d17f089b5b4b477ea6e67fdc \
    --hash=sha256:591ae9f2a647529ca990bc681daebdd52c8791ff06c2bfa05b65163e28102ef2 \
    --hash=sha256:5a7d5dc5140555cf21a6fefbdbf8723f06fcd2f63ef108f2854de715e4422cb4 \
    --hash=sha256:69c0b73548bc525c8cb9a251cddf1931d1db4d2258e9599c28c07ef3580ef354 \
    --hash=sha256:6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50 \
    --hash=sha256:722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698 \
    --hash=sha256:729586769a26dbceff69f7a7dbbf59ab6572b99d94576a5592625d5b411576b9 \
    --hash=sha256:77f0643abe7495da77fb436f50f8dab76dbc6e5fd25d39589a0f1fe6548bfa2b \
    --hash=sha256:795e7751525cae078558e679d646ae45574b47ed6e7771863fcc079a6171a0fc \
    --hash=sha256:7be7b61bb172e1ed687f1754f8e7484f1c8019780f6f6b0786e76bb01c2ae115 \
    --hash=sha256:7c3fb7d25180895632e5d3148dbdc29ea38ccb7fd210aa27acbd1201a1902c6e \
    --hash=sha256:7e68f88e5b8799aa49c85cd116c932a1ac15caaa3f5db09087854d218359e485 \
    --hash=sha256:83891d0e9fb81a825d9a6d61e3f07550ca70a076484292a70fde82c4b807286f \
    --hash=sha256:8485f406a96febb5140bfeca44a73e3ce5116b2501ac54fe953e488fb1d03b12 \
    --hash=sha256:8709b08f4a89aa7586de0aadc8da56180242ee0ada3999749b183aa23df95025 \
    --hash=sha256:8f71bc33915be5186016f675cd83a1e08523649b0e33efdb898db577ef5bb009 \
    --hash=sha256:915c04ba3851909ce68ccc2b8e2cd691618c4dc4c4232fb7982bca3f41fd8c3d \
    --hash=sha256:949b8d66bc381ee8b007cd945914c721d9aba8e27f71959d750a46f7c282b20b \
    --hash=sha256:94c6f0bb423f739146aec64595853541634bde58b2135f27f61c1ffd1cd4d16a \
    --hash=sha256:9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5 \
    --hash=sha256:9b79b7a16f7fedff2495d684f2b59b0457c3b493778c9eed31111be64d58279f \
    --hash=sha256:a320721ab5a1aba0a233739394eb907f8c8da5c98c9181d1161e77a0c8e36f2d \
    --hash=sha256:a4afe79fb3de0b7097d81da19090f4df4f8d3a2b3adaa8764138aac2e44f3af1 \
    --hash=sha256:ad2cf8aa28b8c020ab2fc8287b0f823d0a7d8630784c31e9ee5edea20f406287 \
    --hash=sha256:b8512a91625c9b3da6f127803b166b629725e68af71f8184ae7e7d54686a56d6 \
    --hash=sha256:bc51efed119bc9cfdf792cdeaa4d67e8f6fcccab66ed4bfdd6bde3e59bfcbb2f \
    --hash=sha256:bdc919ead48f234740ad807933cdf545180bfbe9342c2bb451556db2ed958581 \
    --hash=sha256:bdd37121970bfd8be76c5fb069c7751683bdf373db1ed6c010162b2a130248ed \
    --hash=sha256:be8813b57049a7dc738189df53d69395eba14fb99345e0a5994914a3864c8a4b \
    --hash=sha256:c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c \
    --hash=sha256:c47a551199eb8eb2121d4f0f15ae0f923d31350ab9280078d1e5f12b249e0026 \
    --hash=sha256:c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8 \
    --hash=sha256:ccfcd093f13f0f0b7fdd0f198b90053bf7b2f02a3927a30e63f3ccc9df56b676 \
    --hash=sha256:d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6 \
    --hash=sha256:d53197da72cc091b024dd97249dfc7794d6a56530370992a5e1a08983ad9230e \
    --hash=sha256:d6dd0be5b5b189d31db7cda48b91d7e0a9795f31430b7f271219ab30f1d3ac9d \
    --hash=sha256:d88b440e37a16e651bda4c7c2b930eb586fd15ca7406cb39e211fcff3bf3017d \
    --hash=sha256:de8a88e63464af587c950061a5e6a67d3632e36df62b986892331d4620a35c01 \
    --hash=sha256:df2449253ef108a379b8b5d6b43f4b1a8e81a061d6537becd5582fba5f9196d7 \
    --hash=sha256:e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419 \
    --hash=sha256:e1cf1972137e83c5d4c136c43ced9ac51d0e124706ee1c8aa8532c1287fa8795 \
    --hash=sha256:e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1 \
    --hash=sha256:e56b7d45a839a697b5eb268c82a71bd8c7f6c94d6fd50c3d577fa39a9f1409f5 \
    --hash=sha256:e8afc3f2ccfa24215f8cb28dcf43f0113ac3c37c2f0f0806d8c70e4228c5cf4d \
    --hash=sha256:e8fc20152abba6b83724d7ff268c249fa196d8259ff481f3b1476383f8f24e42 \
    --hash=sha256:eaa9599de571d72e2daf60164784109f19978b327a3910d3e9de8c97b5b70cfe \
    --hash=sha256:ec15a59cf5af7be74194f7ab02d0f59a62bdcf1a537677ce67a2537c9b87fcda \
    --hash=sha256:f190daf01f13c72eac4efd5c430a8de82489d9cff23c364c3ea822545032993e \
    --hash=sha256:f34c41761022dd093b4b6896d4810782ffbabe30f2d443ff5f083e0cbbb8c737 \
    --hash=sha256:f3e98bb3798ead92273dc0e5fd0f31ade220f59a266ffd8a4f6065e0a3ce0523 \
    --hash=sha256:f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591 \
    --hash=sha256:f71a396b3bf33ecaa1626c255855702aca4d3d9fea5e051b41ac59a9c1c41edc \
    --hash=sha256:f9e130248f4462aaa8e2552d547f36ddadbeaa573879158d721bbd33dfe4743a \
    --hash=sha256:fed51ac40f757d41b7c48425901843666a6677e3e8eb0abcff09e4ba6e664f50
    # via mako
psycopg==3.3.4 \
    --hash=sha256:b6bbc25ccf05c8fad3b061d9db2ef0909a555171b84b07f29458a447253d679a \
    --hash=sha256:e21207764952cff81b6b8bdacad9a3939f2793367fdac2987b3aac36a651b5bc
    # via -r infra/bootstrap/requirements.in
psycopg-binary==3.3.4 \
    --hash=sha256:018fbed325936da502feb546642c982dcc4b9ffdea32dfef78dbf3b7f7ad4070 \
    --hash=sha256:0579252a1202cd73e4da137a1426e2dae993ae44e757605344282af3a082848c \
    --hash=sha256:136f199a407b5348b9b857c504aff60c77622a28482e7195839ce1b51238c4cc \
    --hash=sha256:13a7f380824c35896dcac7fe0f61440f7ca49d6dc73f3c13a9a4471e6a3b302e \
    --hash=sha256:17a21953a9e5ff3a16dab692625a3676e2f101db5e40072f39dbee2250194d68 \
    --hash=sha256:1dc1f79fd16bb1f3f4421417a514607539f17804d95c7ed617265369d1981cae \
    --hash=sha256:1fbaa292a3c8bb61b45df1ad3da1908ccee7cb889db9425e3557d9e34e2a4829 \
    --hash=sha256:22cdbf5f91ef7bb91fe0c5757e1962d3127a8010256eefd9c61fcaf441802097 \
    --hash=sha256:26df2717e59c0473e4465a97dfb1b7afebaa479277870fd5784d1436470db47c \
    --hash=sha256:276904e3452d6a23d474ef9a21eee19f20eed3d53ddd2576af033827e0ba0992 \
    --hash=sha256:28b7398fdd19db3232c884fb24550bdfe951221f510e195e233299e4c9b78f97 \
    --hash=sha256:2c09aad7051326e7603c14e50636db9c01f78272dc54b3accff03d46370461e6 \
    --hash=sha256:32a6fbf8481e3a370d0d72b860d35948a693cb01281da217f7b2f307636e591a \
    --hash=sha256:41f2ec0fea529832982bcb6c9415de3c86264ebe562b77a467c0fbcd7efbba8d \
    --hash=sha256:46893c26858be12cc49ca4226ed6a60b4bfccadd946b3bebb783a60b38788228 \
    --hash=sha256:47c656a8a7ba6eb0cff1801a4caaa9c8bdc12d03080e273aff1c8ac39971a77e \
    --hash=sha256:494ca54901be8cf9eb7e02c25b731f2317c378efa44f43e8f9bd0e1184ae7be4 \
    --hash=sha256:514404ed543efd620c85602b747df2a23cf1241b4067199e1a66f2d2757aaa41 \
    --hash=sha256:574ea21a9651958f1535c5a1c649c7409e9168bcbffa29a3f2f961f58b322949 \
    --hash=sha256:580ae30a5f95ccd90008ec697d3ed6a4a2047a516407ad904283fa42086936e9 \
    --hash=sha256:5ab28a2a7649df3b72e6b674b4c190e448e8e77cf496a65bd846472048de2089 \
    --hash=sha256:5c4ab71be17bdca30cb34c34c4e1496e2f5d6f20c199c12bad226070b22ef9bf \
    --hash=sha256:612a627d733f695b1de1f9b4bd511c15f999a5d8b915d444bbd7dd71cf3370da \
    --hash=sha256:6402a9d8146cf4b3974ded3fd28a971e83dc6a0333eb7822524a3aa20b546578 \
    --hash=sha256:6b9016b1714da4dd5ecaaa75b82098aa5a0b87854ce9b092e21c27c4ae23e014 \
    --hash=sha256:71e55ccbdfae79a2ed9c6369c3008a3025817ff9d7e27b32a2d84e2a4267e66e \
    --hash=sha256:7465bfe6087d2d5b42d4c53b9b11ca9f218e477317a4a162a10e3c19e984ba8e \
    --hash=sha256:75a9067e236f9b9ae3535b66fe99bddb33d39c0de10112e49b9ab11eee53dc31 \
    --hash=sha256:773d573e11f437ce0bdb95b7c18dc58390494f96d43f8b45b9760436114f7652 \
    --hash=sha256:77df19583501ea288eaf15ac0fe7ad01e6d8091a91d5c41df5c718f307d8e31b \
    --hash=sha256:7f7668f30b9dd5163197e5cbf4e0efd54e00f0a859cc566ce56cfc31f4054839 \
    --hash=sha256:8c0056529e68dbe9184cd4019a1f3d8f3a4ead2f6fc7a5afcf27d3314edd1277 \
    --hash=sha256:94596f9e7633ee3f6440711d43bb70aa31cc0a46a900ab8b4201a366ace5c9e7 \
    --hash=sha256:ab8cca8ef8fb1ccf5b048ae5bd78ba55b9e4b5d472e3ce5ca39ff4d2a9c249e4 \
    --hash=sha256:ad3bc94054876155549fdaedf4a46d1ec69d39a5bcee377148afe498e84c4b8e \
    --hash=sha256:b56b603ebcea8aa10b46228b8410ba7f13e7c2ee54389d4d9be0927fd8ce2a70 \
    --hash=sha256:b6f5a29e9c775b9f12a1a717aa7a2c80f9e1db6f27ba44a5b59c80ac61d2ffcf \
    --hash=sha256:b7bfff1ca23732b488cbca3076fc11bc98d520ee122514fdb17a8e20d3338f5a \
    --hash=sha256:bdef84570ebbce1d42b4e7ea952d21c414c5f118ad02fee00c5625f35e134429 \
    --hash=sha256:c37e024c07308cd06cf3ec51bfd0e7f6157585a4d84d1bce4a7f5f7913719bf8 \
    --hash=sha256:c677c4ad433cb7150c8cd304a0769ae3bcfbe5ea0676eb53faa7b1443b16d0d3 \
    --hash=sha256:cf7f73a4a792bc5db58a4b385d8a1467e8d468f7548702fb0ed1e9b7501b1c13 \
    --hash=sha256:cffc3408d77a27973f33e5d909b624cce683db5fc25964b02fe0aae7886c1007 \
    --hash=sha256:d7b4d40c153fa352ab3cca530f3a0baedf7621b2ebcbd7f084009522c21788fc \
    --hash=sha256:dbfdb9b6cc79f31104a7b162a2b921b765fcc62af6c00540a167a8de47e4ed38 \
    --hash=sha256:df1d567fc430f6df15c9fcf67d87685fc49bdb325adc0db5af1adfb2f44eb5c9 \
    --hash=sha256:e2631da29253a98bd496e6c4813b24e09a4fe3fb2a9e88513305d6f8747cce95 \
    --hash=sha256:e7510c37550f91a187e3660a8cc50d4b760f8c3b8b2f89ebc5698cd2c7f2c85d \
    --hash=sha256:eb05ee1c2b817d27c537333224c9e83c7afb86fe7296ba970990068baf819b16 \
    --hash=sha256:eb4eed2079c01a4850bf467deacfab56d356d4225040170af03dc9958321242d \
    --hash=sha256:ee17a2cf4943cde261adfad1bbc5bf38d6b3776d7afff74c7cabcbeaeb08c260 \
    --hash=sha256:f80e3f2b5331dbbf0901bcb658056c03eeb2c1ef31d774afb0d61598b242e744 \
    --hash=sha256:f9b1c2533af01cd7648378599f82b0b8ae32f293296e6eec5753a625bc97ef28 \
    --hash=sha256:fa1cbc10768a796c96d3243656016bf4e337c81c71097270bb7b0ad6210d9765 \
    --hash=sha256:fbd1d4ed566895ad2d3bf4ddfd8bae90026930ddf29df3b9d91d32c8c47866a7
    # via psycopg
python-dateutil==2.9.0.post0 \
    --hash=sha256:37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3 \
    --hash=sha256:a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427
    # via botocore
s3transfer==0.19.2 \
    --hash=sha256:ba0309fd86be3c27dbf78cdd813c13c5e1df16e5874b99d2535ebbdfb9892993 \
    --hash=sha256:d8168eccca828cbb2cd573675333f3bddd254313a9c42494b84c76b539e8ba25
    # via boto3
six==1.17.0 \
    --hash=sha256:4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274 \
    --hash=sha256:ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81
    # via python-dateutil
sqlalchemy==2.0.54 \
    --hash=sha256:03cbf8d9a67da618bd65500a5eb3ddac89caf4c61e99b2f03fa4a1952a0725a9 \
    --hash=sha256:0e7a76d5dce712ce50435d0f97181eb955ec27d138c004176f01282e063bac52 \
    --hash=sha256:1019abef05a4b5eafc8eae6fb483167fa28a4dbe5f518d577b744f31a5276a37 \
    --hash=sha256:18a8b6417cbb7b735cf91c2b59453c2a554cefa0a8d7bd15aa35740739410d77 \
    --hash=sha256:1d887fbd5d248e250807bd801e697fc73e3b44866ce5f093dbc90512e75bde25 \
    --hash=sha256:24ae093dec196ba37fc2beb0316de53e7871d3d246a50faecbbb53034e41ded2 \
    --hash=sha256:264460333ed0b177cbb1956355d0ee4e0cab83fb415c934ce12a25db2e7be39c \
    --hash=sha256:279bde5bfedb0f3e0f1bdbcffa2daa39c6c54d90f9408ef3b1802001597199f0 \
    --hash=sha256:2f61a70b3b82e2ec7ad6a4f2301422b9ca93ff06917983e41317bcae878bddf6 \
    --hash=sha256:31d5458672a6f72db2c087f4a5098b3c8503ea0254186ff29205d63afa9401a4 \
    --hash=sha256:32de6deded25e8b9b11d07428d496ff24dfbc882b8e990c177266948cb5f3d9e \
    --hash=sha256:330d35f9ce815d35cb1daab038d4d7ec0e907f4d7ed0fc8bcb2411d1f23d0b50 \
    --hash=sha256:34e10af7d274a5c4b7cd0fced5e7361008c5e07d97dd48a93852d5b2f1142a1c \
    --hash=sha256:3de32cc6721eb42c3aad35bcfb244bb7a18f66c00f3582aae6281d6287a339b5 \
    --hash=sha256:415239eb2ddbbc508ba4cac97affb91c0f210548fd1731edda6e529b0bb93015 \
    --hash=sha256:48611087a75d26d798003645c688c7d3cfc26b89dbe4a2c568d6b378d330deae \
    --hash=sha256:4e55a0b96a1577a1e108c91ccdeeb9cd92768f28ce206597311c3bf6d6423abd \
    --hash=sha256:4e8a4afcc7d714cc3c8a57facdff4c3529f5f93d71e54b7da1e03e022c9089c9 \
    --hash=sha256:5417322b3c025dd82918725d3bf09ec105fac95efc195722b8b06e1d9c381139 \
    --hash=sha256:5800ddea045c2c860ef1d359a07a3066c7c0c426f45e3abc3874e116cb3c6937 \
    --hash=sha256:63cae7210fea9899e0bf35c1f1ae55d3ddd9c6d47cae8b6b43d945afa79dd65b \
    --hash=sha256:68d994e9b0d0423a02a20039631fa6fcbb7fa829a992f7605025774940305d19 \
    --hash=sha256:69cab115c40fd02c5a22c68e4ee630fa6ef9a1650f1de944419aab1f7096fc4f \
    --hash=sha256:6b6d4e601c4f6d85e99bb3416107cc9418c5603ca73d4ee0f5f8d79c2a1ed9e8 \
    --hash=sha256:6f84099e4b04a5c2d44500a2a8302eee5af4bc6fee63e8c6e9cf6786e747280e \
    --hash=sha256:7108f410f596c5ac22fe43ba467e864d27c4e1477ae89e90c6c87120b2c1be23 \
    --hash=sha256:744fb219a390561a57dbbd59cd69a22b5b5b2facfde794c1f79236dd847fa67a \
    --hash=sha256:762cfe4d340c56368256d936a98b620a9a5650e49c1c84eba51d6edd17ffefb2 \
    --hash=sha256:7b973e4facc2f80e42f5a27b841feb7e202661881a6320580abbe597a28a007f \
    --hash=sha256:7d03084f3352dd92048cb19c71d90f116d076c9c7937e0ebc7752c4685de6d38 \
    --hash=sha256:7e33a631ab1474f8fe6b910bd1a07b7b8009c4c78cdd3fb18001b03e3bc2e1d2 \
    --hash=sha256:842540e4382472f23c79589995752648d14696a8200d0807ed8c5c59c92ade44 \
    --hash=sha256:87ba8834318b0d8dc94fc6f405d071b5c08be32a6c3fd68107fd6952ee949615 \
    --hash=sha256:92622fbbda1b1fe1632f3402a6e516a93c0e41d9158839c6b3dfb12117f26b72 \
    --hash=sha256:a0956dc754d3884da7fe60097110ec7a8a105d26afa2f0844468f4b1598c6912 \
    --hash=sha256:abd6b21bc58e91c1932eb5d6d7f1bd44a551dfec7b6a7f517c3638ccd67233a0 \
    --hash=sha256:b374e3bc91e246a942592a98ba6a23be76fff21358b00546ac8c0ebc0fd0e00b \
    --hash=sha256:b67749f7da3985a529cefbb1474783cb91ef44371cb9713630bade3de908760d \
    --hash=sha256:b67c1744e453af833667fc1b84de07adb4a64f3536ef52a8ec5ac2b941d43970 \
    --hash=sha256:b6c419c83a87fd901f0b1b5338ffcb82471c3ac32a86bb8883688c18f8eb85d3 \
    --hash=sha256:b9086b8ad48280ef6a7ba68262d5e44f7db1c4cb1973e8cdae8a9f467ae66f51 \
    --hash=sha256:baa8521e8ee9f24e75dfc7aaabc08020e551ef0d48d7c3e3536f5cddf277586b \
    --hash=sha256:c1a3455a88f66e4851792bedb098ed942912253d31caed1dbc58afbfa9e875cd \
    --hash=sha256:ca05f4e7852cf48083b0cf157e4f9504b7068780422a50fa82f45353b8c5e14a \
    --hash=sha256:cad78d04254967bdbcccbed5e631d88fe4868530946ab0929aa45e9032849518 \
    --hash=sha256:cf89e92bf0d4204a6afcc17af27b9271ed9c7e34e17d6f80c085d431ea4a1747 \
    --hash=sha256:d31a2bc06a854ee52dd86b455be4df7c750b28817e2d1b884e31fff126c4fd7b \
    --hash=sha256:d566099d60cded87d175d4171dc899b9613d2e3b663573364565ca1b27ccd241 \
    --hash=sha256:d65f8ca742ef1e1e14bc417ef59dc2ddf207a7b66b30cfdc6152447314e030cf \
    --hash=sha256:d6adf80277372a89910a0f3ccfe960b846d279dc55b366dd5c5ec07f41c84758 \
    --hash=sha256:deeab253fe01a770f634c7007c73702df2324c868a79ae756507a9a1a76294fe \
    --hash=sha256:e08397c6c42f53b2488acde9108b8bfefd52d7afd1bf2f03d2ffcab7a204aceb \
    --hash=sha256:e1f455db400289f77ba2f7b62fffafe8875153812d0e3777aa4ff2b34a0fc1f7 \
    --hash=sha256:f3ea33bcf0aa599c1511fe5c9fb126f45aa450419084c4823f786155fe4c79f1 \
    --hash=sha256:f4e8f955d13af83fb4e35c3472e5377ee22d3445eada1e5e48199588edb69835 \
    --hash=sha256:f5c09090b1a7c4d389d1431f820931e8df318f82caafc53f9a72c872fef467c5 \
    --hash=sha256:f8cc6532f930c27974e9239e5ce5abebe7600ba9807cea4fcf42f1b6cab18fe7 \
    --hash=sha256:ffba7eb2d67c7505e82a0902aa854d8824b74c28a183820d6a8bd3cfd0f812c2
    # via alembic
typing-extensions==4.16.0 \
    --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8 \
    --hash=sha256:dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5
    # via
    #   alembic
    #   psycopg
    #   sqlalchemy
urllib3==2.8.0 \
    --hash=sha256:0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3 \
    --hash=sha256:63bf2ead4c879426ebf22ef2a781eeb4aa3b4ae798a0435506f8687fd5bb9b63
    # via botocore

```
### `infra/terraform/tests/package_c.tftest.hcl`

size=8979; sha256=571e2925d1a6f5d243c87f7c45746e82c9238bb0e4ebedec3dd238f9be0b290c; truncated=false

```text
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  mock_data "aws_route53_zone" {
    defaults = {
      zone_id      = "Z123456789"
      name         = "example.com."
      private_zone = false
    }
  }

  mock_resource "aws_db_instance" {
    defaults = {
      db_name = "paprnav"
      master_user_secret = [{
        secret_arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-test"
      }]
    }
  }

  mock_data "aws_acm_certificate" {
    defaults = {
      arn    = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
      domain = "pilot.example.com"
      status = "ISSUED"
      tags   = { Project = "paprnav" }
    }
  }
}

variables {
  pilot_hostname               = "pilot.example.com"
  pilot_certificate_arn        = "arn:aws:acm:us-east-1:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  route53_zone_id              = "Z123456789"
  route53_zone_name            = "example.com"
  budget_notification_email    = "pilot-owner@example.com"
  policy_updater_principal_arn = "arn:aws:iam::527257972989:role/paprnav-policy-updater"
  api_image                    = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  frontend_image               = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-frontend@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  bootstrap_image              = "527257972989.dkr.ecr.us-east-1.amazonaws.com/paprnav/pilot-bootstrap@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  first_admin_email            = "first-admin@example.com"
  first_admin_name             = "First Admin"
  first_admin_organization     = "Paprnav"
}

run "valid_gate_inputs" {
  command = plan

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }
}

run "valid_certificate_gate" {
  command = plan

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  assert {
    condition = (
      data.aws_acm_certificate.pilot.domain == var.pilot_hostname &&
      data.aws_acm_certificate.pilot.most_recent == false &&
      length(data.aws_acm_certificate.pilot.statuses) == 1 &&
      data.aws_acm_certificate.pilot.statuses[0] == "ISSUED" &&
      length(data.aws_acm_certificate.pilot.types) == 1 &&
      data.aws_acm_certificate.pilot.types[0] == "AMAZON_ISSUED" &&
      length(data.aws_acm_certificate.pilot.key_types) == 1 &&
      contains(data.aws_acm_certificate.pilot.key_types, "RSA_2048") &&
      length(data.aws_acm_certificate.pilot.tags) == 1 &&
      lookup(data.aws_acm_certificate.pilot.tags, "Project", "") == "paprnav"
    )
    error_message = "The ACM lookup must remain exact, issued, Amazon-issued, RSA_2048, Project-owned, and ambiguity rejecting."
  }
}

run "wrong_certificate_arn_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:527257972989:certificate/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_domain_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { domain = "unrelated.example.net" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_status_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { status = "PENDING_VALIDATION" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_tag_is_blocked" {
  command = plan

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { tags = { Project = "other" } }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_account_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-east-1:111111111111:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

run "wrong_certificate_region_is_blocked" {
  command = plan

  variables {
    pilot_certificate_arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555"
  }

  override_data {
    target = data.aws_acm_certificate.pilot
    values = { arn = "arn:aws:acm:us-west-2:527257972989:certificate/11111111-2222-3333-4444-555555555555" }
  }

  plan_options {
    target = [terraform_data.certificate_input_gate]
  }

  expect_failures = [terraform_data.certificate_input_gate]
}

# Export this plan with `terraform test -json -verbose` for the bounded Python
# request oracle in test_pilot_package_c.py. Only computed ARNs are mocked; the
# WAF statements, field selectors, transformations and regexes are real config.
run "waf_auth_and_upload_contract" {
  command = plan

  override_resource {
    target          = aws_wafv2_regex_pattern_set.login_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-login/11111111-1111-1111-1111-111111111111"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.invitation_paths
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-invitation/22222222-2222-2222-2222-222222222222"
    }
  }
  override_resource {
    target          = aws_wafv2_regex_pattern_set.upload_path
    override_during = plan
    values = {
      arn = "arn:aws:wafv2:us-east-1:527257972989:regional/regexpatternset/paprnav-upload/33333333-3333-3333-3333-333333333333"
    }
  }

  plan_options {
    target = [aws_wafv2_web_acl.pilot]
  }

  assert {
    condition = length([
      for rule in aws_wafv2_web_acl.pilot.rule : rule
      if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
      ]) == 2 && alltrue(flatten([
        for rule in aws_wafv2_web_acl.pilot.rule : [
          for predicate in one(one(rule.statement).rate_based_statement).scope_down_statement[0].and_statement[0].statement : (
            length(predicate.byte_match_statement) == 1 ? (
              one(predicate.byte_match_statement).search_string == "POST" &&
              one(predicate.byte_match_statement).positional_constraint == "EXACTLY" &&
              length(one(predicate.byte_match_statement).field_to_match[0].method) == 1 &&
              one(one(predicate.byte_match_statement).text_transformation).type == "NONE"
              ) : (
              length(one(predicate.regex_pattern_set_reference_statement).field_to_match[0].uri_path) == 1 &&
              one(one(predicate.regex_pattern_set_reference_statement).text_transformation).type == "URL_DECODE"
            )
          )
        ] if contains(["login-rate-limit", "invitation-rate-limit"], rule.name)
    ]))
    error_message = "Both auth rules must match raw POST methods and URL_DECODE the URI predicate itself."
  }

  assert {
    condition = alltrue(concat(
      [for visibility in aws_wafv2_web_acl.pilot.visibility_config : !visibility.sampled_requests_enabled],
      flatten([for rule in aws_wafv2_web_acl.pilot.rule : [
        for visibility in rule.visibility_config : !visibility.sampled_requests_enabled
      ]])
    ))
    error_message = "No WAF sampling may retain session-bearing requests."
  }
}

run "wrong_api_repository_is_blocked" {
  command = plan

  variables {
    api_image = "527257972989.dkr.ecr.us-east-1.amazonaws.com/unrelated/api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "wrong_hosted_zone_identity_is_blocked" {
  command = plan

  variables {
    route53_zone_name = "unrelated.example.net"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

run "placeholder_external_input_is_blocked" {
  command = plan

  variables {
    external_mode             = true
    budget_notification_email = "owner@example.invalid"
  }

  plan_options {
    target = [terraform_data.deployment_input_gate]
  }

  expect_failures = [terraform_data.deployment_input_gate]
}

```
### `scripts/build_pilot_release_context.py`

size=13259; sha256=7625442d2f4c4bf856c1daa5d91e948ba40b669e29a69c5f1e43f8dccb381b7d; truncated=false

```text
#!/usr/bin/env python3
"""Build deterministic API, frontend, or sealed bootstrap contexts from Git."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = REPO_ROOT / ".ai/pilot-package-c-context-v1.json"
BOUNDARY_POLICY = REPO_ROOT / ".ai/pilot-release-boundary-v1.json"
MANIFEST_NAME = "release-context.json"


class ContextError(RuntimeError):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True)
    if check and result.returncode:
        raise ContextError(result.stderr.decode(errors="replace").strip() or "git command failed")
    return result


def resolve_commit(ref: str) -> str:
    if not ref or ref.startswith("-"):
        raise ContextError("release ref must be an explicit non-option Git ref")
    return git("rev-parse", "--verify", f"{ref}^{{commit}}").stdout.decode("ascii").strip()


def tree_entries(commit: str) -> dict[str, tuple[str, str]]:
    raw = git("ls-tree", "-rz", "--full-tree", commit).stdout
    result: dict[str, tuple[str, str]] = {}
    for record in raw.rstrip(b"\0").split(b"\0") if raw else []:
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8", "strict")
        if path in result or kind != "blob":
            raise ContextError("release tree contains duplicate or unsupported entries")
        result[path] = (mode, object_id)
    return result


def dirty_paths() -> set[str]:
    raw = git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    records = raw.rstrip(b"\0").split(b"\0") if raw else []
    result: set[str] = set()
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 4:
            raise ContextError("unparseable Git status record")
        status_code = record[:2].decode("ascii")
        result.add(record[3:].decode("utf-8", "strict"))
        if "R" in status_code or "C" in status_code:
            index += 1
            if index >= len(records):
                raise ContextError("unparseable Git rename/copy record")
            result.add(records[index].decode("utf-8", "strict"))
        index += 1
    return result


def validate_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if not path or path.startswith("/") or ".." in parsed.parts or str(parsed) != path:
        raise ContextError("unsafe context path")


def is_forbidden(path: str, policy: dict[str, Any]) -> bool:
    return path in policy["forbiddenPaths"] or any(
        path.startswith(prefix) for prefix in policy["forbiddenPrefixes"]
    ) or "20260916_0030" in path


def candidate_authority(commit: str) -> dict[str, Any]:
    """Apply Package A's one canonical candidate/protected-blob gate."""

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import verify_pilot_release_boundary as boundary

    boundary_policy = json.loads(
        BOUNDARY_POLICY.read_text(encoding="utf-8"),
        object_pairs_hook=boundary.unique_json_object,
    )
    result = boundary.verify_release(REPO_ROOT, commit, boundary_policy)
    if result["status"] != "pass":
        raise ContextError("Package A candidate authority failed: " + "; ".join(result["errors"]))
    return boundary_policy


def overlay_files(
    path: Path | None,
    commit: str,
    policy: dict[str, Any],
    boundary_policy: dict[str, Any],
) -> tuple[dict[str, bytes], list[str]]:
    dirty = dirty_paths()
    if path is None:
        if dirty:
            raise ContextError("working tree is dirty and no reviewed overlay manifest was supplied")
        return {}, []
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if set(manifest) != {"version", "sourceCommit", "reviewedInputs", "preservedExclusions"}:
        raise ContextError("overlay manifest has an unexpected schema")
    if manifest.get("version") != "paprnav-reviewed-overlay-v2" or manifest.get("sourceCommit") != commit:
        raise ContextError("overlay manifest version or source commit differs")
    entries = manifest.get("reviewedInputs")
    preserved = manifest.get("preservedExclusions")
    if not isinstance(entries, list) or not isinstance(preserved, list) or not (entries or preserved):
        raise ContextError("overlay manifest has no reviewed inputs or preserved exclusions")
    if not all(isinstance(item, str) for item in preserved) or len(preserved) != len(set(preserved)):
        raise ContextError("preserved exclusions must be unique paths")
    for source_path in preserved:
        validate_path(source_path)
    expected_paths: set[str] = set()
    result: dict[str, bytes] = {}
    protected_paths = set(boundary_policy.get("approvedMigrationAuthoritySha256", {})) | set(
        boundary_policy.get("protectedBlobSha256", {})
    )
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ContextError("overlay entry has an unexpected schema")
        source_path = entry["path"]
        if not isinstance(source_path, str) or not isinstance(entry["sha256"], str):
            raise ContextError("overlay entry path and sha256 must be strings")
        validate_path(source_path)
        if is_forbidden(source_path, policy):
            raise ContextError("overlay manifest contains a forbidden path")
        if source_path in protected_paths:
            raise ContextError("Package A protected authority may not be supplied by an overlay")
        if source_path in preserved:
            raise ContextError("a path cannot be both a reviewed input and a preserved exclusion")
        absolute = REPO_ROOT / source_path
        info = absolute.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ContextError("overlay path is not one ordinary file")
        content = absolute.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ContextError("overlay file hash differs")
        expected_paths.add(source_path)
        result[source_path] = content
    expected_paths.update(preserved)
    if dirty != expected_paths:
        raise ContextError("dirty working-tree inventory differs from the reviewed overlay manifest")
    return result, sorted(preserved)


def git_blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}").stdout


def selected_sources(
    context_name: str,
    commit: str,
    policy: dict[str, Any],
    overlays: dict[str, bytes],
) -> dict[str, bytes]:
    config = policy["contexts"][context_name]
    prefix = config["sourcePrefix"]
    entries = tree_entries(commit)
    candidate_paths = set(entries) | set(overlays)
    selected: dict[str, bytes] = {}
    for source_path in sorted(candidate_paths):
        if not source_path.startswith(prefix):
            continue
        if is_forbidden(source_path, policy):
            raise ContextError("release input contains a forbidden path")
        if any(source_path.startswith(item) for item in config["excludePrefixes"]):
            continue
        if PurePosixPath(source_path).name in config["excludeNames"]:
            continue
        if source_path in overlays:
            content = overlays[source_path]
        else:
            mode, _ = entries[source_path]
            if mode != "100644":
                raise ContextError("release input is not a regular non-executable file")
            content = git_blob(commit, source_path)
        destination = source_path[len(prefix):]
        validate_path(destination)
        selected[destination] = content
    missing = sorted(path for path in config["requiredPaths"] if path not in candidate_paths)
    if missing:
        raise ContextError(f"required release inputs are absent: {missing}")
    return selected


def add_sealed_migration(commit: str, files: dict[str, bytes]) -> str:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import build_pilot_migration_context as migration

    policy = json.loads(BOUNDARY_POLICY.read_text(encoding="utf-8"))
    manifest, migration_files = migration.context_spec(REPO_ROOT, commit, policy)
    for path, content in migration_files.items():
        files[f"migration/{path}"] = content
    return manifest["manifestSha256"]


def context_spec(
    context_name: str,
    ref: str,
    policy: dict[str, Any],
    overlay_manifest: Path | None,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    if context_name not in policy["contexts"]:
        raise ContextError("unknown release context")
    commit = resolve_commit(ref)
    boundary_policy = candidate_authority(commit)
    overlays, preserved_exclusions = overlay_files(
        overlay_manifest,
        commit,
        policy,
        boundary_policy,
    )
    selected = selected_sources(context_name, commit, policy, overlays)
    source_prefix = policy["contexts"][context_name]["sourcePrefix"]
    files = {f"bootstrap/{path}" if context_name == "bootstrap" else path: content
             for path, content in selected.items()}
    migration_digest = None
    if policy["contexts"][context_name].get("sealedMigrationContext"):
        migration_digest = add_sealed_migration(commit, files)
    entries = [
        {"path": path, "sizeBytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        for path, content in sorted(files.items())
    ]
    body = {
        "version": policy["version"],
        "context": context_name,
        "sourceCommit": commit,
        "sourcePrefix": source_prefix,
        "reviewedInputsSha256": hashlib.sha256(canonical([
            {"path": path, "sha256": hashlib.sha256(content).hexdigest()}
            for path, content in sorted(overlays.items())
        ])).hexdigest(),
        "preservedExclusions": preserved_exclusions,
        "migrationManifestSha256": migration_digest,
        "buildArgs": policy["contexts"][context_name]["buildArgs"],
        "platforms": policy["expectedPlatforms"],
        "files": entries,
    }
    manifest = {**body, "manifestSha256": hashlib.sha256(canonical(body)).hexdigest()}
    files[MANIFEST_NAME] = canonical(manifest)
    return manifest, files


def write_context(destination: Path, files: dict[str, bytes]) -> None:
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ContextError("destination must not exist")
    if destination.parent.resolve() != destination.parent.absolute():
        raise ContextError("destination parent may not traverse a symlink")
    destination.mkdir(mode=0o755)
    for relative, content in sorted(files.items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        target.write_bytes(content)
        target.chmod(0o444)


def verify_context(destination: Path, expected: dict[str, bytes]) -> None:
    actual: set[str] = set()
    for path in destination.rglob("*"):
        relative = path.relative_to(destination).as_posix()
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o444:
            raise ContextError("context contains a symlink, hard link, or mode drift")
        if relative not in expected or path.read_bytes() != expected[relative]:
            raise ContextError("context inventory or bytes differ")
        actual.add(relative)
    if actual != set(expected):
        raise ContextError("context is missing expected files")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--context", choices=("api", "frontend", "bootstrap"), required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--overlay-manifest", type=Path)
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        manifest, files = context_spec(args.context, args.ref, policy, args.overlay_manifest)
        if args.action == "build":
            write_context(args.destination, files)
        verify_context(args.destination, files)
    except (ContextError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({
        "status": "pass",
        "context": args.context,
        "sourceCommit": manifest["sourceCommit"],
        "manifestSha256": manifest["manifestSha256"],
        "fileCount": len(manifest["files"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `scripts/generate_pilot_deploy_policy.py`

size=7082; sha256=46710684fc691563c7b705f75c0136714d3610142ee21f384b5aaf71cc3cdd0e; truncated=false

```text
#!/usr/bin/env python3
"""Generate bounded pilot prerequisite IAM documents from explicit inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ACCOUNT = "527257972989"
REGION = "us-east-1"
DEPLOY_POLICY_ARN = f"arn:aws:iam::{ACCOUNT}:policy/paprnav-terraform-deploy"
ZONE_RE = re.compile(r"^Z[A-Z0-9]{8,32}$")
PRINCIPAL_RE = re.compile(rf"^arn:aws:iam::{ACCOUNT}:(?:user|role)/[^\s]+$")
KMS_RE = re.compile(rf"^arn:aws:kms:{REGION}:{ACCOUNT}:key/[0-9a-f-]+$")
HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$")


def statement(sid: str, actions: list[str], resource: str | list[str], condition: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"Sid": sid, "Effect": "Allow", "Action": actions, "Resource": resource}
    if condition:
        result["Condition"] = condition
    return result


def generate(zone_id: str, pilot_hostname: str, updater_principal: str, kms_key_arn: str) -> dict[str, Any]:
    if ZONE_RE.fullmatch(zone_id) is None:
        raise ValueError("invalid Route53 zone ID")
    if HOSTNAME_RE.fullmatch(pilot_hostname) is None:
        raise ValueError("pilot hostname must be one canonical lower-case DNS hostname")
    if PRINCIPAL_RE.fullmatch(updater_principal) is None:
        raise ValueError("updater principal must be an exact account IAM user or role ARN")
    if KMS_RE.fullmatch(kms_key_arn) is None:
        raise ValueError("Secrets Manager KMS key must be one exact account/region key ARN")
    service_roles = {
        "rds.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/rds.amazonaws.com/AWSServiceRoleForRDS",
        "ecs.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS",
        "elasticloadbalancing.amazonaws.com": f"arn:aws:iam::{ACCOUNT}:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing",
    }
    deploy_statements = [
        statement(
            "AcmListCertificates",
            ["acm:ListCertificates"],
            "*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "AcmReadCertificateMetadata",
            ["acm:DescribeCertificate", "acm:ListTagsForCertificate", "acm:GetCertificate"],
            f"arn:aws:acm:{REGION}:{ACCOUNT}:certificate/*",
            {"StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement("WafInventory", ["wafv2:ListWebACLs", "wafv2:ListRegexPatternSets", "wafv2:GetWebACLForResource"], "*"),
        statement(
            "WafCreateTaggedPilotResources",
            ["wafv2:CreateWebACL", "wafv2:CreateRegexPatternSet"],
            "*",
            {"StringEquals": {"aws:RequestTag/Project": "paprnav", "aws:RequestedRegion": REGION}},
        ),
        statement(
            "WafManagePilotResources",
            ["wafv2:GetWebACL", "wafv2:UpdateWebACL", "wafv2:DeleteWebACL", "wafv2:GetRegexPatternSet", "wafv2:UpdateRegexPatternSet", "wafv2:DeleteRegexPatternSet", "wafv2:TagResource", "wafv2:UntagResource"],
            [
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*",
                f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/regexpatternset/paprnav-*/*",
            ],
        ),
        statement(
            "WafAssociatePilotAlb",
            ["wafv2:AssociateWebACL", "wafv2:DisassociateWebACL"],
            [f"arn:aws:wafv2:{REGION}:{ACCOUNT}:regional/webacl/paprnav-*/*", f"arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/app/paprnav-*/*"],
        ),
        statement("Route53Inventory", ["route53:ListHostedZones", "route53:GetChange"], "*"),
        statement(
            "Route53ExactPilotZone",
            ["route53:GetHostedZone", "route53:ListResourceRecordSets", "route53:ChangeResourceRecordSets", "route53:ListTagsForResource"],
            f"arn:aws:route53:::hostedzone/{zone_id}",
        ),
        statement(
            "PilotSecretLifecycleWithoutValues",
            ["secretsmanager:CreateSecret", "secretsmanager:DescribeSecret", "secretsmanager:TagResource", "secretsmanager:UntagResource", "secretsmanager:DeleteSecret", "secretsmanager:RestoreSecret", "secretsmanager:PutResourcePolicy", "secretsmanager:GetResourcePolicy", "secretsmanager:DeleteResourcePolicy"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:/paprnav/pilot/*",
        ),
        statement(
            "RdsManagedSecretCreation",
            ["secretsmanager:CreateSecret"],
            "*",
            {"StringLike": {"secretsmanager:Name": "rds!db-*"}, "StringEquals": {"aws:RequestedRegion": REGION}},
        ),
        statement(
            "RdsManagedSecretTagging",
            ["secretsmanager:TagResource"],
            f"arn:aws:secretsmanager:{REGION}:{ACCOUNT}:secret:rds!db-*",
        ),
        statement("RdsManagedSecretKmsDescribe", ["kms:DescribeKey"], kms_key_arn),
    ]
    for index, (service_name, role_arn) in enumerate(service_roles.items(), start=1):
        deploy_statements.append(statement(
            f"CreateServiceLinkedRole{index}",
            ["iam:CreateServiceLinkedRole"],
            role_arn,
            {"StringEquals": {"iam:AWSServiceName": service_name}},
        ))
    operator = {
        "Version": "2012-10-17",
        "Statement": [statement(
            "VersionOnlyPaprnNavDeployPolicy",
            ["iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion"],
            DEPLOY_POLICY_ARN,
        )],
    }
    return {
        "version": "paprnav-pilot-generated-prerequisites-v1",
        "inputs": {"hostedZoneId": zone_id, "pilotHostname": pilot_hostname, "operatorUpdaterPrincipalArn": updater_principal, "secretsManagerKmsKeyArn": kms_key_arn},
        "deployPolicySupplement": {"Version": "2012-10-17", "Statement": deploy_statements},
        "operatorUpdaterProofPolicy": operator,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hosted-zone-id", required=True)
    parser.add_argument("--pilot-hostname", required=True)
    parser.add_argument("--operator-updater-principal-arn", required=True)
    parser.add_argument("--secrets-manager-kms-key-arn", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        generated = generate(
            args.hosted_zone_id,
            args.pilot_hostname,
            args.operator_updater_principal_arn,
            args.secrets_manager_kms_key_arn,
        )
    except ValueError as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "output": str(args.output), "statementCount": len(generated["deployPolicySupplement"]["Statement"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
