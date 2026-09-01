# Review packet: review-infrastructure

Stage: closure
Generated: 2026-08-23T01:12:22+00:00
Base: `HEAD`
Head: `9e45397d24fd1e9e2e988a7decf42941d346929c`
Scope fingerprint: `90f5234bca5843a73bcbbf7a7cf5a6158910c607b994e30a427d8e7d71b7a37b`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

# Decision packet: review-infrastructure

## Objective

Create durable Paprnav infrastructure for a Codex builder, an independent Codex
adversarial reviewer, and a Claude external critic.

## User-visible outcome

High-risk work enters review at design time, iterates by implementation slice,
and closes through an evidence-backed finding ledger.

## Safety and correctness invariants

- The builder cannot certify its own work.
- A design blocker prevents implementation from passing its gate.
- Claude output is independently validated rather than automatically accepted.
- Packets identify staged, unstaged, untracked, and explicitly excluded scope.
- Closure rejects unresolved blockers and unsupported dispositions.

## Current behavior

Claude receives a generic working-tree prompt late in implementation. Paprnav
has historical review documents but no repository agent policy or finding
ledger.

## Proposed design

Use root `AGENTS.md` for orchestration policy, a repository-local skill for the
reusable workflow, `.ai/agents` for role briefs, `.ai/review-runs` for durable
state, deterministic scripts for packet/ledger checks, and Claude Code CLI only
for external criticism.

## Alternatives considered

A bespoke multi-agent API service was rejected because Codex already provides
runtime subagents. Claude as primary reviewer was rejected because it lacks the
task's iterative decision context.

## Trust, authorization, and audit boundaries

The coordinator dispositions findings. Builder and reviewers supply evidence.
Claude runs read-only in plan mode. Local credentials and raw diagnostics stay
ignored.

## Read paths and consumers

Codex reads `AGENTS.md`, the local skill, role briefs, packets, and ledgers.
Humans read Markdown reports. Claude reads a mechanically generated packet and
direct repository files.

## Write paths and administrative paths

Run creation writes task templates. Packet assembly writes manifest and packet.
Validation reads run artifacts. Claude streaming writes review and diagnostics.

## Migration, compatibility, correction, and rollback

There is no database migration. Existing `.ai/reviews` remain historical. The
Claude command interface intentionally changes to require a task packet; repo
search found no automated caller. Rollback must revert the modified Claude
wrapper, environment example, and documentation together with the new
infrastructure to their pre-change Git versions.

## Test strategy

Run shell syntax checks, Python compilation, skill validation, review-run
creation, scoped packet generation, negative closure validation, and an
independent Codex adversarial review.

## Expected file scope

`AGENTS.md`, `.agents/skills/adversarial-review`, `.ai/agents`,
`.ai/review-templates`, `.ai/REVIEW_PROCESS.md`, `.ai/CLAUDE_REVIEWER.md`,
`.gitignore`, and the review scripts.

## Known uncertainty

Repository-local skill discovery may require a new Codex task before it appears
in the available-skill catalog. The system skill validator currently lacks its
PyYAML runtime dependency in this environment. Repository attestations cannot
authenticate Codex runtime identity; the coordinator must record the identity
returned by the actual subagent tool.


## Current finding ledger

```json
[
  {
    "id": "review-infrastructure-AR-001",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Builder and reviewer are distinct and mandatory design blockers prevent implementation closure.",
    "summary": "Independent design and implementation reviews were documented but not enforced.",
    "evidence": ["scripts/validate-review-run.py did not require review attestations", "the pilot had no design review artifact"],
    "impact": "A builder could certify its own work and bypass the early gate.",
    "requiredClosure": "Require fingerprinted review records with distinct identities and passed design and implementation stages.",
    "disposition": "Added reviews.json attestations, record-review.py, and stage enforcement.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: latest stage result is authoritative, failures roll phase back, and identities must be nonempty and distinct."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-002",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Review and closure cover the final working-tree state.",
    "summary": "Stale packets and post-review changes could pass closure.",
    "evidence": ["manifest head and generatedAt were only checked for presence", "Claude accepted an arbitrary packet path"],
    "impact": "Reviewed content could differ from content being closed.",
    "requiredClosure": "Fingerprint scoped file content and bind final review to the current fingerprint.",
    "disposition": "Added per-file hashes, scope fingerprint, artifact hashes, and final-state comparison.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: verifiers re-enumerate Git state and bind review to the current scope fingerprint."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-003",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "Packets disclose omissions and justify excluded dirty scope.",
    "summary": "Scope exclusions and unreadable or truncated files were silently accepted.",
    "evidence": ["outOfScopeDirtyFiles had no required reason", "unreadable text became empty and truncation was unmarked"],
    "impact": "Material changes could be absent without a review finding.",
    "requiredClosure": "Require exclusion rationale and record size, hash, read status, and truncation.",
    "disposition": "Packet generation now refuses unexplained exclusions and records content metadata.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: exclusions require rationale and omitted/truncated content carries size, hash, and status."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-004",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "high",
    "status": "closed",
    "invariant": "The finding ledger is complete, typed, and evidence-backed.",
    "summary": "The declared finding schema was not enforced.",
    "evidence": ["validator accepted missing IDs and required fields"],
    "impact": "Malformed or unsupported dispositions could satisfy closure.",
    "requiredClosure": "Enforce required fields, enums, evidence, owners, rationale, and revisit conditions.",
    "disposition": "Validator now enforces the ledger contract without an optional runtime dependency.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: ledger types, required fields, allowed properties, evidence, and dispositions are enforced."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-005",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Every Claude finding is reconciled into the authoritative ledger.",
    "summary": "Claude criticism was not connected to the ledger.",
    "evidence": ["Claude returned Markdown and closure ignored its finding IDs"],
    "impact": "A Claude blocker could be lost while the run closed.",
    "requiredClosure": "Reject closure when a Claude finding ID lacks a ledger entry.",
    "disposition": "Closure validation scans Claude artifacts and requires every stable ID in the ledger.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: Claude Markdown and diagnostics cannot escape the task directory and stable IDs must reconcile."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-006",
    "stage": "implementation",
    "reviewer": "codex-adversary-review_infrastructure_adversary",
    "severity": "medium",
    "status": "closed",
    "invariant": "Generated review controls do not contaminate implementation scope.",
    "summary": "Review-run artifacts recursively entered their own packets.",
    "evidence": ["the previous packet appeared as an untracked scoped file"],
    "impact": "Packets grew recursively and scope became nondeterministic.",
    "requiredClosure": "Exclude generated manifest, packet, and review records from implementation scope.",
    "disposition": "Generated control artifacts are now excluded and embedded only in dedicated sections.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Implementation adversary PASS: current-run controls are excluded from implementation inventory and embedded once."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-D-001",
    "stage": "design",
    "reviewer": "codex-adversary-review_infrastructure_design",
    "severity": "blocker",
    "status": "closed",
    "invariant": "A coordinating runtime assigns a reviewer distinct from the builder.",
    "summary": "Repository review identity strings could be mistaken for authenticated independence.",
    "evidence": ["record-review.py accepts coordinator-supplied identity strings"],
    "impact": "The local record could overstate the guarantee it provides.",
    "requiredClosure": "Define runtime assignment as the trust boundary and repository attestations as audit evidence.",
    "disposition": "Policy now states the boundary explicitly and requires the actual returned subagent identity.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Design adversary PASS: runtime assignment boundary and non-cryptographic audit semantics are explicit."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-D-002",
    "stage": "design",
    "reviewer": "codex-adversary-review_infrastructure_design",
    "severity": "blocker",
    "status": "closed",
    "invariant": "Final-state verification detects files added after packet generation.",
    "summary": "Fingerprint recomputation covered only paths already in the manifest.",
    "evidence": ["validate-review-run.py and verify-review-packet.py iterated manifest.files"],
    "impact": "New scoped or excluded changes could bypass the final review.",
    "requiredClosure": "Re-enumerate Git state and compare scoped and excluded inventories before review and closure.",
    "disposition": "Both verifiers now rebuild the inventory before hashing and compare excluded files.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Design adversary PASS: both verifiers re-enumerate scoped and excluded Git state."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-D-003",
    "stage": "design",
    "reviewer": "codex-adversary-review_infrastructure_design",
    "severity": "high",
    "status": "closed",
    "invariant": "Design review precedes implementation through monotonic phases.",
    "summary": "Gate ordering was documented but not represented or validated.",
    "evidence": ["reviews.json allowed retrospective unordered pass records"],
    "impact": "A team could backfill design approval after implementation.",
    "requiredClosure": "Add framed, design-reviewed, implementation, implementation-reviewed, and closed transitions.",
    "disposition": "Added state.json, transition scripts, and an explicit retrospective bootstrap exception for this pilot.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Design adversary PASS: monotonic phases exist and this pilot is explicitly retrospective."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-D-004",
    "stage": "design",
    "reviewer": "codex-adversary-review_infrastructure_design",
    "severity": "high",
    "status": "closed",
    "invariant": "The compatibility decision and rollback procedure are accurate.",
    "summary": "Deleting new files would not restore the modified Claude wrapper.",
    "evidence": ["claude-review.sh is an existing modified file with a breaking command interface"],
    "impact": "Existing callers could break and the stated rollback was incomplete.",
    "requiredClosure": "Inventory consumers and document the breaking cutover and complete Git rollback set.",
    "disposition": "Repository search found no automated caller; policy now documents the cutover and complete rollback set.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Design adversary PASS: operator example, cutover inventory, manifest, and rollback set align."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-CC-001",
    "stage": "external_critic",
    "reviewer": "claude-sonnet-5",
    "severity": "high",
    "status": "closed",
    "invariant": "Every run requires an independent closure-stage review of the final state.",
    "summary": "Bootstrap runs could validate without a closure-stage attestation.",
    "evidence": ["Claude review traced implementation review substitution and the weaker bootstrap phase check."],
    "impact": "A run could claim closure without its mandatory final review.",
    "requiredClosure": "Require a passed closure review and closed phase for every run.",
    "disposition": "Validator now requires distinct passed implementation and closure records and phase closed for all runs.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Codex implementation adversary PASS: distinct implementation and closure attestations plus closed phase are mandatory."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-CC-002",
    "stage": "external_critic",
    "reviewer": "claude-sonnet-5",
    "severity": "high",
    "status": "closed",
    "invariant": "Every phase transition is reproducible through audited tooling.",
    "summary": "Bootstrap phase progression had no script path and required manual state editing.",
    "evidence": ["Claude review found no writer for bootstrapException and no valid framed bootstrap transition."],
    "impact": "Legitimate and illegitimate manual phase assertions were indistinguishable.",
    "requiredClosure": "Add an explicit bootstrap transition requiring a passed design review and recorded reason.",
    "disposition": "advance-review-run.py now supports an explicit reasoned design_reviewed bootstrap transition after a design pass.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Codex implementation adversary PASS: explicit reasoned bootstrap transition requires the latest design result to pass."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-CC-003",
    "stage": "external_critic",
    "reviewer": "claude-sonnet-5",
    "severity": "high",
    "status": "closed",
    "invariant": "Following the documented workflow can produce a valid closed run.",
    "summary": "Documentation omitted the review-recording and phase-advance commands.",
    "evidence": ["Claude grep found no durable documentation references to either required script."],
    "impact": "A coordinator following the skill would create a permanently unclosable run.",
    "requiredClosure": "Document exact design, implementation, transition, and closure commands.",
    "disposition": "The process and skill now document all required commands and immutable artifact rules.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Codex implementation adversary PASS: packet, attestation, phase advance, implementation, and closure commands are documented."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-CC-004",
    "stage": "external_critic",
    "reviewer": "claude-sonnet-5",
    "severity": "high",
    "status": "closed",
    "invariant": "Every Claude finding is structurally validated and reconciled.",
    "summary": "Free-form Markdown regex matching could silently miss Claude findings.",
    "evidence": ["Claude demonstrated that non-H3 or differently formatted findings evade regex reconciliation."],
    "impact": "A formatting deviation could allow a real blocker to bypass the ledger.",
    "requiredClosure": "Require and validate a structured JSON finding artifact.",
    "disposition": "Claude must now emit a machine JSON block, the runner extracts a sidecar, and closure validates its structure and IDs.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Codex implementation adversary PASS: JSON sidecars are extracted, structured, validated, and reconciled; diagnostics are excluded."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-CC-005",
    "stage": "external_critic",
    "reviewer": "claude-sonnet-5",
    "severity": "medium",
    "status": "closed",
    "invariant": "The audit trail distinguishes failed and successful Claude runs accurately.",
    "summary": "A failed Claude artifact looked like a review and closure incorrectly said Claude was never invoked.",
    "evidence": ["The first Claude Markdown contained only ENOTFOUND while closure said Claude was not invoked."],
    "impact": "Future readers could misinterpret invocation history and review completeness.",
    "requiredClosure": "Rename failed outputs distinctly and correct the closure record.",
    "disposition": "Failed output is now an ignored .error.md artifact; future failures are renamed automatically; closure records both attempts.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": ["Codex implementation adversary PASS: failed and malformed Claude outputs become .error.md and closure records both attempts."],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-C-001",
    "stage": "closure",
    "reviewer": "codex-adversary-final_review_infrastructure_closure",
    "severity": "blocker",
    "status": "fixed_pending_verification",
    "invariant": "Only actual Claude runner output is required to have a structured Claude sidecar.",
    "summary": "A Codex implementation report beginning with claude- was misclassified as Claude output.",
    "evidence": ["validate-review-run.py globbed every claude-*.md and demanded a sidecar for claude-findings-implementation-closure.md."],
    "impact": "A valid run could not close after its mandatory closure attestation.",
    "requiredClosure": "Use the runner's explicit Claude external-critic artifact namespace.",
    "disposition": "Validator discovery is restricted to claude-external-critic-*.md, matching the runner's output contract.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": [],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-C-002",
    "stage": "closure",
    "reviewer": "codex-adversary-final_review_infrastructure_closure",
    "severity": "blocker",
    "status": "fixed_pending_verification",
    "invariant": "The Claude runner and validator share one authoritative artifact namespace.",
    "summary": "Validator discovery was narrower than the runner's allowed output names.",
    "evidence": ["Validator scanned claude-external-critic-*.md while the wrapper allowed any claude-*.md and the environment example omitted the required suffix."],
    "impact": "A documented successful Claude review could bypass sidecar and ledger reconciliation.",
    "requiredClosure": "Enforce the same exact timestamped or suffixed external-critic namespace in runner, validator, and examples.",
    "disposition": "Wrapper Markdown and diagnostic validation plus the environment example now require claude-external-critic-<suffix> names, matching validator discovery.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": [],
    "supersedes": []
  },
  {
    "id": "review-infrastructure-AR-C-003",
    "stage": "closure",
    "reviewer": "codex-adversary-final_review_infrastructure_closure",
    "severity": "blocker",
    "status": "fixed_pending_verification",
    "invariant": "Successful Claude output cannot use a filename suffix reserved for ignored failures or partial diagnostics.",
    "summary": "The main output regex allowed successful .error.md and .partial.md names that validation excludes.",
    "evidence": ["A custom claude-external-critic-manual.error.md satisfied the wrapper regex but was excluded by validator discovery."],
    "impact": "A successful custom Claude review could bypass sidecar and ledger reconciliation.",
    "requiredClosure": "Disallow dots and reserved compound suffixes in the configurable main-output suffix.",
    "disposition": "Main output suffix is now one alphanumeric followed only by alphanumeric, underscore, or hyphen before .md.",
    "owner": "paprnav-platform",
    "revisitCondition": null,
    "closureEvidence": [],
    "supersedes": []
  }
]

```

