# Decision packet: T082-AWS-INVITE-PILOT-E

## Objective

Execute the smallest reviewed AWS release that lets at most ten external pilot
users/aircraft generate useful product feedback, achievements, error evidence,
and recorded costs. Reach an initial **manual-workflow cohort** before paid OCR
activation; complete the parent OCR acceptance only after its separate gates.
This decision is a proposed execution contract, not authorization to mutate AWS
or an assertion that any execution gate has passed.

Authority: parent T082 decision and design remediation; Package A final
implementation PASS (`adversarial-implementation-package-a-remediation-3.md`),
Package B `adversarial-implementation-remediation-1.md`, Package C closure and
ACM amendment, and Package D/its privacy amendment final closure attestations.
A/B `closure.md` files are unfilled templates; do not cite them as closure
proof. Use their recorded findings/review attestations and have the coordinator
resolve any missing final release attestation before candidate approval.

The parent `delivery-objective-amendment.md` adopted 2026-09-19 governs this
execution package. It fixes the external-pilot deadline at 2026-10-19, limits
work in progress to this critical-path family, keeps unfinished V4 disabled,
and caps ordinary verification at one targeted suite/end-to-end path plus one
family-level review. Mandatory authorization, tenant, migration, provider,
spend, recovery, and release gates remain unchanged. The live delivery status
is maintained in the parent `delivery-scoreboard.md`.

## User-visible outcome

- Initial cohort: paste a short-lived invitation, sign in over the canonical
  HTTPS origin, create aircraft and manual logbook entries, upload/download
  consented source files, submit feedback, and inspect authorized activity.
  Uploaded jobs remain pending; OCR completion is not promised at this stage.
- Existing non-V4 AD views remain decision support. On a fresh database, absent
  source/coverage data must be displayed as absent/degraded/needs review. No AD
  ingestion or paid extraction is implied by inviting users.
- Operator: correlate sanitized errors with user reports, inspect real
  achievements/feedback and incomplete recorded OCR estimates, and retain
  dated AWS cost/budget evidence with its billing delay and scope stated.
- Later bounded OCR acceptance: one consented, explicitly selected upload
  completes real OCR, page review, and entry creation after provider, cost,
  durable-attempt, and worker gates. That success does not enable bulk OCR.

## Safety and correctness invariants

1. **Authority:** every external mutation has an explicit recorded operator
   authorization naming identity, account/region, exact artifact/plan digest,
   resources, limits, and stop action. Design/review PASS and available IAM
   permissions alone authorize none of them. Authorization may cover a precise
   batch; changed inputs, plans, authority, or scope invalidate that batch.
2. **Candidate:** all production inputs come from one reviewed candidate commit
   descended from `19fe8e2e170687ed65deed78cb1af99d60f601e9`. The Package A
   verifier passes the exact 44-file authority and sole head `20260913_0029`.
   No preserved T081/0030 file or modified protected model enters the candidate.
3. **Runtime identity:** API/frontend/bootstrap ECR digests, platform, labels,
   context hashes, task revisions, effective commands, and running ECS image
   digests agree. API starts through the reviewed `pilot_server.py` launcher;
   no command override bypasses the privacy protocol.
4. **Privileged isolation:** bootstrap runs non-root with read-only root/context,
   fixed phase command, no application checkout, editable install, unexpected
   startup hook, mount, or command/environment override. Migration reaches only
   0029 using its own RDS-admin secret; API/worker use `paprnav_app`.
5. **Zero-first:** initial foundation has API/frontend desired counts zero, no
   running service/worker/bootstrap task, and worker schedule DISABLED.
   Bootstrap/verification must pass before service counts increase.
6. **Ingress/tenant:** TLS, exact origin/cookie policy, WAF, ALB-only service
   ingress, invite-only identity, and fresh platform-admin authorization are
   verified live before external invitations. Two unrelated tenants cannot
   access each other's records by identifiers or filters, including after
   revocation. Every V4 route and startup gate remains closed.
7. **Privacy:** synthetic credential/content canaries never appear in captured
   application/frontend/bootstrap/CloudWatch or enabled edge diagnostics.
   A healthy log sink delivers correlated sanitized failure evidence; a missing
   event is failed observability evidence, never proof of success.
8. **Secrets:** no credential value enters Git, Terraform variables/state/plan,
   command arguments, build context/layer, review evidence, or chat. Secret
   ARNs/version identifiers may be evidence; database URLs/passwords/tokens
   may not. A deploy-role permission audit distinguishes secret lifecycle
   permission from value access rather than assuming the supplement removes
   pre-existing grants.
9. **Provider:** manual cohort has no worker run/schedule, no provider API key,
   no paid provider invocation from any reachable API/admin/job path, and no
   fake deterministic OCR result represented as a real transcription. Unknown
   pricing/attempt coverage never becomes zero or complete.
10. **Paid gate:** before the first paid call, a durable pre-call attempt binds
    actor/tenant/upload/job, immutable input/version, provider/mode, units,
    positive approved rate, ceiling, claim, and stable idempotency identity.
    Concurrent workers cannot both claim; ambiguous outcomes cannot retry
    automatically. Recovery/reconciliation is proven before live spend.
11. **Durability:** private encrypted RDS has deletion protection, seven-day
    automated backups, and final snapshots; S3 remains encrypted, private,
    versioned, and `force_destroy=false`. Restore into an isolated new database
    proves application records and corresponding S3 object versions recover.
    No rollback deletes volunteer evidence or runs an unreviewed downgrade.
12. **Cost:** a named recipient owns a real budget, threshold delivery, daily
    recorded spend checks, and stop action before invitations/paid OCR. Budget
    notifications are delayed alerts, not an enforceable spending cap.
13. **ACM/state:** deploy has no ACM mutation authority. Exact issued owned
    certificate and hosted zone pass live identity gates; removed certificate
    resource addresses are absent from actual state. Unexpected durable-resource
    replacement/deletion, state drift, or missing lock protection stops apply.

