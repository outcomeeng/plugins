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

- Two or more sibling nodes share a need → factor it into an enabler at a lower index
- Infrastructure that has no direct user-facing value but enables user-facing value
- Removing it would break its dependents

See `templates/nodes/enabler-name.md` for the spec format.

</enabler>

<outcome>

**Directory suffix:** `.outcome`
**Purpose:** Hypothesis connecting a testable output to a measurable change in user behavior and its expected business impact.

The hypothesis has three parts:

- **Output** — what the software does. Assertions specify this. Locally verifiable by tests or review.
- **Outcome** — measurable change in user behavior the output is expected to produce. Requires real users to validate.
- **Impact** — business value: increase revenue, sustain revenue, reduce costs, or avoid costs.

Assertions specify the **output** — not the outcome or impact. You can test what the software does; you can only hypothesize about the user behavior change and business value it leads to.

**When to create an outcome:**

- The behavior has direct or indirect user-facing value
- You can express a hypothesis about what change its output produces
- You can define assertions that specify the output

See `templates/nodes/outcome-name.md` for the spec format.

</outcome>

<common_structure>

**Directory structure:**

```text
NN-slug.{enabler|outcome}/
├── slug.md              # Spec file (no type suffix, no numeric prefix)
├── tests/               # Co-located test files
│   ├── {test files}     # Named by project convention (see below)
│   └── ...
├── PLAN.md              # Escape hatch: deferred plan (optional)
├── ISSUES.md            # Escape hatch: known issues (optional)
└── NN-child.{enabler|outcome}/   # Nested child nodes (optional)
```

**Spec file naming:**

- The spec file is always `{slug}.md` — no type suffix, no numeric prefix
- The slug matches the directory name without the numeric prefix and type suffix
- Example: `43-status-rollup.outcome/` contains `status-rollup.md`

**Test files:**

- Co-located in `tests/` within the node directory
- Must indicate test level (unit, integration, e2e) in the filename
- Naming follows the project's language convention, e.g.:
  - TypeScript: `slug.unit.test.ts`, `slug.integration.test.ts`
  - Python: `test_slug.unit.py`, `test_slug.integration.py`
- Assertions specify output, verified by test (`[test]`), enforcement (`[enforce]`), or review (`[review]`)

</common_structure>
