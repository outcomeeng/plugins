<overview>
Every assertion in a node spec must be one of five structured types. The first four default to `[test]` evidence. Compliance assertions choose between `[test]`, `[enforce]`, or `[review]` depending on whether the constraint is automatable by tests, by static analysis, or requires human judgment.

| Type            | Quantifier                      | Test strategy            | Use when                                      |
| --------------- | ------------------------------- | ------------------------ | --------------------------------------------- |
| **Scenario**    | There exists (this case works)  | Example-based            | Specific user journey or interaction          |
| **Mapping**     | For all over a finite set       | Parameterized            | Input-output correspondence over known values |
| **Conformance** | External oracle                 | Tool validation          | Must match an external standard or schema     |
| **Property**    | For all over a type/value space | Property-based           | Invariant that must hold for all valid inputs |
| **Compliance**  | ALWAYS/NEVER behavioral rules   | Review, test, or enforce | Constraints from decisions, semantic rules    |

</overview>

<scenario>

**Quantifier:** There exists — "this specific case works."

A scenario describes a concrete interaction in natural language.

```markdown
- Given a tree with all valid children, when status is computed, then the parent reports valid ([test](tests/status.unit.test.{ext}))
```

**Test strategy:** Example-based tests. Each scenario maps to one or more test cases with concrete inputs and expected outputs.

**When to use:** User journeys, specific interactions, error cases, edge cases that need explicit coverage.

</scenario>

<mapping>

**Quantifier:** For all over a finite, enumerable set.

A mapping defines input-output correspondence across a known set of values. Often expressed as a table.

```markdown
- HTTP 200 with JSON body maps to "success" response ([test](tests/api.unit.test.{ext}))
- HTTP 404 maps to "not found" error ([test](tests/api.unit.test.{ext}))
- HTTP 422 with validation errors maps to "invalid input" response ([test](tests/api.unit.test.{ext}))
```

**Test strategy:** Parameterized tests. Each row in the mapping becomes a test case.

**When to use:** State machines, lookup tables, enum-to-behavior mappings, finite configuration spaces.

</mapping>

<conformance>

**Quantifier:** External oracle — "must match what this reference says."

A conformance assertion states that output must match an external standard, schema, or reference.

```markdown
- API response conforms to OpenAPI v3.1 schema ([test](tests/schema.unit.test.{ext}))
- Output conforms to POSIX exit code conventions ([test](tests/exit-codes.unit.test.{ext}))
```

**Test strategy:** Tool-based validation. Use schema validators, linters, or comparison against reference output.

**When to use:** Schema compliance, format standards, API contracts, protocol conformance.

</conformance>

<property>

**Quantifier:** For all over a type or value space — "this invariant always holds."

A property assertion states something that must be true for all valid inputs, not just specific examples.

```markdown
- Serialization is deterministic: same input always produces the same output ([test](tests/serialize.unit.test.{ext}))
- Ordering is transitive: if A constrains B and B constrains C, then A constrains C ([test](tests/ordering.unit.test.{ext}))
```

**Test strategy:** Property-based testing (e.g., Hypothesis for Python, fast-check for TypeScript). Generate random valid inputs and verify the property holds.

**When to use:** Algebraic invariants, idempotency, commutativity, determinism guarantees, "for all valid X, Y holds."

</property>

<compliance>

**Quantifier:** ALWAYS/NEVER — behavioral rules that constrain the node's output.

A compliance assertion states a rule the node's output must always or never exhibit. Some trace back to a PDR or ADR decision; others are intrinsic to the node itself.

```markdown
- ALWAYS: page presents the OSS tier as the full core toolchain — PDR-15 positions open-source as complete ([review](../../15-product-offering.pdr.md))
- NEVER: reference XiperHLS — deferred per PDR-15 ([test](tests/open-source.unit.test.{ext}))
```

**Test strategy:** Review (`[review]`) for semantic constraints requiring human or agent judgment. Test (`[test]`) when the constraint is automatable (e.g., string absence). Enforce (`[enforce]`) when a linter rule in the validation pipeline catches violations (see `<evidence_mechanisms>`).

**When to use:** PDR/ADR compliance rules, semantic constraints that can't be falsified by regex, behavioral boundaries that define what the node must not do.

