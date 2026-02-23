# Growing a Spec Tree for Deterministic Context

"How things are done around here" is culture — norms, shortcuts and constraints earned over the lifetime of a team. They are sometimes written down but rarely up-to-date because humans construct and maintain them through conversation and practice. AI coding agents are missing out on all of this. They don't internalize the expensive lessons acquired during outages and lack tacit knowledge.

When context is missing, agents fills in the gaps — always confidently, often wrong. In my interactions with Claude Code and Codex, I keep observing three distinct failure modes, which compound each other once a codebase outgrows a single context window.

The first is the drift of value, where value refers to the whole raison d'être for the project. This phenomenon is observed by any euphoric vibe coder as they keep tweaking their product and suddenly observe that things that seemed to have been working suddenly very clearly don't work anymore. Spec-driven development (SDD), i.e., supporting the development of software by some form of specification, has been touted as the antidote to this. Böckeler [distinguishes three variants of SDD](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)

- *Spec-first:* the spec generates tasks and is discarded,
- *spec-anchored:* the spec stays in the repo as living documentation, and
- *spec-as-source:* (the spec is the source of truth that code is derived from).

Tools like [Spec Kit](https://github.com/github/spec-kit), [Kiro](https://kiro.dev/), and [OpenSpec](https://openspec.dev/) all address variants of the same problem: how to get agents to respect constraints.

But even when specs are kept, the progress signal remains task completion. When the spec captures only *what to build*, the product is defined by "what we did" rather than "what it is." Dead code accumulates because nobody can tie it back to a purpose. Change requests from product look arbitrary because the value function isn't in the artifact being changed. If the only persistent artifact is output, output becomes permanent.

### Heuristic context

Context selection in most agentic workflows is heuristic: grepping for keywords, embedding similarity, tool defaults. As the repo grows, the selection is hard to review and unstable from one run to the next. Ask an agent to add a feature and it will happily create a new helper function, unaware that a validated implementation already exists two directories over.

I realized I needed a systematic way to inject context when I noticed I had developed a reflex to press <kbd>Esc</kbd> whenever I saw an agent searching the codebase.

### Spec–test drift

Even with specs and tests in the repo, the binding between them decays with every change. A spec evolves, tests still pass for the old behavior, and the repo no longer contains a reviewable signal of what is currently believed to be true. Git tracks every content change, but it cannot answer the question that matters: do the tests that pass still validate what the spec currently claims?

---

Over the last year, I have developed a structure that addresses all three.

## From outputs to outcomes

Over the past decade, product thinking moved from outputs to outcomes (cf. Joshua Seiden's book "Outcomes over Output"). Focusing on outcomes means iterating on outputs until a measurable outcome — typically a change in user behavior, such as renewing a subscription — is achieved or the hypothesis that drove its creation is scrapped.

I had to discard a core assumption to arrive at this: specs are not for planning. The spec is the product's source of truth — what users should be able to do, expressed as testable assertions. Every spec begins with an outcome hypothesis: the reason this node exists, expressed as a belief about what change it will produce. Assertions define what must be true about the output for the hypothesis to become verifiable. There is no outcome without an output.

With this inversion, my conversation with agents shifts from directing implementation to maintaining what users need. The agent detects what code needs to change by running the tests; how it addresses the gap is driven by skills. If the gap is large, agents make plans, adjust them, and discard them after execution. The plan is disposable because the spec is durable.

The overhead would be unacceptable for humans. But agents are cheap to rerun and good at mechanical bookkeeping — they can maintain this structure as a side effect of doing the work.

Three guidelines follow. They are not abstractions; they are practical consequences of the fact that agents cannot participate in the conversations that produce tacit knowledge.

### Always be converging

> Iterate on a durable artifact in small, reviewable steps such that each step is reversible and repeatable, and each reduces uncertainty about what the system should do.

Agents will get things wrong. Because every agent starts from the spec — not the implementation — mistakes do not compound: go back one step, try again with a different prompt or a different agent, and the spec anchors the retry.

### Determinism unless creation is the goal

> Never generate what can be derived deterministically.

If you know what you want the agent to base its actions on, provide it as deterministic context and keep it from grepping the codebase. Whenever you observe that it is looking for prior art, ask yourself if you should create or augment a skill so that you control what the agent considers worthy of imitation.

Wherever a deterministic mechanism can replace a probabilistic one, use it: curate context rather than letting agents search the codebase, link traceability explicitly rather than inferring it, let pre-commit hooks catch what agent judgment would miss. Reserve the generative capacity of agents for the parts that require it. Global and local constraints — Product Decision Records (PDRs capture product constraints such as pricing, compliance, and retention that must hold across a subtree) and Architecture Decision Records (ADRs) — must be co-located with the specs they apply to.

### Ask what matters

> Expose the maximum leverage decisions, let the agent handle the rest.

Any operational system must expose the highest leverage decisions to a human — either ex ante or ex post — and use the industriousness of agents to update all dependent decisions when you change them. The structure must separate intended behavior (spec) from whether that behavior holds (tests + lock file).

These guidelines are design constraints, not abstractions. Together they point toward a specific kind of artifact: a maintained system of record that captures both what a team decided and why — where the spec is not a planning document that rots after sprint one, but the product's source of truth.

## The Spec Tree

The **Spec Tree** is a git-native product structure, managed by the `spx` CLI, built on these constraints. Git-native is deliberate: blob hashes, co-location, and deterministic context all depend on file content being in the repo. Agents are increasingly optimized for finding and editing local files; how well they navigate an organization's third-party knowledge base is not something I would bet on. Every node co-locates a spec, its tests, and a lock file that binds them — tracking not just what changed, but what has been validated and whether that validation is still current. Remaining work is the set of assertions not yet satisfied or no longer current — progress measured by assertions validated, not tickets closed.

### Building the tree

Start with the product file:

```text
spx/
└── spx-cli.product.md
```

`spx-cli.product.md` captures why this product should exist and what change in user behavior it aims to achieve. The filename convention is `{product-name}.product.md`.

Decisions crystallize before implementation begins. A PDR (Product Decision Record) establishes a product constraint; ADRs (Architecture Decision Records) capture technical choices. The human makes the decision; agents create the record and propagate changes through dependent nodes. Enablers provide infrastructure that higher-index nodes depend on:

```text
spx/
├── spx-cli.product.md
├── 15-tree-structure-contract.pdr.md
├── 15-cli-framework.adr.md
├── 15-randomized-test-generation.adr.md
└── 21-test-harness.enabler/
    ├── test-harness.md
    └── tests/
        └── test-harness.unit.test.ts
```

Numeric prefixes encode dependency order within each directory. A decision at a lower index constrains every sibling with a higher index — and that sibling's descendants. All three decisions share index 15: they are independent of each other but constrain everything at index 21 and above. The test harness at index 21 is an **enabler node** (`.enabler` suffix): infrastructure that higher-index nodes depend on.

Prefixes use a sparse integer distribution to predictably space nodes and absorb future insertions. By establishing a sufficiently large coordinate space upfront, new nodes cleanly slot into the existing integer gaps. In my experience with projects up to 100k lines of code, two-digit prefixes are sufficient. To distribute an expected maximum of $N$ nodes evenly across a two-digit range from $i_{\textrm{min}} = 10$ to $i_{\textrm{max}} = 99$, the index $i_k$ for the $k$-th item is calculated as

$$i_k = i_{\textrm{min}} + \left\lfloor k \times \frac{i_{\textrm{max}}-i_{\textrm{min}}}{N+1} \right\rfloor$$

For $N=7$, this leads to a sequence $i_k = 21, 32, 43, 54, 65, 76, 87$, where

$$i_k = 10 +  k \times 11.$$

The product grows. Enablers build on each other; outcomes deliver customer-facing value at higher indices:

```text
spx/
├── spx-cli.product.md
├── 15-tree-structure-contract.pdr.md
├── 15-cli-framework.adr.md
├── 15-randomized-test-generation.adr.md
├── 21-test-harness.enabler/
│   ├── test-harness.md
│   └── tests/
│       └── test-harness.unit.test.ts
├── 22-e2e-harness.enabler/
│   ├── e2e-harness.md
│   └── tests/
│       └── e2e-harness.e2e.test.ts
├── 32-parse-directory-tree.enabler/
│   ├── parse-directory-tree.md
│   ├── 21-spx-lock-state.enabler/
│   │   ├── spx-lock-state.md
│   │   └── tests/
│   │       └── spx-lock-state.unit.test.ts
│   ├── 21-test-link-state.enabler/
│   │   ├── test-link-state.md
│   │   └── tests/
│   │       └── test-links.unit.test.ts
│   └── tests/
│       └── parse-directory-tree.unit.test.ts
├── 43-node-status.enabler/
│   ├── node-status.md
│   ├── 32-node-state-machine.enabler/
│   │   ├── node-state-machine.md
│   │   └── tests/
│   │       └── node-state-machine.unit.test.ts
│   └── tests/
│       └── node-status.unit.test.ts
├── 54-spx-tree-interpretation.outcome/
│   ├── spx-tree-interpretation.md
│   ├── 21-parent-child-links.enabler/
│   │   ├── parent-child-links.md
│   │   └── tests/
│   │       └── build.unit.test.ts
│   ├── 43-status-rollup.outcome/
│   │   ├── status-rollup.md
│   │   └── tests/
│   │       └── status.unit.test.ts
│   ├── 54-spx-tree-status.outcome/
│   │   ├── spx-tree-status.md
│   │   └── tests/
│   │       └── spx-tree-status.unit.test.ts
│   └── tests/
│       └── spx-tree-interpretation.unit.test.ts
├── 76-cli-integration.outcome/
│   ├── cli-integration.md
│   └── tests/
│       └── cli-integration.integration.test.ts
├── 87-e2e-workflow.outcome/
│   ├── e2e-workflow.md
│   ├── 43-e2e-validation.outcome/
│   │   ├── e2e-validation.md
│   │   └── tests/
│   │       ├── errors.integration.test.ts
│   │       ├── formats.integration.test.ts
│   │       └── performance.integration.test.ts
│   └── tests/
│       └── e2e-workflow.e2e.test.ts
└── AGENTS.md
```

**Enabler nodes** (`.enabler` suffix) exist to serve other nodes — infrastructure that would be removed if all its dependents were retired. **Outcome nodes** (`.outcome` suffix) each express one hypothesis and the testable assertions that define its output. Position in the tree implies scope: `21-test-harness.enabler/` at the root level serves all nodes in the product; `21-parent-child-links.enabler/` nested inside `54-spx-tree-interpretation.outcome/` serves only its sibling nodes and their descendants. The spec file inside each node is `{slug}.md` — no type suffix, no numeric prefix. Enabler specs start with `## Enables`; outcome specs with `## Outcome`.

When a behavior spans multiple nodes, the assertion lives in the lowest common ancestor. The ancestor's spec captures cross-cutting behaviors; child nodes handle their local concerns. If an ancestor accumulates too many cross-cutting assertions, that is a signal to extract a shared enabler at a lower index.

Fractional indexing can be used as an escape hatch to avoid cascading renumbering in the rare event a gap is fully exhausted. To insert a new node `integration-harness` between `21-test-harness.enabler` and `22-e2e-harness.enabler`, one would use `20.5-integration-harness`

Adding a new outcome — say, formatting `spx` output as JSON or as a table — means inserting a child node under `76-cli-integration.outcome/`:

```text
76-cli-integration.outcome/
├── cli-integration.md
├── 32-output-format.outcome/
│   ├── output-format.md
│   └── tests/
│       └── output-format.unit.test.ts
└── tests/
    └── cli-integration.integration.test.ts
```

No sibling at the root level is affected. Growth is bounded: a new node touches only its parent and ancestors, never its siblings. The tree need not be right from the start — fractional indexing absorbs insertions without renumbering, and because each lock file tracks only its own spec and tests, restructuring a subtree does not invalidate sibling nodes.

## What a node looks like

The spec at `54-spx-tree-interpretation.outcome/43-status-rollup.outcome/status-rollup.md`:

```markdown
## Outcome

We believe that aggregating child node states into a parent status will let developers identify stale subtrees without inspecting each node individually.

### Assertions

- A parent with all valid children reports valid ([test](tests/status.unit.test.ts))
- A parent with any stale child reports stale ([test](tests/status.unit.test.ts))
- A parent with any needs-work child needs work ([test](tests/status.unit.test.ts))
```

Every assertion links to the test file meant to prove it — the `spx` CLI parses the Markdown AST to extract these links. The invariant: every assertion must be covered by at least one test file. The human writes the hypothesis and its assertions; the agent writes the tests and implementation to prove them.

Numeric prefixes encode dependency scope. Within each directory, a lower-index item provides context to every sibling at a higher index — and to that sibling's descendants. Decisions constrain; enablers provide infrastructure; all are part of the deterministic context for higher-index nodes.

The lock file at `54-spx-tree-interpretation.outcome/43-status-rollup.outcome/spx-lock.yaml`:

```yaml
schema: spx-lock/v1
blob: a3b7c12
tests:
  - path: tests/status.unit.test.ts
    blob: 9d4e5f2
```

Every `blob` is a Git blob hash — the same content-addressable hash Git computes for file contents. Because blob hashes track content, not paths, renaming a file does not invalidate its hash — update the path in the lock file and the blob still matches. The lock file is written only when all tests pass — it records that the spec and its tests were in agreement at the time of writing, not that they still are.

Edit `status-rollup.md` and its Git blob hash changes. The `blob` in the lock file no longer matches. The node is stale — visibly, before anyone runs a test. Change a test file and its `blob` breaks the same way.

Because the lock file contains only hashes — no timestamps — it is deterministic: writing it twice on the same state produces the same file. Two agents working on the same node with the same state produce identical lock files. After a branch merge, lock files regenerate the same way `npm install` regenerates a package lock — but unlike package locks, the output is fully deterministic: discard both sides, relock, done.

Each node's lock file tracks only its own spec and tests. Subtree validity is checked by walking the tree, examining each descendant independently. A leaf change does not invalidate the root.

## Deterministic context injection

In most agentic workflows, context is assembled heuristically — search, embeddings, tool-use defaults. The selection is hard to review and unstable as the repo grows. The Spec Tree enables deterministic context injection: the `spx` CLI walks the tree from the product level down to the target node and applies one structural rule: at each directory along the path, inject all lower-index siblings' specs. Ancestor specs along the path are always included. Test files are excluded.

If an agent is assigned `54-spx-tree-interpretation.outcome/43-status-rollup.outcome`, deterministic context injection provides:

```text
spx/
  spx-cli.product.md                          <-- product spec
  15-tree-structure-contract.pdr.md            <-- index 15 < 54
  15-cli-framework.adr.md                      <-- index 15 < 54
  15-randomized-test-generation.adr.md         <-- index 15 < 54
  21-test-harness.enabler/
    test-harness.md                            <-- index 21 < 54
  32-parse-directory-tree.enabler/
    parse-directory-tree.md                    <-- index 32 < 54
  43-node-status.enabler/
    node-status.md                             <-- index 43 < 54
  54-spx-tree-interpretation.outcome/
    spx-tree-interpretation.md                 <-- ancestor spec
    21-parent-child-links.enabler/
      parent-child-links.md                    <-- index 21 < 43
    43-status-rollup.outcome/                  [TARGET]
      status-rollup.md                         <-- target spec
      tests/                                   -- ignored
    54-spx-tree-status.outcome/                -- index 54 >= 43
  76-cli-integration.outcome/                  -- index 76 >= 54
  87-e2e-workflow.outcome/                     -- index 87 >= 54
```

The agent sees exactly the context the tree provides. It doesn't search the codebase for "prior art"; the tree provides the authoritative context deterministically. Because the tree is traversable top-down, an agent can always resume work even if prior changes haven't fully propagated.

A mismatch between the lock file and the current state of spec or tests does not mean behavior changed — it means the evidence is stale. Tests detect behavioral drift; the lock makes it visible when the evidence needs refreshing.

If the deterministic context payload for a single node routinely exceeds an agent's reliable working set, the tree is telling you the component is doing too much. The structure forces architectural boundaries: when a node requires too much context, it is a signal to decompose further.

The tree is designed for tree filesystem browsers — VS Code, Neovim (neo-tree, nvim-tree), JetBrains IDEs. When navigating to a node, a human opens the ancestor chain — the same deterministic context that injection provides to the agent. ADRs and PDRs sit as files in each directory, discoverable without opening any subdirectory. Sibling nodes are visible but need not be opened.

## The operational loop

Three commands form the core loop:

```text
$ spx status --tree 54-spx-tree-interpretation.outcome
54-spx-tree-interpretation.outcome/    needs work (no lock file)
  21-parent-child-links.enabler/       valid
  43-status-rollup.outcome/            stale
    status-rollup.md changed           (was a3b7c12, now 5e9f1d8)
  54-spx-tree-status.outcome/          needs work (no lock file)

$ spx lock 54-spx-tree-interpretation.outcome/43-status-rollup.outcome
Running tests...
  tests/status.unit.test.ts            3 passed
Lock regenerated: 43-status-rollup.outcome/spx-lock.yaml

$ spx verify --tree 54-spx-tree-interpretation.outcome
54-spx-tree-interpretation.outcome/    needs work
  21-parent-child-links.enabler/       valid
  43-status-rollup.outcome/            valid
  54-spx-tree-status.outcome/          needs work
```

- `spx status` reads the tree and shows node states without running tests.
- `spx lock` runs tests and writes the lock file — only when all pass.
- `spx verify` compares hashes without running tests — cheap verification that the lock still holds.
- `spx verify --fix` verifies first, and if stale, locks. Designed for pre-commit hooks; in CI, `spx lock` must produce zero changes.

If tests fail, `spx lock` exits with an error and leaves the existing lock file unchanged — the node remains in its previous state. The lock tracks spec-and-test currency, not implementation correctness — whether the code still passes requires running `spx lock`.

## What's actually new here

The Spec Tree combines three independently valuable mechanisms in a single structure:

**Outcome hypothesis as organizing principle.** Every node begins with a belief about what change it will produce — making value explicit and keeping it in the artifact that gets changed. This is the antidote to value drift: when product learning changes, the spec still contains *why it exists*.

**Drift detection via lock file.** Git blob hashes bind spec content to test evidence. When either side changes, the hash breaks and the node is visibly stale — before anyone runs a test. This makes spec–test drift visible regardless of how context is assembled.

**Deterministic context from tree structure.** The path from root to node defines what context an agent receives — lower-index siblings at each directory along the path, plus ancestor specs. This replaces heuristic context selection regardless of whether a lock file exists.

Each stands on its own. Together they close the loop: the outcome hypothesis says *why* the node exists; the tree controls *what context* an agent uses; the lock file shows *whether* the spec is validated. All three are maintained by agents as a side effect of doing the work.

All three accept explicit trade-offs. Markdown links between assertions and test files are automatically validatable — the lock file detects when either has changed without the other. Deterministic context injection provides what we would ask a human to read before working on a node, not what is guaranteed to be both sufficient and minimal. The agent is made aware of what exists; it is not prevented from exploring further. This is a more targeted version of constitutions and steering documents — tailored to each node the agent accesses, not applied globally.

The Spec Tree makes the state of the product readable — which assertions hold, which are stale, which have no evidence yet — and ensures every agent works from the same deterministic context.

## What's next

This post introduced the Spec Tree as a structure — one that encodes what users should be able to do (specs with assertions) and what has been validated (lock files with blob hashes). The tree can always be reconstructed from the product level down because the structure is the specification; what is lost in reconstruction is the validation state, which `spx lock` regenerates by running tests.

The next posts will cover the agent skills that make this structure operational — how agents maintain, review, and remediate code within the constraints the tree defines — and how the methodology extends beyond the repo to connect assertion-level validation to product-level outcomes.
