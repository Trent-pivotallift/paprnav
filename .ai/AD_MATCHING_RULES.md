# paprnav AD-To-Logbook Matching Rules

Last updated: 2026-07-25

This document defines the first-pass matching rules for T051/T052. It is a product and implementation boundary, not an official compliance attestation.

## Scope

The matcher compares approved structured AD extractions against structured aircraft logbook entries and creates reproducible candidate or unresolved records. It should bias toward human review when applicability or compliance evidence is uncertain.

## Inputs

- Aircraft identity and component facts:
  - make/model
  - serial number
  - engine make/model/serial
  - propeller make/model/serial
- Approved AD extraction output:
  - AD number
  - title
  - affected products
  - compliance actions
  - compliance intervals
  - supersession references
  - source URLs
  - provider/version/schema/input hash
- Current AD supersession graph.
- Structured logbook entries:
  - date
  - section
  - description
  - raw OCR text when available
  - review status
  - tach/hobbs/total time when available
- OCR evidence links already attached to logbook entries.

## Outputs

The first-pass matcher persists:

- `ADMatchResult`
  - aircraft
  - directive
  - extraction
  - status
  - match type
  - confidence
  - rationale
  - unresolved reasons
  - algorithm name/version
  - input hash
- `ADMatchEvidence`
  - candidate logbook entry
  - matched text
  - confidence
  - rationale
- `ADMatchAdjudication`
  - pending review task for unresolved or uncertain results.

## Statuses

- `candidate_satisfied`: the system found logbook evidence that appears to satisfy the AD.
- `needs_adjudication`: the system cannot safely conclude satisfaction, applicability, or compliance timing.
- Future statuses after human review: satisfied, not_satisfied, not_applicable, needs_more_info, deferred.

These are product workflow statuses. They are not official legal compliance statements.

## Match Types

- `one_time`: no recurring interval is present in the approved extraction.
- `simple_recurring`: the approved extraction contains a structured compliance interval, such as tach-hour or calendar interval.
- Future types: conditional, component_specific, serial_range, life_limited_part, recurring_complex.

## Evidence Rules

Candidate logbook entries may be cited when description or raw OCR text contains:

- the AD number
- affected product words
- compliance/action words such as inspect, replace, comply, modify
- title terms from the AD source

Each cited entry stores the matched text and rationale. OCR-created entries remain traceable through existing `LogbookEntryEvidence` records.

`candidate_satisfied` requires all of:

- an explicit AD-prefixed reference that normalizes to the directive number
- a positive compliance or inspection disposition
- a human-verified logbook entry

Negated statements such as `not complied`, `did not comply`, `not inspected`, or
`inspection not completed` are never positive compliance evidence. They remain
reviewable evidence and route to adjudication. When one OCR line contains
multiple clauses or AD citations, each AD's disposition is parsed from the
line context owned by that citation and bounded by neighboring AD citations and
sentence separators. Internal comma-set-off phrases remain in the claim, while
decimal regulation references such as `43.13` are not sentence boundaries.
Negative evidence is evaluated conservatively across the citation context.
Positive compliance or inspection evidence must occur in the citation's
immediate clause so an unrelated later action cannot promote the AD to
`candidate_satisfied`.

## HITL Adjudication Rules

Create a pending adjudication task when:

- no candidate logbook entry is found for an applicable AD
- applicability is missing or too broad
- compliance action is missing or unstructured
- recurrence exists but interval data is not normalized
- conditional or component-specific applicability cannot be resolved from aircraft/component facts
- evidence is only lexical and lacks enough confidence for a candidate-satisfied result
- supersession cannot be represented cleanly

## Supersession Rules

- Superseded ADs should not appear as currently required unless history is explicitly requested.
- The first matcher reads the supersession graph and matches current approved directives.
- Historical matching can be added later as a separate mode.

## Confidence

Confidence is a local `0.0-1.0` score derived from lexical evidence, not a regulatory confidence score.

High-confidence candidates generally include an AD number citation. Lower-confidence candidates may include only product/action/title overlap and should remain reviewable.

## Current Implementation

The current implementation is `deterministic_ad_logbook_matcher` version `0.3.0`.

It handles:

- normalized two- and four-digit explicit AD references
- verified one-time positive compliance evidence
- negative-language guards that prevent false satisfaction
- recurring AD evidence routed to adjudication until due-state calculation exists
- unresolved cases routed to adjudication
- evidence/rationale persistence
- one structured-text parse per entry per aircraft matching run
- idempotent replay by algorithm/version/input hash

Older versioned replay records remain stored for audit, while the normal
aircraft match-list API returns only results from the current algorithm version.
Its `matcherStatus` distinguishes `current`, `pending_recomputation`, and
`not_run`; matching remains an explicit worker operation rather than a side
effect of a GET request.

It does not yet handle:

- final human adjudication UI/API
- complex serial-number applicability
- official compliance attestation
- legal/currentness decisions beyond the persisted source and supersession graph
