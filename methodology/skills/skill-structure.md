# Skill Structure

## Plugin: `spec-tree`

All skills in this document belong to the `spec-tree` plugin. Skill names have no suffix — they are invoked as `/understand`, `/author`, etc. (or fully qualified as `spec-tree:understand`).

## Design principles

Three methodology steps drive all work. Audit gates operate within each step. See [`src/plugins/spec-tree/skills/understand/SKILL.md`](../../src/plugins/spec-tree/skills/understand/SKILL.md) for the authoritative inline foundation.

1. **Declare** — write specs: assertions, hypotheses, decisions. Node becomes Declared.
2. **Spec** — establish test, evaluate, or audit evidence that makes assertions verifiable. Node becomes Specified.
3. **Apply** — write implementation code that makes deterministic evidence pass and satisfies agentic evidence. Node becomes Passing.

Planning is transient — `PLAN.md` coordination notes left by `/handoff`, not durable artifacts.

Within these steps:

- Foundation skills load once per live marker; compaction expires the marker and requires a reload.
- `understand` is the single shared library: methodology, structure, templates.
- `contextualize` handles deterministic context injection from tree structure.
- Spec-tree action skills check for foundation markers before working; invoke foundations if absent.
- `verify` is the public evidence entry point and selects test, evaluate, or audit from the real subject's verdict.
- `test` remains the generic deterministic-evidence specialist invoked after `verify` selects test; `eval` owns generic eval authoring after its follow-on implementation.
- `apply` orchestrates the full declare → spec → apply flow with audit gates at each step.
- `commit-changes` creates local checkpoints independently of verification state, with Conventional Commits, selective staging, and atomic concerns; readiness gates still require their declared verification predicates.
- `manage-github-pr` routes shipping intent through committing, PR opening, PR management, merge, and closure. `open-pr` and `manage-pr` are internal protocols loaded by `manage-github-pr`.
- Make conversational flow explicit and consistent across action skills.
- Keep migration concerns in a separate optional structure document.

## Spec Tree methodology

Outcome Engineering centers on the **Spec Tree** — a git-native product structure where each node co-locates a spec and its path-bearing evidence. The tree addresses three failure modes of agentic development: value drift, heuristic context, and spec-evidence drift.

Every outcome begins with a hypothesis about user behavior; every enabler declares a deterministic shared capability. Assertions define verifiable claims about the output. Nodes progress through four states: **Declared** (spec only), **Specified** (spec + evidence, implementation not started), **Failing** (implementation exists but evidence fails), and **Passing** (evidence passes).

The tree structure enables deterministic context injection: the path from root to any node defines exactly what context an agent receives, replacing heuristic search with curated, reviewable context.

## Key concepts

- **Spec Tree** — git-native product structure in `spx/`
- **Enabler nodes** (`.enabler`) — infrastructure that higher-index nodes depend on
- **Outcome nodes** (`.outcome`) — hypotheses with testable assertions
- **Deterministic context injection** — tree structure defines agent context
- **Four node states** — Declared → Specified → Failing → Passing

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
- `tests/` -- co-located test files when the first `[test]` assertion exists
- `evals/{rule-slug}/` -- co-located eval artifacts when the first `[eval]` assertion exists

Enabler specs open with `PROVIDES ... SO THAT ... CAN ...`. Outcome specs open with `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`. Both are followed by `## Assertions` with typed test links:

```markdown
## Outcome

We believe that [hypothesis].

### Assertions

- Assertion text ([test](tests/file.scenario.l1.test.ts))
```

Every assertion carries exactly one current evidence tag. Test and eval tags link to co-located evidence; audit remains pathless.

### Product file

The root of every tree is `{product-name}.product.md`, capturing why the product exists and what change in user behavior it aims to achieve.

### Decision records

PDRs (product decisions) and ADRs (architecture decisions) are co-located at any directory level. Their numeric prefix encodes dependency scope within that directory:

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

