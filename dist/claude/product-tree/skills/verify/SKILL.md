---
name: verify
description: >-
  ALWAYS invoke this skill when selecting or establishing evidence for spec
  assertions, decision verification rules, or a product-tree scope.
argument-hint: <full-spx-node-or-decision-path|spx/> [repair-block]
allowed-tools: Read, Glob, Grep, Edit, Write, Skill, Bash(spx validation markdown), Bash(trash:*)
---

<objective>

Validated spec assertions and decision verification rules routed to test, evaluate, probe, or audit from the verdict their real subjects can produce.

</objective>

<essential_principles>

- Validate any existing tag shape before reading the subject. An absent tag proceeds to classification; unsupported tagged input returns `blocked` with no selected verification type, specialist, or evidence shape.
- For every validated assertion, select exactly one current verification type before any specialist chooses assertion type, level, language expression, producer specialization, or verifier.
- Choose test when behavior has a deterministic verdict, evaluate when an LLM-driven producer emits structured output a deterministic grader can score, probe when only an executed observation of the running node settles the claim, and audit when no deterministic, attested, or structural verdict exists.
- Deterministic CLI state takes test even when an LLM only reads that state out for an independent comparison, and model-generated behavior takes evaluate even when a CLI exposes it.
- For spec assertions, recognize only an absent tag, `[test](path)`, `[eval](path)`, `[probe](path)`, `[audit:{rule-slug}]`, and the pathless `[audit]` a repository whose toolchain has not adopted the slug form still carries. For ADR/PDR rules, recognize an absent tag awaiting classification or the decision grammar: one assertion-type tag under `### Testing`, `[eval]` under `### Eval`, and `[audit:{rule-slug}]` with a slug unique within the record, or the pathless `[audit]` a toolchain without slug support still carries, under `### Audit`. Treat every other tag shape as invalid input without naming, aliasing, or translating it.
- Derive evidence shape from the target artifact and selected verification type regardless of specialist availability: spec test, eval, and probe assertions are path-bearing; spec audit assertions carry a rule slug and no path, or the pathless form while the toolchain admits only that; decision rules carry requirements whose implementing specs own executable evidence links. A capability gap never changes the selected route's evidence shape.
- Check the runtime skill catalog before invoking a selected path-bearing specialist — `/test`, `/eval`, or `/probe`. An absent specialist produces `capability-required`, never `routed`, and the result still names the selected specialist and evidence shape; `null` values belong only to the blocked shape.
- Keep routing acyclic: this skill composes specialists and never composes itself through them.
- Use skill `product-tree:wait-for-load` for every resource-intensive command: run each one under that skill's guard line in the foreground, and report a result only after every such line has exited.
- Keep judgment isolated: selecting audit records the audit requirement and leaves the verdict to the applicable auditor context; selecting probe records the protocol link and leaves the attested run to the Author.
- Emit one structured result per spec assertion or decision rule, and render the report table from those results alone.
- Leave every edit made before the invocation as it stands. Before the invocation first writes a file, Read its content as that file's snapshot; a rollback restores a file the invocation wrote to its snapshot, edits made before the run included, and returns a file the invocation created to absent.

</essential_principles>

<workflow>

<step name="load-context">

When `$ARGUMENTS` is empty, abort before checking markers: "A canonical product-tree target is required. Supply `spx/`, one full `spx/...` node path, or one full `spx/.../*.adr.md` or `spx/.../*.pdr.md` decision path."

Require a live `<PRODUCT_TREE_FOUNDATION>` marker. Use skill `product-tree:understand` when it is absent. For a node or product-root target, require a `<PRODUCT_TREE_CONTEXT>` marker matching the target. For a decision target, require the marker for its containing node, or `spx/` for a product-level decision. Use skill `product-tree:contextualize` for that canonical context target when its marker is absent.

Accept only `spx/`, one canonical full `spx/...` node path, or one canonical full decision path ending in `.adr.md` or `.pdr.md`. Read spec assertions from a spec target and `## Verification` rules from a decision target. For a product-root or aggregate target, walk the declared scope deterministically rather than selecting files by keyword, then partition the selected subjects by their owning canonical node or decision path. Each specialist invocation receives one supported node or decision target, never the aggregate target. Text after the target is a repair block: the verbatim result of each rejected verdict and the exact command line and output of each failed deterministic command of an earlier round on this target. Carry it into this workflow as repair input: repair every finding and failure it names within this workflow's scope, and report each one's disposition in the result.

</step>

<step name="validate-input">

Inspect only the existing tag shape before reading the subject or its verdict. For spec assertions, an absent tag or one current verification tag proceeds to classification. For decision rules, an absent tag proceeds to classification regardless of its current subsection; a present tag proceeds only when the enclosing subsection and tag match the decision grammar: `### Testing` carries exactly one of `[scenario]`, `[mapping]`, `[conformance]`, `[property]`, or `[compliance]`; `### Eval` carries `[eval]`; `### Audit` carries `[audit:{rule-slug}]` with a slug unique within the record, or the pathless `[audit]` where the toolchain has no slug support.

