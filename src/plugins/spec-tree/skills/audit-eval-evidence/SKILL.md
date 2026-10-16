---
name: audit-eval-evidence
description: >-
  Eval-evidence audit methodology — judges whether a spec node's eval suite
  provides evidence its `[eval]` assertions are fulfilled, covering producer
  coupling, oracle independence, assertion alignment, falsifiability, and run
  evidence, and records the judgment as one root unit and one child unit per
  gate in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), {{! tool('use_skill') !}}
---

<objective>

A sealed `spx verification run` judging whether a spec node's eval suite provides evidence its `[eval]` assertions are fulfilled, with one root unit for the node spec and one child unit per gate (`producer-coupling`, `oracle-independence`, `assertion-alignment`, `falsifiability`, `run-evidence`), every finding on touched text recorded on its unit, returned as the run token, the run file, and the rendered projection, whose `terminalStatus` is `approved` or `rejected`, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

- NEVER modify eval artifacts, skill bodies, prompts, cases, history, or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `/contextualize` or `/sync-base`: both can move the checkout, and this audit leaves the checkout unmoved. Step 1 loads the node spec's context read-only.
- NEVER run eval suites, tests, validation, coverage, linters, type-checkers, or other deterministic verification inside the audit — establish evidence quality by reading.
- NEVER approve prompt-only simulation as evidence for skill, agent, classifier, or script behavior.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every finding.
- ALWAYS draw each finding's `rule` from `<rule_catalog>` in `${CLAUDE_SKILL_DIR}/references/evidence-model.md` and carry the severity its row declares — a rule outside the catalog is a gap in the standard, never a finding.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the eval evidence for it.
- NEVER reject on text the changeset leaves unchanged and does not invalidate — return that finding as `filed`, and NEVER raise a recorded finding's severity or let a `filed` finding start to reject unless the run names a changed basis. `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines touched text, the finding key, and the `filed` line.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`.

</constraints>

<essential_principles>

**PRODUCER COUPLING FIRST.**

An eval that never exercises the actual producing skill, agent, classifier, or script will pass regardless of what that producer contains. Check coupling before oracle quality or run history. For claims about skill behavior, a prompt that merely asks for a simulated verdict while restating the desired rules is not evidence about the skill.

Five gates are judged in strict order: producer coupling, oracle independence, assertion alignment, falsifiability, and run evidence. A suite missing any property has zero evidentiary value for the assertion it claims to verify.

**JUDGE BY READING.**

This audit runs no deterministic verification. Establish evidence quality by reading `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, relevant run summaries, and the producing artifact.

**BINARY OUTCOME.**

The run finishes `approved` or `rejected`. A gate whose inspection cannot be completed is `incomplete` with its cause recorded, so the run finishes `rejected`; it never becomes an approval through an unevaluated gate.

</essential_principles>

<audit_workflow>

<request_contract>

`$ARGUMENTS` supplies the request when non-empty; when it is empty, the request is the one the request text carries, and the empty substitution binds nothing. The request is a JSON object with exactly two fields. `path` is the product-relative path of the node spec whose `[eval]` evidence is audited, spaces preserved. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` in `${CLAUDE_SKILL_DIR}/references/run-recording.md` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or an empty `path`, returns `BLOCKED` with run token `not-started` naming the exact field before any command runs.

Use skill `spec-tree:spec-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that the finding payload of `${CLAUDE_SKILL_DIR}/references/run-recording.md` records in `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<step name="load_context">

