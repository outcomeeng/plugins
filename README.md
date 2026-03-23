# Outcome Engineering Plugin Marketplace

A Claude Code plugin marketplace (`outcomeeng/claude`) for [Outcome Engineering](https://outcome.engineering) and [SPX](https://spx.sh) — spec-driven development with skills and commands for testing, Python and TypeScript engineering, and productivity.

## Philosophy

1. **RTFM:** Follow state-of-the-art (SOTA) model prompting guidance, such as [structured prompts based on XML tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags#tagging-best-practices)
2. **KILO:**: *Keep It Local and Observable,* to facilitate discovery by agents by keeping the golden source for all specifications locally within the project's Git repository

## Quick Start

### 1. Install the SPX CLI

```bash
npm install -g @outcomeeng/spx
```

SPX is the developer CLI for spec-driven development. See [@outcomeeng/spx on npm](https://www.npmjs.com/package/@outcomeeng/spx) for details.

### 2. Add the marketplace and install plugins

```bash
# Add the marketplace
claude plugin marketplace add outcomeeng/claude

# Recommended plugins
claude plugin install spec-tree@outcomeeng   # spec-driven development + commands
claude plugin install prose@outcomeeng       # writing and reviewing prose
claude plugin install claude@outcomeeng      # meta-skills for plugin development
```

### 3. Use skills and commands

**`spec-tree` — spec-driven development + commands:**

```text
> /commit                          # commit with Conventional Commits
> /handoff                         # create context handoff for next session
> /pickup                          # continue from a previous handoff
> /tdd                             # start the TDD flow
> /rtfm                            # stop ad hoc work, follow methodology
> /clarify                         # gather requirements before executing
> /testing                         # write tests driven by spec assertions
> /coding                          # TDD flow: architect, test, code + review
```

**`prose` — writing and reviewing:**

```text
> /writing-prose                   # activate prose craft for long-form text
> /reviewing-prose                 # review text for formulaic patterns
> Write a blog post about X        # Claude invokes /writing-prose automatically
```

**`claude` — plugin development:**

```text
> /creating-skills                 # create a new SKILL.md with guidance
> /auditing-skills                 # audit an existing skill for best practices
> /creating-commands               # create a new slash command
```

### Language plugins (install per project)

```bash
claude plugin install typescript@outcomeeng  # TypeScript engineering
claude plugin install python@outcomeeng      # Python engineering
```

These add language-specific skills like `/testing-typescript`, `/coding-python`, `/reviewing-typescript`, etc.

### Spec Tree framework (for spec-driven projects)

```bash
claude plugin install spec-tree@outcomeeng   # Spec Tree framework
```

### Updating plugins

```bash
# Update this marketplace
claude plugin marketplace update outcomeeng

# Or update all marketplaces
claude plugin marketplace update
```

For automatic updates, run `claude`, navigate to `/plugin marketplace`, select this marketplace, and enable `Enable auto-update`.

## Available Plugins

### claude

Meta-skills for Claude Code plugin development.

| Type  | Name                  | Purpose                         |
| ----- | --------------------- | ------------------------------- |
| Skill | `/creating-skills`    | Create and refine skills        |
| Skill | `/creating-commands`  | Create slash commands with XML  |
| Skill | `/creating-subagents` | Create and configure subagents  |
| Skill | `/auditing-skills`    | Audit skills for best practices |
| Skill | `/auditing-commands`  | Audit slash commands            |
| Skill | `/auditing-subagents` | Audit subagent configurations   |

Credit: `/creating-skills` is inspired by [TÂCHES Claude Code Resources](https://github.com/glittercowboy/taches-cc-resources?tab=readme-ov-file#skills).

### spec-tree

Spec Tree framework for spec-driven development. Three phases: spec-tree maintenance, implementation, commit.

| Type    | Name                  | Phase | Purpose                                        |
| ------- | --------------------- | ----- | ---------------------------------------------- |
| Skill   | `/understanding`      | 1     | Foundation skill — loaded before any other     |
| Skill   | `/contextualizing`    | 1     | Deterministic context loading from tree        |
| Skill   | `/bootstrapping`      | 1     | Interview user, scaffold new spec tree         |
| Skill   | `/authoring`          | 1     | Add, define, create specs and features         |
| Skill   | `/decomposing`        | 1     | Break down, split, scope work                  |
| Skill   | `/refactoring`        | 1     | Move nodes, re-scope, extract shared enablers  |
| Skill   | `/aligning`           | 1     | Review, check consistency, audit, find gaps    |
| Skill   | `/testing`            | 2     | Write tests driven by spec assertions          |
| Skill   | `/reviewing-tests`    | 2     | Adversarial review of test evidence            |
| Skill   | `/coding`             | 2     | TDD flow: architect, test, code + review gates |
| Skill   | `/committing-changes` | 3     | Conventional Commits with selective staging    |
| Command | `/commit`             |       | Git commit with Conventional Commits           |
| Command | `/tdd`                |       | Start TDD flow                                 |
| Command | `/rtfm`               |       | Stop ad hoc work, follow methodology           |
| Command | `/clarify`            |       | Clarify ambiguous requirements                 |
| Command | `/handoff`            |       | Create timestamped context handoff             |
| Command | `/pickup`             |       | Load and continue from previous handoff        |

Credit: `/handoff` is inspired by [TÂCHES Claude Code Resources](https://github.com/glittercowboy/taches-cc-resources/tree/main?tab=readme-ov-file#context-handoff).

### core

Standalone commit workflow for projects that don't use the Spec Tree. Provides `/commit`, `/handoff`, and `/pickup` without spec-tree skills. Install `spec-tree` instead if your project has an `spx/` directory.

| Type    | Name                  | Purpose                                 |
| ------- | --------------------- | --------------------------------------- |
| Skill   | `/committing-changes` | Commit message guidance                 |
| Command | `/commit`             | Git commit with Conventional Commits    |
| Command | `/handoff`            | Create timestamped context handoff      |
| Command | `/pickup`             | Load and continue from previous handoff |

### test (legacy)

Standalone testing methodology. Spec-tree users should use `spec-tree` instead, which includes testing as a superset.

| Type  | Name               | Purpose                           |
| ----- | ------------------ | --------------------------------- |
| Skill | `/testing`         | Foundational testing methodology  |
| Skill | `/reviewing-tests` | Foundational test review protocol |

### typescript

Complete TypeScript development workflow.

| Type  | Name                                 | Purpose                            |
| ----- | ------------------------------------ | ---------------------------------- |
| Agent | `typescript-simplifier`              | Simplify code for maintainability  |
| Skill | `/testing-typescript`                | TypeScript-specific testing        |
| Skill | `/coding-typescript`                 | Implementation with remediation    |
| Skill | `/reviewing-typescript`              | Strict code review                 |
| Skill | `/architecting-typescript`           | ADR producer with testing strategy |
| Skill | `/reviewing-typescript-architecture` | ADR validator                      |

### python

Complete Python development workflow.

| Type    | Name                             | Purpose                            |
| ------- | -------------------------------- | ---------------------------------- |
| Command | `/autopython`                    | Autonomous implementation          |
| Skill   | `/testing-python`                | Python-specific testing patterns   |
| Skill   | `/coding-python`                 | Implementation with remediation    |
| Skill   | `/reviewing-python`              | Strict code review                 |
| Skill   | `/architecting-python`           | ADR producer with testing strategy |
| Skill   | `/reviewing-python-architecture` | ADR validator                      |

### prose

Prose craft skills for writing and reviewing.

| Type  | Name               | Purpose                                      |
| ----- | ------------------ | -------------------------------------------- |
| Skill | `/writing-prose`   | Write varied, specific, human prose          |
| Skill | `/reviewing-prose` | Review and edit prose for formulaic patterns |

### frontend

Frontend design and styling.

| Type  | Name                  | Purpose                                |
| ----- | --------------------- | -------------------------------------- |
| Skill | `/designing-frontend` | Create distinctive frontend interfaces |

### specs (legacy)

Legacy `specs/` directory support.

| Type  | Name                   | Purpose                            |
| ----- | ---------------------- | ---------------------------------- |
| Skill | `/managing-specs`      | Manage specs structure and ADRs    |
| Skill | `/understanding-specs` | Load context before implementation |

### spx-legacy (deprecated)

**Deprecated — superseded by spec-tree.** Legacy Outcome Engineering (spx/) skills.

| Type  | Name                 | Purpose                                 |
| ----- | -------------------- | --------------------------------------- |
| Skill | `/writing-prd`       | Write product requirements              |
| Skill | `/managing-spx`      | Create and manage spx/ specs            |
| Skill | `/understanding-spx` | Load context before implementation      |
| Skill | `/decomposing-*`     | Decompose PRDs to capabilities/features |

---

## Build Your Own Marketplace

Want to create your own plugin marketplace? Fork this repo as a starting point.

### Clone and Set Up

```bash
# Clone as your own marketplace
git clone https://github.com/outcomeeng/claude.git ~/Code/my-claude-plugins
cd ~/Code/my-claude-plugins

# Remove origin and set up your own remote
git remote remove origin
git remote add origin git@github.com:yourusername/my-claude-plugins.git
```

### Add as a Local Marketplace

During development, add your local clone as a marketplace:

```bash
claude plugin marketplace add ~/Code/my-claude-plugins
```

This lets you edit skills and commands locally with changes available immediately.

### Repository Structure

```text
my-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
└── plugins/
    └── my-plugin/
        ├── .claude-plugin/
        │   └── plugin.json       # Plugin metadata and version
        ├── commands/
        │   └── my-command.md     # Slash commands
        └── skills/
            └── my-skill/
                └── SKILL.md      # Agent skills
```

| Concept         | What it is                                 |
| --------------- | ------------------------------------------ |
| **Skill**       | Agent guidance (SKILL.md files)            |
| **Command**     | Slash command (`/build` → `build.md`)      |
| **Plugin**      | Namespace grouping related skills/commands |
| **Marketplace** | Index pointing to plugins                  |

### Publish Your Marketplace

Once your marketplace is on GitHub, others can add it:

```bash
claude plugin marketplace add yourusername/my-claude-plugins
claude plugin install my-plugin@my-claude-plugins
```

## Documentation

- [Claude Code Plugins](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference)

## License

MIT
