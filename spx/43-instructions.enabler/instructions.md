# Instructions

PROVIDES instruction-authoring meta-skills for Codex and Claude Code — creating and auditing skills and subagents, and the agent-prompt conventions they share
SO THAT plugin authors
CAN build high-quality plugins that follow established patterns and best practices

## Assertions

- ALWAYS: subagent authoring guidance follows the plugin-list standing authorization, explicit skill
  trigger, target-only input, native-schema, and model-profile policy in
  `spx/15-subagent-execution.pdr.md` for both supported agents ([audit]).

### Compliance

- ALWAYS: separate builder skills from auditor skills — builders produce, auditors evaluate ([audit])
- ALWAYS: centralize prompt voice, description, and constraint conventions in `/agent-prompt-standards` — prompt craft is shared across skills and subagents ([audit])
- ALWAYS: auditor skills produce structured verdicts, not code changes — audit skills are read-only ([audit])
- NEVER: use auditor skills to modify files — they inform decisions but do not implement them ([audit])
- ALWAYS: `/audit-skill` and `/audit-subagent` start one `spx verification run` before judging, record every scope unit and finding through it, seal it, and return the run token with the rendered projection, whose terminal status is the verdict; a refused payload or finish returns a blocked result ([audit])
- ALWAYS: `skill-auditor` and `subagent-auditor` pass the raw target and a fixed run-driver identity to their skill and relay the run token and the rendered projection unchanged, or the complete blocked diagnostic ([audit])
