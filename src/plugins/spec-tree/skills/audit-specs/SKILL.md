---
name: audit-specs
description: >-
  Spec-node audit methodology — judges one output or variant spec against the
  node-spec form, covering section structure, atemporal voice, and per-assertion
  tag fitness.
argument-hint: "<node-spec-file-path>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git branch --show-current:*)
---

<objective>

A verdict on one output or variant spec, including prior enabler/outcome forms — APPROVED or REJECTED, with findings naming the section or assertion, rule, and evidence for section structure, atemporal voice, or declaration form and tag fitness.

</objective>

<constraints>

**VERIFICATION TYPE MUST FIT THE CLAIM.**

The canonical template distinguishes untagged authoring declarations directly under `## Assertions` from routed assertions. Drafts may coexist with routed subsections and receive all applicable declaration-quality checks without missing-tag or missing-heading findings. For routed assertions, apply the foundation's tag and malleability rules. `/verify` selects the verification type; after test is selected, `/test` selects the test assertion type. Two checks decide selected-tag fitness:

- Under a `[test]` tag, the assertion type (scenario, mapping, conformance, property, compliance) fits the claim's quantifier. A universal claim (ALWAYS / NEVER / "for all" / "for every" / "no input") is never `scenario`, because a scenario proves one case and cannot establish a claim about every case; `scenario` fits only a single existential interaction.
- The tag is reachable for the claim's subject. A claim whose subject is the content of an authored prose or documentation artifact — text the product authors and maintains in a document, not executable behavior — is never `[test]`. Behavioral evidence cannot verify it: the only evidence available reads the authored text and asserts on it, which proves the prose was authored, not that code behaves — whether the read is direct or laundered through test infrastructure. Such a claim's tag is `[eval]` or `[audit]`.

A required tag missing from a routed assertion, an unsupported bare mechanism tag, a duplicate tag, an assertion type the `/test` router would not produce, or `[test]` on a prose-content claim is a finding. Declaration approval establishes no evidence completeness, implementation correctness, or Passing state for untagged claims.

**HEADINGS DESCRIBE CLAIM SHAPE.**

The headings under `## Assertions` group claims by shape independently of verification type. `### Scenarios` holds specific existential interactions. `### Mappings`, `### Conformance`, `### Properties`, and `### Compliance` hold their corresponding universal claim shapes. Classify the assertion text before considering its tag: a `Given … when … then …` assertion is an existential scenario under every verification type and is mismatched under `### Compliance`; an `ALWAYS:` or `NEVER:` assertion is universal and belongs under `### Compliance` unless its content establishes a mapping, conformance rule, or property. A universal ALWAYS/NEVER rule remains under `### Compliance` when its verification type is `[audit]` or `[eval]`; the heading does not assign the test-only compliance assertion type. A verification-type heading such as `### Test`, `### Eval`, or `### Audit` is outside the node-template shape and is a `heading-mismatch` finding.

**ATEMPORAL VOICE.**

A node states product truth. "The status rollup reports failing when any child fails" — not "We changed the rollup to propagate failures."

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. No middle ground.

**ARTIFACT BOUNDARY.**

Decision-record form (ADR/PDR) is audited by `/audit-adr` and `/audit-pdr`; test-evidence quality is audited by `/audit-tests`. This audit checks the node spec's own form, not its tests or its decisions.

