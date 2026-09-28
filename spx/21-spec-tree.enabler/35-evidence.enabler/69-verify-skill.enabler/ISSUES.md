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
against `evals/routing/cases.jsonl`. Six cases describe the subject in wording that
mirrors the producer's `classify-subject` table: in
`routes-semantic-constraint-to-audit`, `accepts-slugged-audit-tag`,
`routes-structured-producer-to-evaluate`, `routes-observation-claim-to-probe`,
`routes-observation-claim-to-probe-specialist`, and
`routes-deterministic-behavior-to-test`, the `subject.kind` and `subject.verdict`
inputs are nearly readable from keywords. A later eval-evidence audit finding states
the same defect, verbatim: "In routes-semantic-constraint-to-audit,
accepts-slugged-audit-tag, routes-structured-producer-to-evaluate,
routes-observation-claim-to-probe, routes-observation-claim-to-probe-specialist and
routes-deterministic-behavior-to-test, the subject.kind and subject.verdict inputs
nearly restate the producer's classify-subject table rows (for example 'no
deterministic or structurally scored verdict', 'attested observation of the running
node through an executed protocol', 'structured JSON projection scored by fixed
cases'). Given the enum values listed in prompt.template.md, the answer is visible
without applying the producer's methodology."

**Impact**: a producer that matches keywords instead of classifying the verdict
the subject can produce passes those cases, so they supply weak evidence for the
routing assertions they back.

**Settlement condition**: the `subject.kind` and `subject.verdict` wording of all
six cases above no longer mirrors the `classify-subject` table, and an
eval-evidence audit reports no `oracle-leakage` warning.

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

## The read-order principle forbids a read that context loading already performs

**Evidence**: `instructions:skill-auditor` warning `f-009`, severity `WARNING`, rule `internal-consistency-read-order`,
against `src/plugins/spec-tree/skills/verify/SKILL.md` line 18, verbatim: "the
principle says \"Read no subject before its tag shape validates\", and line 43 says
to inspect tag shape \"before reading the subject\". But load-context already reads
every assertion or rule (line 35) and snapshots its exact text (line 37) before
validate-input runs, and line 45 refers to \"its `subject` field\", which the skill
never defines. Change to: state the prohibition in terms the steps can satisfy, and
define or drop \"subject field\"." The cited lines hold that text at head
`0c5ea733221d272f571005528ec87bcb7fb1e1dc`.

**Impact**: `load-context` reads and snapshots every subject before `validate-input`
runs, so no run of the workflow satisfies the principle as written, and the blocked
path's stopping point names a field the skill never defines, leaving what Claude may
read before blocking a subject undecidable.

**Settlement condition**: the skill states the prohibition in terms its steps can
satisfy and defines or drops "subject field", and an isolated skill audit of
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no finding under the rule
`internal-consistency-read-order`.

## The audit input rule hands subjects to a specialist the workflow never runs

**Evidence**: `instructions:skill-auditor` warning `f-011`, severity `WARNING`, rule `internal-consistency-audit-route`,
against `src/plugins/spec-tree/skills/verify/SKILL.md` line 83, verbatim: "the audit
bullet opens with \"the route hands its specialist every subject selected for
audit\", then says the specialist is the isolated verifier, \"which this workflow
never runs\". Change to: wording that says the audit route hands nothing to a
specialist and writes the tag itself." The cited line holds that text at head
`0c5ea733221d272f571005528ec87bcb7fb1e1dc`.

**Impact**: the audit bullet's input rule and its next sentence contradict each
other on whether anything is handed off, so a reader can take the audit route as a
specialist dispatch and look for a hand-off result the workflow never produces.

**Settlement condition**: the audit bullet states that the audit route hands nothing
to a specialist and writes the tag itself, and an isolated skill audit of
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no finding under the rule
`internal-consistency-audit-route`.

## The report-table rule covers a blocked assertion but not a blocked decision rule

**Evidence**: `instructions:skill-auditor` warning `f-012`, severity `WARNING`, rule `coverage-gap-blocked-decision-rule`,
against `src/plugins/spec-tree/skills/verify/SKILL.md` line 129, verbatim: "the
human-table rule covers only \"a blocked assertion\", but validate-input (line 43)
can also block a decision rule. Change to: cover every blocked subject, both spec
assertions and decision rules." The cited lines hold that text at head
`0c5ea733221d272f571005528ec87bcb7fb1e1dc`.

**Impact**: a decision target with an unsupported tag shape produces a blocked row
whose subject column has no stated rendering, so the table may repeat the tag text
the blocked path forbids repeating.

**Settlement condition**: the human-table rule covers every blocked subject, spec
assertions and decision rules alike, and an isolated skill audit of
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no finding under the rule
`coverage-gap-blocked-decision-rule`.

## One paragraph carries four separate input rules

**Evidence**: `instructions:skill-auditor` warning `f-013`, severity `WARNING`, rule `readability-dense-paragraph`,
against `src/plugins/spec-tree/skills/verify/SKILL.md` line 78, verbatim: "one
paragraph of about 180 words defines tag ownership, keep-or-replace, placing decision
rules, and snapshot coverage together. Change to: separate those rules, for example
as a list." The cited line holds that paragraph at head
`0c5ea733221d272f571005528ec87bcb7fb1e1dc`.

**Impact**: applying any one of the four rules requires parsing the other three, and
an edit to one sentence can silently change another rule sharing the paragraph.

**Settlement condition**: tag ownership, keep-or-replace, decision-rule placement,
and snapshot coverage each stand as a separate rule, and an isolated skill audit of
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no finding under the rule
`readability-dense-paragraph`.
