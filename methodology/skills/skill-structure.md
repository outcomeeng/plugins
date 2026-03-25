# Skill Structure

## Plugin: `spec-tree`

All skills in this document belong to the `spec-tree` plugin. Skill names have no suffix — they are invoked as `/understanding`, `/authoring`, etc. (or fully qualified as `spec-tree:understanding`).

## Design principles

The `spec-tree` plugin covers three phases with distinct concerns:

1. **Spec-tree** — creating and maintaining the spec tree (the product structure itself).
2. **Implementation** — using the spec tree to build software (TDD flow driven by specs).
3. **Commit** — recording results into version control.

Within these phases:

- Foundation skills load once per conversation using marker pattern (no persistent state).
- `understanding` is the single shared library: methodology, structure, templates.
- `contextualizing` handles deterministic context injection from tree structure.
- Spec-tree action skills check for foundation markers before working; invoke foundations if absent.
- `testing` and `reviewing-tests` are supersets of their `test` plugin counterparts, adding tree-specific concerns. No cross-plugin dependency at runtime.
- `coding` orchestrates the TDD flow: architecture, tests, code — with review gates at each phase.
- `committing-changes` enforces Conventional Commits with selective staging and atomic commits.
- Make conversational flow explicit and consistent across action skills.
- Keep migration concerns in a separate optional structure document.

## Spec Tree methodology

Outcome Engineering centers on the **Spec Tree** — a git-native product structure where each node co-locates a spec and its tests. The tree addresses three failure modes of agentic development: value drift, heuristic context, and spec-test drift.

Every node begins with an outcome hypothesis — a belief about what change it will produce. Assertions define testable claims about the output. Nodes progress through four states: **Spec** (spec only), **Potential** (spec + tests, implementation not started), **Failing** (implementation exists but tests fail), and **Realized** (tests pass).

The tree structure enables deterministic context injection: the path from root to any node defines exactly what context an agent receives, replacing heuristic search with curated, reviewable context.

## Key concepts

- **Spec Tree** — git-native product structure in `spx/`
- **Enabler nodes** (`.enabler`) — infrastructure that higher-index nodes depend on
- **Outcome nodes** (`.outcome`) — hypotheses with testable assertions
- **Deterministic context injection** — tree structure defines agent context
- **Four node states** — Spec → Potential → Failing → Realized

### Node types

Two node types:

| Node type   | Directory suffix | Spec header                                        | Purpose                                                            |
| ----------- | ---------------- | -------------------------------------------------- | ------------------------------------------------------------------ |
| **Enabler** | `.enabler`       | `PROVIDES ... SO THAT ... CAN ...`                 | Infrastructure that would be removed if all its dependents retired |
| **Outcome** | `.outcome`       | `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...` | Hypothesis about what change a behavior will produce               |

Nodes are nestable at any depth. The tree is not limited to three levels.

### Spec format

Every node directory contains:

- `{slug}.md` -- the spec file (no type suffix, no numeric prefix)
- `tests/` -- co-located test files

Enabler specs open with `PROVIDES ... SO THAT ... CAN ...`. Outcome specs open with `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Both are followed by `## Assertions` with typed test links:

```markdown
## Outcome

We believe that [hypothesis].

### Assertions

- Assertion text ([test](tests/file.unit.test.ts))
```

Every assertion must link to at least one test file.

### Product file

The root of every tree is `{product-name}.product.md`, capturing why the product exists and what change in user behavior it aims to achieve.

### Decision records

PDRs (product constraints) and ADRs (architecture choices) are co-located at any directory level. Their numeric prefix encodes dependency scope within that directory:

```text
spx/
├── product-name.product.md
├── 15-constraint-name.pdr.md
├── 15-technical-choice.adr.md
└── 21-first-enabler.enabler/
```

### Sparse integer ordering

Numeric prefixes encode dependency order within each directory. A lower-index item constrains every sibling with a higher index -- and that sibling's descendants. Items sharing the same index are independent of each other.

Distribution formula for N expected items across range [10, 99]:

```text
i_k = 10 + floor(k * 89 / (N + 1))
```

For N=7: sequence 21, 32, 43, 54, 65, 76, 87.

Fractional indexing (e.g., `20.5-slug`) is the escape hatch when integer gaps are exhausted.

### Node states

A node's state is derived from what exists and whether tests pass:

