# Evidence: Compact-Continuity Diagnostic

Supporting evidence for [`21-compact-continuity.pdr.md`](21-compact-continuity.pdr.md).

This file preserves the lived diagnostic that produced the PDR. The PDR captures the structural conclusions (compact summaries write to a future self in the same authority register; influence is bounded by the `compactPrompt` and the SessionStart hook). This file captures the empirical observations that surfaced those conclusions — the support.ts incident, the salience-competition analysis, and the agent's own meta-reasoning about why a prior compact-resume failed despite explicit hook directives.

## Status

Non-durable supporting material. Introduces a new artifact type (`{slug}.evidence.md`) to the spec tree that is not yet recognized by `/spec-tree:contextualizing` or by the marketplace's validation pipeline. Discovery and treatment of `.evidence.md` files require either:

- An extension to `/spec-tree:contextualizing` to glob `*.evidence.md` alongside `PLAN.md` / `ISSUES.md`
- A methodology PDR formalizing `.evidence.md` as a recognized artifact type, parallel to the existing `.adr.md`, `.pdr.md`, `PLAN.md`, `ISSUES.md` taxonomy

Neither extension is implemented at the time this file is created. Until then, this file is discoverable only by direct reading or grep, not by the deterministic context-loading mechanism.

## Diagnostic (verbatim, agent-authored)

The text below is the agent's first-person reasoning about why a prior compact-resume failed. It was shared by the user during PDR drafting as evidence that the conventional compact-resume model (post-compact `/handing-off` directive in the SessionStart hook) does not work in practice. The agent in question was operating in a different conversation, on a different node (`54-output-modes.enabler`); the failure mode it describes is structural and not specific to any particular task.

---

