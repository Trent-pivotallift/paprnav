Now I have full evidence to write the review.

---

# Review: review-infrastructure (external-critic stage)

## 1. Scope Limitations

- Reviewed all files listed in the packet manifest directly, plus consumers not in the manifest: `scripts/claude-review-stream.py` (unmodified, pre-existing consumer of `claude-review.sh`), and the actual `.ai/review-runs/review-infrastructure/*` artifacts produced by this pilot run (decision.md, findings.json, reviews.json, state.json, closure.md, adversarial-*.md, claude-*.md) — these are the best real evidence of whether the infrastructure works, since this run is a live self-test of the system under review.
- I ran read-only verification commands: `bash -n` on both shell scripts, `python3 -m py_compile` on all six Python scripts, and `python3 scripts/validate-review-run.py --task review-infrastructure` (exits 0). I did not modify any files.
- I did not audit the unrelated AD-applicability changes (`backend/app/**`, `frontend/**`, `.ai/ad-calibration/**`, etc.). They are correctly declared out-of-scope in the manifest with a machine-checked rationale, and appear to belong to a separate, independently-reviewed task (`t081`, per `.ai/reviews/claude-t081-*.md`). I did not re-review that work.
- I could not exercise the actual Codex-runtime subagent assignment (identity issuance) since that happens outside this repository; I evaluated only the repository-side attestation and validation logic, consistent with the design's own stated trust boundary.
- Two prior Claude invocation attempts for this exact run exist in `.ai/review-runs/review-infrastructure/`: `claude-external-critic-20260822T231735Z.*` (failed with a DNS/API connectivity error) and `claude-external-critic-20260823T003808Z.*` (this session, network available). I inspected both.

## 2. Findings

### review-infrastructure-CC-001 — Bootstrap/retrospective runs can satisfy `validate-review-run.py` without any independent closure-stage review, and this run's own closure claim is unbacked by that stage

**Violated invariant:** "Closure rejects unresolved blockers and unsupported dispositions" (decision.md, `.ai/review-runs/review-infrastructure/decision.md:17`); REVIEW_PROCESS.md gate 6 ("Closure... Completion requires... a final review of the resulting working tree.").

**Evidence:**
- `scripts/validate-review-run.py:176` — `implementation_review = latest_by_stage.get("closure") or latest_by_stage.get("implementation")`: a passed **implementation**-stage review is accepted as a substitute for a **closure**-stage review.
- `scripts/validate-review-run.py:183-186`: for non-bootstrap runs, `phase` must equal `"closed"` to pass; but for any run with `bootstrapException` set, `phase` only needs to be `"implementation_reviewed"` — a strictly weaker bar that does not require the closure stage to ever run.
- `phase` is set to `"closed"` **only** by a passed `--stage closure` call in `scripts/record-review.py:63-64`.
- `.ai/review-runs/review-infrastructure/reviews.json` contains only `design` and `implementation` stage entries — no `"stage": "closure"` entry exists.
- `.ai/review-runs/review-infrastructure/state.json` shows `"phase": "implementation_reviewed"`, not `"closed"`.
- I confirmed the run nonetheless reports as closable: `python3 scripts/validate-review-run.py --task review-infrastructure` → `review run is closable`.

**Impact:** The task's own decision packet lists "Closure rejects unresolved blockers and unsupported dispositions" as a safety invariant, and REVIEW_PROCESS.md documents closure as a distinct, mandatory final gate with its own independent reviewer. This pilot's `closure.md` declares the outcome as final ("independent design and implementation reviews now pass... All ten Codex adversarial findings are closed") without a closure-stage review ever having occurred, and the tooling accepted that as sufficient. Any future run that sets `bootstrapException` (nothing restricts who may set it or when — see CC-002) inherits the same weaker bar and can skip the closure gate entirely while still printing "review run is closable."

**Required closure:** Either (a) require a passed `closure`-stage review for **every** run regardless of `bootstrapException`, or (b) if the bootstrap exception is meant to relax this, state that explicitly in `decision.md`/`REVIEW_PROCESS.md` as an intentional, scoped, one-time relaxation, and still record an actual closure-stage attestation for `review-infrastructure` before considering it closed. As it stands, `review-infrastructure` is not closed by its own contract.

---

### review-infrastructure-CC-002 — No script implements the "framed → design_reviewed → implementation" phase transition for bootstrap runs; this run's own phase progression could only have been produced by hand-editing `state.json` outside any tracked tool

**Violated invariant:** "A design blocker prevents implementation from passing its gate" (decision.md invariant); AR-D-003's closure disposition claim that "transition scripts... an explicit retrospective bootstrap exception" were added.