## Current behavior

This builder made no AWS query. The coordinator supplied fresh read-only
2026-09-19 evidence: assumed deploy role in account `527257972989`, `us-east-1`;
ACTIVE `paprnav-pilot` cluster with zero services/running/pending tasks; no pilot
RDS; API/frontend ECR repositories MUTABLE, AES256, scan-on-push and empty;
bootstrap ECR repository absent; RDS/ECS/ELB service-linked roles absent; deploy
policy v5 with one attachment, last updated 2026-07-10. ACM ListCertificates
and Route53 ListHostedZones remain denied. WAF inventory denial is retained
from Package C's preflight and needs refresh. Coordinator raw evidence belongs
in the execution packet. These dated observations do not waive rechecking
dependencies that change before execution.

Terraform pins AWS provider 5.100.0 and remote S3 state at
`paprnav-pilot-terraform-state-527257972989/pilot/terraform.tfstate`, encrypted
with native S3 lockfile support. It proposes immutable API/frontend/bootstrap
repositories, fixed zero-count services, a DISABLED 15-minute worker schedule,
RDS PostgreSQL 16.3, `db.t4g.micro`, and a $300 monthly budget with 50%/80%
actual and 100% forecast notifications. Availability, current engine support,
quotas, prices, and current state must be refreshed before execution; do not
silently substitute an engine/provider/image version.

API configuration is deterministic OCR; worker configuration is Textract with
no explicit paid-page/rate/mode gate. Defaults include three PDF pages, Textract
sync mode, and a zero estimated page price. `app/workers/ocr.py` selects every
queued/failed job; `process_ingestion_job` flushes an OCRRun before calling the
provider but does not durably commit a protected pre-call attempt. There is no
single-job/claim/idempotent-recovery execution contract. A one-off run of this
worker is therefore not an approved bounded OCR experiment.

Package D reports `recordedRunsOnly=true` and
`paidAttemptCoverageComplete=false`. Completed, failed, pending, unpriced,
unattributed, and reconciliation-required rows remain separate; missing rows
can conceal paid calls. The locked-image privacy evidence (113 cases) is local,
not evidence of deployed log delivery, actual sockets, or ECS replacement.

The working tree includes reviewed A-D files alongside modified
`backend/app/models/core.py`, T081 tests/contracts, and untracked 0030 artifacts.
The Git index and all unrelated work remain untouched by this design.

## Proposed design

### E0 — No-mutation preparation and explicit inputs

Finish decision/design review; inventory staged, unstaged, and untracked paths;
draft candidate inclusion/exclusion hashes, execution commands, identity matrix,
rollback actions, and acceptance checklist. Local fixture validation, offline
Terraform mock plans, context inspection, and local disposable tests may run
without cloud writes. This phase does not contact AWS/providers, push images,
change DNS/secrets, stage/commit, run migrations on AWS, or start services.

Required inputs are recorded in a restricted operator input sheet, with only
non-secret evidence copied into the review run:

| Input | Required before / owner evidence |
| --- | --- |
| Canonical hostname, public zone ID and exact zone name | Certificate/plan; DNS owner and authorization for the one application alias |
| Exact ACM ARN and provisioning-owner principal | Plan; same account/region, exact primary hostname, ISSUED, AMAZON_ISSUED, RSA_2048, `Project=paprnav`, unambiguous lookup; validation/renewal CNAME ownership |
| Budget recipient and accountable cost/incident operator | Foundation/invites; delivery confirmation, approved monthly cap and restore/OCR allowance |
| Exact IAM policy-updater principal/session ARN, accountable owner, and MFA/federation provenance | IAM prerequisite; proof of permission to inventory every policy/boundary consumer, create/version/tag the exact `paprnav-terraform-deploy-pilot-supplement` policy, and attach/detach only that policy on the exact deploy role, not assumed from the bootstrap user; root MFA or centralized root-credential-removal evidence remains a release gate |
| KMS key ARN | IAM prerequisite; actual `aws/secretsmanager` key in this account/region and usable key policy; customer-managed substitution requires separate review |
| Secret-population principal and secret values | Activation; generated invite signing value and one-use admin password enter Secrets Manager securely; RDS manages master and runtime-role task generates application password |
| First admin email/name/platform organization | Bootstrap; human ownership and private handoff, no demo account/password |
| Cohort identities/roles/contact channel and consent | Invitations; start with two unrelated test tenants, then small named cohort, total at most ten users/aircraft |
| Provider choice/mode/credential authority/page and dollar ceilings | Paid gate only; Textract task role needs no static key; non-AWS providers require separate secret/IAM/design review |
| Session-revocation, restore, stop-task/service operators | Activation; exact authorized principals and scoped actions; no implicit master-secret access |

Missing execution inputs stop at a dry-run packet listing unresolved fields.
Provider inputs alone do not block the manual cohort; missing hostname, TLS,
budget, admin, release, recovery, or least-privilege evidence does.

### E1 — Read-only preflight and IAM/certificate prerequisites

With read-only operator access, refresh STS caller/account/region, actual deploy
policy/trust/boundary/SCP effects, policy versions, quotas/engine availability,
state metadata/serial/lineage and resource inventory, ECR/ECS/RDS/S3/log/budget
inventory, exact zone/certificate/KMS metadata, and service-linked roles.
Denied calls remain unknown; do not interpret denial as absence. Inspect actual
remote state for removed ACM certificate/validation/validation-record addresses.
If present, stop for a reviewed state reconciliation preserving renewal CNAMEs;
never apply a plan that deletes them to match the new read-only ACM design.

