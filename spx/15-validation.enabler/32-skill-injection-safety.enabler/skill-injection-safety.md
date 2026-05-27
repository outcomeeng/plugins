# Skill Injection Safety Validation

PROVIDES validation that no SKILL.md contains a loader-executable command-injection fence token — a fenced block whose info string begins with `!`, which the Claude Code skill loader executes as a shell command at load time
SO THAT skill authors and marketplace maintainers
CAN commit skill files that the skill loader registers without executing embedded documentation content

## Assertions

### Scenarios

- Given a SKILL.md whose content contains a command-injection fence token, when validated, then the script exits non-zero and the error names the file and the line ([test](tests/test_skill_injection_safety.scenario.l1.py))
- Given a SKILL.md with no command-injection fence token, when validated, then no error is reported and the script exits zero ([test](tests/test_skill_injection_safety.scenario.l1.py))
- Given several SKILL.md paths where one contains the token, when validated, then the script names the offending file and exits non-zero ([test](tests/test_skill_injection_safety.scenario.l1.py))
- Given a path whose basename is not `SKILL.md`, when passed to the validator, then it is skipped ([test](tests/test_skill_injection_safety.scenario.l1.py))

### Compliance

- NEVER: a committed SKILL.md contains a loader-executable command-injection fence token — the skill loader executes such a fence at registration time, which crashes skill load and renders the skill unusable ([test](tests/test_skill_injection_safety.compliance.l1.py))
