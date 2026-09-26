# Live v1 policy delta and later-authorized runbook

No AWS mutation is authorized by this artifact.

## Mechanically proved delta

The complete 15-statement live v1 document is fixed at
`backend/tests/fixtures/iam/paprnav-terraform-deploy-pilot-supplement-v1.json`
(file SHA-256 `72050286d45bfabb04a83637e5cfb67f81efe563e7b194001305107838e94100`).
Package C normalizes IAM scalar/list and statement-order differences, then proves
the 16-statement v5 candidate equals live v1 plus only:

1. `acm:GetCertificate` on
   `arn:aws:acm:us-east-1:527257972989:certificate/*`, retaining
   `aws:RequestedRegion=us-east-1`.
2. `wafv2:AssociateWebACL` and `wafv2:DisassociateWebACL` on the additional
   association resource
   `arn:aws:elasticloadbalancing:us-east-1:527257972989:loadbalancer/app/paprnav-pilot/*`.
3. `scheduler:ListSchedules` on `*`, constrained by
   `aws:RequestedRegion=us-east-1`.

Every live condition and all other live action/resource semantics remain exact.
In particular, WAF inventory/creation tags, schedule region, strict secret
creation name/tags, split secret lifecycle, and service-linked-role constraints
are unchanged. Existing baseline reads already cover `DescribeSecret`,
`GetResourcePolicy`, and `kms:DescribeKey`; no new secret-resource-policy or KMS
grant is added. Live v1 and v5 contain no Route 53 grant. Squarespace remains the
DNS authority for `paprnav.com`; Terraform emits only the external
`pilot.paprnav.com CNAME -> <ALB DNS>` handoff.

Candidate: 4,194 compact characters; compact SHA-256
`54e9853b4cb82b6240ddcd05f4b4641124d63d270856acb01e06acd9320eca65`.

## Authorized update and rollback

1. Re-read the policy/default version, all policy versions, both fully paginated
   consumer inventories, deploy-role attachment, and tags. Stop unless v1 is
   still default, the deploy role is the sole permissions-policy consumer,
   boundary use is zero, a version slot is free, and `AuditAttribution=Claude`
   remains present.
2. Generate v5 with `paprnav.com`, `pilot.paprnav.com`, the approved updater ARN,
   and exact recorded KMS ARN. Verify the compact hash above and run Package C,
   saved-plan validation, and IAM Access Analyzer against that exact document.
3. Under separate M1 authorization, create one policy version with
   `SetAsDefault=true`. Do not attach, detach, tag, delete, or alter v1.
4. Re-read versions, consumers, attachment, tags, and effective permissions.
   Confirm the new default hash, sole attachment, unchanged attribution tag,
   the three enumerated deltas, and zero Route 53 actions.
5. On failure, restore v1 semantics using the authority actually available to
   the approved updater. If `iam:SetDefaultPolicyVersion` is available, set v1
   back as default. Otherwise, create a new version from the preserved exact v1
   document with `SetAsDefault=true`. Re-read all state and retain failed
   non-default versions for separately authorized cleanup. Never blind-retry.

## Execution result

The repository operator approved the existing project deploy role as updater.
On 2026-09-25 America/Chicago, session
`arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/botocore-session-1790386879`
created v2 with `SetAsDefault=true`. The mutation created no other AWS object
and did not attach, detach, tag, delete, or alter v1.

Post-state verification found v2 default and v1 preserved; one permissions-
policy consumer (`paprnav-terraform-deploy`); zero permissions-boundary
consumers; unchanged `Project=paprnav`, `Environment=pilot`, and
`AuditAttribution=Claude` tags; and the same two deploy-role attachments. The
live v2 document equals the approved 16-statement candidate. Live
`acm:GetCertificate` and `scheduler:ListSchedules` calls succeeded. AWS IAM
Access Analyzer returned zero findings before publication. Package C passed
with 125 tests and 2 skips. No Route 53 permission was introduced.

The executing role grants `iam:CreatePolicyVersion` but not
`iam:SetDefaultPolicyVersion`. Its tested rollback is therefore to publish the
preserved v1 document as a new default version, restoring v1 semantics without
deleting audit evidence.
