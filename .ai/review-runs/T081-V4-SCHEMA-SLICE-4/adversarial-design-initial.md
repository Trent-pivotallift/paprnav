# T081 V4 Schema Slice 4 — initial adversarial design review

Reviewer: `/root/v4_s4_design_adversary`

Reviewed base: `4840a0b4bc5d7334ddcf51a80e39c8fa84b7b0c2`

Decision SHA-256: `a337ae91010ebb7c17e49ee3dffc720c3b0848a218b4bbebda920a379ce6a356`

Outcome: **FAIL. Do not advance to implementation.**

The review was read-only. Staged and unstaged changes were empty; the only
untracked scope was the Slice-4 review-run directory. No implementation or
database tests were run because this is a design gate.

## Blockers

### T081-V4-S4-B-001 — Release-eligible acceptance is impossible

S4-I09/I12/I24 require an implemented evaluator for an actionable node and all
release-required nodes to be actionable. Current Slice-3A conditions, rules,
and expressions are constrained to `evaluator_contract='none'` in the ORM,
migration 0027, and reconstruction verifier. Slice 3A expressly reserves an
evaluator for separate review. A synthetic known-value candidate therefore
cannot prove release eligibility without inventing evaluator authority.

Required closure: make Slice 4 candidate-only/rejection only until a separately
reviewed evaluator exists, or explicitly add and review the complete evaluator,
normalization, predicate/operator, version, and calibration expansion. Replace
the impossible positive release test with a negative gate proof if bounded.

### T081-V4-S4-B-002 — Exact gate and independent SQL contract are absent

The packet promises a future specification but does not freeze every node
family, base gate, controlling status, evidence requirement, dependency
direction, cycle rule, aggregate minimum, reason, or calibration oracle. The
existing graphs contain structural, expression, prerequisite, termination,
recurrence, search-hint, and correction relationships with materially different
semantics. Caller-supplied gate rows or hashes cannot be their own SQL authority.

Required closure: add the complete normative matrix before implementation.
Migration-owned SQL must independently derive the expected rows and edges from
trusted projection inputs and fixed rule data. Include exact direct-SQL
counterexamples and hand-declared fixture oracles.

### T081-V4-S4-B-003 — Lifecycle has no pre-decision aggregate

The proposed drafts and pending request exist before an immutable decision
version, but no review-case root, event owner, creation command, uniqueness/CAS
boundary, or remediation path is defined. Event and state names are mixed and
`review_requested` is omitted. Strong acceptance integrity would also prevent
recording rejection of the malformed inputs that most need remediation.

Required closure: define the immutable review-case aggregate, event/state fold,
creation timing, unique keys, predecessor hashes, draft/request concurrency,
re-review rules, and a rejection path that can record unverifiable inputs while
preserving stronger acceptance gates.

## High findings

### T081-V4-S4-H-001 — Signing lock order conflicts with current V4 writers

The packet locks membership last. Existing candidate and 3A/3B writers lock the
user/membership before proposals, creating a membership/proposal deadlock
cycle. Existing-row locks also do not prevent append-only corrections or
authorship rows.

Required closure: freeze one shared order across signing, candidates,
materialization, evidence, corrections, gate administration, and direct SQL;
name advisory/predicate locks for append-only sets and add forced interleavings.

### T081-V4-S4-H-002 — Parent-required V3 freeze has no activation disposition

The parent design freezes new V3 approvals/corrections at V4 deployment. Slice
4 explicitly leaves the live V3 publication route and buttons unchanged.

Required closure: define the exact activation point and accountable slice. If
it is Slice 4, add and review a V3-write gate. If later, explicitly amend the
coexistence interval and explain why the parent contract remains safe.

### T081-V4-S4-H-003 — Supporting-document admission is undecided

The workflow is conditional, while its proposed issuer/admission/scope binding
cannot be represented by unchanged validator-2 and 3B forces retention to
unknown. Existing source download is not a supporting-document admission or
access-policy service.

Required closure: either explicitly defer it, keep dependent nodes
nonactionable, and name the later owner, or specify the complete immutable
acquisition/access/authenticity/scope/admission lifecycle and versioned binding.

### T081-V4-S4-H-004 — Read verification has no single-snapshot/version contract

Historical and current revalidation spans mutable heads but the packet does not
require one repeatable-read snapshot or preserve the original gate/authorship/
policy verifier. Read committed can mix generations and current rules can
misclassify valid history.

Required closure: use one separate repeatable-read, read-only snapshot per
operation; distinguish frozen historical verification from current eligibility;
define unsupported old-version handling and forced concurrent-change tests.

### T081-V4-S4-H-005 — Existing auth helper cannot supply promised validity

The current helper checks role/status but membership has no validity interval or
immutable version. ORM identity-map caching is not necessarily refreshed by a
locking query, and expected input hashes do not cover membership changes.

Required closure: define validity and the submit CAS token from the actual
model; freshly fetch/refresh locked scalar state; add an independent SQL
actor/membership check; preserve historical snapshots without comparing them to
current role/status; and test downgrade/deactivation races.

## Medium findings

### T081-V4-S4-M-001 — Machine authorship and cutoff lack provenance

Existing candidate submissions are all attributable platform-admin actions;
there is no machine-only actor. Proposal content deduplicates while later
submissions/relationships may append, so recomputing authorship can rewrite the
meaning of old signoff.

Required closure: conservatively treat current submissions as human, freeze
the exact contributing event IDs/cutoff, distinguish creator/resubmitter/
corrector, and defer machine-only status absent a trusted provenance path.

### T081-V4-S4-M-002 — Form preservation/edit mapping is incomplete

The broad UI controls do not map every validator-2 root family, ordered list,
optional-property presence, and typed reference. A form correction could drop
or reorder valid semantics even though the predecessor remains immutable.

Required closure: freeze complete editable/read-only control mapping, exact
preservation rules, semantic diff, reference revalidation, and focused edits
for recurrence, ordered actions, corrections, unknowns, and search hints.

### T081-V4-S4-M-003 — Rollout stages do not match proposed gates

One app and one DB gate cannot separately stage reads, draft/request writes, and
terminal signoff. A migration cannot observe flags on all application replicas.

Required closure: define real capability controls, defaults, database reporting,
deployment procedure, enforceable downgrade checks, and complete occupancy.

## Sound boundary

The non-publication boundary is sound. Current released readers select approved
V3 extractions, and isolated V4 review/signoff tables would not by themselves
enter catalog, search, matching, coverage, compliance, or due-state readers.

## Gate result

All eleven findings remain open. No finding is accepted risk, rejected, or
closed. Required design decisions before re-review are: executable acceptance
states; the complete gate/SQL matrix; review-case lifecycle/remediation; shared
locking and read snapshots; supporting-document scope; and the V3-freeze
activation point.
