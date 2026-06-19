---
name: audit-specs
description: >-
  Spec-node audit methodology preloaded by the spec-auditor agent. Dispatch
  spec-auditor to audit a spec node; the main conversation reaches this audit
  only through that agent.
allowed-tools: Read, Grep, Glob, Bash
---

<dispatch_gate>

This audit runs in the spec-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the spec-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

Audit a spec node — an enabler or outcome `{slug}.md` — for its section structure, atemporal voice, and per-assertion tag fitness: every assertion carries a valid verification-type tag that fits its claim, and no claim about authored prose carries `[test]`.

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions.

</objective>

<essential_principles>

**VERIFICATION TYPE MUST FIT THE CLAIM.**

Every assertion carries exactly one verification-type tag — `[test]`, `[eval]`, or `[audit]` (`[review]` is the legacy spelling of `[audit]`). `/test` selects the tag; this audit verifies the selection fits the claim — an audit that accepts any present tag verifies nothing. Two checks decide fitness:

- Under a `[test]` tag, the assertion type (scenario, mapping, conformance, property, compliance) fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction.
- The tag is reachable for the claim's subject. A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — is never `[test]`. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim's tag is `[eval]` or `[audit]`.

A missing tag, a bare mechanism tag, a tag carried more than once, an assertion type the `/test` router would not produce for the claim, or `[test]` on a prose-content claim is a finding.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualize` on the directory containing the node spec. Do not proceed without the `<SPEC_TREE_CONTEXT>` marker for that directory.

</step>

<step name="read_node">

**Step 2: Read the node**

Read the node spec under audit. Identify its kind statement (the enabler `PROVIDES … SO THAT … CAN …` or outcome `WE BELIEVE THAT … WILL … CONTRIBUTING TO …` opening), its `## Assertions` section, and each assertion with its inline verification-type tag.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Verify three structural properties:

1. The node opens with a well-formed kind statement (no "Purpose" preamble) — an enabler's `PROVIDES … SO THAT … CAN …` carrying all three clauses, or an outcome's `WE BELIEVE THAT … WILL … CONTRIBUTING TO …` carrying all three. A missing clause, or a template that does not match the node's kind, is a malformed kind statement.
2. An `## Assertions` section is present and carries at least one assertion-type heading.
3. Each assertion-type heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it is of that heading's type — a `### Scenarios` heading whose assertions are universals is mismatched.

**No kind statement or no `## Assertions` section → REJECT — "missing-section." A kind statement that does not match its node's enabler/outcome template → REJECT — "malformed-kind-statement." An empty assertion-type heading, or one whose assertions are not of its type → REJECT — "heading-mismatch."**

</step>

<step name="audit_voice">

**Step 4: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (REJECT)                     | Atemporal (correct)                |
| ------------------------------------- | ---------------------------------- |
| "We added a rollup so failures show"  | "The rollup propagates failures"   |
| "Currently the parser accepts X"      | "The parser accepts X"             |
| "After the rewrite, status derives Y" | "Status derives from test results" |

**Any temporal language in any section → REJECT — "temporal-voice."**

</step>

<step name="audit_tag_fitness">

**Step 5: Per-assertion tag fitness**

For each assertion under `## Assertions`:

1. The assertion carries exactly one verification-type tag — `([test](path))` and `([eval](path))` carry a path; `([audit])` is bare by design, and `([review])` is its legacy spelling, also bare. A missing tag, a tag carried more than once, or a `[test]` or `[eval]` mechanism tag with no path is invalid; a bare `([audit])` or `([review])` is valid.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<essential_principles>` (a universal is never `scenario`). Reject a type the `/test` router would not produce; do not relitigate a choice the router leaves open between equally valid types.
3. The tag is reachable for the claim's subject. When the claim's subject is the content of an authored prose or documentation artifact rather than executable behavior, `[test]` is unreachable — its only evidence reads the authored text and asserts on it (directly or through a fixture or harness that exposes or reads the artifact), proving the prose was authored rather than that code behaves. The tag belongs in `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint).

**A missing tag, a duplicate tag, or a bare mechanism tag → REJECT — "invalid-tag." A `[test]` assertion type that contradicts the claim's quantifier → REJECT — "evidence-type-mismatch." `[test]` on a claim whose subject is authored prose content → REJECT — "prose-coupling."**

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings. If any property fails: REJECTED. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `${CLAUDE_SKILL_DIR}/../audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The `overall` is `PASS` iff every property row is `PASS`; `FAIL` if any row is `FAIL`; `UNKNOWN` if a property cannot be evaluated. Findings carry severity `REJECT` for blocking violations and `WARNING`/`INFO` otherwise.

```json
{
  "schema_version": 1,
  "skill": "audit-specs",
  "target": "<node-spec-file-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "tag-fitness", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (`missing-section`, `malformed-kind-statement`, `heading-mismatch`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, `prose-coupling`); the `message` field carries the one-line detail.

</verdict_format>

<failure_modes>

**Failure 1: Passed a `[test]` claim about a document's prose**

Claude read an assertion — "the skill body states the three-gate vocabulary ([test])" — and passed it because a `[test]` tag was present and pointed at a file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The tag belongs in `[eval]` or `[audit]`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 5 check 3 — when the claim's subject is the content of an authored prose or documentation artifact, `[test]` is unreachable. Reject it as "prose-coupling" and remediate to `[eval]` or `[audit]`.

**Failure 2: Passed a universal claim tagged `scenario`**

Claude saw a `### Compliance` assertion — a universal ALWAYS/NEVER claim — tagged `([test](… scenario …))` and passed it because the assertion type named one of the five. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified.

How to avoid: Step 5 check 2 verifies the assertion type fits the quantifier. Reject a universal tagged `scenario`, and any type the router would not produce — without relitigating a choice the router leaves open between equally valid types.

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualize` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] Node read — kind statement and `## Assertions` identified
- [ ] Section structure: kind statement well-formed, `## Assertions` present, and each assertion-type heading non-empty and matched to its type
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Per-assertion tag fitness: each assertion carries one valid tag; each `[test]` assertion type fits the claim's quantifier; no `[test]` tag on an authored-prose-content claim
- [ ] Verdict issued: APPROVED or REJECTED
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
