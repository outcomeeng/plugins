# Issues: Herdr Environment

## DEBT: captured oracle artifacts lack source provenance

The captured usage and public-response artifacts under `outcomeeng_testing/fixtures/herdr_environment/` carry no tool name or source version. The adapter ADR declares `herdr` 0.9.1 as their source-tool version pin, together with the pin-change and live-drift recapture conditions, while the fixture family has no artifact-owned representation of that pin yet.

**Impact**: a reader cannot determine from a captured artifact or its fixture family which source-tool release produced it, so stale-oracle detection depends on the ADR rather than inspectable fixture provenance. The ADR declaration leads the fixtures until the evidence layer catches up.

**Settlement condition**: a separate Change adds the exact tool and version provenance to every captured usage and response artifact, or adds a fixture-owned manifest that each artifact declares, then establishes the applicable deterministic test evidence and test-evidence audit on the committed subject.

**Evidence**: changes-review run `2026-09-19_05-37-13-476-8f079ea7b727` reported the full fixture class at head `5ad33be7f066e9eae2272e085a6e31ec85fede2d`.
