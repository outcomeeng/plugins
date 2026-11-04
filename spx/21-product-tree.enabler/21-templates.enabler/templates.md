---
id: 01a0ebba-5f61-73ed-9937-44782e89f16e
malleability: spec
---

# Templates

PROVIDES the artifact type templates — product document, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each product-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

- ALWAYS: decision and output-node templates distinguish untagged authoring declarations directly under `## Verification` or `## Assertions` from the grouped examples produced after verification selection, and permit both forms in one artifact.
- NEVER: a declaration template treats authoring approval as evidence completeness or Passing state.
- pdr-opening: ALWAYS: the PDR template opens with an optional paragraph of one `DEFINES <term> AS <definition>` line per term the decision owns, then a paragraph of `GOVERNS <subject>`, `SO THAT <who relies on it>`, and `CAN RELY ON <behavior>` lines, and carries no Product properties section and no Rationale section. [audit]
- mapping-subsection: ALWAYS: the PDR template and each output-kind and variant spec template write a mapping rule as its own `### Mapping: <slug>` subsection holding one sentence that ends in the tag `[mapping]` and a table with one row per case, whose first column holds a short name for the case. [audit]
- rule-groups: ALWAYS: the PDR template and each output-kind and variant spec template write every other rule as one sentence, opened by its slug and ended by exactly one tag, in a group headed `### <assertion type>: <subject>` when its rules share one subject or `### <assertion type>` when they share none, naming Eval, Probe, or Audit in place of the assertion type for a rule with that tag, and a group of more than seven rules splits by subject. [audit]
- form-text: NEVER: a document written from the PDR template or from an output-kind or variant spec template holds text outside its opening, a rule, or a table. [audit]
- levels: A stdlib script shipped in the product-tree plugin derives three views of a document written from the PDR template or from an output-kind or variant spec template from its structure alone, as follows. [test: mapping, l1]

  | Case    | View                                                                                                             |
  | ------- | ---------------------------------------------------------------------------------------------------------------- |
  | level-1 | the path, the title, and the opening                                                                             |
  | level-2 | level 1, then each subsection heading, each rule's slug and sentence, and the first column of each mapping table |
  | level-3 | the whole file                                                                                                   |

- audit-tag-forms: ALWAYS: every decision and spec template writes each audit rule with the tag `[audit]` led by the rule's slug, and no template writes `[audit:{rule-slug}]`. [audit]

### Compliance

- ALWAYS: the understanding skill provides templates for the product document, ADRs, PDRs, one spec per output kind — substrate, capability, domain, interface, surface — the variant spec, the outcome record, and the probe protocol ([audit])
- ALWAYS: each output-kind spec template opens with its kind's contract — `SUPPLIES`, `PROVIDES`, `OWNS`, `ADAPTS ... FOR`, or `EXPOSES ... TO`, each continuing `SO THAT ... CAN ...` — and the variant template opens with its parent's form ([audit])
- ALWAYS: the output-kind and variant templates contain an Assertions section, and the product template carries front matter with `id` and `kind: product` and a title as its only required content ([audit])
- ALWAYS: define required sections for each artifact type — skills derive their validation rules from these templates ([audit])
- adr-testing-tag: ALWAYS: the ADR decision template requires each `### Testing` rule to carry a single assertion-type tag — one of scenario, mapping, conformance, property, compliance. [audit]
- NEVER: duplicate template content in downstream skills — skills reference templates, they do not copy them ([audit])
