# Verification

PROVIDES Outcome Engineering verification governance for verdict modes, verification types, assertion evidence, and verifier responsibilities
SO THAT methodology specs, plugin implementations, runtime tools, and language standards
CAN share one verification model across deterministic tests, deterministic evals, agentic audits, agentic reviews, and validation gates

## Assertions

### Compliance

- ALWAYS: verification terminology, verdict modes, verification types, assertion tags, and local-versus-CI responsibility derive from `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: specs outside this subtree that implement verification behavior cite `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` when they rely on its taxonomy, dispatcher, scope, or verifier-responsibility rules ([audit])
- ALWAYS: agentic-verification governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/21-agentic-verification.enabler/agentic-verification.md` when it concerns the agent-adapter contract for invoking a coding-agent runtime on behalf of a verification surface ([audit])
- ALWAYS: test-verification governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/test-verification.md` when it concerns deterministic test evidence, test-infrastructure ownership, or test-evidence audit semantics ([audit])
- ALWAYS: eval-verification governance lives under `spx/31-outcomeeng.enabler/31-verification.enabler/31-eval-verification.enabler/eval-verification.md` when it concerns deterministic eval evidence, eval-harness ownership, or eval-evidence audit semantics ([audit])
- NEVER: a plugin-specific verification spec redefines the verification type set, verdict modes, assertion tags, or verifier responsibility split locally ([audit])