**Evidence:**
- `scripts/create-review-run.sh:27` initializes every run with `"bootstrapException": null`. No script ever writes a non-null value.
- `scripts/record-review.py:39,59,67`: all three phase-transition branches for the `design` stage are explicitly gated with `and not state.get("bootstrapException")`. When `bootstrapException` is set, recording a design review — pass **or** fail — never changes `phase` at all.
- `scripts/advance-review-run.py:14`: `--to implementation` requires `state.get("phase") == "design_reviewed"`; nothing else can produce that phase value.
- Net effect: for a run with `bootstrapException` set, there is **no code path** in this changeset that moves `phase` away from `"framed"`.
- Yet `.ai/review-runs/review-infrastructure/state.json` has `"bootstrapException": "..."` and `"phase": "implementation_reviewed"`, and its `reviews.json` records design/implementation reviews dated `2026-08-22T22:59:10Z` through `23:06:17Z` — i.e., this exact phase value exists today, produced by neither `record-review.py` nor `advance-review-run.py`.

**Impact:** The mechanism that is supposed to make "design blocks implementation" auditable and tool-enforced does not exist for the one case (bootstrap) where the whole exception was invented. The actual `state.json` for this pilot must have been hand-written, which means there is no reproducible, versioned procedure future coordinators can follow to legitimately create another bootstrap run — and, more importantly, nothing distinguishes a legitimate hand-edit (this pilot) from an illegitimate one (a coordinator skipping design review on a non-bootstrap task by copying this pattern). The written record (`reviews.json`) does still show a real passed, distinct-identity design review occurred, so the substantive safety property was likely honored here — but the tooling cannot itself prove that the phase value wasn't simply asserted.

**Required closure:** Add an explicit, audited script command (e.g., `advance-review-run.py --to design_reviewed --bootstrap-reason "..."`) that transitions phase for bootstrap runs based on an existing passed `design`-stage review record, so no run's `phase` value is ever produced by manual JSON editing.

---

### review-infrastructure-CC-003 — The documented workflow entry points never mention `record-review.py` or `advance-review-run.py`, so following the docs as written cannot produce a closable run

**Violated invariant:** Decision packet's "Read paths and consumers": "Codex reads `AGENTS.md`, the local skill, role briefs, packets, and ledgers" as the operational guide.

**Evidence:**
- `grep -rn "record-review\|advance-review-run" --include="*.md" .` (excluding the auto-generated `review-packet.md`) returns **zero** hits in `AGENTS.md`, `.ai/REVIEW_PROCESS.md`, `.ai/CLAUDE_REVIEWER.md`, or `.agents/skills/adversarial-review/SKILL.md`.
- `.agents/skills/adversarial-review/SKILL.md:17-37` ("Review the design", "Review implementation slices") only instructs adding findings to `findings.json` and generating the packet — it never says to run `scripts/record-review.py` to attest the review or `scripts/advance-review-run.py` to move the phase forward.
- `scripts/validate-review-run.py:175-186` hard-requires populated `reviews.json` entries and (for non-bootstrap runs) `phase == "closed"` to declare closability.

**Impact:** A coordinator/builder who follows only the shipped skill/process docs (the intended durable interface, per the decision packet) will populate `findings.json` and the packet but never call the two scripts that actually make a run closable. The run will be permanently stuck failing `validate-review-run.py` with "no passed independent design review" / "review phase is not closed," with no guidance in the documentation on how to fix it. This is a real usability defect discovered by the very audit the packet asked for ("report missing consumers... omitted from the manifest" — these two scripts are in scope but have no documented caller in the skill or process docs).

**Required closure:** Add explicit `record-review.py`/`advance-review-run.py` invocation examples to `.ai/REVIEW_PROCESS.md` gates 2/3/4/6 and to the corresponding `SKILL.md` sections.

---

### review-infrastructure-CC-004 — Claude-finding reconciliation depends entirely on exact, unenforced Markdown heading formatting, so a formatting deviation silently drops findings from ledger reconciliation

**Violated invariant:** "Claude output is independently validated rather than automatically accepted" (decision.md); AR-005 closure evidence ("stable IDs must reconcile").

**Evidence:**
- `scripts/validate-review-run.py:191-196`: reconciliation is implemented purely as `re.findall(r"(?m)^###\s+(.+)$", claude_text)` against every H3 heading in the file, then a second regex hunts for `{task}-CC-\d+` tokens anywhere in the text.
- There is no structural (e.g., JSON/YAML front-matter) requirement for Claude's findings; the entire contract is "use `###` and this exact ID pattern," enforced only by a prompt instruction in `scripts/claude-review.sh` (lines ~122-125), not by any output schema the model is forced into.
- If the model uses a different heading level, omits the em dash, uses a different ID delimiter, or expresses a real blocker as prose/bullets instead of an H3 heading, `re.findall(rf"{task}-CC-\d+", claude_text)` finds nothing for that finding, and it is silently excluded from the reconciliation check — no error is raised, `validate-review-run.py` reports the run closable. Conversely, any other legitimate H3 subheading in Claude's output (e.g., under "Verification Notes") that doesn't happen to contain the ID pattern raises a spurious ledger error, encouraging future maintainers to weaken the check to make it pass — a natural erosion path back to (a).

