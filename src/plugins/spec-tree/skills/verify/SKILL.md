---
name: verify
description: >-
  ALWAYS invoke this skill when selecting or establishing evidence for spec
  assertions, decision verification rules, or a spec-tree scope.
argument-hint: <full-spx-node-or-decision-path|spx/>
allowed-tools: Read, Glob, Grep, Edit, {{! tool('use_skill') !}}, Bash(spx validation markdown:*)
---

<objective>

Validated spec assertions and decision verification rules routed to test, evaluate, probe, or audit from the verdict their real subjects can produce, each reported as one structured routing result.

</objective>

<essential_principles>

- Read no subject before its tag shape validates; unsupported input takes the blocked result and nothing else.
- Select exactly one current verification type for every validated subject before any specialist chooses assertion type, level, language expression, producer specialization, or verifier.
- Classify the behavior under assertion, never the interface that exposes it: deterministic CLI state is test even when an LLM only reports that state for an independent comparison, and model-generated behavior is evaluate even when a CLI exposes it. A readout reports existing state without interpreting its meaning or deciding the verdict; fixed expectations and a deterministic grader alone never make model-generated behavior deterministic.
- A subject keeps an edit only when its route ends `routed` and the closing validation exits 0; every other ending leaves the subject exactly as the run found it.
- Route one-directionally: invoke each selected specialist once per owning target, and never re-enter this workflow from a specialist result.
- Construct no evidence and render no verdict: the selected specialist owns test evidence, eval evidence, or the probe protocol and its attested run, and the isolated verifier owns the audit verdict.

</essential_principles>

<workflow>

<step name="load-context">

When `$ARGUMENTS` is empty, abort: "A canonical spec-tree target is required. Supply `spx/`, one full `spx/...` node path, or one full `spx/.../*.adr.md` or `spx/.../*.pdr.md` decision path." Abort with the same message for any target other than `spx/`, one canonical full `spx/...` node path, or one canonical full decision path ending in `.adr.md` or `.pdr.md`.

Require a live `<SPEC_TREE_FOUNDATION>` marker. When it is absent: Use skill `spec-tree:understand`. For a node or product-root target, require a `<SPEC_TREE_CONTEXT>` marker matching `$ARGUMENTS`. For a decision target, require the marker for its containing node, or `spx/` for a product-level decision. When that marker is absent: Use skill `spec-tree:contextualize`. Pass that canonical context target. When either skill aborts, report its abort unchanged and stop.

Read the assertions of the node's own spec file from a node target and the `## Verification` rules from a decision target. The product-root target `spx/` is the aggregate target: Glob `spx/**/*.md`, drop every path under `spx/local/` or under a `tests/`, `evals/`, `probes/`, or `knowledge/` directory, and keep exactly the subject files — the root product spec (`spx/*.spec.md`, or the prior `spx/*.product.md`), every node spec whose basename is its directory's slug followed by `.spec.md` (or the prior `.md`), and every `*.adr.md` and `*.pdr.md` file. No other file contributes a subject: `ISSUES.md`, `PLAN.md`, and outcome records carry none. Take spec assertions from the spec files and `## Verification` rules from the decision files, in path order, then partition the subjects by their owning canonical node or decision path. Each specialist invocation receives one supported node or decision target, never the aggregate target.

Before the first edit to any subject, record each subject's exact text and position — file, section, and subsection — as the run's snapshot.

</step>

<step name="validate-input">

Inspect only the existing tag shape before reading the subject or its verdict. A spec assertion proceeds to classification when it carries no tag or exactly one of `[test](path)`, `[eval](path)`, `[probe](path)`, `[audit:{rule-slug}]`, or the pathless `[audit]`. A decision rule proceeds when it carries no tag, regardless of its current subsection, or when its enclosing subsection and tag match the decision grammar: `### Testing` carries exactly one of `[scenario]`, `[mapping]`, `[conformance]`, `[property]`, or `[compliance]`; `### Eval` carries `[eval]`; `### Audit` carries `[audit]`.

Any other tag shape ends processing of that subject immediately. Stop before reading its `subject` field, and skip `classify-subject` and `route-specialist` for it. Do not inspect or classify the subject, repeat, name, alias, or translate the tag text, select a specialist, or derive an evidence path or requirement. Its only output is the blocked row of `record-result`.

