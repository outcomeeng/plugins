<overview>

Detailed evidence model for test auditing. Read this before auditing any test file.

Evidence design establishes whether the proposed proof shape can carry the assertion. Four downstream properties then define executed test evidence: coupling, falsifiability, alignment, and coverage. This reference provides the design reconstruction, reference contract, taxonomy, verification procedures, and concrete examples.

</overview>

<table_of_contents>

- `<coupling_taxonomy>` — coupling categories and examples
- `<evidence_design_model>` — independent pre-test reconstruction and defect classes
- `<reference_validation>` — role-specific traceability contract
- `<coupling_verification>` — import and execution-path coupling procedure
- `<test_file_declaration_model>` — test-file ownership screening before coupling
- `<falsifiability_model>` — mutation analysis and double exceptions
- `<alignment_verification>` — assertion-to-expectation alignment
- `<coverage_protocol>` — coverage-by-reading procedure

</table_of_contents>

<evidence_design_model>

Reconstruct the evidence design from the governing declaration and the live evidence chain. The packet produced during authoring is useful context and never proof. For each assertion, determine:

1. The assertion quantifier and domain: existential, finite source-owned, external contract, open, or composable.
2. The independent oracle that decides the expected result without asking the implementation under test.
3. A concrete condition under which the evidence could pass while the assertion remained false.
4. Execution level from dependency availability and execution pain.
5. Required source contracts and whether their implementation exists.
6. Required harness responsibilities: setup, teardown, cleanup, real-behavior access, seed policy, replay, and diagnostics.
7. Required generator behavior: meaningful variation, composition, shrinking, or systematic exploration.
8. Fixture status: absent, rejected shape, or inert whole-payload candidate with scoped operator approval.
9. Property replay path: harness-owned seed or replay input plus failure diagnostics.

An open or composable input space defaults to generated or property-based evidence. Fixed examples and constant-only generator wrappers surrender most of that state space and produce `insufficient-domain-variation`. Operator approval of a fixture exception does not turn fixed examples into property evidence.

A fixture candidate is acceptable only when the complete payload shape is material to the behavior and the payload is passed as inert input by path, bytes, copy, or directory tree. Fixture modules, constant bags, copied protocol values, token lists, expected-output files, and finite stand-ins for open domains produce `fixture-not-whole-payload`.

Scoped fixture approval records all of these facts for the named assertion and payload role:

- why the complete payload is material;
- why generation or property evidence is infeasible or wasteful;
- which state-space coverage is surrendered;
- which harness owns setup, cleanup, seed policy, replay, and diagnostics;
- the recommended generated or property-based alternative.

A valid candidate lacking that decision produces `fixture-approval-missing`.

Record every observable design defect before leaving the design pass. One defect never suppresses another row or assertion. The core defect vocabulary is:

- `missing-governing-reference`
- `invalid-reference`
- `missing-independent-oracle`
- `insufficient-domain-variation`
- `fixture-not-whole-payload`
- `fixture-approval-missing`
- `missing-replay-harness`

</evidence_design_model>

<reference_validation>

Local evidence-design references use Markdown links whose targets are relative to the product root. A valid local target has no leading `/`, `./`, or `../`, contains no traversal segment or backslash, resolves to an existing exact artifact, and matches the declared role. A prose name, inline-code path, absolute path, `file://` URI, or directory does not establish traceability.

