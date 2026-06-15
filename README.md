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
> /commit                          # commit with Conventional Commits
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

Plugin development: /creating-skills, /creating-commands, /creating-subagents

| Type  | Name                           | Purpose                                                                                                                                  |
| ----- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/auditing-commands`           | Auditing, reviewing, or evaluating slash command .md files                                                                               |
| Skill | `/auditing-skills`             | Auditing, reviewing, or evaluating SKILL.md files                                                                                        |
| Skill | `/auditing-subagents`          | Auditing, reviewing, or evaluating subagent configuration files                                                                          |
| Skill | `/creating-commands`           | Creating or editing slash commands                                                                                                       |
| Skill | `/creating-skills`             | Creating, editing, or improving SKILL.md files                                                                                           |
| Skill | `/creating-subagents`          | Creating, editing, or configuring subagents                                                                                              |
| Skill | `/standardizing-agent-prompts` | Agent prompt writing conventions enforced across all creator and auditor skills                                                          |
| Skill | `/standardizing-skills`        | Skill authoring standards enforced across all creating and auditing skills                                                               |
| Agent | `command-auditor`              | Auditing, reviewing, or evaluating slash command .md files for best practices compliance, or when the user asks to audit a command       |
| Agent | `skill-auditor`                | Auditing, reviewing, or evaluating SKILL.md files for best practices compliance, or when the user asks to audit a skill                  |
| Agent | `subagent-auditor`             | Auditing, reviewing, or evaluating subagent configuration files for best practices compliance, or when the user asks to audit a subagent |

### frontend

Frontend design: /designing-frontend skill

| Type  | Name                  | Purpose                                                    |
| ----- | --------------------- | ---------------------------------------------------------- |
| Skill | `/designing-frontend` | Designing or building web components, pages, or dashboards |

### hdl

HDL engineering: /reviewing-vhdl, /reviewing-systemverilog (idiomatic VHDL-2008 and SystemVerilog IEEE 1800-2017 review)

| Type  | Name                       | Purpose                                                                                          |
| ----- | -------------------------- | ------------------------------------------------------------------------------------------------ |
| Skill | `/reviewing-systemverilog` | Reviewing SystemVerilog or Verilog code for idiomatic style, synthesizability, or best practices |
| Skill | `/reviewing-vhdl`          | Reviewing VHDL code for idiomatic style, synthesizability, or best practices                     |

### prose

Prose craft for external prose (/writing-prose, /auditing-prose) and internal team docs (/writing-internal-docs, /auditing-internal-docs)

| Type  | Name                           | Purpose                                                                                                                                                                                                                                                  |
| ----- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/auditing-internal-docs`      | Auditing or reviewing internal team documents for cleanup                                                                                                                                                                                                |
| Skill | `/auditing-prose`              | Auditing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                  |
| Skill | `/standardizing-internal-docs` | Catalog of anti-patterns and positive patterns for internal team documents (Notion pages, runbooks, scorecards, hiring rubrics, internal policies, decision records, design specs, competency models)                                                    |
| Skill | `/standardizing-prose`         | Prose anti-patterns enforced across all skills                                                                                                                                                                                                           |
| Skill | `/writing-internal-docs`       | Writing or editing internal team documents that live in a workspace: Notion pages, runbooks, hiring rubrics and scorecards, internal policies, decision records, design specs, competency models, onboarding guides, status pages, internal wiki content |
| Skill | `/writing-prose`               | Writing reader-facing documents such as public docs, web pages, and product messages for outside readers like developers and customers                                                                                                                   |

### python

Python engineering: /testing-python, /coding-python, /auditing-python, /architecting-python, /auditing-python-architecture

