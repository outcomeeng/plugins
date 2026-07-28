# Templates

PROVIDES the artifact type templates (product, ADR, PDR, enabler, outcome) that define what each spec-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

### Compliance

- ALWAYS: the understanding skill provides templates for product specs, ADRs, PDRs, enabler nodes, and outcome nodes ([audit])
- ALWAYS: the enabler and outcome templates contain an Assertions section ([audit])
- ALWAYS: define required sections for each artifact type — skills derive their validation rules from these templates ([audit])
- ALWAYS: the ADR and PDR decision templates require each `### Testing` rule to carry a single assertion-type tag — one of scenario, mapping, conformance, property, compliance ([audit])
- NEVER: duplicate template content in downstream skills — skills reference templates, they do not copy them ([audit])
