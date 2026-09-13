# T081-V4-SCHEMA-SLICE-3B expression closure review 3

**Verdict: PASS**

**Reviewer runtime identity:** `/root/v4_s3b_design_adversary`

**Reviewed packet SHA-256:** `2773f8f5a961f8b89a846bc3cc7fadd0d9a63fef7884a4ef53c8d93bb10fe800`

The packet hash matched the assignment and
`scripts/verify-review-packet.py --task T081-V4-SCHEMA-SLICE-3B --stage implementation --base 9ad410b`
reported `review packet is current` immediately before this report.

No blocker or high finding remains in the bounded EACT/EBR/EREC/EEDGE
construction and trusted-source boundary. E-IMPL-001 and E-IMPL-002 are closed
in substance by the evidence below; ledger disposition remains the coordinator's
responsibility.

## Closure evidence

### Shared stack-safe cycle oracle

`backend/app/services/ad_v4_graph.py:first_cycle_node` implements deterministic
iterative three-color DFS with an explicit stack. Both required paths call this
same primitive:

- candidate validation: `backend/app/services/ad_v4_candidates.py:528-531`;
- obligation combined graph: `backend/app/services/ad_v4_obligations.py:1375-1405`.

The primitive assumes a closed string-key graph. That assumption is satisfied
before invocation: candidate validation resolves every rule, requirement,
correction, and supersession target into its registry; the obligation builder
resolves requirement-state leaves against the verified Q family and explicitly
rejects unresolved prerequisite/termination targets. I found no caller that
passes an open graph.

I compared `first_cycle_node` with an independent Kahn-cycle oracle across 4,800
random closed directed graphs containing self edges, disconnected components,
cross edges, DAGs, and cycles. Results agreed in every case. Long-chain behavior
uses heap stack depth rather than Python call-stack depth.

### E-IMPL-001 mixed graph and resource closure

Independent reruns confirmed:

- expression `A -> B` plus prerequisite `B -> A` rejects with
  `combined requirement graph cycle`;
- expression `A -> B` plus termination `B -> A` rejects identically;
- a valid acyclic expression/prerequisite/termination graph accepts;
- unresolved cross-edge targets reject and self edges are detected as cycles;
- exactly 40,000 source edge occurrences accept;
- a 40,001st termination occurrence rejects even when it duplicates an already
  present prerequisite target, proving graph-set deduplication cannot conceal
  resource consumption.

The obligation walk increments `expression_reference_count` for every source
`requirement_state_ref`, while the combined helper separately adds every
prerequisite and termination source occurrence before comparing with the
generated `maxGraphEdges`. The generated `graph_cycle_check` contract gate
remains mandatory.

### E-IMPL-002 validator/materializer agreement

I reconstructed the actual prior counterexample as a complete validator-2
request envelope:

- 1,100 schema-valid requirements with contiguous sequence strings;
- one shared valid evidence binding and otherwise valid closed unions;
- forward requirement-state chain
  `req-0000 -> req-0001 -> ... -> req-1099`;
- encoded length 742,487 bytes, below the 2,000,000-byte request limit and within
  the source-node budget.

`parse_v4_request_bytes` plus `validate_v4_envelope` accepts the acyclic
envelope. Closing the last node back to `req-0000` rejects with controlled
`ADV4Error.code == "cyclic_reference"`; no `RecursionError` leaks.

The exported `materialize_expression_family` likewise accepts a 1,100-hop
acyclic family (1,100 expression owners) and rejects its closed cycle with
`ObligationIntegrityError("combined requirement graph cycle")`. Validator and
materializer therefore agree at the formerly failing trusted-source boundary.

## Regression evidence

```text
pytest -q tests/test_ad_v4_candidates.py::test_semantic_validator_handles_long_requirement_chains_without_python_recursion \
  tests/test_ad_v4_obligations.py -k 'test_semantic_validator_handles_long_requirement_chains_without_python_recursion or expression or combined_requirement_graph'
-> 20 passed, 66 deselected, 1 warning

pytest -q tests/test_ad_v4_candidates.py tests/test_ad_v4_applicability.py \
  tests/test_ad_v4_obligations.py
-> 128 passed, 1 warning
```

The bounded expression implementation may advance. This PASS does not close
DOC-001, later Slice-3B families, persistence, API integration, IA, or whole-
Slice-3B implementation/closure review; all remain explicitly open.
