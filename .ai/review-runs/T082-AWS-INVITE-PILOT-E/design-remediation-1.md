# Package E design remediation 1

## Outcome

The Package E design now contains bounded closure designs for both initial
review findings. No implementation, Git staging/commit, AWS/provider call, or
external mutation occurred.

## E-DESIGN-001 — bootstrap connection contract

The design now requires every sealed bootstrap task to receive non-secret
endpoint and port directly from the exact Terraform-managed RDS instance.
`bootstrap.py` must read only username/password from the RDS-managed secret and
must reject missing/invalid endpoint, invalid port, wrong username, secret
endpoint override attempts, and runtime task overrides. The fix is tested with
the realistic managed-secret shape and requires refreshed sealed-image/task
evidence plus independent complete-family review before candidate construction.

This is a prelaunch functional dependency, not generalized hardening. Manually
rewriting the AWS-managed secret is forbidden.

## E-DESIGN-002 — quota-feasible IAM publication

The selected layout preserves the current baseline and publishes the generated
permissions as a separate customer-managed policy:

`arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`

With stable valid fixture inputs, compact JSON sizes are 5,011 characters for
the baseline, 3,731 for the supplement, and 8,704 for the invalid merge. The
merge exceeds AWS's 6,144-character per-managed-policy limit; the two individual
policies fit. The updater proof must cover only the exact supplement lifecycle
and its attachment/detachment on the exact deploy role, using `iam:PolicyARN`
where applicable. Baseline v5 remains unchanged. Deletion is separate authority.

The design now requires hashes, character/attachment/version quota checks,
Access Analyzer and effective simulation. It also states honestly that existing
broad baseline grants remain effective; operator authorization limits are not
misrepresented as IAM denies. A wholesale baseline redesign is deferred because
it is not required to invite the bounded MVP cohort.

## Review boundary and routing

The two fixes form one pre-execution implementation family because both feed the
same clean candidate, sealed bootstrap image and live foundation plan. Route the
builder to Sol high and the independent complete-family reviewer to Astra high.
Candidate construction and all AWS mutation remain blocked until design re-review
passes, implementation passes its independent review, and the two findings are
closed with exact evidence.

- Design remediation builder: `/root/t082_package_e_design_remediation`
- Requested route: GPT-6 Astra xhigh
- Actual model: `model not exposed by runtime`
- Actual effort: `effort not exposed`
- Coordinator: `/root`; model/effort not exposed by runtime

