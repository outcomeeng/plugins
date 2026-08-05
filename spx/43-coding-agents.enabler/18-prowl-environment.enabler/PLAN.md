## Eval coverage for the operate-prowl skill body

The delegation-handback, environment-trap, and operator-target-resolution
assertions carry `[audit]` evidence, matching the node's existing evidence model
for claims about what a shipped skill instructs. Two of the three are reachable
by `[eval]`: a producer-file suite over
`src/plugins/coding-agents/skills/operate-prowl/SKILL.md` could grade a
structured verdict for target resolution and for handback ordering.

**Why this is a separate slice**: it needs a new eval suite with its own
`prompt.template.md`, a case set, CI trigger regeneration, and cost-bearing
runs against a second producer — the coordination suite's producer is
`coordinate-agents` and cannot exercise `operate-prowl`'s own prose. The
environment-trap assertion stays `[audit]` regardless, since no structural
verdict distinguishes a skill that names a trap from one that does not.

**Next step**: author `evals/operation-surface/` with `prompt_source.producer`
set to the operate-prowl skill body, covering operator-target resolution and
handback push ordering, and re-tag those two assertions `[eval]`.
