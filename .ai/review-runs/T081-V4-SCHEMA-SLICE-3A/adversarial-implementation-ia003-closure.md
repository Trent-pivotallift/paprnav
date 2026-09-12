# Targeted implementation closure: IA-003

Date: 2026-09-09  
Reviewer: `/root/v4_s3a_impl_adversary`  
Builder/coordinator: `/root`  
Packet SHA-256: `a3084bacf0b883bbe3d1da74553671ab69635560de9a82ed9e3c1b64064e47cf`

## Verdict

**PASS.** No residual IA-003 finding.

## Independent closure evidence

- Canonical successor identity is compared exactly before resolution; unknown,
  mismatched, missing, and ambiguous targets remain non-resolved and create no
  target-local row or stale event.
- Deterministic outgoing dependencies resolve only to one exact predecessor AD
  projection. Each resolved signal creates one deterministic target-local
  incoming dependency, and the stale event names that exact same-projection
  cause through a composite foreign key and canonical cause envelope.
- PostgreSQL derives the proposal's own, predecessor, and successor AD numbers,
  sorts/deduplicates them, and obtains deterministic transaction advisory locks.
  The application, direct projection INSERT trigger, and deferred validator use
  the same database helper, closing both application and direct-SQL phantom
  predecessor races.
- Causal partial unique indexes, deterministic hashes, deferred global
  uniqueness validation, and direct-SQL negative coverage prevent forged,
  duplicate, or cross-projection event causes.
- PostgreSQL tests 09-11 cover exact, mismatched, and ambiguous resolution;
  test 12 covers both concurrent application orderings; test 13 proves a raw
  projection INSERT blocks on the database-native AD lock.
- The clean disposable PostgreSQL matrix passed 14/14. Focused host tests passed
  36/36 and the broader relevant host/calibration/API suite passed 50/50. All
  disposable databases were removed and `paprnav_db` was not targeted.

The reviewer also verified downgrade dependency order: tables/triggers are
removed before the advisory-lock helper, leaving no dangling dependency.
