# Ledger entry-point tested coverage

The cases executed against `scripts/derive_ledger.py`, with the inputs each
uses. Read this when judging what the entry point is proven to do; the parent
skill's `<ledger_derivation>` carries the invocation contract an operation needs.

Each case below fails when the behavior it covers is disabled or inverted.

## Reachability and result shape

- the empty document
  `{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}`
  exits zero with empty stderr and writes a result carrying exactly `ledger`,
  `schemaVersion`, and `status: "succeeded"`, whose ledger carries exactly the
  ten keys named in `<ledger_derivation>` with empty collections, an empty
  running spend, and zero wall time

## Derivation from populated inputs

- one mail record whose body carries a `ledger` object holding a pass, head,
  verdict, decision, failure, finding provenance, read, spend, and wall time
  places each value in its own collection under that record's mail provenance,
  totals the spend under its currency, and totals the duration
- a body carrying no `ledger` object — unparseable text, a JSON scalar, a JSON
  array, an object with other keys, and event fields carried at the top level
  rather than under `ledger` — derives the ledger of a document with no record
- every declared read cause records one read carrying that cause and payload
- amounts across several currencies total per currency at their own decimal
  precision, and durations across mail records and journal runs total together
- journal runs repeating one `runToken` derive the ledger of their first
  occurrences alone
- every entry names the mail store `id` or `runToken` that carried it

## Rejections

Each exits two with empty stderr and a result carrying exactly `detail`,
`schemaVersion`, and `status: "invalid-input"`:

- `schemaVersion` `2`, whose detail names the schema-version field and the
  required version
- the malformed stdin document `{`, whose detail is non-empty
- a read whose cause lies outside the declared set, whose detail names the
  admitted causes and the offending record's position
- an argument vector other than `derive`, whose detail names the required
  operation and every token received
