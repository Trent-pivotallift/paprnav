# Candidate AD extraction V4 schema

Status: builder proposal; independent design review required  
Schema name: `ad_extraction_v4`  
Domain contract: `.ai/AD_EXTRACTION_DOMAIN_CONTRACT.md` version 1.1  
Implementation authorization: none

## 1. Design summary

V4 is a signed structured-decision graph, not a copy of the AD and not an
aircraft compliance record. It contains only the reviewed semantics needed for
candidate applicability and obligation/due-state modeling. It references exact
immutable source fragments stored in the official-evidence domain.

The five domains are separate:

| Domain | Authority | Representative storage | V4 relationship |
| --- | --- | --- | --- |
| Official AD evidence | Retained source bytes and immutable fragments | `ad_source_documents`, new `ad_evidence_fragments` | V4 references fragment IDs and hashes |
| Structured AD decision | Signed platform-admin decision | existing extraction/review audit plus new V4 decision/semantic tables | Canonical V4 JSON and relational projection |
| Aircraft configuration | Versioned aircraft/component/modification facts | aircraft/configuration tables | Evaluated against V4 rules; never embedded in V4 |
| Aircraft compliance evidence | Logbook/supporting records and reviewed claims | logbook/evidence/compliance tables | Compared with V4 requirements; never changes V4 |
| Paprnav assessment | Reproducible result from signed inputs | versioned assessment/due-state projections | Non-authoritative and stale-aware |

Three choices remove the observed bloat:

1. Exact clause text lives once in `ad_evidence_fragments`. A V4 decision maps
   short evidence keys to immutable fragment ID/hash pairs.
2. Manufacturer/model populations live in `productScopes`; shared installed
   equipment, modification, and other predicates live once in
   `conditionDefinitions`; `applicabilityRules` join them.
3. Requirements are stored once and point to applicability rule keys. They are
   not cloned once for every model or query target.

The review API may return joined fragment text and derived labels for display,
but those fields are read-only and are excluded from canonical hashing and
decision submission.

## 2. Canonical V4 envelope

The following is an illustrative, valid JSON document. It deliberately leaves
timing unknown rather than inventing a value. It demonstrates the representation
and is not a source-complete calibration result for AD 2024-14-03.

```json
{
  "schemaVersion": "ad_extraction_v4",
  "decisionKey": "ad-2024-14-03-v4-draft-1",
  "directiveIdentity": {
    "adNumber": {
      "state": "known",
      "value": "2024-14-03",
      "evidenceKeys": ["ev-rule-identity"]
    },
    "amendment": {
      "state": "known",
      "value": "39-22784",
      "evidenceKeys": ["ev-rule-identity"]
    },
    "revision": {
      "state": "not_applicable",
      "reason": "source_defines_no_revision_for_this_issue",
      "evidenceKeys": ["ev-rule-identity"],
      "temporalScope": {"kind": "directive_version"}
    },
    "effectiveDate": {
      "state": "unknown",
      "reason": "not_yet_reviewed",
      "evidenceKeys": ["ev-effective-date-section"],
      "temporalScope": {"kind": "directive_version"}
    },
    "regulatoryStatus": {
      "state": "known",
      "value": "current",
      "evidenceKeys": ["ev-publication-status"]
    }
  },
  "evidenceBindings": {
    "ev-rule-identity": {
      "fragmentId": "aef_rule_identity",
      "fragmentHash": "sha256:example-rule-identity"
    },
    "ev-publication-status": {
      "fragmentId": "aef_publication_status",
      "fragmentHash": "sha256:example-publication-status"
    },
    "ev-effective-date-section": {
      "fragmentId": "aef_effective_date",
      "fragmentHash": "sha256:example-effective-date"
    },
    "ev-applicability-table": {
      "fragmentId": "aef_applicability_table",
      "fragmentHash": "sha256:example-applicability-table"
    },
    "ev-installed-configuration": {
      "fragmentId": "aef_installed_configuration",
      "fragmentHash": "sha256:example-installed-configuration"
    },
    "ev-action-update": {
      "fragmentId": "aef_action_update",
      "fragmentHash": "sha256:example-action-update"
    },
    "ev-amoc-authority": {
      "fragmentId": "aef_amoc_authority",
      "fragmentHash": "sha256:example-amoc-authority"
    }
  },
  "incorporatedDocuments": [
    {
      "documentRefKey": "doc-garmin-service-information",
      "documentType": "service_bulletin",
      "documentNumber": {
        "state": "unknown",
        "reason": "not_yet_reviewed",
        "evidenceKeys": ["ev-action-update"],
        "temporalScope": {"kind": "directive_version"}
      },
      "revision": {
        "state": "unknown",
        "reason": "not_yet_reviewed",
        "evidenceKeys": ["ev-action-update"],
        "temporalScope": {"kind": "directive_version"}
      },
      "retention": {
        "state": "unknown",
        "reason": "not_obtained",
        "evidenceKeys": ["ev-action-update"],
        "temporalScope": {"kind": "directive_version"}
      },
      "evidenceKeys": ["ev-action-update"]
    }
  ],
  "productScopes": [
    {
      "scopeKey": "scope-commander-aircraft",
      "productRole": "airframe",
      "manufacturer": {
        "sourceValue": "Commander Aircraft Corporation",
        "normalizedIdentity": {
          "state": "known",
          "value": "Commander Aircraft Corporation",
          "evidenceKeys": ["ev-applicability-table"]
        }
      },
      "modelScope": {
        "kind": "listed",
        "sourceDesignations": ["112", "114"],
        "evidenceKeys": ["ev-applicability-table"]
      },
      "serialScope": {"kind": "all", "evidenceKeys": ["ev-applicability-table"]},
      "partNumberScope": {
        "kind": "not_applicable",
        "reason": "source_scope_is_by_model_and_serial_not_part_number",
        "evidenceKeys": ["ev-applicability-table"]
      },
      "evidenceKeys": ["ev-applicability-table"]
    },
    {
      "scopeKey": "scope-daher-aircraft",
      "productRole": "airframe",
      "manufacturer": {
        "sourceValue": "DAHER Aerospace",
        "normalizedIdentity": {
          "state": "known",
          "value": "DAHER Aerospace",
          "evidenceKeys": ["ev-applicability-table"]
        }
      },
      "modelScope": {
        "kind": "listed",
        "sourceDesignations": ["TBM 700", "TBM 850"],
        "evidenceKeys": ["ev-applicability-table"]
      },
      "serialScope": {"kind": "all", "evidenceKeys": ["ev-applicability-table"]},
      "partNumberScope": {
        "kind": "not_applicable",
        "reason": "source_scope_is_by_model_and_serial_not_part_number",
        "evidenceKeys": ["ev-applicability-table"]
      },
      "evidenceKeys": ["ev-applicability-table"]
    }
  ],
  "conditionDefinitions": [
    {
      "conditionKey": "condition-gfc500-gsa28-installed",
      "conditionType": "installed_equipment",
      "operator": "is_installed",
      "subject": {
        "productRole": "appliance",
        "manufacturer": {
          "state": "known",
          "value": "Garmin",
          "evidenceKeys": ["ev-installed-configuration"]
        },
        "modelOrSeries": {
          "state": "known",
          "value": "GFC 500 / GSA 28 configuration",
          "evidenceKeys": ["ev-installed-configuration"]
        }
      },
      "temporalBasis": {"kind": "at_applicability_evaluation"},
      "evidenceKeys": ["ev-installed-configuration"]
    }
  ],
  "applicabilityRules": [
    {
      "ruleKey": "rule-affected-airplanes-with-installed-configuration",
      "scopeExpression": {
        "nodeType": "any",
        "operands": [
          {"nodeType": "scope_ref", "scopeKey": "scope-commander-aircraft"},
          {"nodeType": "scope_ref", "scopeKey": "scope-daher-aircraft"}
        ]
      },
      "conditionExpression": {
        "nodeType": "predicate_ref",
        "conditionKey": "condition-gfc500-gsa28-installed"
      },
      "exclusionRuleKeys": [],
      "evidenceKeys": ["ev-applicability-table", "ev-installed-configuration"]
    }
  ],
  "requirements": [
    {
      "requirementKey": "requirement-software-update",
      "activationExpression": {
        "nodeType": "rule_ref",
        "ruleKey": "rule-affected-airplanes-with-installed-configuration"
      },
      "requirementType": "corrective_action",
      "action": {
        "actionType": "software_update",
        "approvedDataDocumentRefKeys": ["doc-garmin-service-information"],
        "evidenceKeys": ["ev-action-update"]
      },
      "prerequisiteRequirementKeys": [],
      "branch": {"kind": "required", "evidenceKeys": ["ev-action-update"]},
      "initialTiming": {
        "state": "unknown",
        "reason": "not_yet_reviewed",
        "evidenceKeys": ["ev-action-update"],
        "temporalScope": {"kind": "directive_version"}
      },
      "recurrence": {"kind": "none", "evidenceKeys": ["ev-action-update"]},
      "terminatingEffect": {"kind": "none", "evidenceKeys": ["ev-action-update"]},
      "evidenceKeys": ["ev-action-update"]
    }
  ],
  "amocAuthorityProvisions": [
    {
      "provisionKey": "amoc-general-authority",
      "approvingAuthority": {
        "state": "unknown",
        "reason": "not_yet_reviewed",
        "evidenceKeys": ["ev-amoc-authority"],
        "temporalScope": {"kind": "directive_version"}
      },
      "evidenceKeys": ["ev-amoc-authority"]
    }
  ],
  "supersessionRelations": []
}
```