## Changed-file manifest

```json
{
  "taskId": "review-infrastructure",
  "stage": "closure",
  "generatedAt": "2026-08-23T01:12:22+00:00",
  "baseRef": "HEAD",
  "head": "9e45397d24fd1e9e2e988a7decf42941d346929c",
  "scopePaths": [
    "AGENTS.md",
    ".agents",
    ".ai/agents",
    ".ai/review-templates",
    ".ai/REVIEW_PROCESS.md",
    ".ai/CLAUDE_REVIEWER.md",
    ".gitignore",
    "scripts/create-review-run.sh",
    "scripts/build-review-packet.py",
    "scripts/advance-review-run.py",
    "scripts/record-review.py",
    "scripts/validate-review-run.py",
    "scripts/verify-review-packet.py",
    "scripts/extract-claude-findings.py",
    "scripts/claude-review.sh",
    "scripts/claude-review.env.example"
  ],
  "scopeFingerprint": "90f5234bca5843a73bcbbf7a7cf5a6158910c607b994e30a427d8e7d71b7a37b",
  "files": [
    {
      "path": ".agents/skills/adversarial-review/SKILL.md",
      "status": "??",
      "size": 3111,
      "sha256": "f3d22abdadd7dcf24ac4bd152327257910bc84bf111ed73984a286a3af472048",
      "readStatus": "readable"
    },
    {
      "path": ".agents/skills/adversarial-review/agents/openai.yaml",
      "status": "??",
      "size": 226,
      "sha256": "533cb157d2a047af6d630ad3b1018ee5a0fe64d70fc60ae4ef0b097932f4568a",
      "readStatus": "readable"
    },
    {
      "path": ".agents/skills/adversarial-review/references/checklists.md",
      "status": "??",
      "size": 1201,
      "sha256": "9d541c157c9a603e7c5e08b70a5af1b6b63d38d61eee0e820970cb0cdd964d2c",
      "readStatus": "readable"
    },
    {
      "path": ".agents/skills/adversarial-review/references/severity.md",
      "status": "??",
      "size": 815,
      "sha256": "2aa99b4cbfa276b425022c0d4b03d17d47ba5d3a682f3ae5770b98a6b6290ff3",
      "readStatus": "readable"
    },
    {
      "path": ".ai/CLAUDE_REVIEWER.md",
      "status": " M",
      "size": 1396,
      "sha256": "88e81861a8be90991ad4f02604ccd9bd4a26a341701da623522bbfd83325c7ee",
      "readStatus": "readable"
    },
    {
      "path": ".ai/REVIEW_PROCESS.md",
      "status": "??",
      "size": 5101,
      "sha256": "f9e7b5875fa3eeb9ea7211a0709fc575ee5c8ae1d3a563fa5ac3ce5e893b73c2",
      "readStatus": "readable"
    },
    {
      "path": ".ai/agents/ADVERSARIAL_REVIEWER.md",
      "status": "??",
      "size": 1184,
      "sha256": "2af95ada3305a879630f8abb2938c46c5afeb95ac60b68f9c21c6bb44c583ffc",
      "readStatus": "readable"
    },
    {
      "path": ".ai/agents/BUILDER.md",
      "status": "??",
      "size": 798,
      "sha256": "fa050074b25531049c148b883f612d96401184ee1a4a6ee0a40ffb32272d9fe8",
      "readStatus": "readable"
    },
    {
      "path": ".ai/agents/CLAUDE_CRITIC.md",
      "status": "??",
      "size": 689,
      "sha256": "4cdd97dc7f3a6f9150d07420bc4b18ef22eafc9ab8ec78a137a9ad086f8a1c42",
      "readStatus": "readable"
    },
    {
      "path": ".ai/agents/COORDINATOR.md",
      "status": "??",
      "size": 641,
      "sha256": "187f4bf574aab3097e37d361bcc2eb88d60bee5ea6f9e9f8e6eb52a5e3e05af2",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-templates/CLOSURE_REPORT.md",
      "status": "??",
      "size": 205,
      "sha256": "424db2c94c845505141b080d221940e552e2474dfd5d8627ef6312978177e7d3",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-templates/DECISION_PACKET.md",
      "status": "??",
      "size": 413,
      "sha256": "35cac3ae79315c642a6fa21731cf934087ebf9199d79d298479bd2ec92821677",
      "readStatus": "readable"
    },
    {
      "path": ".ai/review-templates/FINDINGS.json.schema",
      "status": "??",
      "size": 1354,
      "sha256": "f45ba4ae03d3a0b9592c16e29da271f6c9800899dc0d54f09c25fb3d61d4f033",
      "readStatus": "readable"
    },
    {
      "path": ".gitignore",
      "status": " M",
      "size": 613,
      "sha256": "9dd1e108e1665a824dbd044595bef0d3c86c4342b3c97e91d0d8da23e2b4f096",
      "readStatus": "readable"
    },
    {
      "path": "AGENTS.md",
      "status": "??",
      "size": 1768,
      "sha256": "1bd67ae08070dac1b0235b9a8eac37f361ec29a670740538d135286b37c6b5b5",
      "readStatus": "readable"
    },
    {
      "path": "scripts/advance-review-run.py",
      "status": "??",
      "size": 1499,
      "sha256": "79812e2775c508d85471b71df624ceb0df77bd533e393f8457079c4e44c6c301",
      "readStatus": "readable"
    },
    {
      "path": "scripts/build-review-packet.py",
      "status": "??",
      "size": 6611,
      "sha256": "e3c250fc3e7caba48b8c380f66b4d0281123c78703312726f6d340e046771394",
      "readStatus": "readable"
    },
    {
      "path": "scripts/claude-review.env.example",
      "status": " M",
      "size": 1310,
      "sha256": "78485086320ace6cab94d505f3838f1c46f9f3fcec171517caa022fee9f00532",
      "readStatus": "readable"
    },
    {
      "path": "scripts/claude-review.sh",
      "status": " M",
      "size": 7418,
      "sha256": "31cd1c57e58f9f76830f08ca16ee023950cc456c196518387c296a942931a883",
      "readStatus": "readable"
    },
    {
      "path": "scripts/create-review-run.sh",
      "status": "??",
      "size": 1056,
      "sha256": "bdf8cd4f27538c050bb23f3dd1589da44e71e182d7decf574ffa32012175b631",
      "readStatus": "readable"
    },
    {
      "path": "scripts/extract-claude-findings.py",
      "status": "??",
      "size": 895,
      "sha256": "496aee7459e5bd25c2227379fac6ebfbd79628ef9861e3cd59ad3efeebe01707",
      "readStatus": "readable"
    },
    {
      "path": "scripts/record-review.py",
      "status": "??",
      "size": 3817,
      "sha256": "e6e71ea75efd76e09b5d1459604927a0fea321ba472ff922cbe92c2c4f921e18",
      "readStatus": "readable"
    },
    {
      "path": "scripts/validate-review-run.py",
      "status": "??",
      "size": 13262,
      "sha256": "0140dd027181d292b28d58effb72329db13ef499773205200f2d775d19697ca8",
      "readStatus": "readable"
    },
    {
      "path": "scripts/verify-review-packet.py",
      "status": "??",
      "size": 3517,
      "sha256": "85628d0df430addcee5c67cb4cd5cc1ebfb39c4488c4dff8838de81fa87a7a14",
      "readStatus": "readable"
    }
  ],
  "outOfScopeDirtyFiles": [
    {
      "path": ".ai/AD_APPLICABILITY_SCHEMA_REVIEW.md",
      "status": "A "
    },
    {
      "path": ".ai/AD_SOURCE_PROOF_2026-08-04.md",
      "status": "M "
    },
    {
      "path": ".ai/API_CONTRACT.md",
      "status": "M "
    },
    {
      "path": ".ai/DATA_MODEL.md",
      "status": "M "
    },
    {
      "path": ".ai/GOAL_TASKS.md",
      "status": "M "
    },
    {
      "path": ".ai/LOCAL_MVP_DEMO.md",
      "status": "M "
    },
    {
      "path": ".ai/PROVIDER_REFERENCES.md",
      "status": "M "
    },
    {
      "path": ".ai/ad-calibration/1998-17-11.requirements.json",
      "status": "A "
    },
    {
      "path": ".ai/ad-calibration/2002-13-04.requirements.json",
      "status": "A "
    },
    {
      "path": ".ai/ad-calibration/2008-26-10.requirements.json",
      "status": "A "
    },
    {
      "path": ".ai/ad-calibration/2011-10-09.requirements.json",
      "status": "A "
    },
    {
      "path": ".ai/ad-calibration/2024-14-03.requirements.json",
      "status": "A "
    },
    {
      "path": ".ai/ad-calibration/README.md",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-remediation-closure-20260822.md",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-reviewer-calibration-20260822.md",
      "status": "A "
    },
    {
      "path": ".ai/reviews/claude-t081-schema-data-20260822.md",
      "status": "A "
    },
    {
      "path": "backend/README.md",
      "status": "M "
    },
    {
      "path": "backend/app/api/routes/ads.py",
      "status": "M "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0021_add_ad_applicability_v3.py",
      "status": "A "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0022_harden_ad_review_materialization.py",
      "status": "A "
    },
    {
      "path": "backend/app/db/migrations/versions/20260822_0023_backfill_ad_v3_amoc_envelope.py",
      "status": "A "
    },
    {
      "path": "backend/app/models/core.py",
      "status": "M "
    },
    {
      "path": "backend/app/schemas/ads.py",
      "status": "M "
    },
    {
      "path": "backend/app/scripts/audit_ad_review_evidence.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/correct_approved_ad_review.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/prepare_ad_compliance_reviews.py",
      "status": "A "
    },
    {
      "path": "backend/app/scripts/seed_dev.py",
      "status": "M "
    },
    {
      "path": "backend/app/scripts/stage_ad_review_proposal.py",
      "status": "A "
    },
    {
      "path": "backend/app/services/ad_applicability.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_compliance_population.py",
      "status": "A "
    },
    {
      "path": "backend/app/services/ad_extraction.py",
      "status": "M "
    },
    {
      "path": "backend/app/services/ad_recurrence.py",
      "status": "M "
    },
    {
      "path": "backend/docker-compose.yml",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_ingestion.py",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_matching.py",
      "status": "M "
    },
    {
      "path": "backend/tests/test_ad_recurrence.py",
      "status": "M "
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/page.tsx",
      "status": "M "
    },
    {
      "path": "frontend/paprnav-frontend/src/app/(authenticated)/logbook/ads/reviews/page.tsx",
      "status": "A "
    },
    {
      "path": "frontend/paprnav-frontend/src/lib/api.ts",
      "status": "M "
    }
  ],
  "outOfScopeReason": "Pre-existing AD applicability work and historical review artifacts are unrelated to the review-infrastructure task."
}
```

