# Plan: complete the specification boundary

The first executable slice delivers `/spec` for an existing artifact or one unambiguous new artifact. Later slices extend that proven entry point across structural declaration work and implementation-time declaration discovery.

The first slice also makes the spec auditor apply the existing node-template shape consistently: universal audit-backed rules remain under `### Compliance`, and the heading describes claim shape without assigning the test-only compliance assertion type. The broader verification-heading migration remains tracked in `spx/21-spec-tree.enabler/35-evidence.enabler/ISSUES.md` because it requires per-file judgment across roughly 75 node specs.

## Sequence model

Every declaration-changing sequence starts with `/spec` unless another orchestrator already holds a **decision-ready artifact packet**. `/author` writes artifacts only after scope, structure, placement, and content are settled.

## Structure and ordering

This is the full composition of the authoring concern. Two ordered children use the full `[10, 99]` horizon, producing indices `39` and `69` from `10 + floor(k * 89 / 3)` for `k` in `{1, 2}`.

| Predecessor                                                                                                                          | Ordering basis    | Constraining contribution                                | Successor                                                                                                             | Required by                              | Consequence if absent                                                  | Disposition        |
| ------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------- | ------------------ |
| [`spx/21-spec-tree.enabler/54-authoring.enabler/39-artifact-authoring.enabler`](39-artifact-authoring.enabler/artifact-authoring.md) | Provider/consumer | Decision-ready artifact mutation and validation protocol | [`spx/21-spec-tree.enabler/54-authoring.enabler/69-spec-workflow.enabler`](69-spec-workflow.enabler/spec-workflow.md) | `/spec` persistence and validation steps | `/spec` duplicates artifact-writing rules or cannot persist its result | Ordered dependency |

The only child pair is ordered by this row. No same-index or unordered child pair remains.

## Selected first slice

**Demonstrable value.** A product operator invokes `/spec` with an existing artifact path or one new artifact whose type, parent, and index are uniquely determined by loaded context. The workflow gathers only unresolved content decisions, writes the artifact through `/author`, aligns affected lower declarations, validates the result, and reports the next executable handoff.

**Work queue.** The slice crosses two merge cycles and applies these existing nodes in ascending index order:

1. [`spx/21-spec-tree.enabler/35-evidence.enabler`](../35-evidence.enabler/evidence.md)
2. [`spx/21-spec-tree.enabler/54-authoring.enabler/39-artifact-authoring.enabler`](39-artifact-authoring.enabler/artifact-authoring.md)
3. [`spx/21-spec-tree.enabler/54-authoring.enabler/69-spec-workflow.enabler`](69-spec-workflow.enabler/spec-workflow.md)
4. [`spx/21-spec-tree.enabler/65-apply.enabler`](../65-apply.enabler/apply.md)
5. [`spx/21-spec-tree.enabler/68-audit.enabler/32-audit-specs.enabler`](../68-audit.enabler/32-audit-specs.enabler/audit-specs.md)

**Merge 1: stable declaration form.** Clarify that a node heading describes claim shape independently of the verification type selected by `/test`. Make `/audit-specs` accept the canonical universal audit rule under `### Compliance` consistently and add eval cases that reproduce both prior contradictory verdicts.

**Merge 2: focused `/spec` workflow.** Add artifact-class routing to `/apply` before language detection so skill-backed nodes invoke `/create-skill`, skill validation, and `skill-auditor`; language architecture, test, and code skills run only when the implementation artifact requires that language. Then make `/author` internal and packet-driven, add public `/spec`, and cover existing-artifact updates plus one unambiguous new artifact.

| Slice property       | Selected behavior                                                                                                                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actor                | Product operator changing durable Spec Tree truth                                                                                                                                                                          |
| Invocation           | `/spec <full-artifact-path-or-settled-intent>`                                                                                                                                                                             |
| Inputs               | Existing declaration context or one new artifact with uniquely determined type, parent, and index; operator-owned content decisions only where repository truth does not settle them                                       |
| Behavior             | Load context, interview unresolved content, produce a decision-ready packet, invoke `/author`, align downstream declarations, validate, and report the next handoff                                                        |
| Persisted result     | Created or modified declaration files merged through the repository lifecycle                                                                                                                                              |
| Inspection surface   | `/spec` result report, changed declaration paths, `spx spec context`, `spx spec status --format json`, and the merged changeset                                                                                            |
| First useful failure | Before mutation, report the unresolved ownership or structure decision and the exact `/decompose` or `/refactor` handoff                                                                                                   |
| Verification         | Spec audits; routing evals; `skill-auditor`; `spx validation markdown`; `spx spec status --format json`; `just check-skills`; `just docs-check`; whole-changeset review; repository full gate after agentic gates converge |

