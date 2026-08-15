---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into the owning repository's session queue — including the invoking repository, the spec-tree plugin repository, the spx CLI repository, or another spec-tree dependency. NEVER edit installed dependency source or run the current work through full handoff closure merely to record a needed follow-up.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(printenv CODEX_THREAD_ID), Bash(printenv CLAUDE_SESSION_ID), Bash(spx session list:*), Bash(spx session show:*), Bash(spx -C:* diagnose*), Bash(spx -C:* session handoff*), Bash(spx -C:* session list*), Bash(spx -C:* session show*), Bash(git status:*), Bash(git rev-parse --path-format=absolute --git-common-dir), Bash(git remote get-url origin), Bash(git -C:* branch --show-current), Bash(git -C:* rev-parse --path-format=absolute --git-common-dir), Bash(git -C:* rev-parse --show-toplevel), Bash(git -C:* rev-parse --verify refs/remotes/origin/*), Bash(git -C:* remote get-url origin), Bash(claude plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*), AskUserQuestion
---

<objective>
A minimal follow-up filed or reused in the owning spec-tree repository's active session queue — capturing Claude's observation without disturbing tracked work, the active branch, or unrelated sessions.

</objective>

<when_to_invoke>
Editing a spec-tree component's installed source directly to record a needed change rewrites shared infrastructure for every consumer session that uses it, with no review. The `/issue` skill files or reuses the observation in the owning repository's session queue instead, where that repository's workflow triages and acts on it. The owning repository may be the invoking repository; recording a proportional follow-up never requires closing the current work.

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

When the target is ambiguous or the path does not resolve, ask the user which dependency the follow-up concerns and for its checkout directory through the structured-question tool. NEVER guess a path. A target that resolves to the invoking repository by git common directory or normalized origin identity is valid and enters `<same_repository_filing>`.

</target_resolution>

<git_ref_resolution>
Resolve the target dependency's stable pickup anchor before filing the handoff. Use the target repository's current branch only when it exists on origin:

```bash
git -C <target-dir> branch --show-current
git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>
```

If the target checkout is detached or its current branch does not exist on origin, ask the user for the pushed target branch that should own the follow-up. NEVER file a fresh-session handoff with an empty or guessed `git_ref`; `/pickup` uses `git_ref` as the branch it fetches and checks out in the dependency repository.

</git_ref_resolution>

<same_repository_filing>

Treat equal absolute git common directories or equal normalized origin identities as one repository identity. This includes another linked worktree in the same pool and a separate clone of the same origin. Do not stop or redirect the observation into full `/handoff` closure.

Resolve a queue-safe `<queue-host>` before reading or writing sessions:

- For a compliant single-working-tree target, use the target root.
- For a compliant bare-repository pool, run `spx -C <target-dir> diagnose --format json`, read the sole `worktree-pool` record, and use its absolute `readings.mainCheckoutPath`. Require `verdict=compliant`, a non-empty absolute main-checkout path, and matching normalized origin identity. Do not switch, detach, commit, or otherwise move the invoking or target worktree.
- If the topology cannot produce a queue-safe checkout, stop with the exact diagnostic. Never reformulate the write against the active feature worktree.

Before mutation, run `spx -C <queue-host> session list --json`, which covers both `todo` and `doing`, then snapshot every returned record's complete body with `spx -C <queue-host> session show <id>`. Inspect those bodies for plausible matches. A match carries the dependency-followup body contract and describes the same observation and affected surfaces; a different title or wording does not make the observation distinct. When matches exist, reuse exactly one — prefer `doing` over `todo`, then the oldest full session id — report any additional matching ids as pre-existing duplicates, and create nothing. Deduplication is by reuse, never by archiving, releasing, deleting, editing, or moving an existing session.

When no match exists, create exactly one follow-up against `<queue-host>`. Snapshot every active session record first and require all pre-existing ids, statuses, metadata, and bodies to remain unchanged afterward. The only permitted queue delta is the one new `todo` session.

</same_repository_filing>

<workflow>

