# AD Coverage And Cost Attribution Refinement

Date: 2026-07-26

Status: complete for the fixture-backed reuse and attribution loop

## Result

Paprnav now treats the DRS corpus as a platform-shared, versioned source.
Aircraft onboarding materializes or reuses coverage for normalized airframe and
installed-component identities. A later client with a previously resolved
identity receives an association to the same coverage; the source is not
downloaded, extracted, or stored again for that client.

The implementation follows decision D023 in `.ai/DECISIONS.md`.

## Implemented Path

1. A manually entered/verified aircraft identity is normalized into active
   airframe, engine, propeller, rotorcraft, drivetrain, and appliance component
   facts where present.
2. Each fact resolves to an `ApplicabilityTarget`.
3. Paprnav reuses or creates the target's single `ADCoverageSet`.
4. The coverage references the latest retained complete DRS source snapshot and
   records a content-derived coverage version.
5. `ADCoverageSubscription` associates the client organization and aircraft,
   retaining whether that aircraft first triggered creation.
6. Identity changes deactivate obsolete associations instead of deleting their
   history.
7. DRS snapshot import refreshes already-materialized coverage.
8. AD matching uses only verified logbook entries and records aircraft-specific
   comparison usage.

No coverage resolver performs a network download. Missing source data produces
`awaiting_source_snapshot`; a target without parsed applicability produces
`pending_applicability`; partial source data produces `degraded_source`.

## Cost Boundary

`ADCostLedgerEntry` separates:

- `shared_source`: physical DRS/source storage and source processing;
- `coverage_set`: reusable applicability materialization and estimated logical
  storage;
- `aircraft`: coverage association and AD/logbook comparison work.

Actual incurred cost and allocated cost are separate fixed-precision values.
The initial entries use zero cost where pricing is not calibrated. This means
"uncalibrated and unallocated," not "free."

The first triggering client is retained for provenance. Billing is explicitly
inactive, no allocation policy is active, and the first client is not assigned
the shared source/setup cost.

## Admin View

`GET /api/v1/admin/ad-costs` and `/admin/ad-costs` are restricted to an active
`platform_admin` membership. They show:

- retained DRS snapshots and physical storage bytes;
- target coverage grouped by component type, make, and model;
- coverage/source version and freshness status;
- AD and source-document counts;
- estimated logical coverage storage;
- clients and aircraft benefiting from each coverage;
- the first-trigger relationship;
- actual cost and separate allocated cost.

Estimated logical coverage bytes are labeled separately from physical source
storage and must not be combined into a customer invoice.

## Verification

- dedicated reuse and attribution fixtures: **2 passed out of 2**;
- focused DRS/AD/matching/MVP regression: **23 passed out of 23**;
- complete backend regression: **105 passed out of 105**;
- Alembic migration heads: **1 passed out of 1**, head
  `20260726_0016`;
- PostgreSQL offline migration SQL generation: passed;
- frontend lint: passed with **0 errors** and one pre-existing image warning;
- frontend production build: **1 passed out of 1**, including
  `/admin/ad-costs`;
- repository diff whitespace validation: passed.

The two-client fixture retained one DRS source snapshot, created three reusable
coverage sets for airframe/engine/propeller, created six aircraft associations,
and created **0 duplicate source snapshots**.

## Corpus Boundary

This loop used controlled AD/DRS and aircraft fixtures only. It did not use the
22-page full-product validation partition or the 11-page final holdout. Those
remain reserved for the integrated ingestion, human review, identity,
applicability, matching, adjudication, and worklist stages.

## Remaining Work Before The 22-Page Partition

- Reconcile and harden live DRS source retrieval and Federal Register
  enrichment/delta monitoring.
- Expand applicability fixtures for serial ranges, conditional requirements,
  component installation history, twin engines, appliances, and rotorcraft.
- Add calibrated AWS/storage/provider costs to the ledger without activating
  customer allocation.
- Harden the durable worker claim/retry/dead-letter path.
- Exercise the full verified-entry-to-AD-worklist path with controlled
  fixtures, including recurring, superseded, negative, and unresolved cases.
- Predeclare the 22-page full-product acceptance report before opening that
  partition.