## Diff against base

```diff
diff --git a/.ai/CLAUDE_REVIEWER.md b/.ai/CLAUDE_REVIEWER.md
index ab8d2bf..eb7a9e2 100644
--- a/.ai/CLAUDE_REVIEWER.md
+++ b/.ai/CLAUDE_REVIEWER.md
@@ -1,79 +1,32 @@
-# Claude Code Reviewer
+# Claude external critic
 
-Side-fork conclusion:
+Claude is an independent critic inside the Codex-led adversarial review process.
+It is not the primary reviewer, decision owner, or closure authority. Read
+`.ai/REVIEW_PROCESS.md` for the complete workflow.
 
-- Claude Code is installed and authenticated in the user's interactive terminal.
-- `antigravity` is not on `PATH`.
-- Claude's valid permission modes include `plan`.
-- Codex can see the `claude` executable, but this execution context does not share the user's Claude login.
+## Infrastructure
 
-Current auth state in Codex:
+- `scripts/build-review-packet.py` mechanically assembles scope and context.
+- `scripts/claude-review.sh` invokes Claude Code in read-only plan mode.
+- `scripts/claude-review-stream.py` preserves streamed output and diagnostics.
+- `.ai/review-runs/<task-id>/` stores the decision, manifest, ledger, review,
+  and closure artifacts.
+- `.env.claude-review` optionally bridges an API key into ignored local state.
 
-- `claude -p` from Codex returns `Not logged in`.
-- `claude doctor` from Codex reports Claude Code `2.1.206` and notes that macOS Keychain is not writable in this execution context.
-
-Operational decision:
-
-- The reviewer automation is `scripts/claude-review.sh`.
-- The script can be run by Codex when Claude auth is available in this process.
-- If Codex lacks Claude login, the script supports an ignored `.env.claude-review` bridge that sets `ANTHROPIC_API_KEY` for Claude `--bare` mode.
-- Review output is written to `.ai/reviews/` so findings can be brought back into the main Codex thread for triage.
-- The script uses Claude `--permission-mode plan` and asks Claude not to edit files.
-- The script defaults `CLAUDE_REVIEW_MODEL=sonnet`. Use Sonnet for normal high-stakes review; choose a higher model only when the work is unusually critical, ambiguous, or architecture-heavy.
-- The wrapper uses Claude's `stream-json` output so model/session/status events and
-  final-text deltas remain visible during long reviews.
-- Each run preserves final Markdown, raw JSONL events, a Claude debug log, and
-  partial text. An interrupted run is not reported as successful and retains
-  enough diagnostics to distinguish interruption from authentication or API
-  failure.
-
-When to use Claude:
-
-- Use Claude after Codex has looped or self-reviewed at least twice on high-stakes work.
-- Use Claude for complex or critical logic, security decisions, privacy/data-retention decisions, AWS/IAM/Terraform changes, cost/billing decisions, migrations, and other changes where a missed issue could be expensive or unsafe.
-- Do not one-shot critical app portions. Implement, self-review, verify, revise if needed, then run Claude review.
-- Do not run Claude for low-level tasks with clear existing patterns unless those tasks touch one of the high-stakes areas above.
-- Treat Claude output as review input, not automatic truth. Codex triages findings into fix-now, document/accept-risk, or defer with rationale.
-
-Run:
-
-```bash
-scripts/claude-review.sh
-```
-
-Optional model override:
+## Run
 
 ```bash
