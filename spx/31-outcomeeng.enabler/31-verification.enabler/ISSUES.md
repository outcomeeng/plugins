# Issues: Verification

Known defects in this node's governance. Coordination note; not spec truth.

## Materialized eval prompts are generated extents with no declared relation

`spx/local/generated-sources.toml` declares six relations and is described by the
root guide as "the committed declaration of every generated extent in this
repository". Materialized eval prompts are not among them.

Twelve `eval.toml` files (of nineteen `prompt.md` files under `spx/`) carry a
`[prompt_source]` table naming `kind`, `producer`, and `template`.
`outcomeeng_evals/producer_prompt.py` renders each producer into its sibling
`prompt.md`, and the `eval-prompts` gate step runs
`outcomeeng-evals materialize-prompts spx --repo-root . --check`, which
regenerates and byte-compares them. A file a gate regenerates and byte-compares
is a generated extent by the same test every declared relation satisfies.

Two consequences follow from the gap:

- Agentic verification cannot exclude these extents from judgment, because the
  exclusion is keyed on the declaration and the root guide forbids inferring
  generated status from path names. A reviewer reading a `prompt.md` diff judges
  rendered producer text as if it were hand-authored spec content.
- A drifted prompt has no sanctioned repair command. Every other relation names a
  `just` recipe in its `regenerate` field; the repo has no
  `just materialize-prompts`, so repairing the gate means invoking
  `outcomeeng-evals` directly, against the root guide's Justfile-interface rule.

**Resolution shape**: author the relation under
`spx/31-outcomeeng.enabler/31-verification.enabler/15-generated-attribution.pdr.md`
— outputs `spx/**/evals/**/prompt.md` restricted to evals declaring
`[prompt_source]`, sources the producer file and `prompt.template.md` each
`eval.toml` names plus the `eval.toml` itself, generator
`outcomeeng_evals/producer_prompt.py` — and add the `just` recipe its
`regenerate` field names. Decide first whether the `outputs` glob may cover the
seven `prompt.md` files that declare no `[prompt_source]` and are therefore
hand-authored, since a relation that claims them would exclude authored content
from judgment.

**Evidence.** Surfaced when the `eval-prompts` gate step failed on
`spx/43-coding-agents.enabler/32-inter-worktree-coordination.enabler/evals/coordination-decision/prompt.md`
after its `/coordinate-agents` producer advanced on the default branch. The
regeneration was committed; the attribution gap it exposed is recorded here.

**Why this is separate.** The fix edits `spx/local/generated-sources.toml`, a
governance surface whose governing decision is this node's
`15-generated-attribution.pdr.md`, and it must classify all nineteen `prompt.md`
files rather than the one a regeneration touched. Both belong to this node's
decision, not to a changeset that regenerated a single extent.

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
