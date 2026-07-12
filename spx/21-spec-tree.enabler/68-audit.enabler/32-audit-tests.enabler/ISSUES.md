# Issues - Audit Tests

Known follow-ups for the audit-tests node. Coordination note; not spec truth.

## Deterministic evidence bypasses the skill-driven producer

Test-evidence audit on branch checkpoint
`bf7b434a56ffc443b1590d45e1142b47b1c869df` rejected the node's scenario and
property evidence:

- `outcomeeng_testing/harnesses/audit_tests.py` constructs preclassified
  `AuditCase` values and verifies `audit_case_verdict` responses instead of
  making the real `test-evidence-auditor` and `spec-tree:audit-tests` producer
  classify source and test artifacts.
- The coupling-taxonomy property verifies category membership and count without
  proving that the real producer emits the required distinct audit responses.

The affected evidence files and harness are unchanged from `origin/main`. The
operator chose to defer their redesign so the adversarial test-evidence contract
can proceed without expanding this changeset or modifying eval artifacts.

Governing workflow: `spec-tree:test`, `python:test-python`,
`python:python-test-standards`, and `python:audit-python-tests`.

Revisit condition: before these deterministic tests are cited as passing evidence
for the scenario and property assertions, replace or remove the parallel
preclassified model and prove the assertions through the real skill-driven
producer. Any replacement evidence must execute the actual auditor over real
source-to-test-infrastructure chains and must receive test-evidence audit approval.