Generate the supplement using `scripts/generate_pilot_deploy_policy.py` and all
four real inputs (zone, hostname, updater ARN, KMS ARN). The compact current
baseline is 5,011 characters and the amended representative supplement is
4,796; their 9,769-character merge exceeds AWS's non-adjustable 6,144-character
customer-managed-policy limit. The supplement is therefore a separate policy,
not a baseline replacement or merged version:
`arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`.
Retain hashes and character counts for both policies, attachment/version quota
checks, Access Analyzer results, and representative effective-policy simulation.
The broad baseline remains effective, so do not claim IAM-enforced denial of
unrelated regional resources already allowed by it. Distinguish supplement
resource/condition checks, explicit operator authorization limits, and actual
effective IAM denies. Do not grant administrator access to bypass inventory.

Run the executable static authority before M1:
`python3 scripts/pilot_iam_authority.py coverage --generated <generated.json>`.
Retain its JSON output and policy digest. Any nonzero exit stops publication.
The pinned lifecycle catalog binds every expanded Terraform instance and runtime
policy to the reviewed source hashes; source drift requires refreshed review.
The gate also requires the exact reviewed generator construction and baseline
digest, rejects scope/condition widening, and proves no possible excluded-action
grant overlaps any pilot secret ARN. Conditional grants cannot evade this check.
Additional `.tf.json` or override configuration is unreviewed and stops the gate.

**M1, separately authorized IAM mutation:** the named updater creates the exact
tagged supplemental customer-managed policy when absent, or creates/sets a new
version when it already exists, then attaches only that policy to the exact
`arn:aws:iam::527257972989:role/paprnav-terraform-deploy` role. Its proof policy
must bind `CreatePolicy`, `GetPolicy`, `GetPolicyVersion`,
`ListPolicyVersions`, `ListEntitiesForPolicy`, `CreatePolicyVersion`,
`SetDefaultPolicyVersion`, `TagPolicy`, and any separately authorized rollback deletion to the exact
supplement ARN; `AttachRolePolicy`/`DetachRolePolicy` bind the exact role and
the exact supplement through `iam:PolicyARN`. Baseline v5 and its attachment
are unchanged. Before versioning an existing supplement, exhaust
`ListEntitiesForPolicy` pagination for both permissions-policy and
permissions-boundary use and stop on any consumer other than the recorded exact
deploy-role attachment or on any boundary use. Record pre/post attachments,
versions, hashes and effective permissions. Rollback restores the prior default
version and exact prior attachment state: detach only a supplement newly
attached by this operation, retain one already attached, and keep a previously
detached policy detached. Ambiguous calls require re-reading actual policy,
version/default, and fully paginated consumer state before recovery; never
blindly detach or delete. Deleting exact non-default versions or a new detached
policy requires explicit deletion authority and zero unexpected consumers. A
partially created policy is never treated as attached authority.

The mandatory offline M1 preflight is
`python3 scripts/pilot_iam_authority.py publication --pre-state <pre-state.json> --candidate-sha256 <candidate-sha256>`.
The candidate hash is SHA-256 of the supplement JSON canonicalized by the
authority's `digest()` (sorted keys, compact separators). Build the restricted
snapshot from fresh GetPolicy evidence, ListPolicyVersions plus each version's
canonical document hash, both ListEntitiesForPolicy usage filters, fully
paginated ListAttachedRolePolicies, and observed policy/attachment quotas.
Each page is `{request: <exact parameters>, response: <raw response>}` including
`IsTruncated` and continuation `Marker`; include empty entity arrays. An absent
policy requires the exact `NoSuchEntity` GetPolicy result, never a denial. The
snapshot schema is implemented by `snapshot()` in the authority; tests supply
synthetic examples, not live evidence. Existing policies include ARN, PolicyId,
default, AttachmentCount and PermissionsBoundaryUsageCount. Preserve the prior
snapshot and serialize this operation; no other policy writer may run concurrently.

Only the returned steps are eligible for the separately approved M1 batch.
Re-read/revalidate after every call. Any ambiguous result stops forward execution
and requires fresh observations, then
`python3 scripts/pilot_iam_authority.py recovery --pre-state <pre-state.json> --observed-state <observed-state.json> --candidate-sha256 <candidate-sha256>`.
Re-run after each recovery step until no steps remain. Recovery restores the
prior default and attachment state; newly created policies/versions remain as
explicit residuals awaiting separate deletion authority. These commands cannot
call AWS or execute mutations and never supply MFA/owner/M1 authorization.
Successful GetPolicy metadata and any `getPolicyError` are mutually exclusive;
contradictory preflight or recovery observations stop instead of preferring one.

**M2, separately authorized certificate/DNS prerequisite:** the certificate
owner provisions/validates/tags the supplied certificate if absent. The deploy
role remains ACM read-only. Retain issuer, exact domain/ARN/tag/status and
renewal-record evidence; application alias creation is in the later foundation
plan. Do not reuse certificate mutation prose from C's superseded decision.

**M3, separately authorized service-role prerequisite:** create only the three
missing RDS/ECS/ELB service-linked roles through the constrained deploy actions,
or include their service-triggered creation explicitly in the foundation
authorization. Verify existence/trust; do not attempt to delete them on failure.
Refresh all previously denied inventories and resolve any remaining denial
before a final refreshing plan.

### E1A — Required pre-execution implementation amendments

Before candidate construction, complete one coherent reviewed family that fixes
the two design-review dependencies without widening the product:

1. Bind `PAPRNAV_DATABASE_HOST` and `PAPRNAV_DATABASE_PORT` in every sealed
   bootstrap task definition directly from `aws_db_instance.postgres.address`
   and `.port`. `bootstrap.py` obtains only `username` and `password` from the
   RDS-managed secret, requires `paprnav_admin`, and obtains host/port only from
   those non-secret environment fields. It validates a nonempty host and an
   integer port in 1–65535. M8 permits no run-task command or environment
   override, so an operator cannot redirect privileged bootstrap connectivity.
   Do not add host/port to, or manually rewrite, the RDS-managed secret.
