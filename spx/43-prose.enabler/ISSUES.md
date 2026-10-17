# Issues: Prose Plugin

## The prose auditor has no enforced read-only runtime boundary

`src/plugins/prose/agents/prose-auditor.md` grants unrestricted `Bash` while
its prompt promises a read-only audit. The generated Codex definition omits
`sandbox_mode`, and the generated Claude definition retains the unrestricted
shell grant. A prompt prohibition therefore supplies no enforced mutation
boundary in either emitted configuration.

**Required handling**: identify the shell operations `prose:audit-prose`
actually requires, restrict the Claude grant to those operations, and declare
the corresponding read-only native boundary for Codex. Retain a minimal
isolated audit result for the exact emitted role.

**Evidence**: `instructions:subagent-auditor` finding `f-001` against
`src/plugins/prose/agents/prose-auditor.md` on Change #76 head
`843ddd709b058970d414ec755cc10121ff6bb5ff`.

## Eval evidence for the prose surface stays deferred

The style-adherence and structure-conformance evals for the prose surface remain unwritten by operator decision: the eval harness is under repair in a separate concurrent effort, and no spec node names that effort yet, so this entry is the owning record rather than a pointer. Revisit when the eval surface is operational.

[`spx/15-spec-coverage.adr.md`](spx/15-spec-coverage.adr.md) places this node's deliverable in the `[eval]` category — the prose surface is LLM-driven behavior whose skills emit a structured verdict. Until that lane exists, every assertion here is verified by a dispatched verifier agent session.

## The three kind style layers use markdown headings

`/skill-standards` recommends pure XML structure for a skill's file set; `prose-standards/SKILL.md` complies while `references/documentation.md`, `references/copy.md`, and `references/interface.md` use markdown `#`/`##` headings. Converting the three reference files is a structural rewrite of each file, deferred as a separate concern because the chat-voice changeset touches their content, not their structure. Surfaced by the skill audit on the chat-voice branch.

## The documentation layer's Overrides section lists entries with no base rule behind them

Two Overrides entries trace to no base rule they relax: the bold row-key cell restates the base table pack's own permission, and the parentheses allowance names no base parenthesis ban. Reworking the section so every declared override cites the relaxed base rule, or reclassifies as additive kind guidance, is a layer-taxonomy change beyond the chat-voice changeset. Surfaced by the skill audit on the chat-voice branch.

## The audit-prose body frames its inputs as what a dispatch or caller supplies

Rule `caller-independence`, found by the `skill-auditor` run `2026-10-13_23-22-04-233-88fc0c8e61f3` (instructions 0.20.0) on head `3142f91a24cd730db5c8dae65112eb91a89b8d5c`, unit `src/plugins/prose/skills/audit-prose/SKILL.md`.

**Evidence**: `src/plugins/prose/skills/audit-prose/SKILL.md` names its caller or a dispatch in these passages, none of which the base-revision changeset changes: the `<constraints>` bullets "a dispatch with no kind" and "whatever kind the dispatch supplied"; the `<kind_intake>` sentences "a dispatch naming any of these" and "A kind named in the arguments or the caller's request"; `<audit_workflow>` step 2 "when the dispatch names no text, paths, or target at all" and step 4 "whatever the dispatch names, pastes, or points to"; and the `<success_criteria>` bullet "A dispatch naming a governed artifact … a dispatch carrying no kind or no target". The lines that changeset changes state the base revision as an argument.

**Impact**: the skill describes its invocation context in place of its own inputs, so a reader learns who calls it before learning what it takes, and the body disagrees with its own argument hint.

**Settlement condition**: every passage states its input as the skill's own argument (kind, text or paths, optional base revision) and names no caller or dispatch.

## The audit-prose verdict is the bare run token, with no rendered projection or blocked diagnostic

Rule `auditor-verdict-format`, found by the `skill-auditor` run `2026-10-13_23-22-04-233-88fc0c8e61f3` (instructions 0.20.0) on head `3142f91a24cd730db5c8dae65112eb91a89b8d5c`.

**Evidence**: the `<verdict_format>` bullet "The final message is exactly the raw run token", `<audit_workflow>` step 6 "end with the raw run token as the final message — no prose after it", and the last `<success_criteria>` bullet return only the token. The `<constraints>` bullet on an unavailable journal or `spx` CLI says "report the exact availability failure" and states no diagnostic fields. The instructions 0.20.0 standard asks a run-recording auditor to return the run token with the unmodified rendered projection of the sealed run, or a blocked diagnostic whose full schema the verdict format states.

