# Verification

PROVIDES Outcome Engineering verification governance for verdict modes, verification types, assertion evidence, and verifier responsibilities
SO THAT methodology specs, plugin implementations, runtime tools, and language standards
CAN share one verification model across deterministic tests, deterministic evals, agentic audits, agentic reviews, and validation gates

## Assertions

### Compliance

- ALWAYS: verification terminology, verdict modes, verification types, assertion tags, and local-versus-CI responsibility derive from `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` ([audit])
- ALWAYS: specs outside this subtree that implement verification behavior cite `spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md` when they rely on its taxonomy, dispatcher, scope, or verifier-responsibility rules ([audit])
- ALWAYS: test verification governs deterministic test evidence, test-infrastructure ownership, and assertion-flow ownership without redefining the verification taxonomy ([audit])
- ALWAYS: audit verification governs portable agentic judgment methods by artifact type, while plugin-specific wrappers, persistence, and result delivery remain implementation concerns outside methodology governance ([audit])
- NEVER: a plugin-specific verification spec redefines the verification type set, verdict modes, assertion tags, or verifier responsibility split locally ([audit])
