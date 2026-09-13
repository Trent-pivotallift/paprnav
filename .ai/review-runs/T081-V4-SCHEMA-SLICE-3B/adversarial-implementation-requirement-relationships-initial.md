# Adversarial implementation review: Q7/Q9/Q10 requirement relationships

- Task: `T081-V4-SCHEMA-SLICE-3B`
- Stage: bounded implementation review
- Reviewer runtime: `/root/v4_s3b_design_adversary`
- Builder runtime: `/root`
- Reviewed packet SHA-256:
  `fe8fa962c490ae14fcd49cdfad289ec5db8cb8cc38ed78520a6d1cee466b1cd6`
- Verdict: **FAIL**

## Q-REL-IMPL-001 — High — malformed mapping/discriminator inputs leak Python exceptions

The bounded scope claims controlled fail-closed rejection of malformed Q7/Q9/Q10
source shapes. `_validate_requirement_relationship_source` accepts generic
`Mapping` values, although the downstream canonicalizer only serializes exact
`dict` objects, and it tests membership of `terminatingEffect.kind` before
establishing that the discriminator is a string/hashable.

The reviewer reproduced both failures through the public materializer:

- `terminatingEffect.kind=[]` raises raw `TypeError: unhashable type: 'list'`;
- a `MappingProxyType` requirement or terminating-effect object raises raw
  `TypeError: Object of type mappingproxy is not JSON serializable`.

This violates the controlled-rejection invariant and can turn forged or corrupt
trusted-source values into an unclassified 500/error-contract bypass.

Required closure:

1. validate the discriminator type before mapping membership or indexing;
2. align accepted object types with the canonicalizer, either by requiring exact
   dictionaries or by safely normalizing generic mappings;
3. add list/dict discriminator and `MappingProxyType`/`UserDict` regressions at
   both materialize and verified-read rebuild boundaries, all asserting
   `ObligationIntegrityError`.

## Confirmed unaffected invariants

No other blocker or high finding was identified. Independent probes confirmed:

- a custom E -> Q10 -> Q9 three-family cycle rejects while its acyclic analog
  accepts;
- Q7 unions, evidence, semantic identity, and parent/root agreement are coherent;
- Q9/Q10 order, IDs, hashes, target wiring, and restamp/equality checks are
  coherent;
- the candidate validator now charges graph limits by source occurrence;
- the generated Q7/Q9/Q10 contract checks are otherwise coherent.

The reviewer observed 33 focused passing tests and the builder's 163-test
candidate/obligation gate. Persistence and `T081-V4-S3B-DOC-001` remain open and
were outside this bounded review.
