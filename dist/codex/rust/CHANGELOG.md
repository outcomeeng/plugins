# Changelog — rust plugin

Rust engineering: coding, testing, architecture, the matching concern audits, and the `rust-simplifier` agent.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

## 0.8.1

### Fixed

- **Every worked example keeps its assertion in the test.** The test standards stated the predicate seam and contradicted it in all fourteen examples, each a single call to an `assert_*` harness function. Copying an example no longer produces a test the standard rejects.
- **No example gives a test-only case a production address.** Cases that had been placed in a module under test so the test could cite a production path are now the interaction the spec declares, transcribed into the test body. The origin table gains that assertion-assigned origin, so following it no longer pushes a scenario case into production.
- **The binding rule and the harness failure mode stop contradicting the assertion-assigned origin.** The origin table admits a spec-declared case inline, while the binding rule still sent every binding that chose case data out to infrastructure or a source contract, and the coding skill's failure mode still gave the source module the case values and expected results. A consumer could satisfy one instruction or the other. The binding rule now excepts the case the assertion type assigns, and the source module owns the vocabulary the expectation is written in.
- **CLI examples assert through the declared assertion API.** `.assert().success()` was a verdict the library owned; the examples now take the `Output` and assert on it. Command names come from the owning production module rather than string literals.
- **Generated values reach a test only through the property harness.** Scenario examples at every level sampled a generator once with no seed, so a failure was unreproducible and the next run drew a different value; each now takes the case its assertion assigns.
- **`trybuild` cases carry no verdict in their fixture names.** Case paths are neutral and the test selects `pass` or `compile_fail` per case, so inverting a compile-time claim edits only the test.
- Both property examples import `prop_assert_eq!`; neither compiled as written.

## 0.8.0

### Removed

- `Skill` from the lifecycle skill's `allowed-tools`
- `MARKETPLACE-CHANGELOG.md`; it ships with the spec-tree plugin

## 0.7.0

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
