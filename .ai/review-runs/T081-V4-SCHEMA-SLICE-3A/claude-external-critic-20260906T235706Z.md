## 1. Scope Limitations

- This review run has **no code diff**. `git diff HEAD` and the packet's own "Diff against base" section are both empty; the working tree is clean except for the untracked `.ai/review-runs/T081-V4-SCHEMA-SLICE-3A/` review-run directory itself. The task is therefore a pure **design-decision review** (`decision.md`, embedded twice in the packet plus two internal adversarial rounds), not a review of implemented code, migrations, or tests.
- No AWS/IAM/Terraform/billing artifacts exist in this scope; the design is entirely a PostgreSQL/FastAPI schema-and-service proposal, so those review dimensions do not apply here.
- I independently re-derived the five v2 hash-domain hex strings (proposal, evidence-bindings, candidate-event, submission, submission-relationship, subtree, projection) in Python and they match the packet byte-for-byte. I cross-checked the design's characterization of the current schema (`ad_extraction_v4.schema.json`), migration `20260901_0026`, and calibration fixtures against the actual files in the repo; every specific claim I checked (condition subject shape, search-hint shape, expression node types, `changedSemanticRef` namespace enum, `officialDocument` shape, existing v1 hash domains, existing "any active membership" auth helper, existing deferred-constraint-trigger precedent, absence of a feature-flag mechanism) was accurate.
- I did not re-derive every one of the 28 numbered invariants line-by-line against every calibration fixture (e.g., full 224-row and 182-row cardinality re-enumeration); I relied on spot checks plus the internal adversary's already-closed, evidence-backed findings for those, per instructions not to repeat adequately-closed findings.
- Because there is no implementation yet, several of my observations are about the decision document's internal consistency and enforceability rather than runtime defects.

