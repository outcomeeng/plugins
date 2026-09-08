---
name: verify
description: >-
  ALWAYS invoke this skill when selecting or establishing evidence for spec
  assertions, decision verification rules, or a spec-tree scope.
argument-hint: <full-spx-node-or-decision-path|spx/>
allowed-tools: Read, Glob, Grep, Edit, Skill
---

<objective>

Validated spec assertions and decision verification rules routed to test, evaluate, probe, or audit from the verdict their real subjects can produce.

</objective>

<essential_principles>

- Validate any existing tag shape before reading the subject. An absent tag proceeds to classification; unsupported tagged input returns `blocked` with no selected verification type, specialist, or evidence shape.
- For every validated assertion, select exactly one current verification type before any specialist chooses assertion type, level, language expression, producer specialization, or verifier.
- Choose test when behavior has a deterministic verdict, evaluate when an LLM-driven producer emits structured output a deterministic grader can score, probe when only an executed observation of the running node settles the claim, and audit when no deterministic, attested, or structural verdict exists.
- For spec assertions, recognize only an absent tag, `[test](path)`, `[eval](path)`, `[probe](path)`, `[audit:{rule-slug}]`, and the pathless `[audit]` a repository whose toolchain has not adopted the slug form still carries. For ADR/PDR rules, recognize an absent tag awaiting classification or the decision grammar: one assertion-type tag under `### Testing`, `[eval]` under `### Eval`, and `[audit]` under `### Audit`. Treat every other tag shape as invalid input without naming, aliasing, or translating it.
- Derive evidence shape from the target artifact and selected verification type regardless of specialist availability: spec test, eval, and probe assertions are path-bearing; spec audit assertions carry a rule slug and no path, or the pathless form while the toolchain admits only that; decision rules carry requirements whose implementing specs own executable evidence links. A capability gap never changes the selected route's evidence shape.
- Check the runtime skill catalog before invoking a selected path-bearing specialist — `/test`, `/eval`, or `/probe`. An absent specialist produces `capability-required`, never `routed`, and the result still names the selected specialist and evidence shape; `null` values belong only to the blocked shape.
- Keep routing acyclic: `/verify` invokes specialists; specialists never invoke `/verify`.
- Keep judgment isolated: selecting audit records the audit requirement and leaves the verdict to the applicable auditor context; selecting probe records the protocol link and leaves the attested run to the Author.

</essential_principles>

<workflow>

<step name="load-context">

When `$ARGUMENTS` is empty, abort before checking markers: "A canonical spec-tree target is required. Supply `spx/`, one full `spx/...` node path, or one full `spx/.../*.adr.md` or `spx/.../*.pdr.md` decision path."

Require a live `<SPEC_TREE_FOUNDATION>` marker. Invoke `/understand` when it is absent. For a node or product-root target, require a `<SPEC_TREE_CONTEXT>` marker matching `$ARGUMENTS`. For a decision target, require the marker for its containing node, or `spx/` for a product-level decision. Invoke `/contextualize` for that canonical context target when its marker is absent.

Accept only `spx/`, one canonical full `spx/...` node path, or one canonical full decision path ending in `.adr.md` or `.pdr.md`. Read spec assertions from a spec target and `## Verification` rules from a decision target. For a product-root or aggregate target, walk the declared scope deterministically rather than selecting files by keyword, then partition the selected subjects by their owning canonical node or decision path. Each specialist invocation receives one supported node or decision target, never the aggregate target.

</step>

<step name="validate-input">

Inspect only the existing tag shape before reading the subject or its verdict. For spec assertions, an absent tag or one current verification tag proceeds to classification. For decision rules, an absent tag proceeds to classification regardless of its current subsection; a present tag proceeds only when the enclosing subsection and tag match the decision grammar: `### Testing` carries exactly one of `[scenario]`, `[mapping]`, `[conformance]`, `[property]`, or `[compliance]`; `### Eval` carries `[eval]`; `### Audit` carries `[audit]`.

Any other tag shape triggers an immediate terminal return for that assertion. Return before reading the `subject` field or applying any rule from `classify-subject`, `route-specialist`, or `record-result`. Do not inspect or classify the subject, repeat the tag text, select a specialist, or derive an evidence shape. The assertion has no selected verification type. Report `blocked` with the generic reason `unsupported-tag-shape`; in structured output, set `verification_type`, `specialist`, and `evidence_shape` to `null`.

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

Prefer the strongest reachable evidence in that order after applying this boundary. A prose-content existence check is never deterministic behavior evidence; reading authored text and asserting its wording proves only that the text was authored.

Ignore an existing current tag or decision subsection as classification authority. Input validation has already stopped every unsupported tag shape. Classify the remaining subject from its real verdict. For a decision rule, move it to the subsection matching the selected verification type before its specialist supplies the subsection's tag shape.

</step>

<step name="route-specialist">

