---
name: audit-eval-evidence
description: >-
  Eval-evidence audit methodology — judges whether a spec node's eval suite
  provides evidence its `[eval]` assertions are fulfilled, covering producer
  coupling, oracle independence, assertion alignment, falsifiability, and run
  evidence, and records the judgment as a root unit with one child unit per
  gate in an SPX file-scoped verification run.
argument-hint: "<JSON object with path and runDriver>"
allowed-tools: Read, Grep, Glob, Write, Bash(spx verification run:*), Bash(git merge-base:*), Bash(git diff:*), Skill
---

<objective>

A sealed `spx verification run` on one spec node's file against the eval-evidence model in `${CLAUDE_SKILL_DIR}/references/evidence-model.md`, whose verdict is a `terminalStatus` of `approved` or `rejected`, with each finding on touched text recorded on the gate it concerns and each gate it cannot decide recorded `incomplete` with its cause, returned as the run token, the run file, and the rendered projection, followed by each other finding as a `filed` line; or the complete `BLOCKED` diagnostic when the run cannot finish.

</objective>

<constraints>

- NEVER modify eval artifacts, skill bodies, prompts, cases, history, the spec, or any other product file — the only state the audit changes is its payload files in the session scratch directory and the SPX run journal its own recording commands write, and the file-write tool writes payload files only.
- NEVER invoke `product-tree:contextualize` or `product-tree:sync-base`, and never fetch, rebase, or otherwise move the checkout — the audit reads the head as it stands, so it changes no checkout state.
- NEVER run evals, tests, validation, coverage, linters, type-checkers, or other deterministic verification inside the audit — establish evidence quality by reading `eval.toml`, `prompt.md`, `cases.jsonl`, `history.jsonl`, relevant run summaries, and the producing artifact.
- NEVER delegate the audit to another session, or finish a run whose inspection is incomplete because of elapsed time, context pressure, or unfinished reading; an unavailable required inspection leaves its gate `incomplete` with the cause recorded, never an unevaluated unit.
- ALWAYS name the assertion, the failed property, and the evidentiary gap in every finding — the author repairs from the finding alone, and a finding missing any of the three leaves the repair unbounded.
- NEVER approve prompt-only simulation as evidence for skill, agent, classifier, or script behavior — a prompt that simulates the producer scores the simulation, never the shipped producer the assertion governs.
- NEVER issue a finding the evidence model does not support — drop an unbacked finding rather than reject the eval evidence for it.
- NEVER name a finding rule identifier outside the `rejection_categories` table of `${CLAUDE_SKILL_DIR}/references/evidence-model.md`.
- NEVER reject, or record on a unit, a finding that lies outside touched text; classify every finding as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, return each standing finding as `filed`, and never raise its severity or let it reject unless the run names a changed basis.
- ALWAYS persist audit state through `spx verification run`, started before any judgment; NEVER use markdown comments, tracked files, or a hand-formatted verdict as audit state.
- ALWAYS write each payload as one rendered JSON object to its own file and pass the file by path as `<payload_files>` states; NEVER send a payload through a heredoc, a pipe, or an inline argument, build one with an interpreter or `printf` stage, or repair one through command substitution or post-hoc text substitution.
- ALWAYS issue each `spx verification run` mutation as its own command and wait for its exit before the next one — parallel writes race sequence assignment and corrupt the sealed journal.
- NEVER write the run journal or its context anywhere but the locations `spx verification run` resolves. When the native permission policy refuses a run-recording write — a payload file, a run-recording command, or the journal — stop at that write, retry it no more, write to no other location, and return `BLOCKED` with `diagnostic: configuration error` naming the refused path; the host grants the paths, and this skill never widens its own access.
- NEVER retry a rejected command with a rewritten payload; the first command that exits nonzero ends the audit with `BLOCKED`, except the one rerun `<payload_files>` allows for a payload file named absent.

</constraints>

<audit_workflow>

<request_contract>

