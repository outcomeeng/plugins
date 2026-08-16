---
name: audit-prose
description: >-
  Prose audit methodology — judges the human-facing text in scope against the anti-pattern catalog, the supplied kind's style and structure layers, and every triggered rule pack.
model: "{{! term('configured_agent_craft_model') !}}"
argument-hint: "<interface|documentation|copy> <text or paths>"
allowed-tools: Read, Glob, Grep, Skill, Bash
---

{!% require_skill 'prose:prose-standards' %!}

{!% require_skill 'prose:prose-architecture-standards' %!}

<objective>

A verdict on human-facing text against the prose standards — APPROVED, or REJECTED with each journal finding naming the rule, location, severity, and message; the final message is the sealed run's raw token.

</objective>

<constraints>

- NEVER modify the text under review — this audit produces a verdict only.
- NEVER derive the kind from the text. Judging against an inferred kind confirms text written for the wrong slot as correct, which is the error this surface exists to catch. No question is asked; a dispatch with no kind — or no target — records the blocked outcome in `<verdict_format>` and reads nothing.
- NEVER audit without the journal — when the `verification-run-journal-standards` skill or the `spx` CLI is unavailable, report the exact availability failure instead of auditing from memory or emitting an unjournaled verdict.
- NEVER audit text another surface owns — a repository- or domain-governed artifact (spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, root agent guide), a chat response, or operational prose (a code comment, a commit message, an agent-facing instruction) is answered with the `governed-elsewhere` finding, whatever kind the dispatch supplied. Ownership outranks a supplied kind.
- NEVER flag a pattern the supplied kind's overrides explicitly permit — an override is the catalog's decision, not an oversight. A use outside an override's bounds stays a finding.
- NEVER excuse a base-catalog match as "single use" or "it works here" — every match outside an override is a finding.
- NEVER gather a finished result and dump its events at the end — each finding is appended the instant it is raised, per the streaming rule in `/verification-run-journal-standards`.

</constraints>

<kind_intake>

Before either step below, check ownership. A spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is governed by its own workflow, and chat responses and operational prose — a code comment, a commit message, an agent-facing instruction — stay outside the prose surface the same way; a dispatch naming any of these is answered with the `governed-elsewhere` finding rather than an audit against the kind it supplied. Ownership outranks a supplied kind, so a kind arriving at step 1 never resolves past this check.

The kind is an input. Resolve it in this order and stop at the first that yields one:

1. **The invocation.** A kind named in the arguments or the caller's request — `interface`, `documentation`, or `copy`.
2. **The repository's map.** When the repository declares a path-to-kind map at `spx/local/prose.md` and the target path matches an entry, that entry is the kind.

Neither yields one, so no text is read: record the blocked outcome per `<verdict_format>` and stop.

One text carries one kind. Register variation inside it is judged by the `/prose-standards` `<rule_packs>`, which bind on a feature rather than on a kind.

</kind_intake>

<audit_workflow>

1. Check ownership through `<kind_intake>`. A governed artifact is answered with the `governed-elsewhere` finding — open the run, append that one finding, complete rejected, seal, and return the token.

2. Resolve the kind through `<kind_intake>`. Without one — or when the dispatch names no text, paths, or target at all — open the run, append one `severity` `unknown` finding with `rule` `missing-kind` or `missing-target` and `file` `<no target supplied>` when no target exists, complete with the terminal status the rollup yields, seal, and return the token; no text is read.

3. Open the run. Invoke the `verification-run-journal-standards` skill, then `spx journal open --type audit`; capture the run token and append the scope-entered event carrying the run's identity.

4. Read the text under audit — whatever the dispatch names, pastes, or points to — and read the supplied kind's style layer from `/prose-standards` `<kind_layers>` and structural conventions from `/prose-architecture-standards` `<kind_structures>`, plus the governing prose ADR when the repository's spec tree carries one for the target.

5. Sweep, streaming as the run advances. One scope-advanced event per unit swept, one finding-reported event the instant each finding is raised:
   - the base catalog — word choice, sentence structure, paragraph structure, tone, formatting, composition — against the full `/prose-standards` descriptions, applying the kind's overrides;
   - the voice canon, rule by rule;
   - the kind's style layer — every cap that is a count is checked by count;
   - the kind's structural conventions, and conformance to the governing prose ADR where one exists;
   - every rule pack a feature of the text triggers, over the passages carrying that feature.