**Impact**: a caller reads no verdict from the final message and has no defined shape for a run that cannot open its journal.

**Settlement condition**: the prose node's assertion on the audit run's final message and the `<verdict_format>` both return the run token with the unmodified rendered projection, and the verdict format states the blocked-diagnostic schema. The node's spec assertion requires the bare token, so the fix starts with that assertion, which the skill standard outranks.

## The audit-prose run keys findings per sentence, not per unit and rule

Rule `auditor-run-keys`, found by the `skill-auditor` run `2026-10-13_23-22-04-233-88fc0c8e61f3` (instructions 0.20.0) on head `3142f91a24cd730db5c8dae65112eb91a89b8d5c`.

**Evidence**: `<audit_workflow>` step 5 sweeps one sentence at a time, appends "one finding per violated rule" for each sentence, and records a scope-advanced event per sentence; the `<verdict_format>` first bullet lets one rule recur once per offending sentence in one file and keys no unit or finding. The instructions 0.20.0 standard asks a run-recording auditor to key each scope unit by audit class, kind, concern, and subject path, key each finding as `<unit-key>:<rule-id>`, and record at most one finding per rule per file listing every violating location.

**Impact**: two runs over the same text cannot match their findings by key, and one file can carry several findings under one rule.

**Settlement condition**: the prose node's spec assertions on the sweep and the finding record, and `/audit-prose` with them, key each unit and finding as the standard states and fold every violating location of one rule in one file into one finding. This is a separate, larger concern: the fix amends the node's audit-run assertion and the run-journal record shape every journal-recording auditor shares, beyond the base-revision scoping change that surfaced it.

## The audit-prose objective and last success criterion state the same output

Rule `objective-criteria-distinct`, severity debt, found by the `skill-auditor` run `2026-10-13_23-22-04-233-88fc0c8e61f3` (instructions 0.20.0) on head `3142f91a24cd730db5c8dae65112eb91a89b8d5c`.

**Evidence**: `<objective>` ends "whose raw run token is the final message", and the last `<success_criteria>` bullet reads "The final message is exactly the raw run token of a sealed run." Neither line is changed by the base-revision changeset.

**Impact**: the criterion restates the output instead of naming a property that shows the output sound.

**Settlement condition**: the last success criterion states a soundness property of the sealed run, and the objective alone names the output's shape. The settlement of the verdict-format entry above rewrites both lines, so the two settle together.

## Standing skill-audit finding on text the skill rename leaves unchanged

A sealed `skill-auditor` run over the renamed `author-prose-architecture` skill rejected it on text that the rename (Change 475) neither changes nor invalidates. The finding below falls on lines outside the rename's hunk, and it is recorded once with the run that raised it. The path is the current skill directory; line numbers are current-head lines. Severity is the run's.

### `author-prose-architecture`

- `empty_argument_behavior` (debt): `src/plugins/prose/skills/author-prose-architecture/SKILL.md:6` and `:27-39` (`<kind_intake>`). The skill takes input (argument-hint `[interface|documentation|copy] <what to structure>`) but states behavior only for an absent kind; it states nothing for an absent `<what to structure>`, the artifact set the ADR governs. Finding key `instructions:skill:file:src/plugins/prose/skills/author-prose-architecture/SKILL.md:empty_argument_behavior`. Run `2026-10-17_01-17-14-696-90c7ae07a509`, read at head `c9e338b951c62f42c28f1832faf30689706d9ee8`. Base-ref evidence: `git diff -M -U0 origin/main HEAD -- src/plugins/prose/skills` records the file as a rename of `architect-prose/SKILL.md` (similarity 99%) whose only hunk is line `:2`, the `name` field; lines `:6` and `:27-39` are outside every hunk, and neither cites, quotes, or depends on the changed name.

**Resolution shape**: state in the skill what it does when the arguments name no artifact set or governed path, for example asking for it or deriving it from a stated source.

**Revisit condition**: resolve the finding when the skill next changes, since the fix needs a prose version bump and its own `skill-auditor` gate.

**Evidence**: the sealed run named above, under the audit run store of branch `work/change-475`. The run's terminal status is `rejected` on this single finding, which is standing under property 11 of [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md); the rulings at https://github.com/outcomeeng/changes/issues/475#issuecomment-6226715607 (item 2) and https://github.com/outcomeeng/changes/issues/475#issuecomment-6227759607 (items 1 and 2) bind the record.
