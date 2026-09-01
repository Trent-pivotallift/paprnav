# AD Extraction Domain Contract

Status: domain-owner approved for schema design; implementation not authorized  
Contract version: 1.1  
Domain owner: Paprnav platform administration  
Approval recorded: 2026-08-25 in the Paprnav T081 task  
Calibration-scope clarification recorded: 2026-08-29 in the Paprnav T081 task  
Last reviewed against cited primary sources: 2026-08-25  
Safety posture: fail closed; machine extraction and matching are decision support, not regulatory approval

## Purpose

Paprnav must retain the complete official Airworthiness Directive (AD) as
authoritative evidence. It does not need to convert the complete AD into
structured data.

This contract defines the minimum regulatory meaning Paprnav must preserve to
support candidate matching, evidence review, and due-state calculations. It is
intentionally independent of any JSON, API, or PostgreSQL representation. A
proposed technical schema must conform to this contract; it must not redefine
the contract to accommodate an existing implementation.

## Domain boundaries

The system must keep the following domains separate:

1. **Official AD evidence** — the complete retained regulatory document,
   corrections, incorporated references, source identity, and content hashes.
2. **Structured AD decision data** — the small, source-supported subset needed
   to identify candidate applicability and model compliance obligations.
3. **Aircraft configuration** — the aircraft, airframe, engines, propellers,
   appliances, installed parts, modifications, serial numbers, part numbers,
   Supplemental Type Certificates (STCs), and configuration history against
   which applicability is evaluated.
4. **Aircraft maintenance and compliance evidence** — what the aircraft's
   logbooks and supporting records actually state about work performed,
   completion, approval for return to service, AD status, and next-due state.
5. **Paprnav assessment** — a derived, attributable conclusion about candidate
   applicability, evidence sufficiency, and due state. An assessment is not
   source evidence and does not itself constitute regulatory approval.

No domain may silently substitute for another. In particular, an AD number
found in a logbook is not by itself evidence that the required action was
performed, and a machine-generated match is not a final applicability
determination.

## Questions Paprnav must answer

For each aircraft, Paprnav should support answering:

- Which ADs may apply to its airframe, engines, propellers, installed
  appliances, parts, and modifications?
- Is each potentially applicable AD represented in the aircraft records?
- Does the record document a compliance method, an AD-prescribed method or
  approved-data reference, or an aircraft-specific approved AMOC?
- When was compliance accomplished, expressed by the applicable date,
  aircraft time, cycles, or component time?
- Is the action recurring, and when is the next action due?
- Was the obligation superseded, terminated, or satisfied through an approved
  alternative?
- Is the available source, configuration, or maintenance evidence insufficient,
  requiring human determination?
- Does the logbook identify an AD that was not on Paprnav's generated list? If
  so, create an applicability discrepancy for administrator review.

The FAA states that an applicability search must consider the aircraft,
engines, propellers, installed appliances, model series, and relevant installed
parts or modifications. See [FAA applicability and compliance
guidance](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/app_comp).

## Minimum structured AD information

Only information needed to support candidate matching, obligation modeling,
due-state calculation, source review, and audit should be structured.

| Area | Needed structured information |
| --- | --- |
| Identity | AD number, revision or amendment identity, effective date, and current or superseded status |
| Applicability | Product role, manufacturer, model or series, Supplemental Type Certificate (STC), serial-number or part-number scope, installed-equipment or modification conditions, and exclusions |
| Obligations | Stable requirement identity and the required action or approved-data reference |
| Timing | Initial deadline, recurring interval, governing time or cycle metric, anchor, and whichever-first or whichever-later logic |
| Branches | Alternatives, prerequisites, exceptions, terminating actions, and installation prohibitions |
| Authority | The AD's general AMOC provision, kept separate from any aircraft-specific approved AMOC actually used |
| Evidence | Reference to the authoritative document, retained source hash, page, paragraph or table location, and preserved source clause |

This information is substantially less than the complete AD.

## Applicability

Applicability must preserve relationships rather than flatten them into display
strings. Paprnav must be able to distinguish:

- aircraft, engine, propeller, appliance, installed part, and modification
  roles;
- source manufacturer identity from any reviewed normalized search identity;
- manufacturer, model, series, serial number, STC, and part number;
- configuration-wide conditions from conditions specific to one branch;
- included populations from exclusions;
- known scope from expressions or ambiguity that require human review; and
- the configuration time period for which a component or modification was
  installed.

A broad search result is a candidate AD. Applicability becomes affirmative only
when the recorded configuration satisfies every evaluable condition. Missing,
ambiguous, or unsupported conditions must remain uncertain rather than being
treated as applicable or not applicable.

`Unknown` is an explicit domain state, not a synonym for a missing or null
value. An unknown value must retain a reason such as not observed, unavailable,
not extracted, not yet reviewed, or conflicting evidence, together with its
evidence and temporal scope. `Null` must not be used to represent regulatory or
configuration uncertainty.

## Compliance obligations and timing

The structured representation must preserve each independently actionable
obligation and its relationship to the applicable product or configuration.
It must support:

- one-time and recurring actions;
- inspections, replacements, modifications, limitations, reporting, and
  installation prohibitions;
- alternative and conditional branches;
- prerequisites and exceptions;
- initial and recurring thresholds;
- calendar, aircraft-time, cycle, and component-time metrics;
- effective-date, completion-event, installation-event, and other explicit
  source anchors;
- whichever-first and whichever-later combinations;
- terminating actions; and
- incorporated service information or other approved-data references.

The exact regulatory action and timing clauses must be preserved once as
evidence. Normalized semantics may support calculation, but they must not
replace or silently paraphrase the source clause.

## Official source evidence

Paprnav must:

- retain the complete official PDF once, together with its source identity and
  verified content hash;
- retain corrections and other authoritative documents that alter the rule;
- preserve exact applicability, action, timing, exception, and
  terminating-action clauses once;
- reference preserved clauses rather than copying identical document IDs and
  text into every model, condition, and obligation;
- preserve page and, where available, paragraph, table, row, or note location;
- preserve references to incorporated service information because the detailed
  method may be contained in a service bulletin or other incorporated
  document;
- retain referenced service bulletins when Paprnav can lawfully obtain them,
  together with their title, document number, revision, date, source,
  administrator attribution, and verified content hash;
- provide an administrator workflow to locate and add a missing service
  bulletin without editing the retained AD or substituting manually entered
  text for the document;
- when a referenced service bulletin remains unavailable, preserve its known
  identity and access status and keep any conclusion that depends on its unseen
  contents unresolved; and
- distinguish source wording from reviewed normalized values.

Preamble material—including discussion, cost estimates, comment responses,
federalism findings, and addresses—does not need structured conversion unless
it is needed for provenance, source navigation, or interpretation of a modeled
rule clause.

The FAA distinguishes the preamble, which provides the basis and purpose, from
the rule, which establishes the regulatory requirements. See [FAA AD content
guidance](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/ad_content).

## Aircraft configuration

Applicability evaluation requires configuration evidence independent of both
the AD and the maintenance-event record. Paprnav should preserve, when known:

- airframe manufacturer, model, serial number, and type or series identity;
- installed engine, propeller, appliance, and component identities;
- part and serial numbers;
- supplemental type certificates and other relevant modifications;
- installation and removal dates, times, or cycles; and
- the source and confidence of each configuration fact.

Paprnav should retain as much STC information as the evidence supports,
including the STC number and revision, affected product or configuration,
installation or removal evidence, effective period, and source. If an STC is
detected but any required identity, installation, or scope information is
incomplete, preserve the detected evidence and mark the missing information as
explicitly `unknown`; do not invent the value or infer that the STC was
installed or applicable.

When configuration history is incomplete, Paprnav must not infer that an AD was
or was not applicable during an unobserved period.

## Aircraft maintenance and compliance evidence