- NEVER modify the node spec under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS judge each assertion's verification type against `/verify` and each test assertion type against `/test` — never accept a present tag as valid by its mere presence.
- ALWAYS name the section or assertion, the violated rule, and the evidence in every REJECT finding.
- NEVER issue a finding the cited rule does not support — drop an unbacked finding rather than reject the node for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Bind the required node-spec path, preserving spaces within it: `$ARGUMENTS` supplies it when that argument is non-empty; when it is empty, the path is the one the request text carries, and the empty substitution binds nothing. If the request carries no path, run `git branch --show-current` for metadata and emit the `<verdict_format>` JSON with `target: ""`, `overall: "REJECTED"`, and all three property rows marked `FAIL`. Each row carries a `missing-target` finding with severity `REJECT`, location `input`, evidence naming the empty input, and a message naming the required node-spec path. Stop before context loading or artifact inspection.

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`, then invoke `/contextualize` on the directory containing the node spec. Read the kind's canonical template beneath that marker's resolved absolute template directory; derive current openings, front matter, and tag forms from it. For a prior enabler/outcome artifact, apply the prior grammar the foundation admits. Reject a product target as `unsupported-target`: product specs carry no assertions and belong to review. Run `git branch --show-current` for metadata. Do not proceed without the foundation, context, and required template; report an unavailable template as `template-missing`.

</step>

<step name="read_node">

**Step 2: Read the node**

Read the node spec. Identify its kind, opening, required front matter, `## Assertions` section, and each assertion's placement and optional tag. Current output kinds use their canonical template's opening; a variant uses its parent's kind. Prior enabler/outcome openings retain their admitted three-clause forms.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Verify three structural properties:

1. The opening and required front matter match the canonical kind template. Prior enablers retain `PROVIDES … SO THAT … CAN …`; prior outcomes retain `WE BELIEVE THAT … WILL … CONTRIBUTING TO …`. A missing required opening clause is `malformed-kind-statement`; missing required front matter is `missing-frontmatter`.
2. An `## Assertions` section contains at least one assertion. Specific untagged declarations may appear directly under it without a heading. Tagged assertions require the template's routed grouping. An empty assertion section is `missing-assertions`.
3. Each claim-shape heading (`### Scenarios`, `### Mappings`, `### Conformance`, `### Properties`, `### Compliance`) holds at least one assertion, and every assertion under it has the heading's claim shape independently of its verification-type tag. Classify explicit forms first: `Given … when … then …` is a scenario and belongs only under `### Scenarios`; `ALWAYS:` and `NEVER:` are universal and belong under `### Compliance` unless their content establishes a mapping, conformance rule, or property. A `### Scenarios` heading whose assertions are universal is mismatched; a `### Compliance` heading whose assertions are universal remains valid with `[test]`, `[eval]`, or `[audit]`; a `### Compliance` heading containing a `Given … when … then …` assertion is mismatched; and a verification-type heading such as `### Audit` is unsupported.

**No kind statement or no `## Assertions` section → REJECT — "missing-section." A kind statement that differs from its template → REJECT — "malformed-kind-statement." An empty, unsupported, or claim-mismatched heading → REJECT — "heading-mismatch." A draft assertion's absent heading is valid.**

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

