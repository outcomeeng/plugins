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

## Two principles still restate rules the workflow states in full

**Evidence**: `instructions:skill-auditor` finding `f-007`, severity `WARNING`,
rule `conciseness_duplication`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` on head
`acf15245ac7d9ef4d2fa40b79431041d27974d61` named four `<essential_principles>`
bullets repeating the tag grammar, the evidence-shape derivation, the
runtime-catalog check, and the judgment boundary; warning `f-011` on head
`5f9bb8e6200221bbe3b812b947b2f96dbeb686df` added the blocked-result shape and the
`capability-required` semantics. The reduction has been applied: at head
`5887001573e291dc8689b1f80510d75cab374880`, where every line number and quotation
in this entry holds, `<essential_principles>` is six bullets at lines 18–23 and
states no tag grammar, evidence-shape derivation, runtime-catalog check, or
`capability-required` semantics; those live only in `validate-input`,
`route-specialist`, and `record-result`. Two restatements remain:

- The blocked-result sentence, line 18: "unsupported input takes the blocked
  result and nothing else", which `validate-input` states in full at line 45:
  "Its only output is the blocked row of `record-result`." The same bullet's
  first clause is the subject of the read-order entry below.
- The judgment boundary, line 23: "Construct no evidence and render no verdict:
  the selected specialist owns test evidence, eval evidence, or the probe
  protocol and its attested run, and the isolated verifier owns the audit
  verdict", which the `route-specialist` bullets at lines 80–83 state route by
  route — each path-bearing specialist owns and writes its own evidence, and the
  audit bullet names "the isolated verifier, which this workflow never runs" —
  and which success criterion line 158 restates as "it produces no agentic
  verdict and no attested run".

**Impact**: each of these two rules lives in a principle and in a workflow step,
so a change to the blocked result or to specialist ownership has two sites to
keep in step. The other four bullets — selection before specialization, the
classification boundary that `classify-subject` cites at line 60 instead of
restating, edit retention across `route-specialist` and `record-result`, and
one-directional routing — are not among the restatements `f-007` and `f-011`
named.

**Settlement condition**: an independent skill audit of the current
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no `conciseness_duplication`
finding against `<essential_principles>`, either accepting the blocked-result
sentence and the judgment boundary as invariants that hold across steps, or after
each is reduced to its invariant with the detail left to the step that owns it.

## Eval cases outside the audited six keep the producer's classification wording

**Evidence**: eval-evidence auditor warning `f-002`, class `oracle-leakage`, named
six routed cases of `evals/routing/cases.jsonl` whose `subject.kind` and
`subject.verdict` inputs restated the producer's `classify-subject` table rows.
Those six now describe each subject by what it is, what it emits, and what settles
it, and share no phrase of two or more words with that table. A changes-review
`debt` finding showed that the entry's first enumeration of the remaining cases was
not exhaustive. A sweep of every case's `subject.kind` and `subject.verdict`
against the `classify-subject` table and the classification-boundary principle of
`src/plugins/spec-tree/skills/verify/SKILL.md` finds the retired wording in each
case below:

- Routed:
  - `routes-cli-state-readout-to-test` — the kind "deterministic CLI registry"
    names the test row's deciding word in a case that expects test; the verdict's
    "LLM" is the evaluate-side word the case exists to exercise.
  - `routes-cli-model-behavior-to-evaluate` — the kind "CLI exposing
    model-generated recommendations" carries the principle's "model-generated", and
    the verdict's "An LLM interprets" carries the evaluate row's "LLM", in a case
    that expects evaluate; the verdict's "fixed cases deterministically grade" is
    the fixed-expectations and deterministic-grader boundary the case exists to
    exercise.
- Capability-gap:
  - `reports-test-capability-gap` — "executable parser" and "finite command exit
    and parsed output", which shares "finite command" with the test row.
  - `reports-eval-capability-gap` — "LLM-driven skill" and "structured JSON
    projection scored by fixed cases", which share "LLM-driven", "structured", and
    "scored by fixed" with the evaluate row.
- Blocked, rejected by `validate-input` before the subject is read:
  - `rejects-unsupported-tag` — "semantic constraint" and "no deterministic or
    structurally scored verdict", which share "semantic constraint" and "no
    deterministic" with the audit row.
  - `rejects-validation-tag`, `rejects-verification-type-name-as-tag`,
    `rejects-test-assertion-type-as-tag`, `rejects-unknown-tag`,
    `rejects-test-tag-without-path`, `rejects-audit-tag-with-path`, and
    `rejects-multiple-verification-tags` — each "deterministic CLI" and "finite
    command exit and parsed output", the latter byte-identical to the retired
    verdict of `reports-test-capability-gap`.

The sweep's other hits are single words that name what a subject is or emits and
share no table phrase: "command" in `routes-deterministic-behavior-to-test`, the
"model" of "language model" in `routes-structured-producer-to-evaluate`, and
"emits", "output", and "settles" in `routes-semantic-constraint-to-audit` and
`accepts-slugged-audit-tag`. The two probe cases carry none. No eval-evidence audit
has yet judged the reworded cases.

**Impact**: a producer that matches keywords instead of classifying the verdict
the subject can produce still passes each routed and capability-gap case above,
because each names the deciding word of the type it expects, so those cases supply
weak evidence for the classification and capability-gap assertions they back. A
conforming producer never classifies a blocked case's subject, so that wording
carries no routing signal but still restates the table.

**Settlement condition**: in every case enumerated above, `subject.kind` and
`subject.verdict` share no phrase of two or more words with the `classify-subject`
table and carry no deciding word of the verification type the case expects — such
as "deterministic" or "finite command" for test, "LLM", "structured", "scored by
fixed", or "model-generated" for evaluate, and "semantic" or "structural" for
audit; a routed boundary case keeps only the opposing type's wording it exists to
exercise; a blocked case carries no deciding word of any type; and an
eval-evidence audit of `evals/routing` reports no `oracle-leakage` warning.

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

## The evaluate and probe routes invoke skills the plugin does not ship, far from their catalog gate

**Evidence**: `instructions:skill-auditor` warning `f-009`, severity `WARNING`, rule
`composed_skill_reference_resolution`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` line 81 on head
`5887001573e291dc8689b1f80510d75cab374880` — a later audit than the one whose `f-009`
the read-order entry above records — verbatim: "the evaluate and probe routes (lines
81-82) instruct `Use skill`spec-tree:eval`.` and `Use skill`spec-tree:probe`.`.
Neither skill exists in the spec-tree plugin at this commit:
`src/plugins/spec-tree/skills/` holds `test` but no `eval` or `probe`. The only guard is
the catalog gate at line 70, far from these bullets. Change to: make the
catalog-listing condition visible where each of those dependency instructions
appears." The cited lines hold that text at that head.

