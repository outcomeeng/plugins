---
name: auditing-product-decisions
description: >-
  ALWAYS invoke this skill when auditing PDRs or after writing a PDR.
  NEVER audit PDRs without this skill.
---

<objective>

Audit whether a PDR establishes enforceable product decisions that flow into spec assertions. Six properties must hold — content classification, invariant quality, compliance quality, atemporal voice, consistency, downstream flow — checked in strict order. A PDR missing any property is a declaration that nothing enforces.

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

</objective>

<quick_start>

**PREREQUISITE**: Invoke `/contextualizing` on the PDR's parent directory.

1. Read the PDR under audit
2. Check six properties in order: content → invariants → compliance → voice → consistency → downstream
3. First property failure = REJECT (skip remaining properties)
4. All six properties hold = APPROVED

**Content classification is the gate.** If a PDR is full of architecture content, it's an ADR in disguise. No further analysis.

</quick_start>

<essential_principles>

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

**DOWNSTREAM FLOW IS MANDATORY.**

A compliance rule that no spec assertion references is an unenforced declaration. The product equivalent of a test with no coupling. Search the governed subtree — if no assertion implements the rule, REJECT.

**ATEMPORAL VOICE.**

Same standard as ADR review. PDRs state product truth. "Users can rely on X" — not "We decided to add X because Y was broken."

**BINARY VERDICT.**

APPROVED or REJECT. No middle ground.

</essential_principles>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Invoke `/contextualizing` on the directory containing the PDR. This loads:

- The product spec (PDR must be consistent with product scope)
- Ancestor PDRs (PDR must not contradict them)
- Sibling ADRs (to verify content isn't misplaced)

Do not proceed without `<SPEC_TREE_CONTEXT>` marker.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit. Identify all sections: Purpose, Context, Decision, Rationale, Trade-offs, Product invariants, Compliance.

Note any missing sections — a PDR without a Compliance section has no enforceable rules.

</step>

<step name="audit_content">

**Step 3a: Content classification**

Read every statement in the PDR. Classify each:

| Content type                | Belongs in      | Finding if in PDR                    |
| --------------------------- | --------------- | ------------------------------------ |
| Observable product behavior | PDR             | Correct                              |
| User-facing guarantee       | PDR (invariant) | Correct                              |
| Technology choice           | ADR             | REJECT — architecture                |
| Implementation approach     | ADR or code     | REJECT — implementation              |
| Data structure or schema    | ADR             | REJECT — architecture                |
| Performance implementation  | ADR             | REJECT (performance guarantee = PDR) |

**Any architecture or implementation content → REJECT — "architecture content in PDR."**

The test: "Would a user care about this statement?" If the answer is no, it probably belongs in an ADR.

</step>

<step name="audit_invariants">

**Step 3b: Invariant quality**

For each product invariant:

1. Is it observable from the user's perspective?
   - "Pages load in under 2 seconds" → observable ✓
   - "Database uses row-level locking" → not user-observable ✗
2. Is it falsifiable — can you describe a scenario where it's violated?
   - "Good user experience" → unfalsifiable ✗
   - "Search returns results in under 500ms" → falsifiable ✓

**Non-observable or unfalsifiable invariant → REJECT — "non-observable invariant."**

</step>

<step name="audit_compliance">

**Step 3c: Compliance quality**

For each MUST/NEVER rule:

1. Is it verifiable by product review, automated test, or automated enforcement?
2. Does it have a `([review])` or `([test](...))` tag?
3. Is it specific enough that two reviewers would agree on pass/fail?

**Unverifiable or untagged compliance rule → REJECT — "unverifiable rule."**

</step>

<step name="audit_voice">

**Step 3d: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (REJECT)                     | Atemporal (correct)                 |
| ------------------------------------- | ----------------------------------- |
| "We discovered that users need X"     | "Users rely on X"                   |
| "Currently the product does X"        | "The product does X"                |
| "After customer feedback, we decided" | "This decision governs X"           |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code) |

**Any temporal language in any section → REJECT — "temporal voice."**

</step>

<step name="audit_consistency">

