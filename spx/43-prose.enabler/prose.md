# Prose

PROVIDES one matched prose authoring and audit surface over composed per-kind style layers
SO THAT skills, agents, and documentation across the marketplace
CAN produce and judge human-facing text in one voice family without selecting among overlapping style skills

The prose plugin exposes exactly two harness-matched skills. `/author-prose` is the writing entry point: it classifies the text kind, composes the kind's author skill, and directs an audit pass. `/audit-prose` is the audit methodology: it classifies the same way, composes the kind's audit skill, and emits a structured verdict; it runs only inside the dispatched `prose-auditor` thin agent. Chat responses to the user route to neither — the plugin's rendered output style governs them.

Style knowledge lives in composed skills the harness never matches. Each text kind carries an equally structured triple — an author skill, a standards skill, and an audit skill — reached only through the two routers. The kinds are copy (self-contained pieces read start to finish), interface (fragments embedded in a designed surface), docs (documentation that explains or instructs the use of a product), and internal-docs (workspace documents for team readers). Every kind's standards derive from the shared `/prose-standards` anti-pattern catalog; kinds differ in register and composition rules, never in voice.

Kind detection is one ordered procedure stated in `/prose-standards` and executed by both routers, first match deciding: a repository- or domain-governed artifact routes to its governing workflow and never enters the prose surface; a workspace document for team readers is internal-docs; text that explains or instructs the use of a product is docs; a fragment embedded in a designed surface is interface; any remaining self-contained piece is copy. A document whose parts differ in kind receives each part's own layer. Text the procedure leaves ambiguous is resolved by asking the user to select a kind from the taxonomy.

The audit verdict is structured: an overall determination of `APPROVED` or `REJECTED` with findings, each carrying the pattern name, its catalog category, the offending quote, a concrete rewrite, and the detected kind, followed by a summary with the violation count and most frequent category.

The plugin ships a rendered output style named `prose` whose voice rules and the interface kind's voice rules render at build time from one authored canon, so the chat voice and the interface style cannot drift apart. The output style ships natively inside the plugin's output-style surface; an agent harness without the output-style concept ignores it.

## Assertions

- ALWAYS: `/author-prose` and `/audit-prose` are the plugin's only harness-matched skills — every per-kind author, standards, and audit skill declares itself composed-only and is reached through a router, never matched directly
- ALWAYS: both routers classify text through the ordered kind-detection procedure — ownership, audience, function, unit, then copy — with first match deciding, so every text resolves to exactly one kind
- ALWAYS: text the detection procedure leaves ambiguous is resolved by asking the user to select a kind from the taxonomy — never by guessing and never by inventing a style outside it
- ALWAYS: an `/audit-prose` verdict is produced only in a dispatched verifier context through the `prose-auditor` agent, and its final message is the structured verdict — overall `APPROVED` or `REJECTED` with findings carrying pattern, category, quote, rewrite, and detected kind
- ALWAYS: every kind's standards skill derives from the shared `/prose-standards` catalog — inherited rules condensed to names, explicit overrides, and kind-specific rules — so kinds differ in register and composition, never in voice
- ALWAYS: the shipped `prose` output style and the interface kind's voice rules render from one authored canon — never a hand-authored second canon
- NEVER: a repository- or domain-governed artifact — a spec, decision record, `SKILL.md`, coordination note, or agent guide — is authored or audited through the prose surface; ownership outranks every later detection test
- NEVER: a chat response to the user routes through the prose surface — the rendered output style governs chat voice
