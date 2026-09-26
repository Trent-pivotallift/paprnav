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
