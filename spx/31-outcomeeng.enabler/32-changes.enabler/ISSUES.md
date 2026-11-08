# Issues

## DEBT [capability]: author-change grants verification-run input and render

Defect class: `capability`.

Finding: `instructions:skill-auditor` runs `2026-10-07_08-30-45-540-0d732cbf18ec`, `2026-10-07_08-39-58-900-2429c7e936a6`, and `2026-10-07_09-44-30-979-fd4d185edb62` raised the `Bash(spx verification run status:*)` grant of `author-change` as rule `allowed-tools-narrowest-grant`, and the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) identified no invocation for the `input`, `status`, and `render` grants in the workflow.

Judgment: Change outcomeeng/changes#333 removed the `status` grant. The `input` and `render` grants stay, and the finding on them is not valid. `<audit_gate>` step 5 of `src/plugins/product-tree/skills/author-change/SKILL.md` reads: "Run `renderCommand` exactly as the result names it", and "Run `spx verification run input` with the `--verification-type`, `--scope-type`, `--scope`, and `--run` values `renderCommand` carries." The narrowest-grant rule asks for no grant beyond what a step uses, and these two grants cover exactly those steps.

Impact: none beyond the audit raising the finding again.

Revisit and settlement condition: none; the entry records the judgment so a later audit meets it.

## DEBT [composition]: author-change and release-change each compose the other

Defect class: `composition`.

Finding: `author-change`'s `<result>` composes `product-tree:release-change` when the session holds the Change and "work stops or transfers with continuation remaining", and `release-change` step 2 composes `product-tree:author-change` for the body revision while the session still holds the Change. `instructions:skill-auditor` run `2026-10-07_09-58-47-435-8a2d1e9aadb0` at head `84f119bf70464dc83a71927ce8c0d18e73bc39dc` raised it as a `blocking` finding, rule `unambiguous-instruction`: the release condition is not decidable from the skill's own state, and a revision inside a release can end by invoking a nested release. Base `0ec15959925f92f0b14891fe2cebd729651bf470` already carried both compositions and the condition; the changeset adds only the `submit` sentence, which is decidable from the persisted Maturity.

Evidence: the sealed run above and the base text of both skills.

Impact: every audit of `author-change` can raise the finding again, so its gate cannot close on this surface alone.

Successor: the Proposed Change outcomeeng/changes#397 carries this defect.

Revisit and settlement condition: one of the two compositions is removed or made decidable from the composing skill's own inputs, and one typed skill audit of `author-change` and of `release-change` raises neither the nested-release finding nor a caller-dependence finding.

## DEBT [adr-pdr-compliance]: the audit-change runner is a generic shipped script beyond fifty lines

Defect class: `adr-pdr-compliance`.

Finding: `src/plugins/product-tree/skills/audit-change/scripts/audit_change_run.py` is a generic shipped script far beyond fifty lines, which [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) holds as debt awaiting extraction of its logic into the SPX CLI once the script proves its value, or removal when it does not.

The `change-auditor` definition `src/plugins/product-tree/agents/change-auditor.md` has no retained release-acceptance evidence: [`spx/15-subagent-execution.pdr.md`](spx/15-subagent-execution.pdr.md) declares release acceptance per supported harness as native loading plus one minimal isolated execution for each of its Standard, Strong, and Fast profiles. Release acceptance belongs to the release, so the changeset that introduces the definition, Change outcomeeng/changes#162, runs no paid invocation.

Evidence: `product-tree:implementation-auditor` run `2026-09-29_08-34-14-821-c605096fd926` raised a `debt` finding under rule `adr-pdr-compliance` against the runner; `wc -l` over the runner derives its current length, so this entry carries no line count. `instructions:subagent-auditor` finding `f-002`, verdict `REJECT`, class `evidence/missing-invocation-evidence`, judged `src/plugins/product-tree/agents/change-auditor.md` on head `02c847e66b2f526804db14eb568fae2a2180b858`. `instructions:subagent-auditor` run `2026-10-28_13-59-20-850-8d402c75be27` on head `dd8730c491e0991759bd92b306c19ed992e9e4dd` returned the same gap `filed` under rule `release_acceptance_evidence`, base-ref evidence `c586b167fcb9c91a0a908c0971b9b449fc0b2aa7..dd8730c491e0991759bd92b306c19ed992e9e4dd`, with this entry as its `issuesEntry`; the lines the run judged lie outside the changeset's edit.

