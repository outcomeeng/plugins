---
name: manage-parent-issue
description: >-
  ALWAYS invoke this skill when continuing an open issue in a repository the operator does not control — answering a maintainer, adding evidence, or reporting the thread's current state.
  NEVER comment on or close an issue in such a repository without this skill.
argument-hint: "[issue number or URL]"
allowed-tools: Read, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_target.py":*), Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api user:*), Bash(printf:*)
---

<objective>
The maintainer's question answered with evidence, and one comment posted to the open issue.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the issue.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is an issue number or URL. A bare number is the number; a URL's trailing path segment is the number. An empty `$ARGUMENTS` stops the flow, because this skill continues an identified thread and never picks one. The URL check needs the resolved base, so Step 2 settles it.

**Step 2 — Resolve the target, then check the number.** Run the resolver named in `/contribution-standards` `<resolution>`. `parent-contribution` and `fork-absent` both continue — a thread needs no head repository. `controlled` and `blocked` stop, reporting the classification and `detail` verbatim.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/resolve_target.py"
```

With `base` resolved, a URL's `owner/name` segments must equal it; a mismatch stops the flow rather than being reconciled.

**Step 3 — Read the thread once.**

```bash
gh issue view "<number>" --repo "<base>" --json state,title,body,comments,labels,author,url
```

Read it one time and report `state` and the last maintainer comment verbatim. `/contribution-standards` forbids polling, watching, and sleeping on the artifact; a maintainer answers on their own schedule.

**STOP when `state` is `CLOSED`.** Report that outcome and return. This gate precedes every later step: a comment posted afterwards notifies every watcher of a thread whose decision is already made, and Step 7 has nothing left to close.

**Step 4 — Answer what was asked.** Identify the maintainer's actual question. Gather the evidence it needs before drafting anything, under `/contribution-standards` `<invariants>` "Carry reproducible evidence" — versions, the base commit observed against, the exact command, and a negative control where the answer makes a defect claim.

When the answer requires a condition that cannot be reproduced in the real surface, say the claim is unverified and say why. A synthesized approximation reported as an observation is worse than no answer, because the maintainer cannot tell which they received.

**Step 5 — GATE: Establish whose thread this is, before writing to it.** Read the authenticated login, which is the only side of this comparison Step 3 does not already supply:

```bash
gh api user --jq '.login'
```

Compare it against `author.login` from the Step 3 read; that field is the only evidence of who filed the issue.

An issue the operator filed is the artifact they already authorized, and a reply continues it. An issue anyone else filed is an unrelated thread: `/contribution-standards` `<invariants>` "Authorization covers the artifact and its revisions" gives a comment there its own in-turn authorization, so present through the runtime's structured-question tool the resolved `base`, the issue number and title, and the choice to reply there or to stop. Post nothing until the operator authorizes it in this turn.

This gate precedes Step 6's write. A comment notifies every watcher of a repository the operator does not control, and that cannot be taken back by deciding afterwards that the thread was someone else's.

**Step 6 — GATE: Review the reply, then post it.** Draft per `<reply_shape>` and review — the prose plugin's `prose-auditor` agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such.

```bash
printf '%s\n' '<line>' '<line>' | gh issue comment "<number>" --repo "<base>" --body-file -
```

**Step 7 — GATE: Close only what the operator opened, and only when authorized.** Step 5 already established the author. An issue anyone else filed is the maintainer's to close; stop there. For an issue the operator filed, closing is a new outward action rather than a revision of the authorized one, so present through the runtime's structured-question tool the resolved `base`, the issue number and title, and the choice to close it or leave it open. Close only after the operator authorizes it in this turn:

```bash
gh issue close "<number>" --repo "<base>"
```

**Step 8 — Return.** Report the issue URL, the state read in Step 3, and what was answered. Do not wait for a response.

</workflow>

<reply_shape>

- Open by answering the question that was asked, before anything else.
- Quote the evidence rather than describing it.
- Mark inference as inference and an unreproduced condition as unverified.
- Cut every sentence about the reply's own process.
- Add a new observation only when it bears on the question; otherwise it belongs in its own issue through `/open-parent-issue`.

</reply_shape>

<constraints>

- MUST read the thread exactly once per invocation and return without waiting.
- MUST name the base repository with `--repo` on every `gh` write.
- MUST answer the maintainer's question before adding anything else.
- MUST establish the issue's author before the first write, and obtain authorization in the same turn before commenting on a thread the operator did not open.
- MUST obtain authorization in the same turn before closing an issue.
- MUST read `gh api user` only for the Step 5 authorship comparison. `/contribution-standards` `<invariants>` "Establish permission from the API" rules the authenticated account out as evidence of permission on the base; it is evidence of identity and nothing else.
- NEVER write through `gh api user`. The `Bash(gh api user:*)` grant matches by prefix, so it admits `-X PATCH` and `-X DELETE` against the operator's own GitHub account; this constraint is the whole containment for those verbs. Read only.
- NEVER pass `--edit-last` or `--delete-last` to `gh issue comment`. The `Bash(gh issue comment:*)` grant matches by prefix and admits both, and either one rewrites or removes a comment a maintainer may already have read. `/contribution-standards` `<invariants>` "Iterate by appending" is the rule; this constraint is its containment here.
- NEVER close, label, or reassign an issue the operator did not open.
- NEVER present a synthesized approximation of the condition as an observation.

</constraints>

<failure_modes>

**A reply was posted before the thread's owner was known.** Claude read the issue, drafted an answer, and commented — then compared the author against the authenticated account, which is where the authorization gate sat. On a thread the operator had not opened, the comment had already notified every watcher of a repository the operator does not control, and GitHub keeps that notification whatever happens to the comment. Establish the author in Step 5, before any write.

</failure_modes>

<success_criteria>

- The resolver returned `parent-contribution` or `fork-absent` before any write.
- The thread was read once, and `state` plus the last maintainer comment appear verbatim.
- The issue's `author.login` was compared against the authenticated login before the comment was posted, and a thread the operator did not open was authorized in that turn.
- The reply's opening sentence answers the question Step 4 identified, and every claim after it is followed by quoted evidence rather than a description of that evidence.
- Inference is marked as inference; an unreproduced condition is marked unverified.
- The reply passed a prose review, reported as unassisted where the prose plugin is absent.
- Any close was authorized in the same turn and applied only to an issue whose `author.login` equals the login `gh api user` reported.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
