<contents>

- `<overview>` — the command-capability surface and the portable syntax
- `<arguments>` — `argument-hint`, `$ARGUMENTS`, named and positional arguments
- `<dynamic_context>` — `!`-backtick context injection
- `<tool_restriction_security>` — `allowed-tools` as a security boundary
- `<file_references>` — `@` product files and the skill-directory token
- `<guard_block_partition>` — the three outcomes a dangerous-command guard block decides between

</contents>

<overview>

A SKILL.md carries every capability a slash command had — arguments, `!`-dynamic context injection, tool restriction, and `@` file references. These rules govern that surface for every skill that authors or audits arguments, dynamic context, tool restriction, or file references, and `<guard_block_partition>` classifies a command a dangerous-command guard blocks.

Author plugin source skills in Claude Code's supported SKILL.md syntax. Generated Codex output is a build-rendering concern: when Codex needs a different invocation surface, the renderer adapts the Codex runtime tree instead of constraining authored source to Codex's currently documented subset.

Prefer the intersection of Claude Code and Codex syntax only when it improves reliability or convenience:

- Use `$ARGUMENTS` for free-form whole-instruction capture, especially when one skill forwards instructions to another skill or when a user-invoked skill accepts natural-language instructions.
- Use positional or named arguments when each argument has a stable token boundary and a named variable improves reliability for a skill Claude or a wrapper agent invokes.
- Use richer Claude-only authoring forms when they make the authored skill clearer; if Codex cannot consume that form directly, update build rendering rather than weakening the source.

</overview>

<arguments>

A skill that operates on user-supplied input handles it explicitly:

- **`argument-hint`** — free-text autocomplete hint shown after `/skill-name`. Present whenever the skill takes arguments; omit for self-contained skills.
- **`$ARGUMENTS`** — consumes the full raw instruction string. Use it when preserving whitespace and multi-word intent matters, including forwarding instructions between lifecycle skills.
- **`$ARGUMENTS[N]` or `$N`** — consumes a numbered positional value when the position is stable and a name would add no clarity.
- **`arguments` with `$name`** — names positional arguments the body substitutes as `$name` (space-separated string or YAML list; names map to positions in order). Use it when a stable token has a domain name, such as `$configuration_target`.
- **Integration** — reference each declared `$name` where the body consumes it (e.g. "Audit the skill at `$skill_path`"), never as unused decoration. An argument declared but never substituted, or substituted but never declared, is a defect.
- **Empty arguments** — a skill that requires input states the requirement and what it does when input is absent; a skill that works with or without input states the fallback (e.g. "operate on the current selection when `$target` is empty" or "use the current changeset when `$ARGUMENTS` is empty").

- ALWAYS: declare `argument-hint` when the skill takes arguments.
- ALWAYS: preserve whole-string capture with `$ARGUMENTS` when collapsing input into positional tokens would change behavior.
- ALWAYS: substitute every declared named argument in the body, and declare every `$name` the body substitutes.
- NEVER: migrate a free-form instruction skill from `$ARGUMENTS` to a named positional argument unless the runtime contract proves the named argument preserves the full rest-of-line input.
- NEVER: require authored source to avoid Claude-supported syntax solely because Codex generated output may need a different form; fix the renderer for Codex.

Examples:

- Free-form forwarding: `/merge` reads `$ARGUMENTS` and forwards `$ARGUMENTS` verbatim to `/manage-github-pr`, preserving multi-word instructions.
- Stable token: `arguments: configuration_target` with `$configuration_target` names one positional value, a configuration path or role, for a creator skill.

</arguments>

<dynamic_context>

A skill injects state-dependent context with the `!`-backtick form inside `<context>` — the same mechanism a command used. Every `!`command`` line inside `<context>` runs unconditionally each time the skill is invoked, including false-positive activations triggered by directive descriptions matching adjacent terms, so heavy commands (session lists, full file contents, cache enumerations) compound a per-load tax:

- Load context only when it is directly relevant to the skill's task — a security-review skill needs git state; a pure-reasoning skill needs none.
- Filter every command so output stays bounded (`spx session list --status doing,todo`, `git log -10`, `head -N`) and never grows monotonically — archives, full caches, and full file trees do.
- Move data into the workflow file that consumes it when the skill loader does not need it for trigger evaluation; the `<context>` block is for trigger-time orientation, not workflow inputs.

- ALWAYS: scope `<context>` `!` commands to state the skill actually consumes at trigger time, filtered to bounded output.
- NEVER: inject state-dependent context the skill does not read, or an unfiltered command whose output grows per load.

</dynamic_context>

<tool_restriction_security>

`allowed-tools` restricts what a skill may do without per-call approval — a security boundary, not only a convenience:

