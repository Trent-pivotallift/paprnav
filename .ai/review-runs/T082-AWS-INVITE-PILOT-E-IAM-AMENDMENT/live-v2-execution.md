# Live IAM supplement v2 execution

Date: 2026-09-25 America/Chicago (`2026-09-26T02:24:47Z` in AWS).

## Authorization and scope

The repository operator explicitly approved the three-delta supplement update
and selected the existing project role
`arn:aws:iam::527257972989:role/paprnav-terraform-deploy`. The executing session
was `arn:aws:sts::527257972989:assumed-role/paprnav-terraform-deploy/botocore-session-1790386879`.

The authorized mutation was limited to creating one new default version of
`arn:aws:iam::527257972989:policy/paprnav-terraform-deploy-pilot-supplement`.
No resource attachment, detachment, deletion, tag change, or Route 53 authority
was authorized or performed.

## Pre-state and candidate evidence

- Default/version inventory: v1 was the sole version and default.
- Consumers: deploy role was the sole permissions-policy consumer; zero
  permissions-boundary consumers.
- Tags: `Project=paprnav`, `Environment=pilot`, and
  `AuditAttribution=Claude`.
- Live v1 matched the committed fixture semantically.
- Candidate: 16 statements, 4,194 compact characters, compact SHA-256
  `54e9853b4cb82b6240ddcd05f4b4641124d63d270856acb01e06acd9320eca65`.
- Candidate matched live v1 plus only `acm:GetCertificate`,
  `scheduler:ListSchedules`, and WAF association authority for the exact pilot
  ALB pattern.
- AWS IAM Access Analyzer findings: none.
- Package C: 125 passed, 2 skipped.

## Mutation and verified post-state

AWS created v2 as default at `2026-09-26T02:24:47Z`. Live v2 matched the
approved candidate semantically. V1 remains non-default and unchanged. Consumer
counts, tags, and deploy-role attachments remain unchanged. Read-only probes
confirmed `acm:GetCertificate` for the issued pilot certificate and
`scheduler:ListSchedules` in `us-east-1` are effective.

## Rollback

The executing role has `iam:CreatePolicyVersion` but not
`iam:SetDefaultPolicyVersion`. If rollback is required, publish the preserved
v1 document as a new version with `SetAsDefault=true`, verify restored v1
semantics and consumers, and retain v2 for audit until separately authorized
cleanup. Four version slots remained before v2; three remain afterward.

## Toolchain evidence

The repository Terraform executable is
`.data/tools/terraform/1.15.8/terraform`. The downloaded official HashiCorp
Darwin arm64 archive matched published SHA-256
`f210110c5698b94d803a7a63cdb0251b5455c150841478808e2bbb343f95ed68`,
and its extracted executable was byte-for-byte identical to the repository
copy (binary SHA-256
`ec83c7c64d8eb67b2d7c37935d6bcbe93b4ec3533b1ee223a8fb07daa098f9e8`).
Terraform configuration validation passed with the locked AWS provider 5.100.0
outside the filesystem sandbox; the initial sandbox failure was solely a denied
local plugin-socket bind.

Per the operator's earlier direction, this bounded AWS path did not add a
separate adversarial reviewer turn. Deterministic policy-delta, Access Analyzer,
live post-state, and rollback evidence were retained instead.
