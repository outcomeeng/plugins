<!-- Generated from the complete producer set:
dist/claude/product-tree/skills/audit-pdr/SKILL.md
dist/claude/product-tree/skills/audit-pdr/references/pdr-evidence-model.md
-->

Apply the complete producer below to the supplied PDR. Return only the producer's structured JSON verdict.

<pre><code>
<!-- Producer: dist/claude/product-tree/skills/audit-pdr/SKILL.md -->

---
name: audit-pdr
description: >-
  PDR audit methodology — judges one PDR against the PDR evidence model,
  covering content classification, property quality, declaration form and tag
  validity, atemporal voice, and consistency with ancestor decisions.
argument-hint: "<pdr-file-path>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git branch --show-current:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A verdict on one PDR against the PDR evidence model — APPROVED or REJECTED, with findings on touched text naming the section, rule, and evidence for content classification, property quality, declaration form and tag validity, atemporal voice, or consistency with the product document and ancestor PDRs, and every other finding returned as `filed`.

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

Use skill `product-tree:understand` when the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`. Read `decisions/decision-name.pdr.md` beneath that marker's resolved absolute template directory, then use skill `product-tree:contextualize` on the directory containing the PDR. Derive the declaration form from that canonical template. Run `git branch --show-current` to populate verdict metadata without granting broader shell authority.

The product document used below is the one `/contextualize` loads in its product-level context step. Use that document's declared audience and interaction surfaces for content classification.

Do not proceed without live `<PRODUCT_TREE_FOUNDATION>` and `<PRODUCT_TREE_CONTEXT>` markers for the PDR directory.

</step>

<step name="read_pdr">

**Step 2: Read the PDR**

Read the PDR under audit. Identify its parts: the opening with its optional DEFINES paragraph and its GOVERNS paragraph, and Verification.

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

Judge the behavior the CAN RELY ON line names against the evidence model's observable, falsifiable, and stable criteria. Stability covers failure and boundary conditions; never silently limit a guarantee to the successful case.

A non-observable or unfalsifiable behavior is a `non-observable-property` finding, and an unstable behavior is an `unstable-property` finding. Record either violation in `property-quality` and mark that row `FAIL`. Name the behavior and the context that breaks the guarantee; a stability finding requires evidence, and an unevaluable criterion follows `<verdict_format>`'s missing-evidence rule.

</step>

<step name="audit_verification">

**Step 5: Declaration form and tag validity**

Rules live under `## Verification`. Preserve Step 2's failed `tag-validity` row when the section is absent; an empty rule loop never clears that finding. If the section contains no rules, mark `tag-validity` as `FAIL` with `missing-verification-rules`.

Check the declaration form the canonical template states. A PDR whose opening lacks a GOVERNS paragraph, whose mapping rule is not its own `### Mapping: <slug>` subsection holding one sentence and a table, whose group holds more than seven rules, or that holds text outside its opening, a rule, or a table is a `declaration-form` finding in `tag-validity`; mark the row `FAIL`, quote the offending text, and name the form it breaks.

A rule directly under the section, outside any group, has the canonical authoring form and may coexist with groups. For every such rule, identify its subject, the observable condition it constrains, and a concrete observation that would violate it. Reject a vague, ambiguous, or unfalsifiable rule with `invalid-draft-rule` in `property-quality`, mark that row `FAIL`, and quote the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Select no evidence type during these checks.

A rule carries no tag, because its group heading names its verification type and its leading slug is its one name. A rule that carries a tag, or whose slug repeats within the PDR, is an `invalid-tag` finding in `tag-validity`; mark the row `FAIL` and quote the rule.

When a group heading names an assertion type, use skill `product-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to each rule's claim and its group's type. If the required reference cannot load, emit a `test-standards-unavailable` finding and a failed `tag-validity` row. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Reject a type whose required domain or oracle contradicts the claim as `assertion-type-mismatch`, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration. Never invoke the mutating `/test` authoring workflow, select a replacement group, or change the PDR during this audit.

Apply content classification, property quality, voice, and consistency to ungrouped and grouped declarations alike. Approval establishes declaration quality only; it supplies no evidence result, implementation claim, or Passing state for an ungrouped rule.

</step>

<step name="audit_voice">

**Step 6: Atemporal voice**

Check the opening and EVERY rule for temporal language:

| Temporal (`temporal-language`)        | Atemporal (correct)                                |
| ------------------------------------- | -------------------------------------------------- |
| "We discovered that users ask for X"  | "Users value X"                                    |
| "Currently the product does X"        | "The product does X"                               |
| "After customer feedback, we decided" | "The product does X to meet customer expectations" |
| "The existing implementation lacks"   | (omit — PDR doesn't reference code)                |

Any temporal language in the opening or a rule is a `temporal-language` finding.

</step>

<step name="audit_consistency">

**Step 7: Consistency**

Compare the PDR against:

1. **Product document** — Does the PDR contradict the product's scope or assertions?
2. **Ancestor PDRs** — Does the PDR contradict constraints from PDRs higher in the tree?
3. **Sibling ADRs** — Does the PDR overlap with architecture concerns?

A contradiction with the product document or an ancestor PDR is a `consistency-violation` finding. A statement that overlaps a sibling ADR's architecture concern is an `architecture-content` finding, judged under Step 3.

</step>

<step name="verdict">

**Step 8: Issue verdict**

Classify every finding per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text keeps severity `blocking`; every other finding becomes `filed`. If any property row holds a `blocking` finding: REJECTED. Otherwise: APPROVED, whatever `filed` findings the rows carry.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The skill's `overall` is `APPROVED` iff every property row is `PASS`; otherwise it is `REJECTED`. A required property that cannot be evaluated is a `FAIL` row with a `blocking` finding naming the missing evidence. Findings within each row carry severity `blocking` for violations on touched text and `filed` for a finding outside touched text. A `filed` finding fails no row and additionally carries `key` (`<pdr-file-path>:<rule-id>`), `baseRefEvidence`, and `issuesEntry` (`path`, `heading`).

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

Claude saw "CAN RELY ON database connections pooled with a maximum of 50 connections." This is an implementation detail observable only by a DBA, not by users. The PDR version would be "CAN RELY ON the product handling at least 500 concurrent users without degradation."

Why it failed: Claude treated an implementation detail measurable by a specialist as a guarantee observable by the product's users.

How to avoid: Step 4 asks "Is the behavior the CAN RELY ON line names falsifiable from the user's perspective?"

**Failure 3: Approved a universal claim tagged as a scenario**

Claude saw the rule "csv-format: ALWAYS: every export conforms to RFC 4180." in a `### Scenario: export` group and approved it because the prose read like a concrete interaction. `ALWAYS` is a universal claim, and a single scenario cannot establish a claim about every case — the group should be `Mapping`, `Conformance`, `Property`, or `Compliance`. The mismatch is `assertion-type-mismatch`, not `invalid-tag`.

