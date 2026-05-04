# Issues

Tracked imperfections in the 18-plugin-build subtree. Remove items as they
are resolved.

## 1. Broken [test] links across 4 spec nodes

Eighteen assertion-test bindings point to five test files that do not
exist. The deleted files were the `*.compliance.l1.py` scaffolds reverted
in `db45d83`, `92a3bb4`, `9285737`, `d4bb176` after the
`/python:auditing-python-tests` audit found categorical defects (false
coupling, source-owned-values violations, narrow string checks).

The include-directive vertical slice committed in `5eb8c8c` resolved 3
of those bindings in `21-source-and-templating.enabler`. The remaining
bindings:

| Spec node                          |   Assertions still broken   | Pointing at (deleted file)                      |
| ---------------------------------- | :-------------------------: | ----------------------------------------------- |
| `21-source-and-templating.enabler` |   4 (asserts 1, 2, 3, 5)    | `test_source_and_templating.compliance.l1.py`   |
| `43-target-emission.enabler`       |           7 (all)           | `test_target_emission.compliance.l1.py`         |
| `65-build-orchestration.enabler`   |           4 (all)           | `test_build_orchestration.compliance.l1.py`     |
| `plugin-build` (parent enabler)    | 1 compliance + 2 properties | `test_plugin_build.{compliance,property}.l1.py` |

Resolution: roll out the include-directive vertical slice pattern
(stage-isolated tests, source-owned constants from
`outcomeeng.scripts.build_plugins`, named scenarios from
`outcomeeng_testing.harnesses.scenarios`, IMPLEMENTED-flag skip-gate)
to each remaining assertion. See `PLAN.md` for ordering.

## 2. 65-build-orchestration assertions need recategorization

The four assertions in `65-build-orchestration.enabler/build-orchestration.md`
describe repo configuration shape (justfile recipe presence, lefthook
hook presence, marketplace JSON paths) rather than build behavior.
The `/python:auditing-python-tests` audit classified the corresponding
test scaffolds as having severed coupling: the tests grep static
config files and never exercise `outcomeeng.scripts.build_plugins`.

Resolution: split the four assertions:

- Structural-shape assertions (recipe existence, hook config existence,
  marketplace JSON path prefixes) become `[review]` tags backed by
  manual or CI-time checklists.
- Behavioral assertions (`just build-skills` actually invokes the
  build; `lefthook` actually fails commits when `dist/` would change)
  become `[test]` at l2, exercised by tests that invoke the just
  binary as a subprocess and inspect what the orchestration did.

The recategorization is a deliberate spec rewrite, not a weakening.
The methodology rule "tests verify behavior, not implementation
shape" applies; static config inspection is a `[review]` concern.
