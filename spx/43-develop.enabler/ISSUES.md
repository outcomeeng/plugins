# Issues: Develop Plugin

## 1. Named-subject convention sweep — prose swept; scoped residuals remain (OPEN)

The `develop` plugin's `standardizing-agent-prompts` `<voice>` rule requires authored prompt
content to drop the subject (imperative mood) by default and name **"Claude"** for behavioral
claims, tendencies, and failure modes. **"the agent"**, **"an agent"**, **"the model"**, and
**"you"** are banned subjects. The build ships authored content verbatim to both runtimes, so the
authored canon is always "Claude".

**Done (this sweep):** every executing-instance agent-subject in authored prompt prose — SKILL.md
bodies, slash-command bodies, and skill `references/*.md` — is swept to imperative or "Claude".
This includes the **compound** forms a naive `\bthe agent\b` grep misses: `the wrapper agent`
(reviewing-changes, thread-store), `the calling agent` / `the calling agent or orchestrator` →
`the caller` (the verdict-emission boilerplate across `auditing`, `auditing-tests`, `audit-adr`,
`audit-pdr`, `auditing-skills`, `auditing-commands`, `auditing-subagents`, `auditing-python`,
`auditing-python-architecture`, `auditing-rust`, `auditing-rust-architecture`,
`auditing-typescript`, `auditing-typescript-architecture`, `reviewing-pr`), `the orchestrating
agent` (architecting-python), and `the next agent` → `the next session` (handoff). Verify with a
**PCRE, case-insensitive** survey — `git grep -niP '\b(the|an|a|this|next|calling|wrapper) (\w+ )?agent\b'`
over `src/plugins/**/*.md` — not POSIX `-E` (git's `-E` does not honor `\b` and silently matches
nothing).

**Two non-voice REJECTs the skill-auditor surfaced and this change also fixes (bounded):**

- `github-actions` invoked `uv run python "${CLAUDE_SKILL_DIR}/scripts/gh_access.py"` and declared
  `Bash(uv run:*)` — a portability break (`uv` is absent in consumer repos). Now `python3` +
  `Bash(python3:*)`, per the `python3`-only plugin constraint.
- `auditing`'s description was passive (`Use when asked by the user to invoke the audit skill`). Now
  directive (`ALWAYS invoke … NEVER …`).

**Legitimate keeps (distinct entity / domain / not the executing instance):** named agents
(`changes-reviewer`/`pr-reviewer`/`Explore`/`applier`/`*-auditor` agent, the operator's `main
agent`, the review command's `main agent`); the `agent` frontmatter field name; multi-agent
orchestration domain content in `creating-subagents/references/`; `coding agent` as an external
*product* category and user-facing "your coding agent" (excalidrawing README); "a separate agent"
delegation advice (large-diagrams); `local agent instructions` (a repo-file category, coding/testing-typescript);
the `<self_reference>` blocks that document banned output-artifact identity strings; and the
rule-documentation lines in `standardizing-agent-prompts` / `auditing-*` that quote the banned
subjects verbatim.

**Residuals (genuinely larger / distinct concern — tracked, not deferred-by-origin):**

- **Subagent definition voice** (`spec-tree/agents/audit-orchestrator.md`, `auditor.md`,
  `pr-review-orchestrator.md`, `spx-updater.md`): pervasive `this agent` / `the agent` referring to
  the *defined* agent (`This agent holds no audit policy of its own`, `as this agent's result`,
  `constructed in this agent`). Whether a subagent definition naming itself counts as the banned
  generic subject is a distinct question governed by the **subagent**-auditor (`auditing-subagents`,
  not the skill-auditor run for this sweep), and the referential forms (`this agent's prose`) do not
  map cleanly to imperative/"Claude". Sweep it as a dedicated subagent-voice pass with a
  `develop:subagent-auditor` gate.
- **`spx/CLAUDE.md` template** (`understanding/templates/spx-claude.md:131`, one `The agent acts on
  each finding` line): a versioned consumer-guide template — fixing it requires a `template_version`
  bump and an `/update-spx` re-render of this repo's `spx/AGENTS.md` and downstream guides.
- **`uv run` beyond `github-actions`** (`python` plugin `uv run pytest`/`ruff`/`mypy`; excalidraw
  `uv run playwright`/`render_excalidraw.py`): a design decision about how each plugin invokes the
  consumer's toolchain and the vendored excalidraw setup — distinct from the bundled-stdlib-helper
  case fixed here.
- **Skill-auditor WARNINGs** (worth-improving, not blocking): `standardizing-skills` 543 lines over
  the 500 ceiling; `reviewing-changes` gerund name vs the imperative convention in
  `spx/local/skills.md`; orphaned `reviewing-changes/references/render/*` and
  `github-actions/scripts/workflow_inspect.py`.
- **Standalone `you` / `the model`** beyond prose: noisy survey, mostly legitimate
  (reader-addressing `you`, domain/data models); classify per-site if pursued.

**Verification gate:** `develop:skill-auditor` (`/auditing-skills`) loads `standardizing-agent-prompts`;
`develop:subagent-auditor` (`/auditing-subagents`) governs the agent-definition files. Run both on
changed targets; the deterministic PCRE `git grep` confirms the named-subject axis specifically.

Surfaced 2026-06-12 while correcting a named-subject regression introduced in PR #169 and fixed in
PR #171 (`understanding` skill).
