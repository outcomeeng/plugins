---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into a spec-tree dependency's own session queue — for observations about the spec-tree plugin, the spx CLI, or another spec-tree dependency needing a change. NEVER edit a spec-tree dependency's installed source directly to record a needed fix; capture it as a handoff in that dependency's queue with this skill.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(pwd), Bash(spx --version:*), Bash(spx -C:* session handoff*), Bash(git -C:* branch --show-current), Bash(git -C:* rev-parse --verify refs/remotes/origin/*), Bash(claude plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*), AskUserQuestion
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

Gather from the invoking context, asking the user only for genuine gaps:

- **Observation** — what was observed: the behavior, the gap, the contradiction.
- **Uncertainty** — what remains unknown or unconfirmed.
- **Checked facts** — what was already verified (commands run, files read, versions observed) and their results.
- **Affected paths** — the paths or surfaces the observation touches, as observed (a file, a command, a skill name) — NOT a node address, decision index, or assertion type in the dependency's spec tree.
- **Next-workflow context** — what the dependency's next pickup needs to begin: how to reproduce, where to look, what "done" looks like.

NEVER assign the dependency's node addresses, decision indices, or assertion types — Claude supplies observations, not the dependency's spec-tree structure. Leave the handoff header `specs` and `files` empty; carry observed paths in the body prose.

</captured_fields>

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

`scripts/resolve_marketplace.py` is covered by this plugin's mapping-level marketplace-resolution test suite.

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

If the target checkout is detached or its current branch does not exist on origin, ask the user for the pushed target branch that should own the follow-up. NEVER file a Path C handoff with an empty or guessed `git_ref`; `/pickup` uses `git_ref` as the branch it fetches and checks out in the dependency repository.

</git_ref_resolution>

<workflow>

**Step 1 — Resolve the target.** When `$ARGUMENTS` names an existing checkout directory, take it as the target only after confirming it is the dependency checkout to receive the handoff. When `$ARGUMENTS` names a dependency token such as `spx`, `spec-tree`, or a CLI/plugin name, resolve the dependency's checkout directory per `<target_resolution>` instead of treating the token as a path. Otherwise determine which dependency the observation concerns and resolve its checkout directory per `<target_resolution>`.

**Step 2 — Resolve `git_ref`.** Resolve the target repository's stable pickup branch per `<git_ref_resolution>`.

**Step 3 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action on dependency pickup.
- `priority` — `high`, `medium`, or `low`.
- `git_ref` — the target dependency branch that exists on origin and that `/pickup` checks out.
- `specs`, `files` — empty arrays; Claude assigns none of the dependency's structure.

**Step 4 — Compose the body.** Write the observation as markdown from `<captured_fields>`: observation, uncertainty, checked facts, affected paths, next-workflow context. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 5 — File the follow-up.** Run `spx -C <target-dir> session handoff`, passing the JSON header line then the body on stdin:

```bash
spx -C <target-dir> session handoff <<'EOF'
{"priority":"high","goal":"<output-shaped goal>","next_step":"<imperative first action>","git_ref":"<target-branch-on-origin>","specs":[],"files":[]}
# <short title>

<observation body — affected paths, checked facts, uncertainty, next-workflow context>
EOF
```

`-C <target-dir>` runs the handoff against the dependency repository, so the recorded `git_ref` and the queued session belong to the target — the invoking repository's git state and session queue stay untouched.

**Step 6 — Report.** Surface the `<HANDOFF_ID>` and `<SESSION_FILE>` the command emits, naming the target repository the follow-up was filed into.

</workflow>

<constraints>

- NEVER edit, commit to, or push the target dependency's tracked source — the only effect on the target is the session document `spx -C <target-dir> session handoff` writes into its `.spx/sessions/todo/`.
- NEVER alter the invoking repository's git state or session queue — `-C <target-dir>` targets the dependency directly.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency workflow classifies.
- NEVER guess the target checkout directory — resolve it deterministically or ask.
- NEVER guess `git_ref` — use a target branch that exists on origin or ask.

</constraints>

<failure_modes>

**Failure 1: Claude filed a target-dependency handoff without a stable branch anchor.**

What happened: Claude wrote a Path C handoff header with `priority`, `goal`, `next_step`, `specs`, and `files`, but omitted `git_ref`.

Why it failed: The target repository's `/pickup` workflow uses `git_ref` as the origin branch it fetches and checks out. Without it, a dependency follow-up can anchor to the wrong checkout state or fail to resume.

How to avoid: Resolve the target dependency branch first, verify `refs/remotes/origin/<branch>` exists, and include that branch in the header's `git_ref`. Ask the user for a pushed target branch when the checkout is detached or the branch is not on origin.

</failure_modes>

<success_criteria>

- [ ] Target dependency checkout directory resolved deterministically or confirmed with the user
- [ ] Target dependency `git_ref` resolved to a branch that exists on origin or confirmed with the user
- [ ] Observation captured as observation-only — no dependency node addresses, decision indices, or assertion types
- [ ] Header carries an output-shaped `goal`, an imperative `next_step`, and the target dependency `git_ref`; `specs` and `files` empty
- [ ] `spx -C <target-dir> session handoff` filed the follow-up into the target repository's queue
- [ ] The invoking repository's git state and session queue are unchanged
- [ ] The created `<HANDOFF_ID>` and `<SESSION_FILE>` reported, naming the target repository

</success_criteria>
