# ACM amendment design review — PASS

## Model routing

- Designer: `/root`.
- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested reviewer route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: ambiguous certificate ownership authority discovered after a
  repeated high-risk implementation finding.

## Outcome

No blocker or high finding. Operator-provisioned ACM ownership is a simpler,
viable invite-pilot boundary. This approves design only, not implementation or
deployment.

## Provider and authorization contract

Pinned AWS provider 5.100.0 supports exact primary-domain lookup with
`statuses = ["ISSUED"]`, `types = ["AMAZON_ISSUED"]`,
`tags = { Project = "paprnav" }`, and `most_recent = false`, which rejects
ambiguous matches. It returns ARN, domain, status, and tags. Certificate type
is established by the fixed selection filter because there is no singular
returned `type` attribute. The operator contract and lookup must also select a
supported key algorithm; RSA_2048 is sufficient for this pilot.

Blocking checks must bind returned metadata to the exact supplied ARN, account,
region, and primary hostname. The lookup must remain plan-time with known
inputs, and the HTTPS listener must consume its verified result.

The complete read-only lookup requires exactly:

- `acm:ListCertificates`
- `acm:DescribeCertificate`
- `acm:ListTagsForCertificate`
- `acm:GetCertificate`

`GetCertificate` returns the public certificate and chain, not the private key.
No ACM mutation or `ExportCertificate` permission is required. Candidate
discovery occurs before tag filtering, so account/region-bounded certificate
metadata reads are acceptable and do not manufacture ownership.

## Handoff, correction, and state

Removing certificate, validation, and validation-record resources is coherent;
the application alias and HTTPS listener remain the intended consumers.
Package E must verify actual backend/state before execution. If any removed
resource address exists, execution stops for a separately reviewed state
handoff because configuration removal could otherwise schedule destruction.

Operator evidence must retain certificate identity, issuance/type, primary
hostname, ownership, DNS-validation evidence, principal, and timestamp.
Validation records remain in place for renewal. Replacement preserves the
currently serving certificate until the new attachment is verified. Multiple
matching owned certificates intentionally block planning; no automatic delete
or retag resolution is allowed.

## Verification and scope

Packet SHA-256 matched
`b6783d36b68c063dc820e50160e406fc7742f556ffce0a81dca9cc7f8eeb7ea6`.
Packet-current verification passed with fingerprint
`31841c31563b1ab64932fe9d4933ef5b0e8ea90dafac620bf34b687615639cf2`.
The reviewer inspected the amendment, parent design/review/remediation history,
current Terraform/IAM generator/tests and consumers, committed baseline, and
dirty inventory. Provider schema extraction was blocked by uninitialized
backend configuration, so conclusions use the exact pinned provider source.
No files changed, tests ran, or cloud actions occurred during review.
