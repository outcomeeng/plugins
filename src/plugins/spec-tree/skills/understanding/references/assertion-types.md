<overview>
Every assertion in a node spec must be one of five structured types. The first four default to `[test]` evidence. Compliance assertions choose among `[test]`, `[eval]`, and `[audit]` — `[test]` when an automated test verifies the constraint, `[eval]` when it governs LLM-driven behavior that emits a parseable structured verdict, and `[audit]` when it needs agent judgment with no structural verdict to score (`[review]` is the legacy spelling of `[audit]`, accepted during migration).

| Type            | Quantifier                      | Test strategy        | Use when                                      |
| --------------- | ------------------------------- | -------------------- | --------------------------------------------- |
| **Scenario**    | There exists (this case works)  | Example-based        | Specific user journey or interaction          |
| **Mapping**     | For all over a finite set       | Parameterized        | Input-output correspondence over known values |
| **Conformance** | External oracle                 | Tool validation      | Must match an external standard or schema     |
| **Property**    | For all over a type/value space | Property-based       | Invariant that must hold for all valid inputs |
| **Compliance**  | ALWAYS/NEVER behavioral rules   | Test, eval, or audit | Constraints from decisions, semantic rules    |

</overview>

<scenario>

**Quantifier:** There exists — "this specific case works."

A scenario describes a concrete interaction in natural language.

```markdown
- Given a tree with all valid children, when status is computed, then the parent reports valid ([test](tests/status.scenario.l1.test.{ext}))
```

**Test strategy:** Example-based tests. Each scenario maps to one or more test cases with concrete inputs and expected outputs.

**When to use:** User journeys, specific interactions, error cases, edge cases that need explicit coverage.

</scenario>

<mapping>

**Quantifier:** For all over a finite, enumerable set.

A mapping defines input-output correspondence across a known set of values. Often expressed as a table.

```markdown
- HTTP 200 with JSON body maps to "success" response ([test](tests/api.mapping.l1.test.{ext}))
- HTTP 404 maps to "not found" error ([test](tests/api.mapping.l1.test.{ext}))
- HTTP 422 with validation errors maps to "invalid input" response ([test](tests/api.mapping.l1.test.{ext}))
```

**Test strategy:** Parameterized tests. Each row in the mapping becomes a test case.

**When to use:** State machines, lookup tables, enum-to-behavior mappings, finite configuration spaces.

</mapping>

<conformance>

**Quantifier:** External oracle — "must match what this reference says."

A conformance assertion states that output must match an external standard, schema, or reference.

```markdown
- API response conforms to OpenAPI v3.1 schema ([test](tests/schema.conformance.l1.test.{ext}))
- Output conforms to POSIX exit code conventions ([test](tests/exit-codes.conformance.l1.test.{ext}))
```

**Test strategy:** Tool-based validation. Use schema validators, linters, or comparison against reference output.

**When to use:** Schema compliance, format standards, API contracts, protocol conformance.

</conformance>

<property>

**Quantifier:** For all over a type or value space — "this invariant always holds."

A property assertion states something that must be true for all valid inputs, not just specific examples.

```markdown
- Serialization is deterministic: same input always produces the same output ([test](tests/serialize.property.l1.test.{ext}))
- Ordering is transitive: if A constrains B and B constrains C, then A constrains C ([test](tests/ordering.property.l1.test.{ext}))
```

**Test strategy:** Property-based testing (e.g., Hypothesis for Python, fast-check for TypeScript). Generate random valid inputs and verify the property holds.

**When to use:** Algebraic invariants, idempotency, commutativity, determinism guarantees, "for all valid X, Y holds."

</property>

<compliance>

**Quantifier:** ALWAYS/NEVER — behavioral rules that constrain the node's output.

A compliance assertion states a rule the node's output must always or never exhibit. Some trace back to a PDR or ADR decision; others are intrinsic to the node itself.

```markdown
- ALWAYS: page presents the OSS tier as the full core toolchain — `spx/15-product-offering.pdr.md` positions open-source as complete ([audit])
- NEVER: reference XiperHLS — deferred by `spx/15-product-offering.pdr.md` ([test](tests/open-source.compliance.l1.test.{ext}))
```

**Test strategy:** Audit (`[audit]`) for semantic constraints requiring agent judgment (`[review]` is the legacy form). Test (`[test]`) when the constraint is automatable — including tests that exercise a lint rule against violating fixtures (see `<evidence_mechanisms>`). Eval (`[eval]`) when the constraint governs LLM-driven behavior — a skill's audit verdict, generated content classification, or rule recognition — and the producing skill emits a structurally validatable verdict whose shape the eval declares.

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

<choosing_mechanism>

After choosing the assertion type, choose its evidence lane:

