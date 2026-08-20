---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into the owning repository's session queue — including the invoking repository, the spec-tree plugin repository, the spx CLI repository, or another spec-tree dependency. NEVER edit installed dependency source or run the current work through full handoff closure merely to record a needed follow-up.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(printenv CLAUDE_CODE_SESSION_ID), Bash(spx -C:* diagnose*), Bash(spx -C:* session handoff*), Bash(spx -C:* session list*), Bash(spx -C:* session show*), Bash(spx session show:*), Bash(git status:*), Bash(git rev-parse --show-toplevel), Bash(git rev-parse --path-format=absolute --git-common-dir), Bash(git remote get-url origin), Bash(git -C:* branch --show-current), Bash(git -C:* config --get core.bare), Bash(git -C:* worktree list --porcelain), Bash(git -C:* symbolic-ref --short refs/remotes/origin/HEAD), Bash(git -C:* rev-parse --path-format=absolute --git-common-dir), Bash(git -C:* rev-parse --show-toplevel), Bash(git -C:* rev-parse --verify refs/remotes/origin/*), Bash(git -C:* remote get-url origin), Bash(claude plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*), AskUserQuestion
---

<objective>
A minimal follow-up filed in the owning spec-tree repository's active session queue — capturing Claude's observation and naming possible overlaps from queue headers.

</objective>

<when_to_invoke>
Editing a spec-tree component's installed source directly to record a needed change rewrites shared infrastructure for every consumer session that uses it, with no review. The `/issue` skill files the observation in the owning repository's session queue instead, where that repository's workflow triages and acts on it. The owning repository may be the invoking repository; recording a proportional follow-up never requires closing the current work.

</when_to_invoke>

<captured_fields>
Capture Claude's OBSERVATION only — never the dependency's internal taxonomy. Claude reports what it saw; the dependency workflow classifies it against its spec tree.

Gather from the invoking context, asking the user only for operator-owned gaps:

- **Observation** — what was observed: the behavior, the gap, the contradiction.
- **Uncertainty** — what remains unknown or unconfirmed.
- **Checked facts** — what was already verified (commands run, files read, versions observed) and their results.
- **Affected paths** — the paths or surfaces the observation touches, as observed (a file, a command, a skill name) — NOT a node address, decision index, or assertion type in the dependency's spec tree.
- **Next-workflow context** — what the dependency's next pickup needs to begin: how to reproduce, where to look, what "done" looks like.

NEVER assign the dependency's node addresses, decision indices, or assertion types — Claude supplies observations, not the dependency's spec-tree structure. Leave the handoff header `specs` and `files` empty; carry observed paths in the body prose.

</captured_fields>

<dependency_followup_body>

Dependency follow-ups use a minimal body contract because Claude assigns none of the target dependency's node taxonomy. Include each section exactly once, in this order:

```text
# <short title>

<observation>
<observed behavior, gap, or contradiction>
</observation>

<uncertainty>
<unknown or unconfirmed facts, or "none">
</uncertainty>

<checked_facts>
<commands, files, versions, and observed results>
</checked_facts>

<affected_paths>
<observed paths or surfaces, with no dependency node taxonomy>
</affected_paths>

<next_workflow_context>
<reproduction entrypoint and observable done state>
</next_workflow_context>
```

This is the sanctioned dependency-followup body contract. It intentionally differs from `/handoff`'s node-oriented body, which describes work already classified inside the current product's spec tree.

</dependency_followup_body>

<target_resolution>
Resolve the target repository's checkout directory `<target-dir>` — the input to identity classification in Step 1; the checkout the handoff command writes into is `<queue-host>`, which Step 1 derives from `<target-dir>` through `<same_repository_filing>` for the invoking repository and equals `<target-dir>` for any other. When `$ARGUMENTS` names a checkout directory or a dependency, take it as the target; otherwise resolve it:

- **The spec-tree plugin, when the invoking repository is the plugins marketplace itself:** run `git rev-parse --show-toplevel` and read `<root>/.claude-plugin/marketplace.json`. When that file parses as JSON, its `name` is `outcomeeng`, and one entry of its `plugins` array has `name` equal to `spec-tree`, the invoking repository is the target — set `<target-dir>` to `<root>` and skip marketplace resolution. This identification runs before any marketplace lookup and never asks the operator for a path.
- **The spec-tree plugin (marketplace):** the registered Directory source. Resolve it from the marketplace registration:

  ```bash
  claude plugin marketplace list --json | python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py" --runtime claude --name outcomeeng
  ```