</compliance>

<choosing_type>

1. Is it a behavioral rule (ALWAYS/NEVER) from a decision or semantic constraint? → **Compliance**
2. Can you enumerate all cases? → **Mapping**
3. Is there an external reference to match? → **Conformance**
4. Must it hold for all inputs (not just examples)? → **Property**
5. Is it a specific interaction or journey? → **Scenario**

When in doubt, start with **Scenario**. Promote to **Mapping** when you discover the domain is finite. Promote to **Property** when you realize the assertion should hold universally. Use **Compliance** when the constraint is about what the node must always or never do.

</choosing_type>

<mixing_types>

A single spec can contain assertions of different types. Group them under typed headings:

```markdown
## Assertions

### Scenarios

- Given a tree with one failing child, when status is computed, parent reports failing ([test](tests/status.unit.test.{ext}))
- Given a tree with all passing children, when status is computed, parent reports passing ([test](tests/status.unit.test.{ext}))

### Mappings

- HTTP status mapping: 200 = success, 404 = not-found, 422 = invalid ([test](tests/api.unit.test.{ext}))

### Properties

- Status rollup is deterministic: same tree always produces same status ([test](tests/status.unit.test.{ext}))
```

Only include headings for assertion types that apply.

</mixing_types>

<evidence_mechanisms>

Every assertion links to one evidence mechanism that verifies it. Three mechanisms exist:

| Mechanism   | Tag                           | Who decides                                 | What it proves                                                            | Verified by   |
| ----------- | ----------------------------- | ------------------------------------------- | ------------------------------------------------------------------------- | ------------- |
| **Test**    | `([test](path/to/test))`      | Automated test (vitest, playwright)         | "The code does X" — exercises behavior with real coupling                 | Test runner   |
| **Enforce** | `([enforce](path/to/config))` | Automated static analysis (ESLint, Semgrep) | "The code never contains Y" or "always uses Z" — constrains structure     | Lint pipeline |
| **Review**  | `([review])`                  | Human or agent judgment                     | "The design follows principle W" — semantic constraint no tool can verify | Audit skill   |

**Test** is the default for Scenario, Mapping, Conformance, and Property assertions. The test file exercises behavior with direct or indirect coupling to the module under test.

**Enforce** is for constraints verified by automated static analysis — ESLint rules, `no-restricted-syntax` selectors, Semgrep patterns. An `[enforce]` tag is NOT a test: a lint rule doesn't import a module or exercise behavior. It walks AST nodes and matches patterns. There's no coupling to a module under test — the rule constrains all files matching a glob. An `[enforce]` tag is NOT a review: a review requires human evaluation, while enforcement is fully automated on every lint invocation with zero human involvement.

The `[enforce]` tag links directly to the file where the enforcement is configured — the ESLint config entry, the custom rule module, or the Semgrep pattern file. It does NOT link to a sibling spec that delegates further.

The evidence chain for `[enforce]`:

1. The assertion in a spec points `[enforce]` at the enforcement mechanism
2. That mechanism must be registered in the pipeline (`eslint.config.ts`, semgrep config, etc.)
3. That mechanism must run as part of `pnpm lint` or `spx validation all`
4. For custom rule modules: the rule itself has separate `[test]` evidence via RuleTester — but that's evidence for the rule's correctness, not for the spec assertion

```markdown
## Example: enforce evidence

# In outcome spec:

- NEVER: use vi.mock() in test files ([enforce](eslint.config.ts))

# In eslint.config.ts:

# The no-restricted-syntax selector catches vi.mock() calls

# Evidence chain: assertion → [enforce] → eslint.config.ts → lint pipeline

# The ESLint rule itself may have RuleTester tests, but those prove the rule works —

# the [enforce] tag proves the constraint is active in the pipeline.
```

**Every `[enforce]` tag must link to a file.** Bare `[enforce]` with no target path is a broken evidence chain — the assertion claims enforcement exists but does not say where.

**The linked file must contain the rule.** An `[enforce]` tag pointing to a file that does not contain or register the enforcement rule is a broken chain — the link exists syntactically but the evidence is not traceable.

</evidence_mechanisms>
