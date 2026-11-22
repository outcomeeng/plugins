---
name: audit-specs
description: >-
  Spec-node audit methodology — judges one output or variant spec against the
  node-spec form, covering section structure, atemporal voice, and per-row
  heading fitness.
argument-hint: "<node-spec-file-path>"
allowed-tools: Read, Grep, Glob, {{! tool('use_skill') !}}, Bash(git branch --show-current:*), Bash(git merge-base:*), Bash(git diff:*)
---

<objective>

A verdict on one output or variant spec, including prior enabler/outcome forms, against the node-spec form — APPROVED or REJECTED, with findings on touched text naming the section or row, rule, and evidence for section structure, atemporal voice, or heading fitness, and every other finding returned as `filed`.

</objective>

<constraints>

**THE GROUP HEADING NAMES THE VERIFICATION TYPE.**

Every row under `## Assertions` stands under a group heading that names its verification type: `Test.Scenario`, `Test.Mapping: <slug>`, `Test.Conformance`, `Test.Property`, `Test.Compliance`, `Evaluate: <slug>`, `Probe`, or `Audit`. Read each heading as the verification type of every row under it: `### Audit: messages` heads audit rows, and `### Test.Compliance: capture` heads compliance tests. A row carries no tag, because its heading names its type and its leading slug is its one name. A tag on a row, such as `([audit])`, is an `invalid-tag` finding, and so is a slug that repeats within the spec. A row under no group heading, or under a heading that names no verification type, is a `heading-mismatch` finding.

**THE ROW'S CLAIM FITS THE TYPE ITS HEADING NAMES.**

The verification-type standard selects the verification type, and after test is selected, the test assertion-type standard selects the assertion type; Step 1 loads both. Three checks decide heading fitness:

- Under a `Test.` heading, the assertion type the heading names fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") never stands under `Test.Scenario`, because a scenario proves one case and cannot establish a claim about every case; that is an `evidence-type-mismatch` finding. A `Given … When … Then …` row is one existential interaction and stands under `Test.Scenario`; under any other `Test.` heading it is a `heading-mismatch` finding. Judge against the `/test` router without relitigating a choice it leaves open between equally valid types.
- A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — never stands under a `Test.` heading. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim is a `prose-coupling` finding; its verification belongs under `Evaluate` or `Audit`.
- A row's slug links an artifact only in the directory its heading's type names: `tests/` under a `Test.` heading, `evals/` under `Evaluate`, and `probes/` under `Probe`. An `Audit` row links no artifact. A row whose evidence does not exist yet stands with its plain slug and draws no finding. Any other link is a `slug-link-mismatch` finding.

Declaration approval establishes no evidence completeness, implementation correctness, or Passing state for a row whose slug links no evidence.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. No middle ground.

**ARTIFACT BOUNDARY.**

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality is audited by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions. NEVER classify a node's content as architecture-versus-product-behavior — that classification is the decision-record audits' concern.

