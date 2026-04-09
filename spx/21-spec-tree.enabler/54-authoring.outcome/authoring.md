# Authoring

WE BELIEVE THAT providing template-driven authoring of spec tree artifacts (product, ADR, PDR, enabler, outcome)
WILL eliminate misplaced content and structural defects in new specs
CONTRIBUTING TO higher first-pass spec quality and reduced alignment corrections

The `/authoring` skill guides placement, index assignment, and content quality using templates from the `/understanding` foundation skill.

## Assertions

### Scenarios

- Given a request to create an outcome node, when the authoring skill runs, then the created spec contains a three-part hypothesis (output, outcome, impact) ([test](tests/test_authoring.unit.py))
- Given existing siblings at indices 21, 32, and 43, when a new independent node is created, then it receives an index that does not collide with existing siblings ([test](tests/test_authoring.unit.py))
- Given a request to create an ADR, when the content contains scenario assertions instead of compliance rules, then the authoring skill flags the content misplacement ([test](tests/test_authoring.unit.py))

### Compliance

- ALWAYS: read the appropriate template before drafting — templates are the structural authority ([review])
- ALWAYS: invoke `/contextualizing` on the parent directory before creating any node — sibling enumeration prevents index collisions ([review])
- NEVER: place implementation details in specs — "how" belongs in ADRs or code ([review])
