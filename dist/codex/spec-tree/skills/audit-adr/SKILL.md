---
name: audit-adr
description: >-
  ADR audit methodology — judges one ADR against the ADR evidence model,
  covering section structure, atemporal voice, and per-rule tag validity.
argument-hint: "<adr-file-path>"
allowed-tools: Read, Grep, Glob, Skill, Bash(git branch --show-current:*)
---

<objective>

A verdict on one ADR against the ADR evidence model — APPROVED or REJECTED, with findings naming the section, rule, and evidence for section structure, atemporal voice, or per-rule declaration form and tag fitness.

</objective>

<constraints>

**ARCHITECTURE BY DEFINITION.**

An ADR's content is architecture — technology choices, data structures, implementation approaches. NEVER classify ADR content as product-behavior-versus-architecture; that classification is the PDR audit's concern. Audit the ADR's form, not whether its content belongs elsewhere.

**ASSERTION TYPE MUST MATCH THE CLAIM.**

Apply the canonical template's authoring and routed forms. Untagged rules directly under `## Verification` await selection and may coexist with routed subsections; judge their specificity, structure, voice, and consistency without inventing a missing-tag finding. Rules inside routed subsections carry the template's required tag. `/verify` selects the verification type, then `/test` selects a Testing rule's assertion type. A universal claim is never `scenario`; a missing required tag inside a routed subsection, unsupported tag, duplicate tag, or quantifier mismatch remains a finding. Approval judges declaration quality and establishes no evidence result or Passing state.

**ATEMPORAL VOICE.**

ADRs state architecture truth. "The build emits one wheel per plugin" — not "We switched to per-plugin wheels because the monolith broke."

**BINARY VERDICT.**

`APPROVED` or `REJECTED`. An unavailable required inspection is a rejection with evidence naming the blocked inspection; it never becomes an approval through an unevaluated row.

**LANGUAGE COMPOSITION BOUNDARY.**

Language-specific ADR concerns — testability-in-Verification (dependency injection, no-mocking), execution-level accuracy — are composed from `/audit-<lang>-architecture` in Step 5b. The language skill judges only those concerns; this skill owns section structure, atemporal voice, and tag validity from the canonical template.

- NEVER modify the ADR under audit or any other file — this audit produces a verdict, never a fix or a commit.
- ALWAYS derive the valid section set from the canonical ADR template before judging structure — never from memory.
- ALWAYS name the section, the violated rule, and the evidence in every REJECT finding.
- NEVER issue a finding the cited rule or canonical template does not support — drop an unbacked finding rather than reject the ADR for it.

</constraints>

<audit_workflow>

<step name="load_context">

**Step 1: Load context**

Read the required ADR path from `$ARGUMENTS`, preserving spaces within the path. If the input is empty or whitespace-only, run `git branch --show-current` for metadata and emit the `<verdict_format>` JSON with `target: ""`, `overall: "REJECTED"`, and all three native rows marked `FAIL`. Each row carries a `missing-target` finding with severity `blocking`, location `input`, `observed` naming the absent target, and `expected` and `message` naming the required ADR path. Stop before context loading or artifact inspection.

Invoke `/understand` when the live `<SPEC_TREE_FOUNDATION>` marker is absent or lacks `Template root`. Read `decisions/decision-name.adr.md` beneath that marker's resolved absolute template directory. The template remains owned by `/understand`. Then invoke `/contextualize` on the directory containing the ADR. Run `git branch --show-current` to populate verdict metadata without granting broader shell authority.

The input is the ADR path alone. Derive its governing node from the containing directory, using canonical `spx/` for a product-root ADR. Retain the successful `/sync-base` result established by `/contextualize`: its `preservation` supplies the committed base and head identities and `branch_paths_after` supplies the current changeset paths. Use that context with the ADR's governed declarations and linked implementation surfaces in Step 5b; no supplied language classification is required.

Do not proceed without the canonical ADR template content and live `<SPEC_TREE_FOUNDATION>` and `<SPEC_TREE_CONTEXT>` markers.

</step>

<step name="read_adr">

**Step 2: Read the ADR**

Read the ADR under audit. Identify its sections: the opening decision statement, Rationale (optional), Invariants (optional), and Verification.

</step>

<step name="audit_structure">

**Step 3: Section structure**

Use the canonical ADR template guidance loaded in Step 1 to derive the valid section set in full — never from memory or a transcribed copy. A structural finding that contradicts the canonical template is unbacked: drop it rather than rejecting the ADR. If the template guidance cannot be loaded, reject with `template-missing` and name the blocked read.

