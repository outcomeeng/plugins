---
name: aligning
description: >-
  ALWAYS invoke this skill when reviewing, auditing, or checking spec file conformance.
  NEVER check spec conformance without this skill.
allowed-tools: Read, Glob, Grep, Bash
---

<objective>

Check Spec Tree files for conformance to templates, atemporal voice, content placement rules, and downstream alignment after higher-level declarations change. Report non-conformances as facts. Do not suggest fixes, rate severity, or prioritize findings.

</objective>

<quick_start>

1. Verify `<SPEC_TREE_FOUNDATION>` marker is present — if not, invoke `/understanding` first
2. Read all references and templates from the understanding skill's directory
3. Glob `spx/**/*.md` (or user-specified scope)
4. Classify each file, check against conformance dimensions, report findings

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

- `${CLAUDE_SKILL_DIR}/../understanding/references/durable-map.md` — `<atemporal_voice>` section: temporal markers table and read-aloud test; `<future_product_truth>` and `<decision_to_spec_alignment>` sections: higher-level changes require lower-spec alignment
- `${CLAUDE_SKILL_DIR}/../understanding/references/what-goes-where.md` — `<common_misplacements>` and `<escape_hatches>` sections: content in wrong artifact type and `PLAN.md` placement for pending node work
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

- `CLAUDE.md` files (product configuration, not specs)
- Files inside `tests/` directories (test code, not specs)
- `PLAN.md` and `ISSUES.md` files for structural, language, and placement conformance (escape hatches, not spec artifacts); downstream alignment checks may inspect whether `PLAN.md` exists
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

Read the `<future_product_truth>` and `<decision_to_spec_alignment>` sections from `durable-map.md`. These provide the same-PR alignment rule for higher-level declaration changes.

This check is a best-effort factual guard over the changed-file set. It detects missing downstream alignment when no lower spec changed under the affected scope, and missing `PLAN.md` grounding when a lower spec absorbs a higher-level declaration without same-slice tests or code. It does not prove that every directly affected lower spec was identified. The authoring or applying workflow remains responsible for enumerating every directly affected child or target spec from the product context and aligning each one.

Determine the changed file set in this order:

1. Use the user-provided changed-file list when one is provided.
2. If the repository has git metadata, use read-only git commands to list changed files against the PR base.
3. If no changed-file set is available, report that downstream alignment was not evaluated.

Classify changed files:

| Changed file kind                         | Meaning                                           |
| ----------------------------------------- | ------------------------------------------------- |
| Product spec, ADR, PDR, or ancestor spec  | Higher-level declaration changed                  |
| Spec file inside a lower node             | Candidate lower-spec alignment                    |
| Test file under the lower node's `tests/` | Candidate same-slice test implementation          |
| Non-`spx/` source file                    | Candidate same-slice code implementation          |
| `PLAN.md` in the lower node               | Pending node work is grounded for future sessions |

For each changed higher-level declaration, identify the constraining scope:

- Product spec: `spx/`
- ADR/PDR: the directory containing the decision file
- Ancestor spec: the node directory containing the spec

Report as findings:

- A changed higher-level declaration has no changed lower spec under its constraining scope in the same changed-file set. Reference: `(ref: decision_to_spec_alignment)`.
- A changed lower spec references or absorbs a changed higher-level declaration, no same-node test file and no non-`spx/` source file changed in the same set, and no `PLAN.md` exists in that lower node. Reference: `(ref: decision_to_spec_alignment)`.

Do NOT report:

- Higher-level declaration files when at least one lower spec under the constraining scope changed in the same set.
- Lower specs when same-node tests or non-`spx/` source files changed in the same set.
- Lower specs when a `PLAN.md` file exists in the lower node.

When the changed-file set includes at least one lower spec under the constraining scope, state that zero-alignment coverage was observed rather than claiming full affected-spec coverage.

</downstream_alignment_conformance>

</conformance_dimensions>

<workflow>

1. **Gate**: Check conversation for `<SPEC_TREE_FOUNDATION>` marker. If absent, stop: "Invoke `/understanding` first."
2. **Load rules**: Read all references and templates listed in `<required_references>` from the understanding skill's directory.
3. **Scope**: Use user-specified path, or default to `spx/` in the product root.
4. **Discover**: Glob `{scope}/**/*.md` to find all markdown files. Exclude `CLAUDE.md` files and files inside `tests/` directories.
5. **Changed files**: Determine the changed-file set for downstream alignment using user input or read-only git commands. If unavailable, record that downstream alignment was not evaluated.
6. **Classify**: Map each file to its artifact type per `<file_classification>`.
7. **Check each file**:
   - If classified: run structural, language, and placement checks
   - If unrecognized: report classification failure, then run language check only (language rules apply to all text)
8. **Check downstream alignment**: Use the changed-file set to report higher-level declaration changes that lack lower-spec alignment or lower-node `PLAN.md` grounding. Treat a clean result as necessary evidence only; it is not proof that every directly affected lower spec was enumerated.
9. **Report**: Emit findings grouped by file path per `<report_format>`.
10. **Summary**: End with counts.

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
- {finding} (ref: decision_to_spec_alignment)

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
- [ ] Changed-file set determined or downstream alignment reported as not evaluated
- [ ] Downstream alignment checks applied to changed higher-level declarations when a changed-file set is available
- [ ] Report contains only factual findings — no suggestions, no severity, no "should"
- [ ] Summary counts emitted

</success_criteria>
