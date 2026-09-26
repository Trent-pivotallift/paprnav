# Package E2 candidate and image preparation

Date: 2026-09-20  
Status: no-mutation scope partition complete; candidate commit, image build,
push, Terraform plan, and AWS execution not started.

## Outcome

The current dirty tree is completely partitioned for candidate construction:

| Class | Paths | Disposition |
| --- | ---: | --- |
| Pilot release source/tooling inputs | 70 | eligible for the clean candidate after exact review and commit authorization |
| T082 review/evidence paths | 118 | retained as audit evidence; final inventory waits for this package's reviewer artifact |
| Preserved T081 Slice 4B paths | 145 | excluded from the pilot candidate |
| Forbidden 0030/protected-model paths | 10 | excluded; the candidate must use the approved baseline model blob |
| Unclassified dirty paths | 0 | any future unclassified path stops construction |

The canonical JSON projection of the 70 release-source entries as
`{path,sha256,sizeBytes}`, sorted by path, currently hashes to
`0c4e7361004a11243d1a777ff78b0f152d2b6bbc21a82a43b558845e477e1ed0`.
This is construction evidence, not a candidate commit or release approval.

That digest and the matching-manifest counts below are historical pre-amendment
evidence after `T082-AWS-INVITE-PILOT-E-IAM-AMENDMENT` changes the IAM
generator, matrix, and focused test. Do not use them for candidate construction;
recompute the complete candidate inventory only after the amendment's
independent implementation and closure reviews pass.
The amendment also adds `scripts/pilot_iam_authority.py`; include that operational
authority in the recomputed reviewed release-source inventory. The historical
70-path list/count is not the current construction allowlist.

## Eligible release-source inventory

```text
.ai/MODEL_ROUTING.md
.ai/PILOT_RELEASE_BOUNDARY.md
.ai/pilot-package-c-context-v1.json
.ai/pilot-release-boundary-v1.json
backend/.env.example
backend/Dockerfile
backend/app/api/deps.py
backend/app/api/routes/admin.py
backend/app/api/routes/ads.py
backend/app/api/routes/aircraft.py
backend/app/api/routes/auth.py
backend/app/api/routes/ingestion.py
backend/app/api/routes/logbook_entries.py
backend/app/api/routes/observability.py
backend/app/api/routes/uploads.py
backend/app/core/config.py
backend/app/core/http_protocol.py
backend/app/core/request_context.py
backend/app/main.py
backend/app/schemas/auth.py
backend/app/schemas/observability.py
backend/app/scripts/revoke_auth_sessions.py
backend/app/scripts/run_ocr_feasibility.py
backend/app/services/ingestion.py
backend/app/services/invitations.py
backend/app/services/pilot_achievements.py
backend/app/services/pilot_summary.py
backend/app/services/session_revocation.py
backend/pilot_server.py
backend/requirements.lock
backend/tests/test_ad_matching.py
backend/tests/test_pilot_invite_tenant_boundary.py
backend/tests/test_pilot_package_c.py
backend/tests/test_pilot_package_d.py
backend/tests/test_pilot_privacy.py
backend/tests/test_pilot_release_boundary.py
frontend/paprnav-frontend/.dockerignore
frontend/paprnav-frontend/.env.example
frontend/paprnav-frontend/Dockerfile
frontend/paprnav-frontend/next.config.ts
frontend/paprnav-frontend/package-lock.json
frontend/paprnav-frontend/package.json
frontend/paprnav-frontend/src/app/(auth)/invite/page.tsx
frontend/paprnav-frontend/src/app/(auth)/page.tsx
frontend/paprnav-frontend/src/app/(auth)/register/page.tsx
frontend/paprnav-frontend/src/app/(authenticated)/observability/page.tsx
frontend/paprnav-frontend/src/app/api/backend/[...path]/route.ts
frontend/paprnav-frontend/src/lib/api.ts
frontend/paprnav-frontend/src/lib/pilot-ocr-summary.ts
frontend/paprnav-frontend/tests/pilot-observability.test.mjs
infra/aws-iam/pilot-policy-matrix.json
infra/bootstrap/Dockerfile
infra/bootstrap/bootstrap.py
infra/bootstrap/grant-manifest.json
infra/bootstrap/reference-data.json
infra/bootstrap/requirements.in
infra/bootstrap/requirements.lock
infra/terraform/database.tf
infra/terraform/ecs_runtime.tf
infra/terraform/load_balancer.tf
infra/terraform/main.tf
infra/terraform/network.tf
infra/terraform/outputs.tf
infra/terraform/tests/package_c.tftest.hcl
infra/terraform/variables.tf
infra/terraform/versions.tf
scripts/build_pilot_migration_context.py
scripts/build_pilot_release_context.py
scripts/generate_pilot_deploy_policy.py
scripts/verify_pilot_release_boundary.py
```