| State         | Condition                                         | What it means                         |
| ------------- | ------------------------------------------------- | ------------------------------------- |
| **Declared**  | Spec exists, no evidence                          | Intent defined, no evidence yet       |
| **Specified** | Spec + evidence exist, implementation does not    | Evidence is declared ahead of code    |
| **Failing**   | Spec + evidence + implementation, evidence fails  | Reality has not caught up to the spec |
| **Passing**   | Spec + evidence + implementation, evidence passes | Evidence confirms the spec            |

Specified and failing are natural, healthy states. They are not problems to fix urgently.

### Deterministic context injection

The tree path from product root to target node defines what context an agent receives. At each directory along the path, all lower-index siblings' specs are injected. Ancestor specs along the path are always included. Test files are excluded.

This replaces heuristic context selection (keyword search, embedding similarity). The agent sees exactly the context the tree provides.

If the deterministic context payload for a node routinely exceeds an agent's reliable working set, the tree signals that the component needs further decomposition.

### Cross-cutting assertions

When a behavior spans multiple nodes, the assertion lives in the lowest common ancestor. If an ancestor accumulates too many cross-cutting assertions, extract a shared enabler at a lower index.

## Intent model (use cases)

### Declare — write specs, decisions, and assertions

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

### Spec — establish evidence that makes assertions verifiable

#### 7. Route evidence driven by spec assertions

7a. Select test, evaluate, or audit from the verdict the real assertion subject can produce.
7b. Route deterministic behavior to `test`, structured LLM-driven output to `eval`, and semantic constraints without a structural verdict to an isolated audit requirement.
7c. Analyze evidence gaps across a subtree — which assertions lack current evidence, which path-bearing links are broken.
7d. Load deterministic context (ancestor ADRs/PDRs, lower-index siblings) before establishing evidence.

#### 8. Write tests after test verification is selected

8a. Extract routed `[test]` assertions and derive the assertion type from each claim's quantifier.
8b. Select execution level and any permitted test-double exception independently of assertion type.
8c. Generate generic test ceremony before delegating language expression to the applicable language skill.
8d. Keep predicates in the linked test file while harnesses expose controlled observations, generators own variable domains, and fixtures remain inert whole-payload inputs.

#### 9. Review test evidence against spec assertions

9a. Adversarial review: how could tests pass while assertions remain unfulfilled?
9b. Tree-level coverage: are all assertions across a subtree covered? Are there orphaned tests?
9c. Cross-cutting assertion review: evidence at the right place for assertions at ancestor nodes?
9d. Decision record compliance from full ancestor chain.

### Apply — write implementation and commit

#### 10. Implement work items using spec-driven verification

10a. Orchestrate architecture → evidence → code steps with agentic gates.
10b. Load methodology and work item context as prerequisites.
10c. Delegate language-specific expression only after generic evidence routing.

#### 11. Commit changes

11a. Stage changes selectively by concern, write Conventional Commits messages.

## Skill map

### Declare

Skills for building and maintaining the durable map — specs, decisions, assertions.

#### Foundation layer

Foundation skills emit live conversation markers so other skills can detect whether foundation context is present. Every compaction expires those markers and requires the foundation and active node context to load again.

| Skill           | Owns                                                                                              | Marker                             | Status      |
| --------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------- | ----------- |
| `understand`    | Methodology, durable map worldview, decomposition semantics, ordering rules, all shared templates | `<SPEC_TREE_FOUNDATION>`           | Implemented |
| `contextualize` | Deterministic context injection from tree structure, path validation, abort/remediation           | `<SPEC_TREE_CONTEXT target="...">` | Implemented |

#### Action layer

Action skills do the work. Before starting, they check conversation history for foundation markers and invoke missing foundations.

| Skill       | Use case | Scope                                                           | Status      |
| ----------- | -------- | --------------------------------------------------------------- | ----------- |
| `bootstrap` | 2        | Interview user, scaffold new spec tree                          | Implemented |
| `author`    | 3        | Create/extend product/ADR/PDR/enabler/outcome from conversation | Implemented |
| `decompose` | 4        | Systematically decompose higher-level nodes to lower levels     | Implemented |
| `refactor`  | 5        | Structural moves, re-scoping, factoring shared enablers         | Implemented |
| `align`     | 6        | Clarify, augment, align, deconflict while preserving truth      | Implemented |

