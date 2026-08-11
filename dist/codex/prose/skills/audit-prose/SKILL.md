---
name: audit-prose
description: >-
  Prose audit methodology — judges human-facing text against the base anti-pattern catalog, the supplied kind's standards layer, and every triggered rule pack, emitting a structured verdict whose findings carry pattern, category, quote, and rewrite.
model: "gpt-5.5"
argument-hint: "<interface|document|copy> <text or paths>"
allowed-tools: Read, Glob, Grep, Skill
---

Invoke the `prose:prose-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>

A structured verdict on human-facing text — `APPROVED`, `REJECTED` with findings carrying pattern, category, quote, and rewrite, or `UNKNOWN` when no kind was supplied.

</objective>

<constraints>

- NEVER modify the text under review — this audit produces a verdict only.
- NEVER derive the kind from the text. Judging against an inferred kind confirms text written for the wrong slot as correct, which is the error this surface exists to catch.
- NEVER audit a repository- or domain-governed artifact here — a spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is answered with the `governed-elsewhere` finding, whatever kind the dispatch supplied. Ownership outranks a supplied kind.
- NEVER audit without a kind. Emit `UNKNOWN` and read nothing.
- NEVER flag a pattern the supplied kind's overrides explicitly permit — an override is the catalog's decision, not an oversight.
- NEVER excuse a base-catalog match as "single use" or "it works here" — every match outside an override is a finding.

</constraints>

<kind_intake>

Before either step below, check ownership. A spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide is governed by its own workflow, and a dispatch naming one is answered with the `governed-elsewhere` finding rather than an audit against the kind it supplied. Ownership outranks a supplied kind, so a kind arriving at step 1 never resolves past this check.

The kind is an input. Resolve it in this order and stop at the first that yields one:

1. **The invocation.** A kind named in the arguments or the caller's request — `interface`, `document`, or `copy`.
2. **The repository's map.** When the repository declares a path-to-kind map at `spx/local/prose.md` and the target path matches an entry, that entry is the kind.

Neither yields one, so no audit runs: emit the `UNKNOWN` verdict in `<verdict_format>` and stop. Asking is unavailable here, because this skill runs inside a dispatched verifier context with no user to ask.

One text carries one kind. Register variation inside it is judged by the `/prose-standards` `<rule_packs>`, which bind on a feature rather than on a kind.

</kind_intake>

<workflow>

1. Check ownership through `<kind_intake>`. A governed artifact is answered with the `governed-elsewhere` finding and stops here, whatever kind the dispatch supplied.

2. Resolve the kind through `<kind_intake>`. Without one, emit `UNKNOWN` and stop before reading the text.

3. Read the text under audit — whatever the dispatch names, pastes, or points to.

4. Invoke the supplied kind's composed audit skill via the Skill tool: `prose:audit-interface`, `prose:audit-document`, or `prose:audit-copy`. That skill loads the kind's standards and sweeps its categories; collect its findings.

5. Identify every feature that triggers a rule pack and confirm the composed skill swept each triggered pack over the passages carrying that feature.

6. Emit the structured verdict in the `<verdict_format>` shape as the final message — no prose outside the JSON object.

</workflow>

<verdict_format>

```json
{
  "schema_version": 1,
  "skill": "audit-prose",
  "overall": "APPROVED",
  "kind": "copy",
  "findings": [],
  "summary": { "violations": 0, "most_frequent_category": null }
}
```

- `overall` is `REJECTED` when at least one finding exists; `APPROVED` means zero findings.
- Each finding carries `pattern` (the catalog anti-pattern or pack rule name), `category` (its catalog section or pack name), `quote` (the offending text verbatim), and `rewrite` (fixed text ready to accept).
- `kind` is the supplied kind, verbatim.
- A sentence carrying multiple co-occurring patterns produces one finding naming every pattern present, listed before single-pattern findings.
- When ownership routes the text away, `overall` is `REJECTED` with a single finding whose `pattern` is `governed-elsewhere` naming the governing workflow.

No kind resolved, so the verdict is blocked instead:

```json
{
  "schema_version": 1,
  "skill": "audit-prose",
  "overall": "UNKNOWN",
  "kind": null,
  "reason": "no kind supplied; the dispatcher supplies one of interface, document, copy",
  "findings": [],
  "summary": { "violations": 0, "most_frequent_category": null }
}
```

- `UNKNOWN` carries `reason` and an empty `findings` array. It judges no text, so it is neither an approval nor a rejection.

</verdict_format>

<success_criteria>

- The final message is exactly the `<verdict_format>` JSON object.
- A dispatch naming a governed artifact — a spec, ADR, PDR, `SKILL.md`, `PLAN.md`, `ISSUES.md`, or root agent guide — produced the `governed-elsewhere` finding without reading the text or invoking `prose:audit-interface`, `prose:audit-document`, or `prose:audit-copy`, whatever kind it supplied.
- The kind in the verdict is the supplied kind, never one this skill concluded.
- A dispatch carrying no kind produced `UNKNOWN` with its reason, and no text was read.
- Every finding carries all four fields, and the rewrite shows fixed text rather than an instruction.
- `summary.violations` equals the findings count, and `most_frequent_category` is the category those findings carry most often.
- Kind overrides produced no false-positive findings.

</success_criteria>

<failure_modes>

**The kind was inferred from the text.**

Claude read the text, recognized a runbook, audited it against the document layer, and returned `APPROVED`. The text had been written as marketing copy for a docs site and was wrong for its slot in exactly the way the audit existed to catch — inferring the kind from the artifact makes the artifact its own standard, so any text is correct for the kind it already resembles. The kind is supplied or the audit does not run.

**The ownership check was stated but never reached.**

Claude placed the ownership rule after the sentence "Resolve it in this order and stop at the first that yields one". A dispatch naming `document` for an ADR resolved at step 1, stopped as instructed, and swept a governed artifact against the document standards. The rule was present and correct, and the reading order made it unreachable. A check that gates a resolution list precedes that list; a check positioned after one asserts its own precedence to a reader who has already stopped.

**A caller check survived a description-only fix.**

Claude removed dispatch language from this skill's description to satisfy the audit-description standard, but left a dispatch gate in the body and a dispatch-tool grant in the frontmatter — the same caller-coupling defect in two other places. A skill never detects, constrains, or branches on the context that invokes it; context placement and dispatch policy belong to the caller. When removing caller coupling, check the description, the frontmatter grants, and the body together — the pattern recurs across all three surfaces.

</failure_modes>
