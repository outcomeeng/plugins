# Issues

## DEBT [capability]: unused author-change verification grants

Defect class: `capability`.

Finding: `author-change` grants `Bash(spx verification run input:*)`, `Bash(spx verification run status:*)`, and `Bash(spx verification run render:*)`, although its delegating workflow does not use them.

Evidence: `src/plugins/spec-tree/skills/author-change/SKILL.md:8` declares all three grants, and the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) identified no corresponding invocation in the workflow.

Impact: the skill carries excess capability beyond the authority required by its delegating workflow.

Successor: the Proposed Change filed after Change #89 merges for the agent-run-journal sequence collision, carrying this defect as its second item.

Revisit and settlement condition: remove all three unused verification-run grants and pass one typed skill audit over the revised `author-change` surface.

## DEBT [specificity]: author-change and change-standards leave checks unnamed

Defect class: `specificity`.

Finding: the typed skill audit of `author-change` on the Change Lifecycle changeset (head `a28a5be91fc2ea04151c283059caa9cb9a11fd12`) found the audit gate not naming which granted `spx verification run` command establishes `terminalStatus`, the rendered projection, and retained-input equality; the structured-question tool unnamed and ungranted where the body asks the operator; and two success criteria ("carries the required authority", "Continuation depends only on…") without a named check.

Evidence: `instructions:skill-auditor` findings f-010, f-012, f-013, f-014 on `src/plugins/spec-tree/skills/author-change/SKILL.md`. The second skill-audit pass on the three Lifecycle skills added: `release-change` step 3 carries six stop-capable operations in one paragraph (f-009), a candidate for numbered sub-steps. The relaunch of the `change-standards` audit added: `SKILL.md` calls the references "rules and no procedure" while `lifecycle.md` carries command forms (f-008), and its first success criterion is not observable at load (f-010). The typed skill audit of `change-standards` on the Proposed-readiness changeset (head `98e924f4f88200425e649c3034f6fb0336f2bcf8`) raised the same "no procedure" claim again: `SKILL.md:30` states that the shared references own the rules and no procedure while `lifecycle.md` carries command-bearing rules, and the same sentence's inventory of `lifecycle.md` omits its `canonical-state` rule (f-009, `WARNING`). The typed skill audit of `author-change` at that head again found no step naming the `spx verification run` command that establishes the audit-gate checks (f-009, `WARNING`).

Impact: the gate's checks rest on judgment where a named command or workflow would make them falsifiable, and a reader of the `change-standards` loading contract receives an inaccurate account of what `lifecycle.md` contains.

Successor: the Proposed Change filed after Change #89 merges for the `author-change` grants (entry above), carrying these as further items.

Revisit and settlement condition: each check named against its granted command, the structured-question tool named and granted, the `change-standards` loading contract describing its references' content accurately with every `lifecycle.md` rule in its inventory, and one typed skill audit of each skill approving with no `specificity` finding.

## DEBT [single-location]: Change skills state one requirement in more than one place

Defect class: `single-location`.

Finding: the first success criterion of `change-standards` states that each record requirement has one canonical statement in the shared reference, while the Definition of Ready tables restate requirements the shared `change-record.md` rules already state: `proposed-input-boundary` restates `received-input-boundary`, and `framed-authority` restates the Intent attestation text the `frame` rule carries. `author-change` `<persistence>` restates the field-home table and the blocker read command that `canonical-state` in `lifecycle.md` owns, and its `<essential_principles>` restates the `change-auditor` dispatch rule that `<audit_gate>` governs.

