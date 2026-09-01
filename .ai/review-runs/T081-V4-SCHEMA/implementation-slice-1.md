# T081 V4 schema — implementation slice 1 evidence

Status: **builder complete; independent implementation review not yet recorded**

## Implemented boundary

This slice implements only immutable, deduplicated retained-source evidence and
correct relevant-page navigation. It does not implement V4 canonical JSON,
normalized applicability/requirement persistence, catalog cutover, publication,
or the menu/form reviewer.

The slice adds:

- immutable content-addressed PNG renditions of verified retained PDF pages;
- read-after-write verification of each new rendition through its configured
  storage backend, including SHA-256, byte count, PNG validity, and dimensions;
- immutable bounded native-text versions bound to the rendition and retained
  source hash;
- one exact, server-derived single-page clause fragment stored once and reused
  by ID/hash rather than copied into each future semantic consumer;
- append-only admitted lifecycle events with one canonical admission root,
  sequence/predecessor constraints, server-validated event hashes, and
  PostgreSQL mutation-rejection triggers for all four evidence tables;
- platform-admin-only page materialization and fragment admission endpoints;
- database-enforced transitive retained-document/directive/publication,
  source-hash, rendition, text-version, and page identity plus server-validated
  page-text, exact-selection, fragment-hash, selector-bound, and non-empty
  checks;
- authoritative `character_end <= char_length(page_text)` enforcement plus
  parser name/version equality with the selected text version; parser
  provenance is part of the canonical fragment hash in Python and PostgreSQL;
- per-source explicit relevant page numbers, start/end metadata, contiguity,
  and `#page=` navigation used by the current admin review GUI;
- `SELECT ... FOR UPDATE` serialization on the attributable source document so
  concurrent same-document admissions cannot race unique row creation.

Existing V3 proposal, review, publication, materialization, and released-read
behavior is unchanged.

## Authorization and audit boundary

Explicit idempotent page materialization POST and fragment admission call the
existing platform-administrator gate. Ordinary GET is read-only: it returns a
verified existing artifact or 404 and never renders, stores, inserts, or
commits. Owner and maintenance-shop accounts receive 403 and cannot inspect or
mutate this global evidence workflow. The API commits only after the fragment
and its admitted lifecycle event are both flushed. Exact clause text is never
accepted from the client; the client sends only offsets and expected hashes.

## Migration behavior

Revision `20260830_0025` is additive after `20260823_0024`.

- Upgrade creates four constrained tables, composite transitive FKs, canonical
  hash/integrity triggers, lifecycle admission/chain constraints, indexes, and
  immutable update/delete triggers. It also adds document/hash and
  directive/document candidate keys needed by the composite FKs.
- Empty downgrade to `20260823_0024` succeeds and removes the slice atomically.
- Downgrade first holds `ACCESS EXCLUSIVE` locks on all four evidence tables,
  then checks emptiness. Occupied downgrade fails before any DDL with `Revision
  0025 contains immutable AD evidence`; verified backup/restore is required
  rather than evidence deletion. A two-session race proves an evidence commit
  that overlaps downgrade makes downgrade wait and then refuse.
- Empty downgrade followed by upgrade succeeds.

PostgreSQL rehearsals used the isolated databases
`paprnav_t081_v4_slice1_remediate` and `paprnav_t081_v4_slice1_empty`.
`paprnav_db` was not migrated or mutated.

## Verification

- Backend focused regression/API tests: **58 passed out of 58**.
- PostgreSQL two-session concurrency, transitive-integrity, lifecycle,
  immutability, and downgrade-race verifier: **2 passed out of 2**.
- Frontend production build/type check: **1 passed out of 1**.
- PostgreSQL migration rehearsals: **4 passed out of 4** (upgrade, occupied
  downgrade rejection, empty downgrade, re-upgrade).

Negative coverage includes wrong retained document, stale/wrong source hash,
page outside the bounded AD section, stale page-text hash, reversed and
out-of-range selectors, tampered retained PDF bytes, newly written or reused
tampered rendition bytes, maintenance-shop GET and POST denial, GET
side-effect-freedom, and explicit noncontiguous page metadata. PostgreSQL
rejects direct-SQL source-chain mismatch, forged lifecycle hashes, and an
otherwise valid fragment without an admitted root. It also rejects an
overlong selector that PostgreSQL `substring` would otherwise truncate and a
forged copied parser identity even when the caller calculates a matching hash.
Lifecycle negatives reject a predecessor root owned by another fragment. A
two-session race to append different sequence-1 successors to the same root
produces exactly one committed canonical transition and one unique-sequence
rejection, leaving no fork.
UPDATE and DELETE are
rejected on rendition, text version, fragment, and lifecycle rows. Two
simultaneous admissions both return successfully, exactly one reports
creation, both return the same fragment ID, and the database contains exactly
one rendition, one text version, one fragment, and one admitted event.

The closure-2 PostgreSQL replay used the isolated database
`paprnav_t081_v4_slice1_closure2`: **2 passed out of 2** in 1.62 seconds. The
database was force-dropped afterward and a read-only inspection found no
slice-verifier database or one-off container residue.

The closure-3 replay added the exact cross-fragment predecessor and concurrent
successor cases and ran the complete focused PostgreSQL file against fresh
`paprnav_t081_v4_slice1_closure3`: **2 passed out of 2** in 1.71 seconds. The
temporary database was dropped after the run.

## Deterministic PostgreSQL verification

`scripts/verify-t081-v4-slice1-postgres.py` is the slice-only verifier for
IA-002, IA-003, IA-004, IA-006, and IA-008. It builds the current image, creates
one validated temporary database, rehearses 0025 upgrade/empty downgrade/
re-upgrade, runs the two focused PostgreSQL tests, confirms head, and drops the
database in `finally`. Every subprocess has a 15–90 second timeout (45 seconds
for the cached build) and a global deadline reserves cleanup and bounds total
wall time to 170 seconds.

The broader `verify-t081-postgres-migrations.sh` is preserved because it also
tests older V3 repair migrations. It is not used as the slice-1 closure proof:
it has no outer or per-command timeout, suppresses output for guarded
downgrades, and launches unrelated legacy concurrency scripts whose non-daemon
workers are only joined with a timeout but are not failed or terminated when
still alive. A blocked database worker can therefore keep the Python process
and one-off container alive indefinitely while concealing the active phase.

## Accepted-design narrowing and deferred work

- This slice supports one page-text selection only and enforces
  `page_end = page_start`. Cross-page/table child selections and coordinate maps
  are deferred to a later reviewed slice; the current schema cannot falsely
  represent a multi-page claim with one text version.
- Page renditions are actual server-rendered PNG bytes (not text mislabeled as
  a rendition). The bounded native-text version is stored in PostgreSQL rather
  than a separate text object; its exact UTF-8 hash is immutable.
- `directive_id` is carried on the fragment in addition to the accepted design
  fields. This prevents a fragment from an adjacent AD in the same full-issue
  PDF from being rebound across directives.
- Native-text-empty/scanned pages and unavailable Poppler rendering fail closed.
  Reviewed OCR/coordinate artifacts remain future work.
- A failed database transaction can leave an unreferenced content-addressed PNG
  object. It cannot become evidence without the hash-bound rows; deterministic
  garbage collection is future operational work.
- V4 decision bindings and approval/release re-verification are intentionally
  absent until later slices. Nothing in this slice makes a candidate
  actionable or released.
