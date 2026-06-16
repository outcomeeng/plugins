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
- **`uv run` beyond `github-actions`** (`python` plugin `uv run pytest`/`ruff`/`mypy`; excalidraw
  `uv run playwright`/`render_excalidraw.py`): a design decision about how each plugin invokes the
  consumer's toolchain and the vendored excalidraw setup — distinct from the bundled-stdlib-helper
  case fixed here.
- **Skill-auditor WARNINGs** (worth-improving, not blocking): `reviewing-changes` gerund name vs the
  imperative convention in `spx/local/skills.md`; orphaned `reviewing-changes/references/render/*` and
  `github-actions/scripts/workflow_inspect.py`. (`standardizing-skills` over the 500-line ceiling —
  resolved: split into `references/runtime-variables.md` and `references/script-standards.md`.)
- **Standalone `you` / `the model`** beyond prose: **DONE — complete across all six plugins.** The
  executing-Claude `you`/`your`/`yourself` sweep ran as a per-plugin pass, converting executing-Claude
  second-person to imperative/declarative and keeping user-facing intake/README/brand second-person,
  subagent role-framing example prompts (`You are a …`), and rule-doc quotes of the banned term.
  Merged: `rust` (#219, + reflexive cleanup #229), `work` (#221), `hdl` (#223), `develop` (#225),
  `python` (#226, + behavioral-claim parity #230), `typescript` (#228). A behavioral claim in
  `auditing-python`/`auditing-typescript` ("what the auditor catches beyond automated tools") was
  named to **"Claude"** (`Claude catches:`) per the `<voice>` behavioral-claim rule. Verify with the
  PCRE survey `git grep -niP "\byou\b|\byour\b|\byourself\b" -- 'src/plugins/<plugin>/**/*.md'`:
  `rust`/`python`/`typescript` return only keeps; `work`/`hdl`/`develop` return only intake/README/
  role-framing/rule-quote keeps. The `the model` survey is clean. This completes the marketplace-wide
  named-subject conformance for the executing-Claude axis.

  **Tracked follow-ups (separate axes, not the `you` sweep — marketplace-wide, do as dedicated passes):**

  - **Passive auditor-skill `description:` directiveness** — the `auditing-*` skills carry
    `description: Use when asked by the user to invoke the … skill` (passive, ~77% activation). The
    `<description_style>` standard mandates the directive `ALWAYS invoke … NEVER …` form (~100%).
    A marketplace-wide pass over every `auditing-*` skill's description.
  - **Uniform `<what_you_do_not_do>` → `<out_of_scope>` tag rename** — `architecting-rust` and
    `architecting-typescript` both use the `<what_you_do_not_do>` section tag (kept identical across
    the two for parity during the `you` sweep). A coordinated rename to `<out_of_scope>` across all
    `architecting-*` skills removes the `you` substring from the structural tag without per-plugin drift.
  - **`<failure_modes>` "the auditor" role-noun → "Claude"** — `auditing-python` (~10 sites) and
    `auditing-typescript` (~9 sites) narrate failure modes with "The auditor …" as the subject. The
    `<failure_mode_writing>` rule names **"Claude"** for failure modes; "the auditor" is a non-Claude
    named subject. Pre-existing and identical across the two plugins; sweep both together to preserve
    parity, gated by `develop:skill-auditor`.

**Verification gate:** `develop:skill-auditor` (`/auditing-skills`) loads `standardizing-agent-prompts`;
`develop:subagent-auditor` (`/auditing-subagents`) governs the agent-definition files. Run both on
changed targets; the deterministic PCRE `git grep` confirms the named-subject axis specifically.

Surfaced 2026-06-12 while correcting a named-subject regression introduced in PR #169 and fixed in
PR #171 (`understanding` skill).
