# Testing Naming

Test filenames encode what kind of evidence the file contains, how painful it is to run, and whether it needs a non-default runner.

## Canonical Pattern

### TypeScript and JavaScript

```text
<subject>.<evidence>.<level>[.<runner>].test.ts
```

### Python

```text
test_<subject>.<evidence>.<level>[.<runner>].py
```

The terminal `test` marker stays constant. The runner token appears only when the runner is not the default.

Other ecosystems should preserve the same subject, evidence, level, and runner axes in whatever native test-file convention they use.

---

## Evidence Tokens

| Token         | Meaning                                   |
| ------------- | ----------------------------------------- |
| `scenario`    | Concrete behavior for a concrete case     |
| `mapping`     | Input-output mapping over a defined set   |
| `conformance` | Output matches a contract or standard     |
| `property`    | Invariant holds over a broad input domain |
| `compliance`  | Rule always or never holds                |

---

## Level Tokens

| Token | Meaning                                  |
| ----- | ---------------------------------------- |
| `l1`  | Cheap, local, almost certainly available |
| `l2`  | Heavier local dependencies               |
| `l3`  | Remote or credentialed dependencies      |

---

## Runner Tokens

- Omit the runner token for the default runner
- Add an explicit runner token for a non-default runner
- Use `playwright` when Playwright is the non-default runner

Example:

- `dispatch.mapping.l1.test.ts`
- `browser-auth.scenario.l2.playwright.test.ts`
- `payments.conformance.l3.test.ts`
- `test_seeded_generators.property.l1.py`

---

## Orthogonality Rule

Runner, level, and evidence mode are separate.

- A runner does not imply a level
- A level does not imply a runner
- An evidence token does not imply either one

Valid examples:

- `scenario + l1 + default runner`
- `scenario + l2 + playwright`
- `conformance + l3 + default runner`

---

## Co-Location

Tests stay with the node they prove.

| Location         | Rule                                               |
| ---------------- | -------------------------------------------------- |
| `spx/.../tests/` | Keep all evidence files with the spec they support |

Do not graduate tests to other directories because they become slower or broader.

---

## Naming Examples

### TypeScript

- `with-test-env.mapping.l1.test.ts`
- `scenarios.scenario.l1.test.ts`
- `local-browser.scenario.l2.playwright.test.ts`
- `stripe-webhook.conformance.l3.test.ts`

### Python

- `test_config_loader.mapping.l1.py`
- `test_scenario_registry.scenario.l1.py`
- `test_browser_auth.scenario.l2.playwright.py`
- `test_checkout_flow.scenario.l3.py`

### Cross-language axis examples

- Python temp-dir export: `scenario + l1 + default runner`
- Rust parser round-trip: `property + l1 + default runner`
- Rust CLI over fixture workspace: `scenario + l2 + default runner`

---

## What to Avoid

Avoid filenames that collapse level, runner, and evidence into one legacy class label. The filename should tell an agent:

1. what proof shape the file contains
2. how expensive it is to run
3. which runner executes it when that runner is not the default
