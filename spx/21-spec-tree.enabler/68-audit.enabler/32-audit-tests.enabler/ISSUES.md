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

## The test-evidence audit carries no guard against synchronizing the audited subject

The test-evidence audit skill loads `/contextualize` for its target node, and `/contextualize` runs `/sync-base`, which rebases the audited branch. `spec-tree:audit-implementation` states that an audit never synchronizes, rebases or otherwise mutates the audited subject; this node's audit path carries no such guard.

**Evidence.** Rollout `agent-a4cedd803fc1a5758.jsonl` of a test-evidence audit dispatched against head `f07db1bbaf225ec031d7a777f02c166daa588871` on 2026-09-16 resolved two conflicts and finished at `15d4309e69c26804cd1b04676248a529fd0235b9`, so the concurrent implementation audit found its sealed head superseded.

**Settlement condition.** The audit selects the Verifier-mode context load that the entry in `spx/21-spec-tree.enabler/18-context-loading.enabler/ISSUES.md` settles, so the audited head stays the dispatched head.

## The shipped test-evidence audit still produces the structured JSON verdict

The assertions state the sealed-run verdict model: the audit run's terminal status is `approved` or `rejected`, and the `test-evidence-auditor` wrapper relays the run token, the run file and the rendered projection. `src/plugins/spec-tree/skills/audit-tests/SKILL.md` and the wrapper still emit the `<verdict_format>` JSON object with no run token or run file, so the assertions describe behavior the shipped producer does not yet have.

**Settlement condition.** outcomeeng/changes#513 rewrites the skill and wrapper onto one `spx verification run` over the exact committed scope under an unchanged semantic verdict model.

**Evidence**: current-head CI review of pull request 671.

## The skill records NOT_APPLICABLE language results in metadata the verdict format does not declare `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `compose_language`, `auditor-verdict-format`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `auditor-verdict-format`: step `compose_language` records each composed language's NOT_APPLICABLE subjects "in verdict metadata", while the `<verdict_format>` metadata object declares only `branch`, `evidence_chain`, and `coverage_traces`.

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## The skill names its composed dependencies as slash invocations `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `load_context`, `composed-dependency-form`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `composed-dependency-form`: step `load_context` names `/understand` and `/contextualize` as slash invocations instead of `Use skill` instructions, and step `compose_language` loads `<lang>-test-standards` and invokes `audit-<lang>-tests` in prose the same way (run `2026-10-12_18-59-15-708-60d26c4e0044`).

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## The last constraint is an author-maintenance note about the skill's own grant `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `<constraints>`, `conciseness`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `conciseness` and `constraint-strong-modals`: the last `<constraints>` bullet is an author-maintenance note about the skill's own `Bash` grant, stated without MUST, NEVER, or ALWAYS.

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## The REJECT-finding constraint carries no rationale `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `<constraints>`, `constraint-rationale`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `constraint-rationale`: the constraint requiring every REJECT finding to name the assertion, the failed property, and the evidentiary gap carries no rationale after a dash.

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## The coverage principle and the first sentence of audit_coverage restate constraints `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `audit_coverage`, `conciseness`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `conciseness` (run `2026-10-12_18-55-10-807-92bff43a2c02`): the `JUDGE COVERAGE BY READING` principle and the first sentence of step `audit_coverage` restate the coverage-by-reading rule that `<constraints>` and Step 3e already state.

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## One step tag wraps three distinct steps `src/plugins/spec-tree/skills/audit-tests/SKILL.md`, `full_chain_ownership`, `semantic-tag-names`

The skill audit run `2026-10-12_18-41-36-254-8cb4eac53023` of
`src/plugins/spec-tree/skills/audit-tests/SKILL.md` at head
`ab5b519f0333258fc6e277b09a458b8b65920941` reported six findings on text the
changeset leaves unchanged; the changeset changes line 20 only
(`git diff -U0 2cf9cd80eebb49dc8a682f45dd08922551d54d76...ab5b519f0333258fc6e277b09a458b8b65920941 -- src/plugins/spec-tree/skills/audit-tests/SKILL.md`).

