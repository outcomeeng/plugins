---
name: eval
description: >-
  ALWAYS invoke this skill before writing or repairing structured-eval evidence for a spec assertion, running eval cases to convergence, or deciding whether eval evidence is current.
argument-hint: <full-spx-node-or-decision-path> [selected-assertions-json-array] [repair-block]
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, request_user_input
---

<objective>
Product Tree `[eval]` evidence that is bound to the repository's own eval command, authored for its producer kind, current against its producer, converged one case at a time, and aggregated into one deterministic suite result.
</objective>

<prerequisites>

Use skill `product-tree:eval-evidence-standards`. If that skill is unavailable, report the missing skill and stop before writing eval evidence.

</prerequisites>

<essential_principles>

- `/eval-evidence-standards` owns what makes eval evidence sound. Where this skill and that standard both speak to coupling, oracle independence, alignment, falsifiability, or run evidence, the standard governs.
- Embed no product runner package, task recipe, path, authentication mode, or model runner. Every such value comes from the repository's instructions and overlays at run time.
- Raise no cost, quota, worker, retry, timeout, or budget ceiling. A run that a default ceiling stops is reported with the exact command and ceiling, and the operator decides.
- Use skill `product-tree:wait-for-load` for every resource-intensive command: run each one under that skill's guard line in the foreground, and report a result only after every such line has exited.
- Write an eval verdict from deterministic scoring only. A model never grades its own producer's output.

</essential_principles>

<workflow>

<step name="load_context">

**Step 1: Load tree context**

Abort when `$ARGUMENTS` is empty: "A canonical spec node or ADR/PDR target is required." Otherwise parse one canonical target followed by an optional JSON array of exact assertion texts already selected for evaluate. Preserve each array string verbatim. Reject malformed JSON or non-string members before reading the target. A decision target uses decision-rule mode and accepts no array. Text after the target and the optional array is a repair block: the verbatim result of each rejected verdict and the exact command line and output of each failed deterministic command of an earlier round. Repair every finding and failure it names, and report each one's disposition.

Check for `<PRODUCT_TREE_FOUNDATION>` and `<PRODUCT_TREE_CONTEXT>` markers. When either is absent: Use skill `product-tree:understand`. Use skill `product-tree:contextualize`.

</step>

<step name="extract_assertions">

**Step 2: Extract eval assertions**

For a spec target, take the assertions already tagged `[eval](path)` plus the exact untagged assertions supplied in the array. Ignore every other untagged assertion. For each, record the assertion text, the eval link and whether `eval.toml` resolves, and the producer the assertion claims emits the structured verdict.

For a decision target, take only `### Eval` rules, record each, and write no eval artifact: the implementing spec owns the executable evidence link.

</step>

<step name="bind_product_command">

**Step 3: Bind the product command**

Resolve the repository's commands for running one eval suite, one eval case, and one node's evals from the root instruction file's product commands and any `spx/local/` overlay. Use those commands exactly, with their default ceilings. When the repository declares no eval command, report the gap and stop before running anything.

</step>

<step name="route_producer">

**Step 4: Author by producer kind**

Classify each assertion's producer as a skill, agent, classifier, script, or command. Author the prompt, cases, and `eval.toml` for that producer kind under `/eval-evidence-standards`. A producer defect an eval exposes returns to the workflow that owns the producer; never edit the producer to make a case pass.

</step>

<step name="inspect_freshness">

**Step 5: Inspect freshness**

For each suite, compare the newest passing row in `history.jsonl` with the current `eval.toml`, prompt, cases, threshold, and producer. A row is current when its recorded commit is an ancestor of HEAD and the changes since it are the suite's own history appends only. Treat unavailable provenance as stale. A current suite needs no run; a stale or absent one proceeds to Step 6.

</step>

<step name="converge_serially">

**Step 6: Converge one case at a time**

Run one case with the bound single-case command and read its deterministic result. On a failing case, decide from the standard whether the case, the prompt, or the producer is at fault, repair the faulting authored artifact within this skill's scope, and rerun that case until it passes or the cause is a producer defect to return. Move to the next case only after the current one converges. Run a case alone; do not raise worker parallelism.

</step>

<step name="aggregate">

**Step 7: Aggregate**

After every case has converged, run the bound suite command once. Take its pass fraction against the declared threshold as the suite result; a run stopped by a budget, timeout, or infrastructure failure is incomplete evidence, never a failing or passing verdict. Update the spec's `[eval](path)` link for each newly evidenced assertion.

</step>

<step name="report">

**Step 8: Report**

```markdown
| # | Assertion | Producer kind | Suite  | Freshness | Result |
| - | --------- | ------------- | ------ | --------- | ------ |
| 1 | {text}    | skill         | {path} | current   | Pass   |
| 2 | {text}    | script        | {path} | stale     | Fail   |
```

</step>

</workflow>

<success_criteria>

- Every eval command run is the repository's own bound command, run at its default ceilings under the wait-for-load guard line.
- Every assertion's suite is authored for its classified producer kind under `/eval-evidence-standards`.
- Every suite's freshness is judged from its history against the current definition and producer before any run.
- Every suite result comes from serial one-case convergence followed by one deterministic aggregate run.
- No product runner, recipe, path, authentication mode, or model appears in this skill.

</success_criteria>
