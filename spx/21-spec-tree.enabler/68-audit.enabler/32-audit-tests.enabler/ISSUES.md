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

## The independent-conformance eval case omits its alias declaration

The `approves-independent-conformance-oracle` case imports
`@testing/generators/routeUrls`, while its artifact package supplies
`testing/generators/routeUrls.ts` and a `package.json` with no `imports`,
`exports`, or path mapping. It supplies no Vitest or TypeScript configuration
that maps `@testing` to `testing/`. The evidence-chain rules require import
resolution to follow a supplied discovery artifact or a repository path, so a
Verifier can correctly reject the case as `incomplete-evidence-chain` instead
of reaching the intended oracle-independence judgment.

**Evidence.** Codex full-suite run `2026-09-19T03-15-41Z` rejected this case
because the alias mapping was absent. A local edit to replace the alias with a
relative import made runs `2026-09-19T03-48-02Z` and
`2026-09-19T03-57-34Z` pass, but those rows and the case edit were discarded
because Change #94 treats the suite as evidence and cannot alter its oracle.

**Settlement condition.** A separate Change decides the intended executable
fixture shape, supplies the matching module-resolution artifact or uses a real
relative import, and establishes the revised case through both full suites.

## `test-evidence-auditor` carries no retained release-acceptance or invocation evidence

[`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) declares release acceptance per harness and per profile: native loading and one minimal isolated execution for each profile. The tree retains no acceptance artifact for the Claude or the Codex Standard row that `src/plugins/spec-tree/agents/test-evidence-auditor.md` selects, and no exact-definition minimal isolated invocation of the definition. The gap is the one the `adr-auditor` entry in `spx/21-spec-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/ISSUES.md` records, and it holds for every marketplace definition: the decision binds acceptance to profiles, and no definition's tool grant or sandbox changes the Standard profile it selects.

**Impact**: nothing in the tree shows the emitted `test-evidence-auditor` definitions loading natively and returning a run token and projection on either harness.

**Settlement condition**: the release retains passing Standard-profile acceptance rows for both harnesses at a location `/audit-subagent` reads, or the subagent standards accept the harness's profile acceptance as a definition's invocation evidence, which <https://github.com/outcomeeng/changes/issues/118> carries; then one `subagent-auditor` run on the definition raises neither a `release_acceptance_evidence` nor an `invocation_evidence_missing` finding.

**Evidence**: two `instructions:subagent-auditor` runs on `src/plugins/spec-tree/agents/test-evidence-auditor.md` at head `400f55c8cbd57291b4a9c70c99a45c4ac0e57ab9`: run `2026-10-16_18-06-32-474-ca1f2d0d044c` raised the blocking rule `release_acceptance_evidence`, and run `2026-10-16_18-10-25-266-c777519799aa` raised the blocking rule `invocation_evidence_missing`. Both ask for retained native loading and one minimal isolated execution of the emitted definition, per profile and harness, as property 3 of [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) states.

## An evidence-scope `/audit-tests` start input retypes the changed paths

For an evidence-scope target, `/audit-tests` writes its start-input file from the `spec-tree:scope-changeset` marker, which retypes `changed_paths`, because that resolver has no output-file option. The retyped list is a transcription of the resolver's output, and the start input carries it in place of the resolver's own file.

**Impact**: the changed-path list the audit run seals is the Verifier's transcription of the resolver's marker, not the resolver's output, so a transcription slip changes the scope the run judges without any resolver evidence of it.

**Settlement condition**: the resolver writes the start input to a caller-named path, or SPX resolves the scope at start.

**Evidence**: the Handoff of outcomeeng/changes#513, hazard (c). This is a known gap with no repair in that Change.
