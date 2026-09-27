---
name: verify
description: >-
  ALWAYS invoke this skill when selecting or establishing evidence for spec
  assertions, decision verification rules, or a spec-tree scope.
argument-hint: <full-spx-node-or-decision-path|spx/>
allowed-tools: Read, Glob, Grep, Edit, Skill
---

<objective>

Validated spec assertions and decision verification rules routed to test, evaluate, probe, or audit from the verdict their real subjects can produce, each reported as one structured routing result.

</objective>

<essential_principles>

- Validate any existing tag shape before reading the subject. An absent tag proceeds to classification; unsupported tagged input returns the blocked result, with reason `unsupported-tag-shape` and no selected verification type, specialist, or evidence shape.
- For every validated assertion, select exactly one current verification type before any specialist chooses assertion type, level, language expression, producer specialization, or verifier.
- Classify the behavior under assertion. Choose test when it has a deterministic verdict, including deterministic CLI state an LLM only reports for an independent comparison; evaluate when model-generated behavior is itself under assertion and emits structured output a deterministic grader can score, even when a CLI exposes it; probe when only an executed observation of the running node settles the claim, and audit when no deterministic, attested, or structural verdict exists.
- For spec assertions, recognize only an absent tag, `[test](path)`, `[eval](path)`, `[probe](path)`, `[audit:{rule-slug}]`, and the pathless `[audit]` a repository whose toolchain has not adopted the slug form still carries. For ADR/PDR rules, recognize an absent tag awaiting classification or the decision grammar: one assertion-type tag under `### Testing`, `[eval]` under `### Eval`, and `[audit]` under `### Audit`. Treat every other tag shape as invalid input without naming, aliasing, or translating it.
- Derive evidence shape from the target artifact and selected verification type regardless of specialist availability: spec test, eval, and probe assertions are path-bearing; spec audit assertions carry a rule slug and no path, or the pathless form while the toolchain admits only that; decision rules carry requirements whose implementing specs own executable evidence links. A capability gap never changes the selected route's evidence shape.
- Check the runtime skill catalog before invoking a selected path-bearing specialist — `/test`, `/eval`, or `/probe`. An absent specialist produces `capability-required`, never `routed`, and the result still names the selected specialist and evidence shape; `null` values belong only to the blocked result.
- Keep routing one-directional: invoke each selected specialist once per owning target and never re-enter this workflow from a specialist result.
- Keep judgment out of routing: selecting audit records the audit requirement and never produces the audit verdict; selecting probe records the protocol link and never executes or attests the run.

</essential_principles>

<workflow>

<step name="load-context">

When `$ARGUMENTS` is empty, abort before checking markers: "A canonical spec-tree target is required. Supply `spx/`, one full `spx/...` node path, or one full `spx/.../*.adr.md` or `spx/.../*.pdr.md` decision path."

Require a live `<SPEC_TREE_FOUNDATION>` marker. When it is absent: Use skill `spec-tree:understand`. For a node or product-root target, require a `<SPEC_TREE_CONTEXT>` marker matching `$ARGUMENTS`. For a decision target, require the marker for its containing node, or `spx/` for a product-level decision. When that marker is absent: Use skill `spec-tree:contextualize`. Pass that canonical context target.

Accept only `spx/`, one canonical full `spx/...` node path, or one canonical full decision path ending in `.adr.md` or `.pdr.md`. Read spec assertions from a spec target and `## Verification` rules from a decision target. For a product-root or aggregate target, walk the declared scope deterministically rather than selecting files by keyword, then partition the selected subjects by their owning canonical node or decision path. Each specialist invocation receives one supported node or decision target, never the aggregate target.

</step>

<step name="validate-input">

Inspect only the existing tag shape before reading the subject or its verdict. For spec assertions, an absent tag or one current verification tag proceeds to classification. For decision rules, an absent tag proceeds to classification regardless of its current subsection; a present tag proceeds only when the enclosing subsection and tag match the decision grammar: `### Testing` carries exactly one of `[scenario]`, `[mapping]`, `[conformance]`, `[property]`, or `[compliance]`; `### Eval` carries `[eval]`; `### Audit` carries `[audit]`.

