# Outcome Engineering Plugin Marketplace

A combined Codex and Claude Code plugin marketplace for [Outcome Engineering](https://outcome.engineering) — the product engineering paradigm where a durable map of your product, maintained as a Spec Tree, serves as the authoritative source of truth for all implementation.

This repository publishes two plugin surfaces from the same source tree:

- `.claude-plugin` packages for Claude Code plugins, commands, and agents
- `.codex-plugin` packages for Codex skill bundles

`AGENTS.md` is a symlink to [`CLAUDE.md`](CLAUDE.md), so Codex and Claude Code read the same repo-level instructions.

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
claude plugin install develop@outcomeeng
```

#### Codex

After adding the marketplace, enable only the plugins a product needs in that repo's committed `.codex/config.toml`:

```toml
[plugins."spec-tree@outcomeeng"]
enabled = true

[plugins."develop@outcomeeng"]
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

From this checkout, `just push-marketplace` wraps the Codex upgrade with cache
path preservation so active sessions with stale skill paths keep resolving for
seven days.

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
| Added / deleted / renamed `commands/<slug>.md` or `agents/<slug>.md`                               | `minor` |
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

The pre-commit hook runs `build-skills` automatically, and `just check`'s `dist-diff` step (`git diff --exit-code dist`) fails when `dist/` is out of sync with `src/`, so each `src/plugins/` change and its regenerated `dist/` commit together. Never hand-edit `dist/`.

## Plugins

Skills are available in both Claude Code and Codex. Commands and agents are Claude Code-only. Every skill, agent, and command across every plugin is listed in the auto-generated catalog below — sourced from `.claude-plugin/marketplace.json` and the YAML frontmatter of each plugin's `SKILL.md`, `agents/*.md`, and `commands/*.md`. Run `just docs` to regenerate after touching any of those files; `just check` enforces freshness.

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

### develop

Plugin development: /create-skills, /create-subagents

| Type  | Name                      | Purpose                                                                                                                                  |
| ----- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/agent-prompt-standards` | Agent prompt writing conventions enforced across all creator and auditor skills                                                          |
| Skill | `/audit-skills`           | SKILL.md audit methodology preloaded by the skill-auditor agent                                                                          |
| Skill | `/audit-subagents`        | Subagent-configuration audit methodology preloaded by the subagent-auditor agent                                                         |
| Skill | `/create-skills`          | Creating, editing, or improving SKILL.md files                                                                                           |
| Skill | `/create-subagents`       | Creating, editing, or configuring subagents                                                                                              |
| Skill | `/skill-standards`        | Skill authoring standards enforced across all creating and auditing skills                                                               |
| Agent | `skill-auditor`           | Auditing, reviewing, or evaluating SKILL.md files for best practices compliance, or when the user asks to audit a skill                  |
| Agent | `subagent-auditor`        | Auditing, reviewing, or evaluating subagent configuration files for best practices compliance, or when the user asks to audit a subagent |

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

### prose

Prose craft for external prose (/write-prose, /audit-prose) and internal team docs (/write-internal-docs, /audit-internal-docs)

| Type  | Name                      | Purpose                                                                                                                                                                                                                                                  |
| ----- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/audit-internal-docs`    | Auditing or reviewing internal team documents for cleanup                                                                                                                                                                                                |
| Skill | `/audit-prose`            | Auditing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                  |
| Skill | `/internal-doc-standards` | Catalog of anti-patterns and positive patterns for internal team documents (Notion pages, runbooks, scorecards, hiring rubrics, internal policies, decision records, design specs, competency models)                                                    |
| Skill | `/prose-standards`        | Prose anti-patterns enforced across all skills                                                                                                                                                                                                           |
| Skill | `/write-internal-docs`    | Writing or editing internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, decision records, design specs, competency models, onboarding guides, status pages, internal wiki content |
| Skill | `/write-prose`            | Writing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                   |

### python

Python engineering: /test-python, /code-python, /audit-python, /architect-python, /audit-python-architecture

| Type  | Name                             | Purpose                                                                                                                                                                |
| ----- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/architect-python`              | Writing ADRs for Python                                                                                                                                                |
| Skill | `/audit-python`                  | Python implementation-code audit methodology — design flaws and ADR compliance — composed by a generic auditor agent for the Python files in scope                     |
| Skill | `/audit-python-architecture`     | Python-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the Python concerns in scope |
| Skill | `/audit-python-tests`            | Python test-evidence audit methodology composed by a dispatched auditor agent for the Python tests in scope                                                            |
| Skill | `/code-python`                   | Writing or fixing implementation code for Python                                                                                                                       |
| Skill | `/python-architecture-standards` | Python ADR conventions enforced across architect and auditor skills                                                                                                    |
| Skill | `/python-standards`              | Python code standards enforced across all skills                                                                                                                       |
| Skill | `/python-test-standards`         | Python testing standards enforced across all skills                                                                                                                    |
| Skill | `/test-python`                   | Writing or fixing tests for Python                                                                                                                                     |

### rust

Rust engineering: /test-rust, /code-rust, /audit-rust, /architect-rust, /audit-rust-architecture

| Type  | Name                           | Purpose                                                                                                                                                               |
| ----- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/architect-rust`              | Writing ADRs for Rust                                                                                                                                                 |
| Skill | `/audit-rust`                  | Rust implementation-code audit methodology — design flaws, ADR compliance, and unsafe/FFI soundness — composed by a generic auditor agent for the Rust files in scope |
| Skill | `/audit-rust-architecture`     | Rust-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the Rust concerns in scope    |
| Skill | `/audit-rust-tests`            | Rust test-evidence audit methodology composed by a dispatched auditor agent for the Rust tests in scope                                                               |
| Skill | `/code-rust`                   | Writing or fixing implementation code for Rust                                                                                                                        |
| Skill | `/rust-architecture-standards` | Rust ADR conventions enforced across architect and auditor skills                                                                                                     |
| Skill | `/rust-standards`              | Rust code standards enforced across all skills                                                                                                                        |
| Skill | `/rust-test-standards`         | Rust test standards enforced across all skills                                                                                                                        |
| Skill | `/test-rust`                   | Writing or fixing tests for Rust                                                                                                                                      |
| Agent | `rust-simplifier`              | Simplifies Rust code for clarity and maintainability                                                                                                                  |

### spec-tree

Spec Tree: /understand, /contextualize, /bootstrap, /author, /decompose, /refactor, /align, /interview, /test, /audit-tests, /audit-adr, /audit-pdr, /apply, /commit-changes, /handoff, /pickup, /refocus, /diagnose

| Type  | Name                       | Purpose                                                                                                                                                                                                                                                                                              |
| ----- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/align`                   | Reviewing, auditing, or checking spec file conformance                                                                                                                                                                                                                                               |
| Skill | `/apply`                   | Implementing any spec-tree work item                                                                                                                                                                                                                                                                 |
| Skill | `/audit`                   | Generic end-to-end code-scope audit orchestration preloaded by audit agents                                                                                                                                                                                                                          |
| Skill | `/audit-adr`               | ADR audit methodology preloaded by the adr-auditor agent                                                                                                                                                                                                                                             |
| Skill | `/audit-pdr`               | PDR audit methodology preloaded by the pdr-auditor agent                                                                                                                                                                                                                                             |
| Skill | `/audit-specs`             | Spec-node audit methodology preloaded by the spec-auditor agent                                                                                                                                                                                                                                      |
| Skill | `/audit-tests`             | Test-evidence audit methodology preloaded by the test-evidence-auditor agent                                                                                                                                                                                                                         |
| Skill | `/author`                  | Adding, defining, or creating specs, decisions, or nodes                                                                                                                                                                                                                                             |
| Skill | `/bootstrap`               | Setting up a new spec tree or when /author detects an empty spx/ directory                                                                                                                                                                                                                           |
| Skill | `/commit-changes`          | Committing changes or when user says "commit"                                                                                                                                                                                                                                                        |
| Skill | `/contextualize`           | Asking about status, progress, or what exists in the spec tree                                                                                                                                                                                                                                       |
| Skill | `/decompose`               | Breaking down, splitting, scoping, composing, or structuring spec tree nodes                                                                                                                                                                                                                         |
| Skill | `/diagnose`                | Diagnosing the health of a spec-tree or spx environment, when checking whether the SessionStart hook fired for the current session, or when troubleshooting a missing session identity, worktree claim, or unreachable spx CLI                                                                       |
| Skill | `/handoff`                 | ALWAYS invoke to close a claimed spec-tree session — archive it, decide session-file creation, prepare continuation context — only once its goal is met with no continuation remaining or continuation by Claude is impossible (context exhausted, user halted, external blocker)                    |
| Skill | `/init-worktrees`          | Setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while pushing every local ref to the remote and carrying a prior checkout's gitignored state across                        |
| Skill | `/inspect-github-actions`  | The user asks about CI failures, workflow logs, GitHub Actions status, pipeline issues, or troubleshooting failed builds                                                                                                                                                                             |
| Skill | `/interview`               | Asking the user anything while creating or modifying any artifact (spec, ADR, PDR, test, code, doc)                                                                                                                                                                                                  |
| Skill | `/manage-github-pr`        | The user asks to open or manage a GitHub pull request, or runs /manage-github-pr                                                                                                                                                                                                                     |
| Skill | `/manage-pr`               | Open-PR management protocol for review and check inspection, follow-up pushes, merge gates, and post-merge cleanup                                                                                                                                                                                   |
| Skill | `/manage-thread-store`     | Persisting or retrieving branch-scoped verification records                                                                                                                                                                                                                                          |
| Skill | `/merge`                   | The user asks to ship, integrate, or merge a changeset into the default branch on origin, or runs /merge                                                                                                                                                                                             |
| Skill | `/merging-standards`       | Shared vocabulary for the merge lifecycle — pre-flight predicates, branch topology gate, push command, the three authority gates (review / merge / production readiness), review classification, integration review surfaces, action tokens, delivered-value boundary, and repo-local overlay topics |
| Skill | `/open-pr`                 | PR opening protocol for REVIEW_READINESS, branch push, ready PR creation, and first management pass                                                                                                                                                                                                  |
| Skill | `/pickup`                  | Resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context                                                                                                                                                                     |
| Skill | `/plan-slice`              | Selecting the next executable slice to implement, planning the next delivery increment, or deciding which spec-tree nodes /apply should build next from an implementation plan                                                                                                                       |
| Skill | `/project-run-journal`     | Verification run-journal projection methodology loaded by audit and review skills when building spx journal events, computing rollups, or rendering verdict surfaces                                                                                                                                 |
| Skill | `/refactor`                | Moving nodes, re-scoping content, or extracting shared enablers                                                                                                                                                                                                                                      |
| Skill | `/refocus`                 | Running ad hoc commands, writing debug scripts, or writing code without a spec                                                                                                                                                                                                                       |
| Skill | `/review-changes`          | Reviewing working changes on a branch against a base ref                                                                                                                                                                                                                                             |
| Skill | `/review-pr`               | Reviewing a pull request or when the user asks to invoke the PR review skill                                                                                                                                                                                                                         |
| Skill | `/scope-changeset`         | Deriving a changeset's base ref, branch slug, branch identity, or merge-base diff scope from git                                                                                                                                                                                                     |
| Skill | `/sync-base`               | ALWAYS invoke this skill to bring a branch behind its base current — before reading product truth, before verifying, and before every merge push                                                                                                                                                     |
| Skill | `/task-tracking-standards` | Runtime task-tracking standards for skills that schedule heartbeats or timers                                                                                                                                                                                                                        |
| Skill | `/test`                    | Writing tests or when learning the testing approach                                                                                                                                                                                                                                                  |
| Skill | `/understand`              | Any spec-tree work to load methodology                                                                                                                                                                                                                                                               |
| Skill | `/update-spx`              | Manually regenerating, refreshing, or scaffolding a product's two spx-level guide files (spx/CLAUDE.md and spx/AGENTS.md) from the installed spec-tree template                                                                                                                                      |
| Agent | `adr-auditor`              | Auditing ADR evidence quality after writing an ADR or before implementing from it                                                                                                                                                                                                                    |
| Agent | `applier`                  | Running the full spec-tree 8-step flow with three audit gates after the user passes --agent to /apply                                                                                                                                                                                                |
| Agent | `audit-orchestrator`       | ALWAYS invoke for a local audit run that carries findings across commits through the audit journal run set                                                                                                                                                                                           |
| Agent | `auditor`                  | Running a one-off audit over a code scope                                                                                                                                                                                                                                                            |
| Agent | `changes-reviewer`         | Reviewing working changes against a base ref                                                                                                                                                                                                                                                         |
| Agent | `pdr-auditor`              | Auditing PDR evidence quality after writing a PDR or before implementing outcomes governed by the PDR                                                                                                                                                                                                |
| Agent | `pr-review-orchestrator`   | Running a CI-side stateful pull request review — runs the PR review and audit over the PR diff, derives resolved and reopened from the pull-request audit journal run set, and posts one fresh combined comment that supersedes the prior display while keeping the latest review prose              |
| Agent | `pr-reviewer`              | Reviewing a pull request                                                                                                                                                                                                                                                                             |
| Agent | `spec-auditor`             | Auditing a spec node's assertion quality after writing an enabler or outcome node spec or before closing it                                                                                                                                                                                          |
| Agent | `spx-updater`              | Applying spec-tree template drift to a product's spx/CLAUDE.md and spx/AGENTS.md guide files in the background — it runs the /update-spx skill autonomously to regenerate stale guides from the installed template                                                                                   |
| Agent | `test-evidence-auditor`    | Auditing test evidence quality against spec assertions after writing tests for a spec node or before closing an outcome                                                                                                                                                                              |

### typescript

TypeScript engineering: /test-typescript, /code-typescript, /audit-typescript, /architect-typescript, /audit-typescript-architecture, typescript-simplifier agent

| Type  | Name                                 | Purpose                                                                                                                                                                        |
| ----- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Skill | `/architect-typescript`              | Writing ADRs for TypeScript                                                                                                                                                    |
| Skill | `/audit-typescript`                  | TypeScript implementation-code audit methodology — design flaws and ADR compliance — composed by a generic auditor agent for the TypeScript files in scope                     |
| Skill | `/audit-typescript-architecture`     | TypeScript-specific ADR architecture audit — dependency injection, no-mocking, level accuracy — composed by the generic adr-auditor agent for the TypeScript concerns in scope |
| Skill | `/audit-typescript-tests`            | TypeScript test-evidence audit methodology composed by a dispatched auditor agent for the TypeScript tests in scope                                                            |
| Skill | `/code-typescript`                   | Writing or fixing implementation code for TypeScript                                                                                                                           |
| Skill | `/test-typescript`                   | Writing or fixing tests for TypeScript                                                                                                                                         |
| Skill | `/typescript-architecture-standards` | TypeScript ADR conventions enforced across architect and auditor skills                                                                                                        |
| Skill | `/typescript-standards`              | TypeScript code standards enforced across all skills                                                                                                                           |
| Skill | `/typescript-test-standards`         | TypeScript testing standards enforced across all skills                                                                                                                        |
| Agent | `typescript-simplifier`              | Simplifies TypeScript code for clarity and maintainability                                                                                                                     |

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

The `develop` plugin's meta-skills are derived from [TÂCHES Claude Code Resources](https://github.com/glittercowboy/taches-cc-resources?tab=readme-ov-file#skills). The `/handoff` and `/pickup` spec-tree commands are based on `/whats-next` from the same project.

## License

MIT
