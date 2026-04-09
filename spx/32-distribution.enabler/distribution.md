# Distribution

PROVIDES the skill distribution pipeline that copies skills from the monorepo to downstream single-plugin repositories
SO THAT users who install individual plugins via GitHub
CAN receive the same skill content as marketplace users

The `distribute_skills.py` script reads `distribution.yml` for the mapping of downstream repos to source plugins, collects skills from each plugin, and copies them to the target repositories.

## Assertions

### Scenarios

- Given a plugin directory with a `skills/` subdirectory containing SKILL.md files, when skills are collected, then each skill's name, description, and path are returned ([test](tests/test_distribute_skills.unit.py))
- Given a plugin directory without a `skills/` subdirectory, when skills are collected, then the plugin is skipped ([test](tests/test_distribute_skills.unit.py))
- Given a skill directory without a SKILL.md file, when skills are collected, then the skill is skipped ([test](tests/test_distribute_skills.unit.py))
- Given a directive-style description ("ALWAYS invoke...NEVER..."), when cleaned, then the ALWAYS/NEVER framing is stripped to produce a plain sentence ([test](tests/test_distribute_skills.unit.py))
- Given a target directory with existing contents, when cleared, then all files and directories are removed except `.git/` ([test](tests/test_distribute_skills.unit.py))
- Given a skill directory containing broken symlinks, when copied, then the broken symlinks are skipped and valid files are copied ([test](tests/test_distribute_skills.unit.py))

### Properties

- Skill collection from multiple plugins produces the union of all skills across all plugins ([test](tests/test_distribute_skills.unit.py))

### Compliance

- NEVER: distribute agent or command files — only skill directories are copied to downstream repos ([review])
- ALWAYS: preserve `.git/` directory when clearing target repo contents ([review])
