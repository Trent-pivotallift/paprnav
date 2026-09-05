# Independent design review: T081-V4-SCHEMA-SLICE-2

Reviewer: `/root/v4_schema_adversary`  
Builder: `/root/v4_schema_builder`  
Stage: design  
Outcome: **FAIL**  
Packet fingerprint: `a99f43e490c5b25d0e7c2b957565f3a3954bddbe855bb44f06655d30a8d57b72`

## Gate result

**0 findings closed out of 10.** There are **8 open blockers** and **2 open high-severity findings**. Implementation is not authorized.

## Findings by severity

### Blockers

1. `T081-V4-S2-DA-001` — the service accepts decoded JSON, after duplicate keys and malformed Unicode have already been lost; the required parser boundary is not implementable as written.
2. `T081-V4-S2-DA-002` — canonical set/sequence classification, decimal spelling, evidence-binding serialization, and creation-event serialization are not closed, so cross-process and PostgreSQL hash identity is underdetermined.
3. `T081-V4-S2-DA-003` — slice-1 has no defined current-usability fold or accepted-successor link, and the design does not define locks that prevent a lifecycle transition racing proposal creation.
4. `T081-V4-S2-DA-004` — the advisory lock uses directive plus content hash rather than writer-scope plus idempotency key; concurrent different payloads with one key can race to a uniqueness error instead of deterministic 409. Request-hash equality also contradicts canonical-hash retry equality.
5. `T081-V4-S2-DA-005` — predecessor and correction reason are attached to deduplicated proposal content but excluded from canonical/API identity, so content reuse loses or misattributes correction relationships.
6. `T081-V4-S2-DA-006` — the closed root cannot represent its own five-packet requirements for a shared recurring timing group, non-controlling applicability search hints, and authoritative correction semantics.
7. `T081-V4-S2-DA-007` — the proposed 5/5 gold fixtures have no portable retained-byte -> exact page text -> admitted fragment ID/hash/event construction path; the current Markdown packets contain logical keys and summaries, not executable slice-1 evidence.
8. `T081-V4-S2-DA-010` — the packet omits the calibration corpus and current predecessor closure state, while its bound predecessor `closure.md` incorrectly says CA-002 and final closure re-attestation remain incomplete.

### High

9. `T081-V4-S2-DA-008` — a retained incorporated-document `known` variant cannot be attributed through slice-1 because fragments require an `ad_publications` relationship and the supporting-document workflow is explicitly deferred.
10. `T081-V4-S2-DA-009` — writer scope and exact authorizing membership snapshot are undefined, and provider-shaped provenance is representable before provider authorization is reviewed.

The finding ledger contains the violated invariant, exact repository evidence, impact, and required closure for each ID.

## Confirmed strengths

- New proposal tables are isolated from the current released readers, which continue to select only signed `ad_extraction_v3` rows and their version-bound materializations.
- The candidate-only CHECK/no-selection/no-release boundary is directionally sound.
- The additive migration and occupied-downgrade lock posture is appropriate in concept.
- The design correctly separates canonical proposal content from source text and preserves unknown/fail-closed treatment for the two absent positive supporting-evidence categories.

These strengths do not close the blockers above. A new current packet and independent closure review are required after the ledger is remediated.
