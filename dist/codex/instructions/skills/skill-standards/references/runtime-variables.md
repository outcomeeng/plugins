<overview>

Runtime variable scopes and how to reference skill-bundled files.

</overview>

<skill_file_references>

Use `${SKILL_DIR}` to reference files within the current skill directory.

Examples using files bundled with the skill that contains the prose:

```markdown
Read `${SKILL_DIR}/references/<bundled-reference>.md`
Run `python3 "${SKILL_DIR}/scripts/<bundled-script>.py" <args>`
```

NEVER reference a skill-bundled file through repository-local source or generated plugin paths, or through legacy plugin-root paths. If the file is not bundled with the current skill, name the capability or owning workflow instead of inventing a filesystem path.

Do NOT define aliases, add troubleshooting sections, or explain compatibility tokens.

</skill_file_references>

<variable_scopes>

| Variable       | Scope                      | Skill content |
| -------------- | -------------------------- | ------------- |
| `${SKILL_DIR}` | Skill's SKILL.md directory | Yes           |

Codex exposes the rendered skill-directory token for bundled references and scripts. This reference declares no plugin-root, plugin-data, project-root, or hook-command variable without a Codex runtime contract.

</variable_scopes>
