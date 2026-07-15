# PLAN: verification run migration

Agentic verification moves onto the published `spx verification run` lifecycle. Audit is the first plugin consumer in this tree: `implementation-auditor` records coverage units, findings, terminal state, and rendered projection through `spx verification run`.

## Active slice

- Audit implementation verification uses `spx verification run start`, `scope add`, `finding add`, `finish`, and `render`.
- Plugin-side audit verdict scripts are removed. SPX owns payload validation, terminal projection rendering, and authoritative finding counts.
- The repository SPX floor and CI pin are `0.6.15`, the published release this slice depends on.

## Later slices

- Reconcile review persistence with the same verification-run surface after audit implementation is runnable.
- Remove remaining review-only `spx journal` helpers when review has an equivalent `spx verification run` path.
- Reconcile artifact-type auditors with verification-run persistence after implementation audit proves the contract.
