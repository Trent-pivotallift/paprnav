# Airworthiness Directive Ingestion & Comparison Pipeline

**Status:** Legacy draft spec. See `.ai/AD_INGESTION_REVIEW.md` and `.ai/MVP_COMPLETION.md` for the current MVP direction.
**Owner:** Trent / PivotalLift
**Purpose:** Ingest FAA Airworthiness Directives (ADs) into AWS, persist them durably, and compare against downloaded aircraft maintenance records.
**Intended consumer:** Engineering agent (Claude Code or human) picking this up cold.

---

## 1. Context

Web app that pulls FAA Airworthiness Directives and compares them against a downloaded aircraft maintenance book to flag potential non-compliance. ADs are FAA-issued rules that mandate maintenance actions on specific aircraft, engines, propellers, or appliances. Missing an applicable AD is a safety and regulatory issue.

This document defines the **ingestion + retention** half of the system. Comparison logic against the mx book is downstream and partially out of scope here.

Current MVP note: paprnav now treats AD-to-logbook matching and HITL adjudication as core MVP behavior. The AWS services below are a future production architecture option, not the required MVP architecture.

---

## 2. Goals & non-goals

### Goals
- Reliable, idempotent ingestion of all current and newly published FAA ADs.
- Immutable raw storage for audit (source-of-truth preservation).
- Structured index queryable by make/model/serial/effective date.
- Resolution of supersession chains so queries return the **currently effective** AD.
- Decision-support output, not compliance attestation.

### Non-goals
- Replacing official FAA compliance tracking.
- Real-time push notifications (poll cadence is acceptable; ADs are not high-velocity).
- Foreign airworthiness authorities (EASA, TCCA) — US FAA only for v1.

---

## 3. Source systems

| Source | Use | Notes |
|---|---|---|
| **Federal Register API** (`https://www.federalregister.gov/developers/api/v1`) | **Primary** discovery + content feed | JSON, public, no auth. Filter by agency=`federal-aviation-administration`, type=`Rule`. ADs publish here first. |
| **FAA Dynamic Regulatory System** (`drs.faa.gov`) | Backfill + reconciliation only | Replaced the legacy RGL. No official API. Scrape sparingly; expect format changes. |
| **FAA Emergency AD listings** | Fast path for emergency ADs | Lower volume but higher urgency. Treat as separate queue. |

**Do not** make DRS the primary path. Federal Register is the system of record for new publications.

---

## 4. Target architecture (AWS)

```
EventBridge Scheduler (every 4–6h)
        │
        ▼
  Poller Lambda  ──► SSM Parameter Store (last-seen watermark)
        │
        ▼
      SQS (ad-discovery-queue, with DLQ)
        │
        ▼
  Fetcher Lambda ──► S3 (raw artifacts, versioned + Object Lock)
        │           ──► DynamoDB (structured AD index)
        │           ──► OpenSearch Serverless (full-text + semantic)
        ▼
  Bedrock (Claude) — applicability extraction, content-hash-keyed cache
```

### Component responsibilities

- **EventBridge Scheduler** — cron trigger. Every 4–6h is enough; ADs are not high-velocity. Add a second schedule (15min) for the emergency AD path.
- **Poller Lambda** — queries Federal Register API with `publication_date >= watermark`. Enqueues one SQS message per new/updated AD. Updates watermark only after successful enqueue.
- **SQS** — decouples discovery from fetch. Enables replay. Configure DLQ with CloudWatch alarm on depth > 0.
- **Fetcher Lambda** — for each message: fetch full HTML + linked PDF, hash content, write raw to S3, extract structured fields, write to DynamoDB, index to OpenSearch, trigger Bedrock extraction if new content hash.
- **S3** — bucket `pivotallift-ad-raw` (or env-prefixed). Versioning **on**. Object Lock in Compliance mode if the legal review supports it; otherwise Governance mode. Layout: `s3://pivotallift-ad-raw/{ad-number}/{version}/{source.html|source.pdf|metadata.json}`.
- **DynamoDB** — see schema below.
- **OpenSearch Serverless** — collection `ad-search`. Hybrid lexical + vector index for fuzzy applicability queries.
- **Bedrock** — Claude (Sonnet or Haiku depending on cost/accuracy bake-off) for applicability extraction. Cache results in DynamoDB keyed by SHA-256 of normalized AD body.

