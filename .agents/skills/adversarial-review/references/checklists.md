# Review checklists

## End-to-end trace

- Source and provenance
- Parsing or ingestion
- Validation and rejection behavior
- Human decision and authorization
- Persistence and transaction boundary
- Derived state, jobs, and caches
- API and UI exposure
- Correction, supersession, and revocation
- Audit attribution and retention

## Schema and migration

- Authoritative versus derived representation
- Source-faithful versus normalized values
- Null, uniqueness, ordering, and concurrency semantics
- Upgrade, downgrade, legacy rows, and mixed-version operation
- Idempotency, retries, partial failure, and stale rows
- Backfill and administrative scripts

## Safety and evidence

- Every critical value is bound to source evidence
- Uncertainty fails closed
- Negative cases cannot become positive decisions
- Publication is gated on every read and write path
- Calibration records exercise the failure mode the schema addresses

## Verification

- Positive, negative, boundary, and replay tests
- All callers/readers of changed symbols inspected
- Staged, unstaged, and untracked scope included
- Contracts and documentation match behavior
- Rollback does not invent or silently discard meaning