Impact: the runner's state, branching, and result contracts ship inside a plugin that a consumer repository cannot version independently or repair without a marketplace release. No execution claim stands for the `change-auditor` definition on any harness or profile until release acceptance retains its evidence.

Revisit and settlement condition: once the runner proves its value in use, its logic moves into the SPX CLI, tested there and consumed by the plugins product as a trusted third-party component, leaving `audit-change` its instruction and no script; a runner that does not prove its value is removed rather than extracted. The definition's gap settles when release acceptance retains, for every supported harness, native loading and one minimal isolated execution of each Standard, Strong, and Fast profile, judged by an independent Auditor with no retry or substitution after a failed or unusable launch.

## DEBT [evidence]: the runner's unreadable-output blocks reach no linked test

Defect class: `evidence`.

Finding: `reconcile` and the finding readers of `audit_change_run.py` block with `unreadable-output` when the rendered projection carries no `auditScopeUnits` array of objects or a finding without an integer `seq` and a payload object. `tests/test_audit_change_run.compliance.l1.py` drives the runner against the real SPX store, which never renders such a projection, so removing either block leaves every linked test passing. The same holds for the other blocked-result branches the real store never reaches: the runner's command wrapper on an `OSError`, a `ValueError`, or undecodable output, the line reader on unparseable or empty command output, the findings reader on a findings group that is not an array, the `retained-input-mismatch` block of `start`, the `OSError` branch of the stdin read in `main`, and the serializer's `RecursionError` fallback. The test-evidence audit of the changes node on head `c9124f951d82668d846e303686b236a52f72a309` raised this as a `WARNING` coverage finding against `src/plugins/product-tree/skills/audit-change/scripts/audit_change_run.py`. The node declares `malleability: verification`, which requires a tagged result for every assertion and no case for each blocked branch, so the finding is recorded here and no case is added.

Impact: the runner's refusal of a malformed projection is unobserved, so a regression there reads a run with no coverage as an empty one.

Revisit and settlement condition: the runner's SPX boundary admits a controlled implementation of its command runner that renders a malformed projection, and a linked case asserts the `unreadable-output` block for each malformed shape.

## DEBT [skill-audit]: close-change names no current-state source for the merge commit

Defect class: `skill-audit`.

Finding: `instructions:skill-auditor` run `2026-10-07_09-02-30-051-33c271dd97cd` at head `917d6106fd969e4baf593ab7b568f0740869537f` raised rule `ambiguous-instruction`, severity `blocking`, against step 3's `Integrated` check in `src/plugins/product-tree/skills/close-change/SKILL.md`: the check reads "the merge commit the record or conversation names", and no loaded rule names a record field that holds it, no grant reads a pull request's merge commit, and no current-state test separates a Change with no changeset from one whose merge commit nobody named. Change outcomeeng/changes#333 repaired the second finding of that run, the undefined noun Frame, in the same step.

Evidence: the sealed run above.

Impact: an `Applied` close can pass its integration check on a merge commit that only the conversation names.

Successor: the Change outcomeeng/changes#392 carries this defect.

Revisit and settlement condition: step 3 names the current-state source of the merge commit with the grant that reads it and the current-state test that establishes a Change has no changeset, and one typed skill audit of `close-change` raises no finding on it.

## DEBT [caller-independence]: the instructions auditors record a run-driver identity the rule reads as dependence on the caller

Defect class: `caller-independence`.

Finding: `/skill-standards` caller independence reads the required `runDriver` input of `instructions:audit-skill` as dependence on the caller: `instructions:skill-auditor` finding f-012 (rule `caller_independence`), severity `REJECT`, against `src/plugins/instructions/skills/audit-skill/SKILL.md:35` at head `add3e3e862f7512a55e8b9655d07f78412abe87c`. The same finding stands against `src/plugins/instructions/skills/audit-subagent/SKILL.md:34` (f-008) and against the `runDriver` input of `/author-skill`'s auditor template, `src/plugins/instructions/skills/author-skill/templates/auditor-skill.md` (f-012), at head `8e631614b562ec5edf05c0e4c80a38625ada90d7`. The Change that made the two instructions auditors record through `spx verification run` settled that input as required, the shape `audit-change` uses, and the typed skill audit of `audit-change` on head `7682aa69f9042b1221456caf7274ca937c083232` raised no `caller_independence` finding. A run-driver identity recorded as provenance, with no branching on it, is input data rather than dependence on the caller, and `/skill-standards` states no such distinction.

Impact: each later audit of those skills raises the finding again, though their behavior meets the rule and no edit to them satisfies it.

