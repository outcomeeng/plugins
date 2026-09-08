---
name: align
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or checking spec file conformance.
  NEVER check spec conformance without this skill.
argument-hint: "[file, directory, or changed-file list]"
allowed-tools: Read, Glob, Grep, Skill
---

<objective>

A factual report of Spec Tree files' non-conformances to templates, atemporal voice, and content-placement rules — including an atemporal rewrite for each temporal-language finding and no severities or prioritization.

</objective>

<principles>

1. **FACTS AND REQUIRED REWRITES ONLY** — Report what violates which rule. Include the atemporal rewrite required for each temporal-language finding; suggest no other fix. Never rate severity. Never say "should", "consider", or "recommend."
2. **RULES FROM UNDERSTANDING** — All conformance rules live in the understanding skill's inline foundation and templates. This skill owns zero rules. Read them at check time.
3. **STRICT CLASSIFICATION** — Only the seven kinds — `.product`, `.substrate`, `.capability`, `.domain`, `.interface`, `.surface`, `.variant` — and the prior `.enabler` and `.outcome` forms a tree authored under a 3.x methodology version still carries are recognized node kinds. Only `.adr.md`, `.pdr.md`, `{slug}.spec.md`, `{slug}.outcome.md`, and the prior forms `{slug}.md` and `*.product.md` are recognized files. Anything else is "unrecognized."
4. **COMPLETE SCAN** — Check every `.md` file in scope. Do not skip files. Do not sample.
5. **FOUNDATION REQUIRED** — The `<SPEC_TREE_FOUNDATION>` marker must be present. If absent, invoke `spec-tree:understand` before continuing.
6. **CHANGESET SCOPE FROM THE SHARED PRIMITIVE** — When checking downstream alignment for a branch changeset, consume the supplied changed-file set derived through `/scope-changeset`. Do not hand-roll base-ref or git-diff derivation in this skill.

</principles>

<required_references>

Invoke `spec-tree:understand` and use its live inline foundation. Read the conditional templates in full before checking conformance:

- Live `/understand` `<atemporal_voice>` and `<decision_to_spec_alignment>`
- Live `/understand` `<assertion_types>` — the five assertion types and their canonical headings
- `${CLAUDE_SKILL_DIR}/../understand/references/artifact-placement.md` `<common_misplacements>` — a conditional reference, read in full
- Live `/understand` `<files_in_a_node>` — the canonical node shape, including the skip targets it declares
- Live `/understand` `<identity_and_kinds>` and `<product_scope>` — the seven kinds, their openings, and containment
- `${CLAUDE_SKILL_DIR}/../understand/templates/decisions/decision-name.adr.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/decisions/decision-name.pdr.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/product/product-name.spec.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/nodes/substrate-name.spec.md`, `capability-name.spec.md`, `domain-name.spec.md`, `interface-name.spec.md`, `surface-name.spec.md`, and `variant-name.spec.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/records/node-name.outcome.md`

</required_references>

<file_classification>

Classify each `.md` file in scope by its filename extension or parent directory suffix:

| Pattern                                              | Classification | Template                                                       |
| ---------------------------------------------------- | -------------- | -------------------------------------------------------------- |
| `*.adr.md`                                           | ADR            | `decision-name.adr.md`                                         |
| `*.pdr.md`                                           | PDR            | `decision-name.pdr.md`                                         |
| `*.spec.md` at the tree root or inside `*.product/`  | Product        | `product-name.spec.md`                                         |
| Spec file inside `*.substrate/` directory            | Substrate      | `substrate-name.spec.md`                                       |
| Spec file inside `*.capability/` directory           | Capability     | `capability-name.spec.md`                                      |
| Spec file inside `*.domain/` directory               | Domain         | `domain-name.spec.md`                                          |
| Spec file inside `*.interface/` directory            | Interface      | `interface-name.spec.md`                                       |
| Spec file inside `*.surface/` directory              | Surface        | `surface-name.spec.md`                                         |
| Spec file inside `*.variant/` directory              | Variant        | `variant-name.spec.md`                                         |
| `*.outcome.md` inside a node directory               | Outcome record | `node-name.outcome.md`                                         |
| `*.product.md` (prior form)                          | Product        | `product-name.spec.md`                                         |
| Spec file inside `*.enabler/` directory (prior form) | Enabler        | `capability-name.spec.md` — the same opening                   |
| Spec file inside `*.outcome/` directory (prior form) | Outcome        | none — report the hypothesis as belonging in an outcome record |
| Any other `.md` file                                 | Unrecognized   | None                                                           |

