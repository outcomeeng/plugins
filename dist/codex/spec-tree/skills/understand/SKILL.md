---
name: understand
description: >-
  ALWAYS invoke this skill when the live SPEC_TREE_FOUNDATION marker is absent
  before direct filesystem access under spx/ or before reading, searching,
  listing, or changing source or test files. NEVER access that product content
  without loading this skill first.
allowed-tools: Read, Glob, Grep
---

<objective>

The complete Spec Tree foundation loaded eagerly in one skill payload and recorded by a live `<SPEC_TREE_FOUNDATION>` marker.

</objective>

<truth_hierarchy>

**TRUTH FLOWS DOWN.** The Spec Tree is a durable, declarative map of what the product does. Its four layers depend on the layer above:

```text
PDR/ADR  →  Spec  →  Test  →  Code
governs     declares   verifies   complies
```

- PDRs and ADRs decide product and architecture truth.
- Specs declare product output in alignment with those decisions.
- Tests are executable evidence derived from specs.
- Code complies with tests.

When layers disagree, the lower layer is in violation.

- NEVER: weaken a decision to match a spec, a spec to match tests, or tests to match code.

Higher-level truth may lead implementation. A coherent product spec, PDR, ADR, or ancestor spec stays authoritative when lower specs, tests, or code have not caught up. Evaluate declaration validity separately from implementation completeness. Current code shape is evidence about code, never authority over higher layers.

When a higher-level artifact changes, align every first affected lower spec in the same changeset. If tests or code remain, record the concrete next step and governing artifact in `PLAN.md` at the first affected lower node. Use `ISSUES.md` for known defects or contradictions. Use `spx/EXCLUDE` only when a node has specs and tests while implementation is absent; exclusion never resolves a conceptual disagreement or permits lower layers to contradict decisions.

Specs declare atemporal truth. Eliminate history and journey language:

| Temporal                           | Atemporal                |
| ---------------------------------- | ------------------------ |
| “We discovered that X”             | “X ensures Y”            |
| “We need to address X”             | “The product provides X” |
| “Currently, the system…”           | “The system…”            |
| “After investigating, we decided…” | “The decision governs…”  |
| “This was introduced because…”     | “The output enables…”    |

Read every spec sentence aloud. If it would sound wrong after the work ships, rewrite it.

Writing a spec makes a declaration. Writing linked evidence makes the declaration verifiable. Removing a spec prunes product truth. The following backlog operations do not exist:

- close, archive, or move a spec to done;
- assign or store a spec status;
- mark a declaration complete by hand;
- weaken a declaration to match its implementation.

A node's state is derived:

- **Declared** — spec exists, no evidence.
- **Specified** — spec and evidence exist while implementation is absent; the node is covered by `spx/EXCLUDE`.
- **Failing** — implementation exists and evidence fails.
- **Passing** — implementation exists and evidence passes.

Specified and failing are valid states. They expose where lower layers must catch up.

</truth_hierarchy>

<node_model>

The tree contains exactly two recursive node types.

**Enabler**

- Directory suffix: `.enabler`
- Spec opening: `PROVIDES ... SO THAT ... CAN ...`
- Purpose: infrastructure removed when all dependents retire.
- Use for shared infrastructure, deterministic capabilities, and output whose assertions are stable and grow by addition.

**Outcome**

- Directory suffix: `.outcome`
- Spec opening: `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`
- Purpose: a bet that one output will produce a measurable user-behavior change contributing to business impact.
- Assertions specify the output. The outcome and impact remain hypotheses requiring real users.
- Use when material uncertainty remains about which output achieves the goal and most assertions could change while the hypothesis stays stable.

Apply the forcing question before choosing an outcome: why can this not be written as `PROVIDES X SO THAT Y CAN Z`? A forced hypothesis signals an enabler.

Valid node nesting:

| Parent  | Child nodes           |
| ------- | --------------------- |
| Outcome | Enablers and outcomes |
| Enabler | Enablers only         |

An enabler can never contain an outcome. If a proposed child under an enabler carries material output uncertainty, either the parent is mistyped or the child is an enabler whose output is fully determined.

Canonical node shape:

```text
NN-{slug}.{enabler|outcome}/
├── {slug}.md
├── tests/                              # when the first [test] file exists
├── evals/{rule-slug}/                  # when the first [eval] exists
├── PLAN.md                             # optional
├── ISSUES.md                           # optional
└── NN-{child-slug}.{enabler|outcome}/
```

- The spec file is `{slug}.md`, with no numeric or type suffix.
- `[test]` evidence is co-located under `tests/`; the directory materializes with the first test file, and its filename encodes one assertion type and execution level according to the product's language convention.
- `[eval]` evidence is co-located under `evals/{rule-slug}/` with `eval.toml`, `cases.jsonl`, `prompt.md`, and `history.jsonl`; full run transcripts stay ignored under `runs/`.
- `PLAN.md` and `ISSUES.md` are optional coordination notes, never product truth.
- ADRs and PDRs are files inside a node directory, never child nodes.

</node_model>

<assertion_model>

Assertions specify locally verifiable product output. They derive from decisions and specs, never from tests or code.

Choose the verification type first:

| Type     | Tag            | Verdict                                                 | Use                                                                                 |
| -------- | -------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| test     | `[test](path)` | deterministic                                           | Behavior is a deterministic function of inputs.                                     |
| evaluate | `[eval](path)` | deterministic score over a producer's structured output | LLM-driven behavior emits a parseable verdict scored against cases and a threshold. |
| audit    | `[audit]`      | agentic                                                 | A semantic constraint has no structural verdict to score.                           |

`[review]` is the legacy spelling of the `[audit]` assertion tag. Review itself is an open-ended changeset gate and backs no assertion tag.

Only `[test]` assertions carry one of five assertion types, selected from the quantifier:

| Assertion type | Quantifier                       | Test strategy             | Use                                                     |
| -------------- | -------------------------------- | ------------------------- | ------------------------------------------------------- |
| Scenario       | There exists                     | Example-based             | One concrete interaction, journey, error, or edge case. |
| Mapping        | For all over a finite set        | Parameterized             | Known input-output or state correspondence.             |
| Conformance    | External or internal oracle      | Validator/tool comparison | Schema, protocol, or declared contract.                 |
| Property       | For all over an open value space | Property-based            | Invariant for every valid input.                        |
| Compliance     | ALWAYS/NEVER rule                | Violating fixtures        | A deterministic behavioral boundary.                    |

A universal is never a scenario. Under `[test]`, choose mapping for a finite source-owned domain, conformance for an oracle, compliance for a rule exercised against violations, and property for an open domain. Choose scenario only for one existential interaction. Evaluate and audit carry no assertion type.

Prefer `[test]` when behavior is deterministic. Use `[eval]` when the real LLM-driven producer emits a parseable contract that a runner can score. Use `[audit]` when no deterministic or structural verdict exists.

Structural lint constraints use `[test]` evidence that runs the rule against violating fixtures and proves detection. Pipeline inclusion is a separate operational concern established by the validation gate.

Group mixed `[test]` assertions by type. Each test file carries one assertion type. Every node, test, ADR, or PDR citation uses its full path from `spx/`.

</assertion_model>

<ordering_model>

All indexed artifacts inside one directory—nodes, ADRs, and PDRs—share one numeric namespace. Prefixes are sibling-local and drive deterministic context loading:

- Lower-index siblings constrain the target and their specs are read.
- Same-index siblings are independent peers; list them without reading them as constraints.
- Higher-index siblings may depend on the target; list them without reading them as constraints.
- A lower-index ADR or PDR constrains higher-index siblings and descendants.

Index assignment is the inverse of this read rule. Giving a new child a higher index declares that each lower-index sibling must be present in its future context. Giving peers the same index declares independence. `/decompose` owns assignment because it must prove the dependency consequence before choosing an index.

Always use complete `spx/...` paths. `32-parser.enabler` and `15-build.adr.md` are ambiguous because other directories may reuse both prefixes.

</ordering_model>

<verification_model>

Verification has five fixed types over two independent axes.

**Verdict mode**