`$ARGUMENTS` is a JSON object with exactly two fields. `path` is the product-relative path of the spec file of the node whose eval evidence is audited. `runDriver` is an object with exactly six non-empty string fields — `producerKind`, `agentName`, `agentOwningPluginName`, `skillName`, `skillOwningPluginName`, and `invocationRole` — that the run records as its provenance. Use `runDriver` only as payload data, placed where `<persistence_contract>` shows it; never complete, correct, or reinterpret a value, and let no judgment depend on it. A missing, extra, or malformed field, or a `path` that names no spec file, returns `BLOCKED` naming the exact field or path before any command runs.

Use skill `product-tree:product-tree-plugin`. Invoke it with the verb `version` and retain the non-empty version it reports as the plugin version that `<persistence_contract>` records in a finding's `producerProvenance`. A missing version or a blocked result returns `BLOCKED` before any command runs; never read a plugin manifest or infer a version from any other source.

</request_contract>

<execution_sequence>

Check the five gates in strict order, producer coupling first: an eval that never exercises the actual producing skill, agent, classifier, or script passes regardless of what that producer contains, and a prompt that merely asks for a simulated verdict while restating the desired rules is not evidence about the skill. A suite missing any property has zero evidentiary value for the assertion it claims to verify.

<step name="load_context">

**Step 1: Load context read-only**

Read the evidence model before auditing: `${CLAUDE_SKILL_DIR}/references/evidence-model.md`

Load the spec node's context by reading, in this order, and starting no audit phase before every read completes:

1. the product document at `spx/`;
2. at each directory from `spx/` down to the directory containing the node spec, that directory's spec, then every decision record (`*.adr.md`, `*.pdr.md`) in it; in the node's own directory, read its decision records and leave its spec to Step 2;
3. every decision a loaded spec or decision cites by full `spx/` path, repeating for each newly read decision until none is unread; a citation to a missing decision file is a `BLOCKED` result naming the citation and the citing file.

The committed changeset is resolved in `classify`.

</step>

<step name="open_run">

**Step 2: Open the run**

Start the run before judging anything:

```bash
spx verification run start --verification-type audit --scope-type file --scope <path> --input <path>
```

A file-scoped run takes the audited path as its input, passed by path, so the retained input equals the audited file and no start payload is built. The command prints a JSON locator; take its `runToken` exactly and use it for every later command. Retain the run target the locator reports as the run file; only the start report names it. Never pass the whole locator as `--run`.

</step>

<step name="map_assertions">

**Step 3: Map `[eval]` assertions to eval artifacts**

Read the spec's Assertions section. For each `[eval]` assertion, extract:

| Field          | Extract                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------- |
| Assertion text | The claim being evaluated                                                                          |
| Eval link      | Path from `([eval](path/to/eval.toml))`                                                            |
| Eval directory | Directory containing `eval.toml`, prompt, and cases                                                |
| Producer       | The skill, agent, classifier, script, or command the assertion claims emits the structured verdict |
| Link status    | File exists or missing                                                                             |

Attribute a missing eval definition to `producer-coupling`, a missing prompt to `producer-coupling`, missing cases to `oracle-quality`, and missing history to `run-evidence`. Record a finding with rule `missing-artifact` on that gate naming the assertion, the missing path, and the failed evidence property. Inspect the remaining available artifacts; a gate the absence prevents inspecting is `incomplete`, with a finding explaining the missing prerequisite as its cause. A known failure takes precedence over an incomplete result for the same gate.

Skip `[test]`, `[audit:{rule-slug}]`, and the pathless `[audit]` that the foundation admits for a toolchain without slug support. They belong to their own evidence lanes.

When the target has no `[eval]` assertions, every gate is `incomplete`, each carrying one finding with rule `no-eval-assertions` at the target spec explaining that no eval evidence is applicable; never imply that evidence was inspected.

</step>

<step name="audit_producer_coupling">

**Step 4: Producer coupling**

