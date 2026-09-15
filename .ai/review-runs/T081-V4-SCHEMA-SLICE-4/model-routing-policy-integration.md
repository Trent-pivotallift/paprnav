# Model-routing policy integration evidence

## Model routing

Builder/coordinator runtime: `/root`  
Actual builder model: `model not exposed by runtime`  
Actual builder effort: `effort not exposed`  
Initial requested verification route: `gpt-5.6-terra` medium  
Escalated verification route: `gpt-5.6-terra` high  
Closure re-attestation route: `gpt-6-astra` xhigh

Routing trigger: the policy edit was localized and mechanically checkable. The
first substantive verification failure increased effort. The second failure in
the same evidence/integration family escalated the complete next pass to Astra
and stopped narrow artifact-by-artifact patching.

Delegated runtime evidence:

- `/root/v4_s4_design_adversary` later reported `model not exposed by runtime`
  and `effort not exposed` for its pre-policy design, implementation, and
  closure reviews. The coordinator checkpoint's Astra description is retained
  only as requested-assignment evidence, not claimed as actual runtime metadata.
- `/root/model_routing_policy_verifier` reported `model not exposed by runtime`
  and `effort not exposed`; it found the missing authoritative model-evidence
  location.
- `/root/model_routing_policy_closure` reported `model not exposed by runtime`
  and `effort not exposed`; it found that the active run's final packet did not
  yet bind the new policy and prospective evidence.
- `/root/model_policy_astra_closure` reported `model not exposed by runtime`
  and `effort not exposed`; the coordinator requested and the runtime accepted
  the Astra xhigh assignment for the final re-attestation.

## Complete integration invariant

Every file intended to share the active Slice-4 commit must be hash-bound into
one current closure packet. Model-evidence requirements apply prospectively
from adoption: immutable reports completed before the policy was written are
not rewritten, while `closure.md`, this integration evidence, and the fresh
closure re-attestation must contain the required actual/unexposed metadata and
routing history.

The final independent reviewer must verify:

- `AGENTS.md` preserves all existing requirements and mandates the linked
  repository policy;
- `.ai/MODEL_ROUTING.md` covers tiers, escalation, separation, dynamic
  availability, notices, review evidence, closure summary, and project-subagent
  mechanics;
- the policy and all active implementation files are present in the fresh
  packet manifest with no unexplained out-of-scope dirty file;
- the prior Slice-4 implementation fingerprint and implementation content
  remain unchanged; and
- the run validates only after the fresh closure re-attestation is recorded.

## Third-loop oracle and file coverage

After the third unsuccessful evidence/integration review, implementation stayed
paused. `adversarial-closure-model-routing-fail-1.md` records the failed Astra
pass. The missing shared oracle is this exhaustive classification of the dirty
commit-intended tree:

1. **Manifest-bound source and policy files:** `AGENTS.md`,
   `.ai/MODEL_ROUTING.md`, and all 23 Slice-4 implementation, migration,
   contract, and test files. `build-review-packet.py` hashes these directly in
   `manifest.json`.
2. **Hash-bound stable review inputs:** the decision, findings ledger, closure
   report, normative matrix, implementation verification, this integration
   evidence, all eleven historical adversarial reports, the failed model-routing
   re-attestation report, and its prospective builder/reviewer metadata
   supplement. Each is passed explicitly as a review input in the final packet;
   none may change after review.
3. **Generated self-reference exceptions:** `manifest.json`,
   `review-packet.md`, and `review-packet.sha256` cannot include their own final
   hashes. The reviewer verifies the packet SHA and manifest entries directly.
4. **Append-only attestation exceptions:** `reviews.json`, `state.json`, and the
   final re-attestation artifact necessarily change or appear only after the
   reviewer returns. Their pre-attestation hashes are anchored below. The
   coordinator must use `record-review.py --reattest`, which verifies the frozen
   packet/fingerprint before appending the new artifact hash and transition,
   then run `validate-review-run.py` to verify review identity separation,
   artifact hashes, phase, and closure coverage.

Pre-attestation bookkeeping anchors:

- `reviews.json`: `9efa540f04696a060afb22cc192c5a30966820f5c613b531017eb575b945d2e2`
- `state.json`: `3907588bbb6e20c5e9164c06d2b8916ef2eb238eec2fa111f335589a9e811b2a`

Only categories 3 and 4 are exempt from direct stable-input binding. Any other
dirty commit-intended file missing from the final manifest or review-input list
is a closure blocker. Reviewer self-report is the oracle for actual model and
effort; requested assignment is recorded separately and never substituted.

No standalone commit is authorized by this evidence.