- **Specificity** — restrict bash to the narrowest pattern that works: `Bash(git add:*)`, `Bash(git commit:*)`, never bare `Bash` or `Bash(git *)` when specific verbs suffice. A broad grant re-admits the destructive and exfiltrating commands the restriction exists to bar.
- **Destructive-operation containment** — a skill that must not delete, force-push, or deploy omits the tools that would let it; the allow-list is the containment.
- **Data-exfiltration containment** — a read-only analysis skill omits `Bash`, `WebFetch`, and `Write` so it cannot send local content outward; grant them only when the task needs them.
- **Audit capabilities** — an `audit-*` skill grants read capabilities and, on a harness that exposes a skill-composition tool, that tool when it composes another skill. Add only the specific Bash commands its workflow requires — read-only commands, and the `spx verification run` verbs that write the audit's own run journal; never grant `Write`/`Edit`.

- ALWAYS: grant the narrowest `allowed-tools` the skill's task needs, restricting bash to specific verb patterns.
- NEVER: grant a destructive or network tool a skill's task does not require, or leave a security-sensitive skill unrestricted.

</tool_restriction_security>

<file_references>

A skill body references a specific product file with the `@` prefix (`@path/to/file`), injecting its content — the same affordance a command had. Use `@` for product files in the consumer's tree; combine it with an argument (`@$target`) for a caller-named product file.

For skill-bundled files, use the runtime's skill-directory token instead of `@` or a repository path. In authored source, write the Claude Code token named `CLAUDE_SKILL_DIR`; the build emits Codex runtime output with the Codex token named `SKILL_DIR`:

```markdown
Read `${SKILL_DIR}/references/<bundled-reference>.md`
Run `python3 "${SKILL_DIR}/scripts/<bundled-script>.py" <args>`
```

NEVER write Codex's skill-directory token in source. NEVER reference bundled plugin files with repository-local authored or generated plugin paths, or with legacy plugin-root paths. If a skill needs a file owned by another skill or another plugin, name the owning workflow or capability rather than manufacturing a cross-plugin filesystem path.

</file_references>

<guard_block_partition>

A dangerous-command guard block on one command ends its command family or admits one split rerun, and the command decides which. The three outcomes partition every blocked command: it falls in exactly one.

**One operation.** A single simple command whose every word is a literal, with no shell expansion. A heredoc that feeds one command is one operation unless its delimiter is unquoted and its body expands, and so is a pipe whose first stage only supplies the payload the one reading command consumes on stdin, because no split of either leaves a smaller command that runs. When any word of such a pipe or of its payload stage expands, its values resolve first and the same pipe runs once with literal words; it is never split, and when the guard blocks that literal pipe the command family ends. A block on one operation ends its command family.

**A composition the parts cannot carry.** A command holding a process substitution, a pipe between two operations other than the payload pipe above, a background `&`, a subshell, or a list that mixes `&&` and `||`. A process substitution has no literal form, because `<(cmd)` hands the command a path to a stream and not the stream's text; a pipe carries a stream, a background `&` carries concurrency, a subshell carries shell state such as a `cd`, and a mixed list carries a status through a skipped part. Parts run one at a time carry none of these. A block on such a command ends its command family, even when it also holds a join or an expansion.

**Compound command.** Every other blocked command:

- two or more operations separated by `;` or a newline, or joined by `&&` alone or by `||` alone;
- one operation whose words the shell expands: a variable, a command substitution, a glob, or a tilde, brace or arithmetic expansion;
- a heredoc with an unquoted delimiter whose body expands.

A block on a compound command admits one rerun of its parts one at a time with every string written literally, in their original order: `;` and a newline separate lists, and each list runs regardless of the one before; within a list, parts joined by `&&` alone run while the part before them succeeded, and parts joined by `||` alone run until one succeeds. Each value resolves before the operation runs:

- a command substitution's inner command runs first on its own, and its output is the literal;
- a variable's value is the literal Claude assigned it, or the output of `printenv <name>` run on its own;
- a glob's matches are the entries of `ls <directory>` or the file-search tool for its literal directory that match the pattern, and a glob with a wildcard in a directory component resolves through the file-search tool on the full pattern;
- a tilde, brace or arithmetic expansion is written out as the literal words it produces;
- a value that is a secret — a token, key or credential — is never printed or written into a command; when resolving one would do that, the block ends the command family.

The operation then runs once with literal arguments. A part the guard blocks on its own is one operation and ends its family; split no part further.

- NEVER: rewrite a blocked operation as another program, strip its flagged clause, or substitute an equivalent command — the rerun changes no operation and removes only the composition the guard objected to.

</guard_block_partition>
