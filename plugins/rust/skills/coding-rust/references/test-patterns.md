<overview>
Move from named, inspectable cases to broader coverage without losing the ability to diagnose failures quickly.
</overview>

<shared_fixture_values>
Keep reusable values in a fixture module close to the governed tests.

```rust
pub struct Case<I, E> {
    pub input: I,
    pub expected: E,
}

pub fn typical_cases() -> Vec<Case<&'static str, usize>> {
    vec![
        Case {
            input: "simple",
            expected: 6,
        },
        Case {
            input: "with-flags",
            expected: 10,
        },
    ]
}
```

</shared_fixture_values>

<named_typical_cases>

```rust
#[test]
fn processes_simple_input() {
    let case = &typical_cases()[0];

    let result = process(case.input);

    assert_eq!(result, case.expected);
}
```

Each failure names a concrete category, so you can inspect the case immediately.
</named_typical_cases>

<named_edge_cases>

```rust
#[test]
fn rejects_empty_input() {
    let result = process("");
    assert!(result.is_err());
}
```

Keep boundary cases separate from the happy path. A failing edge case should say exactly which boundary broke.
</named_edge_cases>

<systematic_coverage>
Use `rstest` or a loop over named cases once the individual scenarios are already clear.

```rust
#[rstest::rstest]
#[case("simple", 6)]
#[case("with-flags", 10)]
fn processes_known_cases(#[case] input: &str, #[case] expected: usize) {
    assert_eq!(process(input).unwrap(), expected);
}
```

</systematic_coverage>

<property_coverage>
Use `proptest` for true universal claims.

```rust
proptest! {
    #[test]
    fn canonical_key_roundtrips(input in "[a-z0-9_-]{1,32}") {
        let parsed = CanonicalKey::parse(&input).unwrap();
        prop_assert_eq!(parsed.as_str(), input);
    }
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

- starting with property tests when no named regression cases exist
- anonymous inline fixtures with no category name
- mocks that assert collaborator calls instead of governed behavior
- source-text inspection in tests
- random generators without reproducibility or a clear invariant

</anti_patterns>
