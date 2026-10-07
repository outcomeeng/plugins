# Issues

## DEBT [capability]: unused author-change verification grants

Defect class: `capability`.

Finding: `author-change` grants `Bash(spx verification run input:*)`, `Bash(spx verification run status:*)`, and `Bash(spx verification run render:*)`, although its delegating workflow does not use them.

Evidence: `src/plugins/spec-tree/skills/author-change/SKILL.md:8` declares all three grants, and the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) identified no corresponding invocation in the workflow. `instructions:skill-auditor` run `2026-10-07_08-30-45-540-0d732cbf18ec` raised it again as rule `allowed-tools-narrowest-grant` for `Bash(spx verification run status:*)` at `SKILL.md:8`, and run `2026-10-07_08-39-58-900-2429c7e936a6` a third time; the grant is unchanged from the base.

Impact: the skill carries excess capability beyond the authority required by its delegating workflow.

Successor: the Proposed Change filed after Change #89 merges for the agent-run-journal sequence collision, carrying this defect as its second item.

Revisit and settlement condition: remove all three unused verification-run grants and pass one typed skill audit over the revised `author-change` surface.

## DEBT [skill-audit]: author-change's Sliced workflow leaves a successor's Maturity unstated

Defect class: `skill-audit`.

Finding: `instructions:skill-auditor` run `2026-10-07_08-39-58-900-2429c7e936a6` at head `229758261d4ce3887351a08e25d81b51b226c062` raised `ambiguous-instruction` against `src/plugins/spec-tree/skills/author-change/workflows/sliced.md` step 2 (line 10): the step authors each successor "as a new Change through this skill" and never states the successor's target Maturity or what becomes of the source's Framed Nodes, Assertion operations, and Decisions, while `<authority_gate>` persists every new Change at `Proposed`. The changeset's diff of `sliced.md` against the base is lines 3, 9, 12, 19, 20 and 22; line 10 is outside it.

Evidence: the sealed run above.

Impact: a split or coalescence leaves open whether the successor carries the source's framed content or re-frames it after its own confirmation at `Proposed`.

Revisit and settlement condition: step 2 names the successor's Maturity and the disposition of the source's completed Framed content, and one typed skill audit of `author-change` raises no `ambiguous-instruction` finding on it.

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

## DEBT [term-ownership]: Change skills use terms and grants their bundles do not define

Defect class: `term-ownership`.

Finding: `change-standards` uses `VERIFICATION_READINESS` and the coverage predicate in `executable-state-evidence` and `<merge_composition>` without naming the skill that defines them. The four `author-change` workflows read "the router's store configuration", a phrase the router never defines, while `SKILL.md` names `spx/local/coordination.md`. `audit-change` grants `printf` without a narrower pattern, and shows `recordedByRunDriver`, `producerIdentity`, and `producerProvenance` as string placeholders in a JSON template whose prose requires objects.

Evidence: `instructions:skill-auditor` finding f-008 (rule `undefined-cross-skill-term`) against `src/plugins/spec-tree/skills/change-standards/references/dor-executable.md:14`, f-007 (rule `ambiguous_reference`) against `src/plugins/spec-tree/skills/author-change/workflows/proposed.md:3`, and f-011, f-012, f-014 against `src/plugins/spec-tree/skills/audit-change/SKILL.md:9` and `:213`, each severity `WARNING`, in the typed skill audits on head `e383a009d0eefd79ad595c5e1febb8ac670e9253`, all approved for those findings.

Impact: a consumer that loads only one of these skills meets a term or input it cannot resolve, and the audit skill's `printf` grant is broader than its workflow.

Revisit and settlement condition: each term names its owning skill or is defined where used, the workflows name `spx/local/coordination.md`, the `printf` grant is narrowed, and the template shows object placeholders; one typed skill audit of each skill then raises none of these findings.

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

## DEBT [bound]: author-change reads a Change's blockers without a named page bound

Defect class: `bound`.

Finding: product property 3 of `spx/15-agent-tools.pdr.md` requires a skill that reads a collection endpoint to name its page bound, and `src/plugins/spec-tree/skills/author-change/SKILL.md` line 112 reads the native blockers with the bare call `gh api repos/<store>/issues/<N>/dependencies/blocked_by`. The `change-standards` reference `lifecycle.md`, `release-change` step 4, and the `allowed-tools` grants of `release-change` and `execute-change` name the bounded form `--method GET -F per_page=100` for the same read.

Evidence: a search of `src/plugins/` for `blocked_by` returns the `author-change` read at line 112 as the one blocker read that names no page size; the `author-change` grant is the prefix `Bash(gh api repos/*/issues/*:*)`, which admits the bounded form.

Impact: a Change with more blockers than the endpoint returns per page gives a blocker comparison in `author-change` built from a partial read, with no blocked result naming the bound.