1. Is the behavior a deterministic function of inputs an automated test can drive? → **`[test]`**
2. Is the behavior LLM-driven, and does the producer emit a parseable structured verdict a runner scores against expected fields under a pass threshold? → **`[eval]`**
3. Is it an irreducible semantic constraint a model must judge, with no structural verdict to score? → **`[audit]`**

Prefer `[test]` when behavior is deterministic. Reach for `[eval]` only when `[test]` cannot exercise the behavior but the producer's output has a parseable contract. Fall back to `[audit]` when no structural verdict exists.

The tag `[review]` is the legacy spelling of `[audit]`, not the `reviewing` verification type. `reviewing` is an open-ended gate that backs no assertion lane (see `references/verification-kinds.md`); read `[review]` on an assertion as `[audit]`.

</choosing_mechanism>

<mixing_types>

A single spec can contain assertions of different types. Group them under typed headings:

```markdown
## Assertions

### Scenarios

- Given a tree with one failing child, when status is computed, parent reports failing ([test](tests/status.scenario.l1.test.{ext}))
- Given a tree with all passing children, when status is computed, parent reports passing ([test](tests/status.scenario.l1.test.{ext}))

### Mappings

- HTTP status mapping: 200 = success, 404 = not-found, 422 = invalid ([test](tests/api.mapping.l1.test.{ext}))

### Properties

- Status rollup is deterministic: same tree always produces same status ([test](tests/status.property.l1.test.{ext}))
```

Only include headings for assertion types that apply. Each evidence type lives in its own test file — the filename encodes the evidence type and execution level (`<subject>.<evidence>.<level>[.<runner>].test.{ext}` / `test_<subject>.<evidence>.<level>[.<runner>].{ext}`).

</mixing_types>

<evidence_mechanisms>

Every assertion links to one evidence mechanism — one of the lanes that back assertions, each backed by a verification type (`references/verification-kinds.md`):

| Lane      | Tag                      | Verdict mode  | Verified by    | What it proves                                                                                                                        |
| --------- | ------------------------ | ------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Test**  | `([test](path/to/test))` | deterministic | test runner    | "The code does X" — an automated test drives behavior that is a deterministic function of its inputs                                  |
| **Eval**  | `([eval](path/to/eval))` | deterministic | eval runner    | "The skill identifies X" — a runner scores the producer's parseable structured verdict against expected fields under a pass threshold |
| **Audit** | `([audit])`              | agentic       | auditing skill | "The design follows principle W" — a semantic constraint a model judges, with no structural verdict to score                          |

The `[eval]` verdict is deterministic even though an LLM produces the output: the runner scores the parsed verdict against expected fields, so no model judges the result. `([review])` is the legacy spelling of the `([audit])` lane and migrates to it — both resolve during migration. The tag `[review]` is NOT the `reviewing` verification type: `reviewing` is an open-ended, principal-level gate that backs no assertion lane. The lane↔type mapping is declared in `references/verification-kinds.md`.

**Test** is the default for Scenario, Mapping, Conformance, and Property assertions, and for Compliance rules with automated verification. The test file exercises behavior with direct or indirect coupling to the module under test.

For structural constraints enforced by a lint rule, the `[test]` evidence is a test that exercises the rule against violating fixtures and asserts the violation is detected. The rule's presence in the validation pipeline is a separate operational concern — confirmed by the pipeline running green on the codebase — not by the spec assertion itself.

**Audit** (`[audit]`; `[review]` is its legacy form) is for semantic constraints that no automated check can verify — "the design follows this principle", "the API feels intuitive", "the copy matches brand voice". An audit tag is valid evidence at the time of the audit; it does not re-verify itself as the code changes.

**Eval** is for behavior that depends on LLM outputs but emits a structurally validatable verdict. The `[eval]` link points at an `eval.toml` definition file inside a per-eval directory; the directory carries the case data (`cases.jsonl`), the prompt template (`prompt.md`), and an append-only `history.jsonl` of run summaries. The dedicated eval runner replays the case set through the producing skill, parses the structured verdict against the per-eval expected fields declared in each case, and scores each case against those fields. Non-determinism is bounded by pass@k and threshold gating. Use `[eval]` when `[test]` cannot exercise LLM behavior directly but the producing skill's output has a parseable contract; prefer `[test]` when behavior is deterministic; fall back to `[audit]` when no structural verdict exists.

Sample link form: `[eval](evals/{rule-slug}/eval.toml)`. The runner's CLI (declared per-project, e.g. `outcomeeng-evals`) consumes the `eval.toml`, resolves sibling paths, and writes results next to it.

When an assertion cites a node, ADR, or PDR as its source, cite the full path from `spx/`. Do not use bare shorthand such as `ADR-15`, `PDR-21`, or `15-build.adr.md`; those names are ambiguous because numeric prefixes repeat in different directories.

</evidence_mechanisms>
