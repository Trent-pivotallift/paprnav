# Package E E0 read-only preflight refresh

Date: 2026-09-19. Account: `527257972989`. Region: `us-east-1`.

## Outcome

Read-only inventory confirms that the reviewed separate-policy design is
quota-feasible, but a real updater principal and user-owned DNS/TLS/operational
inputs are still required before any release candidate or mutation packet can
be approved. No AWS resource, policy, state, secret, Git index, or commit was
changed.

## IAM and KMS evidence

- Deploy role `paprnav-terraform-deploy` has one attached managed policy:
  `arn:aws:iam::527257972989:policy/paprnav-terraform-deploy`.
- Account quota permits 20 managed policies per role, so one supplement
  attachment slot is available at this observation time.
- The exact supplement policy
  `arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`
  does not exist.
- Account inventory reports 3 / 1,500 customer-managed policies.
- The baseline policy has all five version slots occupied (v5 default; v1-v4
  non-default). E1A leaves it unchanged, so no baseline version deletion is
  needed for the separate supplement path.
- The proposed fixture role `paprnav-policy-updater` does not exist. The only
  Paprnav-named identities returned were the deploy role and the historical
  `paprnav-terraform-bootstrap` user. Neither is accepted as updater authority
  by inference; the updater must be explicitly selected and granted the reviewed
  exact supplement/attachment proof policy.
- The account's enabled AWS-managed Secrets Manager KMS key is
  `arn:aws:kms:us-east-1:527257972989:key/ea9571ad-3bc5-4ed5-96d9-070bcad47d60`.
  This is non-secret metadata and must still pass the final key-policy/effective
  permission check before use.

## Previously refreshed AWS state retained

- ECS cluster `paprnav-pilot`: active, zero services/tasks.
- No pilot RDS instance.
- API/frontend ECR repositories exist, are empty, and were observed mutable;
  bootstrap repository absent.
- RDS/ECS/ELB service-linked roles absent.
- ACM and Route53 inventories remain denied to the deploy role, so certificate
  and hosted-zone existence cannot be inferred from that role.

These observations are dated inputs, not mutation authority and not a substitute
for the final refreshing preflight.

## Operator inputs still required

1. Canonical pilot hostname, exact public hosted-zone ID/name, exact issued ACM
   certificate ARN, and the certificate/DNS owner authorized to provision or
   validate them if absent.
2. Real budget notification recipient and accountable cost/incident operator.
3. Exact existing human/automation principal that will receive the reviewed
   updater proof policy, plus authority to create and attach the supplement.
   Creating a new updater identity would be a separate reviewed/authorized IAM
   action.
4. First administrator email, display name, and platform organization name;
   secret values are supplied later through the restricted secret channel and
   must not enter this artifact.
5. Named restore, session-revocation, service-stop, and invitation operators;
   initial cohort identities and consent channel before invitations.

Provider/mode/rate/ceiling inputs are not required for the manual cohort and
remain behind the separate paid-OCR gate.

## Model routing

Model routing: read-only execution-prep coordinator → model not exposed by
runtime (effort not exposed). Trigger: deterministic inventory under the
approved Package E design. No fallback or external mutation is claimed.

