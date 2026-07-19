---
name: verify
description: >-
  ALWAYS invoke this skill when selecting or establishing evidence for spec
  assertions or a spec-tree scope.
argument-hint: <full-spx-node-path|spx/>
allowed-tools: Read, Glob, Grep, Write, Edit, Skill
---

<objective>

Validated spec assertions routed to test, evaluate, or audit evidence from the verdict their real subjects can produce, with unsupported input blocked before classification and specialist work invoked for every selected path.

</objective>

<essential_principles>

- Validate the existing tag shape before reading the subject. Unsupported input returns `blocked` with no selected verification type, specialist, or evidence shape.
- For every validated assertion, select exactly one current verification type before any specialist chooses assertion type, level, language expression, producer specialization, or verifier.
- Choose test when behavior has a deterministic verdict, evaluate when an LLM-driven producer emits structured output a deterministic grader can score, and audit when no deterministic or structural verdict exists.
- Recognize only `[test](path)`, `[eval](path)`, and `[audit]`. Treat every other tag shape as invalid input without naming, aliasing, or translating it.
- Derive evidence shape from the selected verification type regardless of specialist availability: test and evaluate are path-bearing; audit is pathless. A capability gap never changes the selected type's evidence shape.
- Check the runtime skill catalog before invoking a selected path-bearing specialist. An absent specialist produces `capability-required`, never `routed`.
- Keep routing acyclic: `/verify` invokes specialists; specialists never invoke `/verify`.
- Keep judgment isolated: selecting audit records a pathless audit requirement and leaves the verdict to the applicable auditor context.

</essential_principles>

<workflow>

<step name="load-context">

When `$ARGUMENTS` is empty, abort before checking markers: "A canonical spec-tree target is required. Supply `spx/` or one full `spx/...` node path."

Require a live `<SPEC_TREE_FOUNDATION>` marker and a `<SPEC_TREE_CONTEXT>` marker matching `$ARGUMENTS`. Invoke `/understand` or `/contextualize` when either marker is absent.

Accept only `spx/` or one canonical full `spx/...` node path. Read the target spec assertions. For a product-root or aggregate target, walk the declared scope deterministically rather than selecting files by keyword.

</step>

<step name="validate-input">

Inspect only the existing tag shape before reading the subject or its verdict. An absent tag or one current tag proceeds to classification.

Any other tag shape triggers an immediate terminal return for that assertion. Return before reading the `subject` field or applying any rule from `classify-subject`, `route-specialist`, or `record-result`. Do not inspect or classify the subject, repeat the tag text, select a specialist, or derive an evidence shape. The assertion has no selected verification type. Report `blocked` with the generic reason `unsupported-tag-shape`; in structured output, set `verification_type`, `specialist`, and `evidence_shape` to `null`.

</step>

<step name="classify-subject">

For each assertion, identify the real subject and the verdict it can produce:

| Subject capability                                                                 | Verification type | Current tag    |
| ---------------------------------------------------------------------------------- | ----------------- | -------------- |
| Deterministic behavior can fail a finite command                                   | test              | `[test](path)` |
| LLM-driven producer emits parseable structured output scored by fixed expectations | evaluate          | `[eval](path)` |
| Semantic constraint has no deterministic or structural verdict                     | audit             | `[audit]`      |

Classify the real subject's execution, not the determinism of a downstream grader. Ask whether rerunning the real subject with the same input produces the same behavior without model variance. When producing the asserted output requires an LLM, select evaluate even though fixed expectations and a deterministic grader later convert that output into pass or fail. Select test only when the behavior under assertion is itself deterministic.

Prefer the strongest reachable evidence in that order after applying this boundary. A prose-content existence check is never deterministic behavior evidence; reading authored text and asserting its wording proves only that the text was authored.

Ignore an existing current tag as classification authority. Input validation has already stopped every unsupported tag shape. Classify the remaining assertion from its subject and write only the selected current tag.

</step>

<step name="route-specialist">

Route each classified assertion exactly once:

- **test** — invoke `/test`; it owns test assertion typing, execution level, source-contract checks, generic test ceremony, and language delegation.
- **evaluate** — invoke `/eval`; it owns product command binding and producer-specialized eval authoring. When `/eval` is unavailable, preserve evaluate's path-bearing evidence shape and report `EVAL_CAPABILITY_REQUIRED` with the assertion and required producer kind. Never implement eval behavior inside `/verify`.
- **audit** — record the pathless `[audit]` tag and the applicable isolated-verifier requirement with routing status `routed`. The pending isolated-verifier verdict does not make evidence routing blocked. Never produce the audit verdict in this workflow.

Validate the specialist result before updating the assertion. A path-bearing type requires the specialist's canonical co-located evidence path. Audit remains pathless.

</step>

<step name="record-result">

Update each successfully routed assertion with exactly one current tag. Leave blocked unsupported input unchanged; its owning workflow must correct invalid input before invoking `/verify` again.

Report one row per subject:

```text
| Subject | Verification type | Specialist | Evidence path or requirement | Status |
```

Use `routed`, `capability-required`, or `blocked` as status. Never report an assertion verified merely because classification completed; path-bearing evidence must exist and pass its deterministic command, and audit requires its isolated verifier.

For the terminal unsupported-input guard, record no verification type, specialist, or evidence shape. Classification output must never accompany that blocked result.

</step>

</workflow>

<success_criteria>

- Every validated assertion has exactly one selected current verification type derived from its real verdict; unsupported input has none and returns the terminal blocked shape.
- Test work routes through `/test`, eval work routes through `/eval`, and audit work records an isolated-verifier requirement.
- Every path-bearing evidence link is canonical and co-located with its governing node.
- Unsupported tags block the subject and receive no compatibility behavior or vocabulary in the workflow output.
- Specialist dependency direction is acyclic and no agentic verdict is produced in the authoring context.

</success_criteria>
