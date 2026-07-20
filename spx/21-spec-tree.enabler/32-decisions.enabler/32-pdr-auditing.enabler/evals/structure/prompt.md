<!-- Generated from the complete producer set:
src/plugins/spec-tree/skills/audit-pdr/SKILL.md
src/plugins/spec-tree/skills/audit-pdr/references/pdr-evidence-model.md
-->

Apply the complete producer below to the supplied PDR. Return only the producer's structured JSON verdict.

<pre><code>
<!-- Producer: src/plugins/spec-tree/skills/audit-pdr/SKILL.md -->

---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, per-rule tag validity,
  atemporal voice, and consistency with ancestor decisions.
model: sonnet
allowed-tools: Read, Grep, Glob, Skill, Bash(git branch --show-current:*)
---

<objective>

A verdict on one PDR against the PDR evidence model — APPROVED, or REJECTED with each finding naming the section, the violated rule, and the evidence. Findings fall in five categories: content classification (observable product behavior, never architecture), property quality (observable and falsifiable), per-rule tag validity and assertion-type fit, atemporal voice, and consistency with the product spec and ancestor PDRs.

</objective>

<prerequisites>

Read the PDR evidence model's boundary guidance for content classification, property quality, and tag validity before auditing: `${CLAUDE_SKILL_DIR}/references/pdr-evidence-model.md`

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

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent, then invoke `/contextualize` on the directory containing the PDR. Run `git branch --show-current` to populate verdict metadata without granting broader shell authority.

Do not proceed without live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers for the PDR directory.

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
   - under `### Testing` → a `/test`-routed assertion type: one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])` — the rule governs a skill, agent, or classifier whose output has a parseable contract;
   - under `### Audit` → `([audit])` — the rule governs a Spec Tree decision, spec, skill, or agent that admits no deterministic test or graded eval.

   An unsupported bare mechanism tag, a tag that disagrees with its subsection, a missing tag, or more than one tag is invalid.
2. Under `### Testing`, the assertion type fits the claim's shape per the `/test` router. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") takes `mapping`, `conformance`, `compliance`, or `property` — never `scenario`, which fits only a single existential interaction. Reject a type the router would not produce for the claim; do not relitigate a choice the router leaves open between equally-valid types.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot carry a meaningful evidence tag.

**A rule with no subsection tag, a tag disagreeing with its subsection, a bare mechanism tag in place of an assertion type, or more than one tag → REJECT — "invalid-tag." An assertion type that contradicts the claim's shape (a universal tagged `scenario` is the clearest case) → REJECT — "assertion-type-mismatch."**

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

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The skill's `overall` is `APPROVED` iff every property row is `PASS`; otherwise it is `REJECTED`. A required property that cannot be evaluated is a `FAIL` row with a `REJECT` finding naming the missing evidence. Findings within each row carry severity `REJECT` for blocking violations and `WARNING`/`INFO` for non-blocking observations.

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
          "location": "<section or property>",
          "rule": "<violation pattern>",
          "evidence": "<quoted artifact evidence>",
          "message": "<one-line detail>",
          "severity": "REJECT | WARNING | INFO"
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

Each finding carries `location` (the section or property the objective requires it to name), `rule` (the violation pattern, e.g., `architecture-content`, `invalid-tag`, `assertion-type-mismatch`, `temporal-language`), `evidence` (the quoted artifact evidence), `message` (the one-line detail), and `severity`.

</verdict_format>

<failure_modes>

**Failure 1: Approved a PDR full of architecture decisions**

Claude saw a well-structured PDR with a clear decision statement and a Verification section, and approved it. The decision statement said "The system uses PostgreSQL with row-level locking for concurrent session management." That is an architecture decision, not a product decision. Users don't care about PostgreSQL or row-level locking — they care that concurrent sessions work.

How to avoid: Step 3 classifies every statement. "Would a user be able to determine this?" is the test.

**Failure 2: Accepted non-observable properties**

Claude saw "Product properties: Database connections are pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "The product handles at least 500 concurrent users without degradation."

How to avoid: Step 4 asks "Is this falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw a `### Testing` rule "ALWAYS: every export conforms to RFC 4180 ([scenario])" and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the tag should be `mapping`, `conformance`, `property`, or `compliance`. The mismatch is `assertion-type-mismatch`, not `invalid-tag`.