-CLAUDE_REVIEW_MODEL=opus scripts/claude-review.sh
+scripts/create-review-run.sh T123
+python3 scripts/build-review-packet.py --task T123 --base HEAD --stage external-critic
+scripts/claude-review.sh --task T123 --stage external-critic --base HEAD
 ```
 
-Target a critical slice, including untracked files:
-
-```bash
-CLAUDE_REVIEW_FOCUS="OCR metering and AD matching correctness" \
-CLAUDE_REVIEW_PATHS="backend/app/services/ocr_provider.py backend/app/services/ad_matching.py" \
-scripts/claude-review.sh HEAD
-```
+The wrapper refuses to run without a review packet, manifest, and finding
+ledger. Claude must inspect direct repository context, state scope limitations,
+and return stable finding IDs. Codex validates and dispositions every finding.
 
-Optional base ref:
+Use Sonnet by default. Override `CLAUDE_REVIEW_MODEL` only for unusually
+critical or architecture-heavy work. Raw events, debug logs, and partial output
+remain ignored; interrupted runs are not successful reviews.
 
-```bash
-scripts/claude-review.sh origin/main
-scripts/claude-review.sh HEAD
-```
-
-After it finishes, paste the findings or point Codex at the generated `.ai/reviews/claude-review-*.md` file.
-
-Codex-auth bridge:
-
-```bash
-cp scripts/claude-review.env.example .env.claude-review
-chmod 600 .env.claude-review
-$EDITOR .env.claude-review
-```
-
-Set `ANTHROPIC_API_KEY` in that ignored local file. Do not paste the value into chat and do not commit it. Once present, Codex can run:
-
-```bash
-scripts/claude-review.sh
-```
+Do not paste credentials into chat or commit `.env.claude-review`.
diff --git a/.gitignore b/.gitignore
index 6cf54dc..d5eeb36 100644
--- a/.gitignore
+++ b/.gitignore
@@ -25,6 +25,11 @@ backend/.data/
 .ai/reviews/*.events.jsonl
 .ai/reviews/*.partial.md
 .ai/reviews/latest
+.ai/review-runs/*/*.debug.log
+.ai/review-runs/*/*.events.jsonl
+.ai/review-runs/*/*.partial.md
+.ai/review-runs/*/review-packet.sha256
+.ai/review-runs/*/*.error.md
 
 # Terraform local state and provider cache
 .terraform/
diff --git a/scripts/claude-review.env.example b/scripts/claude-review.env.example
index 78d92c7..1130de4 100644
--- a/scripts/claude-review.env.example
+++ b/scripts/claude-review.env.example
@@ -14,13 +14,13 @@ ANTHROPIC_API_KEY=
 # only when a task is unusually critical, ambiguous, or architecture-heavy.
 CLAUDE_REVIEW_MODEL=sonnet
 
-# Optional targeted-review controls.
-# CLAUDE_REVIEW_FOCUS=OCR metering and AD matching correctness
-# CLAUDE_REVIEW_PATHS=backend/app/services/ocr_provider.py backend/app/services/ad_matching.py
+# Target scope when generating the packet, not through environment variables:
+#   python3 scripts/build-review-packet.py --task T123 --base HEAD \
+#     --stage external-critic --path backend/app/services/ocr_provider.py
 
 # Optional artifact overrides. By default these are derived from the Markdown
 # review path and preserve raw events, debug diagnostics, and interrupted text.
-# CLAUDE_REVIEW_OUTPUT=.ai/reviews/claude-review.md
-# CLAUDE_REVIEW_EVENTS=.ai/reviews/claude-review.events.jsonl
-# CLAUDE_REVIEW_DEBUG=.ai/reviews/claude-review.debug.log
-# CLAUDE_REVIEW_PARTIAL=.ai/reviews/claude-review.partial.md
+# CLAUDE_REVIEW_OUTPUT=.ai/review-runs/T123/claude-external-critic-manual.md
+# CLAUDE_REVIEW_EVENTS=.ai/review-runs/T123/claude-external-critic-manual.events.jsonl
+# CLAUDE_REVIEW_DEBUG=.ai/review-runs/T123/claude-external-critic-manual.debug.log
+# CLAUDE_REVIEW_PARTIAL=.ai/review-runs/T123/claude-external-critic-manual.partial.md
diff --git a/scripts/claude-review.sh b/scripts/claude-review.sh
index 004ef24..f3b262d 100755
--- a/scripts/claude-review.sh
+++ b/scripts/claude-review.sh
@@ -6,6 +6,29 @@ if ! command -v claude >/dev/null 2>&1; then
   exit 127
 fi
 
+task_id=""
+review_stage="external-critic"
+base_ref="HEAD"
+packet_path=""
+while [[ $# -gt 0 ]]; do
+  case "$1" in
+    --task) task_id="${2:-}"; shift 2 ;;
+    --stage) review_stage="${2:-}"; shift 2 ;;
+    --base) base_ref="${2:-}"; shift 2 ;;
+    --packet) packet_path="${2:-}"; shift 2 ;;
+    -h|--help)
+      echo "usage: $0 --task <task-id> [--stage <stage>] [--base <ref>] [--packet <path>]"
+      exit 0
+      ;;
+    *) echo "unknown argument: $1" >&2; exit 2 ;;
+  esac
+done
+
+if [[ -z "$task_id" || ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
+  echo "--task with a safe task id is required" >&2
+  exit 2
+fi
+
 repo_root="$(git rev-parse --show-toplevel)"
 cd "$repo_root"
 
@@ -17,21 +40,53 @@ if [[ -f "$env_file" ]]; then
   set +a
 fi
 
-base_ref="${1:-origin/main}"
 if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
-  base_ref="HEAD"
+  echo "base ref does not exist: $base_ref" >&2
+  exit 2
+fi
+
+run_dir=".ai/review-runs/${task_id}"
+if [[ -z "$packet_path" ]]; then
+  packet_path="${run_dir}/review-packet.md"
+fi
+if [[ ! -f "$packet_path" ]]; then
+  echo "review packet does not exist: $packet_path" >&2
+  echo "run: python3 scripts/build-review-packet.py --task $task_id --base $base_ref --stage $review_stage" >&2
+  exit 2
+fi
+if [[ ! -f "${run_dir}/manifest.json" || ! -f "${run_dir}/findings.json" ]]; then
+  echo "review run lacks manifest or finding ledger: $run_dir" >&2
+  exit 2
 fi
 
-mkdir -p .ai/reviews
+python3 scripts/verify-review-packet.py \
+  --task "$task_id" \
+  --stage "$review_stage" \
+  --base "$base_ref" \
+  --packet "$packet_path"
+
+mkdir -p "$run_dir"
 timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
-output_path="${CLAUDE_REVIEW_OUTPUT:-.ai/reviews/claude-review-${timestamp}.md}"
+output_path="${CLAUDE_REVIEW_OUTPUT:-${run_dir}/claude-${review_stage}-${timestamp}.md}"
+output_dir="${output_path%/*}"
+output_name="${output_path##*/}"
+if [[ "$output_dir" != "$run_dir" || ! "$output_name" =~ ^claude-external-critic-[A-Za-z0-9][A-Za-z0-9_-]*\.md$ ]]; then
+  echo "Claude review output must be claude-external-critic-<suffix>.md inside $run_dir" >&2
+  exit 2
+fi
 review_model="${CLAUDE_REVIEW_MODEL:-sonnet}"
-review_focus="${CLAUDE_REVIEW_FOCUS:-High-stakes changes in the current working tree.}"
-review_paths="${CLAUDE_REVIEW_PATHS:-All changed and untracked files relevant to the review focus.}"
 artifact_stem="${output_path%.md}"
 events_path="${CLAUDE_REVIEW_EVENTS:-${artifact_stem}.events.jsonl}"
 debug_path="${CLAUDE_REVIEW_DEBUG:-${artifact_stem}.debug.log}"
 partial_path="${CLAUDE_REVIEW_PARTIAL:-${artifact_stem}.partial.md}"
+for artifact_path in "$events_path" "$debug_path" "$partial_path"; do
+  artifact_dir="${artifact_path%/*}"
+  artifact_name="${artifact_path##*/}"
+  if [[ "$artifact_dir" != "$run_dir" || ! "$artifact_name" =~ ^claude-external-critic-[A-Za-z0-9._-]+\.(events\.jsonl|debug\.log|partial\.md)$ ]]; then
+    echo "Claude diagnostic artifacts must stay inside $run_dir" >&2
+    exit 2
+  fi
+done
 
 claude_args=(
   --print
@@ -49,15 +104,17 @@ if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
 fi
 
 prompt="$(cat <<PROMPT
-You are reviewing the paprnav repository as an external code reviewer.
+You are the independent Claude critic for paprnav review run ${task_id}, stage
+${review_stage}. Read the complete packet at ${packet_path} before reviewing.
 
 Review scope:
 - Current working tree in: ${repo_root}
 - Compare against base ref: ${base_ref}
 - Include staged and unstaged changes.
-- Review focus: ${review_focus}
-- Focus paths: ${review_paths}
+- Treat the packet manifest as a starting point, not a scope boundary.
 - Read listed untracked files directly; they do not appear in ordinary git diff output.
+- Search for affected callers, readers, migrations, jobs, administrative scripts,
+  tests, contracts, and documentation omitted from the manifest.
 - Do not edit files.
 - Do not run destructive commands.
 
@@ -67,6 +124,10 @@ Review stance:
 - Do not spend review attention on low-level patterned edits unless they create one of the risks above.
 - Ground each finding in file paths and line numbers when possible.
 - Separate confirmed issues from questions or speculative risks.
+- Do not repeat closed ledger findings unless their closure evidence is inadequate.
+- Give each finding a stable ID prefixed ${task_id}-CC-.
+- Format every finding heading exactly as: ### ${task_id}-CC-NNN — short title
+- For each finding state the violated invariant, evidence, impact, and required closure.
 - Keep summary brief and secondary.
 
 Useful context:
@@ -82,14 +143,36 @@ Suggested commands if needed:
 - cd frontend/paprnav-frontend && npm run lint
 
 Return Markdown with sections:
-1. Findings
-2. Open Questions
-3. Verification Notes
-4. Brief Summary
+1. Scope Limitations
+2. Findings
+3. Open Questions
+4. Verification Notes
+5. Brief Summary
+
+After Scope Limitations and before prose Findings, emit this required machine
+block. Populate one object per finding, or use an empty array. Do not wrap it in
+any additional fence or omit any field:
+
+<!-- CLAUDE_FINDINGS_JSON -->
+```json
+[
+  {
+    "id": "${task_id}-CC-001",
+    "severity": "high",
+    "invariant": "...",
+    "summary": "...",
+    "evidence": ["path:line and fact"],
+    "impact": "...",
+    "requiredClosure": "..."
+  }
+]
+```
 PROMPT
 )"
 
 echo "Running Claude review against ${base_ref}..."
+echo "Review run ${task_id}, stage ${review_stage}"
+echo "Reading packet from ${packet_path}"
 echo "Writing review to ${output_path}"
 echo "Streaming events to ${events_path}"
 echo "Writing diagnostics to ${debug_path}"
@@ -100,6 +183,9 @@ if ! claude "${claude_args[@]}" "$prompt" |
     --output "$output_path" \
     --events "$events_path" \
     --partial "$partial_path"; then
+  if [[ -f "$output_path" ]]; then
+    mv "$output_path" "${artifact_stem}.error.md"
+  fi
   cat >&2 <<'ERR'
 
 Claude review failed.
@@ -120,6 +206,13 @@ ERR
   exit 1
 fi
 
+if ! python3 scripts/extract-claude-findings.py \
+  --review "$output_path" \
+  --output "${artifact_stem}.findings.json"; then
+  mv "$output_path" "${artifact_stem}.error.md"
+  exit 1
+fi
+
 echo
 echo "Claude review saved to ${output_path}"
 echo "Claude event stream saved to ${events_path}"

```

## Untracked text files

### `.agents/skills/adversarial-review/SKILL.md`

size=3111; sha256=f3d22abdadd7dcf24ac4bd152327257910bc84bf111ed73984a286a3af472048; truncated=false

