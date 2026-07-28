# Outcome Engineering Plugin Marketplace

A combined Codex and Claude Code plugin marketplace for [Outcome Engineering](https://outcome.engineering) — the product engineering paradigm where a durable map of your product, maintained as a Spec Tree, serves as the authoritative source of truth for all implementation.

This repository publishes two plugin surfaces from the same source tree:

- `.claude-plugin` packages for Claude Code skills and thin agents
- `.codex-plugin` packages for Codex skill bundles

`AGENTS.md` and [`CLAUDE.md`](CLAUDE.md) are separate root instruction files that share the product-owned repository guidance and carry harness-specific managed Spec Tree sections.

> `/bootstrap` interviews you about your product, then scaffolds a spec tree — the durable map that drives all implementation.

![Bootstrapping a spec tree — Claude interviews you about your product's scope](assets/tutorial/bootstrap/60-boostrap-02-questionnaire-02.png)

## Philosophy

1. **RTFM:** Follow state-of-the-art (SOTA) model prompting guidance, such as [structured prompts based on XML tags](https://docs.prompts.ag/guidelines)
2. **KILO:** *Keep It Local and Observable* — the golden source for all specifications lives locally within the product's Git repository
3. **ABC:** *Always Be Converging* — the spec tree is the desired state; all activities are driven by it, not the other way around
4. **DCI:** *Deterministic Context Injection* — the spec tree constructs a deterministic context injection plan for the model

## Quick Start

### 1. Install the spx CLI

```bash
npm install -g @outcomeeng/spx
```

The [spx CLI](https://www.npmjs.com/package/@outcomeeng/spx) is the developer tool for Spec Tree maintenance and validation. Required by all engineering plugins.

### 2. Add the marketplace

#### Claude Code

```bash
claude plugin marketplace add outcomeeng/plugins
```

#### Codex

```bash
codex plugin marketplace add outcomeeng/plugins
```

Codex registers the marketplace source in the user's `~/.codex/config.toml` and reads the shared `.codex-plugin` bundles from it.

### 3. Install or use plugins

#### Claude Code

```bash
# Spec Tree methodology (requires spx CLI)
claude plugin install spec-tree@outcomeeng

# Language plugins (install per product, require spx CLI)
claude plugin install python@outcomeeng
claude plugin install typescript@outcomeeng

# Optional plugins
claude plugin install prose@outcomeeng
claude plugin install instructions@outcomeeng
```

#### Codex

After adding the marketplace, enable only the plugins a product needs in that repo's committed `.codex/config.toml`:

```toml
[plugins."spec-tree@outcomeeng"]
enabled = true

[plugins."instructions@outcomeeng"]
enabled = true
```

Add language plugins in projects that use them:

```toml
[plugins."python@outcomeeng"]
enabled = true

[plugins."typescript@outcomeeng"]
enabled = true
```

Add domain plugins the same way:

```toml
[plugins."frontend@outcomeeng"]
enabled = true

[plugins."visual@outcomeeng"]
enabled = true

[plugins."hdl@outcomeeng"]
enabled = true
```

### 4. Bootstrap your spec tree

```text
> /bootstrap                       # set up a new spec tree
```

![Scaffold result — product spec, guides, and nodes created](assets/tutorial/bootstrap/90-boostrap-02-questionnaire-05.png)

### 5. Author, implement, commit

```text
> /author outcome for search       # author a new outcome node
> /author PDR for auth policy      # author a product decision
> /author ADR for caching strategy # author an architecture decision
> /apply                         # start the TDD flow
> /commit-changes                  # commit with Conventional Commits
```

See the [full tutorial](docs/tutorial.md) for the complete workflow — from bootstrapping to handoffs.

### Updating plugins

#### Claude Code

```bash
claude plugin marketplace update outcomeeng
```

#### Codex

```bash
codex plugin marketplace upgrade outcomeeng
```

Repository maintainers can verify both catalogs with
`just verify-marketplace-installation`. The command installs every catalog plugin
through the real Claude Code and Codex CLIs in disposable homes, then runs Codex
agent placement against the invocation checkout. It leaves persistent plugin state
unchanged.

After merged distribution changes, `just install-marketplace` refreshes the
project-scoped Claude Code marketplace and the selected `$CODEX_HOME` from the
canonical GitHub source, installs every plugin from both committed catalogs, and
runs Codex lifecycle placement against the invocation checkout.

### Bumping plugin versions on a branch

When working on the marketplace itself, every branch that changes a plugin's
distribution surface bumps that plugin's version exactly once. The `just bump`
recipe automates this — it detects which plugins changed under `src/plugins/<name>/**`
since `origin/main`, classifies each plugin's change pattern into a semver
segment, and updates the `version` field in every manifest each plugin owns
(`.claude-plugin/plugin.json` and, when present, `.codex-plugin/plugin.json`)
in lockstep:

```bash
just bump                          # auto-detect segment per plugin vs origin/main
just bump-dry                      # preview without writing
just bump-check                    # CI gate: exit non-zero if any changed plugin needs a bump
just bump origin/main minor        # force minor for every changed plugin (warns on disagreements)
just bump main major               # major bump vs local main (must be explicit)
```

#### Auto-detection rules

By default, the segment is detected per plugin from the file-status pattern of
its changes:

| Plugin's changes include…                                                                          | Segment |
| -------------------------------------------------------------------------------------------------- | ------- |
| Added / deleted / renamed `skills/<slug>/SKILL.md`                                                 | `minor` |
| Added / deleted / renamed `agents/<slug>.md`                                                       | `minor` |
| Added `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json` (whole plugin or new surface)    | `minor` |
| Anything else — modifications to existing files, internal helpers, templates, references, fixtures | `patch` |

`major` is never auto-detected — it captures a deliberate stability commitment
and requires explicit `--segment major`. Passing an explicit `--segment` flag
overrides per-plugin detection and emits a stderr warning naming any plugin
whose detected segment differed (so you don't silently override the file-status
evidence). When a plugin already carries a bump on this branch, the bumper skips it and
bumps every other changed plugin in the same pass. It preserves manifest bytes
character-for-character outside the `version` field so bumps produce minimal diffs.

Only paths under `src/plugins/<name>/**` count as distribution-surface changes; edits
to `spx/`, `AGENTS.md`, tests, or other top-level files do not trigger a bump.

### Regenerating the runtime trees

The installed plugin trees under `dist/claude/` and `dist/codex/` are generated from `src/plugins/`. After editing anything under `src/plugins/`, rebuild them:

```bash
just build-skills   # uv run python -m outcomeeng.distribution.build src dist
```

The pre-commit hook runs `build-skills` automatically, and `just check-full`'s `dist-diff` step (`git diff --exit-code dist`) fails when `dist/` is out of sync with `src/`, so each `src/plugins/` change and its regenerated `dist/` commit together. Never hand-edit `dist/`.

## Plugins

Skills are available in both Claude Code and Codex, with generated plugin surfaces carrying the thin agents their target supports. Every skill and thin agent across every plugin is listed in the auto-generated catalog below, sourced from `.claude-plugin/marketplace.json` and the YAML frontmatter of each plugin's `SKILL.md` and `agents/*.md`. Run `just docs` to regenerate after touching any of those files; `just check-full` enforces freshness in CI.

<details>
<summary><strong><code>/bootstrap</code> in action</strong> — interactive product interview and scaffold</summary>

| Step                                                                   | Screenshot                                                                              |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Detect product** — reads CLAUDE.md, identifies what the product does | ![Detect product](assets/tutorial/bootstrap/20-boostrap-01-detect-product.png)          |
| **Outcome hypothesis** — what user behavior change do you expect?      | ![Outcome hypothesis](assets/tutorial/bootstrap/50-boostrap-02-questionnaire-01.png)    |
| **Scope** — what are the major concerns?                               | ![Scope question](assets/tutorial/bootstrap/60-boostrap-02-questionnaire-02.png)        |
| **Shared infrastructure** — should anything be an enabler?             | ![Shared infrastructure](assets/tutorial/bootstrap/70-boostrap-02-questionnaire-03.png) |
| **Confirm** — review the scaffold before creating files                | ![Confirm scaffold](assets/tutorial/bootstrap/80-boostrap-02-questionnaire-04.png)      |
| **Result** — scaffold created with product spec, guides, and nodes     | ![Scaffold result](assets/tutorial/bootstrap/90-boostrap-02-questionnaire-05.png)       |

</details>

<!-- BEGIN PLUGIN CATALOG (generated by `just docs` — do not edit) -->

### coding-agents

Coding-agent environments and coordination: /operate-prowl, /message-agents, /coordinate-agents, /recover-prowl-agents

| Type  | Name                    | Purpose                                                                                                                                                    |
| ----- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/coordinate-agents`    | Coding agents in separate worktrees may overlap, depend on each other, share an external blocker, or need ownership coordination                           |
| Skill | `/message-agents`       | Discovering a Prowl coding-agent recipient or sending facts, ownership proposals, state reports, authorizations, or acknowledgements to another agent pane |
| Skill | `/operate-prowl`        | A workflow needs a public Prowl operation or a correlated delegation handback between Prowl coding agents                                                  |
| Skill | `/recover-prowl-agents` | Preparing for or recovering coding-agent sessions after a Prowl restart                                                                                    |

### frontend

Frontend design: /design-frontend skill

| Type  | Name               | Purpose                                                    |
| ----- | ------------------ | ---------------------------------------------------------- |
| Skill | `/design-frontend` | Designing or building web components, pages, or dashboards |

### hdl

HDL engineering: /review-vhdl, /review-systemverilog (idiomatic VHDL-2008 and SystemVerilog IEEE 1800-2017 review)

| Type  | Name                    | Purpose                                                                                          |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------ |
| Skill | `/review-systemverilog` | Reviewing SystemVerilog or Verilog code for idiomatic style, synthesizability, or best practices |
| Skill | `/review-vhdl`          | Reviewing VHDL code for idiomatic style, synthesizability, or best practices                     |

### instructions

Instruction authoring: /create-skill, /create-subagent

| Type  | Name                      | Purpose                                                                                                                                                                                                                                                                                                   |
| ----- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/agent-prompt-standards` | Agent prompt writing conventions enforced across all creator and auditor skills                                                                                                                                                                                                                           |
| Skill | `/audit-skill`            | SKILL.md audit methodology                                                                                                                                                                                                                                                                                |
| Skill | `/audit-subagent`         | Claude: Subagent-configuration audit methodology; Codex: Custom agent-configuration audit methodology                                                                                                                                                                                                     |
| Skill | `/create-skill`           | Creating, editing, or improving SKILL.md files or bundled workflows, references, templates, and scripts                                                                                                                                                                                                   |
| Skill | `/create-subagent`        | Claude: Creating, editing, or configuring subagents; Codex: Creating, editing, or configuring custom agents                                                                                                                                                                                               |
| Skill | `/skill-standards`        | Skill authoring standards enforced across all creating and auditing skills                                                                                                                                                                                                                                |
| Agent | `skill-auditor`           | Auditing, reviewing, or evaluating SKILL.md files for best practices compliance, or when the user asks to audit a skill                                                                                                                                                                                   |
| Agent | `subagent-auditor`        | Claude: Auditing, reviewing, or evaluating subagent configuration files for best practices compliance, or when the user asks to audit a subagent; Codex: Auditing, reviewing, or evaluating custom agent configuration files for best practices compliance, or when the user asks to audit a custom agent |

### prose

Prose craft for external prose (/write-prose, /audit-prose) and internal team docs (/write-internal-docs, /audit-internal-docs)

| Type  | Name                      | Purpose                                                                                                                                                                                                                                                                                              |
| ----- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/audit-internal-docs`    | Reviewing, auditing, or cleaning up the writing in internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content, and team decision records and design specs |
| Skill | `/audit-prose`            | Auditing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                                                              |
| Skill | `/internal-doc-standards` | Catalog of anti-patterns and positive patterns for internal team documents (Notion pages, runbooks, scorecards, hiring rubrics, internal policies, competency models, team decision records, design specs)                                                                                           |
| Skill | `/prose-standards`        | Prose anti-patterns enforced across all skills                                                                                                                                                                                                                                                       |
| Skill | `/write-internal-docs`    | Writing or editing internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, competency models, onboarding guides, status pages, internal wiki content, and team decision records and design specs                                 |
| Skill | `/write-prose`            | Writing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                                                               |

### python

Python engineering: /test-python, /code-python, /audit-python-code, /audit-python-tests, /audit-python-architecture, /architect-python

| Type  | Name                             | Purpose                                                             |
| ----- | -------------------------------- | ------------------------------------------------------------------- |
| Skill | `/architect-python`              | Writing ADRs for Python                                             |
| Skill | `/audit-python-architecture`     | Python-specific architecture audit                                  |
| Skill | `/audit-python-code`             | Python implementation-code audit methodology                        |
| Skill | `/audit-python-tests`            | Python test-evidence audit methodology                              |
| Skill | `/code-python`                   | Writing or fixing implementation code for Python                    |
| Skill | `/python-architecture-standards` | Python ADR conventions enforced across architect and auditor skills |
| Skill | `/python-standards`              | Python code standards enforced across all skills                    |
| Skill | `/python-test-standards`         | Python testing standards enforced across all skills                 |
| Skill | `/test-python`                   | Writing or fixing tests for Python                                  |

### rust

Rust engineering: /test-rust, /code-rust, /audit-rust-code, /audit-rust-tests, /audit-rust-architecture, /architect-rust, rust-simplifier agent

| Type  | Name                           | Purpose                                                                                                                         |
| ----- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/architect-rust`              | Writing ADRs for Rust                                                                                                           |
| Skill | `/audit-rust-architecture`     | Rust-specific architecture audit                                                                                                |
| Skill | `/audit-rust-code`             | Rust implementation-code audit methodology                                                                                      |
| Skill | `/audit-rust-tests`            | Rust test-evidence audit methodology                                                                                            |
| Skill | `/code-rust`                   | Writing or fixing implementation code for Rust                                                                                  |
| Skill | `/rust-architecture-standards` | Rust ADR conventions enforced across architect and auditor skills                                                               |
| Skill | `/rust-standards`              | Rust code standards enforced across all skills                                                                                  |
| Skill | `/rust-test-standards`         | Rust test standards enforced across all skills                                                                                  |
| Skill | `/test-rust`                   | Writing or fixing tests for Rust                                                                                                |
| Agent | `rust-simplifier`              | Simplifying recently modified Rust code while preserving behavior, ownership semantics, testability, and verified test coverage |

### spec-tree

Spec Tree: /understand, /contextualize, /bootstrap, /author, /decompose, /refactor, /align, /interview, /test, /audit-tests, /audit-eval-evidence, /audit-adr, /audit-pdr, /audit-implementation, /audit-specs, /audit-changeset-coherence, /apply, /commit-changes, /handoff, /pickup, /refocus, /diagnose, /issue

| Type  | Name                          | Purpose                                                                                                                                                                                                                                                                                                                                                         |
| ----- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/align`                      | Reviewing, auditing, or checking spec file conformance                                                                                                                                                                                                                                                                                                          |
| Skill | `/apply`                      | Implementing any spec-tree work item                                                                                                                                                                                                                                                                                                                            |
| Skill | `/audit-adr`                  | ADR audit methodology                                                                                                                                                                                                                                                                                                                                           |
| Skill | `/audit-changeset-coherence`  | Changeset-coherence audit methodology                                                                                                                                                                                                                                                                                                                           |
| Skill | `/audit-eval-evidence`        | Eval-evidence audit methodology                                                                                                                                                                                                                                                                                                                                 |
| Skill | `/audit-implementation`       | Implementation-audit orchestration methodology                                                                                                                                                                                                                                                                                                                  |
| Skill | `/audit-pdr`                  | PDR audit methodology                                                                                                                                                                                                                                                                                                                                           |
| Skill | `/audit-specs`                | Spec-node audit methodology                                                                                                                                                                                                                                                                                                                                     |
| Skill | `/audit-tests`                | Test-evidence audit methodology                                                                                                                                                                                                                                                                                                                                 |
| Skill | `/author`                     | Adding, defining, or creating specs, decisions, or nodes                                                                                                                                                                                                                                                                                                        |
| Skill | `/bootstrap`                  | Setting up a new spec tree or when /author detects an empty spx/ directory                                                                                                                                                                                                                                                                                      |
| Skill | `/commit-changes`             | Committing changes or when user says "commit"                                                                                                                                                                                                                                                                                                                   |
| Skill | `/contextualize`              | Asking about status, progress, or what exists in the spec tree                                                                                                                                                                                                                                                                                                  |
| Skill | `/decompose`                  | Breaking down, splitting, scoping, composing, or structuring spec tree nodes                                                                                                                                                                                                                                                                                    |
| Skill | `/diagnose`                   | Diagnosing the health of a spec-tree or spx environment, when checking whether the SessionStart hook fired for the current session, or when troubleshooting a missing session identity, worktree claim, or unreachable spx CLI                                                                                                                                  |
| Skill | `/handoff`                    | ALWAYS invoke to close active spec-tree work or a merge lifecycle closeout — archive claimed sessions, decide session-file creation, prepare continuation context, and produce operator-useful closeout — only once its goal is met with no continuation remaining, the user halted work, context is exhausted, or an external blocker prevents the next action |
| Skill | `/init-worktrees`             | Setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while pushing every local ref to the remote and carrying a prior checkout's gitignored state across                                                                                   |
| Skill | `/inspect-github-actions`     | The user asks about CI failures, workflow logs, GitHub Actions status, pipeline issues, or troubleshooting failed builds                                                                                                                                                                                                                                        |
| Skill | `/interview`                  | Requirements interviews, draft approval, or unresolved scope/design questions while creating or modifying an artifact (spec, ADR, PDR, test, code, doc)                                                                                                                                                                                                         |
| Skill | `/issue`                      | Filing a follow-up into a spec-tree dependency's own session queue — for observations about the spec-tree plugin, the spx CLI, or another spec-tree dependency needing a change                                                                                                                                                                                 |
| Skill | `/manage-github-pr`           | The user asks to open or manage a GitHub pull request, or runs /manage-github-pr                                                                                                                                                                                                                                                                                |
| Skill | `/manage-pr`                  | Managing, waiting on, or continuing an open pull request lifecycle after a PR exists                                                                                                                                                                                                                                                                            |
| Skill | `/merge`                      | The user asks to ship, integrate, or merge a changeset into the default branch on origin, or runs /merge                                                                                                                                                                                                                                                        |
| Skill | `/merging-standards`          | Shared merge-lifecycle invariants and routing for detailed preflight, branch, review, authority-gate, transport, and closeout policy                                                                                                                                                                                                                            |
| Skill | `/open-pr`                    | PR opening protocol for VERIFICATION_READINESS, branch push, ready PR creation, and the first management pass                                                                                                                                                                                                                                                   |
| Skill | `/pickup`                     | Resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context                                                                                                                                                                                                                                |
| Skill | `/project-run-journal`        | Verification run-journal projection methodology loaded by audit and review skills when building spx journal events, computing rollups, or rendering verdict surfaces                                                                                                                                                                                            |
| Skill | `/refactor`                   | Moving nodes, re-scoping content, or extracting shared enablers                                                                                                                                                                                                                                                                                                 |
| Skill | `/refocus`                    | Running ad hoc commands, writing debug scripts, or writing code without a spec                                                                                                                                                                                                                                                                                  |
| Skill | `/review-changes`             | Reviewing working changes on a branch against a base ref                                                                                                                                                                                                                                                                                                        |
| Skill | `/scope-changeset`            | Canonical git-derived changeset primitives loaded by verification and lifecycle skills instead of re-implementing branch, base-ref, commit-identity, slug, or diff-scope derivation                                                                                                                                                                             |
| Skill | `/slice`                      | Selecting the next executable slice to implement or deciding which spec-tree nodes /apply should build next from an implementation plan                                                                                                                                                                                                                         |
| Skill | `/sync-base`                  | ALWAYS invoke this skill to bring a branch behind its base current — before reading product truth, before verifying, and before every merge push                                                                                                                                                                                                                |
| Skill | `/task-tracking-standards`    | Runtime task-tracking standards for skills that schedule heartbeats or timers                                                                                                                                                                                                                                                                                   |
| Skill | `/test`                       | Writing or repairing deterministic tests for a spec assertion, selecting a decision Testing rule's assertion type, or when learning the testing approach                                                                                                                                                                                                        |
| Skill | `/test-evidence-standards`    | Test-evidence seam, case-provenance, and oracle-independence standards enforced across test authoring and auditing                                                                                                                                                                                                                                              |
| Skill | `/understand`                 | The live SPEC_TREE_FOUNDATION marker is absent before direct filesystem access under spx/ or before reading, searching, listing, or changing source or test files                                                                                                                                                                                               |
| Skill | `/update-instruction-block`   | Manually regenerating, refreshing, or scaffolding a product's root CLAUDE.md and AGENTS.md managed Spec Tree instruction surface from the installed spec-tree template, or reconciling a `shared` region that differs between the two files                                                                                                                     |
| Skill | `/verify`                     | Selecting or establishing evidence for spec assertions, decision verification rules, or a spec-tree scope                                                                                                                                                                                                                                                       |
| Skill | `/wait-for-load`              | Starting a resource-intensive local command or when host load is high                                                                                                                                                                                                                                                                                           |
| Agent | `adr-auditor`                 | Auditing ADR evidence quality after writing an ADR or before implementing from it                                                                                                                                                                                                                                                                               |
| Agent | `changes-reviewer`            | Reviewing working changes against a base ref                                                                                                                                                                                                                                                                                                                    |
| Agent | `changeset-coherence-auditor` | Deciding whether an exact committed changeset is one coherent review unit or requires a dependency-ordered split                                                                                                                                                                                                                                                |
| Agent | `eval-evidence-auditor`       | Auditing eval evidence quality against spec assertions after writing evals for a spec node or before relying on eval evidence                                                                                                                                                                                                                                   |
| Agent | `implementation-auditor`      | ALWAYS invoke for implementation audits over code, tests, and architecture in a changeset scope after implementation changes land or before merging the changeset                                                                                                                                                                                               |
| Agent | `instruction-block-updater`   | Applying spec-tree template drift to a product's root CLAUDE.md and AGENTS.md managed instruction block in the background — it regenerates a stale or absent instruction block from the installed template without user interaction                                                                                                                             |
| Agent | `pdr-auditor`                 | Auditing PDR evidence quality after writing a PDR or before implementing outcomes governed by the PDR                                                                                                                                                                                                                                                           |
| Agent | `spec-auditor`                | Auditing a spec node's assertion quality after writing an enabler or outcome node spec or before closing it                                                                                                                                                                                                                                                     |
| Agent | `test-evidence-auditor`       | Auditing test evidence quality against spec assertions after writing tests for a spec node or before closing an outcome                                                                                                                                                                                                                                         |

### typescript

TypeScript engineering: /test-typescript, /code-typescript, /audit-typescript-code, /audit-typescript-tests, /audit-typescript-architecture, /architect-typescript, typescript-simplifier agent

| Type  | Name                                 | Purpose                                                                                                                       |
| ----- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/architect-typescript`              | Writing ADRs for TypeScript                                                                                                   |
| Skill | `/audit-typescript-architecture`     | TypeScript-specific architecture audit                                                                                        |
| Skill | `/audit-typescript-code`             | TypeScript implementation-code audit methodology                                                                              |
| Skill | `/audit-typescript-tests`            | TypeScript test-evidence audit methodology                                                                                    |
| Skill | `/code-typescript`                   | Writing or fixing implementation code for TypeScript                                                                          |
| Skill | `/test-typescript`                   | Writing or fixing tests for TypeScript                                                                                        |
| Skill | `/typescript-architecture-standards` | TypeScript ADR conventions enforced across architect and auditor skills                                                       |
| Skill | `/typescript-standards`              | TypeScript code standards enforced across all skills                                                                          |
| Skill | `/typescript-test-standards`         | TypeScript testing standards enforced across all skills                                                                       |
| Agent | `typescript-simplifier`              | Simplifying recently modified TypeScript code while preserving behavior, type safety, testability, and verified test coverage |

### work

Work deliverables: /draw-excalidraw (Excalidraw diagrams), /sanitize-powerpoint (PowerPoint deck cleanup)

| Type  | Name                   | Purpose                                                                                                                                                                               |
| ----- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/draw-excalidraw`     | Creating Excalidraw diagrams, visualizing workflows, architectures, or concepts                                                                                                       |
| Skill | `/sanitize-powerpoint` | Sanitizing, cleaning up, auditing, or aligning a PowerPoint (.pptx) deck — slide-master and layout structure, layout type attributes, stray fonts, non-theme colors, or layout naming |

<!-- END PLUGIN CATALOG -->

## Using with other AI agents

Skills are distributed as standalone repositories, compatible with any agent that supports the [Agent Skills](https://vercel.com/docs/agent-resources/skills) open standard.

| Repository                                             | Purpose                                                 | Install                                |
| ------------------------------------------------------ | ------------------------------------------------------- | -------------------------------------- |
| [spec-tree](https://github.com/outcomeeng/spec-tree)   | Spec Tree methodology skills for Outcome Engineering    | `npx skills add outcomeeng/spec-tree`  |
| [python](https://github.com/outcomeeng/python)         | Python engineering skills                               | `npx skills add outcomeeng/python`     |
| [typescript](https://github.com/outcomeeng/typescript) | TypeScript engineering skills                           | `npx skills add outcomeeng/typescript` |
| [foundation](https://github.com/outcomeeng/foundation) | Foundation skills (prose, plugin development, frontend) | `npx skills add outcomeeng/foundation` |

## Documentation

### Claude Code

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)

### Codex

- [Codex](https://openai.com/codex)
- [Codex Overview](https://platform.openai.com/docs/codex/overview)
- `codex plugin --help`
- `codex plugin marketplace --help`

## Credits

The `instructions` plugin's meta-skills are derived from [TÂCHES Claude Code Resources](https://github.com/glittercowboy/taches-cc-resources?tab=readme-ov-file#skills). The `/handoff` and `/pickup` spec-tree commands are based on `/whats-next` from the same project.

## License

MIT