Any other tag shape ends processing of that assertion immediately. Stop before reading the `subject` field, and skip `classify-subject` and `route-specialist` for it. Do not inspect or classify the subject, repeat the tag text, select a specialist, or derive an evidence path or requirement. The assertion has no selected verification type; its only output is the blocked result `record-result` declares: `status` `blocked`, `reason` `unsupported-tag-shape`, and `verification_type`, `specialist`, and `evidence_shape` null.

</step>

<step name="classify-subject">

For each assertion, identify the real subject and the verdict it can produce:

| Subject capability                                                                 | Verification type | Current tag           |
| ---------------------------------------------------------------------------------- | ----------------- | --------------------- |
| Deterministic behavior can fail a finite command                                   | test              | `[test](path)`        |
| LLM-driven producer emits parseable structured output scored by fixed expectations | evaluate          | `[eval](path)`        |
| A claim about the running node that only an executed observation protocol settles  | probe             | `[probe](path)`       |
| Semantic constraint has no deterministic, attested, or structural verdict          | audit             | `[audit:{rule-slug}]` |

Classify the behavior under assertion: deterministic CLI state uses test even when an LLM provides its readout; use evaluate when model-generated behavior is itself being evaluated, including through a CLI. A readout reports existing state for a test's independent comparison without interpreting its meaning or deciding the verdict. Fixed expectations and a deterministic grader alone do not make model-generated behavior deterministic.

Prefer the strongest reachable evidence in that order after applying this boundary. A prose-content existence check is never deterministic behavior evidence; reading authored text and asserting its wording proves only that the text was authored.

Ignore an existing current tag or decision subsection as classification authority. Input validation has already stopped every unsupported tag shape. Classify the remaining subject from its real verdict. For a decision rule, move it to the subsection matching the selected verification type before its specialist supplies the subsection's tag shape.

</step>

<step name="route-specialist">

Route each classified assertion exactly once:

- **test** — when the runtime skill catalog carries the test specialist: Use skill `spec-tree:test`. It owns test assertion typing, execution level, source-contract checks, generic test ceremony, and language delegation. For each spec node, pass that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for test in that node, so the test specialist distinguishes routed work from unrelated untagged assertions. Pass each decision target separately in decision-rule mode with no assertion array, so it selects the rule's assertion-type tag without creating a test file or evidence link inside the ADR/PDR. An aggregate scope fans out through these per-owner invocations. When the catalog does not carry it, preserve the test evidence shape and report `capability-required` with the subject and the target the test specialist would receive. Never author test evidence in this workflow.
- **evaluate** — when the runtime skill catalog carries the eval specialist: Use skill `spec-tree:eval`. For each spec node carrying selected eval assertions, pass that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for evaluate in that node; this filtered set keeps the eval specialist from consuming unrelated untagged assertions. That specialist owns product command binding and producer-specialized eval authoring. For a decision rule, preserve the implementing-spec eval requirement under `### Eval` without writing an evidence path in the decision, and pass that decision target only when the specialist supports decision-rule mode. When the catalog does not carry it, preserve the target artifact's evaluate evidence shape and report `capability-required` with the subject and required producer kind. Never pass an aggregate target to the eval specialist, and never implement eval behavior in this workflow.
- **probe** — when the runtime skill catalog carries the probe specialist: Use skill `spec-tree:probe`. Pass the canonical node target and the exact text of every assertion selected for probe in that node. That specialist owns the protocol at `probes/{probe-slug}/probe.md`, and the assertion records that link with routing status `routed`. When the catalog does not carry it, preserve the probe evidence shape and report `capability-required` with the subject and the protocol path. Never author a protocol, and never execute or attest a run, in this workflow.
- **audit** — record the `[audit:{rule-slug}]` tag with a rule slug unique within its spec — or the pathless `[audit]` tag where the toolchain admits only that form — and the applicable isolated-verifier requirement with routing status `routed`. The pending isolated-verifier verdict does not make evidence routing blocked. Never produce the audit verdict in this workflow.