```text
---
name: adversarial-review
description: Run an independent, staged engineering review from design through closure. Use for safety- or regulatory-critical logic, schemas and migrations, authorization, audit evidence, correction/backfill/destructive data paths, IAM/infrastructure, billing/provider decisions, public contracts, or when the user asks for an adversarial reviewer, builder-reviewer separation, review packet, finding ledger, or Claude critic.
---

# Adversarial review

Read `.ai/REVIEW_PROCESS.md` and the role brief relevant to the assigned role.
Keep builder, adversary, and coordinator responsibilities separate.

## Start a review run

Run `scripts/create-review-run.sh <task-id>`. Have the builder complete
`decision.md` before editing high-risk code. Record safety and correctness
invariants as falsifiable statements.

## Review the design

Spawn a separate Codex subagent with `.ai/agents/ADVERSARIAL_REVIEWER.md`, the
decision packet, and repository access. Require a read-only review. Add findings
to `findings.json`; resolve blockers before implementation.

Record the result with `scripts/record-review.py --stage design`, using the
actual runtime reviewer identity and a new immutable report path. Then run
`scripts/advance-review-run.py --to implementation`.
Generate a current design packet with `scripts/build-review-packet.py --stage
design` immediately before recording the review.

Read `references/checklists.md` for schema, safety, authorization, migration,
and evidence review. Read `references/severity.md` when classifying or closing
findings.

## Review implementation slices

Implement one coherent vertical slice at a time. Generate the review packet:

```bash
python3 scripts/build-review-packet.py --task <task-id> --base <git-ref>
```

Give a separate adversary the packet and direct repository access. Require it
to inspect untracked files and surrounding consumers, not only the diff. The
reviewer reports findings; the builder fixes them; the reviewer verifies them.
Record the passed implementation review with `scripts/record-review.py --stage
implementation` and a new immutable artifact path.

## Use Claude as an external critic

Use Claude only after the Codex adversarial loop has a complete packet. Run:

```bash
scripts/claude-review.sh --task <task-id> --stage external-critic --base <git-ref>
```

Treat Claude output as untrusted review input. Validate every finding in Codex
and record its disposition. Use targeted closure reviews instead of repeatedly
submitting the entire working tree.

The runner requires a structured `*.findings.json` sidecar extracted from the
model's machine block. Every candidate ID must enter the ledger.

## Close

Complete `closure.md`, then run:

```bash
python3 scripts/validate-review-run.py --task <task-id>
```

Before validation, use a separate Codex closure reviewer and record its pass
with `scripts/record-review.py --stage closure` and a new immutable artifact.

Do not close with an open blocker, an accepted risk without owner/rationale, a
closed finding without evidence, or an unexplained scope omission.

```
### `.agents/skills/adversarial-review/agents/openai.yaml`

size=226; sha256=533cb157d2a047af6d630ad3b1018ee5a0fe64d70fc60ae4ef0b097932f4568a; truncated=false

```text
interface:
  display_name: "Adversarial Review"
  short_description: "Gate high-risk changes through independent review"
  default_prompt: "Use $adversarial-review to review this high-risk change from design through closure."

```
### `.agents/skills/adversarial-review/references/checklists.md`

size=1201; sha256=9d541c157c9a603e7c5e08b70a5af1b6b63d38d61eee0e820970cb0cdd964d2c; truncated=false

```text
# Review checklists

## End-to-end trace

- Source and provenance
- Parsing or ingestion
- Validation and rejection behavior
- Human decision and authorization
- Persistence and transaction boundary
- Derived state, jobs, and caches
- API and UI exposure
- Correction, supersession, and revocation
- Audit attribution and retention

## Schema and migration

- Authoritative versus derived representation
- Source-faithful versus normalized values
- Null, uniqueness, ordering, and concurrency semantics
- Upgrade, downgrade, legacy rows, and mixed-version operation
- Idempotency, retries, partial failure, and stale rows
- Backfill and administrative scripts

## Safety and evidence

- Every critical value is bound to source evidence
- Uncertainty fails closed
- Negative cases cannot become positive decisions
- Publication is gated on every read and write path
- Calibration records exercise the failure mode the schema addresses

## Verification

- Positive, negative, boundary, and replay tests
- All callers/readers of changed symbols inspected
- Staged, unstaged, and untracked scope included
- Contracts and documentation match behavior
- Rollback does not invent or silently discard meaning

```
### `.agents/skills/adversarial-review/references/severity.md`

size=815; sha256=2aa99b4cbfa276b425022c0d4b03d17d47ba5d3a682f3ae5770b98a6b6290ff3; truncated=false

```text
# Finding severity and closure

- **Blocker:** can cause unsafe or unauthorized behavior, incorrect regulatory
  state, data loss/corruption, an invalid migration, or makes the claimed review
  impossible. Must close before the gate passes.
- **High:** material correctness, security, privacy, audit, availability, or
  operability defect. Fix or explicitly accept with an accountable owner.
- **Medium:** meaningful gap with bounded impact or missing regression proof.
- **Low:** localized robustness, maintainability, or clarity issue.

A finding is `closed` only after an independent reviewer checks the fix and its
verification evidence. `rejected_finding` requires evidence disproving the
claim. `accepted_risk` requires owner and rationale. Deferral does not reduce
severity and cannot bypass a blocker gate.

```
### `.ai/REVIEW_PROCESS.md`

size=5101; sha256=f9e7b5875fa3eeb9ea7211a0709fc575ee5c8ae1d3a563fa5ac3ce5e893b73c2; truncated=false

```text
# Adversarial engineering review

## Roles

- **Coordinator:** owns scope, gates, finding dispositions, and final closure.
- **Builder:** prepares the decision packet, implements a bounded slice, and
  supplies verification evidence.
- **Codex adversary:** independently attempts to disprove the design and the
  implementation. It does not edit during a review pass.
- **Claude critic:** supplies independent-model criticism from a mechanically
  assembled packet. It does not decide whether a finding is valid or closed.

Role briefs live in `.ai/agents/`. Runtime agents are ephemeral Codex subagents;
the briefs, ledger, and review packets are the durable infrastructure.

Reviewer independence is enforced by the coordinating Codex runtime assigning a
separate subagent. `reviews.json` is an auditable record of that assignment, not
cryptographic proof: anyone able to rewrite the repository can also rewrite its
validator. The coordinator records the actual returned runtime identity.

## Mandatory gates

### 1. Frame

Create `.ai/review-runs/<task-id>/decision.md`. State the problem, invariants,
alternatives, design, affected reads and writes, migration/rollback behavior,
test strategy, and uncertainty.

### 2. Design adversary

Before implementation, give a separate Codex agent the decision packet and
repository access. Record design findings in `findings.json`. Resolve blockers
before changing a migration, public contract, or safety-critical behavior.

Record the result using a new immutable artifact path, then advance:

```bash
python3 scripts/build-review-packet.py --task T123 --base HEAD --stage design
python3 scripts/record-review.py --task T123 --stage design \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-design-final.md
python3 scripts/advance-review-run.py --task T123 --to implementation
```

### 3. Implement by vertical slice

Advance the run from `design_reviewed` to `implementation` before editing.
Keep schema/validation, persistence, publication, derived state, calibration,
and UI slices independently reviewable where practical. The builder records
changed scope, deviations from design, and verification results.

### 4. Implementation adversary

The adversary traces each invariant through source, validation, persistence,
all consumers, correction/supersession, authorization, and tests. It inspects
the actual working tree rather than relying on a selected diff.

Record a passed implementation review before closure:

```bash
python3 scripts/record-review.py --task T123 --stage implementation \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-implementation-final.md
```

### 5. External critic

Generate a review packet with `scripts/build-review-packet.py`. Invoke Claude
only when independent-model disagreement is valuable. Triage its findings in
Codex; never accept or reject them automatically.

### 6. Closure

Re-review fixes, attach verification evidence, and produce `closure.md`.
Completion requires no open blocker, no unexplained scope omission, and a final
review of the resulting working tree.

The final independent reviewer records the mandatory closure stage:

```bash
python3 scripts/record-review.py --task T123 --stage closure \
  --reviewer <runtime-agent-id> --builder <builder-id> --outcome pass \
  --artifact .ai/review-runs/T123/adversarial-closure-final.md
python3 scripts/validate-review-run.py --task T123
```

For the one-time infrastructure bootstrap only, reconstruct the unavailable
early transition after a recorded design pass:

```bash
python3 scripts/advance-review-run.py --task review-infrastructure \
  --to design_reviewed --bootstrap-reason "review tooling bootstrap"
python3 scripts/advance-review-run.py --task review-infrastructure --to implementation
```

## Finding states

`open`, `fix_in_progress`, `fixed_pending_verification`, `closed`,
`accepted_risk`, `rejected_finding`, and `deferred`.

Accepted risk requires an owner and rationale. Closed and rejected findings
require evidence. Deferred blockers do not permit closure.

## Review-run layout

```text
.ai/review-runs/<task-id>/
├── decision.md
├── manifest.json
├── findings.json
├── adversarial-design.md
├── adversarial-implementation.md
├── claude-packet.md
├── claude-critic.md
└── closure.md
```

Raw Claude event streams and debug logs are local diagnostics and should remain
ignored. Human-readable reviews, ledgers, and closure evidence may be committed.

## Compatibility and rollback

The packet requirement is an intentional breaking cutover for
`scripts/claude-review.sh`. Repository search found no automated caller; the
tracked consumer was `.ai/CLAUDE_REVIEWER.md`, updated with the wrapper. Rollback
requires reverting `scripts/claude-review.sh`,
`scripts/claude-review.env.example`, `.ai/CLAUDE_REVIEWER.md`, and the new review
infrastructure together to their pre-change Git versions. Deleting only new
files is not a complete rollback.

```
### `.ai/agents/ADVERSARIAL_REVIEWER.md`

size=1184; sha256=2af95ada3305a879630f8abb2938c46c5afeb95ac60b68f9c21c6bb44c583ffc; truncated=false

```text
# Adversarial reviewer role

Attempt to disprove that the proposed change is safe, complete, internally
consistent, and adequately tested. Review read-only.

For design review, independently restate invariants and trace:

`source -> ingestion -> validation -> human decision -> persistence -> derived state -> API/UI exposure -> correction/supersession -> audit history`

Challenge lossy normalization, missing actors, alternate write paths, nullable
uniqueness, concurrency, idempotency, partial failure, stale derived state,
migration compatibility, rollback, premature publication, and unrepresentative
calibration data.

For implementation review, inspect staged, unstaged, and untracked files. Search
for callers and readers of changed symbols. Map every invariant to code, negative
tests, migration behavior, API behavior, and documentation. Run safe targeted
checks and construct counterexamples.

Lead with findings ordered by severity. Separate confirmed defects, missing
proof, design questions, and accepted limitations. Each finding must state the
violated invariant, evidence, impact, and required closure. A missing file or
unverifiable scope claim is itself a finding.

```
### `.ai/agents/BUILDER.md`

