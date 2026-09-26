# T082 AWS pilot delivery scoreboard

Updated: 2026-09-20  
Target: 2026-10-19  
Days remaining: 29  
Status: reviewed local components exist; no exact release candidate or live AWS
acceptance exists. External execution awaits operator inputs and explicit
release/AWS authorization.

## Pilot gates

| Gate | Status | Evidence / next proof |
| --- | --- | --- |
| Frozen release boundary; unfinished V4 disabled | component implementation reviewed | Package A independent implementation PASS; exact clean-candidate proof remains |
| Invite-only auth, secure sessions, tenant isolation | component implementation reviewed | Package B independent implementation PASS; live two-tenant and revocation proof remains |
| Private PostgreSQL, backups, least-privilege bootstrap | component implementation reviewed | Package C is closed and E1A has independent implementation PASS; fresh RDS migration/bootstrap and restore remain |
| HTTPS AWS application | not operational | hostname/zone/certificate inputs, reviewed plan/apply, images, and live health remain |
| Aircraft/logbook/upload/manual review journey | targeted component checks passed | no complete invited-user acceptance run; fresh AWS database and immutable-image proof remain |
| Bounded real OCR/review journey | remaining | durable paid-attempt/idempotency family, ceilings, one consented real flow |
| Existing non-V4 AD decision support | targeted component checks passed | no complete pilot acceptance run; live degraded/needs-review behavior and labels remain |
| Errors, achievements, feedback, OCR/provider cost visible | local telemetry component closed | Package D closure covers local behavior; live log delivery and real attribution remain |
| AWS cost and budget evidence visible | remaining | live budget recipient/delivery and dated AWS cost evidence remain |
| Deployment, rollback, and recovery | remaining | exact runbook execution, first-release scale-to-zero, and isolated restore; prior-image rollback applies only after an approved prior release exists |
| One external invited user succeeds | remaining | invite only after security, recovery, and spend gates pass |

## Current critical-path package

**Package E2: clean release candidate and no-mutation image/deployment packet.**
E1A's bootstrap/IAM prerequisite implementation has independent PASS. The dirty
tree is now completely partitioned into 70 eligible release-source paths, 118
T082 evidence paths, 145 preserved T081 paths, and 10 forbidden 0030/protected
paths, with zero unclassified paths. Candidate construction awaits the inputs
and explicit commit authorization below; no additional V4 work is on this path.

## Human action blockers

- Canonical pilot hostname and Route 53 zone ID/name.
- Exact issued ACM certificate ARN and certificate/DNS owner.
- Budget recipient and accountable cost/incident operator.
- Exact IAM supplement-policy updater principal.
- First administrator name, email, and platform organization.
- Explicit authorization for the clean release commit and, later, each bounded
  AWS mutation batch. Cohort identities, recovery operators, and paid-OCR
  choices are needed before their respective gates, not before the dry run.

## Remaining test and review evidence

- Verify Package A against the exact clean candidate and immutable image inputs.
- One family review of the concrete Terraform plan/execution packet.
- Fresh-database migration/bootstrap and runtime-role denial checks.
- Live HTTPS, session, two-tenant, privacy/log-delivery, budget, stop/scale-to-zero,
  and isolated-restore acceptance. Test prior-image rollback only after an
  independently approved compatible prior release exists.
- One durable paid-attempt implementation family and review, then one bounded
  real OCR flow.
- One final independent Astra closure review of the deployed evidence.

## Estimated remaining model usage

- Sol high: 2-4 coherent builder turns (candidate/execution packet, activation
  corrections, paid-attempt family, acceptance evidence).
- Astra high/xhigh: 3-5 bounded independent turns (plan/execution family,
  paid-attempt family, any substantive remediation, final closure).
- Terra medium: 1-2 mechanical artifact/hash/runbook updates if needed.

These are planning estimates, not quotas. A failed mandatory gate triggers
reassessment or deferral rather than repeated broad reviews.

## Deferred from the pilot

- T081 V4 schema/acceptance completion and the unreviewed 0030 artifacts.
- Exhaustive V4 semantic/corruption matrices and unrelated hardening.
- Recurring or bulk OCR, broad provider support, and automated customer billing.
- Cognito/MFA, multi-organization invitation expansion, and per-invite stored
  revocation history.
- Rich analytics SaaS, private egress/NAT, multi-region, and high availability.

## Next demonstrable outcome

Resolve the five non-secret operator input groups above and explicitly
authorize the clean candidate commit. Then construct and verify the exact
candidate and produce the no-mutation Terraform/image packet for one
family-level review. Do not stage, commit, push, apply, write a secret, change
DNS, start a service, or invite a user without its existing explicit
authorization gate.