- **The `spx` CLI, or another spec-tree dependency:** the dependency's own checkout. Accept the path from the user or the invoking repository's configuration.
- **The invoking repository's own product:** when the observation concerns the current product — its own specs, skills, scripts, or workflow rather than an installed dependency — set `<target-dir>` to the root `git rev-parse --show-toplevel` reports. Step 1 then classifies it as the same repository, so a self-observation never falls through to the ambiguous-target question.

When the target is ambiguous or the path does not resolve, ask the user which dependency the follow-up concerns and for its checkout directory through the structured-question tool. NEVER guess a path. A target enters `<same_repository_filing>` only when its resolved absolute git common directory equals the invoking repository's; normalized origin identity identifies an external target for confirmation but never grants self-authorization.

</target_resolution>

<git_ref_resolution>
Resolve the target dependency's stable pickup anchor before filing the handoff. Use the target repository's current branch only when it exists on origin:

```bash
git -C <target-dir> branch --show-current
git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>
```

For an external target whose checkout is detached or whose current branch does not exist on origin, ask the user for the pushed target branch that should own the follow-up. For the invoking repository, Step 2 resolves the queue host's origin default branch instead. NEVER file a fresh-session handoff with an empty or guessed `git_ref`; `/pickup` uses `git_ref` as the branch it fetches and checks out in the dependency repository.

</git_ref_resolution>

<same_repository_filing>

Treat equal resolved absolute git common directories as one repository identity. This includes another linked worktree in the same pool. A separate clone has its own queue and remains an external target even when its normalized origin identity matches. Do not stop or redirect a same-repository observation into full `/handoff` closure.

Resolve a queue-safe `<queue-host>` before writing the session. Classify the layout from git alone: run `git -C <common-dir> config --get core.bare` against the absolute git common directory resolved for `<target-dir>` in Step 1, and `git -C <target-dir> worktree list --porcelain`.

- `core.bare` is `false` and the worktree listing carries exactly one `worktree` line — a single working tree: `<queue-host>` is the target root `git -C <target-dir> rev-parse --show-toplevel` reports.
- `core.bare` is `true` — a bare-repository pool: run `spx -C <target-dir> diagnose --format json`, read the sole `worktree-pool` record, and require `verdict=compliant` and a non-empty absolute `readings.mainCheckoutPath`; `<queue-host>` is that path. Require that `git -C <queue-host> rev-parse --path-format=absolute --git-common-dir` equals the common directory resolved in Step 1. Do not switch, detach, commit, or otherwise move the invoking or target worktree.
- `core.bare` is `false` with more than one `worktree` line, a `core.bare` value outside `true`/`false`, a non-compliant or missing `worktree-pool` record, or a main-checkout path whose common directory differs: the topology cannot produce a queue-safe checkout. Stop with the exact command output. Never reformulate the write against the active feature worktree.

Create exactly one fresh `todo` follow-up for every authorized invocation. Before the write, run `spx -C <queue-host> session list --json` once and read only the header fields it returns for `todo` and `doing` sessions — `id`, `status`, `goal`, `next_step`. Collect as `<overlap-ids>` the full ids whose `goal` or `next_step` names an affected path or skill from `<captured_fields>`. Never run `spx session show` on a listed session, never compare bodies, never probe origin for a stored branch, and never reuse or suppress the write because an overlap exists; queue consumers reconcile overlapping observations at pickup. The report names `<overlap-ids>` so the reader sees them beside the new record.

</same_repository_filing>

<workflow>

