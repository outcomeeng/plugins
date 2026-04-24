# Develop

PROVIDES meta-skills for Codex and Claude Code plugin development — creating and auditing skills, commands, subagents, and the agent-prompt conventions they share
SO THAT plugin authors
CAN build high-quality plugins that follow established patterns and best practices

## Assertions

### Compliance

- ALWAYS: separate builder skills from auditor skills — builders produce, auditors evaluate ([review])
- ALWAYS: centralize prompt voice, description, and constraint conventions in `/standardizing-agent-prompts` — prompt craft is shared across skills, commands, and subagents ([review])
- ALWAYS: auditor skills produce structured verdicts, not code changes — audit skills are read-only ([review])
- NEVER: use auditor skills to modify files — they inform decisions but do not implement them ([review])