Verify the decision is stated in the opening (no "Purpose" preamble) and a `## Verification` section is present. Rationale and Invariants are optional — Invariants appears only when the decision establishes algebraic properties.

**No decision statement, or no Verification section → REJECT — "missing-section."**

</step>

<step name="audit_voice">

**Step 4: Atemporal voice**

Check EVERY section for temporal language:

| Temporal (REJECT)                     | Atemporal (correct)             |
| ------------------------------------- | ------------------------------- |
| "We decided to use X because Y broke" | "X governs Z"                   |
| "Currently the build does X"          | "The build does X"              |
| "After profiling, we added caching"   | "Caching reduces latency for Z" |

**Any temporal language in any section → REJECT — "temporal-voice."**

</step>

<step name="audit_tag_validity">

**Step 5: Per-rule tag validity and assertion-type fit**

Read each rule's placement before judging tags. An untagged rule directly under `## Verification` has the canonical authoring form. For every such rule, identify its subject, the condition it constrains, and a concrete observation that would violate it. Reject a vague, ambiguous, or unfalsifiable rule with `invalid-draft-rule` in the `tag-validity` row, mark that row `FAIL`, and quote the rule with the missing or ambiguous criterion. For example, `ALWAYS: improve quality` fails because it names no observable condition. Check each draft rule against the decision statement and governing decisions; a contradiction also produces `invalid-draft-rule`, citing both conflicting declarations. Select no evidence type or tag during these checks.

A tagged rule must have the matching routed subsection. When `### Testing` contains rules, invoke `spec-tree:test-evidence-standards` and load its assertion-type litmus. Apply that reference and the loaded foundation's assertion-type definitions to the declared claim and tag. If the required reference cannot load, emit a blocking `test-standards-unavailable` finding and a failed `tag-validity` row. Judge declaration compatibility only; evidence completeness belongs to evidence auditing. Never invoke the mutating `/test` authoring workflow, select a replacement tag, or change the ADR during this audit.

For each routed rule:

1. The tag is valid for its subsection:
   - under `### Testing` → one of `scenario`, `mapping`, `conformance`, `property`, `compliance`;
   - under `### Eval` → `([eval])`;
   - under `### Audit` → `([audit])`.
2. Under `### Testing`, the declared assertion type is compatible with the claim's quantifier and evidence shape under the loaded foundation and shared assertion-type litmus. A universal claim cannot carry `scenario`. Reject a declared type whose required domain or oracle contradicts the claim, citing the claim and the loaded criterion; do not choose among compatible types or require executable evidence for a declaration.

An unsupported bare mechanism tag, a tag disagreeing with its subsection, a missing tag inside a routed subsection, more than one tag, or an assertion type that contradicts the claim's shape is invalid.

**A routed rule with a missing, unsupported, duplicate, or subsection-mismatched tag → REJECT — "invalid-tag." An assertion type that contradicts the claim's shape → REJECT — "assertion-type-mismatch."**

</step>

<step name="compose_language">

**Step 5b: Compose language-specific architecture concerns**

This skill owns section structure, atemporal voice, and tag validity from the canonical template. Language-specific architecture concerns — dependency injection, no-mocking, execution-level accuracy — are owned by the language audit skill, not by this one.

Classify the ADR from its governed implementation surface and the committed changeset established in Step 1. When the decision constrains no implementation language, classify it as language-neutral and skip composition. Otherwise preserve every implementation-language partition the decision constrains, including cross-language decisions; the repository's predominant language never narrows that set.

For every discovered partition, require the matching `audit-<lang>-architecture` skill and invoke it through the Skill tool with the ADR path. The language skill judges only language-specific concerns and never re-judges section structure, voice, or tags. When a language-specific ADR has no reliable partition or the required skill cannot load, append a `FAIL` row named `language-routing-unavailable` or `language-skill-unavailable` with a blocking finding.

Before consuming a composed result, validate it against the invoked skill's declared verdict contract: the schema and skill identity, matching target, every required concern row exactly once, allowed statuses, required finding fields, explanations for `NOT_APPLICABLE`, and agreement between the rows and overall result. An absent, malformed, incomplete, mismatched, or inconsistent result produces a `FAIL` row and blocking finding named `language-result-invalid`, identifying the failed contract check; accept no partial rows from that result. This boundary validates returned structure without repeating the language audit's judgment.