| State         | Condition                                  | What it means                        |
| ------------- | ------------------------------------------ | ------------------------------------ |
| **Spec**      | Spec exists, no tests                      | Intent defined, no evidence yet      |
| **Potential** | Spec + tests exist, implementation doesn't | Tests excluded via `spx/POTENTIAL`   |
| **Failing**   | Spec + tests + implementation, tests fail  | Reality hasn't caught up to the spec |
| **Realized**  | Spec + tests + implementation, tests pass  | Evidence confirms the spec           |

Potential and failing are natural, healthy states. They are not problems to fix urgently.

### Deterministic context injection

The tree path from product root to target node defines what context an agent receives. At each directory along the path, all lower-index siblings' specs are injected. Ancestor specs along the path are always included. Test files are excluded.

This replaces heuristic context selection (keyword search, embedding similarity). The agent sees exactly the context the tree provides.

If the deterministic context payload for a node routinely exceeds an agent's reliable working set, the tree signals that the component needs further decomposition.

### Cross-cutting assertions

When a behavior spans multiple nodes, the assertion lives in the lowest common ancestor. If an ancestor accumulates too many cross-cutting assertions, extract a shared enabler at a lower index.

## Intent model (use cases)

### Phase 1: Spec-tree — creating and maintaining the product structure

#### 1. Understand Spec Tree context

1a. Systematically ingest context to prepare for a discussion with the user.
1b. Systematically ingest context to prepare for autonomous work.

#### 2. Bootstrap a new Spec Tree

2a. Interview user for product identity, hypothesis, and scope.
2b. Scaffold `spx/` with product spec, CLAUDE.md, and top-level node stubs.

#### 3. Author Spec Tree artifacts

3a. Author from scratch from user conversation/prompt, including clarifying questions.
3b. Extend existing artifacts with new requirements, outcomes, or decisions.

#### 4. Decompose Spec Tree artifacts

4a. Systematically decompose existing higher-level nodes to lower levels.

#### 5. Refactor Spec Tree artifacts

5a. Review and structurally refactor (move/re-scope content) through user conversation.
5b. Factor common aspects into shared enablers at lower indices.

#### 6. Align Spec Tree artifacts

6a. Clarify/augment/align/deconflict artifacts while preserving product truth.

### Phase 2: Implementation — using the spec tree to build software

#### 7. Write tests driven by spec assertions

7a. Extract typed assertions from spec nodes and determine what test evidence is demanded.
7b. Analyze evidence gaps across a subtree — which assertions lack test links, which links are broken.
7c. Generate test scaffolds from assertion types, delegating methodology to `test/testing` and language patterns to language-specific skills.
7d. Load deterministic context (ancestor ADRs/PDRs, lower-index siblings) before writing tests.

#### 8. Review test evidence against spec assertions

8a. Adversarial review: how could tests pass while assertions remain unfulfilled?
8b. Tree-level coverage: are all assertions across a subtree covered? Are there orphaned tests?
8c. Cross-cutting assertion review: evidence at the right place for assertions at ancestor nodes?
8d. Decision record compliance from full ancestor chain.

#### 9. Implement work items using TDD flow

9a. Orchestrate architecture → test → code phases with review gates.
9b. Load methodology and work item context as prerequisites.
9c. Delegate to language-specific plugins for each phase.

### Phase 3: Commit — recording results into version control

#### 10. Commit changes

10a. Stage changes selectively by concern, write Conventional Commits messages.

## Skill map

### Phase 1: Spec-tree

Skills for creating and maintaining the spec tree itself.

#### Foundation layer

Foundation skills load once per conversation. They emit conversation markers so other skills can detect whether foundation context is present.

| Skill             | Owns                                                                                              | Marker                             | Status      |
| ----------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------- | ----------- |
| `understanding`   | Methodology, durable map worldview, decomposition semantics, ordering rules, all shared templates | `<SPEC_TREE_FOUNDATION>`           | Implemented |
| `contextualizing` | Deterministic context injection from tree structure, path validation, abort/remediation           | `<SPEC_TREE_CONTEXT target="...">` | Implemented |

#### Action layer

Action skills do the work. Before starting, they check conversation history for foundation markers and invoke missing foundations.

| Skill           | Use case | Scope                                                           | Status      |
| --------------- | -------- | --------------------------------------------------------------- | ----------- |
| `bootstrapping` | 2        | Interview user, scaffold new spec tree                          | Implemented |
| `authoring`     | 3        | Create/extend product/ADR/PDR/enabler/outcome from conversation | Implemented |
| `decomposing`   | 4        | Systematically decompose higher-level nodes to lower levels     | Implemented |
| `refactoring`   | 5        | Structural moves, re-scoping, factoring shared enablers         | Implemented |
| `aligning`      | 6        | Clarify, augment, align, deconflict while preserving truth      | Implemented |

