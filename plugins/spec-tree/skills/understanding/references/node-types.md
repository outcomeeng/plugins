<overview>
The Spec Tree contains two node types. Every directory in the tree (other than the root and `tests/`) is one of these.
</overview>

<enabler>

**Directory suffix:** `.enabler`
**Spec opening:** `PROVIDES ... SO THAT ... CAN ...`
**Purpose:** Infrastructure that would be removed if all its dependents were retired.

Enablers exist to serve other nodes. They provide shared infrastructure, utilities, or foundational capabilities that higher-index siblings and their descendants depend on.

**Examples:**

- Test harness that all other nodes use
- Parser that multiple outcome nodes depend on
- State machine that several features build on
- Shared configuration or bootstrap logic

**When to create an enabler:**

- Two or more sibling nodes share a need → invoke `/decomposing` to factor it into a shared enabler and assign placement
- Infrastructure that has no direct user-facing value but enables user-facing value
- Removing it would break its dependents

See `templates/nodes/enabler-name.md` for the spec format.

</enabler>

<outcome>

**Directory suffix:** `.outcome`
**Spec opening:** `WE BELIEVE THAT ... WILL ... CONTRIBUTING TO ...`
**Purpose:** A bet on which output achieves a desired user behavior change. The word "hypothesis" means genuine uncertainty — you don't know which output achieves it.

The hypothesis has three parts:

- **Output** — what the software does. Assertions specify this. Locally verifiable by tests or review.
- **Outcome** — measurable change in user behavior the output is expected to produce. Requires real users to validate.
- **Impact** — business value: increase revenue, sustain revenue, reduce costs, or avoid costs.

Assertions specify the **output** — not the outcome or impact. You can test what the software does; you can only hypothesize about the user behavior change and business value it leads to.

**The key property of an outcome:** The majority of assertions could change while the hypothesis stays the same. A landing page that doesn't convert gets redesigned — different assertions, same outcome hypothesis. The hypothesis is stable; the output is experimental.

**When to create an outcome:**

- You cannot fully specify the output because the right design is uncertain
- The same goal could be achieved by a fundamentally different set of assertions
- You are making a bet: "this output will cause this behavior change"

**When NOT to create an outcome:**

- The output is fully determined by its specification (use an enabler)
- The assertions are stable and grow only by addition (use an enabler)
- You find yourself forcing the hypothesis (e.g., "WE BELIEVE THAT providing timestamps WILL cause agents to...") — if the hypothesis feels forced, the node is an enabler

See `templates/nodes/outcome-name.md` for the spec format.

</outcome>

<nesting_rules>

Only two parent-child combinations are valid for directory-level children (nodes):

| Parent  | Valid child nodes     |
| ------- | --------------------- |
| Outcome | Enablers and outcomes |
| Enabler | Enablers only         |

Decision records (ADR/PDR) are files within a node directory, not child nodes. Both enablers and outcomes can contain `.adr.md` and `.pdr.md` files.

**Enablers CANNOT contain outcome children.** An enabler provides infrastructure — its internals decompose into more infrastructure, never into bets. If a child has genuine uncertainty about which output achieves a desired behavior change, either the parent is mis-typed (should be an outcome) or the child is mis-typed (should be an enabler).

**Diagnostic:** If placing an outcome under an enabler, ask whether the child's output is fully determined by its specification. If yes — if the assertions are stable and grow only by addition — it is an enabler. Invoke `/decomposing` for full structure decisions.

</nesting_rules>

<common_structure>

**Directory structure:**

```text
NN-slug.{enabler|outcome}/
├── slug.md              # Spec file (no type suffix, no numeric prefix)
├── tests/               # Co-located [test]-lane evidence files
│   ├── {test files}     # Named by product convention (see below)
│   └── ...
├── evals/               # Co-located [eval]-lane directories (optional)
│   └── {rule-slug}/     # One directory per [eval] assertion
│       ├── eval.toml    # Definition: title, cases, prompt, threshold, trials
│       ├── cases.jsonl  # Durable case data
│       ├── prompt.md    # Prompt template
│       ├── history.jsonl    # Append-only run summaries (committed)
│       └── runs/        # Full transcripts (gitignored)
├── PLAN.md              # Escape hatch: deferred plan (optional)
├── ISSUES.md            # Escape hatch: known issues (optional)
└── NN-child.{enabler|outcome}/   # Nested child nodes (optional)
```

**Spec file naming:**

- The spec file is always `{slug}.md` — no type suffix, no numeric prefix
- The slug matches the directory name without the numeric prefix and type suffix
- Example: `43-status-rollup.outcome/` contains `status-rollup.md`

**Test files (`[test]` lane):**

- Co-located in `tests/` within the node directory
- Must encode evidence type and execution level in the filename — one evidence type per file
  - evidence ∈ {scenario, mapping, conformance, property, compliance}
  - level ∈ {l1, l2, l3}
- Naming follows the product's language convention, e.g.:
  - TypeScript: `slug.scenario.l1.test.ts`, `slug.property.l1.test.ts`, `slug.conformance.l2.test.ts`
  - Python: `test_slug.scenario.l1.py`, `test_slug.property.l1.py`, `test_slug.conformance.l2.py`
- An optional runner token sits between level and the test extension when a non-default runner applies (e.g., `slug.scenario.l2.playwright.test.ts`)
- Verified by `[test]` evidence

**Eval directories (`[eval]` lane):**

- Co-located in `evals/{rule-slug}/` within the node directory, one directory per `[eval]` assertion
- Each directory carries `eval.toml`, `cases.jsonl`, `prompt.md`, and `history.jsonl` (all committed)
- The `runs/` subdirectory holds full transcripts and is gitignored
- Verified by `[eval]` evidence (the dedicated eval runner)

Assertions specify output, verified by `[test]`, `[eval]`, or `[review]` per `<evidence_mechanisms>` in `assertion-types.md`.

</common_structure>
