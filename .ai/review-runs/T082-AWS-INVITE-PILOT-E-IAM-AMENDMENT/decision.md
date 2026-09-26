# Decision packet: T082-AWS-INVITE-PILOT-E-IAM-AMENDMENT

## Objective

Close the remaining static authorization gaps between the current Paprnav pilot
Terraform graph and the separately published
`paprnav-terraform-deploy-pilot-supplement` before any AWS IAM mutation.

This amendment covers deployment authority and its deterministic oracle. It
does not grant administrator access, publish a policy, attach a policy, create
DNS/certificates, apply Terraform, or change application runtime roles.

## User-visible outcome

The operator can publish one quota-feasible supplemental policy which lets the
existing deploy role plan and manage every service in the current invite-only
pilot graph. Paprnav runtime tasks continue to receive only their existing
purpose-specific S3, Textract, and secret permissions.

## Safety and correctness invariants

1. The existing baseline policy v5 remains byte-for-byte unchanged and
   attached. The amendment changes only the generated separate supplement.
2. Every lifecycle action required by the current Terraform configuration is
   either authorized at least privilege or recorded as an explicit fail-closed
   stop gate. Service-prefix presence alone is not evidence of completeness.
3. EventBridge Scheduler authority is limited to the exact
   `default/paprnav-pilot-worker` schedule in account `527257972989`, region
   `us-east-1`.
4. Terraform may pass only the exact
   `paprnav-pilot-worker-scheduler-role` to `scheduler.amazonaws.com` for the
   schedule target. Existing ECS pass-role authority is not widened.
5. WAF tag reads required to reconcile provider `default_tags` are limited to
   the existing Paprnav WAF resource ARN patterns.
6. The supplement remains within the AWS 6,144-character customer-managed
   policy limit and still requires one available role attachment slot.
7. The publication principal is separate from the deploy role and is proved to
   create/version/tag only the exact supplement and attach/detach only that
   supplement on the exact deploy role. Deletion remains separately authorized.
8. Application runtime roles remain separated: frontend has no task policy;
   API has Paprnav artifact-bucket access; worker has the same bucket plus
   Textract; execution/bootstrap roles retain only their stated secret needs.
9. No permission is pre-granted for deferred services such as SES, Cognito,
   third-party OCR, or future background systems. Adding a service requires a
   new authority amendment.
10. Route 53 mutation authority permits only A-record changes for the canonical
    pilot hostname; every name and type in a batch must match. Zone reads remain
    separate, and unrelated/ACM-renewal records cannot be changed.
11. `secretsmanager:UpdateSecret`, `GetSecretValue`, and `PutSecretValue` stay
    outside the deploy supplement. Terraform may create the declared secret
    metadata, but a later description/KMS change is an explicit stop requiring
    separate review and authority because AWS couples metadata and value writes
    under `UpdateSecret`.
12. Publishing or versioning an existing supplement requires a complete
    pre-state consumer inventory. Rollback restores its prior default version
    and attachment state; it never detaches a policy that was already attached.
13. The M1 updater must be a named MFA-protected principal or a federated
    session with recorded strong-authentication provenance. Root-account MFA
    posture is a release gate and is never compensated for with broader IAM.

## Current behavior

Live read-only checks on 2026-09-20 show:

- `paprnav-deploy` assumes
  `arn:aws:iam::527257972989:role/paprnav-terraform-deploy` in `us-east-1`;
- the role has only
  `arn:aws:iam::527257972989:policy/paprnav-terraform-deploy` attached, default
  version `v5`, with no inline policy or permissions boundary;
- both the deploy role and source user
  `arn:aws:iam::527257972989:user/paprnav-terraform-bootstrap` are denied
  `route53:ListHostedZones` and `acm:ListCertificates`;
- bootstrap-user policy inventory is itself denied, so that user's ability to
  publish the supplement is unknown and must not be inferred; and
