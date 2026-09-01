# T081 retrospective design adversary — initial

Reviewer: `/root/t081_design_adversary`

Outcome: FAIL

The packet was current against `HEAD` and included staged, unstaged, and
untracked scope. Direct repository inspection found the following defects. No
files were edited by the reviewer.

## Findings

### T081-DA-1 — Blocker — Applicability predicates are published but never evaluated

`validate_applicability_groups` accepts expression/unknown model and serial
scope. `populate_v3_applicability` persists serial, equipment, and conditions,
but `ad_matching` evaluates only role/make/model. A serial-limited group can
match a known out-of-range component and proceed toward due state. Required
closure: evaluate every supported predicate or force adjudication for every
unimplemented predicate, with negative range/exclusion/equipment tests.

### T081-DA-2 — Blocker — Consumers are not bound to the exact human-signed extraction

Matching selects `ADExtraction.status == approved` without requiring a decided
review or output equality. Catalog release accepts any approved evidence-valid
extraction, and exact match reads gate at directive rather than extraction
identity. Required closure: one centralized released-signed-extraction boundary
requiring reviewer attribution, timestamp, exact output equality, and current
evidence validation on catalog, matching, coverage, rematerialization, and
exact-match reads.

### T081-DA-3 — Blocker — v3 recurrence is controlled by a legacy summary and only one obligation is replayed

Match classification uses top-level `complianceIntervals`; requirement lookup
returns one row and `ADMatchResult` has one due-state link. A v3 recurring
requirement with an empty legacy summary is treated as one-time, and a second
requirement disappears from actionable state. Required closure: drive replay
from every signed current v3 requirement and expose due state per obligation.

### T081-DA-4 — Blocker — Migration/backfill changes signed meaning and rollback destroys v3 state

Migration `0023` inserts an empty AMOC list into extraction, proposal, and
signed decision JSON without reviewer action. Downgrades remove AMOC,
trigger-kind, group identity, equipment, and source evidence. Required closure:
never semantically amend signed decisions; reopen missing-envelope reviews with
attributed audit evidence, and define a guarded irreversible migration/recovery
contract or lossless export.

### T081-DA-5 — Blocker — Component due state silently falls back to aircraft-level time

When component time is absent, `latest_time_state` returns an aircraft-level
state and computes actionable component due status without uncertainty.
Required closure: require an explicit reviewed metric-equivalence mapping or
return unknown; test mismatched engine/airframe time.

### T081-DA-6 — High — Correction does not invalidate all derived state

Correction invalidates matches but leaves applicability, requirements, AMOCs,
current due states, and observable coverage current. Required closure:
supersede/quarantine every derived row and test all readers between correction
and reapproval.

### T081-DA-7 — High — Concurrent decisions can overwrite attribution and signed output

The decision endpoint has neither row lock nor optimistic revision and stores
only the mutable review row. Required closure: serialize the transition and
append immutable decision records containing actor and output hash; add a
two-session concurrency test.

### T081-DA-8 — High — Critical structured fields are not evidence-bound

Page citations are genuine but need not contain the claimed manufacturer,
model, serial scope, equipment logic, AMOC authority, instructions, or
conditions. Required closure: bind every safety-bearing field to exact source
text or force adjudication, with mismatched-field negative tests.

### T081-DA-9 — High — Cached evidence is not verified against retained bytes

Cached pages compare embedded hashes to mutable database metadata, while the
stored object is not rehashed at approval/release and the source endpoint
streams without checking. Required closure: rehash retained bytes or bind an
enforceable immutable object version at approval/release; fail closed and test
storage mutation.

### T081-DA-10 — Medium — Calibration does not exercise the v3 failure surface

The five calibration JSON files are requirement-only drafts, not complete v3
packets with applicability and AMOC envelopes. Required closure: complete
source-cited v3 packets and expected positive/negative adjudication outcomes.

## Design questions

- Decide whether coverage is a released regulatory read and gate it if it is.
- Define any permitted aircraft/component metric equivalence explicitly.
- Choose a truthful irreversible or lossless downgrade contract.

## Accepted limitations

- The retrospective run cannot recreate a pre-implementation design gate.
- A fresh administrator browser session is still required for implementation-
  stage GUI evidence.

**DESIGN OUTCOME: FAIL**