- **Deterministic** — a command scores fixed expectations and returns pass or fail; no model judges the result.
- **Agentic** — Claude applies a skill and judges the subject, from checklist audit to open-ended review.

**Purpose**

- **Conformance** — fit to methodology, language standards, and validation configuration.
- **Correctness** — integrity of the decision → spec → evidence → implementation chain.

The five types are:

- **audit** — agentic conformance or mechanical correctness judgment; backs `[audit]`.
- **validate** — deterministic conformance through format, lint, typing, and static-analysis gates; backs no assertion tag.
- **review** — agentic open-ended correctness judgment over quality, architecture, risk, and layer consistency; backs no assertion tag.
- **evaluate** — deterministic scoring of structured producer output; backs `[eval]`.
- **test** — deterministic execution of behavior; backs `[test]`.

Every verification activity declares its type and purpose. A type's verdict mode is fixed. A model never judges a deterministic verdict. The type set and the two verdict modes never expand without amending this foundation and its governing decision.

When vocabulary overlaps another grammar, resolve verification vocabulary here first and inspect history before classifying a name as defective. Generated output and implementation names are lower-layer evidence.

</verification_model>

<imperfection_protocol>

Record every observed defect in the current-turn ledger immediately: failing validation, broken link, stale reference, dead code, lint violation, missing evidence, inconsistent naming, misplaced file, wrong index, harmful warning, or any other incoherence. Each entry carries:

- the exact imperfection;
- the path, line, command output, or external state that exposed it;
- the skill or workflow governing the fix;
- the proposed handling and current classification.

Apply clear, local, low-risk corrections immediately. Surface a blocking decision through the structured-question tool. Hold a non-blocking decision only until the next natural checkpoint.

The ledger has no origin distinction. Age and authorship never reduce responsibility. Never dismiss a defect as inherited, already broken, or outside the current change merely because another change created it.

Debt the current change causes, surfaces, or invalidates is fix-now wherever it lives. A change invalidates another file when it removes a symbol that file references, enforces a rule it violates, falsifies its guidance, or causes a gate, audit, or review to expose its defect. Location never licenses deferral.

Record and proceed only for work independent of the current change in a surface the change neither touches nor invalidates. Persist that work at the correct tier: decision/spec for durable truth, methodology for reusable workflow, `PLAN.md` for pending node work, and `ISSUES.md` for known node defects. Recording never ends an otherwise actionable session.

Command defaults are authority for cost-bearing and quota-bearing runs. Never raise an explicit or implicit spend, token, worker, retry, timeout, hosted-runner, paid-provider, or external-capacity ceiling without operator approval in the same turn. When a default ceiling blocks a run, report the exact command, ceiling, proposed increase, expected rerun scope, and pause/inspect option.

Apply the closing test at task completion: can the operator reasonably ask “What now?”

- When the stated goal remains actionable, continue the governing workflow.
- A passing check, merge, clean worktree, or persisted note is a milestone, never permission to stop while do-able work remains.
- Run `/handoff` only when the goal is met with no continuation remaining or continuation is impossible because the operator halted work, context is exhausted, or an external blocker prevents the next action.
- Never write `PLAN.md` or a session file to postpone work Claude can perform now.
- When operator judgment is required, close with the structured-question tool rather than a prose offer.

The ledger is conversation-local. Fixed entries disappear. Unresolved entries persist only through the correct durable or coordination artifact. Session files under `.spx/` carry ephemeral initialization context and remain outside Git.

</imperfection_protocol>

<coordination_and_context>

- ALWAYS: `/contextualize` derives deterministic context from tree structure, never keyword search. It loads product truth, ancestry, lower-index constraints, decisions, cited governance, guides, coordination notes, and lifecycle routing for one canonical target.

Coordination notes are stale-prone inputs. Reconcile every loaded `PLAN.md` or `ISSUES.md` against current decisions, specs, evidence, implementation, and user intent before acting. They never declare product truth or cited governance.

`spx/local/` holds product-specific overlays for coding, architecture, testing, and lifecycle skills. Enumerate overlays during context loading and read each only when its governing skill requires it. `spx/local/merging.md` is the optional lifecycle overlay read by `/merge` and `/contextualize`.

