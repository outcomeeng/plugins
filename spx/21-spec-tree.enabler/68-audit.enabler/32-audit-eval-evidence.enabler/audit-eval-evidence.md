# Audit Eval Evidence Delivery

PROVIDES the Spec Tree plugin's `audit-eval-evidence` skill and `eval-evidence-auditor` wrapper implementing the portable eval-evidence audit methodology
SO THAT the main conversation
CAN dispatch isolated verdicts over `[eval]` evidence packages

## Assertions

### Compliance

- ALWAYS: `audit-eval-evidence` implements `spx/31-outcomeeng.enabler/31-verification.enabler/31-audit-verification.enabler/54-audit-eval-evidence.enabler/audit-eval-evidence.md` without redefining producer coupling, oracle independence, alignment, falsifiability, or run-evidence rules ([audit])
- ALWAYS: `audit-eval-evidence` is an agent-preloaded audit skill with a main-conversation dispatch gate ([audit])
- ALWAYS: the `eval-evidence-auditor` agent is a thin wrapper that carries no independent audit policy beyond invoking the audit skill ([audit])