Production identifiers and SHA-256 values must satisfy their real formats; the
example hashes are intentionally non-production placeholders.

## 3. JSON-schema-level rules

### 3.1 Envelope and object discipline

- Root `type: object`, `additionalProperties: false`.
- Required root members: `schemaVersion`, `decisionKey`,
  `directiveIdentity`, `evidenceBindings`, `incorporatedDocuments`,
  `productScopes`, `conditionDefinitions`, `applicabilityRules`,
  `requirements`, `amocAuthorityProvisions`, and `supersessionRelations`.
- `schemaVersion` is `const: ad_extraction_v4`.
- Every nested object has `additionalProperties: false`.
- Canonical input rejects JSON `null` at every depth. A static schema walk and
  runtime canonical validator enforce this; database `NULL` is reserved for
  structurally absent relational columns, never unknown semantics.
- Arrays that represent sets are canonically sorted by their stable key before
  hashing. User order is preserved only for ordered timing/branch sequences.
- `affectedProducts`, `complianceActions`, `complianceIntervals`, display
  labels, confidence summaries, and calculated due values are forbidden root
  properties.

### 3.2 Stable keys and references

- Keys match `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, length 3–128.
- Each key is unique in its namespace. `decisionKey` is globally unique.
- Every `evidenceKey` resolves in `evidenceBindings`.
- Every binding resolves to an immutable fragment belonging to an official or
  admitted incorporated source associated with the directive; both fragment
  ID and hash must match.
- Every scope, condition, rule, requirement, document, prerequisite,
  exclusion, terminating-effect, AMOC, and supersession reference resolves
  inside the same signed decision unless the schema explicitly identifies an
  external directive/document identity.
- Referential checks, uniqueness across arrays, graph-cycle checks, and hash
  checks are semantic validation beyond base JSON Schema and run before review,
  approval, release, and rematerialization.

### 3.3 Known, not-applicable, and unknown values

Safety-relevant optional values use a discriminated union:

```json
{
  "oneOf": [
    {
      "type": "object",
      "required": ["state", "value", "evidenceKeys"],
      "properties": {
        "state": {"const": "known"},
        "value": {},
        "evidenceKeys": {"type": "array", "minItems": 1, "uniqueItems": true}
      },
      "additionalProperties": false
    },
    {
      "type": "object",
      "required": ["state", "reason", "evidenceKeys", "temporalScope"],
      "properties": {
        "state": {"const": "not_applicable"},
        "reason": {"type": "string", "minLength": 1},
        "evidenceKeys": {"type": "array", "minItems": 1, "uniqueItems": true},
        "temporalScope": {"$ref": "#/$defs/temporalScope"}
      },
      "additionalProperties": false
    },
    {
      "type": "object",
      "required": ["state", "reason", "evidenceKeys", "temporalScope"],
      "properties": {
        "state": {"const": "unknown"},
        "reason": {
          "enum": [
            "not_observed",
            "unavailable",
            "not_obtained",
            "not_extracted",
            "not_yet_reviewed",
            "conflicting_evidence",
            "source_ambiguous",
            "unsupported_expression"
          ]
        },
        "evidenceKeys": {"type": "array", "minItems": 1, "uniqueItems": true},
        "temporalScope": {"$ref": "#/$defs/temporalScope"}
      },
      "additionalProperties": false
    }
  ]
}
```

`not_applicable` means the source affirmatively establishes that the concept
does not apply for the stated temporal/domain scope. It is a safety-relevant
negative assertion and therefore requires evidence and a reason. Purely
structural absence is represented by selecting a schema variant that omits the
field, not by an unevidenced `not_applicable`. If the value could matter but is
unavailable, the state is `unknown`.

### 3.4 Product scopes

- `productRole` enum: `airframe`, `engine`, `propeller`, `appliance`,
  `installed_part`, `modification`.
- One scope has one source manufacturer identity. Models are separate values,
  never concatenated with manufacturer.
- `modelScope.kind` is `listed`, `all`, `series_expression`, or `unknown`.
  `listed` requires at least one unique source designation. `unknown` uses the
  standard unknown envelope.
- Serial and part-number scopes are discriminated unions: `all`, `listed`,
  `ranges`, `expression`, `not_applicable`, or `unknown`. Range endpoints and
  inclusivity are explicit strings; no numeric coercion is allowed.
- Product scopes contain no installed-equipment predicates. Those belong in
  reusable condition definitions.
- Source values are immutable reviewed text. A normalized identity is a
  separate known/unknown value and cannot overwrite the source value.

### 3.5 Typed three-valued applicability algebra

Every applicability and branch condition uses a recursively nested expression
AST. There is no implicit meaning for an array of rule keys.

```text
Expression := PredicateRef(key)
            | ScopeRef(key)
            | RuleRef(key)
            | RequirementStateRef(key, state)
            | Not(Expression)
            | All(Expression, Expression, ...)
            | Any(Expression, Expression, ...)
