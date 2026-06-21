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
(review-changes, thread-store), `the calling agent` / `the calling agent or orchestrator` →
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
rule-documentation lines in `agent-prompt-standards` / `audit-*` that quote the banned
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
    `audit-*` descriptions (`description: Use when asked by the user to invoke the … skill`,
    ~77% activation) to the directive `ALWAYS invoke … NEVER …` folded-scalar form (~100%) per
    `<description_style>`: `python` (audit-python, audit-python-architecture), `rust`
    (audit-rust, audit-rust-architecture, audit-rust-tests), `spec-tree` (audit-tests),
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
    `allowed-tools: Read, Grep, Glob, Bash` for every `audit-*` skill and (per `<xml_structure>`)
    omitting `<quick_start>` on validator/gate skills.

    **⚠️ Post-collapse exception (PR #275, the auditor collapse — do NOT strip `Skill`).** The
    generic composing auditors `audit-adr`, `audit-tests`, and `audit` now carry
    `allowed-tools: Read, Grep, Glob, Bash, Skill` — the `Skill` tool is REQUIRED so they compose
    `audit-{lang}*` by language partition per `spx/21-spec-tree.enabler/17-auditing.adr.md`.
    Treating the blanket four-tool rule as absolute would revert the merged composition mechanism
    (composition is unexecutable without `Skill`). Any marketplace-wide allowed-tools sweep must
    keep `Skill` on those three skills. The 10 per-language auditor agents
    (`{python,typescript,rust}-{architecture,code,test}-auditor`, `rust-unsafe-auditor`) were
    removed in the same collapse, so the audit-skill set this sweep ranges over is the post-collapse
    set, and the `<quick_start>`-on-validator question below is the same family-wide deviation now
    tracked in `spx/21-spec-tree.enabler/32-decisions.enabler/ISSUES.md` — reconcile the two rather
    than running parallel passes.

    The touched-file portion is **fixed in this
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
    an `audit-*` skill, so outside the voice axis above) — fold into the directive-description pass
    or this structural pass.

    **Update (agent-only-audit-dispatch change):** the missing `allowed-tools` on
    `develop/audit-skills`, `develop/audit-commands`, and `develop/audit-subagents` is now **fixed**
    — all three gained `allowed-tools: Read, Grep, Glob, Bash` as touched-file debt while their
    descriptions were converted to the agent-preloaded dispatch-steering form. The `<quick_start>`
    question for the 3 develop auditors plus the complex code auditors remains for the dedicated pass.

  - **Verdict-toolchain path portability — marketplace-wide.** Every `audit-*` skill's
    `<output_format>` / `<verdict_format>` cites the JSON schema as the bare path
    `plugins/spec-tree/skills/audit/scripts/verdict.py` and names `emit_verdict.py` as the renderer.
    The `develop:skill-auditor` gate flagged this as a consumer-portability concern (an installed
    consumer tree resolves `plugins/` differently); the inline JSON schema block in each skill is
    already self-contained, so the citation is removable. The deterministic `check-skills` /
    reference-portability gates do not flag it, and the pattern is identical across ~15 skills
    (touched and untouched), so the coherent fix is one marketplace-wide pass, not a per-touched-file
    edit. Out of scope for the agent-only-audit-dispatch change; tracked here for that pass.

  - **Verdict-schema row-taxonomy divergence — marketplace-wide.** The `audit-*` skills do not agree
    on `<output_format>` verdict row names: `audit-skills` emits the three-row
    `keep-these-aspects` / `worth-improving` / `must-fix` shape, while `audit-commands` and
    `audit-subagents` emit a four-row `critical-issues` / `recommendations` / `strengths` /
    `quick-fixes` shape, and the `overall` rule differs with it (`PASS` iff `must-fix` empty vs `PASS`
    iff `critical-issues` carries no `REJECT`). All claim conformance to the canonical schema in
    `audit/scripts/verdict.py`. Reconciling requires deciding whether `verdict.py` mandates a uniform
    row taxonomy or treats row names as free-form labels over a fixed envelope — a verification-contract
    question governed by `spx/15-audit-result-delivery.pdr.md` and the auditing nodes, affecting
    `emit_verdict.py` rendering and any auditor agent that indexes on row names. The class spans the
    14 verdict-emitting skills (touched and untouched), so the coherent fix is one marketplace-wide
    pass, not a per-touched-file edit. Surfaced by the `develop:skill-auditor` gate during the PR3
    `Skill`-append; out of scope for that frontmatter change.

**Verification gate:** `develop:skill-auditor` (`/audit-skills`) loads `agent-prompt-standards`;
`develop:subagent-auditor` (`/audit-subagents`) governs the agent-definition files. Run both on
changed targets; the deterministic PCRE `git grep` confirms the named-subject axis specifically.

Surfaced 2026-06-12 while correcting a named-subject regression introduced in PR #169 and fixed in
PR #171 (`understand` skill).

## 2. Skill-delegation `Skill` allowed-tools gap — language + develop + prose plugins (OPEN)

A skill whose body invokes another skill needs `Skill` in `allowed-tools`, or the delegation
requires per-call approval. Two body patterns delegate: the `{!% require_skill … %!}` macro (which
renders to "Invoke the `<skill>` skill before proceeding") and an explicit `Invoke /<skill>`
prerequisite (for example `/understand`, `/contextualize`, the `/test` family). This is the same
requirement the PR #275 composing auditors already satisfy (entry 1 above) — generalized to every
delegating skill, not only `audit-adr` / `audit-tests` / `audit`.

