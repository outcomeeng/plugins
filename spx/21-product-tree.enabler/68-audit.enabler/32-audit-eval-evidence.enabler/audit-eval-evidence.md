---
id: 01a0ebba-5f66-7099-bada-7c7269176a77
malleability: spec
---

# Audit Eval Evidence

PROVIDES an audit methodology verifying eval evidence proves the behavior a spec's Evaluate Assertions claim
SO THAT product-tree projects can rely on eval runs as evidence about the producing skill, agent, or classifier rather than about a copied prompt simulation
CAN reject eval suites that would still pass when the real producer is broken or absent

## Assertions

### Audit: eval evidence audit

- standalone-skill: ALWAYS: the `audit-eval-evidence` skill is an agent-preloaded audit skill that names no caller and stays invocable on its own; the isolation from Author context an audit verdict requires binds the Author context per [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), never this skill
- thin-wrapper: ALWAYS: the `eval-evidence-auditor` agent is a thin wrapper that carries no independent audit policy beyond invoking `product-tree:audit-eval-evidence` with the raw target and its run-driver identity, and relays the run token, the run file, and the rendered projection unchanged
- read-only-context: ALWAYS: before any audit phase, `/audit-eval-evidence` loads read-only at the audited snapshot the complete Walk to the target spec node as the work — every ancestor spec from the root, at each level along the path every sibling spec and each Decision Record indexed below the child the path continues through, every `ISSUES.md` along the path, the published contracts of the target's immediate children, the target's own Decision Records and spec, its Knowledge `index.md` and its Outcome record — then each decision a loaded spec or decision cites from another subtree, once; it runs no command that fetches, rebases, or moves the checkout, so the audit changes no checkout state
- run-recording: ALWAYS: `/audit-eval-evidence` records its audit through `spx verification run` on a file scope anchored on the node's spec file: one root unit with `auditKind` `eval-evidence` and one child per gate. A passing gate is `audited`, a failing gate is `audited` with a finding, and a gate it cannot decide is `incomplete` with its cause recorded, so the run seals `rejected`. It returns the run token, the run file, and the rendered projection, or a blocked diagnostic when spx refuses a recorded payload or the finish
- producer-coupling-first: ALWAYS: audit the evidence of each Evaluate Assertion for producer coupling first — a suite that does not exercise or load the actual producing skill, agent, classifier, or script cannot prove that producer's behavior
- no-prompt-only-simulation: ALWAYS: reject prompt-only simulations for claims about skill, agent, or classifier behavior — changing the real producer to unrelated text must make the evidence fail or the eval has no evidentiary value
- later-gates: ALWAYS: check oracle independence, assertion alignment, falsifiability, and run evidence after producer coupling passes
- touched-text-only: ALWAYS: the eval-evidence auditor rejects only on touched text under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no touched finding exists
- no-deterministic-runs: NEVER: run eval suites, tests, coverage, validation, or any other deterministic verification inside the eval-evidence audit — the main agent and CI own deterministic runs, and the audit judges evidence quality by reading artifacts
- record-as-judged: ALWAYS: `/audit-eval-evidence` records the root unit as soon as the run starts, each gate unit as soon as the judgment of its gate completes, and each finding on touched text as soon as it is raised and its unit is recorded, so no unit or finding waits for the judgment of a later unit
