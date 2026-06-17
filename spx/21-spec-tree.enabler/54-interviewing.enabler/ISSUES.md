# Issues: interviewing

Reconcile against `interviewing.md`, `src/plugins/spec-tree/skills/interview/SKILL.md`, and any calling skill before acting.

## 1. `AskUserQuestion` trigger makes operational yes/no prompts look like interviews

The interviewing skill frontmatter says `Triggers: AskUserQuestion, seeking draft approval, stuck on scope or design. NEVER ask without this skill.` That wording can be read as a routing rule that any structured question must load `/interview`, including mechanical workflow prompts such as how to handle a guide-template drift note. The spec's intended surface is narrower: `/interview` provides requirements-gathering methodology for artifact creation or modification, with pre-analysis, decide-first reasoning, coverage tracking, and materially distinct options.

Suggested fix:

- Narrow the skill description so `/interview` triggers only for requirements interviews and unresolved artifact design/scope decisions. A workflow that merely needs the runtime structured-question tool for a yes/no operational decision should use that workflow's own rules without loading `/interview`.
- In the Questioning Protocol, clarify that "Always use AskUserQuestion" applies only after `/interview` is already the correct workflow and a genuine interview question remains. The rule is limited to tool choice inside an interview rather than global skill routing before every structured question.
- Add a failure mode or eval case for a guide-drift or imperfection-handling prompt where the correct behavior is to decide locally or ask through the governing workflow, without loading `/interview` unless the unresolved decision is actually about artifact requirements, scope, or design.
