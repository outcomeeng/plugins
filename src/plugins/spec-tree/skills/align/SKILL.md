---
name: align
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or checking spec file conformance.
  NEVER check spec conformance without this skill.
argument-hint: "[path|changeset]"
allowed-tools: Read, Glob, Grep, Skill
---

<objective>

A factual report of Spec Tree files' non-conformances to templates, atemporal voice, and content-placement rules — no fixes, severities, or prioritization.

</objective>

<principles>

1. **FACTS ONLY** — Report what violates which rule. Never suggest how to fix it. Never rate severity. Never say "should", "consider", or "recommend."
2. **RULES FROM UNDERSTANDING** — Mandatory conformance rules live in the inline `/understand` foundation sections; operational references and templates supplement them. This skill owns zero rules. Read the required sources at check time.
3. **STRICT CLASSIFICATION** — Only `.enabler` and `.outcome` are recognized node types. Only `.adr.md`, `.pdr.md`, and `.product.md` are recognized decision/product files. Anything else is "unrecognized."
4. **COMPLETE SCAN** — Check every `.md` file in scope. Do not skip files. Do not sample.
5. **FOUNDATION REQUIRED** — The `<SPEC_TREE_FOUNDATION>` marker must be present. If absent, stop and instruct the user to invoke `/understand` first.
6. **CHANGESET SCOPE FROM THE SHARED PRIMITIVE** — When checking downstream alignment for a branch changeset, invoke `/scope-changeset` and use `branch_scope(base, repo)` from its `changeset_scope.py` API. Do not hand-roll base-ref or git-diff derivation in this skill.

</principles>

<required_references>

**References (conformance rules):**

- Live `/understand` `<atemporal_voice>` and `<layer_precedence>` — atemporal voice and truth-flow rules
- `/understand` operational reference `what-goes-where` — `<common_misplacements>` table: content in wrong artifact type
- Live `/understand` `<enabler>`, `<outcome>`, and `<nesting_rules>` — node classification and nesting

**Templates (structural rules):**

- `/understand` template `decision-name.adr.md` — required ADR sections
- `/understand` template `decision-name.pdr.md` — required PDR sections
- `/understand` template `product-name.product.md` — required product sections
- `/understand` template `enabler-name.md` — required enabler sections
- `/understand` template `outcome-name.md` — required outcome sections

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

**Spec file** means the file whose name matches the directory slug. Example: `auth.md` inside `10-auth.enabler/`. Other `.md` files in the directory (like `{{! file('root_guide', 'claude') !}}` and `{{! file('root_guide', 'codex') !}}`) are not spec files — skip them.

**Unrecognized** includes directories with suffixes like `.capability`, `.feature`, `.story`. These are not Spec Tree node types. Report the classification failure as a finding.

**Files to skip entirely:**

- `{{! file('root_guide', 'claude') !}}` and `{{! file('root_guide', 'codex') !}}` files (agent guides, not specs)
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
- **Unrecognized assertion type**: Assertion heading not in the five types (Scenarios, Mappings, Conformance, Properties, Compliance)

**Do NOT report:**

- Extra sections beyond the template (specs may have product-specific additions)
- Missing optional sections (templates mark optional sections with "Only include if...")

</structural_conformance>

<language_conformance>

Apply the atemporal-voice rules from the live `/understand` `<atemporal_voice>`. They provide two checking mechanisms:

**A. Temporal markers table** — The left column lists specific phrases to find. Scan every line for matches.

**B. Read-aloud test** — "Read any sentence aloud. If it would sound wrong after the work is done, it's temporal." Apply to each non-template sentence.

Common temporal patterns caught by the read-aloud test that may not appear in the markers table:

- "supersedes" / "replaces" / "deprecated" (narrates history of decisions)
- "previously" / "used to" / "was" / "has been" (past tense narration)
- "going to" / "will need to" / "plan to" (future intentions)
- "migrate" / "transition" / "phase out" (describes a journey)
- Problem framing: "Users face X" / "X is broken" / "X causes Y" (narrates a gap to fill)

**Report as findings:**

- Line number, the temporal text, which rule it violates (specific marker or read-aloud test)
- Reference: `(ref: /understand <atemporal_voice>)`

**Do NOT report:**

- Template placeholder text (e.g., `{1-3 sentences: what concern...}`)
- Content inside code fences
- Content inside HTML comments

</language_conformance>

<placement_conformance>

Read the `<common_misplacements>` table from `what-goes-where.md`. For each row, check whether the file contains content that belongs elsewhere.

