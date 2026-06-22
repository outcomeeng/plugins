---
name: audit-pdr
description: >-
  PDR audit methodology preloaded by the pdr-auditor agent. Dispatch pdr-auditor
  to audit a PDR; the main conversation reaches this audit only through that agent.
allowed-tools: Read, Grep, Glob, Bash, Skill
---

<dispatch_gate>

This audit runs in the pdr-auditor agent's isolated context. When this skill loads in the main conversation rather than inside a dispatched audit agent, STOP — dispatch the pdr-auditor agent instead of running this audit here. The separate context keeps the verdict free of the bias the main conversation accumulates while doing the work under audit. An already-dispatched agent that preloaded this skill is in the right context and proceeds.

</dispatch_gate>

<objective>

A verdict on one PDR against the PDR evidence model — APPROVED, or REJECTED with each finding naming the section, the violated rule, and the evidence. Findings fall in five categories: content classification (observable product behavior, never architecture), property quality (observable and falsifiable), per-rule tag validity and evidence-type fit, atemporal voice, and consistency with the product spec and ancestor PDRs.

</objective>

<prerequisites>

Read the PDR evidence model completely before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

</prerequisites>

<essential_principles>

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

"Users" means the audience the product document declares, and "observe" means observe through the interaction surfaces that document names — not a fixed end-user-application assumption. When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface, the CLI, filesystem, and version-control state that audience operates is product behavior; the internal algorithm, in-memory data structure, persisted schema, and library choices that audience never touches stay architecture.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. No middle ground.

</essential_principles>

<constraints>

- NEVER modify the PDR under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS read the PDR evidence model before judging — derive the rule set from it, never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every REJECT finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the PDR for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualize` on the directory containing the PDR.

Do not proceed without the `<SPEC_TREE_CONTEXT>` marker for the PDR directory.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit. Identify its sections: the opening decision statement, Rationale, Product properties, and Verification.

Note any missing sections — a PDR without a Verification section is unenforceable.

</step>

<step name="audit_content">

**Step 3: Content classification**

First, read the product document loaded in Step 1 and name its declared audience and the interaction surfaces through which that audience operates the product. "Observable" is judged against that audience: a statement is product behavior when the declared audience observes or operates it. For a product whose audience operates a command-line, filesystem, version-control, or other infrastructure surface, the CLI commands, on-disk layout, and version-control state that audience runs and inspects are observable product behavior — not architecture. The architecture line falls at what the audience never operates: the internal algorithm by which a tool reaches an observable result, the in-memory data structures it holds, the schema it persists, and the libraries it depends on.

Then read every statement in the PDR. Classify each:

| Content type                       | Belongs in     | Finding if in PDR                    |
| ---------------------------------- | -------------- | ------------------------------------ |
| Observable product behavior        | PDR            | Correct                              |
| Observable non-functional property | PDR (property) | Correct                              |
| Technology choice                  | ADR            | REJECT — architecture                |
| Implementation approach            | ADR or code    | REJECT — implementation              |
| Data structure or schema           | ADR            | REJECT — architecture                |
| Performance implementation         | ADR            | REJECT (performance guarantee = PDR) |

**Any architecture or implementation content → REJECT — finding rule "architecture-content."**

The test: "Would the product document's declared audience observe or operate this?" If yes, it is product behavior. If only an implementer of the tool — never the audience — would know it, it belongs in an ADR. Do not flag a tooling product's CLI, filesystem, or version-control state as architecture merely because it names git, a path, or a command; that state is what its audience operates. Reserve the architecture finding for the tool's internal algorithm, data structures, schema, and library choices.

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

**Non-observable or unfalsifiable property → REJECT — finding rule "non-observable-property."**

</step>

<step name="audit_verification">

**Step 5: Per-rule verification tag validity**

Rules live under `## Verification`, grouped into `### Testing`, `### Eval`, and `### Audit` subsections by verification type. For each rule:

1. The rule carries exactly one tag, and the tag is valid for its subsection:
   - under `### Testing` → a `/test`-routed evidence type: one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])` — the rule governs a skill, agent, or classifier whose output has a parseable contract;
   - under `### Audit` → `([audit])` — the rule governs a Spec Tree decision, spec, skill, or agent that admits no deterministic test or graded eval.

   A bare mechanism tag (`([review])`/`([test])`), a tag that disagrees with its subsection, a missing tag, or more than one tag is invalid.
2. Under `### Testing`, the evidence type fits the claim's shape per the `/test` router. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") takes `mapping`, `conformance`, `compliance`, or `property` — never `scenario`, which fits only a single existential interaction. Reject a type the router would not produce for the claim; do not relitigate a choice the router leaves open between equally-valid types.

A rule earns a sound tag only when it is verifiable (a test, eval, or auditing skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot carry a meaningful evidence tag.

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an evidence type, or more than one tag → REJECT — "invalid-tag." An evidence type that contradicts the claim's shape (a universal tagged `scenario` is the clearest case) → REJECT — "evidence-type-mismatch."**

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

**Any temporal language in any section → REJECT — finding rule "temporal-language."**

</step>

<step name="audit_consistency">

**Step 7: Consistency**

Compare the PDR against:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

**Contradiction with product spec or ancestor PDR → REJECT — finding rule "consistency-violation."**
**Overlap with ADR → finding (content misplacement) but not automatic REJECT.**

</step>

<step name="verdict">

**Step 8: Issue verdict**

Scan all findings. If any property fails: REJECTED. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as JSON conforming to the canonical schema in `plugins/spec-tree/skills/audit/scripts/verdict.py`. The skill's entire output is the JSON verdict. The caller captures the JSON and routes it through `emit_verdict.py` with the requested `--format` (defaulting to `markdown+json` for PR-comment delivery).

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
    { "name": "tag-validity", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | UNKNOWN", "findings": [] },
    { "name": "consistency", "status": "PASS | FAIL | UNKNOWN", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding's `rule` field carries the violation pattern (e.g., `architecture-content`, `invalid-tag`, `evidence-type-mismatch`, `temporal-language`); the `message` field carries the one-line detail.

</verdict_format>

<failure_modes>

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

How to avoid: Step 3 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

How to avoid: Step 4 asks "Is this falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw a `### Testing` rule "ALWAYS: every export conforms to RFC 4180 ([scenario])" and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the tag should be `mapping`, `conformance`, `property`, or `compliance`. The mismatch is `evidence-type-mismatch`, not `invalid-tag`.

How to avoid: Step 5 reads the quantifier first. A universal (ALWAYS / NEVER / "for all" / "no input") tagged `scenario` is `evidence-type-mismatch`; a structural tag problem — bare mechanism tag, wrong subsection, missing tag, more than one tag — is `invalid-tag`.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 3 reads the product document's declared audience first and judges "observable" against it. A git topology, a path layout, or a CLI behavior the audience operates is product behavior. Reserve `architecture-content` for what the audience never operates — the tool's internal algorithm, in-memory data structures, persisted schema, and library choices — which stays an ADR concern even for a tooling product.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every PDR rule was judged with none skipped — content classification, property quality, per-rule tag validity and evidence-type fit, atemporal voice, and consistency (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no rule left unevaluated.
- Each REJECT finding is falsifiable: it names the section, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable or unfalsifiable property, the mismatched tag, the temporal phrase, or the contradicted product spec or ancestor PDR.
- The same PDR yields the same verdict.

</success_criteria>