**Step 1: Load context read-only**

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`

When the live `<SPEC_TREE_FOUNDATION>` marker is absent: Use skill `spec-tree:understand`.

Load the node spec's context with `Read`, `Glob`, and `Grep` alone, in this order:

1. The product spec.
2. Each spec and every decision record in each directory on the path from `spx/` to the directory containing the node spec, root first, the node spec under audit excluded.
3. Every decision that a loaded spec or decision cites by full `spx/` path, each read once.

A decision that a loaded record cites and that cannot be read is a `context-unavailable` finding on the root unit, recorded in Step 5. Do not proceed without the live `<SPEC_TREE_FOUNDATION>` marker.

</step>

<step name="open_run">

**Step 2: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built.

The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="map_assertions">

**Step 3: Map `[eval]` assertions to eval artifacts**

Read the node spec's Assertions section. An absent or unreadable target returns `BLOCKED` with the exact failure. For each `[eval]` assertion, extract:

| Field          | Extract                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------- |
| Assertion text | The claim being evaluated                                                                          |
| Eval link      | Path from `([eval](path/to/eval.toml))`                                                            |
| Eval directory | Directory containing `eval.toml`, prompt, and cases                                                |
| Producer       | The skill, agent, classifier, script, or command the assertion claims emits the structured verdict |
| Link status    | File exists or missing                                                                             |

Attribute a missing eval definition to `producer-coupling`, a missing prompt to `producer-coupling`, missing cases to `oracle-independence`, and missing history to `run-evidence`. Record that gate as failing with a `missing-artifact` finding naming the assertion, the missing path, and the failed evidence property. Inspect the remaining available artifacts; a gate whose inspection the absence prevents is `incomplete`, and its `gate-undecidable` finding names the missing prerequisite. A known failure takes precedence over an undecidable result for the same gate.

Skip `[test]`, `[probe]`, and `[audit]` assertions. They belong to their own evidence lanes.

When the node has no `[eval]` assertions, every gate unit is `not-applicable` and no gate is judged; the run carries no finding and never implies that evidence was inspected.

Resolve the touched text of the inspected artifacts as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, so Steps 4 and 5 can classify each finding.

</step>

<step name="audit_gates">

**Step 4: Judge the five gates, in strict order**

<property name="producer-coupling">

Classify how the eval reaches the producer:

| Category         | Definition                                                                                  | Outcome                                                                |
| ---------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Direct           | The eval runner invokes the producing skill, agent, classifier, script, or command directly | Proceed                                                                |
| Harness-mediated | The eval invokes a harness that loads and runs the producer without replacing its behavior  | Proceed after verifying the harness chain                              |
| Prompt-loaded    | The prompt loads the producer body as context while the case drives a verdict task          | Proceed only when the artifact under audit is the loaded producer text |
| Simulation       | The prompt restates the desired policy or asks for a simulated verdict without the producer | `producer-coupling` finding                                            |
| False            | Metadata names the producer but the prompt or harness never uses it                         | `producer-coupling` finding                                            |
| Unknown          | The artifact path cannot establish how the producer is reached                              | `producer-coupling` finding                                            |

When `eval.toml` declares `prompt_source.kind = "producer-section"`, treat the materialized prompt as Prompt-loaded only after verifying the producer path, selected section, and prompt template exist and `prompt.md` is current with that source. The selected producer section is the artifact under audit for that suite; a mutation to that section must change the materialized prompt. Do not require the eval runner to invoke the whole skill, agent, classifier, or script when the assertion is about the selected section's behavior: the loaded section is the producer artifact for that suite. A hand-authored prompt that copies the same policy without `prompt_source` remains Simulation.

Apply the evidence model's `<producer_coupling>` counterfactual reading procedure. If the eval would still pass after the identified producer mutation, classify as Simulation or False and record the `producer-coupling` finding.

</property>

<property name="oracle-independence">

Read `prompt.md` and `cases.jsonl` side by side. Check whether the prompt sent to the producer leaks the expected verdict, expected finding IDs, exact answer table, or rule mapping in a way that makes the case self-answering.

Expected fields belong in the grader input, not in the task prompt the producer answers. A case may include expected verdict data for deterministic scoring; the model-facing prompt must still require the producer to infer the verdict from the scenario and its own methodology.

Self-answering prompt or case construction is an `oracle-leakage` finding.

</property>

<property name="assertion-alignment">

Read the spec assertion, the eval cases, and the expected verdict fields. Answer:

1. Does each expected verdict field correspond to behavior the assertion claims?
2. Do the negative cases target the assertion's failure mode?
3. Could the assertion be unfulfilled while the eval suite passes?

If the assertion could be unfulfilled while the suite passes, record an `assertion-alignment` finding.

</property>

<property name="falsifiability">

Name a concrete mutation to the producing artifact that would make at least one case fail. For `producer-section` suites, the mutation targets the selected producer section and reaches the eval through prompt materialization. Write it down:

```text
Producer: the /manage-pr skill's post-merge guidance section
Mutation: replace the post-merge marketplace sync rule with unrelated text
Impact: the post-merge-sync-required case returns REJECT because the producer omits the required follow-up
```

Cannot name a mutation to the producer that changes the eval result → `falsifiability` finding.

</property>

<property name="run-evidence">

Read `history.jsonl` and, when available, the referenced run summary. Check that the committed history contains a successful run for the current eval definition, threshold, and case set.

Budget-exhausted, timeout, interrupted, or infrastructure-failed runs are operational evidence only. They do not prove behavior. A passing history row for a stale prompt, stale case set, or different producer does not prove the current assertion.

Missing, stale, or operationally incomplete run evidence → `run-evidence` finding. A recorded commit that cannot be inspected makes the gate undecidable, not stale.

</property>

</step>

<step name="classify">

**Step 5: Classify and record**

Classify every finding per `${CLAUDE_SKILL_DIR}/references/touched-text.md`: a finding on touched text is recorded on its unit with the severity its catalog row declares; every other finding is standing, returned as a `filed` line, and recorded nowhere in the run.

Once judgment is complete, read `${CLAUDE_SKILL_DIR}/references/run-recording.md` before the first `scope add`; its `<persistence_contract>` gives the unit identities and payloads and its `<payload_files>` gives how each payload reaches a command. Add the root unit first, because a run admits one root and every child names it, then one child unit per gate, then each finding on touched text on the unit of the gate it names; a finding that names no gate sits on the root. A decided gate is `audited`, whether it holds or carries findings; a gate with nothing to judge is `not-applicable`; a gate whose inspection could not be completed is `incomplete` and carries its `gate-undecidable` finding.

</step>

<step name="finish">

**Step 6: Finish and render**

Derive `rejected` when a finding on touched text exists or any unit is `incomplete`, and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `PASS`, `FAIL`, `APPROVED`, or `REJECTED` envelope and no restated findings. After the projection, return each standing finding as a `filed` line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`, then each `not-applicable` gate as a line:

