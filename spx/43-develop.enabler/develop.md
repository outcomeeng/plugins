# Develop

PROVIDES meta-skills for Codex and Claude Code plugin development — creating and auditing skills, commands, subagents, and agent prompt standards
SO THAT plugin authors
CAN build high-quality plugins following established patterns and best practices

The develop plugin contains the reference skill `/standardizing-agent-prompts`, builder skills `/creating-skills`, `/creating-commands`, `/creating-subagents`, and auditor skills `/auditing-skills`, `/auditing-commands`, `/auditing-subagents`.

## Assertions

### Compliance

- ALWAYS: separate builder skills from auditor skills — builders produce, auditors evaluate ([review])
- ALWAYS: centralize prompt voice, description, and constraint conventions in `/standardizing-agent-prompts` ([review])
- ALWAYS: auditor skills produce structured verdicts, not code changes — audit skills are read-only ([review])
- NEVER: use auditor skills to modify files — they inform decisions but do not implement them ([review])