2. Update the IAM generator, policy matrix and tests to emit the exact separate
   supplement lifecycle and updater proof described by M1. Preserve the existing
   baseline rather than trimming broad grants opportunistically in this pilot.

Realistic tests use the RDS-managed-secret shape `{username,password}` plus the
Terraform-derived endpoint/port, and reject missing/invalid endpoint, invalid
port, wrong username, secret fields attempting to override endpoint/port, and
task-definition/run-task overrides. Terraform assertions bind both environment
values to the exact RDS resource. IAM tests reproduce 5,011 / 4,796 / 9,769
compact counts with stable fixture inputs, enforce each policy's 6,144-character
limit and attachment/version quotas, and prove exact policy/role scoping and
rollback actions. Build and inspect a refreshed sealed bootstrap image and task
definition after the family passes.

This family is a launch dependency, not generalized hardening. Route its
coherent implementation to Sol high and its complete-family adversarial review
to a separate Astra high reviewer. Candidate construction remains blocked until
that review passes and E-DESIGN-001/002 are independently closed.

### E2 — Reviewed candidate, images, and repository bootstrap

**L1, separate candidate-construction authorization:** construct a clean
`codex/` release checkout/commit from the approved baseline and exact reviewed
A-D/privacy/IaC/tooling changes, with explicit reviewed file/hunk inventory.
Never commit the dirty source checkout wholesale. Preserve protected model and
migration blobs from their approved authority, and exclude all T081/0030 paths
in both boundary manifests, not merely their migration filenames. Include all
required new launcher/protocol/services/locks and reviewed operational files.
Compare candidate content hashes against approved packets; any missing approval
or overlapping unresolved hunk returns to review. Record resulting commit SHA.

Run `verify_pilot_release_boundary.py --ref <candidate>`; from the clean
candidate run `build_pilot_release_context.py build/verify` for `api`,
`frontend`, and `bootstrap`, with explicit unique destinations and `--ref`.
Build/verify the sealed migration context independently. Do not use an overlay
to bypass the candidate authority gate: final release has no dirty overlay.
Retain all manifests/hashes, exact build args, base digests, lockfiles and
linux/amd64 platform. Build locally from those contexts; inspect final layers,
users, entrypoints, imported dependency origins/startup hooks, and labels.
Run the affected exact-image/privacy and fresh PostgreSQL/bootstrap checks;
test-only oracle images must not accidentally become production images.

The recorded foundation lacks the bootstrap ECR repository. Resolve this
dependency before pushing: **M4, explicitly approved ECR-only prerequisite
plan/apply** creates only `aws_ecr_repository.bootstrap` and makes existing
API/frontend repositories immutable with scan-on-push. Use an exceptional
narrowly targeted saved plan of those exact repository resources, with actual
read-only identity inputs and locally derived digest-shaped inputs; review its
full dependency/action list and reject unrelated changes. This is not a full
foundation apply. Retain why targeting was necessary and immediately follow it
with a full refreshing plan after push. If targeting cannot produce only those
actions, stop for a reviewed repository-only bootstrap artifact instead.

**M5, explicitly authorized image pushes:** push the three inspected images to
the exact pilot repositories, using unique immutable release tags. Resolve
registry manifest digests, pull/inspect them, and bind ECR digest/platform to
local context/labels and scan findings. Local Docker image IDs are not registry
manifest digests. Block unresolved material scan findings; do not widen the
conditional dependency exclusions accepted in C. Retain immutable digests and
use only `repository@sha256:...` in Terraform. Push grants no apply permission.

### E3 — Full refreshing plan and zero-service foundation

Use the candidate Terraform, pinned provider/lock, approved non-secret inputs,
`external_mode=true`, real subscriber/updater, and three pushed digests.
Read remote state first; verify encryption/versioning/access and lockfile
permissions, lineage/serial, and no competing execution. Do not fall back to
local state, migrate backend, force-unlock, import, or state-remove implicitly.
A refreshing `plan -out` normally writes a remote lock: authorize this bounded
state-lock operation separately from read-only inventory; protect local plan
and state material as restricted evidence. Never publish a full raw state dump.

Before any M6 approval, export the exact saved binary plan with
`terraform show -json <saved-plan> > <saved-plan.json>` and run
`python3 scripts/pilot_iam_authority.py plan --generated <generated.json> --plan-json <saved-plan.json> --saved-plan <saved-plan> --terraform-bin <trusted-terraform>`.
Require exit 0 and retain the returned JSON-file/canonical-plan/policy hashes
alongside the returned saved-binary and embedded-configuration hashes. The gate
compares every embedded module/configuration file with the reviewed sources,
runs read-only `terraform show -json` on that same binary using the trusted
operator-installed executable, and requires the supplied JSON to match exactly.
A JSON file alone cannot pass. Re-run this gate immediately before apply and
require identical hashes. The gate rejects the entire plan, including
mixed plans, for secret description/KMS changes, unknown secret inputs, legacy
names/ARNs, secret replacement/deletion, incomplete/targeted plans, and omitted
or unknown managed instances. Only creates and tag-only/no-op secret transitions
are eligible. Computed create outputs (ARN/id/name_prefix/policy/replica) may be
unknown because the bound source declares none as configurable inputs; any
new configuration returns through review. This gate supplements the full E3
review and grants no apply authority.

Review saved plan JSON and hash: zero services, disabled scheduler, correct
certificate and alias, exact network/WAF paths and rates, no public RDS, no
runtime master credentials, right execution/task roles, private/versioned S3,
backup/deletion controls, budget/filter/subscriber/log retention, and no durable
resource destroy/replacement. Confirm existing tag-mutability updates and new
ECR resource were absorbed with no unexpected drift. Price the actual planned
ALB/WAF/RDS/Fargate/public IPv4/logs/storage/backups/S3/ECR/restore shape using
current AWS pricing before approval; no historical estimate is current evidence.

