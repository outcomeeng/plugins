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
2. **KILO:** *Keep It Local and Observable* — the golden source for all specifications lives locally within the project's Git repository

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

# Language plugins (install per project, require spx CLI)
claude plugin install python@outcomeeng
claude plugin install typescript@outcomeeng

# Optional plugins
claude plugin install prose@outcomeeng
claude plugin install develop@outcomeeng
```

#### Codex

After adding the marketplace, enable only the plugins a project needs in that repo's committed `.codex/config.toml`:

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

## Plugins

Unless marked otherwise, the skills described below are available in both Claude Code and Codex. Commands and agents are Claude Code-only.

### spec-tree

The core of [Outcome Engineering](https://outcome.engineering). Three steps: **declare** (write specs), **spec** (write tests), **apply** (write implementation). Audit gates operate within each step.

Codex support: the same skill set is available through the `spec-tree` Codex plugin. The slash commands and bundled agents listed below are Claude Code-only.

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

| Type    | Name                    | Step    | Purpose                                                 |
| ------- | ----------------------- | ------- | ------------------------------------------------------- |
| Skill   | `/understanding`        | declare | Foundation skill — loaded before any other              |
| Skill   | `/contextualizing`      | declare | Deterministic context loading from tree                 |
| Skill   | `/bootstrapping`        | declare | Interview user, scaffold new spec tree                  |
| Skill   | `/authoring`            | declare | Add, define, create specs and nodes                     |
| Skill   | `/decomposing`          | declare | Break down, split, scope work                           |
| Skill   | `/refactoring`          | declare | Move nodes, re-scope, extract shared enablers           |
| Skill   | `/aligning`             | declare | Check consistency, conformance, find gaps (audit gate)  |
| Skill   | `/interviewing`         | declare | Domain-agnostic interview methodology                   |
| Skill   | `/testing`              | spec    | Write tests driven by spec assertions                   |
| Skill   | `/auditing-tests`       | spec    | Audit test evidence quality (audit gate)                |
| Skill   | `/applying`             | *all*   | Orchestrator: declare + spec + apply with audit gates   |
| Skill   | `/committing-changes`   | apply   | Conventional Commits with selective staging             |
| Agent   | `applier`               |         | Autonomous TDD agent — runs the full flow as a subagent |
| Agent   | `test-evidence-auditor` |         | Test evidence audit subagent (preloads auditing skill)  |
| Agent   | `pdr-auditor`           |         | PDR audit subagent (preloads auditing skill)            |
| Command | `/bootstrap`            |         | Set up a new spec tree                                  |
| Command | `/author`               |         | Author a spec tree artifact (auto-detects type)         |
| Command | `/commit`               |         | Git commit with Conventional Commits                    |
| Command | `/apply`                |         | Run TDD flow on a subtree or from `spx/EXCLUDE`         |
| Command | `/rtfm`                 |         | Stop ad hoc work, follow methodology                    |
| Command | `/clarify`              |         | Clarify ambiguous requirements                          |
| Command | `/handoff`              |         | Create timestamped context handoff                      |
| Command | `/pickup`               |         | Load and continue from previous handoff                 |

### typescript

Complete TypeScript development workflow. Requires spx CLI.

Codex support: the same skills are available through the `typescript` Codex plugin. The agents listed below are Claude Code-only.

| Type  | Name                                | Purpose                            |
| ----- | ----------------------------------- | ---------------------------------- |
| Agent | `typescript-simplifier`             | Simplify code for maintainability  |
| Agent | `typescript-code-auditor`           | Code audit subagent                |
| Agent | `typescript-architecture-auditor`   | ADR audit subagent                 |
| Agent | `typescript-test-auditor`           | Test evidence audit subagent       |
| Skill | `/testing-typescript`               | TypeScript-specific testing        |
| Skill | `/coding-typescript`                | Implementation with remediation    |
| Skill | `/auditing-typescript`              | Strict code audit                  |
| Skill | `/architecting-typescript`          | ADR producer with testing strategy |
| Skill | `/auditing-typescript-architecture` | ADR audit                          |

### python

Complete Python development workflow. Requires spx CLI.

Codex support: the same skills are available through the `python` Codex plugin. `/autopython` and the agents listed below are Claude Code-only.

| Type    | Name                            | Purpose                            |
| ------- | ------------------------------- | ---------------------------------- |
| Agent   | `python-code-auditor`           | Code audit subagent                |
| Agent   | `python-architecture-auditor`   | ADR audit subagent                 |
| Agent   | `python-test-auditor`           | Test evidence audit subagent       |
| Command | `/autopython`                   | Autonomous implementation          |
| Skill   | `/testing-python`               | Python-specific testing patterns   |
| Skill   | `/coding-python`                | Implementation with remediation    |
| Skill   | `/auditing-python`              | Strict code audit                  |
| Skill   | `/architecting-python`          | ADR producer with testing strategy |
| Skill   | `/auditing-python-architecture` | ADR audit                          |

### prose

Prose craft skills for writing and reviewing. No spx CLI required.

| Type  | Name               | Purpose                                      |
| ----- | ------------------ | -------------------------------------------- |
| Skill | `/writing-prose`   | Write varied, specific, human prose          |
| Skill | `/reviewing-prose` | Review and edit prose for formulaic patterns |

### develop

Meta-skills for Codex and Claude Code plugin development. No spx CLI required.

| Type  | Name                  | Purpose                         |
| ----- | --------------------- | ------------------------------- |
| Skill | `/creating-skills`    | Create and refine skills        |
| Skill | `/creating-commands`  | Create slash commands with XML  |
| Skill | `/creating-subagents` | Create and configure subagents  |
| Skill | `/auditing-skills`    | Audit skills for best practices |
| Skill | `/auditing-commands`  | Audit slash commands            |
| Skill | `/auditing-subagents` | Audit subagent configurations   |

Credit: These meta skills are derived from [TÂCHES Claude Code Resources](https://github.com/glittercowboy/taches-cc-resources?tab=readme-ov-file#skills). The commands `/handoff` and `/pickup` are based on `/whats-next` from the same project.

### frontend

Frontend design and styling. No spx CLI required.

| Type  | Name                  | Purpose                                |
| ----- | --------------------- | -------------------------------------- |
| Skill | `/designing-frontend` | Create distinctive frontend interfaces |

### hdl

HDL engineering skills for VHDL and SystemVerilog code review. No spx CLI required.

| Type  | Name                       | Purpose                                                              |
| ----- | -------------------------- | -------------------------------------------------------------------- |
| Skill | `/reviewing-vhdl`          | Idiomatic VHDL-2008 review with synthesizability analysis            |
| Skill | `/reviewing-systemverilog` | Idiomatic SystemVerilog IEEE 1800-2017 review for Vivado and Quartus |

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

## License

MIT
