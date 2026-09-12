# T081 V4 Slice 3A Strategy Reset

The following direction governs the main task from 2026-09-10:

> Change strategy for T081-V4-SCHEMA-SLICE-3A immediately.
>
> Stop the counterexample-by-counterexample micro-patching loop. Do not discard existing work, stage, commit, or begin another narrow implementation review.
>
> First, stabilize and reassess the current working tree:
>
> 1. Record the latest reviewer result and preserve all existing valid fixes.
> 2. Keep IA-001 open. Do not claim completion based on partial owner families.
> 3. Produce one complete normative mapping matrix covering every canonical V4 applicability shape:
>    - canonical path and union branch
>    - semantic-node type, key, parent, pointer, ordinal, and deterministic identity
>    - physical typed-owner table and row identity
>    - required/optional columns and nullability
>    - evidence owner, purpose, cardinality, and inheritance
>    - identity-mapping behavior and absence cases
>    - references, child cardinalities, ordering, and failure behavior
>    - Python materialization rule
>    - PostgreSQL commit-time rule
>    - read-time verification rule
>    - positive and direct-SQL corruption tests
>
> Cover all remaining families together in the matrix: conditions/value assertions/designation groups and members, expressions and edges, rules and exclusions, and search hints/groups/members. Include the already implemented product/designation family so inconsistencies are visible.
>
> Before further schema edits, identify where Python, SQL, and read verification duplicate rules. Propose a construction that minimizes three-way drift—prefer a declarative specification and shared test oracle or generated expectations. Explain any rules that must remain independently implemented for defense in depth.
>
> Then implement IA-001 in complete, meaningful families rather than tiny counterexample patches:
>
> - conditions + value assertions + designation groups/members
> - expressions + edges + rules/exclusions
> - search hints + groups/members
> - final global exactly-one-owner and full reconstruction/evidence verification
>
> For each family, complete its full schema-valid union matrix and negative tests before requesting adversarial review. Do not send a review packet whose closure claims exceed the implemented checks.
>
> Required final gates:
>
> - every semantic node has exactly one matching physical typed owner;
> - no extra, missing, reordered, cross-projection, misclassified, or differently valued owner graph can commit through direct SQL;
> - materialization, PostgreSQL validation, and read verification agree for every closed union branch;
> - the five calibration packets round-trip exactly;
> - reconstruction GET fails closed on typed-owner, identity, evidence, hash, reference, and cardinality drift;
> - clean host and freshly migrated disposable PostgreSQL suites pass;
> - the independent reviewer closes IA-001 with no residual blocker.
>
> Continue using the adversarial-review process and preserve builder/reviewer separation. The reviewer system is finding real defects; the strategy change is to provide it with complete invariant-driven families instead of successive marginal patches. Do not commit until IA-001, implementation review, and closure review all pass.