### Spec

Skills for selecting and establishing evidence. `verify` is the public router; evidence specialists own their mechanism after selection.

| Skill         | Use case | Scope                                                             | Invoked by       | Status      |
| ------------- | -------- | ----------------------------------------------------------------- | ---------------- | ----------- |
| `verify`      | 7        | Select test, evaluate, or audit and route the selected specialist | Public entry     | Implemented |
| `test`        | 8        | Generic deterministic test ceremony and language delegation       | `verify`         | Implemented |
| `eval`        | 7        | Generic eval authoring and producer-specialist delegation         | `verify`         | Planned     |
| `eval-skill`  | 7        | Skill-producer eval specialization                                | `eval`           | Planned     |
| `audit-tests` | 9        | Adversarial review of test evidence against spec assertions       | Auditor workflow | Implemented |

`spec-tree:verify` is the public evidence surface. It classifies the real subject before any specialist chooses assertion type, execution level, language expression, producer specialization, or verifier. After test is selected, `spec-tree:test` owns generic test decisions and delegates only language-specific expression to the applicable language skill. The planned `spec-tree:eval` follows the same generic-to-specialist direction for eval authoring.

`spec-tree:audit-tests` is a **superset** of `test/audit-tests`. It incorporates the full adversarial review protocol (4 phases, binary verdict) and adds tree-level coverage analysis, cross-cutting assertion review, and decision record compliance from the full ancestor chain.

### Apply

Skills for writing implementation code and committing results. `apply` is an orchestrator that spans all three steps (declare → spec → apply) with audit gates — it exists because Claude skips declaring prerequisites without guardrails.

| Skill              | Use case | Scope                                                                       | Status      |
| ------------------ | -------- | --------------------------------------------------------------------------- | ----------- |
| `apply`            | 10       | Orchestrator: declare → spec → apply with audit gates                       | Implemented |
| `commit-changes`   | 11       | Conventional Commits with selective staging and atomic commits              | Implemented |
| `manage-github-pr` | 11       | Route shipping intent through commit, PR open, PR management, and merge     | Implemented |
| `open-pr`          | 11       | Internal PR-opening protocol loaded by `manage-github-pr`                   | Implemented |
| `manage-pr`        | 11       | Internal open-PR management and merge protocol loaded by `manage-github-pr` | Implemented |

## Ownership model

### Declare

- **`understand`** is the single shared library for all Spec Tree knowledge:
  - Durable map worldview (specs are permanent product documentation)
  - Decomposition semantics (enabler vs outcome, nesting depth, when to extract shared enablers)
  - Structure and sparse integer ordering rules
  - All shared templates (product, ADR, PDR, enabler, outcome)
  - Template access instructions
- **`contextualize`** owns deterministic context injection:
  - Walks the tree from product root to target node
  - At each directory along the path, injects all lower-index siblings' specs
  - Validates artifact existence along the path
  - Returns context manifest or abort with remediation
  - Bootstrap mode: returns empty manifest with `bootstrap=true` when creating into an empty tree (no abort)
- **Action skills** (`author`, `decompose`, `refactor`, `align`) do not duplicate foundation content. They reference `understand` for templates and methodology.

### Spec

- **`verify`** owns verification-type selection and evidence routing:
  - Classifies only test, evaluate, or audit from the real subject's verdict
  - Invokes `test` for deterministic behavior and `eval` for structured LLM-driven output
  - Records a pathless isolated-verifier requirement for audit
  - Contains no language-specific test ceremony or producer-specific eval ceremony
- **`test`** owns spec-tree test writing (superset of `test/test`):
  - Incorporates full testing methodology (5 stages, 5 factors, 7 exceptions)
  - Extracts typed assertions from spec nodes, determines what evidence is demanded
  - Analyzes evidence gaps across subtrees — which assertions lack tests, which links are broken
  - Generates test scaffolds from assertion types (Scenario → example-based, Property → property-based, etc.)
  - Loads deterministic context (ancestor ADRs/PDRs, lower-index siblings) before writing tests