**M6, explicit foundation apply:** approve and apply that exact fresh saved
plan only after the executable E3 gate passes on its exact JSON export, with a
bounded spend window and stop authority. A gate stop prohibits the entire apply;
do not target around it. Record outputs (ARNs/IDs,
never values), state serial and apply result. Verify service desired/running/
pending counts zero, scheduler disabled, no unexpected tasks, durable controls,
TLS/certificate association and DNS, and budget configuration. Partial apply
stops; refresh/review the resulting state and a new plan before resuming.

### E4 — Secrets and sealed database bootstrap

**M7, explicit secret population:** dedicated authorized operator writes the
invitation secret and one-use first-admin password into their exact new ARNs
through a non-echoing SDK/secure input path, no shell arguments/history/files
or Terraform secret-version resources. Validate shape/strength privately.
RDS creates its managed admin secret; do not copy it into runtime configuration
or modify its schema. Retain only successful version/ARN/time/actor evidence.
Bootstrap receives the admin ARN plus the non-secret endpoint/port bound from
the exact Terraform RDS resource and fetches username/password in-process. API
receives only app URL and invite values via its execution role; worker receives
only app URL; frontend gets none.

**M8, explicit migration/bootstrap and verification authority:** record exact
task-definition revision/digest, cluster, subnet/security group, role, phase,
no mounts/overrides, and expected database endpoint. Run one phase at a time:
`migration` to 0029, `reference`, `runtime-role`, then `first-admin`.
Before migration retain a manual pre-change snapshot if a database already has
data; an unexpected nonempty initial deployment is a stop, not a bootstrap
target. Each phase must finish successfully and be verified before the next.

Verify the actual Alembic head and inventory, canonical three reference rows,
idempotent reference rerun, exact grants and negative app-role privileges.
Runtime-role changes the password, publishes its generated app URL, checks
returned version at AWSCURRENT, and makes a fresh application-role connection.
If publication fails, keep services zero and rerun this phase with new generated
credentials; never guess, log, or manually copy the failed password.
First-admin creates the permanent consumption marker and all identity/audit
rows atomically; a second invocation/revoked-admin attempt must fail closed.
Run destructive/concurrent fault tests in a disposable database, not against
pilot identities. Live verification uses bounded read/denial probes.

After successful private admin login/handoff, separately authorize retirement
of the one-use bootstrap password value/access and record the disposition.
Do not delete the permanent DB consumption marker or casually rotate the admin's
application password. Keep migration/runtime-role task authority unavailable
for ordinary application work. All verification tasks using privileged secrets
are explicit M8 actions, not implicit permission for arbitrary shell overrides.

### E5 — Activation and pre-invite acceptance

**M9, explicit API/frontend activation:** existing Terraform hard-codes counts
zero. For this bounded pilot, operator sets exact service revisions to one API
and one frontend through approved ECS UpdateService calls; scheduler stays
DISABLED. Record these two counts as intentional operational drift. No later
Terraform apply may run without refreshing and reviewing count reconciliation;
an unattended apply would reset counts to zero. A future count-variable change
requires its own reviewed IaC slice and is not necessary for first learning.

Verify running digests, launcher/no API command override, task role/config,
health/target routing, direct same-origin API and unavailable Next proxy,
HTTP redirect, certificate/hostname chain, cookie flags, CSRF, registration
rejection, V4 404s, and unauthenticated/admin authorization. Use synthetic
canaries for malformed requests, handled/unexpected errors, streaming download,
correlation, log delivery, graceful stop/replacement and bounded reconnect.
Inject DB failure only in an isolated disposable acceptance task; do not revoke
live DB/network permissions to simulate it. Privacy backpressure/cancellation
evidence is bounded by observed I/O and cooperative shutdown; blocked logging
or an unresponsive task requires operator replacement. Retain actual recovery
timing, not an invented hard deadline.

Inspect effective CloudWatch streams, retention (30 days), read/write principals
and frontend/bootstrap diagnostics as well as API logs. Keep raw access logs,
WAF sampling and body capture disabled; verify actual edge logging settings
before sending private data. Prove one sanitized failure arrives with the
response correlation ID and no canary content. Missing logs halt exposure.

Create two synthetic unrelated tenant identities via real invitation flow and
test valid/replayed/tampered/expired codes, role restrictions, current membership
revocation, cross-tenant IDs/filter inputs for aircraft/upload/download/jobs/
entries/events/feedback/cost, forbidden ordinary feedback triage/admin summary,
and audited session revocation. Never put invite codes in URLs or evidence.
Exercise manual entry, upload/download and feedback; verify canonical
`invite_accepted`, `aircraft_created`, `upload_received`, and
`logbook_entry_created` counts and failure non-success. Page/AD achievements
require real completed eligible workflows; absent ones remain absent.

Complete the pre-invite restore drill below, establish budget notification
delivery and current recorded spend, and obtain independent execution review.
**M10, explicit invitation issuance/delivery:** named cohort and authorized
private channel; operator issues at most 24-hour codes, starts small, and grows
only to the ten-user/aircraft bound. Sending any invite is a separate approved
external communication; code contents are never logged. Explain OCR pending
and decision-support limits in the cohort instructions. Capture feedback
through the app with safe request/workflow references.

### E6 — Bounded paid-provider/worker gate, independent of initial invitations

Do not run the existing all-queued/all-failed worker, even once, merely because
the schedule is disabled. Before paid OCR, prepare and independently approve a
small coherent implementation slice for durable attempts, single-job selection,
atomic claim, explicit page/mode/provider limits, stable idempotency/recovery,
and reconciliation. Existing JSON fields may be used only if their persistence
and locking oracle proves the entire invariant; a new schema requires a new
reviewed migration/authority amendment and revision ownership. Never repurpose
T081's 0030 or waive Package A's fixed head casually. If that cannot be closed
within the pilot slice, retain the useful manual cohort and report OCR pending.

