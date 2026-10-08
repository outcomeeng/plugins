# Issues

## DEBT [capability]: author-change grants verification-run input and render

Defect class: `capability`.

Finding: `instructions:skill-auditor` runs `2026-10-07_08-30-45-540-0d732cbf18ec`, `2026-10-07_08-39-58-900-2429c7e936a6`, and `2026-10-07_09-44-30-979-fd4d185edb62` raised the `Bash(spx verification run status:*)` grant of `author-change` as rule `allowed-tools-narrowest-grant`, and the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) identified no invocation for the `input`, `status`, and `render` grants in the workflow.

Judgment: Change outcomeeng/changes#333 removed the `status` grant. The `input` and `render` grants stay, and the finding on them is not valid. `<audit_gate>` step 5 of `src/plugins/spec-tree/skills/author-change/SKILL.md` reads: "Run `renderCommand` exactly as the result names it", and "Run `spx verification run input` with the `--verification-type`, `--scope-type`, `--scope`, and `--run` values `renderCommand` carries." The narrowest-grant rule asks for no grant beyond what a step uses, and these two grants cover exactly those steps.

Impact: none beyond the audit raising the finding again.

Revisit and settlement condition: none; the entry records the judgment so a later audit meets it.

## DEBT [composition]: author-change and release-change each compose the other

Defect class: `composition`.

Finding: `author-change`'s `<result>` composes `spec-tree:release-change` when the session holds the Change and "work stops or transfers with continuation remaining", and `release-change` step 2 composes `spec-tree:author-change` for the body revision while the session still holds the Change. `instructions:skill-auditor` run `2026-10-07_09-58-47-435-8a2d1e9aadb0` at head `84f119bf70464dc83a71927ce8c0d18e73bc39dc` raised it as a `blocking` finding, rule `unambiguous-instruction`: the release condition is not decidable from the skill's own state, and a revision inside a release can end by invoking a nested release. Base `0ec15959925f92f0b14891fe2cebd729651bf470` already carried both compositions and the condition; the changeset adds only the `submit` sentence, which is decidable from the persisted Maturity.

Evidence: the sealed run above and the base text of both skills.

Impact: every audit of `author-change` can raise the finding again, so its gate cannot close on this surface alone.

Successor: the Proposed Change outcomeeng/changes#397 carries this defect.

Revisit and settlement condition: one of the two compositions is removed or made decidable from the composing skill's own inputs, and one typed skill audit of `author-change` and of `release-change` raises neither the nested-release finding nor a caller-dependence finding.

## DEBT [adr-pdr-compliance]: the audit-change runner is a generic shipped script beyond fifty lines

Defect class: `adr-pdr-compliance`.

Finding: `src/plugins/spec-tree/skills/audit-change/scripts/audit_change_run.py` is a generic shipped script far beyond fifty lines, which [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) holds as debt awaiting extraction of its logic into the SPX CLI once the script proves its value, or removal when it does not.

The `change-auditor` definition `src/plugins/spec-tree/agents/change-auditor.md` has no retained release-acceptance evidence: [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) declares release acceptance per supported harness as native loading plus one minimal isolated execution for each of its Standard, Strong, and Fast profiles. Release acceptance belongs to the release, so the changeset that introduces the definition, Change outcomeeng/changes#162, runs no paid invocation.

Evidence: `spec-tree:implementation-auditor` run `2026-09-29_08-34-14-821-c605096fd926` raised a `debt` finding under rule `adr-pdr-compliance` against the runner; `wc -l` over the runner derives its current length, so this entry carries no line count. `instructions:subagent-auditor` finding `f-002`, verdict `REJECT`, class `evidence/missing-invocation-evidence`, judged `src/plugins/spec-tree/agents/change-auditor.md` on head `02c847e66b2f526804db14eb568fae2a2180b858`.

Impact: the runner's state, branching, and result contracts ship inside a plugin that a consumer repository cannot version independently or repair without a marketplace release. No execution claim stands for the `change-auditor` definition on any harness or profile until release acceptance retains its evidence.

Revisit and settlement condition: once the runner proves its value in use, its logic moves into the SPX CLI, tested there and consumed by the plugins product as a trusted third-party component, leaving `audit-change` its instruction and no script; a runner that does not prove its value is removed rather than extracted. The definition's gap settles when release acceptance retains, for every supported harness, native loading and one minimal isolated execution of each Standard, Strong, and Fast profile, judged by an independent Auditor with no retry or substitution after a failed or unusable launch.

## DEBT [evidence]: the runner's unreadable-output blocks reach no linked test

Defect class: `evidence`.

