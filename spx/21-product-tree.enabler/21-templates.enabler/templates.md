---
id: 01a0ebba-5f61-73ed-9937-44782e89f16e
malleability: spec
---

# Templates

PROVIDES the artifact type templates — product document, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each product-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

### Audit: template form

- decision-openings: The PDR template opens with `GOVERNS <subject>`, `SO THAT <who relies on it>` and `CAN RELY ON <behavior>`, and the ADR template with `CONSTRAINS <part of the build>`, `TO <the chosen mechanism>` and `SO THAT <the property the build gains>`, the PDR Opening optionally preceded by one `DEFINES <term> AS <definition>` line per term the PDR owns, and neither carries a Rationale, Product properties, or Invariants section.
- rule-groups: The PDR and ADR templates and each output-kind and variant spec template write every rule outside a Mapping or Evaluate subsection opened by its slug and a colon, a Compliance rule with ALWAYS or NEVER after the colon and a Scenario rule with only its slug and the colon on its first line and indented Given, When, Then and And lines after it, in a group headed `### Test.<assertion type>: <subject>` for a Scenario, Conformance, Property or Compliance rule when its rules share one subject or `### Test.<assertion type>` when they share none, headed `### Audit`, or in a spec template `### Probe`, with its subject for a rule verified that way, at every Malleability, and a group of more than ten rules splits by subject.
- mapping-subsection: The PDR and ADR templates and each output-kind and variant spec template write a mapping rule as its own `### Test.Mapping: <slug>` subsection holding one sentence and a table with one row per case, whose first cell in each row holds the slug of its case, unique within its table.
- eval-subsection: The PDR and ADR templates and each output-kind and variant spec template write an eval as its own `### Evaluate: <slug>` subsection holding one sentence and a case table whose rows give each case's input and expected output; the table is the one source of the eval's cases.
- no-tags: No PDR or ADR template and no output-kind or variant spec template writes a tag on a rule; the group heading names the rule's verification type, the rule's leading slug is its one name, and a spec rule gains its evidence link only when its evidence exists.
- form-text: A document written from the PDR or ADR template or from an output-kind or variant spec template holds no text outside its opening, its rules, and their tables.
- approval-is-not-evidence: No declaration template treats authoring approval as evidence completeness or Passing state.

### Audit: template set

- template-set: The understanding skill provides templates for the product document, ADRs, PDRs, one spec per output kind — substrate, capability, domain, interface, surface — the variant spec, the outcome record, and the probe protocol.
- kind-openings: Each output-kind spec template opens with its kind's contract — `SUPPLIES`, `PROVIDES`, `OWNS`, `ADAPTS ... FOR`, or `EXPOSES ... TO`, each continuing `SO THAT ... CAN ...` — and the variant template opens with its parent's form.
- assertions-section: The output-kind and variant templates contain an Assertions section, and the product template carries front matter with `id` and `kind: product` and a title as its only required content.
- required-sections: Define required sections for each artifact type — skills derive their validation rules from these templates.
- no-template-copies: Downstream skills reference templates and duplicate none of their content.

### Test.Mapping: [levels](tests/test_document_levels.mapping.l1.py)

A stdlib script derives three views of a document written from the PDR or ADR template or from an output-kind or variant spec template from its structure alone.

| Case             | View                                                                                                                                                        |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| level-1          | the path, the title, and the opening                                                                                                                        |
| level-2          | level 1, then each subsection heading, each rule's slug and sentence, and the case column of each Mapping and Evaluate table                                |
| level-2-evaluate | for a record whose only table is an Evaluate case table: level 1, then each subsection heading, each rule's slug and sentence, and that table's case column |
| level-3          | the whole file                                                                                                                                              |

### Probe: levels

- [levels-probe](probes/levels-probe/probe.md): An attested run of the levels script over the PDR and capability examples and over a spec holding an Evaluate subsection retains each document's level 2 view as its artifact, the Evaluate case column included
