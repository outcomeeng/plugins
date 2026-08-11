<contents>

- `<overview>` — the progression and the predicate rule every example keeps
- `<source_contract_values>` — source-owned case values
- `<named_typical_cases>` — one named category per test
- `<named_edge_cases>` — boundary cases kept separate
- `<systematic_coverage>` — iteration over a source-owned enumeration
- `<property_coverage>` — generator domain, harness run policy, test-owned invariant
- `<ordering_strategy>` — trivial to complex
- `<anti_patterns>` — rejections

</contents>

<overview>
Move from named, inspectable cases to broader coverage without losing the ability to diagnose failures quickly.

Every example below keeps the assertion macro in the `#[test]` body. A harness supplies setup, resources, and property-run policy; a generator supplies the domain; the source module owns the case values and the expected results. A harness call that both acts and judges hides the predicate and is rejected.
</overview>

<source_contract_values>
Keep reusable source-owned values in source modules and reusable generated domains in `<product>-testing`.

```rust
use product::inputs::{simple_input_case, Status};

#[test]
fn processes_simple_input() {
    let processed = process(simple_input_case()).unwrap();

    assert_eq!(processed.status, Status::Accepted);
}
```

</source_contract_values>

<named_typical_cases>

```rust
use product::inputs::{unicode_input_case, Status};

#[test]
fn processes_unicode_input() {
    let processed = process(unicode_input_case()).unwrap();

    assert_eq!(processed.status, Status::Accepted);
}
```

Each failure names a concrete category, so the failing case is immediately inspectable.
</named_typical_cases>

<named_edge_cases>

```rust
use product::inputs::empty_input_case;
use product::ProcessError;

#[test]
fn rejects_empty_input() {
    let rejected = process(empty_input_case());

    assert!(matches!(rejected, Err(ProcessError::Empty)));
}
```

Keep boundary cases separate from the happy path. A failing edge case should say exactly which boundary broke.
</named_edge_cases>

<systematic_coverage>
Iterate the source-owned enumeration once the individual scenarios are already clear. The source module owns both the input and the expected result, so the loop adds coverage without the test author inventing a case.

```rust
use product::inputs::KNOWN_CASES;

#[test]
fn processes_known_cases() {
    for case in KNOWN_CASES {
        let processed = process(case.input).unwrap();

        assert_eq!(processed.status, case.expected_status, "case {}", case.name);
    }
}
```

</systematic_coverage>

<property_coverage>
Use `proptest` for true universal claims. The harness owns case count, seed, regression persistence, and replay output; the closure owns the invariant.

```rust
use <product>_testing::generators::keys::canonical_key_strings;
use <product>_testing::harnesses::properties::run_property;

#[test]
fn canonical_key_roundtrips() {
    run_property(canonical_key_strings(), |raw| {
        let parsed = CanonicalKey::parse(&raw).unwrap();

        prop_assert_eq!(parsed.to_string(), raw);
        Ok(())
    });
}
```

</property_coverage>

<ordering_strategy>
Run tests from trivial to complex:

1. import and environment checks
2. named typical cases
3. named edge cases
4. table-driven coverage
5. property tests

</ordering_strategy>

<anti_patterns>

- a harness call that both acts and judges, so the `#[test]` body carries no assertion macro
- starting with property tests when no named regression cases exist
- anonymous inline fixtures with no category name
- mocks that assert collaborator calls instead of governed behavior
- source-text inspection in tests
- random generators without reproducibility or a clear invariant

</anti_patterns>