size=798; sha256=fa050074b25531049c148b883f612d96401184ee1a4a6ee0a40ffb32272d9fe8; truncated=false

```text
# Builder role

Before editing, complete the decision packet with:

- problem and user-visible outcome;
- safety and correctness invariants;
- current behavior and authoritative data representation;
- alternatives and why they were rejected;
- trust, authorization, and audit boundaries;
- affected read paths, write paths, jobs, and administrative scripts;
- migration, compatibility, rollback, correction, and supersession behavior;
- negative and positive test strategy;
- uncertainty and expected file scope.

After design approval, implement one coherent vertical slice. Report changed
files, deviations from the accepted design, tests run, failures, and newly found
consumers. Resolve accepted findings but do not mark them closed; closure belongs
to an independent reviewer and coordinator.

```
### `.ai/agents/CLAUDE_CRITIC.md`

size=689; sha256=4cdd97dc7f3a6f9150d07420bc4b18ef22eafc9ab8ec78a137a9ad086f8a1c42; truncated=false

```text
# Claude external critic role

Provide independent-model criticism, not project authority. Review the supplied
decision record, manifest, current ledger, diff, untracked scope, consumers, and
tests. Inspect repository files directly when the packet identifies them.

Seek defects missed by the Codex builder/adversary loop. Do not repeat closed
findings unless their closure evidence is inadequate. State scope limitations
first. Do not edit files.

Return findings ordered by severity with a stable ID, violated invariant,
evidence, impact, and required closure, followed by questions and concise
verification notes. The coordinating Codex agent will validate and disposition
the output.

```
### `.ai/agents/COORDINATOR.md`

size=641; sha256=187f4bf574aab3097e37d361bcc2eb88d60bee5ea6f9e9f8e6eb52a5e3e05af2; truncated=false

```text
# Coordinator role

Own the review run, not the implementation opinion.

1. Decide whether the change triggers adversarial review.
2. Create the run and assign distinct builder and reviewer roles.
3. Enforce design, slice, external-critic, and closure gates.
4. Validate every finding against repository evidence.
5. Assign dispositions and prevent closure with open blockers.
6. Preserve a complete scope manifest and final verification record.

Do not ask the builder to certify its own closure. Do not treat Claude output as
truth. When reviewer and builder disagree, resolve the disputed invariant with
code, contract, or test evidence.

```
### `.ai/review-templates/CLOSURE_REPORT.md`

size=205; sha256=424db2c94c845505141b080d221940e552e2474dfd5d8627ef6312978177e7d3; truncated=false

```text
# Closure report: {{TASK_ID}}

## Outcome

## Invariants verified

## Findings disposition summary

## Verification performed

## Final scope reviewed

## Accepted risks and deferred work

## Not verified

```
### `.ai/review-templates/DECISION_PACKET.md`

size=413; sha256=35cac3ae79315c642a6fa21731cf934087ebf9199d79d298479bd2ec92821677; truncated=false

```text
# Decision packet: {{TASK_ID}}

## Objective

## User-visible outcome

## Safety and correctness invariants

## Current behavior

## Proposed design

## Alternatives considered

## Trust, authorization, and audit boundaries

## Read paths and consumers

## Write paths and administrative paths

## Migration, compatibility, correction, and rollback

## Test strategy

## Expected file scope

## Known uncertainty

```
### `.ai/review-templates/FINDINGS.json.schema`

size=1354; sha256=f45ba4ae03d3a0b9592c16e29da271f6c9800899dc0d54f09c25fb3d61d4f033; truncated=false

```text
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "stage", "reviewer", "severity", "status", "invariant", "summary", "evidence", "impact", "requiredClosure", "closureEvidence"],
    "properties": {
      "id": {"type": "string", "minLength": 1},
      "stage": {"enum": ["design", "implementation", "external_critic", "closure"]},
      "reviewer": {"type": "string", "minLength": 1},
      "severity": {"enum": ["blocker", "high", "medium", "low"]},
      "status": {"enum": ["open", "fix_in_progress", "fixed_pending_verification", "closed", "accepted_risk", "rejected_finding", "deferred"]},
      "invariant": {"type": "string", "minLength": 1},
      "summary": {"type": "string", "minLength": 1},
      "evidence": {"type": "array", "minItems": 1, "items": {"type": ["string", "object"]}},
      "impact": {"type": "string", "minLength": 1},
      "requiredClosure": {"type": "string", "minLength": 1},
      "disposition": {"type": ["string", "null"]},
      "owner": {"type": ["string", "null"]},
      "revisitCondition": {"type": ["string", "null"]},
      "closureEvidence": {"type": "array", "items": {"type": "string", "minLength": 1}},
      "supersedes": {"type": "array", "items": {"type": "string"}}
    },
    "additionalProperties": false
  }
}

```
### `AGENTS.md`

size=1768; sha256=1bd67ae08070dac1b0235b9a8eac37f361ec29a670740538d135286b37c6b5b5; truncated=false

```text
# Paprnav agent workflow

Use the adversarial review process for changes involving regulatory or safety
semantics, schemas or migrations, authorization, audit evidence, destructive
data operations, provider/billing decisions, infrastructure/IAM, or public API
contracts. Read `.ai/REVIEW_PROCESS.md` and use the repository-local
`adversarial-review` skill.

For qualifying work:

1. Create a review run and write the decision packet before implementation.
2. Use a separate Codex subagent for design review. The builder may not review
   its own work.
3. Resolve design blockers before migrations, contracts, or implementation.
4. Implement one coherent vertical slice at a time.
5. Use a separate Codex subagent to adversarially review every high-risk slice.
6. Use Claude only as an external critic at selected decision boundaries, after
   the Codex adversarial loop has produced a complete review packet.
7. Record every finding and disposition. Do not declare completion while a
   blocker remains open or closure evidence is absent.

The coordinating Codex runtime must create the reviewer assignment and record
the returned reviewer identity; repository scripts cannot authenticate runtime
identity and are not a security boundary. The adversarial reviewer is read-only
unless the coordinator explicitly assigns a later fix task. Reviewers must
inspect staged, unstaged, and untracked files,
plus callers, readers, migrations, administrative scripts, tests, and relevant
contracts. A scope omission is a review finding, not an implicit exclusion.

Claude output is review input rather than authority. The coordinating Codex
agent validates and dispositions each finding as fixed, rejected with evidence,
accepted risk with an owner, or deferred with rationale.

```
### `scripts/advance-review-run.py`

size=1499; sha256=79812e2775c508d85471b71df624ceb0df77bd533e393f8457079c4e44c6c301; truncated=false

```text
#!/usr/bin/env python3
"""Advance a review run through its monotonic implementation phase."""

import argparse
import json
import pathlib
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True)
parser.add_argument("--to", required=True, choices=("design_reviewed", "implementation"))
parser.add_argument("--bootstrap-reason")
args = parser.parse_args()
repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
run_dir = repo / ".ai" / "review-runs" / args.task
state_path = run_dir / "state.json"
state = json.loads(state_path.read_text())
reviews = json.loads((run_dir / "reviews.json").read_text())
design_reviews = [review for review in reviews if review.get("stage") == "design"]
design_passed = bool(design_reviews) and design_reviews[-1].get("outcome") == "pass"
if not design_passed:
    raise SystemExit("passed design attestation is missing")
if args.to == "design_reviewed":
    if state.get("phase") != "framed" or not args.bootstrap_reason:
        raise SystemExit("bootstrap transition requires framed phase and --bootstrap-reason")
    state["bootstrapException"] = args.bootstrap_reason
    state["phase"] = "design_reviewed"
else:
    if state.get("phase") != "design_reviewed":
        raise SystemExit("run must have passed design review before implementation")
    state["phase"] = "implementation"
state_path.write_text(json.dumps(state, indent=2) + "\n")

```
### `scripts/build-review-packet.py`

size=6611; sha256=e3c250fc3e7caba48b8c380f66b4d0281123c78703312726f6d340e046771394; truncated=false