<!-- CLAUDE_FINDINGS_JSON -->
```json
[
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-001",
    "severity": "medium",
    "invariant": "Every other safety/correctness invariant in this design is enforced by the database or application transaction rather than by operator discipline (e.g., invariant 2's 'creation-time validity is not trusted'); the staged validator-2/3A rollout should meet the same bar.",
    "summary": "The mandatory deployment order (apply 0027 -> dual-reader app -> enable v2 writer -> enable 3A routes) has no concrete code-level gate. The codebase has no existing feature-flag mechanism, so nothing prevents a rolling deploy from serving v2 writes or 3A routes from an instance before all instances are dual-readers.",
    "evidence": [
      "review-packet.md:1262-1269 'Deployment order is mandatory: 1. apply 0027 ... 2. deploy the compatibility application ... 3. enable the v2 writer after all serving instances are dual readers; and 4. enable the 3A materializer/routes only after v2 writes are proven.'",
      "grep for feature_flag/FEATURE_FLAG/ENABLE_*/settings.FEATURE across backend/app returned zero matches, confirming there is no existing toggle mechanism this design could rely on.",
      "Every other invariant in the same document (e.g., invariant 2, invariant 24) is phrased as a transaction-enforced or trigger-enforced guarantee, not a manual rollout instruction."
    ],
    "impact": "A rolling/blue-green deploy that briefly runs mixed old/new application instances (a routine production pattern) could serve v2 candidate writes or 3A materialization from a not-yet-fully-rolled-out fleet, or could enable 3A routes before the v2 writer has been proven safe in production, silently violating the design's own stated sequencing without any error, log, or DB rejection.",
    "requiredClosure": "Define a concrete, code-level gate (e.g., an environment/config flag read at router-registration or write-path time) that makes 'v2 writer enabled' and '3A routes enabled' explicit, independently togglable states rather than an implicit consequence of which code version is deployed. Add a test or startup check proving the 3A routes/v2 writer cannot activate merely because migration 0027 has run."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-002",
    "severity": "medium",
    "invariant": "The design's stated in-scope/out-of-scope boundary (Objective section) and its 'Expected file scope' section should name every namespace and table Slice 3A is authorized to touch, so an implementer or later reviewer can verify boundary compliance without re-deriving it from a 1,500-line design body.",
    "summary": "Section 2.1.1 requires Slice 3A to create a shared, proposal-scoped correction foundation that stores canonical `authoritativeCorrections` content and verified `officialDocuments` identity hashes -- two top-level V4 namespaces distinct from the four-field applicability subtree {productScopes, conditionDefinitions, applicabilityRules, applicabilitySearchHints}. Neither namespace is mentioned in the Objective's in/out-of-scope bullet list, nor explicitly named in the 'Expected file scope' section, even though the mandatory 2008-26-10 calibration assertion depends on it.",
    "evidence": [
      "review-packet.md:28-63 (Objective) lists what's out of scope for 3A/deferred to 3B but never mentions `authoritativeCorrections` or `officialDocuments`.",
      "review-packet.md:581-655 (section 2.1.1) defines `ad_v4_candidate_corrections`, `_correction_refs`, `_correction_semantic_bindings`, `_correction_evidence_links` storing `officialDocuments reference keys`, their `verified document-identity hashes`, and namespace refs spanning `requirements|recurrenceGroups|amocAuthorityProvisions` (3B-owned) in addition to 3A-owned namespaces.",
      "backend/app/schemas/ad_extraction_v4.schema.json $defs.proposal.properties includes `authoritativeCorrections` and `officialDocuments` as independent top-level arrays, confirming these are namespaces outside the four-field subtree definition in invariant 3.",
      "review-packet.md:1458-1489 ('Expected file scope') mentions only 'the additive 3A tables' generically and never names the correction-foundation tables or namespaces, while the mandatory test for 2008-26-10 (review-packet.md:1369-1372) requires 'exact shared correction-2010 foundation with two ordered refs, two evidence links once, one 3A scope binding, and one explicit future-3B requirement ref'."
    ],
    "impact": "An implementer following the Objective/Expected-file-scope sections literally could reasonably treat the correction-foundation tables as unauthorized scope creep and omit them, causing the mandatory 2008-26-10 reconstruction test (and the whole DA-002 closure) to fail; conversely, a later reviewer auditing 'did 3A only touch what it said it would' has no single authoritative scope list to check against, since the two scope-defining sections disagree with the detailed design.",
    "requiredClosure": "Update the Objective's out-of-scope list and the 'Expected file scope' section to explicitly name the correction-foundation tables and the `authoritativeCorrections`/`officialDocuments` namespaces they read/verify, so the document's own scope statement is internally consistent with section 2.1.1 and the mandatory calibration test."
  },
  {
    "id": "T081-V4-SCHEMA-SLICE-3A-CC-003",
    "severity": "low",
    "invariant": "'Write paths and administrative paths' asserts no new operational writer (job/CLI/seed/etc.) is added beyond the single platform-admin POST service.",
    "summary": "The stale-fold section introduces 'a background repair function [that] may append missing deterministic events after a crash,' which reads as a new asynchronous/scheduled process, apparently in tension with the explicit claim elsewhere that no provider job, CLI, seed, or generic writer is added.",
    "evidence": [
      "review-packet.md:1081-1085 'A background repair function may append missing deterministic events after a crash; it uses the same locks and event identity and requires no human review.'",
      "review-packet.md:1205-1213 ('Write paths and administrative paths') states 'No provider job, CLI, seed, V3 translator, calibration loader, frontend form, or generic ORM CRUD writer is added,' and that 'Its internal deterministic stale-event helper is part of the same service/repository boundary,' without clarifying whether the crash-repair helper is invoked synchronously (e.g., opportunistically on the next POST/GET) or via a new scheduled/background worker process."
    ],
    "impact": "If implementation interprets 'background repair function' as a new cron/worker process, that is new operational surface (deployment unit, scheduling, monitoring) not accounted for anywhere else in the design's operational sections, and could be missed by an implementation reviewer who only checks for 'no new job' against the explicit write-paths sentence.",
    "requiredClosure": "Clarify in the design that the repair helper is invoked inline/opportunistically from existing request paths (not a new scheduled process), or, if a real background worker is intended, add it explicitly to the write-paths/operational sections and its own authorization/idempotency contract."
  }
]
```

## 2. Findings

### T081-V4-SCHEMA-SLICE-3A-CC-001 — Rollout sequencing has no code-enforced gate

See JSON above for full evidence. Every other safety property in this document is backed by a database trigger, composite FK, or in-transaction recheck (the document is explicit about this philosophy — e.g. "Eligibility is rechecked inside the write transaction; creation-time validity is not trusted"). The one exception is the mandatory four-step production rollout order, which currently depends entirely on operators deploying instances in the right sequence, in a codebase that has no existing feature-flag primitive to fall back on. This is exactly the kind of migration/rollout risk the review brief asks to be scrutinized closely.

