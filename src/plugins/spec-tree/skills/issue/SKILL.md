---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into a spec-tree dependency's own session queue — for observations about the spec-tree plugin, the spx CLI, or another spec-tree dependency needing a change. NEVER edit a spec-tree dependency's installed source directly to record a needed fix; capture it as a handoff in that dependency's queue with this skill.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(pwd), Bash(printf:*), Bash(spx --version:*), Bash(spx -C:* session handoff*), Bash(spx -C:* session show:*), Bash(git -C:* branch --show-current), Bash(git -C:* branch --remotes --contains HEAD), Bash(git -C:* symbolic-ref --short refs/remotes/origin/HEAD), Bash(git -C:* rev-parse HEAD), Bash(git -C:* rev-parse --verify refs/remotes/origin/*), {!% if target == 'codex' %!}Bash(codex plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*),{!% else %!}Bash(claude plugin marketplace list:*), Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py":*),{!% endif %!} {{! tool('ask_user') !}}
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

<target_resolution>
Resolve the target dependency's checkout directory — the working directory `spx -C <target-dir> session handoff` runs against. When `$ARGUMENTS` names a checkout directory or a dependency, take it as the target; otherwise resolve it:

- **The spec-tree plugin (marketplace):** the registered Directory source. Resolve it from the marketplace registration:
  {!% if target == 'codex' %!}
  ```bash
  codex plugin marketplace list --json | python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py" --runtime codex --name outcomeeng
  ```
  {!% else %!}
  ```bash
  claude plugin marketplace list --json | python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_marketplace.py" --runtime claude --name outcomeeng
  ```
  {!% endif %!}
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
Resolve whether the target dependency has a non-default work branch that pickup must preserve. Include `git_ref` only when that current work branch exists on origin:

```bash
git -C <target-dir> branch --show-current
git -C <target-dir> rev-parse --verify refs/remotes/origin/<branch>
```

Resolve the default branch with `git -C <target-dir> symbolic-ref --short refs/remotes/origin/HEAD`, then remove its leading `origin/` to obtain the branch-name form the session contract stores. When the current branch equals that normalized default branch, or when the checkout is detached, run `git -C <target-dir> branch --remotes --contains HEAD` and omit `git_ref` only when the output contains an `origin/*` ref. Record the expected derived anchor before filing: the normalized default branch name for a default-branch checkout, or `git -C <target-dir> rev-parse HEAD` for a detached checkout. When no origin ref contains `HEAD`, ask for a pushed target branch instead of omitting or guessing the anchor.

</git_ref_resolution>

<workflow>

**Step 1 — Resolve the target.** When `$ARGUMENTS` names an existing checkout directory, take it as the target only after confirming it is the dependency checkout to receive the handoff. When `$ARGUMENTS` names a dependency token such as `spx`, `spec-tree`, or a CLI/plugin name, resolve the dependency's checkout directory per `<target_resolution>` instead of treating the token as a path. Otherwise determine which dependency the observation concerns and resolve its checkout directory per `<target_resolution>`.

**Step 2 — Resolve the pickup anchor.** Resolve an optional target work branch per `<git_ref_resolution>`; otherwise let the target repository derive its default-branch or commit-SHA anchor.

**Step 3 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action on dependency pickup.
- `priority` — `high`, `medium`, or `low`.
- `git_ref` — include only for a target dependency work branch that exists on origin and that `/pickup` must check out; omit for a derived default-branch or commit-SHA anchor.
- `specs`, `files` — empty arrays; Claude assigns none of the dependency's structure.

**Step 4 — Compose the body.** Write the observation as markdown from `<captured_fields>`: observation, uncertainty, checked facts, affected paths, next-workflow context. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 5 — File the follow-up.** Run `spx -C <target-dir> session handoff`, passing the JSON header line then the body on stdin:

```bash
spx -C <target-dir> session handoff <<'EOF'
{"priority":"high","goal":"<output-shaped goal>","next_step":"<imperative first action>","git_ref":"<target-branch-on-origin>","specs":[],"files":[]}
# <short title>

## Observation
<observation>

## Uncertainty
<uncertainty>

## Checked facts
<checked facts>

## Affected paths
<affected paths>

## Next-workflow context
<next-workflow context>
EOF
```

For a programmatic runner that requires one physical command line, send the same bytes with one `printf` argument per output line:

```bash
printf '%s\n' '{"priority":"high","goal":"<output-shaped goal>","next_step":"<imperative first action>","git_ref":"<target-branch-on-origin>","specs":[],"files":[]}' '# <short title>' '' '## Observation' '<observation>' '' '## Uncertainty' '<uncertainty>' '' '## Checked facts' '<checked facts>' '' '## Affected paths' '<affected paths>' '' '## Next-workflow context' '<next-workflow context>' | spx -C <target-dir> session handoff
```

Omit the `git_ref` member when no target work branch must be preserved. Literal apostrophes inside a single-quoted `printf` argument use `'"'"'` so the one-line command preserves the body bytes.

`-C <target-dir>` runs the handoff against the dependency repository, so the recorded `git_ref` and the queued session belong to the target — the invoking repository's git state and session queue stay untouched.

**Step 6 — Verify and report.** Parse `<HANDOFF_ID>` and `<SESSION_FILE>`, then run `spx -C <target-dir> session show --json <HANDOFF_ID>`. Confirm its stored `git_ref` equals the supplied work branch, the normalized default branch name, or the detached commit SHA recorded as the expected derived anchor in Step 2. A missing or different anchor stops the workflow as a failed filing; do not report the handoff as resumable. After the anchor matches, surface the exact `<HANDOFF_ID>` and `<SESSION_FILE>`, naming the target repository the follow-up was filed into.

</workflow>

<constraints>

- NEVER edit, commit to, or push the target dependency's tracked source — the only effect on the target is the session document `spx -C <target-dir> session handoff` writes into its `.spx/sessions/todo/`.
- NEVER alter the invoking repository's git state or session queue — `-C <target-dir>` targets the dependency directly.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency workflow classifies.
- NEVER guess the target checkout directory — resolve it deterministically or ask.
- NEVER guess `git_ref` — include a verified target work branch, omit it for a derived default-branch or commit-SHA anchor, or ask when unpushed target work needs preservation.

</constraints>

<failure_modes>

**Failure 1: Claude omitted the work branch while target work still needed preservation.**

What happened: Claude wrote a fresh handoff header without `git_ref` while the target dependency had unpushed work on a feature branch.

Why it failed: The derived default-branch or commit-SHA anchor could not preserve work that existed only on the feature branch.

How to avoid: When target work must survive pickup, resolve the target dependency branch, verify `refs/remotes/origin/<branch>` exists, and include it as `git_ref`. Omit `git_ref` only when the target repository can derive the intended default-branch or commit-SHA anchor.

</failure_modes>

<success_criteria>

- The target dependency queue contains one fresh, resumable handoff whose stored `git_ref`, read back through `spx -C <target-dir> session show --json <HANDOFF_ID>`, equals the supplied origin branch or the intended derived default-branch or commit-SHA anchor.
- The handoff records only the observation and an output-shaped continuation goal; it invents no target node, decision, assertion, or implementation detail.
- The handoff header leaves `specs` and `files` empty so the target session re-derives governance after pickup.
- The invoking repository's git state and session queue remain byte-for-byte unchanged.
- The operator receives the target repository identity plus the exact `<HANDOFF_ID>` and `<SESSION_FILE>` needed to inspect the filed follow-up.

</success_criteria>