```text
not-applicable: <unit-key> | subjects: <path> | explanation: <why no eval evidence applies to the node>
```

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a prompt-only skill simulation**

Claude accepted an eval that asked Claude to simulate a skill verdict from inline rules while never loading or invoking the real skill. Replacing the real skill body with unrelated text did not change the eval result, so the eval proved the prompt's rubric, not the skill.

How to avoid: the `producer-coupling` gate checks coupling first. Prompt-only simulation is a `producer-coupling` finding for claims about producer behavior.

**Failure 2: Treated a budget failure as behavioral evidence**

Claude read a budget-exhausted eval run and treated the failed suite as evidence the rule was wrong. The run never completed enough cases to prove behavior.

How to avoid: the `run-evidence` gate separates operational failures from behavioral pass evidence. Budget, timeout, and interruption rows never prove assertion fulfillment.

**Failure 3: Loaded context through the synchronizing skills**

Claude invoked `/contextualize` to load the node spec's context, and its `/sync-base` step rebased or advanced the checkout under the audit, so the head the audit judged differed from the head it started on.

How to avoid: Load context with the read-only steps of Step 1 and never invoke either skill.

**Failure 4: Approved a run over a gate it could not decide**

Claude could not inspect the recorded commit of a history row, recorded the `run-evidence` gate as `audited` with no finding, and finished `approved`. The gate was never decided, so the approval claimed evidence nobody read.

How to avoid: record the gate `incomplete` with a `gate-undecidable` finding naming the unavailable commit, and finish `rejected`.

</failure_modes>

<success_criteria>

- Every `[eval]` assertion's suite was judged on all five gates with none skipped, and every unit the run holds is `audited`, `not-applicable`, or `incomplete`.
- Every recorded finding lies on touched text, or names an undecidable gate, and sits on an accepted unit, naming the assertion or eval artifact, the failed property, the evidentiary gap, and how the eval could pass while the assertion is unfulfilled.
- Every standing finding appears as a `filed` line carrying its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The terminal status is `rejected` exactly when a finding on touched text is recorded or a gate is `incomplete`, so no standing finding decides it.
- No deterministic command was run inside the audit; evidence quality was established by reading the eval artifacts, the producing artifact, and committed run summaries.
- The checkout the audit judged is the checkout it started on and left, so the verdict describes one head.
- The same node spec, eval artifacts, run evidence, context, and base yield the same units, finding keys, and terminal status.

</success_criteria>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/evidence-model.md` — eval evidence properties, artifact taxonomy, and the rule catalog.
- `${CLAUDE_SKILL_DIR}/references/touched-text.md` — touched text, finding key, severity retention, and the `filed` line.
- `${CLAUDE_SKILL_DIR}/references/run-recording.md` — unit identities, payload schemas, and payload-file rules for the run.

</reference_guides>
