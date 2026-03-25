<overview>
Every assertion in a node spec must be one of five structured types. The first four are machine-testable. Compliance captures constraints requiring human or agent judgment.

| Type            | Quantifier                      | Test strategy   | Use when                                      |
| --------------- | ------------------------------- | --------------- | --------------------------------------------- |
| **Scenario**    | There exists (this case works)  | Example-based   | Specific user journey or interaction          |
| **Mapping**     | For all over a finite set       | Parameterized   | Input-output correspondence over known values |
| **Conformance** | External oracle                 | Tool validation | Must match an external standard or schema     |
| **Property**    | For all over a type/value space | Property-based  | Invariant that must hold for all valid inputs |
| **Compliance**  | ALWAYS/NEVER behavioral rules   | Review or test  | Constraints from decisions, semantic rules    |

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

**Test strategy:** Review (`[review]`) for semantic constraints requiring human or agent judgment. Test (`[test]`) when the constraint is automatable (e.g., string absence).

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
- Given a tree with all realized children, when status is computed, parent reports realized ([test](tests/status.unit.test.{ext}))

### Mappings

- HTTP status mapping: 200 = success, 404 = not-found, 422 = invalid ([test](tests/api.unit.test.{ext}))

### Properties

- Status rollup is deterministic: same tree always produces same status ([test](tests/status.unit.test.{ext}))
```

Only include headings for assertion types that apply.

</mixing_types>
