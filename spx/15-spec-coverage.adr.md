# Spec Coverage Scope

CONSTRAINS the evidence the Assertions of every checked-in marketplace plugin carry
TO at least one Node for each plugin, test evidence for executable code, eval evidence for LLM-driven skill behavior that emits a structured verdict, and audit evidence for skill design or intent
SO THAT the Product Tree maps every plugin and each Assertion is verified by the one mechanism able to falsify it

## Verification

### Audit: evidence selection

- every-plugin-node: Every checked-in marketplace plugin has at least one Node in the Product Tree; a plugin directory that no Node governs fails the audit.
- code-test-evidence: An Assertion about executable code carries test evidence; an audit verdict standing in for that evidence fails the audit.
- llm-eval-evidence: An Assertion about LLM-driven skill behavior whose producing skill emits a structured verdict whose shape the eval declares carries eval evidence, scored against curated cases through the eval harness `spx/13-infrastructure.enabler/25-eval-harness.enabler/eval-harness.md` governs.
- intent-audit-evidence: An Assertion about skill design or intent that no structural verdict can falsify carries audit evidence.
- no-markdown-structure-tests: No automated test of a pure-skill plugin parses markdown structure; such a test fails the audit, because formatting-shaped evidence proves nothing about behavior.
- structural-eval-grading: No eval grades its cases by interpreting free-form LLM prose; the grader reads structural verdict fields against per-eval expected structures.
- cli-state-readout: Deterministic CLI state takes test evidence even when an LLM only reads that state out for an independent comparison, and model-generated behavior takes eval evidence even when a CLI exposes it; an Assertion that takes the other evidence fails the audit.
