# Bootstrapping

PROVIDES an interactive bootstrapping flow that scaffolds an initial spec tree from user interviews
SO THAT new projects
CAN adopt the Spec Tree methodology with a consistent tree structure

## Assertions

### Scenarios

- Given a project with no `spx/` directory, when bootstrapping runs, then a product spec and `spx/CLAUDE.md` are created ([test](tests/test_bootstrapping.unit.py))
- Given a product name and hypothesis provided by the user, when bootstrapping runs, then the product spec contains the provided hypothesis in the three-part format ([test](tests/test_bootstrapping.unit.py))
- Given bootstrapping completes, when `spx/CLAUDE.md` is examined, then it contains the correct `template_version` matching the installed spec-tree plugin ([test](tests/test_bootstrapping.unit.py))

### Compliance

- ALWAYS: interview the user before creating the tree — never assume product scope ([review])
- NEVER: create a spec tree without a product spec — the product spec is the root of all context ([review])
