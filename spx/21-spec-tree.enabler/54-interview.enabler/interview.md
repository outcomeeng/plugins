# Interview

PROVIDES a domain-agnostic structured interview methodology — pre-analysis, decide-first reasoning, one-question-at-a-time coverage tracking, pushback, and structured options
SO THAT every spec-tree skill that gathers requirements
CAN elicit complete, decision-ready input without asking what the repository already answers or offloading decisions the agent is equipped to make

## Assertions

### Compliance

- ALWAYS: research the codebase, product docs, and the input before the first question and share a structured analysis brief — never ask what the repository or docs already answer ([audit])
- ALWAYS: reason each decision through to a recommendation before asking, and ask the operator only when the decision is genuinely the operator's and unsettled by the code, specs, decisions, or sensible defaults — otherwise decide and proceed ([audit])
- ALWAYS: present options as materially distinct end-states with the recommendation stated first — never a real option paired with a strawman, and never one judgment split into a false balance ([audit])
- ALWAYS: ask one question at a time and display the evolving coverage map before each question, advancing coverage rather than spiraling on a single area ([audit])
- ALWAYS: challenge contradictions, over-engineering, and missing edge cases, and hard-block on a security or privacy risk until it is acknowledged and addressed ([audit])
- ALWAYS: treat existing code as content that informs vocabulary and constraints, never as the structure of the artifact being created ([audit])
- ALWAYS: complete by coverage — propose writing only when every coverage area is sufficiently explored, never by question count or elapsed time ([audit])
- NEVER: record a vague non-answer as a resolved assertion — force specificity, or record it as an open decision ([audit])
