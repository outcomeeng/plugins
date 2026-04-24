# Outcome Engineering Plugin Marketplace

Combined Codex and Claude Code marketplace (`outcomeeng/plugins`) delivering the Spec Tree methodology for [Outcome Engineering](https://outcome.engineering) — the product engineering paradigm where human-written specifications are the authoritative source of truth.

`AGENTS.md` is the canonical repo instruction file. `CLAUDE.md` is a symlink to this file so Codex and Claude Code share the same project instructions.

## Marketplace Is a Product

We develop this marketplace as a product using its own Spec Tree. The product specs are in `spx/` (the durable map).

## Runtime Surfaces

This repository publishes two plugin surfaces from the same source tree:

- `.claude-plugin` for Claude Code plugins, commands, and agents
- `.codex-plugin` for Codex skill bundles

Shared plugins ship both manifests where supported.

## Agent Runtime Guidance

This file is shared by Claude Code and Codex. Follow the rule's intent with the tool names available in the current runtime.

| Capability                       | Claude Code                      | Codex                                        |
| -------------------------------- | -------------------------------- | -------------------------------------------- |
| Structured question with choices | `AskUserQuestion`                | `request_user_input`                         |
| Read files                       | `Read`                           | `exec_command` with `rg`, `sed`, or `cat`    |
| Edit files                       | `Edit` / `Write`                 | `apply_patch`                                |
| Search files                     | `Glob` / `Grep`                  | `exec_command` with `rg` or `rg --files`     |
| Read-only research agents        | `Task` / configured subagents    | `spawn_agent` only when explicitly requested |
| Project plugin settings          | `.claude/settings.json`          | `.codex/config.toml`                         |
| User-level plugin registration   | `~/.claude/` via `claude plugin` | `~/.codex/config.toml` via `codex plugin`    |

When these instructions say `AskUserQuestion`, Codex must use `request_user_input`. When these instructions say `Read`, `Edit`, or `Write`, Codex must use its local shell and patch tools in a way that preserves the same behavior.

## Marketplace Methodology

This file covers repository rules that apply across both agents.

Claude Code-specific methodology — skill structure patterns, testing philosophy, research on skill activation — lives in [`methodology/`](methodology/CLAUDE.md). Read [`methodology/CLAUDE.md`](methodology/CLAUDE.md) when creating or restructuring skills, writing tests, or tuning skill descriptions for reliable activation.

Spec-tree methodology rules (node types, states, assertion types, ordering) live in `plugins/spec-tree/skills/understanding/references/` and are authoritative over `methodology/`.

## Historical Context

The Outcome Engineering methodology has evolved through three generations. Only the current one is active.

| Generation              | Plugin       | Directory     | Node types                     | Context skill          | Status      |
| ----------------------- | ------------ | ------------- | ------------------------------ | ---------------------- | ----------- |
| 1st (Jul 2025–Jan 2026) | `specs`      | `specs/work/` | `capability → feature → story` | `/understanding-specs` | **Legacy**  |
| 2nd (Jan–Mar 2026)      | `spx-legacy` | `spx/`        | `capability → feature → story` | `/understanding-spx`   | **Legacy**  |
| 3rd (Mar 2026–)         | `spec-tree`  | `spx/`        | `enabler`, `outcome`           | `/contextualizing`     | **Current** |

**What changed across generations:**

- **1st → 2nd**: Moved from `specs/work/` to `spx/`, adopted durable map principles and sparse integer ordering. The three-level hierarchy (`capability/feature/story`) remained.
- **2nd → 3rd**: Replaced the fixed three-level hierarchy with two recursive node types (`enabler`, `outcome`) that nest to arbitrary depth. Replaced `understanding-spx` with `contextualizing`. Merged the separate `spx` and `code` plugins into `spec-tree`.

Historical plugin implementations are pruned from this repository. The history table explains why old project directories or installed plugins may still appear outside this checkout.

## Critical Rules

- ⚠️ **NEVER answer ANY question without invoking at least one skill first** - If the question touches testing, specs, code, architecture, or any topic covered by a skill, invoke the relevant skill BEFORE answering. Skills are the authoritative source — not grep results, not existing files, not your training data. See skill table below.
- ⚠️ **NEVER write code without invoking a skill first** - See skill table below
- ⚠️ **NEVER manually navigate `spx/` hierarchy** - Use `/contextualizing spx/path/to/node` skill
- ⚠️ **ALWAYS read CLAUDE.md in subdirectories** - When working with files in `spx/`, or any other directory, read that directory's CLAUDE.md FIRST if it exists
- ⚠️ **Skills are ALWAYS authoritative over existing files** - When a skill template prescribes a structure (e.g., Architectural Constraints table), follow the skill — not patterns found in existing spec files. Existing files may contain non-standard sections added before skills existed. Never infer framework conventions from existing files; always read the skill.
- ⚠️ **NEVER maintain backward compatibility** - When rewriting a module, replace it entirely. No legacy aliases, no re-exports of old names, no shims. Update all imports across the codebase to use the new API.
- ⚠️ **NEVER reference specs or decisions from code** - No `ADR-21`, `PDR-13`, or similar in code comments or docstrings. Specs are the source of truth; code should not duplicate or point to them. The `semgrep` rule enforces this.
- ⚠️ **NEVER manually delete untracked files or empty directories** - Git doesn't track empty dirs; `.DS_Store` and `__pycache__` are gitignored artifacts. Use `just clean` to remove them
- ⚠️ **NEVER use general-purpose agents to create or modify ANY files** - Agents (subagents, background agents) must ONLY be used for read-only research: searching code, reading files, running read-only commands. ALL file creation, editing, and writing MUST be done by the `applier` agent (see `spec-tree` plugin) or remain in the main conversation context
- ⚠️ **Python skill examples use `product.*` / `product_testing.*`** - Not `src.*` or `src_testing.*`. The `src` convention is ambiguous across Python ecosystems; `product` is unambiguous and signals "the thing we're building"
- ⚠️ **Audit skills (`auditing-*`) must be read-only** - They produce verdicts, not code changes. `allowed-tools` should not include `Write` or `Edit`. The calling workflow decides what happens after the verdict
- ⚠️ **NEVER weaken a spec to match code or tests** - When an audit finds an unfulfilled assertion, write the missing test or fix the implementation. The declaration governs. Removing or downgrading an assertion to make the audit pass is the exact failure mode the methodology exists to prevent.
- ⚠️ **Work plans MUST include audit gates** - After each structural step (tree surgery, spec authoring, test writing), run the relevant audit before proceeding. Do not batch all audits to the end — defects compound across steps.

- ✅ **Always use `just test`** - Never bare pytest (just run loads .env automatically)
- ✅ **When uncertain, ASK STRUCTURED QUESTIONS. Never guess implementation patterns, test methodology or requirements.**
- ✅ **ALWAYS USE the runtime's structured-question tool for questions with predefined options.** Claude Code uses `AskUserQuestion`; Codex uses `request_user_input`. Do NOT use structured questions for open-ended questions where the user needs to provide free-form context — ask in plain text instead.
- ✅ **When you are wrong, KEEP ASKING STRUCTURED QUESTIONS. Never assume that you are bothering the user. As long as you are thinking deeply and asking high-leverage questions, you are doing the right thing.**
- ✅ **Dog-food platform features in skills** - When you discover an undocumented Claude Code capability (e.g., `skills:` field in subagents), check whether our skills teach it and update them if not

## Read Tool Output

The `</output>` tag at the end of Read tool results is the tool's output delimiter — it is NOT part of the file content. Never treat it as a "stray closing tag" or attempt to remove it from files.

## Markdown Formatting Rules

**IMPORTANT: Pseudo-XML in Markdown Code Fences**

When documenting XML-like syntax that isn't valid XML (pseudo-XML with text content, no proper elements), **ALWAYS use `text` as the language identifier**, not `xml`:

```text
<!-- ✅ CORRECT: Use "text" for pseudo-XML -->
<metadata>
  timestamp: [UTC timestamp]
  project: [Project name]
</metadata>
```

**Why:** The markup formatter (`markup_fmt`) in dprint will attempt to format XML code fences and can mangle pseudo-XML syntax. Using `text` prevents this issue while maintaining syntax highlighting compatibility with most linters.

**NEVER USE:**

- `` ```xml `` for pseudo-XML (causes formatting issues)
- `` ``` `` with no language identifier (rejected by some markdown linters)

## Documentation

### Official Anthropic Resources

**Core Documentation:**

- [Create plugins](https://code.claude.com/docs/en/plugins) - How to create and structure plugins
- [Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) - How to create and distribute marketplaces
- [Plugins Reference](https://code.claude.com/docs/en/plugins-reference) - Complete technical specifications, schemas, and CLI commands
- [Discover Plugins](https://code.claude.com/docs/en/discover-plugins) - How users find and install plugins
- [Agent Skills](https://code.claude.com/docs/en/skills) - Creating and using Skills

**Announcements:**

- [Claude Code Plugins Announcement](https://www.anthropic.com/news/claude-code-plugins) - Official plugin system launch
- [Agent Skills Introduction](https://www.anthropic.com/news/skills) - Skills feature announcement

**Best Practices:**

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Agentic coding patterns

### OpenAI / Codex Resources

- [Codex](https://openai.com/codex) - Codex product overview
- [Codex Overview](https://platform.openai.com/docs/codex/overview) - Codex cloud and local workflow overview
- `codex --help` - Local CLI reference
- `codex plugin --help` - Local plugin management reference

## Develop Plugin

Meta-skills for Codex and Claude Code plugin development: creating and auditing skills, commands, subagents, and agent prompt standards.

### Skills

| Skill                          | Purpose                                                            |
| ------------------------------ | ------------------------------------------------------------------ |
| `/standardizing-skills`        | Skill authoring standards (reference, loaded by creating/auditing) |
| `/standardizing-agent-prompts` | Voice, description, constraint conventions (reference)             |
| `/creating-skills`             | Create and refine skills                                           |
| `/creating-commands`           | Create slash commands with XML structure                           |
| `/creating-subagents`          | Create and configure subagents                                     |
| `/auditing-skills`             | Audit skills for best practices compliance                         |
| `/auditing-commands`           | Audit slash commands for best practices                            |
| `/auditing-subagents`          | Audit subagent configurations                                      |

## HDL Plugin

HDL engineering skills for VHDL and SystemVerilog code review.

### Skills

| Skill                      | Purpose                                                              |
| -------------------------- | -------------------------------------------------------------------- |
| `/reviewing-vhdl`          | Idiomatic VHDL-2008 review with synthesizability analysis            |
| `/reviewing-systemverilog` | Idiomatic SystemVerilog IEEE 1800-2017 review for Vivado and Quartus |

## Frontend Plugin

Frontend design and coding skills and commands.

### Skills

| Skill                 | Purpose                                                  |
| --------------------- | -------------------------------------------------------- |
| `/designing-frontend` | Create distinctive, production-grade frontend interfaces |

## Visual Plugin

Diagram authoring skills.

### Skills

| Skill            | Purpose                                                               |
| ---------------- | --------------------------------------------------------------------- |
| `/excalidrawing` | Author Excalidraw diagrams for workflows, architectures, and concepts |

## Prose Plugin

Prose craft skills for writing and reviewing.

### Skills

| Skill                  | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `/standardizing-prose` | Prose anti-patterns enforced across all skills (reference) |
| `/writing-prose`       | Write varied, specific, human prose (always active)        |
| `/reviewing-prose`     | Review and edit prose for formulaic patterns (on request)  |

## TypeScript Plugin

Complete TypeScript development workflow with testing, implementation, and review.

### Skills

| Skill                                    | Purpose                                                       |
| ---------------------------------------- | ------------------------------------------------------------- |
| `/standardizing-typescript-architecture` | ADR conventions shared by architect and auditor (reference)   |
| `/standardizing-typescript`              | TypeScript code standards (reference, loaded by other skills) |
| `/standardizing-typescript-tests`        | TypeScript test standards + ESLint rule plugin (reference)    |
| `/testing-typescript`                    | TypeScript-specific testing patterns                          |
| `/coding-typescript`                     | Implementation workhorse with remediation loop                |
| `/auditing-typescript`                   | Strict code audit with zero-tolerance                         |
| `/auditing-typescript-tests`             | TypeScript test evidence audit (4-property model)             |
| `/architecting-typescript`               | ADR producer with Compliance-based testability                |
| `/auditing-typescript-architecture`      | ADR audit with structured per-concern verdict                 |

### Agents

| Agent                             | Purpose                                                |
| --------------------------------- | ------------------------------------------------------ |
| `typescript-code-auditor`         | Code audit subagent (preloads auditing skill)          |
| `typescript-architecture-auditor` | ADR audit subagent (preloads auditing skill)           |
| `typescript-test-auditor`         | Test evidence audit subagent (preloads auditing skill) |
| `typescript-simplifier`           | Simplifies recently-modified code; verifies tests pass |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Level 1/Level 2/Level 3)

## Python Plugin

Complete Python development workflow with testing, implementation, and review.

### Skills

| Skill                                | Purpose                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| `/standardizing-python-architecture` | ADR conventions shared by architect and auditor (reference) |
| `/standardizing-python`              | Python code standards (reference, loaded by other skills)   |
| `/standardizing-python-tests`        | Python test standards (reference, loaded by other skills)   |
| `/testing-python`                    | Python-specific testing patterns                            |
| `/coding-python`                     | Implementation workhorse with remediation loop              |
| `/auditing-python`                   | Strict code audit with zero-tolerance                       |
| `/auditing-python-tests`             | Python test evidence audit (4-property model)               |
| `/architecting-python`               | ADR producer with Compliance-based testability              |
| `/auditing-python-architecture`      | ADR audit with structured per-concern verdict               |

### Agents

| Agent                         | Purpose                                                |
| ----------------------------- | ------------------------------------------------------ |
| `python-code-auditor`         | Code audit subagent (preloads auditing skill)          |
| `python-architecture-auditor` | ADR audit subagent (preloads auditing skill)           |
| `python-test-auditor`         | Test evidence audit subagent (preloads auditing skill) |

### Core Principles

- No mocking - dependency injection only
- Reality is the oracle
- Behavior testing, not implementation testing
- Tests at appropriate levels (Level 1/Level 2/Level 3)

## Spec Tree Plugin

The Spec Tree methodology for [Outcome Engineering](https://outcome.engineering). Three steps drive the methodology: **declare, spec, apply**. Audit gates operate within each step. See `plugins/spec-tree/skills/understanding/references/durable-map.md` for the authoritative methodology reference.

| Step        | What happens                  | Node state after |
| ----------- | ----------------------------- | ---------------- |
| **Declare** | Write spec (assertions)       | Declared         |
| **Spec**    | Write tests (make verifiable) | Specified        |
| **Apply**   | Write implementation code     | Passing          |

Planning is ephemeral — `PLAN.md` escape hatches left by `/handoff`. Not a durable artifact.

### Skills

| Skill                         | Step    | Purpose                                                                 |
| ----------------------------- | ------- | ----------------------------------------------------------------------- |
| `/understanding`              | declare | Foundation skill — loaded before any other                              |
| `/contextualizing`            | declare | Deterministic context loading from tree                                 |
| `/bootstrapping`              | declare | Interview user, scaffold new spec tree                                  |
| `/authoring`                  | declare | Add, define, create specs, decisions, and nodes                         |
| `/decomposing`                | declare | Break down, split, scope work                                           |
| `/refactoring`                | declare | Move nodes, re-scope, extract shared enablers                           |
| `/aligning`                   | declare | Check consistency, conformance, find gaps (audit gate)                  |
| `/interviewing`               | declare | Domain-agnostic interview methodology (used by bootstrapping/authoring) |
| `/refocusing`                 | declare | Redirects ad hoc work and throwaway scripts back onto a spec            |
| `/testing`                    | spec    | Write tests driven by spec assertions                                   |
| `/auditing-tests`             | spec    | Audit test evidence quality (audit gate)                                |
| `/auditing-product-decisions` | spec    | Audit PDR evidence quality (audit gate)                                 |
| `/applying`                   | *all*   | Orchestrator: runs declare + spec + apply in sequence with audit gates  |
| `/committing-changes`         | apply   | Conventional Commits with selective staging                             |
| `/handing-off`                | apply   | Close a session with reflection, persistence, and a handoff file        |
| `/picking-up`                 | apply   | Resume spec-tree work from a saved handoff session                      |

### Agents

| Agent                   | Purpose                                                        |
| ----------------------- | -------------------------------------------------------------- |
| `applier`               | Autonomous TDD agent — runs the full 8-step flow as a subagent |
| `test-evidence-auditor` | Test evidence audit subagent (preloads auditing-tests skill)   |
| `pdr-auditor`           | PDR audit subagent (preloads auditing-product-decisions skill) |

### Commands

| Command      | Purpose                                                                    |
| ------------ | -------------------------------------------------------------------------- |
| `/bootstrap` | Set up a new spec tree (invokes `/bootstrapping`)                          |
| `/author`    | Author a spec tree artifact (auto-detects type)                            |
| `/commit`    | Git commit with Conventional Commits (auto-context)                        |
| `/apply`     | Run TDD flow on a subtree or discover work from `spx/EXCLUDE`              |
| `/rtfm`      | Stop ad hoc work and follow the methodology                                |
| `/clarify`   | Clarify ambiguous requirements                                             |
| `/handoff`   | Create timestamped context handoff                                         |
| `/pickup`    | Load and continue from previous handoff                                    |
| `/release`   | Close session without creating a handoff file (archives in-scope sessions) |

## When to Dispatch Agents vs Invoke Skills

Auditor skills can be invoked directly in the main conversation or dispatched as subagents. Each auditor agent preloads the corresponding skill via the `skills:` frontmatter field.

- **One audit, user wants to discuss findings** → invoke the skill directly
- **Multiple audits in parallel** → dispatch subagents, collect verdicts
- **Autonomous flow (e.g., `/apply --agent`)** → the `applier` agent handles audit dispatch internally

| Skill                               | Agent                             |
| ----------------------------------- | --------------------------------- |
| `/auditing-product-decisions`       | `pdr-auditor`                     |
| `/auditing-tests`                   | `test-evidence-auditor`           |
| `/auditing-{language}`              | `{language}-code-auditor`         |
| `/auditing-{language}-architecture` | `{language}-architecture-auditor` |
| `/auditing-{language}-tests`        | `{language}-test-auditor`         |

## Proactive Skill Invocation

Certain skills must be invoked **automatically** when specific conditions are met, without waiting for explicit user request.

**BEFORE implementing any work item**, you MUST:

1. **Invoke `/contextualizing`** on the target node
   - **Trigger**: User requests implementation of a work item
   - **Purpose**: Load complete context hierarchy (product → decisions → ancestors → target)
   - **Example**: User says "implement this outcome" → STOP and invoke `/contextualizing` FIRST
   - **Non-negotiable**: Do NOT read spec files directly without invoking this skill

2. **Invoke `/authoring`** when creating specs or nodes
   - **Trigger**: User requests creating a product spec, ADR, PDR, enabler, or outcome
   - **Purpose**: Access templates, understand index assignment
   - **Example**: User says "create an outcome for search" → STOP and invoke `/authoring`
   - **Critical**: Templates are in the `understanding` skill's directory, NOT in the project

**Pattern**: These skills are preparatory and blocking. You MUST invoke them BEFORE writing code or documents.

**Rationale**: Without these skills, you will:

- Miss requirements and violate ADRs
- Search for templates that don't exist in the project
- Create nodes with incorrect indices
- Generate specs with wrong structure

## For Claude Agents Modifying This Marketplace

### ⛔ Subagent Restrictions

**NEVER use subagents (Agent tool) to create or modify any file.** All file creation and modification must happen in the main conversation context using Read, Edit, and Write tools directly. Subagents are for research, exploration, and auditing only.

### ⛔ Path Restrictions

**NEVER manually write to these locations:**

- `~/.claude/` - User home directory, not project-specific
- Any path containing `.claude` in user home
- `.claude/` files, except `.claude/settings.json` updates produced by Claude CLI project-scope plugin commands

**ALWAYS write to project directories:**

- `plugins/` - Plugin code, skills, commands, templates
- `spx/` - Specs as durable map (see [spx/CLAUDE.md](spx/CLAUDE.md))
- `.spx/` - Tool operational files (sessions, cache) - gitignored
- `.claude/settings.json` - Claude project-scope plugin settings created by `claude plugin ... --scope project` and committed for collaborators
- `.codex/config.toml` - Codex project-scope config for the plugin set this repository needs
- Project root - Package files, config files

**Rationale:** Manual file operations in `.claude/` require extra permission and break workflow. Claude CLI project-scope plugin commands are the exception because they update `.claude/settings.json` for the repository's shared plugin set. Codex project config belongs in `.codex/config.toml` so collaborators inherit the plugin enablement for this repo after trusting the project.

### ⛔ File Removal Restrictions

**Tracked files with no changes:** Use `git rm` to remove files that are committed in git and have no uncommitted modifications.

**All other files:** You CANNOT remove files that are untracked or have uncommitted changes. Do not attempt to circumvent this restriction. Instead, **ALWAYS** provide the exact `rm` command to the user and **WAIT** until the user has confirmed they have executed it before proceeding.

### Before Making Changes

1. **Read the context**: Check [CLAUDE.md](CLAUDE.md:1) (this file) for current structure
2. **Check existing commands**: Use Glob to find existing `.md` files in `plugins/*/commands/`
3. **Review plugin structure**: Each plugin has its own `plugin.json` in `.claude-plugin/`
   - Codex-capable plugins also have `.codex-plugin/plugin.json`

### After Adding/Modifying Commands or Skills

Before committing, invoke `/committing-changes` — it loads marketplace-specific rules (versioning, file targets, commit workflow) from `spx/local/committing-changes.md`.

### Quick Reference: File Locations

```
outcomeeng/plugins/                 # Marketplace: outcomeeng
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
├── .spx/                          # Tool operational (gitignored)
│   └── sessions/                  # Session handoffs
├── outcomeeng/                    # Python package
│   ├── scripts/                  # Build/validation tools
│   └── testing/                  # Test infrastructure
├── plugins/
│   ├── develop/                  # Meta-skills for plugin development
│   │   ├── .claude-plugin/       # Claude Code manifest
│   │   ├── .codex-plugin/        # Codex manifest
│   │   └── skills/
│   │       ├── standardizing-skills/
│   │       ├── creating-skills/
│   │       ├── creating-commands/
│   │       ├── creating-subagents/
│   │       ├── auditing-skills/
│   │       ├── auditing-commands/
│   │       └── auditing-subagents/
│   ├── frontend/
│   │   └── skills/
│   │       └── designing-frontend/
│   ├── hdl/                       # HDL engineering
│   │   └── skills/
│   │       ├── reviewing-vhdl/
│   │       └── reviewing-systemverilog/
│   ├── prose/
│   │   └── skills/
│   │       ├── standardizing-prose/
│   │       ├── writing-prose/
│   │       └── reviewing-prose/
│   ├── python/
│   │   ├── agents/
│   │   │   ├── python-code-auditor.md
│   │   │   ├── python-architecture-auditor.md
│   │   │   └── python-test-auditor.md
│   │   └── skills/
│   │       └── (9 skills)
│   ├── spec-tree/                # Spec Tree — 3 phases
│   │   ├── agents/
│   │   │   ├── applier.md
│   │   │   ├── test-evidence-auditor.md
│   │   │   └── pdr-auditor.md
│   │   ├── bin/
│   │   │   └── session-start
│   │   ├── commands/
│   │   │   ├── apply.md
│   │   │   ├── author.md
│   │   │   ├── bootstrap.md
│   │   │   ├── clarify.md
│   │   │   ├── commit.md
│   │   │   ├── handoff.md
│   │   │   ├── pickup.md
│   │   │   ├── release.md
│   │   │   └── rtfm.md
│   │   ├── hooks/
│   │   │   └── hooks.json
│   │   └── skills/
│   │       └── (16 skills)
│   ├── typescript/
│   │   ├── agents/
│   │   │   ├── typescript-code-auditor.md
│   │   │   ├── typescript-architecture-auditor.md
│   │   │   ├── typescript-test-auditor.md
│   │   │   └── typescript-simplifier.md
│   │   └── skills/
│   │       └── (9 skills)
│   └── visual/
│       └── skills/
│           └── excalidrawing/
├── pyproject.toml                 # uv project config + dev deps
├── spx/                           # Specs as durable map
│   ├── CLAUDE.md                 # Specs directory guide
│   ├── EXCLUDE                    # Nodes skipped by the quality gate
│   ├── local/                    # Project-specific skill overlays
│   │   └── committing-changes.md
│   ├── 15-spec-coverage.adr.md
│   ├── 15-test-language.adr.md
│   ├── 15-audit-verdict-format.pdr.md
│   ├── 15-validation.enabler/
│   └── 21-spec-tree.enabler/
│       ├── 15-context-loading.enabler/
│       ├── 21-templates.enabler/
│       ├── 32-decisions.enabler/
│       │   └── 32-pdr-auditing.enabler/
│       └── 32-evidence.enabler/
│           ├── 21-sync-exclude.enabler/
│           ├── 32-test-auditing.enabler/
│           └── 43-audit-verdict-schema.enabler/
└── CLAUDE.md                      # This file
```

## How to commit

Always invoke the skill `/committing-changes` and adhere to its git commit message guidance.

## After pushing marketplace changes

When publishing marketplace changes from this repo, prefer the `just` helper so push and local marketplace refresh happen in one step:

```bash
just push-marketplace
just push-marketplace origin main
```

## Missing plugins or skills

### Claude Code

When repo-required Claude plugins are missing, ask the user before changing project-scoped Claude settings. Use Claude's project scope so the marketplace and enabled plugins are written to `.claude/settings.json`; commit that file so collaborators get the same plugin set.

```bash
claude plugin marketplace add outcomeeng/plugins --scope project

for plugin in develop python prose spec-tree; do
  claude plugin install "${plugin}@outcomeeng" --scope project
done
```

If an installed project-scoped plugin has been disabled, re-enable it at project scope:

```bash
for plugin in develop python prose spec-tree; do
  claude plugin enable "${plugin}@outcomeeng" --scope project
done
```

After changing plugin state in a running Claude Code session, run `/reload-plugins`.

### Codex

Codex marketplace registration is user-scoped. Ask the user before changing `~/.codex/config.toml`, then register the marketplace once:

```bash
codex plugin marketplace add outcomeeng/plugins
```

Enable plugins per project by committing `.codex/config.toml`. Keep the project list explicit so each repo gets only the plugins it needs:

```toml
[plugins."develop@outcomeeng"]
enabled = true

[plugins."prose@outcomeeng"]
enabled = true

[plugins."spec-tree@outcomeeng"]
enabled = true
```

Add language or domain plugins only for projects that use them:

```toml
[plugins."python@outcomeeng"]
enabled = true

[plugins."typescript@outcomeeng"]
enabled = true
```

If a user's global Codex config already enables a plugin that the project should keep off, add an explicit project override:

```toml
[plugins."typescript@outcomeeng"]
enabled = false
```
