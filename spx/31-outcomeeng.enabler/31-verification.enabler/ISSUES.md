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
`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`,
which owns whether a declaration may claim a file its generator never writes.

**Evidence.** An earlier form of this entry recorded the inverse defect — the
extents were generated but undeclared, and the relation's `regenerate` field
named no `just` recipe. Both are resolved: the relation and
`just eval-materialize-prompts` now exist. That fix chose the unrestricted glob,
which converts the original risk into the live one recorded above.

**Why this is separate.** The fix edits `spx/local/generated-sources.toml`, a
governance surface whose governing decision is this node's
`15-generated-attribution.pdr.md`, and it must classify all nineteen `prompt.md`
files. That belongs to this node's decision, not to a changeset that renames
skills.

## Three decisions in this subtree carry untyped Verification rules

`/verify`'s decision grammar groups every decision rule under `### Testing`,
`### Eval`, or `### Audit` and gives it that subsection's tag. Every product-level
decision follows it. Three decisions in this subtree place their rules directly
under a bare `## Verification` with no subsection and no tag on any rule:

| Decision                                                              | Untagged rules |
| --------------------------------------------------------------------- | -------------- |
| `18-verification-component.adr.md`                                    | 4              |
| `21-agentic-verification.enabler/21-adapter-contract.adr.md`          | 6              |
| `21-conformance-verification.enabler/15-skill-instrumentation.pdr.md` | 6              |

An untagged rule names no verification type, so nothing selects evidence for it
and `/audit-adr` and `/audit-pdr` reject the decision on every run.

**Resolution shape**: route each rule through `/verify` to select its type from
the verdict its real subject can produce, then group the rules under the matching
subsection and apply that subsection's tag. Several rules in
`21-adapter-contract.adr.md` describe deterministic process behavior — bounded
subprocess, no resident watcher, verbatim telemetry fields — so the sweep may
select `### Testing` for some rules rather than sending all three decisions to
`### Audit`.

**Evidence.** Surfaced by the `/audit-pdr` verdict that rejected
`spx/14-skill-naming.pdr.md` for exactly this defect. That PDR is fixed in the
changeset that found it; the defect-class sweep across the touched node reaches
these three, which sit under decisions this changeset does not otherwise govern
and whose contexts are not loaded.
