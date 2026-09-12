# Adversarial design review: typed-view equivalence amendment

Reviewer runtime identity: `/root/v4_s3a_impl_adversary`  
Packet SHA-256: `80be157ce7a44c6cae0caa6b7c5a5664ac28b1d0195273900bc2b076c971d4d8`  
Outcome: **FAIL**

## Blocker 1: typed-view totality is neither specified nor enforced

The proposed contract names view columns but does not normatively define the
canonical source paths, deterministic row identities, required and optional
joins, cardinalities, nullability, or failure behavior for every union branch.
An incomplete inner join can silently omit an owner occurrence and a left join
can introduce a null that the approved physical schema forbids, while the exact
datum graph remains valid because the views are outside the deferred invariant.

Closure requires a normative mapping and database-verifiable totality,
uniqueness, non-null, and cardinality checks for every view, plus positive and
negative vectors for all closed schema branches. The coordinator rejects this
amendment and returns to the approved physical typed-owner design.

## Blocker 2: database cannot establish validator-2 conformance

The equivalence proof assumes validator-2 has established closed shapes,
references, and acyclicity, but direct SQL can stamp a self-consistent proposal
envelope without executing validator-2. The exact graph can therefore project
invalid canonical content which physical typed CHECK and FK constraints would
reject. This contradicts the direct-SQL threat model.

Closure would require a non-forgeable database validation boundary or an
explicitly narrowed threat model. The coordinator rejects both changes for this
slice and retains the approved physical typed-table boundary.

## High: privilege contract is absent

Structural non-updatability does not define grants, revocations, view security
behavior, or whether application/research roles can query the generic datum
table directly. The proposed view surface therefore does not enforce the
no-generic-query-escape invariant.

Closure would require explicit role privileges and tests under those roles.
Because the equivalence amendment is rejected, this item is dispositioned with
the amendment and does not authorize view implementation.

No files were edited by the reviewer.
