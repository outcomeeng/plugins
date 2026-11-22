---
id: 01a1281a-5c35-7339-ac52-207f93675c4c
malleability: spec
---

# Audit Assertions

PROVIDES the isolated Agentic verdict on each Audit Assertion of one node's spec, judged against the subject the Assertion names and recorded through `spx verification run`
SO THAT an Applier, a merge gate and a status claim
CAN read an Audit result from a sealed run

## Assertions

### Audit: judgment and recording

- judges-audit-assertions: ALWAYS: `/audit-assertions` judges every row that stands under an `Audit` group heading of the target spec, each by its leading slug, against the subject that row names, and judges no row under another group heading
- read-only-context: ALWAYS: before any audit phase, `/audit-assertions` loads read-only at the audited snapshot the complete Walk to the target spec node as the work — every ancestor spec from the root, at each level along the path every sibling spec and each Decision Record indexed below the child the path continues through, every `ISSUES.md` along the path, the published contracts of the target's immediate children, the target's own Decision Records and spec, its Knowledge `index.md` and its Outcome record — then each decision a loaded spec or decision cites from another subtree, once; it runs no command that fetches, rebases, or moves the checkout, so the audit changes no checkout state
- run-recording: ALWAYS: `/audit-assertions` starts one `spx verification run` before judging, records, when the spec has an Audit Assertion, one root scope unit for the audited node spec, keyed by the audited spec path and carrying no parent and no designator, and one child scope unit per Audit Assertion, keyed by its leading slug, with the root as its parent and with every finding on its child unit, and records no unit for a spec with no Audit Assertion, seals the run, and returns the run token, the run file, and the rendered projection
- no-declaration-judgment: NEVER: `/audit-assertions` judges how an assertion is declared or selected; declaration form and heading fitness belong to the spec audit
- thin-wrapper: ALWAYS: `assertion-auditor` passes the raw target spec path and a fixed run-driver identity to its skill, starts without the caller's authoring history, and relays the run token, the run file, and the rendered projection unchanged, or the complete blocked diagnostic
- touched-text-only: ALWAYS: `/audit-assertions` rejects only on touched text under [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md), returns each other finding as `filed`, and approves when no finding on touched text exists
- unit-shape: ALWAYS: the assertion audit of a spec with an Audit Assertion records the root unit and every child unit with audit class `spec` and audit kind `spec` and the audited node spec path as the unit subject, and places the Assertion's leading slug in the unit key and in the message of every finding on a child unit
- payload-files: ALWAYS: the assertion audit records each start input, scope-add payload and finding-add payload through a file written with the file-write tool in the session scratch directory and passed by path as the payload-path rule of `/skill-standards` states, adds each scope unit as its own scope-add command that stops the audit on a nonzero exit other than the one rerun the payload-path rule allows, teaches no heredoc, no pipe-built payload and no statement that its payloads never travel through a scratch file, and the assertion auditor's definition grants the file-write tool and no stage that builds a payload in the shell
- launched-run-seals: Given a node spec with an Audit Assertion, when a launched assertion auditor audits it under the pinned published SPX floor, then the run seals with terminal status `approved` or `rejected`

### Test.Scenario: sealed run

- [sealed-run-accepted](tests/test_audit_assertions_sealed_run.scenario.l3.py):
  - Given the scope payload shape that the assertion audit states
  - When a run records a unit of that shape and a finding on that unit through the pinned published SPX CLI and finishes
  - Then the CLI accepts every payload, seals the run, and returns the unit key and the terminal status the finding derives

### Test.Conformance: payload floor

- [payload-accepted](tests/test_audit_assertions_payload.conformance.l3.py):
  - Given a scope payload whose audit class is `spec`, whose audit kind is `spec`, and whose subject is a node spec path
  - When the pinned published SPX floor checks that payload's class and kind
  - Then the floor accepts the payload
