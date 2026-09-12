# IA-001 source/scope closure review 1

Reviewer runtime identity: `/root/v4_s3a_impl_adversary`  
Packet SHA-256: `f4b0256a82e420170a225a49d121913e954af549500efb6c31e68236f75abc0c`  
Outcome: **FAIL** (`IA-006` PASS; `IA-007` FAIL)

## IA-006: PASS

Listed model occurrences now carry exact model mappings. Listed serial and
part-number occurrences remain exact designation values with null mapping
relations. Application materialization, deferred expected-node accounting,
typed comparisons, verified reads, and PostgreSQL positive/wrong-kind vectors
use the same discriminator. No residual counterexample was found.

## IA-007: FAIL

Mapping rows and their evidence were verified thoroughly, but product,
designation-scope, assertion, value, and range semantic nodes still received
partial read-time checks. Deterministic IDs, identity hashes, node keys,
canonical hashes, projection/proposal identity, and evaluator fields were not
all recomputed. The assertion count was also a lower bound. Administrative
corruption with the immutable UPDATE trigger disabled could therefore pass the
reconstruction endpoint while generic datum rows remained unchanged.

Required closure: use one exact semantic-node verifier for every bounded owner,
make counts exact, verify evaluator fields, and add endpoint corruption vectors
for product/value/range semantic hashes.

No files were edited by the reviewer.