Finding: `reconcile` and the finding readers of `audit_change_run.py` block with `unreadable-output` when the rendered projection carries no `auditScopeUnits` array of objects or a finding without an integer `seq` and a payload object. `tests/test_audit_change_run.compliance.l1.py` drives the runner against the real SPX store, which never renders such a projection, so removing either block leaves every linked test passing. The same holds for the other blocked-result branches the real store never reaches: the runner's command wrapper on an `OSError`, a `ValueError`, or undecodable output, the line reader on unparseable or empty command output, the findings reader on a findings group that is not an array, the `retained-input-mismatch` block of `start`, the `OSError` branch of the stdin read in `main`, and the serializer's `RecursionError` fallback. The test-evidence audit of the changes node on head `c9124f951d82668d846e303686b236a52f72a309` raised this as a `WARNING` coverage finding against `src/plugins/spec-tree/skills/audit-change/scripts/audit_change_run.py`.

Impact: the runner's refusal of a malformed projection is unobserved, so a regression there reads a run with no coverage as an empty one.

Revisit and settlement condition: the runner's SPX boundary admits a controlled implementation of its command runner that renders a malformed projection, and a linked case asserts the `unreadable-output` block for each malformed shape.

## DEBT [skill-contract]: audit-change's grants deviate from the audit baseline, its reason table stays inline and its verdict returns the reduced finish result

Defect class: `skill-contract`.

Judgment: Change outcomeeng/changes#333 settled two findings on `audit-change`: the BLOCKED result states its three shapes as labeled shapes, and the piping prohibition reads "never piped into another command" in the skill and in `changes.md`. One deviation is a separate larger concern whose fix belongs in the audit-grant rule of `/skill-standards` in the instructions plugin, which Change outcomeeng/changes#344 edits: `/skill-standards` requires an audit skill to add `allowed-tools: Read, Grep, Glob`, while `audit-change` grants the runner invocation and the skill-composition tool and no Read, Grep, or Glob, because the runner's journal appends make its grant a write grant; its constraints state the deviation. Two findings are not valid against their governing text and stay recorded as judged:

- Rules `progressive-disclosure-conditional-detail` and `conciseness`, against the reason table of `<runner_contract>`: moving the table to a bundled reference needs a Read grant, which the skill declines in its constraints ("grants no Read, Grep, or Glob: the runner is the audit's only read path"), and the table is the complete inventory a blocked result is matched against.
- Rules `auditor-verdict-format` and `auditor-skeleton-verdict-format`, against `<verdict_format>`: the completed verdict returns the unchanged `finish` result, which omits the projection's `events` and `auditScopeUnits`. `changes.md` states that result as the contract: "whose result carries the run token, the rendered projection's run-level fields, every finding payload verbatim, and the one command that reproduces the complete rendered projection from the sealed run".

Evidence: `instructions:skill-auditor` runs `2026-10-07_09-05-51-393-d08dac7359db` and `2026-10-07_09-31-07-355-24f22aa9dd57`, and the earlier runs on heads `007c3871de7b82f7592325be191d26fbfa8aee8d` and `95da1302cb72c523328f0d7d02b3a05b23df603b`.

Impact: each later audit of the skill can raise the grant deviation and the two judged findings again.

Revisit and settlement condition: the audit standards state that an audit skill whose only read path is a bundled runner that appends to the SPX verification-run journal grants that runner and the skill-composition tool and no Read, Grep, or Glob, may hold its reason inventory inline, and may return a reduced result the owning spec declares; one typed skill audit of `audit-change` then raises none of the three findings.

## DEBT [subagent-contract]: change-auditor restates the skill's result contract and carries a description-match description

Defect class: `subagent-contract`.

Finding: two warnings stand against the `change-auditor` definition. Its `<output_format>` restates the skill's result contract field by field, and its list of fields for a failed command omits `liveSha256`, `sha256`, and `retainedSha256`, which the skill's `<verdict_format>` carries for `candidate-changed` and `retained-input-mismatch`. Its description is directive description-match wording, although the owning skills dispatch the role by exact configured name.

Evidence: `instructions:subagent-auditor` findings f-003 (rule `description-style/exact-name-invocation`) and f-004 (rule `configuration/thin-wrapper-contract-copy`), each severity `WARNING`, against `src/plugins/spec-tree/agents/change-auditor.md` lines 3 and 91, in the typed subagent audit on head `95da1302cb72c523328f0d7d02b3a05b23df603b`, which rejected on the standing findings f-001 and f-002 recorded in the native-artifact node and in the `adr-pdr-compliance` entry above. The directive description is the wording every spec-tree agent definition carries.

Impact: the wrapper's copied field list drifts each time the runner contract changes, and a relaying session can take the narrower list as the expected shape; the description invites a launch the calling skills have not instructed.

Revisit and settlement condition: the wrapper points at the skill's `<verdict_format>` for the completed, `OUTSIDE_CONTRACT`, and runner-blocked shapes and keeps only its own pre-run diagnostic shape, and the description states its subject and the conditions under which the owning skills invoke the role in passive wording; one typed subagent audit of `change-auditor` then raises neither warning.

## DEBT [skill-audit]: close-change names no current-state source for the merge commit

Defect class: `skill-audit`.

