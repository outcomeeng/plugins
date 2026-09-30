---
name: implement-change
description: >-
  Language-implementation workflow for one spec-tree node: the target language's installed architect, code, and simplify skills run in one session, invoked with a canonical node path.
argument-hint: "<full-spx-node-path> [repair-block]"
allowed-tools: Read, Glob, Grep, Bash(git rev-parse HEAD), Bash(git diff --name-only:*), {{! tool('use_skill') !}}
---

<objective>
One spec-tree node's implementation in its target language, with every language decision it depends on persisted, every deterministic check the language skills select passing, and the language's simplification applied where the language ships one.
</objective>

<load_gating>

Use skill `spec-tree:wait-for-load` for every resource-intensive command any step below runs: run the waiter and that command as one line in the foreground, and report a result only after every such line has exited.

</load_gating>

<workflow>

1. Take the canonical full `spx/...` node path from the start of `$ARGUMENTS`. When it is empty or not a node path, change nothing and return `blocked` with reason `target-required`. Text after the target is a repair block: the verbatim result of each rejected verdict and the exact command line and output of each failed deterministic command of an earlier round on this target. Carry it into this workflow as repair input: repair every finding and failure it names within this workflow's scope, and report each one's disposition in the result.
2. Use skill `spec-tree:contextualize` for that node path, then record `git rev-parse HEAD` as the node's starting head.
3. Read the skill inventory this session carries. Every installed `code-{lang}` skill names one available language `{lang}`; record its exact installed name and the exact installed names of the `architect-{lang}` and `simplify-{lang}` skills beside it. Never invoke a skill to find out whether it exists.
4. Select the target language: the language in which the node's linked evidence and the implementation it reaches are written; for a node with neither yet, the language a loaded decision names for its implementation. When evidence and implementation are written in different languages, or more than one language matches, return `blocked` with reason `language-ambiguous`, naming each candidate. When a node with neither has no loaded decision naming its language, return `blocked` with reason `language-undeclared`. When the selected language is not available, return `blocked` with reason `language-unavailable`, naming it.
5. When no ADR in the loaded context governs the language architecture the node's implementation uses, use the `architect-{lang}` skill by the exact name step 3 recorded, for the node, then use skill `spec-tree:author` to persist the decision it returns before any code depends on it. When no `architect-{lang}` skill is installed for the selected language, change nothing and return `blocked` with reason `architect-unavailable`, naming the language.
6. Use the `code-{lang}` skill by the exact name step 3 recorded, for the node, and run every deterministic check it selects to passing, through the language skill's own command grants or the harness's per-call approval.
7. Use skill `spec-tree:commit-changes` to checkpoint the changes steps 5 and 6 made, recording the verification state. A check from step 6 that did not reach passing ends here with status `failed`, naming the check, its output, and this checkpoint.
8. When `simplify-{lang}` is installed, use it by the exact name step 3 recorded, on that checkpoint. Its `failed` result makes this skill's status `failed` and its `blocked` result makes it `blocked` with the simplify reason; any other result continues. When it is absent, skip to the result.
9. When step 8 left changes, use skill `spec-tree:commit-changes` to checkpoint them. The final checkpoint is the one this result reports.

Every composed skill's result is read before the next step. A `blocked` result from any composed skill ends this skill `blocked` with that skill's name and reason unchanged; a `failed` result, or a result outside that skill's declared contract, ends it `failed` with that skill's name and result. Step 8 states its own mapping for `simplify-{lang}`.

</workflow>

<constraints>

- NEVER launch a subagent — every language skill runs in this session.
- NEVER run a language skill for a language other than the one step 4 selected.
- NEVER name a specific language in a decision this skill makes; the installed skills carry every language rule.

</constraints>

<output_format>

Return the status — `completed`, `blocked`, or `failed` — with the node path, the selected language, the skills run in order with each skill's result unchanged, every path `git diff --name-only <starting-head>` reports since the starting head step 2 recorded, the final checkpoint's full commit id, and each deterministic command with its exit code. A `blocked` result carries its reason and, for `language-ambiguous`, the candidate languages; a `failed` result names the composed skill or check that failed and its output.

</output_format>

<success_criteria>

- Every language skill that ran belongs to the one language step 4 selected, and ran in this session.
- Every language decision the implementation depends on was persisted through `spec-tree:author` before the code that depends on it.
- A `completed` result carries a passing exit code for every deterministic check the language skills selected.
- No step produced a subagent launch.

</success_criteria>