**Step 1 — Resolve and classify the target.** When `$ARGUMENTS` names an existing checkout directory, take it as the target only after confirming it is the repository to receive the follow-up. When `$ARGUMENTS` names a dependency token such as `spx`, `spec-tree`, or a CLI/plugin name, resolve the dependency's checkout directory per `<target_resolution>` instead of treating the token as a path. Otherwise determine which component the observation concerns and resolve its checkout directory per `<target_resolution>`, applying its invoking-repository identification before any marketplace lookup. Resolve both git common directories with `git rev-parse --path-format=absolute --git-common-dir` and `git -C <target-dir> rev-parse --path-format=absolute --git-common-dir`. Resolve both origin URLs with `git remote get-url origin` and `git -C <target-dir> remote get-url origin`, then normalize each to its lowercase host plus repository path by translating scp-style syntax to host/path form, removing the transport and user prefix, trimming leading and trailing slashes, and removing a terminal `.git`. Set `same_repository=true` only when the resolved absolute common directories are equal; otherwise set `same_repository=false`. Use normalized origin identity to identify and report the target, never to authorize its queue mutation. Resolve `<queue-host>` through `<same_repository_filing>` when `same_repository=true`; otherwise `<queue-host>` is `<target-dir>`.

**Step 2 — Resolve `git_ref`.** For a different repository, resolve the target repository's stable pickup branch per `<git_ref_resolution>`. For the invoking repository, run `git -C <queue-host> symbolic-ref --short refs/remotes/origin/HEAD`, remove the leading `origin/`, and verify the resulting `refs/remotes/origin/<default-branch>` with `git -C <queue-host> rev-parse --verify` before using it. When the symbolic ref is unset or the verification fails, stop with the exact command, exit code, and stderr — never proceed with an empty or guessed `git_ref`, and never write `refs/remotes/origin/HEAD` to repair it. The follow-up starts from the origin default branch regardless of the branch attached to `<queue-host>`. NEVER switch either checkout to obtain a branch.

**Step 3 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action on dependency pickup.
- `priority` — `high`, `medium`, or `low`.
- `git_ref` — the target dependency branch that exists on origin and that `/pickup` checks out.
- `specs`, `files` — empty arrays; Claude assigns none of the dependency's structure.

**Step 4 — Compose the body.** Write the observation from `<captured_fields>` using `<dependency_followup_body>` exactly. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 5 — Snapshot state and list overlaps.** Capture the exact output of `git status --porcelain=v1 --untracked-files=all` from the invoking repository as the before-state for the tracked-worktree mutation check. When `same_repository=true`, run the header-only overlap listing in `<same_repository_filing>` and record `<overlap-ids>`, possibly empty.

**Step 6 — GATE: Confirm an external target, then file.** When `same_repository=false`, the handoff writes into a different repository queue. Resolving or naming a path is not authorization to mutate that queue, so obtain confirmation through `AskUserQuestion` before the first mutating command, presenting:

- the **absolute** `<target-dir>` verbatim, as `git -C <target-dir> rev-parse --show-toplevel` reports it;
- that repository's normalized origin identity from step 1;
- the resolved `git_ref` and the follow-up's `goal`;
- two options — file the follow-up into that repository, or stop for inspection.

The explicit `/issue` invocation authorizes one fresh same-repository queue write, so `same_repository=true` does not add a second confirmation. Every `same_repository=false` target requires this confirmation, including a separate clone with the same normalized origin identity and a checkout path named directly in `$ARGUMENTS`. STOP on anything but explicit approval, leaving both repositories unchanged.

Then resolve the current agent session identity verbatim from the variable the agent publishes with `printenv CLAUDE_CODE_SESSION_ID` and STOP when it is empty. Run `spx -C <queue-host> session handoff`, passing the JSON header line then the body on stdin:

```bash
spx -C <queue-host> session handoff <<'EOF'
{"priority":"high","goal":"<output-shaped goal>","next_step":"<imperative first action>","git_ref":"<target-branch-on-origin>","specs":[],"files":[]}
# <short title>

<observation>
...
</observation>

<uncertainty>
...
</uncertainty>

<checked_facts>
...
</checked_facts>

<affected_paths>
...
</affected_paths>

<next_workflow_context>
...
</next_workflow_context>
EOF
```

`-C <queue-host>` runs the handoff against the owning repository's queue without moving the active checkout. For a different repository, the invoking session queue stays untouched. For the invoking repository, the only permitted queue delta is this one new `todo` follow-up.

