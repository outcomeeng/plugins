---
name: align
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or checking spec file conformance.
  NEVER check spec conformance without this skill.
allowed-tools: Read, Glob, Grep, Skill
---

<objective>

A factual report of Spec Tree files' non-conformances to templates, atemporal voice, and content-placement rules.

</objective>

<principles>

1. **FACTS ONLY** — Report what violates which rule. Never suggest how to fix it. Never rate severity. Never say "should", "consider", or "recommend."
2. **RULES FROM UNDERSTANDING** — All conformance rules live in the understanding skill's references and templates. This skill owns zero rules. Read them at check time.
3. **STRICT CLASSIFICATION** — Only `.enabler` and `.outcome` are recognized node types. Only `.adr.md`, `.pdr.md`, and `.product.md` are recognized decision/product files. Anything else is "unrecognized."
4. **COMPLETE SCAN** — Check every `.md` file in scope. Do not skip files. Do not sample.
5. **FOUNDATION REQUIRED** — The `<SPEC_TREE_FOUNDATION>` marker must be present. Invoke `/understand` when it is absent before continuing.
6. **CHANGESET SCOPE FROM THE SHARED PRIMITIVE** — When checking downstream alignment for a branch changeset, invoke `/scope-changeset` and use `branch_scope(base, repo=repo)` from its `changeset_scope.py` API. Do not hand-roll base-ref or git-diff derivation in this skill.

</principles>

<required_references>

Invoke `/understand align` as a composed skill capability. Proceed only when it returns both a live `<SPEC_TREE_FOUNDATION>` marker and a `<SPEC_TREE_FOUNDATION_MATERIALS profile="align">` receipt. The owning skill loads these materials into the conversation; never resolve them through a cross-skill filesystem path.

**References (conformance rules):**

- `durable-map` — `<atemporal_voice>` section: temporal markers table and read-aloud test
- `what-goes-where` — `<common_misplacements>` table: content in wrong artifact type
- `node-types` — `<enabler>` and `<outcome>` sections: directory suffix classification

**Templates (structural rules):**

- `adr` — required ADR sections
- `pdr` — required PDR sections
- `product` — required product sections
- `enabler` — required enabler sections
- `outcome` — required outcome sections

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

Read the `<atemporal_voice>` section from `durable-map.md`. It provides two checking mechanisms:

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
- Reference: `(ref: atemporal_voice)`

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

Read the `<decision_to_spec_alignment>` section from `durable-map.md`. For changeset checks, use `/scope-changeset` to derive the changed-file set through `branch_scope(base, repo=repo)`.

For each changed higher-level declaration — product spec, ADR, PDR, or ancestor spec — report a finding when the changed-file set contains neither:

- the first affected lower spec or specs that receive the new truth, nor
- a `PLAN.md` in the first affected node grounding the remaining downstream implementation.

Report only the factual gap: the changed higher-level declaration, the constraining scope, and the absent lower-spec or `PLAN.md` grounding. Do not choose the downstream structure in `/align`; structural ownership questions route to `/decompose`.

</downstream_alignment_conformance>

</conformance_dimensions>

<workflow>

1. **Gate**: Invoke `/understand align` as a composed skill capability, even when a standard foundation marker is already live.
2. **Load rules**: Require the live foundation marker and `align` materials receipt, then use every named reference and template loaded by that invocation. A missing receipt is a blocked conformance check, never permission to guess or skip a rule.
3. **Scope**: Use user-specified path, or default to `spx/` in the product root. When the user asks to check a branch changeset, invoke `/scope-changeset` and derive the changed-file set from its `branch_scope(base, repo=repo)` API.
4. **Discover**: Glob `{scope}/**/*.md` to find all markdown files. Exclude `{{! file('root_guide', 'claude') !}}` and `{{! file('root_guide', 'codex') !}}` files and files inside `tests/` directories.
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
- Line {N}: "{text}" — {rule violated} (ref: atemporal_voice)

Placement:
- {finding} (ref: what-goes-where)

Downstream alignment:
- {finding} (ref: durable-map decision_to_spec_alignment)

---

{N} files checked. {M} findings across {K} files.
```

**Formatting rules:**

- Omit dimension headings (Structural / Language / Placement) when a file has no findings for that dimension
- Omit files with zero findings entirely
- If all files pass all checks: `"0 findings."`
- For unrecognized files, replace the Classification line with: `Classification: Unrecognized — {reason}`

</report_format>

<success_criteria>

The alignment report is sound when:

- Every in-scope Spec Tree artifact appears either as a classified subject with factual non-conformances or in the checked-file count with no findings.
- Every finding names the file, violated conformance dimension, and governing foundation rule or template.
- Downstream-alignment findings identify the changed higher-level declaration and the absent first-lower-spec or `PLAN.md` grounding.
- The report contains no remediation advice, severity, prioritization, or unsupported inference.
- File and finding counts reconcile with the report body.

</success_criteria>
