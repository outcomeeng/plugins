---
name: audit-pdr
description: ALWAYS use when auditing a PDR or after making changes to a PDR
allowed-tools: Read, Grep, Glob, Bash
---

<objective>

Audit a PDR for its consistency, clarity, and strict conformance to the PDR evidence model.

</objective>

<prerequisites>

Read the PDR evidence model completely before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

</prerequisites>

<essential_principles>

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**BINARY VERDICT.**

`APPROVED` or `REJECT`. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualizing` on the directory containing the PDR.

Do not proceed without the `<SPEC_TREE_CONTEXT>` marker for the PDR directory.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit. Identify its sections: the opening decision statement, Rationale, Product properties, and Verification.

Note any missing sections — a PDR without a Verification section is unenforceable.

</step>

<step name="audit_content">

**Step 3: Content classification**

Read every statement in the PDR. Classify each:

| Content type                       | Belongs in     | Finding if in PDR                    |
| ---------------------------------- | -------------- | ------------------------------------ |
| Observable product behavior        | PDR            | Correct                              |
| Observable non-functional property | PDR (property) | Correct                              |
| Technology choice                  | ADR            | REJECT — architecture                |
| Implementation approach            | ADR or code    | REJECT — implementation              |
| Data structure or schema           | ADR            | REJECT — architecture                |
| Performance implementation         | ADR            | REJECT (performance guarantee = PDR) |

**Any architecture or implementation content → REJECT — "architecture content in PDR."**

The test: "Would a user care about this statement?" If the answer is no, it probably belongs in an ADR.

</step>

<step name="audit_properties">

**Step 4: Property quality**

For each product property:

1. Is it observable from the user's perspective?
   - "Pages load in under 2 seconds" → observable ✓
   - "Database uses row-level locking" → not user-observable ✗
2. Is it falsifiable — is there a scenario where it's violated?
   - "Good user experience" → unfalsifiable ✗
   - "Search returns results in under 500ms" → falsifiable ✓

**Non-observable or unfalsifiable property → REJECT — "non-observable property."**

</step>

<step name="audit_verification">

**Step 5: Per-rule verification tag validity**

Rules live under `## Verification`, grouped into `### Testing`, `### Eval`, and `### Audit` subsections by verification type. For each rule:

1. The rule carries exactly one tag, and the tag is valid for its subsection:
   - under `### Testing` → a `/testing`-routed evidence type: one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])` — the rule governs a skill, agent, or classifier whose output has a parseable contract;
   - under `### Audit` → `([audit])` — the rule governs a Spec Tree decision, spec, skill, or agent that admits no deterministic test or graded eval.

   A bare mechanism tag (`([review])`/`([test])`), a tag that disagrees with its subsection, a missing tag, or more than one tag is invalid.
2. Under `### Testing`, the evidence type fits the claim's shape per the `/testing` router. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") takes `mapping`, `conformance`, `compliance`, or `property` — never `scenario`, which fits only a single existential interaction. Reject a type the router would not produce for the claim; do not relitigate a choice the router leaves open between equally-valid types.
3. Is the rule specific enough that two reviewers invariably would agree on pass/fail?

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an evidence type, or more than one tag → REJECT — "invalid-mode-tag." An evidence type that contradicts the claim's shape (a universal tagged `scenario` is the clearest case) → REJECT — "evidence-type-mismatch."**

</step>

<step name="audit_voice">

**Step 6: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (REJECT)                     | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

**Any temporal language in any section → REJECT — "temporal voice."**

</step>

<step name="audit_consistency">

**Step 7: Consistency**

Compare the PDR against:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

**Contradiction with product spec or ancestor PDR → REJECT — "consistency violation."**
**Overlap with ADR → finding (content misplacement) but not automatic REJECT.**

</step>

<step name="verdict">

**Step 8: Issue verdict**

Scan all findings. If any property fails: REJECT. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/auditing/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

The skill's `overall` is `PASS` iff every property row is `PASS`; `FAIL` if any property is `FAIL`; `UNKNOWN` if a property cannot be evaluated. Findings within each row carry severity `REJECT` for blocking violations and `WARNING`/`INFO` for non-blocking observations.

```json
{
  "schema_version": 1,
  "skill": "audit-pdr",
  "target": "<pdr-file-path>",
  "overall": "PASS | FAIL | UNKNOWN",
  "rows": [
    { "name": "content-classification", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "property-quality", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "mode-validity", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "consistency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (e.g., `architecture-content`, `invalid-mode-tag`, `evidence-type-mismatch`, `temporal-language`); the `message` field carries the one-line detail.

</verdict_format>

<failure_modes>

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

How to avoid: Step 3 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

How to avoid: Step 4 asks "Is this falsifiable from the user's perspective?"

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualizing` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] PDR read — all sections identified
- [ ] Content classification: every statement classified as product behavior or flagged
- [ ] Property quality: each property checked for observability and falsifiability
- [ ] Per-rule tag validity and evidence-type fit: each rule's tag validated against its Verification subsection (Testing → one of the five evidence types, Eval → `[eval]`, Audit → `[audit]`), and each `### Testing` rule's evidence type verified against the claim's shape per `/testing` (a universal is never `scenario`)
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Consistency: compared against product spec and ancestor PDRs
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
