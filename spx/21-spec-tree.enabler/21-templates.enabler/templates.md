# Templates

PROVIDES the artifact type templates — product spec, ADR, PDR, the five output-kind specs, the variant spec, the outcome record, and the probe protocol — that define what each spec-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

### Compliance

- ALWAYS: the understanding skill provides templates for the product spec, ADRs, PDRs, one spec per output kind — substrate, capability, domain, interface, surface — the variant spec, the outcome record, and the probe protocol ([audit])
- ALWAYS: each output-kind spec template opens with its kind's contract — `SUPPLIES`, `PROVIDES`, `OWNS`, `ADAPTS ... FOR`, or `EXPOSES ... TO`, each continuing `SO THAT ... CAN ...` — and the variant template opens with its parent's form ([audit])
- ALWAYS: the output-kind and variant templates contain an Assertions section, and the product template carries front matter with `id` and `kind: product` and a title as its only required content ([audit])
- ALWAYS: define required sections for each artifact type — skills derive their validation rules from these templates ([audit])
- ALWAYS: the ADR and PDR decision templates require each `### Testing` rule to carry a single assertion-type tag — one of scenario, mapping, conformance, property, compliance ([audit])
- NEVER: duplicate template content in downstream skills — skills reference templates, they do not copy them ([audit])