**Step 3e: Consistency**

Compare the PDR against:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

**Contradiction with product spec or ancestor PDR → REJECT — "consistency violation."**
**Overlap with ADR → finding (content misplacement) but not automatic REJECT.**

</step>

<step name="audit_downstream">

**Step 3f: Downstream flow**

For each compliance rule in the PDR, search the governed subtree for spec assertions that reference or implement the rule.

```bash
# Find specs in the governed subtree
Glob: "spx/{pdr-scope}/**/*.md"

# Search for references to this PDR's compliance rules
Grep: pattern matching the PDR's MUST/NEVER rule text or PDR filename
```

Report flow status for each rule:

```text
MUST: "all pages load in under 2 seconds" ([review])
→ Referenced by: spx/.../21-performance.outcome assertions ✓

NEVER: "expose internal IDs in URLs" ([test](tests/url-safety.unit.test.ts))
→ Referenced by: spx/.../21-url-safety.outcome assertions ✓

NEVER: "use branded terminology in error messages" ([review])
→ Referenced by: (none) ✗ — unenforced
```

**Any compliance rule with zero downstream assertions → REJECT — "unenforced rule."**

A compliance rule — whether tagged `[review]` or `[test]` — still needs a downstream spec assertion. The tag means "this is how it's verified" — but if no spec declares the behavior, there's nothing to verify against.

</step>

<step name="verdict">

**Step 4: Issue verdict**

Scan all findings. If any property fails: REJECT.

</step>

</audit_workflow>

<verdict_format>

**Approved:**

```text
Audit: {pdr-path}
Verdict: APPROVED

| # | Property | Status | Detail |
|---|----------|--------|--------|
| 1 | Content classification | PASS | All statements are product behavior |
| 2 | Invariant quality | PASS | N invariants, all user-observable |
| 3 | Compliance quality | PASS | N rules, all verifiable with tags |
| 4 | Atemporal voice | PASS | No temporal language |
| 5 | Consistency | PASS | Consistent with product spec and ancestors |
| 6 | Downstream flow | PASS | All N rules referenced in subtree |
```

**Rejected:**

```text
Audit: {pdr-path}
Verdict: REJECT

| # | Property Failed | Finding | Detail |
|---|-----------------|---------|--------|
| 1 | Content classification | architecture content | "Use JWT tokens" is a technology choice |
| 2 | Downstream flow | unenforced rule | "NEVER: expose internal IDs" has no downstream assertion |

Unenforced declarations:
{List each compliance rule with no downstream spec assertion}
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a PDR full of architecture decisions**

Reviewer saw a well-structured PDR with Purpose, Decision, Compliance sections. Approved. The Decision section said "The system uses PostgreSQL with row-level locking for concurrent session management." That's an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

How to avoid: Step 3a classifies every statement. "Would a user care?" is the test.

**Failure 2: Approved unenforced compliance rules**

Reviewer checked the PDR's Compliance section — well-written MUST/NEVER rules with `[review]` tags. Approved. No spec in the entire subtree referenced these rules. The product could violate every rule and no test, enforcement, or review would catch it.

How to avoid: Step 3f searches the governed subtree. Zero downstream assertions = unenforced = REJECT.

**Failure 3: Accepted non-observable invariants**

Reviewer saw "Product invariants: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

How to avoid: Step 3b asks "Is this observable from the user's perspective?"

</failure_modes>

<success_criteria>

Audit is complete when:

- [ ] `/contextualizing` invoked — `<SPEC_TREE_CONTEXT>` marker present
- [ ] PDR read — all sections identified
- [ ] Content classification: every statement classified as product behavior or flagged
- [ ] Invariant quality: each invariant checked for observability and falsifiability
- [ ] Compliance quality: each rule checked for verifiability and tagging
- [ ] Atemporal voice: every section checked for temporal language
- [ ] Consistency: compared against product spec and ancestor PDRs
- [ ] Downstream flow: each compliance rule searched in governed subtree
- [ ] Verdict issued: APPROVED or REJECT
- [ ] For REJECT: each finding has property, category, and detail

</success_criteria>