| Role                                            | Primary reference                                                           | Secondary reference                                                                                                         | Validation                                                                                                |
| ----------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Governed test infrastructure or source contract | Exact assertion-bearing spec file or full decision-record path under `spx/` | Existing implementation artifact                                                                                            | The governance target exists and is a spec or decision file; implementation-only traceability fails       |
| Assertion subject                               | Exact assertion text plus its assertion-bearing spec file under `spx/`      | Stable heading fragment when durable                                                                                        | The target exists and contains the assertion                                                              |
| Deterministic test evidence                     | Exact co-located typed file from the assertion's `[test]` link              | Imported infrastructure implementations                                                                                     | Target exists under the governing node's `tests/` and filename encodes assertion type and execution level |
| Eval evidence                                   | Exact `eval.toml` from the assertion's `[eval]` link                        | Producer and sibling eval artifacts                                                                                         | Definition exists; an eval-directory link fails                                                           |
| External authority                              | Stable canonical URL, schema identifier, or standard identifier             | Product-root-relative Markdown link to the local spec or full decision adopting it                                          | External authority never replaces local governance                                                        |
| Runtime replay identity                         | Verbatim source-emitted seed, replay token, or run token                    | Product-root-relative Markdown links to the harness or run-journal implementation and exact governing spec or full decision | Identity is copied exactly and never invented as a file link                                              |

When governed implementation exists, both governance and implementation links are mandatory. When it is planned and absent, link the governing spec, record the implementation as absent, and stop dependent test authoring until its TDD flow creates the artifact. Never manufacture a broken implementation link.

Validate syntax, path shape, target existence, target artifact kind, and required pairings. Use `missing-governing-reference` when an implementation or prose name is the only traceability for a governed artifact; use `invalid-reference` for every other reference-contract failure.

</reference_validation>

<coupling_taxonomy>

Coupling categories with definitions and code examples.

**Direct coupling** — Test imports the module under test and calls its functions directly.

```typescript
import { parseConfig } from "../src/config-parser";

it("parses nested sections", () => {
  const result = parseConfig(input);
  expect(result.section.key).toBe("value");
});
```

**Indirect coupling** — Test imports a test harness that wraps the module. Coupling exists but is mediated.

```typescript
import { ConfigTestHarness } from "./harness";

it("parses nested sections", () => {
  const harness = new ConfigTestHarness();
  const result = harness.parseAndValidate(input);
  expect(result.section.key).toBe("value");
});
```

When indirect coupling is found, verify the harness itself has direct coupling to the module. If the harness is also a tautology, the coupling chain is broken.

**Transitive coupling** — Test imports something that depends on the module under test, but does not import the module directly.

```typescript
import { Application } from "../src/app";

it("loads configuration", () => {
  const app = new Application();
  expect(app.config.section.key).toBe("value");
});
```

May be legitimate when the test exercises cross-module evidence at L2 or L3. Verify the test level matches the assertion level.

**False coupling** — Test imports the module but never exercises the code path relevant to the assertion.

```typescript
import { parseConfig, validateConfig } from "../src/config-parser";

it("validates config structure", () => {
  // Assertion is about PARSING but test only validates
  const result = validateConfig(hardcodedConfig);
  expect(result.valid).toBe(true);
  // parseConfig is imported but never called
});
```

The import exists syntactically but the assertion-relevant function is never called.

**Partial coupling** — Test exercises some code paths but not the ones the assertion specifies.

```typescript
import { parseConfig } from "../src/config-parser";

it("parses flat config", () => {
  // Assertion is about NESTED SECTIONS but test covers flat only
  const result = parseConfig("key=value");
  expect(result.key).toBe("value");
});
```

**No coupling** — Test imports only its test framework. A tautology.

```typescript
import { describe, expect, it } from "vitest";

const GRAY = { L: 0.98, C: 0.003, H: 85 };

it("has correct chroma", () => {
  expect(GRAY.C).toBe(0.003); // Tests a constant it declared itself
});
```

This test passes if every file in the codebase is deleted.

**Severed coupling** — Test imports the module under test and then replaces the imported behavior with a mock, fake, stub, monkeypatch, intercepted response, or equivalent mechanism.

```typescript
import { queryDatabase } from "../src/database";

vi.mock("../src/database", () => ({
  queryDatabase: vi.fn().mockResolvedValue([{ id: "test" }]),
}));

it("loads records", async () => {
  await expect(loadRecords()).resolves.toHaveLength(1);
});
```

The import exists, but the real behavior never runs. REJECT — coupling severed.