- NEVER modify the node spec under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS judge each row's heading against the standards Step 1 loads — never accept a heading as fitting by its mere presence.
- ALWAYS name the section or row, the violated rule, and the evidence in every `blocking` finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the node for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` form; `${CLAUDE_SKILL_DIR}/references/rule-catalog.md` defines the rule identifiers.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Bind the required node-spec path, preserving spaces within it: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the path is the one the request text carries, and the empty substitution binds nothing. If the request carries no path, run `git branch --show-current` for metadata and emit the `<verdict_format>` JSON with `target: ""`, `overall: "REJECTED"`, and all three property rows marked `FAIL`. Each row carries a `missing-target` finding with severity `blocking`, unit `input`, locations `["input"]`, `observed` naming the empty input, and `expected` and `message` naming the required node-spec path. Stop before context loading or artifact inspection.

Use skill `product-tree:understand` when the live `<PRODUCT_TREE_FOUNDATION>` marker is absent or lacks `Template root`. Read the kind's canonical template beneath that marker's resolved absolute template directory; derive current openings and front matter from it. For a prior enabler/outcome artifact, apply the prior grammar the foundation admits. Reject a product target as `unsupported-target`: product documents carry no assertions and belong to review. Report an unavailable template as `template-missing`.

Before any audit phase, load read-only, at the snapshot the checkout holds, the complete Walk to the target spec node as the work: every ancestor spec from the root; at each level along the path, every sibling spec and each Decision Record indexed below the child the path continues through; every `ISSUES.md` along the path; the published contracts of the target's immediate children; the target's own Decision Records and spec, its Knowledge `index.md`, and its Outcome record. Then load, once, each decision a loaded spec or decision cites from another subtree. Run no command that fetches, rebases, or moves the checkout, so the audit changes no checkout state.

Use skill `product-tree:verify` for the verification-type standard and use skill `product-tree:test` for the test assertion-type standard that Step 5 applies; read them as standards and run no authoring step either skill describes. Run `git branch --show-current` for metadata. Do not proceed without the foundation, the loaded Walk, and the required template.

</step>

<step name="read_node">

**Step 2: Read the node**

Read the node spec. Identify its kind, opening, required front matter, `## Assertions` section, each group heading, and each row's leading slug, link, and claim. Current output kinds use their canonical template's opening; a variant uses its parent's kind. Prior enabler/outcome openings retain their admitted three-clause forms.

Resolve the touched text of the node spec as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, so Steps 3 to 5 can classify each finding.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Verify three structural properties:

1. The opening and required front matter match the canonical kind template. Prior enablers retain `PROVIDES … SO THAT … CAN …`; prior outcomes retain `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`. A missing or malformed opening clause is `malformed-kind-statement`; missing required front matter is `missing-frontmatter`.
2. An `## Assertions` section contains at least one row. An empty assertion section is `missing-assertions`.
3. Every row stands under a group heading that names its verification type, from the set `<constraints>` lists, and every group heading holds at least one row.

**No kind statement or no `## Assertions` section → `blocking` — "missing-section." A kind statement that differs from its template → `blocking` — "malformed-kind-statement." A row under no group heading, a heading that names no verification type, or an empty group → `blocking` — "heading-mismatch."**

</step>

<step name="audit_voice">

**Step 4: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (blocking)                   | Atemporal (correct)                |
| ------------------------------------- | ---------------------------------- |
| "We added a rollup so failures show"  | "The rollup propagates failures"   |
| "Currently the parser accepts X"      | "The parser accepts X"             |
| "After the rewrite, status derives Y" | "Status derives from test results" |

**Any temporal language in any section → `blocking` — "temporal-voice."**

</step>

<step name="audit_heading_fitness">

**Step 5: Per-row heading fitness**

For each row under `## Assertions`:

1. The row carries no tag, and its leading slug repeats nowhere in the spec.
2. Its claim fits the type its heading names — apply the quantifier rule from `<constraints>`: a universal never stands under `Test.Scenario`, and a `Given … When … Then …` row stands under no other `Test.` heading. Reject an assertion type the test assertion-type standard would not produce; do not relitigate a choice it leaves open.
3. A claim about authored prose or documentation content stands under no `Test.` heading — apply the prose-coupling rule from `<constraints>`.
4. Its slug links an artifact only in the directory its heading's type names, and an `Audit` row links none.
5. Its claim is specific and falsifiable: it names a subject, a condition, and an observation that would violate it.

**A tag on a row, or a repeated slug → `blocking` — "invalid-tag." A universal under `Test.Scenario` → `blocking` — "evidence-type-mismatch." A `Given … When … Then …` row under another `Test.` heading → `blocking` — "heading-mismatch." An authored-prose claim under a `Test.` heading → `blocking` — "prose-coupling," remediated to `Evaluate` or `Audit`. A link outside the heading type's directory, or a link on an `Audit` row → `blocking` — "slug-link-mismatch." An unfalsifiable row → `blocking` — "unfalsifiable-assertion."**

</step>

<step name="verdict">

**Step 6: Issue verdict**

