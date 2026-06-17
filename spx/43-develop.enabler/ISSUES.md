# Issues: Develop Plugin

## 1. Named-subject convention sweep — prose swept; scoped residuals remain (OPEN)

The `develop` plugin's `agent-prompt-standards` `<voice>` rule requires authored prompt
content to drop the subject (imperative mood) by default and name **"Claude"** for behavioral
claims, tendencies, and failure modes. **"the agent"**, **"an agent"**, **"the model"**, and
**"you"** are banned subjects. The build ships authored content verbatim to both runtimes, so the
authored canon is always "Claude".

**Done (this sweep):** every executing-instance agent-subject in authored prompt prose — SKILL.md
bodies, slash-command bodies, and skill `references/*.md` — is swept to imperative or "Claude".
This includes the **compound** forms a naive `\bthe agent\b` grep misses: `the wrapper agent`
(reviewing-changes, thread-store), `the calling agent` / `the calling agent or orchestrator` →
`the caller` (the verdict-emission boilerplate across `audit`, `audit-tests`, `audit-adr`,
`audit-pdr`, `audit-skills`, `audit-commands`, `audit-subagents`, `audit-python`,
`audit-python-architecture`, `audit-rust`, `audit-rust-architecture`,
`audit-typescript`, `audit-typescript-architecture`, `review-pr`), `the orchestrating
agent` (architect-python), and `the next agent` → `the next session` (handoff). Verify with a
**PCRE, case-insensitive** survey — `git grep -niP '\b(the|an|a|this|next|calling|wrapper) (\w+ )?agent\b'`
over `src/plugins/**/*.md` — not POSIX `-E` (git's `-E` does not honor `\b` and silently matches
nothing).

**Two non-voice REJECTs the skill-auditor surfaced and this change also fixes (bounded):**

- `inspect-github-actions` invoked `uv run python "${CLAUDE_SKILL_DIR}/scripts/gh_access.py"` and declared
  `Bash(uv run:*)` — a portability break (`uv` is absent in consumer repos). Now `python3` +
  `Bash(python3:*)`, per the `python3`-only plugin constraint.
- `audit`'s description was passive (`Use when asked by the user to invoke the audit skill`). Now
  directive (`ALWAYS invoke … NEVER …`).

**Legitimate keeps (distinct entity / domain / not the executing instance):** named agents
(`changes-reviewer`/`pr-reviewer`/`Explore`/`applier`/`*-auditor` agent, the operator's `main
agent`, the review command's `main agent`); the `agent` frontmatter field name; multi-agent
orchestration domain content in `create-subagents/references/`; `coding agent` as an external
*product* category and user-facing "your coding agent" (draw-excalidraw README); "a separate agent"
delegation advice (large-diagrams); `local agent instructions` (a repo-file category, coding/test-typescript);
the `<self_reference>` blocks that document banned output-artifact identity strings; and the
rule-documentation lines in `agent-prompt-standards` / `auditing-*` that quote the banned
subjects verbatim.

**Residuals (genuinely larger / distinct concern — tracked, not deferred-by-origin):**

- **Subagent definition voice** (`spec-tree/agents/audit-orchestrator.md`, `auditor.md`,
  `pr-review-orchestrator.md`, `spx-updater.md`): pervasive `this agent` / `the agent` referring to
  the *defined* agent (`This agent holds no audit policy of its own`, `as this agent's result`,
  `constructed in this agent`). Whether a subagent definition naming itself counts as the banned
  generic subject is a distinct question governed by the **subagent**-auditor (`audit-subagents`,
  not the skill-auditor run for this sweep), and the referential forms (`this agent's prose`) do not
  map cleanly to imperative/"Claude". Sweep it as a dedicated subagent-voice pass with a
  `develop:subagent-auditor` gate.
- **`uv run` beyond `inspect-github-actions`** (`python` plugin `uv run pytest`/`ruff`/`mypy`; excalidraw
  `uv run playwright`/`render_excalidraw.py`): a design decision about how each plugin invokes the
  consumer's toolchain and the vendored excalidraw setup — distinct from the bundled-stdlib-helper
  case fixed here.
- **Skill-auditor WARNINGs** (worth-improving, not blocking): spec-tree review-change skill name vs the
  imperative convention in `spx/local/skills.md`; orphaned `review-changes/references/render/*` and
  `inspect-github-actions/scripts/workflow_inspect.py`. (`skill-standards` over the 500-line ceiling —
  resolved: split into `references/runtime-variables.md` and `references/script-standards.md`.)
