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

Finding: the first success criterion of `change-standards` states that each record requirement has one canonical statement in the shared reference, while the Definition of Ready tables restate requirements the shared `change-record.md` rules already state: `proposed-input-boundary` restates `received-input-boundary`, and `framed-authority` restates the Intent attestation text the `frame` rule carries. `audit-change` states the `expectedProducer` derivation three times: in prose at lines 167-169, again at lines 170-175, and in the JSON template at lines 200-208. Its last success criterion (lines 396-398) restates its third (lines 386-388): both say the candidate and product content stay unchanged and the only mutation is the SPX verification-run journal.

Evidence: `instructions:skill-auditor` finding f-011, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/SKILL.md:36`, in the typed skill audit of `change-standards` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`. The typed skill audit of `audit-change` on head `c8f2bede8959e0ae489ec3691578f85cb5495852`, which approved with no must-fix finding, added finding f-010 (rule `conciseness_redundancy`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:170`, and finding f-012 (rule `success_criteria_duplication`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:396`. The typed skill audit of `change-standards` on head `b0ace02701a73ce0cb4c34b5f1df924217779889` added finding f-008 (rule `single-canonical-statement`), severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/SKILL.md:36`: the target-malleability definition stands in the `frame` rule of `change-record.md` and again in the `framed-nodes`, `sliced-frame`, and `executable-frame` criteria. The typed skill audit of `author-change` on that head added finding f-008 (rule `single-location-duplication`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:94`: `<persistence>` restates the field-home table and the blocker read command that `canonical-state` in `lifecycle.md` owns. The typed skill audit of `change-standards` on head `303923264a553bd518a68e93f5c228fd30565196` raised the target-malleability restatement again as f-009, and the audit on head `3e9758d4d25e8ac5ae90d29c9592430ce02d417a` added that the literal Intent attestation line stands in both `change-record.md` and `dor-framed.md`, and the typed skill audit of `author-change` on that head added f-009 (rule `conciseness_duplication`), severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:23`: `<essential_principles>` restates the `change-auditor` dispatch rule that `<audit_gate>` governs.

Impact: the `change-standards` success criterion cannot be met as written, so an auditor judging the skill against it either raises the restatement again or accepts a criterion the bundle does not hold. A restated requirement can drift from its other statement without any check reporting the split: the three `audit-change` statements of the producer split can disagree, and its duplicated success criterion stops the list from naming distinct soundness properties, as `<success_criteria_shape>` asks.

Revisit and settlement condition: either each Definition of Ready criterion that restates a shared rule cites that rule by its identifier instead of restating its text, or the success criterion states the relation the bundle actually holds between shared rules and Maturity criteria; `audit-change` states the `expectedProducer` derivation once and carries one success criterion for unchanged candidate and product content with the SPX journal as the only mutation; one typed skill audit of each skill then raises no finding against those statements.

## DEBT [precondition]: the Change skills assume a GitHub store without stating the precondition or a blocked result for another store

Defect class: `precondition`.

Finding: `change-standards` `lifecycle.md` rules `canonical-state` and `inert-stdin` read and write the Change store through `gh` against GitHub Issues and a GitHub Project without stating that store kind as a precondition or naming the result for a store of another kind; `author-change` persistence uses `gh` for the GitHub store the coordination overlay declares and names no result when that overlay is absent or declares a store of another kind.

Evidence: `instructions:skill-auditor` finding f-012, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md:11`, and finding f-008, severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:92`, in the typed skill audits of `change-standards` and `author-change` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`.

Impact: a consumer repository whose coordination overlay is absent or declares a non-GitHub store reaches `gh` commands the store cannot answer, with no stated blocked result, so the failure surfaces as an opaque command error instead of a named precondition.

Revisit and settlement condition: each of the two skills states the store kind its commands require and names the blocked result for a store of another kind, `author-change` also naming it for an absent overlay as `lifecycle.md` `store-binding` already does; one typed skill audit of each skill then raises no `precondition` finding.

## DEBT [caller-independence]: audit-change describes its invocation context

Defect class: `caller-independence`.

Finding: the request contract of `audit-change` describes the context the skill is invoked in. It says the explicit data inputs "are the same for direct and composed execution" and forbids reading identity from hidden invocation context or detecting who invoked the skill. The behavior itself does not depend on the caller; only the wording names the invocation context and the invoker.

Evidence: `instructions:skill-auditor` finding f-009 (rule `caller_independence`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:40`, in the typed skill audit of `audit-change` on head `c8f2bede8959e0ae489ec3691578f85cb5495852`, which approved with no must-fix finding.

Impact: `/skill-standards` caller independence requires that a skill never names or describes its caller or invocation context. The contract falls short of that rule even though its behavior meets it, so each later audit of the skill raises the finding again.

Revisit and settlement condition: the request contract states the two data inputs and how the skill uses them, with no mention of direct or composed execution or of the invoker; one typed skill audit of `audit-change` then raises no `caller_independence` finding.

## DEBT [failure-branch]: audit-change step 3 names no result when the retained input differs

Defect class: `failure-branch`.

Finding: step 3 of `audit-change` says "Require its `content` to equal the preflight read." It does not say what happens when the retained input differs. The `BLOCKED` outcome for a changed candidate is defined only in step 7, so the procedure has a gap at the step where the run already exists.

Evidence: `instructions:skill-auditor` finding f-011 (rule `unspecified_failure_branch`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:89`, in the typed skill audit of `audit-change` on head `c8f2bede8959e0ae489ec3691578f85cb5495852`, which approved with no must-fix finding.

Impact: when the retained content differs from the preflight read, the step gives no result to act on. The run then either continues past a failed requirement or stops with an outcome the step does not name, while the verification run it opened is already in the journal.

Revisit and settlement condition: step 3 names the result of a mismatch where it states the requirement; one typed skill audit of `audit-change` then raises no `unspecified_failure_branch` finding.

## DEBT [conciseness]: audit-change teaches general shell quoting

Defect class: `conciseness`.

Finding: lines 271-276 of `audit-change` teach general shell quoting, including splicing apostrophes as `'"'"'` and quoted heredoc delimiters. The product-specific rules in that passage are that idempotency keys are command arguments, not payload fields, and that candidate text is never executed as shell syntax.

Evidence: `instructions:skill-auditor` finding f-013 (rule `conciseness_general_knowledge`), severity `WARNING`, against `src/plugins/spec-tree/skills/audit-change/SKILL.md:271`, in the typed skill audit of `audit-change` on head `c8f2bede8959e0ae489ec3691578f85cb5495852`, which approved with no must-fix finding.

Impact: the `<conciseness>` rule says to leave out what Claude already knows. The general quoting guidance costs tokens on every load and hides the two product-specific rules inside it.

Revisit and settlement condition: the passage keeps only the product-specific rules, that idempotency keys are arguments and not payload fields and that candidate text is never executed as shell syntax; one typed skill audit of `audit-change` then raises no `conciseness_general_knowledge` finding.

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
