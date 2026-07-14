<contents>

- `<overview>` — runtime syntax and input-contract principles
- `<arguments>` — argument declaration, substitution, and empty-input behavior
- `<dynamic_context>` — bounded state-dependent context injection
- `<tool_restriction_security>` — runtime-specific capability boundaries
- `<file_references>` — product files and bundled skill files

</contents>

<overview>

A SKILL.md carries every capability a slash command had — arguments, `!`-dynamic context injection, tool restriction, and `@` file references. These rules govern that surface; `/audit-skills` enforces them and `/create-skills` teaches them.

{!# Authored marketplace source targets Claude Code SKILL.md syntax; the build renders target-native Codex guidance. #!}
{!% if target == 'claude' %!}
Use Claude Code's supported SKILL.md syntax.
{!% else %!}
Use Codex's supported skill syntax.
{!% endif %!}

Prefer stable forms that preserve the caller's input contract:

- Use `$ARGUMENTS` for free-form whole-instruction capture, especially when one skill forwards instructions to another skill or when a user-invoked skill accepts natural-language instructions.
- Use positional or named arguments when each argument has a stable token boundary and a named variable improves reliability for a skill invocation or wrapper.
- Use richer runtime-specific forms only when the active runtime documents them and they preserve the skill's input contract.

</overview>

<arguments>

A skill that operates on user-supplied input handles it explicitly:

- **`argument-hint`** — free-text autocomplete hint shown after `/skill-name`. Present whenever the skill takes arguments; omit for self-contained skills.
- **`$ARGUMENTS`** — consumes the full raw instruction string. Use it when preserving whitespace and multi-word intent matters, including forwarding instructions between lifecycle skills.
- **`$ARGUMENTS[N]` or `$N`** — consumes a numbered positional value when the position is stable and a name would add no clarity.
- **`arguments` with `$name`** — names positional arguments the body substitutes as `$name` (space-separated string or YAML list; names map to positions in order). Use it when a stable token has a domain name, such as `$configured_agent_path`.
- **Integration** — reference each declared `$name` where the body consumes it (e.g. "Audit the skill at `$skill_path`"), never as unused decoration. An argument declared but never substituted, or substituted but never declared, is a defect.
- **Empty arguments** — a skill that requires input states the requirement and what it does when input is absent; a skill that works with or without input states the fallback (e.g. "operate on the current selection when `$target` is empty" or "use the current changeset when `$ARGUMENTS` is empty").

- ALWAYS: declare `argument-hint` when the skill takes arguments.
- ALWAYS: preserve whole-string capture with `$ARGUMENTS` when collapsing input into positional tokens would change behavior.
- ALWAYS: substitute every declared named argument in the body, and declare every `$name` the body substitutes.
- NEVER: migrate a free-form instruction skill from `$ARGUMENTS` to a named positional argument unless the runtime contract proves the named argument preserves the full rest-of-line input.
  {!% if target == 'claude' %!}
- NEVER: require authored source to avoid Claude-supported syntax solely because Codex generated output may need a different form; the marketplace renderer owns Codex adaptation.
  {!% else %!}
- NEVER: use an argument form the Codex skill surface does not support; choose a documented Codex form that preserves the caller's input contract.
  {!% endif %!}

Examples:

- Free-form forwarding: `/merge` reads `$ARGUMENTS` and forwards `$ARGUMENTS` verbatim to `/manage-github-pr`, preserving multi-word instructions.
- Stable token: `arguments: configured_agent_path` with `$configured_agent_path` names one path-like positional value for an audit skill.

</arguments>

<dynamic_context>

A skill injects state-dependent context with the `!`-backtick form inside `<context>` — the same mechanism a command used. The firing-and-filtering rules in `<xml_structure>`'s `<context>` guidance govern it: every `!` line runs on every skill load, including false-positive activations, so:

- Load context only when it is directly relevant to the skill's task — a security-review skill needs git state; a pure-reasoning skill needs none.
- Filter every command so output stays bounded (`--status`, `head -N`, `--oneline`) and never grows monotonically.

- ALWAYS: scope `<context>` `!` commands to state the skill actually consumes, filtered to bounded output.
- NEVER: inject state-dependent context the skill does not read, or an unfiltered command whose output grows per load.

</dynamic_context>

<tool_restriction_security>

{!% if target == 'claude' %!}
`allowed-tools` restricts what a skill may do without per-call approval — a security boundary, not only a convenience:

- **Specificity** — restrict bash to the narrowest pattern that works: `Bash(git add:*)`, `Bash(git commit:*)`, never bare `Bash` or `Bash(git *)` when specific verbs suffice. A broad grant re-admits the destructive and exfiltrating commands the restriction exists to bar.
- **Destructive-operation containment** — a skill that must not delete, force-push, or deploy omits the tools that would let it; the allow-list is the containment.
- **Data-exfiltration containment** — a read-only analysis skill omits `Bash`, `WebFetch`, and `Write` so it cannot send local content outward; grant them only when the task needs them.
- **Read-only audits** — an `audit-*` skill carries `Read, Grep, Glob, Bash` (plus `Skill` when it composes another skill) and never `Write`/`Edit`, per the read-only audit rule.

- ALWAYS: grant the narrowest `allowed-tools` the skill's task needs, restricting bash to specific verb patterns.
- NEVER: grant a destructive or network tool a skill's task does not require, or leave a security-sensitive skill unrestricted.
  {!% else %!}
  Codex skill metadata names supported capability boundaries; it does not enforce Claude-style shell-subcommand patterns such as `Bash(git add:*)`.

- ALWAYS: render only Codex-supported tool identifiers or capability categories in `allowed-tools`.
- ALWAYS: keep exact command constraints in workflow prose and follow the active Codex approval policy for each shell call.
- ALWAYS: omit shell from `allowed-tools` when Codex cannot express the workflow's narrow command boundary; require per-call approval instead.
- NEVER: replace a narrow Claude shell grant with bare `Bash` in Codex output.
- NEVER: describe a shell-subcommand pattern in Codex skill metadata as an approval or containment boundary.
  {!% endif %!}

</tool_restriction_security>

<file_references>

{!# Source-only maintainer guidance: use the file and tool template globals for
runtime-divergent product filenames and tool names. Generated runtime guidance
must contain the resolved name and no renderer syntax. Skill-directory tokens
are handled separately by the build's target rewrite. #!}

Use the active runtime's product filename and tool name:

```markdown
Read `{{! file('root_guide') !}}` for the active runtime's product guide.
Use `{{! tool('ask_user') !}}` for the active runtime's structured-question tool.
```

A skill body references a specific product file with the `@` prefix (`@path/to/file`), injecting its content — the same affordance a command had. Use `@` for product files in the consumer's tree; combine it with an argument (`@$target`) for a caller-named product file.

For skill-bundled files, use the runtime's skill-directory token instead of `@` or a repository path:

```markdown
Read `${CLAUDE_SKILL_DIR}/references/<bundled-reference>.md`
Run `python3 "${CLAUDE_SKILL_DIR}/scripts/<bundled-script>.py" <args>`
```

NEVER reference bundled plugin files with repository-local source or generated paths, or with legacy plugin-root paths. If a skill needs a file owned by another skill or another plugin, name the owning workflow or capability rather than manufacturing a cross-plugin filesystem path.

</file_references>
