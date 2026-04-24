<overview>

Platform-specific constraints that affect skill authoring: dprint's `markup_fmt` handling of nested code fences, and Claude Code's bash-safety checker for `!` expansion. Read this before adding code-fenced examples to a SKILL.md or using `!` commands.

</overview>

<nested_code_fences>

**Single-nested 3-backtick inside a 4-backtick fence is fine.**

`````text
````markdown
<example>
```yaml
name: demo
```
</example>
````
`````

**Multi-nested breaks.** Never nest multiple 3-backtick blocks inside a single 4-backtick fence — `markup_fmt` (dprint) prematurely closes the outer fence after the first inner fence, destroying all subsequent content.

**Workaround:** when you need to show a markdown template that itself contains multiple code blocks, move the template into `references/` and point to it:

```markdown
<example_review>
Read `${CLAUDE_SKILL_DIR}/references/example-review.md` for a complete example.
</example_review>
```

</nested_code_fences>

<bash_expansion_restrictions>

`!` bash expansion in skill commands has restrictions. Use single quotes for outer strings when inner strings contain double quotes:

```bash
# ✅ Single quotes outside, double quotes inside
!`spx session list || echo 'Ask user to install: "npm install --global @outcomeeng/spx"'`

# ❌ Triggers "ambiguous syntax" permission error
!`spx session list || echo "Ask user to install: \"npm install --global @outcomeeng/spx\""`
```

**Avoid in `!` commands:**

- Shell operators: `(N)` nullglob, `*` globbing in zsh
- Parameter substitution: `${f/DOING/TODO}`
- Loops: `while read f; do ... done`
- Complex awk/sed pipelines with nested quotes

These all trigger permission errors from the Claude Code bash safety checker.

</bash_expansion_restrictions>
