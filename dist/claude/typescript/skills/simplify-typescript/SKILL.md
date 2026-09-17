---
name: simplify-typescript
description: >-
  ALWAYS invoke this skill when simplifying TypeScript implementation while preserving behavior.
argument-hint: "<HEAD|base...head>"
allowed-tools: Read, Glob, Grep, Edit, Skill, Bash(git status:*), Bash(git rev-parse:*), Bash(git diff:*)
---

Use skill `typescript:typescript-test-standards`.

<objective>
Simpler TypeScript implementation with unchanged behavior and type safety, accompanied by a scope and verification report.
</objective>

<constraints>

- MUST preserve public behavior, dependency-injection seams, error wrapping, and typed errors.
- MUST preserve strict types, guards, generic constraints, explicit annotations, and the product's import boundaries and aliases.
- NEVER modify tests, test infrastructure, specs, or generated files; simplify only implementation already changed in the selected scope.
- NEVER change behavior to enable a simplification, add dependencies, or weaken coverage and validation requirements.
- NEVER commit, publish, or launch another subagent as part of simplification.
- Product verification commands outside this skill's narrow Git preapprovals use the harness's normal per-call approval path. Resolve the exact product command, honor existing operator authorization, and request any missing permission before execution; denied or unavailable permission returns `blocked`. Never substitute a command to avoid approval.

</constraints>

<workflow>

1. Require `$ARGUMENTS` to be `HEAD` or an explicit committed three-dot range. For absent or invalid input, return `blocked` before mutation. Read the product's CLAUDE.md and invoke `/understand` when its foundation marker is absent.
2. Invoke `/scope-changeset` with the supplied target and consume its `COMMITTED_CHANGESET_SCOPE` marker. The provider executes its own committed-scope command; do not import its Python API or invent a resolver command. Require the resolved head to equal the checkout's full `HEAD` and the worktree to be clean. Record both endpoint identities and the complete changed-path set. A scope-resolution failure returns `blocked` with its diagnostic.
3. Select changed, present TypeScript implementation files, excluding generated extents and test/evidence files using the product's declarations and `/typescript-test-standards`. Derive their governing nodes through spec-linked evidence and invoke `/contextualize` on their lowest common ancestor before reading implementation. After context loading, require the same full `HEAD` and a clean worktree again; otherwise return `blocked` with the changed subject. If no implementation qualifies, return `unchanged` with the empty scope. Missing governance returns `blocked`.
4. Inspect the selected implementation and the evidence covering its behavior. Apply `/typescript-test-standards` to coverage and test quality. Missing or inadequate behavioral coverage returns `blocked` with the affected file or function and evidence gap; do not create tests to bypass this condition.
5. Resolve the baseline test command from the product guide and the inspected evidence. Use existing evidence; if correct work requires changed behavior or changed evidence, return `blocked` before editing.
6. Run the product's required baseline tests and record actual exit codes. A failed or unavailable baseline returns `blocked` without edits. Identify only changes whose behavioral equivalence can be explained from the code and evidence; when none improves clarity safely, return `unchanged` with the reason.
7. Invoke `typescript:code-typescript` with the governing node, selected files, and the behavior-preserving simplification requirement. Follow its complete discovery, standards, and validation contract while preserving the evidence. Retain the exact patch owned by this invocation. Require the same tests afterward and every typecheck, lint, format, and validation check required by `/code-typescript`, using product commands and preserving process exit codes. Collect those results once; never mask a failing process through output truncation or a pipeline.
8. Compare the resulting diff with the recorded scope and baseline. Confirm tests, evidence, seams, and type contracts remain unchanged. Follow `<recovery>` on any failed check or uncertain equivalence, then return `<result>`.

</workflow>

<coding_result>

When invoking `typescript:code-typescript`, request its completion report with changed paths, the behavior preserved by each edit, the evidence used, executed commands and exit codes, and unresolved constraints. Execute that composed workflow in this session.

Before Step 8, require every report component and compare it against the retained diff and captured command results. Every changed path must belong to the selected scope, every reported successful check must have a zero exit code, and every omitted required check or unresolved constraint must be identified. A missing report component or contradiction returns `failed` through the recovery procedure; never infer completion from a generic success statement.

Merge the validated report into the final JSON: retained paths into `changed_paths`, each edit and its equivalence explanation into `changes`, inspected tests and covered behavior into `evidence`, actual command observations into `verification`, and remaining constraints into `blockers`. Preserve this skill's before/after/recovery phases and its stricter behavior-preservation boundaries.

</coding_result>

<recovery>

On a post-edit verification failure, reverse only this invocation's patch and run the affected check against the restored content. Never reset or restore a whole file over another writer's changes. If concurrent edits prevent safe reversal, leave them intact and report the exact collision and remaining patch. Return `failed`, retaining the original command, exit code, diagnostic, and recovery outcome even when restoration succeeds.

If a required skill, product command, decision, or permission is unavailable, report `blocked` with the exact prerequisite and next required action. After edits, first apply the same recovery rule. Never install dependencies or invent a replacement verification command.

</recovery>

<result>

Return one JSON object with these fields:

- `status`: `simplified`, `unchanged`, `blocked`, or `failed`; `reason`: the outcome explanation.
- `target`: the supplied target unchanged; `base` and `head`: full resolved commit identities, or null when resolution failed.
- `scope`: selected implementation paths; `changed_paths`: paths still changed by this invocation.
- `changes`: each applied simplification's path, reason, and behavioral-equivalence explanation.
- `evidence`: inspected test paths and the behavior each covers.
- `verification`: executed commands with `phase` (`before`, `after`, or `recovery`), `command`, and actual `exit_code`. List every required but unexecuted check in `blockers`.
- `blockers`: exact prerequisites, evidence gaps, failing diagnostics, or uncertainty; empty on success.
- `recovery`: an object with `status` (`not-needed`, `reverted`, or `conflict`) and `details`.

`simplified` requires a nonempty retained patch, sufficient unchanged evidence, and all required checks passing. `unchanged` requires no retained patch and a `reason` explaining why the scope was empty or no safe improvement was found. Never represent an unexecuted check as passing or a simplification report as an independent audit approval.

</result>

<failure_modes>

**A library reference was treated as an executable capability.** Claude instructed the simplifier to use `resolve_committed_scope` even though the provider exposed only an importable API. The workflow had no shipped command to execute. Invoke `/scope-changeset` with the target and consume the marker its own command establishes; never invent an import script during simplification.

</failure_modes>

<success_criteria>

- Every retained edit belongs to the resolved TypeScript implementation scope and improves clarity without changing behavior, error contracts, seams, or type safety.
- Unchanged behavioral tests pass before and after edits, and the complete `/code-typescript` validation requirements pass.
- The report accounts for every retained edit, executed check, unexecuted required check, and recovery action.
- A blocked prerequisite causes no retained edit unless a reported concurrent-write collision prevents safe recovery.

</success_criteria>
