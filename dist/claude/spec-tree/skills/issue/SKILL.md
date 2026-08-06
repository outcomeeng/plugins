---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into a spec-tree dependency's own session queue — for observations about the spec-tree plugin, the spx CLI, or another spec-tree dependency needing a change. NEVER edit a spec-tree dependency's installed source directly to record a needed fix; capture it as a handoff in that dependency's queue with this skill.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(pwd), Bash(printenv CODEX_THREAD_ID), Bash(printenv CLAUDE_SESSION_ID), Bash(spx --version:*), Bash(spx session show:*), Bash(spx -C:* session handoff*), Bash(spx -C:* session show*), Bash(git status:*), Bash(git rev-parse --path-format=absolute --git-common-dir), Bash(git remote get-url origin), Bash(git -C:* branch --show-current), Bash(git -C:* rev-parse --path-format=absolute --git-common-dir), Bash(git -C:* rev-parse --show-toplevel), Bash(git -C:* rev-parse --verify refs/remotes/origin/*), Bash(git -C:* remote get-url origin), Bash(claude plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*), AskUserQuestion
---

<context>
**Working Directory:**
!`pwd`

**spx CLI:**
!`spx --version`

</context>

<objective>
A follow-up recorded as a handoff session in a spec-tree dependency repository's own session queue — capturing Claude's observation and shaped so the dependency workflow resumes from it.

</objective>

<when_to_invoke>
Editing a spec-tree dependency's installed source directly to record a needed change rewrites shared infrastructure for every consumer session that uses it, with no review. The `/issue` skill files the observation as a handoff into the dependency's own session queue instead, where the dependency workflow triages and acts on it.

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
Resolve the target dependency's checkout directory — the working directory `spx -C <target-dir> session handoff` runs against. When `$ARGUMENTS` names a checkout directory or a dependency, take it as the target; otherwise resolve it:

- **The spec-tree plugin (marketplace):** the registered Directory source. Resolve it from the marketplace registration:

  ```bash
  claude plugin marketplace list --json | python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py" --runtime claude --name outcomeeng
  ```

- **The `spx` CLI, or another spec-tree dependency:** the dependency's own checkout. Accept the path from the user or the invoking repository's configuration.

When the target is ambiguous or the path does not resolve, ask the user which dependency the follow-up concerns and for its checkout directory through the structured-question tool. NEVER guess a path.

</target_resolution>

<script_testing>

`${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py` is covered by this plugin's mapping-level marketplace-resolution test suite.

Tested inputs:

- Claude marketplace JSON with a Directory source returns the registered path.
- Codex marketplace JSON with a local `marketplaceSource` returns the registered path.
- Malformed marketplace JSON returns a clear invalid-JSON error.
- A missing local marketplace returns a clear target-resolution error.
- No temporary files are created.

</script_testing>

<git_ref_resolution>
Resolve the target dependency's stable pickup anchor before filing the handoff. Use the target repository's current branch only when it exists on origin:

```bash
git -C <target-dir> branch --show-current
git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>
```

If the target checkout is detached or its current branch does not exist on origin, ask the user for the pushed target branch that should own the follow-up. NEVER file a fresh-session handoff with an empty or guessed `git_ref`; `/pickup` uses `git_ref` as the branch it fetches and checks out in the dependency repository.

</git_ref_resolution>

<workflow>

**Step 1 — Resolve the target.** When `$ARGUMENTS` names an existing checkout directory, take it as the target only after confirming it is the dependency checkout to receive the handoff. When `$ARGUMENTS` names a dependency token such as `spx`, `spec-tree`, or a CLI/plugin name, resolve the dependency's checkout directory per `<target_resolution>` instead of treating the token as a path. Otherwise determine which dependency the observation concerns and resolve its checkout directory per `<target_resolution>`. Resolve both git common directories with `git rev-parse --path-format=absolute --git-common-dir` and `git -C <target-dir> rev-parse --path-format=absolute --git-common-dir`. Resolve both origin URLs with `git remote get-url origin` and `git -C <target-dir> remote get-url origin`, then normalize each to its lowercase host plus repository path by translating scp-style syntax to host/path form, removing the transport and user prefix, trimming leading and trailing slashes, and removing a terminal `.git`. If either the absolute common directories or normalized origin identities are equal, STOP because `/issue` is only for a different dependency repository and the invoking repository must remain unchanged. The common-directory comparison rejects another worktree in the same pool; the origin comparison rejects a separate clone of the same product.

**Step 2 — Resolve `git_ref`.** Resolve the target repository's stable pickup branch per `<git_ref_resolution>`.

**Step 3 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action on dependency pickup.
- `priority` — `high`, `medium`, or `low`.
- `git_ref` — the target dependency branch that exists on origin and that `/pickup` checks out.
- `specs`, `files` — empty arrays; Claude assigns none of the dependency's structure.

