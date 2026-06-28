---
name: interview
description: >-
  ALWAYS invoke before requirements interviews, draft approval, or unresolved
  scope/design questions while creating or modifying an artifact (spec, ADR,
  PDR, test, code, doc). NEVER invoke solely because a workflow uses AskUserQuestion for an operational choice.
argument-hint: <file-path-or-requirement>
---

<objective>
A decision-ready requirements packet for the calling workflow: resolved choices, remaining open decisions, coverage state, and artifact constraints.

</objective>

<essential_principles>

**Pre-Analysis Protocol**

Before asking ANY questions:

1. Research the codebase — existing patterns, conventions, tech stack
2. Read product docs — README, CLAUDE.md, existing specs
3. Analyze the input — what's defined, ambiguous, missing
4. Form preliminary opinions (e.g., "this approach seems fragile", "auth model is underspecified")

Perform this research in the main conversation unless the active repository and runtime instructions explicitly authorize a bounded research subagent for interview pre-analysis. When that authorization exists, use only the authorized subagent shape for bounded read-only research. Read named files, skill files, skill references, the repository's CLAUDE.md instruction file, and user-provided files in the main conversation. Summarize findings as a structured brief and share it with the user before the first question.

**Structure caveat — existing code informs content, not structure.** Pre-analysis reveals what the code *is* and how it is *filed* — packages, modules, directories, files. That is the implementation: the lowest layer. It informs vocabulary, constraints, and open decisions. It must never become the structure of the artifact about to be created. Do not let the code's module or file layout dictate spec-tree node boundaries or document sections. Separate "how the code is organized" from "what the product does for its consumers" — only the latter drives structure.

When modifying an existing document, read it first. The coverage map starts from the document's existing sections — the interview focuses on deltas, not re-covering settled content.

**Decide-First Protocol**

A question is the last resort, not the first move. Before composing any question:

- **Reason to a recommendation.** Work the decision through to the answer the code, the specs, the decisions, and sensible defaults point to. Carry that reasoning into the question — never ask a question without first trying to answer it.
- **Ask only what is genuinely the operator's to decide.** A question is warranted only when the decision is the operator's and the evidence does not settle it — a product bet, a priority call, a preference with real trade-offs. When the code, specs, decisions, or a sensible default already settle it, decide and proceed; do not stage a question to ratify a call already made.
- **No genuine fork → no question.** If reasoning leaves one defensible answer, take it and state the call. A question with only one real answer wastes a turn and pushes back onto the operator a decision the evidence already made.

When a question is warranted, its options obey:

- **Materially distinct end-states.** Every option is a different outcome a reasonable operator might choose — never one real option padded with a strawman, and never one judgment split into a false 50/50.
- **Recommendation first.** State the recommended option first and label it as recommended; the description gives the trade-off that earns the recommendation. Hiding the recommendation to look neutral hands the operator a decision the evidence was enough to make.

**Questioning Protocol**

- **One question at a time** — never batch. Go deep before moving on.
- **Inside an active interview, use AskUserQuestion** — structured choices (2-4 options per question), never open-ended. A workflow's use of AskUserQuestion for an operational choice does not by itself make the prompt an interview.
- **No obvious questions** — never ask what can be inferred from input or codebase analysis
- **Options must require judgment** — no "yes/no", no obviously-correct choices
- **Describe trade-offs** — each option's description explains consequences, not just what it is
- **Think before asking** — spend a turn reasoning about what the interview has surfaced so far, what's still ambiguous, and what question would resolve the most uncertainty

**Coverage Protocol**

Maintain an evolving coverage map. Display it before each question:

```text
Coverage: Problem [done] | Users [done] | API Design [current] | Data Model [pending] | Security [pending]
```

Coverage areas are dynamic:

- **Generic defaults**: Problem, Users, Technical Approach, Risks, Constraints
- **Calling skill overrides**: When a calling skill provides domain-specific areas, use those instead
- **Refine as the interview proceeds**: Split broad areas (e.g., "Technical Approach" into "API Design" + "Data Model")
- **Add discovered areas**: New concerns that emerge during conversation
- **Mark [done]**: When an area is sufficiently explored

**Pushback Protocol**

When any of these appear:

- **Contradictions** with previous answers — challenge directly, cite the specific prior answer
- **Over-engineering** for the scope — call it out, propose a simpler alternative
- **Missing edge cases** — probe with concrete scenarios ("what happens when X?")
- **Security/privacy risks** — HARD BLOCK. Refuse to proceed until the user acknowledges and addresses each concern.

Disagreement escalation: if the user disagrees with pushback:

1. Ask 1-2 targeted follow-up questions to stress-test the decision
2. Then accept and record BOTH perspectives in the decisions log

**Completion Protocol**

Coverage-based completion — never end by question count or elapsed time:

- When all areas are [done], propose: "I think we've covered [list]. Ready to write?"
- The user can push further or accept
- If an area still has gaps, keep probing — don't round up

**Auto-split detection**: if coverage grows beyond ~8 major areas, propose splitting into separate documents with a dependency order.

**State Persistence Protocol**

Write interview state to `.<name>.interview-state.json`:

- All Q&A pairs and coverage map state
- Timestamp and codebase analysis summary
- Output status and any generated document path

Resume: if state file exists, re-validate against current codebase state, flag stale answers, continue from where the interview left off.

</essential_principles>

<intake>

**When loaded by another skill**: Skip. The calling skill specifies coverage areas and domain context. Apply `<essential_principles>` directly.

**When invoked directly** (`/interview`):

If user provided input with `/interview <input>`:

1. Analyze the input
2. Infer what the user needs from the input and current state:
   - Existing artifact provided → read it first, derive coverage from its sections, focus on gaps and deltas
   - Decision framing ("should we X or Y") → coverage centers on options, criteria, trade-offs
   - Problem framing ("why does X", "X is broken") → coverage builds a causal chain from symptoms to root cause
   - New idea with no artifact → generic coverage defaults (Problem, Users, Approach, Risks, Constraints)
3. If the input maps to an existing spec-tree skill (`/bootstrap`, `/author`, `/decompose`, `/align`), suggest that skill instead — it will load `/interview` for methodology and bring its own domain knowledge

If no input: ask "What would you like to interview about?"

**Resume**: If `.interview-state.json` exists near the referenced path, offer to resume.

</intake>

<routing>

| Response                                    | Action                                                   |
| ------------------------------------------- | -------------------------------------------------------- |
| File path or requirement text               | Read `${CLAUDE_SKILL_DIR}/workflows/direct-interview.md` |
| "resume" or references a previous interview | Check for `.interview-state.json`, resume if found       |
| Input maps to a spec-tree skill             | Suggest that skill instead                               |

</routing>