Classify how the eval reaches the producer into one category of the evidence model's `<producer_coupling>` table, including the `prompt_source.kind = "producer-section"` case, and apply that table's verdict for the category. Apply the evidence model's `<producer_coupling>` counterfactual reading procedure. If the eval would still pass after the identified producer mutation, classify as Simulation or False and record rule `producer-coupling`.

</step>

<step name="audit_oracle_independence">

**Step 5: Oracle independence**

Read `prompt.md` and `cases.jsonl` side by side. Check whether the prompt sent to the producer leaks the expected verdict, expected finding IDs, exact answer table, or rule mapping in a way that makes the case self-answering.

Expected fields belong in the grader input, not in the task prompt the producer answers. A case may include expected verdict data for deterministic scoring; the model-facing prompt must still require the producer to infer the verdict from the scenario and its own methodology.

Self-answering prompt or case construction is rule `oracle-leakage`.

</step>

<step name="audit_alignment">

**Step 6: Assertion alignment**

Read the spec assertion, the eval cases, and the expected verdict fields. Answer:

1. Does each expected verdict field correspond to behavior the assertion claims?
2. Do the negative cases target the assertion's failure mode?
3. Could the assertion be unfulfilled while the eval suite passes?

If the assertion could be unfulfilled while the suite passes, record rule `assertion-alignment`.

</step>

<step name="audit_falsifiability">

**Step 7: Falsifiability**

Name a concrete mutation to the producing artifact that would make at least one case fail, as the evidence model's `<falsifiability_model>` defines. Write it down:

```text
Producer: the /manage-pr skill's post-merge guidance section
Mutation: replace the post-merge marketplace sync rule with unrelated text
Impact: the post-merge-sync-required case returns REJECT because the producer omits the required follow-up
```

Cannot name a mutation to the producer that changes the eval result -> record rule `falsifiability`.

</step>

<step name="audit_run_evidence">

**Step 8: Run evidence**

Read `history.jsonl` and, when available, the referenced run summary. Check that the committed history contains a successful run for the current eval definition, threshold, and case set.

Budget-exhausted, timeout, interrupted, or infrastructure-failed runs are operational evidence only. They do not prove behavior. A passing history row for a stale prompt, stale case set, or different producer does not prove the current assertion.

Missing or stale run evidence is rule `run-evidence`.

</step>

<step name="classify">

**Step 9: Classify**

Resolve the base and run the diff commands as `${CLAUDE_SKILL_DIR}/references/touched-text.md` states, and sort every finding into touched text or standing text.

</step>

<step name="record">

**Step 10: Record**

Add the root scope unit first, because a run admits one root and every child names it, then one child scope unit per gate in strict order, then each finding on touched text on its child unit, per `<persistence_contract>`. A gate that holds, or that carries findings, is `audited`; a gate the inspection cannot decide is `incomplete` and carries a finding that records its cause. A standing finding is recorded nowhere in the run.

</step>

<step name="finish">

**Step 11: Finish**

Derive `rejected` when a finding on touched text exists or any gate is `incomplete`, and `approved` otherwise, whatever standing findings exist. Run the finish and render commands:

```bash
spx verification run finish --verification-type audit --scope-type file --scope <path> --run <token> --terminal-status <approved-or-rejected>
spx verification run render --verification-type audit --scope-type file --scope <path> --run <token>
```

</step>

</execution_sequence>

<persistence_contract>

Add a scope unit with `spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <payload-file> --idempotency-key '<unitId>'`, the payload file written per `<payload_files>`. The root unit's `unitId` is the audited `<path>`, its concern partition is `eval-evidence`, and it omits `parentUnitId`; the run admits one root. Each child unit's `unitId` is `eval-evidence:<designator>:<path>` and its `parentUnitId` is the root's `unitId`. The designator is `producer-coupling`, `oracle-quality`, `assertion-alignment`, `falsifiability`, or `run-evidence`. The class `spec` and kind `eval-evidence` are the pair `spx` accepts for this audit.

The root unit:

