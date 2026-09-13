# T081-V4-SCHEMA-SLICE-3B expression closure review 1

**Verdict: FAIL**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `fa449dd1ae46d12db8b2174b869129769ecb910d4815c6b6047147271ef2b532`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B --stage implementation --base 9ad410b`
reported `review packet is current` immediately before this review and report.

## Targeted E-IMPL-001 closure checks

The original omission is corrected:

- expression `A -> B` plus prerequisite `B -> A` rejects with
  `combined requirement graph cycle`;
- expression `A -> B` plus termination `B -> A` rejects with the same controlled
  error;
- an acyclic mixed expression/prerequisite/termination graph accepts;
- an unresolved source target rejects, and a self edge is detected as a cycle;
- the source-occurrence counter accepts exactly 40,000 edges and rejects the
  40,001st even when that final termination occurrence duplicates an already
  present prerequisite target.

`_verify_combined_requirement_graph` now combines requirement-state expression
dependencies, `prerequisiteRequirementKeys`, and
`terminatingEffect.requirementKeys` (`backend/app/services/ad_v4_obligations.py:1374-1401`).
The expression walk counts every requirement-state source occurrence separately
(`:1464, 1471, 1517-1528`), and construction invokes the combined oracle
(`:1620-1624`). `_validate_expression_contract` also requires the generated
`graph_cycle_check` algorithm (`:1283-1285`).

These changes close the original mixed-edge bypass in substance, but the new
finding below prevents a closure PASS.

## Finding

### T081-V4-S3B-E-IMPL-002 — High — valid deep acyclic requirement chains overflow Python recursion

**Violated invariant.** Every schema-valid graph within the declared source and
graph limits must be handled deterministically. An acyclic graph must not crash
the materializer, and graph failure must fail closed with a controlled integrity
or resource error.

**Exact evidence.** The new DFS is recursive: `visit()` calls itself once per
unvisited dependency hop (`backend/app/services/ad_v4_obligations.py:1403-1418`).
I constructed 1,100 complete, schema-shaped requirement objects using valid
unions, contiguous sequences, evidence, and one forward prerequisite per row:

```text
req-0000 -> req-0001 -> ... -> req-1099
```

This source passes `_canonical_requirement_source`'s 75,000-node resource check,
passes D/Q construction and verification, and reaches the expression combined
graph oracle. `materialize_expression_family(...)` then raises the raw runtime
exception:

```text
RecursionError maximum recursion depth exceeded
```

Calling `_verify_combined_requirement_graph` directly with the same acyclic
chain reproduces the exception. The committed tests arrange their 2,000-node
40,000-edge DAG so lexical traversal visits every backward target first; that
exercises edge count but not dependency depth, and therefore does not expose the
overflow.

**Impact.** A valid, within-budget candidate graph can crash ingestion or
materialization instead of being accepted. This is a material availability and
operability defect at a declared regulatory input boundary. It also makes graph
behavior depend on traversal topology and the interpreter recursion limit rather
than the reviewed resource contract.

**Required closure.** Replace recursive graph traversal with an iterative
three-color DFS/topological equivalent using an explicit stack, preserving
deterministic key ordering and cycle detection. Add durable tests that:

- accept a schema-shaped acyclic chain longer than Python's recursion limit and
  still within `maxTotalNodes`;
- reject a cycle closed at the far end of such a chain with
  `ObligationIntegrityError`, never `RecursionError`;
- retain the mixed prerequisite/termination cases and exact 40,000/40,001
  source-occurrence boundary tests.

Because `backend/app/services/ad_v4_candidates.py:_assert_acyclic` uses the same
recursive pattern, closure should either share the iterative primitive or add a
matching validator regression so source validation and materialization cannot
diverge on the same graph.

## Verification executed

```text
pytest -q tests/test_ad_v4_obligations.py -k 'expression or combined_requirement_graph'
-> 18 passed, 66 deselected

pytest -q tests/test_ad_v4_candidates.py tests/test_ad_v4_applicability.py \
  tests/test_ad_v4_obligations.py
-> 126 passed, 1 warning
```

The independent mixed-cycle, unresolved/self, acyclic-mixed, 40,000/40,001, and
1,100-hop-chain probes described above were also executed. No closure PASS is
issued. DOC-001, later families, persistence, API, IA, and whole-Slice-3B closure
remain out of scope and open.