For the smallest experiment select one consented source object/version, one
job, one tenant/user, and at most three approved pages (lower if provider mode
requires). The operator supplies an exact positive current unit rate, hard
attempt/page/dollar allowance, provider mode and timeout. Count pages before
any paid request; default zero price or an unset/unbounded limit fails closed.
Prefer one provider path; no comparative/AB calls, fallback providers, automatic
retries, fan-out, AD paid extraction, or broad queue catch-up. Textract identity
is the exact task IAM role; Mistral keys or other providers are not required to
reach first learning. Async mode additionally requires stable client token,
persisted provider job ID, poll-only recovery, and supported permissions;
current sync mode must not be called idempotent by assertion.

Retain local/concurrency/crash evidence for before Start, after Start/before
job-ID persistence, after job-ID persistence, during poll, and after completion
before domain commit. Durable unknown outcomes retain attribution and an
operator reconciliation requirement; the next run cannot re-charge them.
Review changed image/task/environment/IAM/grants as one family and reissue
candidate/digest/plan evidence for changed dependencies.

**M11, explicit paid execution:** authorize the exact single-job task/digest,
provider/mode/pages/rate/maximum USD and stop/reconciliation operator. Keep the
recurring scheduler disabled; task count one and no automatic retries. After
completion verify page review and derived entry/achievement, recorded usage
and attributed rate/estimate/billing classification, provider request/job
evidence, and delayed aggregate AWS spend. Capture unknowns without inventing
zero. Stop the worker after this flow. Recurring scheduling, another job, or
cohort-wide OCR requires new bounded authority and sufficient reconciliation
evidence; it is not needed for this package's one-flow acceptance.

### E7 — Acceptance, cost, and recovery evidence

Use two explicit milestones: **manual cohort ready** after E5, and **full parent
pilot acceptance** after E6's real bounded OCR flow. Do not report the latter
while provider gates are pending. The evidence index binds candidate/digests,
policy/plan hashes, operator authorizations, state serials, task revisions,
TLS/WAF/tenant/privacy checks, achievements/feedback, recorded costs, backup/
restore and rollback evidence to timestamps and sanitized IDs.

Budget proposal is $300/month, subject to actual plan pricing and operator
approval; 50%/80% actual and 100% forecast are existing thresholds. Operator
records daily dated actual/forecast AWS spend and provider exposures, including
reporting lag and shared/unallocated categories. Confirm `Project` cost-tag
activation and that the filter captures intended spend; if new tag billing data
lags, use an explicit broader/account reconciliation with unrelated spend
separated. Prove notification delivery with a separately authorized temporary
bounded test threshold/budget and restore it, or another real supported delivery
test; configuration alone is not delivery proof. Such changes require M12.

At 50% investigate forecast/attribution; at 80% suspend paid work and cohort
growth pending operator review; at forecast beyond cap or unbounded unknown
exposure, stop new traffic/work using the preauthorized stop procedure.
The approved fixed-cost forecast plus restore allowance and variable reserve
must fit the cap before activation. Keeping ALB/RDS/storage after stopping
tasks still costs money; record remaining burn, do not promise an instant cap.

**M12, explicit backup/restore and operational tests:** snapshot a synthetic
pre-invite dataset and restore to a new isolated private DB identifier with
retained encryption/deletion protection. Record ARN/time/status, measured
recovery duration and recoverable timestamp. Reconnect only a disposable
acceptance task with an appropriately scoped temporary secret/role; verify
0029/reference/grants, both tenant records, achievements/feedback, session
revocation plan, and download checksums for the matching S3 object version IDs.
Never repoint the live database to a drill or start a worker. Record permitted
cleanup of disposable resources separately, preserving required snapshots and
never using destroy against pilot data. Repeat the drill only for a changed
recovery dependency or a real incident. Seven-day backups and 90-day old S3
versions have different horizons; the evidence identifies the recoverable pair.

Set initial operational targets of recovery within one business day and at most
24 hours of lost writes, subject to measured restore/PITR evidence and operator
acceptance before invitations. A test that misses those bounds blocks the
milestone until the owner explicitly revises the cohort promise or fixes it.

### Dependency, risk, and review cadence

Scores are risk / complexity / centrality / uncertainty, each 1–5.

| Family | Dependencies and scores | Reversibility/oracle | Review boundary and exit evidence |
| --- | --- | --- | --- |
| Inputs, state, IAM/ACM | A-C; 5/3/5/4 | Separate supplement attach/detach reversible; cert/DNS ownership persistent; policy/state oracle | Astra design; quota-feasible policy hashes, live effective matrix and exact inputs |
| Bootstrap/IAM amendment | E design; 5/3/5/2 | Source/image changes reversible; deterministic managed-secret and policy-size oracles | Sol high implementation, then Astra high complete-family review; realistic secret connection and exact attachment proof |
| Candidate/ECR/images | A-D/privacy; 4/3/5/2 | Local rebuild reversible; push persistent; hashes/locks strong | One coherent family review; candidate/context/digest equality |
| Foundation/bootstrap | prior two; 5/4/5/3 | Data/role/secret changes require snapshots or rerun protocol | Astra implementation/execution boundary; zero services, 0029, grant/admin proof |
| Activation/manual cohort | foundation, budget, recovery; 5/3/4/3 | Counts reversible, volunteer writes retained; live ACL/privacy oracle | Independent pre-invite review; HTTPS/two tenants/logs/restore/cost |
| Paid single-job flow | manual runtime plus new attempt contract; 5/4/3/5 | Charges irreversible, ambiguity durable; crash/concurrency oracle | Separate Astra design/implementation; one authorized flow and reconciliation |
| Final acceptance | applicable milestones; 5/3/5/3 | Attest only retained evidence | Independent Astra xhigh closure; complete evidence index/no blockers |

