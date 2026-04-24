# PLAN — Commands cluster + shared mechanics refactor

**Status:** deferred. This plan is an escape hatch to be executed in a fresh session. Delete this file when the work lands.

## Context

After the `standardizing-skills` refactor (commit 73b60cb + follow-up), the develop plugin has a clean skills cluster (`21-skills.enabler/`) but no parallel cluster for commands or subagents. Investigation showed:

- **Subagents cluster depends on skills** — `/creating-subagents` already loads `/standardizing-skills` for XML structure principles. This is documented by the node-ordering: skills at 21, subagents higher.
- **Commands cluster is independent** — `/creating-commands` and `/auditing-commands` share no standards with skills.

But the "independent" framing hides a problem: commands and skills share ~30% of their underlying rules — `!` bash safety, Claude Code variable scopes (`${CLAUDE_PLUGIN_ROOT}` etc.), and `allowed-tools` semantics. Those rules currently live only in `/standardizing-skills`. Any future `/standardizing-commands` would either duplicate them (drift risk) or cross-reference `/standardizing-skills` (commands reading skill-structural standards is conceptually wrong).

The right home is `/standardizing-agent-prompts`. It already covers cross-artifact prose conventions (voice, descriptions, constraint language, anti-patterns). Extending it to own the shared *mechanical* rules gives all three clusters — skills, commands, subagents — one source of truth for platform-level plumbing.

## Outcome

- `/standardizing-agent-prompts` owns every rule that applies to prompt artifacts regardless of type (skills, commands, subagents).
- `/standardizing-skills` sheds its cross-artifact content and keeps only skill-specific standards.
- A new `/standardizing-commands` is created covering command-specific standards.
- Skills, commands, and subagents clusters all load `/standardizing-agent-prompts` first, then their type-specific reference.

## What moves where

### Out of `/standardizing-skills` → into `/standardizing-agent-prompts`

