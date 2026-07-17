# Audit Eval Evidence

PROVIDES an audit methodology for deciding whether eval evidence proves the behavior claimed by an `[eval]` spec assertion
SO THAT artifact-type eval-evidence auditors across delivery plugins
CAN reject suites that grade a copied prompt simulation instead of the real producing skill, agent, classifier, script, or command

## Assertions

### Compliance

- ALWAYS: audit producer coupling first — the suite exercises or loads the actual producer named by the assertion ([audit])
- ALWAYS: reject a prompt-only simulation when changing or removing the real producer would leave the eval passing ([audit])
- ALWAYS: check oracle independence, assertion alignment, falsifiability, and current run evidence after producer coupling passes ([audit])
- ALWAYS: findings identify the exact eval or producer artifact and the failed evidence property ([audit])
- NEVER: run eval suites, tests, coverage, validation, or other deterministic verification inside the agentic eval-evidence audit ([audit])
