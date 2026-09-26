# T082 30-day delivery objective amendment

Date adopted: 2026-09-19  
Target: 2026-10-19  
Authority: user-approved delivery objective; this amendment governs T082 where
older packet language can be read more broadly.

## Outcome and scope freeze

The overriding delivery objective is an invite-only AWS pilot within 30 days.
Optimize for the shortest safe path to external-user learning. Post-pilot
completeness, exhaustive schema closure, speculative hardening, and document or
test volume are not release requirements.

A change belongs on the critical path only if its absence would prevent:

1. an invited user from completing the pilot workflow;
2. tenant isolation or basic account security;
3. durable storage or recovery;
4. meaningful error, achievement, feedback, or cost evidence;
5. bounded AWS/provider spend; or
6. deployment and rollback.

Unfinished V4 functionality remains disabled. It enters this release only when
a concrete failed pilot gate proves that the existing workflow depends on it.
T081 and the unreviewed 0030 candidate-acceptance work remain preserved and
deferred.

## Release gates

- HTTPS and invite-only accounts with secure, revocable sessions.
- Cross-tenant denial for user, aircraft, upload, logbook, feedback, event, and
  cost data.
- Private PostgreSQL, protected source objects, backups, and a proved restore.
- Aircraft, logbook, upload, bounded OCR/review, and existing non-V4 AD
  decision-support journey.
- Attributable sanitized errors, achievements, feedback, OCR/provider cost,
  and AWS-cost/budget evidence.
- Budget notifications, per-operation ceilings, and an operator stop action.
- Repeatable deployment, first-release stop/scale-to-zero, and data-preserving
  recovery. After an independently approved prior image exists, prove
  compatible previous-image rollback.
- Successful use by at least one external invited user.

## Delivery cadence

| Window | Exit result |
| --- | --- |
| Days 1-5 (Sep 19-23) | Release boundary, invite/auth design, and deployment scope closed |
| Days 6-12 (Sep 24-30) | AWS HTTPS application running against a fresh database |
| Days 13-18 (Oct 1-6) | Complete invited-user journey works end to end |
| Days 19-23 (Oct 7-11) | Errors, achievements, feedback, OCR cost, and AWS cost are visible |
| Days 24-27 (Oct 12-15) | First external users invited and pilot-blocking defects repaired |
| Days 28-30 / deadline (Oct 16-19) | Acceptance run, restore/rollback proof, and release decision |

Maintain a deployable build at least weekly. Each working day must target a
demonstrable product or release-gate outcome; prose, test count, and review
iteration count do not constitute progress.

## Work-in-progress and evidence budget

- Keep one coherent critical-path package in progress at a time.
- Use one implementation pass and one independent family-level review after the
  package's targeted evidence is complete. Do not review each file, test,
  generated artifact, hash, or marginal correction separately.
- Default verification is the smallest deterministic or targeted regression
  suite that proves the changed contract, plus the applicable end-to-end pilot
  path.
- Authorization, tenant isolation, destructive data paths, migrations,
  provider idempotency, paid-operation ceilings, release gates, and the
  end-to-end pilot require direct evidence.
- Do not build exhaustive combinatorial or corruption matrices unless they
  protect a pilot-critical invariant.
- Permit one remediation and re-review within a package. A second substantive
  failure in the same family stops construction and triggers an invariant,
  architecture, or oracle reassessment under `.ai/MODEL_ROUTING.md`; it does
  not create an unlimited micro-patching loop.
- A time or review ceiling never waives a failed mandatory gate. Defer the
  feature or stop the release when a safe bounded implementation cannot pass.

## Model and decision routing

- Terra medium: mechanical, reversible work derived from approved authority.
- Sol high: approved coherent implementation, including routine AWS-release
  construction.
- Astra high/xhigh: ambiguous security, IAM, provider-spend, migration, or
  invariant decisions; independent family review; and final closure.
- Do not use Astra for routine construction that Sol can perform under an
  approved design. Record actual runtime model/effort when exposed.

## Daily control loop

Update `delivery-scoreboard.md` once per working day and whenever a gate or
human blocker changes. It records days remaining, passed and remaining pilot
gates, the single current package, human decisions, required tests/reviews,
estimated Sol/Astra usage, and proposed deferrals.

Human decisions on critical-path inputs should be raised as concrete, bounded
choices and resolved within hours where possible. No AWS mutation, secret
write, image push, DNS change, migration, invitation, or commit is authorized
by this amendment; the existing explicit authorization and commit gates remain.