- the v5 baseline covers EC2/VPC, ELB, ECS, ECR, RDS, logs/CloudWatch, budgets,
  Paprnav S3, Paprnav IAM roles/policies, KMS, SSM, and older Paprnav secret ARN
  patterns, but has no ACM, Route 53, WAFv2, or Scheduler authority.

The previously reviewed supplement closes ACM, Route 53, WAFv2, current secret
paths, KMS-description, and exact service-linked-role gaps. Static comparison
against `aws_scheduler_schedule.worker` found two omissions:

- schedule CRUD/read actions; and
- `iam:PassRole` of the schedule's exact target role to
  `scheduler.amazonaws.com`.

WAF resources inherit provider `default_tags`, but the supplement also omits
`wafv2:ListTagsForResource`, which the provider needs to reconcile `tags_all`.

The initial independent design review also proved that zone-wide Route 53
writes and unconditional existing-policy rollback were too broad, and that
Secrets Manager metadata updates cannot be granted without also authorizing
value writes. Live account-summary evidence reports `AccountMFAEnabled=0` and
`MFADevicesInUse=0`; this does not exclude external federation, but no updater
session may execute M1 until strong-authentication provenance is recorded.

## Proposed design

Amend the generated deploy supplement with these bounded authorities:

| Family | Actions | Resource and condition |
| --- | --- | --- |
| Scheduler inventory | `scheduler:ListSchedules` | `*`, `aws:RequestedRegion=us-east-1` |
| Exact worker schedule | `scheduler:GetSchedule`, `CreateSchedule`, `UpdateSchedule`, `DeleteSchedule` | `arn:aws:scheduler:us-east-1:527257972989:schedule/default/paprnav-pilot-worker` |
| Scheduler target pass-role | `iam:PassRole` | exact `arn:aws:iam::527257972989:role/paprnav-pilot-worker-scheduler-role`, `iam:PassedToService=scheduler.amazonaws.com` |
| WAF tag reconciliation | `wafv2:ListTagsForResource` | existing Paprnav regional web-ACL and regex-pattern-set ARN patterns |
| Exact DNS alias mutation | `route53:ChangeResourceRecordSets` | exact hosted zone plus `ForAllValues:StringEquals` for normalized record name=`pilot_hostname`, record type=`A`, and action in `CREATE`,`UPSERT`,`DELETE` |
| Policy consumer preflight | `iam:ListEntitiesForPolicy` | exact supplement ARN; caller checks both permissions-policy and permissions-boundary uses before any version change |

Split Route 53 read and write statements. Reads remain limited to the exact zone
where resource scoping is supported; `GetChange` and hosted-zone inventory stay
read-only. The change statement uses AWS Route 53 batch condition keys so a
mixed request containing any other name or type fails as a whole.

Retain the approved ACM, WAF, secret, KMS, and three exact service-linked-role
statements. Explicitly deny by omission `secretsmanager:UpdateSecret`,
`GetSecretValue`, and `PutSecretValue` for the deploy role. The current secret
descriptions are supplied during `CreateSecret`; any later Terraform plan that
requires `UpdateSecret` stops before apply and returns for separate review.

Extend the policy matrix and focused test from service-family presence to an
explicit resource/lifecycle/action oracle, including the deliberate secret
update stop. Recompute compact policy sizes and hashes; former size constants
are evidence from the superseded generator and must change.

The full pilot permission partition is:

| Principal | Current pilot purpose | Permission families |
| --- | --- | --- |
| Named policy updater | publish/attach supplement only | exact IAM supplement lifecycle, pre-version consumer inventory, and exact role attachment |
| Terraform deploy role | state, images, foundation, DNS alias, cost controls, disabled worker schedule | STS/IAM read; S3 state/artifacts; ECR; VPC/ELB/WAF; ECS; RDS; Secrets metadata/lifecycle without value reads; Route 53; ACM read; logs; budgets; Scheduler; constrained pass-role/service-linked-role |
| ECS execution roles | pull images, publish logs, inject declared secrets | AWS execution managed policy plus exact API/worker secret ARNs |
| API task role | upload/logbook artifacts | exact Paprnav artifact bucket objects/list |
| Worker task role | OCR artifacts and Textract | exact artifact bucket plus Textract detect/start/get |
| Frontend task role | no AWS API use | no task policy |
| Bootstrap task roles | one fixed database/bootstrap phase | exact required secret reads/writes only |
| Scheduler target role | launch disabled worker when later enabled | exact worker task definition/cluster and exact worker role pass-through |