```json
{
  "unitId": "<path>",
  "auditClass": "spec",
  "auditKind": "eval-evidence",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "eval-evidence"
  },
  "expectedProducer": {
    "producerKind": "skill",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "audit-eval-evidence",
    "skillOwningPluginName": "product-tree",
    "invocationRole": "leaf-skill"
  },
  "recordedByRunDriver": {
    "producerKind": "<runDriver.producerKind>",
    "agentName": "<runDriver.agentName>",
    "agentOwningPluginName": "<runDriver.agentOwningPluginName>",
    "skillName": "<runDriver.skillName>",
    "skillOwningPluginName": "<runDriver.skillOwningPluginName>",
    "invocationRole": "<runDriver.invocationRole>"
  }
}
```

A child unit carries the same fields with `unitId` `eval-evidence:<designator>:<path>`, `parentUnitId` `<path>`, `coverageStatus` `audited` or `incomplete`, and `priorContext.concernPartition` the designator:

```json
{
  "unitId": "eval-evidence:<designator>:<path>",
  "parentUnitId": "<path>",
  "auditClass": "spec",
  "auditKind": "eval-evidence",
  "subject": "<path>",
  "coverageRequirement": "required",
  "coverageStatus": "audited | incomplete",
  "priorContext": {
    "changedFilePartition": "<path>",
    "concernPartition": "<designator>"
  },
  "expectedProducer": "<the root unit's expectedProducer object, repeated exactly>",
  "recordedByRunDriver": "<the root unit's recordedByRunDriver object, repeated exactly>"
}
```

Add a finding with `spx verification run finding add` and the same selectors, `--payload <payload-file>` per `<payload_files>`, and `--idempotency-key '<unitId>:<rule>'`, the finding key `${CLAUDE_SKILL_DIR}/references/touched-text.md` defines. Its payload names an accepted child unit; `producerIdentity` repeats that unit's `expectedProducer`; `producerProvenance` carries the plugin version `<request_contract>` retained in both version fields, and no `toolVersion`; `rule` is an identifier from the `rejection_categories` table of `${CLAUDE_SKILL_DIR}/references/evidence-model.md`, and `location` lists every assertion text or eval artifact where that rule is violated, separated by `;`. A finding that records the cause of an `incomplete` unit names the unavailable inspection in `observed`.

```json
{
  "unitId": "<accepted-unit-key>",
  "producerIdentity": "<the unit's expectedProducer object, repeated exactly>",
  "producerProvenance": {
    "agentOwningPluginVersion": "<product-tree-plugin-version>",
    "skillOwningPluginVersion": "<product-tree-plugin-version>"
  },
  "rule": "<rejection-category-rule-id>",
  "severity": "blocking",
  "location": "<assertion-text-or-eval-artifact>[; <further-location>...]",
  "message": "<designator>: <evidentiary-gap>",
  "evidence": {
    "observed": "<observed-state>",
    "expected": "<state the rule requires>"
  }
}
```

These objects are the sanctioned payload schema for this audit; never derive a replacement from command help or CLI source.

</persistence_contract>

<payload_files>

Quote every idempotency key as one single-quoted argument; encode a literal apostrophe with the splice `'"'"'`.

- ALWAYS copy the scratch directory the harness names for the session into each payload path character for character, and write each scope and finding payload with the file-write tool to its own file there, under a name unique to this run and payload, such as `<run-token>-scope-<n>.json` and `<run-token>-finding-<n>.json`. Where the harness names no scratch directory, use the one the hosting environment designates, such as `$RUNNER_TEMP` on a hosted runner.
- ALWAYS write only payload files with the file-write tool.
- ALWAYS stop before the command that reads a payload file when the file-write result reports a path that the scratch directory does not contain by whole path components, returning the `<verdict_format>` diagnostic naming the reported path.
- ALWAYS pass `--payload` the path exactly as the file-write tool's result reports it, copied from that result, never retyped from memory.
- ALWAYS pass the file as the value of `--payload`, its path written out literally:

  ```bash
  spx verification run scope add --verification-type audit --scope-type file --scope <path> --run <token> --payload <scope-file> --idempotency-key '<unitId>'
  ```

