# Independent review: sealed migration authority architecture

## Outcome

**PASS — architecture only.** The amendment replaces the incomplete import-name
blacklist with a sound boundary: arbitrary checkout files never enter the
privileged execution context. Unknown future DBAPI or dependency names cannot
gain authority through repository shadowing.

Reviewed amendment SHA-256:
`eb675256176e509132834eb673d3bf7b494e1229d97e32788fa4220416482f51`.

No architecture blocker/high remains. Implementation is not approved;
`T082-A-002` remains open pending implementation and execution evidence.

## Required implementation evidence

- Define exact source-to-destination mapping, especially
  `backend/alembic.ini` to `/migration/alembic.ini`, while preserving package
  and SQL-relative paths.
- Validate raw Git names, modes, hashes, and exact output inventory without
  following symlinks or reusing an existing destination.
- Include positive controls proving injected modules execute under the
  vulnerable invocation but not the sealed invocation. Preserve actual DBAPI
  loading and check canonical import origins, not only sentinel output.
- Require the migration secret at launch; missing configuration may not fall
  back to development credentials. Secrets stay out of manifests, image layers,
  and diagnostics.
- Preserve context integrity during execution with a read-only context and
  explicit bytecode suppression; `python -I` alone is insufficient.
- The later AWS/image owner must bind interpreter, installed dependencies,
  startup hooks, context, and command to the immutable image/task definition;
  mounts, editable installs, or overrides cannot reintroduce checkout files.

Package A's local oracle proves construction and import isolation, not container
filesystem isolation or PostgreSQL success. Those remain later gates.

## Model routing

- Architecture author: `/root`; actual model `model not exposed by runtime`;
  actual effort `effort not exposed`.
- Reviewer: `/root/t082_pilot_design_adversary`; GPT-6 Astra xhigh requested;
  actual model `model not exposed by runtime`; actual effort
  `effort not exposed`.
- Trigger: independent architecture review after the third repeated
  release-authority/oracle failure.