**Prose-coupling** — Test reads an authored prose or documentation body — a skill body, a spec body, a prompt, any text the product authors and maintains — and asserts substrings of its content. The test couples to the document's text, never to executable behavior: it passes whatever the document literally contains, and no code runs.

```python
SKILL = repo_root / "authored_skill.md"


def test_skill_declares_the_policy() -> None:
    assert (
        "MERGE_READINESS" in SKILL.read_text()
    )  # the prose was authored, not behavior
```

This holds full-chain: a harness that exposes the authored path as a constant, or a reader function that performs the `read_text` inside test infrastructure, does not convert a prose assertion into behavioral coupling — follow the read to its source and classify by what is ultimately exercised. The only mutation that falsifies such a test is an edit to the authored prose, never a change to code, so it carries no behavioral evidence. REJECT — the claim belongs in `[eval]` or `[audit]`, and the spec assertion is retagged. Reading an authored *source-code* file for a structural lint that exercises a rule against it is not prose-coupling; the discriminator is whether the subject is authored prose/documentation or executable behavior.

</coupling_taxonomy>

<coupling_verification>

**Procedure:**

1. Read import statements at the top of the test file
2. Classify each: framework, library, or codebase
3. Zero codebase imports → REJECT (no coupling)
4. For each codebase import:
   - Is the imported module the one the assertion is about? → Direct
   - Is it a test harness? → Indirect (follow the chain — verify harness has real coupling)
   - Is it a consumer of the module? → Transitive (verify test level)
5. Check whether the imported behavior is replaced by a mock, fake, stub, monkeypatch, or equivalent mechanism:
   - Imported then replaced → Severed coupling
6. Check whether the assertion-relevant function/method is actually called:
   - Imported but never called → False coupling
   - Called but on wrong inputs or code paths → Partial coupling

</coupling_verification>

<test_file_declaration_model>

Executed test files are assertion files, not data/configuration homes. Read declarations before coupling so ownership failures cannot be hidden behind imports or naming style.

Reject every variable or constant declaration in executed test files. A variable or constant owns state in the assertion file even when the name looks harmless, and the remediation is to move that state to the correct owner. Reject framework fixture parameters and property-generated parameters for the same reason: they bind setup or generated data in the assertion file rather than behind a harness-owned entrypoint.

- runner settings, seed policy, retries, or framework configuration
- test data, boundary bags, expected outputs, or reusable cases
- fixture paths or fixture contents
- generator choices, arbitrary domains, or singleton wrappers
- harness setup policy, reusable resources, cleanup policy, or diagnostics
- source-owned singleton shapes, protocol tokens, status values, command names, rule identifiers, or message identifiers

Reject local function declarations when they own setup, reusable cases, fixture handling, generator selection, harness behavior, diagnostics, or source-owned vocabulary.

Casing and declaration shape are irrelevant. `MAPPING_RUNS`, `mappingRuns`, `runs`, and `function mappingRuns()` carry the same ownership defect when the declaration owns runner configuration.

Property-based evidence must be reproducible. A property harness or wrapper owns seed selection, run counts, and failure reporting. The failure output must include the seed and replay path. A test file that declares its own seed/run-count or calls a property framework without reproducible seed reporting fails the declaration screen.

Valid remediation targets:

- Source contract for source-owned vocabulary or singleton shapes
- Spec-governed generator for variable input domains
- Spec-governed harness for configuration, resource lifecycle, seed policy, and replay diagnostics
- Inert fixture for real whole-payload samples read, copied, or passed by path
- Eval case data when curated LLM/eval cases make generated JSONL wasteful and not tractable

</test_file_declaration_model>

<falsifiability_model>

**Mutation analysis**

For each codebase import with behavior coupling, name a concrete mutation:

```text
Module: src/config-parser.ts
Mutation: parseConfig returns empty object instead of parsed sections
Impact: "parses nested sections" fails — expect(result.section.key) throws
```

The mutation must be:

