# Package D design-inheritance review — FAIL

## Model routing

- Designer/coordinator: `/root`.
- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested reviewer route: GPT-6 Astra, high.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.

Package D remains within the approved parent design, but the following bounded
clarifications are required before implementation. No migration or paid-provider
implementation is required.

## T082-D-001 — High — Recorded OCR rows do not prove complete paid-attempt exposure

The ingestion service creates and flushes `OCRRun`, invokes the provider, and
commits later. A crash can therefore leave no row. Provider metadata arrives
after the call, and billing status is not proof of a charge.

Close by defining Package D as a recorded-run projection, marking paid-attempt
coverage and reconciliation completeness unavailable, reporting known partial
estimates separately from unknown amounts, and keeping lifecycle, pricing,
attribution, and billing classifications independent. Historical billing tags
must not be silently reattributed to a current owner. Complete exposure
accounting remains Package E's durable-attempt gate.

## T082-D-002 — High — Extracted-entry transaction and actor semantics are unresolved

The ingestion service returns existing entries on retry, assigns the uploader
as entry creator, and commits new entries/evidence before the HTTP route writes
events. Route-level achievement recording cannot be atomic. A non-HTTP
feasibility caller also uses the service.

Close by binding the ingestion service and non-HTTP caller into scope. Emit
events only for newly created entries before their commit, using explicitly
supplied authenticated actor context. Existing-entry retries do not mint
creation evidence. Preserve non-HTTP commit behavior without inventing a pilot
actor.

## T082-D-003 — Medium — Deduplication lacks representative/order semantics

The identity key does not define which duplicate represents success or when
date/actor filters and recent-row limits apply.

Close by selecting the earliest `(event_time, id)` first-success representative
before date/actor grouping and recent-row limits. Aggregate counts remain
independent of display limits.

## Required implementation boundary

Keep models and migrations unchanged. Page success requires completed OCR plus
confirmed order and completeness. AD achievements require a successful
committed human decision, exclude the conflict/409 path, and preserve the two
approved AD subject types. Use fixed-property events and content-free error
categories; expose neither raw workflow reasons nor exception messages.
Preserve Package B authorization, Package A gates, the real budget-subscriber
prerequisite, and disabled paid workers.

Packet SHA-256 matched
`c244bef7db6f8bfeb2461abe38bb3a29ad6eead7c669fc98243ff09614c98f4e`.
Current fingerprint was
`c8d03eed16b405d84027bf14f8cb596afcd13c9eac289a29413070a48839ac55`.
No edit, test, staging, commit, or cloud action occurred during review.