```text
#!/usr/bin/env python3
"""Build a deterministic review packet from Git state and review artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess


def git(repo: pathlib.Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def task_id(value: str) -> str:
    if not value or any(not (char.isalnum() or char in "._-") for char in value):
        raise argparse.ArgumentTypeError("invalid task id")
    return value


def changed_files(repo: pathlib.Path, base: str) -> list[dict[str, str]]:
    entries: dict[str, str] = {}
    for line in git(repo, "diff", "--name-status", base, "--").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            entries[fields[-1]] = fields[0]
    for line in git(repo, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if len(line) >= 4:
            path = line[3:].split(" -> ", 1)[-1]
            entries[path] = line[:2]
    return [{"path": path, "status": entries[path]} for path in sorted(entries)]


def in_scope(path: str, scopes: list[str]) -> bool:
    return not scopes or any(path == scope or path.startswith(scope.rstrip("/") + "/") for scope in scopes)


def metadata(repo: pathlib.Path, item: dict[str, str]) -> dict[str, object]:
    result: dict[str, object] = dict(item)
    path = repo / item["path"]
    if not path.is_file():
        return {**result, "size": 0, "sha256": None, "readStatus": "absent"}
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return {**result, "size": None, "sha256": None, "readStatus": f"read_error:{type(exc).__name__}"}
    return {**result, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "readStatus": "readable"}


def scope_fingerprint(head: str, files: list[dict[str, object]]) -> str:
    encoded = json.dumps({"head": head, "files": files}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def read_utf8(path: pathlib.Path) -> tuple[str, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return "", "binary_or_non_utf8"
    except OSError as exc:
        return "", f"read_error:{type(exc).__name__}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, type=task_id)
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--stage", default="implementation")
    parser.add_argument("--path", action="append", default=[], dest="paths")
    parser.add_argument("--out-of-scope-reason")
    args = parser.parse_args()

    repo = pathlib.Path(git(pathlib.Path.cwd(), "rev-parse", "--show-toplevel").strip())
    if not git(repo, "rev-parse", "--verify", "--quiet", args.base, check=False).strip():
        raise SystemExit(f"base ref does not exist: {args.base}")
    run_dir = repo / ".ai" / "review-runs" / args.task
    decision, findings = run_dir / "decision.md", run_dir / "findings.json"
    if not decision.is_file() or not findings.is_file():
        raise SystemExit(f"review run is incomplete: {run_dir}")

    all_files = changed_files(repo, args.base)
    implementation_candidates = [
        item for item in all_files
        if not item["path"].startswith(f".ai/review-runs/{args.task}/")
    ]
    scoped = [
        item for item in implementation_candidates
        if in_scope(item["path"], args.paths)
    ]
    out_of_scope = [item for item in implementation_candidates if item not in scoped]
    if out_of_scope and not args.out_of_scope_reason:
        raise SystemExit("dirty files exist outside scope; provide --out-of-scope-reason")
    files = [metadata(repo, item) for item in scoped]
    unreadable = [item for item in files if str(item["readStatus"]).startswith("read_error")]
    if unreadable:
        raise SystemExit(f"cannot read scoped files: {[item['path'] for item in unreadable]}")

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    head = git(repo, "rev-parse", "HEAD").strip()
    manifest = {
        "taskId": args.task,
        "stage": args.stage,
        "generatedAt": generated_at,
        "baseRef": args.base,
        "head": head,
        "scopePaths": args.paths,
        "scopeFingerprint": scope_fingerprint(head, files),
        "files": files,
        "outOfScopeDirtyFiles": out_of_scope,
        "outOfScopeReason": args.out_of_scope_reason,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    untracked: list[str] = []
    for item in files:
        if item["status"] != "??":
            continue
        relative = pathlib.Path(str(item["path"]))
        text, error = read_utf8(repo / relative)
        if error:
            untracked.append(f"### `{relative}`\n\nContent omitted: `{error}`; size={item['size']}; sha256={item['sha256']}.")
            continue
        truncated = len(text) > 200_000
        untracked.append(
            f"### `{relative}`\n\nsize={item['size']}; sha256={item['sha256']}; "
            f"truncated={str(truncated).lower()}\n\n```text\n{text[:200_000]}\n```"
        )

    decision_text, _ = read_utf8(decision)
    findings_text, _ = read_utf8(findings)
    diff_args = ["diff", args.base, "--", *args.paths] if args.paths else ["diff", args.base, "--"]
    packet = f"""# Review packet: {args.task}

Stage: {args.stage}
Generated: {generated_at}
Base: `{args.base}`
Head: `{head}`
Scope fingerprint: `{manifest['scopeFingerprint']}`

## Reviewer instructions

Read `.ai/agents/ADVERSARIAL_REVIEWER.md`. Inspect repository files directly.
Treat the manifest as a starting point and report missing consumers or unjustified
scope exclusions as findings.

## Decision packet

{decision_text}

## Current finding ledger

```json
{findings_text}
```

## Changed-file manifest

```json
{json.dumps(manifest, indent=2)}
```

## Diff against base

```diff
{git(repo, *diff_args)}
```

## Untracked text files

{chr(10).join(untracked) if untracked else 'None.'}
"""
    packet_path = run_dir / "review-packet.md"
    packet_path.write_text(packet)
    (run_dir / "review-packet.sha256").write_text(hashlib.sha256(packet.encode()).hexdigest() + "\n")
    print(packet_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `scripts/create-review-run.sh`

size=1056; sha256=bdf8cd4f27538c050bb23f3dd1589da44e71e182d7decf574ffa32012175b631; truncated=false

```text
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <task-id>" >&2
  exit 2
fi