The first merge resolves the current gate evidence: identical canonical `### Compliance` audit assertions received both APPROVED and REJECTED spec-auditor verdicts, while `### Audit` received deterministic REJECTED verdicts under the current audit prompt. Merge 2 starts only after the canonical shape yields one stable APPROVED result.

| Starting state                                       | Valid sequence                                                                                                                       |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Empty tree                                           | `/spec` -> `/bootstrap` -> `/decompose spx/` -> `/author`                                                                            |
| Existing artifact, settled change                    | `/spec` -> `/contextualize` -> `/author` -> `/align`                                                                                 |
| Existing artifact, unsettled requirements            | `/spec` -> `/contextualize` -> `/interview` -> `/author` -> `/align`                                                                 |
| New artifact with unambiguous ownership              | `/spec` -> `/contextualize` -> `/interview` when needed -> `/author` -> `/align`                                                     |
| New nodes or unsettled decision ownership            | `/spec` -> `/contextualize` -> `/interview` when needed -> `/decompose` -> `/author` -> `/align`                                     |
| Structure-preserving move or re-scope                | `/spec` -> `/contextualize` -> `/interview` when needed -> `/refactor` -> `/author` -> `/align`                                      |
| Plan names nodes that do not exist                   | `/slice` -> `/spec` -> `/decompose` or `/author` -> `/slice` -> `/apply`                                                             |
| Apply finds an entailed declaration gap              | `/apply` -> `/contextualize` -> declaration-readiness check -> `/author` -> applicable declaration audit -> resume the per-node flow |
| Apply finds an unsettled product or structure choice | `/apply` -> `/spec` -> `/slice` when the queue changes -> resume `/apply`                                                            |

## Later slices

### Structural declaration routes

- Make `/decompose` return a settled structure packet and delegate every child-spec write to `/author`.
- Make `/refactor` delegate declaration rewrites to `/author` after it applies the settled structural operation.
- Route `/slice` plans with missing nodes through `/spec`, then resume selection over the updated durable map.
- Preserve `/bootstrap` as the empty-tree specialist while making `/spec` the public entry point.

### Apply declaration readiness

- Add a declaration-readiness preflight to [`spx/21-spec-tree.enabler/65-apply.enabler`](../65-apply.enabler/apply.md) before architecture begins.
- Permit `/apply` to invoke `/author` only when loaded declarations uniquely determine the artifact change.
- Route every unresolved product, scope, ownership, or structure decision through `/spec` and resume only after declarations converge.
- Make language architect skills return decision-ready ADR content to `/apply`; persist it through `/author` rather than writing ADRs through a parallel path.
- Re-run slice selection when declaration work changes the node queue or observable-value boundary.

### Surface migration and evidence

- Replace public `/author` guidance in the root router, README, contextualization failures, bootstrap routing, and skill cross-references with `/spec`.
- Mark `/author` as `user-invocable: false` and give it a passive description that states its packet contract.
- Add eval evidence for `/spec` routing across settled edits, unresolved requirements, structural changes, and apply handbacks.
- Add audit evidence that `/author`, `/decompose`, `/refactor`, and language architect skills no longer duplicate declaration orchestration or artifact-writing rules.
- Rebuild both generated plugin trees and verify Claude and Codex catalogs expose `/spec` while hiding `/author` from operator autocomplete.

## Constraints carried forward

- `/spec` owns operator interaction; `/author` owns deterministic artifact mutation.
- `/apply` may author only a change uniquely entailed by loaded declarations.
- `/decompose` remains the sole owner of node boundaries, ordering evidence, and indices.
- `/test` remains the sole owner of verification-type and assertion-type selection.
- A declaration change reaches its requested delivery boundary through the repository merge lifecycle after declaration audits and deterministic validation pass.
