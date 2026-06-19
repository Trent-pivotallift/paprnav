# paprnav AD-To-Logbook Matching Rules

Last updated: 2026-06-18

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

Candidate logbook entries are cited when description or raw OCR text contains:

- the AD number
- affected product words
- compliance/action words such as inspect, replace, comply, modify
- title terms from the AD source

Each cited entry stores the matched text and rationale. OCR-created entries remain traceable through existing `LogbookEntryEvidence` records.

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

The first implementation is `deterministic_ad_logbook_matcher` version `0.1.0`.

It handles:

- one-time AD evidence
- simple recurring AD evidence when the interval is structured
- unresolved cases routed to adjudication
- evidence/rationale persistence
- idempotent replay by algorithm/version/input hash

It does not yet handle:

- final human adjudication UI/API
- complex serial-number applicability
- official compliance attestation
- legal/currentness decisions beyond the persisted source and supersession graph
