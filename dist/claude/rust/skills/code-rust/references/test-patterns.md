<contents>

- `<overview>` — the progression and the predicate rule every example keeps
- `<source_contract_values>` — source-owned expected results beside a spec-declared case
- `<one_scenario_per_test>` — one spec scenario per test
- `<boundary_cases>` — boundary cases the spec or rule names
- `<systematic_coverage>` — iteration over the finite domain production owns
- `<property_coverage>` — generator domain, harness run policy, test-owned invariant
- `<ordering_strategy>` — trivial to complex
- `<anti_patterns>` — rejections

</contents>

<overview>
Move from named, inspectable cases to broader coverage without losing the ability to diagnose failures quickly.

Every example below keeps the assertion macro in the `#[test]` body. A harness supplies setup, resources, and property-run policy; a generator supplies the domain; the source module owns the vocabulary the expectation is written in. A scenario's own case is the interaction the spec declares, transcribed into the test — adding it to a production module so the test can import it gives the case a production address without giving it a production contract.
</overview>

<source_contract_values>
Keep reusable source-owned values in source modules and reusable generated domains in `<product>-testing`. `Status` is source-owned because production returns it; the input is the interaction the governing scenario declares.

```rust
use product::Status;

#[test]
fn processes_simple_input() {
    let processed = process("id=42;kind=widget").unwrap();

    assert_eq!(processed.status, Status::Accepted);
}
```

</source_contract_values>

<one_scenario_per_test>
One spec scenario per test, named for the interaction it carries. A second scenario is a second spec assertion, never a second member of a "typical case" set the test author assembled.

```rust
use product::Status;

#[test]
fn processes_unicode_input() {
    let processed = process("id=42;kind=wîdget").unwrap();

    assert_eq!(processed.status, Status::Accepted);
}
```

Each failure names a concrete interaction, so the failing case is immediately inspectable.
</one_scenario_per_test>

<boundary_cases>
A boundary case is evidence when the spec declares it or the governing rule names it as a violating input. `ProcessError::Empty` is the source-owned rejection contract; the empty input is what the rule names.

```rust
use product::ProcessError;

#[test]
fn rejects_empty_input() {
    let rejected = process("");

    assert!(matches!(rejected, Err(ProcessError::Empty)));
}
```

Keep boundary cases separate from the happy path. A failing boundary case must say exactly which boundary broke.
</boundary_cases>

<systematic_coverage>
Iterate the finite domain production owns once the individual scenarios are already clear. Production dispatches on `INPUT_KINDS` and encodes through its own encoder, so the loop covers the whole mapping and the expectation derives from the input rather than from a case table the test author wrote beside it.

```rust
use product::inputs::{encode, INPUT_KINDS};

#[test]
fn every_registered_kind_round_trips() {
    for kind in INPUT_KINDS {
        let processed = process(&encode(kind)).unwrap();

        assert_eq!(processed.kind, *kind, "kind {kind:?}");
    }
}
```

A generator belongs to a property assertion, where the harness owns the seed and reports the replay input. Sampling one generated value inside an ordinary `#[test]` reports no seed, so the failing case is gone on the next run.

</systematic_coverage>

<property_coverage>
Use `proptest` for true universal claims. The harness owns case count, seed, regression persistence, and replay output; the closure owns the invariant.

```rust
use proptest::prop_assert_eq;
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
- a case value moved into a production module solely so a test can cite that module as its import path
- starting with property tests when no named regression cases exist
- anonymous inline fixtures with no category name
- mocks that assert collaborator calls instead of governed behavior
- source-text inspection in tests
- random generators without reproducibility or a clear invariant

</anti_patterns>
