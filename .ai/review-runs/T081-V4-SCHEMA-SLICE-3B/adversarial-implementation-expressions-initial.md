# T081-V4-SCHEMA-SLICE-3B expression-family implementation review — initial

**Verdict: FAIL**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `517a173104ecc8e0b35c1e5efe2c46256f99ee0b7f3487451b2e777e7abb9dfd`

The packet hash matched the assignment and `scripts/verify-review-packet.py`
reported `review packet is current` before review. After I reported the finding
below, the coordinator changed the shared working tree to begin its fix. The
packet consequently became stale during the pass. This report and verdict are
therefore intentionally bound to the exact packet above and are not a review or
PASS of the later working tree.

## Findings

### E-IMPL-001 — High — the claimed global requirement-cycle check omits prerequisite and termination edges

**Violated invariant.** Requirement-state expression references must participate
in the one combined acyclic requirement graph with prerequisite and terminating
edges. The bounded scope expressly claims a global cycle check; the approved
decision says the complete graph combines these edge classes.

**Exact evidence.** In the reviewed `backend/app/services/ad_v4_obligations.py`,
`state_dependencies` starts empty for each requirement, `walk()` adds only
`requirement_state_ref` targets, and the final DFS visits only that map
(`_build_expression_family`, packet lines 1411-1413, 1465-1475, and 1567-1580).
It never reads `prerequisiteRequirementKeys` or
`terminatingEffect.requirementKeys`. By contrast, the normative validator builds
one `requirement_graph` and adds expression, prerequisite, and termination edges
before `_assert_acyclic` (`backend/app/services/ad_v4_candidates.py:622-671`).
The approved decision likewise requires the complete acyclic graph
(`decision.md:115-118, 401-405`).

I independently reproduced acceptance with two otherwise constructible
requirements:

```text
req-a.activationExpression = requirement_state_ref(req-b, unknown)
req-b.prerequisiteRequirementKeys = [req-a]
```

`materialize_expression_family(...)` returned an expression family (`ACCEPTED
2`) instead of raising. The same missing union applies when the reverse edge is
supplied by `terminatingEffect.requirementKeys`.

**Impact.** The pure construction/read oracle can attest an expression family
whose source already contains a combined regulatory dependency cycle. That
contradicts its in-scope safety claim and creates a common-mode gap before the
later persistence check: expression-only tests pass although the complete
requirement graph is invalid.

**Required closure.** Use a shared combined-graph oracle over all three edge
classes, fail unresolved/self/cyclic targets closed, and bind its use to the
generated `graph_cycle_check` contract. Add direct tests for at least:

- expression `A -> B` plus prerequisite `B -> A`;
- expression `A -> B` plus termination `B -> A`;
- an acyclic mixed graph that remains accepted;
- exact aggregate graph-edge resource boundaries without collapsing source
  occurrences in the resource count.

Then rebuild a fresh packet and independently re-run the counterexamples.

## Other bounded results

- The reviewed snapshot materializes all seven expression branches and all
  three contexts. Generated occurrence descriptors supply the three root
  selectors, parents, and ordinals; recursive construction preserves full
  pointers, expression paths, semantic parentage, and operand ordinals.
- `not`, `all`, and `any` arity is enforced. EEDGE identity uses the generated
  ordered preimage `{projectionId, requirementNodeId, context,
  parentExpressionId, childExpressionId, ordinal}`. Rebuilding and complete
  immutable-family equality reject the tested missing, reordered, cross-target,
  cross-projection, restamped, and differently valued rows.
- Q and D dependencies are reverified from the supplied canonical source before
  expression lookup. Requirement-state self-reference and expression-only
  cycles are rejected.
- Slice-3A carriers are internally checked for proposal/projection, allowed node
  type, key-bearing canonical bytes, source-canonical byte round trip, identity,
  prefix, and content hash. The scope correctly does **not** claim this carrier
  is an independent Slice-3A authority. Final integration review must still
  prove carriers are created only after the existing full Slice-3A verified-read
  path; arbitrary `make_applicability_target()` values are not authoritative.
- Source, AST, edge, array, depth, string, and total-node limits are read from the
  generated contract. The long-pointer/repeated-subtree test exercises a pointer
  over 255 characters. Exact large-limit tests remain advisable at closure,
  especially after combining graph edge classes.
- The mapping manifest/digest, generator self-digest and shape pin, recursively
  immutable generated Python, generated SQL selector, union/reference
  descriptors, and physical expression column inventory were inspected. I did
  not find a second blocker/high defect in the bounded snapshot.

## Verification executed

```text
python3 scripts/verify-review-packet.py ... -> review packet is current
.venv/bin/python -m pytest -q tests/test_ad_v4_candidates.py \
  tests/test_ad_v4_applicability.py tests/test_ad_v4_obligations.py
-> 122 passed, 1 warning
```

The green host suite did not include either mixed-cycle counterexample above.
Persistence, API/timing/later families, IA, and DOC-001 were not reviewed or
closed by this bounded pass.