How to avoid: Step 5 reads the quantifier first. A universal (ALWAYS / NEVER / "for all" / "no input") tagged `scenario` is `assertion-type-mismatch`; a structural tag problem — bare mechanism tag, wrong subsection, missing tag, more than one tag — is `invalid-tag`.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 3 reads the product document's declared audience first and judges "observable" against it. A git topology, a path layout, or a CLI behavior the audience operates is product behavior. Reserve `architecture-content` for what the audience never operates — the tool's internal algorithm, in-memory data structures, persisted schema, and library choices — which stays an ADR concern even for a tooling product.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every PDR rule was judged with none skipped — content classification, property quality, per-rule tag validity and assertion-type fit, atemporal voice, and consistency (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no rule left unevaluated.
- Each REJECT finding is falsifiable: it names the section, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable or unfalsifiable property, the mismatched tag, the temporal phrase, or the contradicted product spec or ancestor PDR.
- The same PDR yields the same verdict.

</success_criteria>


<!-- Producer: src/plugins/spec-tree/skills/audit-pdr/references/pdr-evidence-model.md -->

<overview>

Detailed boundary guidance for PDR content classification, property quality, and tag validity. Read this before auditing any PDR.

The audit skill owns the complete five-property workflow, including atemporal voice and consistency. This reference defines the three properties whose classification boundaries require extended examples.

</overview>

<contents>

- `<content_classification>` — observable product behavior versus architecture, grounded in the product document's declared audience and interaction surfaces, with tooling-product examples
- `<property_quality>` — observable, falsifiable, stable product properties
- `<tag_validity>` — per-rule verification tag and assertion-type fit

</contents>

<content_classification>

PDRs govern observable product behavior. Every statement must pass the user test: "Would the product document's declared audience observe or operate this?" The product document the audit loads names the audience and the interaction surfaces through which it operates the product; "observable" is judged against that declaration, never a fixed end-user-application assumption.

**Product behavior (belongs in PDR):**

- "Sessions expire after 1 hour of inactivity" — user observes expiry
- "Search results appear within 500ms" — user observes latency
- "The product supports 4 theme variants" — user selects themes
- "Uploaded files are limited to 10MB" — user hits the limit
- "Export produces valid CSV" — user opens the file

**Architecture (belongs in ADR):**

- "Sessions use JWT with 1-hour TTL" — user doesn't know about JWT
- "Search uses Elasticsearch" — user doesn't know the engine
- "Themes are implemented via CSS custom properties" — user doesn't see CSS
- "File validation uses multer middleware" — user doesn't see middleware
- "CSV generation uses fast-csv library" — user doesn't see the library

**Boundary cases:**

| Statement                                         | Verdict                                 | Reasoning                           |
| ------------------------------------------------- | --------------------------------------- | ----------------------------------- |
| "The API returns JSON responses"                  | PDR if user-facing API, ADR if internal | Depends on who the "user" is        |
| "Pages load in under 2 seconds"                   | PDR                                     | User observes load time             |
| "Response time is O(n log n)"                     | ADR                                     | User observes speed, not complexity |
| "The system handles 500 concurrent users"         | PDR                                     | User experiences the capacity       |
| "The database handles 500 concurrent connections" | ADR                                     | User doesn't see connections        |
| "Dark mode is the default theme"                  | PDR                                     | User sees the default               |
| "Dark mode uses L=0.03 OKLCH background"          | ADR                                     | User sees dark, not the color math  |

**Tooling and infrastructure products.** When the product document declares an audience that operates the product through a command-line, filesystem, version-control, or other infrastructure surface — engineers, agents, operators — the surface that audience runs and inspects is the product's observable behavior. Naming a command, a path, or a version-control concept is not by itself architecture; the audience operates exactly those things.

**Tooling product behavior (belongs in PDR):**

- "The tool recognizes two on-disk layouts: a single working tree and a worktree pool" — the audience inspects the layout on disk
- "Running the build command in a clean checkout produces a `dist/` directory" — the audience runs the command and sees the output
- "A shared state directory resolves to the same path from every worktree in a pool" — the audience relies on the resolved path
- "An unknown subcommand exits non-zero with a usage message" — the audience observes the exit code and message

**Tooling architecture (belongs in ADR), even though the product is tooling:**

- "The layout detector caches results in an in-memory map keyed by path" — the audience never sees the cache
- "The classifier reads metadata in a single pass and skips re-validating unchanged entries" — internal algorithm of the tool
- "State is persisted as newline-delimited JSON records" — a serialization schema the audience does not operate
- "The CLI is built on the Cobra command framework" — a library choice invisible to the audience

| Statement                                            | Verdict | Reasoning                                       |
| ---------------------------------------------------- | ------- | ----------------------------------------------- |
| "The repository uses a bare-repo worktree pool"      | PDR     | The audience inspects the layout on disk        |
| "Layout detection queries a version-control config"  | ADR     | The detection mechanism is internal to the tool |
| "A new worktree is created detached at the base tip" | PDR     | The audience observes the worktree state        |
| "Worktree records are held in a linked list"         | ADR     | The data structure is invisible to the audience |

**The escalation test:** When a statement is ambiguous, ask: "If this changed, would the declared audience file a bug report or a feature request?" If yes → PDR. If only an implementer of the tool — never the audience — would notice → ADR.

</content_classification>

<property_quality>

Product properties are guarantees users can rely on. They must be:

1. **Observable** — a user can perceive whether the property holds
2. **Falsifiable** — a scenario exists where it's violated
3. **Stable** — the property holds across all contexts, not just happy paths

**Good properties:**

| Property                                   | Observable                    | Falsifiable                         | Stable                 |
| ------------------------------------------ | ----------------------------- | ----------------------------------- | ---------------------- |
| "All pages load in under 2 seconds"        | User times page load          | Load a page, measure > 2s           | Applies to all pages   |
| "Theme selection persists across sessions" | User returns, sees same theme | Change theme, close browser, reopen | Applies always         |
| "Uploaded files never exceed stated limit" | User gets rejection           | Upload 11MB to 10MB limit           | Applies to all uploads |

**Bad properties:**

| Property                          | Problem                                  |
| --------------------------------- | ---------------------------------------- |
| "Good user experience"            | Not falsifiable — what counts as "good"? |
| "Database connections are pooled" | Not user-observable                      |
| "Code follows best practices"     | Not falsifiable — whose practices?       |
| "The system is scalable"          | Not falsifiable without a threshold      |
| "Fast response times"             | Not falsifiable — how fast is "fast"?    |

**Fixing bad properties:**

- "Good user experience" → "Core user flows complete in under 3 clicks"
- "The system is scalable" → "The system handles 500 concurrent users without degradation"
- "Fast response times" → "API responses return within 200ms at p95"

</property_quality>

<tag_validity>

Verification rules are the enforceable part of a PDR, grouped under `## Verification` into `### Testing`, `### Eval`, and `### Audit` by verification type. Each rule carries a tag valid for its subsection, and a `### Testing` rule's assertion type fits the claim:

1. **Tag matching its subsection** — under `### Testing`, a `/test`-routed assertion type (`scenario`/`mapping`/`conformance`/`property`/`compliance`); under `### Eval`, `([eval])`; under `### Audit`, `([audit])`. An unsupported bare mechanism tag, a missing tag, more than one tag, or a tag that disagrees with its subsection is `invalid-tag`.
2. **Assertion-type fit** — a `### Testing` rule's assertion type fits the claim's quantifier per the `/test` router; a universal `ALWAYS`/`NEVER` claim tagged `scenario` is `assertion-type-mismatch`, since a single case cannot establish a universal.

A rule earns a sound tag only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot carry a meaningful evidence tag.

**Well-formed verification rules:**

```markdown
## Verification

### Testing

- ALWAYS: all text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes ([property])
- ALWAYS: export files conform to RFC 4180 CSV format ([conformance])
- NEVER: expose internal database IDs in user-facing URLs ([property])
- NEVER: display raw error messages from backend services to users ([compliance])

### Audit

- ALWAYS: every theme variant is selectable from the settings surface ([audit])
```

**Ill-formed verification rules:**

```markdown
### MUST

- Provide an intuitive interface ← unverifiable
- Follow accessibility best practices ← vague (which practices? what level?)
- Be fast ← no threshold

### NEVER

- Have bugs ← not actionable
- Break ← not specific
```

**Fixing bad rules:**

- "Follow accessibility best practices" → "Meet WCAG 2.1 Level AA for all interactive components ([compliance])"
- "Be fast" → "API responses return within 200ms at p95 under normal load ([property])"

</tag_validity>

</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
