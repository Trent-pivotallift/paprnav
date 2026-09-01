# Pre‑Human‑Calibration Audit — AD Extraction v3 Schema & Materialization

**Scope caveat:** the packet omits `ad_compliance_population.py`, `prepare_ad_compliance_reviews.py`, `stage_ad_review_proposal.py`, `correct_approved_ad_review.py`, `audit_ad_review_evidence.py`, and all touched tests. Those are write paths into the same tables (one is literally named "correct approved review"), so the reviewer‑JSON→DB trace below is **partial by construction**. Line numbers are approximate (≈) post‑image positions derived from hunk headers.

---

## BLOCKERS

**B1 — `anchorKind` is silently discarded; every recurring trigger is persisted as anchored to last compliance.**
`ad_extraction.py:≈60` defines `anchorKind ∈ {effective_date, last_compliance, installation, manufacture, unknown}`, but `ad_recurrence.py:≈300` (`normalize_interval`) returns `trigger_payload(metric, value, unit, source_text)` with no anchor, and `ad_recurrence.py:≈180` writes `anchor_kind=trigger.get("anchorKind", "last_compliance")`. `evaluate_trigger` (`ad_recurrence.py:≈515`) then computes due dates from `last_event.occurred_on` unconditionally. An AD whose recurrence anchors to effective date or installation will produce a wrong due date with no unresolved reason. Safety‑critical.

**B2 — Interval values/units are never evidence‑bound.**
`validate_requirement_evidence` (`ad_extraction.py:≈960`) verifies only group citations, equipment‑condition citations, requirement citations, and `actionText` verbatim containment. `initialThresholds[].sourceText` and `recurringTriggers[].sourceText` are free text that is never located on a retained page, and the numeric `value`/`unit` are never cross‑checked against the cited wording. A hallucinated "100 hours" for a source "10 hours" passes `extraction_approval_blockers` (`ad_extraction.py:≈1420`) cleanly. Intervals are the highest‑consequence numbers in the record and are the least verified.

**B3 — Requirement→group scoping fails silently and can wipe the requirement set.**
`ad_recurrence.py:≈60-75` scopes rows by `row.applicability_group_key in applicability_group_keys`, where the persisted key is `clean(group.get("groupKey"))` (whitespace‑collapsed, `ad_applicability.py:≈228`) but the referenced key is `str(key).strip()` (not collapsed). Any internal‑whitespace difference yields zero scoped rows → zero requirements for that spec, no exception, no `ensure_issue`. If *all* specs mis‑scope, `active_hashes` is empty and the stale sweep at `ad_recurrence.py:≈195` supersedes every existing current requirement for the directive. Approval then reports success while the compliance table is emptied.

**B4 — Per‑group compliance actions are cross‑contaminated in the persisted applicability row.**
`ad_applicability.py:≈240` writes `compliance_actions=output_actions(extraction.output)` and `compliance_intervals=(extraction.output or {}).get("complianceIntervals")` onto **every** group. The v3 model deliberately scopes requirements via `applicabilityGroupKeys`, and this write throws that scoping away at the target level. Any consumer reading `ADTargetApplicability.compliance_actions` (the pre‑existing legacy read path) will attribute all actions to all makes/models.

**B5 — Publication gating is enforced in one endpoint only; the write path is ungated.**
`directive_has_verified_release_evidence` (`ads.py:≈245`) correctly fails closed, but it is applied *only* in `list_directives` (`ads.py:≈190`). `list_aircraft_matches` (`ads.py:≈350`) serializes `directive` with no such gate, and `ensure_review_for_extraction` (`ad_extraction.py:≈620`) auto‑approves LLM output, sets `directive.review_status="approved"` + `approved_at`, and calls `populate_applicability_from_extraction` **and now** `materialize_requirements_from_extraction` — without ever invoking `extraction_approval_blockers`, `source_evidence_status`, or the AD‑number identity check. Machine approval writes applicability, requirements, triggers, and due state that owners can reach through the matches endpoint. The gate must move to the write path, or at minimum be applied uniformly to every directive‑exposing endpoint.

**B6 — AMOC is absent from schema, validation, and persistence.**
No `amoc`, alternative‑method‑of‑compliance, or approving‑authority field exists in `AD_EXTRACTION_JSON_SCHEMA` (`ad_extraction.py:≈130-265`), `validate_requirement` (`ad_extraction.py:≈890`), or the migration. `requirementType: "alternative"` conflates in‑rule alternatives with AMOCs, which are separately approved artifacts with their own numbers and citations. A record that cannot represent an AMOC cannot represent AD compliance status.

**B7 — Unique constraint loses its guarantee under PostgreSQL NULL semantics.**
`20260822_0021_add_ad_applicability_v3.py:38-52` adds nullable `applicability_group_key` to `uq_ad_target_applicability`. In PG (<15 default), NULLs are distinct, so every legacy/non‑v3 row (`upsert_target_applicability` called with `applicability_group_key=None`, `ad_applicability.py:≈78`) and every row with a null `source_publication_id` is now unconstrained. Idempotency depends solely on the SELECT‑then‑INSERT at `ad_applicability.py:≈70-95`, which is racy. Use `NULLS NOT DISTINCT`, a partial unique index, or a non‑null sentinel key.

**B8 — Migration is not safely reversible and back‑fills nothing.**
`downgrade()` (`…_v3.py:55-76`) drops the columns and recreates the narrow constraint; if any duplicates were created while the loose constraint was live, the downgrade fails mid‑migration. There is no pre‑flight duplicate check on upgrade, no backfill/`server_default` for `equipment_conditions`/`source_payload`, and `op.drop_constraint` will fail outright on SQLite if any test/dev path runs migrations there.