---

## 5. Data models

### DynamoDB table: `airworthiness_directives`

| Attribute | Type | Notes |
|---|---|---|
| `ad_number` (PK) | String | e.g. `2024-12-05` |
| `version` (SK) | Number | Monotonic. 1 for initial publish, increment on correction/amendment. |
| `effective_date` | String (ISO) | |
| `publication_date` | String (ISO) | |
| `federal_register_id` | String | FR document number |
| `s3_raw_uri` | String | `s3://.../source.html` |
| `content_hash` | String | SHA-256 of normalized body |
| `supersedes` | StringSet | Other AD numbers |
| `superseded_by` | String | Null if currently effective |
| `applicability` | Map | See applicability schema |
| `compliance_times` | List<Map> | Action + deadline tuples |
| `status` | String | `effective` \| `superseded` \| `withdrawn` |
| `extraction_confidence` | Number | 0.0–1.0 from Bedrock pass |
| `last_updated_at` | String (ISO) | |

**GSIs:**
- `make-model-index` — PK `make#model`, SK `effective_date` — for "what ADs apply to a Cessna 172R?"
- `status-effective-index` — PK `status`, SK `effective_date` — for "what's currently effective?"

### Applicability schema (Map)
```json
{
  "aircraft": [
    {
      "make": "Cessna",
      "model": "172R",
      "serial_ranges": [{"from": "17280001", "to": "17281234"}],
      "year_range": {"from": 1996, "to": 2004}
    }
  ],
  "engines": [],
  "propellers": [],
  "appliances": [],
  "equipment_conditions": ["with Garmin GNS 430W installed"],
  "extraction_notes": "Serial range explicitly listed; equipment condition inferred from paragraph 3"
}
```

### S3 raw layout
```
s3://pivotallift-ad-raw/
  {ad-number}/
    v{version}/
      source.html
      source.pdf
      metadata.json   # FR API response snapshot
      extraction.json # Bedrock output (if applicable)
```

---

## 6. Implementation phases

### Phase 0 — scaffolding (1–2 days)
- [ ] Terraform/CDK module for the bucket, table, queue, two Lambdas, EventBridge schedule.
- [ ] SSM watermark parameter, initialized to a date 30 days back.
- [ ] CloudWatch dashboard: poll success rate, queue depth, DLQ depth, fetcher errors, S3 PutObject count.
- [ ] Alarm on DLQ depth > 0, alarm on poller success rate < 95% over 6h.

### Phase 1 — raw ingestion working end-to-end (3–5 days)
- [ ] Poller queries FR API, paginates, enqueues to SQS, updates watermark.
- [ ] Fetcher writes raw HTML + linked PDF + FR metadata to S3 with versioning.
- [ ] Minimal DynamoDB write: `ad_number`, `version`, `effective_date`, `s3_raw_uri`, `content_hash`, `status=effective`.
- [ ] **Acceptance:** run for 7 days, confirm every FAA AD published in that window is in S3 + DynamoDB with no DLQ messages.

### Phase 2 — structured extraction (3–5 days)
- [ ] Bedrock extraction step in fetcher (or separate Lambda triggered by DynamoDB stream).
- [ ] Populate `applicability`, `compliance_times`, `supersedes`.
- [ ] Cache by `content_hash` to avoid re-extracting unchanged documents.
- [ ] Track `extraction_confidence`; route < 0.7 to a manual-review queue (SQS + simple admin UI later).
- [ ] **Acceptance:** spot-check 20 random ADs against the source PDF; applicability fields correct on ≥ 18.

