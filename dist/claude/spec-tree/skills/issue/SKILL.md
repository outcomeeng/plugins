---
name: issue
description: >-
  ALWAYS invoke this skill when filing a follow-up into a spec-tree dependency's own session queue — when an agent in a consumer or product repository notices the spec-tree plugin, the spx CLI, or another spec-tree dependency needs a change. NEVER edit a spec-tree dependency's installed source directly to record a needed fix; capture it as a handoff in that dependency's queue with this skill.
argument-hint: "[target-dir-or-dependency]"
allowed-tools: Read, Grep, Glob, Bash(pwd), Bash(spx --version:*), Bash(spx session handoff:*), Bash(claude plugin marketplace list:*), Bash(python3:*), Bash(printf:*), Bash(echo:*), AskUserQuestion
---

<context>
**Working Directory:**
!`pwd`

**spx CLI:**
!`spx --version || echo 'Ask user to install spx CLI: "npm install --global @outcomeeng/spx"'`

</context>

<objective>
A follow-up recorded as a handoff session in a spec-tree dependency repository's own session queue — capturing the invoking agent's observation and shaped so the dependency's agents resume from it.

</objective>

<when_to_invoke>
Editing a spec-tree dependency's installed source directly to record a needed change rewrites shared infrastructure for every agent that uses it, with no review. The `/issue` skill files the observation as a handoff into the dependency's own session queue instead, where the dependency's agents triage and act on it through their own workflows.

</when_to_invoke>

<captured_fields>
Capture the invoking agent's OBSERVATION only — never the dependency's internal taxonomy. The agent reports what it saw; the dependency's own agents classify it against their spec tree.

Gather from the invoking context, asking the user only for genuine gaps:

- **Observation** — what was observed: the behavior, the gap, the contradiction.
- **Uncertainty** — what remains unknown or unconfirmed.
- **Checked facts** — what was already verified (commands run, files read, versions observed) and their results.
- **Affected paths** — the paths or surfaces the observation touches, as observed (a file, a command, a skill name) — NOT a node address, decision index, or assertion type in the dependency's spec tree.
- **Next-workflow context** — what the dependency's next agent needs to begin: how to reproduce, where to look, what "done" looks like.

NEVER assign the dependency's node addresses, decision indices, or assertion types — the invoking agent supplies observations, not the dependency's spec-tree structure. Leave the handoff header `specs` and `files` empty; carry observed paths in the body prose.

</captured_fields>

<target_resolution>
Resolve the target dependency's checkout directory — the working directory `spx session handoff -C <target-dir>` runs against. When `$ARGUMENTS` names a checkout directory or a dependency, take it as the target; otherwise resolve it:

- **The spec-tree plugin (marketplace):** the registered Directory source. Resolve it from the marketplace registration:

  ```bash
  claude plugin marketplace list --json | python3 -c 'import json,sys; print(next((e["path"] for e in json.load(sys.stdin) if e.get("source")=="directory"), ""))'
  ```

- **The `spx` CLI, or another spec-tree dependency:** the dependency's own checkout. Accept the path from the user or the invoking repository's configuration.

When the target is ambiguous or the path does not resolve, ask the user which dependency the follow-up concerns and for its checkout directory through the structured-question tool. NEVER guess a path.

</target_resolution>

<workflow>

**Step 1 — Resolve the target.** When `$ARGUMENTS` names a dependency or a checkout directory, take it as the target. Otherwise determine which dependency the observation concerns and resolve its checkout directory per `<target_resolution>`.

**Step 2 — Compose the header.** Build the JSON header:

- `goal` — output-shaped: name the deliverable or end-state the follow-up produces, not a generic activity verb.
- `next_step` — imperative: the first action the dependency's agent takes on pickup.
- `priority` — `high`, `medium`, or `low`.
- `specs`, `files` — empty arrays; the invoking agent assigns none of the dependency's structure.

**Step 3 — Compose the body.** Write the observation as markdown from `<captured_fields>`: observation, uncertainty, checked facts, affected paths, next-workflow context. State observations as facts; do not prescribe the dependency's fix in its own taxonomy.

**Step 4 — File the follow-up.** Run `spx session handoff -C <target-dir>`, piping the JSON header line then the body to stdin. An interactive Claude Code or Codex session may use a quoted heredoc; a programmatic runner uses one physical `printf` line:

```bash
printf '%s\n' '{"priority":"high","goal":"<output-shaped goal>","next_step":"<imperative first action>","specs":[],"files":[]}' '# <short title>' '' '<observation body — affected paths, checked facts, uncertainty, next-workflow context>' | spx session handoff -C <target-dir>
```

`-C <target-dir>` runs the handoff against the dependency repository, so the recorded `git_ref` and the queued session belong to the target — the invoking repository's git state and session queue stay untouched.

**Step 5 — Report.** Surface the `<HANDOFF_ID>` and `<SESSION_FILE>` the command emits, naming the target repository the follow-up was filed into.

</workflow>

<constraints>

- NEVER edit, commit to, or push the target dependency's tracked source — the only effect on the target is the session document `spx session handoff -C` writes into its `.spx/sessions/todo/`.
- NEVER alter the invoking repository's git state or session queue — `-C <target-dir>` targets the dependency directly.
- NEVER record the dependency's internal taxonomy (node address, decision index, assertion type) — capture observations; the dependency's agents classify.
- NEVER guess the target checkout directory — resolve it deterministically or ask.

</constraints>

<success_criteria>

- [ ] Target dependency checkout directory resolved deterministically or confirmed with the user
- [ ] Observation captured as observation-only — no dependency node addresses, decision indices, or assertion types
- [ ] Header carries an output-shaped `goal` and an imperative `next_step`; `specs` and `files` empty
- [ ] `spx session handoff -C <target-dir>` filed the follow-up into the target repository's queue
- [ ] The invoking repository's git state and session queue are unchanged
- [ ] The created `<HANDOFF_ID>` and `<SESSION_FILE>` reported, naming the target repository

</success_criteria>
