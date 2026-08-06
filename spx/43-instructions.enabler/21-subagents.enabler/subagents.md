# Subagents

PROVIDES the meta-skills that create, standardize, and audit subagent configurations
SO THAT plugin authors
CAN produce configured agents that load and return reliable verdicts in every agent harness the marketplace targets

The subagents-about-subagents cluster is three peers with distinct roles:

- `/create-subagent` routes subagent creation and editing.
- `/subagent-standards` owns the canonical rules — configuration fields, tool grants, model selection, context isolation, and the invocation contract. Loaded by the other two.
- `/audit-subagent` evaluates one subagent configuration against `/subagent-standards` and `/agent-prompt-standards`, producing structured verdicts without modifying files.

## Assertions

### Compliance

- ALWAYS: `/subagent-standards` owns every rule `/audit-subagent` enforces — standards and enforcement stay in one place so drift cannot open between them ([audit])
- ALWAYS: `/create-subagent` and `/audit-subagent` load `/subagent-standards` before doing any authoring or evaluation work — prevents memory-based assessment ([audit])
- ALWAYS: `/audit-subagent` judges exactly one subagent configuration per invocation, and auditing several configurations dispatches one invocation per configuration ([eval](evals/invocation-scope/eval.toml))
- ALWAYS: `/create-subagent` writes a configuration to the invocation checkout by default, and reaches a user-scope destination outside it — creating, editing, or deleting — only after operator confirmation naming the absolute destination, one approval covering one write ([audit])
- NEVER: `/create-subagent` widens an approved checkout-scope write to user scope on its own judgment that the configured agent suits other projects — that destination applies to every project on the machine and no repository reviews it ([audit])
- NEVER: restate `/subagent-standards` or `/agent-prompt-standards` rules inside `/create-subagent` or `/audit-subagent` — a single source of truth prevents drift between standard and enforcer ([audit])