This matrix is complete for actions required by the configuration currently
declared in `infra/terraform`, with `UpdateSecret` explicitly represented as a
stop gate rather than silently missing. It is not a promise that an undeclared
future feature already has permission.

## Alternatives considered

- **Add only Route 53 and ACM list actions now:** rejected because it would
  require another policy version before Terraform can manage WAF, secrets, and
  Scheduler, and would conceal known launch blockers.
- **Merge into baseline v5:** rejected; the prior design review reproduced that
  the baseline plus supplement exceeds AWS's 6,144-character managed-policy
  limit.
- **Attach AWS managed full-access policies or AdministratorAccess:** rejected;
  materially broader than the pilot graph and weakens rollback/evidence.
- **Remove the disabled worker schedule:** rejected for this amendment because
  it is part of the approved pilot graph. Keeping it disabled bounds spend; its
  deployment authority must still be correct.
- **Grant `scheduler:*` on `*`:** rejected because Scheduler supports exact
  schedule ARNs and exact target-role pass-through.
- **Grant `secretsmanager:UpdateSecret` for metadata convenience:** rejected
  because the same API can write a secret value. Description/KMS changes stop
  for separate review instead.
- **Accept zone-wide DNS mutation:** rejected because Route 53 exposes condition
  keys for normalized names, record types, and batch actions.

## Trust, authorization, and audit boundaries

The user has requested a step-by-step permission path but has not yet authorized
an IAM mutation or identified a principal proven able to publish the supplement.
Design, code, local tests, AWS read-only inventory, and independent review are
authorized; policy creation/versioning/attachment remains a separate explicit
M1 gate.

The deploy role must not be used to edit its own attached authority. The
candidate updater is `paprnav-terraform-bootstrap`, but its updater permissions
are unknown because it cannot list its own policies. A human administrator must
either prove that exact updater policy or use another named MFA-protected
principal. No secret values are required for this work.

The M1 authorization record must name an accountable human owner and bind the
actual updater session ARN plus its MFA/federation provenance. Current
`AccountMFAEnabled=0` and `MFADevicesInUse=0` evidence is a high operational
concern. Before external invitation, the owner must either enable root-account
MFA or prove centralized root-access controls that intentionally remove direct
root credentials; before M1, the updater session itself must independently be
strongly authenticated.

## Read paths and consumers

- AWS CLI/SDK read-only identity, IAM, Route 53, ACM, WAF, Scheduler, quota, and
  resource inventory;
- Terraform AWS provider 5.100.0 plan/refresh for every declared resource;
- `scripts/generate_pilot_deploy_policy.py`;
- `infra/aws-iam/pilot-policy-matrix.json`;
- Package C focused authorization tests; and
- Package E execution/preflight evidence.

## Write paths and administrative paths

Repository implementation changes are limited to the generator, matrix,
focused tests, and this amendment's evidence. After independent review and
explicit M1 authorization, the named updater may create or version only
`paprnav-terraform-deploy-pilot-supplement` and attach only that policy to
`paprnav-terraform-deploy`.

Terraform apply, DNS/certificate mutation, image pushes, secret population,
service activation, and schedule enablement remain outside this amendment.

## Migration, compatibility, correction, and rollback

There is no data migration. The baseline policy stays attached. Publication is
additive and reversible:

1. record supplement existence, every version/default hash, exact role
   attachment state, attachment/version quotas, and results of
   `ListEntitiesForPolicy` for both permissions-policy and permissions-boundary
   use;