- **`audit-tests`** owns spec-tree test review (audit gate within spec step):
  - Incorporates full adversarial review protocol (4 phases, binary verdict)
  - Tree-level coverage: are all assertions across a subtree covered? Orphaned test files?
  - Cross-cutting assertion review: evidence at the right place for ancestor-level assertions
  - Decision record compliance from full ancestor chain (not just manually found ADRs/PDRs)

### Apply

- **`apply`** orchestrates the full declare → spec → apply flow:
  - Spans all three steps because Claude skips declaring prerequisites without guardrails
  - Delegates to language-specific plugins (Python or TypeScript) for architecture, testing, and implementation
  - Runs every applicable evidence audit, implementation audit, and changeset review to convergence
- **`commit-changes`** owns the git commit workflow:
  - Conventional Commits format with selective staging
  - Classifies changes by concern, one concern per commit
  - Records product validation as `passing`, `failing`, or `not-run` without using it as commit authorization
  - Preserves hooks and returns exact hook failures without bypassing them
- **`manage-github-pr`** owns shipping orchestration:
  - Detects instructed, existing-changeset, empty, and open-PR modes
  - Reads local lifecycle routing from `spx/local/merging.md` via `understand`
  - Invokes the implementation, commit, opening, managing, merge, and closure skills
- **`open-pr`** and **`manage-pr`** own internal PR lifecycle protocols:
  - `open-pr` evaluates `VERIFICATION_READINESS`, pushes, opens the ready PR, and schedules the first heartbeat
  - `manage-pr` inspects reviews/checks, drives follow-up pushes, evaluates merge gates, merges, and runs post-merge cleanup

## Marker-based state detection

Foundation skills emit XML markers into the conversation when loaded. All declare and spec skills check for these markers before starting work. Apply skills (`commit-changes`) operate independently; `manage-github-pr` checks the foundation marker so local lifecycle routing is known. This follows the same pattern as `/pickup` emitting `<PICKUP_ID>` for `/handoff` to find.

| Marker                                   | Emitted by      | Checked by                                            | Meaning                              |
| ---------------------------------------- | --------------- | ----------------------------------------------------- | ------------------------------------ |
| `<SPEC_TREE_FOUNDATION>`                 | `understand`    | Declare action skills, `verify`, evidence specialists | Methodology and templates are loaded |
| `<SPEC_TREE_CONTEXT target="full/path">` | `contextualize` | Declare action skills, `verify`, evidence specialists | Target artifacts are loaded          |

**Decision rule:**

- No `<SPEC_TREE_FOUNDATION>` in conversation: invoke `understand`
- No `<SPEC_TREE_CONTEXT>` matching current target: invoke `contextualize`
- Target path changed since last `<SPEC_TREE_CONTEXT>`: re-invoke `contextualize`

## Template ownership

`understand` owns the foundation references, examples, and artifact templates.
`update-instruction-block` owns the instruction-block template it renders. Other skills name
the owning template capability rather than manufacturing a cross-skill filesystem token:

```text
understand/
├── SKILL.md
├── examples/
│   ├── adr-example.md
│   ├── enabler-example.md
│   ├── outcome-example.md
│   └── pdr-example.md
├── references/
│   ├── excluded-nodes.md
│   └── product-domain-shapes.md
└── templates/
    ├── product/
    │   └── product-name.product.md
    ├── decisions/
    │   ├── decision-name.adr.md
    │   └── decision-name.pdr.md
    └── nodes/
        ├── enabler-name.md
        └── outcome-name.md

update-instruction-block/
└── templates/
    └── instruction-block.md
```

Action skills request the owning capability by template identity, for example: "Use
`understand`'s `templates/nodes/outcome-name.md` node template." The owning skill resolves its
bundled file. Do not introduce a second base-directory variable or a repository-local plugin
path.

## Conversational flow contract

Declare action skills follow this interaction contract:

