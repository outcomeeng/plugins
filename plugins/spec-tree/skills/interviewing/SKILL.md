---
name: interviewing
description: >-
  ALWAYS invoke BEFORE asking the user anything while creating or modifying any
  artifact (spec, ADR, PDR, test, code, doc). Triggers: AskUserQuestion,
  seeking draft approval, stuck on scope or design. NEVER ask without this
  skill.
argument-hint: <file-path-or-requirement>
---

<objective>
Domain-agnostic interview methodology for structured requirements gathering. Provides the HOW of interviewing — questioning technique, coverage tracking, pushback protocol, progress display, and preview rendering. Domain knowledge (WHAT to ask about) comes from the calling skill or the user.

Works two ways without duplication:

- **Direct invocation** (`/interviewing`): Asks what to interview about, then conducts a methodology-driven interview
- **Referenced by other skills**: Calling skill reads `/interviewing` for the methodology, then applies it with its own domain-specific coverage areas and templates

</objective>

<essential_principles>

**Pre-Analysis Protocol**

Before asking ANY questions:

1. Research the codebase — existing patterns, conventions, tech stack
2. Read project docs — README, CLAUDE.md, existing specs
3. Analyze the input — what's defined, ambiguous, missing
4. Form preliminary opinions (e.g., "this approach seems fragile", "auth model is underspecified")

Use an Explore agent for codebase research. Summarize findings as a structured brief and share it with the user before the first question.

When modifying an existing document, read it first. The coverage map starts from the document's existing sections — the interview focuses on deltas, not re-covering settled content.

**Questioning Protocol**

- **One question at a time** — never batch. Go deep before moving on.
- **Always use AskUserQuestion** — structured choices (2-4 options per question), never open-ended
- **No obvious questions** — never ask what can be inferred from input or codebase analysis
- **Options must require judgment** — no "yes/no", no obviously-correct choices
- **Describe trade-offs** — each option's description explains consequences, not just what it is
- **Think before asking** — spend a turn reasoning about what you've learned so far, what's still ambiguous, and what question would resolve the most uncertainty

**Coverage Protocol**

Maintain an evolving coverage map. Display it before each question:

```text
Coverage: Problem [done] | Users [done] | API Design [current] | Data Model [pending] | Security [pending]
```

Coverage areas are dynamic:

- **Generic defaults**: Problem, Users, Technical Approach, Risks, Constraints
- **Calling skill overrides**: When a calling skill provides domain-specific areas, use those instead
- **Refine as you go**: Split broad areas (e.g., "Technical Approach" into "API Design" + "Data Model")
- **Add discovered areas**: New concerns that emerge during conversation
- **Mark [done]**: When an area is sufficiently explored

**Pushback Protocol**

When you detect:

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

**Preview Protocol**

After the interview completes, offer an interactive HTML preview for visual review:

1. Read `${CLAUDE_SKILL_DIR}/references/preview-template.md` for the complete HTML template
2. Map each coverage area to a styled section card
3. Every block-level content element gets `class="commentable"` with a unique `data-id="{sectionIndex}-{elementIndex}"`
4. Render any decisions log as a collapsible table (collapsed by default)
5. Write to `<output-dir>/.preview-<name>.html` and open in browser

Tell the user:

- **Click any paragraph, bullet, or table row** to add an inline comment
- **Click "Revise"** when done — comments auto-copied to clipboard
- **Paste feedback** back into Claude Code for revision
- **Click "Approved"** when satisfied — generates the final document

Revision loop: parse feedback, clarify ambiguous comments with AskUserQuestion, regenerate, repeat until approved.

**State Persistence Protocol**

Write interview state to `.<name>.interview-state.json`:

- All Q&A pairs and coverage map state
- Timestamp and codebase analysis summary
- Preview status (generated? feedback rounds?)

Resume: if state file exists, re-validate against current codebase state, flag stale answers, continue from where the interview left off.

</essential_principles>

<intake>

**When loaded by another skill**: Skip. The calling skill specifies coverage areas and domain context. Apply `<essential_principles>` directly.

**When invoked directly** (`/interviewing`):

If user provided input with `/interviewing <input>`:

1. Analyze the input
2. Infer what the user needs from the input and current state:
   - Existing artifact provided → read it first, derive coverage from its sections, focus on gaps and deltas
   - Decision framing ("should we X or Y") → coverage centers on options, criteria, trade-offs
   - Problem framing ("why does X", "X is broken") → coverage builds a causal chain from symptoms to root cause
   - New idea with no artifact → generic coverage defaults (Problem, Users, Approach, Risks, Constraints)
3. If the input maps to an existing spec-tree skill (`/bootstrapping`, `/authoring`, `/decomposing`, `/aligning`), suggest that skill instead — it will load `/interviewing` for methodology and bring its own domain knowledge

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

<reference_index>
All in `${CLAUDE_SKILL_DIR}/references/`:

| File                | Purpose                                                                       |
| ------------------- | ----------------------------------------------------------------------------- |
| preview-template.md | Complete HTML/CSS/JS template for interactive previews with inline commenting |

</reference_index>

<workflows_index>
All in `${CLAUDE_SKILL_DIR}/workflows/`:

| Workflow            | Purpose                                                              |
| ------------------- | -------------------------------------------------------------------- |
| direct-interview.md | Generic interview for direct invocation (no domain-specific context) |

</workflows_index>

<failure_modes>

**Failure 1: Question spiral without coverage progress**

Claude asks 15+ questions all drilling into one area (e.g., "API Design") while ignoring other pending areas on the coverage map. The interview grows without making the coverage map advance. User gets frustrated; context window fills with narrow detail.

How to avoid: Before each question, check the coverage map. If an area is at 3+ consecutive questions and still not marked [done], ask yourself whether you're probing a real gap or just exploring. Move to the next pending area when the current one has enough signal to draft the spec section — depth is for unclear cases, not comprehensive documentation.

**Failure 2: Accepting vague answers without pushback**

User responds with "we'll figure it out later" or "just make it work for the common case." Claude records the non-answer and moves on. The resulting spec has holes that surface during implementation.

How to avoid: "We'll figure it out later" is pushback bait. Ask a concrete follow-up: "What's the common case? Describe one user who hits this." Force specificity. If the user genuinely doesn't know, record it as an open decision with a `([review])` tag, not as a resolved assertion.

**Failure 3: Losing coverage state in long conversations**

After 30+ turns, Claude loses track of which areas are [done] vs [pending]. Coverage map stops being displayed. Questions start repeating or missing obvious areas. Context compression eats the early interview.

How to avoid: Display the coverage map before EVERY question, not just the first one. The display is a forcing function — writing it out pulls the state back into active context. If you catch yourself not displaying it, that's the signal to stop and re-read your own previous turns.

**Failure 4: Generated spec doesn't trace back to interview**

Spec is written from Claude's synthesis, not from the recorded Q&A. Assertions appear that were never discussed. The decisions log is empty or missing. User reviews the spec and asks "where did this come from?" — agent can't answer.

How to avoid: Every section of the generated spec must trace to a specific coverage area explored in the interview. Every assertion must map to something the user said. The decisions log is NOT optional — if there was any pushback, disagreement, or trade-off, it belongs in the log with the user's final answer.

**Failure 5: Skipping pre-analysis to get to questions faster**

Claude invokes `/interviewing`, reads the intake question, and immediately starts asking the user things. No codebase scan, no doc reading, no analysis brief. Every question the user answers could have been inferred from the codebase. User gets annoyed that Claude didn't do its homework.

How to avoid: Pre-Analysis Protocol is non-negotiable. Launch the Explore agent before the first question. Share the brief. The user should never have to tell you something that exists in the codebase or docs.

</failure_modes>

<success_criteria>
A well-conducted interview:

- Pre-analysis completed before first question
- Every question used AskUserQuestion with 2-4 non-obvious options
- Coverage map displayed and updated before each question
- Pushback applied when contradictions or risks detected
- Decisions log captures every pushback and its resolution
- All coverage areas marked [done] before proposing completion
- Preview offered and revision loop completed (if opted in)
- Output document captures all findings with traceability to interview Q&A

</success_criteria>