**B9 — Unconditional overwrite of `serial_range` on every upsert.**
`ad_applicability.py:≈96` now sets `applicability.serial_range = serial_range` with default `None`. The legacy branch (`ad_applicability.py:≈175`) never passes it, so any previously stored serial scope on an "extraction"‑basis row is nulled on re‑run. Callers outside this packet (source‑row ingestion) would suffer the same erasure. Serial applicability is exclusion‑bearing data; erasing it is an over‑application hazard.

**B10 — Approval evidence is recomputed, not pinned.**
`decide_extraction_review` (`ads.py:≈505`) validates against `full_text_pages_for_extraction(...)`, which falls back to `extract_full_text_pages` (re‑reading storage) whenever the cache fails `persisted_source_pages` (`ad_extraction.py:≈1075`). On approval the code writes `extraction.output` but never re‑persists `retainedSourcePages`. The approved record therefore may not contain the exact pages the human approved against — the audit trail is breakable precisely in the case where it matters.

---

## HIGH (near‑blocker)

**H1 — Wrongly admitted "correction" text can back citations.** `bounded_source_document_pages` (`ad_extraction.py:≈1265`) admits `identity_unverified` documents when *any* sibling is verified, using `correction_document_mentions_ad` (`≈1305`), which only requires the AD number, a correction keyword, and a Part 39 phrase anywhere in a slice that may itself have been anchored by the title‑term fallback in `bounded_issue_pages` (`≈1200`). Foreign rule text can enter the page index and satisfy `validate_citations_against_pages`.

**H2 — Reviewer edits to `complianceActions` are silently overwritten.** `decide_extraction_review` (`ads.py:≈503`) pipes `payload.output` through `derive_compliance_action_summaries` (`ad_extraction.py:≈543`) *before* validation and persistence; `complianceActions` and `affectedProducts` are replaced with derived values. A deliberate human correction to those fields cannot be saved.

**H3 — Legacy field re‑conflates manufacturer and model.** `affected_product_labels` (`ad_extraction.py:≈565`) and `affected_products_from_applicability` (`≈860`) join make+model into one string — the exact concatenation the v3 prompt forbids (`≈32`). `populate_applicability_from_extraction` branches on key presence, not `schema_version` (`ad_applicability.py:≈140`), so any v3 output lacking `applicabilityGroups` falls back to `parse_product_text` string parsing of those conflated labels. `affected_products_from_applicability` also includes `"historical"` status rows.

**H4 — Empty‑group re‑extraction leaves stale `current` rows.** `populate_v3_applicability` (`ad_applicability.py:≈198`) returns early on empty groups *before* the supersede `UPDATE`, so prior current applicability (and, via the `if applicability_rows:` guard at `ad_recurrence.py:≈194`, prior requirements) persist unchanged.

**H5 — `list_extraction_reviews` serializes and re‑parses every review per request.** `ads.py:≈270-300` builds `serialized_reviews` for *all* reviews just to compute counters, and each `serialize_review` (`≈740`) may re‑read and re‑parse retained PDFs. O(N) PDF parses per page load.

**H6 — `equipmentCombinationLogic` (AND vs OR of installed equipment) has no first‑class column.** Persisted only inside `source_payload` (`ad_applicability.py:≈244`); `equipment_conditions` is stored without its combining operator, so any consumer reading that column alone will guess.

---

## MEDIUM / FOLLOW‑UPS

- `initialThresholds` are never materialized — they only append `initial_threshold_requires_adjudication` (`ad_recurrence.py:≈80`). Fail‑closed, but the initial compliance window is unrepresentable. (`ad_recurrence.py:≈80`)
- `citations` and `confidence` are not updated on the existing‑hash branch (`ad_recurrence.py:≈188-192`); edited citations never propagate.
- Pre‑2000 identity regex: `official_ad_number` yields `98-17-11` (`ad_extraction.py:≈1325`) and `source_evidence_status` (`≈1345`) anchors with `\b`, which cannot match `1998-17-11` in retained text → false quarantine.
- `list_directives` applies `LIMIT` *before* the release‑evidence filter (`ads.py:≈185-196`) → under‑filled, unstable pages.
- `ad_number.desc()` lexicographic ordering across 2‑ and 4‑digit year formats (`ads.py:≈186`).
- `review_id` miss returns an empty list rather than 404; `currentOffset = matching_index or 0` (`ads.py:≈288`).
- `quarantinedCount` counts all non‑verified reviews including already‑decided ones (`ads.py:≈300`).
- `models = model_scope.get("models") or [None]` (`ad_applicability.py:≈212`) creates `model=NULL` targets for `kind ∈ {expression, unknown}` — over‑broad target identity.
- Serial `excludedValues` survive only inside opaque JSON (`ad_applicability.py:≈236`); no consumer in this packet enforces them.
- `terminatingAction` is an uncited free string (`ad_extraction.py:≈250`) with no link to the requirement it terminates.
- Confirm `Any` is imported in `ad_applicability.py` (used at `≈195` in the new signature; not visible in the packet).

---

## Verdict

**FAIL FOR HUMAN CALIBRATION.**

The v3 separation of manufacturer/model/serial/equipment/groups is genuinely well‑formed at the schema and validation layer, and the identity/evidence gating is thoughtfully fail‑closed. But the materialization layer discards `anchorKind` (B1), leaves interval numbers unverified (B2), can silently zero the requirement set (B3), cross‑contaminates actions across groups (B4), and the approval gate is bypassed entirely by the auto‑approval path that now also writes requirements (B5). Add the missing AMOC model (B6), the NULL‑weakened unique constraint (B7/B8), and `serial_range` erasure (B9). Human calibration against these outputs would be calibrating against records that do not faithfully encode the source. Resolve B1–B10 and re‑submit with the omitted scripts and tests included in the packet.
