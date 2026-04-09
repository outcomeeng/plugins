# Bootstrapping

WE BELIEVE THAT an interactive bootstrapping flow that scaffolds an initial spec tree from user interviews
WILL reduce the barrier to adopting the Spec Tree methodology in new projects
CONTRIBUTING TO faster methodology adoption and consistent tree structure across projects

The `/bootstrapping` skill interviews the user about their product, scaffolds the initial tree with a product spec and `spx/CLAUDE.md`, and recommends initial top-level nodes.

## Assertions

### Scenarios

- Given a project with no `spx/` directory, when bootstrapping runs, then a product spec and `spx/CLAUDE.md` are created ([test](tests/test_bootstrapping.unit.py))
- Given a product name and hypothesis provided by the user, when bootstrapping runs, then the product spec contains the provided hypothesis in the three-part format ([test](tests/test_bootstrapping.unit.py))
- Given bootstrapping completes, when `spx/CLAUDE.md` is examined, then it contains the correct `template_version` matching the installed spec-tree plugin ([test](tests/test_bootstrapping.unit.py))

### Compliance

- ALWAYS: interview the user before creating the tree — never assume product scope ([review])
- NEVER: create a spec tree without a product spec — the product spec is the root of all context ([review])