</step>

<step name="classify-subject">

For each validated subject, identify the real subject and the verdict it can produce:

| Subject capability                                                                 | Verification type | Spec assertion tag                              |
| ---------------------------------------------------------------------------------- | ----------------- | ----------------------------------------------- |
| Deterministic behavior can fail a finite command                                   | test              | `[test](path)`                                  |
| LLM-driven producer emits parseable structured output scored by fixed expectations | evaluate          | `[eval](path)`                                  |
| A claim about the running node that only an executed observation protocol settles  | probe             | `[probe](path)`                                 |
| Semantic constraint has no deterministic, attested, or structural verdict          | audit             | `[audit:{rule-slug}]` or `[audit]`, per `audit` |

Apply the classification boundary in `<essential_principles>`, then prefer the strongest reachable evidence in the table's order. A prose-content existence check is never deterministic behavior evidence; reading authored text and asserting its wording proves only that the text was authored.

Ignore an existing current tag or decision subsection as classification authority, and classify each subject from its real verdict alone; `route-specialist` decides whether that tag stays.

</step>

<step name="route-specialist">

Route each classified subject exactly once, one owning target — the canonical node or decision path from `load-context` — at a time.

First settle, without editing any subject, every route that ends before a specialist runs. A path-bearing route — test, evaluate, or probe — composes its specialist only when the runtime skill catalog lists that specialist's entry, `spec-tree:test`, `spec-tree:eval`, or `spec-tree:probe`; never assume one is installed. An absent entry ends the route `capability-required`. A decision target reaches a path-bearing specialist only in decision-rule mode, and a specialist supports that mode only when its catalog entry's argument contract names an ADR/PDR decision target, as the test specialist's does. Resolve each decision rule selected for a path-bearing route in this order:

1. Probe — the decision grammar has no probe subsection, so the route ends `capability-required` with a reason stating that its implementing spec owns the probe protocol.
2. The catalog does not list the selected specialist — the route ends `capability-required`.
3. The selected specialist's argument contract names no decision target — the route ends `capability-required` with a reason naming the missing decision-rule mode. When the eval specialist's argument contract names only node targets, every decision rule selected for evaluate ends this way.

A route settled here edits nothing: its subject keeps its existing tag and reports the reason its row names.

Every continuing route applies one input rule. A tag belongs to a verification type as the classification table's tag column and the decision grammar state it: a spec assertion's `[test](path)`, `[eval](path)`, `[probe](path)`, or `[audit:{rule-slug}]` and `[audit]`; a decision rule's place in `### Testing`, `### Eval`, or `### Audit` together with that subsection's tag, since `validate-input` admits a tagged rule only with its own subsection's tag. A tag of the selected type stays, with its path, so evidence a subject already links is never discarded. A tag of another type is replaced: before the owning target's first specialist runs, the spec assertion loses that tag, or the decision rule is placed untagged in its selected subsection, and the selected specialist, or the audit step, then writes the selected type's tag. An untagged decision rule outside its selected subsection is placed there untagged at the same point, because a specialist in decision-rule mode reads only that subsection. The snapshot from `load-context` holds every removed tag and every moved rule.

