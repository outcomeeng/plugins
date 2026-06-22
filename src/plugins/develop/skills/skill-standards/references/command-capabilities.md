<overview>

A SKILL.md carries every capability a slash command had — arguments, `!`-dynamic context injection, tool restriction, and `@` file references. These rules govern that surface; `/audit-skills` enforces them and `/create-skills` teaches them. Author each capability the skill way, not the command way: a command's `$ARGUMENTS` / `$1` maps to a skill's `arguments` field with `$name` substitution.

</overview>

<arguments>

A skill that operates on user-supplied input declares it explicitly:

- **`argument-hint`** — free-text autocomplete hint shown after `/skill-name`. Present whenever the skill takes arguments; omit for self-contained skills.
- **`arguments`** — names the positional arguments the body substitutes as `$name` (space-separated string or YAML list; names map to positions in order). This is the skill analog of a command's `$ARGUMENTS` (all args) and `$1`/`$2`/`$3` (positional): a command names positions by number, a skill names them by identifier.
- **Integration** — reference each `$name` where the body consumes it (e.g. "Audit the skill at `$skill_path`"), never as unused decoration. An argument declared but never substituted, or substituted but never declared, is a defect.
- **Empty arguments** — a skill that requires an argument states the requirement and what it does when the argument is absent; a skill that works with or without one states the fallback (e.g. "operate on the current selection when `$target` is empty").

- ALWAYS: declare `argument-hint` when the skill takes arguments.
- ALWAYS: substitute every declared argument in the body, and declare every `$name` the body substitutes.
- NEVER: copy a command's bare `$ARGUMENTS` / `$1` into a skill body — skills name arguments through the `arguments` field.

</arguments>

<dynamic_context>

A skill injects state-dependent context with the `!`-backtick form inside `<context>` — the same mechanism a command used. The firing-and-filtering rules in `<xml_structure>`'s `<context>` guidance govern it: every `!` line runs on every skill load, including false-positive activations, so:

- Load context only when it is directly relevant to the skill's task — a security-review skill needs git state; a pure-reasoning skill needs none.
- Filter every command so output stays bounded (`--status`, `head -N`, `--oneline`) and never grows monotonically.

- ALWAYS: scope `<context>` `!` commands to state the skill actually consumes, filtered to bounded output.
- NEVER: inject state-dependent context the skill does not read, or an unfiltered command whose output grows per load.

</dynamic_context>

<tool_restriction_security>

`allowed-tools` restricts what a skill may do without per-call approval — a security boundary, not only a convenience:

- **Specificity** — restrict bash to the narrowest pattern that works: `Bash(git add:*)`, `Bash(git commit:*)`, never bare `Bash` or `Bash(git *)` when specific verbs suffice. A broad grant re-admits the destructive and exfiltrating commands the restriction exists to bar.
- **Destructive-operation containment** — a skill that must not delete, force-push, or deploy omits the tools that would let it; the allow-list is the containment.
- **Data-exfiltration containment** — a read-only analysis skill omits `Bash`, `WebFetch`, and `Write` so it cannot send local content outward; grant them only when the task genuinely needs them.
- **Read-only audits** — an `audit-*` skill carries `Read, Grep, Glob, Bash` (plus `Skill` when it composes another skill) and never `Write`/`Edit`, per the read-only audit rule.

- ALWAYS: grant the narrowest `allowed-tools` the skill's task needs, restricting bash to specific verb patterns.
- NEVER: grant a destructive or network tool a skill's task does not require, or leave a security-sensitive skill unrestricted.

</tool_restriction_security>

<file_references>

A skill body references a specific file with the `@` prefix (`@path/to/file`), injecting its content — the same affordance a command had. Use it for a file the skill always reads; combine it with an argument (`@$target`) for a caller-named file. Prefer a `${CLAUDE_SKILL_DIR}` path for skill-bundled files (see `references/runtime-variables.md`); `@` is for product files in the consumer's tree.

</file_references>