The final candidate review must compare every entry with the applicable A-D,
privacy, and E1A implementation/review packet. A path appearing here is not by
itself proof that every current byte is approved.

The latest parent, B, C, ACM-amendment, D, privacy-amendment, and E manifests
jointly bind 69 of these 70 paths. All 69 current files match their latest
manifest hashes byte-for-byte, with zero missing or drifted paths. The remaining
path is `.ai/MODEL_ROUTING.md`; it is repository operating policy rather than a
runtime/build input and has a separate independent policy review history. The
candidate review must nevertheless inventory it explicitly.

## Preserved forbidden inventory

```text
backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_contract.json
backend/app/db/migrations/sql/20260916_0030_candidate_acceptance_integrity.sql
backend/app/db/migrations/versions/20260916_0030_add_ad_v4_candidate_acceptance.py
backend/app/models/core.py
backend/app/services/ad_v4_acceptance_persistence_contract.py
backend/tests/test_ad_v4_acceptance_persistence.py
backend/tests/test_ad_v4_acceptance_persistence_postgres.py
backend/tests/test_ad_v4_model_source_authority.py
backend/tests/test_ad_v4_model_source_authority_postgres.py
scripts/generate-ad-v4-acceptance-persistence.py
```

All paths under `.ai/review-runs/T081-V4-SCHEMA-SLICE-4B/` are also preserved
outside the candidate. No preserved file was modified or removed.

## Boundary checks

- `HEAD` remains baseline `19fe8e2e170687ed65deed78cb1af99d60f601e9`.
- The expected `HEAD` verifier failure is exactly the target configuration
  amendment: committed `backend/app/core/config.py` is old, while the working
  target hash equals policy hash
  `a9015bedd4362c5cbfc3bda6b05ccce4e92984c958b8087d4dd8d10344562cf4`.
- The committed protected `backend/app/models/core.py` hash equals policy hash
  `be50bfb1009cd24b1787cf2ceeff1377e92a82c2825aaa74023dec74852ae7ac`.
  The dirty protected model has a different hash and is excluded.
- The migration graph at `HEAD` retains sole head `20260913_0029`; all other 43
  migration-authority blobs match policy and no excluded path is committed.
- Every A-E finding ledger currently has zero unresolved entries. This does not
  substitute for exact-candidate or E2 independent review.

## Focused verification

- Recomputed partition after adding these E2 artifacts: 343 dirty paths = 188
  candidate/evidence paths + 145 preserved T081 paths + 10 forbidden paths;
  zero unclassified. The candidate side contains 70 release-source paths and
  118 T082 evidence paths.
- Recomputed the 70-path canonical inventory digest: exact match with
  `0c4e7361004a11243d1a777ff78b0f152d2b6bbc21a82a43b558845e477e1ed0`.
- Recomputed latest-manifest coverage: 69 bound paths, 69 byte-for-byte
  matches, zero drift or missing files.
- Parsed the release/context/IAM/bootstrap JSON authorities successfully.
- Repository `git diff --check`: pass.
- Product tests and image builds were not repeated because this slice changes
  only execution-preparation evidence and the daily scoreboard. Their retained
  hashes remain unchanged.

## AWS identity refresh

Read-only configuration and STS checks on 2026-09-20 verified that AWS profile
`paprnav-deploy` assumes
`arn:aws:iam::527257972989:role/paprnav-terraform-deploy` from source profile
`paprnav-bootstrap` in `us-east-1`. The role has a one-hour maximum session,
Paprnav/pilot/Codex tags, and no permissions boundary. The role remains denied
Route 53 hosted-zone listing and ACM certificate listing, so it cannot discover
or prove the hostname, zone, or certificate. No AWS state was changed.

## Next bounded actions

1. Receive the non-secret hostname/zone/certificate, budget owner, exact updater
   principal/session plus accountable owner and MFA/federation provenance,
   root-access posture evidence, and first-admin identity in
   `e2-operator-inputs.md`.
2. Receive explicit authorization to construct the clean release commit. Do
   not stage or commit the broad dirty tree.
3. Construct the candidate from the 70 reviewed release-source paths plus the
   final T082 evidence set while restoring the approved protected model blob and
   excluding T081/0030.
4. Run Package A verification on that commit, then build and verify the API,
   frontend, bootstrap, and sealed migration contexts from the commit without
   overlays.
5. Build and inspect linux/amd64 images locally. ECR creation, mutability
   changes, pushes, and Terraform planning remain separately gated.
6. Submit one complete E2 family packet to an independent Astra reviewer.

## Model routing

- Builder/coordinator: `/root`; requested GPT-5.6 Sol high; actual model
  `model not exposed by runtime`; actual effort `effort not exposed`.
- Trigger: coherent candidate/image preparation under the approved Package E
  design. Independent Astra review is deferred until the complete family packet
  exists.