- **test** — Input rule: the route hands its specialist every subject selected for test — untagged, already tagged for test, or tagged for another type — keeps a test tag, and replaces another type's tag with a test tag. Use skill `spec-tree:test`. It owns test assertion typing, execution level, source-contract checks, generic test ceremony, and language delegation, and it writes the `[test](path)` link or the `### Testing` rule's assertion-type tag.
- **evaluate** — Input rule: the route hands its specialist every subject selected for evaluate — untagged, already tagged for evaluate, or tagged for another type — keeps an evaluate tag, and replaces another type's tag with an evaluate tag. Use skill `spec-tree:eval`. It owns product command binding and producer-specialized eval authoring, and it writes the `[eval](path)` link or the `### Eval` rule's `[eval]` tag.
- **probe** — Input rule: the route hands its specialist every subject selected for probe — untagged, already tagged for probe, or tagged for another type — keeps a probe tag, and replaces another type's tag with a probe tag. Use skill `spec-tree:probe`. It owns the protocol at `probes/{probe-slug}/probe.md`, and it writes the assertion's `[probe](path)` link to it.
- **audit** — Input rule: the route hands its specialist every subject selected for audit — untagged, already tagged for audit, or tagged for another type — keeps an audit tag, and replaces another type's tag with an audit tag. The specialist is the isolated verifier, which this workflow never runs, so this step writes the tag itself, and only into a subject that carries none: in a spec that already carries a slugged audit tag, write `[audit:{rule-slug}]` with a rule slug unique within its spec; in a spec whose audit tags are all pathless, write `[audit]`. In a spec with no audit tag, write the slug form and run `spx validation markdown`: replace it with the pathless `[audit]` when that run reports the slug tag as invalid, and keep the slug form on every other exit, leaving the closing validation in `record-result` to decide the run. A decision rule placed in `### Audit` carries `[audit]`. Record the applicable isolated-verifier requirement; the pending isolated-verifier verdict does not make the route blocked.

Each path-bearing specialist runs once per owning target and receives the argument form the test specialist declares. For a spec node, pass the canonical node target followed, when any exists, by a JSON array of the exact current text of every subject selected for that route that is untagged when the specialist runs, a subject whose tag the input rule removed included. A subject that kept its tag of the selected type is absent from the array, because the specialist's own extraction reads it through that tag. For a decision, pass the canonical decision target alone, in decision-rule mode; the specialist reads only its selected subsection.

Placing a decision rule in a subsection moves it to the end of that subsection unless it already sits there, creating the subsection under `## Verification` in the order `### Testing`, `### Eval`, `### Audit` when it is absent.

Validate each subject once every specialist for its owning target has returned. A path-bearing spec assertion requires a specialist result naming it and exactly one tag of its selected type whose path is canonical and co-located with its governing node. A decision rule requires its selected subsection and exactly one canonical tag of that subsection, while its implementing specs own evidence paths. A specialist that aborts, errors, or returns no result for a subject fails this validation. Then restore from the snapshot every subject of the owning target whose result is not `routed` — a tag the input rule removed, a rule it placed, and any edit a specialist made to that subject — and remove a subsection this run created that the restore leaves empty.

</step>

<step name="record-result">

The run's durable edits are every change a route made to a subject — a tag written or removed, a subsection placement, or an evidence link — whether this workflow or a specialist wrote it. The specialist's own evidence artifacts stay with that specialist. After every route has ended, run `spx validation markdown` once. Exit 0 keeps the durable edits. Any other exit, including a command that fails to start, restores every edited subject from the snapshot and removes every subsection this run created that the restore leaves empty; each subject whose route had ended `routed` then takes the validation row below, and every other subject keeps its row.

Every invocation ends in exactly one of these outcomes:

| Invocation terminal path                                   | Output                                                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| `$ARGUMENTS` empty or not a canonical target               | The `load-context` abort message; no subject result                    |
| `spec-tree:understand` or `spec-tree:contextualize` aborts | That skill's abort, reported unchanged; no subject result              |
| The target carries no spec assertion or decision rule      | An empty result set; the report states that the target has no subjects |
| The target carries subjects                                | One structured result per subject, from the table below                |

Every subject yields exactly one result; the first matching row decides it:

| Subject terminal path                                                                            | `status`              | `verification_type` | `specialist`                                      | `evidence_shape` | `reason`                                          |
| ------------------------------------------------------------------------------------------------ | --------------------- | ------------------- | ------------------------------------------------- | ---------------- | ------------------------------------------------- |
| Unsupported tag shape                                                                            | `blocked`             | `null`              | `null`                                            | `null`           | `unsupported-tag-shape`, exactly                  |
| A route a later row would end `routed`; the closing `spx validation markdown` exits other than 0 | `capability-required` | selected type       | selected specialist, `isolated-verifier` included | selected shape   | the failed validation and its exit                |
| Audit, for a spec assertion or a decision rule                                                   | `routed`              | `audit`             | `isolated-verifier`                               | `pathless`       | the recorded isolated-verifier requirement        |
| Decision rule selected for probe                                                                 | `capability-required` | `probe`             | `/probe`                                          | `path-bearing`   | the implementing spec's ownership of the protocol |
| Test, evaluate, or probe; the catalog does not list the specialist                               | `capability-required` | selected type       | `/test`, `/eval`, or `/probe`                     | `path-bearing`   | the absent catalog entry and the route's target   |
| Decision rule; the selected specialist declares no decision-rule mode                            | `capability-required` | selected type       | `/test` or `/eval`                                | `path-bearing`   | the missing decision-rule mode                    |
| Test, evaluate, or probe; the specialist result fails validation                                 | `capability-required` | selected type       | `/test`, `/eval`, or `/probe`                     | `path-bearing`   | the failed check                                  |
| Test, evaluate, or probe; the specialist result passes validation                                | `routed`              | selected type       | `/test`, `/eval`, or `/probe`                     | `path-bearing`   | the evidence or protocol path                     |