1. **Intake** -- Ask for target path/scope and intended operation.
2. **Foundation gate** -- Check for `<SPEC_TREE_FOUNDATION>` marker; invoke `understand` if absent.
3. **Target context gate** -- Check for `<SPEC_TREE_CONTEXT>` matching target; invoke `contextualize` if absent or mismatched. Context is injected deterministically from tree structure. Abort with explicit remediation if required artifacts are missing.
4. **Plan** -- Present concise execution plan and expected outputs.
5. **Execute** -- Perform workflow steps. Keep user in the loop at major decision points.
6. **Evidence gate** -- Invoke `verify` so every assertion routes to current test, evaluate, or audit evidence.
7. **Deliver** -- Summarize changes, decisions, and next actions.

`apply` has its own 8-step flow that reuses steps 1–3 internally. `commit-changes` has no dependency on spec-tree foundations.

## Mode-specific flows

### Declare

Each flow documents only what is unique to that mode. All declare action skills share the standard preflight (steps 1–3) and postflight (steps 6–7) from the conversational flow contract above.

#### `understand`

1. Load Spec Tree methodology, structure semantics, and template index.
2. Emit `<SPEC_TREE_FOUNDATION>` marker with loaded module summary.

#### `contextualize`

1. Invoke `sync-base` before reading product truth; proceed only after `already_current` or `rebased` establishes a current checkout.
2. Intake and validate the canonical full target path.
3. Walk from the product root to the target, collecting every ancestor spec and lower-index sibling spec at each level.
4. Include every applicable ADR, PDR, explicitly cited methodology-governance decision, guide file, and local lifecycle overlay without heuristic filtering.
5. List linked tests and the applicable test-directory state without reading test bodies.
6. If the exact product-root target has a product spec and no nodes, emit `bootstrap=true`; reject missing node targets.
7. Emit `<SPEC_TREE_CONTEXT target="full/path">` with the complete manifest, sync-base status, and lifecycle continuation state.

#### `bootstrap`

1. Check for existing product spec — redirect to `author` if tree already exists.
2. Interview user for product identity, hypothesis, and scope.
3. Identify top-level nodes (3–7 concerns), classify as enabler or outcome.
4. Present scaffold plan and wait for confirmation.
5. Create `spx/` with product spec, CLAUDE.md, and top-level node stubs.
6. Recommend next steps (fill assertions with `author`, decompose with `decompose`).

#### `author`

1. Detect empty tree → invoke `bootstrap` if no product spec exists.
2. Intake node type (enabler or outcome), intended location, and path.
3. Clarify user intent and unresolved product decisions.
4. Draft artifact using templates from `understand` and Spec Tree rules.
5. Validate atemporal voice, consistency, and testability (assertions link to test files for outcomes).
6. Return draft, open decisions, and recommended next steps (decomposition or test creation).

#### `decompose`

1. Intake source node and target decomposition depth.
2. Apply decomposition methodology (enabler vs outcome, scope, sparse integer ordering).
3. Produce child nodes with explicit boundaries and dependencies.
4. Validate decomposition quality (no excessive nesting, correct node types, no misplaced assertions).
5. Return decomposition output with rationale for splits and boundaries.

#### `refactor`

1. Intake structural change request (move, re-scope, extract shared enabler).
2. Analyze impact across hierarchy and decision records.
3. Propose structural change set (moves, consolidations, new enabler nodes).
4. Apply refactoring updates.
5. Validate cross-node consistency after structural changes.

#### `align`

1. Intake alignment request (clarify, augment, deconflict).
2. Analyze contradictions, gaps, or ambiguities across affected nodes.
3. Propose alignment changes with rationale.
4. Apply clarification or deconfliction updates.
5. Validate cross-node consistency and report unresolved conflicts.

### Spec

#### `test`

Generic deterministic-evidence specialist invoked after `verify` selects test.

1. Load methodology and tree context via foundation skills.
2. Accept only assertions already routed to `[test]` by `verify`.
3. Extract typed assertions from target spec node(s) — Scenario, Property, Mapping, Conformance, Compliance.
4. For each assertion, determine what test evidence is demanded (assertion type → test pattern).
5. Analyze evidence gaps: which assertions have test links? Which links resolve? Which are stale?
6. For assertions lacking tests, generate generic ceremony using assertion type to select the test pattern, then delegate language expression to the applicable language skill.
7. Report evidence summary: which assertions have tests, which do not, and which are stale.

