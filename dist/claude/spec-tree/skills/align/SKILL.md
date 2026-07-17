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
3. **STRICT CLASSIFICATION** — Only `.enabler` and `.outcome` are recognized node types. Only `.adr.md`, `.pdr.md`, and `.product.md` are recognized decision/product files. Anything else is "unrecognized."
4. **COMPLETE SCAN** — Check every `.md` file in scope. Do not skip files. Do not sample.
5. **FOUNDATION REQUIRED** — The `<SPEC_TREE_FOUNDATION>` marker must be present. If absent, invoke `spec-tree:understand` before continuing.
6. **CHANGESET SCOPE FROM THE SHARED PRIMITIVE** — When checking downstream alignment for a branch changeset, consume the supplied changed-file set derived through `/scope-changeset`. Do not hand-roll base-ref or git-diff derivation in this skill.

</principles>

<required_references>

Invoke `spec-tree:understand` and use its live inline foundation. Read the conditional templates in full before checking conformance:

- Live `/understand` `<atemporal_voice>` and `<decision_to_spec_alignment>`
- Live `/understand` `<assertion_types>` — the five assertion types and their canonical headings
- Live `/understand` `<common_misplacements>`
- Live `/understand` `<enabler>` and `<outcome>`
- `${CLAUDE_SKILL_DIR}/../understand/templates/decisions/decision-name.adr.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/decisions/decision-name.pdr.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/product/product-name.product.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/nodes/enabler-name.md`
- `${CLAUDE_SKILL_DIR}/../understand/templates/nodes/outcome-name.md`

</required_references>

<file_classification>

Classify each `.md` file in scope by its filename extension or parent directory suffix:

| Pattern                                 | Classification | Template                  |
| --------------------------------------- | -------------- | ------------------------- |
| `*.adr.md`                              | ADR            | `decision-name.adr.md`    |
| `*.pdr.md`                              | PDR            | `decision-name.pdr.md`    |
| `*.product.md`                          | Product        | `product-name.product.md` |
| Spec file inside `*.enabler/` directory | Enabler        | `enabler-name.md`         |
| Spec file inside `*.outcome/` directory | Outcome        | `outcome-name.md`         |
| Any other `.md` file                    | Unrecognized   | None                      |

**Spec file** means the file whose name matches the directory slug. Example: `auth.md` inside `10-auth.enabler/`. Other `.md` files in the directory (like `CLAUDE.md` and `AGENTS.md`) are not spec files — skip them.

**Unrecognized** includes directories with suffixes like `.capability`, `.feature`, `.story`. These are not Spec Tree node types. Report the classification failure as a finding.

**Files to skip entirely:**

- `CLAUDE.md` and `AGENTS.md` files (agent guides, not specs)
- Files inside `tests/` directories (test code, not specs)
- `PLAN.md` and `ISSUES.md` files (stale-prone coordination notes, not spec artifacts)
- Files inside `spx/local/` directory (skill overlays, not spec artifacts)

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

For each classified enabler or outcome spec, invoke `/contextualize` on the spec's canonical full node path and compare the spec against every applicable ADR and PDR in the resulting context. A governing decision wins over the spec.

**Report as findings:**

- The spec path and incompatible declaration
- The conflicting ADR or PDR's full path and governing rule
- Reference: the full `spx/.../*.adr.md` or `spx/.../*.pdr.md` path

**Do NOT report:**

- A decision cited only by `PLAN.md`, `ISSUES.md`, or another coordination note
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

Read the live `/understand` `<common_misplacements>` table. For each row, check whether the file contains content that belongs elsewhere.

**Key signals:**

| Signal in file                              | Wrong location | Correct location |
| ------------------------------------------- | -------------- | ---------------- |
| Architecture choice or technical approach   | Spec           | ADR              |
| Product decision or user guarantee          | Spec           | PDR              |
| Outcome hypothesis (WE BELIEVE THAT...)     | ADR or PDR     | Outcome spec     |
| Implementation detail (code patterns, APIs) | Spec           | Code             |
| "How to build it"                           | Spec           | ADR or code      |
| Cross-cutting invariant                     | Child spec     | Ancestor spec    |

**Report as findings:**

- File, approximate location, what content was found, where it belongs per the table
- Reference: `(ref: common_misplacements)`

</placement_conformance>

<downstream_alignment_conformance>

Use the live `/understand` `<decision_to_spec_alignment>` section. For changeset checks, use the exact changed-file set derived through `/scope-changeset`. Stop and request that derived set when it is absent; never derive git scope inside `/align`.

For each changed higher-level declaration — product spec, ADR, PDR, or ancestor spec — report a finding when the changed-file set contains neither:

- the first affected lower spec or specs that receive the new truth, nor
- a `PLAN.md` in the first affected node grounding the remaining downstream implementation.

Report only the factual gap: the changed higher-level declaration, the constraining scope, and the absent lower-spec or `PLAN.md` grounding. Do not choose the downstream structure in `/align`; structural ownership questions route to `/decompose`.

</downstream_alignment_conformance>

</conformance_dimensions>

<failure_modes>

**Evidence specialization reported as duplication.** Claude reported child `[test]` rules over concrete workflow-observability helpers as duplicates of marketplace-wide ancestor `[review]` rules. The finding collapsed deterministic falsification at a narrow code surface into semantic judgment at a broad scope, so removing the child rules would have weakened the evidence chain. Compare both content and evidence mechanism before reporting duplication: same-content and same-evidence repetition is misplaced, while child `[test]` concretizing ancestor `[audit]` or legacy `[review]` is valid specialization.

</failure_modes>

<workflow>

1. **Gate**: Check the conversation for a live `<SPEC_TREE_FOUNDATION>` marker. If absent, invoke `spec-tree:understand` and resume only after it emits the marker.
2. **Load rules**: Read every inline leaf and sibling-relative template named in `<required_references>`.
3. **Scope**: Read `$ARGUMENTS` as the complete scope input. When it names one Markdown file, use that file directly; when it names a directory, use that directory; when it is empty, default to `spx/` in the product root. For a branch changeset, consume the exact changed-file set supplied in `$ARGUMENTS` after derivation through `/scope-changeset`; stop with that requirement when the set is absent.
4. **Discover**: For a file scope, use that file directly. For a directory scope, glob `{scope}/**/*.md`. For a changeset scope, use every Markdown path in the supplied changed-file set directly. In every mode, exclude `CLAUDE.md` and `AGENTS.md`, `PLAN.md`, `ISSUES.md`, files inside `tests/`, and files inside `spx/local/`.
5. **Classify**: Map each file to its artifact type per `<file_classification>`.
6. **Check each file**:
   - If classified: run structural, language, and placement checks; for an enabler or outcome spec, also run ancestor-decision conformance through `/contextualize`
   - If unrecognized: report classification failure, then run language check only (language rules apply to all text)
7. **Check downstream alignment for changesets**: For changed product specs, ADRs, PDRs, and ancestor specs, report missing first affected lower specs or first-affected-node `PLAN.md` grounding.
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
- [ ] Placement findings preserve valid evidence-mechanism specialization and report only content misplaced under live `/understand` `<common_misplacements>`
- [ ] A changeset report identifies every changed higher-level declaration lacking both first-affected lower-spec alignment and first-affected-node `PLAN.md` grounding
- [ ] Finding and file counts in the summary equal the report body
- [ ] The report contains no severity, prioritization, or repair guidance beyond required atemporal rewrites

</success_criteria>