task_id="$1"
if [[ ! "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "task-id must contain only letters, numbers, dot, underscore, or hyphen" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
run_dir="$repo_root/.ai/review-runs/$task_id"
if [[ -e "$run_dir" ]]; then
  echo "review run already exists: $run_dir" >&2
  exit 1
fi

mkdir -p "$run_dir"
sed "s/{{TASK_ID}}/$task_id/g" "$repo_root/.ai/review-templates/DECISION_PACKET.md" > "$run_dir/decision.md"
sed "s/{{TASK_ID}}/$task_id/g" "$repo_root/.ai/review-templates/CLOSURE_REPORT.md" > "$run_dir/closure.md"
printf '[]\n' > "$run_dir/findings.json"
printf '[]\n' > "$run_dir/reviews.json"
printf '{\n  "phase": "framed",\n  "bootstrapException": null\n}\n' > "$run_dir/state.json"
printf '{\n  "taskId": "%s",\n  "generatedAt": null,\n  "baseRef": null,\n  "head": null,\n  "files": []\n}\n' "$task_id" > "$run_dir/manifest.json"

echo "created review run: $run_dir"

```
### `scripts/extract-claude-findings.py`

size=895; sha256=496aee7459e5bd25c2227379fac6ebfbd79628ef9861e3cd59ad3efeebe01707; truncated=false

```text
#!/usr/bin/env python3
"""Extract the required structured Claude finding block from a review."""

import argparse
import json
import pathlib
import re

parser = argparse.ArgumentParser()
parser.add_argument("--review", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()
text = pathlib.Path(args.review).read_text(encoding="utf-8")
match = re.search(r"<!-- CLAUDE_FINDINGS_JSON -->\s*```json\s*(\[.*?\])\s*```", text, re.DOTALL)
if not match:
    raise SystemExit("Claude review lacks CLAUDE_FINDINGS_JSON block")
try:
    findings = json.loads(match.group(1))
except json.JSONDecodeError as exc:
    raise SystemExit(f"invalid Claude findings JSON: {exc}") from exc
if not isinstance(findings, list):
    raise SystemExit("Claude findings JSON must be an array")
pathlib.Path(args.output).write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")

```
### `scripts/record-review.py`

size=3817; sha256=e6e71ea75efd76e09b5d1459604927a0fea321ba472ff922cbe92c2c4f921e18; truncated=false

```text
#!/usr/bin/env python3
"""Record a review attestation against the current packet fingerprint."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--stage", required=True, choices=("design", "implementation", "closure"))
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--builder", required=True)
    parser.add_argument("--outcome", required=True, choices=("pass", "fail"))
    parser.add_argument("--artifact", required=True)
    args = parser.parse_args()
    if not args.reviewer.strip() or not args.builder.strip() or args.reviewer == args.builder:
        raise SystemExit("nonempty reviewer and builder identities must be distinct")
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    manifest = json.loads((run_dir / "manifest.json").read_text())
    if not all(manifest.get(key) for key in ("baseRef", "head", "scopeFingerprint")):
        raise SystemExit("generate a current review packet before recording a review")
    artifact = (repo / args.artifact).resolve()
    if repo not in artifact.parents or not artifact.is_file():
        raise SystemExit("artifact must be an existing repository file")
    reviews_path = run_dir / "reviews.json"
    reviews = json.loads(reviews_path.read_text())
    artifact_relative = str(artifact.relative_to(repo))
    if any(review.get("artifact") == artifact_relative for review in reviews):
        raise SystemExit("review artifacts are immutable; use a new artifact path")
    state_path = run_dir / "state.json"
    state = json.loads(state_path.read_text())
    phase = state.get("phase")
    if args.stage == "design" and phase != "framed" and not state.get("bootstrapException"):
        raise SystemExit("design review is only valid in the framed phase")
    if args.stage == "implementation" and phase != "implementation":
        raise SystemExit("implementation review requires the implementation phase")
    if args.stage == "closure" and phase != "implementation_reviewed":
        raise SystemExit("closure review requires a passed implementation review")
    reviews.append({
        "stage": args.stage,
        "reviewer": args.reviewer,
        "builder": args.builder,
        "outcome": args.outcome,
        "reviewedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "baseRef": manifest["baseRef"],
        "head": manifest["head"],
        "scopeFingerprint": manifest["scopeFingerprint"],
        "artifact": artifact_relative,
        "artifactSha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    })
    reviews_path.write_text(json.dumps(reviews, indent=2) + "\n")
    if args.outcome == "pass":
        if args.stage == "design" and not state.get("bootstrapException"):
            state["phase"] = "design_reviewed"
        elif args.stage == "implementation":
            state["phase"] = "implementation_reviewed"
        elif args.stage == "closure":
            state["phase"] = "closed"
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    else:
        if args.stage == "design" and not state.get("bootstrapException"):
            state["phase"] = "framed"
        elif args.stage == "implementation":
            state["phase"] = "implementation"
        elif args.stage == "closure":
            state["phase"] = "implementation_reviewed"
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `scripts/validate-review-run.py`

size=13262; sha256=0140dd027181d292b28d58effb72329db13ef499773205200f2d775d19697ca8; truncated=false

```text
#!/usr/bin/env python3
"""Validate evidence and final-state gates for a review run."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess


STATUSES = {"open", "fix_in_progress", "fixed_pending_verification", "closed", "accepted_risk", "rejected_finding", "deferred"}
TERMINAL = {"closed", "accepted_risk", "rejected_finding", "deferred"}
SEVERITIES = {"blocker", "high", "medium", "low"}
STAGES = {"design", "implementation", "external_critic", "closure"}
REQUIRED = {"id", "stage", "reviewer", "severity", "status", "invariant", "summary", "evidence", "impact", "requiredClosure", "closureEvidence"}
ALLOWED = REQUIRED | {"disposition", "owner", "revisitCondition", "supersedes"}


def sections_have_content(text: str, headings: list[str]) -> list[str]:
    missing: list[str] = []
    lines = text.splitlines()
    for heading in headings:
        try:
            start = lines.index(f"## {heading}") + 1
        except ValueError:
            missing.append(heading)
            continue
        content = []
        for line in lines[start:]:
            if line.startswith("## "):
                break
            if line.strip():
                content.append(line)
        if not content:
            missing.append(heading)
    return missing


def changed_inventory(repo: pathlib.Path, base: str, task: str, scopes: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    entries: dict[str, str] = {}
    diff = subprocess.run(["git", "diff", "--name-status", base, "--"], cwd=repo, text=True, capture_output=True, check=True).stdout
    for line in diff.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            entries[fields[-1]] = fields[0]
    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo, text=True, capture_output=True, check=True).stdout
    for line in status.splitlines():
        if len(line) >= 4:
            entries[line[3:].split(" -> ", 1)[-1]] = line[:2]
    candidates = [{"path": path, "status": value} for path, value in sorted(entries.items()) if not path.startswith(f".ai/review-runs/{task}/")]
    inside = [item for item in candidates if not scopes or any(item["path"] == scope or item["path"].startswith(scope.rstrip("/") + "/") for scope in scopes)]
    return inside, [item for item in candidates if item not in inside]


def current_fingerprint(repo: pathlib.Path, manifest: dict[str, object], task: str) -> tuple[str, list[dict[str, str]]]:
    inventory, outside = changed_inventory(repo, str(manifest["baseRef"]), task, list(manifest.get("scopePaths", [])))
    prior_by_path = {str(item["path"]): item for item in manifest.get("files", [])}
    current: list[dict[str, object]] = []
    for inventory_item in inventory:
        item = dict(prior_by_path.get(inventory_item["path"], inventory_item))
        item.update(inventory_item)
        path = repo / str(item["path"])
        if path.is_file():
            payload = path.read_bytes()
            item.update(size=len(payload), sha256=hashlib.sha256(payload).hexdigest(), readStatus="readable")
        else:
            item.update(size=0, sha256=None, readStatus="absent")
        current.append(item)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
    encoded = json.dumps({"head": head, "files": current}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), outside


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    args = parser.parse_args()
    if not args.task or any(not (char.isalnum() or char in "._-") for char in args.task):
        raise SystemExit("invalid task id")
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    errors: list[str] = []
    required_files = ("decision.md", "findings.json", "manifest.json", "reviews.json", "state.json", "closure.md")
    for name in required_files:
        if not (run_dir / name).is_file():
            errors.append(f"missing {name}")
    if errors:
        print("\n".join(errors))
        return 1
    try:
        findings = json.loads((run_dir / "findings.json").read_text())
        manifest = json.loads((run_dir / "manifest.json").read_text())
        reviews = json.loads((run_dir / "reviews.json").read_text())
        state = json.loads((run_dir / "state.json").read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"invalid review data: {exc}")
        return 1
    if not isinstance(findings, list):
        errors.append("findings.json must contain an array")
        findings = []
    if not isinstance(reviews, list):
        errors.append("reviews.json must contain an array")
        reviews = []

    seen: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            errors.append(f"finding[{index}] must be an object")
            continue
        missing = REQUIRED - finding.keys()
        label = finding.get("id") or f"finding[{index}]"
        if missing:
            errors.append(f"{label} lacks required fields: {sorted(missing)}")
        extras = finding.keys() - ALLOWED
        if extras:
            errors.append(f"{label} has unsupported fields: {sorted(extras)}")
        if not isinstance(finding.get("id"), str) or not finding.get("id", "").strip() or label in seen:
            errors.append(f"missing or duplicate finding id: {label}")
        seen.add(str(label))
        if finding.get("stage") not in STAGES or finding.get("severity") not in SEVERITIES or finding.get("status") not in STATUSES:
            errors.append(f"{label} has invalid stage, severity, or status")
        for field in ("reviewer", "invariant", "summary", "impact", "requiredClosure"):
            if not isinstance(finding.get(field), str) or not finding.get(field).strip():
                errors.append(f"{label} has empty {field}")
        if not isinstance(finding.get("evidence"), list) or not finding.get("evidence") or any(not isinstance(item, (str, dict)) or (isinstance(item, str) and not item.strip()) for item in finding.get("evidence", [])):
            errors.append(f"{label} lacks evidence")
        if not isinstance(finding.get("closureEvidence"), list) or any(not isinstance(item, str) or not item.strip() for item in finding.get("closureEvidence", [])):
            errors.append(f"{label} has invalid closure evidence")
        if "supersedes" in finding and (not isinstance(finding["supersedes"], list) or any(not isinstance(item, str) for item in finding["supersedes"])):
            errors.append(f"{label} has invalid supersedes")
        for field in ("disposition", "owner", "revisitCondition"):
            if field in finding and finding[field] is not None and not isinstance(finding[field], str):
                errors.append(f"{label} has invalid {field}")
        status = finding.get("status")
        if status not in TERMINAL:
            errors.append(f"{label} is not dispositioned: {status}")
        if finding.get("severity") == "blocker" and status == "deferred":
            errors.append(f"{label} is a deferred blocker")
        if status in {"closed", "rejected_finding"} and not finding.get("closureEvidence"):
            errors.append(f"{label} lacks closure evidence")
        if status in {"accepted_risk", "deferred"} and not all(finding.get(key) for key in ("owner", "disposition", "revisitCondition")):
            errors.append(f"{label} {status} lacks owner, rationale, or revisit condition")

    if not manifest.get("generatedAt") or not manifest.get("baseRef") or not manifest.get("scopeFingerprint"):
        errors.append("manifest has not been generated with a fingerprint")
    if manifest.get("outOfScopeDirtyFiles") and not manifest.get("outOfScopeReason"):
        errors.append("out-of-scope dirty files lack a reason")
    current, current_outside = current_fingerprint(repo, manifest, args.task)
    if manifest.get("scopeFingerprint") != current:
        errors.append("working tree changed after packet generation")
    if current_outside != manifest.get("outOfScopeDirtyFiles"):
        errors.append("dirty out-of-scope inventory changed after packet generation")

    latest_by_stage: dict[str, dict[str, object]] = {}
    review_required = {"stage", "reviewer", "builder", "outcome", "reviewedAt", "baseRef", "head", "scopeFingerprint", "artifact", "artifactSha256"}
    for index, review in enumerate(reviews):
        if not isinstance(review, dict) or review_required - review.keys():
            errors.append(f"review[{index}] is malformed")
            continue
        if any(not isinstance(review.get(field), str) or not review.get(field, "").strip() for field in review_required):
            errors.append(f"review[{index}] has empty or non-string fields")
            continue
        if review["stage"] not in {"design", "implementation", "closure"} or review["outcome"] not in {"pass", "fail"}:
            errors.append(f"review[{index}] has invalid stage or outcome")
            continue
        latest_by_stage[str(review["stage"])] = review
        if review["reviewer"] == review["builder"]:
            errors.append(f"{review['stage']} reviewer is the builder")
        artifact = repo / str(review["artifact"])
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != review["artifactSha256"]:
            errors.append(f"review artifact missing or changed: {review['artifact']}")
    design_review = latest_by_stage.get("design")
    implementation_review = latest_by_stage.get("implementation")
    closure_review = latest_by_stage.get("closure")
    if not design_review or design_review.get("outcome") != "pass":
        errors.append("no passed independent design review")
    if not implementation_review or implementation_review.get("outcome") != "pass":
        errors.append("no passed independent implementation review")
    if not closure_review or closure_review.get("outcome") != "pass":
        errors.append("no passed independent closure review")
    if closure_review and closure_review.get("scopeFingerprint") != manifest.get("scopeFingerprint"):
        errors.append("final implementation review does not cover current scope fingerprint")
    if state.get("phase") != "closed":
        errors.append(f"review phase is not closed: {state.get('phase')}")

    ledger_ids = {str(item.get("id")) for item in findings if isinstance(item, dict)}
    successful_claude = [
        path for path in run_dir.glob("claude-external-critic-*.md")
        if not path.name.endswith((".error.md", ".partial.md"))
    ]
    for claude_path in successful_claude:
        sidecar = claude_path.with_suffix(".findings.json")
        if not sidecar.is_file():
            errors.append(f"Claude review lacks structured findings: {claude_path.name}")
            continue
        try:
            candidates = json.loads(sidecar.read_text())
        except json.JSONDecodeError:
            errors.append(f"Claude findings are invalid JSON: {sidecar.name}")
            continue
        if not isinstance(candidates, list):
            errors.append(f"Claude findings must be an array: {sidecar.name}")
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("id"), str):
                errors.append(f"Claude finding is malformed in {sidecar.name}")
                continue
            candidate_id = candidate["id"]
            required_candidate = {"id", "severity", "invariant", "summary", "evidence", "impact", "requiredClosure"}
            if required_candidate - candidate.keys() or candidate.get("severity") not in SEVERITIES or not isinstance(candidate.get("evidence"), list) or not candidate.get("evidence"):
                errors.append(f"Claude finding is structurally invalid: {candidate_id}")
            if not re.fullmatch(rf"{re.escape(args.task)}-CC-\d+", candidate_id):
                errors.append(f"Claude finding has invalid ID: {candidate_id}")
            if candidate_id not in ledger_ids:
                errors.append(f"Claude finding is not dispositioned in ledger: {candidate_id}")

    decision = (run_dir / "decision.md").read_text()
    closure = (run_dir / "closure.md").read_text()
    for section in sections_have_content(decision, ["Objective", "Safety and correctness invariants", "Proposed design", "Test strategy"]):
        errors.append(f"decision section is empty: {section}")
    for section in sections_have_content(closure, ["Outcome", "Invariants verified", "Verification performed", "Final scope reviewed", "Not verified"]):
        errors.append(f"closure section is empty: {section}")
    if errors:
        print("review run is not closable:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"review run is closable: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
### `scripts/verify-review-packet.py`

size=3517; sha256=85628d0df430addcee5c67cb4cd5cc1ebfb39c4488c4dff8838de81fa87a7a14; truncated=false

```text
#!/usr/bin/env python3
"""Reject stale or mismatched packets before external review."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--packet", required=True)
    args = parser.parse_args()
    repo = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=True).stdout.strip())
    run_dir = repo / ".ai" / "review-runs" / args.task
    manifest = json.loads((run_dir / "manifest.json").read_text())
    packet = (repo / args.packet).resolve()
    expected_hash = (run_dir / "review-packet.sha256").read_text().strip()
    errors = []
    if manifest.get("taskId") != args.task or manifest.get("stage") != args.stage or manifest.get("baseRef") != args.base:
        errors.append("task, stage, or base does not match manifest")
    if not packet.is_file() or hashlib.sha256(packet.read_bytes()).hexdigest() != expected_hash:
        errors.append("packet is missing or changed")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
    entries = {}
    diff = subprocess.run(["git", "diff", "--name-status", str(manifest["baseRef"]), "--"], cwd=repo, text=True, capture_output=True, check=True).stdout
    for line in diff.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            entries[fields[-1]] = fields[0]
    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo, text=True, capture_output=True, check=True).stdout
    for line in status.splitlines():
        if len(line) >= 4:
            entries[line[3:].split(" -> ", 1)[-1]] = line[:2]
    scopes = list(manifest.get("scopePaths", []))
    candidates = [{"path": path, "status": value} for path, value in sorted(entries.items()) if not path.startswith(f".ai/review-runs/{args.task}/")]
    inventory = [item for item in candidates if not scopes or any(item["path"] == scope or item["path"].startswith(scope.rstrip("/") + "/") for scope in scopes)]
    outside = [item for item in candidates if item not in inventory]
    if outside != manifest.get("outOfScopeDirtyFiles"):
        errors.append("dirty out-of-scope inventory changed after packet generation")
    prior_by_path = {str(item["path"]): item for item in manifest.get("files", [])}
    files = []
    for inventory_item in inventory:
        item = dict(prior_by_path.get(inventory_item["path"], inventory_item))
        item.update(inventory_item)
        path = repo / str(item["path"])
        if path.is_file():
            payload = path.read_bytes()
            item.update(size=len(payload), sha256=hashlib.sha256(payload).hexdigest(), readStatus="readable")
        else:
            item.update(size=0, sha256=None, readStatus="absent")
        files.append(item)
    encoded = json.dumps({"head": head, "files": files}, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != manifest.get("scopeFingerprint"):
        errors.append("working tree changed after packet generation")
    if errors:
        raise SystemExit("; ".join(errors))
    print("review packet is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```
