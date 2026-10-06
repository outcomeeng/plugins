# Fixture changesets

Each fixture describes one consumer repository and one committed changeset that is about to go through `/merge` on the GitHub-PR transport. Deterministic verification passes on every fixture. The repository's `spx/local/merging.md` overlay is absent in every fixture.

## Fixture 1

The repository has a Product Tree under `spx/`. The changeset changes these paths:

- `spx/20-billing.capability/billing.spec.md`
- `spx/20-billing.capability/tests/test_invoice.scenario.l1.py` (a `[test]` file linked from `billing.spec.md`)
- `src/billing/invoice.py` (imported by that linked test)
- `spx/24-tax.capability/evals/rounding/cases.jsonl` (an `[eval]` artifact linked from `spx/24-tax.capability/tax.spec.md`)

Front matter of each touched node's spec:

- `spx/20-billing.capability/billing.spec.md`: `id: 01a0ebba-0000-7000-8000-000000000001`, `malleability: spec`
- `spx/24-tax.capability/tax.spec.md`: `id: 01a0ebba-0000-7000-8000-000000000002`, `malleability: spec`

## Fixture 2

The repository has a Product Tree under `spx/`. The changeset changes these paths:

- `spx/20-billing.capability/tests/test_invoice.scenario.l1.py` (a `[test]` file linked from `billing.spec.md`)
- `src/billing/invoice.py` (imported by that linked test)
- `spx/30-ledger.capability/tests/test_posting.mapping.l1.py` (a `[test]` file linked from `spx/30-ledger.capability/ledger.spec.md`)
- `src/ledger/posting.py` (imported by that linked test)

Front matter of each touched node's spec:

- `spx/20-billing.capability/billing.spec.md`: `id: 01a0ebba-0000-7000-8000-000000000001`, `malleability: spec`
- `spx/30-ledger.capability/ledger.spec.md`: `id: 01a0ebba-0000-7000-8000-000000000003` and no other field

## Fixture 3

The repository has no `spx/` directory. Its root agent guide declares `make verify` as its verify command. The changeset changes these paths:

- `src/server/routes.py`
- `tests/test_routes.py`
- `README.md`
