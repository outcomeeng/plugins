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

## Four principles restate rules the workflow already states in full

**Evidence**: `instructions:skill-auditor` finding `f-007`, severity `WARNING`,
rule `conciseness_duplication`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` on head
`acf15245ac7d9ef4d2fa40b79431041d27974d61`. Four `<essential_principles>` bullets
repeat the tag grammar, the evidence-shape derivation, the runtime-catalog check,
and the judgment boundary that individual workflow steps already state.

**Impact**: the tag grammar and the evidence-shape rule each live in two places,
so the next grammar change has two sites to keep in step, and the duplicated
bullets add no capability at trigger time. The skill auditor's warning `f-011` on
head `5f9bb8e6200221bbe3b812b947b2f96dbeb686df` also names the blocked-result
shape and the `capability-required` semantics, each stated in both the
principles and the workflow steps.

**Settlement condition**: `<essential_principles>` retains only the invariants
that hold across steps, each workflow step owns its own grammar and shape detail,
and an independent skill audit accepts the reduced principles.

## Routed eval cases mirror the producer's classification wording

**Evidence**: eval-evidence auditor warning `f-002`, class `oracle-leakage`,
against `evals/routing/cases.jsonl`. Several routed cases describe the subject in
wording that mirrors the producer's `classify-subject` table, so
`routes-semantic-constraint-to-audit`, `routes-structured-producer-to-evaluate`,
`routes-observation-claim-to-probe`, and
`routes-observation-claim-to-probe-specialist` are nearly readable from keywords.

**Impact**: a producer that matches keywords instead of classifying the verdict
the subject can produce passes those cases, so they supply weak evidence for the
routing assertions they back.

**Settlement condition**: routed-case wording no longer mirrors the
`classify-subject` table, and an eval-evidence audit reports no
`oracle-leakage` warning.

## Routed path-bearing cases cannot observe the specialist-result validation

**Evidence**: eval-evidence auditor warning `f-003` against `evals/routing/cases.jsonl`,
verbatim: "The routed path-bearing cases (routes-deterministic-behavior-to-test,
routes-cli-state-readout-to-test, routes-cli-model-behavior-to-evaluate,
routes-structured-producer-to-evaluate, routes-observation-claim-to-probe-specialist)
expect status 'routed'. The producer's record-result table ends a path-bearing route
'routed' only after the specialist result passes validation. The case input supplies
no specialist result, so these cases cannot tell a producer that follows the
validation rule from one that reports 'routed' once the catalog lists the specialist."

**Impact**: a producer that reports `routed` as soon as the runtime skill catalog
lists the selected specialist, without validating that specialist's result, passes
every routed path-bearing case, so those cases supply no evidence for the
validation row that separates `routed` from `capability-required` on a failed check.

**Settlement condition**: the routing eval's case input carries a specialist result
for each routed path-bearing case, a case whose specialist result fails validation
expects `capability-required` with the failed check, and an eval-evidence audit
reports no `f-003`-class warning against the routed cases.