For Part 91 records, the current AD-status record includes the AD number and
revision, method of compliance, and, for recurring actions, the time and date
the next action is required. The underlying maintenance entry ordinarily
includes a description of the work or an acceptable-data reference, completion
date, and the signature and certificate information of the person approving
the work for return to service. See [14 CFR §
91.417](https://www.govinfo.gov/content/pkg/CFR-2024-title14-vol2/pdf/CFR-2024-title14-vol2-part91.pdf)
and [14 CFR §
43.9](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-43/section-43.9).

Paprnav must store separately:

- what the source record actually states;
- machine-extracted candidate values;
- reviewed normalized values;
- Paprnav's evidence-sufficiency assessment; and
- any attributable human determination.

The product should not represent that Paprnav itself approves a compliance
method. It may report whether the record documents a method, whether the method
corresponds to a modeled AD-prescribed method or approved-data reference, and
whether an approved AMOC reference is present and verified.

## AMOC distinctions

The following concepts must not be conflated:

1. **AD AMOC provision** — language in the AD identifying the authority or
   process by which an alternative method may be requested or approved.
2. **Aircraft-specific approved AMOC** — an actual approval relied upon for a
   particular aircraft or affected population, including its approval
   reference, scope, method, conditions, and any revised compliance time.

An AMOC can change both the method and the compliance time. Paprnav must not
treat the presence of a general AMOC paragraph as evidence that an alternative
was approved or used for an aircraft. See [FAA AMOC
guidance](https://www.faa.gov/aircraft/air_cert/continued_operation/ad/alt_moc).
When aircraft evidence is unclear, the customer-facing assessment is
**Possible AMOC—unverified**. That state does not establish that an AMOC was
approved or used and requires human review.

## Assessment vocabulary

Paprnav must be able to distinguish at least:

- AD listed and adequately documented;
- AD listed but compliance evidence incomplete;
- potentially applicable AD not found in the aircraft records;
- logbook AD not applicable to the recorded configuration;
- recurring AD with next-due information missing;
- candidate applicability with insufficient configuration evidence;
- **Possible AMOC—unverified** when an aircraft record mentions or appears to
  rely on an AMOC but its approval, authenticity, scope, or aircraft binding is
  incomplete;
- superseded or terminated obligation; and
- uncertain—human determination required.

Assessments must identify the evidence and configuration state on which they
were based. New evidence or a configuration correction must make affected
assessments stale and trigger reevaluation.

The canonical assessment labels are customer-facing. Their meaning must remain
stable and auditable. Presentation settings may change ordering, filtering, or
supplemental explanation, but they must not rename a canonical state, suppress
a material warning, or change an approval blocker.

## Aircraft-specific applicability discrepancy review

When an aircraft record identifies an AD that Paprnav did not include in its
generated candidate list, the system must create a source-cited coverage
discrepancy for administrator review. A logbook mention must not automatically
change the released AD catalog, establish applicability, or establish
compliance.

The administrator workflow should follow the source-comparison pattern of the
AD extraction review page, but it must use structured menus rather than a JSON
editor. It must display the official AD evidence, the relevant aircraft-record
evidence, the recorded aircraft configuration, and the reason the AD was
excluded from the generated list.

The administrator records why the AD applies, may apply, does not apply, or
cannot yet be determined by selecting and documenting the applicable basis:

- affected product role: airframe, engine, propeller, appliance, installed
  part, or modification;
- manufacturer, model, series, serial number, or part number relationship;
- installed-equipment or modification condition, including an STC when
  relevant;
- current or historical installation period;
- applicable inclusion, exclusion, exception, or branch in the AD; and
- insufficient or conflicting source, configuration, or record evidence.

The decision must retain the administrator's identity, organization and role,
time, selected rationale, notes, and cited evidence. An aircraft-specific
determination must not silently modify global AD applicability. If the review
indicates that the retained AD extraction or catalog is incomplete, the system
must open a separate global AD remediation review. A change to the AD,
configuration, or supporting evidence makes the affected determination stale
and requires reevaluation.

## Derived versus authoritative information

The following are examples of derived information and must not become
independent regulatory truth:

- flattened affected-product labels;
- display-oriented compliance-action summaries;
- calculated next-due dates, times, or cycles;
- candidate applicability rankings;
- search indexes;
- fleet coverage counts; and
- user-interface grouping or navigation labels.

Derived values must be reproducible from the reviewed structured AD data,
aircraft configuration, and aircraft evidence. They must retain links to those
inputs and be invalidated when an input changes.

## Human review boundary

Machine extraction is always a proposal. A reviewer must be able to compare
each safety-relevant structured value with the exact retained source clause.
The reviewer interface must:

- open the correct retained document at the relevant page or page range;
- show source evidence without requiring repeated text in the editable data;
- distinguish source wording, normalized values, and derived display values;
- explain uncertainty and approval blockers;
- prevent approval when source identity, source hash, citation, applicability,
  timing, obligation, or branch evidence is missing or inconsistent; and
- preserve reviewer identity, decision time, reviewed content, and later
  corrections as immutable audit history.

Human review is required when a recurring next-due date, time, or cycle is
first established or corrected. The decision must retain the governing
requirement, last-compliance event, date and time-or-cycle inputs, calculation,
reviewer, and review time. A new compliance event or a change to any signed
input requires a new review of the resulting recurring next-due value.

Human review is not required for:

- candidate generation;
- marking information `unknown` or stale;
- rebuilding search indexes or caches; or
- deterministic recalculation from unchanged, previously signed inputs.

Those automatic operations must preserve the signed input identities and may
not change an authoritative decision or convert uncertainty into an affirmative
state.

## Required search and review capabilities

A conforming design must support at least these questions without parsing
flattened display strings:

- Find ADs potentially applicable to a manufacturer, model, and series.
- Find ADs applicable to a particular engine, propeller, appliance, installed
  part, or modification.
- Determine whether a serial or part number is included, excluded, or unknown.
- Find obligations involving a particular installed-equipment condition.
- Find one-time or recurring obligations by time, cycle, or calendar metric.
- Determine the source clause and retained document supporting a result.
- Identify requirements whose conditions cannot be evaluated automatically.
- Identify an aircraft record that lacks method, completion, approval, or
  recurring next-due evidence.
- Recalculate affected assessments after an AD correction, configuration
  change, or logbook-evidence correction.

## Non-negotiable invariants

1. The complete official AD and every authoritative correction are retained as
   immutable evidence; structured data never replaces them.
2. Only the minimum operational subset is structured.
3. Source clauses are preserved once and referenced; identical citation text is
   not repeated throughout the canonical structured decision.
4. Official source evidence, structured AD data, aircraft configuration,
   aircraft records, and Paprnav assessments remain separate.
5. Every safety-relevant structured value is traceable to retained evidence.
6. Source wording and normalized meaning remain distinguishable.
7. Uncertainty, missing configuration, and unsupported logic fail closed to
   human determination.
8. An AD number alone is not evidence of compliance.
9. General AMOC authority is not an aircraft-specific AMOC approval.
10. Paprnav reports evidence and assessments; it does not grant regulatory
    approval.
11. Derived summaries never drive authoritative persistence or matching.
12. Corrections, supersedure, configuration changes, and evidence changes
    invalidate affected derived state and require attributable reevaluation.

## Calibration expectations

Candidate schemas must be tested against representative directives covering:

- broad tables of manufacturers and models with shared conditions;
- serial and part-number ranges and exclusions;
- installed appliances and modifications;
- conditional and alternative compliance branches;
- one-time and recurring timing with multiple metrics;
- terminating actions and installation prohibitions;
- incorporated service information, including referenced-but-unretained and
  retained-but-unverified fail-closed states;
- corrections and superseding directives; and
- the distinction between general AMOC authority, **possible
  AMOC—unverified**, and verified aircraft-specific AMOC use.

For every calibration case, the review must identify the expected candidate
applicability, obligations, timing, evidence references, negative aircraft or
component cases, unresolved clauses, and the queries the result must support.

The initial five-packet AD calibration set is not required to contain lawfully
obtained incorporated service-bulletin bytes or a real aircraft-specific AMOC
approval/use record. Those are separately administered evidence types, not
facts that may be manufactured from an AD. The initial gate must instead prove:

- a referenced service bulletin can retain its source-stated identity while
  absent or unverified bytes remain explicit `unknown`/candidate-only and no
  dependent method becomes actionable;
- a general AD AMOC provision never becomes an aircraft-specific use record;
- an incomplete aircraft AMOC reference is customer-facing as **possible
  AMOC—unverified**, remains candidate-only, and grants no compliance, timing,
  or terminating-action credit;
- only an authorized administrator can ingest those evidence types, with
  immutable bytes, verified content hash, source attribution, access status,
  and an append-only review decision before any dependent node becomes
  actionable; and
- deterministic recalculation from unchanged signed inputs does not require a
  new review, while changed evidence or signed inputs invalidates dependent
  assessments and invokes the existing human-review boundary.

When Paprnav later lawfully obtains a real incorporated service bulletin or a
real aircraft-specific AMOC-use record, its source-complete reviewed packet must
be added as a regression fixture. Future fixture availability extends the
calibration corpus; it is not a prerequisite for the initial five-packet V4
schema-design gate.

## Resolved domain decisions

The domain owner made the following decisions during human review:

- what evidence is sufficient to mark a compliance method as corresponding to
  an AD-prescribed method? The aircraft record must identify the correct AD and
  revision and contain a work description that corresponds to the applicable
  required action, or cite the approved data prescribing that action. Method
  correspondence may be established by exact wording or an attributable human
  review of equivalent wording; it must not be inferred from the AD number or a
  generic statement such as "AD complied with" alone. Method correspondence
  does not by itself establish adequately documented compliance. That assessment
  also requires the applicable completion, approval-for-return-to-service, and
  recurring next-due evidence described by this contract.

- when an incorporated service document must also be retained? Retain
  referenced service bulletins when lawfully obtainable. If one is unavailable,
  an administrator may locate and add it through the document-review workflow;
  until then, preserve its identity and access status and leave conclusions
  depending on its contents unresolved.
- how service-bulletin and aircraft-specific AMOC evidence participates in the
  initial calibration gate? Both are authorized administrator-ingested evidence
  types. Initial calibration proves their absent/unverified fail-closed states
  and the immutable retention/review workflow; it does not require those real
  artifacts to exist. A lawfully obtained, reviewed real example becomes a
  regression fixture when available.
- how an aircraft-specific AMOC's scope and authenticity are verified? When the
  documentation is unclear, display **Possible AMOC—unverified** and require
  human review. Do not state that the AMOC was approved or used until its
  approval reference, authenticity, scope, conditions, and aircraft or
  configuration binding are verified.
- which applicability and due-state conclusions require explicit human
  signoff? A newly established or corrected recurring next-due date, time, or
  cycle requires attributable human review. Candidate generation, marking
  information `unknown` or stale, rebuilding indexes or caches, and
  deterministic recalculation from unchanged signed inputs do not. A new
  compliance event or changed signed input requires a new review of the
  resulting recurring next-due value.
- how historical configuration uncertainty is presented? Do not guess. Use an
  explicit `unknown` state with a reason, evidence scope, and time period; do
  not use `null` to represent uncertainty.
- where component-specific maintenance evidence belongs? Engine, propeller,
  appliance, and installed-part work orders, serials, return-to-service tags,
  and maintenance entries remain attached to that component's evidence record
  or logbook. The aircraft association is a time-bounded installation
  relationship; copying the evidence into a generic airframe record must not
  become separate authority.
- how a reviewed directive with an explicit unknown is exposed? It may be
  retained for administrator and aircraft-specific discovery only as
  **Uncertain—human determination required**. It is not a released or
  automation-eligible directive and must not establish affirmative
  applicability, compliance, terminating-action credit, a next-due value, or
  coverage. Missing source identity, retained evidence, minimum applicability,
  or minimum obligation data remains remediation-only.
- which assessment labels are customer-facing versus internal review states?
  The canonical assessment labels are customer-facing. Presentation may be
  configured, but material warnings and approval blockers remain visible and
  the stored meaning of a label cannot be changed.

Schema authors and reviewing models may identify contradictions or propose a
change for domain-owner consideration, but they must not silently alter these
decisions in code or data structure.
