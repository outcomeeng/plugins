# Issues: Consumption Control

## Test evidence carries no assertion-design records

The twelve linked files under this node's `tests/` directory carry no retrievable assertion-design records from their authoring Activities. Each record requires the assertion and quantifier, production subject and observable seam, case-provenance owner, oracle owner, rejected production mutation, and linked failure observation.

**Evidence:** the Change's Activity 3 handoff supplies the implementation and test files without the original records. The Plugins Maintainer's disposition records their absence and preserves the node's `malleability: spec` boundary. No Verifier judging test evidence runs on this changeset; the decision-record audits judge their decision records.

**Impact:** later evidence audits lack the original design provenance for these twelve files. A record reconstructed after its test exists cannot establish the pre-authoring prerequisite.

**Settlement condition:** the Change that hardens this node below `spec` authors the assertion-design records before its evidence audits.

## DEBT [consistency]: reinstall with another launch-agents directory abandons the prior plist `src/plugins/coding-agents/skills/control-token-spend/scripts/usage_schedule.py`, `install_plan`, `consistency`

CI review on PR 659 at head `862a3f2efaced60b77b4f30693cf20eb4889e0e8` (comment of 2026-10-12T14:15:18Z) found that `install_plan()` in `src/plugins/coding-agents/skills/control-token-spend/scripts/usage_schedule.py` derives each job plist path from the invocation's `--launch-agents-dir`, which the saved configuration does not persist. The ownership checks in `install()` inspect only the new plan's paths and never the paths the prior installation manifest records.

**Impact:** a reinstall that names a different launch-agents directory leaves the previous plist file at its old location, unreported, against the skill's contract to preserve and report changed or unowned installed jobs. The launchd registration itself is replaced, because launchctl keys on the label.

**Settlement condition:** install diffs the prior manifest's recorded plist paths against the new plan and reports or reconciles every path the plan no longer names.

## DEBT [evidence]: no linked test installs twice into one root

The same CI review found that `installation_observation` and `native_installation_observation` in `outcomeeng_testing/harnesses/consumption_control.py` each call `install(..., True)` once per fresh workspace. The unowned launch agent, externally changed launch agent, externally changed asset, prior-load bootout and bootstrap, and asset-retention branches of `usage_schedule.py` run only on a second installation into a root that already carries a manifest, so no linked test reaches them.

**Impact:** the installation assertion's failure-exposure and retention branches stand on inspection, not evidence.

**Settlement condition:** a linked test installs twice into one root and observes each of those branches.

## DEBT [evidence]: report evidence never reaches a zero denominator `outcomeeng_testing/generators/consumption_control.py`, `growing_contexts`, `evidence`

The same CI review found that the context-growth, cost-growth, measured-cost-share, and cache-read-share ratios are `None` when their denominator is zero, and `usage_reports.py` renders that case as `unknown` in HTML and as an empty CSV field. `growing_contexts()` in `outcomeeng_testing/generators/consumption_control.py` draws every context from positive integers, and the report and context fixtures carry positive usage counters, so no linked test reaches the `unknown` rendering.

**Impact:** the report assertion's unknown-attribution rendering stands on inspection, not evidence.

**Settlement condition:** the report or context generators include a zero-context or zero-measured-cost case, and a linked test asserts the `unknown` rendering.
