# Skill Frontmatter Validation

PROVIDES validation that SKILL.md frontmatter fields conform to the union of Agent Skills open standard fields and Claude Code binary-extracted fields
SO THAT skill authors
CAN commit skill files that the installed Claude Code CLI will accept without manual field-list maintenance

## Assertions

### Scenarios

- Given a SKILL.md with only standard Agent Skills fields, when validated, then no errors are reported ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with an unknown field (`foo-bar`), when validated, then an error is reported naming the invalid field ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with no frontmatter, when validated, then no errors are reported ([test](tests/test_skill_frontmatter.unit.py))
- Given a file that is not named SKILL.md, when passed to the validator, then it is skipped ([test](tests/test_skill_frontmatter.unit.py))
- Given the Claude binary is unavailable, when valid fields are requested, then the standard fields are returned as fallback ([test](tests/test_skill_frontmatter.unit.py))
- Given binary extraction fails, when valid fields are requested, then the standard fields are returned as fallback ([test](tests/test_skill_frontmatter.unit.py))

### Compliance

- NEVER: hardcode Claude Code-specific fields — they are derived from the binary at runtime per [15-field-extraction.adr.md](15-field-extraction.adr.md) ([review])