Finding: `instructions:skill-auditor` run `2026-10-07_09-02-30-051-33c271dd97cd` at head `917d6106fd969e4baf593ab7b568f0740869537f` raised rule `ambiguous-instruction`, severity `blocking`, against step 3's `Integrated` check in `src/plugins/spec-tree/skills/close-change/SKILL.md`: the check reads "the merge commit the record or conversation names", and no loaded rule names a record field that holds it, no grant reads a pull request's merge commit, and no current-state test separates a Change with no changeset from one whose merge commit nobody named. Change outcomeeng/changes#333 repaired the second finding of that run, the undefined noun Frame, in the same step.

Evidence: the sealed run above.

Impact: an `Applied` close can pass its integration check on a merge commit that only the conversation names.

Successor: the Change outcomeeng/changes#392 carries this defect.

Revisit and settlement condition: step 3 names the current-state source of the merge commit with the grant that reads it and the current-state test that establishes a Change has no changeset, and one typed skill audit of `close-change` raises no finding on it.

## DEBT [caller-independence]: the instructions auditors record a run-driver identity the rule reads as dependence on the caller

Defect class: `caller-independence`.

Finding: `/skill-standards` caller independence reads the required `runDriver` input of `instructions:audit-skill` as dependence on the caller: `instructions:skill-auditor` finding f-012 (rule `caller_independence`), severity `REJECT`, against `src/plugins/instructions/skills/audit-skill/SKILL.md:35` at head `add3e3e862f7512a55e8b9655d07f78412abe87c`. The same finding stands against `src/plugins/instructions/skills/audit-subagent/SKILL.md:34` (f-008) and against the `runDriver` input of `/create-skill`'s auditor template, `src/plugins/instructions/skills/create-skill/templates/auditor-skill.md` (f-012), at head `8e631614b562ec5edf05c0e4c80a38625ada90d7`. The Change that made the two instructions auditors record through `spx verification run` settled that input as required, the shape `audit-change` uses, and the typed skill audit of `audit-change` on head `7682aa69f9042b1221456caf7274ca937c083232` raised no `caller_independence` finding. A run-driver identity recorded as provenance, with no branching on it, is input data rather than dependence on the caller, and `/skill-standards` states no such distinction.

Impact: each later audit of those skills raises the finding again, though their behavior meets the rule and no edit to them satisfies it.

Revisit and settlement condition: `/skill-standards` states that a run-driver identity recorded as provenance, with no branching on it, is input data; one typed skill audit of each of `audit-skill`, `audit-subagent`, and `create-skill` then raises no `caller_independence` finding.

## DEBT [bound]: orchestrate-change reads nested connections at first:50 with no blocked result

Defect class: `bound`.

Finding: product property 3 of [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) covers a `gh api graphql` call reading a connection and requires a named page bound and a blocked result when the result fills it. `src/plugins/coding-agents/skills/orchestrate-change/SKILL.md` line 52 reads `issueFieldValues(first:50)` with no blocked result when the connection returns 50 nodes. Change outcomeeng/changes#333 added that blocked result to the `canonical-state` rule of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md`, which carried the other nested reads; the Change edits no file of `orchestrate-change`.

Evidence: `spec-tree:changes-reviewer` run `2026-10-06_19-01-19-956-109edd5dce9a` on head `7ab8c651a26303d97d3b99534f17a215c2bf2a66`, finding `consistency` against `lifecycle.md:23`; the `orchestrate-change` read names its bound and returns no blocked result at 50 nodes.

Impact: an issue that carries 50 or more field values drops a value from the `orchestrate-change` read with no blocked result.

Revisit and settlement condition: `orchestrate-change` states that a connection returning 50 nodes is a blocked read naming `50 field values`, and one typed skill audit of `orchestrate-change` follows the edit.

## DEBT [tooling-limit]: the GitHub GraphQL budget belongs to the account, and the REST rate-limit endpoint misreports it

Defect class: `tooling-limit`.

Finding: GitHub's GraphQL budget is one per account, shared by every session that authenticates as that account. One unbounded paginated GraphQL query spends the budget for all of them, after which every session stops at its next GitHub call, Executors and attestations included. The REST rate-limit endpoint does not show the stop: while GraphQL refused calls, the endpoint still reported thousands of GraphQL points remaining.

Evidence: the Observation of outcomeeng/changes#168 records a query whose cursor variable `gh` did not recognise, which refetched its first page 575 times in the background and spent the account's GraphQL budget. `gh api graphql --paginate` fills the cursor from a variable named `$endCursor`; any other name leaves the cursor unset, so each page request repeats the first. The Change store's reads, among them the `Predecessors` read of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md`, are the heaviest users of that budget in this product.

Impact: a session cannot learn from the REST endpoint whether its next GraphQL call will succeed, so a refusal arrives with no earlier signal, and the refusal reaches every session on the account at once. The page bound written in each skill's text keeps any one call from spending the budget; it does not give a session a way to read what remains.

Revisit and settlement condition: GitHub reports the GraphQL budget consistently across its REST and GraphQL interfaces, or a read that establishes GraphQL availability without spending the budget is documented and the Change skills cite it in their blocked results.