- ALWAYS add each scope unit and each finding with its own literal command and its own payload file, one at a time, and stop the audit at the first command that exits nonzero, other than the one rerun on an absent-payload diagnostic that the next bullet allows, returning the `<verdict_format>` diagnostic.
- A permission refusal is no absent payload file and takes no rerun.
- ALWAYS, when a command exits nonzero with a diagnostic that names its payload file as absent, run that command once more with the path copied from the file-write result; on a second failure, stop with the `<verdict_format>` diagnostic naming the run token.
- NEVER remove a payload file; the harness clears its scratch directory.

</payload_files>

</audit_workflow>

<verdict_format>

Return the run token, the run file, and the unchanged `spx verification run render` output; its `terminalStatus` is authoritative. Add no `PASS`, `FAIL`, or `UNKNOWN` envelope and no restated findings. After the projection, return each standing finding on its own line in the form `${CLAUDE_SKILL_DIR}/references/touched-text.md` gives, or `filed: none`.

When a command exits nonzero or a prerequisite is absent, return:

```text
BLOCKED
runToken: <exact-token-if-start-succeeded-or-not-started>
command: <exact-command-attempted>
payloadSource: <payload-file-path|none>
payloadKey: <unitId-or-finding-idempotency-key-or-none>
exitCode: <exact-exit-code-or-none>
stderr: <exact-stderr-or-none>
diagnostic: <configuration error naming the refused path, or none>
```

</verdict_format>

<failure_modes>

**Failure 1: Approved a prompt-only skill simulation**

Claude accepted an eval that asked Claude to simulate a skill verdict from inline rules while never loading or invoking the real skill. Replacing the real skill body with unrelated text did not change the eval result, so the eval proved the prompt's rubric, not the skill.

How to avoid: Step 4 checks producer coupling first. Prompt-only simulation is rule `producer-coupling` for claims about producer behavior.

**Failure 2: Treated a budget failure as behavioral evidence**

Claude read a budget-exhausted eval run and treated the failed suite as evidence the rule was wrong. The run never completed enough cases to prove behavior.

How to avoid: Step 8 separates operational failures from behavioral pass evidence. Budget, timeout, and interruption rows never prove assertion fulfillment.

**Failure 3: Rejected the run on a defect in text the changeset left alone**

Claude found a real violation in an unchanged eval artifact and recorded it on the unit, so the run rejected a changeset that did not cause the defect. Classify each finding by its location, record only findings on touched text, and return every other finding as `filed`.

**Failure 4: Moved the checkout while loading context**

Claude ran the context loader that rebases the audited branch, so the head under audit was replaced by another commit. Load the context by reading files at the head as it stands.

</failure_modes>

<success_criteria>

- Every `[eval]` assertion's suite was judged on all five gates with none skipped, and every child unit names the root.
- A gate that holds or carries findings is `audited`; a gate whose required inspection was unavailable is `incomplete` with its cause recorded, and the run seals `rejected`.
- Every recorded finding lies on touched text or records the cause of an `incomplete` gate, sits on an accepted unit, is keyed by an identifier from the evidence model, and names the assertion or eval artifact, the failed evidence property, the evidentiary gap, and how the eval could pass while the assertion is unfulfilled.
- Every standing finding carries its key, `baseRefEvidence`, and `issuesEntry`, and rejects no run.
- The `terminalStatus` derives from findings on touched text and incomplete gates alone, whatever standing findings exist.
- The checkout's head is the same before and after the audit.
- The same target, governing requirements, eval artifacts, run evidence, and base yield the same units, finding keys, and terminal status.

</success_criteria>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/evidence-model.md` — eval evidence properties, artifact taxonomy, and rejection categories.
- `${CLAUDE_SKILL_DIR}/references/touched-text.md` — touched text, finding key, severity retention, and the `filed` line.

</reference_guides>