How to avoid: Step 5 reads the quantifier first and separates a quantifier mismatch from a structural form problem.

**Failure 4: Flagged a tooling product's observable state as architecture**

Claude audited a PDR for a command-line tool whose product document declares its audience operates the product through a CLI and an on-disk layout. The PDR described the repository layout the audience inspects on disk and the version-control state it observes. Claude saw git commands and filesystem paths, applied the end-user-application reflex ("a user does not see git"), and rejected the statements as `architecture-content`. That is a false positive: the declared audience operates exactly that surface, so the layout is observable product behavior.

How to avoid: Step 3 reads the product document's declared audience first and judges "observable" against it.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every PDR rule was judged with none skipped — content classification, property quality (observability, falsifiability, and stability), declaration form, tag absence, slug uniqueness and assertion-type fit, atemporal voice, and consistency (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no rule left unevaluated.
- Each `blocking` finding lies on touched text, and every finding outside touched text appears as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.
- Each `blocking` finding is falsifiable: it names the location, the violated rule, and the evidence — the architecture content wrongly placed, the non-observable, unfalsifiable, or unstable behavior, absent verification section or rules, the unverifiable rule, the broken declaration form, the tag or repeated slug, the mismatched assertion type, the temporal phrase, or the contradicted product document or ancestor PDR.
- An absent or empty Verification section fails `tag-validity`; an unmet property-quality criterion fails `property-quality`. Neither condition can disappear through an empty iteration or receive an overall `APPROVED` verdict.
- The same PDR yields the same verdict.

</success_criteria>


<!-- Producer: dist/claude/product-tree/skills/audit-pdr/references/pdr-evidence-model.md -->

<overview>

Detailed boundary guidance for PDR content classification, property quality, and declaration form and tag validity. Read this before auditing any PDR.

The audit skill owns the complete five-property workflow, including atemporal voice and consistency. This reference defines the three properties whose classification boundaries require extended examples.

</overview>

<contents>

- `<content_classification>` — observable product behavior versus architecture, grounded in the product document's declared audience and interaction surfaces, with tooling-product examples
- `<property_quality>` — observable, falsifiable, stable behavior the CAN RELY ON line names
- `<tag_validity>` — declaration form, tag absence, slug uniqueness, and assertion-type fit

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

The behavior the CAN RELY ON line names is a guarantee users can rely on. It must be:

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

Derive the form from the canonical PDR template. A rule directly under `## Verification`, outside any group, awaits selection and receives the same clarity and falsifiability checks. The checks below apply to the declaration; authoring approval supplies no evidence result:

1. **Declaration form** — the PDR opens with a GOVERNS paragraph, writes each mapping rule as its own `### Mapping: <slug>` subsection holding one sentence and a table, keeps each group to at most seven rules, and holds no text outside its opening, a rule, or a table. A violation is `declaration-form`.
2. **No tag, one slug** — a rule carries no tag, because its group heading names its verification type, and its leading slug is its one name and repeats nowhere in the PDR. A tag on a rule, or a repeated slug, is `invalid-tag`.
3. **Assertion-type fit** — a rule's assertion type, named by its group heading, fits the claim's quantifier per the `/test` router; a universal `ALWAYS`/`NEVER` claim in a `### Scenario` group is `assertion-type-mismatch`, since a single case cannot establish a universal.

A rule is sound only when it is verifiable (a test, eval, or audit skill can determine pass/fail) and specific (two independent reviewers would agree on the verdict); an unverifiable or vague rule cannot sit in any group.

**Well-formed verification rules:**

```markdown
## Verification

### Property: contrast

- contrast-floor: ALWAYS: all text/background color pairs maintain ΔL ≥ 0.80 contrast in all themes.
- no-internal-ids: NEVER: expose internal database IDs in user-facing URLs.

### Conformance: export

- csv-format: ALWAYS: export files conform to RFC 4180 CSV format.

### Audit

- theme-variants-selectable: ALWAYS: every theme variant is selectable from the settings surface.
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

- "Follow accessibility best practices" → "wcag-aa: ALWAYS: all interactive components meet WCAG 2.1 Level AA", in a `### Compliance` group
- "Be fast" → "response-latency: ALWAYS: API responses return within 200ms at p95 under normal load", in a `### Property` group

</tag_validity>

</code></pre>

The PDR input (JSON-encoded):

```json
{input_json}
```
