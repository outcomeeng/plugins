# Tutorial: Outcome Engineering with the Spec Tree Methodology

This tutorial walks through the full workflow — from bootstrapping a spec tree in a new or existing project to authoring specs, implementing code, and committing changes.

## Prerequisites

```bash
# Install the spx CLI
npm install -g @outcomeeng/spx

# Add the marketplace and install plugins
claude plugin marketplace add outcomeeng/claude
claude plugin install spec-tree@outcomeeng

# Install a language plugin for your project
claude plugin install python@outcomeeng      # or typescript@outcomeeng
```

## 1. Bootstrap a spec tree

The `/bootstrap` command works for both **existing projects** (where code already exists) and **blank projects** (starting from scratch). It reads your project's CLAUDE.md and codebase to understand what the product does, then interviews you to fill in the gaps.

### Existing project

If you have a project with code but no spec tree, `/bootstrap` detects the product from your existing files:

```text
> /bootstrap
```

It reads CLAUDE.md, package.json, README, or whatever describes your project, then asks targeted questions about what's missing.

![Bootstrap detects the product from CLAUDE.md](../assets/tutorial/bootstrap/20-boostrap-01-detect-product.png)

### What it asks

The interview gathers three things:

**Outcome hypothesis** — What change in user behavior do you expect?

![Outcome hypothesis question with structured options](../assets/tutorial/bootstrap/50-boostrap-02-questionnaire-01.png)

**Scope** — What are the major things this product does? Each becomes a top-level node.

![Scope question with progressive options](../assets/tutorial/bootstrap/60-boostrap-02-questionnaire-02.png)

**Shared infrastructure** — Do any concerns share dependencies that should be extracted as enablers?

![Shared infrastructure question](../assets/tutorial/bootstrap/70-boostrap-02-questionnaire-03.png)

### Confirm the scaffold

Before creating any files, the skill presents the full plan and lets you refine it:

![Confirm scaffold with options to refine](../assets/tutorial/bootstrap/80-boostrap-02-questionnaire-04.png)

### Result

The scaffold creates the product spec, a project guide, and top-level node stubs with the correct directory structure and sparse integer ordering:

![Scaffold result showing created files](../assets/tutorial/bootstrap/90-boostrap-02-questionnaire-05.png)

Your `spx/` directory now has a product spec, CLAUDE.md guide, and enabler/outcome nodes ready to fill in.

## 2. Author specs and decisions

Use `/author` to create any spec-tree artifact. It detects what you want from the argument:

```text
> /author outcome for search          # create an outcome node
> /author PDR for auth policy          # create a product decision
> /author ADR for caching strategy     # create an architecture decision
> /author enabler for test harness     # create a shared enabler
```

The skill:

1. Loads the foundation methodology (`/understanding`)
2. Loads context for the placement location (`/contextualizing`)
3. Reads the appropriate template
4. Asks clarifying questions about genuine gaps
5. Drafts the artifact in atemporal voice
6. Validates and creates the files

<!-- TODO: Add screenshot of /author in action -->

### Outcome nodes

Every outcome has a three-part hypothesis:

- **Output** — what the software does (tested by assertions)
- **Outcome** — measurable change in user behavior
- **Impact** — business value

The skill guides you through writing each part and suggests typed assertions (Scenario, Property, Mapping, Conformance, Compliance).

### Decision records

ADRs (architecture decisions) and PDRs (product decisions) govern what the product does. They use MUST/NEVER compliance rules verified by audit.

```text
> /author ADR for database choice
```

The skill asks about the decision, alternatives considered, trade-offs accepted, and compliance rules.

## 3. Decompose nodes

When a node accumulates too many assertions (>7) or contains independent concerns, break it down:

```text
> /decomposing
```

The skill:

1. Reads the target node's assertions
2. Groups them by independent concern
3. Presents the proposed split for your review
4. Assigns enabler/outcome types and sparse integer indices
5. Creates child directories with spec stubs
6. Redistributes assertions from parent to children

<!-- TODO: Add screenshot of /decomposing in action -->

## 4. Check consistency

Use `/aligning` to review specs for contradictions, gaps, or quality issues:

```text
> /aligning
```

It checks:

- Atemporal voice (no temporal language like "currently" or "we need to")
- Cross-node consistency (no conflicting assertions)
- Content placement (architecture in ADRs, not in specs)
- Assertion completeness (every outcome has typed assertions with test links)

<!-- TODO: Add screenshot of /aligning in action -->

## 5. Write tests

Use `/testing` to write tests driven by spec assertions:

```text
> /testing
```

The skill extracts typed assertions from the spec, determines what test evidence is needed, and generates test scaffolds. It delegates methodology decisions to the 5-stage testing router (what level, what doubles) and language patterns to `/testing-python` or `/testing-typescript`.

<!-- TODO: Add screenshot of /testing in action -->

## 6. Implement with TDD

The `/apply` command starts the full TDD flow — architecture, tests, then code — with review gates at each step:

```text
> /apply spx/21-auth.outcome
```

This invokes the `/applying` skill, which orchestrates 8 steps:

1. Load methodology (`/understanding`)
2. Load work item context (`/contextualizing`)
3. Architect — produce ADR via `/architecting-python` or `/architecting-typescript`
4. Review architecture — loop until APPROVED
5. Write tests — via `/testing-python` or `/testing-typescript`
6. Review tests — loop until APPROVED
7. Implement — via `/coding-python` or `/coding-typescript`
8. Review code — loop until APPROVED

Without arguments, `/apply` determines work from conversation context or falls back to `spx/EXCLUDE`.

<!-- TODO: Add screenshot of /apply in action -->

## 7. Commit changes

Use `/commit` for Conventional Commits with selective staging:

```text
> /commit
```

The skill:

1. Runs project validation (`just check`, `pnpm run check`, etc.)
2. Classifies changes by concern (type + scope)
3. Stages specific files for one concern at a time
4. Writes a commit message in imperative mood
5. Repeats for remaining concerns

Multiple concerns = multiple commits. The skill never uses `git add .`.

<!-- TODO: Add screenshot of /commit in action -->

## 8. Hand off and pick up

When you need to continue work in a fresh session:

```text
> /handoff                             # create a timestamped handoff
```

This saves the current context — what you were working on, what's done, what's next — to `.spx/sessions/`.

To resume in a new session:

```text
> /pickup                              # list and claim a previous handoff
```

<!-- TODO: Add screenshot of /handoff and /pickup in action -->

## 9. Refactor the tree

When the structure needs to change — moving nodes, re-scoping assertions, extracting shared enablers:

```text
> /refactoring
```

Four operations:

- **Move** — relocate a node under a different parent
- **Re-scope** — shift assertions between existing siblings
- **Extract enabler** — factor shared infrastructure from 2+ siblings into a lower-index enabler
- **Consolidate** — merge two nodes that are really the same concern

The skill analyzes impact (broken links, ADR/PDR scope changes), applies changes, and validates consistency afterward.

<!-- TODO: Add screenshot of /refactoring in action -->

## 10. Stop ad hoc work

If you catch yourself writing code without specs, debugging without tests, or skipping the methodology:

```text
> /rtfm
```

This stops the current ad hoc work and restarts the proper TDD flow from Step 1. It's a corrective command — use it when you realize you're off track.

## Workflow summary

| Step          | What you do                                       | Command/Skill                    |
| ------------- | ------------------------------------------------- | -------------------------------- |
| **Setup**     | Install spx CLI, add marketplace, install plugins | `npm install -g @outcomeeng/spx` |
| **Bootstrap** | Create spec tree for your product                 | `/bootstrap`                     |
| **Author**    | Create specs, decisions, nodes                    | `/author`                        |
| **Decompose** | Break down large nodes                            | `/decomposing`                   |
| **Align**     | Check consistency and quality                     | `/aligning`                      |
| **Test**      | Write tests from spec assertions                  | `/testing`                       |
| **Implement** | TDD flow: architect → test → code                 | `/apply`                         |
| **Commit**    | Selective staging, Conventional Commits           | `/commit`                        |
| **Hand off**  | Save context for next session                     | `/handoff` → `/pickup`           |
| **Refactor**  | Restructure the tree                              | `/refactoring`                   |
| **Correct**   | Stop ad hoc work, restart methodology             | `/rtfm`                          |