### Phase 2: Implementation

Skills for using the spec tree to build software. Each builds on a standalone `test` plugin counterpart, adding tree-specific concerns.

| Skill             | Use case | Scope                                                                | Builds on              | Status      |
| ----------------- | -------- | -------------------------------------------------------------------- | ---------------------- | ----------- |
| `testing`         | 7        | Write tests driven by spec assertions, evidence gap analysis         | `test/testing`         | Implemented |
| `reviewing-tests` | 8        | Adversarial review of test evidence against spec assertions          | `test/reviewing-tests` | Implemented |
| `coding`          | 9        | TDD flow: architecture → test → code with review gates at each phase | —                      | Implemented |

`spec-tree:testing` is a **superset** of `test/testing`. It incorporates the full testing methodology (5 stages, 5 factors, 7 exceptions) and adds spec-tree-specific concerns: assertion extraction from spec nodes, evidence gap analysis across subtrees, test scaffold generation driven by assertion type, and deterministic context loading from the tree. A spec-tree user invokes `spec-tree:testing`; a non-spec-tree user invokes `test/testing`. No cross-plugin dependency at runtime.

`spec-tree:reviewing-tests` is a **superset** of `test/reviewing-tests`. It incorporates the full adversarial review protocol (4 phases, binary verdict) and adds tree-level coverage analysis, cross-cutting assertion review, and decision record compliance from the full ancestor chain.

`spec-tree:coding` orchestrates the TDD flow. Phases 1–2 load methodology and context via Phase 1 foundation skills. Phases 3–8 delegate to language-specific plugins (Python or TypeScript) for architecture, testing, and implementation — each with a review gate that loops until approved.

### Phase 3: Commit

Skills for recording results into version control.

| Skill                | Use case | Scope                                                          | Status      |
| -------------------- | -------- | -------------------------------------------------------------- | ----------- |
| `committing-changes` | 10       | Conventional Commits with selective staging and atomic commits | Implemented |

### Commands

Commands provide dynamic context injection and invoke the corresponding skill.

| Command    | Phase | Invokes              | Purpose                                               |
| ---------- | ----- | -------------------- | ----------------------------------------------------- |
| `/clarify` | 1     | —                    | Gather requirements through questioning before acting |
| `/handoff` | 1     | —                    | Create timestamped handoff for session continuity     |
| `/pickup`  | 1     | —                    | Load handoff document to continue previous work       |
| `/tdd`     | 2     | `coding`             | Start TDD flow with auto-injected project context     |
| `/rtfm`    | 2     | `coding`             | Stop ad hoc work, restart proper TDD flow             |
| `/commit`  | 3     | `committing-changes` | Git commit with auto-injected branch/status/diff      |

## Ownership model

### Phase 1: Spec-tree

- **`understanding`** is the single shared library for all Spec Tree knowledge:
  - Durable map worldview (specs are permanent product documentation)
  - Decomposition semantics (enabler vs outcome, nesting depth, when to extract shared enablers)
  - Structure and sparse integer ordering rules
  - All shared templates (product, ADR, PDR, enabler, outcome)
  - Template access instructions
- **`contextualizing`** owns deterministic context injection:
  - Walks the tree from product root to target node
  - At each directory along the path, injects all lower-index siblings' specs
  - Validates artifact existence along the path
  - Returns context manifest or abort with remediation
  - Bootstrap mode: returns empty manifest with `bootstrap=true` when authoring into an empty tree (no abort)
- **Action skills** (`authoring`, `decomposing`, `refactoring`, `aligning`) do not duplicate foundation content. They reference `understanding` for templates and methodology.

### Phase 2: Implementation

- **`testing`** owns spec-tree test writing (superset of `test/testing`):
  - Incorporates full testing methodology (5 stages, 5 factors, 7 exceptions)
  - Extracts typed assertions from spec nodes, determines what evidence is demanded
  - Analyzes evidence gaps across subtrees — which assertions lack tests, which links are broken
  - Generates test scaffolds from assertion types (Scenario → example-based, Property → property-based, etc.)
  - Loads deterministic context (ancestor ADRs/PDRs, lower-index siblings) before writing tests
