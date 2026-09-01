# AD Compliance Extraction Calibration Set

Status: the linked records are new pending v3 reviews. The
`*.requirements.json` files are retained v2 requirement calibration evidence;
they cannot publish by themselves. AD 2024-14-03's earlier approval is
quarantined because its v2 applicability was materialized as disconnected
manufacturer/model strings. The remaining four were never completed.

The shortlist deliberately covers five different compliance structures from the
14 source-verified reviews. The requirement arrays remain useful source-faithful
drafts, but a publishable v3 review must also contain complete
`applicabilityGroups` and every requirement must add
`applicabilityGroupKeys`. The linked source-bound v3 reviews are already staged;
open the relevant link and edit the complete JSON object in the GUI. The GUI remains the authoritative place to
validate and publish a complete extraction. See
[`AD_APPLICABILITY_SCHEMA_REVIEW.md`](../AD_APPLICABILITY_SCHEMA_REVIEW.md) for
the field rules and PostgreSQL mapping.

## Shortlist

| Pattern | Current v3 review | Complete v3 proposal | Requirement calibration draft |
| --- | --- | --- | --- |
| One-time calendar action plus installation prohibition | [AD 2024-14-03 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_94f8a23dd22a457faf007aa588601018) | [2024-14-03.v3.proposal.json](2024-14-03.v3.proposal.json) — populated in GUI; unresolved OCR, serial-scope, and Note 1 method-schema issues intentionally block approval | [2024-14-03.requirements.json](2024-14-03.requirements.json) |
| Recurring 100-hour/12-month whichever-first inspection; corrective work does not terminate recurrence | [AD 2011-10-09 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_89e2c6f1798743a49fb249c407895620) | Not yet built | [2011-10-09.requirements.json](2011-10-09.requirements.json) |
| Conditional engine-family branches plus installation prohibition | [AD 2002-13-04 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_d8feca4a3f4a4ceab3974cea332a27f5) | Not yet built | [2002-13-04.requirements.json](2002-13-04.requirements.json) |
| Applicability determination, inspect-or-remove alternative, and repair-or-replace branch | [AD 98-17-11 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_c317487e391740dcade16e4451cf4ae4) | Not yet built | [1998-17-11.requirements.json](1998-17-11.requirements.json) |
| Different IFR/non-IFR paths, whichever-first/later thresholds, temporary placarding, corrective action, installation control, and reporting | [AD 2008-26-10 review](http://localhost:3000/logbook/ads/reviews?reviewId=arv_d75c981204fa4795a5f3b15e5ea8394e) | Not yet built | [2008-26-10.requirements.json](2008-26-10.requirements.json) |

## Retained source PDFs

Use **Open in browser** while the local API is running and you are signed in as
a Paprnav administrator. **Open local file** opens the same retained artifact
directly from the workspace.

### AD 2024-14-03

- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_63da3892cf8b4124b49e4066c57858a0/content)
- [Open local file: 2024-15529.pdf](../../backend/.data/ad-sources/federal_register/c7/c7be1903331497057fb55faf9ed5994e61774d8acd287cbbc1cb0da5df423b89/2024-15529.pdf)
- Source document: `asd_63da3892cf8b4124b49e4066c57858a0`
- SHA-256: `c7be1903331497057fb55faf9ed5994e61774d8acd287cbbc1cb0da5df423b89`

### AD 2011-10-09

- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_dca1a807cdab483bbb876bfac5af99b7/content)
- [Open local file: 2011-10988.pdf](../../backend/.data/ad-sources/federal_register/cd/cdcf75940451488e47858bd49c40615803325652ef3143d0df4178a95fe577fe/2011-10988.pdf)
- Source document: `asd_dca1a807cdab483bbb876bfac5af99b7`
- SHA-256: `cdcf75940451488e47858bd49c40615803325652ef3143d0df4178a95fe577fe`

### AD 2002-13-04

- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_2c509af5b8df4eb2aa1cbc2f2563d54d/content)
- [Open local file: 02-16174.pdf](../../backend/.data/ad-sources/federal_register/6a/6abbb7724df98bf571ab84e9d58b18f5ef87a0e89aa29817670c17f4461714b7/02-16174.pdf)
- Source document: `asd_2c509af5b8df4eb2aa1cbc2f2563d54d`
- SHA-256: `6abbb7724df98bf571ab84e9d58b18f5ef87a0e89aa29817670c17f4461714b7`

### AD 98-17-11

- [Open in browser](http://localhost:8000/api/v1/ads/source-documents/asd_9e7cba005b4c4529a699537f4c64940c/content)
- [Open local file: FR-1998-08-20.pdf](../../backend/.data/ad-sources/govinfo/e8/e86e204d59ad3464f31aac3945b73b03ad60adff6989ec3702a99f2d2fa06374/FR-1998-08-20.pdf)
- Source document: `asd_9e7cba005b4c4529a699537f4c64940c`
- SHA-256: `e86e204d59ad3464f31aac3945b73b03ad60adff6989ec3702a99f2d2fa06374`

### AD 2008-26-10

Original final rule:

- [Open original in browser](http://localhost:8000/api/v1/ads/source-documents/asd_37922ee632e24a23a5f0ecd1aa4809fe/content)
- [Open local original: E8-30465.pdf](../../backend/.data/ad-sources/federal_register/17/177c3ed17897931c0dcb902e2e867fdc7348526441d2885f26f80974402e201f/E8-30465.pdf)
- Source document: `asd_37922ee632e24a23a5f0ecd1aa4809fe`
- SHA-256: `177c3ed17897931c0dcb902e2e867fdc7348526441d2885f26f80974402e201f`

2010 correction:

- [Open correction in browser](http://localhost:8000/api/v1/ads/source-documents/asd_3c7aa0ef184646e2b32b1171e44b4f7a/content)
- [Open local correction: 2010-28579.pdf](../../backend/.data/ad-sources/federal_register/67/676a282adba0fea1ef7ddb87787ce85746ea8eb08b43ac28cf059f7ccff39db2/2010-28579.pdf)
- Source document: `asd_3c7aa0ef184646e2b32b1171e44b4f7a`
- SHA-256: `676a282adba0fea1ef7ddb87787ce85746ea8eb08b43ac28cf059f7ccff39db2`

## Review method

1. Open the retained source or stable review link.
2. Create source-cited `applicabilityGroups`. Keep official manufacturer and
   model wording in separate fields; preserve model/serial scope, installed-
   equipment conditions, exceptions, and uncertainty. Add each group key to
   the requirements it governs.
3. Compare every draft `actionText`, condition, threshold, trigger, combination
   rule, terminating-action statement, and citation with the displayed source.
   Preserve the regulatory wording in `actionText`; put normalized meaning in
   the other structured fields rather than paraphrasing the action.
   Treat every existing draft as untrusted calibration input: timing clauses,
   values, requirement types, and citations must be rechecked against the PDF.
   Copy the exact timing clause into `sourceText` and preserve its `anchorKind`.
   Capture the AD's AMOC paragraph in `amocProvisions` rather than an alternative
   maintenance requirement.
4. Edit the requirement draft. Do not remove an `uncertaintyReasons` entry until
   the ambiguity is resolved in the source or the schema/methodology is changed.
5. Replace the full extraction object's `requirements` value with the reviewed
   array; never paste a requirements array as the top-level JSON value. The server
   derives `affectedProducts` and `complianceActions`; do not edit those fields
   as authoritative data.
6. Use **Edit, validate & publish** only after the entire directive—not merely
   the representative calibration passages—has been accounted for.

The first pass should focus on whether the schema can faithfully represent the
source. It should not be treated as a production approval quota.

Any remaining `uncertaintyReasons` now blocks **Approve & publish**. The record
remains editable in the GUI so the calibration question can be resolved without
publishing a partially modeled directive.

AD 2008-26-10 is intentionally reviewed as a two-document source packet. The
2010 correction removes model 188, corrects the Unsafe Condition paragraph
label, and changes the reporting address; the original rule contains the full
compliance table. The review page now retains both bounded sections rather than
silently choosing one document.
