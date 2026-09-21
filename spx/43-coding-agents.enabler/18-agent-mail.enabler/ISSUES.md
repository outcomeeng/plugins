# Issues: Agent Mail

## DEBT: captured oracle artifacts lack source provenance

The captured usage and public-response artifacts under `outcomeeng_testing/fixtures/agent_mail/` carry no tool name or source version. The adapter ADR declares `am` 0.3.24 for store grammar and responses and `@outcomeeng/spx` 0.7.1 for the diagnosis response, together with the pin-change and live-drift recapture conditions, while the fixture family has no artifact-owned representation of those pins yet.

**Impact**: a reader cannot determine from a captured artifact or its fixture family which source-tool release produced it, so stale-oracle detection depends on the ADR rather than inspectable fixture provenance. The ADR declaration leads the fixtures until the evidence layer catches up.

**Settlement condition**: a separate Change adds the exact tool and version provenance to every captured usage and response artifact, or adds a fixture-owned manifest that each artifact declares, then establishes the applicable deterministic test evidence and test-evidence audit on the committed subject.

**Evidence**: changes-review run `2026-09-19_05-37-13-476-8f079ea7b727` reported the full fixture class at head `5ad33be7f066e9eae2272e085a6e31ec85fede2d`.

## The delegation property assertion is evidenced only after its semicolon

The Properties assertion beginning "An order to an agent session in an environment whose surface produces no pane-borne handback block" carries two clauses. Its linked evidence, `tests/test_agent_mail.property.l1.py`'s `test_terminal_handbacks_reduce_to_exactly_one_result`, drives `terminal_record_kinds` only and calls `terminal_handback` and `reduce_terminal`, so it establishes the clause after the semicolon and nothing before it. No case exercises an `order` kind, a `delegation-request` kind, the three-record correlation chain, the environment-surface precondition, or delivery through this capability: `command_for` and `execute` are never reached from that file.

**Impact**: the adapter could reject every `order` and `delegation-request` record and the node's evidence would still pass, so the assertion's first clause is declared without a result.

**Settlement condition**: a case drives an `order` record and its `delegation-request` through the capability's own send path under one correlation, reaching the terminal handback the existing case already reduces, and the assertion's first clause gains a linked result.

**Evidence**: `spec-tree:test-evidence-auditor` finding `f-001` on head `d6d1b5458af190ac9d1f05775c869c08ab206c95`, rule `alignment`. The assertion and its test both predate the changeset that surfaced it, which changed neither.
