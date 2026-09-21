# Issues: Agent Mail

## DEBT: captured oracle artifacts lack source provenance

The captured usage and public-response artifacts under `outcomeeng_testing/fixtures/agent_mail/` carry no tool name or source version. The adapter ADR declares `am` 0.3.24 for store grammar and responses and `@outcomeeng/spx` 0.7.1 for the diagnosis response, together with the pin-change and live-drift recapture conditions, while the fixture family has no artifact-owned representation of those pins yet.

**Impact**: a reader cannot determine from a captured artifact or its fixture family which source-tool release produced it, so stale-oracle detection depends on the ADR rather than inspectable fixture provenance. The ADR declaration leads the fixtures until the evidence layer catches up.

**Settlement condition**: a separate Change adds the exact tool and version provenance to every captured usage and response artifact, or adds a fixture-owned manifest that each artifact declares, then establishes the applicable deterministic test evidence and test-evidence audit on the committed subject.

**Evidence**: changes-review run `2026-09-19_05-37-13-476-8f079ea7b727` reported the full fixture class at head `5ad33be7f066e9eae2272e085a6e31ec85fede2d`.

## DEBT: orphaned robot-inbox fixture family awaits operator removal

The obsolete robot-inbox fixture family has no repository reference:

- `outcomeeng_testing/fixtures/agent_mail/usage/robot-inbox.txt`
- `outcomeeng_testing/fixtures/agent_mail/responses/robot-inbox.json`
- `outcomeeng_testing/fixtures/agent_mail/responses/robot-inbox.include-bodies.json`
- `outcomeeng_testing/fixtures/agent_mail/responses/robot-inbox.include-bodies.acked.json`

**Impact**: the agent-mail fixture inventory contains a retired command-response family that no linked evidence consumes, so readers cannot distinguish retained evidence from stale capture state by reachability.

**Settlement condition**: removed by the operator.

**Evidence**: a repository-wide `robot-inbox` reference scan returned no consumers while the four files remained present. The operator withheld removal and directed that every file remain unchanged.