#### `audit-tests`

Superset of `test/audit-tests`. Incorporates the full adversarial review protocol, adds tree-specific concerns.

1. Load methodology and tree context via foundation skills.
2. Execute the 4 foundational review phases from `test/audit-tests` (spec structure, evidentiary integrity, lower-level assumptions, ADR/PDR compliance).
3. Tree-level coverage: walk subtree, verify all assertions across all nodes have test evidence.
4. Cross-cutting assertion review: for assertions at ancestor nodes, verify evidence is provided at the appropriate place.
5. Orphan detection: identify test files not linked from any assertion.
6. Decision record compliance from full ancestor chain loaded via `contextualize`.
7. Binary verdict: APPROVED or REJECT. No middle ground.

### Apply

#### `apply`

Orchestrates the full declare → spec → apply flow. Spans all three steps because Claude skips declaring prerequisites without guardrails.

1. Load methodology via `understand` once per session and current work-item context via `contextualize` for every node.
2. Architect through the applicable language skill and obtain an approved architecture-auditor verdict on an exact committed scope.
3. Invoke `verify`; route selected deterministic evidence through `test` or the applicable eval workflow, then obtain the required evidence-auditor verdicts.
4. Implement through the applicable language coding skill and obtain an approved implementation-auditor projection.
5. Create atomic local checkpoints through `commit-changes` whenever tracked or untracked work differs from `HEAD`, preserving `passing`, `failing`, or `not-run` verification state.
6. Dispatch gating audits and reviews only after required deterministic verification passes, against a clean exact checkpoint; keep live-file audits advisory.
7. Run artifact evidence audits for every changed test or eval surface and a whole-changeset review for cross-node changes, repairing and checkpointing each rejected head.
8. Run the repository's full deterministic gate once after all agentic gates converge on the same clean committed head.

#### `commit-changes`

1. Record the latest product-validation state as `passing`, `failing`, or `not-run`.
2. Review changes: `git status`, `git diff`.
3. Classify changes by concern — group by type+scope.
4. Stage specific files for one concern (never `git add .`).
5. Write a Conventional Commits message (imperative, under 50 chars).
6. Commit with hooks enabled, confirm the full `HEAD` changed, report remaining paths and validation state, then repeat from step 4 for remaining concerns.

#### `manage-github-pr`

1. Detect mode from arguments, branch state, working tree, commits ahead of base, and existing PR state.
2. Load `understand` when the foundation marker is absent so local lifecycle routing is known.
3. State the lifecycle plan and proceed autonomously by default; use the runtime's structured-question tool before mutation only when the local merge overlay opts into confirmation.
4. Invoke implementation skills when the requested work is not yet in the tree.
5. Invoke `commit-changes`, then the internal `open-pr` and `manage-pr` protocols unless the local lifecycle overlay declares a different route.
6. Invoke `handoff` after merge unless the route stops earlier; the handoff skill decides whether any continuation needs a session file.

#### `open-pr`

Internal protocol loaded by `manage-github-pr`.

1. Load `merging-standards`, `commit-changes`, and `task-tracking-standards`.
2. Establish branch hygiene and topology.
3. Establish `VERIFICATION_READINESS` through deterministic verification and local review convergence.
4. Push with explicit destination ref.
5. Open the PR ready and schedule the first heartbeat.

#### `manage-pr`

Internal protocol loaded by `manage-github-pr`.

1. Identify the open PR and inspect review, check, comment, and base-drift state.
2. Classify and act on review findings by validity and phase.
3. Re-establish `VERIFICATION_READINESS` before every follow-up push.
4. Refresh the heartbeat.
5. Evaluate `MERGE_READINESS`, merge when it holds, then evaluate `DEPLOYMENT_READINESS` and `RELEASE_READINESS` before their declared post-merge actions and cleanup.