Evidence: `instructions:skill-auditor` finding f-011, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/SKILL.md:36`, in the typed skill audit of `change-standards` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`. The typed skill audit of `change-standards` on head `b0ace02701a73ce0cb4c34b5f1df924217779889` added finding f-008 (rule `single-canonical-statement`), severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/SKILL.md:36`: the target-malleability definition stands in the `frame` rule of `change-record.md` and again in the `framed-nodes`, `sliced-frame`, and `executable-frame` criteria. The typed skill audit of `author-change` on that head added finding f-008 (rule `single-location-duplication`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:94`: `<persistence>` restates the field-home table and the blocker read command that `canonical-state` in `lifecycle.md` owns. The typed skill audit of `change-standards` on head `303923264a553bd518a68e93f5c228fd30565196` raised the target-malleability restatement again as f-009, and the audit on head `3e9758d4d25e8ac5ae90d29c9592430ce02d417a` added that the literal Intent attestation line stands in both `change-record.md` and `dor-framed.md`, and the typed skill audit of `author-change` on that head added f-009 (rule `conciseness_duplication`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:23`: `<essential_principles>` restates the `change-auditor` dispatch rule that `<audit_gate>` governs.

Impact: the `change-standards` success criterion cannot be met as written, so an auditor judging the skill against it either raises the restatement again or accepts a criterion the bundle does not hold. A restated requirement can drift from its other statement without any check reporting the split.

Revisit and settlement condition: either each Definition of Ready criterion that restates a shared rule cites that rule by its identifier instead of restating its text, or the success criterion states the relation the bundle actually holds between shared rules and Maturity criteria; one typed skill audit of each of `change-standards` and `author-change` then raises no finding against those statements.

## DEBT [precondition]: the Change skills assume a GitHub store without stating the precondition or a blocked result for another store

Defect class: `precondition`.

Finding: `change-standards` `lifecycle.md` rules `canonical-state` and `inert-stdin` read and write the Change store through `gh` against GitHub Issues and a GitHub Project without stating that store kind as a precondition or naming the result for a store of another kind; `author-change` persistence uses `gh` for the GitHub store the coordination overlay declares and names no result when that overlay is absent or declares a store of another kind.

Evidence: `instructions:skill-auditor` finding f-012, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md:11`, and finding f-008, severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:92`, in the typed skill audits of `change-standards` and `author-change` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`.

Impact: a consumer repository whose coordination overlay is absent or declares a non-GitHub store reaches `gh` commands the store cannot answer, with no stated blocked result, so the failure surfaces as an opaque command error instead of a named precondition.

Revisit and settlement condition: each of the two skills states the store kind its commands require and names the blocked result for a store of another kind, `author-change` also naming it for an absent overlay as `lifecycle.md` `store-binding` already does; one typed skill audit of each skill then raises no `precondition` finding.

## DEBT [caller-independence]: the instructions auditors record a run-driver identity the rule reads as dependence on the caller

Defect class: `caller-independence`.

Finding: `/skill-standards` caller independence reads the required `runDriver` input of `instructions:audit-skill` as dependence on the caller: `instructions:skill-auditor` finding f-012 (rule `caller_independence`), severity `REJECT`, against `src/plugins/instructions/skills/audit-skill/SKILL.md:35` at head `add3e3e862f7512a55e8b9655d07f78412abe87c`. The same finding stands against `src/plugins/instructions/skills/audit-subagent/SKILL.md:34` (f-008) and against the `runDriver` input of `/create-skill`'s auditor template, `src/plugins/instructions/skills/create-skill/templates/auditor-skill.md` (f-012), at head `8e631614b562ec5edf05c0e4c80a38625ada90d7`. The Change that made the two instructions auditors record through `spx verification run` settled that input as required, the shape `audit-change` uses, and the typed skill audit of `audit-change` on head `7682aa69f9042b1221456caf7274ca937c083232` raised no `caller_independence` finding. A run-driver identity recorded as provenance, with no branching on it, is input data rather than dependence on the caller, and `/skill-standards` states no such distinction.

Impact: each later audit of those skills raises the finding again, though their behavior meets the rule and no edit to them satisfies it.

Revisit and settlement condition: `/skill-standards` states that a run-driver identity recorded as provenance, with no branching on it, is input data; one typed skill audit of each of `audit-skill`, `audit-subagent`, and `create-skill` then raises no `caller_independence` finding.

## DEBT [granularity]: the Executable evidence criterion bundles three obligations

Defect class: `granularity`.

Finding: `executable-state-evidence` carries three independently judgeable obligations under one identifier: the selected `VERIFICATION_READINESS` predicates, the per-node results with their producers, and the decision-record audits.

Evidence: `instructions:skill-auditor` finding f-009 (rule `ambiguous-criterion`), severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/references/dor-executable.md:14`, in the typed skill audit of `change-standards` on head `b0ace02701a73ce0cb4c34b5f1df924217779889`, which approved with no must-fix finding. The audits on heads `303923264a553bd518a68e93f5c228fd30565196` and `9e5aa8f2f0aa09d8e161620b8c6733165d1ef1b8` raised the same shape as f-012 and f-010 (rule `conciseness-readability`) against `src/plugins/spec-tree/skills/change-standards/references/dor-executable.md:14`.

Impact: a finding against the criterion cannot name which of its three obligations failed.

Revisit and settlement condition: each of the three obligations is judgeable under its own criterion or clause; one typed skill audit of `change-standards` then raises no finding against the bundling.

## DEBT [provenance]: audit-change records the spec-tree version for any supplied agent-owning plugin

Defect class: `provenance`.

Finding: `audit-change` accepts any well-formed `runDriver` identity, yet it always records the `spec-tree` plugin version as the agent-owning plugin version, including when the supplied `agentOwningPluginName` names another plugin. Its step 1 also says to read the live file once, while step 3 reads the retained input and step 7 re-reads the live file.

Evidence: `instructions:skill-auditor` findings f-009 (rule `internal_consistency_provenance`) against `src/plugins/spec-tree/skills/audit-change/SKILL.md:58` and f-011 (rule `instruction_clarity`) against `src/plugins/spec-tree/skills/audit-change/SKILL.md:71`, both severity `WARNING`, in the typed skill audit of `audit-change` on head `b0ace02701a73ce0cb4c34b5f1df924217779889`, which approved with no must-fix finding.

Impact: a run's provenance can pair a foreign plugin name with the `spec-tree` version, and the "once" wording can lead Claude to skip the step-7 live re-read that detects a changed candidate.

Revisit and settlement condition: the request contract names the version source for a supplied agent-owning plugin other than `spec-tree`, and step 1 scopes its single read to the preflight; one typed skill audit of `audit-change` then raises neither finding.

## DEBT [constraint-language]: author-change states one hardened prohibition without NEVER

Defect class: `constraint-language`.

Finding: `<local_draft>` in `author-change` states "Do not delete a draft automatically after publication." while the neighboring hardened rules use NEVER.

Evidence: `instructions:skill-auditor` finding f-010 (rule `constraint_language`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:32`, in the typed skill audit of `author-change` on head `303923264a553bd518a68e93f5c228fd30565196`, which approved with no must-fix finding.

Impact: the prohibition reads weaker than the rules around it, so constraint strength varies inside one section.

Revisit and settlement condition: the prohibition is stated with NEVER; one typed skill audit of `author-change` then raises no `constraint_language` finding.

## DEBT [consistency]: change-standards states three contracts that disagree with the rules beside them

Defect class: `consistency`.

Finding: the `frame` rule in `change-record.md` says `# Frame` carries only facts established at the declared Maturity, while `proposed-questions` requires consequential unresolved questions to stay explicit in `# Frame`. The `store-independence` rule defers each field's store home to "the persisting skill", while `canonical-state` in `lifecycle.md` assigns those homes itself. The objective of `change-standards` reads as if selecting `Lifecycle` loads the Lifecycle rules in place of the record contract, while the loading contract always reads `change-record.md`.

Evidence: `instructions:skill-auditor` findings f-008 (rule `internal-consistency`) against `src/plugins/spec-tree/skills/change-standards/references/change-record.md:74`, f-010 (rule `caller-independence`) against `src/plugins/spec-tree/skills/change-standards/references/change-record.md:100`, and f-011 (rule `objective-shape`) against `src/plugins/spec-tree/skills/change-standards/SKILL.md:13`, each severity `WARNING`, in the typed skill audit of `change-standards` on head `3e9758d4d25e8ac5ae90d29c9592430ce02d417a`, which approved with no must-fix finding.

Impact: a Proposed record that keeps its open questions in `# Frame` as its Definition of Ready requires breaks the shared `frame` rule, the standard depends on an unnamed caller for field homes its own Lifecycle reference declares, and a reader of the objective can take the Lifecycle load to exclude the record contract.

Revisit and settlement condition: the `frame` rule admits the open questions the Proposed Definition of Ready requires, `store-independence` names the Lifecycle rules as the source of field homes, and the objective states that the record contract accompanies every selection; one typed skill audit of `change-standards` then raises none of the three findings.

## DEBT [cumulative-completeness]: later Definitions of Ready drop Framed qualifiers and leave the malleability order unstated

Defect class: `cumulative-completeness`.

Finding: `sliced-frame` and `executable-frame` ask only for each "Assertion operation" and "governing or intended Decision", while `framed-assertions` requires each operation by owning Node and exact target and `framed-decisions` requires the Frame to retain each settled choice; the Sliced and Executable tables claim to include the complete Framed requirements. The Executable composition selects predicates by the least malleable target, and no reference in `change-standards` states the order of `spec`, `verification`, and `implementation`.

Evidence: `instructions:skill-auditor` findings f-008 (rule `cumulative-definition-completeness`) against `src/plugins/spec-tree/skills/change-standards/references/dor-sliced.md:11` and f-009 (rule `ambiguous-ordering`) against `src/plugins/spec-tree/skills/change-standards/references/dor-executable.md:25`, both severity `WARNING`, in the typed skill audit of `change-standards` on head `9e5aa8f2f0aa09d8e161620b8c6733165d1ef1b8`, which approved with no must-fix finding.

Impact: a Sliced or Executable record can pass after dropping exact assertion targets or settled choices that Framed required, and an Author or Verifier derives the least malleable target from the word "floor" alone.

Revisit and settlement condition: the Sliced and Executable criteria carry the Framed qualifiers, and the shared `frame` rule or the composition states the malleability order; one typed skill audit of `change-standards` then raises neither finding.

## DEBT [cohesion]: one author-change principle carries two concerns

Defect class: `cohesion`.

Finding: one `<essential_principles>` bullet in `author-change` combines Framed attestation handling with the `change-auditor` dispatch rule.

Evidence: `instructions:skill-auditor` finding f-009 (rule `principle_cohesion`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:23`, in the typed skill audit of `author-change` on head `9e5aa8f2f0aa09d8e161620b8c6733165d1ef1b8`.

Impact: the `attestation-required` stop and the audit-isolation rule cannot be located or applied on their own.

Revisit and settlement condition: each concern stands in its own bullet; one typed skill audit of `author-change` then raises no `principle_cohesion` finding.

## DEBT [decidability]: the Applied precondition rests on undefined terms

Defect class: `decidability`.

Finding: the Lifecycle section of `54-change-record.pdr.md` requires for `Applied` that "the Assertions and evidence governing the Change's Nodes" are "satisfied" and "the Output delivered", terms whose meaning comes only from the foundation's node-state and delivery-boundary definitions.

Evidence: `spec-tree:pdr-auditor` finding `invalid-draft-rule`, severity `WARNING`, on `spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md` at head `9e5aa8f2f0aa09d8e161620b8c6733165d1ef1b8`, in an audit that approved.

Impact: two Verifiers can differ on what "satisfied" requires for a Node the Frame does not require `Passing`.

Revisit and settlement condition: the decision states the Applied precondition in terms of the state each Frame requires for its Nodes and the delivery boundary; one PDR audit then raises no finding against the rule.

## DEBT [term-ownership]: Change skills use terms and grants their bundles do not define

Defect class: `term-ownership`.

Finding: `change-standards` uses `VERIFICATION_READINESS` and the coverage predicate in `executable-state-evidence` and `<merge_composition>` without naming the skill that defines them. The four `author-change` workflows read "the router's store configuration", a phrase the router never defines, while `SKILL.md` names `spx/local/coordination.md`. `audit-change` grants `printf` without a narrower pattern, and shows `recordedByRunDriver`, `producerIdentity`, and `producerProvenance` as string placeholders in a JSON template whose prose requires objects. The Executable `# Activities` criterion of `54-change-record.pdr.md` names its subject "an agent" where the Executor Role is meant.

Evidence: `instructions:skill-auditor` finding f-008 (rule `undefined-cross-skill-term`) against `src/plugins/spec-tree/skills/change-standards/references/dor-executable.md:14`, f-007 (rule `ambiguous_reference`) against `src/plugins/spec-tree/skills/author-change/workflows/proposed.md:3`, and f-011, f-012, f-014 against `src/plugins/spec-tree/skills/audit-change/SKILL.md:9` and `:213`, each severity `WARNING`, in the typed skill audits on head `e383a009d0eefd79ad595c5e1febb8ac670e9253`, all approved for those findings; `spec-tree:pdr-auditor` finding `consistency-violation`, severity `WARNING`, on `spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md` at that head, in an audit that approved.

Impact: a consumer that loads only one of these skills meets a term or input it cannot resolve, and the audit skill's `printf` grant is broader than its workflow.

Revisit and settlement condition: each term names its owning skill or is defined where used, the workflows name `spx/local/coordination.md`, the `printf` grant is narrowed, the template shows object placeholders, and the Executable criterion names the Executor; one typed skill audit of each skill and one PDR audit then raise none of these findings.

## DEBT [entry-conditions]: author-change leaves two entry points and one trigger phrase unstated

Defect class: `entry-conditions`.

Finding: the Executable workflow's step 1 resolves only a Sliced Change, while the router says each workflow handles creation and revision at its level, so revising a Change already at Executable has no stated entry condition. The description's trigger "interviewing ... a Change record" does not match how a request for a Change is phrased.

Evidence: `instructions:skill-auditor` findings f-008 (rule `routing_contradiction`) against `src/plugins/spec-tree/skills/author-change/workflows/executable.md:9` and f-010 (rule `description_trigger_phrasing`) against `src/plugins/spec-tree/skills/author-change/SKILL.md:4`, both severity `WARNING`, in the typed skill audit of `author-change` on head `e2b7d787e3a8cd92005c2522d12aa9d5a57ec688`, which approved with no must-fix finding.

Impact: a revision of an Executable record proceeds on a guessed entry condition, and description matching misses requests phrased as refining a Change.

Revisit and settlement condition: the Executable workflow states its entry for a current Executable record, and the description uses the verbs a request for a Change uses; one typed skill audit of `author-change` then raises neither finding.

## DEBT [restatement]: audit-change step 5 lists record subjects the standards own

Defect class: `restatement`.

Finding: step 5 of `audit-change` lists the record content it judges — the four-section order, Output, Value, per-node target malleability, the Intent attestation, the accountable person, and the Executable predicates against `<merge_composition>` — while its own constraint says `change-standards` owns contract content and the skill owns only procedure.

Evidence: `instructions:skill-auditor` finding f-009 (rule `standards_content_restated_in_auditor`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:110`, in the typed skill audit of `audit-change` on head `d7bec8eb8a49a33aee1141fdf9c255c8fa719c66`, which approved with no must-fix finding.

Impact: a rule `change-standards` adds, renames, or rescopes can drift from the step's list, and the step can read as a narrower checklist than the loaded inventory.

Revisit and settlement condition: step 5 judges against the loaded rule and criterion inventory without restating its subjects; one typed skill audit of `audit-change` then raises no `standards_content_restated_in_auditor` finding.

## DEBT [adr-pdr-compliance]: the audit-change runner is a generic shipped script beyond fifty lines

Defect class: `adr-pdr-compliance`.

Finding: `src/plugins/spec-tree/skills/audit-change/scripts/audit_change_run.py` is a generic shipped script far beyond fifty lines, which `spx/12-shipped-scripting.adr.md` holds as debt awaiting extraction of its logic into the SPX CLI once the script proves its value, or removal when it does not.

The `change-auditor` definition `src/plugins/spec-tree/agents/change-auditor.md` has no retained release-acceptance evidence: `spx/15-subagent-execution.pdr.md` declares release acceptance per supported harness as native loading plus one minimal isolated execution for each of its Standard, Strong, and Fast profiles. Release acceptance belongs to the release, so the changeset that introduces the definition, Change outcomeeng/changes#162, runs no paid invocation.

Evidence: `spec-tree:implementation-auditor` run `2026-09-29_08-34-14-821-c605096fd926` raised a `debt` finding under rule `adr-pdr-compliance` against the runner; `wc -l` over the runner derives its current length, so this entry carries no line count. `instructions:subagent-auditor` finding `f-002`, verdict `REJECT`, class `evidence/missing-invocation-evidence`, judged `src/plugins/spec-tree/agents/change-auditor.md` on head `02c847e66b2f526804db14eb568fae2a2180b858`.

Impact: the runner's state, branching, and result contracts ship inside a plugin that a consumer repository cannot version independently or repair without a marketplace release. No execution claim stands for the `change-auditor` definition on any harness or profile until release acceptance retains its evidence.

Revisit and settlement condition: once the runner proves its value in use, its logic moves into the SPX CLI, tested there and consumed by the plugins product as a trusted third-party component, leaving `audit-change` its instruction and no script; a runner that does not prove its value is removed rather than extracted. The definition's gap settles when release acceptance retains, for every supported harness, native loading and one minimal isolated execution of each Standard, Strong, and Fast profile, judged by an independent Auditor with no retry or substitution after a failed or unusable launch.

## DEBT [evidence]: the runner's unreadable-output blocks reach no linked test

Defect class: `evidence`.

Finding: `reconcile` and the finding readers of `audit_change_run.py` block with `unreadable-output` when the rendered projection carries no `auditScopeUnits` array of objects or a finding without an integer `seq` and a payload object. `tests/test_audit_change_run.compliance.l1.py` drives the runner against the real SPX store, which never renders such a projection, so removing either block leaves every linked test passing. The same holds for the other blocked-result branches the real store never reaches: the runner's command wrapper on an `OSError`, a `ValueError`, or undecodable output, the line reader on unparseable or empty command output, the findings reader on a findings group that is not an array, the `retained-input-mismatch` block of `start`, the `OSError` branch of the stdin read in `main`, and the serializer's `RecursionError` fallback. The test-evidence audit of the changes node on head `c9124f951d82668d846e303686b236a52f72a309` raised this as a `WARNING` coverage finding against `src/plugins/spec-tree/skills/audit-change/scripts/audit_change_run.py`.

Impact: the runner's refusal of a malformed projection is unobserved, so a regression there reads a run with no coverage as an empty one.

Revisit and settlement condition: the runner's SPX boundary admits a controlled implementation of its command runner that renders a malformed projection, and a linked case asserts the `unreadable-output` block for each malformed shape.

## DEBT [internal-consistency]: author-change forbids interpolation and then interpolates the title

Defect class: `internal-consistency`.

Finding: `author-change` says to NEVER interpolate record content into executable shell syntax, and its persistence step then puts the record's `title` into `gh issue create` and `gh issue edit` as a single-quoted `--title` argument. That form is legitimate only under the `inert-stdin` rule of `change-standards`, which the skill cites separately, so the absolute prohibition reads as forbidding the step the persistence workflow requires.

Evidence: `instructions:skill-auditor` finding f-009 (rule `internal_consistency`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:34`, in the typed skill audit of `author-change` on head `7682aa69f9042b1221456caf7274ca937c083232`, which approved with no must-fix finding. The lines lie outside the audit-change runner changeset's diff.

Impact: Claude meets two absolute instructions that disagree on the title write.

Revisit and settlement condition: the prohibition is scoped to the `inert-stdin` rule, or the title step cites that rule's single-quote form; one typed skill audit of `author-change` then raises no `internal_consistency` finding.

## DEBT [skill-contract]: audit-change's grant deviation and its inline reason table stay open

Defect class: `skill-contract`.

Finding: two warnings stand against `audit-change` after its approving audit. The `allowed-tools` grant omits the `Read`, `Grep`, and `Glob` baseline that `/skill-standards` requires of audit skills, because the runner is the audit's only read path and its journal appends make the grant a write grant; the skill states the deviation, and no standard or overlay records it. The reason table in `<runner_contract>` states every blocked condition inline, so each invocation loads text the workflow needs only to relay a blocked result unchanged, while the completeness of that table is itself a review requirement.

Evidence: `instructions:skill-auditor` findings f-008 (rule `audit-skill-read-only-allowed-tools`) and f-009 (rule `progressive-disclosure-conditional-detail`), each severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md`, in the typed skill audit of `audit-change` on head `007c3871de7b82f7592325be191d26fbfa8aee8d`, which approved with no must-fix finding.

The typed skill audit on head `95da1302cb72c523328f0d7d02b3a05b23df603b` approved again with no must-fix finding and raised the grant deviation as f-007 (rule `audit-allowed-tools-read-only`) and two further warnings: the `result:` placeholder of the BLOCKED block packs three result shapes into one line joined by "; or" (f-008, rule `verdict-format-legibility`, against `SKILL.md` line 236), and the constraint that forbids piping "into a command that masks its exit status" implies that some piping is allowed although the runner-only constraint forbids every other command (f-009, rule `constraint-precision`, against `SKILL.md` line 23). The piping wording is the wording the changes spec states for the same rule.

Impact: each later audit of the skill raises the grant warning again, the table's size pulls against the review rule that it name every blocked condition, a reader matches a stop condition against one compound placeholder, and the piping qualifier reads as an exception.

Revisit and settlement condition: `/skill-standards` or `spx/local/skills.md` records the journal-writing grant as a sanctioned exception to the audit read-only rule, the exhaustive condition text moves to a bundled reference the skill loads only for a blocked result, each BLOCKED result shape stands as its own labeled shape, and the skill and the changes spec state the piping prohibition without the qualifier; one typed skill audit of `audit-change` then raises none of the warnings.

## DEBT [subagent-contract]: change-auditor restates the skill's result contract and carries a description-match description

Defect class: `subagent-contract`.

Finding: two warnings stand against the `change-auditor` definition. Its `<output_format>` restates the skill's result contract field by field, and its list of fields for a failed command omits `liveSha256`, `sha256`, and `retainedSha256`, which the skill's `<verdict_format>` carries for `candidate-changed` and `retained-input-mismatch`. Its description is directive description-match wording, although the owning skills dispatch the role by exact configured name.

Evidence: `instructions:subagent-auditor` findings f-003 (rule `description-style/exact-name-invocation`) and f-004 (rule `configuration/thin-wrapper-contract-copy`), each severity `WARNING`, against `src/plugins/spec-tree/agents/change-auditor.md` lines 3 and 91, in the typed subagent audit on head `95da1302cb72c523328f0d7d02b3a05b23df603b`, which rejected on the standing findings f-001 and f-002 recorded in the native-artifact node and in the `adr-pdr-compliance` entry above. The directive description is the wording every spec-tree agent definition carries.

Impact: the wrapper's copied field list drifts each time the runner contract changes, and a relaying session can take the narrower list as the expected shape; the description invites a launch the calling skills have not instructed.

Revisit and settlement condition: the wrapper points at the skill's `<verdict_format>` for the completed, `OUTSIDE_CONTRACT`, and runner-blocked shapes and keeps only its own pre-run diagnostic shape, and the description states its subject and the conditions under which the owning skills invoke the role in passive wording; one typed subagent audit of `change-auditor` then raises neither warning.

## DEBT [ambiguity]: the handoff-record rule says "exactly" and then admits optional lines

Defect class: `ambiguity`.

Finding: the `handoff-record` rule of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md` says a Handoff is one comment carrying "exactly these lines", and the sentence after its template admits optional context lines after the five.

Evidence: `instructions:skill-auditor` run `2026-10-06_18-43-56-339-bb1779a50595`, rule `audit-skill-ambiguity`, severity `debt`, against `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md` lines 59-71 at head `4be7a922d11c27af632039953b5baf36db8b999f`, the post-edit audit of the page-bound changeset. That changeset's diff of the file is line 23 alone, so the finding lies outside the changed text.

Impact: a Handoff author cannot tell whether the two optional lines break the "exactly" requirement, and `release-change` states a matching "exactly the five continuation lines" criterion.

Revisit and settlement condition: the rule states the five required lines and the two optional lines in one consistent statement, and `release-change` matches it; one typed skill audit of `change-standards` then raises no `audit-skill-ambiguity` finding.