Any other tag shape triggers an immediate terminal return for that assertion. Return before reading the `subject` field or applying any rule from `classify-subject`, `route-specialist`, or `record-result`. Do not inspect or classify the subject, repeat the tag text, select a specialist, or derive an evidence shape. The assertion has no selected verification type. Report `blocked` with the generic reason `unsupported-tag-shape`, in the blocked result shape `record-result` defines.

</step>

<step name="classify-subject">

For each assertion, identify the real subject and the verdict it can produce:

| Subject capability                                                                 | Verification type | Current tag           |
| ---------------------------------------------------------------------------------- | ----------------- | --------------------- |
| Deterministic behavior can fail a finite command                                   | test              | `[test](path)`        |
| LLM-driven producer emits parseable structured output scored by fixed expectations | evaluate          | `[eval](path)`        |
| A claim about the running node that only an executed observation protocol settles  | probe             | `[probe](path)`       |
| Semantic constraint has no deterministic, attested, or structural verdict          | audit             | `[audit:{rule-slug}]` |

Classify the real subject's execution, not the determinism of a downstream grader. Ask whether rerunning the real subject with the same input produces the same behavior without model variance. When producing the asserted output requires an LLM, select evaluate even though fixed expectations and a deterministic grader later convert that output into pass or fail. Select test only when the behavior under assertion is itself deterministic.

The same boundary decides an assertion that names a CLI. When the CLI computes the asserted state deterministically and an LLM only reads that state out for an independent comparison, select test: the state the CLI prints is the subject. When the asserted output is generated by a model and a CLI only exposes it, select evaluate: the model's output is the subject.

Prefer the strongest reachable evidence in that order after applying this boundary. A prose-content existence check is never deterministic behavior evidence; reading authored text and asserting its wording proves only that the text was authored.

Ignore an existing current tag or decision subsection as classification authority. Input validation has already stopped every unsupported tag shape. Classify the remaining subject from its real verdict. A spec assertion whose current tag already names the selected verification type keeps that tag, is not passed to a specialist again, and reports `routed` with its existing evidence path or rule slug. A spec assertion whose current tag names another verification type has that tag removed before routing, so it reaches the selected specialist as an untagged assertion, and its row names the removed tag. For a decision rule, move it to the subsection matching the selected verification type before its specialist supplies the subsection's tag shape; that move is the rule's provisional placement. When the rule's route ends other than `routed`, restore the record to its snapshot so the rule stands where it stood before the move. The decision grammar has no probe subsection, so a decision rule whose claim only an executed observation settles stays unchanged and reports `blocked` with reason `probe-on-decision-rule`, its verification type `probe`, its exact rule text as subject text, and a `null` specialist and evidence shape; the spec that implements the rule carries its probe assertion.

</step>

<step name="route-specialist">

Route each classified assertion exactly once:

- **test** — use skill `product-tree:test`; it owns test assertion typing, execution level, source-contract checks, generic test ceremony, and language delegation. For each spec node, pass that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for test in that node so `/test` can distinguish routed work from unrelated untagged assertions. Pass each decision target separately in decision-rule mode with no assertion array so `/test` selects the rule's assertion-type tag without creating a test file or evidence link inside the ADR/PDR. An aggregate scope fans out through these per-owner invocations.
- **evaluate** — for each spec node carrying selected eval assertions, use skill `product-tree:eval` with that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for evaluate in that node. This filtered set prevents `/eval` from consuming unrelated untagged assertions. `/eval` owns product command binding and producer-specialized eval authoring. For a decision rule, preserve the implementing-spec eval requirement under `### Eval` without writing an evidence path in the decision, and use skill `product-tree:eval` with that decision target only when it supports decision-rule mode. When the required capability is unavailable, preserve the target artifact's evaluate evidence shape and report `capability-required` with the subject and required producer kind. Never pass an aggregate target to `/eval` or implement eval behavior inside this skill.
- **probe** — use skill `product-tree:probe` with the canonical node target and the exact text of every assertion selected for probe in that node when the runtime skill catalog carries it; it owns the protocol at `probes/{probe-slug}/probe.md`, and the assertion records that link with routing status `routed`. When `/probe` is not installed, preserve the probe evidence shape and report `capability-required` with the subject and the protocol path. Never author a protocol or attest a run inside this skill.
- **audit** — record the `[audit:{rule-slug}]` tag with a rule slug unique within its spec — or the pathless `[audit]` tag where the toolchain admits only that form — and the applicable isolated-verifier requirement with routing status `routed`. The pending isolated-verifier verdict does not make evidence routing blocked. Never produce the audit verdict in this workflow.

When the invocation carried a repair block, pass each specialist, after its target and assertion array, the repair items that concern that target's evidence verbatim, including items on an assertion whose current tag this workflow keeps; such an assertion's specialist is invoked for its repair items even though the assertion is not routed again.

Validate the specialist result before updating the subject. A path-bearing spec assertion requires the specialist's canonical co-located evidence path. A decision rule requires the canonical subsection and tag, while its implementing specs own evidence paths. Spec audit assertions carry no path.

</step>

<step name="record-result">

