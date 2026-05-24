# Outcome Engineering Plugin Marketplace

Combined Codex and Claude Code marketplace (`outcomeeng/plugins`) delivering the Spec Tree methodology for [Outcome Engineering](https://outcome.engineering) — the product engineering paradigm where human-written specifications are the authoritative source of truth.

`AGENTS.md` is the canonical repo instruction file. `CLAUDE.md` is a symlink to this file so Codex and Claude Code share the same product instructions.

## Reviewing pull requests

Read [`REVIEW.template.md`](REVIEW.template.md) at the repository root before posting any findings on a pull request in this repository. The template is the consumer-override surface for the `/standardizing-merging` skill — by default it mirrors the skill's three-severity (`BLOCKING` / `DEBT` / `FOLLOW-UP`) × six-category (`consistency` / `security` / `performance` / `evidence` / `standards` / `architecture`) taxonomy and the comment shape every finding must follow. Severity ranks (`P0`, `P1`, `P2`, `P3`, `critical`, `high`, `medium`, `low`, `minor`, `nit`) are not valid finding headings here, and neither are the legacy class labels `NEEDS-ANSWER` and `NOTE` — open questions are reframed as findings, and bare commentary or praise is omitted. If a review has no `BLOCKING` or `DEBT` items, say so directly — do not manufacture lower-priority findings to prove that review happened.

## Two audiences, two design surfaces

This repo is two things at once.

It is a **product**, with its own spec tree under `spx/`, its own decision records, and its own implementation under `outcomeeng/` and `plugins/`. The reader of work in those directories is this product's own developers and agents. You may name this repo's nodes, languages, and conventions directly.

It is also a **methodology shipped as plugins** under `plugins/`. Those plugins install into hundreds of consumer repositories whose spec trees, languages, layouts, and conventions are unknown at design time. The reader of work in `plugins/` is a consumer agent in some other repository. Any design that assumes this repo's tree, this repo's languages, this repo's overlay declarations, or this repo's specific node addresses is wrong for that audience. Skill content that ships under `plugins/` references language-neutral mechanisms or per-language conventions; never a marketplace-internal node path, never a single-language test filename pattern, never a PDR or ADR specific to this product.

Carrying assumptions from one surface to the other is the most common source of wrong design here. Designing a `plugins/` change as if every consumer were this repo, or naming this repo's PDR in a shipped skill body, breaks the change for every consumer that is not this repo. The Plugin Portability Constraints section below deepens the consumer-audience rules; references to specific nodes, languages, and overlays elsewhere in this file apply only when the audience is this repo's own developers.

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
| Product plugin settings          | `.claude/settings.json`          | `.codex/config.toml`                         |
| User-scope plugin registration   | `~/.claude/` via `claude plugin` | `~/.codex/config.toml` via `codex plugin`    |

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

Historical plugin implementations are pruned from this repository. The history table explains why old product directories or installed plugins may still appear outside this checkout.

## Critical Rules

- ⚠️ **NEVER answer ANY question without invoking at least one skill first** - If the question touches testing, specs, code, architecture, or any topic covered by a skill, invoke the relevant skill BEFORE answering. Skills are the authoritative source — not grep results, not existing files, not your training data. See the plugin catalog in [`README.md`](README.md#plugins) for the available skills.
- ⚠️ **NEVER write code without invoking a skill first** - See the plugin catalog in [`README.md`](README.md#plugins) for language-specific coding skills.
- ⚠️ **NEVER touch a spec-tree node without invoking `/contextualizing` first** - Before implementing work on an existing node, editing an existing spec file, or opening a PR whose diff sits inside `spx/` or imports modules tested by `spx/`, invoke `/contextualizing <full-path-of-existing-node>`. The skill loads the full ancestry (product → decisions → ancestors → target) deterministically. Reading spec files directly leaves you with partial context, missing decisions, and downstream errors. The "Spec-tree navigation" section below explains how to identify the governing node from a diff.
- ⚠️ **NEVER create a spec-tree artifact without invoking `/authoring` first** - Before creating a product spec, ADR, PDR, enabler, or outcome, invoke `/authoring`. The skill carries the templates, the index-assignment procedure, and chains into `/contextualizing` on the parent directory so sibling enumeration prevents index collisions. Do not invoke `/contextualizing` directly on a not-yet-existing node path — it will abort with "Target path not found"; the bootstrap-mode entry point belongs to `/authoring`.
- ⚠️ **ALWAYS read CLAUDE.md in subdirectories** - When working with files in `spx/`, or any other directory, read that directory's CLAUDE.md FIRST if it exists
- ⚠️ **Skills are ALWAYS authoritative over existing files** - When a skill template prescribes a structure (e.g., Architectural Constraints table), follow the skill — not patterns found in existing spec files. Existing files may contain non-standard sections added before skills existed. Never infer framework conventions from existing files; always read the skill.
- ⚠️ **NEVER maintain backward compatibility** - When rewriting a module, replace it entirely. No legacy aliases, no re-exports of old names, no shims. Update all imports across the codebase to use the new API.
- ⚠️ **NEVER reference specs or decisions from code** - No `ADR-21`, `PDR-13`, or similar in code comments or docstrings. Specs are the source of truth; code should not duplicate or point to them. The `semgrep` rule enforces this.
- ⚠️ **NEVER manually delete untracked files or empty directories** - Git doesn't track empty dirs; `.DS_Store` and `__pycache__` are gitignored artifacts. Use `just clean` to remove them
- ⚠️ **NEVER use general-purpose agents to create or modify ANY files** - Agents (subagents, background agents) must ONLY be used for read-only research: searching code, reading files, running read-only commands. ALL file creation, editing, and writing MUST be done by the `applier` agent (see `spec-tree` plugin) or remain in the main conversation context
- ⚠️ **The methodology is multi-language** - Skill content shipped under `plugins/` that names a test filename pattern, an import syntax, or any other language-specific token is wrong unless framed per-language with a cross-reference. Authoritative conventions live in `spx/15-test-language.adr.md` for this product and in each `plugins/<lang>/skills/standardizing-<lang>-tests/SKILL.md` for consumers. Never write `test_*.py` (or any single-language pattern) into a skill body that ships to consumer projects — the file under audit may be a `.test.ts`, a `.rs` test module, or whatever the consumer's language plugin declares.
- ⚠️ **Python skill examples use `product.*` / `product_testing.*`** - Not `src.*` or `src_testing.*`. The `src` convention is ambiguous across Python ecosystems; `product` is unambiguous and signals "the thing we're building"
- ⚠️ **Audit skills (`auditing-*`) must be read-only** - They produce verdicts, not code changes. `allowed-tools` should not include `Write` or `Edit`. The calling workflow decides what happens after the verdict
- ⚠️ **NEVER weaken a spec to match code or tests** - When an audit finds an unfulfilled assertion, write the missing test or fix the implementation. The declaration governs. Removing or downgrading an assertion to make the audit pass is the exact failure mode the methodology exists to prevent.
- ⚠️ **Work plans MUST include audit gates** - After each structural step (tree surgery, spec authoring, test writing), run the relevant audit before proceeding. Do not batch all audits to the end — defects compound across steps.
- ⚠️ **Every change destined for the default branch passes through the local review gate first** - Before any `git push` of a PR branch, run the `changes-reviewer` agent on the working diff. The agent runs in an isolated context so the verdict is not biased by what the operator's main agent has been doing. When the agent is not installed (some consumer environments), fall back to the `/review-changes` slash command — both invoke the same `reviewing-changes` skill chain. The gate stops the push on any finding with `severity == "blocking"` or `severity == "debt"`. `follow_up` findings are fixed in-PR unless the fix would widen scope substantively, in which case the deferral is recorded in the relevant node's `ISSUES.md` or `PLAN.md`. `/opening-pr` Step 3 invokes this gate automatically; the spec assertion + `[eval]` evidence live at `spx/21-spec-tree.enabler/76-pr-workflow.enabler/pr-workflow.md` and `spx/21-spec-tree.enabler/76-pr-workflow.enabler/evals/local-review-gate/`.
- 🛑 **STOP TRIGGER — NEVER call `sleep` to wait or pace work** - No `sleep 30`, no `sleep 210; echo wake`, no `sleep` inside a backgrounded command, no `sleep` in a `while`/`until` loop. Every shell `sleep` spawns a subprocess (and file descriptors) the harness does not reliably reap; across turns and concurrent agents they accumulate until the host is exhausted and the agent is killed — this has happened in this repo. Wait via the runtime's timer mechanism instead — see "Process hygiene" below. If an earlier turn left a `sleep` running, identify it and terminate it by PID before doing anything else.

- ✅ **Always use `just test`** - Never bare pytest (just run loads .env automatically)
- ✅ **When uncertain, ASK STRUCTURED QUESTIONS. Never guess implementation patterns, test methodology or requirements.**
- ✅ **ALWAYS USE the runtime's structured-question tool for questions with predefined options.** Claude Code uses `AskUserQuestion`; Codex uses `request_user_input`. Do NOT use structured questions for open-ended questions where the user needs to provide free-form context — ask in plain text instead.
- ✅ **When you are wrong, KEEP ASKING STRUCTURED QUESTIONS. Never assume that you are bothering the user. As long as you are thinking deeply and asking high-leverage questions, you are doing the right thing.**
- ✅ **Dog-food platform features in skills** - When you discover an undocumented Claude Code capability (e.g., `skills:` field in subagents), check whether our skills teach it and update them if not
- ⚠️ **YAML `description:` fields must not contain word-then-colon mid-sentence** - A pattern like `description: ALWAYS invoke when: (1) ...` causes a YAML parse error: the parser reads `when:` as a nested key, silently drops all frontmatter, and the skill loads with empty metadata. Rephrase to avoid `when:`, `note:`, `if:`, and similar colon-containing words inside unquoted description values. Run `just check` after editing any SKILL.md to catch this before committing.

## Process hygiene

This harness spawns helper processes — a periodic `pgrep` to monitor background tasks, plus a shell and its children for every Bash call — and does not reliably reap them. A construct that creates many short-lived children (a poll loop), a long-lived child the monitor keeps polling (`gh run watch`, a backgrounded `sleep`, an idle keep-alive command), or several heavy process trees running at once will exhaust the per-user process limit: `posix_spawn` then returns `EAGAIN`, the monitor's `pgrep` keeps failing, and the agent is force-killed. The leak is not fixable here, so the rules below keep agents from triggering it. They apply with the tool names of the current runtime — Codex's `exec_command` is the equivalent of Bash, and so on.

### Waiting and re-checking never use a shell construct

No `while`/`until` poll loop. No `gh run watch`, in any form. No `sleep` to wait or pace work — foreground *or* backgrounded, on its own or in a loop. To wait for a build, CI run, process, or PR review to resolve, or to re-check on an interval, hand the wait to the runtime timer and let it re-invoke you:

- **Claude Code:** `/loop` for recurring work; `ScheduleWakeup` for a single delayed re-check (pass the continuation prompt so the next firing resumes the task).
- **Codex:** for waits where no process needs to stay open, such as GitHub PR reviews or CI runs, create a thread heartbeat through the Automations UI or any available runtime automation tool. The heartbeat may start a new thread, so the prompt must name the repository, PR number, branch, current thread purpose, and the exact state to inspect. Use a minute-based cadence such as every five minutes. Prefer this over keeping `exec_command` sessions open.

Example heartbeat prompt for a new thread: `In outcomeeng/plugins PR #25 on branch work/python-testing-pdr-alignment, inspect checks, formal reviews, PR comments, and inline review threads. Report only material changes. Continue the repository-governed review loop, and stop this heartbeat when the PR is merged, closed, or has no remaining review action.`

If an earlier turn left a `sleep` or a poll loop running, identify it and terminate it by PID before doing anything else.

### Background commands: one at a time, short-lived, never a keep-alive

Every backgrounded command is a process the monitor `pgrep`s on a timer. Run one at a time, only when the work genuinely must continue across a wait, and only when it will exit on its own. Never start a background command whose job is to "stay alive" — a pile of monitored processes (or one that never exits) is the `pgrep` storm itself.

### Heavy subprocess trees: sparingly, serially, load-aware

`just check`, a full `pytest` run, `uv run …`, and similar each fork dozens of children. Before launching one, read `uptime` and compare the sustained loadavg (the 5- and 15-minute figures) to the host's core count (`nproc`, or `sysctl -n hw.ncpu` on macOS): if loadavg exceeds it the machine is overcommitted — defer rather than pile on. Never run two heavy commands concurrently. Run `just check` once before committing, not repeatedly "to be sure".

### Other forks add up

- Don't spawn subagents you don't need — each is its own process tree.
- Redirect a long-running command's output to a file (`> /tmp/check.log 2>&1`) and read it in a separate call, rather than piping through `grep`/`tail`/`head` — the pipeline holds extra processes and file descriptors open for the command's lifetime.

## Plugin Portability Constraints

Plugins from this marketplace are installed into consumer projects that share none of this repository's tooling. When a skill or agent invokes a script that ships inside a plugin, the script runs against the consumer's environment — not against this repo's `uv`, `pyproject.toml`, or `outcomeeng_*` packages.

Authors of skills, agents, and the scripts they invoke must assume:

- ⚠️ **Only `plugins/` is guaranteed present.** Consumer checkouts do not contain `outcomeeng/`, `outcomeeng_evals/`, `outcomeeng_testing/`, `spx/`, or any other top-level directory from this repo. Anything a plugin script needs at runtime must live under that plugin's own directory tree.
- ⚠️ **`python3` only — no `uv`.** Skill content invokes scripts via `python3 "${CLAUDE_SKILL_DIR}/path/to/script.py"` — the skill loader substitutes the path before the agent sees it. Hooks (in `hooks/hooks.json`) and MCP server configs use `${CLAUDE_PLUGIN_ROOT}` instead, since they have no skill directory. Agent definition files (under `agents/`) get neither variable substituted in the prompt body and `${CLAUDE_PLUGIN_ROOT}` is not a Bash environment variable, so agents must reach `scripts/` only by invoking a skill that resolves the path. **Python 3.11 is the minimum version.** Scripts may use `StrEnum`, `tomllib`, exception groups, and other 3.11 features without conditional fallbacks; consumers on older Python must upgrade. No `uv run`, no `pip install`, no project-scoped virtualenv.
- ⚠️ **Stdlib only.** No `click`, no `pydantic`, no third-party JSON Schema, no `tomllib`-via-package. `argparse`, `json`, `dataclasses`, `enum`, `pathlib`, `subprocess`, `sys`, `typing` — that's the toolbox. Anything richer must be vendored or replaced.
- ⚠️ **No on-the-fly dependency installation.** Skills must not run `pip install`, `uv pip install`, `npm install`, or any other package fetch as part of their normal flow. Consumers approve plugin installation once; runtime side effects must not include further installations.

The `outcomeeng_*` Python packages in this repo are part of the marketplace's own toolchain (validation, distribution, eval harness) — they exist to build and test the plugins, not to be invoked by skills inside consumer projects. Code that lives outside `plugins/` is not portable.

When a skill genuinely needs richer Python machinery, the right answer is usually to write the logic in stdlib-only form, ship it inside the plugin, and document the `python3 "${CLAUDE_SKILL_DIR}/..."` invocation in the skill body.

## Read Tool Output

The `</output>` tag at the end of Read tool results is the tool's output delimiter — it is NOT part of the file content. Never treat it as a "stray closing tag" or attempt to remove it from files.

## Markdown Formatting Rules

**IMPORTANT: Pseudo-XML in Markdown Code Fences**

When documenting XML-like syntax that isn't valid XML (pseudo-XML with text content, no proper elements), **ALWAYS use `text` as the language identifier**, not `xml`:

```text
<!-- ✅ CORRECT: Use "text" for pseudo-XML -->
<metadata>
  timestamp: [UTC timestamp]
  product: [Product name]
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

## Plugin Catalog

Every skill, agent, and command across every plugin is listed in the auto-generated catalog in [`README.md`](README.md#plugins), sourced from `.claude-plugin/marketplace.json` and the YAML frontmatter of each plugin's `SKILL.md`, `agents/*.md`, and `commands/*.md`. Run `just docs` to regenerate; `just check` enforces freshness. Do not maintain plugin tables in this file.

## Spec Tree Methodology

The Spec Tree methodology for [Outcome Engineering](https://outcome.engineering). Three steps drive the methodology: **declare, spec, apply**. Audit gates operate within each step. See `plugins/spec-tree/skills/understanding/references/durable-map.md` for the authoritative methodology reference.

| Step        | What happens                  | Node state after |
| ----------- | ----------------------------- | ---------------- |
| **Declare** | Write spec (assertions)       | Declared         |
| **Spec**    | Write tests (make verifiable) | Specified        |
| **Apply**   | Write implementation code     | Passing          |

Planning artifacts are ephemeral — `PLAN.md` and `ISSUES.md` are committed escape hatches that `/handoff` leaves in node directories. They carry deferred plans and known issues, not spec truth; `/contextualizing` reads them, conformance checks skip them, and they are removed once resolved.

### Spec-tree navigation: declaration and inverse

The methodology declares forward:

```text
PDR/ADR → spec assertion → [test](path) link → test file → import → implementation file
```

The PR flow, the apply flow, and any code-change workflow need the *inverse* — from a code change in the diff back to the spec that governs it:

```text
implementation file
  → grep imports across spx/**/tests/  (per-language import syntax)
  → set of test files
  → spec assertions linking those test files via [test]
  → containing node directory under spx/
```

`spx/` contains only specs, decision records, escape hatches, and `tests/` subdirectories. Implementation code lives outside `spx/` (in `plugins/`, in `outcomeeng/`, etc.). The inverse navigation walks from an outside-`spx/` file in the diff, through the import graph into an inside-`spx/` test, then up to the spec assertion linking that test, then up to the containing node.

If multiple implementation files in the diff resolve to multiple nodes, take their lowest common ancestor in the tree — `/contextualizing` on the LCA pulls constraining context for every descendant.

An implementation file in the diff that no test imports has no governing spec assertion — a coverage gap the PR is shipping. Specs declare; tests verify; code complies. Surface the gap; do not invent a node to load.

Per-language test conventions live in `spx/15-test-language.adr.md` (this product uses pytest with `test_<subject>.<evidence>.<level>.py`) and in each language plugin's `standardizing-<lang>-tests` skill. In a consumer repo, the consumer's spec tree and language plugin determine the conventions; the inverse-navigation procedure is the same.

### Archiving a stale session without `/release`

`/release` runs the full reflection-and-persistence protocol before archiving. When pickup loads a session whose declared scope has already landed (verified by reading the session file and `git log`), and the conversation produced no new insights, escape hatches, or methodology changes, run `spx session archive <session-id>` directly:

```bash
spx session archive 2026-04-01_10-44-24
```

The shortcut is valid only when the agent has already inspected the session content and confirmed that reflection would surface nothing. For any session where the agent did meaningful work this conversation, run `/release` so reflection actually happens.

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

## For Claude Agents Modifying This Marketplace

### ⛔ Subagent Restrictions

**NEVER use subagents (Agent tool) to create or modify any file.** All file creation and modification must happen in the main conversation context using Read, Edit, and Write tools directly. Subagents are for research, exploration, and auditing only.

### ⛔ Path Restrictions

**NEVER manually write to these locations:**

- `~/.claude/` - User home directory, not product-specific
- Any path containing `.claude` in user home
- `.claude/` files, except `.claude/settings.json` updates produced by Claude CLI product-scope plugin commands

**ALWAYS write to product directories:**

- `plugins/` - Plugin code, skills, commands, templates
- `spx/` - Specs as durable map (see [spx/CLAUDE.md](spx/CLAUDE.md))
- `.spx/` - Tool operational files (sessions, cache) - gitignored
- `.claude/settings.json` - Claude product-scope plugin settings created by `claude plugin ... --scope project` and committed for collaborators
- `.codex/config.toml` - Codex product-scope config for the plugin set this repository needs
- Product root - Package files, config files

**Rationale:** Manual file operations in `.claude/` require extra permission and break workflow. Claude CLI product-scope plugin commands are the exception because they update `.claude/settings.json` for the repository's shared plugin set. Codex product config belongs in `.codex/config.toml` so collaborators inherit the plugin enablement for this repo after trusting the project.

### ⛔ File Removal Restrictions

**Tracked files with no changes:** Use `git rm` to remove files that are committed in git and have no uncommitted modifications.

**All other files:** You CANNOT remove files that are untracked or have uncommitted changes. Do not attempt to circumvent this restriction. Instead, **ALWAYS** provide the exact `rm` command to the user and **WAIT** until the user has confirmed they have executed it before proceeding.

### Before Making Changes

1. **Read the context**: Check [CLAUDE.md](CLAUDE.md:1) (this file) for current structure
2. **Check existing commands**: Use Glob to find existing `.md` files in `plugins/*/commands/`
3. **Review plugin structure**: Each plugin has its own `plugin.json` in `.claude-plugin/`
   - Codex-capable plugins also have `.codex-plugin/plugin.json`

### After Adding/Modifying Commands or Skills

Commit and open the PR through the steps in [Git workflow](#git-workflow) — `/committing-changes` then `/open-pr`.

**When adding a new plugin**, register it in **both** marketplace catalogs:

| File                               | Surface     |
| ---------------------------------- | ----------- |
| `.claude-plugin/marketplace.json`  | Claude Code |
| `.agents/plugins/marketplace.json` | Codex       |

`just check` will fail if a plugin directory is missing from either catalog.

### Top-level layout

- `plugins/` — skills, agents, commands shipped to consumer repos. One subdirectory per plugin. The plugin catalog in [`README.md`](README.md#plugins) is authoritative for what each plugin contains; this file does not duplicate it.
- `spx/` — this product's spec tree (durable map). See [`spx/CLAUDE.md`](spx/CLAUDE.md). Per-node `local/` holds product-specific skill overlays.
- `outcomeeng/`, `outcomeeng_testing/`, `outcomeeng_evals/` — this product's Python toolchain (validation, distribution, eval harness) and its test infrastructure. Not portable to consumer projects; do not import from inside any plugin.
- `.claude-plugin/marketplace.json` — Claude Code marketplace catalog (one entry per shipped plugin).
- `.agents/plugins/marketplace.json` — Codex marketplace catalog (mirror of the above).
- `.spx/` — gitignored operational files (sessions, audit state).
- `.claude/settings.json`, `.codex/config.toml` — product-scoped runtime settings, committed for collaborators.
- `AGENTS.md` (this file), `CLAUDE.md` (symlink to `AGENTS.md`), `REVIEW.template.md` — repo-level instruction surfaces.

For the contents of any plugin or `spx/` subdirectory, run `ls` or read the catalog. The directory layout under each plugin follows the conventions in `plugins/develop/skills/`.

## Git workflow

### Autonomy

In this marketplace the agent operates the git workflow autonomously. The conservative system default — "ask before every commit, push, and PR action" — is **overridden** here. Standing authorization covers:

- Committing changes via `/committing-changes` (the skill loads the marketplace's commit rules from `spx/local/committing-changes.md`; the agent does not bypass the skill).
- Pushing the feature branch via `/opening-pr` (which runs the branch-hygiene checks and `git push -u origin HEAD:refs/heads/<branch>`).
- Opening the draft PR via `/opening-pr` (which calls `gh pr create --draft` with a curated title and body).
- Iterating on the PR via `/managing-pr` (commit + push + base-sync rebase with a `--force-with-lease` push of the PR's own feature branch + heartbeat + review inspection).
- Merging via `/managing-pr` under the gate-green-autonomous default declared by `/standardizing-merging` `<pr_authority_gate>` and refined in `spx/local/merging.md`.

The skills are mandatory: every commit goes through `/committing-changes`; every PR open goes through `/opening-pr`; every PR iteration goes through `/managing-pr`. The agent never invokes `git commit`, `git push`, `gh pr create`, or `gh pr merge` outside the skill flow.

The autonomy does **not** cover: blind force-push (`git push --force`) or force-push of any shared or protected branch, branch deletion on the remote outside the merge flow, direct push to `main` outside `just push-marketplace`, skipping pre-commit hooks (`--no-verify`), skipping commit signing, or any action explicitly forbidden by the Git Safety Protocol or `<self_reference_policy>`. Those still require explicit human instruction in the same turn. The `--force-with-lease` push of the PR's own feature branch that `/managing-pr` performs after a base-sync rebase is covered by the standing authorization above — it is a guarded non-fast-forward push of the agent's own branch, not a blind overwrite.

Use the workflow the user chooses for the current change. Pull requests are the default path for feature work, production behavior changes, broad refactors, publishing changes, and anything that needs review. Node-local `PLAN.md` and `ISSUES.md` coordination files may be committed directly when the user needs collaborators to see the coordination state immediately.

### Lifecycle

For pull-request work, the path is:

1. **Branch.** Cut a feature branch off `origin/main` — `fix/…`, `feat/…`, `docs/…`, or `work/…`.
2. **Bump plugin versions** when the branch's first plugin-distribution commit is about to land. Run `just bump-dry` to preview, then `just bump` to write — the tool detects every plugin with changes under `plugins/<name>/**` since `origin/main`, classifies each plugin's change pattern into a semver segment (a plugin that gains, loses, or renames a skill/command/agent/manifest gets `minor`; everything else gets `patch`), and writes the resulting version in every manifest each plugin owns (`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`). The same run can produce `minor` for one plugin and `patch` for another. The tool refuses to write when the branch already carries a bump (per `spx/local/committing-changes.md`'s "bump once per branch" rule). Auto-detection never selects `major` — pass `--segment major` (or `minor`/`patch`) to force a segment for every changed plugin; explicit overrides emit a stderr warning naming any plugin whose detected segment differed. The mutually-exclusive `--check` mode exits non-zero if any changed plugin still needs a bump; CI calls `just bump-check` to enforce that every PR carries its version bump.
3. **Commit.** Invoke `/committing-changes`. It loads the marketplace's commit rules — Conventional Commits, the version-bump policy, which manifests to touch — from `spx/local/committing-changes.md`.
4. **Open the PR.** Invoke `/open-pr`. It runs branch-hygiene checks, pushes the branch with an explicit destination ref (`git push -u origin HEAD:refs/heads/<branch>`), opens a draft PR with a curated title and body, and creates or requests a thread heartbeat so review/check re-inspection is handled by the runtime timer instead of a shell wait or watch loop. If the runtime can only create a new thread, seed that heartbeat with the repository, PR number, branch, and review-loop instructions. It loads `spx/local/opening-pr.md` for the marketplace-specific pre-flight checks and template sections.
5. **Review and merge.** Invoke `/managing-pr`. It drives the post-creation loop — three-surface review inspection, three-severity triage of findings, follow-up pushes — and merges autonomously when `<merge_gate>` passes. The marketplace's `spx/local/merging.md` overlay loads via `/standardizing-merging` `<repo_local_overlay>` and supplies the project-specific merge command, closure gate, and post-merge sync; merge authority stays on the skill's autonomous default. The overlay's merge command is `gh pr merge <n> --merge` followed by `git push origin --delete <branch>` (the rebase-merge default conflicts with the marketplace's merge-commit history style; the separate remote-delete sidesteps the multi-worktree failure where `git checkout main` errors when `main` is already checked out elsewhere). Verify the merge with `gh pr view <n> --json state,mergedAt,mergeCommit`.
6. **Sync.** Once a PR with plugin distribution changes merges, refresh your local marketplace install:

   ```bash
   git switch main && git pull
   just sync-marketplace <previous-main-ref>
   ```

   `just sync-marketplace` refreshes the local Claude marketplace cache, preserves the Codex cache compatibility symlinks, and runs `validate_install` and `check-installed`. It accepts an optional base ref; when the range from that ref to `HEAD` has no changes under `plugins/`, `.claude-plugin/`, or `.agents/plugins/`, it exits without refreshing the marketplace. It does not push or pull — do the `git pull` yourself first.

### Publishing directly to `main`

When the user chooses direct `main` publication, commit intentionally, run the relevant validation gate for the files changed, and push using the product's publishing command when one exists. In this marketplace, use `just push-marketplace` rather than bare `git push`; the recipe pushes first, then refreshes the local marketplace only when the pushed range changed plugin distribution files:

```bash
just push-marketplace               # git push (current branch) + just sync-marketplace
just push-marketplace origin main   # explicit remote/branch
```

Bare `git push origin main` skips the change-aware publish wrapper. For plugin distribution changes that means the local marketplace stays stale, the Codex compatibility symlinks are not created, and `validate_install` never runs.

⚠️ **NEVER run `claude plugin update`, `claude plugin marketplace update`, or `codex plugin marketplace upgrade` by hand.** These are the primitives that `just sync-marketplace` (and therefore `just push-marketplace`) already orchestrates in the right order. Running them manually risks the wrong product scope, steps out of order, or skipped post-install validation. Read the Justfile before any marketplace operation.

### How the marketplace cache resolves to skill content

`.claude-plugin/marketplace.json` declares each plugin with a relative `source: "./plugins/<name>"` path. The runtime resolves every install — pinned or unpinned — through the versioned cache directories under `~/.claude/plugins/cache/outcomeeng/<plugin>/<version>/`. Each `claude plugin marketplace upgrade` adds a new version directory; prior version directories persist alongside it. Per `spx/13-infrastructure.enabler/32-installation.enabler/21-claude-cache-preservation.pdr.md`, the marketplace sync recipe replaces prior version directories with symlinks to the current version, so any resolved version path lands on the same content.

The Skill tool loads SKILL.md content into per-session memory the first time the skill is invoked. `/reload-plugins` re-indexes the cache and re-reads SKILL.md from disk during registration; first invocations after the reload pick up the disk content. Skills already loaded into session memory keep their cached content for the rest of the session until compaction re-attaches from disk.

### Smoke-testing skill changes

While the change is still on your feature branch:

1. Edit the working-tree skill files.
2. Commit, then run `just sync-marketplace` (or `just push-marketplace` if pushing at the same time).
3. Run `/reload-plugins`.
4. Invoke the skill — first invocation after the reload reads the new content from the cache.

The sync recipe propagates working-tree changes into the cache directories that `/reload-plugins` re-indexes. Without it the cache stays at the prior published state and reload re-reads the same bytes. After a PR merge or direct `main` publication that changes plugin distribution files, `git switch main && git pull && just sync-marketplace <previous-main-ref>` followed by `/reload-plugins` brings every layer current — working tree, marketplace catalog, per-session memory.

## Missing plugins or skills

### Claude Code

When repo-required Claude plugins are missing, ask the user before changing product-scoped Claude settings. Use Claude's product scope so the marketplace and enabled plugins are written to `.claude/settings.json`; commit that file so collaborators get the same plugin set.

```bash
claude plugin marketplace add outcomeeng/plugins --scope project

for plugin in develop python prose spec-tree; do
  claude plugin install "${plugin}@outcomeeng" --scope project
done
```

If an installed product-scoped plugin has been disabled, re-enable it at product scope:

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

Enable plugins per product by committing `.codex/config.toml`. Keep the product list explicit so each repo gets only the plugins it needs:

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

If a user's global Codex config already enables a plugin that the product should keep off, add an explicit product override:

```toml
[plugins."typescript@outcomeeng"]
enabled = false
```
