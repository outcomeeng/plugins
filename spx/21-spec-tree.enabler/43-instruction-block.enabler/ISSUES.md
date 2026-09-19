# Issues: Instruction Block

## Topology mapping evidence owns its cases in the linked test

`tests/test_instruction_block.mapping.l1.py:13` declares `_TopologyCase`, and
`_topology_cases()` selects the finite topology cases and expected region bodies
inside the linked test. The Python test standards require case data to come from
its semantic owner and expected results to follow an independent construction law.
The case table leaves the evidence dependent on the test author's selected examples.

**Evidence**: the isolated test-evidence audit of this node at
`4d1bd7bba4f66612ae57221295b624b215c65f5e` returned `REJECTED`, finding `f-001`,
for test-owned data. Its trace reaches the instruction-block mapping harness,
generator, distribution module, and shipped instruction-block script.

**Settlement condition**: the mapping evidence covers the complete finite topology
domain through a source-owned enumeration or meaningful generator and derives
expected region bodies independently, with every comparison in the linked test.
Moving the same hand-picked table into a generator alone does not settle the issue.

**Disposition**: Change #41 modifies the separate compliance test's exception
boundaries. The mapping test is outside that changeset's diff. The auditor-verdict
rule in `spx/15-merging.pdr.md` requires this finding to be recorded here and keeps
it from blocking that corrective merge; its rejected verdict remains recorded.

## Existing evidence re-declares production vocabulary and author-chosen expectations

The isolated test-evidence audit of this node on head `df87dc4ffbe8f209a10f75aa86874b7503ef60a0` rejected five artifacts the router-narrowing changeset did not touch, beside the topology-table finding recorded above:

- `tests/test_instruction_block.scenario.l1.py` hand-writes the status tokens `absent`, `stale`, and `current` that `InstructionStatus` in the shipped generator owns, and passes the harness keys `claude` and `codex` as literals where the generator's `AGENT_HARNESS_INSTRUCTION_FILENAMES` mapping and the harness constants already own them.
- `tests/test_instruction_block.compliance.l1.py` copies the module invocation, the lefthook path, the pre-commit build command, and the two retired direct-template arguments that `outcomeeng/distribution/instruction_block.py` declares as named constants, and its refresh-workflow tests choose their shell tokens and the digest width themselves, so no production behavior exists whose mutation fails them.
- `outcomeeng_testing/fixtures/instruction_block/near-identical-shared.md` stores the author's own computation of the expected common span over the two near-identical inputs and is consumed as a mapping expectation; the node's property harness already carries the independent oracle for that span.

**Evidence.** Findings `f-002` through `f-006` of that audit; each subject lies outside the changeset's diff, so the merging decision routes them here rather than to the merge.

**Settlement condition.** The scenario and compliance tests import every status token, harness key, and build constant from its owning module; the refresh-workflow assertions read their expected tokens from a source-owned workflow contract or reclassify; the near-identical expectation derives from the property harness's oracle instead of a stored answer; and a test-evidence audit of the node approves.

## `/update-instruction-block` Step 5 reads as one paragraph over six topologies

Step 5 of `src/plugins/spec-tree/skills/update-instruction-block/SKILL.md` verifies six distinct first-encounter topologies — an established surface with a valid region, the bootstrap span mapping, one file missing, both files missing, a delegating body adopted, and tracked-versus-untracked recoverability — in one unbroken paragraph. An operator scanning it after a run parses the whole block to find the branch matching their topology. Step 3's ambiguity reports already use the per-branch bullet shape this section wants.

`<examples>` covers stale-router regeneration, delegation adoption, and a recency tie. The one-file-missing seeding topology that Step 4 and Step 5 both name carries no worked example.

**Resolution shape**: restructure Step 5's verification into one bullet per topology, mirroring the nested detection/recommendation/apply shape Step 3's five report kinds now carry, and add a further example showing a repository with only one root instruction file present, its seeded counterpart, and the resulting region wrap.

**Why it is large**: the restructure rewords all six topology branches, not the clauses a delegation change appends, and the missing example is for a topology no delegation change touches. Step 3's five ambiguity bullets are no longer part of this entry: a change edited one of them, which exhausted their deferral, and all five were restructured in that changeset. Both are editorial passes over the whole skill body whose surface is the file's structure rather than any one behavior, and each invalidates the skill-authoring gate for the entire surface — best taken in one pass gated by `skill-auditor` rather than folded into an unrelated behavior change.

**Evidence**: surfaced by `instructions:audit-skills` on the changeset that added delegating-root-file adoption, as `worth-improving` findings on an otherwise approved surface. The same audit's two other findings are resolved in that changeset: the three stop conditions carry explicit `GATE` labels, and the two success criteria that asked for a confirmation now name the diff that decides them.

## Root instruction terminology decision

The node concept is "instruction block" across this node, its decision, the generator, the skill and template, the recipes, the workflow, the root instruction-file prose, and `spx/15-validation.enabler/32-runtime-token.enabler/runtime-token.md`. The broader term "guide" remains internally consistent for these distinct surfaces:

- `spx/15-validation.enabler/32-reference-portability.enabler/reference-portability.md` and `outcomeeng/validation/reference_portability.py` — "retired generated guide paths `spx/CLAUDE.md` and `spx/AGENTS.md`".
- `spx/18-plugin-build.enabler/15-build-architecture.adr.md` — "the agent guide read as `CLAUDE.md`/`AGENTS.md`" and the `file`-kind token.
- `spx/21-spec-tree.enabler/76-merge.enabler/merge.md` and the merge skills — "never … editing a generated guide".
- The build runtime-token registry name `root_guide` (`outcomeeng/distribution/build.py`) and its ~60 `{{! file('root_guide') !}}` call sites across every plugin, governed by `spx/18-plugin-build.enabler/21-source-and-templating.enabler/21-runtime-parameterization.enabler`.

Renaming "the agent guide" and `root_guide` requires one product-vocabulary decision followed by a coordinated build-token migration. Revisit this issue before any change renames either term; until that decision, "guide" remains the general description of the root files and `root_guide` remains the build token.

## Generator migration awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` runs well past the fifty-line threshold — parse, dotted-version compare, language/harness filtering, router rendering, shared-region parsing with whole-side git-recency reconcile, and biggest-identical-span bootstrap — imported as a module by `outcomeeng_testing/harnesses/instruction_block.py` and exercised by the four `l1` suites here. Past fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose logic moves into the SPX CLI once the script proves its value; this generator has proven its value many times over. The render model (router block plus shared regions, reconciled by git recency) keeps that obligation alive even though it deletes the earlier command-slot parser.

The migration requires an unpublished `@outcomeeng/spx` capability and a cross-repo port. Until that capability is published and the consuming floor advances, the generator ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md`. The migration is filed in the spx CLI's session queue (`outcomeeng/spx`, handoff `2026-07-04_14-49-08`); revisit this issue when that handoff publishes the required capability.

## The background updater duplicates its skill and leaves write authority undefined

The configured-agent audit of
`src/plugins/spec-tree/agents/instruction-block-updater.md` during Change #76
rejected three boundaries:

- the wrapper runs `--reconcile` and `--write` through `Bash` while its source
  declares no native writable sandbox boundary;
- its role and protocol still describe `spec-tree:update-instruction-block` as
  preloaded or injected even though generated Codex configuration explicitly
  says skill enablement is not a preload guarantee; and
- its protocol copies the skill's detect, reconcile, render, write,
  verification, marker-reading, and ambiguity handling instead of remaining a
  thin skill-backed wrapper.

**Required handling**: choose the native workspace-write boundary for the two
root instruction files, reduce the wrapper to an explicit skill invocation plus
the background runner's material non-interactive constraint, and relay the
skill-owned result contract. Retain one minimal isolated update against a
disposable product checkout.

**Evidence**: `instructions:subagent-auditor` findings `f-001` through `f-003`
against `src/plugins/spec-tree/agents/instruction-block-updater.md` on Change
#76 head `843ddd709b058970d414ec755cc10121ff6bb5ff`.

## Generated root instruction files exceed the declared byte budget

The `regenerate-instruction-blocks` pre-commit hook reports
`CLAUDE.md 58417/32768 breach (25649 over)` and
`AGENTS.md 61159/32768 breach (28391 over)`. The render-model decision keeps a
standing breach report-only until the surface fits, then fails regressions, so
the hook succeeds while the harness can truncate both files.

**Required handling**: continue moving operational policy from the root router
into the skills that consume it until both generated files fit the 32768-byte
combined project-document ceiling, then preserve the passing boundary in the
gate.

**Evidence**: repeated `regenerate-instruction-blocks` hook output while
committing Change #76, including commit
`7ddd752f1cf44e22a51fe7beed45225c99e6a393`.

## Pinned router prose is coupled to structural test evidence

**Evidence.** Five `[test]` claims pin the Codex canonical-subagent-registry
wording, missing-definition repair wording, checkout scope-split wording,
operator-question mutation-privilege-revocation wording, and Codex
Verifier-spawning-boundary wording. The drift-gate assertion describes a
regression by "a surface that previously fit," introducing temporal wording into
an atemporal spec. The Operator questions exception for an orchestrating session
with officers in flight has no assertion. `spx/12-shipped-scripting.adr.md`
establishes that agreement between a spec-declared value and its complying
source uses audit evidence because every deterministic oracle repeats the
declaration. `spx/15-spec-coverage.adr.md` establishes that tests over Markdown
structure prove formatting rather than behavior.

**Impact.** The five links couple Passing to pinned wording and structure while
providing no behavioral verdict for the claims they label; the drift-gate claim
records history rather than permanent truth; and the Operator questions
exception has no declared verification path.

**Settlement condition.** The instruction-block node's decision names one
verification form for pinned router prose, the drift-gate claim states its rule
atemporally, and the Operator questions exception is authored as an assertion in
that form.
