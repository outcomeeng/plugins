---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions.
argument-hint: "<pdr-file-path>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git branch --show-current:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A verdict on one PDR against the PDR evidence model — APPROVED or REJECTED, with findings on touched text naming the section, rule, and evidence for content classification, property quality, declaration form and tag fitness, atemporal voice, or consistency with the product spec and ancestor PDRs, and every other finding returned as `filed`.

</objective>

<constraints>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

**PRODUCT BEHAVIOR, NOT ARCHITECTURE.**

PDRs govern what the product does, behavior that its users experience. "Sessions expire after 1 hour" is product behavior. "Sessions use JWT with 1-hour TTL" is architecture. If the content describes HOW something is built rather than WHAT users observe, it belongs in an ADR.

**ATEMPORAL VOICE.**

PDRs state atemporal product truth without historical context. No references to past behavior or events.

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. No middle ground.

- NEVER modify the PDR under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS read the PDR evidence model before judging — derive the rule set from it, never from memory.
- ALWAYS name the location, the violated rule, and the evidence in every `blocking` finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the PDR for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` form; `${CLAUDE_SKILL_DIR}/references/rule-catalog.md` defines the rule identifiers.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Bind the required PDR path, preserving spaces within it: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the path is the one the request text carries, and the empty substitution binds nothing. If the request carries no path, run `git branch --show-current` for metadata and emit the `<verdict_format>` JSON with `target: ""`, `overall: "REJECTED"`, and all five property rows marked `FAIL`. Each row carries a `missing-target` finding with severity `blocking`, unit `input`, locations `["input"]`, evidence naming the empty input, and a message naming the required PDR path. Stop before context loading or artifact inspection.

Use skill `product-tree:understand` when the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`. Read `decisions/decision-name.pdr.md` beneath that marker's resolved absolute template directory, then use skill `product-tree:contextualize` on the directory containing the PDR. Derive declaration form and required tags from that canonical template. Run `git branch --show-current` to populate verdict metadata without granting broader shell authority.

The product document used below is the product spec loaded by `/contextualize` in its product-level context step. Use that spec's declared audience and interaction surfaces for content classification.

Do not proceed without live `<PRODUCT_TREE_FOUNDATION>` and `<PRODUCT_TREE_CONTEXT>` markers for the PDR directory.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit. Identify its sections: the opening decision statement, Rationale, Product properties, and Verification.

Resolve the touched text of the PDR as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, so Steps 3 to 7 can classify each finding.

Record an absent `## Verification` section as a `missing-section` finding in the `tag-validity` row, marking that row `FAIL`. Name the expected section and identify its absence as evidence. Continue the remaining checks so the verdict covers every evaluable property; an unenforceable PDR cannot receive `APPROVED`.

</step>

<step name="audit_content">

**Step 3: Content classification**

First, read the product document loaded in Step 1 and name its declared audience and the interaction surfaces through which that audience operates the product. Then read every statement in the PDR and classify it by the evidence model's content classification, judging "observable" against that audience:

| Content type                       | Belongs in     | Finding if in PDR                                      |
| ---------------------------------- | -------------- | ------------------------------------------------------ |
| Observable product behavior        | PDR            | Correct                                                |
| Observable non-functional property | PDR (property) | Correct                                                |
| Technology choice                  | ADR            | `architecture-content`                                 |
| Implementation approach            | ADR or code    | `architecture-content`                                 |
| Data structure or schema           | ADR            | `architecture-content`                                 |
| Performance implementation         | ADR            | `architecture-content` (a guarantee is a PDR property) |

Record each `architecture-content` finding in the `content-classification` row.

</step>

<step name="audit_properties">

**Step 4: Property quality**

Judge each product property against the evidence model's observable, falsifiable, and stable criteria. Stability covers failure and boundary conditions; never silently limit a guarantee to the successful case.

A non-observable or unfalsifiable property is a `non-observable-property` finding, and an unstable property is an `unstable-property` finding. Record either violation in `property-quality` and mark that row `FAIL`. Name the property and the context that breaks the guarantee; a stability finding requires evidence, and an unevaluable criterion follows `<verdict_format>`'s missing-evidence rule.

</step>

<step name="audit_verification">

**Step 5: Per-rule verification tag validity**

Rules live under `## Verification`. Preserve Step 2's failed `tag-validity` row when the section is absent; an empty rule loop never clears that finding. If the section contains no rules, mark `tag-validity` as `FAIL` with `missing-verification-rules`. An untagged rule directly under the section has the canonical authoring form and may coexist with routed subsections. For every such rule, identify its subject, the observable condition it constrains, and a concrete observation that would violate it. Reject a vague, ambiguous, or unfalsifiable rule with `invalid-draft-rule` in `property-quality`, mark that row `FAIL`, and quote the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Select no evidence type or tag during these checks; an absent draft tag alone causes no finding.

