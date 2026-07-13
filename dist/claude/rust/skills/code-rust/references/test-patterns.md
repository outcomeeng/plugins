<overview>
Move from named, inspectable cases to broader coverage without losing the ability to diagnose failures quickly. Code examples use `acme_testing` as the compilable stand-in for the consumer package's `<package>_testing` dev-dependency crate.
</overview>

<source_contract_values>
Keep reusable source-owned values in source modules and reusable generated domains in `<package>-testing`.

```rust
use product::inputs::simple_input_case;

#[test]
fn processes_simple_input() {
    acme_testing::harnesses::processing::assert_processes_case(simple_input_case(), process);
}
```

</source_contract_values>

<named_typical_cases>

```rust
#[test]
fn processes_simple_input() {
    acme_testing::harnesses::processing::assert_processes_case(simple_input_case(), process);
}
```

Each failure names a concrete category, so the failing case is immediately inspectable.
</named_typical_cases>

<named_edge_cases>

```rust
#[test]
fn rejects_empty_input() {
    acme_testing::harnesses::processing::assert_rejects_empty_input(process);
}
```

Keep boundary cases separate from the happy path. A failing edge case should say exactly which boundary broke.
</named_edge_cases>

<systematic_coverage>
Use a harness assertion over named cases once the individual scenarios are already clear.

```rust
#[test]
fn processes_known_cases() {
    acme_testing::harnesses::processing::assert_processes_known_cases(
        acme_testing::generators::processing::known_process_cases(),
        process,
    );
}
```

</systematic_coverage>

<property_coverage>
Use `proptest` for true universal claims.

```rust
#[test]
fn canonical_key_roundtrips() {
    acme_testing::harnesses::properties::assert_canonical_key_roundtrips(
        acme_testing::generators::keys::canonical_key_strings(),
        CanonicalKey::parse,
    );
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
