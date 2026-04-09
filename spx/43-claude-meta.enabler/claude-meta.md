# Claude Meta

PROVIDES meta-skills for Claude Code plugin development — creating and auditing skills, commands, and subagents
SO THAT plugin authors
CAN build high-quality Claude Code plugins following established patterns and best practices

The claude plugin contains 6 skills: `/creating-skills`, `/creating-commands`, `/creating-subagents` (builders) and `/auditing-skills`, `/auditing-commands`, `/auditing-subagents` (auditors).

## Assertions

### Compliance

- ALWAYS: separate builder skills from auditor skills — builders produce, auditors evaluate ([review])
- ALWAYS: auditor skills produce structured verdicts, not code changes — audit skills are read-only ([review])
- NEVER: use auditor skills to modify files — they inform decisions but do not implement them ([review])