Emit one structured result per subject. The structured result is the output contract, carrying exactly these fields:

- `verification_type` — `test`, `evaluate`, `probe`, `audit`, or `null`
- `specialist` — `/test`, `/eval`, `/probe`, `isolated-verifier`, or `null`
- `status` — `routed`, `capability-required`, or `blocked`
- `evidence_shape` — `path-bearing` for a test, evaluate, or probe route, `pathless` for an audit route, or `null`; a decision rule reports its implementing spec's evidence shape
- `reason` — a concise string naming what the row's `reason` column states; the blocked result's is the exact literal

A `capability-required` result keeps the selected route intact: it names the selected verification type, the selected specialist — `isolated-verifier` included — and that route's evidence shape, because a capability gap or a failed check never changes the route. `null` belongs to the blocked result alone, and no classification output accompanies a blocked result. Never report a subject verified merely because classification completed. A `routed` result states that the route's tag, and a path-bearing route's evidence path, passed the validation in `route-specialist` and the closing `spx validation markdown`; it never states that the evidence passes. Running that evidence belongs to the specialist and to deterministic verification outside this workflow, and an audit subject awaits its isolated verifier.

Render the human report as a table from those same results, one row per result: a subject column, then one column per field. The subject names a blocked assertion as unsupported input without repeating its tag text. Each `null` field renders as an em dash. The table adds and drops no field, so the structured results and the table are two surfaces of one output.

Example:

```text
| Subject | verification_type | specialist | status | evidence_shape | reason |
| --- | --- | --- | --- | --- | --- |
| Node A deterministic rule | test | /test | routed | path-bearing | deterministic parser output; evidence at tests/{canonical-evidence-filename} |
| Node B producer rule | evaluate | /eval | capability-required | path-bearing | model-generated structured output; /eval absent from the runtime skill catalog |
| Node C semantic rule | audit | isolated-verifier | capability-required | pathless | spx validation markdown exited 1; prior text restored from the snapshot |
| Node D unsupported input | — | — | blocked | — | unsupported-tag-shape |
```

</step>

</workflow>

<success_criteria>

- Every invocation ends in exactly one declared invocation outcome, and every subject yields exactly one structured result from the first matching subject row, carrying `verification_type`, `specialist`, `status`, `evidence_shape`, and `reason`; the human table renders from those results with an em dash for each `null` field.
- Every validated spec assertion or decision rule has exactly one selected current verification type derived from its real verdict; unsupported input has none and returns the blocked result with reason `unsupported-tag-shape`.
- Every `capability-required` result names its selected verification type, specialist — `isolated-verifier` included — and evidence shape.
- Every subject a route continues with carries, before its specialist runs or its audit tag is written, either no tag or a tag of its selected type: a tag of the selected type stays with its path, and a tag of another type is replaced, identically on the test, evaluate, probe, and audit routes.
- A decision rule a path-bearing specialist reads sits in its selected subsection before that specialist runs — untagged unless it already sat there with that subsection's tag — and returns to its recorded text and position when its route ends other than `routed`.
- The run's durable edits stand only when the closing `spx validation markdown` exits 0; any other exit leaves every subject as the snapshot recorded it and every formerly routed subject reporting `capability-required`.
- Every path-bearing spec evidence link that stands is canonical and co-located with its governing node; decision rules carry no executable evidence links.
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
