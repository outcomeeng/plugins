# Issues: Verification

Known defects in this node's governance. Coordination note; not spec truth.

## The eval-prompt relation claims seven hand-authored prompts

`spx/local/generated-sources.toml` declares a relation whose `outputs` glob is
`spx/**/evals/**/prompt.md`, with sources spanning each eval's
`prompt.template.md` and `eval.toml` plus `src/plugins/**`, `dist/claude/**`, and
`dist/codex/**`, and `just eval-materialize-prompts spx` as its regeneration
command.

The glob is unrestricted, and only some of the files it claims are generated.
Nineteen `prompt.md` files sit under `spx/`; twelve of their `eval.toml` files
carry a `[prompt_source]` table naming `kind`, `producer`, and `template`, and
`outcomeeng_evals/producer_prompt.py` renders those twelve. The remaining seven
declare no `[prompt_source]` and are hand-authored.

The consequence runs opposite to an undeclared extent. Because the root guide
keys the exclusion on the declaration, agentic verification excludes every file
the glob claims — including the seven authored ones — so a reviewer skips
authored spec content as though a generator had produced it, and a defect in one
of those prompts reaches the default branch unjudged. The regeneration command
only rewrites the twelve it can render, so the gate never contradicts the
over-broad claim.

**Resolution shape**: restrict the relation's `outputs` to the evals that declare
`[prompt_source]`, or split it into one relation for the generated twelve and an
explicit non-generated classification for the seven. The governing decision is
this node's
[`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md),
which owns whether a declaration may claim a file its generator never writes.

**Evidence.** An earlier form of this entry recorded the inverse defect — the
extents were generated but undeclared, and the relation's `regenerate` field
named no `just` recipe. Both are resolved: the relation and
`just eval-materialize-prompts` now exist. That fix chose the unrestricted glob,
which converts the original risk into the live one recorded above.

**Why this is separate.** The fix edits `spx/local/generated-sources.toml`, a
governance surface whose governing decision is this node's
[`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md), and it must classify all nineteen `prompt.md`
files. That belongs to this node's decision, not to a changeset that renames
skills.

## Three decisions in this subtree carry untyped Verification rules

`/verify`'s decision grammar groups every decision rule under `### Testing`,
`### Eval`, or `### Audit` and gives it that subsection's tag. Every product-level
decision follows it. Three decisions in this subtree place their rules directly
under a bare `## Verification` with no subsection and no tag on any rule:

| Decision                                                                                                                                                                                                                                         | Untagged rules |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| [`spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/18-verification-component.adr.md)                                                                       | 4              |
| [`spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md)                   | 6              |
| [`spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/21-conformance-verification.enabler/15-skill-instrumentation.pdr.md) | 6              |

An untagged rule names no verification type, so nothing selects evidence for it
and `/audit-adr` and `/audit-pdr` reject the decision on every run.

**Resolution shape**: route each rule through `/verify` to select its type from
the verdict its real subject can produce, then group the rules under the matching
subsection and apply that subsection's tag. Several rules in
[`spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/21-adapter-contract.adr.md) describe deterministic process behavior — bounded
subprocess, no resident watcher, verbatim telemetry fields — so the sweep may
select `### Testing` for some rules rather than sending all three decisions to
`### Audit`.

**Evidence.** Surfaced by the `/audit-pdr` verdict that rejected
[`spx/14-skill-naming.pdr.md`](spx/14-skill-naming.pdr.md) for exactly this defect. That PDR is fixed in the
changeset that found it; the defect-class sweep across the touched node reaches
these three, which sit under decisions this changeset does not otherwise govern
and whose contexts are not loaded.

## The agentic runners carry no generated-extent skip mechanics

The bundled review and audit runners record no skipped generated extent in a run journal. The skip-and-record disposition [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md) declares reaches agentic runs through the root-instruction rule their agents load, which cannot emit scope-evidence journal events.

**Settlement condition.** The `spx` verification scope projection ships and the review and audit runners consume its projection in place of the instruction prose.

## The coherence audit names no declared generated-source relationship

`spx/21-spec-tree.enabler/68-audit.enabler/32-changeset-coherence.enabler/changeset-coherence.md` and the shipped `src/plugins/spec-tree/skills/audit-changeset-coherence/SKILL.md` require declared generated-source relationship evidence without naming `spx/local/generated-sources.toml` as that source or citing the governing decision.

**Settlement condition.** The node spec cites the declaration and the decision, and the skill reads its evidence from the declaration, in one changeset that carries the plugin version bump, the regeneration and the skill audit.

## Generators that consume their own declared inputs carry no migration obligation

`outcomeeng/catalog/plugin_catalog.py` reading `.claude-plugin/marketplace.json` and `outcomeeng_evals/ci_triggers.py` discovering `eval.toml` files are generators consuming their own declared inputs. They generate; they derive no generated-source attribution, so [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md) places no migration obligation on them. A Verifier skips this class.

**Revisit condition.** Either generator begins deriving generated-source attribution, which brings the migration obligation, or [`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md) states that a generator consuming only its own declared inputs carries none, after which this entry is deleted.

## A merging decision governs the apply flow's Verifier dispatches

[`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) is titled "Agent Authority over Merging" and opens on the `VERIFY -> PREVIEW -> MERGE -> DEPLOY -> RELEASE -> CLOSE` lifecycle, while its dispatch-readiness, repeated-class, finish-before-wait and bounded-projection rules bind the apply flow's per-node and whole-changeset gates as well. The rules' natural owner is [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), which already decides who dispatches an agentic verification, the Author and Verifier isolation, the defect-class sweep, the commit-before-read boundary and the deterministic-before-agentic ordering.

**Settlement condition.** The readiness record, repeated-class invalidation, finish-before-wait and bounded-projection rules move into [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) reduces to the merge-lifecycle specialization that cites them, and the realizing assertions in `spx/21-spec-tree.enabler/76-merge.enabler/merge.md`, `spx/21-spec-tree.enabler/65-apply.enabler/apply.md` and the two PR-lifecycle node specs re-point; `merging-standards` keeps the section text its merge transports read.

**Revisit condition.** A third workflow outside the delivery path needs the readiness record, or [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) is next restructured.

## An implementation audit and a changeset review read one shipped executable to opposite verdicts

On head `ccaef088c98007c963125af0fc621040d1f6b51b`, `spec-tree:implementation-auditor` run `2026-09-22_20-40-39-797-98d0f564dc05` approved `src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py` with zero findings, and `spec-tree:changes-reviewer` run `2026-09-22_20-40-26-221-404eea4ba809` rejected line 181 of the same file by executing it: a JSON array under a read's `cause` raised `TypeError` outside the refused-source handler, against a contract of one invalid-input result on stdout and exit two. The repair landed at `1ea3cf1567a963c6466366098155fcaa3a04d01a`; the divergence is a difference in what each Verifier looked at.

**Impact.** An implementation audit's approval of an executable carries no claim about the behavior the code's declared contract makes, so the two verdicts cannot both stand as gate evidence for one claim.

**Settlement condition.** A decision states whether an implementation audit of a shipped executable executes it, so that audit's scope and verdict claim say so, or whether the verdict about executed behavior belongs only to a Verifier that executes, so the audit's approval is scoped to what reading establishes. [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md) bars an agentic run from running deterministic verification; whether a one-off execution of the subject is that is part of what is unsettled.

**Related.** The two Verifier rules that collide on pinning a spec-declared tuning value, in the verification subtree's test-verification node, record two Verifiers reading two decisions to opposite verdicts, which amending one decision resolves.
