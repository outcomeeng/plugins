# Ledger entry-point tested coverage

## Contents

- [Executing evidence](#executing-evidence)
- [Reachability and result shape](#reachability-and-result-shape)
- [Derivation from populated inputs](#derivation-from-populated-inputs)
- [Rejections](#rejections)

The cases executed against `${CLAUDE_SKILL_DIR}/scripts/derive_ledger.py`, with
the inputs each uses and the evidence that executes it. Read this when judging
what the entry point is proven to do; the parent skill's `<ledger_derivation>`
carries the invocation contract an operation needs.

Each case below fails when the behavior it covers is disabled or inverted.

## Executing evidence

Every case below is executed rather than asserted here, by a suite that lives
with this plugin's source beside the spec node governing this skill. That suite
ships with no plugin: an installed plugin tree carries the entry point without
it, so a change to the entry point is checked by running the suite where the
plugin's source lives, against the recorded claim below.

The suite is a set of co-located execution-level-1 test files sharing the
subject `ledger_derivation`, one file for each assertion type the cases below
carry — `scenario` for an existential run, `mapping` for the finite declared
domain, `property` for an open generated domain — spelled in the source
repository's own language and test-naming convention, so the set grows with the
labels rather than with a count recorded here. Each file reaches the entry point
through that repository's officer-orchestration test harness and the generators
that harness composes, so the harness, not a test file, owns how the script is
loaded and run. Every case below opens with the assertion type whose file
executes it.

## Reachability and result shape

- `scenario` — the empty document
  `{"schemaVersion":1,"change":"owner/changes#123","mailRecords":[],"journalRuns":[]}`
  exits zero with empty stderr and writes a result carrying exactly `ledger`,
  `schemaVersion`, and `status: "succeeded"`, whose ledger carries exactly
  `change`, `passes`, `heads`, `verdicts`, `decisions`, `failures`,
  `findingProvenance`, `reads`, `runningSpend`, and `wallTimeSeconds`, with
  every collection empty, an empty running spend, and a zero wall time

## Derivation from populated inputs

- `scenario` — one mail record whose body carries a `ledger` object holding a
  pass, head, verdict, decision, failure, finding provenance, read, spend, and
  wall time places each value in its own collection under that record's mail
  provenance, totals the spend under its currency, and totals the duration
- `property` — a body carrying no `ledger` object — unparseable text, a `ledger`
  key whose value is an integer literal wider than the interpreter converts, a
  JSON scalar, a JSON array, an object with other keys, and event fields carried
  at the top level rather than under `ledger` — derives the ledger of a document
  with no record
- `mapping` — every declared read cause records one read carrying that cause and
  payload
- `property` — amounts across several currencies total per currency at their own
  decimal precision, and durations across mail records and journal runs total
  together, over amounts and durations whose precision ranges from absent
  through widths no double represents to coefficients longer than the default
  decimal context carries, each total compared against a sum taken with no
  rounding
- `property` — both totals are emitted as decimal text carrying every digit of
  the amount and duration the record supplied
- `property` — mail records repeating one store `id` and journal runs repeating
  one `runToken` derive the ledger of their first occurrences alone
- `property` — a finding provenance or read one record lists several times is
  recorded once per occurrence
- `property` — every entry names the mail store `id` or `runToken` that carried
  it

## Rejections

Each exits two with empty stderr and a result carrying exactly `detail`,
`schemaVersion`, and `status: "invalid-input"`:

- `scenario` — `schemaVersion` `2`, whose detail names the schema-version field
  and the required version
- `scenario` — the malformed stdin document `{`, whose detail is non-empty
- `property` — documents the JSON parser refuses, generated as text no JSON
  production opens, as an integer literal wider than the interpreter converts
  from a digit string — that literal standing alone and carried inside an
  otherwise well-formed envelope — as a nesting run past the scanner's own
  recursion guard, and as bytes no codec decodes between bytes that do; the
  digit width and the nesting depth are read from the running interpreter
  rather than fixed here, and each document is answered with a non-empty detail
  rather than a traceback
- `property` — every schema version other than the declared integer, generated
  as booleans, floats carrying the declared version's own value, other integers,
  text, and null, each detail naming the schema-version field and the required
  version
- `property` — a read whose cause lies outside the declared set, whose detail
  names the admitted causes and the offending record's position
- `property` — an argument vector other than `derive`, whose detail names the
  required operation and every token received