A tagged rule requires its matching routed subsection. When `### Testing` contains rules, use skill `product-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, emit a `test-standards-unavailable` finding and a failed `tag-validity` row. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the PDR during this audit.

For each routed rule, judge tag validity and assertion-type fit as the evidence model's tag validity states. Under `### Testing`, apply the loaded foundation's assertion-type definitions and the shared litmus to the declared claim and tag: reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion, and do not choose among compatible types or require executable evidence for a declaration.

A routed rule with a missing, unsupported, duplicate, repeated-slug, or subsection-mismatched tag, or one that is unverifiable or vague, is an `invalid-tag` finding in `tag-validity`; mark the row `FAIL`, quote the rule, and identify the missing observable condition or ambiguous criterion. An assertion type that contradicts the claim's shape is an `assertion-type-mismatch` finding.

Apply content classification, property quality, voice, and consistency to draft and routed declarations alike. Approval establishes declaration quality only; it supplies no evidence result, implementation claim, or Passing state for an untagged rule.

</step>

<step name="audit_voice">

**Step 6: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (`temporal-voice`)           | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

Any temporal language in any section is a `temporal-voice` finding.

</step>

<step name="audit_consistency">

**Step 7: Consistency**

Compare the PDR against:

1. **Product spec** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

A contradiction with the product spec or an ancestor PDR is a `consistency-violation` finding. A statement that overlaps a sibling ADR's architecture concern is an `architecture-content` finding, judged under Step 3.

</step>

<step name="verdict">

**Step 8: Issue verdict**

Classify every finding per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text keeps severity `blocking`; every other finding becomes `filed`. If any property row holds a `blocking` finding: REJECTED. Otherwise: APPROVED, whatever `filed` findings the rows carry.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The skill's `overall` is `APPROVED` iff every property row is `PASS`; otherwise it is `REJECTED`. A required property that cannot be evaluated is a `FAIL` row with a `blocking` finding naming the missing evidence. Findings within each row carry severity `blocking` for violations on touched text and `filed` for a finding outside touched text. A `filed` finding fails no row and additionally carries `baseRefEvidence`, and `issuesEntry` (`path`, `heading`).

```json
{
  "schema_version": 1,
  "skill": "audit-pdr",
  "target": "<pdr-file-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "content-classification",
      "status": "PASS | FAIL",
      "findings": [
        {
          "rule": "<rule-id>",
          "severity": "blocking | filed",
          "locations": ["<section, property, or rule text>"],
          "evidence": "<quoted artifact evidence>",
          "message": "<one-line detail>"
        }
      ]
    },
    { "name": "property-quality", "status": "PASS | FAIL", "findings": [] },
    { "name": "tag-validity", "status": "PASS | FAIL", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL", "findings": [] },
    { "name": "consistency", "status": "PASS | FAIL", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding is keyed `<pdr-file-path>:<rule-id>` and carries `rule` (the `<rule-id>`), `severity`, `locations` (every location in the PDR where that rule is violated), `evidence` (the quoted artifact evidence), and `message` (the one-line detail). Every `<rule-id>` comes from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, and a finding names no identifier outside it. A passing row carries an empty `findings` array or only `filed` findings.

</verdict_format>

<failure_modes>

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

Why it failed: Claude treated structural completeness as proof of correct content classification.

How to avoid: Step 3 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

Why it failed: Claude treated an implementation detail measurable by a specialist as a guarantee observable by the product's users.

How to avoid: Step 4 asks "Is this falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw a `### Testing` rule "ALWAYS: every export conforms to RFC 4180 ([scenario])" and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the tag should be `mapping`, `conformance`, `property`, or `compliance`. The mismatch is `assertion-type-mismatch`, not `invalid-tag`.

How to avoid: Step 5 reads the quantifier first and separates a quantifier mismatch from a structural tag problem.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 3 reads the product document's declared audience first and judges "observable" against it.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every PDR rule was judged with none skipped — content classification, property quality (observability, falsifiability, and stability), per-rule tag validity and assertion-type fit, atemporal voice, and consistency (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no rule left unevaluated.
- Each `blocking` finding lies on touched text, and every finding outside touched text appears as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.
- Each `blocking` finding is falsifiable: it names the location, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable, unfalsifiable, or unstable property, absent verification section or rules, the unverifiable rule or mismatched tag, the temporal phrase, or the contradicted product spec or ancestor PDR.
- An absent or empty Verification section fails `tag-validity`; an unmet property-quality criterion fails `property-quality`. Neither condition can disappear through an empty iteration or receive an overall `APPROVED` verdict.
- The same PDR yields the same verdict.

</success_criteria>
