# T081-V4-SCHEMA-SLICE-3B expression closure review 2

**Verdict: FAIL**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `bd0a93a1988a8f7a3a10326af97d21f0c0c8cfa5df0788ae45dbcfd6110a6278`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B --stage implementation --base 9ad410b`
reported `review packet is current` immediately before this report.

## Targeted closure results

The bounded obligation expression helper now passes all direct closure attacks:

- expression `A -> B` plus prerequisite `B -> A` rejects;
- expression `A -> B` plus termination `B -> A` rejects;
- the valid acyclic mixed graph accepts;
- unresolved prerequisite/termination targets reject and self edges are cycles;
- exactly 40,000 source edge occurrences accept, while a 40,001st occurrence
  rejects even when it duplicates an existing target;
- public `materialize_expression_family` accepts a 1,100-hop acyclic chain and
  rejects the corresponding long cycle with `ObligationIntegrityError`.

The explicit-stack three-color traversal in
`backend/app/services/ad_v4_obligations.py:1403-1423` is deterministic, has no
Python call-stack dependence, and showed no false positive or false negative in
the bounded probes. The combined source-edge construction and generated
`graph_cycle_check` gate remain intact. This closes E-IMPL-001 and the expression
helper portion of E-IMPL-002 in substance.

## Residual finding

### T081-V4-S3B-E-IMPL-002 — High — the required trusted-source validator still overflows on the same valid chain

**Violated invariant.** Materialization and its mandatory canonical-source
validation boundary must agree for every schema-valid, within-budget graph and
must not depend on Python recursion depth. The E scope accepts only trusted
canonical requirements, so normal validation must be able to establish that
trust for every graph the public E materializer claims to support.

**Exact evidence.** `backend/app/services/ad_v4_candidates.py:_assert_acyclic`
still implements recursive DFS (`:527-543`). I constructed an actual complete
validator-2 request envelope with:

- 1,100 schema-valid requirements and contiguous sequence strings;
- one shared valid evidence binding;
- valid action, branch, timing, recurrence, termination, and applicability
  references;
- a forward acyclic requirement-state chain
  `req-0000 -> req-0001 -> ... -> req-1099`;
- encoded request size 742,487 bytes, below the 2,000,000-byte limit, and source
  node count below the 75,000-node limit.

`parse_v4_request_bytes(...)` succeeds. `validate_v4_envelope(...)` then raises:

```text
RecursionError maximum recursion depth exceeded
```

The failure occurs in the source-validation graph DFS before the now-iterative
expression materializer can be reached. This is part of the source validation
and trusted-canonical dependency boundary, not the excluded API or persistence
implementation.

**Impact.** The E helper and validator disagree at a declared valid boundary.
A normal within-budget candidate that the corrected expression materializer can
represent cannot be validated, producing an uncontrolled availability failure.
E-IMPL-002 is therefore not closed end to end.

**Required closure.** Replace candidate `_assert_acyclic` with an iterative
three-color/explicit-stack traversal or a genuinely shared stack-safe graph
primitive. Preserve the validator's controlled `ADV4Error("cyclic_reference")`
behavior. Add normal-envelope tests, not only direct obligation-helper tests,
that:

- accept the 1,100-hop acyclic requirement-state chain through
  `validate_v4_envelope`;
- reject the corresponding long cycle with `ADV4Error.code ==
  "cyclic_reference"`, never `RecursionError`;
- retain the obligation materialization long-chain tests and mixed-edge/resource
  boundary tests.

Rebuild a fresh packet and independently rerun both validator and materializer
paths.

## Verification executed

```text
pytest -q tests/test_ad_v4_obligations.py -k 'expression or combined_requirement_graph'
-> 19 passed, 66 deselected, 1 warning
```

Independent direct probes covered both mixed cycles, acyclic mixed construction,
missing/self targets, 40,000/40,001 duplicate source occurrence counting, and
the public E materializer's 1,100-hop acyclic/cyclic paths. The separate complete
742,487-byte validator envelope reproduced the residual raw recursion failure.

No PASS is issued. DOC-001, later families, persistence, API, IA, and whole
Slice-3B closure remain out of scope and open.