**Closed (PR #279, branch `fix/skill-delegation-allowed-tools`):** every affected skill in the three
touched plugins — spec-tree (`decompose`, `refactor`, `test`, `audit-pdr`, `audit-specs`), python
(`architect-python`, `code-python`, `test-python`, `audit-python`, `audit-python-tests`,
`audit-python-architecture`), and rust (`architect-rust`, `code-rust`, `test-rust`, `audit-rust`,
`audit-rust-tests`, `audit-rust-architecture`). The `audit-*` skills keep their read-only tool set
(`Skill` added, no `Write`/`Edit`).

**Remaining (untouched plugins — follow-up PRs, each its own version bump). Per-plugin playbooks live
in each plugin's owning node; this section holds the develop half and the shared heuristic.**

- **develop — PR3 (develop half) — CLOSED (this PR, branch `fix/skill-delegation-allowed-tools-develop-prose`).**
  `Skill` appended to `allowed-tools` on the three read-only audit skills carrying the
  `{!% require_skill … %!}` macro: `audit-commands`, `audit-skills`, `audit-subagents` (now
  `Read, Grep, Glob, Bash, Skill`; no `Write`/`Edit`). `agent-prompt-standards` is a reference skill
  ("invoke X **instead of me**") and was correctly NOT a gap. The `develop:skill-auditor` gate ran on
  every changed SKILL.md and additionally surfaced a touched-file must-fix fixed in this PR — the
  `<final_step>` "Implement all fixes automatically" option contradicted the read-only audit contract
  in `audit-commands` and `audit-subagents` (both reworded to "Return the prioritized findings to the
  caller for implementation"). The marketplace-wide classes the gate re-flagged (`<quick_start>` on
  validators, bare verdict-path citation, verdict-schema row-taxonomy) stay tracked in §1.
- **typescript — PR2, entangled. CLOSED** (branch `fix/typescript-skill-delegation-allowed-tools`).
  All 6 skills gained `Skill`; `architect-typescript` (`<objective>`) and `audit-typescript`
  (`<repo_local_overlay>`, quick_start Read-rewrite, dangling `rules/` removal) remediated; the
  typescript-unique `code-typescript` missing-`<objective>` and `audit-typescript` duplicate-prose
  defects fixed as touched-file debt. Marketplace-wide classes the gate also surfaced are deferred and
  recorded in `spx/43-typescript.enabler/ISSUES.md`.
- **prose — PR3 (prose half) — CLOSED (this PR, same branch).** `Skill` appended to `audit-prose`,
  `audit-internal-docs` (both now `Read, Glob, Grep, Bash, Skill`, read-only), and `write-internal-docs`
  (now `Read, Edit, Write, Glob, Grep, Skill`). See `spx/43-prose.enabler/ISSUES.md`.

**Detection heuristic (the lesson — for any future allowed-tools sweep).** A skill needs `Skill` in
`allowed-tools` iff its body operationally invokes another skill. The two signals are the
`{!% require_skill … %!}` macro (renders at build to "Invoke the `<skill>` skill before proceeding")
and a `Invoke /<skill>` / `invoke /<skill>` prerequisite in **either** case. The PR #279 sweep
initially missed ~14 skills because the discovery grep matched only lowercase `invoke /`. Enumerate a
plugin's gaps with `grep -liE 'require_skill|invoke`?/[a-z]' src/plugins/<plugin>/skills/*/SKILL.md`,
then DROP reference/standards skills (`*-standards`,`agent-prompt-standards`,`prose-standards`):
they tell the reader to "invoke X **instead of** me" and do not themselves delegate, and skills with
an **empty**`allowed-tools`are unrestricted (no gap). The`audit-*`read-only constraint permits`Skill`(it loads context, it is not`Write`/`Edit`).

**Pre-existing skill-body quality debt surfaced by the `develop:skill-auditor` gate during the PR #279
sweep (separate skill-quality pass — the `allowed-tools` change itself is auditor-confirmed clean on
all 17 touched skills):** the gate, run per the AGENTS.md skill-auditor requirement on every edited
SKILL.md, flagged pre-existing body defects unrelated to the one-line `allowed-tools` change. The two
unambiguous structural bugs were fixed in PR #279 as touched-file debt — `rust/code-rust`'s
`<testing_methodology>` / `</test_methodology>` tag mismatch, and the orphaned (uncited)
`python/audit-python-tests/references/python-test-audit-examples.md` (now cited via `<reference_guides>`).
The remaining items are the same already-tracked marketplace classes (entry 1 above) and belong to
their dedicated passes, not this frontmatter sweep: the bare `plugins/spec-tree/skills/audit/scripts/verdict.py`
path citation across the audit skills (verdict-toolchain portability); `<quick_start>` carried by the
complex code/audit validators; and now also `rust/code-rust`'s duplicate `<reference_loading>` +
`<repo_local_overlay>` blocks (one is redundant — the two auditor runs disagreed on which to keep, so
it is a content judgment for the skill-quality pass) and `python/audit-python-tests`'s reference file
using markdown headings rather than pure-XML structure.
