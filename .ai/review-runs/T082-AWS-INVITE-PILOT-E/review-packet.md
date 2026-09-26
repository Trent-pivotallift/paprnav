# Review packet: T082-AWS-INVITE-PILOT-E

Stage: implementation
Generated: 2026-09-19T23:02:24+00:00
Base: `HEAD`
Head: `19fe8e2e170687ed65deed78cb1af99d60f601e9`
Scope fingerprint: `e0628f9566074128e50e9a9d50bfe12f4f85c6175483af52b050a633b30c8d8e`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

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
| Exact IAM policy-updater principal ARN | IAM prerequisite; proof of permission to create/version/tag the exact `paprnav-terraform-deploy-pilot-supplement` policy and attach/detach only that policy on the exact deploy role, not assumed from the bootstrap user |
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
baseline is 5,011 characters and a representative generated supplement is
3,731; their 8,704-character merge exceeds AWS's non-adjustable 6,144-character
customer-managed-policy limit. The supplement is therefore a separate policy,
not a baseline replacement or merged version:
`arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`.
Retain hashes and character counts for both policies, attachment/version quota
checks, Access Analyzer results, and representative effective-policy simulation.
The broad baseline remains effective, so do not claim IAM-enforced denial of
unrelated regional resources already allowed by it. Distinguish supplement
resource/condition checks, explicit operator authorization limits, and actual
effective IAM denies. Do not grant administrator access to bypass inventory.

**M1, separately authorized IAM mutation:** the named updater creates the exact
tagged supplemental customer-managed policy when absent, or creates/sets a new
version when it already exists, then attaches only that policy to the exact
`arn:aws:iam::527257972989:role/paprnav-terraform-deploy` role. Its proof policy
must bind `CreatePolicy`, `GetPolicy`, `GetPolicyVersion`,
`ListPolicyVersions`, `CreatePolicyVersion`, `SetDefaultPolicyVersion`,
`TagPolicy`, and any separately authorized rollback deletion to the exact
supplement ARN; `AttachRolePolicy`/`DetachRolePolicy` bind the exact role and
the exact supplement through `iam:PolicyARN`. Baseline v5 and its attachment
are unchanged. Record pre/post attachments, versions, hashes and effective
permissions. Rollback detaches only the supplement and restores its prior
default version when one exists; deleting its exact non-default versions or the
new detached policy requires explicit deletion authority and zero unexpected
attachments. A partially created policy is never treated as attached authority.

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
values to the exact RDS resource. IAM tests reproduce 5,011 / 3,731 / 8,704
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

Review saved plan JSON and hash: zero services, disabled scheduler, correct
certificate and alias, exact network/WAF paths and rates, no public RDS, no
runtime master credentials, right execution/task roles, private/versioned S3,
backup/deletion controls, budget/filter/subscriber/log retention, and no durable
resource destroy/replacement. Confirm existing tag-mutability updates and new
ECR resource were absorbed with no unexpected drift. Price the actual planned
ALB/WAF/RDS/Fargate/public IPv4/logs/storage/backups/S3/ECR/restore shape using
current AWS pricing before approval; no historical estimate is current evidence.

