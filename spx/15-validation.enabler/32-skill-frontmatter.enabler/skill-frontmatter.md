# Skill Frontmatter Validation

PROVIDES validation that SKILL.md frontmatter fields conform to the union of Agent Skills open standard fields and a curated Claude Code field allowlist
SO THAT skill authors
CAN commit skill files that both Anthropic's published validator and the installed Claude Code CLI will accept

## Assertions

### Scenarios

- Given a SKILL.md with only standard Agent Skills fields, when validated, then no errors are reported ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with a Claude Code-specific field (`disable-model-invocation`), when validated, then no errors are reported ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with an unknown field (`foo-bar`), when validated, then an error is reported naming the invalid field ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with a name that is not kebab-case, when validated, then an error is reported referencing the name format rule ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with a description containing angle brackets, when validated, then an error is reported referencing the description rule ([test](tests/test_skill_frontmatter.unit.py))
- Given a SKILL.md with no frontmatter, when validated, then an error is reported referencing the missing frontmatter ([test](tests/test_skill_frontmatter.unit.py))
- Given a file that is not named SKILL.md, when passed to the validator, then it is skipped ([test](tests/test_skill_frontmatter.unit.py))

### Compliance

- NEVER: hardcode the Agent Skills open standard field list in the wrapper — the vendored `quick_validate.py` is the source of truth per [15-frontmatter-validation.adr.md](15-frontmatter-validation.adr.md) ([review])
- NEVER: modify the vendored `quick_validate.py` in place — extensions live in the wrapper's Claude Code allowlist per [15-frontmatter-validation.adr.md](15-frontmatter-validation.adr.md) ([review])