Update each successfully routed spec assertion with exactly one current tag. Update each decision rule with the selected verification subsection and that subsection's canonical tag shape. Leave blocked unsupported input unchanged.

Record one structured result per spec assertion or decision rule, with exactly these fields:

```json
{
  "subject": { "path": "<source path>", "line": 14, "text": "<the subject's exact text>" },
  "verification_type": "test",
  "specialist": "/test",
  "status": "routed",
  "evidence_shape": "path-bearing",
  "reason": "<why the subject ends in this status>"
}
```

- `subject.path` is the subject's source path, and `subject.line` is the line the subject holds in that file after the run. `subject.text` is the subject's exact text, and `null` exactly when `reason` is `unsupported-tag-shape`.
- `status` is `routed`, `capability-required`, or `blocked`.
- `verification_type` is `test`, `evaluate`, `probe`, `audit`, or `null`; `specialist` is `/test`, `/eval`, `/probe`, `isolated-verifier`, or `null`.
- A set `evidence_shape` is `path-bearing` for a spec test, eval, or probe assertion, `pathless` for a spec audit assertion, and `requirement` for a decision rule. A `capability-required` result keeps its selected route: it names the selected verification type, the absent specialist, and the evidence shape that route has, `requirement` for a decision rule included.
- A `routed` or `capability-required` result names its verification type, specialist, and evidence shape.
- `reason` names, for a `routed` result, its evidence path or requirement and any tag `classify-subject` removed; for a `capability-required` result, the absent specialist or the failed validation; and for a `blocked` result, `unsupported-tag-shape` or `probe-on-decision-rule`.
- A `blocked` result from `validate-input` carries `null` as its subject text, verification type, specialist, and evidence shape. Classification output never accompanies it.

Never report an assertion verified merely because classification completed; path-bearing evidence must exist and pass its deterministic command, and audit requires its isolated verifier.

</step>

<step name="close">

When the invocation made a durable edit, run `spx validation markdown` once after every route has ended. When it exits non-zero, roll back: restore every file the invocation wrote to its snapshot with Write, and return every file the invocation created to absent through the host's `trash` command. Then turn every `routed` result to `capability-required`, keeping its verification type, specialist, and evidence shape, with a `reason` that names the failed validation and its exit code. A file the host supplies no `trash` command for stays in place, and the `reason` of each affected result names it. Edits made before the invocation stay as they were in every rollback.

</step>

<step name="report">

Return the structured results, then render the human report from them alone, one row per result:

```text
| Subject | Verification type | Specialist | Evidence shape | Status | Reason |
```

- `Subject` holds the subject's path and line, as `<path>:<line>`, then its text when the text is not `null`.
- Every `null` value shows as an em dash, `—`.
- Each row agrees with its result field by field.

When the invocation carried a repair block, add one line per repair item after the table: the item as the block names it, and its disposition — `forwarded to /<specialist>` with that specialist's reported outcome, `repaired` for a classification or tag defect this workflow fixed, or `not-owned` with the reason when no step of this workflow or its specialists owns the fix.

Example:

```text
| Subject | Verification type | Specialist | Evidence shape | Status | Reason |
| spx/10-a.capability/a.spec.md:12 `- parse-record: ALWAYS: ...` | test | /test | path-bearing | routed | tests/<the language's compliance test file> |
| spx/20-b.capability/15-b.adr.md:9 `- atomic-save: ALWAYS: ...` | test | /test | requirement | capability-required | /test is not installed |
| spx/30-c.capability/c.spec.md:14 | — | — | — | blocked | unsupported-tag-shape |
```

</step>

</workflow>

<success_criteria>

- Every validated spec assertion or decision rule has exactly one selected current verification type derived from its real verdict; unsupported input has none and returns the terminal blocked shape.
- Test work routes through `/test`, eval work routes through `/eval`, probe work records the protocol link or the missing capability, and audit work records an isolated-verifier requirement.
- Every path-bearing spec evidence link is canonical and co-located with its governing node; decision rules carry no executable evidence links.
- Unsupported tags block the subject and receive no compatibility behavior or vocabulary in the workflow output.
- Specialist dependency direction is acyclic and no agentic verdict is produced in the authoring context.
- Every subject has one structured result with all six fields, and the report table renders from those results alone.
- After a failed route or a failed closing validation, every file holds what it held before the run.

</success_criteria>

<failure_modes>

**Claude passed an aggregate target to a specialist**

- **What happened:** Claude accepted `spx/` as a target, then forwarded that aggregate target unchanged to `/test`, whose contract accepts one node or decision.
- **Why it failed:** The router advertised a broader scope than its specialist interface could consume, so aggregate test work had no valid delegation path.
- **How to avoid:** Partition aggregate subjects by owning canonical node or decision and invoke each path-bearing specialist once per owner.

**Claude classified an unsupported tag before blocking it**

- **What happened:** Claude read the subject and selected a verification type after encountering a tag outside the current grammar.
- **Why it failed:** Classification leaked compatibility behavior and produced routing fields for input the workflow promises to leave unclassified.
- **How to avoid:** Validate tag shape first and return the terminal blocked result with null verification type, specialist, and evidence shape before reading the subject.

</failure_modes>
