# Bootstrapping

PROVIDES an interactive bootstrapping flow that scaffolds a product-root spec tree from user interviews
SO THAT new projects
CAN adopt the Spec Tree methodology while delegating top-level structure to `/decompose spx/`

## Assertions

### Compliance

- ALWAYS: bootstrapping a product with no `spx/` directory creates a product spec and a managed Spec Tree instruction block in root `CLAUDE.md` and `AGENTS.md` ([audit])
- ALWAYS: bootstrapping writes the product name and hypothesis provided by the user into the product spec in the three-part format ([audit])
- ALWAYS: bootstrapping writes a root `CLAUDE.md` and `AGENTS.md` managed Spec Tree instruction block whose `template_version` matches the installed spec-tree plugin ([audit])
- ALWAYS: interview the user before creating the tree — never assume product scope ([audit])
- ALWAYS: detect brownfield — a product already implemented in code while `spx/` is absent or empty — and note it before the interview ([audit])
- ALWAYS: cover consumers, jobs, surfaces, actors and sidedness, constraints, success signals, and top-level intent in the interview, applying `/interview`'s methodology rather than a forked interview ([audit])
- ALWAYS: in brownfield, derive top-level intent from the product dimensions — consumers, jobs, surfaces, actors — never from the code's package, module, directory, or file layout ([audit])
- ALWAYS: create the product spec and the root `CLAUDE.md` and `AGENTS.md` managed Spec Tree instruction block before any top-level child nodes — the root must exist before composition ([audit])
- ALWAYS: record top-level product intent, constraints, examples, and unresolved questions in `spx/PLAN.md` when the user provides candidate areas ([audit])
- ALWAYS: delegate top-level child composition to `/decompose spx/` — bootstrapping records product intent, decomposition owns child boundaries, node types, ordering evidence, and indices ([audit])
- NEVER: create a spec tree without a product spec — the product spec is the root of all context ([audit])
- NEVER: assign top-level child indices or create top-level child nodes inside bootstrapping ([audit])