6. Complete and seal. Append the run-completed event with the terminal status the rollup yields, seal the run, and end with the raw run token as the final message — no prose after it.

</audit_workflow>

<verdict_format>

The verdict is the sealed audit run, produced through the `/verification-run-journal-standards` projection — never a terminal JSON object.

- Each finding maps onto the `/verification-run-journal-standards` finding record. `rule` carries the pattern name — the catalog anti-pattern, pack rule, or structural rule; a sentence carrying multiple co-occurring patterns produces one finding naming every pattern present. `file` and `line` carry the offending text's location — the audited path, or the dispatch-supplied label with the line inside pasted text, `line` null for a whole-text finding. `severity` carries the classification the rollup reads: `reject` for every violation. `message` pairs the catalog category with the offending quote verbatim and a rewrite ready to accept.
- The rollup follows `/verification-run-journal-standards`: any `reject` finding makes the run's terminal status rejected; no findings, approved.
- Ownership routes the text away: one finding with `rule` `governed-elsewhere` at `severity` `reject`, its message naming the governing workflow or the reason the text stays outside the prose surface when no workflow governs it; terminal status rejected.
- No kind or no target supplied: one finding at `severity` `unknown` whose `rule` is `missing-kind` or `missing-target`, whose `file` is the literal `<no target supplied>` when no target exists, and whose message names the missing input — a missing kind names the three-kind vocabulary — so the rollup yields the failed terminal status, the blocked run in the channel's status vocabulary; no text is read.
- The final message is exactly the raw run token, so the sealed run is inspectable while it ran and after — scope progress, each finding, and the terminal status are read from the journal, not from a message.

</verdict_format>

<failure_modes>

**The kind was inferred from the text.**

Claude read the text, recognized a runbook, audited it against the documentation layer, and approved it. The text had been written as marketing copy for a docs site and was wrong for its slot in exactly the way the audit existed to catch — inferring the kind from the artifact makes the artifact its own standard, so any text is correct for the kind it already resembles. The kind is supplied or the audit does not run.

**The ownership check was stated but never reached.**

Claude placed the ownership rule after the sentence "Resolve it in this order and stop at the first that yields one". A dispatch naming a kind for an ADR resolved at step 1, stopped as instructed, and swept a governed artifact against that kind's standards. The rule was present and correct, and the reading order made it unreachable. A check that gates a resolution list precedes that list; a check positioned after one asserts its own precedence to a reader who has already stopped.

**The finding vocabulary named fields the record does not carry.**

Claude described each finding as carrying `pattern`, `category`, `quote`, and `rewrite` — the prose vocabulary — while the journal projection's record carries `file`, `line`, `rule`, `severity`, and `message`. A run built from the prose vocabulary appended events with no `severity` key, so the rollup read `None` for every finding and approved every run, and the rendered surface showed blank locations and messages. A skill that drives a shared projection states its output in that projection's field names and maps its domain vocabulary onto them explicitly.

**A caller check survived a description-only fix.**

Claude removed dispatch language from this skill's description to satisfy the audit-description standard, but left a dispatch gate in the body and a dispatch-tool grant in the frontmatter — the same caller-coupling defect in two other places. A skill never detects, constrains, or branches on the context that invokes it; context placement and dispatch policy belong to the caller. When removing caller coupling, check the description, the frontmatter grants, and the body together — the pattern recurs across all three surfaces.

</failure_modes>

<success_criteria>

- Every applicable rule was judged — base categories, voice canon, kind style layer, kind structural conventions, and every triggered pack — none skipped as unlikely.
- The sealed run states its terminal status, and every finding is falsifiable in the journal finding record per `<verdict_format>`: the pattern as its rule, a location, a severity the rollup reads, and a message pairing category, verbatim quote, and a rewrite showing fixed text.
- Scope progress and each finding were appended as the run advanced; the same text and kind yield the same findings.
- A dispatch naming a governed artifact produced the `governed-elsewhere` finding without reading the text; a dispatch carrying no kind or no target produced the failed terminal status naming the missing input without reading the text.
- The kind judged is the supplied kind, never one this skill concluded, and the kind's overrides produced no false-positive findings.
- The final message is exactly the raw run token of a sealed run.

</success_criteria>