Classify every finding per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text keeps severity `blocking`; every other finding becomes `filed`. If any property row holds a `blocking` finding: REJECTED. Otherwise: APPROVED, whatever `filed` findings the rows carry.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The `overall` is `APPROVED` iff every property row is `PASS`; otherwise it is `REJECTED`. A row holding only `filed` findings is `PASS`. A required property that cannot be evaluated is a `FAIL` row with a `blocking` finding naming the missing evidence. Findings use the severities `blocking`, for a violation on touched text, which rejects the node, and `filed`, for a finding outside touched text, which fails no row.

```json
{
  "schema_version": 1,
  "skill": "audit-specs",
  "target": "<node-spec-file-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    {
      "name": "section-structure",
      "status": "PASS | FAIL",
      "findings": [
        {
          "key": "<node-spec-file-path>:<rule-id>",
          "rule": "<rule-id>",
          "severity": "blocking | filed",
          "locations": ["<section or row>"],
          "message": "<one-line detail>",
          "observed": "<quoted artifact evidence>",
          "expected": "<what the rule requires>"
        }
      ]
    },
    { "name": "atemporal-voice", "status": "PASS | FAIL", "findings": [] },
    { "name": "heading-fitness", "status": "PASS | FAIL", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding is keyed `<node-spec-file-path>:<rule-id>` and carries `rule` (the `<rule-id>`), `severity`, `locations` (every section or row of the node spec where that rule is violated), `message`, `observed`, and `expected`; a `filed` finding additionally carries `key`, `baseRefEvidence`, and `issuesEntry` (`path`, `heading`). Every `<rule-id>` comes from `${CLAUDE_SKILL_DIR}/references/rule-catalog.md`, and a finding names no identifier outside it.

</verdict_format>

<failure_modes>

**Failure 1: Passed a prose claim under a `Test.` heading**

Claude read a row — "the skill body states the three-gate vocabulary" under `### Test.Compliance: body` — and passed it because the row linked a test file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The row belongs under `Evaluate` or `Audit`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 5 check 3 applies the prose-coupling rule from `<constraints>`; reject the row as "prose-coupling."

**Failure 2: Passed a universal claim under `Test.Scenario`**

Claude saw an ALWAYS/NEVER row under `### Test.Scenario: capture` and passed it because the heading named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the row ships unverified.

How to avoid: Step 5 check 2 verifies the assertion type fits the quantifier. Reject a universal under `Test.Scenario`, and any type the test assertion-type standard would not produce — without relitigating a choice it leaves open between equally valid types.

**Failure 3: Rejected an untagged Audit row, or passed a tagged one**

Claude read the 3.x tag model into a 4.0 spec. It rejected a row under `### Audit: messages` because the row carried no `[audit]` tag, and passed a row that carried `([audit])` because the tag matched the heading. In the 4.0 form the heading alone names the verification type, so the untagged row is correct and the tag is the defect.

How to avoid: `<constraints>` reads each group heading as the type of its rows. Step 5 check 1 rejects every tag on a row as `invalid-tag`, and approves an untagged row under any heading that names its type.

**Failure 4: Passed an existential scenario under `Test.Compliance`**

Claude read a `Given … When … Then …` row under `### Test.Compliance: capture` and approved the node because the heading named a test type. The row is one existential interaction; a compliance test exercises a rule against violating fixtures, so the heading names a type the claim does not fit.

How to avoid: Step 5 check 2 classifies the row's form before accepting its heading. Reject a `Given … When … Then …` row under any `Test.` heading other than `Test.Scenario` with `heading-mismatch`.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every spec-node rule was judged with none skipped — section structure with every row under a typed group heading, atemporal voice, and per-row heading fitness (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no row left unevaluated.
- Each `blocking` finding lies on touched text, and every finding outside touched text appears as `filed` with its key, `baseRefEvidence`, and `issuesEntry`.
- Each `blocking` finding is falsifiable: it names the section or row, the violated rule, and the evidence — the malformed kind statement, the ungrouped row or mismatched heading, the temporal phrase, the tag or repeated slug, the quantifier-mismatched heading, the prose claim under a `Test.` heading, or the misplaced link.
- The same node spec yields the same verdict.

</success_criteria>