2. when the supplement exists, stop before versioning unless its only permitted
   consumer is the exact deploy-role attachment state recorded in pre-state and
   it has zero permissions-boundary use;
3. create the policy when absent or create/set one new version when the clean
   existing-policy preflight passes;
4. attach it only when the exact deploy role was not already attached;
5. verify post-state and effective positive/negative permissions;
6. on failure, restore the prior default version when one existed and restore
   the exact prior attachment state: detach only a newly attached supplement,
   retain one that was already attached, and leave a previously detached policy
   detached; and
7. delete versions or the policy only under separately recorded deletion
   authorization and after reproving zero unexpected attachments or boundary
   use.

If the actual updater cannot perform these exact actions, stop. Do not widen
the deploy role or use administrator access as a workaround.

## Test strategy

- Deterministically enumerate each Terraform AWS resource/data source and map
  its create/read/update/delete or read-only lifecycle actions to baseline,
  supplement, or an explicit stop gate; ignore local-only
  `aws_iam_policy_document` only by recorded rule.
- Assert exact Scheduler schedule ARN, four schedule actions, regional list,
  exact target-role ARN, and `iam:PassedToService=scheduler.amazonaws.com`.
- Assert WAF tag-read coverage without widening ARN patterns.
- Assert Route 53 reads are separated from writes; direct and mixed-batch
  changes fail unless every normalized record name is the canonical hostname
  and every type is A.
- Assert deploy authority excludes `UpdateSecret`, `GetSecretValue`, and
  `PutSecretValue`, and bind the metadata-update stop gate to the current secret
  resources.
- Test publication state transitions for absent, detached-existing,
  attached-existing, shared-policy, permissions-boundary, and partial-failure
  cases. Only the first three clean branches may proceed and rollback must
  reproduce exact pre-state.
- Preserve ACM, service-linked-role, updater, and separately authorized
  deletion assertions.
- Recompute policy compact size/hash and prove each individual policy fits the
  6,144-character limit while the merged policy remains disallowed.
- Run Access Analyzer validation on the exact generated document before
  publication and, when the updater identity is known, effective-policy
  simulation for required allows and forbidden negatives.
- After attachment, rerun previously denied Route 53/ACM reads plus Scheduler,
  WAF, secret, and service-linked-role inventory. A denied call remains unknown,
  not evidence of absence.
- Submit the coherent amendment once to an independent Astra reviewer; do not
  create separate review turns for each permission or generated artifact.

## Expected file scope

- `.ai/review-runs/T082-AWS-INVITE-PILOT-E-IAM-AMENDMENT/**`
- `scripts/generate_pilot_deploy_policy.py`
- `infra/aws-iam/pilot-policy-matrix.json`
- `backend/tests/test_pilot_package_c.py`
- Package E operator/preparation evidence only if needed to bind live findings

No Terraform resource, application source, database/model/migration, T081, Git
index, or AWS resource belongs in this implementation scope.

## Known uncertainty

- The owned hostname, Route 53 zone ID/name, and exact ACM certificate ARN are
  still unknown because both available identities are denied discovery.
- The bootstrap user's updater authority is unknown; listing its policies is
  denied.
- The actual MFA-protected or federated updater principal/session and
  accountable owner are not yet supplied; M1 is blocked.
- Root-account MFA or centralized root-access-removal evidence is not yet
  supplied; external pilot release is blocked.
- Organization SCP/session-policy effects and live service quotas are not yet
  proved.
- A live Terraform refresh/plan can reveal provider calls absent from static
  analysis; any new permission must return through this bounded review rather
  than be patched ad hoc during apply.

## Model routing

- Designer/coordinator: `/root`.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: AWS IAM authorization design, least-privilege invariant synthesis,
  and a newly discovered central deployment blocker; Astra high/xhigh is the
  preferred policy tier.
- Independent design reviewer: separate subagent, requested GPT-6 Astra xhigh.