**Spec file** means the file whose name matches the directory slug: `auth.spec.md` inside `10-auth.capability/`, or `auth.md` inside `10-auth.enabler/` in the prior form. Other `.md` files in the directory (like `CLAUDE.md` and `AGENTS.md`) are not spec files — skip them.

**Unrecognized** includes directories with suffixes like `.feature` or `.story`. These are not Spec Tree node kinds. Report the classification failure as a finding.

**Files to skip entirely:**

- `CLAUDE.md` and `AGENTS.md` files (agent guides, not specs)
- Files inside `tests/` directories (test code, not specs)
- `ISSUES.md` files, and any `PLAN.md` a tree authored under a 3.x version still carries (stale-prone coordination notes, not spec artifacts)
- Files inside `spx/local/` directory (skill overlays, not spec artifacts)
- Files inside an `evals/` directory sitting directly under a node directory (the co-located `[eval]` evidence lane the canonical node shape in live `/understand` `<files_in_a_node>` declares, not spec artifacts); an `evals/` directory anywhere else stays in scope
- Files inside a `knowledge/` directory sitting directly under a node directory or the product root (knowledge bundles the canonical node shape in live `/understand` `<files_in_a_node>` declares, not spec artifacts); a `knowledge/` directory anywhere else stays in scope

</file_classification>

<conformance_dimensions>

<structural_conformance>

Compare each classified file's `##` headings against its template's `##` headings.

**Report as findings:**

- **Missing section**: Template has `## Purpose` but file does not
- **Name mismatch**: File has `## Problem` where template expects `## Purpose`
- **Unrecognized assertion type**: Assertion heading not in the five types defined by live `/understand` `<assertion_types>` (Scenarios, Mappings, Conformance, Properties, Compliance)

**Do NOT report:**

- Extra sections beyond the template (specs may have product-specific additions)
- Missing optional sections (templates mark optional sections with "Only include if...")

</structural_conformance>

<ancestor_decision_conformance>

For each classified output-kind spec, including the prior forms, invoke `/contextualize` on the spec's canonical full node path and compare the spec against every applicable ADR and PDR in the resulting context. A governing decision wins over the spec.

**Report as findings:**

- The spec path and incompatible declaration
- The conflicting ADR or PDR's full path and governing rule
- Reference: the full `spx/.../*.adr.md` or `spx/.../*.pdr.md` path

**Do NOT report:**

- A decision cited only by `ISSUES.md` or another coordination note
- A lower-layer test or implementation mismatch as a decision contradiction

</ancestor_decision_conformance>

<language_conformance>

Use the live `/understand` `<atemporal_voice>` section. It provides two checking mechanisms:

**A. Temporal markers table** — The left column lists specific phrases to find. Scan every line for matches.

**B. Read-aloud test** — "Read any sentence aloud. If it would sound wrong after the work is done, it's temporal." Apply to each non-template sentence.

**Report as findings:**

- Line number, the temporal text, which rule it violates (specific marker or read-aloud test)
- Reference: `(ref: atemporal_voice)`

**Do NOT report:**

- Template placeholder text (e.g., `{1-3 sentences: what concern...}`)
- Content inside code fences
- Content inside HTML comments

</language_conformance>

<placement_conformance>

Read the `<common_misplacements>` section of `/understand` `references/artifact-placement.md`. For each row, check whether the file contains content that belongs elsewhere.

**Key signals:**

| Signal in file                              | Wrong location    | Correct location                 |
| ------------------------------------------- | ----------------- | -------------------------------- |
| Architecture choice or technical approach   | Spec              | ADR                              |
| Product decision or user guarantee          | Spec              | PDR                              |
| A condition only real use settles           | Spec, ADR, or PDR | The output node's outcome record |
| Implementation detail (code patterns, APIs) | Spec              | Code                             |
| "How to build it"                           | Spec              | ADR or code                      |
| Cross-cutting invariant                     | Child spec        | Ancestor spec                    |

**Report as findings:**

- File, approximate location, what content was found, where it belongs per the table
- Reference: `(ref: common_misplacements)`

</placement_conformance>

<downstream_alignment_conformance>

Use the live `/understand` `<decision_to_spec_alignment>` section. For changeset checks, use the exact changed-file set derived through `/scope-changeset`. Stop and request that derived set when it is absent; never derive git scope inside `/align`.

