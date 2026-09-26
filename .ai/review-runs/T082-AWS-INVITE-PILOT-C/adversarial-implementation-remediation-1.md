# Package C remediation-1 review — FAIL

## Model routing

- Reviewer: `/root/t082_pilot_design_adversary`.
- Requested route: GPT-6 Astra, xhigh.
- Actual model: `model not exposed by runtime`.
- Actual effort: `effort not exposed`.
- Trigger: independent review of a complete remediation family after a failed
  infrastructure/IAM/bootstrap implementation review.

## Verified packet and scope

The reviewer verified packet SHA-256
`d0139cfe1eeb6221b4a892ba41fce8502d896bc7538a56f45cc99da280ded4d5`
and packet-current fingerprint
`70e183d789399e905ff8f3649d9dc9e38211f89e32d9b6bbd8c7b600bc6f894b`.
Review covered the remediation files, bound design and history, dirty-tree
exclusions, bootstrap and configuration consumers, release builder,
Terraform/IAM/WAF, retained tests, Docker evidence, and frontend production
dependencies. Ten targeted non-database tests passed with one deselected. No
broad suite was run. No reviewer edit, staging, commit, or cloud action
occurred.

## Findings remaining

### T082-C-010 — High — Invitation WAF normalization remains incomplete

The invitation rate-limit statement applies `URL_DECODE` to the HTTP method,
while its URI regex still uses `NONE`. The routed
`/api/v1/auth/invitations/%61ccept` form therefore remains unthrottled. Login
normalization is fixed.

Close by normalizing the invitation URI predicate, retaining method matching,
and testing encoded and trailing-slash routes against the actual generated
statements without broadening the upload exception.

### T082-C-012 — Medium residual — Certificate ownership can still change

The remediated policy blocks unowned tagging and deletion, but permits
`AddTagsToCertificate` on an owned certificate with `Project` among allowed
keys and does not constrain the new value. An owned certificate can therefore
be changed to `Project=other`.

Close by excluding ownership-key mutation or requiring the ownership value to
remain unchanged, with assertions over the complete request conditions.

### T082-C-014 — Medium residual — Retained oracles are not structurally bound

The WAF regression uses a hard-coded decoding helper and only checks that
`URL_DECODE` appears somewhere, so it passes despite T082-C-010. ACM assertions
likewise miss ownership-value replacement. Three-image construction and
non-root metadata evidence are present. The synthetic first-admin fixture
proves transaction and control behavior, not full migrated-schema
compatibility; that limitation must remain explicit.

Close by binding bounded WAF and ACM oracles to the actual generated field and
condition structures.

### T082-C-015 — High — Production Next.js WebSocket SSRF exposure

The Linux standalone image contains Next.js 16.1.6, and the public ALB/WAF
configuration does not block WebSocket upgrades. Maintainer advisory
GHSA-c4j6-fc7j-m34r identifies crafted upgrade requests against the built-in
Node server as an SSRF path, fixed in 16.2.5.

Close by upgrading the production Next version to a patched release and
rebuilding and revalidating the image, or by implementing and proving the
maintainer's upgrade-blocking mitigation before exposure.

## Closed findings

- C-007: API and worker select the `DATABASE_URL` JSON key, and application
  configuration receives the URL.
- C-008: percent escaping is confined to the Alembic ConfigParser boundary and
  reserved-character cases pass.
- C-009: blocking preconditions bind repository and actual hosted-zone
  identity.
- C-011: all five WAF sampling configurations are disabled.
- C-013: canonical Package A verification precedes construction; reviewed
  inputs and preserved exclusions are separated and protected overlays fail.

## Dependency disposition

The twelve npm audit entries are package-level aggregates, not twelve
demonstrated production exploits. Seven development-tool packages have no
deployed request-controlled path. Three build/transitive packages had no
established deployed exploit path. Next.js and Sharp are present in the
production image: C-015 blocks exposure; the Windows-only RCE is inapplicable
to the inspected Linux image; no current Server Action manifest or
attacker-controlled AVIF input path was established. These conditional
exclusions must be revisited if those features change.

## Residual execution gates

Operator identities and inputs, refreshed AWS policy evidence, a final
committed candidate, pushed image digests, authorized plan, and Package E
deployment/database proofs remain execution gates. Local image IDs are not
deployment digests.