Route approved coherent implementation to Sol high, deterministic generated
artifacts to Terra/Sol medium, and invariant/IAM/provider design or adversarial
closure to Astra high/xhigh per policy. Review coherent families once; repeat
only after material changes/findings. Review includes callers, readers, scripts,
untracked/staged/unstaged scope and inherited limits. The coordinator assigns
separate read-only design/implementation/closure reviewers and records returned
identities, exact packet fingerprints and all finding dispositions. Claude is
optional critic only after a complete Codex packet, never an approval substitute.

## Alternatives considered

- Waiting for OCR hardening before any invites delays feedback on already
  closed workflows; staged manual learning preserves the paid-call gate.
- Running the existing worker once is rejected: it enumerates all queued/failed
  jobs and has no durable single-claim/ambiguous-charge protection.
- Adding Cognito, multi-region HA, NAT gateways, a billing product, analytics
  SaaS or full T081 completion is deferred; none is required for ten users.
- Applying everything before immutable pushes is rejected because task inputs
  must bind real digests; the narrow ECR prerequisite breaks that dependency.
- Broadly committing the current tree, deploying latest tags, and using the
  master identity at runtime violate closed A-C boundaries.
- Treating budget email or Package D estimates as a hard cost limiter is rejected
  because billing lag and missing pre-call records leave unknown exposure.

## Trust, authorization, and audit boundaries

Execution identity/action/resource matrix (the effective policy, not this table,
is the grant; all mutations additionally need the checkpoint authorization):

| Identity | Allowed function/action family | Resource boundary / forbidden expansion |
| --- | --- | --- |
| Read-only operator | STS, inventory/describe, policy/state metadata, Access Analyzer/simulation | Exact account/region; no value reads or lock writes in read-only phase |
| Named strongly authenticated IAM updater | Create/get/list/version/tag exact supplement; inventory permissions-policy and boundary consumers; attach/detach exact supplement | Exact supplement policy ARN and exact deploy role with `iam:PolicyARN`; complete pre-state required; baseline unchanged; detach only to restore a newly attached pre-state; deletion separately authorized |
| Certificate/DNS owner | Provision/validate/tag ACM, retain renewal CNAME | Supplied hostname/cert/zone; independent of deploy ACM reads |
| Deploy role | Reviewed Terraform resources, exact-zone alias, named service-role creation, ECR push, scoped ECS service/task actions | Pilot resources/account/region; prove effective PassRole and secret-value denials; no ACM mutation |
| Secret operator | PutSecretValue and metadata/version checks | Exact invite/first-admin ARNs; not general RDS/app-secret read access |
| API execution role | ECR pull/log delivery; Get/Describe app DB and invite secrets | No master/first-admin secret |
| Worker execution role | ECR pull/log delivery; Get/Describe app DB secret | No invitation/master/first-admin secret |
| Frontend/bootstrap execution roles | ECR pull/log delivery | No secret injection permission |
| API task role / DB login | Artifact bucket objects/list; `paprnav_app` DML/sequence inventory | No provider invocation, DB DDL/roles/alembic/control-schema access |
| Frontend task role | No data/provider/secret authority | No RDS inbound grant |
| Migration/reference task role | Get/Describe managed RDS secret; fixed sealed phases | Exact admin secret, no app secret publication or first-admin password |
| Runtime-role task role | Get/Describe admin, Put/Describe app URL | Exact two secret ARNs; no Get app value; zero-service rerun only |
| First-admin task role | Get/Describe admin and one-use password | Fixed first-use phase and permanent DB sentinel |
| Worker task role | Artifact bucket plus reviewed Textract actions | Current Textract `Resource=*` reflects service support, not open provider choice; only activated at M11 |
| Scheduler role | RunTask exact worker revision; PassRole exact worker roles to ECS | Schedule stays disabled for this one-flow pilot |
| Recovery/session operator | Explicit snapshot/restore, scoped temporary secret/task, audited revocation | Named DB/snapshot/task/secret; no unreviewed arbitrary admin task |
| Platform admin | Issue invites, tenant-wide summaries, feedback disposition | Fresh application membership; cannot apply Terraform/read infrastructure secrets |

Restrict evidence readers: first-admin/contact data, state/plan files and provider
identifiers are operationally sensitive even without secret values. Keep raw
failure output private; publish sanitized check results and hashes. Audit
CloudTrail/event metadata where available without storing secret request values.

## Read paths and consumers

Browser/auth/aircraft/manual logbook/upload/download/feedback and non-V4 AD
views; ordinary scoped observability and administrator pilot summary; operator
CloudWatch, ECS, Budget/billing, S3 version, RDS recovery and Terraform state
inspection; release-context/IAM generators, migration/grant/reference manifests,
Dockerfiles/locks, and future worker/reconciliation consumers. Record any newly
discovered provider/diagnostic caller as a gate dependency, not an exclusion.

## Write paths and administrative paths

Only this decision and its design-review/remediation artifacts are written
during design. Future E1A, L1 and M1–M12 enumerate
candidate creation, policy/certificate/service-role/ECR prerequisites, image
push, state locking/apply, secret population, migration/bootstrap, service
activation, invite communications, paid provider call, recovery and test-budget
mutations. Separate authorizations may group exact steps but cannot be inferred
from one another. Ordinary cohort writes use existing application transactions;
there is no schema change in the initial manual slice.

## Migration, compatibility, correction, and rollback

Use only sealed 0029 plus C's separately manifested bootstrap/control schema.
No dev seed, general Alembic head discovery, untracked 0030, or automatic
downgrade. Save state serial/lineage, policy default version, task revisions,
digests, secret version identifiers, and snapshot/object-version IDs before
changes. Record drift and compatibility before every subsequent apply.