1. An untagged assertion directly under `## Assertions` is an authoring declaration; check its specificity and falsifiability without selecting evidence. For routed assertions, apply the foundation's malleability rule and canonical tag forms: test, eval, and probe carry paths; audit carries its rule slug, or the admitted pathless form for a toolchain without slug support. Missing required tags, duplicate or unsupported tags, and path-bearing mechanisms without a path are `invalid-tag`.
2. Under `[test]`, the assertion type fits the claim's quantifier — apply the quantifier rule from `<constraints>` (a universal is never `scenario`). Reject a type the `/test` router would not produce; do not relitigate a choice the router leaves open between equally valid types.
3. The tag is reachable for the claim's subject. When the claim's subject is the content of an authored prose or documentation artifact rather than executable behavior, `[test]` is unreachable — its only evidence reads the authored text and asserts on it (directly or through a fixture or harness that exposes or reads the artifact), proving the prose was authored rather than that code behaves. The tag belongs in `[eval]` (a graded judgment over the producer's structured verdict) or `[audit]` (a semantic constraint).

**A required tag missing from a routed assertion, a duplicate tag, or an unsupported bare mechanism tag → REJECT — "invalid-tag." A `[test]` assertion type that contradicts the claim's quantifier → REJECT — "evidence-type-mismatch." `[test]` on an authored-prose claim → REJECT — "prose-coupling." An unfalsifiable draft → REJECT — "unfalsifiable-assertion."**

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings. If any property fails: REJECTED. Otherwise: APPROVED.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The `overall` is `APPROVED` iff every property row is `PASS`; otherwise it is `REJECTED`. A required property that cannot be evaluated is a `FAIL` row with a `REJECT` finding naming the missing evidence. Findings carry severity `REJECT` for blocking violations and `WARNING`/`INFO` otherwise.

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
          "location": "<section or assertion>",
          "rule": "<violation pattern>",
          "evidence": "<quoted artifact evidence>",
          "message": "<one-line detail>",
          "severity": "REJECT | WARNING | INFO"
        }
      ]
    },
    { "name": "atemporal-voice", "status": "PASS | FAIL", "findings": [] },
    { "name": "tag-fitness", "status": "PASS | FAIL", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Every finding carries the section or assertion in `location`, the violation pattern in `rule` (`missing-target`, `unsupported-target`, `template-missing`, `missing-frontmatter`, `missing-section`, `missing-assertions`, `malformed-kind-statement`, `heading-mismatch`, `temporal-voice`, `invalid-tag`, `evidence-type-mismatch`, `unfalsifiable-assertion`, or `prose-coupling`), the quoted artifact basis in `evidence`, a one-line `message`, and `severity`. A passing row carries an empty `findings` array.

</verdict_format>

<failure_modes>

**Failure 1: Passed a `[test]` claim about a document's prose**

Claude read an assertion — "the skill body states the three-gate vocabulary ([test])" — and passed it because a `[test]` tag was present and pointed at a file. The only evidence such a claim admits reads the authored body and asserts a substring of it, so it proves the prose was typed, not that code behaves. The tag belongs in `[eval]` or `[audit]`. The coupling is identical whether the test reads the body directly or through a harness constant or reader helper — full-chain, the claim still verifies prose.

How to avoid: Step 5 check 3 — when the claim's subject is the content of an authored prose or documentation artifact, `[test]` is unreachable. Reject it as "prose-coupling" and remediate to `[eval]` or `[audit]`.

**Failure 2: Passed a universal claim tagged `scenario`**

Claude saw a `### Compliance` assertion — a universal ALWAYS/NEVER claim — tagged `([test](… scenario …))` and passed it because the assertion type named one of the five. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified.

How to avoid: Step 5 check 2 verifies the assertion type fits the quantifier. Reject a universal tagged `scenario`, and any type the router would not produce — without relitigating a choice the router leaves open between equally valid types.

**Failure 3: Rejected universal audit rules under `### Compliance`**

Claude read the evidence node's universal `[audit]` rules under `### Compliance` and rejected them as `heading-mismatch` because audit assertions carry no assertion type. That conflated the heading's claim-shape grouping with the test-only compliance assertion type and contradicted the canonical node templates.

How to avoid: Step 3 judges the heading from the claim's quantifier and form independently of its verification-type tag. Keep universal ALWAYS/NEVER rules under `### Compliance` with `[test]`, `[eval]`, or `[audit]`; reject verification-type headings such as `### Audit` instead.

**Failure 4: Passed an existential scenario under `### Compliance`**

Claude read a `Given … when … then …` assertion under `### Compliance` and approved the node because the assertion carried `[eval]`. The tag described how the verdict was established; it did not change the assertion from a specific existential interaction into a universal rule.

How to avoid: Step 3 classifies explicit assertion form before verification type. Treat every `Given … when … then …` assertion as a scenario and reject it under any heading other than `### Scenarios` with `heading-mismatch`.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every spec-node rule was judged with none skipped — claim-shape heading structure independent of verification type, atemporal voice, and per-assertion tag fitness (coverage-complete).
- The verdict states an overall APPROVED/REJECTED, every property row carrying its determination, with no assertion left unevaluated.
- Each REJECT finding is falsifiable: it names the section or assertion, the violated rule, and the evidence — the malformed kind statement, the empty or mismatched heading, the temporal phrase, the invalid tag, the quantifier-mismatched assertion type, or the prose-coupled `[test]`.
- The same node spec yields the same verdict.

</success_criteria>