- **Standalone `you` / `the model`** beyond prose: **DONE — complete across all six plugins.** The
  executing-Claude `you`/`your`/`yourself` sweep ran as a per-plugin pass, converting executing-Claude
  second-person to imperative/declarative and keeping user-facing intake/README/brand second-person,
  subagent role-framing example prompts (`You are a …`), and rule-doc quotes of the banned term.
  Merged: `rust` (#219, + reflexive cleanup #229), `work` (#221), `hdl` (#223), `develop` (#225),
  `python` (#226, + behavioral-claim parity #230), `typescript` (#228). A behavioral claim in
  `audit-python`/`audit-typescript` ("what the auditor catches beyond automated tools") was
  named to **"Claude"** (`Claude catches:`) per the `<voice>` behavioral-claim rule. Verify with the
  PCRE survey `git grep -niP "\byou\b|\byour\b|\byourself\b" -- 'src/plugins/<plugin>/**/*.md'`:
  `rust`/`python`/`typescript` return only keeps; `work`/`hdl`/`develop` return only intake/README/
  role-framing/rule-quote keeps. The `the model` survey is clean. This completes the marketplace-wide
  named-subject conformance for the executing-Claude axis.

  **Tracked follow-ups — DONE (named-subject voice axes, branch `work/named-subject-voice-followups`):**

  - **Passive auditor-skill `description:` directiveness — DONE.** Converted the 9 passive
    `auditing-*` descriptions (`description: Use when asked by the user to invoke the … skill`,
    ~77% activation) to the directive `ALWAYS invoke … NEVER …` folded-scalar form (~100%) per
    `<description_style>`: `python` (audit-python, audit-python-architecture), `rust`
    (audit-rust, audit-rust-architecture, audit-rust-tests), `spec-tree` (auditing-tests),
    `typescript` (audit-typescript, audit-typescript-architecture, audit-typescript-tests).
    The `develop`/`prose` auditors and `audit-python-tests` were already directive.
  - **Uniform `<what_you_do_not_do>` → `<out_of_scope>` tag rename — DONE.** Renamed the section
    tag in the only two skills that carry it — `architect-rust` and `architect-typescript`
    (identical sections, parity preserved). `architect-python` has no such section.
  - **`<failure_modes>` "the auditor" role-noun → "Claude" — DONE.** Converted every executing-
    instance "The auditor"/"This auditor" subject to "Claude" per `<failure_mode_writing>` in
    `audit-python` (5 sites) and `audit-typescript` (5 sites). The `develop:skill-auditor`
    gate surfaced the identical pattern in `audit-python-architecture` (6 sites) and
    `audit-typescript-architecture` (5 sites) — both swept in the same change to keep parity (the
    axis under-enumerated the architecture auditors). The deterministic PCRE survey returns clean.

  **New tracked follow-up (surfaced by the skill-auditor gate during the voice sweep — separate, structural):**

  - **Audit-skill structural conformance — marketplace-wide.** `skill-standards` mandates
    `allowed-tools: Read, Grep, Glob, Bash` for every `auditing-*` skill and (per `<xml_structure>`)
    omitting `<quick_start>` on validator/gate skills. The touched-file portion is **fixed in this
    PR** (the local `changes-reviewer` gate raised it as in-scope touched-file debt): `audit-tests`
    gained `allowed-tools` and dropped its `<quick_start>` (its `/contextualize` prerequisite and
    coupling-gate already live in `<essential_principles>`/`<audit_workflow>`/`<success_criteria>`),
    and `audit-python-architecture` + `audit-typescript-architecture` completed their
    `allowed-tools` (`Read, Grep` → `Read, Grep, Glob, Bash`). **Remaining (untouched files, dedicated
    pass):** `allowed-tools` absent in `develop/audit-commands`, `develop/audit-skills`,
    `develop/audit-subagents`; `<quick_start>` carried by those 3 `develop` auditors plus the
    complex code auditors `audit-python`, `audit-rust`, `audit-typescript` (whether a
    multi-phase code auditor is a "validator" that must omit `<quick_start>` is the unsettled design
    call for that pass — the skill-auditor split on it). Also:
    `spec-tree/review-pr` carries the same passive `Use when asked by the user …` description (not
    an `auditing-*` skill, so outside the voice axis above) — fold into the directive-description pass
    or this structural pass.

**Verification gate:** `develop:skill-auditor` (`/audit-skills`) loads `agent-prompt-standards`;
`develop:subagent-auditor` (`/audit-subagents`) governs the agent-definition files. Run both on
changed targets; the deterministic PCRE `git grep` confirms the named-subject axis specifically.

Surfaced 2026-06-12 while correcting a named-subject regression introduced in PR #169 and fixed in
PR #171 (`understand` skill).
