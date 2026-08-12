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

Step 3a of `/audit-tests` judges a source symbol the test cites by declared-contract ownership, so an absent in-repository caller opens the ownership question rather than settling it and the audit inspects dynamic registration, the published package surface, generated and reflective use, and consumers outside the checkout before reporting a symbol as laundered. No case in the shared `cases.jsonl` supplies such a symbol, so reverting that rule to a blanket "absent caller proves laundering" changes no case outcome and neither suite carries falsifiable evidence that the behavior is present.

**Status against the standard.** `/audit-eval-evidence` `gate-4-falsifiability` is `REJECT` for both suites: a producer behavior an assertion claims must be reachable by a case that fails when the behavior is removed.

**Why it is recorded rather than resolved here.** Authoring the case is small; establishing it is not. A case reaches evidence only through a run against the real producer, and both suites already carry no passing full-suite run for their current ten cases under the entry above. An eleventh case committed with an unvalidated expected verdict adds an untested claim about grader behavior to a suite awaiting rebuild. Recorded by operator direction, with the same rebuild as its home.

**Resolution shape.** Add the case to the rebuilt suite: a symbol with no in-repository importer whose ownership rests on a published surface — a protocol only third parties implement, a packaging entry point, or a registry lookup — with an approving expected verdict, so removing the declared-contract rule turns that case red. Run it with the rest of the suite at the default budget and commit the resulting rows.
