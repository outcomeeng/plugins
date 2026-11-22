# Issues: Audit Assertions

## The payload-accepted Conformance Assertion names no contract file

Evidence: `audit-assertions.md` declares `payload-accepted` under `### Test.Conformance: payload floor` and links `tests/test_audit_assertions_payload.conformance.l3.py`. That test records scope units through the pinned published SPX CLI and compares each unit's audit class and audit kind with `ASSERTION_AUDIT_CLASS` and `ASSERTION_AUDIT_KIND` from `outcomeeng/validation/assertion_audit_contract.py`; it reads no contract file. The Node holds no `contracts/` directory. A Conformance Assertion checks one Node's output against a contract a file defines, and the Node that owns that contract keeps the file in its `contracts/` directory, where the Assertion links it.

Impact: the row's type promises validation against a contract that no file states, so no reader or Verifier can check the test against a contract, and the Assertion's type does not match its Evidence.

Settlement condition: the Node keeps the contract file of the scope payload in its `contracts/` directory and the row links it, or the row is retyped and its test carries the type of its new heading.
