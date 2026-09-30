---
name: implement-change
description: >-
  ALWAYS invoke this skill when a round of a Change needs a spec-tree node's language implementation written or repaired. NEVER write a Change's implementation code without this skill.
argument-hint: "<full-spx-node-path>"
allowed-tools: Read, Glob, Grep, {{! tool('use_skill') !}}
---

<objective>
One spec-tree node's implementation in its target language — the language decision where one is needed, the code, and the simplification where the language ships one — produced by that language's installed skills in this one session, with every load-gated command's exit collected.
</objective>

<workflow>

1. Take the canonical full `spx/...` node path from `$ARGUMENTS`. When it is empty or not a node path, change nothing and return `blocked` with reason `target-required`.
2. Use skill `spec-tree:contextualize` for that node path.
3. Read the skill inventory this session carries. Every installed `code-{lang}` skill names one available language `{lang}`; record the `architect-{lang}` and `simplify-{lang}` skills installed beside it. Never invoke a skill to find out whether it exists.
4. Select the target language: the one available language in which the node's linked evidence and the implementation it reaches are written. When no available language matches, return `blocked` with reason `language-unavailable`. When more than one matches, return `blocked` with reason `language-ambiguous`, naming each candidate.
5. When the node's work needs a language architecture decision, run `architect-{lang}` for the node. Persist the decision it returns through `/author` before any code depends on it.
6. Run `code-{lang}` for the node, and run every deterministic check it selects to passing.
7. When `simplify-{lang}` is installed, run it on the committed result of step 6 and apply its result contract. When it is absent, skip this step.
8. Run every command `/wait-for-load` gates in the foreground, and report a result only after every such command has exited.

</workflow>

<constraints>

- NEVER launch a subagent — every language skill runs in this session.
- NEVER run a language skill for a language other than the one step 4 selected.
- NEVER name a specific language in a decision this skill makes; the installed skills carry every language rule.

</constraints>

<output_format>

Return the node path, the selected language, the skills run in order, each skill's result unchanged, the changed paths, and each deterministic command with its exit code. A blocked result carries its reason and the candidate languages when step 4 found several.

</output_format>

<success_criteria>

- Every language skill that ran belongs to the one language step 4 selected, and ran in this session.
- Every deterministic command the language skills selected exited, and its exit code is in the result.
- No step produced a subagent launch.

</success_criteria>
