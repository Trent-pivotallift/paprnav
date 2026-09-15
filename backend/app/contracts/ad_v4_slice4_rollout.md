# V4 Slice-4 rejection-only rollout boundary

Migration `20260913_0029` is expand-first. It installs the database gates
`reviewer4_draft_enabled=false` and `reviewer4_decision_enabled=false`. The
application flags `PAPRNAV_AD_V4_SLICE4_READS_ENABLED`,
`PAPRNAV_AD_V4_SLICE4_DRAFTS_ENABLED`, and
`PAPRNAV_AD_V4_SLICE4_DECISIONS_ENABLED` also default to false.

This migration supports review cases, immutable annotation drafts, frozen
review requests, and graph-free rejection signoffs only. It does not install an
acceptance branch, decision-node graph, publication, current selection, V3
freeze, search, matching, coverage, compliance, or due-state behavior.

Roll out in this order:

1. migrate every database through `0029` while both new database gates remain
   disabled;
2. deploy an `0029`-aware binary to every API replica;
3. enable read routes and verify bounded repeatable-read queue/detail checks;
4. enable the application draft flag, then `reviewer4_draft_enabled`, to admit
   cases, drafts, and review requests;
5. enable the application decision flag, then
   `reviewer4_decision_enabled`, to admit rejecting signoffs.

Disabling either application or database gate fails closed. Operational
rollback means disabling the decision flag/gate first, then the draft
flag/gate, while retaining an `0029`-aware reader so immutable history remains
verifiable. Existing V3 and V4 candidate/projection reads remain unchanged.

Physical downgrade is allowed only while both Slice-4 database gates are
disabled and all six Slice-4 review tables are empty. Once any review history
exists, physical downgrade is prohibited; preserve the schema and use the
disabled-gate operational rollback instead.

Candidate-only acceptance remains a later reviewed vertical. Release-eligible
acceptance remains blocked until a separately reviewed executable evaluator
and any required supporting-document admission work exist. Slice 5 owns the V3
freeze at the first actual release/current-selection activation.
