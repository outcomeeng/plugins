# Templates

PROVIDES the artifact type templates (product, ADR, PDR, enabler, outcome) that define what each spec-tree artifact must contain
SO THAT all downstream skills (authoring, auditing, aligning)
CAN operate from a shared structural definition rather than ad hoc conventions

## Assertions

### Scenarios

- Given the understanding skill's templates directory, when listed, then template files exist for product, ADR, PDR, enabler, and outcome ([test](tests/test_templates.unit.py))
- Given a node template (enabler or outcome), when its content is parsed, then it contains an Assertions section ([test](tests/test_templates.unit.py))

### Compliance

- ALWAYS: define required sections for each artifact type — skills derive their validation rules from these templates ([review])
- NEVER: duplicate template content in downstream skills — skills reference templates, they do not copy them ([review])