Revisit and settlement condition: `author-change` reads the blockers as one page of 100 and returns a blocked result naming `100 blockers, one page` when the page holds 100 entries, and one typed skill audit of `author-change` follows the edit. The edit landed with the `author-change` revision of Change outcomeeng/changes#333, in `<persistence>` step 3 and its readback, after the two skill-auditor runs the cap allows; the audit that follows it remains.

## DEBT [skill-audit]: release-change carries four skill-audit debt findings on untouched text

Defect class: `skill-audit`.

Finding: `instructions:skill-auditor` runs `2026-10-07_06-54-14-356-29144e907dbd` and `2026-10-07_07-00-31-515-9145a4b7a10a` rejected the audits of `release-change` on `debt` findings, the first at head `d9fa8e14bf24d13be6b4ef928134643b134a96c0` and the second at head `9d7f098b0afb894c102143d3bc4e2aaeaa993588`. The changeset's diff of `src/plugins/spec-tree/skills/release-change/SKILL.md` against the base is line 9, the `gh api repos/*/issues/*/dependencies/blocked_by` grant, and line 33, step 4. The first run's `ambiguity` finding on step 4 lay on changed text and is fixed; the second run raised none there. The remaining findings lie on text the changeset does not change:

- Rule `objective-shape`, line 13 (`<objective>`): the objective names "step 2" and the readback, which belong to `<workflow>`.
- Rule `internal-consistency` or `ambiguous_instruction`, line 27 (step 3.1): the default-branch stop promises no store write, while step 2 has already revised the Change body through `author-change`.
- Rule `ambiguous_instruction`, line 38 (step 6): the readback compares Maturity with "the value read after step 2 completes", and no step instructs that read.
- Rule `tool-restriction-security`, line 9 (`allowed-tools`): the grants `Bash(git branch --show-current)` and the operator-question tool appear in no workflow step. Line 9 is a changed line, and the changeset changes only its blocker-read grant.

A third run, `2026-10-07_08-52-18-926-0f98a52ab60b` at head `5261c8caaab4cdb1b7ba770e09cf242d2e792f7d` over the diff range `0ec15959925f92f0b14891fe2cebd729651bf470` to that head, rejected on two `debt` findings: the grants of line 10 (`Bash(git branch --show-current)` and the operator-question tool) and the contradiction between step 3.1 and the step 2 store write, which the success criterion for an `Executable` refusal repeated. The criterion lies on text the `submit` result added and now says "refused without further mutation after the body revision"; the grants and step 3.1 lie on untouched text and stay here.

Evidence: the three sealed runs above; the diff range is the one named in each finding.

Impact: a reader of the skill meets a stop guarantee that a prior store write contradicts, a readback comparison with no defined source, and two grants no step uses.

Revisit and settlement condition: the objective names only properties of the released state, step 3.1 is evaluated before the first store write or names the step 2 write, a step reads and retains Maturity after step 2, the unused grants are removed, and one typed skill audit of `release-change` raises none of these findings.

## DEBT [skill-audit]: claim-change carries two skill-audit debt findings on untouched text

Defect class: `skill-audit`.

Finding: `instructions:skill-auditor` run `2026-10-07_08-56-10-509-00e01382e95f` at head `e72782baf7b84d35c41258660d70117f7548a5c2` rejected the audit of `claim-change` on two `debt` findings. The changeset's diff of `src/plugins/spec-tree/skills/claim-change/SKILL.md` against base `0ec15959925f92f0b14891fe2cebd729651bf470` is line 24, step 2's report of a `Submitted` Change, and line 62, its success criterion. Both findings lie on text the changeset does not change:

- Rule `caller-independence`, line 41 (step 6): the marker paragraph states which marker the release and close skills act on, a selection rule that belongs to those skills or to the shared Lifecycle standard.
- Rule `skill-intent-ambiguity`, line 42 (step 7): the step states no outcome for a Handoff branch absent on origin or for a failed fetch or switch, and no rule for the fresh branch name when another worktree holds the branch.

Evidence: the sealed run above and the diff range named in the finding.

Impact: a reader of the skill meets a statement about other skills' behavior and a checkout step that stays silent on two failure inputs.

Revisit and settlement condition: step 6 states only the marker the skill emits, the target-selection rule lives in the skills that read the marker or in the shared Lifecycle standard, step 7 states the outcome for every `Branch or PR` value and for a failed fetch or switch and names how a fresh branch is chosen, and one typed skill audit of `claim-change` raises neither finding.

## DEBT [bound]: close-change routes no blocked result for a successor read that reaches its bound

Defect class: `bound`.