Revisit and settlement condition: `/skill-standards` states that a run-driver identity recorded as provenance, with no branching on it, is input data; one typed skill audit of each of `audit-skill`, `audit-subagent`, and `author-skill` then raises no `caller_independence` finding.

## DEBT [tooling-limit]: the GitHub GraphQL budget belongs to the account, and the REST rate-limit endpoint misreports it

Defect class: `tooling-limit`.

Finding: GitHub's GraphQL budget is one per account, shared by every session that authenticates as that account. One unbounded paginated GraphQL query spends the budget for all of them, after which every session stops at its next GitHub call, Executors and attestations included. The REST rate-limit endpoint does not show the stop: while GraphQL refused calls, the endpoint still reported thousands of GraphQL points remaining.

Evidence: the Observation of outcomeeng/changes#168 records a query whose cursor variable `gh` did not recognise, which refetched its first page 575 times in the background and spent the account's GraphQL budget. `gh api graphql --paginate` fills the cursor from a variable named `$endCursor`; any other name leaves the cursor unset, so each page request repeats the first. The Change store's reads, among them the `Predecessors` read of `src/plugins/product-tree/skills/change-standards/references/lifecycle.md`, are the heaviest users of that budget in this product.

Impact: a session cannot learn from the REST endpoint whether its next GraphQL call will succeed, so a refusal arrives with no earlier signal, and the refusal reaches every session on the account at once. The page bound written in each skill's text keeps any one call from spending the budget; it does not give a session a way to read what remains.

Revisit and settlement condition: GitHub reports the GraphQL budget consistently across its REST and GraphQL interfaces, or a read that establishes GraphQL availability without spending the budget is documented and the Change skills cite it in their blocked results.

## DEBT [voice]: change-standards lifecycle inert-stdin names the agent as a subject

Defect class: `voice`.

Finding: the `inert-stdin` rule in `src/plugins/product-tree/skills/change-standards/references/lifecycle.md` (line 67) uses "the agent" as the subject of "the agent never removes the file". Prompt text in skill content states an instruction in imperative voice or names Claude, and never uses "the agent" as a subject.

Evidence: `instructions:skill-auditor` run `2026-10-17_18-16-04-154-bd168bad0aee`, terminal status approved, returned a `filed` finding under rule `banned_subject` for unit `instructions:skill:file:src/plugins/product-tree/skills/change-standards/references/lifecycle.md`, base-ref evidence `ffb6bdca9cfea5d4657fd86c184487179df6432e..a101e169becf514e2c8a76cb4f82fe1aa4a7135a`. Observed: line 67 reads "...and the agent never removes the file." Expected: "NEVER remove the file", or a sentence naming Claude. The line lies outside the changeset.

Impact: a later audit of `change-standards` can raise the finding again.

Revisit and settlement condition: `inert-stdin` in `lifecycle.md` states the instruction in imperative voice or names Claude as its subject, and one typed skill audit of `change-standards` raises no `banned_subject` finding on it.

## DEBT [source-ownership]: the audit-change harnesses read their expected bounds from spec prose `outcomeeng_testing/harnesses/audit_change_authority.py` `read-authority` `source-ownership`

Defect class: `source-ownership`.

Finding: `spec_page_bound()` in `outcomeeng_testing/harnesses/audit_change_authority.py` reads the page size and page count of `read-authority` from the text of the `audit-change.md` assertion by regular expression, and `spec_issue_page_bound()` and `spec_field_value_bound()` in `outcomeeng_testing/harnesses/audit_change_relations.py` read the `read-relations` bounds the same way. The spec-declared value and the runner that complies with it agree as audit evidence, and a rewording of an assertion breaks the harness while no behavior changes.

Evidence: `product-tree:test-evidence-auditor` on `spx/31-outcomeeng.enabler/32-changes.enabler/61-audit-change.enabler` at head `6e585cb782cd868ed3e4e1cafe5ef80ca11b0414`, finding `f-004`, severity `WARNING`, property `source-ownership`, rule `source-ownership`. The harness text lies outside the changeset's edit, which changes only the spec path in the authority harness and removes the absorbers fixture from the relations harness. The Maintainer ruled the finding filed.

Impact: a rewording of the `read-authority`, `read-relations-pages`, or `read-relations-fields` assertion fails three linked tests with no change in the runner's behavior.

Revisit and settlement condition: the runner exports the bounds it enforces as source-owned constants, the harnesses import them, the agreement between the assertion text and those constants is audit evidence, and one test-evidence audit of the Node raises no `source-ownership` finding on the harnesses.