```

`All` and `Any` require at least two operands. `Not` has exactly one operand.
Expression and reference graphs are acyclic. Constant true/false nodes are not
accepted because every regulatory positive or negative must be evidence-bound.
The canonical object uses a `nodeType` discriminator and `operands`/reference
keys; nested depth and node count have configured limits to prevent resource
exhaustion.

Leaf predicate types are closed and typed:

`ScopeRef` references one reviewed product-scope key. `PredicateRef` references
one reviewed condition definition whose executable leaf is one of the closed
typed predicates below; there is no separate untyped condition expression.

- `identity_equals` and `identity_in`: product role plus manufacturer,
  model/series, part, serial, or STC identity;
- `identifier_in_range`: typed serial or part-number comparator and inclusive
  endpoints;
- `component_installed` / `component_not_installed`;
- `modification_installed` / `modification_not_installed`;
- `configuration_attribute_equals`;
- `temporal_overlap`: date, aircraft-time, component-time, or cycle intervals;
- `source_inclusion` / `source_exclusion`; and
- `reviewed_manual_predicate`, which always evaluates unknown until an
  attributable aircraft-specific determination supplies true or false.

Each predicate identifies its comparator version and temporal scope. Unsupported
series expressions or comparators evaluate unknown; substring matching is not a
fallback.

The evaluator domain is `T` (proven true), `F` (proven false), and `U`
(unknown/conflicting/unsupported). Kleene strong three-valued truth tables are
normative:

| A | NOT A |
| --- | --- |
| T | F |
| F | T |
| U | U |

| A | B | ALL(A,B) | ANY(A,B) |
| --- | --- | --- | --- |
| T | T | T | T |
| T | F | F | T |
| T | U | U | T |
| F | T | F | T |
| F | F | F | F |
| F | U | F | U |
| U | T | U | T |
| U | F | F | U |
| U | U | U | U |

N-ary `All` and `Any` fold these tables without reordering semantic sequence.
A known fact comparison yields T or F. Missing/conflicting fact, unsupported
comparator, or incomplete temporal coverage yields U. A source exclusion may
yield F only when its negative assertion and the compared configuration fact
are both evidence-bound; absence of a fact yields U.

An applicability rule has one `scopeExpression` (usually `Any` of scope refs)
and one `conditionExpression`; its result is `All(scopeExpression,
conditionExpression)`. Requirements use a single `activationExpression`, not an
ambiguous list. Multiple intended rule references must therefore state `Any`
or `All` explicitly.

Expression evaluation records `evaluatorVersion`, input-version IDs, result,
and a node-by-node trace. Only T may activate an actionable requirement; F is
inactive; U is candidate-only/human-determination-required.

### 3.6 Requirements, timing, and branch state machine

- A requirement has exactly one `activationExpression` and contains one
  normalized action object plus evidence keys resolving to the exact source
  action clause.
- `requirementType` is a controlled enum, initially `inspection`,
  `replacement`, `modification`, `software_update`, `limitation`, `reporting`,
  `installation_prohibition`, `corrective_action`, or `other_reviewed`.
- Detailed method may be represented by `approvedDataDocumentRefKeys`; the
  source wording remains in evidence fragments.
- Initial timing is known or unknown. A known timing contains a logic group
  (`all`, `whichever_first`, `whichever_later`) and one or more threshold terms.
- Each threshold term has metric (`calendar`, `aircraft_time`, `component_time`,
  `cycles`, or `other_reviewed`), decimal value encoded as a string, unit,
  comparison operator, anchor, and evidence keys. Floating-point JSON numbers
  are forbidden for time/cycle thresholds.
- Recurrence is `none`, `interval`, `conditioned`, or `unknown`. An interval has
  the same explicit metric/value/unit/anchor and evidence rules.
- Branch kind is `required`, `alternative_member`, `conditional`, or
  `exception`. Conditional and exception branches require a typed predicate
  expression. Alternative members share an alternative-group key and each has
  its own activation expression.
- Branch activation is normative: expression T = active, F = inactive, U =
  unresolved and non-actionable. For an exclusive alternative group, exactly
  one member must be T and every other member F before automatic selection. No
  T with any U is unresolved; more than one T is a contradictory extraction;
  all F is inactive only when the source permits no branch, otherwise it is a
  validation error. Nonexclusive alternatives activate every T member but any
  U remains a separate unresolved obligation.
- Prerequisite and terminating relationships are keys, not copied requirements.
  The combined dependency, branch-reference, and terminating graph must be
  acyclic. A terminating action names precisely which requirement keys it
  terminates and its evidence. A terminating effect applies only after a signed
  aircraft compliance event satisfies its own T-valued activation expression.

### 3.7 Documents, STCs, and AMOCs

- `incorporatedDocuments` represents known service-bulletin or other
  approved-data identities, revisions, dates, and retention/access states.
- `retention.state: known` identifies the retained `ADSourceDocument` and
  content hash. Unavailable content uses explicit unknown and cannot support
  facts not visible in retained evidence.
- An administrator adding a missing service bulletin creates a retained source
  document and evidence version; it does not edit a prior fragment or signed
  decision.
- AD-level STC applicability uses a `modification_or_stc` condition with a
  structured STC identity. Missing number, revision, affected product, or scope
  is explicit unknown. Actual installation/removal belongs to aircraft
  configuration.
- `amocAuthorityProvisions` contains only the rule's general AMOC authority and
  source references. It must not contain claims that a particular aircraft used
  an AMOC.
- Actual AMOC approval/use is an aircraft compliance-evidence object with
  approval reference, approving authority, authenticity, scope, conditions,
  aircraft/configuration binding, revised method/timing, and reviewer decision.
  Incomplete evidence maps to **possible AMOC—unverified**.

Service-bulletin retention and aircraft-specific AMOC use are administrator-
ingested evidence workflows; neither record may be synthesized merely to make a
calibration packet complete. The authorized workflow is:

1. An active, appropriately scoped administrator opens the unresolved document
   or AMOC evidence task. Server authorization is rechecked at submit and bound
   to the membership/aircraft-assignment snapshot described in section 7.3.
2. The administrator records source attribution: evidence type, issuing body,
   document/approval number, revision/date when known, acquisition source/URL,
   acquisition time, access/license classification, related AD, and—for an AMOC
   candidate—the claimed aircraft/configuration scope.
3. The server retains the original bytes immutably, computes SHA-256, records
   storage identity and byte count, and creates source-hash-bound rendition/text
   versions. Uploading replacement bytes creates a new version; it never edits
   the prior artifact.
4. A human reviewer independently compares issuer, identity, revision,
   authenticity, completeness, source attribution, and applicable scope with
   the retained bytes. For an AMOC, the reviewer must also verify approval,
   conditions, aircraft/configuration binding, method, and any revised timing.
5. Until admission and human review both succeed, service-bulletin-dependent
   nodes remain `candidate_only`/human-determination-required and an AMOC mention
   displays **possible AMOC—unverified**. Neither state may grant affirmative
   applicability, compliance, terminating credit, next-due values, or released
   actionability.
6. Admission appends document/evidence/signoff lifecycle events and creates a
   new signed input version. A changed input invalidates dependent assessments
   and recurring-due signoff as required by the domain contract. Recalculation
   from the identical already-signed input hashes is deterministic and requires
   no additional human review.

The initial five-packet calibration gate verifies the structural workflow and
these absent/unverified outcomes. A lawfully retained real bulletin or verified
aircraft-specific AMOC-use packet becomes an additional regression fixture when
available; its absence does not authorize invented fixture data and does not by
itself block the initial schema-design gate.

## 4. Evidence fragment and reference model

### 4.1 Immutable page rendition and text versions

No reviewer or parser may submit text and make it authoritative merely by
hashing it. Retained bytes are first projected into immutable, hash-bound page
artifacts:

`ad_source_page_renditions`

- `id`, `source_document_id`, `source_content_hash`, one-based `page_number`;
- renderer name/version/configuration hash, media type, pixel dimensions;
- immutable rendition storage key and `rendition_hash`;
- unique `(source_document_id, source_content_hash, page_number,
  renderer_configuration_hash)`.

`ad_source_page_text_versions`

- `id`, rendition ID, OCR/native extractor name/version/configuration hash;
- immutable text storage key, exact UTF-8 `text_hash`, and glyph/word coordinate
  map storage key/hash;
- extraction quality and native/OCR classification as recorded observations;
- unique `(rendition_id, extractor_configuration_hash, text_hash)`.

The stored page text and coordinate map are generated server-side from the
retained bytes. Reprocessing creates another version; it never updates an old
one. A reviewer may select which page-text version supports a new decision, but
cannot edit its text.

### 4.2 Immutable fragment

`ad_evidence_fragments` is in the official-evidence domain:

| Column | Purpose |
| --- | --- |
| `id` | Stable fragment ID |
| `source_document_id` | FK to immutable retained bytes |
| `source_content_hash` | Approval/release guard bound to the rendition |
| `page_text_version_id` | FK to immutable rendered/extracted page text |
| `page_start`, `page_end` | One-based PDF page range |
| `paragraph_locator` | Paragraph/section label where available |
| `table_locator`, `row_locator`, `note_locator` | Optional bounded location |
| `character_start`, `character_end` | Required offsets for text selection; multi-region fragments use child selections |
| `region_map_hash` | Hash of bounding boxes when a table/column needs coordinates |
| `exact_text` | Server-derived substring/region text; never accepted from the client |
| `fragment_hash` | Hash over source, rendition, text-version and region hashes, offsets, locator, and derived exact text |
| `parser_name`, `parser_version` | Extraction provenance |
| `created_at`, `created_by` | Attribution |
| lifecycle | No mutable status column; append-only lifecycle events determine usability |

Fragments may cover an exact paragraph or a bounded table section. A full-page
text blob is not automatically a clause fragment. Overlap is permitted when
different regulatory units require distinct bounded evidence, but identical
fragment hashes deduplicate.

Cross-page/table fragments use immutable
`ad_evidence_fragment_selections(fragment_id, sequence, page_text_version_id,
character_start, character_end, region_coordinates, selection_hash)`. The
database or fragment service derives `exact_text` from selections in sequence
and verifies every offset/coordinate against the immutable text/rendition.

`ad_evidence_fragment_lifecycle_events` is append-only with event types
`admitted`, `superseded`, and `quarantined`, actor/reason/time, predecessor
event hash, and event hash. Current usability is a deterministic fold or cache;
it is never an in-place mutation of the fragment.

### 4.3 Decision binding

`ad_decision_evidence_bindings` maps `(decision_version_id, evidence_key)` to
one fragment ID and expected fragment hash. Semantic nodes link to bindings by
FK. The local key makes canonical JSON readable; the immutable ID/hash prevents
key reassignment from changing a signed decision.

Approval validates:

1. retained bytes still hash to `source_content_hash`;
2. the document is attributable to the directive or an admitted incorporated
   document;
3. rendition/text hashes match the retained source, selectors are in bounds,
   and the server-derived exact text/hash still matches;
4. fragment hash matches; and
5. each normalized safety value—including `not_applicable`, exclusions, and
   negative installed-equipment/STC assertions—is supported by fragments
   linked for that exact semantic purpose.

The reviewer source navigator labels primary AD evidence separately from a
full-issue audit source and opens at `page_start`. For a full Federal Register
issue, it shows the admitted page range rather than implying page 1 is the AD.

## 5. Normalized PostgreSQL mapping

### 5.1 Signed decision root

`ad_decision_versions`

- `id`, `directive_id`, `schema_version`, `decision_key`
- `canonical_json`, `canonical_hash`, `evidence_binding_hash`
- `source_extraction_id`, `review_id`, `review_decision_event_id`
- immutable creator/provenance fields only; lifecycle, correction, selection,
  reviewer authority, and publication are append-only events/relationships
- unique `(directive_id, decision_key)` and unique canonical hash per directive

`ad_current_decision_selections` has one row per directive with
`decision_version_id`, `selection_generation`, and last selection-event ID. It
is an operational compare-and-swap pointer, not audit authority. A partial
unique index on version-bound projections enforces at most one selected
generation per directive. The pointer changes only in the same serializable
transaction that appends the selection event and activates complete projections.

### 5.2 Shared semantic/evidence infrastructure

`ad_semantic_nodes`

- `id`, `decision_version_id`, `node_type`, `node_key`, `node_hash`
- unique `(decision_version_id, node_type, node_key)`

Each typed semantic row has a one-to-one FK to a semantic node.
`ad_semantic_evidence_links(node_id, evidence_binding_id, purpose, sequence)`
then gives every kind of node an FK-enforced evidence path without a
polymorphic owner ID.

### 5.3 Lossless typed-value, temporal, and logic foundation

Canonical V4 is reconstructable byte-for-byte (after RFC 8785-style canonical
ordering) from relational rows. SQL `NULL` means only “column unused for this
discriminated variant”; it never means unknown.

`ad_value_assertions` stores field-level three-valued assertions:

- `id`, `semantic_node_id`, `field_code`, `state`, `value_type`;
- exactly one typed value column when known: `text_value`, `date_value`,
  `decimal_value`, `integer_value`, `boolean_value`, `enum_value`, or typed
  identity FK;
- `reason_code` and `temporal_scope_id` for unknown/not-applicable;
- unique `(semantic_node_id, field_code)`;
- FK evidence through `ad_value_assertion_evidence(assertion_id,
  evidence_binding_id, purpose, sequence)`.

Normative checks:

```text
CHECK state IN ('known', 'unknown', 'not_applicable')
CHECK value_type IN ('text','date','decimal','integer','boolean','enum',
                     'manufacturer','model','series','stc','document')
