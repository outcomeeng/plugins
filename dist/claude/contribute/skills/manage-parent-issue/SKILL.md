---
name: manage-parent-issue
description: >-
  ALWAYS invoke this skill when continuing an open issue in a repository the operator does not control — answering a maintainer, adding evidence, or reporting the thread's current state.
argument-hint: "[issue number or URL]"
allowed-tools: Read, Glob, Grep, Skill, Agent, AskUserQuestion, Bash(python3 "${CLAUDE_SKILL_DIR}/../contribution-standards/scripts/resolve_target.py":*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(git rev-parse:*), Bash(git log:*), Bash(printf:*)
---

<objective>
The open issue's current thread read once, the maintainer's question answered with evidence, and one comment posted.
</objective>

<workflow>

**Step 1 — Load the standards and resolve the issue.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

`$ARGUMENTS` is an issue number or URL. A bare number is the number; a URL's trailing path segment is the number. An empty `$ARGUMENTS` stops the flow, because this skill continues an identified thread and never picks one. The URL check needs the resolved base, so Step 2 settles it.

**Step 2 — Resolve the target, then check the number.** Run the resolver named in `/contribution-standards` `<resolution>`. `parent-contribution` and `fork-absent` both continue — a thread needs no head repository. `controlled` and `blocked` stop, reporting the classification and `detail` verbatim.

With `base` resolved, a URL's `owner/name` segments must equal it; a mismatch stops the flow rather than being reconciled.

**Step 3 — Read the thread once.**

```bash
gh issue view "<number>" --repo "<base>" --json state,title,body,comments,labels,url
```

Read it one time and report `state` and the last maintainer comment verbatim. `/contribution-standards` forbids polling, watching, and sleeping on the artifact; a maintainer answers on their own schedule.

**Step 4 — Answer what was asked.** Identify the maintainer's actual question. Gather the evidence it needs before drafting anything, under `/contribution-standards` `<invariants>` "Carry reproducible evidence" — versions, the base commit observed against, the exact command, and a negative control where the answer makes a defect claim.

When the answer requires a condition that cannot be reproduced in the real surface, say the claim is unverified and say why. A synthesized approximation reported as an observation is worse than no answer, because the maintainer cannot tell which they received.

**Step 5 — GATE: Review the reply, then post it.** Draft per `<reply_shape>` and review — the prose plugin's `prose-auditor` agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such.

```bash
printf '%s\n' '<line>' '<line>' | gh issue comment "<number>" --repo "<base>" --body-file -
```

**Step 6 — GATE: Close only what the operator opened, and only when authorized.** An issue anyone else filed is the maintainer's to close; stop there. For an issue the operator filed, closing is a new outward action, not a revision of the authorized one, so present through the runtime's structured-question tool the resolved `base`, the issue number and title, and the choice to close it or leave it open. Close only after the operator authorizes it in this turn:

```bash
gh issue close "<number>" --repo "<base>"
```

**Step 7 — Return.** Report the issue URL, the state read in Step 3, and what was answered. Do not wait for a response.

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
- MUST obtain authorization in the same turn before closing an issue.
- NEVER close, label, or reassign an issue the operator did not open.
- NEVER present a synthesized approximation of the condition as an observation.

</constraints>

<success_criteria>

- The resolver returned `parent-contribution` or `fork-absent` before any write.
- The thread was read once, and `state` plus the last maintainer comment appear verbatim.
- The reply answers the question that was asked, with quoted evidence.
- Inference is marked as inference; an unreproduced condition is marked unverified.
- The reply passed a prose review, reported as unassisted where the prose plugin is absent.
- Any close was authorized in the same turn and applied only to an issue the operator opened.
- The pass returned without polling, watching, or sleeping.

</success_criteria>
