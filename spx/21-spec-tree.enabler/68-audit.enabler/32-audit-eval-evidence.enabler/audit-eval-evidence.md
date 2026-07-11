# Audit Eval Evidence

PROVIDES an audit methodology verifying eval evidence proves the behavior claimed by `[eval]` spec assertions
SO THAT spec-tree projects can rely on eval runs as evidence about the producing skill, agent, or classifier rather than about a copied prompt simulation
CAN reject eval suites that would still pass when the real producer is broken or absent

## Assertions

### Compliance

- ALWAYS: the `audit-eval-evidence` skill is an agent-preloaded audit skill with a main-conversation dispatch gate ([audit])
- ALWAYS: the `eval-evidence-auditor` agent is a thin wrapper that carries no independent audit policy beyond invoking `spec-tree:audit-eval-evidence` ([audit])
- ALWAYS: audit `[eval]` evidence for producer coupling first — a suite that does not exercise or load the actual producing skill, agent, classifier, or script cannot prove that producer's behavior ([audit])
- ALWAYS: reject prompt-only simulations for claims about skill, agent, or classifier behavior — changing the real producer to unrelated text must make the evidence fail or the eval has no evidentiary value ([audit])
- ALWAYS: check oracle independence, assertion alignment, falsifiability, and run evidence after producer coupling passes ([audit])
- NEVER: run eval suites, tests, coverage, validation, or any other deterministic verification inside the eval-evidence audit — the main agent and CI own deterministic runs, and the audit judges evidence quality by reading artifacts ([audit])