### T081-V4-SCHEMA-SLICE-3A-CC-002 — Scope statement omits the correction-foundation namespaces it actually requires

See JSON above. This is a documentation-consistency finding, not a logic defect in section 2.1.1 itself (which I independently traced against the real `2008-26-10.proposal.json` correction-2010 object and schema and found accurate). The risk is that the parts of the document meant to bound scope (Objective, Expected file scope) don't match the part that actually defines the work (section 2.1.1), which is the exact kind of drift the "expected file scope" gate exists to prevent for later implementation reviewers.

### T081-V4-SCHEMA-SLICE-3A-CC-003 — "Background repair function" wording conflicts with the "no new job" claim

See JSON above. Low severity because it's a clarity/definition gap rather than a demonstrated defect, but worth resolving before implementation since it touches the operational-surface guarantee the design otherwise takes seriously.

## 3. Open Questions

- The design's own "Known uncertainty" item 4 (PostgreSQL deferred-constraint-trigger reconstruction cost on the 224-model packet) is an honestly flagged, accepted risk rather than a hidden one; I did not find a stronger technical objection to it beyond what's already recorded, but I'd still ask for a concrete statement-timeout/measurement plan before merging the migration, since it's the one place a "correctness" gate could become a production incident if it times out under load rather than just failing a test.
- Section 2.1.1's correction root is fixed at `generation 1` with no described path for a second generation (e.g., a later re-correction of the same official document pair). This is presumably deferred by design, but the document doesn't say so explicitly — worth a one-line confirmation that generation versioning is out of scope for 3A/3B and reserved for a future slice.
- Is `platform_admin` scoped globally to the user (so "another valid membership" language in invariant 24 is about the user having admin rights in a *different* org) or could a user hold `platform_admin` in one org and a non-admin role in another? The design's authorization contract reads correctly either way, but a one-line model description would remove ambiguity for implementers.

## 4. Verification Notes

- Confirmed via direct hex computation that all seven v2 hash-domain byte strings in the packet are correct.
- Confirmed the existing v1 hash-domain constants in `backend/app/services/ad_v4_candidates.py:49-53` follow the same naming convention the v2 domains extend.
- Confirmed `conditionSubject`, `searchHint`, `expression`, `applicabilityRule`, `changedSemanticRef`, `officialDocument`, and `knownString` definitions in `backend/app/schemas/ad_extraction_v4.schema.json` match every specific structural claim made about them in the decision packet.
- Confirmed the existing `ensure_platform_admin`-style "any active membership" authorization pattern in `backend/app/api/routes/admin.py:19-26` and the `Idempotency-Key`/`Paprnav-Acting-Membership-Id` header conventions in `backend/app/api/routes/ads.py`, both cited as evidence in the closed DA-007 finding — accurate.
- Confirmed `CREATE CONSTRAINT TRIGGER ... DEFERRABLE INITIALLY DEFERRED` is already used four times in `20260901_0026_add_ad_v4_candidates.py`, supporting the technical feasibility of the proposed deferred-completeness-check pattern for Slice 3A.
- Confirmed the real `2008-26-10.proposal.json` fixture's `authoritativeCorrections` content matches the packet's stated correction-2010 example exactly (two changed-semantic-refs, two evidence keys).
- Confirmed the currently-stored `2002-13-04.proposal.json` fixture still uses the old flattened v1 `manufacturer: "multiple"` / 6-model hint shape, consistent with this being a design-only phase where the "corrected" v2 fixtures described in the decision are not yet implemented.
- Did not run backend tests or lint, since there is no code change in this review's scope (diff against base is empty); running the existing v1 test suite would not exercise anything this design changes.

## 5. Brief Summary

This is a mature, twice-adversarially-reviewed design document with no accompanying code change. All ten previously-closed internal findings that I spot-checked (DA-004's series-expression/canonicalization-version fix, DA-010's rollout/downgrade lock ordering, plus cross-checks of DA-001/002/005/006/007/008/009 against the real schema and fixtures) are supported by accurate evidence and appear genuinely closed. My independent pass surfaces three new, non-blocking findings: an unenforced production rollout sequence (CC-001), a scope-statement/detailed-design inconsistency around the correction-foundation namespaces (CC-002), and an ambiguous "background repair function" description (CC-003). None of these are blockers to a design PASS, but CC-001 and CC-002 should be resolved before implementation begins, given the document's own stated bar of "server-enforced, not operator-trusted" invariants.