**Key signals:**

| Signal in file                              | Wrong location | Correct location     |
| ------------------------------------------- | -------------- | -------------------- |
| Architecture choice or technical approach   | Spec           | ADR                  |
| Product decision or user guarantee          | Spec           | PDR                  |
| Outcome hypothesis (WE BELIEVE THAT...)     | ADR or PDR     | Outcome spec         |
| Implementation detail (code patterns, APIs) | Spec           | Code                 |
| "How to build it"                           | Spec           | ADR or code          |
| Cross-cutting invariant                     | Child spec     | Ancestor spec or PDR |

**Report as findings:**

- File, approximate location, what content was found, where it belongs per the table
- Reference: `(ref: what-goes-where)`

</placement_conformance>

<downstream_alignment_conformance>

Apply the decision-to-spec alignment rules from the live `/understand` `<decision_to_spec_alignment>`. For changeset checks, use `/scope-changeset` to derive the changed-file set through `branch_scope(base, repo)`.

For each changed higher-level declaration — product spec, ADR, PDR, or ancestor spec — report a finding when the changed-file set contains neither:

- the first affected lower spec or specs that receive the new truth, nor
- a `PLAN.md` in the first affected node grounding the remaining downstream implementation.

Report only the factual gap: the changed higher-level declaration, the constraining scope, and the absent lower-spec or `PLAN.md` grounding. Do not choose the downstream structure in `/align`; structural ownership questions route to `/decompose`.

</downstream_alignment_conformance>

</conformance_dimensions>

<workflow>

1. **Gate**: Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If absent, stop: "Invoke `/understand` first."
2. **Load rules**: Apply the live inline `/understand` `<atemporal_voice>`, `<layer_precedence>`, `<decision_to_spec_alignment>`, `<enabler>`, `<outcome>`, and `<nesting_rules>` sections, then read the operational reference and templates listed in `<required_references>`.
3. **Scope**: Read `$ARGUMENTS` as the requested path or changeset scope. When it is empty, default to `spx/` in the product root. For a branch changeset, invoke `/scope-changeset`, set the scope kind to `changeset`, and retain the complete changed-file set returned by `branch_scope(base, repo)`. For a path, set the scope kind to `path` and retain the path.
4. **Discover**: For `changeset` scope, iterate the retained changed-file set and keep its Markdown files. For `path` scope, Glob `{scope}/**/*.md`. In both modes, exclude `{{! file('root_guide', 'claude') !}}` and `{{! file('root_guide', 'codex') !}}` files and files inside `tests/` directories.
5. **Classify**: Map each file to its artifact type per `<file_classification>`.
6. **Check each file**:
   - If classified: run structural, language, and placement checks
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

Language:
- Line {N}: "{text}" — {rule violated} (ref: /understand <atemporal_voice>)

Placement:
- {finding} (ref: what-goes-where)

Downstream alignment:
- {finding} (ref: /understand <decision_to_spec_alignment>)

---

{N} files checked. {M} findings across {K} files.
```

**Formatting rules:**

- Omit dimension headings (Structural / Language / Placement) when a file has no findings for that dimension
- Omit files with zero findings entirely
- If all files pass all checks: `"0 findings."`
- For unrecognized files, replace the Classification line with: `Classification: Unrecognized — {reason}`

</report_format>

<failure_modes>

**Failure: Checked a changed higher-level declaration in isolation.** Claude reported a product spec, ADR, PDR, or ancestor spec as aligned after checking only that file's structure and language, while no first affected lower spec or node-local `PLAN.md` carried the new truth. The check missed the declaration-to-spec boundary because it treated alignment as per-file linting instead of a changeset relationship. For changeset scope, derive the changed-file set through `/scope-changeset` and apply `<downstream_alignment_conformance>` before reporting.

</failure_modes>

<success_criteria>

- The report accounts for every Markdown file in scope as classified or unrecognized, with no silent omission.
- Every finding names the exact file and location, the governing template or rule, and the observed contradiction, gap, language defect, or placement defect.
- Structural findings use the template for the classified artifact type; language findings cover every file, and placement findings cover every classified file.
- For changeset scope, every changed higher-level declaration is accounted for by aligned first affected lower specs or by a finding naming the absent lower-spec and `PLAN.md` grounding.
- Findings state facts only, with no severity, proposed fix, suggestion, or `should` wording.
- Per-file and summary counts reconcile exactly; a clean scope renders exactly `0 findings.`
- Repeating alignment over the same file contents and scope yields the same classifications, findings, and counts.

</success_criteria>