For each changed higher-level declaration — product spec, ADR, PDR, or ancestor spec — report a finding when the changed-file set contains neither:

- the first affected lower spec or specs that receive the new truth, nor
- a Change, referenced from the changeset or its commit message, carrying the remaining downstream evidence or implementation work.

Report only the factual gap: the changed higher-level declaration, the constraining scope, and the absent lower-spec or Change grounding. Do not choose the downstream structure in `/align`; structural ownership questions route to `/decompose`.

</downstream_alignment_conformance>

</conformance_dimensions>

<failure_modes>

**Evidence specialization reported as duplication.** Claude reported child `[test]` rules over concrete workflow-observability helpers as duplicates of marketplace-wide ancestor semantic-evidence rules. The finding collapsed deterministic falsification at a narrow code surface into semantic judgment at a broad scope, so removing the child rules would have weakened the evidence chain. Compare both content and evidence mechanism before reporting duplication: same-content and same-evidence repetition is misplaced, while child `[test]` concretizing ancestor `[audit]` is valid specialization.

</failure_modes>

<workflow>

1. **Gate**: Check the conversation for a live `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `spec-tree:understand` and resume only after it emits the marker.
2. **Load rules**: Read every inline leaf and sibling-relative template named in `<required_references>`.
3. **Scope**: Read `$ARGUMENTS` as the complete scope input. When it names one Markdown file, use that file directly; when it names a directory, use that directory; when it is empty, default to `spx/` in the product root. For a branch changeset, consume the exact changed-file set supplied in `$ARGUMENTS` after derivation through `/scope-changeset`; stop with that requirement when the set is absent.
4. **Discover**: For a file scope, use that file directly. For a directory scope, glob `{scope}/**/*.md`. For a changeset scope, use every Markdown path in the supplied changed-file set directly. In every mode, exclude `CLAUDE.md` and `AGENTS.md`, `PLAN.md`, `ISSUES.md`, files inside `tests/`, files inside `spx/local/`, files inside an `evals/` directory sitting directly under a node directory, and files inside a `knowledge/` directory sitting directly under a node directory or the product root.
5. **Classify**: Map each file to its artifact type per `<file_classification>`.
6. **Check each file**:
   - If classified: run structural, language, and placement checks; for an output-kind spec, also run ancestor-decision conformance through `/contextualize`
   - If unrecognized: report classification failure, then run language check only (language rules apply to all text)
7. **Check downstream alignment for changesets**: For changed product specs, ADRs, PDRs, and ancestor specs, report missing first affected lower specs or Change grounding.
8. **Report**: Emit findings grouped by file path per `<report_format>`.
9. **Summary**: End with counts.

</workflow>

<report_format>

```text
## Alignment Report: {scope}

### {file path}
Classification: {type}

Structural:
- {finding}

Decision alignment:
- {finding} (ref: {full decision path})

Language:
- Line {N}: "{text}" — {rule violated} (ref: atemporal_voice) → Atemporal: "{rewrite}"

Placement:
- {finding} (ref: common_misplacements)

Downstream alignment:
- {finding} (ref: /understand decision_to_spec_alignment)

---

{N} files checked. {M} findings across {K} files.
```

**Formatting rules:**

- Omit dimension headings (Structural / Decision alignment / Language / Placement / Downstream alignment) when a file has no findings for that dimension
- Omit files with zero findings entirely
- If all files pass all checks: `"{N} files checked. 0 findings across 0 files."`
- For unrecognized files, replace the Classification line with: `Classification: Unrecognized — {reason}`

</report_format>

<success_criteria>

- [ ] Every in-scope Markdown artifact is either represented by a finding or included in the report's checked-file count; declared skip targets are absent
- [ ] Every finding names the full file path, artifact classification or failure, violated authoritative rule, and applicable conformance dimension
- [ ] Every classified node spec is checked against all applicable governing ADRs/PDRs, and every contradiction finding names the full decision path
- [ ] Every temporal-language finding includes the source line, temporal text, governing atemporal-voice rule, and a concrete atemporal rewrite
- [ ] Placement findings preserve valid evidence-mechanism specialization and report only content misplaced under `/understand` `references/artifact-placement.md` `<common_misplacements>`
- [ ] A changeset report identifies every changed higher-level declaration lacking both first-affected lower-spec alignment and Change grounding
- [ ] Finding and file counts in the summary equal the report body
- [ ] The report contains no severity, prioritization, or repair guidance beyond required atemporal rewrites

</success_criteria>