| Type  | Name                                 | Purpose                                                                                                                                 |
| ----- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/architecting-python`               | Writing ADRs for Python                                                                                                                 |
| Skill | `/auditing-python`                   | Asked by the user to invoke the Python code audit skill                                                                                 |
| Skill | `/auditing-python-architecture`      | Asked by the user to invoke the Python architecture audit skill                                                                         |
| Skill | `/auditing-python-tests`             | The user asks to audit Python test evidence, review Python tests for spec-tree evidence quality, or evaluate Python test infrastructure |
| Skill | `/coding-python`                     | Writing or fixing implementation code for Python                                                                                        |
| Skill | `/standardizing-python`              | Python code standards enforced across all skills                                                                                        |
| Skill | `/standardizing-python-architecture` | Python ADR conventions enforced across architect and auditor skills                                                                     |
| Skill | `/standardizing-python-tests`        | Python testing standards enforced across all skills                                                                                     |
| Skill | `/testing-python`                    | Writing or fixing tests for Python                                                                                                      |
| Agent | `python-architecture-auditor`        | Audit Python ADRs for conventions, testability, and voice                                                                               |
| Agent | `python-code-auditor`                | Audit Python code for design flaws and ADR compliance                                                                                   |
| Agent | `python-test-auditor`                | Audit Python test code for evidence quality using the 4-property model                                                                  |

### rust

Rust engineering: /testing-rust, /coding-rust, /auditing-rust, /architecting-rust, /auditing-rust-architecture, rust-unsafe-auditor agent

| Type  | Name                               | Purpose                                                               |
| ----- | ---------------------------------- | --------------------------------------------------------------------- |
| Skill | `/architecting-rust`               | Writing ADRs for Rust                                                 |
| Skill | `/auditing-rust`                   | Asked by the user to invoke the Rust code audit skill                 |
| Skill | `/auditing-rust-architecture`      | Asked by the user to invoke the Rust architecture audit skill         |
| Skill | `/auditing-rust-tests`             | Asked by the user to invoke the Rust test audit skill                 |
| Skill | `/coding-rust`                     | Writing or fixing implementation code for Rust                        |
| Skill | `/standardizing-rust`              | Rust code standards enforced across all skills                        |
| Skill | `/standardizing-rust-architecture` | Rust ADR conventions enforced across architect and auditor skills     |
| Skill | `/standardizing-rust-tests`        | Rust test standards enforced across all skills                        |
| Skill | `/testing-rust`                    | Writing or fixing tests for Rust                                      |
| Agent | `rust-architecture-auditor`        | Audit Rust ADRs for conventions, testability, and voice               |
| Agent | `rust-code-auditor`                | Audit Rust code for design flaws and ADR compliance                   |
| Agent | `rust-simplifier`                  | Simplifies Rust code for clarity and maintainability                  |
| Agent | `rust-test-auditor`                | Audit Rust test code for evidence quality using the 4-property model  |
| Agent | `rust-unsafe-auditor`              | Specialized soundness audit for Rust unsafe blocks and FFI boundaries |

### spec-tree

Spec Tree: /understanding, /contextualizing, /bootstrapping, /authoring, /decomposing, /refactoring, /aligning, /interviewing, /testing, /auditing-tests, /audit-adr, /audit-pdr, /applying, /committing-changes, /bootstrap, /author, /commit, /handoff, /pickup, /rtfm, /clarify

| Type    | Name                     | Purpose                                                                                                                                                                                                                                                                                                                                      |
| ------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill   | `/aligning`              | Reviewing, auditing, or checking spec file conformance                                                                                                                                                                                                                                                                                       |
| Skill   | `/applying`              | Implementing any spec-tree work item                                                                                                                                                                                                                                                                                                         |
| Skill   | `/audit-adr`             | ALWAYS use when auditing an ADR or after making changes to an ADR                                                                                                                                                                                                                                                                            |
| Skill   | `/audit-pdr`             | ALWAYS use when auditing a PDR or after making changes to a PDR                                                                                                                                                                                                                                                                              |
| Skill   | `/auditing`              | Auditing a code scope end-to-end — a diff, a branch, or a commit — partitioning by language and emitting one structured verdict                                                                                                                                                                                                              |
| Skill   | `/auditing-tests`        | Asked by the user to invoke the test evidence audit skill                                                                                                                                                                                                                                                                                    |
| Skill   | `/authoring`             | Adding, defining, or creating specs, decisions, or nodes                                                                                                                                                                                                                                                                                     |
| Skill   | `/bootstrapping`         | Setting up a new spec tree or when /authoring detects an empty spx/ directory                                                                                                                                                                                                                                                                |
| Skill   | `/changeset-scope`       | Deriving a changeset's base ref, branch slug, branch identity, or merge-base diff scope from git                                                                                                                                                                                                                                             |
| Skill   | `/committing-changes`    | Committing changes or when user says "commit"                                                                                                                                                                                                                                                                                                |
| Skill   | `/contextualizing`       | Asking about status, progress, or what exists in the spec tree                                                                                                                                                                                                                                                                               |
| Skill   | `/decomposing`           | Breaking down, splitting, scoping, composing, or structuring spec tree nodes                                                                                                                                                                                                                                                                 |
| Skill   | `/github-actions`        | The user asks about CI failures, workflow logs, GitHub Actions status, pipeline issues, or troubleshooting failed builds                                                                                                                                                                                                                     |
| Skill   | `/github-pr`             | The user asks to open or manage a GitHub pull request, or runs /github-pr                                                                                                                                                                                                                                                                    |
| Skill   | `/handoff`               | ALWAYS invoke to close an in-scope spec-tree session — archive it, decide session-file creation, prepare continuation context — only once its goal is met with no continuation remaining or continuation by Claude is impossible (context exhausted, user halted, external blocker)                                                          |
| Skill   | `/init-worktrees`        | Setting up a repository's git worktree layout — classifying a checkout as a single tree, a bare-repo worktree pool, or non-compliant, and provisioning the bare-repo pool while carrying a prior checkout's .spx across                                                                                                                      |
| Skill   | `/interviewing`          | Asking the user anything while creating or modifying any artifact (spec, ADR, PDR, test, code, doc)                                                                                                                                                                                                                                          |
| Skill   | `/managing-pr`           | Open-PR management protocol for review and check inspection, follow-up pushes, merge gates, and post-merge cleanup                                                                                                                                                                                                                           |
| Skill   | `/merge`                 | The user asks to ship, integrate, or merge a changeset into trunk, or runs /merge                                                                                                                                                                                                                                                            |
| Skill   | `/opening-pr`            | PR opening protocol for REVIEW_READINESS, branch push, ready PR creation, and first heartbeat                                                                                                                                                                                                                                                |
| Skill   | `/pickup`                | Resuming prior spec-tree work, loading a handoff session, claiming queued session work, or continuing from another saved context                                                                                                                                                                                                             |
| Skill   | `/refactoring`           | Moving nodes, re-scoping content, or extracting shared enablers                                                                                                                                                                                                                                                                              |
| Skill   | `/refocusing`            | Running ad hoc commands, writing debug scripts, or writing code without a spec                                                                                                                                                                                                                                                               |
| Skill   | `/reviewing-changes`     | Reviewing working changes on a branch against a base ref                                                                                                                                                                                                                                                                                     |
| Skill   | `/reviewing-pr`          | Asked by the user to invoke the PR review skill                                                                                                                                                                                                                                                                                              |
| Skill   | `/standardizing-merging` | Shared vocabulary for the PR flow — pre-flight predicates, branch topology gate, push command, the three PR-authority gates (review / merge / production readiness), review classification, three review surfaces, action tokens, and repo-local overlay topics                                                                              |
| Skill   | `/testing`               | Writing tests or when learning the testing approach                                                                                                                                                                                                                                                                                          |
| Skill   | `/thread-store`          | Persisting or retrieving branch-scoped verification records                                                                                                                                                                                                                                                                                  |
| Skill   | `/tracking-tasks`        | Runtime task-tracking standards for skills that schedule heartbeats or timers                                                                                                                                                                                                                                                                |
| Skill   | `/understanding`         | Any spec-tree work to load methodology                                                                                                                                                                                                                                                                                                       |
| Skill   | `/update-spx`            | Updating, refreshing, or scaffolding a product's spx/CLAUDE.md from the installed spec-tree template                                                                                                                                                                                                                                         |
| Agent   | `adr-auditor`            | Audit ADR evidence quality                                                                                                                                                                                                                                                                                                                   |
| Agent   | `applier`                | Autonomous TDD agent. Runs the full spec-tree 8-step flow on a node with three audit gates                                                                                                                                                                                                                                                   |
| Agent   | `audit-orchestrator`     | ALWAYS invoke for a stateful local audit run that carries findings across commits                                                                                                                                                                                                                                                            |
| Agent   | `auditor`                | Running a one-off audit over a code scope                                                                                                                                                                                                                                                                                                    |
| Agent   | `changes-reviewer`       | Reviewing working changes against a base ref                                                                                                                                                                                                                                                                                                 |
| Agent   | `pdr-auditor`            | Audit PDR evidence quality                                                                                                                                                                                                                                                                                                                   |
| Agent   | `pr-review-orchestrator` | Running a CI-side stateful pull request review — runs the PR review and the deterministic six-phase audit over the PR diff, ingests the prior audit verdict from the PR comment thread, derives resolved and reopened against it, and posts one fresh combined comment that supersedes the prior audit while keeping the latest review prose |
| Agent   | `pr-reviewer`            | Reviewing a pull request                                                                                                                                                                                                                                                                                                                     |
| Agent   | `spx-updater`            | Applying spec-tree template drift to a product's spx/CLAUDE.md in the background — it runs the /update-spx skill autonomously to re-render a stale guide from the installed template                                                                                                                                                         |
| Agent   | `test-evidence-auditor`  | Audit test evidence quality against spec assertions                                                                                                                                                                                                                                                                                          |
| Command | `/apply`                 | Run the spec-tree TDD flow on a subtree or discover work from spx/EXCLUDE                                                                                                                                                                                                                                                                    |
| Command | `/author`                | Author a spec tree artifact (product, ADR, PDR, enabler, outcome)                                                                                                                                                                                                                                                                            |
| Command | `/bootstrap`             | Set up a new spec tree for this product                                                                                                                                                                                                                                                                                                      |
| Command | `/clarify`               | Gather requirements through questioning before executing a task                                                                                                                                                                                                                                                                              |
| Command | `/commit`                | Commit following Conventional Commits                                                                                                                                                                                                                                                                                                        |
| Command | `/review-changes`        | Run reviewing-changes against the current branch's diff                                                                                                                                                                                                                                                                                      |
| Command | `/rtfm`                  | Stop ad hoc work and follow the spec-tree methodology                                                                                                                                                                                                                                                                                        |

### typescript

TypeScript engineering: /testing-typescript, /coding-typescript, /auditing-typescript, /architecting-typescript, /auditing-typescript-architecture, typescript-simplifier agent

| Type  | Name                                     | Purpose                                                                    |
| ----- | ---------------------------------------- | -------------------------------------------------------------------------- |
| Skill | `/architecting-typescript`               | Writing ADRs for TypeScript                                                |
| Skill | `/auditing-typescript`                   | Asked by the user to invoke the TypeScript code audit skill                |
| Skill | `/auditing-typescript-architecture`      | Asked by the user to invoke the TypeScript architecture audit skill        |
| Skill | `/auditing-typescript-tests`             | Asked by the user to invoke the TypeScript test audit skill                |
| Skill | `/coding-typescript`                     | Writing or fixing implementation code for TypeScript                       |
| Skill | `/standardizing-typescript`              | TypeScript code standards enforced across all skills                       |
| Skill | `/standardizing-typescript-architecture` | TypeScript ADR conventions enforced across architect and auditor skills    |
| Skill | `/standardizing-typescript-tests`        | TypeScript testing standards enforced across all skills                    |
| Skill | `/testing-typescript`                    | Writing or fixing tests for TypeScript                                     |
| Agent | `typescript-architecture-auditor`        | Audit TypeScript ADRs for conventions, testability, and voice              |
| Agent | `typescript-code-auditor`                | Audit TypeScript code for design flaws and ADR compliance                  |
| Agent | `typescript-simplifier`                  | Simplifies TypeScript code for clarity and maintainability                 |
| Agent | `typescript-test-auditor`                | Audit TypeScript test code for evidence quality using the 4-property model |

### work

Work deliverables: /excalidrawing (Excalidraw diagrams), /sanitizing-powerpoint (PowerPoint deck cleanup)

| Type  | Name                     | Purpose                                                                                                                                                                               |
| ----- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill | `/excalidrawing`         | Creating Excalidraw diagrams, visualizing workflows, architectures, or concepts                                                                                                       |
| Skill | `/sanitizing-powerpoint` | Sanitizing, cleaning up, auditing, or aligning a PowerPoint (.pptx) deck — slide-master and layout structure, layout type attributes, stray fonts, non-theme colors, or layout naming |

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