Route each classified assertion exactly once:

- **test** — invoke `/test`; it owns test assertion typing, execution level, source-contract checks, generic test ceremony, and language delegation. For each spec node, pass that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for test in that node so `/test` can distinguish routed work from unrelated untagged assertions. Pass each decision target separately in decision-rule mode with no assertion array so `/test` selects the rule's assertion-type tag without creating a test file or evidence link inside the ADR/PDR. An aggregate scope fans out through these per-owner invocations.
- **evaluate** — for each spec node carrying selected eval assertions, invoke `/eval` with that canonical node target plus a JSON array containing the exact text of every untagged assertion selected for evaluate in that node. This filtered set prevents `/eval` from consuming unrelated untagged assertions. `/eval` owns product command binding and producer-specialized eval authoring. For a decision rule, preserve the implementing-spec eval requirement under `### Eval` without writing an evidence path in the decision, and invoke `/eval` with that decision target only when it supports decision-rule mode. When the required capability is unavailable, preserve the target artifact's evaluate evidence shape and report `EVAL_CAPABILITY_REQUIRED` with the subject and required producer kind. Never pass an aggregate target to `/eval` or implement eval behavior inside `/verify`.
- **probe** — invoke `/probe` with the canonical node target and the exact text of every assertion selected for probe in that node when the runtime skill catalog carries it; it owns the protocol at `probes/{probe-slug}/probe.md`, and the assertion records that link with routing status `routed`. When `/probe` is not installed, preserve the probe evidence shape and report `capability-required` with the subject and the protocol path. Never author a protocol or attest a run inside `/verify`.
- **audit** — record the `[audit:{rule-slug}]` tag with a rule slug unique within its spec — or the pathless `[audit]` tag where the toolchain admits only that form — and the applicable isolated-verifier requirement with routing status `routed`. The pending isolated-verifier verdict does not make evidence routing blocked. Never produce the audit verdict in this workflow.

Validate the specialist result before updating the subject. A path-bearing spec assertion requires the specialist's canonical co-located evidence path. A decision rule requires the canonical subsection and tag, while its implementing specs own evidence paths. Spec audit assertions carry no path.

</step>

<step name="record-result">

Update each successfully routed spec assertion with exactly one current tag. Update each decision rule with the selected verification subsection and that subsection's canonical tag shape. Leave blocked unsupported input unchanged; its owning workflow must correct invalid input before invoking `/verify` again.

Report one row per subject:

```text
| Subject | Verification type | Specialist | Evidence path or requirement | Status |
```

Use `routed`, `capability-required`, or `blocked` as status. A `capability-required` row keeps the selected route intact: the specialist is the absent path-bearing specialist (`/test`, `/eval`, or `/probe`) and the evidence shape is `path-bearing`; `isolated-verifier` and `pathless` belong to audit alone. Never report an assertion verified merely because classification completed; path-bearing evidence must exist and pass its deterministic command, and audit requires its isolated verifier.

Example:

```text
| Subject | Verification type | Specialist | Evidence path or requirement | Status |
| Node A deterministic rule | test | /test | tests/test_rule.compliance.l1.py | routed |
| Node B producer rule | evaluate | /eval | structured eval capability required | capability-required |
| Node C unsupported input | — | — | — | blocked |
```

For the terminal unsupported-input guard, record no verification type, specialist, or evidence shape. Classification output must never accompany that blocked result.

</step>

</workflow>

<success_criteria>

- Every validated spec assertion or decision rule has exactly one selected current verification type derived from its real verdict; unsupported input has none and returns the terminal blocked shape.
- Test work routes through `/test`, eval work routes through `/eval`, probe work records the protocol link or the missing capability, and audit work records an isolated-verifier requirement.
- Every path-bearing spec evidence link is canonical and co-located with its governing node; decision rules carry no executable evidence links.
- Unsupported tags block the subject and receive no compatibility behavior or vocabulary in the workflow output.
- Specialist dependency direction is acyclic and no agentic verdict is produced in the authoring context.

</success_criteria>

<failure_modes>

**Claude passed an aggregate target to a specialist**

- **What happened:** Claude accepted `spx/` as a `/verify` target, then forwarded that aggregate target unchanged to `/test`, whose contract accepts one node or decision.
- **Why it failed:** The router advertised a broader scope than its specialist interface could consume, so aggregate test work had no valid delegation path.
- **How to avoid:** Partition aggregate subjects by owning canonical node or decision and invoke each path-bearing specialist once per owner.

**Claude classified an unsupported tag before blocking it**

- **What happened:** Claude read the subject and selected a verification type after encountering a tag outside the current grammar.
- **Why it failed:** Classification leaked compatibility behavior and produced routing fields for input the workflow promises to leave unclassified.
- **How to avoid:** Validate tag shape first and return the terminal blocked result with null verification type, specialist, and evidence shape before reading the subject.

</failure_modes>
