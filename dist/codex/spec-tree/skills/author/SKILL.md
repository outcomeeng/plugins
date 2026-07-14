---
name: author
user-invocable: false
description: >-
  Spec Tree artifact-writing protocol invoked by parent workflows with a
  decision-ready artifact packet. Hidden from operator autocomplete and
  model-invocable by specification workflows.
argument-hint: "<decision-ready-artifact-packet>"
allowed-tools: Read, Glob, Grep, Write, Edit, Skill
---

<objective>

A canonical Spec Tree artifact written from a decision-ready packet, with changed paths and validation results returned to the calling workflow.

</objective>

<input_contract>

Read the decision-ready artifact packet from `$ARGUMENTS`. Require every field below before reading a template or writing a file:

- `operation`: `create` or `update`.
- `artifact_type`: `product`, `adr`, `pdr`, `enabler`, or `outcome`.
- `target_path`: the canonical full repository-relative artifact path under `spx/`.
- `context_target`: exact `spx/` for a top-level artifact or the canonical full `spx/...` address of the owning parent node.
- `content`: settled complete artifact content, including caller-supplied evidence links for every assertion.
- `structure_decision`: the settled placement and index decision for a create operation, or `not_applicable` for an update whose path already exists.

Reject an incomplete packet by returning the absent or invalid fields to the caller. NEVER interview the operator, infer a missing field, choose an artifact type, select an owning node, assign an index, settle content, or route unresolved structure from inside `/author`.

</input_contract>

<constraints>

- ALWAYS preserve the packet's settled operation, artifact type, target path, content, and structure decision.
- ALWAYS use the canonical foundation template for the declared artifact type.
- ALWAYS preserve an outcome's three-part output, outcome, and impact hypothesis.
- NEVER select an assertion's verification type or assertion type; every assertion arrives with its caller-supplied evidence link.
- NEVER write tests, implementation, architecture beyond the packet's decision-record content, `PLAN.md`, `ISSUES.md`, or `spx/EXCLUDE`.
- NEVER invoke `/interview`, `/decompose`, `/refactor`, `/align`, `/test`, `/apply`, `/merge`, or another delivery workflow. Return any unresolved requirement to the caller.
- NEVER summarize for the operator or recommend a next workflow. The caller owns alignment, verification, and delivery.

</constraints>

<workflow>

<step number="1" name="Validate packet">

Validate the packet against `<input_contract>` before mutation.

For `create`:

- Require a canonical collision-free `target_path` whose parent is represented by `context_target`.
- Require `structure_decision` to settle the owning directory and index where the artifact type uses one.
- Reject an existing target path.

For `update`:

- Require the target path to exist.
- Require its existing artifact kind to match `artifact_type`.
- Reject any requested move, rename, re-index, or type change; those choices belong to the calling structure workflow.

</step>

<step number="2" name="Load foundation and context">

Require a live `<SPEC_TREE_FOUNDATION>` marker. Invoke `/understand` when it is absent, then read the canonical foundation template and filled example for `artifact_type`.

Require a live `<SPEC_TREE_CONTEXT target="{context_target}">` marker. Invoke `/contextualize {context_target}` when it is absent or targets another address.

For a create operation, confirm the loaded context still shows the packet's target path and index as collision-free. For an update operation, confirm the loaded context still identifies the target's owning node. Return a discrepancy to the caller instead of revising the packet.

</step>

<step number="3" name="Validate settled content">

Validate `content` before writing:

- Structure matches the canonical product, ADR, PDR, enabler, or outcome template.
- Product truth uses atemporal voice.
- Every node, ADR, and PDR reference uses its canonical full path from `spx/`.
- Content belongs in the declared artifact type under the loaded placement constraints.
- Enabler and outcome nesting follows the foundation node-type rules.
- Every assertion carries a caller-supplied `[test]`, `[eval]`, or `[audit]` evidence link; `/author` makes no evidence classification.
- An outcome contains the three-part output, outcome, and impact hypothesis.
- ADR/PDR verification sections and tags match the canonical decision template.

Return every failed check to the caller without writing a partial artifact.

</step>

<step number="4" name="Write artifact">

For `create`, create only the directories required by `target_path` and write `content` at that exact path. For `update`, replace the existing artifact content at `target_path` without changing its path or artifact type.

Record every path created or modified during this step. Write no path absent from the packet except directories required to contain a created target.

</step>

<step number="5" name="Validate written artifact">

Read the written artifact back and repeat the content checks from Step 3 against the persisted bytes. Confirm:

- The target exists at exactly `target_path`.
- Its filename and containing directory follow the canonical artifact grammar.
- Its persisted structure, voice, references, evidence links, and placement match the validated packet.
- The recorded changed-path set contains the target artifact and no unrequested artifact.

When a post-write check fails, return `status: failed` with the exact failed checks and changed paths. Do not start repair work that requires a new product, structure, evidence, alignment, or delivery decision.

</step>

<step number="6" name="Return result">

Return this result to the calling workflow:

```text
<AUTHOR_RESULT>
status: passed | failed
operation: create | update
artifact_type: product | adr | pdr | enabler | outcome
target_path: spx/...
changed_paths:
  - spx/...
validation:
  - check: [canonical check]
    result: passed | failed
    detail: [specific evidence]
</AUTHOR_RESULT>
```

The result is an internal workflow handoff. Perform no alignment, verification orchestration, user-facing summary, commit, push, PR action, or merge.

</step>

</workflow>

<failure_modes>

**Failure 1: Claude treated direct invocation as permission to gather requirements.** `/author` asked the operator to choose an artifact type and placement because its packet was incomplete. The hidden protocol then became a second specification workflow. Avoid this by returning the incomplete packet to the caller without drafting or mutation.

**Failure 2: Claude resolved structure while writing.** `/author` inferred an owning node or assigned an index after context loading exposed ambiguity. The write bypassed `/decompose` and made placement depend on authoring heuristics. Avoid this by requiring `structure_decision` before entry and returning any context discrepancy to the caller.

**Failure 3: Claude initiated alignment and delivery.** `/author` invoked `/align` and produced operator-facing next steps after writing. The protocol absorbed responsibilities owned by its calling workflow. Avoid this by ending at `<AUTHOR_RESULT>` with changed paths and validation results.

</failure_modes>

<success_criteria>

- [ ] Frontmatter keeps `/author` hidden from operator autocomplete and model-invocable by parent workflows.
- [ ] Every write starts from a complete decision-ready packet and matching loaded context.
- [ ] Create operations use collision-free settled paths and indices; update operations target existing artifacts without structural changes.
- [ ] Persisted content matches the canonical template, atemporal voice, full-path reference, evidence-link, placement, and node-type rules.
- [ ] Outcome artifacts preserve the three-part output, outcome, and impact hypothesis.
- [ ] The caller receives exact changed paths and per-check validation results through `<AUTHOR_RESULT>`.
- [ ] `/author` performs no interview, scope choice, structure resolution, evidence classification, test or implementation work, alignment, or delivery.

</success_criteria>