- **`reviewing-tests`** owns spec-tree test review (superset of `test/reviewing-tests`):
  - Incorporates full adversarial review protocol (4 phases, binary verdict)
  - Tree-level coverage: are all assertions across a subtree covered? Orphaned test files?
  - Cross-cutting assertion review: evidence at the right place for ancestor-level assertions
  - Decision record compliance from full ancestor chain (not just manually found ADRs/PDRs)
- **`coding`** owns the TDD implementation flow:
  - 8-phase orchestration: methodology → context → architect → review → test → review → implement → review
  - Phases 1–2 reuse Phase 1 foundation skills (`understanding`, `contextualizing`)
  - Phases 3–8 delegate to language-specific plugins (Python or TypeScript)
  - Three review gates that loop until approved — no exceptions

### Phase 3: Commit

- **`committing-changes`** owns the git commit workflow:
  - Conventional Commits format with selective staging
  - Classifies changes by concern, one concern per commit
  - Runs project validation before committing

## Marker-based state detection

Phase 1 foundation skills emit XML markers into the conversation when loaded. All skills that depend on spec-tree context — Phase 1 action skills and Phase 2 skills (`testing`, `reviewing-tests`, `coding`) — check for these markers before starting work. Phase 3 (`committing-changes`) operates independently and does not check markers. This follows the same pattern as `/pickup` emitting `<PICKUP_ID>` for `/handoff` to find.

| Marker                                   | Emitted by        | Checked by                                | Meaning                              |
| ---------------------------------------- | ----------------- | ----------------------------------------- | ------------------------------------ |
| `<SPEC_TREE_FOUNDATION>`                 | `understanding`   | Phase 1 action skills, all Phase 2 skills | Methodology and templates are loaded |
| `<SPEC_TREE_CONTEXT target="full/path">` | `contextualizing` | Phase 1 action skills, all Phase 2 skills | Target artifacts are loaded          |

**Decision rule:**

- No `<SPEC_TREE_FOUNDATION>` in conversation: invoke `understanding`
- No `<SPEC_TREE_CONTEXT>` matching current target: invoke `contextualizing`
- Target path changed since last `<SPEC_TREE_CONTEXT>`: re-invoke `contextualizing`

## Template ownership

`understanding` owns all templates. Action skills access them via the foundation skill's base directory:

```text
${UNDERSTANDING_DIR}/
├── SKILL.md
├── references/
│   ├── durable-map.md
│   ├── decomposition-semantics.md
│   ├── node-types.md
│   ├── assertion-types.md
│   ├── ordering-rules.md
│   └── what-goes-where.md
└── templates/
    ├── product/
    │   └── product-name.product.md
    ├── decisions/
    │   ├── decision-name.adr.md
    │   └── decision-name.pdr.md
    └── nodes/
        ├── enabler-name.md
        └── outcome-name.md
```

Action skills reference templates with: `Read: ${UNDERSTANDING_DIR}/templates/nodes/outcome-name.md`

## Conversational flow contract

Phase 1 spec-tree action skills follow this interaction contract:

1. **Intake** -- Ask for target path/scope and intended operation.
2. **Foundation gate** -- Check for `<SPEC_TREE_FOUNDATION>` marker; invoke `understanding` if absent.
3. **Target context gate** -- Check for `<SPEC_TREE_CONTEXT>` matching target; invoke `contextualizing` if absent or mismatched. Context is injected deterministically from tree structure. Abort with explicit remediation if required artifacts are missing.
4. **Plan** -- Present concise execution plan and expected outputs.
5. **Execute** -- Perform workflow steps. Keep user in the loop at major decision points.
6. **Evidence gate** -- Verify spec assertions have test evidence. (Placeholder — not yet active.)
7. **Deliver** -- Summarize changes, decisions, and next actions.

Phase 2 (`coding`) has its own 8-phase flow that reuses steps 1–3 internally. Phase 3 (`committing-changes`) has no dependency on spec-tree foundations.

## Mode-specific flows

### Phase 1: Spec-tree

Each flow documents only what is unique to that mode. All Phase 1 action skills share the standard preflight (steps 1–3) and postflight (steps 6–7) from the conversational flow contract above.

#### `understanding`

1. Load Spec Tree methodology, structure semantics, and template index.
2. Emit `<SPEC_TREE_FOUNDATION>` marker with loaded module summary.

#### `contextualizing`

1. Intake target path/scope and operation type.
2. Walk tree from product root to target node.
3. At each directory along the path, collect lower-index siblings' specs.
4. Include ancestor specs along the path. Exclude test files.
5. Validate collected artifacts exist and are readable.
6. If operation is `author` and no artifacts exist at target level, return empty manifest with `bootstrap=true` instead of aborting.
7. Emit `<SPEC_TREE_CONTEXT target="full/path">` with context manifest: collected specs, open decisions, readiness status.

