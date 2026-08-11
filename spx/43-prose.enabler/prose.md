# Prose

PROVIDES one matched prose authoring and audit surface over composed per-kind style layers
SO THAT skills, agents, and documentation across the marketplace
CAN produce and judge human-facing text in one voice family without selecting among overlapping style skills

The prose plugin exposes exactly two harness-matched skills. `/author-prose` is the writing entry point: it takes the kind, composes that kind's author skill, and directs an audit pass. `/audit-prose` is the audit methodology: it takes the kind, composes that kind's audit skill, and emits a structured verdict; it runs only inside the dispatched `prose-auditor` thin agent. Chat responses to the user route to neither — the plugin's rendered output style governs them. Operational prose — a code comment, a commit message, an agent-facing instruction — likewise stays outside the prose surface, with the workflow that owns it.

The kind is an input to both routers, never a conclusion either one reaches. Writing precedes the text, so no property of the text is available when authoring begins; judging against an inferred kind confirms text written for the wrong slot as correct, which is the error the surface exists to catch. The caller supplies the kind, a repository may declare a path-to-kind map its owner writes, and an interactive router with neither asks once from the fixed list. A dispatched audit that receives no kind emits a blocked verdict and reads nothing.

The kinds are interface (text inside a designed surface), document (a page in a document set), and copy (a standalone piece read start to finish). A kind exists only where it carries a rule no other kind carries. Style knowledge lives in composed skills the harness never matches: each kind carries an equally structured triple — an author skill, a standards skill, and an audit skill — reached only through the two routers. Every kind's standards derive from the shared `/prose-standards` anti-pattern catalog and transclude the one authored voice canon, so kinds differ in register and composition, never in voice.

Register variation inside one text is carried by rule packs, not by a second kind. A pack declares the observable feature that triggers it and the rules that then bind: numbered steps or imperative procedure trigger the instruction caps, and a table triggers the table-shape rules. Packs fire inside every kind, so a runbook's procedure and an essay's table are each governed wherever they appear, and one text carries exactly one kind.

The audit verdict is structured: an overall determination of `APPROVED`, `REJECTED`, or `UNKNOWN`. `APPROVED` and `REJECTED` carry findings, each with the pattern name, its catalog category, the offending quote, and a concrete rewrite. `UNKNOWN` carries no findings and names the reason the audit did not run. Both determinations that carry findings are followed by a summary with the violation count and most frequent category.

The plugin ships a rendered output style named `prose` whose voice rules and every kind's voice rules render at build time from one authored canon, so no consumer of that voice can drift from another. The output style ships natively inside the plugin's output-style surface; an agent harness without the output-style concept ignores it.

## Assertions

### Compliance

- ALWAYS: `/author-prose` and `/audit-prose` are the plugin's only harness-matched skills — every per-kind author, standards, and audit skill declares itself composed-only and is reached through a router, never matched directly ([audit])
- ALWAYS: the kind is supplied to both routers — as a caller argument, from a repository's declared path-to-kind map, or from the one question an interactive router asks — and neither router derives it from the text, the request, or the destination ([audit])
- ALWAYS: an `/audit-prose` verdict is produced only in a dispatched verifier context through the `prose-auditor` agent, and its final message is the structured verdict — `APPROVED` or `REJECTED` with findings carrying pattern, category, quote, and rewrite, or `UNKNOWN` naming the reason and the kind list and judging no text ([audit])
- ALWAYS: every kind's standards skill derives from the shared `/prose-standards` catalog — inherited rules condensed to names, explicit overrides, and kind-specific rules — so kinds differ in register and composition, never in voice ([audit])
- ALWAYS: the shipped `prose` output style and every kind's voice rules render from one authored canon — never a hand-authored second canon ([audit])
- ALWAYS: a kind carries at least one rule no other kind carries, and register variation inside one text is governed by a rule pack whose trigger is an observable feature of that text ([audit])
- NEVER: text another surface owns is authored or audited through the prose surface, and ownership outranks a supplied kind — a repository- or domain-governed artifact (spec, decision record, `SKILL.md`, coordination note, agent guide) stays with its governing workflow, a chat response is governed by the rendered output style, and operational prose (code comment, commit message, agent-facing instruction) stays with the workflow that owns it ([audit])
