# Issues: Bootstrapping

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The authoring flows still instruct creating PLAN.md notes

Methodology 4.0 admits `ISSUES.md` as the only node-local note and routes pending work to a Change; the `/understand` foundation states both rules in its coordination model, and `spx/knowledge/log.md` records the retirement of every `PLAN.md` note in this repository. The authoring surfaces still teach the retired artifact as live structure-intent input:

- `bootstrapping.md` asserts "record top-level product intent, constraints, examples, and unresolved questions in `spx/PLAN.md` when the user provides candidate areas", and the shipped `/bootstrap` skill creates `spx/PLAN.md` for every newly bootstrapped product tree (`src/plugins/spec-tree/skills/bootstrap/SKILL.md` lines 81, 110, 121, 133, 158, 164 and 184).
- `/decompose` reads `spx/PLAN.md` and node-local `PLAN.md` files as structure intent and records reserved index horizons in them (`src/plugins/spec-tree/skills/decompose/SKILL.md` lines 48, 55, 57, 77, 92, 212, 275 and 276), and `decomposing.md` states the same behavior at its lines 19 and 28.
- `aligning.md` line 20, `refactoring.md` line 18 and `spx/21-spec-tree.enabler/54-authoring.enabler/69-spec-workflow.enabler/spec-workflow.md` line 19 name `PLAN.md` as the place for remaining delivery work and as a note to preserve.
- The router template names "`PLAN.md`/`ISSUES.md` structure intent" in `src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md` line 109, and the template renders into the managed blocks of the root `CLAUDE.md` and `AGENTS.md`.

**Impact.** A tree bootstrapped or decomposed through these flows, in this repository or a consumer's, acquires the `PLAN.md` notes the methodology no longer admits, so the retirement this repository completed does not hold for new work.

**Settlement condition.** No shipped skill, template or spec instructs creating a `PLAN.md` note in a tree authored under methodology 4.0. Each passage routes the intent to a Change or an `ISSUES.md` entry, or scopes the `PLAN.md` note to a tree authored under a 3.x version, the form the `/understand` foundation already states.

**Carriers.** `outcomeeng/changes#21` carries the `/author`, `/align`, `/contextualize` and `/refactor` routing. `outcomeeng/changes#19`, now Refined, carried the `/decompose` routing. No Change yet carries this node's spec and assertion, the `/bootstrap` skill or the router template.

**Evidence.** The current-head CI review of pull request #621 on head `05f37665892f0c008a9c6f792dc360ea4396aa51` (run `https://github.com/outcomeeng/plugins/actions/runs/37174605666`) reported the gap as a `DEBT` finding in category `consistency`, citing the sites above.
