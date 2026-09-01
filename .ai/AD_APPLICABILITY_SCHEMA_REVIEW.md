# AD applicability extraction and relational persistence review

Status: proposed design for `ad_extraction_v3`
Decision owner: Paprnav platform administration
Safety posture: fail closed; machine extraction is a proposal until source-verified approval

## Why v2 is not safe enough

`ad_extraction_v2` represents applicability as `affectedProducts: string[]`. That field loses the relationships needed for reliable matching and search:

- manufacturer and model are not separate typed values;
- a manufacturer may appear as one list item while its models appear as unrelated sibling items;
- a combined value such as `Cessna Aircraft Company 150A` cannot be split reliably because manufacturer names contain spaces;
- serial-number limits, installed-equipment conditions, aliases, and source wording have no stable location;
- a compliance requirement cannot state which applicability branch it governs;
- the current materializer guesses that the first word is the make and all remaining words are the model.

The result is relational data that looks normalized but is semantically wrong. For example, a model-only string such as `172D` becomes a make with no model, while `Textron Aviation Inc.` becomes make `Textron` and model `Aviation Inc.`. This prevents exact manufacturer/model search and can produce false aircraft matches.

## Authoritative v3 extraction shape

`applicabilityGroups` is authoritative. `affectedProducts` is a server-derived compatibility/display field and reviewer edits to it are ignored or rejected if inconsistent.

Each group preserves one source-defined applicability branch. Models within a group are an OR list under the same manufacturer, serial scope, conditions, and evidence.

```json
{
  "applicabilityGroups": [
    {
      "groupKey": "paragraph-c-cessna-150-series",
      "productType": "aircraft",
      "productSubtype": "small_airplane",
      "manufacturer": {
        "sourceName": "Cessna Aircraft Company",
        "normalizedName": "Textron Aviation Inc."
      },
      "modelApplicability": {
        "kind": "listed",
        "models": [
          {
            "sourceDesignation": "150A",
            "normalizedDesignation": "150A",
            "aliases": []
          }
        ],
        "sourceText": "Model 150A airplanes"
      },
      "serialNumberApplicability": {
        "kind": "all",
        "values": [],
        "ranges": [],
        "excludedValues": [],
        "sourceText": "all serial numbers"
      },
      "equipmentCombinationLogic": "all",
      "equipmentConditions": [],
      "conditions": [],
      "citations": [
        {
          "sourceDocumentId": "asd_example",
          "pageNumber": 2,
          "text": "This AD applies to Cessna Aircraft Company Model 150A airplanes, all serial numbers."
        }
      ],
      "confidence": 0.98,
      "uncertaintyReasons": []
    }
  ],
  "requirements": [
    {
      "requirementKey": "paragraph-g-inspection",
      "applicabilityGroupKeys": ["paragraph-c-cessna-150-series"],
      "requirementType": "one_time",
      "actionText": "Within 100 hours time-in-service after the effective date of this AD, inspect ...",
      "initialThresholds": [],
      "recurringTriggers": [],
      "combinationLogic": "all",
      "conditions": [],
      "terminatingAction": null,
      "citations": [],
      "confidence": 0.98,
      "uncertaintyReasons": []
    }
  ]
}
```

Rules:

1. `manufacturer.sourceName` and `models[].sourceDesignation` preserve the official wording exactly.
2. Normalized names are optional search/matching identities. They must not overwrite source wording. When no approved normalization is known, use `null`; the server falls back to the source value.
3. Never put a manufacturer and model in the same string, and never place manufacturer and model as unrelated sibling strings.
4. A group has one manufacturer. `modelApplicability.kind` is `listed`, `all`, `expression`, or `unknown`; `listed` requires at least one separate model object. Separate source branches become separate groups.
5. `serialNumberApplicability.kind` is one of `all`, `values`, `ranges`, `expression`, or `unknown`. `sourceText` preserves qualifications that cannot be losslessly reduced.
6. Installed equipment is a condition on the primary product, not another primary model. Each equipment condition has its own typed manufacturer/model identity and citation.
7. Every group and requirement has page-level citations. Citation text must exist on the retained page.
8. Every requirement explicitly lists the group keys it governs. The server does not silently apply every requirement to every target.
9. Uncertainty blocks publication. A reviewer either resolves it from evidence or sends the record to remediation.
10. Every timing value, unit, anchor clause, and terminating-action statement is copied from cited text. `anchorKind` is semantic data, not a display hint.
11. `amocProvisions` captures the AD's AMOC authority paragraph separately from in-rule alternative requirements. Each provision has source-faithful authority text, approving authority, submission instructions, conditions, citations, confidence, and uncertainty.
12. `combinationLogic` is preserved as `all`, `whichever_first`, `whichever_later`, or `alternative`. `whichever_later` selects the latest applicable threshold; `alternative` fails closed for adjudication rather than being reduced to `all`.

## JSON to PostgreSQL mapping

The extraction JSON is retained unchanged on `ad_extractions.output` and the approved reviewer copy on `ad_extraction_reviews.decision_output`. Those JSON records are the auditable proposal and decision, not the query model.