- **Concrete** — a specific change, not "if something breaks"
- **Relevant** — changes the behavior the assertion claims to verify
- **Detectable** — the test's assertions would actually catch it

If no such mutation can be named: the test is unfalsifiable.

**Mocking severs coupling**

A test that imports a module then replaces it with a mock:

```typescript
import { database } from "../src/database";
vi.mock("../src/database", () => ({ query: vi.fn().mockResolvedValue([]) }));
```

The real `database.query` never runs. Any change to the real module — schema changes, query bugs, connection failures — is invisible. Import + mock = coupling severed.

**Exception cross-reference with `/test` methodology**

Test doubles used under the 7 legitimate exception cases are not "coupling severed." The auditor must identify which exception applies:

| Exception                | Double type           | Why coupling is maintained                         |
| ------------------------ | --------------------- | -------------------------------------------------- |
| 1. Failure modes         | Stub returning errors | Tests error handling of real integration           |
| 2. Interaction protocols | Spy recording calls   | Tests call sequence against real interface         |
| 3. Time/concurrency      | Fake clock            | Tests timing logic with real code                  |
| 4. Safety                | Stub that records     | Tests intent without destructive side effects      |
| 5. Combinatorial cost    | Configurable fake     | Tests breadth with fake that mirrors real behavior |
| 6. Observability         | Spy recording details | Tests request details the real system hides        |
| 7. Contract testing      | Contract stub         | Tests serialization/parsing against real schema    |

For each test double found:

1. Identify which exception applies (must be one of the 7)
2. Verify the double type matches the exception (see table)
3. Verify the test actually tests what the exception enables
4. If no exception applies → coupling is severed → REJECT

</falsifiability_model>

<alignment_verification>

**Procedure:**

Read the spec assertion and the test's expect/assert statements side by side.

1. Does the test exercise the exact behavior the assertion describes?
   - Assertion says "Given X, when Y, then Z"
   - Test must: set up X, perform Y, assert Z

2. Could the assertion be unfulfilled while the test passes?
   - If yes → misaligned

3. Is the test strategy appropriate for the assertion type?
   - Property assertion → must use property-based framework
   - Mapping assertion → must be parameterized over the input set
   - Conformance assertion → must use tool/schema validation

**Common misalignment patterns:**

| Assertion says                   | Test does                   | Finding                              |
| -------------------------------- | --------------------------- | ------------------------------------ |
| "Handles nested sections"        | Tests flat config only      | Partial behavior — misaligned        |
| "All themes meet threshold"      | Tests one theme             | Incomplete coverage — misaligned     |
| "Serialization is deterministic" | Tests one input             | Needs property test — wrong strategy |
| "API returns 404 for missing"    | Tests 200 for existing      | Wrong scenario — misaligned          |
| "Parser rejects invalid input"   | Asserts no exception thrown | Inverted assertion — misaligned      |

</alignment_verification>

<coverage_protocol>

**Step-by-step:**

1. **Identify assertion-relevant source files.** From the spec assertion and test imports, determine which source files the test should exercise.

2. **Read the production path.** Identify the functions, branches, methods, or command paths whose behavior the assertion claims.

3. **Read the test path.** Follow the test's imports and calls into the production path.

4. **Judge reachability.** Decide whether the test drives execution into the assertion-relevant path. Name the specific path reached or missed.

5. **Report the trace, not a measured percentage:**

   ```text
   Assertion-relevant path: src/config-parser.ts::parse_config nested-section branch
   Test path: tests/test_config.py::test_nested_sections -> parse_config(input)
   Coverage judgment: reaches assertion-relevant path
   ```

**Edge cases:**

- **No coverage tooling**: irrelevant to this audit. Do not record a finding for missing tooling.
- **Trivially total path**: when the assertion-relevant behavior is one total path and the test reaches it, annotate as `saturated`; the other three properties carry assertion strength.
- **Shared execution path**: multiple tests may reach the same path. Judge whether this test reaches the path; do not compare deltas.

</coverage_protocol>
