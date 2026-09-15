# Model-routing metadata supplement

This supplement completes the prospective metadata contract for
`adversarial-closure-model-routing-fail-1.md` without rewriting that hash-bound
review report.

## Model routing

Builder/coordinator runtime: `/root`  
Actual builder model: `model not exposed by runtime`  
Actual builder effort: `effort not exposed`  
Reviewer runtime: `/root/model_policy_astra_closure`  
Actual reviewer model: `model not exposed by runtime`  
Actual reviewer effort: `effort not exposed`  
Requested reviewer assignment: `gpt-6-astra`, xhigh  
Trigger: closure re-attestation after recurring failures in the
model-evidence/integration family.

The failed review's own `## Model routing` section already records reviewer
identity, unexposed actual metadata, requested assignment, trigger, and packet
hash. It omitted builder metadata because the reviewer's returned report did
not contain those fields. This supplement is the authoritative prospective
builder/reviewer metadata companion for that immutable report. Requested model
selection is not represented as exposed actual runtime metadata.