</coordination_and_context>

<delivery_boundary>

- ALWAYS: no value is delivered until the changeset reaches the default branch on origin through `/merge`. Local edits, tests, audits, reviews, commits, pushes, and clean branches are checkpoints.

After verification and any successful commit or push, continue through `/merge` unless the operator explicitly limited the request to proposal, analysis, review, branch-only, or local-only work. A terse “continue,” “ship it,” or “finish” continues the active lifecycle.

A blocker exists only when the immediate next action needs operator input or an external state change, every independent local action is complete, and the applicable gates have run or produced concrete failing evidence.

</delivery_boundary>

<workflow>

1. Load this complete inline foundation on every invocation. A marker in a compaction summary, session file, handoff note, or prior-run statement does not count. After compaction, treat the marker as absent until this workflow emits it again.
2. Check internal consistency across `<truth_hierarchy>`, `<node_model>`, `<assertion_model>`, `<ordering_model>`, `<verification_model>`, and `<imperfection_protocol>`. Surface any contradiction immediately. No mandatory foundation reference read follows this step.
3. Locate these operational references and list their paths without reading them until another skill needs them:
   - `references/what-goes-where.md`
   - `references/excluded-nodes.md`
   - `references/product-domain-shapes.md`
   - node-local `PLAN.md` and `ISSUES.md`
   - `spx/local/*.md`
     Also locate the legacy compatibility pointers `references/durable-map.md`, `references/node-types.md`, `references/assertion-types.md`, `references/ordering-rules.md`, `references/verification-kinds.md`, and `references/imperfection-protocol.md`. Never read them as foundation content; each redirects old links to the canonical inline section in this file.
4. Read `spx/local/merging.md` when present. Changes destined for the default branch route through `/merge`; absence of the overlay applies the default lifecycle.
5. Locate the five authoring templates and `examples/*.md`; read them only when authoring:
   - `templates/product/product-name.product.md`
   - `templates/decisions/decision-name.adr.md`
   - `templates/decisions/decision-name.pdr.md`
   - `templates/nodes/enabler-name.md`
   - `templates/nodes/outcome-name.md`
6. Read the complete root `AGENTS.md` once when present. It routes skill invocation and carries product commands outside the managed router.
7. Emit the marker:

```text
<SPEC_TREE_FOUNDATION>
Loaded inline: truth-hierarchy, node-model, assertion-model, ordering-model, verification-model, imperfection-protocol
Operational references available: what-goes-where, excluded-nodes, product-domain-shapes
Local lifecycle route: changes route through /merge; spx/local/merging.md refines the route when present
Default-branch completion boundary: delivered value reaches the default branch on origin through /merge; verified local work remains unfinished unless explicitly limited or stopped at an explicit gate with no independent action remaining
Routing guide: loaded from AGENTS.md | absent
Templates available: product, adr, pdr, enabler, outcome
Examples available in: examples/
</SPEC_TREE_FOUNDATION>
```

</workflow>

<failure_modes>

**Mandatory references made progressive disclosure fictional.**

Claude loaded `SKILL.md`, then opened six references required on every fresh invocation. One aggregate read truncated, forcing repeat reads and making the nominal overview/reference split slower than one complete payload.

Keep unconditional foundation truth inline and govern the total eager payload. Reserve references for conditional operational detail, templates, and examples.

**Higher-level truth was shaped to current code.**

Claude treated implementation incompleteness as evidence against a coherent decision. Preserve the higher declaration, align the first affected lower specs, and record concrete lower-layer work.

**A pushed branch was reported as complete.**

Claude treated a transport checkpoint as delivered value. Continue through `/merge` until the changeset reaches the default branch on origin or an explicit gate blocks every remaining independent action.

</failure_modes>

<success_criteria>

- The six foundation domains are present inline and require no secondary file reads.
- Internal foundation sections contain no contradiction in truth flow, node grammar, assertion selection, ordering, verification vocabulary, or imperfection handling.
- Operational references, templates, examples, overlays, and the root guide are located or read according to the workflow.
- A live `<SPEC_TREE_FOUNDATION>` marker records the inline payload.

</success_criteria>