**Step 1 — Resolve and classify the target.** When `$ARGUMENTS` names an existing checkout directory, take it as the target only after confirming it is the repository to receive the follow-up. When `$ARGUMENTS` names a dependency token such as `spx`, `spec-tree`, or a CLI/plugin name, resolve the dependency's checkout directory per `<target_resolution>` instead of treating the token as a path. Otherwise determine which component the observation concerns and resolve its checkout directory per `<target_resolution>`. Resolve both git common directories with `git rev-parse --path-format=absolute --git-common-dir` and `git -C <target-dir> rev-parse --path-format=absolute --git-common-dir`. Resolve both origin URLs with `git remote get-url origin` and `git -C <target-dir> remote get-url origin`, then normalize each to its lowercase host plus repository path by translating scp-style syntax to host/path form, removing the transport and user prefix, trimming leading and trailing slashes, and removing a terminal `.git`. Set `same_repository=true` when either the absolute common directories or normalized origin identities are equal; otherwise set `same_repository=false`. Equal identity is a valid same-repository filing, not a stop. Resolve `<queue-host>` through `<same_repository_filing>` when `same_repository=true`; otherwise `<queue-host>` is `<target-dir>`.

**Step 2 — Resolve `git_ref`.** For a different repository, resolve the target repository's stable pickup branch per `<git_ref_resolution>`. For the invoking repository, resolve the queue host's current branch and verify it exists on origin; the follow-up starts from the queue host's stable branch rather than the active feature branch. NEVER switch either checkout to obtain a branch.

**Step 3 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action on dependency pickup.
- `priority` — `high`, `medium`, or `low`.
- `git_ref` — the target dependency branch that exists on origin and that `/pickup` checks out.
- `specs`, `files` — empty arrays; Claude assigns none of the dependency's structure.

**Step 4 — Compose the body.** Write the observation from `<captured_fields>` using `<dependency_followup_body>` exactly. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 5 — Snapshot state and deduplicate.** Before filing, capture the exact output of `git status --porcelain=v1 --untracked-files=all` from the invoking repository. This is the before-state for the tracked-worktree mutation check. When `same_repository=true`, run the active-queue search and snapshot in `<same_repository_filing>`. If a matching session exists, record its full id as `<HANDOFF_ID>`, set `result=reused`, and skip Step 6's mutation.

**Step 6 — GATE: Confirm an external target, then file when needed.** When `result=reused`, perform no mutation and continue to verification. When `same_repository=false`, the handoff writes into a repository the operator may not have named in this turn. Resolving a path is not authorization to write there, so obtain confirmation through `AskUserQuestion` before the first mutating command unless `$ARGUMENTS` named that checkout path directly, presenting:

- the **absolute** `<target-dir>` verbatim, as `git -C <target-dir> rev-parse --show-toplevel` reports it;
- that repository's normalized origin identity from step 1;
- the resolved `git_ref` and the follow-up's `goal`;
- two options — file the follow-up into that repository, or stop for inspection.

Skip external-target confirmation only when `$ARGUMENTS` named the different checkout directly and step 1 already confirmed it. The explicit `/issue` invocation authorizes one deduplicated same-repository queue write, so `same_repository=true` does not add a second confirmation. STOP on anything but explicit approval, leaving both repositories unchanged.

Then resolve the current runtime identity verbatim (`printenv CODEX_THREAD_ID` in Codex; `printenv CLAUDE_SESSION_ID` in Claude Code) and STOP when it is empty. Run `spx -C <queue-host> session handoff`, passing the JSON header line then the body on stdin:

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