**M6, explicit foundation apply:** approve and apply that exact fresh saved
plan, with a bounded spend window and stop authority. Record outputs (ARNs/IDs,
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
| Named IAM updater | Create/get/list/version/tag exact supplement; attach/detach exact supplement | Exact supplement policy ARN and exact deploy role with `iam:PolicyARN`; baseline unchanged; deletion separately authorized |
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

IAM rollback detaches only the exact supplemental policy, restores its prior
default version when applicable, and leaves the baseline policy and attachment
unchanged. Deletion requires separate authority and confirmation of zero
unexpected attachments. DNS/secret/version changes and drill
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


## Current finding ledger

```json
[
  {
    "id": "E-DESIGN-001",
    "stage": "design",
    "reviewer": "/root/t082_package_e_design_review",
    "severity": "high",
    "status": "fixed_pending_verification",
    "invariant": "The sealed fixed-phase bootstrap must connect to the exact Terraform-managed RDS instance without changing the RDS-managed secret schema.",
    "summary": "Bootstrap requires host and port inside an RDS-managed secret that does not contain them, while Terraform supplies no separate endpoint or port.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-initial.md",
      "infra/bootstrap/bootstrap.py:83-95",
      "infra/terraform/ecs_runtime.tf:42-47",
      "https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_jdbc.html"
    ],
    "impact": "All four bootstrap phases fail before connecting, blocking the manual invite cohort.",
    "requiredClosure": "Amend the design and implement a reviewed bootstrap/IaC contract that binds non-secret endpoint and port to the exact RDS resource, keeps credentials in the managed secret, adds realistic missing/mismatch tests, and refreshes image/task evidence.",
    "closureEvidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md:E1A",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/design-remediation-1.md"
    ]
  },
  {
    "id": "E-DESIGN-002",
    "stage": "design",
    "reviewer": "/root/t082_package_e_design_review",
    "severity": "high",
    "status": "closed",
    "invariant": "The IAM prerequisite must fit AWS policy quotas and be publishable and reversible by the explicitly named updater authority.",
    "summary": "The proposed merged customer-managed policy is approximately 8,704 non-whitespace characters, exceeding AWS's 6,144-character managed-policy limit.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-initial.md",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md",
      "infra/aws-iam/paprnav-terraform-deploy-policy.json",
      "scripts/generate_pilot_deploy_policy.py",
      "https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html"
    ],
    "impact": "M1 cannot publish the proposed merge; splitting the policy would require authority and rollback behavior not covered by the current design.",
    "requiredClosure": "Select and independently review a quota-feasible bounded policy layout with exact updater create/version/attach/detach/delete authority, rollback, character-count evidence, and honest effective allow/deny claims.",
    "closureEvidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md:M1",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/design-remediation-1.md",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md"
    ]
  },
  {
    "id": "E-IMPL-001",
    "stage": "implementation",
    "reviewer": "/root/t082_package_e_e1a_review",
    "severity": "medium",
    "status": "fixed_pending_verification",
    "invariant": "The focused Terraform oracle must resolve and verify the exact database host and port in every one of the four bootstrap task definitions at plan time.",
    "summary": "Package C Terraform resource mocks use apply-time defaults while the bootstrap assertions run at plan time, so container definitions can remain unknown.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md",
      "infra/terraform/tests/package_c.tftest.hcl"
    ],
    "impact": "The added HCL assertions are not yet a deterministic executable oracle for the production bootstrap environment contract.",
    "requiredClosure": "Supply plan-time mock values for every resource dependency of the bootstrap container JSON, retain all-four-phase assertions, execute the focused Terraform test with pinned tooling, and obtain independent verification.",
    "closureEvidence": [
      "infra/terraform/tests/package_c.tftest.hcl",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md"
    ]
  }
]

```

## Hash-bound review inputs

### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md`

size=47768; sha256=d5258800221b15e94590161fa52acabdb04d4d8c7fabbde89b4f01923f328b7a

```text
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
| Exact IAM policy-updater principal ARN | IAM prerequisite; proof of permission to create/version/tag the exact `paprnav-terraform-deploy-pilot-supplement` policy and attach/detach only that policy on the exact deploy role, not assumed from the bootstrap user |
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
baseline is 5,011 characters and a representative generated supplement is
3,731; their 8,704-character merge exceeds AWS's non-adjustable 6,144-character
customer-managed-policy limit. The supplement is therefore a separate policy,
not a baseline replacement or merged version:
`arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`.
Retain hashes and character counts for both policies, attachment/version quota
checks, Access Analyzer results, and representative effective-policy simulation.
The broad baseline remains effective, so do not claim IAM-enforced denial of
unrelated regional resources already allowed by it. Distinguish supplement
resource/condition checks, explicit operator authorization limits, and actual
effective IAM denies. Do not grant administrator access to bypass inventory.

**M1, separately authorized IAM mutation:** the named updater creates the exact
tagged supplemental customer-managed policy when absent, or creates/sets a new
version when it already exists, then attaches only that policy to the exact
`arn:aws:iam::527257972989:role/paprnav-terraform-deploy` role. Its proof policy
must bind `CreatePolicy`, `GetPolicy`, `GetPolicyVersion`,
`ListPolicyVersions`, `CreatePolicyVersion`, `SetDefaultPolicyVersion`,
`TagPolicy`, and any separately authorized rollback deletion to the exact
supplement ARN; `AttachRolePolicy`/`DetachRolePolicy` bind the exact role and
the exact supplement through `iam:PolicyARN`. Baseline v5 and its attachment
are unchanged. Record pre/post attachments, versions, hashes and effective
permissions. Rollback detaches only the supplement and restores its prior
default version when one exists; deleting its exact non-default versions or the
new detached policy requires explicit deletion authority and zero unexpected
attachments. A partially created policy is never treated as attached authority.

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
values to the exact RDS resource. IAM tests reproduce 5,011 / 3,731 / 8,704
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

Review saved plan JSON and hash: zero services, disabled scheduler, correct
certificate and alias, exact network/WAF paths and rates, no public RDS, no
runtime master credentials, right execution/task roles, private/versioned S3,
backup/deletion controls, budget/filter/subscriber/log retention, and no durable
resource destroy/replacement. Confirm existing tag-mutability updates and new
ECR resource were absorbed with no unexpected drift. Price the actual planned
ALB/WAF/RDS/Fargate/public IPv4/logs/storage/backups/S3/ECR/restore shape using
current AWS pricing before approval; no historical estimate is current evidence.

**M6, explicit foundation apply:** approve and apply that exact fresh saved
plan, with a bounded spend window and stop authority. Record outputs (ARNs/IDs,
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
| Named IAM updater | Create/get/list/version/tag exact supplement; attach/detach exact supplement | Exact supplement policy ARN and exact deploy role with `iam:PolicyARN`; baseline unchanged; deletion separately authorized |
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

IAM rollback detaches only the exact supplemental policy, restores its prior
default version when applicable, and leaves the baseline policy and attachment
unchanged. Deletion requires separate authority and confirmation of zero
unexpected attachments. DNS/secret/version changes and drill
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

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/findings.json`

size=4051; sha256=d73c851a775f0ac288f3a00369a78e89e7daef32c75492522c2ecdc1082a5d89

```text
[
  {
    "id": "E-DESIGN-001",
    "stage": "design",
    "reviewer": "/root/t082_package_e_design_review",
    "severity": "high",
    "status": "fixed_pending_verification",
    "invariant": "The sealed fixed-phase bootstrap must connect to the exact Terraform-managed RDS instance without changing the RDS-managed secret schema.",
    "summary": "Bootstrap requires host and port inside an RDS-managed secret that does not contain them, while Terraform supplies no separate endpoint or port.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-initial.md",
      "infra/bootstrap/bootstrap.py:83-95",
      "infra/terraform/ecs_runtime.tf:42-47",
      "https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_jdbc.html"
    ],
    "impact": "All four bootstrap phases fail before connecting, blocking the manual invite cohort.",
    "requiredClosure": "Amend the design and implement a reviewed bootstrap/IaC contract that binds non-secret endpoint and port to the exact RDS resource, keeps credentials in the managed secret, adds realistic missing/mismatch tests, and refreshes image/task evidence.",
    "closureEvidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md:E1A",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/design-remediation-1.md"
    ]
  },
  {
    "id": "E-DESIGN-002",
    "stage": "design",
    "reviewer": "/root/t082_package_e_design_review",
    "severity": "high",
    "status": "closed",
    "invariant": "The IAM prerequisite must fit AWS policy quotas and be publishable and reversible by the explicitly named updater authority.",
    "summary": "The proposed merged customer-managed policy is approximately 8,704 non-whitespace characters, exceeding AWS's 6,144-character managed-policy limit.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-initial.md",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md",
      "infra/aws-iam/paprnav-terraform-deploy-policy.json",
      "scripts/generate_pilot_deploy_policy.py",
      "https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html"
    ],
    "impact": "M1 cannot publish the proposed merge; splitting the policy would require authority and rollback behavior not covered by the current design.",
    "requiredClosure": "Select and independently review a quota-feasible bounded policy layout with exact updater create/version/attach/detach/delete authority, rollback, character-count evidence, and honest effective allow/deny claims.",
    "closureEvidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md:M1",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/design-remediation-1.md",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md"
    ]
  },
  {
    "id": "E-IMPL-001",
    "stage": "implementation",
    "reviewer": "/root/t082_package_e_e1a_review",
    "severity": "medium",
    "status": "fixed_pending_verification",
    "invariant": "The focused Terraform oracle must resolve and verify the exact database host and port in every one of the four bootstrap task definitions at plan time.",
    "summary": "Package C Terraform resource mocks use apply-time defaults while the bootstrap assertions run at plan time, so container definitions can remain unknown.",
    "evidence": [
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md",
      "infra/terraform/tests/package_c.tftest.hcl"
    ],
    "impact": "The added HCL assertions are not yet a deterministic executable oracle for the production bootstrap environment contract.",
    "requiredClosure": "Supply plan-time mock values for every resource dependency of the bootstrap container JSON, retain all-four-phase assertions, execute the focused Terraform test with pinned tooling, and obtain independent verification.",
    "closureEvidence": [
      "infra/terraform/tests/package_c.tftest.hcl",
      ".ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md"
    ]
  }
]

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-remediation-1.md`

size=1798; sha256=b9f32b6ae9408808259b6191ac03cf7d70d553c01454fc3f9e217a42efd21abd

```text
# Package E design remediation review 1

## Outcome

**PASS — remediation design only.** No new finding was identified.

## Finding dispositions

- **E-DESIGN-001 — design resolved, implementation verification pending.**
  Terraform supplies the exact RDS endpoint/port while the managed secret
  supplies credentials. Override rejection, realistic tests, refreshed
  image/task evidence, and independent implementation review are mandatory.
- **E-DESIGN-002 — design resolved, implementation verification pending.**
  The exact separate supplement ARN, updater lifecycle, exact role plus
  `iam:PolicyARN` restrictions, quota gates, and rollback are coherent. The
  reviewer reproduced compact sizes 5,011 / 3,731 / 8,704; the individual
  policies fit the 6,144-character limit. Version/attachment checks and
  separately authorized deletion remain required. Existing baseline
  `Resource=*` limits are stated honestly.

Both findings remain `fixed_pending_verification` until implementation evidence
passes independent review. Source edits require the recorded design PASS, phase
advancement, and declared E1A scope. Candidate construction and AWS/provider
mutations remain blocked by later review and authorization gates. The design is
proportionate to the invite-only MVP.

## Boundary and identity

- Reviewer: `/root/t082_package_e_design_reviewer_2`
- Role: independent read-only design-remediation adversary
- Requested route: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Packet SHA-256:
  `925a3df756f124eab2dbde9c2004230f683935eefaf179433f24c3b8035e606c`
- All 13 bound inputs, embedded manifest, HEAD, and fingerprint matched.
- No files, Git state, AWS resources, secrets, or providers were mutated by the
  reviewer.


```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-implementation.md`

size=6964; sha256=f62583525e7da778669fb80febfb212cf42252073b694429c9a4b1ab62fb290c

```text
# Package E E1A implementation evidence

## Outcome

Implemented the approved pre-execution bootstrap connection and separate IAM
supplement family. No AWS/provider call, secret-value access, remote image
build/push, Git staging, or commit occurred. This is builder evidence only;
E-DESIGN-001 and E-DESIGN-002 remain `fixed_pending_verification` until the
coordinator obtains an independent implementation review.

## Model routing

- Builder runtime identity: `/root/t082_package_e_e1a_implementation`.
- Approved/requested route: GPT-5.6 Sol high for the coherent, approved
  multi-file implementation.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: authorization-sensitive IAM publication plus the privileged sealed
  bootstrap database trust boundary, with approved design and deterministic
  negative/size oracles.
- No fallback is claimed. The coordinator must record the separately assigned
  implementation reviewer identity and its exposed model/effort.

## Changed scope

- `infra/bootstrap/bootstrap.py`
  - Reads only `username` and `password` from the managed-secret document.
  - Requires `PAPRNAV_DATABASE_HOST` and `PAPRNAV_DATABASE_PORT`, validates a
    sane DNS-style host and an integer port in `1..65535`, and ignores secret
    host/port/database fields.
- `infra/terraform/ecs_runtime.tf`
  - Binds the common environment of all four fixed-phase bootstrap task
    definitions directly to `aws_db_instance.postgres.address` and `.port`.
- `scripts/generate_pilot_deploy_policy.py`
  - Keeps the baseline ARN distinct, emits the exact separately named pilot
    supplement, scopes updater lifecycle actions to that supplement, and
    scopes role attach/detach to the exact deploy role with
    `iam:PolicyARN`.
  - Emits destructive deletion authority in a separate proof policy and
    records publication quota preconditions.
- `infra/aws-iam/pilot-policy-matrix.json`
  - Mirrors separate supplement/updater/deletion authorities and states that
    the broad unchanged baseline remains effective.
- `backend/tests/test_pilot_package_c.py`
  - Adds realistic credential-only managed-secret tests, host/port negative
    and boundary cases, secret override resistance, exact Terraform source
    bindings, policy scope, quota, count, and unchanged-baseline assertions.
- `infra/terraform/tests/package_c.tftest.hcl`
  - Adds mocked RDS address/port and plan assertions for all four fixed-phase
    task definitions.
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-implementation.md`
  - This builder evidence.

No file outside the declared scope was edited. Existing Package A-D, T081/0030,
and `backend/app/models/core.py` work was preserved.

## Deterministic policy evidence

Stable fixture inputs:

- hosted zone: `Z123456789ABC`
- hostname: `pilot.example.com`
- updater: `arn:aws:iam::527257972989:role/paprnav-policy-updater`
- KMS key: `arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555`

Results:

- unchanged baseline compact characters: `5011`
- supplement compact characters: `3731`
- invalid merged compact characters: `8704`
- per-policy character limit: `6144`
- baseline file SHA-256:
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`
- supplement compact SHA-256:
  `11885bca4559c55e7dc81181ea5b59ab167903b5ef72a0571d28a6541e6cd11e`

The generator and matrix require one available role-attachment slot and, when
versioning an existing supplement, one available policy-version slot under the
five-version limit. These are publication preconditions, not claims about live
quota state. Deletion of exact non-default versions or the exact detached
supplement is separately authorized and requires a zero-unexpected-attachment
operator check; ordinary updater authority contains no delete action.

## Focused verification

1. `.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py`
   - Not run: exit `127`; the repository-root `.venv` does not exist.
2. `python3 -m pytest -q backend/tests/test_pilot_package_c.py`
   - Not run: exit `1`; system Python has no `pytest` module.
3. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py`
   - PASS: `25 passed, 2 skipped, 81 warnings in 0.17s`.
   - Skips were the existing optional Terraform-plan JSON oracle and disposable
     PostgreSQL test because their opt-in environment inputs were absent.
4. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py -k 'admin_connection or bootstrap_task_definitions or generated_supplement' --disable-warnings`
   - PASS: `16 passed, 11 deselected, 1 warning in 0.07s`.
5. `backend/.venv/bin/python -m py_compile infra/bootstrap/bootstrap.py scripts/generate_pilot_deploy_policy.py backend/tests/test_pilot_package_c.py`
   - PASS.
6. `python3 -m json.tool infra/aws-iam/pilot-policy-matrix.json >/dev/null`
   - PASS.
7. `python3 scripts/generate_pilot_deploy_policy.py --hosted-zone-id Z123456789ABC --pilot-hostname pilot.example.com --operator-updater-principal-arn arn:aws:iam::527257972989:role/paprnav-policy-updater --secrets-manager-kms-key-arn arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555 --output /private/tmp/t082-e1a-policy-fixture.json`
   - PASS: `statementCount=15`, status `pass`.
8. Compact JSON count/hash Python fixture over the unchanged baseline and the
   generated supplement.
   - PASS: `5011 / 3731 / 8704` and hashes recorded above.
9. `git diff --check`
   - PASS.

## Deviations and unavailable checks

- `terraform test` was not run because neither `terraform` nor `tofu` is
  installed and no local executable was available. The Terraform mock test was
  added for the coordinator/reviewer to run where the existing pinned tooling
  is available. The focused Python source oracle passed and binds the literal
  RDS expressions; no substitute Terraform PASS is claimed.
- Python `hcl2` parsing was unavailable (`No module named 'hcl2'`); no HCL parse
  PASS is claimed.
- The optional disposable PostgreSQL test did not run because
  `PAPRNAV_PACKAGE_C_TEST_POSTGRES_URL` was absent. The non-database bootstrap
  connection contract tests passed.
- No refreshed image was built or remote task definition inspected in this
  bounded source implementation. Those candidate/image checks remain after
  independent implementation review and under their later authorization gate.
- No design deviation or newly discovered source consumer required expanding
  the declared scope.

## Review handoff

The independent reviewer should inspect staged, unstaged, and untracked files;
verify the managed-secret/environment provenance through every bootstrap phase;
run the Terraform mock test with pinned local tooling; reproduce the compact
counts and baseline hash; and verify exact updater, attachment, rollback, and
deletion scope. The builder does not close either finding or attest review.

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md`

size=3046; sha256=d05cb5921f283e7e9ce7d9705da875358aa7faaa4079b23db904870452c72330

```text
# Package E E1A independent implementation review

## Outcome

**FAIL.** One bounded verification defect remains. No production bootstrap or
IAM lifecycle defect was found.

## Finding

### E-IMPL-001 — Medium — Terraform bootstrap assertions depend on unknown plan values

The required oracle must verify all four rendered task definitions.
`infra/terraform/tests/package_c.tftest.hcl` uses a `command = plan` run, but
its resource mocks do not set `override_during = plan`. RDS address/master-secret
ARN and application/first-admin secret ARNs can therefore remain unknown, making
`container_definitions` and both assertions indeterminate. This is a static
finding, not an executed Terraform failure.

Required closure: provide plan-time values for every resource dependency of the
container JSON, retain assertions over all four phases, and record the focused
execution result when tooling is available.

## Prior finding dispositions

- **E-DESIGN-001:** production source remediation verified; retain
  `fixed_pending_verification` until E-IMPL-001 closes. All four callers use
  `admin_connection`; credentials come only from the managed secret and
  endpoint/port from Terraform environment. Secret location fields cannot
  override them. Runtime environment overrides remain an M8 operator
  prohibition, not an IAM-enforced protection from the broad deploy role.
- **E-DESIGN-002:** independently verified and eligible for closure. Generator,
  matrix, tests, exact ARNs, `iam:PolicyARN` restrictions, deletion separation,
  quotas, rollback preconditions, and baseline limitations agree.

## Verification and boundary

- Focused pytest: 19 passed, 8 deselected.
- Independent synthetic counterexamples: 30 passed for credentials, hosts,
  ports, secret override attempts, and all four phase entry paths.
- `git diff --check` passed; index was empty; all six manifest hashes matched.
- Baseline file was byte-identical to `HEAD`, SHA-256
  `da2420f54b0a24623eebc522de4cffb8a7969e3d22f75abae11de44884b8a78e`.
- Compact counts reproduced as 5,011 / 3,731 / 8,704. Baseline/supplement/merge
  compact hashes were `dc7e543afbd7b42f459118591499e9d11f7b5b1be29f8a93e2bf22a8f722083d`,
  `11885bca4559c55e7dc81181ea5b59ab167903b5ef72a0571d28a6541e6cd11e`,
  and `ca3a137632d4f678ef50b67e5258b8a66b5cfee5393b0f98655ba480c961aa31`.
Terraform execution, live IAM effectiveness/quotas, PostgreSQL execution,
refreshed image, and deployed task evidence remain unverified.

Reviewer inspected actual staged/unstaged/untracked inventory, the six scope
files, bootstrap consumers, RDS/task configuration, migration boundary,
baseline IAM, and execution/rollback contract. No repository or external state
was mutated.

## Identity and packet

- Reviewer: `/root/t082_package_e_e1a_review`
- Requested route: GPT-6 Astra high
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Builder: `/root/t082_package_e_e1a_implementation`
- Packet SHA-256:
  `03a78436169dff812099a258c7cdd60910bca05abb22839448ef68da427e333b`

```
### `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md`

size=6824; sha256=0b9a08ca59847050dc9fe0c879ccee10a5b22a68ac86b3d46b9668b23c06cdf4

```text
# Package E E1A remediation 1

## Outcome

Remediated only E-IMPL-001. The focused `command = plan` Terraform run now
supplies plan-time values for every resource attribute that feeds the four
bootstrap `container_definitions`. The production expressions, direct
`aws_db_instance.postgres.address` / `.port` assertions, and fixed-command
assertion across all four phases are unchanged. No application or Terraform
source behavior changed.

This is builder evidence, not independent verification or finding closure. The
ledger remains unchanged for the coordinator and separate reviewer.

## Model routing

- Builder runtime identity: `/root/t082_package_e_e1a_remediation_1`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: first substantive failed implementation review; bounded remediation
  of a deterministic Terraform plan-time oracle gap.
- No fallback is claimed. Builder/reviewer separation remains required.

## Changed scope

- `infra/terraform/tests/package_c.tftest.hcl`
  - Replaced the apply-time RDS type mock with run-scoped
    `override_during = plan` overrides covering the complete resource-derived
    bootstrap JSON graph.
  - Added a plan-known valid `aws_iam_policy_document` data mock after the first
    real Terraform execution showed that targeted IAM role schema validation
    otherwise failed before reaching the container assertions.
- `.ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md`
  - Records the dependency audit, implementation, and verification evidence.

No other file was edited, staged, or committed by this builder. No AWS call,
secret access, network access, or provider operation occurred.

## Complete bootstrap container JSON dependency audit

The four `aws_ecs_task_definition.bootstrap` instances are `migration`,
`reference`, `runtime-role`, and `first-admin`.

| Consumer phases | Resource-derived JSON attribute | Exact plan mock |
| --- | --- | --- |
| all four | `aws_db_instance.postgres.address` | `paprnav-bootstrap-plan.invalid` |
| all four | `aws_db_instance.postgres.port` | `5432` |
| all four | `aws_db_instance.postgres.db_name` | `paprnav` |
| all four | `aws_db_instance.postgres.master_user_secret[0].secret_arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-package-c-plan` |
| all four | `aws_cloudwatch_log_group.bootstrap.name` | `/paprnav/package-c/bootstrap-plan` |
| `runtime-role` | `aws_secretsmanager_secret.database_url.arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/app-database-plan-000001` |
| `first-admin` | `aws_secretsmanager_secret.first_admin_password.arn` | `arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/first-admin-plan-000001` |

The remaining JSON inputs are plan-known literals, variables, or `each.key`:
the image digest, container name, essential flag, fixed phase command, common
environment literals, AWS region, first-admin identity fields, empty secrets,
read-only root flag, init flag, log driver, and stream prefix. Task and execution
role ARNs are task-definition attributes outside `container_definitions`; they
cannot make the decoded JSON assertion unknown.

The host assertion still compares every rendered environment directly with
`aws_db_instance.postgres.address`; the port assertion still compares it with
`tostring(aws_db_instance.postgres.port)`. The command assertion still iterates
the same four-instance resource map and requires the sole command to equal each
phase key. No assertion was weakened and the run remains `command = plan`.

All mock identifiers are inert test values. The host uses the reserved
`.invalid` top-level domain and no secret value is represented.

## Focused verification

1. `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q backend/tests/test_pilot_package_c.py -k bootstrap_task_definitions --disable-warnings`
   - PASS: `1 passed, 26 deselected, 1 warning in 0.06s`.
2. `python3 -m json.tool .ai/review-runs/T082-AWS-INVITE-PILOT-E/findings.json >/dev/null`
   - PASS.
3. Balanced-delimiter and exact override-structure check over
   `infra/terraform/tests/package_c.tftest.hcl`.
   - PASS: braces, brackets, and parentheses balanced; four
     `override_during = plan` blocks and all four exact resource targets are
     present.
   - Pygments' `TerraformLexer` reports error tokens for existing Terraform
     test-language keywords and is not a usable full HCL parser here; no parser
     PASS is claimed.
4. `git diff --check --no-index /dev/null infra/terraform/tests/package_c.tftest.hcl`
   - PASS for whitespace (the expected diff exit for an untracked file is
     ignored only after `--check` reports no whitespace error).
5. `git diff --check --no-index /dev/null .ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md`
   - PASS for whitespace under the same untracked-file convention.

## Terraform execution evidence

The builder found no local Terraform/OpenTofu CLI. The coordinator then
downloaded Terraform 1.15.8 for Darwin arm64 into a temporary directory from
the official HashiCorp release host. The archive SHA-256
`f210110c5698b94d803a7a63cdb0251b5455c150841478808e2bbb343f95ed68`
matched the official 1.15.8 checksum file. Nothing was installed into the
repository or a system path.

The first sandboxed test reached provider startup but could not bind its local
Unix socket (`operation not permitted`); this was a sandbox failure, not a test
result. The first permitted local run then exposed a real mock dependency:
targeting the task definitions also plans their IAM roles, and the mocked
`aws_iam_policy_document.json` was not valid JSON. The coordinator added one
plan-known valid, empty policy-document mock. This changes test infrastructure
only and does not weaken the bootstrap assertions.

Final command:

`TF_IN_AUTOMATION=1 CHECKPOINT_DISABLE=1 AWS_EC2_METADATA_DISABLED=true /private/tmp/paprnav-terraform.UdPxeL/terraform -chdir=infra/terraform test -filter=tests/package_c.tftest.hcl -no-color`

- PASS: `13 passed, 0 failed`.
- `bootstrap_database_location_is_bound_to_rds` passed at plan time.
- Terraform emitted only expected targeting warnings from the pre-existing
  bounded test design.
- The mock provider made no AWS call and no credentials or secret values were
  supplied.

The coordinator reran the focused Python source oracle after the additional
mock: `1 passed, 26 deselected`. `git diff --check` also passed.

## Review handoff

The independent reviewer should reproduce or inspect the focused Terraform
result, confirm all four plan assertions resolve, inspect the actual working
tree, and disposition E-IMPL-001.

Coordinator extension model/effort: `model not exposed by runtime` / `effort
not exposed`. No AWS/provider/secret mutation, staging, or commit occurred.

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
### `.ai/PILOT_RELEASE_BOUNDARY.md`

size=6653; sha256=41e01eda7ad31da31a74d920c1b1b6b267f2ca25d34a5acc69bf3d8ca437dad3

```text
# Pilot release boundary

The invite-only AWS pilot is built from an explicit reviewed Git commit. It is
not built from the current working directory. Before packaging a candidate,
run:

```bash
python3 scripts/verify_pilot_release_boundary.py --ref <commit>
```

The verifier reads the commit tree named by `--ref`, applies
`.ai/pilot-release-boundary-v1.json`, and fails unless:

- the approved pilot baseline is an ancestor;
- the migration graph has the single reviewed head `20260913_0029`;
- the exact 44-file migration authority inventory and every SHA-256 match the
  reviewed policy, with no duplicate metadata, missing predecessor, graph cycle,
  extra root, or unsupported dependency/branch metadata;
- the reviewed `backend/app/models/core.py` blob is unchanged; and
- no T081 Slice 4B or unreviewed 0030 artifact is present.

The authority inventory includes every committed file under
`backend/app/db/migrations/`, regardless of extension: all 29 revision sources,
all three SQL sidecars executed by 0028/0029, `env.py`, `script.py.mako`, and the
directory's remaining files. It also includes `backend/alembic.ini` and the
minimal repository support modules used by `env.py`: `app/core/config.py`,
`app/db/base.py`, `app/models/core.py`, and their package `__init__.py` files.
The separate expected-head and protected-model checks remain mandatory.

All inventory names and hashes come from baseline commit
`19fe8e2e170687ed65deed78cb1af99d60f601e9`, except the explicitly recorded
`app/core/config.py` target amendment containing the Package A V4 gates and
Package B pilot trust-boundary settings. Its exact SHA-256 is
`a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4` and must
receive independent implementation approval. The baseline therefore fails with
exactly that configuration difference. A mocked candidate containing the
approved target bytes passes; this is not evidence that a release commit
already exists. Run the verifier on the eventual reviewed candidate commit
before image construction.

Additions, removals, renames, and content changes in these source inputs require
an explicit reviewed policy amendment. This verifier proves source inventory,
hashes, and graph correctness. A source pass does not prove import isolation
when running from the full checkout.
Git names are enumerated as raw NUL-delimited bytes, compared as bytes, and
decoded with `surrogateescape` only for ASCII-escaped JSON output. Quoted,
tab/newline, non-ASCII, and non-UTF-8 names cannot bypass the authority or T081
prefix checks.

Build the migration execution context separately:

```bash
backend/.venv/bin/python scripts/build_pilot_migration_context.py build --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
backend/.venv/bin/python scripts/build_pilot_migration_context.py verify --ref <reviewed-commit> --destination /private/tmp/paprnav-migration-<unique>
```

The destination and every ancestor must be real directories with no symlink
traversal; the destination itself must not exist. The builder resolves the ref
once, reads Git blobs and modes at that commit, validates all inputs before
creation, and maps `backend/alembic.ini` to `alembic.ini` and each approved
`backend/app/...` source to `app/...`. It copies no arbitrary checkout input,
regardless of current or future driver/import name. In particular, `.env`,
bytecode, tests, and unapproved replacement modules never enter the context.

The exact output is 44 regular files plus `migration-context.json`. Each entry
records source/destination paths, Git mode, byte length, and SHA-256. The
manifest records the exact source commit and a deterministic SHA-256 over
canonical JSON without the digest field. Source mode must be `100644`; context
files are `0444` and directories `0555`. Verification compares the manifest and
every file byte back to the reviewed commit/policy and rejects extra/missing
files or directories, symlinks, hard links, and mode drift. Unsafe, duplicate,
or non-UTF-8 manifest paths fail. A failed write leaves an incomplete directory
for inspection; it cannot be reused or pass verification.

The script's local `run` mode requires an explicit nonempty `DATABASE_URL`,
verifies the context before/after execution, forces `PAPRNAV_DISABLE_DOTENV=1`
and `PYTHONDONTWRITEBYTECODE=1`, and launches `python -I -B -m alembic` from the
context with its absolute configuration path and fixed head `20260913_0029`.
`-B` is explicit because `-I` ignores Python environment variables. Runtime
credentials are never recorded in the context/manifest or passed as command
arguments; child output is suppressed because driver errors may contain URLs.
The local wrapper needs repository access for verification and is not the
production task entrypoint.

Package A's execution oracle runs the actual committed `env.py` through Alembic
and actual SQLAlchemy `engine_from_config`, stopping after driver loading and
before any database connection. Both `psycopg.py` and `psycopg/__init__.py`
sentinels execute in the vulnerable checkout control. In the sealed control,
the real installed psycopg, Alembic, and SQLAlchemy resolve to the interpreter's
canonical site-packages, and no checkout source directory is on `sys.path`.
The local virtual environment is located beneath the repository; only its
exact installed site-packages root is allowed, never application/editable
source paths. Output remains unchanged and contains no bytecode after execution.

Package E must bind the dedicated migration image, interpreter, installed
dependencies/startup hooks, read-only context, command/environment, image labels,
and task definition to an immutable image digest. It must prove the application
checkout is absent from the task filesystem/import path and cannot reenter via
mounts or overrides, require the migration-only runtime secret, and prove a fresh
PostgreSQL upgrade. These local tests do not establish container isolation,
package provenance, database migration success, or AWS execution readiness.

`PAPRNAV_ENV=pilot` defaults the pilot-wide V4 route gate off. Startup also
fails if that gate or any narrower V4 write, projection, draft, or decision
gate is enabled. Every `/api/v1/ads/**/v4/**` request then receives a generic
404 before authentication or request-body parsing. Local and test environments
retain their existing V4 behavior unless the route gate is explicitly false.

Passing this check is necessary release evidence, not authorization to deploy.
It does not validate an image digest, modify AWS, migrate a database, or close
the preserved T081 review run. Those remain later reviewed pilot gates.

```
### `.ai/MODEL_ROUTING.md`

size=10194; sha256=043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261

```text
# Paprnav model-routing policy

This policy is mandatory for every Codex task in this repository. Route each
meaningful phase independently; do not choose one model for an entire task when
later phases have different risk or review needs.

## Routing tiers

Choose the highest tier triggered by the work. Complexity, safety impact, and
review history override convenience or expected speed.

| Work | Preferred routing |
| --- | --- |
| Mechanical, localized, low-risk edits with an obvious oracle and limited blast radius | GPT-5.6 Luna (`gpt-5.6-luna`) or GPT-5.6 Terra (`gpt-5.6-terra`), medium |
| Coherent multi-file implementation whose design is already approved | GPT-5.6 Sol (`gpt-5.6-sol`), high |
| Schema or migration design; authorization; regulatory or safety semantics; invariant synthesis; adversarial review; closure review | GPT-6 Astra (`gpt-6-astra`), high or xhigh |

Use xhigh for interacting invariants, ambiguous trust boundaries, concurrency or
rollback reasoning, closure after substantive findings, or when high effort has
not resolved the review class. Use high for a well-framed problem with explicit
invariants and a strong test oracle.

Low-risk routing applies only when all of these are true:

- the change is localized and mechanically checkable;
- failure cannot alter authorization, regulatory meaning, safety behavior,
  persisted schema, audit evidence, billing/provider choice, or a public
  contract;
- rollback is straightforward; and
- no review-history escalation below applies.

When a phase mixes tiers, use the highest triggered tier or split it into
bounded phases with explicit handoffs. An approved design is required before
routing coherent high-risk implementation to Sol; design and invariant work
remain Astra work.

## Risk-adjusted planning and review cadence

For multi-phase work, score each remaining package independently from 1 (low)
to 5 (high) on risk, technical complexity, dependency centrality, and
uncertainty. Record dependencies, downstream consumers, reversibility, the
strength of deterministic oracles, design-approval state, and relevant review
history. File count and apparent edit size are not risk scores: a one-line ACL
or migration change can be high-risk, while a large generated rewrite can be
mechanical.

Optimize expected total effort, including likely rework and review cost. Route
to Astra earlier when ambiguity, centrality, or repeated findings make a Sol
pass likely to require another implementation/review loop. Conversely, use
Terra medium or Sol medium for deterministic work mechanically derived from an
approved authority, even when it touches many generated files.

Review once at each meaningful invariant-bearing family boundary:

- review a coherent design together with its generated contracts, manifests,
  hashes, counts, and deterministic validator results;
- do not create standalone reviewer turns for each generated artifact or for
  mechanical implementation that stays within the approved design;
- request one implementation review after the coherent family and its full
  positive/negative evidence are complete;
- repeat a review or broad test only when changed dependencies can invalidate
  prior evidence; and
- retain independent design, implementation, and closure review for high-risk
  schema, migration, authorization, regulatory, IAM, or invariant work.

If an agent has completed the technical analysis but continues expanding prose,
direct it to publish a compact reviewable artifact and return. Drafting length
is not additional verification.

## Review-history escalation

Count substantive failures within the current finding family or review loop.
Formatting-only feedback and infrastructure/transient failures do not count.

1. After the first substantive failed review, increase reasoning effort for the
   next pass and reassess whether the issue is a local defect, a missing
   invariant, a design error, an oracle gap, or a scope omission.
2. After the second failed review, or whenever the same finding family recurs,
   route the next pass to GPT-6 Astra and stop counterexample-by-counterexample
   patching. Restate the complete invariant and close the coherent family with
   its positive and negative matrix.
3. After the third unsuccessful loop, pause implementation. Identify and record
   the missing invariant, architecture decision, or shared test oracle before
   further code changes. Resume only after that gap is resolved and, for work
   governed by the adversarial-review process, independently reviewed.

Examples:

- A first concurrency-review failure moves the next pass to higher effort and
  reclassifies the issue as lock ordering, transaction isolation, or test
  coverage before editing.
- A second malformed-row counterexample in the same schema family moves the
  work to Astra and replaces one-off trigger patches with a complete union and
  corruption matrix.
- A third reconstruction mismatch stops implementation until the canonical
  mapping invariant and shared oracle are explicit.

Escalation never authorizes broader product scope or bypasses an approval gate.

## Builder and reviewer separation

Builder/reviewer separation is mandatory regardless of model. A model upgrade
does not make self-review independent. Qualifying work must still follow
`AGENTS.md`, `.ai/REVIEW_PROCESS.md`, and the repository-local
`adversarial-review` skill.

- Assign design, implementation, and closure adversaries as separate read-only
  project subagents unless the coordinator explicitly assigns a later fix task.
- Do not let the builder attest its own review stage, even when builder and
  reviewer would use the same model family.
- Record the actual runtime reviewer identity; a model name is not an identity.

## Dynamic availability and fallbacks

Use the preferred model when it is available. Otherwise choose the closest
available capability tier that can safely perform the phase:

1. For Astra-routed work, prefer the strongest available model at high or xhigh
   and preserve the mandatory independent-review gates. If no available model
   is adequate for the risk, pause and report the limitation.
2. For Sol-routed work, fall back to Astra at high, or to the strongest
   available implementation model at high when Astra is unavailable.
3. For Luna/Terra-routed work, use the other model at medium, then the closest
   available general implementation tier at medium.

Never silently claim or imply use of an unavailable model. In the phase notice
and any review artifact, record the actual fallback model and the reason. If the
runtime does not expose its model, write exactly `model not exposed by runtime`
rather than inferring it. If effort is not exposed, say `effort not exposed`.

## Required status commentary

At the start of every meaningful phase, report the role, exact model, reasoning
effort, and routing trigger. Report again whenever the role, model, or effort
changes. A meaningful phase includes framing/design, implementation, focused
verification, adversarial review, remediation after a failed review, and final
closure. Do not repeat the notice during routine progress updates when none of
those fields changed.

Use exactly this shape:

```text
Model routing: <role> → <exact model> (<effort>). Trigger: <brief reason>.
```

For a fallback, include it in the trigger, for example:

```text
Model routing: implementation builder → gpt-5.6-terra (high). Trigger: approved multi-file implementation; gpt-5.6-sol unavailable, closest implementation fallback.
```

Identify delegated builder and reviewer models in coordinator commentary. When
a delegated runtime does not expose its model, use the required unavailable
metadata wording rather than the requested model name.

## Review artifacts and closure

When known, every adversarial-review artifact must record:

- builder runtime identity, actual model, and effort;
- reviewer runtime identity, actual model, and effort;
- the routing trigger; and
- any fallback, unavailability, or unexposed runtime metadata.

Use a `## Model routing` section in each new design, implementation, remediation,
and closure-review artifact. Use a `## Model assignments` section in
`closure.md` to summarize the full run. These sections are the authoritative,
human-readable evidence locations; do not rely on task-local commentary or
model-selection requests as proof of the runtime used.

The independent closure reviewer must verify these sections against the phase
notices, returned runtime identities, and known delegation metadata. Missing,
inconsistent, inferred, or silently substituted model/effort evidence is a
closure blocker even if `validate-review-run.py` otherwise passes. Record
`model not exposed by runtime` or `effort not exposed` when applicable; that is
valid evidence of unavailable metadata, not permission to guess.

Do not rewrite historical attestations merely because model metadata was not
previously required. New review reports and closure evidence must be accurate
about what the runtime exposed. Final closure must summarize model assignments
for design, implementation, remediation, implementation review, and closure
review, including fallbacks.

For a review run already in progress when this policy is adopted, completed
reports are historical for this purpose even if they are still uncommitted. Do
not rewrite those immutable reports. Instead, bind this policy and the current
working tree into a fresh closure packet, summarize every known, unexposed, and
requested assignment in `closure.md`, and obtain a compliant independent
closure re-attestation before the files share a commit.

## Delegation mechanics

Use project subagents for bounded model-specific work when repository policy
and the active task permit delegation. Give each subagent one coherent role,
explicit scope, requested model and effort, and required evidence. Use the
repository's subagent mechanism so work remains attached to the current task;
do not create user-visible tasks merely to switch models.

The coordinator remains responsible for integrating results, checking actual
runtime metadata, preserving the working tree, and enforcing review gates.

```

## Changed-file manifest

```json
{
  "taskId": "T082-AWS-INVITE-PILOT-E",
  "stage": "implementation",
  "generatedAt": "2026-09-19T23:02:24+00:00",
  "baseRef": "HEAD",
  "head": "19fe8e2e170687ed65deed78cb1af99d60f601e9",
  "scopePaths": [
    "infra/bootstrap/bootstrap.py",
    "infra/terraform/ecs_runtime.tf",
    "scripts/generate_pilot_deploy_policy.py",
    "infra/aws-iam/pilot-policy-matrix.json",
    "backend/tests/test_pilot_package_c.py",
    "infra/terraform/tests/package_c.tftest.hcl"
  ],
  "scopeFingerprint": "e0628f9566074128e50e9a9d50bfe12f4f85c6175483af52b050a633b30c8d8e",
  "files": [
    {
      "path": "backend/tests/test_pilot_package_c.py",
      "status": "??",
      "size": 37372,
      "sha256": "bd91ffa5b6c2673d72533d4da5392ee2cb9efbd3700d39714fd1cfdb17c647f8",
      "readStatus": "readable"
    },
    {
      "path": "infra/aws-iam/pilot-policy-matrix.json",
      "status": "??",
      "size": 4392,
      "sha256": "fdad7b377c87dc8bd893dc1c58ef21cbfa42bf5338f841dd59f23d1bab2b8690",
      "readStatus": "readable"
    },
    {
      "path": "infra/bootstrap/bootstrap.py",
      "status": "??",
      "size": 19625,
      "sha256": "0156bcf3f1c6049c36b188585d2ec079224ac3b076f989e68e951d365691d121",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/ecs_runtime.tf",
      "status": " M",
      "size": 16003,
      "sha256": "a26e117cec908e595a459332133247c019e4bf4e8e44d0f2177a0f4ad9590650",
      "readStatus": "readable"
    },
    {
      "path": "infra/terraform/tests/package_c.tftest.hcl",
      "status": "??",
      "size": 11432,
      "sha256": "ff2289ddcefc8a5cd9b944827b456bfac71005c7681aa79ae7f974170b1fbffe",
      "readStatus": "readable"
    },
    {
      "path": "scripts/generate_pilot_deploy_policy.py",
      "status": "??",
      "size": 8437,
      "sha256": "51b81d7e60011056ab80735f6073570125b7a103782835314ef785da15d2c39e",
      "readStatus": "readable"
    }
  ],
  "reviewInputs": [
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/decision.md",
      "status": "review_input",
      "size": 47768,
      "sha256": "d5258800221b15e94590161fa52acabdb04d4d8c7fabbde89b4f01923f328b7a",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/findings.json",
      "status": "review_input",
      "size": 4051,
      "sha256": "d73c851a775f0ac288f3a00369a78e89e7daef32c75492522c2ecdc1082a5d89",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-design-remediation-1.md",
      "status": "review_input",
      "size": 1798,
      "sha256": "b9f32b6ae9408808259b6191ac03cf7d70d553c01454fc3f9e217a42efd21abd",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-implementation.md",
      "status": "review_input",
      "size": 6964,
      "sha256": "f62583525e7da778669fb80febfb212cf42252073b694429c9a4b1ab62fb290c",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/adversarial-implementation-e1a-initial.md",
      "status": "review_input",
      "size": 3046,
      "sha256": "d05cb5921f283e7e9ce7d9705da875358aa7faaa4079b23db904870452c72330",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-E/e1a-remediation-1.md",
      "status": "review_input",
      "size": 6824,
      "sha256": "0b9a08ca59847050dc9fe0c879ccee10a5b22a68ac86b3d46b9668b23c06cdf4",
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
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C-ACM-AMENDMENT/closure.md",
      "status": "review_input",
      "size": 3803,
      "sha256": "43f945cba5a3ee21de96ea36100d3fae190c91ea4ed335e96da75a1a31deb7f2",
      "readStatus": "readable"
    },
    {
      "path": ".ai/PILOT_RELEASE_BOUNDARY.md",
      "status": "review_input",
      "size": 6653,
      "sha256": "41e01eda7ad31da31a74d920c1b1b6b267f2ca25d34a5acc69bf3d8ca437dad3",
      "readStatus": "readable"
    },
    {
      "path": ".ai/MODEL_ROUTING.md",
      "status": "review_input",
      "size": 10194,
      "sha256": "043890c6138ba45f88dcb8a4ea209d288f4a8e8625cf60d9127408c1ff240261",
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
      "path": ".ai/pilot-package-c-context-v1.json",
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
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-closure-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/adversarial-implementation-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/aws-readonly-preflight.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/package-c-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-C/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-closure-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-design-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-design-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/adversarial-implementation-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/design-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D-PRIVACY-AMENDMENT/state.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-final.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-closure-remediation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-design-closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-design-inheritance.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-initial.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/adversarial-implementation-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/closure.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/decision.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/findings.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/manifest.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-implementation.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-1.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-2.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/package-d-remediation-3.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/review-packet.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/review-recording-delta.md",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/reviews.json",
      "status": "??"
    },
    {
      "path": ".ai/review-runs/T082-AWS-INVITE-PILOT-D/state.json",
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
      "path": "backend/Dockerfile",
      "status": " M"
    },
    {
      "path": "backend/app/api/deps.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/admin.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/aircraft.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/auth.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/ingestion.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/logbook_entries.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/api/routes/uploads.py",
      "status": " M"
    },
    {
      "path": "backend/app/core/config.py",
      "status": " M"
    },
    {
      "path": "backend/app/core/http_protocol.py",
      "status": "??"
    },
    {
      "path": "backend/app/core/request_context.py",
      "status": "??"
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
      "path": "backend/app/schemas/observability.py",
      "status": " M"
    },
    {
      "path": "backend/app/scripts/revoke_auth_sessions.py",
      "status": "??"
    },
    {
      "path": "backend/app/scripts/run_ocr_feasibility.py",
      "status": " M"
    },
    {
      "path": "backend/app/services/ad_v4_acceptance_persistence_contract.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/ingestion.py",
      "status": " M"
    },
    {
      "path": "backend/app/services/invitations.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/pilot_achievements.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/pilot_summary.py",
      "status": "??"
    },
    {
      "path": "backend/app/services/session_revocation.py",
      "status": "??"
    },
    {
      "path": "backend/pilot_server.py",
      "status": "??"
    },
    {
      "path": "backend/requirements.lock",
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
      "path": "backend/tests/test_pilot_package_d.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_privacy.py",
      "status": "??"
    },
    {
      "path": "backend/tests/test_pilot_release_boundary.py",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.dockerignore",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/.env.example",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/Dockerfile",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/next.config.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package-lock.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/package.json",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(auth)/register/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": " M"
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/pilot-ocr-summary.ts",
      "status": "??"
    },
    {
      "path": "frontend/paprnav-frontend/tests/pilot-observability.test.mjs",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/Dockerfile",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/grant-manifest.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/reference-data.json",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.in",
      "status": "??"
    },
    {
      "path": "infra/bootstrap/requirements.lock",
      "status": "??"
    },
    {
      "path": "infra/terraform/database.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/load_balancer.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/main.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/network.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/outputs.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/variables.tf",
      "status": " M"
    },
    {
      "path": "infra/terraform/versions.tf",
      "status": " M"
    },
    {
      "path": "scripts/build_pilot_migration_context.py",
      "status": "??"
    },
    {
      "path": "scripts/build_pilot_release_context.py",
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
  "outOfScopeReason": "Implementation re-review is limited to the complete approved E1A family and E-IMPL-001 remediation. Existing Package A-D and preserved T081/0030 dirty-tree files are inherited evidence or intentionally excluded; reviewer must inspect relevant surrounding consumers and report dependency omissions."
}
```

## Diff against base

```diff
diff --git a/infra/terraform/ecs_runtime.tf b/infra/terraform/ecs_runtime.tf
index 03a8b85..036bae0 100644
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
@@ -9,33 +8,83 @@ data "aws_iam_policy_document" "ecs_task_assume_role" {
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
+    { name = "PAPRNAV_DATABASE_HOST", value = aws_db_instance.postgres.address },
+    { name = "PAPRNAV_DATABASE_PORT", value = tostring(aws_db_instance.postgres.port) },
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
@@ -53,29 +102,29 @@ resource "aws_iam_role" "worker_task" {
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
 
@@ -87,36 +136,15 @@ resource "aws_iam_role_policy" "api_task" {
 
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
@@ -127,33 +155,50 @@ resource "aws_iam_role_policy" "worker_task" {
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
@@ -162,36 +207,23 @@ resource "aws_ecs_task_definition" "api" {
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
@@ -200,38 +232,23 @@ resource "aws_ecs_task_definition" "frontend" {
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
@@ -240,79 +257,125 @@ resource "aws_ecs_task_definition" "worker" {
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
@@ -327,27 +390,17 @@ resource "aws_iam_role" "worker_scheduler" {
 
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
@@ -363,27 +416,21 @@ resource "aws_iam_role_policy" "worker_scheduler" {
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

```

## Untracked text files

### `backend/tests/test_pilot_package_c.py`

size=37372; sha256=bd91ffa5b6c2673d72533d4da5392ee2cb9efbd3700d39714fd1cfdb17c647f8; truncated=false

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
                    }
                )
            }

    captured: dict[str, str] = {}

    def run(*_: object, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs["env"])  # type: ignore[arg-type]
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setattr(bootstrap.subprocess, "run", run)
    bootstrap.run_migration(Secrets())
    assert "%%" in captured["DATABASE_URL"]
    config = Config(str(REPO_ROOT / "backend/alembic.ini"))
    config.set_main_option("sqlalchemy.url", captured["DATABASE_URL"])
    parsed = make_url(config.get_section(config.config_ini_section)["sqlalchemy.url"])
    assert parsed.password == password


def test_admin_connection_uses_only_managed_credentials_and_terraform_endpoint(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "pilot-db.example.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", "paprnav")
    connection = bootstrap.admin_connection(Secrets())
    assert connection == {
        "host": "pilot-db.example.internal",
        "port": 5432,
        "dbname": "paprnav",
        "user": "paprnav_admin",
        "password": "secret",
        "sslmode": "require",
    }


@pytest.mark.parametrize("host", [None, "", " ", "https://db.internal", "db..internal"])
def test_admin_connection_rejects_missing_blank_or_invalid_host(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    host: str | None,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    if host is None:
        monkeypatch.delenv("PAPRNAV_DATABASE_HOST", raising=False)
    else:
        monkeypatch.setenv("PAPRNAV_DATABASE_HOST", host)
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    with pytest.raises(bootstrap.BootstrapError, match="(required environment|database host)"):
        bootstrap.admin_connection(Secrets())


@pytest.mark.parametrize(
    ("port", "message"),
    [
        (None, "required environment"),
        ("", "required environment"),
        ("postgres", "port environment input is invalid"),
        (" 5432", "port environment input is invalid"),
        ("0", "outside 1..65535"),
        ("65536", "outside 1..65535"),
    ],
)
def test_admin_connection_rejects_missing_invalid_or_out_of_range_port(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    port: str | None,
    message: str,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "paprnav_admin", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    if port is None:
        monkeypatch.delenv("PAPRNAV_DATABASE_PORT", raising=False)
    else:
        monkeypatch.setenv("PAPRNAV_DATABASE_PORT", port)
    with pytest.raises(bootstrap.BootstrapError, match=message):
        bootstrap.admin_connection(Secrets())


def test_admin_connection_rejects_wrong_username(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({"username": "postgres", "password": "secret"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    with pytest.raises(bootstrap.BootstrapError, match="wrong username"):
        bootstrap.admin_connection(Secrets())


def test_admin_connection_secret_location_fields_cannot_override_environment(
    bootstrap: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Secrets:
        def get_secret_value(self, **_: str) -> dict[str, str]:
            return {"SecretString": json.dumps({
                "username": "paprnav_admin",
                "password": "secret",
                "host": "attacker.example.net",
                "port": 1,
                "dbname": "other",
            })}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin-secret")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", "db.internal")
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", "5432")
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", "paprnav")
    connection = bootstrap.admin_connection(Secrets())
    assert (connection["host"], connection["port"], connection["dbname"]) == (
        "db.internal",
        5432,
        "paprnav",
    )


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


def test_bootstrap_task_definitions_bind_exact_rds_location_without_overrides() -> None:
    terraform = (REPO_ROOT / "infra/terraform/ecs_runtime.tf").read_text(encoding="utf-8")
    assert terraform.count(
        '{ name = "PAPRNAV_DATABASE_HOST", value = aws_db_instance.postgres.address }'
    ) == 1
    assert terraform.count(
        '{ name = "PAPRNAV_DATABASE_PORT", value = tostring(aws_db_instance.postgres.port) }'
    ) == 1
    assert "PAPRNAV_DATABASE_HOST" not in terraform.split("bootstrap_common_environment = [", 1)[0]
    assert "PAPRNAV_DATABASE_PORT" not in terraform.split("bootstrap_common_environment = [", 1)[0]
    assert "containerOverrides" not in terraform
    assert "overrides" not in terraform


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


def test_generated_supplement_is_separate_quota_feasible_and_exactly_attachable() -> None:
    generator = load_module(
        "paprnav_package_e_policy_generator",
        REPO_ROOT / "scripts/generate_pilot_deploy_policy.py",
    )
    baseline_path = REPO_ROOT / "infra/aws-iam/paprnav-terraform-deploy-policy.json"
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    generated = generator.generate(
        "Z123456789ABC",
        "pilot.example.com",
        "arn:aws:iam::527257972989:role/paprnav-policy-updater",
        "arn:aws:kms:us-east-1:527257972989:key/11111111-2222-3333-4444-555555555555",
    )
    assert baseline_path.read_bytes() == baseline_bytes

    compact = lambda value: json.dumps(value, separators=(",", ":"))
    supplement = generated["deployPolicySupplement"]
    invalid_merge = {
        "Version": "2012-10-17",
        "Statement": baseline["Statement"] + supplement["Statement"],
    }
    assert len(compact(baseline)) == 5011
    assert len(compact(supplement)) == 3731
    assert len(compact(invalid_merge)) == 8704
    limits = generated["publicationPreconditions"]
    assert len(compact(baseline)) <= limits["customerManagedPolicyCharacterLimit"]
    assert len(compact(supplement)) <= limits["customerManagedPolicyCharacterLimit"]
    assert len(compact(invalid_merge)) > limits["customerManagedPolicyCharacterLimit"]
    assert limits == {
        "customerManagedPolicyCharacterLimit": 6144,
        "requiredAvailableRoleAttachmentSlots": 1,
        "requiredAvailablePolicyVersionSlotsWhenExisting": 1,
        "managedPolicyVersionLimit": 5,
    }

    baseline_arn = "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy"
    supplement_arn = baseline_arn + "-pilot-supplement"
    deploy_role_arn = "arn:aws:iam::527257972989:role/paprnav-terraform-deploy"
    assert generated["baselinePolicyArn"] == baseline_arn
    assert generated["supplementPolicyArn"] == supplement_arn
    assert generated["deployRoleArn"] == deploy_role_arn

    updater = generated["operatorUpdaterProofPolicy"]["Statement"]
    lifecycle = one([item for item in updater if item["Sid"] == "ManageExactPilotSupplement"])
    assert lifecycle["Resource"] == supplement_arn
    assert set(lifecycle["Action"]) == {
        "iam:CreatePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListPolicyVersions",
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion",
        "iam:TagPolicy",
    }
    attachment = one([item for item in updater if item["Sid"] == "AttachExactPilotSupplement"])
    assert attachment["Action"] == ["iam:AttachRolePolicy", "iam:DetachRolePolicy"]
    assert attachment["Resource"] == deploy_role_arn
    assert attachment["Condition"] == {"ArnEquals": {"iam:PolicyARN": supplement_arn}}
    assert all(baseline_arn != item["Resource"] for item in updater)

    deletion = generated["operatorSeparatelyAuthorizedDeletionProofPolicy"]["Statement"]
    assert deletion == [{
        "Sid": "DeleteExactPilotSupplementOnly",
        "Effect": "Allow",
        "Action": ["iam:DeletePolicyVersion", "iam:DeletePolicy"],
        "Resource": supplement_arn,
    }]
    assert not any(
        action in {"iam:DeletePolicy", "iam:DeletePolicyVersion"}
        for item in updater
        for action in item["Action"]
    )

    matrix = json.loads((REPO_ROOT / "infra/aws-iam/pilot-policy-matrix.json").read_text(encoding="utf-8"))
    assert matrix["deployPolicyArn"] == baseline_arn
    assert matrix["supplementPolicyArn"] == supplement_arn
    assert matrix["deployRoleArn"] == deploy_role_arn
    assert matrix["publicationPreconditions"] == limits
    assert "baseline remains attached and unchanged" in matrix["effectiveAuthorizationNote"]
    updater_rows = [row for row in matrix["rows"] if row["principal"] == "named IAM policy updater"]
    assert len(updater_rows) == 2
    matrix_lifecycle = one([row for row in updater_rows if "iam:CreatePolicy" in row["actions"]])
    matrix_attachment = one([row for row in updater_rows if "iam:AttachRolePolicy" in row["actions"]])
    assert matrix_lifecycle["resourceTemplate"] == "${SUPPLEMENT_POLICY_ARN}"
    assert matrix_attachment["resourceTemplate"] == "${DEPLOY_ROLE_ARN}"
    assert matrix_attachment["condition"] == "ArnEquals iam:PolicyARN=${SUPPLEMENT_POLICY_ARN}"
    deletion_row = one([
        row for row in matrix["rows"]
        if row["principal"] == "separately authorized IAM rollback/deletion operator"
    ])
    assert set(deletion_row["actions"]) == {"iam:DeletePolicy", "iam:DeletePolicyVersion"}
    assert deletion_row["resourceTemplate"] == "${SUPPLEMENT_POLICY_ARN}"
    assert "Not included in ordinary updater authority" in deletion_row["condition"]


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
                })}
            assert SecretId == "first-admin"
            return {"SecretString": json.dumps({"password": "first-admin-password"})}

    monkeypatch.setenv("PAPRNAV_ADMIN_SECRET_ARN", "admin")
    monkeypatch.setenv("PAPRNAV_FIRST_ADMIN_SECRET_ARN", "first-admin")
    monkeypatch.setenv("PAPRNAV_DATABASE_HOST", str(connection_args["host"]))
    monkeypatch.setenv("PAPRNAV_DATABASE_PORT", str(connection_args["port"]))
    monkeypatch.setenv("PAPRNAV_DATABASE_NAME", str(connection_args["dbname"]))
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
### `infra/aws-iam/pilot-policy-matrix.json`

size=4392; sha256=fdad7b377c87dc8bd893dc1c58ef21cbfa42bf5338f841dd59f23d1bab2b8690; truncated=false

```text
{
  "version": "paprnav-pilot-policy-matrix-v2",
  "accountId": "527257972989",
  "region": "us-east-1",
  "deployPolicyArn": "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy",
  "supplementPolicyArn": "arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement",
  "deployRoleArn": "arn:aws:iam::527257972989:role/paprnav-terraform-deploy",
  "effectiveAuthorizationNote": "The supplement is a separate customer-managed policy. The existing broad baseline remains attached and unchanged, so operator authorization limits must not be represented as effective IAM denies.",
  "publicationPreconditions": {
    "customerManagedPolicyCharacterLimit": 6144,
    "requiredAvailableRoleAttachmentSlots": 1,
    "requiredAvailablePolicyVersionSlotsWhenExisting": 1,
    "managedPolicyVersionLimit": 5
  },
  "rows": [
    {
      "principal": "named IAM policy updater",
      "actions": ["iam:CreatePolicy", "iam:GetPolicy", "iam:GetPolicyVersion", "iam:ListPolicyVersions", "iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion", "iam:TagPolicy"],
      "resourceTemplate": "${SUPPLEMENT_POLICY_ARN}",
      "condition": "Creates or versions only the separately named pilot supplement; the baseline policy and its default version are unchanged."
    },
    {
      "principal": "named IAM policy updater",
      "actions": ["iam:AttachRolePolicy", "iam:DetachRolePolicy"],
      "resourceTemplate": "${DEPLOY_ROLE_ARN}",
      "condition": "ArnEquals iam:PolicyARN=${SUPPLEMENT_POLICY_ARN}"
    },
    {
      "principal": "separately authorized IAM rollback/deletion operator",
      "actions": ["iam:DeletePolicyVersion", "iam:DeletePolicy"],
      "resourceTemplate": "${SUPPLEMENT_POLICY_ARN}",
      "condition": "Not included in ordinary updater authority. Delete only exact non-default versions or the detached supplement after separately recorded authorization and verification of zero unexpected attachments."
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
### `infra/bootstrap/bootstrap.py`

size=19625; sha256=0156bcf3f1c6049c36b188585d2ec079224ac3b076f989e68e951d365691d121; truncated=false

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
DATABASE_HOST = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)


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
    required = {"username", "password"}
    if not required.issubset(value):
        raise BootstrapError("RDS administrator secret is missing required credentials")
    if value["username"] != "paprnav_admin":
        raise BootstrapError("RDS administrator secret has the wrong username")
    if not isinstance(value["password"], str) or not value["password"]:
        raise BootstrapError("RDS administrator secret has an invalid password")

    host = require_env("PAPRNAV_DATABASE_HOST")
    if DATABASE_HOST.fullmatch(host) is None:
        raise BootstrapError("database host environment input is invalid")
    port_text = require_env("PAPRNAV_DATABASE_PORT")
    if re.fullmatch(r"[0-9]{1,5}", port_text) is None:
        raise BootstrapError("database port environment input is invalid")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise BootstrapError("database port environment input is outside 1..65535")
    return {
        "host": host,
        "port": port,
        "dbname": os.getenv("PAPRNAV_DATABASE_NAME", "paprnav"),
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
### `infra/terraform/tests/package_c.tftest.hcl`

size=11432; sha256=ff2289ddcefc8a5cd9b944827b456bfac71005c7681aa79ae7f974170b1fbffe; truncated=false

```text
mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  # Targeting the bootstrap task definitions also plans their IAM role
  # dependencies. Keep every mocked policy document valid at plan time so
  # provider schema validation cannot obscure the container assertions.
  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }

  mock_data "aws_route53_zone" {
    defaults = {
      zone_id      = "Z123456789"
      name         = "example.com."
      private_zone = false
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

run "bootstrap_database_location_is_bound_to_rds" {
  command = plan

  # The assertions decode container_definitions during planning, so every
  # resource-derived value in that JSON must be known before apply.
  override_resource {
    target          = aws_db_instance.postgres
    override_during = plan
    values = {
      address = "paprnav-bootstrap-plan.invalid"
      port    = 5432
      db_name = "paprnav"
      master_user_secret = [{
        secret_arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:rds!db-package-c-plan"
      }]
    }
  }

  override_resource {
    target          = aws_secretsmanager_secret.database_url
    override_during = plan
    values = {
      arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/app-database-plan-000001"
    }
  }

  override_resource {
    target          = aws_secretsmanager_secret.first_admin_password
    override_during = plan
    values = {
      arn = "arn:aws:secretsmanager:us-east-1:527257972989:secret:paprnav/package-c/first-admin-plan-000001"
    }
  }

  override_resource {
    target          = aws_cloudwatch_log_group.bootstrap
    override_during = plan
    values = {
      name = "/paprnav/package-c/bootstrap-plan"
    }
  }

  plan_options {
    target = [aws_ecs_task_definition.bootstrap]
  }

  assert {
    condition = alltrue([
      for phase, task in aws_ecs_task_definition.bootstrap : (
        lookup({
          for item in jsondecode(task.container_definitions)[0].environment : item.name => item.value
        }, "PAPRNAV_DATABASE_HOST", "") == aws_db_instance.postgres.address &&
        lookup({
          for item in jsondecode(task.container_definitions)[0].environment : item.name => item.value
        }, "PAPRNAV_DATABASE_PORT", "") == tostring(aws_db_instance.postgres.port)
      )
    ])
    error_message = "Every sealed bootstrap task must bind its host and port directly to the Terraform-managed RDS instance."
  }

  assert {
    condition = alltrue([
      for phase, task in aws_ecs_task_definition.bootstrap : (
        length(jsondecode(task.container_definitions)[0].command) == 1 &&
        jsondecode(task.container_definitions)[0].command[0] == phase
      )
    ])
    error_message = "Each bootstrap task definition must retain its one fixed phase command."
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
### `scripts/generate_pilot_deploy_policy.py`

size=8437; sha256=51b81d7e60011056ab80735f6073570125b7a103782835314ef785da15d2c39e; truncated=false

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
SUPPLEMENT_POLICY_ARN = f"{DEPLOY_POLICY_ARN}-pilot-supplement"
DEPLOY_ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/paprnav-terraform-deploy"
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
        "Statement": [
            statement(
                "ManageExactPilotSupplement",
                [
                    "iam:CreatePolicy",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:ListPolicyVersions",
                    "iam:CreatePolicyVersion",
                    "iam:SetDefaultPolicyVersion",
                    "iam:TagPolicy",
                ],
                SUPPLEMENT_POLICY_ARN,
            ),
            statement(
                "AttachExactPilotSupplement",
                ["iam:AttachRolePolicy", "iam:DetachRolePolicy"],
                DEPLOY_ROLE_ARN,
                {"ArnEquals": {"iam:PolicyARN": SUPPLEMENT_POLICY_ARN}},
            ),
        ],
    }
    deletion = {
        "Version": "2012-10-17",
        "Statement": [statement(
            "DeleteExactPilotSupplementOnly",
            ["iam:DeletePolicyVersion", "iam:DeletePolicy"],
            SUPPLEMENT_POLICY_ARN,
        )],
    }
    return {
        "version": "paprnav-pilot-generated-prerequisites-v2",
        "inputs": {"hostedZoneId": zone_id, "pilotHostname": pilot_hostname, "operatorUpdaterPrincipalArn": updater_principal, "secretsManagerKmsKeyArn": kms_key_arn},
        "baselinePolicyArn": DEPLOY_POLICY_ARN,
        "supplementPolicyArn": SUPPLEMENT_POLICY_ARN,
        "deployRoleArn": DEPLOY_ROLE_ARN,
        "publicationPreconditions": {
            "customerManagedPolicyCharacterLimit": 6144,
            "requiredAvailableRoleAttachmentSlots": 1,
            "requiredAvailablePolicyVersionSlotsWhenExisting": 1,
            "managedPolicyVersionLimit": 5,
        },
        "deployPolicySupplement": {"Version": "2012-10-17", "Statement": deploy_statements},
        "operatorUpdaterProofPolicy": operator,
        "operatorSeparatelyAuthorizedDeletionProofPolicy": deletion,
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