CHECK known       => exactly one matching typed value is non-NULL
                     AND reason_code IS NULL
CHECK unknown     => every typed value IS NULL
                     AND reason_code IS NOT NULL
                     AND temporal_scope_id IS NOT NULL
CHECK not_applicable => every typed value IS NULL
                     AND reason_code IS NOT NULL
                     AND temporal_scope_id IS NOT NULL
```

A deferred constraint trigger requires at least one admitted evidence binding
for every assertion at signed-publication time, including not-applicable. State
and value-type columns are PostgreSQL enums or reference-table FKs with stable
codes; free-form reason strings cannot drive evaluation.

Typed supporting tables:

- `ad_temporal_scopes`: discriminator plus inclusive/exclusive start/end date,
  aircraft-time, component-time, or cycle columns; CHECK permits exactly one
  metric family and validates ordered known endpoints. Unknown endpoints are
  child `ad_value_assertions`, never NULL-as-unknown.
- `ad_manufacturer_identities`, `ad_model_identities`, and
  `ad_series_definitions`: source identity, reviewed normalized registry ID,
  series comparator kind/version, and typed members/range terms. Every model
  identity has a required manufacturer-identity FK and is unique by
  `(registry_version, manufacturer_identity_id, normalized_designation)`;
  manufacturer and model are never persisted as one combined identity string.
  Unsupported prose is an unknown assertion, not executable SQL/regex.
- `ad_stc_identities`: STC number, revision, holder, affected-product relation,
  and each field's assertion ID. `ad_stc_scope_relations` links affected product
  roles/scopes. No STC predicate is opaque JSON.
- `ad_identifier_scopes`, `ad_identifier_values`, and
  `ad_identifier_ranges`: identifier kind (`serial`, `part_number`), inclusion
  polarity, lexical comparator version, value/endpoints, and inclusivity.
- `ad_logic_expressions`: decision version, expression key, node type, result
  type, evaluator version. `ad_logic_expression_edges(parent_id, child_id,
  sequence)` represents nested `All`/`Any`/`Not`; typed ref tables connect leaf
  nodes to scope, condition, rule, requirement-state, or predicate IDs. CHECK
  and deferred triggers enforce arity, same-decision references, and acyclicity.
- `ad_predicates`: closed predicate type, comparator version, subject role,
  temporal-scope ID, and FKs to typed identity/identifier/STC objects. There is
  no general matching JSON column.

Field-by-field canonical mapping:

| Canonical field | Relational authority |
| --- | --- |
| `schemaVersion`, `decisionKey` | `ad_decision_versions` constrained columns |
| directive AD/amendment/revision/effective-date/status | one `ad_value_assertions` row per named field on the directive node |
| evidence-key to fragment/hash | `ad_decision_evidence_bindings` with unique decision/key and FKs |
| document type/number/revision/retention/access | `ad_referenced_documents` plus one assertion per variable field |
| product role/manufacturer | `ad_product_scopes` role plus manufacturer assertion/identity FK |
| model kind/list/series | constrained scope kind plus `ad_product_scope_models` or typed series FK |
| serial/part scope | typed identifier-scope/value/range rows |
| condition type/operator/subject/temporal basis | `ad_condition_definitions` and typed predicate/identity/temporal FKs |
| nested scope/condition/activation expression | expression nodes/edges and typed refs |
| rule exclusions | evidence-bound `Not`/source-exclusion predicate; no free-form list |
| requirement/action/branch | `ad_requirements`, action assertion/type, branch table, activation-expression FK |
| document references | FK join from action/requirement to `ad_referenced_documents` |
| initial/recurring timing | timing group plus typed term rows and value assertions |
| prerequisite/alternative/termination edges | constrained same-decision FK edge tables |
| general AMOC provision/authority | typed provision row plus authority assertions/evidence |
| supersession relation | immutable typed relationship edge plus evidence links |

Every semantic table has `decision_version_id`, a same-version FK/constraint,
and unique `(decision_version_id, stable_key)`. All joins used for matching are
FK-backed and typed. JSONB may cache a canonical node for debugging but is never
read by applicability, timing, or authorization evaluators.

Round-trip acceptance requires:

1. validate and canonicalize submitted JSON;
2. persist all typed rows in one transaction;
3. reconstruct JSON solely from rows and ordered keys;
4. canonicalize again; and
5. require identical bytes/hash before a signoff can be recorded.

Database-negative tests directly attempt invalid state/value combinations,
missing value evidence, cross-decision references, duplicate stable keys,
invalid expression arity/cycles, mixed temporal metrics, reversed ranges,
untyped STC/series predicates, and orphan fragment/document FKs.

### 5.4 Incorporated documents

`ad_referenced_documents`

- semantic node / decision version
- document type, source identity state/value/reason
- document number/revision/date state/value/reason
- retention state/reason; optional retained `source_document_id`
- expected retained hash, access classification, current status

Service-bulletin addition appends a referenced-document version or new decision;
it never mutates the signed identity used by an older decision.

### 5.5 Applicability

`ad_product_scopes`

- semantic node / decision version / `scope_key`
- product role
- source manufacturer value
- normalized manufacturer identity ID or explicit unknown state/reason
- model-scope kind, serial-scope kind, part-scope kind

`ad_product_scope_models`

- scope ID, source designation, normalized model identity ID/state/reason,
  sequence; unique source designation per scope
- the normalized model identity's manufacturer FK must equal the scope's
  normalized manufacturer identity; a deferred constraint rejects cross-maker
  model links

`ad_identifier_scope_values` and `ad_identifier_scope_ranges`

- scope ID, identifier kind (`serial` or `part_number`), inclusion/exclusion,
  source value or range endpoints/inclusivity, normalized comparison strategy

`ad_condition_definitions`

- semantic node / decision version / `condition_key`
- condition type, operator, subject product role
- normalized subject identity columns where safe
- typed predicate and temporal FKs; non-authoritative display JSON only
- temporal-basis kind and explicit unknown metadata

`ad_applicability_rules`

- semantic node / decision version / `rule_key`
- scope-expression and condition-expression FKs plus evaluator version

`ad_applicability_rule_scopes(rule_id, scope_id)` and
`ad_applicability_rule_conditions(rule_id, condition_id, polarity)` implement
the reusable joins. `ad_applicability_rule_exclusions(rule_id,
excluded_rule_id)` preserves explicit exclusions.

Existing `applicability_targets`/`ad_target_applicability` may be populated as
version-bound compatibility/search projections while readers migrate. Their
copied citations, conditions, actions, intervals, and source payload are not V4
authority. Long term, catalog search can query the V4 scope/model tables
directly.

Normative search behavior:

- the primary aircraft workflow resolves the aircraft by primary key, reads its
  already-reviewed canonical model identity ID, and joins that ID directly to
  the indexed AD scope/model mapping; it does not repeat manufacturer/model
  text matching and does not require a manufacturer-table join on the hot path;
- make-only search filters the manufacturer identity/source-name field and
  returns every linked model scope;
- model-only search filters model identity/source designation and returns the
  associated manufacturer with every result;
- make-and-model search joins both typed identities and requires both to match
  the same product scope; and
- a concatenated `"manufacturer model"` value may exist only as a derived
  display/search document, never as authoritative applicability data.

Indexes cover reviewed normalized manufacturer ID, exact source manufacturer,
reviewed normalized model ID, exact source designation, and the composite
manufacturer/model join. Search projections retain the source decision version
and cannot broaden an unknown normalization into an affirmative match.

The hot-path index set is deliberately small: aircraft primary key, aircraft
canonical model identity ID, and AD scope/model mapping by model identity ID.
Additional text/fuzzy research indexes belong to a rebuildable derived search
projection, not the authoritative aircraft-applicability transaction path.

Some ADs identify non-controlling product examples using language such as
“used on, but not limited to.” Preserve these in evidence-bound
`ad_applicability_search_hints` with product role, separate manufacturer/model
identity states, relation kind, `exhaustive = false`, and source decision/
evidence binding. Search hints may generate a possible component candidate but
cannot be referenced by an applicability expression, cannot establish a
positive or negative match, and cannot suppress an unlisted configuration.
Aircraft-ID evaluation must still resolve the controlling installed-component
predicates.

### 5.6 Requirements, timing, and branches

`ad_requirements`

- semantic node / decision version / `requirement_key`
- requirement type, action type, review state
- no `target_applicability_id`

`ad_requirements.activation_expression_id` gives explicit nested rule semantics
without cloning the requirement. A derived requirement/rule join may accelerate
queries but is not authority.

`ad_requirement_document_refs(requirement_id, referenced_document_id, purpose)`
links approved data/service information.

`ad_requirement_branches`

- requirement ID, branch kind, alternative group key, predicate state

`ad_requirement_dependencies(requirement_id, prerequisite_requirement_id,
dependency_kind)` and `ad_terminating_effects(terminating_requirement_id,
terminated_requirement_id)` preserve graph relationships.

`ad_timing_groups`

- semantic node, requirement ID, timing kind (`initial` or `recurring`), logic,
  state/reason

`ad_timing_terms`

- timing group ID, sequence, metric, decimal value as `NUMERIC`, unit,
  comparison operator, anchor kind, anchor requirement/event reference state

Evidence attaches to the action node, timing group, and individual timing terms
as needed. Exact action/timing text is not copied into these rows.

### 5.7 General AMOC authority

`ad_amoc_authority_provisions`

- semantic node / decision version / provision key
- approving-authority state/value/reason
- submission destination fields where source-supported
- no aircraft ID, compliance event, or claim of actual use

### 5.8 Aircraft configuration domain

V4 does not embed these rows. A conforming later slice should introduce or
extend:

- `aircraft_configuration_versions`: immutable input set and current pointer;
- `aircraft_configuration_facts`: airframe/component identity, part/serial,
  state (`known`, `unknown`, `not_applicable`), reason, confidence, and validity
  period by date/aircraft time/component time/cycles;
- `aircraft_configuration_fact_evidence`: exact record/source links;
- `aircraft_modifications`: STC/modification identity and revision states,
  installation/removal evidence and effective period.

The existing `aircraft` and `installed_components` rows may remain transitional
projections. A missing `removed_at` must not be interpreted as proof of current
installation when the source history is incomplete.

### 5.9 Aircraft maintenance/compliance evidence domain

Recommended separation:

- `aircraft_ad_evidence_items`: immutable logbook/supporting-record spans and
  hashes—what the source actually says—with record scope (`aircraft`,
  `engine`, `propeller`, `appliance`, or `installed_part`) and the applicable
  component/version ID;
- `aircraft_ad_claim_versions`: machine candidate versus reviewed normalized AD
  number/revision, method/action correspondence, completed requirement keys,
  completion date, aircraft TIS, cycles/component time where applicable,
  return-to-service identity, and recorded next due;
- `aircraft_ad_determinations`: attributable aircraft-specific applicability,
  evidence-sufficiency, terminating-action, and compliance decisions;
- `aircraft_amoc_uses`: possible/verified approval reference, authenticity,
  scope, method, timing changes, aircraft/configuration binding, and signoff;
- existing `ad_compliance_events` as a version-bound projection of sufficiently
  reviewed claims, not the raw evidence authority.

An AD number plus generic “AD complied with” cannot create a verified compliance
event. The correct AD/revision and matching work description or approved-data
reference are necessary but still do not replace completion,
return-to-service, and recurring next-due evidence.

A recurring completion event resets only the timing groups whose full active
requirement set it evidences. It retains the completed requirement keys and all
source-required anchor metrics. A partial or ambiguous entry cannot reset a
shared recurrence group. For a 100-hour/12-month whichever-first rule, the
versioned due calculation derives both bounds from the qualifying completion's
aircraft TIS and date, then selects the earlier bound for display and signoff.

Component-specific work orders, repair dates, engine/part serials,
return-to-service tags, and component markings remain authoritative under the
component evidence record. An immutable installation relation binds that
component to an aircraft over a date/time/cycle interval. Aircraft-ID matching
traverses the relevant current or historical installation; it does not copy
the component evidence into a generic aircraft claim or lose the evidence when
the component moves between aircraft.

### 5.10 Derived assessment domain

`aircraft_ad_assessment_versions`

- aircraft, current AD decision version, configuration version, compliance
  evidence/determination version set, algorithm version, input hash
- canonical customer-facing assessment code
- explanation/evidence links, stale reason, calculated-at, current flag

Calculated due values remain versioned projections. A separately signed
recurring-due determination stores the governing requirement, compliance event,
date/time/cycle inputs, calculation, reviewer, and decision time. Identical
replay preserves that signature; changed inputs stale it.

## 6. Admin reviewer workflow

The global AD extraction page must use forms, not a raw JSON editor:

1. **Source identity and navigation**
   - label primary official AD versus audit/full-issue sources;
   - show source hash and relevant page range;
   - open the PDF at the first admitted page;
   - quarantine mismatched source identity/hash.
2. **Evidence-fragment workspace**
   - highlight exact paragraphs/table rows in bounded source pages;
   - create/reuse a fragment; display every semantic use of that fragment;
   - prevent silent text editing—correction creates a new fragment.
3. **Directive identity form**
   - AD number, amendment/revision, effective date, status;
   - each control has known/not-applicable/unknown state and evidence selector.
4. **Product-scope table**
   - product-role menu, manufacturer field, one model per row, serial/part scope
     controls, normalization review;
   - bulk paste/import table rows without copying shared predicates.
5. **Shared-condition library**
   - installed equipment, part, STC/modification, configuration, and historical
     condition menus;
   - show which applicability rules reuse each condition.
6. **Applicability rule builder**
   - select multiple product scopes, all/any/none condition logic, exclusions,
     and evidence; no free-form condition-key duplication.
7. **Requirement and timing forms**
   - action-type menu, applicability-rule multi-select, approved-data document
     selector, prerequisites/alternatives/exceptions, terminating-effect
     selector;
   - explicit metric/unit/anchor/whichever-first/later controls;
   - exact clause appears beside the normalized values.
8. **Referenced documents and AMOC authority**
   - service-bulletin identity/access/retention status and “Add retained
     document” workflow;
   - general AMOC authority only, with warning that aircraft-specific use is
     reviewed elsewhere.
9. **Unknown and blocker summary**
   - each unknown has reason, evidence, scope, and automation consequence;
   - distinguish publication blocker from allowed candidate-only adjudication.
10. **Decision preview and signoff**
    - compact tree/table plus read-only canonical JSON download;
    - show proposed relational cardinality (for example, five scopes, one
      shared condition, one rule, two requirements), not 182 copied blobs;
    - approve/publish, reject/remediate, and save-draft are distinct events.

The aircraft-specific coverage-discrepancy page follows the same source
comparison pattern but uses the domain-owner-approved menus: product role,
manufacturer/model/series/serial/part relationship, installed equipment/STC,
historical period, inclusion/exclusion/branch, and insufficient/conflicting
evidence. Its decision never edits global AD data; a suspected catalog defect
opens a separate global remediation review.

## 7. Publication and human-signoff gates

### 7.1 Global V4 publication

Required:

- authenticated active `platform_admin` membership;
- exact schema and semantic validation;
- attributable directive identity and verified retained official document;
- all referenced fragment/document hashes reverified;
- at least one product scope, applicability rule, and independently actionable
  requirement;
- no orphan/cyclic references;
- source support for every known safety-relevant value;
- explicit consequence for each reviewed unknown;
- immutable review event, canonical/evidence hashes, reviewer identity/role,
  and transactionally selected current decision.

The schema and lifecycle distinguish `candidate_only` from
`released_actionable`. `candidate_only` is not publication/release: it is never
selected as current released authority, never appears in the released AD
catalog, and never populates compliance, due-state, terminating-credit, or
coverage rows. Every semantic node also records its computed automation gate:
`candidate_only`, `human_determination_required`, or `actionable`; a parent node
cannot be more permissive than any dependency. Only a fully source-supported
decision whose required nodes are actionable may enter
`released_actionable`.

The domain owner permits reviewed packets containing an explicit unknown to be
retained in `candidate_only` for administrator and aircraft-specific
human-review discovery. Their customer-facing assessment is
`Uncertain—human determination required`. Candidate-only records remain barred
from the released catalog and from affirmative applicability, compliance,
terminating-action credit, next-due values, and coverage. Missing source
identity/hash, minimum applicability, requirement, or evidence binding always
blocks both release and candidate acceptance and remains remediation-only.

### 7.2 Aircraft-specific signoff

Human review is required for:

- final applicable/not-applicable decisions that resolve unknown configuration;
- logbook-versus-generated-list coverage discrepancies;
- material configuration/STC installation-history determinations;
- equivalent (not exact) work-description correspondence;
- adequately documented compliance and terminating-action credit;
- verified aircraft-specific AMOC use; and
- every first-established or corrected recurring next-due date/time/cycle and
  every recalculation affected by a new compliance event or changed signed
  input.

No new human review is required for candidate generation, marking unknown or
stale, rebuilding indexes/caches, or deterministic recalculation from unchanged
previously signed inputs.

### 7.3 Authorization snapshot and provisional review policy

Every human signoff is an immutable `ad_signoff_event` bound to:

- actor user ID;
- exact active `organization_membership_id`, organization ID, role, status,
  and membership validity observed at decision time;
- for aircraft-scoped decisions, the exact aircraft assignment/ownership scope
  ID(s), aircraft ID, organization ID, assignment role/status/validity;
- authorization policy name/version, evaluated endpoint/action, captured claims
  hash, decision time, and server authorization result;
- proposal author/editor event IDs and a computed self-review relationship;
- canonical decision/determination hash, expected predecessor event/hash, and
  signature/event hash.

The snapshot is stored in constrained columns plus immutable snapshot JSON for
future audit. Foreign keys bind the historical membership/assignment records;
those records may be deactivated but not deleted while referenced. A current
role name copied into the signoff is not sufficient authority evidence.

Scope rules:

- global source fragments, service-bulletin admission, V4 semantics, and
  release require active `platform_admin` membership at signoff;
- aircraft-specific applicability/evidence/due decisions require an active
  authorized membership and aircraft ownership/assignment scope for that
  aircraft; they cannot edit global AD semantics;
- UI visibility is not a control. Every create/edit/sign/reject/document-content
  endpoint repeats server-side authorization inside the decision transaction.

Provisional conservative policy pending an explicit domain-owner dual-control
decision:

1. one eligible human signoff is sufficient; dual control is not claimed;
2. a person who manually created or edited the exact proposal, evidence
   fragment, referenced document admission, or aircraft determination revision
   cannot be its sole approving signer;
3. reviewing a machine-only proposal is not self-review; merely opening or
   commenting on it does not create authorship;
4. the signer's identity matching a maintenance-record approving person is
   recorded as an audit relationship but is not by itself Paprnav proposal
   self-review; and
5. if no independent authorized signer is available, the object remains
   pending rather than weakening the policy.

All determinations and signoffs append; correction creates a successor event.
Concurrency tests use row locking/CAS and a uniqueness constraint on the
accepted successor for an expected predecessor. Direct API tests cover inactive
membership, wrong organization, missing/expired aircraft assignment, role
downgrade between page load and submit, self-review, concurrent reviewers, and
attempted global mutation by a shop administrator.

## 8. V3 compatibility, migration, correction, and rollback

### 8.1 Additive coexistence

- V1/V2/V3 extraction and review JSON remains immutable audit evidence.
- V4 uses new tables and explicit decision-version IDs. Existing columns are
  not repurposed to mean V4.
- On V4 deployment, all new V3 approvals and corrections freeze platform-wide.
  Existing signed V3 decisions remain read-only transitional authority until a
  V4 decision is selected or the directive is quarantined. Reads never merge
  V3 and V4.
- Every derived/search row records source decision version and algorithm
  version. Stale V3 and V4 projections cannot both be current.

### 8.2 Candidate translation

The V3 translator may:

- hash/deduplicate exact `(sourceDocumentId, pageNumber, text)` citations into
  proposed evidence fragments after verifying them against retained pages;
- convert each V3 manufacturer/model group into product scopes;
- deduplicate byte-identical equipment/condition objects and evidence;
- translate group-key requirement links into proposed rule links;
- translate thresholds and AMOC authority into proposed V4 nodes; and
- record source V3 decision ID/hash and translator version.

It must not:

- use `affectedProducts`, `complianceActions`, or `complianceIntervals` as
  authority;
- infer that similar prose is semantically identical;
- invent normalization, STC, service-bulletin, serial/part, timing, or branch
  semantics;
- rewrite the V3 decision; or
- publish/materialize the proposal without platform-admin source review.

### 8.3 Immutable lifecycle, correction, and supersession state machine

`ad_decision_lifecycle_events` is append-only:

- decision version, sequence, event type, reason, actor/authorization snapshot;
- expected prior event ID/hash, predecessor event hash, event payload hash, and
  event hash; unique `(decision_version_id, sequence)` and prior-event CAS;
- event types: `proposal_created`, `review_requested`, `review_rejected`,
  `candidate_only_accepted`, `released_actionable_accepted`, `selected`,
  `deselected`, `invalidated`, and `quarantined`.

The deterministic fold states are `proposal`, `pending_review`, `rejected`,
`candidate_only`, `released_actionable`, `invalidated`, and `quarantined`.
Permitted transitions are:

```text
proposal -> pending_review
pending_review -> rejected | candidate_only | released_actionable | quarantined
candidate_only -> invalidated | quarantined
released_actionable -> invalidated | quarantined
invalidated -> (terminal; a correction is a new decision version)
rejected -> (terminal)
quarantined -> (terminal; remediation is a new version)
```

Selection is a separate event and is permitted only for a folded
`released_actionable` state. `candidate_only` is never selected as released
authority and cannot populate released catalog, coverage, compliance, due, or
terminating-credit rows. It may be retained only for administrator and
aircraft-specific human-review discovery with the customer-facing assessment
`Uncertain—human determination required`.

`ad_decision_relationships` is immutable and evidence-bound with types
`corrects_decision`, `replaces_decision`, and `invalidates_decision`.
`ad_directive_relationships` separately models regulatory `supersedes` and
`corrects_directive`; a database CHECK prevents self-edges, unique typed edges
prevent duplicates, and deferred graph validation prevents cycles where the
relation must be acyclic.

`ad_invalidation_events` names the changed evidence/document/configuration/
decision input, its old/new hash, affected decision/projection/assessment IDs,
actor or system identity, reason, and algorithm version. Projections are never
mutated from current to stale as audit authority; a new projection generation
is built and the prior generation is deselected by an event.

Correction procedure:

1. create a new immutable decision version linked by `corrects_decision`;
2. review/sign it without changing the selected predecessor;
3. build and validate a complete new projection generation off-line;
4. in one serializable transaction, CAS the expected current selection,
   append invalidation/deselection/selection events, and select the new
   generation; and
5. enqueue deterministic downstream replay using the committed generation ID.

Any error before commit leaves the predecessor selected and appends no partial
events. An error after commit leaves the new decision selected and the replay
queue retryable; released readers still enforce generation completeness.
Supersession never deletes the superseded directive, obligations, or evidence.

### 8.4 Rollback

- Disable V4 writes and current-pointer promotion first.
- A directive that has ever selected a correcting or superseding V4 decision
  may not fall back to V3. Application rollback quarantines it until a
  compatible V4 reader is restored or a new source-reviewed decision is made.
- An unchanged directive with no V4 correction relationship may temporarily
  retain its already-selected source-verified V3 predecessor only under an
  explicit rollback event and generation CAS. No new V3 approval is allowed.
- Preserve all V4 proposals, decisions, fragments, and review events. Do not
  downgrade destructively once V4 regulatory data exists.
- Restore schema only from a verified backup if physical removal is necessary.

Failure-injection rehearsal must interrupt every boundary: fragment admission,
decision event append, projection build, pre-CAS, post-CAS/pre-outbox, and
downstream replay. Tests assert one selected generation, no event without its
transactional pointer consequence, no partial projection visibility,
idempotent retry, and no corrected-V4 fallback to V3.

## 9. Calibration and negative tests

### 9.1 Required calibration matrix

| Pattern | Positive proof | Required negative proof |
| --- | --- | --- |
| Broad manufacturer/model table with shared equipment | One condition reused by all intended scopes; exact table fragment | Same model without equipment is human-required/not applicable, never affirmative |
| Manufacturer/model series | Structured series rule matches supported members | Similar prefix or another manufacturer does not match |
| Serial/part range and exclusion | Boundary values and explicit exclusion | Outside endpoint, excluded value, malformed/unknown serial |
| Engine/propeller/appliance/installed part | Correct component role and identity | Same identity on wrong role/component or removed configuration |
| STC/modification | Known STC identity plus supported installation period | Detected incomplete STC remains unknown; no inferred installation |
| One-time/recurring multi-metric | Correct anchor, unit, whichever logic | Missing metric/anchor never yields a due value |
| Conditional/alternative branch | Only satisfied branch obligations activate | System does not choose an undocumented alternative |
| Terminating action | Explicitly named obligations terminate after reviewed event | Generic modification text grants no terminating credit |
| Installation prohibition | Future-installation rule preserved separately | It is not converted into recurring maintenance |
| Service bulletin | Initial gate: source-stated identity, absent/unverified candidate-only state, and authorized immutable admin-retention workflow | Missing/unseen bulletin-dependent fact stays unknown and non-actionable; later real retained example becomes a regression fixture |
| General AMOC authority | Stored without aircraft claim | General paragraph cannot create compliance or actual AMOC use |
| Aircraft-specific AMOC | Initial gate: no AD-level provision becomes actual use; structural admin-ingestion/review path is complete | Incomplete mention displays **possible AMOC—unverified**, grants no credit, and later real verified use becomes a regression fixture |
| Correction/supersession | New version stales exact affected results | Old rows do not remain current or resurrect on rollback |

### 9.2 2024-14-03 bloat regression

The source-complete calibration must assert:

- all retained PDF buttons identify whether they are primary AD or full-issue
  audit sources and open the relevant page range;
- the five manufacturer populations are scopes with individual model rows;
- the common Garmin installed-configuration predicate is one condition row;
- one applicability rule may reference all scopes sharing that predicate;
- one evidence fragment/table row is reused rather than copied per model;
- no canonical `affectedProducts` array contains the 182 display labels;
- each obligation is one row regardless of 182 model search identities; and
- read-only derived labels, if emitted, cannot be submitted or materialized as
  authority.

### 9.3 Initial supporting-evidence absence gate

The initial five-packet set passes the supporting-evidence portion only when it
proves all of the following without fabricated bytes:

- the 2008-26-10 packet preserves all four incorporated-bulletin identities,
  records their retention/verification state as unknown, and remains
  candidate-only for any method conclusion dependent on their unseen content;
- each packet keeps general AMOC authority separate from aircraft-specific use;
- an unverified aircraft record mentioning an AMOC deterministically produces
  customer label **possible AMOC—unverified**, candidate-only eligibility, and
  no compliance/timing/terminating credit;
- the authorized retention workflow requires original immutable bytes, SHA-256,
  issuer/source/acquisition/access attribution, human authenticity/scope review,
  append-only lifecycle/signoff events, and invalidation on changed inputs; and
- replay with identical signed evidence/version hashes yields the same
  assessment and does not request another human review.

The gate does not claim that retained bulletin content or actual verified AMOC
use has been positively calibrated. Those future real examples are mandatory
regression additions when available, not prerequisites for initial V4 design
approval.

### 9.4 Structural negative tests

Reject:

- any JSON `null`;
- unknown without reason, evidence, or temporal scope;
- duplicate keys or references to missing keys;
- fragment ID/hash mismatch or fragment from an unrelated document;
- exact text that does not occur at the retained locator;
- manufacturer/model concatenation submitted as a single product identity;
- listed scope with no models;
- applicability rule with no scope;
- requirement with no applicability rule or action evidence;
- unsupported threshold metric, unit, anchor, comparison, or decimal value;
- cyclic prerequisites/terminating effects;
- general AMOC provision containing an aircraft-use claim;
- derived summaries in canonical input; and
- V4 promotion if another current decision changed after review began.

### 9.5 Persistence and authorization tests

- N listed models create N searchable model rows but only one shared condition,
  rule, and requirement where source semantics are shared.
- Foreign keys prevent orphan evidence and semantic links.
- Re-running materialization is idempotent for a canonical decision hash.
- Version-bound search never returns stale/mixed V3/V4 rows.
- Concurrent approval uses a row lock/optimistic version and records exactly one
  current decision.
- Unauthorized maintenance-shop users receive 403 from global source,
  fragment, document-add, and publish endpoints even if they call the API
  directly.
- Authorized aircraft/shop review cannot mutate global V4 rows.
- Source-byte/hash change quarantines release and document download.
- V3 translator output is pending and V3 JSON/hash remains byte-identical.
- Rollback eligibility checks reject a semantically invalidated predecessor.

## 10. Implementation slices after design approval

Recommended independent high-risk slices:

1. immutable evidence fragments and relevant-page source navigation;
2. V4 JSON validator, canonical hashing, and proposal storage only;
3. V4 normalized schema/migration and materialization without read cutover;
4. menu/form reviewer UI and signed publication gate;
5. released catalog/search cutover with version-bound projections;
6. aircraft configuration/coverage discrepancy representation;
7. compliance-evidence/AMOC/signoff separation and due-state cutover;
8. V3 candidate translator, quarantine policy, and rollback rehearsal.

Each slice needs a separate adversarial implementation review. Migrations,
public contracts, and publication behavior must not begin until design blockers
are closed.

## 11. Recorded design decisions

1. Manufacturer/model normalization is governed by a separate versioned
   identity registry. Global AD review signs the source identity and exact
   reviewed registry mapping; changing the registry does not rewrite a signed
   decision.
2. A configuration fact known only at aircraft/component time or cycles uses a
   typed metric observation and explicit temporal scope. Its calendar component
   is `unknown` with a reason, never SQL or JSON null and never an inferred date.
3. Service-bulletin identity, revision, retention status, and access status may
   be displayed. Document content is served only when its access/license policy
   permits that user and purpose; lack of access leaves dependent conclusions
   unresolved.
4. One independent, attributable, authorized reviewer is sufficient for the
   initial V4 policy. The proposal/document/fragment author cannot be the sole
   approving signer. Policy versioning permits later dual-control adoption.
5. New V3 approvals and corrections freeze platform-wide at V4 deployment.
6. A directive corrected or superseded by a selected V4 decision always
   quarantines on incompatible-reader rollback; it never falls back to V3.
7. Customer-facing assessment codes live in a versioned database reference set
   with immutable code/meaning versions. Application enums may mirror, but do
   not define, that authority.

These choices are part of the reviewed design contract and may not be silently
changed in migrations or implementation.