**Step 4 — Compose the body.** Write the observation from `<captured_fields>` using `<dependency_followup_body>` exactly. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 5 — Snapshot the invoking repository.** Before filing, capture the exact output of `git status --porcelain=v1 --untracked-files=all` from the invoking repository. This is the before-state for the tracked-worktree mutation check.

**Step 6 — GATE: Confirm the target, then file the follow-up.** The handoff writes into a repository the operator did not name in this turn, resolved from a marketplace registration rather than supplied as a path. Resolving a path is not authorization to write to it, so obtain confirmation through `AskUserQuestion` before the first mutating command, presenting:

- the **absolute** `<target-dir>` verbatim, as `git -C <target-dir> rev-parse --show-toplevel` reports it;
- that repository's normalized origin identity from step 1;
- the resolved `git_ref` and the follow-up's `goal`;
- two options — file the follow-up into that repository, or stop for inspection.

Skip the confirmation only when `$ARGUMENTS` named the target checkout directly and step 1 already confirmed it; a target reached by marketplace resolution always asks. STOP on anything but explicit approval, leaving both repositories unchanged.

Then resolve the current runtime identity verbatim (`printenv CODEX_THREAD_ID` in Codex; `printenv CLAUDE_SESSION_ID` in Claude Code) and STOP when it is empty. Run `spx -C <target-dir> session handoff`, passing the JSON header line then the body on stdin:

```bash
spx -C <target-dir> session handoff <<'EOF'
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

`-C <target-dir>` runs the handoff against the dependency repository, so the recorded `git_ref` and the queued session belong to the target — the invoking repository's git state and session queue stay untouched.

**Step 7 — Verify the stored follow-up.** Parse `<HANDOFF_ID>` and `<SESSION_FILE>` from the command output, then run `spx -C <target-dir> session show --json <HANDOFF_ID>`. Require the command to find the handoff in that target repository and require its stored `git_ref` to equal the origin-backed branch resolved in step 2, with `specs` and `files` both empty arrays. Require its stored `agent_session_id` to equal the runtime identity resolved in step 6 and require a non-empty `created_at`. Run `spx session show --json <HANDOFF_ID>` from the invoking repository and require it to report that the target handoff id is absent there; unrelated invoking-repository queue changes are ignored. Re-run `git status --porcelain=v1 --untracked-files=all` and require it to match the step 5 snapshot byte-for-byte. A missing target handoff, field mismatch, invoking-repository copy of the handoff id, or git-state difference blocks success and is reported with the observed values.

**Step 8 — Report.** Surface the verified `<HANDOFF_ID>` and `<SESSION_FILE>`, naming the target repository the follow-up was filed into.

</workflow>

<constraints>

- NEVER edit, commit to, or push the target dependency's tracked source — the only effect on the target is the session document `spx -C <target-dir> session handoff` writes into its `.spx/sessions/todo/`.
- NEVER alter the invoking repository's git state or session queue — `-C <target-dir>` targets the dependency directly.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency workflow classifies.
- NEVER guess the target checkout directory — resolve it deterministically or ask.
- NEVER guess `git_ref` — use a target branch that exists on origin or ask.
- NEVER target the invoking repository — current-product observations stay in that product's normal spec-tree workflow.

</constraints>

<failure_modes>

**Failure 1: Claude filed a target-dependency handoff without a stable branch anchor.**

What happened: Claude wrote a fresh-session handoff header with `priority`, `goal`, `next_step`, `specs`, and `files`, but omitted `git_ref`.

Why it failed: The target repository's `/pickup` workflow uses `git_ref` as the origin branch it fetches and checks out. Without it, a dependency follow-up can anchor to the wrong checkout state or fail to resume.

How to avoid: Resolve the target dependency branch first, verify `refs/remotes/origin/<branch>` exists, and include that branch in the header's `git_ref`. Ask the user for a pushed target branch when the checkout is detached or the branch is not on origin.

</failure_modes>

<success_criteria>

- [ ] Target resolution produced the exact checkout directory used by every `spx -C <target-dir>` command.
- [ ] The invoking and target absolute git common directories differ.
- [ ] The invoking and target normalized origin repository identities differ.
- [ ] `git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>` succeeded for the stored `git_ref`.
- [ ] Every target not named directly by `$ARGUMENTS` as a checkout path — whether marketplace-resolved or resolved from the invoking repository's configuration — was approved by the operator through the step 6 confirmation, which named the absolute target root verbatim, before any `spx -C <target-dir>` mutation ran.
- [ ] `spx -C <target-dir> session show --json <HANDOFF_ID>` found the created handoff in the target queue and reported the expected `git_ref`, `specs: []`, `files: []`, runtime `agent_session_id`, and non-empty `created_at`.
- [ ] The observation body contains no dependency node address, decision index, or assertion type.
- [ ] `spx session show --json <HANDOFF_ID>` reports the target handoff id absent from the invoking repository, while its `git status --porcelain=v1 --untracked-files=all` output matches the pre-handoff snapshot byte-for-byte.
- [ ] The verified `<HANDOFF_ID>` and `<SESSION_FILE>` are reported with the target repository.

</success_criteria>
