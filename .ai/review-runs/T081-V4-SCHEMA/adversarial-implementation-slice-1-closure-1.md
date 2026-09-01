# T081-V4-SCHEMA implementation slice 1 — closure review 1

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: implementation closure  
Decision: **FAIL**  
Packet fingerprint reviewed: `090ebfd5058adce0695b7fd91d425b0aa6dea47d60ca67d6580fe94172f90c1d`

## Outcome

**3 findings closed out of 7 submitted for closure.** IA-001, IA-005, and
IA-007 are independently proven closed. IA-002, IA-003, IA-004, and IA-006
remain `fixed_pending_verification` because the isolated PostgreSQL wrapper was
interrupted before returning a result. A new blocker, IA-008, was found by
direct trigger counteranalysis. The implementation gate remains **FAIL**.

## Closure replay

| Finding | Result | Closure evidence |
|---|---|---|
| T081-V4-IA-001 | CLOSED | Current packet binds decision, ledger, proposal, and slice declaration; packet verifier passed with the fingerprint above. |
| T081-V4-IA-002 | NOT CLOSED | Composite source-chain FKs and integrity triggers are present, but the same fragment trigger still admits a claimed end offset beyond the page text; see IA-008. The PostgreSQL runtime replay did not complete. |
| T081-V4-IA-003 | NOT CLOSED | Root, predecessor, sequence, canonical hash, deferred admission, and reuse checks are present by inspection. Critical PostgreSQL negative execution did not complete, so closure is not asserted. |
| T081-V4-IA-004 | NOT CLOSED | Downgrade now acquires `ACCESS EXCLUSIVE` locks before preflight and the two-session test is structurally appropriate. The actual race replay did not return a result. |
| T081-V4-IA-005 | CLOSED | New rendition bytes are read through the configured backend and checked for hash, length, PNG validity, and dimensions before row creation; corrupt-readback test passed. |
| T081-V4-IA-006 | NOT CLOSED | Harness expects head 0025 and test source covers all four tables, but the wrapper was interrupted and therefore did not substantiate its 14/14 claim in this review. |
| T081-V4-IA-007 | CLOSED | GET is now read-only and 404s before materialization; explicit idempotent POST creates the artifact. Authorization and side-effect tests passed. |

## New blocker

### T081-V4-IA-008 — out-of-bounds selectors and copied parser provenance remain database-valid

**Violated invariant:** PostgreSQL authority must constrain every selector to
the referenced immutable text and bind extraction provenance to that text
version.

The fragment validation trigger derives text using PostgreSQL `substring` but
does not check `character_end <= char_length(authoritative_text)`. PostgreSQL
silently truncates an overlong substring. A direct caller can therefore submit
`character_end` beyond the page length, store the truncated result as
`exact_text`, and calculate the canonical hash with the false larger end. The
trigger accepts the row. The same trigger neither compares copied
`parser_name`/`parser_version` with the referenced text-version row nor includes
them in fragment identity.

**Required closure:** add an authoritative upper-bound check, constrain or
remove copied parser provenance, update canonical identity if provenance is
retained, and run direct PostgreSQL negative tests for both counterexamples.

## Verification performed

- Refreshed packet freshness and explicit-input binding: **1 passed out of 1**.
- Focused evidence/API suite: **5 passed out of 5**.
- Full isolated PostgreSQL/migration wrapper: **0 completed out of 1**. It was
  interrupted after approximately nine minutes without returning output. Its
  cleanup trap succeeded; a read-only database check found **0** leftover
  `paprnav_t081_verify_*` databases. `paprnav_db` was not targeted.
- PostgreSQL closure claims: **0 independently credited**. Code and test-source
  inspection were completed, but no runtime pass is inferred from an
  interrupted command.

The packet is expected to become stale when this ledger and immutable review
artifact are recorded. A builder remediation packet must bind IA-008's fix and
fresh PostgreSQL evidence before another closure review.