Validate the specialist result before updating the subject. A path-bearing spec assertion requires the specialist's canonical co-located evidence path. A decision rule requires the canonical subsection and tag, while its implementing specs own evidence paths. Spec audit assertions carry no path.

</step>

<step name="record-result">

Update each successfully routed spec assertion with exactly one current tag. Update each decision rule with the selected verification subsection and that subsection's canonical tag shape. Leave blocked unsupported input unchanged, and write no tag, subsection, or evidence link for it.

Emit one structured result per subject. The structured result is the output contract, carrying exactly these fields:

- `verification_type` — `test`, `evaluate`, `probe`, `audit`, or `null`
- `specialist` — `/test`, `/eval`, `/probe`, `isolated-verifier`, or `null`
- `status` — `routed`, `capability-required`, or `blocked`
- `evidence_shape` — `path-bearing` for a test, evaluate, or probe route, `pathless` for an audit route, or `null`
- `reason` — a concise string naming why the route holds, including the evidence path, protocol path, required producer kind, or requirement the route reported

A `capability-required` result keeps the selected route intact: the specialist is the absent path-bearing specialist (`/test`, `/eval`, or `/probe`) and the evidence shape is `path-bearing`; `isolated-verifier` and `pathless` belong to audit alone. A blocked result carries `status` `blocked`, the literal `reason` `unsupported-tag-shape`, and `null` in `verification_type`, `specialist`, and `evidence_shape`, and no classification output accompanies it. Never report an assertion verified merely because classification completed; path-bearing evidence must exist and pass its deterministic command, and audit requires its isolated verifier.

Render the human report as a table from those same results, one row per result: a subject column, then one column per field. The subject names a blocked assertion as unsupported input without repeating its tag text. Each `null` field renders as an em dash. The table adds and drops no field, so the structured results and the table are two surfaces of one output.

Example:

```text
| Subject | verification_type | specialist | status | evidence_shape | reason |
| Node A deterministic rule | test | /test | routed | path-bearing | deterministic parser output; evidence at tests/{canonical-evidence-filename} |
| Node B producer rule | evaluate | /eval | capability-required | path-bearing | model-generated structured output; /eval absent from the runtime skill catalog |
| Node C unsupported input | — | — | blocked | — | unsupported-tag-shape |
```

</step>

</workflow>

<success_criteria>

- Every validated spec assertion or decision rule has exactly one selected current verification type derived from its real verdict; unsupported input has none and returns the blocked result with reason `unsupported-tag-shape`.
- Every subject yields exactly one structured result carrying `verification_type`, `specialist`, `status`, `evidence_shape`, and `reason`, and the human table renders from those results with an em dash for each `null` field.
- Test, eval, and probe work each either routes to its specialist or records `capability-required` with the evidence shape preserved; audit work records an isolated-verifier requirement.
- Every path-bearing spec evidence link is canonical and co-located with its governing node; decision rules carry no executable evidence links.
- Unsupported tags block the subject and receive no compatibility behavior or vocabulary in the workflow output.
- Each selected specialist is invoked once per owning target, this workflow is never re-entered from a specialist result, and it produces no agentic verdict and no attested run.

</success_criteria>

<failure_modes>

**Claude passed an aggregate target to a specialist**

- **What happened:** Claude accepted `spx/` as this workflow's target, then forwarded that aggregate target unchanged to the test specialist, whose contract accepts one node or decision.
- **Why it failed:** The router advertised a broader scope than its specialist interface could consume, so aggregate test work had no valid delegation path.
- **How to avoid:** Partition aggregate subjects by owning canonical node or decision and invoke each path-bearing specialist once per owner.

**Claude classified an unsupported tag before blocking it**

- **What happened:** Claude read the subject and selected a verification type after encountering a tag outside the current grammar.
- **Why it failed:** Classification leaked compatibility behavior and produced routing fields for input the workflow promises to leave unclassified.
- **How to avoid:** Validate tag shape first and return the terminal blocked result with null verification type, specialist, and evidence shape before reading the subject.

</failure_modes>
