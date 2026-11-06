---
id: 01a0ebba-5f61-73ed-9937-44782e89f16e
malleability: spec
---

# Templates

PROVIDES the artifact type templates — product document, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each product-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

- authoring-and-routed-forms: ALWAYS: decision and output-node templates distinguish untagged authoring declarations directly under `## Verification` or `## Assertions` from the grouped examples produced after verification selection, and permit both forms in one artifact.
- approval-is-not-evidence: NEVER: a declaration template treats authoring approval as evidence completeness or Passing state.
- decision-openings: The PDR and ADR templates open with an optional paragraph of one `DEFINES <term> AS <definition>` line per term the decision owns, then the paragraph below, and carry no Rationale, Product properties, or Invariants section.

  | Case | Opening paragraph                                                                                       |
  | ---- | ------------------------------------------------------------------------------------------------------- |
  | pdr  | `GOVERNS <subject>`, `SO THAT <who relies on it>`, `CAN RELY ON <behavior>`                             |
  | adr  | `CONSTRAINS <part of the build>`, `TO <the chosen mechanism>`, `SO THAT <the property the build gains>` |

- mapping-subsection: ALWAYS: the PDR and ADR templates and each output-kind and variant spec template write a mapping rule as its own `### Mapping: <slug>` subsection holding one sentence and a table with one row per case, whose first column holds a short name for the case.
- rule-groups: ALWAYS: the PDR and ADR templates and each output-kind and variant spec template write every other rule as one sentence opened by its slug, in a group headed `### <assertion type>: <subject>` when its rules share one subject or `### <assertion type>` when they share none, naming Probe or Audit in place of the assertion type for a rule verified that way, and a group of more than ten rules splits by subject.
- eval-subsection: ALWAYS: the PDR and ADR templates and each output-kind and variant spec template write an eval as its own `### Eval: <slug>` subsection holding one sentence and a case table whose rows give each case's Given and Then; the table is the one source of the eval's cases.
- form-text: NEVER: a document written from the PDR or ADR template or from an output-kind or variant spec template holds text outside its opening, a rule, or a table.
- levels: A stdlib script derives three views of a document written from the PDR or ADR template or from an output-kind or variant spec template from its structure alone, as follows. ([test](tests/test_document_levels.mapping.l1.py))

  | Case    | View                                                                                                             |
  | ------- | ---------------------------------------------------------------------------------------------------------------- |
  | level-1 | the path, the title, and the opening                                                                             |
  | level-2 | level 1, then each subsection heading, each rule's slug and sentence, and the first column of each mapping table |
  | level-3 | the whole file                                                                                                   |

- levels-probe: An attested run of the levels script over the PDR and capability examples retains each example's level 2 view as its artifact. ([probe](probes/levels-probe/probe.md))
- no-tags: NEVER: the PDR or ADR template or an output-kind or variant spec template writes a tag on a rule; the group heading names the rule's verification type, the rule's leading slug is its one name, and a spec rule gains its evidence link only when its evidence exists.

### Compliance

- template-set: ALWAYS: the understanding skill provides templates for the product document, ADRs, PDRs, one spec per output kind — substrate, capability, domain, interface, surface — the variant spec, the outcome record, and the probe protocol ([audit])
- kind-openings: ALWAYS: each output-kind spec template opens with its kind's contract — `SUPPLIES`, `PROVIDES`, `OWNS`, `ADAPTS ... FOR`, or `EXPOSES ... TO`, each continuing `SO THAT ... CAN ...` — and the variant template opens with its parent's form ([audit])
- assertions-section: ALWAYS: the output-kind and variant templates contain an Assertions section, and the product template carries front matter with `id` and `kind: product` and a title as its only required content ([audit])
- required-sections: ALWAYS: define required sections for each artifact type — skills derive their validation rules from these templates ([audit])
- no-template-copies: NEVER: duplicate template content in downstream skills — skills reference templates, they do not copy them ([audit])