Append only validated rows. Qualify each composed row name with its language to preserve distinct concerns across partitions. Map its findings to this verdict's fields: retain the rule, message, observed, and expected evidence, use the child location or file as `location`, and mark findings that reject the ADR as `blocking`. A composed `FAIL` always rejects the ADR; no omitted row or empty result counts as passing coverage.

One case is not a composition failure. When the governed context establishes that the changeset itself ships the ADR's language plugin, unpublished and uninstalled in this session, no `audit-<lang>-architecture` skill can exist yet. Judge the decision directly against the skill files its rules name and the cross-language decisions, and record a row named `language-skill-unpublished` as `NOT_APPLICABLE` with the evidence establishing that case. An absent installed skill alone never establishes unpublished status.

</step>

<step name="verdict">

**Step 6: Issue verdict**

Scan all findings and native or composed rows. If any row is `FAIL`, issue `REJECTED`; otherwise issue `APPROVED`.

</step>

</audit_workflow>

<verdict_format>

Emit the verdict as a single JSON object. This JSON is the skill's entire output; never a prose or markdown verdict.

The `overall` is `APPROVED` iff every native and composed row is `PASS` or `NOT_APPLICABLE`; otherwise it is `REJECTED`. Every `NOT_APPLICABLE` row explains why its concern does not apply. A required property that cannot be evaluated is a `FAIL` row with a blocking finding naming the unavailable inspection. Findings use the audit-run severities `blocking` or `debt`; this binary ADR gate emits `blocking` for every finding that rejects the ADR.

```json
{
  "schema_version": 1,
  "skill": "audit-adr",
  "target": "<adr-file-path>",
  "overall": "APPROVED | REJECTED",
  "rows": [
    { "name": "section-structure", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "atemporal-voice", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] },
    { "name": "tag-validity", "status": "PASS | FAIL | NOT_APPLICABLE", "explanation": "<required when NOT_APPLICABLE>", "findings": [] }
  ],
  "metadata": { "branch": "<branch>" }
}
```

Each finding carries `rule`, `severity: "blocking"`, `location`, `message`, `observed`, and `expected`. Native findings use `missing-target`, `missing-section`, `temporal-voice`, `invalid-draft-rule`, `invalid-tag`, `assertion-type-mismatch`, `template-missing`, `test-standards-unavailable`, `language-routing-unavailable`, `language-skill-unavailable`, or `language-result-invalid`; validated composed findings retain the invoked skill's rule identifier.

</verdict_format>

<failure_modes>

**Failure 1: Imported the PDR content gate into an ADR audit**

Claude flagged "uses PostgreSQL with row-level locking" as architecture content that does not belong — in an ADR. An ADR's content is architecture by definition; there is no product-versus-architecture classification to run. The PDR audit's content gate has no place here.

How to avoid: The ADR audit checks form — structure, voice, tag validity. Content classification is the PDR audit's concern only.

**Failure 2: Passed a universal rule tagged `scenario`**

Claude saw a `### Testing` rule — a universal ALWAYS/NEVER claim — tagged `([scenario])`, and passed it because a tag was present and named one of the five assertion types. A scenario proves one case; it cannot establish a claim about every case, so the assertion ships unverified — phantom green. The quantifier mismatch is a deterministic error, not a matter of taste.

How to avoid: Step 5 verifies the assertion type fits the claim's shape per the `/test` router. Reject a universal tagged `scenario` (and any type the router would not produce for the claim). The one line the audit does not cross is relitigating a choice the router leaves open between equally-valid types — that, and only that, is `/test`'s to decide.

**Failure 3: Applied routed tag requirements to authoring declarations**

Claude rejected untagged authoring rules because the routed-form tag requirement was applied before verification selection. Derive the form from the artifact and canonical template. Judge every draft rule, preserve routed-rule checks, and never interpret declaration approval as evidence completeness.

</failure_modes>

<success_criteria>

The verdict is sound when:

- Every ADR rule was judged with none skipped — section structure, atemporal voice, and per-rule tag validity and assertion-type fit; when a language is in scope, the composed `/audit-<lang>-architecture` rows are judged too (coverage-complete).
- The verdict states one `APPROVED` or `REJECTED` overall determination, every native and composed row carrying `PASS`, `FAIL`, or explained `NOT_APPLICABLE`, with no rule left unevaluated.
- Each REJECT finding is falsifiable: it names the section, the violated rule, and the evidence — the missing section, the temporal phrase, or the mismatched tag.
- The same ADR yields the same verdict.

</success_criteria>
