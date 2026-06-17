<overview>

Runtime variable scopes and how to reference skill-bundled files. Read this before referencing files from a SKILL.md body or wiring hook `command:` paths.

</overview>

<skill_file_references>

Use the Claude Code skill-directory token (`CLAUDE_SKILL_DIR` in shell-variable form) to reference files within skill source. Claude Code expands it to the absolute path of the skill's directory before Claude sees the content.
Do not write `SKILL_DIR` in source; the build emits that token for Codex output.

```markdown
Read `${CLAUDE_SKILL_DIR}/references/example.md`
```

Do NOT define aliases, add troubleshooting sections, or explain compatibility tokens. Author the Claude Code token once; the build owns Codex compatibility.

</skill_file_references>

<variable_scopes>

| Variable                | Scope                      | Skill content (`!` commands) | Hook `command:` field |
| ----------------------- | -------------------------- | ---------------------------- | --------------------- |
| `${CLAUDE_SKILL_DIR}`   | Skill's SKILL.md directory | Yes                          | **No**                |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin installation root   | No                           | **Yes**               |
| `${CLAUDE_PLUGIN_DATA}` | Plugin persistent data dir | No                           | **Yes**               |
| `$CLAUDE_PROJECT_DIR`   | Product working directory  | No                           | **Yes**               |

For hook scripts bundled with a plugin skill, use `${CLAUDE_PLUGIN_ROOT}`:

```yaml
hooks:
  PostToolUse:
    - matcher: "Skill"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/my-skill/scripts/hook.sh"
```

</variable_scopes>
