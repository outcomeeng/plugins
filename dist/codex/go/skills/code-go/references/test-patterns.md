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

Every example below keeps the comparison and the `testing.T` failure call in the `Test*` body. A harness supplies setup, resources, and property-run policy; a generator supplies the domain; the source package owns the vocabulary the expectation is written in. A scenario's own case is the interaction the spec declares, transcribed into the test — adding it to a production package so the test can import it gives the case a production address without giving it a production contract.
</overview>

<source_contract_values>
Keep reusable source-owned values in source packages and reusable generated domains in `internal/testinfra/`. `Status` is source-owned because production returns it; the input is the interaction the governing scenario declares.

```go
func TestProcessesSimpleInput(t *testing.T) {
    processed, err := process.Run("id=42;kind=widget")
    if err != nil {
        t.Fatalf("Run: %v", err)
    }

    if processed.Status != process.StatusAccepted {
        t.Errorf("Status: got %v, want %v", processed.Status, process.StatusAccepted)
    }
}
```

</source_contract_values>

<one_scenario_per_test>
One spec scenario per test, named for the interaction it carries. A second scenario is a second spec assertion, never a second member of a "typical case" set the test author assembled.

```go
func TestProcessesUnicodeInput(t *testing.T) {
    processed, err := process.Run("id=42;kind=wîdget")
    if err != nil {
        t.Fatalf("Run: %v", err)
    }

    if processed.Status != process.StatusAccepted {
        t.Errorf("Status: got %v, want %v", processed.Status, process.StatusAccepted)
    }
}
```

Each failure names a concrete interaction, so the failing case is immediately inspectable.
</one_scenario_per_test>

<boundary_cases>
A boundary case is evidence when the spec declares it or the governing rule names it as a violating input. `process.ErrEmpty` is the source-owned rejection contract; the empty input is what the rule names.

```go
func TestRejectsEmptyInput(t *testing.T) {
    _, err := process.Run("")

    if !errors.Is(err, process.ErrEmpty) {
        t.Fatalf("Run: got %v, want %v", err, process.ErrEmpty)
    }
}
```

Keep boundary cases separate from the happy path. A failing boundary case must say exactly which boundary broke.
</boundary_cases>

<systematic_coverage>
Iterate the finite domain production owns once the individual scenarios are already clear. Production dispatches on `inputs.Kinds` and encodes through its own encoder, so the loop covers the whole mapping and the expectation derives from the input rather than from a case table the test author wrote beside it.

```go
func TestEveryRegisteredKindRoundTrips(t *testing.T) {
    for _, kind := range inputs.Kinds {
        t.Run(kind.String(), func(t *testing.T) {
            processed, err := process.Run(inputs.Encode(kind))
            if err != nil {
                t.Fatalf("Run: %v", err)
            }

            if processed.Kind != kind {
                t.Errorf("Kind: got %v, want %v", processed.Kind, kind)
            }
        })
    }
}
```

A generator belongs to a property assertion, where the harness owns the seed and reports the replay input. Drawing one generated value inside an ordinary `Test*` function reports no seed, so the failing case is gone on the next run.

</systematic_coverage>

<property_coverage>
Use `rapid` for true universal claims. The harness owns check count, seed, and replay output; the closure owns the invariant.

```go
import (
    "pgregory.net/rapid"

    "<module>/internal/testinfra/generators"
    "<module>/internal/testinfra/harnesses"
)

func TestCanonicalKeyRoundTrips(t *testing.T) {
    harnesses.RunProperty(t, generators.CanonicalKeyStrings(), func(t *rapid.T, raw string) {
        parsed, err := keys.Parse(raw)
        if err != nil {
            t.Fatalf("Parse(%q): %v", raw, err)
        }

        if got := parsed.String(); got != raw {
            t.Fatalf("String: got %q, want %q", got, raw)
        }
    })
}
```

</property_coverage>

<ordering_strategy>
Run tests from trivial to complex:

1. import and environment checks
2. named typical cases
3. named edge cases
4. table-driven coverage over a source-owned enumeration
5. property tests

</ordering_strategy>

<anti_patterns>

- a `t.Helper()` function that both acts and judges, so the `Test*` body carries no comparison
- a case value moved into a production package solely so a test can cite that package as its import path
- a table literal of author-invented rows presented as a mapping
- starting with property tests when no named regression cases exist
- anonymous inline fixtures with no category name
- mocks that assert collaborator calls instead of governed behavior
- source-text inspection in tests
- random generators without reproducibility or a clear invariant

</anti_patterns>
