---
name: manage-upstream-issue
description: >-
  ALWAYS invoke this skill when continuing an open issue in a repository the operator does not control — answering a maintainer, adding evidence, or reporting the thread's current state.
  NEVER comment on or close an issue in such a repository without this skill.
argument-hint: "[issue number or URL]"
allowed-tools: Read, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} {{! tool('ask_user') !}}, Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api user:*), Bash(printf:*)
---

<objective>
The maintainer's question answered with evidence in one comment on the open issue, or that thread's state reported when it asked nothing.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the issue.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is an issue number or URL. A bare number is the number; a URL's trailing path segment is the number. An empty `$ARGUMENTS` stops the flow, because this skill continues an identified thread and never picks one. The URL check needs the resolved base, so Step 2 settles it.

**Step 2 — Establish the target, then check the number.** Read the live `<UPSTREAM_TARGET>` marker; invoke `/upstream` when none is live. `upstream-contribution`, `head-ambiguous`, and `fork-absent` all continue — a thread needs no head repository. `controlled` and `blocked` stop, reporting the classification and `detail` verbatim.

With `base` resolved, a URL's `owner/name` segments must equal it; a mismatch stops the flow rather than being reconciled.

**Step 3 — Read the thread once.**

```bash
gh issue view "<number>" --repo "<base>" --json state,title,body,comments,labels,author,url
```

Read it one time and report `state` and the last maintainer comment verbatim. `/contribution-standards` forbids polling, watching, and sleeping on the artifact; a maintainer answers on their own schedule.

**STOP when `state` is `CLOSED`.** Report that outcome and return. This gate precedes every later step: a comment posted afterwards notifies every watcher of a thread whose decision is already made, and Step 7 has nothing left to close.

**Step 4 — Answer what was asked.** Identify the maintainer's actual question. Gather the evidence it needs before drafting anything, under `/contribution-standards` `<invariants>` "Carry reproducible evidence" — versions, the base commit observed against, the exact command, and a negative control where the answer makes a defect claim. Those probes belong to the subject tool rather than to this skill, so they run per `/contribution-standards` `<capability_scope>`.

When the answer requires a condition that cannot be reproduced in the real surface, say the claim is unverified and say why. A synthesized approximation reported as an observation is worse than no answer, because the maintainer cannot tell which they received.

**Step 5 — GATE: Establish whose thread this is, before writing to it.** Read the authenticated login, which is the only side of this comparison Step 3 does not already supply:

```bash
gh api user --jq '.login'
```

Compare it against `author.login` from the Step 3 read; that field is the only evidence of who filed the issue.

An issue the operator filed is the artifact they already authorized, and a reply continues it. An issue anyone else filed is an unrelated thread: `/contribution-standards` `<invariants>` "Authorization covers the artifact and its revisions" gives a comment there its own in-turn authorization, so present through the runtime's structured-question tool the resolved `base`, the issue number and title, and the choice to reply there or to stop. Post nothing until the operator authorizes it in this turn.

This gate precedes Step 6's write. A comment notifies every watcher of a repository the operator does not control, and that cannot be taken back by deciding afterwards that the thread was someone else's.

**Step 6 — GATE: Review the reply, then post it.** A reply is posted only when the thread asked for one. An invocation that reports the thread's current state, and a thread where the maintainer has asked nothing since the last reply, both skip this step and continue to Step 7: a comment that answers no question is a notification the maintainer did not ask for, on a repository the operator does not control. Step 7 still runs, because closing depends on Step 5's author comparison and never on a comment having been posted — a thread that asks nothing is exactly the thread an operator may want closed.

With a question to answer, draft per `<reply_shape>` and review — the prose plugin's `prose-auditor` thin agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such.

```bash
printf '%s\n' '<line>' '<line>' | gh issue comment "<number>" --repo "<base>" --body-file -
```

**Step 7 — GATE: Close only what the operator opened, and only when authorized.** Step 5 already established the author. An issue anyone else filed is the maintainer's to close; stop there. For an issue the operator filed, closing is a new outward action rather than a revision of the authorized one, so present through the runtime's structured-question tool the resolved `base`, the issue number and title, and the choice to close it or leave it open. Close only after the operator authorizes it in this turn:

```bash
gh issue close "<number>" --repo "<base>"
```