- `semantic-tag-names`: `<step name="full_chain_ownership">` wraps Steps 2b, 3, and 3a, three distinct steps under one name.

**Settlement condition**: the skill states the metadata field for NOT_APPLICABLE language results in `<verdict_format>`, composes `spec-tree:understand` and `spec-tree:contextualize` with `Use skill`, moves the grant note out of the runtime prompt, gives the REJECT-finding constraint its rationale, splits the combined step tag, and a skill audit approves.

## Assertion 15 requires a literal rule the skill does not define `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`, `assertion 15`, `literal-rule-undefined`

The sealed assertion-audit run `2026-10-17_01-48-01-824-32b1ebea83ce` of `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`, read at head `1097a3b67e61591f80830bc56e1f7091d46b1a1b`, reported two findings on text the changeset neither changes nor invalidates. Under property 11 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) both are standing. Base-ref evidence for both: `git diff -U0 origin/main HEAD` against `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md` and `src/plugins/spec-tree/skills/audit-tests/SKILL.md` records hunks only at `audit-tests.md:98` and `SKILL.md:299`, `:301`, and `:303`, so assertions 15 and 20 and the `SKILL.md` passages below lie outside every hunk.

- `literal-rule-undefined` (debt): assertion 15 of `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md:118` requires the literal rule at testability, coupling, falsifiability, and rejection, with the allowlist `{-1, 0, 1, 2}` for numbers and `{""}` for strings. `src/plugins/spec-tree/skills/audit-tests/SKILL.md:49` says only "Apply the literal rule by reading the test's literals against their sources". Neither it nor `test-evidence-standards` states the allowlist or applies the rule at the four points. Finding key `assertion:ordinal-15:spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md:literal-rule-undefined`. Run `2026-10-17_01-48-01-824-32b1ebea83ce`.

**Settlement condition**: the skill and `test-evidence-standards` state the numeric and string allowlist and apply the literal rule at testability, coupling, falsifiability, and rejection, and direct a rejection of bare literals to name a library origin, a production-owned constant, or a generator, and a skill audit and an assertion audit approve.

## Assertion 20 requires a remediation the skill does not direct `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`, `assertion 20`, `positive-pattern-remediation-absent`

The sealed assertion-audit run `2026-10-17_01-48-01-824-32b1ebea83ce` of `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md`, read at head `1097a3b67e61591f80830bc56e1f7091d46b1a1b`, reported two findings on text the changeset neither changes nor invalidates. Under property 11 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) both are standing. Base-ref evidence for both: `git diff -U0 origin/main HEAD` against `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md` and `src/plugins/spec-tree/skills/audit-tests/SKILL.md` records hunks only at `audit-tests.md:98` and `SKILL.md:299`, `:301`, and `:303`, so assertions 15 and 20 and the `SKILL.md` passages below lie outside every hunk.

- `positive-pattern-remediation-absent` (debt): assertion 20 of `spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md:123` requires the verdict to name a library origin, a production-owned constant, or a generator when bare literals are rejected. `src/plugins/spec-tree/skills/audit-tests/SKILL.md` and `test-evidence-standards` never direct the verdict to name one; the only remediation passage, `SKILL.md:55`, names remediation targets for rejected bindings and not for rejected literals. Finding key `assertion:ordinal-20:spx/21-spec-tree.enabler/68-audit.enabler/32-audit-tests.enabler/audit-tests.md:positive-pattern-remediation-absent`. Run `2026-10-17_01-48-01-824-32b1ebea83ce`.

**Settlement condition**: the skill and `test-evidence-standards` state the numeric and string allowlist and apply the literal rule at testability, coupling, falsifiability, and rejection, and direct a rejection of bare literals to name a library origin, a production-owned constant, or a generator, and a skill audit and an assertion audit approve.
