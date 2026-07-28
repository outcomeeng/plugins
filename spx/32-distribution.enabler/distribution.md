# Distribution

PROVIDES the skill distribution pipeline that copies skills from the monorepo to downstream single-plugin repositories
SO THAT users who install individual plugins via GitHub
CAN receive the same skill content as marketplace users

Distribution maps downstream repositories to built Claude plugins, collects each plugin's skills, and copies those skills to the target repositories.

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

### Compliance

- NEVER: distribute agent files — only skill directories are copied to downstream repos ([audit])
- ALWAYS: preserve `.git/` directory when clearing target repo contents ([audit])
- ALWAYS: the distribution workflow triggers from the committed Claude runtime tree and source plugin changes — retired `plugins/` source paths never gate distribution ([test](tests/test_distribution_workflow.compliance.l1.py))
- ALWAYS: the distribution workflow runs on the Python version declared by `pyproject.toml` — CI uses the same interpreter contract as the project metadata ([test](tests/test_distribution_workflow.compliance.l1.py))
