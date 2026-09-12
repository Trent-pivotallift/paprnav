# IA-001 Normative Matrix — Holistic Design Reassessment

Outcome: **FAIL**  
Reviewer: `/root/v4_s3a_impl_adversary`  
Builder/coordinator: `/root`  
Packet SHA-256:
`c010cdc417c332f799b078b9e91e1000377103d8980fcbc9fa134ec95f490742`

This was a holistic pre-schema design reassessment, not a narrow
implementation closure review. The reviewer found five contract defects:

1. **High — deterministic mapping identity mismatch.** The matrix used
   `sourceOccurrenceNodeId`, while the approved/current restricted-JCS preimage
   uses `occurrence`. Property names change every identity hash.
2. **High — the proposed manifest could not bind executable rules.** It named
   Python functions but did not define a serializable selector/extractor DSL,
   generator contract, or golden generated output.
3. **High — evidence-parent meaning was ambiguous.** Exact occurrence evidence
   and enclosing condition/group/scope evidence may differ, but the matrix did
   not define which set supports a mapping or require both to be checked.
4. **Medium — physical domains were incomplete.** In particular,
   not-applicable reasons are canonical identifiers up to 512 characters while
   the existing assertion owner uses 64 characters; the field-code registry
   and full SQL domain/nullability contract were absent.
5. **Medium — group cardinality excluded all-series groups.** C8 incorrectly
   required at least one model member instead of at least one member across the
   model/series union; H3 needed the same explicit wording and branch vectors.

The reviewer found the proposed `model_or_series` mapping kind source-faithful
and found the expression path, operand ordering, same-projection references,
cycle/orphan rules, and mapping-free serial/part rules conceptually sound.

Required closure is incorporated in the next matrix revision and must be
independently re-reviewed before schema work resumes.