Approval performs a deterministic materialization transaction:

1. Validate v3 structure, normalized group-key references, citations, source-faithful action/timing/terminating wording, and AMOC authority wording.
2. Supersede prior extraction-derived applicability rows for the directive.
3. Expand each applicability group into one relational row per listed model,
   or one manufacturer-wide row when the source model scope is not a list.
4. Upsert `applicability_targets` using the normalized manufacturer/model identity, falling back to source identity when normalization is absent.
5. Create `ad_target_applicability` rows carrying the group key, source identity, typed serial scope, equipment conditions, conditions, citations, confidence, and complete source group payload.
6. Materialize each requirement only onto applicability rows whose group key appears in `requirements[].applicabilityGroupKeys`.
7. Materialize initial and recurring triggers separately while preserving each trigger's source anchor.
8. Materialize AMOC provisions as independently indexed relational rows.
9. Supersede stale requirement/AMOC rows, invalidate affected aircraft matches, and replay downstream compliance state.

### Relational versus JSON columns

Values used for equality joins and fleet-neutral search are relational and indexed:

- `applicability_targets.product_type`
- `applicability_targets.product_subtype`
- `applicability_targets.make`
- `applicability_targets.model`
- `ad_target_applicability.applicability_group_key`
- directive/review/status foreign keys and status columns
- `ad_compliance_triggers.trigger_kind`, metric, value, unit, and `anchor_kind`
- `ad_amoc_provisions.provision_key`, approving authority, and status

Source-faithful or polymorphic evidence stays JSON beside the relational row:

- source manufacturer/model wording and aliases;
- serial scope, including ranges or non-reducible expressions;
- installed-equipment conditions;
- source conditions and citations;
- complete source group payload.

This is intentional hybrid persistence. PostgreSQL is used relationally for stable identities and joins; JSON is retained for variable regulatory evidence that must not be flattened or guessed. Aircraft-specific serial and equipment evaluation remains fail-closed when a condition cannot be normalized.

## Search contract

The released catalog supports independent filters for:

- free text (AD number/title plus structured target identities);
- AD number;
- directive currency status;
- product type;
- manufacturer;
- model.

Manufacturer and model filters query `applicability_targets` through current `ad_target_applicability` rows; they do not inspect or split `affectedProducts` strings. Aircraft pages continue to supply make, model, installed components, and serial context automatically.

## Current inconsistencies and disposition

| Inconsistency | Risk | Disposition |
| --- | --- | --- |
| Combined manufacturer/model strings | Incorrect make/model columns | v3 typed groups; no authoritative string parsing |
| Manufacturer and model as sibling strings | Orphan targets and false matches | v3 group relationship |
| One requirement copied to all applicability rows | Wrong compliance obligation on some products | explicit `applicabilityGroupKeys` |
| Paraphrased compliance actions | Meaning may change | source-faithful action text plus citation validation |
| Hallucinated deadline/interval values | Wrong due state | timing source text, value, unit, and anchor evidence validation |
| AMOC paragraph conflated with an alternative action | Wrong compliance semantics | dedicated `amocProvisions` and relational AMOC rows |
| Nullable applicability identity columns | Duplicate PostgreSQL rows | NULL-safe unique expression index |
| Foreign Federal Register document attached to an AD | Reviewer sees unrelated source text | source identity must be verified per retained document before pages are admitted |
| UI says manufacturer/model search but API only searches title/AD number | Misleading and incomplete query | relational target search and separate filters |
| Approved v2 rows remain queryable | Known malformed targets can be released | v2 becomes audit-only; v3 re-review is required |

## Migration and compatibility

- `ad_extraction_v3` is a new schema version. Existing v2 extractions and decisions remain immutable audit records but cannot newly publish or satisfy the v3 release gate.
- Existing relational rows are not auto-corrected from legacy strings because doing so would repeat the unsafe guess. They are superseded only when a source-verified v3 review is approved.
- `affectedProducts` may be emitted as a derived label list for legacy read paths during transition. It must never drive v3 relational materialization.
- Calibration records should be re-staged as v3. Known malformed approved records, including AD 2024-14-03, must be reopened/quarantined until a v3 decision replaces them.

## Reviewer checklist

Before publishing, the administrator confirms:

1. The retained document and bounded pages are the actual AD named in the proposal.
2. Source manufacturer and model wording are copied into separate fields.
3. Normalized identities are conservative and do not change the regulated population.
4. Every model belongs to the correct manufacturer/group.
5. Serial scope, installed-equipment conditions, exceptions, and applicability logic are represented or explicitly unresolved.
6. Every requirement identifies its applicable groups.
7. Action wording is source-faithful and each citation points to the displayed retained document/page.
8. No uncertainty remains before approval; otherwise reject/send to remediation.
9. Initial thresholds and recurring triggers have the correct source anchor and exact cited timing clause.
10. The AMOC paragraph is captured in `amocProvisions`, not as a maintenance action.