<workflows_index>
All in `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow            | Purpose                                                              |
| ------------------- | -------------------------------------------------------------------- |
| direct-interview.md | Generic interview for direct invocation (no domain-specific context) |

</workflows_index>

<failure_modes>

**Failure 1: Question spiral without coverage progress**

Claude asks 15+ questions all drilling into one area (e.g., "API Design") while ignoring other pending areas on the coverage map. The interview grows without making the coverage map advance. User gets frustrated; context window fills with narrow detail.

How to avoid: Before each question, check the coverage map. If an area is at 3+ consecutive questions and still not marked [done], ask whether the question probes a real gap or just explores. Move to the next pending area when the current one has enough signal to draft the spec section — depth is for unclear cases, not comprehensive documentation.

**Failure 2: Accepting vague answers without pushback**

User responds with "we'll figure it out later" or "just make it work for the common case." Claude records the non-answer and moves on. The resulting spec has holes that surface during implementation.

How to avoid: "We'll figure it out later" is pushback bait. Ask a concrete follow-up: "What's the common case? Describe one user who hits this." Force specificity. If the user genuinely doesn't know, record it as an open decision with a `([audit])` tag, not as a resolved assertion.

**Failure 3: Losing coverage state in long conversations**

After 30+ turns, Claude loses track of which areas are [done] vs [pending]. Coverage map stops being displayed. Questions start repeating or missing obvious areas. Context compression eats the early interview.

How to avoid: Display the coverage map before EVERY question, not just the first one. The display is a forcing function — writing it out pulls the state back into active context. A turn that skips the display is the signal to stop and re-read the previous turns.

**Failure 4: Generated spec doesn't trace back to interview**

Spec is written from Claude's synthesis, not from the recorded Q&A. Assertions appear that were never discussed. The decisions log is empty or missing. User reviews the spec and asks "where did this come from?" — agent can't answer.

How to avoid: Every section of the generated spec must trace to a specific coverage area explored in the interview. Every assertion must map to something the user said. The decisions log is NOT optional — if there was any pushback, disagreement, or trade-off, it belongs in the log with the user's final answer.

**Failure 5: Skipping pre-analysis to get to questions faster**

Claude invokes `/interview`, reads the intake question, and immediately starts asking the user things. No codebase scan, no doc reading, no analysis brief. Every question the user answers could have been inferred from the codebase. User gets annoyed that Claude didn't do its homework.

How to avoid: Pre-Analysis Protocol is non-negotiable. Complete the codebase, docs, and input research before the first question. Use an Explore agent only when the active repository and runtime instructions explicitly authorize that bounded research subagent; otherwise perform the same read-only research in the main conversation. Share the brief. The user should never have to supply something that exists in the codebase or docs.

**Failure 6: Asking a question the evidence already settled**

Claude framed a question — "should the parser tolerate trailing commas?" — whose answer the loaded spec and the existing parser already fixed. The operator answered the obvious, and the turn produced nothing the code did not already say. A variant: Claude reasoned to a clear recommendation, then asked anyway "to confirm", staging a decision it had already made.

How to avoid: Decide-First Protocol. Reason the decision through first. Ask only when the answer is genuinely the operator's and the evidence does not settle it. When one defensible answer remains, take it and state the call — do not ask to ratify it.

**Failure 7: Strawman options and false balance**

Claude offered "use the existing validation harness" against "hand-roll a bespoke validator from scratch" — the second option a strawman no one would pick, dressed up to make the question look like a real choice. Or it split a single judgment into a fabricated 50/50 to appear neutral, when one option was plainly correct.

How to avoid: every option is a materially distinct end-state a reasonable operator might actually choose. If only one option survives scrutiny, there is no question — decide and proceed. When a question is real, state the recommended option first and label it recommended; do not manufacture a counterweight to look balanced.

**Failure 8: Treating every structured workflow prompt as an interview**

Claude saw a workflow use AskUserQuestion for an operational choice and invoked `/interview`, turning a local workflow decision into requirements gathering.

Why it failed: `/interview` governs requirements, scope, design, and draft-approval questions for artifacts. Structured tool choice alone is not a routing trigger.

How to avoid: Invoke `/interview` only when the unresolved decision concerns artifact requirements, scope, design, or draft approval. For mechanical workflow choices, follow the governing workflow and use AskUserQuestion directly when that workflow requires it.

</failure_modes>

<success_criteria>
A decision-ready requirements packet is sound when:

- Every resolved choice names the evidence that settled it or the operator answer that decided it.
- Every remaining open decision names the missing evidence or operator judgment still required.
- The coverage map marks each area `[done]`, `[current]`, or `[pending]`, with no generated artifact section relying on a pending area as if it were resolved.
- The decisions log records each pushback, disagreement, trade-off, and final disposition.
- Every generated artifact section traces to a coverage area and, where applicable, to a specific Q&A entry or pre-analysis finding.
- Artifact constraints name the output format, output location, and any task-breakdown format selected for follow-on work.

</success_criteria>
