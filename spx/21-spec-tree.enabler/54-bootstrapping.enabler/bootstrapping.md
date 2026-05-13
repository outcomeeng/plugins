# Bootstrapping

PROVIDES an interactive bootstrapping flow that scaffolds a product-root spec tree from user interviews
SO THAT new projects
CAN adopt the Spec Tree methodology while delegating top-level structure to `/decomposing spx/`

## Assertions

### Scenarios

- Given a product with no `spx/` directory, when bootstrapping runs, then a product spec and `spx/CLAUDE.md` are created ([test](tests/test_bootstrapping.unit.py))
- Given a product name and hypothesis provided by the user, when bootstrapping runs, then the product spec contains the provided hypothesis in the three-part format ([test](tests/test_bootstrapping.unit.py))
- Given bootstrapping completes, when `spx/CLAUDE.md` is examined, then it contains the correct `template_version` matching the installed spec-tree plugin ([test](tests/test_bootstrapping.unit.py))

### Compliance

- ALWAYS: interview the user before creating the tree — never assume product scope ([review])
- ALWAYS: create the product spec and `spx/CLAUDE.md` before any top-level child nodes — the root must exist before composition ([review])
- ALWAYS: record top-level product intent, constraints, examples, and unresolved questions in `spx/PLAN.md` when the user provides candidate areas ([review])
- ALWAYS: delegate top-level child composition to `/decomposing spx/` — bootstrapping records product intent, decomposition owns child boundaries, node types, ordering evidence, and indices ([review])
- NEVER: create a spec tree without a product spec — the product spec is the root of all context ([review])
- NEVER: assign top-level child indices or create top-level child nodes inside bootstrapping ([review])