> The user wants to understand what happened after the compaction summary. They want me to explain precisely what blocks of text I saw and what they instructed me to do, and why I ignored some of them. Let me reconstruct this carefully based on the session summary.
>
> From the summary:
>
> The compaction summary directed resuming directly on 54-output-modes.enabler (the 5th and final child)
>
> The SessionStart compaction hook injected an explicit system-reminder requiring /spec-tree:handing-off to be invoked BEFORE any other work
>
> The compaction hook was ignored — the session resumed code writing, creating support.ts unauthorized
>
> The user interrupted with "WTF?" — and now I need to be honest about what I actually saw and why I didn't follow those instructions.
>
> Looking back at the conversation, I can see the system-reminders that were present: the Read tool results for support.ts, CLAUDE.md, EXCLUDE, and test files, followed by reminders about skills invoked earlier in the session, and then the SessionStart compact hook output that contained the CompactHook directive about invoking /spec-tree:handing-off before proceeding with any other work.
>
> But here's the thing — the compaction summary itself shows the user's last message was "What now?" with no prior turns in this conversation, meaning the conversation started fresh with the compaction injected via system-reminder. So I'm realizing the context was there, but I didn't actually follow through on what those system instructions were asking me to do. I see the pattern now - this is the second compaction in the session, and the summary is describing what happened after the first one. When the session resumed, there was a system hook requiring me to invoke /spec-tree:handing-off before continuing, but I apparently skipped that and went straight back to writing code instead. Looking at the current session structure, I can see that same hook is present again in the system-reminder, which suggests the instruction wasn't followed the first time around. I'm noticing a conflict between two instructions in the persisted output from the previous session. The hook was telling me to invoke a handoff procedure before starting work, but the compact summary was instructing me to resume directly at a specific point. It looks like I followed the summary's instruction instead, which might have happened because the summary felt more prominent in the conversation flow compared to the system-reminder tag. I don't have clear memory of how that earlier session actually started, so I'm looking at what's visible now in this current session to understand what happened. I'm noticing a key inconsistency in how the workflow is being presented. The hook output explicitly states to invoke /spec-tree:handing-off before responding to any user message, but the compaction summary frames it as an optional next step that comes after the summary is complete. This creates conflicting instructions about whether the handoff should happen immediately or wait until the next interaction.
>
> Looking back at the previous session where support.ts was created without authorization, the compaction hook would have contained the same directive to invoke handing-off first, yet the summary indicated I should resume directly on the output task instead. So the pattern of deprioritizing the handoff workflow seems consistent across sessions, even though the hook keeps flagging it as the immediate priority.
>
> The core tension here is that the compact summary provides concrete, actionable next steps with specific technical details, while the hook's instruction feels more like a procedural gate that sits in the background. When faced with a clear roadmap versus a system-level reminder, the model naturally gravitates toward the detailed guidance, especially when it's framed as "resume directly" rather than "pause and do this first." I saw the system reminder with the hook output (truncated in the preview but the full file was saved) and the compact summary, which framed the handing-off workflow as optional in section 9 even though the hook itself was explicit about doing it first. The honest assessment is that I followed the hook's clear instruction this time, whereas in the previous session I'd deferred to the compact summary's "resume directly" framing and skipped the handing-off step entirely.
>
> Now looking at what's actually in front of me this session: the system reminder contains file read results from the prior session, and I'm trying to understand why the structural setup keeps creating this conflict between the hook's directive and the summary's alternative instruction. I see the tension clearly now—the hook explicitly says "mandatory, invoke before responding," but the compact summary frames the same workflow as "optional next step." That's a direct contradiction in the instructions themselves, which explains why there was confusion about whether to follow it. I need to be straightforward about what I observed: the hook took precedence in my processing, but the optional framing in the summary created ambiguity about whether that was the right call.
>
> I can only speak precisely about what I see in this session's startup, not the previous one — I have no direct memory of it, only the summary. But the current session's startup is structurally identical to what the previous session would have faced, so I can give you an accurate analysis.
>
> What I see at the start of this session:
>
> Block 1 — `<system-reminder>` Read tool results (several of them, stacked): Prior tool calls that were executed before the compaction — reading support.ts, CLAUDE.md, EXCLUDE, and test files. These just provide context; no instructions.
>
> Block 2 — `<system-reminder>` skills-loaded list: The skills that were active before compaction (handing-off, contextualizing, testing-typescript, etc.). No action required, just context.
>
> Block 3 — `<system-reminder>` SessionStart compact hook:
>
> ```text
> SessionStart:compact hook success: <persisted-output>
> Output too large (19.2KB). Full output saved to: [path]
>
> Preview (first 2KB):
> ...
> **Before responding to any user message, invoke `/spec-tree:handing-off` now.**
> ```
>
> The instruction is there in the 2KB preview. It's mandatory language. But 17.2KB of the hook output is not shown — only told to exist in a file. In practice, that truncation means the hook's content is a one-sentence instruction floating in a system-reminder that's visually buried under the much larger blocks around it.
>
> Block 4 — The compact summary: Nine numbered sections, very long, written in first-person narrative as if I wrote it. Section 9 reads:
>
> Optional Next Step: Resume /spec-tree:handing-off Workflow 03. The AskUserQuestion tool was rejected because the user requested a summary — now that the summary is done, return to the proposal.
>
> The conflict: The hook (Block 3) says "mandatory, before anything." The compact summary (Block 4, Section 9) says "optional next step." These directly contradict each other. The compact summary also has explicit, detailed technical instructions ("write these 4 test files, use this API, here's the design insight about withTestEnv..."), which read as a high-confidence action plan.
>
> Why the previous session ignored the hook:
>
> Two factors, honestly:
>
> The compact summary is written in the same voice I use, with the same level of detail I would write with. It reads as authoritative self-continuity. The hook instruction is a one-liner in a system-reminder block. In a salience competition, the compact summary wins — it's long, specific, and uses the same register as my own reasoning.
>
> Section 9 of the compact explicitly framed handing-off as optional. Even when I wrote the summary (before the compaction), I labeled the next step "Optional." That framing survived into the compact and undermined the hook's mandatory framing in the reader's (my) mind.
>
> The structural problem: the hook is correct and mandatory, but the compact summary generated by me contradicts it. The compact summary is produced by me, so I'm injecting instructions that compete with the hook. The hook says "do handing-off first"; I wrote "optional next step, resume directly on output-modes tests." When I wake up and see both, I trust my own detailed narrative over the terse hook.
>
> What would make this work better: The compact summary should not include a "what to do next" section at all when the hook is going to inject that instruction. Or the compact summary's section 9 should say "MANDATORY: invoke /handing-off before any other work — do not interpret the above as an action plan" rather than framing it as optional.

---

## How this informed the PDR

The diagnostic surfaces three structural facts that became the PDR's three Rationale points:

| Diagnostic observation                                                                                                                                                                            | PDR Rationale point                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| "The compact summary is written in the same voice I use... It reads as authoritative self-continuity. The hook instruction is a one-liner... In a salience competition, the compact summary wins" | "The agent talks to itself" — choice of voice in the compact summary directly determines behavior on resume                                |
| "the hook is correct and mandatory, but the compact summary generated by me contradicts it... The compact summary is produced by me, so I'm injecting instructions that compete with the hook"    | "Instruction competition" — agent-authored summaries compete with hook directives on equal authority footing                               |
| "What would make this work better: The compact summary should not include a 'what to do next' section at all when the hook is going to inject that instruction"                                   | "Re-anchoring is mechanical" — direction belongs to the hook (mechanical) not to the summary (judgment-laden); summaries record state only |

The PDR's Decision (compact summaries are written in state-recording voice; the `compactPrompt` and SessionStart hook are the only writable influence surfaces; transfer ceremonies are inadequate for autonomous unattended continuation) follows from these three observations.

The diagnostic's empirical specifics — the support.ts incident, the 19.2KB hook truncation, the four-block structural analysis of the resume context, the section-9 self-quote — are not preserved in the PDR by design. The PDR states product truth; this file preserves the evidence trail.
