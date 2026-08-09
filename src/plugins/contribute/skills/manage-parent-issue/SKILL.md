---
name: manage-parent-issue
description: >-
  ALWAYS invoke this skill when continuing an open issue in a repository the operator does not control — answering a maintainer, adding evidence, or reporting the thread's current state.
argument-hint: "[issue number or URL]"
allowed-tools: Read, Glob, Grep, Skill,{!% if target == 'claude' %!} Agent,{!% else %!} {{! tool('spawn_agent') !}}, {{! tool('wait_agent') !}}, {{! tool('close_agent') !}},{!% endif %!} Bash(python3 "${CLAUDE_SKILL_DIR}/../contribution-standards/scripts/resolve_target.py":*), Bash(gh issue view:*), Bash(gh issue list:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh api:*), Bash(git rev-parse:*), Bash(git log:*), Bash(printf:*)
---

<objective>
The open issue's current thread read once, the maintainer's question answered with evidence, and one comment posted.
</objective>

<workflow>

**Step 1 — Load the standards.** Invoke `/contribution-standards` through the runtime's skill-composition surface.

**Step 2 — Resolve the target.** Run the resolver named in `/contribution-standards` `<resolution>`. `parent-contribution` and `fork-absent` both continue — a thread needs no head repository. `controlled` and `blocked` stop, reporting the classification and `detail` verbatim.

**Step 3 — Read the thread once.**

```bash
gh issue view "$number" --repo "$base" --json state,title,body,comments,labels,url
```

Read it one time and report `state` and the last maintainer comment verbatim. `/contribution-standards` forbids polling, watching, and sleeping on the artifact; a maintainer answers on their own schedule.

**Step 4 — Answer what was asked.** Identify the maintainer's actual question. Gather the evidence it needs before drafting anything, under `/contribution-standards` `<invariants>` "Carry reproducible evidence" — versions, the base commit observed against, the exact command, and a negative control where the answer makes a defect claim.

When the answer requires a condition that cannot be reproduced in the real surface, say the claim is unverified and say why. A synthesized approximation reported as an observation is worse than no answer, because the maintainer cannot tell which they received.

**Step 5 — GATE: Review the reply, then post it.** Draft per `<reply_shape>` and review — the prose plugin's `prose-auditor` agent where installed, `/contribution-standards` `<outward_text>` unassisted where not, stated as such.

```bash
printf '%s\n' '<line>' '<line>' | gh issue comment "$number" --repo "$base" --body-file -
```

**Step 6 — Close only what the operator opened.** An issue the operator filed may be closed once resolved, and closing it is a new outward action requiring authorization in that turn. An issue anyone else filed is the maintainer's to close.

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
