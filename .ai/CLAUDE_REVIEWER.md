# Claude Code Reviewer

Side-fork conclusion:

- Claude Code is installed and authenticated in the user's interactive terminal.
- `antigravity` is not on `PATH`.
- Claude's valid permission modes include `plan`.
- Codex can see the `claude` executable, but this execution context does not share the user's Claude login.

Current auth state in Codex:

- `claude -p` from Codex returns `Not logged in`.
- `claude doctor` from Codex reports Claude Code `2.1.206` and notes that macOS Keychain is not writable in this execution context.

Operational decision:

- The reviewer automation is `scripts/claude-review.sh`.
- The script can be run by Codex when Claude auth is available in this process.
- If Codex lacks Claude login, the script supports an ignored `.env.claude-review` bridge that sets `ANTHROPIC_API_KEY` for Claude `--bare` mode.
- Review output is written to `.ai/reviews/` so findings can be brought back into the main Codex thread for triage.
- The script uses Claude `--permission-mode plan` and asks Claude not to edit files.
- The script defaults `CLAUDE_REVIEW_MODEL=sonnet`. Use Sonnet for normal high-stakes review; choose a higher model only when the work is unusually critical, ambiguous, or architecture-heavy.

When to use Claude:

- Use Claude after Codex has looped or self-reviewed at least twice on high-stakes work.
- Use Claude for complex or critical logic, security decisions, privacy/data-retention decisions, AWS/IAM/Terraform changes, cost/billing decisions, migrations, and other changes where a missed issue could be expensive or unsafe.
- Do not one-shot critical app portions. Implement, self-review, verify, revise if needed, then run Claude review.
- Do not run Claude for low-level tasks with clear existing patterns unless those tasks touch one of the high-stakes areas above.
- Treat Claude output as review input, not automatic truth. Codex triages findings into fix-now, document/accept-risk, or defer with rationale.

Run:

```bash
scripts/claude-review.sh
```

Optional model override:

```bash
CLAUDE_REVIEW_MODEL=opus scripts/claude-review.sh
```

Optional base ref:

```bash
scripts/claude-review.sh origin/main
scripts/claude-review.sh HEAD
```

After it finishes, paste the findings or point Codex at the generated `.ai/reviews/claude-review-*.md` file.

Codex-auth bridge:

```bash
cp scripts/claude-review.env.example .env.claude-review
chmod 600 .env.claude-review
$EDITOR .env.claude-review
```

Set `ANTHROPIC_API_KEY` in that ignored local file. Do not paste the value into chat and do not commit it. Once present, Codex can run:

```bash
scripts/claude-review.sh
```