**Step 7 — Verify the stored or reused follow-up.** For `result=created`, parse `<HANDOFF_ID>` and `<SESSION_FILE>` from the command output. For either result, run `spx -C <queue-host> session show --json <HANDOFF_ID>` and require the session to exist in the owning repository with empty `specs` and `files`, non-empty `git_ref`, non-empty `agent_session_id`, and non-empty `created_at`. A created session must carry the Step 2 `git_ref` and the runtime identity resolved in Step 6; a reused session must remain byte-identical to its Step 5 snapshot rather than being rewritten to the newly resolved branch or runtime identity. When `same_repository=false`, run `spx session show --json <HANDOFF_ID>` from the invoking repository and require the id to be absent there. When `same_repository=true`, require every pre-existing active-session record and body to be unchanged for either result; for `result=created`, additionally require exactly one new `todo` id equal to `<HANDOFF_ID>`. Re-run `git status --porcelain=v1 --untracked-files=all` and require it to match the Step 5 snapshot byte-for-byte. A missing follow-up, field mismatch, unexpected queue delta, external-target copy in the invoking queue, or git-state difference blocks success and is reported with the observed values.

**Step 8 — Report.** Surface `result=created|reused`, the verified `<HANDOFF_ID>`, and `<SESSION_FILE>` when the command supplies it, naming the repository whose queue owns the follow-up. When pre-existing duplicates were observed, list their full ids without mutating them.

</workflow>

<constraints>

- NEVER edit, commit to, or push the owning repository's tracked source — the only possible effect is one session document `spx -C <queue-host> session handoff` writes into its `.spx/sessions/todo/` when no active semantic match exists.
- NEVER alter the invoking repository's tracked git state or active branch. A same-repository filing may add one deduplicated `todo` session and makes no other queue change.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency workflow classifies.
- NEVER guess the target checkout directory — resolve it deterministically or ask.
- NEVER guess `git_ref` — use a target branch that exists on origin or ask.
- NEVER archive, release, delete, edit, replace, or move an existing session while deduplicating — reuse is the only deduplication mutation policy.

</constraints>

<failure_modes>

**Failure 1: Claude filed a target-dependency handoff without a stable branch anchor.**

What happened: Claude wrote a fresh-session handoff header with `priority`, `goal`, `next_step`, `specs`, and `files`, but omitted `git_ref`.

Why it failed: The target repository's `/pickup` workflow uses `git_ref` as the origin branch it fetches and checks out. Without it, a dependency follow-up can anchor to the wrong checkout state or fail to resume.

How to avoid: Resolve the target dependency branch first, verify `refs/remotes/origin/<branch>` exists, and include that branch in the header's `git_ref`. Ask the user for a pushed target branch when the checkout is detached or the branch is not on origin.

</failure_modes>

<success_criteria>

- [ ] Target resolution produced the exact owning checkout and the queue-safe checkout used by every `spx -C <queue-host>` session command.
- [ ] Equal git common directories or normalized origin identities were classified as `same_repository=true`; unequal identities were classified as `same_repository=false`.
- [ ] Same-repository filing resolved a queue-safe checkout without switching, detaching, committing, or handing off the active worktree.
- [ ] Both `todo` and `doing` were searched before a same-repository write; one matching active follow-up was reused, or exactly one new `todo` follow-up was created when no match existed.
- [ ] `git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>` succeeded for the stored `git_ref`.
- [ ] Every different-repository target not named directly by `$ARGUMENTS` as a checkout path was approved by the operator through the Step 6 confirmation, which named the absolute target root verbatim, before mutation; a same-repository filing relied on the explicit `/issue` invocation and made at most one deduplicated queue write.
- [ ] `spx -C <queue-host> session show --json <HANDOFF_ID>` found the handoff with `specs: []`, `files: []`, non-empty `git_ref`, non-empty `agent_session_id`, and non-empty `created_at`; a created handoff carried the resolved branch and current runtime identity, while a reused handoff stayed byte-identical to its snapshot.
- [ ] The observation body contains no dependency node address, decision index, or assertion type.
- [ ] For a different repository, `spx session show --json <HANDOFF_ID>` reports the target handoff id absent from the invoking repository; for the invoking repository, every pre-existing active session remains unchanged and the only permitted delta is one created `todo` id.
- [ ] The invoking repository's `git status --porcelain=v1 --untracked-files=all` output matches the pre-handoff snapshot byte-for-byte.
- [ ] `result=created|reused`, the verified `<HANDOFF_ID>`, and `<SESSION_FILE>` when available are reported with the owning repository.

</success_criteria>