| Section                                                                                                                               | Reason                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `<bash_expansion_restrictions>` (via `references/platform-constraints.md`)                                                            | Claude Code `!` safety checker applies to skills, commands, subagent tool calls |
| Variable scopes table (in `<templates_and_variables>`) — `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `$CLAUDE_PROJECT_DIR` rows | Runtime variables are cross-artifact                                            |
| `allowed-tools` field semantics (the prose explaining the field, not per-type examples)                                               | Same field, same semantics, across all three artifact types                     |

### Stays in `/standardizing-skills`

| Section                                                           | Reason                                                                                                                                                               |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<frontmatter>`                                                   | Skill-specific field set (`disable-model-invocation`)                                                                                                                |
| `<naming_conventions>`                                            | Gerund convention, directory-match rule                                                                                                                              |
| `<descriptions>`                                                  | Activation-rate research is skill-specific (auto-activation doesn't apply to commands)                                                                               |
| `<xml_structure>`                                                 | Required tags + conditional tags are skill-specific (commands have different required tags)                                                                          |
| `<progressive_disclosure>`                                        | SKILL.md < 500 lines, references/ pattern                                                                                                                            |
| `<conciseness>`                                                   | Carries over to commands but reads well as a skill principle; OK to duplicate the test sentence in commands if needed                                                |
| `<skill_types>` (6-type taxonomy)                                 | Pure skill concept                                                                                                                                                   |
| `<reference_skills>`                                              | Pure skill concept                                                                                                                                                   |
| `${CLAUDE_SKILL_DIR}` row (of variables)                          | Skill-specific variable                                                                                                                                              |
| `<nested_code_fences>` (via `references/platform-constraints.md`) | dprint/`markup_fmt` rule — applies to markdown body in any artifact, but the current content lives alongside bash restrictions. Move both to agent-prompts or split. |
| `<xml_tag_formatting>` (blank-line rule)                          | Markdown-parser rule applies to any pseudo-XML in prompts; decide whether to promote                                                                                 |
| `<validation_rule>`                                               | Applies to scripts authored alongside skills; could move if commands also ship scripts                                                                               |
| `<script_testing_rule>`                                           | Applies to `scripts/` inside skills; commands rarely ship scripts — probably stays skill-specific                                                                    |

**Open question 1:** `<nested_code_fences>` and `<xml_tag_formatting>` are about markdown authoring for prompt bodies. They apply to skills, command bodies, subagent bodies alike. Promote to `/standardizing-agent-prompts` or leave in `/standardizing-skills` with cross-reference from commands/subagents?

### Into new `/standardizing-commands`

| Section                                                                                                                         | Source                                                           |
| ------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Command frontmatter spec (`description`, `argument-hint`, `model`, `allowed-tools`)                                             | Extract from `creating-commands/SKILL.md` + references           |
| Command XML body tags (required: `<objective>`, `<process>`, `<success_criteria>`; conditional: `<context>`, `<examples>`, ...) | Extract from `creating-commands/SKILL.md`                        |
| Argument handling (`$ARGUMENTS`, `argument-hint` semantics)                                                                     | Extract from `creating-commands/references/arguments.md`         |
| `!` expansion *usage patterns* for dynamic context                                                                              | Extract from `creating-commands/references/patterns.md`          |
| `allowed-tools` patterns specific to commands                                                                                   | Extract from `creating-commands/references/tool-restrictions.md` |
| Command file placement (`.claude/commands/` vs `~/.claude/commands/`)                                                           | Extract from `creating-commands/SKILL.md`                        |

Safety restrictions for `!` expansion are inherited from `/standardizing-agent-prompts`, not repeated.

### `/creating-commands` and `/auditing-commands` shrink

After the extraction:

- `/creating-commands/SKILL.md` becomes a router + workflows, parallel to the post-refactor `/creating-skills` (~100 lines).
- `/creating-commands/references/` keeps only workflow content (patterns for intent-based commands, pattern examples for dynamic context *usage*); deletes standards duplicates.
- `/auditing-commands/SKILL.md` `<critical_workflow>` reads `/standardizing-agent-prompts` + `/standardizing-commands` only. Drops any creating-commands/references reads (if any exist — audit current state).

## Scope tension — flag before executing

`/standardizing-agent-prompts` currently declares in its own `<objective>`:

> "This skill governs prompt *craft* (how to write text). Prompt *structure* (which XML tags to use, file organization) is governed by the creator skills themselves."

Option 2 expands that scope to include *platform-level runtime plumbing* (bash safety, variable scopes). Two ways to handle:

- **(a) Rename and broaden.** Rename to `/standardizing-prompt-artifacts` or similar. Update the objective to cover prose craft + runtime plumbing. Cleanest semantics; touches every consumer that references the old name.
- **(b) Keep the name, broaden the scope silently.** Update the objective to include runtime plumbing but keep the name. Less churn; the name becomes slightly less accurate.

**Recommendation:** (b) for the follow-up session. The skill name is already loaded by three clusters and referenced in audit workflows; renaming multiplies the scope. A crisp scope-expansion note in the objective (`"covers shared prose conventions AND runtime plumbing that apply across skills, commands, and subagents"`) is enough.

**Open question 2:** Confirm which option before starting the file moves.

## Execution sequence

1. **Expand `/standardizing-agent-prompts`** — add `<bash_safety>`, `<runtime_variables>`, `<allowed_tools>` sections. Update the objective. If promoting `<nested_code_fences>` and `<xml_tag_formatting>`, add those too.
2. **Trim `/standardizing-skills`** — remove the promoted sections; replace with a single cross-reference at the top: "Read `/standardizing-agent-prompts` for runtime plumbing (bash, variables, allowed-tools) that applies to every prompt artifact."
3. **Update the `/standardizing-skills` reference file `platform-constraints.md`** — either delete (if fully absorbed into agent-prompts) or retain only skill-specific content.
4. **Create `/standardizing-commands`** — new reference skill with `disable-model-invocation: true`, passive description, and the command-specific standards listed above.
5. **Rewrite `/creating-commands/SKILL.md`** as a router — same shape as the post-refactor `/creating-skills/SKILL.md`. Preserve the workflows and references that are genuinely command-authoring workflow (not standards).
6. **Delete obsolete `/creating-commands/references/` content** — the standards sections that moved out.
7. **Rewrite `/auditing-commands/SKILL.md` `<critical_workflow>`** — reads `/standardizing-agent-prompts` and `/standardizing-commands` only.
8. **Update subagents** — `/creating-subagents/SKILL.md:250` and `/creating-subagents/references/writing-subagent-prompts.md:12` currently cross-reference `/standardizing-skills` for XML structure. After the refactor, the XML structure rules they need (nested code fences, XML tag formatting) may live in `/standardizing-agent-prompts`. Update the cross-references accordingly.
9. **Update spec tree** — this enabler (`43-develop.enabler/`) gains a sibling pair alongside `21-skills.enabler/`:
   - `21-commands.enabler/commands.md` (independent of skills)
   - `32-subagents.enabler/subagents.md` (depends on skills via XML rules; and depends on commands? probably not — confirm)
10. **Run verifications** — self-audit each refactored skill; grep for dangling references to `/standardizing-skills` that should now point to `/standardizing-agent-prompts`.

## Verification

- Every artifact type's auditor (`/auditing-skills`, `/auditing-commands`, `/auditing-subagents`) reads exactly two references: `/standardizing-agent-prompts` and the type-specific `/standardizing-{type}`.
- No rule appears in more than one standardizing-* skill — grep for bash-safety keywords, variable-scope table entries, `allowed-tools` prose should each return one home.
- `/auditing-skills` passes against every refactored skill.
- The `43-develop.enabler/` sibling tree has three child enablers with correct dependency indices.

## Open questions to resolve at session start

1. **Nested code fences + XML tag formatting**: promote to `/standardizing-agent-prompts` or keep in `/standardizing-skills` with cross-reference?
2. **Rename `/standardizing-agent-prompts`?** Recommendation says no; confirm.
3. **Does `/standardizing-subagents` need to exist?** Current state: `/creating-subagents` has its own in-line standards. If the refactor also creates `/standardizing-subagents`, the develop plugin ends up with three parallel reference skills (skills, commands, subagents) + `/standardizing-agent-prompts`. That's four. Decide whether subagents gets its own standardizer or continues referencing `/standardizing-skills` (which becomes conceptually odd after the refactor).
4. **Audit of `/creating-commands/references/patterns.md` (828 lines)** — almost certainly mixes standards and workflow. Classify before splitting.

## What this session produced

- `spx/43-develop.enabler/develop.md` — removed the skill-enumeration paragraph, kept aggregate compliance rules
- `spx/43-develop.enabler/21-skills.enabler/skills.md` — new child enabler for the skills-about-skills cluster with 5 compliance assertions