**Step 7 — Verify the created follow-up.** Parse `<HANDOFF_ID>` and `<SESSION_FILE>` from the handoff output. Read that returned record once with `spx -C <queue-host> session show --json <HANDOFF_ID>`. Require `status=todo`; the Step 3 `goal`, `next_step`, `priority`, `git_ref`, empty `specs`, and empty `files`; a non-empty `agent_session_id` equal to the runtime identity resolved in Step 6; and a non-empty `created_at`. When `same_repository=false`, run `spx session show --json <HANDOFF_ID>` from the invoking repository and require the id to be absent there. Re-run `git status --porcelain=v1 --untracked-files=all` and require it to match the Step 5 snapshot byte-for-byte. A missing record, field mismatch, external-target copy in the invoking queue, or git-state difference blocks success and is reported with the observed values. Do not read any other session.

**Step 8 — Report.** Surface `result=created`, the verified `<HANDOFF_ID>`, and `<SESSION_FILE>` when the command supplies it, naming the repository whose queue owns the follow-up, and list `<overlap-ids>` verbatim as possible overlaps for the reader — or state that the header listing found none.

</workflow>

<constraints>

- NEVER edit, commit to, or push the owning repository's tracked source — the only possible effect is one session document `spx -C <queue-host> session handoff` writes into its `.spx/sessions/todo/`.
- NEVER alter the invoking repository's tracked git state or active branch. A same-repository filing adds exactly one fresh `todo` session.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency workflow classifies.
- NEVER guess the target checkout directory — resolve it deterministically or ask.
- NEVER guess `git_ref` — use a target branch that exists on origin or ask.
- NEVER read the body of, compare, archive, release, delete, edit, replace, move, or reuse an existing active session while filing the follow-up — the header listing is the only read of other sessions, and it only names possible overlaps.

</constraints>

<failure_modes>

**Failure 1: Claude filed a target-dependency handoff without a stable branch anchor.**

What happened: Claude wrote a fresh-session handoff header with `priority`, `goal`, `next_step`, `specs`, and `files`, but omitted `git_ref`.

Why it failed: The target repository's `/pickup` workflow uses `git_ref` as the origin branch it fetches and checks out. Without it, a dependency follow-up can anchor to the wrong checkout state or fail to resume.

How to avoid: Resolve the target dependency branch first, verify `refs/remotes/origin/<branch>` exists, and include that branch in the header's `git_ref`. Ask the user for a pushed target branch when the checkout is detached or the branch is not on origin.

**Failure 2: Claude turned filing into queue triage.**

What happened: Claude listed active sessions, read their bodies, judged whether an existing observation was semantically equivalent, probed origin for each candidate's stored branch, and reused a match instead of writing.

Why it failed: Filing one timestamped record became a second issue-triage workflow that delayed recording the observation, and a reused session carried none of the new facts. Queue consumers already reconcile overlap at pickup.

How to avoid: Read only the header listing, name possible overlaps in the report, run `spx session handoff` once, read only the returned record, and finish.

**Failure 3: Claude asked the operator for the plugins checkout it was standing in.**

What happened: Marketplace resolution returned no local source, so Claude asked the operator which checkout owned the spec-tree follow-up although the invoking repository carried the marketplace catalog naming `spec-tree`.

Why it failed: The invoking checkout already identified itself as the target; the question pushed a deterministic check onto the operator.

How to avoid: Read `<root>/.claude-plugin/marketplace.json` before any marketplace lookup and take the invoking repository as the target when it names the `outcomeeng` marketplace with the `spec-tree` plugin.

</failure_modes>

<success_criteria>

- The report names the exact owning checkout and queue host, classifies self-authorization solely by resolved git-common-directory equality, and records operator approval before any external-queue mutation.
- The result is exactly `created`, names the verified full session id and owning repository, and each authorized invocation creates exactly one new `todo` session.
- The stored follow-up has the dependency-followup body, empty `specs` and `files`, the resolved branch `git_ref`, and complete session identity metadata without dependency taxonomy.
- The report lists possible overlaps by full id from the header listing alone; filing reads no other session's body, performs no semantic deduplication or origin probe, and leaves the invoking repository's tracked git state byte-identical; a separate repository receives no mutation beyond the approved follow-up.
- An invoking checkout carrying the `outcomeeng` marketplace catalog with the `spec-tree` plugin is taken as the spec-tree target without a marketplace lookup or an operator-supplied path.

</success_criteria>
