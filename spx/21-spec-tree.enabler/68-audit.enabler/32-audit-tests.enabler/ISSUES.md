# Issues

## SPX evidence graph integration

The test-evidence audit receives an explicit evidence package from its caller and follows direct imports from the linked tests into harnesses, generators, fixtures, discovery files, and production code. It does not discover or claim an authoritative repository-wide evidence graph.

Revisit when SPX exposes its product document through decision records, specs, tests, and code as a structured graph projection. At that point, make the SPX projection the audit's evidence inventory input and remove caller-owned path discovery that the projection supersedes.

Do not implement a competing repository graph or Markdown walker in this repository.

## No passing full-suite run evidence for the current 10-case set

Both `[eval]` suites under `evals/` (`full-chain-ownership`, `full-chain-ownership-codex`) grew to ten cases — five added by the semantic-evidence-seam changeset (`rejects-fixture-owned-protocol`, `rejects-discovery-owned-protocol`, `rejects-production-derived-oracle`, `approves-independent-conformance-oracle`, `rejects-harness-owned-predicate`). No committed `history.jsonl` row runs all ten current cases to a pass: `full-chain-ownership`'s newest full run predates the additions (seven cases), and every later row is a single-case rerun; `full-chain-ownership-codex`'s one ten-case run scored `pass_rate` 0.7 against the 0.85 threshold and failed, with only single-case reruns after it.

**Status against the standard.** `/audit-eval-evidence` `audit_run_evidence` requires a committed successful run for the current eval definition, threshold, and case set; both suites are `REJECT` "missing run evidence". The eval-evidence auditor and the local changeset review independently reported this class.

**Why it is recorded rather than resolved here.** Producing the evidence requires paid full-suite runs, and the Codex suite scores below threshold on the current cases, so a run would not clear the gate. The suites are slated for a complete rebuild, so passing-run production against the current definitions is superseded work. Run verification is deferred by operator direction pending that rebuild.

**Resolution shape.** Fold these suites into the planned eval rebuild — reconcile the ten cases and the grader against the current producers, run each suite to a pass at or above threshold at the default budget, and commit the resulting `history.jsonl` rows. Until then the two suites carry no current passing-run evidence.

## No case exercises declared-contract ownership

Step 3a of `/audit-tests` judges a source symbol the test cites by declared-contract ownership, so an absent in-repository caller opens the ownership question rather than settling it and the audit inspects the declared surfaces the checkout carries — packaging entry points and export declarations, protocol implementations, registry and reflective lookups, generated use, and declared schemas — before reporting a symbol as laundered. No case in the shared `cases.jsonl` supplies such a symbol, so reverting that rule to a blanket "absent caller proves laundering" changes no case outcome and neither suite carries falsifiable evidence that the behavior is present.

**Status against the standard.** `/audit-eval-evidence` `gate-4-falsifiability` is `REJECT` for both suites: a producer behavior an assertion claims must be reachable by a case that fails when the behavior is removed.

**Why it is recorded rather than resolved here.** Authoring the case is small; establishing it is not. A case reaches evidence only through a run against the real producer, and both suites already carry no passing full-suite run for their current ten cases under the entry above. An eleventh case committed with an unvalidated expected verdict adds an untested claim about grader behavior to a suite awaiting rebuild. Recorded by operator direction, with the same rebuild as its home.

**Resolution shape.** Add the case to the rebuilt suite: a symbol with no in-repository importer whose ownership rests on a published surface — a protocol only third parties implement, a packaging entry point, or a registry lookup — with an approving expected verdict, so removing the declared-contract rule turns that case red. Run it with the rest of the suite at the default budget and commit the resulting rows.

## Eval run history is stale for both full-chain-ownership suites

`evals/full-chain-ownership`: the newest full-suite passing row (2026-07-17,
git SHA `873fdf84c65d2c5d6dd98e4d9ff63e93c3289da3`) ran 7 cases against a current
set of 10; the later rows on `056264a21829b8124eb21a4f96a0b3dc44c68172` are
single-case reruns. Neither SHA is an ancestor of the current head, and the
producer `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `cases.jsonl`,
`eval.toml`, `prompt.md`, and `test-evidence-standards/SKILL.md` all changed after
every recorded run.

`evals/full-chain-ownership-codex`: the only run over the current 10-case set
(2026-07-18, git SHA `c18af21b3b023a88d37912da8e5d1273c059cda7`) scored 0.7
against the 0.85 threshold and recorded `passed: false`; every later row is a
single-case rerun, two of them failing. The producer
`dist/codex/spec-tree/skills/audit-tests/SKILL.md`, the shared `cases.jsonl`,
`eval.toml`, and `prompt.md` changed after the newest row.

**Settlement condition**: one passing full-suite run of each eval on a head that
carries the current producers, with its rows committed to each `history.jsonl`;
the Codex suite's last full result is a behavioral failure, so its rerun may
surface producer defects to repair first.

**Evidence**: `spec-tree:eval-evidence-auditor` findings `f-004` and `f-005` on
head `a65659114b99767b90b4d920550fff5dc0824794` during Change #76, whose prototype boundary runs no eval.
