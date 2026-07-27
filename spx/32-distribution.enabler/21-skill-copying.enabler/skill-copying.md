# Skill Copying

PROVIDES skill collection, metadata cleanup, target cleanup, and copying from built plugins into downstream single-plugin repositories
SO THAT downstream plugin repositories
CAN receive the same skill content as marketplace installations

## Assertions

### Scenarios

- Given a plugin directory with a `skills/` subdirectory containing SKILL.md files, when skills are collected, then each skill's name, description, and path are returned ([test](tests/test_distribute_skills.scenario.l1.py))
- Given a plugin directory without a `skills/` subdirectory, when skills are collected, then the plugin is skipped ([test](tests/test_distribute_skills.scenario.l1.py))
- Given a skill directory without a SKILL.md file, when skills are collected, then the skill is skipped ([test](tests/test_distribute_skills.scenario.l1.py))
- Given a directive-style description ("ALWAYS invoke...NEVER..."), when cleaned, then the ALWAYS/NEVER framing is stripped to produce a plain sentence ([test](tests/test_distribute_skills.scenario.l1.py))
- Given a target directory with existing contents, when cleared, then all files and directories are removed except `.git/` ([test](tests/test_distribute_skills.scenario.l1.py))
- Given a skill directory containing broken symlinks, when copied, then the broken symlinks are skipped and valid files are copied ([test](tests/test_distribute_skills.scenario.l1.py))

### Properties

- Skill collection from multiple plugins produces the union of all skills across all plugins ([test](tests/test_distribute_skills.property.l1.py))
