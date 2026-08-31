# Issues: Instruction Block

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
