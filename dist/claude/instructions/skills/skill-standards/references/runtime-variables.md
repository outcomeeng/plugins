<overview>

Runtime variable scopes and how to reference skill-bundled files. Read this before referencing files from a SKILL.md body or wiring hook `command:` paths.

</overview>

<skill_file_references>

Use the runtime's skill-directory token to reference files within the current skill directory. In authored source, write the Claude Code token named `CLAUDE_SKILL_DIR`; the build emits Codex runtime output with the Codex token named `SKILL_DIR`.

Authored source examples, using files bundled with the skill that contains the prose:

```markdown
Read `${CLAUDE_SKILL_DIR}/references/<bundled-reference>.md`
Run `python3 "${CLAUDE_SKILL_DIR}/scripts/<bundled-script>.py" <args>`
```

NEVER write Codex's skill-directory token in source. NEVER reference a skill-bundled file through repository-local authored or generated plugin paths, or through legacy plugin-root paths. If the file is not bundled with the current skill, name the capability or owning workflow instead of inventing a filesystem path.

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
