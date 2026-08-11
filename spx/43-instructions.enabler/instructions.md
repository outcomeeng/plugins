# Instructions

PROVIDES instruction-authoring meta-skills for Codex and Claude Code — creating and auditing skills and subagents, and the agent-prompt conventions they share
SO THAT plugin authors
CAN build high-quality plugins that follow established patterns and best practices

## Assertions

### Compliance

- ALWAYS: instruction-artifact work — a skill, agent, template, or instruction surface — starts from complete spec-tree context, and a change that makes a behavioral rule enforceable authors the governing assertion in the owning node before any enforcement surface is edited ([audit])
- ALWAYS: separate builder skills from auditor skills — builders produce, auditors evaluate ([audit])
- ALWAYS: centralize prompt voice, description, and constraint conventions in `/agent-prompt-standards` — prompt craft is shared across skills and subagents ([audit])
- ALWAYS: auditor skills produce structured verdicts, not code changes — audit skills are read-only ([audit])
- NEVER: use auditor skills to modify files — they inform decisions but do not implement them ([audit])
