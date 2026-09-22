# Ledger entry-point tested coverage

The cases executed against `${SKILL_DIR}/scripts/derive_ledger.py`, with
the inputs each uses. Read this when judging what the entry point is proven to
do; the parent skill's `<ledger_derivation>` carries the invocation contract an
operation needs.

Each case below fails when the behavior it covers is disabled or inverted.

## Reachability and result shape

- the empty document
  `{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}`
  exits zero with empty stderr and writes a result carrying exactly `ledger`,
  `schemaVersion`, and `status: "succeeded"`, whose ledger carries exactly the
  keys named in `<ledger_derivation>` with empty collections, an empty running
  spend, and a zero wall time

## Derivation from populated inputs

- one mail record whose body carries a `ledger` object holding a pass, head,
  verdict, decision, failure, finding provenance, read, spend, and wall time
  places each value in its own collection under that record's mail provenance,
  totals the spend under its currency, and totals the duration
- a body carrying no `ledger` object — unparseable text, a `ledger` key whose
  value is an integer literal wider than the interpreter converts, a JSON
  scalar, a JSON array, an object with other keys, and event fields carried at
  the top level rather than under `ledger` — derives the ledger of a document
  with no record
- every declared read cause records one read carrying that cause and payload
- amounts across several currencies total per currency at their own decimal
  precision, and durations across mail records and journal runs total together,
  over amounts and durations whose precision ranges from absent through widths
  no double represents to coefficients longer than the default decimal context
  carries, each total compared against a sum taken with no rounding
- both totals are emitted as decimal text carrying every digit of the amount
  and duration the record supplied
- mail records repeating one store `id` and journal runs repeating one
  `runToken` derive the ledger of their first occurrences alone
- a finding provenance or read one record lists several times is recorded once
  per occurrence
- every entry names the mail store `id` or `runToken` that carried it

## Rejections

Each exits two with empty stderr and a result carrying exactly `detail`,
`schemaVersion`, and `status: "invalid-input"`:

- `schemaVersion` `2`, whose detail names the schema-version field and the
  required version
- the malformed stdin document `{`, whose detail is non-empty
- documents the JSON parser refuses, generated as text no JSON production opens
  and as an integer literal wider than the interpreter converts — that literal
  standing alone and carried inside an otherwise well-formed envelope — each
  answered with a non-empty detail rather than a traceback
- every schema version other than the declared integer, generated as booleans,
  floats carrying the declared version's own value, other integers, text, and
  null, each detail naming the schema-version field and the required version
- a read whose cause lies outside the declared set, whose detail names the
  admitted causes and the offending record's position
- an argument vector other than `derive`, whose detail names the required
  operation and every token received