**Impact:** The one server-side backstop meant to prevent a Claude-identified blocker from being silently lost is only as reliable as the model's incidental adherence to a prompt-requested string format, with no independent structural validation. This is a real gap for exactly the failure mode AR-005 claims to have closed.

**Required closure:** Require Claude to emit findings as a fenced JSON/YAML block (mirroring `FINDINGS.json.schema`) in addition to/instead of prose headings, and validate that block structurally, rather than regex-matching free-form Markdown headings.

---

### review-infrastructure-CC-005 — Failed Claude invocation artifacts are retained under the same naming convention as successful reviews and are not gitignored, while `closure.md` inaccurately states Claude was never invoked

**Violated invariant:** Packet/audit-trail accuracy ("Packets identify staged, unstaged, untracked, and explicitly excluded scope" — closure.md is part of that audit trail and should be accurate).

**Evidence:**
- `.ai/review-runs/review-infrastructure/claude-external-critic-20260822T231735Z.md` contains only: `API Error: Can't reach the API server — check your internet or DNS (ENOTFOUND)`. Its `.debug.log` confirms 11 failed connection attempts (`getaddrinfo ENOTFOUND api.anthropic.com`).
- This file matches the `.gitignore` allow-list (only `*.debug.log`, `*.events.jsonl`, `*.partial.md`, and `review-packet.sha256` are ignored under `.ai/review-runs/*/`), so it would be committed as if it were a legitimate review artifact.
- `.ai/review-runs/review-infrastructure/closure.md` ("Not verified" section) states: "Claude was not invoked." This is factually incorrect — Claude was invoked twice (`231735Z` failed on connectivity; `003808Z`, this session, succeeded).

**Impact:** Low direct risk, but this is exactly the kind of audit-trail inaccuracy the whole system exists to prevent. A future reader of `closure.md` would reasonably conclude no Claude attempt was made, when in fact an attempt failed and left an artifact that looks superficially like a completed (empty) review.

**Required closure:** Correct `closure.md` to state that Claude was invoked and failed due to connectivity, and/or have `claude-review-stream.py`/`claude-review.sh` name or tag error-terminated outputs distinctly (e.g., `*.error.md`) so they aren't mistaken for substantive reviews and aren't swept into `claude-*.md` glob-based reconciliation logic.

## 3. Open Questions

- Is the intent that `bootstrapException` may be used again for future infra changes, or was it meant strictly as a one-time pilot exception that should be structurally disabled going forward (e.g., by removing the code path once this run closes)? CC-001/CC-002 are more severe if this remains generally available.
- Should `.ai/reviews/*.md` (the pre-existing, still-actively-used convention, e.g. `claude-t081-*.md` dated today) be explicitly deprecated in favor of `.ai/review-runs/<task>/`, or are both conventions meant to coexist indefinitely?

## 4. Verification Notes

- `bash -n scripts/create-review-run.sh scripts/claude-review.sh` — both pass.
- `python3 -m py_compile` on all six changed Python scripts — passes.
- `python3 scripts/validate-review-run.py --task review-infrastructure` — reports "review run is closable" despite CC-001/CC-002 above.
- Confirmed `findings.json` has exactly 10 entries, all `status: closed`, matching `closure.md`'s claim.
- Confirmed no `"stage": "closure"` entry exists in `reviews.json`, and `state.json.phase == "implementation_reviewed"`.
- Confirmed via `grep` that no script other than `create-review-run.sh` (initializing to `null`) touches `bootstrapException`.
- Confirmed via `grep` that `record-review.py`/`advance-review-run.py` are absent from `AGENTS.md`, `.ai/REVIEW_PROCESS.md`, `.ai/CLAUDE_REVIEWER.md`, and the skill's `SKILL.md`.
- Did not run `npm run lint` or the backend pytest suite — out of scope for this task (no backend/frontend code changes belong to review-infrastructure).

## 5. Brief Summary

The Codex builder/adversary loop closed 10 well-reasoned findings covering identity spoofing, staleness, scope-omission, ledger schema, and Claude reconciliation. However, this external critic found that the pilot's own closure does not actually satisfy the process it built: no closure-stage review was ever recorded, the bootstrap phase progression has no supporting tooling and must have been hand-edited, the primary documentation omits two scripts required for any run to close, and the Claude-reconciliation safety net is regex-fragile. These are concrete, evidence-backed gaps in the review-infrastructure's own claimed guarantees, not speculative concerns.