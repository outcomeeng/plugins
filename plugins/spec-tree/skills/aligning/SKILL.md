---
name: aligning
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or checking spec file conformance.
  NEVER check spec conformance without this skill.
allowed-tools: Read, Glob, Grep
---

<objective>

Check Spec Tree files for conformance to templates, atemporal voice, and content placement rules. Report non-conformances as facts. Do not suggest fixes, rate severity, or prioritize findings.

</objective>

<quick_start>

1. Verify `<SPEC_TREE_FOUNDATION>` marker is present — if not, invoke `/understanding` first
2. Read all references and templates from the understanding skill's directory
3. Glob `spx/**/*.md` (or user-specified scope)
4. Classify each file, check against three dimensions, report findings

</quick_start>

<principles>

1. **FACTS ONLY** — Report what violates which rule. Never suggest how to fix it. Never rate severity. Never say "should", "consider", or "recommend."
2. **RULES FROM UNDERSTANDING** — All conformance rules live in the understanding skill's references and templates. This skill owns zero rules. Read them at check time.
3. **STRICT CLASSIFICATION** — Only `.enabler` and `.outcome` are recognized node types. Only `.adr.md`, `.pdr.md`, `.prd.md`/`.product.md` are recognized decision/product files. Anything else is "unrecognized."
4. **COMPLETE SCAN** — Check every `.md` file in scope. Do not skip files. Do not sample.
5. **FOUNDATION REQUIRED** — The `<SPEC_TREE_FOUNDATION>` marker must be present. If absent, stop and instruct the user to invoke `/understanding` first.

</principles>

<required_references>

**References (conformance rules):**

- `${CLAUDE_SKILL_DIR}/../understanding/references/durable-map.md` — `<atemporal_voice>` section: temporal markers table and read-aloud test
- `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md` — `<common_misplacements>` table: content in wrong artifact type
- `${CLAUDE_SKILL_DIR}/../understanding/references/node-types.md` — `<enabler>` and `<outcome>` sections: directory suffix classification

**Templates (structural rules):**

- `${CLAUDE_SKILL_DIR}/../understanding/templates/decisions/decision-name.adr.md` — required ADR sections
- `${CLAUDE_SKILL_DIR}/../understanding/templates/decisions/decision-name.pdr.md` — required PDR sections
- `${CLAUDE_SKILL_DIR}/../understanding/templates/product/product-name.product.md` — required product sections
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/enabler-name.md` — required enabler sections
- `${CLAUDE_SKILL_DIR}/../understanding/templates/nodes/outcome-name.md` — required outcome sections

</required_references>

<file_classification>

Classify each `.md` file in scope by its filename extension or parent directory suffix:

| Pattern                                 | Classification | Template                  |
| --------------------------------------- | -------------- | ------------------------- |
| `*.adr.md`                              | ADR            | `decision-name.adr.md`    |
| `*.pdr.md`                              | PDR            | `decision-name.pdr.md`    |
| `*.prd.md` or `*.product.md`            | Product        | `product-name.product.md` |
| Spec file inside `*.enabler/` directory | Enabler        | `enabler-name.md`         |
| Spec file inside `*.outcome/` directory | Outcome        | `outcome-name.md`         |
| Any other `.md` file                    | Unrecognized   | None                      |

**Spec file** means the file whose name matches the directory slug. Example: `auth.md` inside `10-auth.enabler/`. Other `.md` files in the directory (like `CLAUDE.md`) are not spec files — skip them.

**Unrecognized** includes directories with suffixes like `.capability`, `.feature`, `.story`. These are not Spec Tree node types. Report the classification failure as a finding.

**Files to skip entirely:**

- `CLAUDE.md` files (project configuration, not specs)
- Files inside `tests/` directories (test code, not specs)
- `PLAN.md` and `ISSUES.md` files (non-durable escape hatches, not spec artifacts)
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

- Extra sections beyond the template (specs may have project-specific additions)
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

</conformance_dimensions>

<workflow>

1. **Gate**: Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If absent, stop: "Invoke `/understanding` first."
2. **Load rules**: Read all references and templates listed in `<required_references>` from the understanding skill's directory.
3. **Scope**: Use user-specified path, or default to `spx/` in the project root.
4. **Discover**: Glob `{scope}/**/*.md` to find all markdown files. Exclude `CLAUDE.md` files and files inside `tests/` directories.
5. **Classify**: Map each file to its artifact type per `<file_classification>`.
6. **Check each file**:
   - If classified: run structural, language, and placement checks
   - If unrecognized: report classification failure, then run language check only (language rules apply to all text)
7. **Report**: Emit findings grouped by file path per `<report_format>`.
8. **Summary**: End with counts.

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

- [ ] `<SPEC_TREE_FOUNDATION>` marker verified present
- [ ] All references and templates read from understanding skill
- [ ] Every `.md` file in scope classified or reported as unrecognized
- [ ] Structural checks run against correct template per file type
- [ ] Language checks applied to all files (including unrecognized)
- [ ] Placement checks applied to all classified files
- [ ] Report contains only factual findings — no suggestions, no severity, no "should"
- [ ] Summary counts emitted

</success_criteria>