### Phase 3 — supersession resolution (2 days)
- [ ] Backfill `superseded_by` by walking `supersedes` arrays.
- [ ] Lambda triggered on DynamoDB stream updates the chain when a new AD lands.
- [ ] Mark older versions `status=superseded`.
- [ ] **Acceptance:** query "currently effective ADs for Cessna 172" returns no superseded entries.

### Phase 4 — search & query API (3 days)
- [ ] OpenSearch Serverless collection, index mapping for AD body + applicability fields.
- [ ] API Gateway + Lambda: `GET /ads?make=&model=&serial=&effective_after=`.
- [ ] Hybrid query: structured filter on DynamoDB GSI, full-text fallback on OpenSearch.

### Phase 5 — historical backfill (1 week, can run in background)
- [ ] One-shot script: walk FR API back N years; alternatively scrape DRS for ADs pre-dating FR coverage.
- [ ] Run during off-hours; rate-limit aggressively.

### Phase 6 — comparison against mx book (separate spec)
- Out of scope for this document. Inputs to that spec from this one:
  - DynamoDB query API by make/model/serial.
  - S3 URIs for citation back to source.
  - Confidence scores for ranking matches.

---

## 7. Non-obvious considerations

### Supersession is a graph, not a list
ADs reference and replace each other across years. Model `supersedes` and `superseded_by` explicitly. The "currently effective" AD for a given concern is the tail of the chain. Resolve at query time, not at ingest, because new ADs can supersede old ones in the future.

### Applicability parsing is where the project lives or dies
The matching logic is "does AD X apply to aircraft Y?" The AD body says things like *"Cessna 172R, serial numbers 17280001 through 17281234, equipped with Garmin GNS 430W."* Regex handles ~70%. The rest is prose. Use a Bedrock pass with Claude to produce structured output, validate against a JSON schema, and surface `extraction_confidence` to the UI. Never silently accept low-confidence extractions for safety-critical fields.

### Liability framing
Any output that says "you are in compliance" is a regulatory and legal claim. The system surfaces **candidate matches** with citations back to S3-stored source documents. The user (A&P, IA, owner) makes the compliance determination. Get this wording reviewed before any production UI.

### Mx book is the harder side
- If the mx book is structured (logbook export from ForeFlight, CAMP, etc.) — fine, parse the JSON/XML.
- If it's a scanned PDF — Textract + Bedrock entity extraction. Plan for human review on low-confidence aircraft identification (tail number, serial, engine SN).
- False negatives (missed AD applicability) are far worse than false positives. Bias toward over-flagging with confidence scores.

### Federal Register quirks
- Corrections are published as separate documents, not edits. Watch for "Correction" in the title and link them to the parent AD via `version`.
- The HTML and PDF can differ slightly. PDF is the legal artifact; HTML is for parsing. Store both.

### Cost notes
- DynamoDB on-demand is fine until volume justifies provisioned.
- OpenSearch Serverless has a minimum OCU floor — defer Phase 4 until you have something to search.
- Bedrock cost: cache by `content_hash`. Most ADs you process once forever.

---

## 8. Open questions

1. Is Object Lock Compliance mode acceptable, or does the team need Governance mode for operational flexibility?
2. How far back does the historical backfill need to go? Active ADs only, or full history including superseded?
3. Mx book input format(s) we need to support in Phase 6 — confirm before that spec is written.
4. Multi-tenant from day one, or single-tenant first? Affects table partition key design.
5. Notification channel for newly published ADs affecting a user's aircraft — email, in-app, both?

---

## 9. References

- Federal Register API: https://www.federalregister.gov/developers/api/v1
- FAA DRS: https://drs.faa.gov
- 14 CFR Part 39 (Airworthiness Directives): regulatory basis for ADs
- AWS Object Lock: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