**Step 8 — Return.** Report the issue URL, the state read in Step 3, and what was answered — or that the thread asked nothing this pass. Do not wait for a response.

</workflow>

<reply_shape>

- Open by answering the question that was asked, before anything else.
- Quote the evidence rather than describing it.
- Mark inference as inference and an unreproduced condition as unverified.
- Cut every sentence about the reply's own process.
- Add a new observation only when it bears on the question; otherwise it belongs in its own issue through `/open-upstream-issue`.

</reply_shape>

<worked_example>

One reply on a fictional `acme/parser` issue reporting that `--strict` is ignored when the config file sets `strict: false`, to compare a draft against.

The maintainer's comment, which is the question Step 4 identifies:

```text
Does this reproduce without a config file present?
```

The reply:

```text
No — with no config file the flag takes effect.

$ rm parser.yml
$ parser --strict sample.txt; echo "exit $?"
sample.txt:1:5: unexpected '='
exit 1

parser 4.2.0, acme/parser at 4f9c2a1, the same sample.txt as the report.

That reads as the file's value overriding the flag rather than the reverse —
an inference from these two runs, not something I confirmed in the source.
```

The first sentence answers the question asked, before anything else. The command output stands quoted rather than summarized as "it worked". The precedence claim carries its own inference marker, because the run compared two exit codes and never read the merge. The reply thanks nobody, describes none of its own process, and proposes no fix.

</worked_example>

<constraints>

- MUST read the thread exactly once per invocation and return without waiting.
- NEVER comment on or close an issue whose `state` is `CLOSED`. Report that outcome and return; the decision is already made, and a comment notifies every watcher of it.
- MUST name the base repository with `--repo` on every `gh` write.
- MUST answer the maintainer's question before adding anything else.
- NEVER post a comment when the thread asked nothing — a state-only invocation returns what it read and writes nothing.
- MUST establish the issue's author before the first write, and obtain authorization in the same turn before commenting on a thread the operator did not open.
- MUST obtain authorization in the same turn before closing an issue.
- MUST read `gh api user` only for the Step 5 authorship comparison. `/contribution-standards` `<invariants>` "Establish permission from the API" rules the authenticated account out as evidence of permission on the base; it is evidence of identity and nothing else.
- NEVER pass an `-X` method flag to `gh api user`. The `Bash(gh api user:*)` grant matches by prefix, so it admits every verb against the operator's own GitHub account — `-X PATCH` and `-X DELETE` among them; this constraint is the whole containment for all of them. Read only.
- NEVER pass `--edit-last` or `--delete-last` to `gh issue comment`. The `Bash(gh issue comment:*)` grant matches by prefix and admits both, and either one rewrites or removes a comment a maintainer may already have read. `/contribution-standards` `<invariants>` "Iterate by appending" is the rule; this constraint is its containment here.
- NEVER close, label, or reassign an issue the operator did not open.
- NEVER present a synthesized approximation of the condition as an observation.

</constraints>

<failure_modes>

**A reply was posted before the thread's owner was known.** Claude read the issue, drafted an answer, and commented — then compared the author against the authenticated account, which is where the authorization gate sat. On a thread the operator had not opened, the comment had already notified every watcher of a repository the operator does not control, and GitHub keeps that notification whatever happens to the comment. Establish the author in Step 5, before any write.

</failure_modes>

<success_criteria>

- The `<UPSTREAM_TARGET>` marker read for this pass carries `classification="upstream-contribution"`, `"head-ambiguous"`, or `"fork-absent"`, established before any write.
- The thread was read once, and `state` plus the last maintainer comment appear verbatim.
- A `state` of `CLOSED` returned that outcome and wrote nothing; every criterion below covers a pass on an open thread.
- The issue's `author.login` was compared against the authenticated login before the comment was posted, and a thread the operator did not open was authorized in that turn.
- Where the thread asked a question, the reply's opening sentence answers the one Step 4 identified and every claim after it is followed by quoted evidence rather than a description of that evidence; where it asked none, no comment was posted.
- Inference is marked as inference; an unreproduced condition is marked unverified.
- The reply passed a prose review, reported as unassisted where the prose plugin is absent.
- Any close was authorized in the same turn and applied only to an issue whose `author.login` equals the login `gh api user` reported.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