Finding: the successor read of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md` (`canonical-state`) returns a blocked read that names `100 issues per page, 10 pages` when the store's `issues` connection still has `hasNextPage` true after page 10, and derives no successor from it. `src/plugins/spec-tree/skills/close-change/SKILL.md` step 3, `Refined` branch (line 32), reads successors under `canonical-state` and routes two outcomes: zero records refuses the close as "Output continues nowhere", and a named successor the store does not hold refuses naming it. Its `<result>` and its success criteria name no blocked-read outcome, so in a store past the bound the derived set is empty and the close is refused for a false reason with the bound dropped.

Evidence: `spec-tree:changes-reviewer` run `2026-10-07_07-21-26-874-21ad0d862cb0` on head `da009a7f1d3d3145258259d9055d7a6a61482044`, finding `consistency` against `close-change/SKILL.md:32`. The Observation of outcomeeng/changes#168 places no skill edit for `close-change` in that Change's Nodes.

Impact: a Change in a store with more issues than the bound cannot be closed `Refined`, and the refusal names no bound.

Revisit and settlement condition: `close-change` step 3, its `<result>` and its success criteria carry a blocked outcome for a successor read that reaches its bound, which refuses the close and names `100 issues per page, 10 pages`, and one typed skill audit of `close-change` follows the edit.

## DEBT [bound]: claim-change lists candidates at a bound and returns no blocked result when the list fills it

Defect class: `bound`.

Finding: `src/plugins/spec-tree/skills/claim-change/SKILL.md` step 1 (line 23) lists candidate Changes with `gh issue list --repo <store> --state open --json number,title,assignees,url --limit 50` and offers up to three from the list. The call names its bound. Product property 3 of `spx/15-agent-tools.pdr.md` also requires a call whose result fills its bound to return a blocked result naming the bound, and step 1 returns none when 50 issues come back, so a store with more open issues than the bound reports a partial list, or `No candidate`, as complete.

Evidence: `spec-tree:changes-reviewer` run `2026-10-06_18-56-26-316-837e0b2a122f` on head `27de076ed368f5eee6477012d9526a89a8af2b77`, finding `consistency` against `claim-change/SKILL.md:23`. The Observation of outcomeeng/changes#168 lists the `--limit 50` read as already bounded and places no skill edit for it in that Change's Nodes.

Impact: `claim-change` can offer a partial candidate set as the whole store.

Revisit and settlement condition: step 1 returns a blocked candidate listing that names `50 issues` when the list returns 50 entries, or the decision states which reads the blocked-result clause covers; one typed skill audit of `claim-change` follows the edit.

## DEBT [bound]: the Change store reads carry nested connections at first:50 with no blocked result

Defect class: `bound`.

Finding: product property 3 of `spx/15-agent-tools.pdr.md` covers a `gh api graphql` call reading a connection and requires a named page bound and a blocked result when the result fills it. The queries of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md` read connections named at `first:50` with no blocked result: `issueFieldValues(first:50)` in the field read (line 19) and in the nested read of the successor query (line 23), and `issueFields(first:50)` in the field-id resolution (line 21). `src/plugins/coding-agents/skills/orchestrate-change/SKILL.md` line 52 reads `issueFieldValues(first:50)` the same way. The successor query's outer `issues(first:100)` connection carries its page count and blocked result.

Evidence: `spec-tree:changes-reviewer` run `2026-10-06_19-01-19-956-109edd5dce9a` on head `7ab8c651a26303d97d3b99534f17a215c2bf2a66`, finding `consistency` against `lifecycle.md:23`. Each query names its bound, and none returns a blocked result when a connection returns 50 nodes.

Impact: an organization that defines 50 or more issue fields, or an issue that carries 50 or more field values, drops a `Predecessors`, `Lifecycle`, or other value from the read with no blocked result.

Revisit and settlement condition: the decision states whether the blocked-result clause covers a nested connection read at a fixed size, or each of these reads states that a connection returning 50 nodes is a blocked read naming `50 issue fields`; one typed skill audit of each of `change-standards` and `orchestrate-change` follows the edit.

## DEBT [tooling-limit]: the GitHub GraphQL budget belongs to the account, and the REST rate-limit endpoint misreports it

Defect class: `tooling-limit`.

Finding: GitHub's GraphQL budget is one per account, shared by every session that authenticates as that account. One unbounded paginated GraphQL query spends the budget for all of them, after which every session stops at its next GitHub call, Executors and attestations included. The REST rate-limit endpoint does not show the stop: while GraphQL refused calls, the endpoint still reported thousands of GraphQL points remaining.

Evidence: the Observation of outcomeeng/changes#168 records a query whose cursor variable `gh` did not recognise, which refetched its first page 575 times in the background and spent the account's GraphQL budget. `gh api graphql --paginate` fills the cursor from a variable named `$endCursor`; any other name leaves the cursor unset, so each page request repeats the first. The Change store's reads, among them the `Predecessors` read of `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md`, are the heaviest users of that budget in this product.

Impact: a session cannot learn from the REST endpoint whether its next GraphQL call will succeed, so a refusal arrives with no earlier signal, and the refusal reaches every session on the account at once. The page bound written in each skill's text keeps any one call from spending the budget; it does not give a session a way to read what remains.

Revisit and settlement condition: GitHub reports the GraphQL budget consistently across its REST and GraphQL interfaces, or a read that establishes GraphQL availability without spending the budget is documented and the Change skills cite it in their blocked results.