Stop immediately for wrong identity/digest/state, cross-tenant disclosure,
secret/canary leakage, unknown migration state, failed privilege/restore proof,
unhealthy/missing log evidence, invalid TLS/WAF, unexpected data replacement,
unbounded provider exposure, or cap breach. Preauthorize emergency scale-to-zero,
worker stop/schedule disable and containment before activation. Stopping a task
after a paid request is not provider cancellation or proof of zero charge.

First release has no prior approved production image: rollback is service count
zero with data retained. Later rollback selects a prior independently approved
privacy-safe digest only when schema/grants/config compatibility is proven;
otherwise stop writes, snapshot, restore into a new private RDS instance, verify
tenant data/S3 versions, publish a new app URL under explicit authority, and
repoint/restart services. Keep the old DB for investigation. Account for
post-snapshot writes and renewed/revoked sessions; do not silently resurrect
revoked sessions in restored data. Revoke all restored sessions before exposure
and rotate outstanding invitation authority if appropriate, under scoped
authorization. Invite-secret rotation invalidates codes, not existing sessions.

IAM rollback restores the supplement's exact prior default version and
attachment state, detaching it only when this operation newly attached it, and
leaves the baseline policy and attachment unchanged. Ambiguous calls require
actual-state recovery after complete policy/boundary consumer inventory.
Deletion requires separate authority and confirmation of zero unexpected
consumers. DNS/secret/version changes and drill
cleanup each need exact resource authority. Restore/rollback never deletes
volunteer data, disables deletion protection, clears bootstrap consumption, or
enables T081 features. Preserve final-snapshot and S3 retention semantics.

## Test strategy

Carry forward unchanged A-D proofs; rerun only dependency-affected checks.
Deterministic release checks cover candidate graph/hash/mode and forbidden
content, double-built manifests, image labels/platform/runtime inventory,
exact locked privacy oracle, Terraform mock gates, the realistic RDS-managed
secret plus exact endpoint/port bootstrap contract, IAM size/attachment/version
quotas and honest effective allow/deny matrix,
fresh PostgreSQL 0029/bootstrap/idempotency/concurrency/grant negatives, and
frontend same-origin/invite/admin rendering. Retain actual commands/results,
not an unchecked checklist. Do not run the broad T081 suite for this package.

Live acceptance follows E5–E7: TLS/health/WAF upload/auth exceptions, secure
session/CSRF/invite negatives, two tenants and revocation, correlated sanitized
failures with live log delivery, manual/upload/feedback achievements, recorded
spend and real budget delivery, isolated restore and stop/replacement. Paid
activation additionally needs the complete durable-attempt crash/claim oracle
and one bounded real flow. Negative provider tests are local/stubbed and do not
make paid calls. No synthetic forced error may expose real user content.

The implementation review packet includes exact input completeness, artifact
hashes, authorizations and execution outcomes. Closure verifies all applicable
evidence plus known limitations, no open blocker, no unsupported pass claims,
and no model assignment inferred from requested routing. Manual acceptance
and full acceptance are recorded separately; no unavailable result is marked
passed or accepted by silence.

## Expected file scope

Design/remediation write scope is exactly this decision and
`design-remediation-1.md`, plus coordinator-owned immutable review and ledger
artifacts. No application, IaC, IAM, model, migration, release policy, index or
commit edits and no cloud/provider action occur in this pass. After design PASS,
the E1A implementation scope is limited to the bootstrap/IaC connection
contract, IAM generator/matrix, and their existing focused tests; it requires a
new scope declaration before editing. Future approved implementation may add a
concise non-secret execution/evidence runbook and the narrowly scoped provider
attempt family after its separate design gate. Preserve unrelated dirty work.

## Known uncertainty

No execution input sheet, release candidate commit, pushed registry digests,
current effective IAM/zone/cert/state inventory, real secret values, live plan,
notification-delivery proof, or recovery measurement is established by this
decision. Required identity/hostname/budget/admin inputs are unresolved. The
bootstrap-repository targeting path and live policy attachments/versions need
preflight proof. The separate-policy layout is designed but not implemented or
independently closed. Existing PostgreSQL 16.3 availability must be checked.

The durable paid-attempt protocol is absent, so full OCR acceptance remains a
real engineering dependency, not an operator checkbox. A successful manual
cohort does not close it. Package D cannot prove missing paid attempts, invoice
accuracy or cost allocation; failed sinks can lose safe evidence, and its local
cooperative shutdown bounds do not establish production task liveness.

Post-pilot: cohort expansion, broad/recurring OCR, per-invite revocation and
multi-organization invites, managed identity/recovery/MFA, automated billing,
complete provider reconciliation, richer analytics, private egress/HA, and
T081 V4 acceptance semantics. Do not pull these into initial deployment unless
a concrete failed gate makes one necessary. The current stop point is a
reviewable dry-run decision and missing-input inventory; no apply is assumed.

## Model routing

- Builder/runtime identity: `/root/t082_package_e_execution_design`.
- Requested route: `gpt-6-astra` high. Actual model:
  `model not exposed by runtime`; actual effort: `effort not exposed`.
- Trigger: AWS/IAM/secrets/provider execution design following closed package
  boundaries, with irreversible actions, cost exposure and rollback semantics.
- Coordinator: `/root`; actual model/effort must be recorded from its runtime
  notice. This builder does not self-review or attest execution/closure.
- Independent reviewer is not assigned by this artifact. Coordinator must
  record the actual returned reviewer identity and exposed model/effort in a
  new immutable report; preferred Astra high for this framed design and xhigh
  for interacting provider/rollback invariants or closure after findings.
- Initial reviewer `/root/t082_package_e_design_review` returned FAIL after an
  Astra xhigh request; actual model/effort were not exposed. Design-remediation
  builder `/root/t082_package_e_design_remediation` was requested as Astra
  xhigh; actual model/effort were not exposed. After it returned the bounded
  technical selection but continued drafting, the coordinator interrupted the
  turn and converted that selection into this compact amendment. Independent
  re-review remains mandatory.
