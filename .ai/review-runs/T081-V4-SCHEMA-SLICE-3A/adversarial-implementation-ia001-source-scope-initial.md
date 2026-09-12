# IA-001 source/scope physical-owner sub-slice review

Reviewer runtime identity: `/root/v4_s3a_impl_adversary`  
Packet SHA-256: `0618bbcee0e225440257eb84b8ebde6c2facc3843c8b0b57a7e9e6c2a73bdc61`  
Outcome: **FAIL**

## IA-006: listed serial and part occurrences were mislabeled as models

The canonical designation-scope union permits `listed` for model, serial, and
part-number fields. The implementation created a `model` identity mapping for
every listed value, including serial and part-number values; the apparent
`series` branch was unreachable. The deferred SQL validator repeated the same
classification, so application and database agreed on an invalid meaning.

Required closure: listed model values retain exact model mappings. Listed
serial/part-number values remain exact designation values but have no identity
mapping because the closed identity domain has neither serial nor part number.
Enforce the distinction in application and SQL and add positive and wrong-kind
PostgreSQL vectors.

## IA-007: verified reads did not verify identity/evidence owner semantics

The read verifier compared product and designation values but omitted mapping
semantic identity/parent, evidence parent, origin/state/reason/temporal/
namespace/version/review union, mapping identity hash, and exact inherited
evidence sets. Generic datum reconstruction could therefore pass after typed
identity/evidence corruption.

Required closure: verify every source/scope assertion, mapping, semantic node,
provenance union, deterministic identity, absence case, and exact evidence set
on reconstruction; add a corruption test through the reconstruction endpoint.

Other bounded source/scope behavior was found substantially correct. IA-001
overall remains open for the other physical owner families. No files were
edited by the reviewer.
