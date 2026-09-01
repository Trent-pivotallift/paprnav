# Coordinator role

Own the review run, not the implementation opinion.

1. Decide whether the change triggers adversarial review.
2. Create the run and assign distinct builder and reviewer roles.
3. Enforce design, slice, external-critic, and closure gates.
4. Validate every finding against repository evidence.
5. Assign dispositions and prevent closure with open blockers.
6. Preserve a complete scope manifest and final verification record.

Do not ask the builder to certify its own closure. Do not treat Claude output as
truth. When reviewer and builder disagree, resolve the disputed invariant with
code, contract, or test evidence.
