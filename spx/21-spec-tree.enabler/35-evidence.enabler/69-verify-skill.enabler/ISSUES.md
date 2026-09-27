# Issues

## Routing eval run history is stale

The newest passing row for `evals/routing` (9/9, git SHA
`4a8fdd878001296cf9a11cc2fa2be1a3ad9997fb`) predates later changes to the
producer, cases, assertions, and materialized prompt. It supplies no passing
execution claim for the current routing behavior.

The isolated eval-evidence audit reported `FAIL` on 2026-09-15, finding `f-001`
in the history file during Change #14. A later audit reported `f-005` on head
`a65659114b99767b90b4d920550fff5dc0824794` during Change #76 after its
frontmatter rewrite rematerialized the prompt. The operator instructed that
local eval execution remain skipped while normal CI is allowed; no current
passing run is claimed.

**Settlement condition**: one passing run of
`just eval spx/21-spec-tree.enabler/35-evidence.enabler/69-verify-skill.enabler/evals/routing/eval.toml`
on a head that carries the current producer, with its row committed to
`history.jsonl`, followed by an independent eval-evidence audit accepting that
evidence.

## The blocked result names structured fields the declared output does not carry

**Evidence**: `instructions:skill-auditor` finding `f-006`, severity `WARNING`, rule
`undefined_output_contract_reference`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` on head
`acf15245ac7d9ef4d2fa40b79431041d27974d61`. The `validate-input` step instructs
setting `verification_type`, `specialist`, and `evidence_shape` to `null` in
structured output, and two later lines reference an evidence shape and a terminal
blocked shape, while the skill's only declared output is a five-column text table
carrying none of those field names.

**Impact**: a normative instruction stands against an output contract the skill
never declares, so two runs can emit different blocked payloads and the first
success criterion cannot be falsified.

**Settlement condition**: the skill declares the structured shape whose field
names those instructions use, or states the blocked result solely in the declared
table's terms, and an independent skill audit accepts the result contract.

## Four principles restate rules the workflow already states in full

**Evidence**: `instructions:skill-auditor` finding `f-007`, severity `WARNING`,
rule `conciseness_duplication`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` on head
`acf15245ac7d9ef4d2fa40b79431041d27974d61`. Four `<essential_principles>` bullets
repeat the tag grammar, the evidence-shape derivation, the runtime-catalog check,
and the judgment boundary that individual workflow steps already state.

**Impact**: the tag grammar and the evidence-shape rule each live in two places,
so the next grammar change has two sites to keep in step, and the duplicated
bullets add no capability at trigger time.

**Settlement condition**: `<essential_principles>` retains only the invariants
that hold across steps, each workflow step owns its own grammar and shape detail,
and an independent skill audit accepts the reduced principles.
