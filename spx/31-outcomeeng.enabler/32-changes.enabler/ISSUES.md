# Issues

## DEBT [capability]: unused author-change verification grants

Defect class: `capability`.

Finding: `author-change` grants `Bash(spx verification run input:*)`, `Bash(spx verification run status:*)`, and `Bash(spx verification run render:*)`, although its delegating workflow does not use them.

Evidence: `src/plugins/spec-tree/skills/author-change/SKILL.md:8` declares all three grants, and the hosted review at [PR #583](https://github.com/outcomeeng/plugins/pull/583#issuecomment-5730664407) identified no corresponding invocation in the workflow.

Impact: the skill carries excess capability beyond the authority required by its delegating workflow.

Successor: the Proposed Change filed after Change #89 merges for the agent-run-journal sequence collision, carrying this defect as its second item.

Revisit and settlement condition: remove all three unused verification-run grants and pass one typed skill audit over the revised `author-change` surface.

## DEBT [specificity]: author-change leaves four checks and one workflow unnamed

Defect class: `specificity`.

Finding: the typed skill audit of `author-change` on the Change Lifecycle changeset (head `a28a5be91fc2ea04151c283059caa9cb9a11fd12`) found the audit gate not naming which granted `spx verification run` command establishes `terminalStatus`, the rendered projection, and retained-input equality; the split and coalesce lineage operations routed to a workflow no bundle names; the structured-question tool unnamed and ungranted where the body asks the operator; and two success criteria ("carries the required authority", "Continuation depends only on…") without a named check.

Evidence: `instructions:skill-auditor` findings f-010, f-012, f-013, f-014 on `src/plugins/spec-tree/skills/author-change/SKILL.md`. The second skill-audit pass on the three Lifecycle skills added: `release-change` step 3 carries six stop-capable operations in one paragraph (f-009), a candidate for numbered sub-steps. The relaunch of the `change-standards` audit added: `SKILL.md` calls the references "rules and no procedure" while `lifecycle.md` carries command forms (f-008), and its first success criterion is not observable at load (f-010). The typed skill audit of `change-standards` on the Proposed-readiness changeset (head `98e924f4f88200425e649c3034f6fb0336f2bcf8`) raised the same "no procedure" claim again: `SKILL.md:30` states that the shared references own the rules and no procedure while `lifecycle.md` carries command-bearing rules, and the same sentence's inventory of `lifecycle.md` omits its `canonical-state` rule (f-009, `WARNING`). The typed skill audit of `author-change` at that head again found no step naming the `spx verification run` command that establishes the audit-gate checks (f-009, `WARNING`).

Impact: the gate's checks and the lineage operations rest on judgment where a named command or workflow would make them falsifiable, and a reader of the `change-standards` loading contract receives an inaccurate account of what `lifecycle.md` contains.

Successor: the Proposed Change filed after Change #89 merges for the `author-change` grants (entry above), carrying these as further items.

Revisit and settlement condition: each check named against its granted command, the lineage workflow named or the operation stopped with a named result, the structured-question tool named and granted, the `change-standards` loading contract describing its references' content accurately with every `lifecycle.md` rule in its inventory, and one typed skill audit of each skill approving with no `specificity` finding.

## DEBT [single-location]: change-standards states one requirement in more than one place

Defect class: `single-location`.

Finding: the first success criterion of `change-standards` states that each record requirement has one canonical statement in the shared reference, while the Definition of Ready tables restate requirements the shared `change-record.md` rules already state: `proposed-input-boundary` restates `received-input-boundary`, and `framed-authority` restates the Intent attestation text the `frame` rule carries.

Evidence: `instructions:skill-auditor` finding f-011, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/SKILL.md:36`, in the typed skill audit of `change-standards` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`.

Impact: the `change-standards` success criterion cannot be met as written, so an auditor judging the skill against it either raises the restatement again or accepts a criterion the bundle does not hold. A restated requirement can drift from its other statement without any check reporting the split.

Revisit and settlement condition: either each Definition of Ready criterion that restates a shared rule cites that rule by its identifier instead of restating its text, or the success criterion states the relation the bundle actually holds between shared rules and Maturity criteria; one typed skill audit of `change-standards` then raises no finding against those statements.

## DEBT [precondition]: the Change skills assume a GitHub store without stating the precondition or a blocked result for another store

Defect class: `precondition`.

Finding: `change-standards` `lifecycle.md` rules `canonical-state` and `inert-stdin` read and write the Change store through `gh` against GitHub Issues and a GitHub Project without stating that store kind as a precondition or naming the result for a store of another kind; `author-change` persistence uses `gh` for the GitHub store the coordination overlay declares and names no result when that overlay is absent or declares a store of another kind.

Evidence: `instructions:skill-auditor` finding f-012, severity `WARNING`, against `src/plugins/spec-tree/skills/change-standards/references/lifecycle.md:11`, and finding f-008, severity `WARNING`, against `src/plugins/spec-tree/skills/author-change/SKILL.md:92`, in the typed skill audits of `change-standards` and `author-change` on head `98e924f4f88200425e649c3034f6fb0336f2bcf8`.

Impact: a consumer repository whose coordination overlay is absent or declares a non-GitHub store reaches `gh` commands the store cannot answer, with no stated blocked result, so the failure surfaces as an opaque command error instead of a named precondition.

Revisit and settlement condition: each of the two skills states the store kind its commands require and names the blocked result for a store of another kind, `author-change` also naming it for an absent overlay as `lifecycle.md` `store-binding` already does; one typed skill audit of each skill then raises no `precondition` finding.