#### `bootstrapping`

1. Check for existing product spec — redirect to `authoring` if tree already exists.
2. Interview user for product identity, hypothesis, and scope.
3. Identify top-level nodes (3–7 concerns), classify as enabler or outcome.
4. Present scaffold plan and wait for confirmation.
5. Create `spx/` with product spec, CLAUDE.md, and top-level node stubs.
6. Recommend next steps (fill assertions with `authoring`, decompose with `decomposing`).

#### `authoring`

1. Detect empty tree → invoke `bootstrapping` if no product spec exists.
2. Intake node type (enabler or outcome), intended location, and path.
3. Clarify user intent and unresolved product decisions.
4. Draft artifact using templates from `understanding` and Spec Tree rules.
5. Validate atemporal voice, consistency, and testability (assertions link to test files for outcomes).
6. Return draft, open decisions, and recommended next steps (decomposition or test creation).

#### `decomposing`

1. Intake source node and target decomposition depth.
2. Apply decomposition methodology (enabler vs outcome, scope, sparse integer ordering).
3. Produce child nodes with explicit boundaries and dependencies.
4. Validate decomposition quality (no excessive nesting, correct node types, no misplaced assertions).
5. Return decomposition output with rationale for splits and boundaries.

#### `refactoring`

1. Intake structural change request (move, re-scope, extract shared enabler).
2. Analyze impact across hierarchy and decision records.
3. Propose structural change set (moves, consolidations, new enabler nodes).
4. Apply refactoring updates.
5. Validate cross-node consistency after structural changes.

#### `aligning`

1. Intake alignment request (clarify, augment, deconflict).
2. Analyze contradictions, gaps, or ambiguities across affected nodes.
3. Propose alignment changes with rationale.
4. Apply clarification or deconfliction updates.
5. Validate cross-node consistency and report unresolved conflicts.

### Phase 2: Implementation

#### `testing`

Superset of `test/testing`. Incorporates the full methodology, adds tree-specific concerns.

1. Load methodology and tree context via foundation skills.
2. Extract typed assertions from target spec node(s) — Scenario, Property, Mapping, Conformance, Compliance.
3. For each assertion, determine what test evidence is demanded (assertion type → test pattern).
4. Analyze evidence gaps: which assertions have test links? Which links resolve? Which are stale?
5. For assertions lacking tests, generate scaffolds using assertion type to select test pattern. Delegate methodology decisions (level, doubles) to the 5-stage router. Delegate language patterns to language-specific skills.
6. Report evidence summary: which assertions have tests, which don't, which are stale.

#### `reviewing-tests`

Superset of `test/reviewing-tests`. Incorporates the full adversarial review protocol, adds tree-specific concerns.

1. Load methodology and tree context via foundation skills.
2. Execute the 4 foundational review phases from `test/reviewing-tests` (spec structure, evidentiary integrity, lower-level assumptions, ADR/PDR compliance).
3. Tree-level coverage: walk subtree, verify all assertions across all nodes have test evidence.
4. Cross-cutting assertion review: for assertions at ancestor nodes, verify evidence is provided at the appropriate place.
5. Orphan detection: identify test files not linked from any assertion.
6. Decision record compliance from full ancestor chain loaded via `contextualizing` (not just manually found ADRs/PDRs).
7. Binary verdict: APPROVED or REJECT. No middle ground.

#### `coding`

1. Load methodology via `understanding` (once per session).
2. Load work item context via `contextualizing` (every node).
3. Architect: produce ADR via language-specific `/architecting-[language]` skill.
4. Review architecture via `/reviewing-[language]-architecture` — loop until APPROVED.
5. Test: write tests via `/testing-[language]` skill.
6. Review tests via `/reviewing-[language]-tests` — loop until APPROVED.
7. Implement: write code via `/coding-[language]` skill.
8. Review code via `/reviewing-[language]` — loop until APPROVED.

### Phase 3: Commit

#### `committing-changes`

1. Run project validation (e.g., `just check`).
2. Review changes: `git status`, `git diff`.
3. Classify changes by concern — group by type+scope.
4. Stage specific files for one concern (never `git add .`).
5. Write Conventional Commits message (imperative, under 50 chars).
6. Commit, then repeat from step 4 for remaining concerns.