**Impact**: each of the two bullets reads as an unconditional instruction to invoke a
skill the plugin does not ship. Only the catalog gate at line 70, which ends a route
whose specialist the runtime skill catalog does not list as `capability-required`
before any continuing route reaches these bullets, keeps the invocation off a missing
skill, so a reader who applies either bullet without carrying that gate forward
invokes a skill no catalog lists.

**Settlement condition**: the evaluate and probe bullets each state, where they
instruct the invocation, that the route reaches it only when the runtime skill catalog
lists that specialist, and an isolated skill audit of
`src/plugins/spec-tree/skills/verify/SKILL.md` raises no finding under the rule
`composed_skill_reference_resolution`.

## Evaluate and probe specialists receive the test specialist's argument form

**Evidence**: `instructions:skill-auditor` warning `f-010`, severity `WARNING`, rule
`specialist_contract_assumption`, against
`src/plugins/spec-tree/skills/verify/SKILL.md` line 85 on head
`5887001573e291dc8689b1f80510d75cab374880`, verbatim: "'Each path-bearing specialist
runs once per owning target and receives the argument form the test specialist
declares.' This applies `spec-tree:test`'s argument contract
(`<full-spx-node-or-decision-path> [selected-assertions-json-array]`) to eval and probe
specialists whose contracts the skill cannot inspect. Meanwhile line 70 requires
reading each specialist's own catalog argument contract for decision-rule mode. Change
to: state which argument contract governs a non-test specialist's invocation." The
cited lines hold that text at that head.

**Impact**: line 85 fixes one argument form for every path-bearing specialist, while
line 70 decides decision-rule mode from each specialist's own catalog argument
contract and line 74 anticipates an eval contract that names only node targets. The
skill therefore names two contracts for one invocation, and an eval or probe
specialist whose declared contract differs from the test specialist's receives an
argument form it never declared.

**Settlement condition**: the skill states which argument contract governs an eval or
probe specialist's invocation, consistent with the catalog-contract reading at line
70, and an isolated skill audit of `src/plugins/spec-tree/skills/verify/SKILL.md`
raises no finding under the rule `specialist_contract_assumption`.

## Language code skills count every audit routing row and match only the pathless tag

**Evidence**: `src/plugins/go/skills/code-go/SKILL.md:95`,
`src/plugins/typescript/skills/code-typescript/SKILL.md:241`,
`src/plugins/rust/skills/code-rust/SKILL.md:89`, and
`src/plugins/python/skills/code-python/SKILL.md` lines 49, 53, 61, and 309 count every
`/verify` row whose verification type is audit with no status filter, require each
reported `preserved`, and match only the literal `([audit])`. The Go line, which the
TypeScript and Rust lines repeat word for word, reads verbatim: "For each `/verify`
routing row whose verification type is audit, re-read the routed spec or decision
artifact and confirm the exact subject still carries `([audit])`. The completion report
includes one `Audit requirements` row per audit routing row with the full `spx/...`
source path, exact subject text, and status `preserved`. The row count must equal the
routing result's audit-row count; when that count is zero, report
`Audit requirements: none selected`." Python line 49 reads verbatim: "For every `/verify` routing row whose
verification type is audit, the authoritative requirement is the exact
assertion or decision-rule text in the routed spec or decision artifact carrying
`([audit])`." `/verify`'s `record-result` reports an audit subject `capability-required`
after restoring it from the snapshot when the closing `spx validation markdown` exits
other than 0, and its audit route writes `[audit:{rule-slug}]` into a spec that already
carries a slugged audit tag.

**Impact**: when the closing `spx validation markdown` fails, the audit rows `/verify`
reports as `capability-required` are miscounted, and slugged `[audit:{rule-slug}]` rows
are missed whatever their status.

**Settlement condition**: the four skills count only routed audit rows and match both the
slugged and the pathless audit tag forms. A follow-up Change owns that repair.
