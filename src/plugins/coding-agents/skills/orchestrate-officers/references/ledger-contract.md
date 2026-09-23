# Ledger entry-point contract

## Contents

- [Input document](#input-document)
- [Mail records](#mail-records)
- [Journal runs](#journal-runs)
- [The derived ledger](#the-derived-ledger)
- [Refused sources](#refused-sources)

The parent skill's `<ledger_derivation>` carries the invocation form and the
rule for accepting a result. This reference carries what the document holds,
what the ledger holds, and which sources the entry point refuses — so contract
detail the entry point gains later lands here rather than growing the skill
body.

## Input document

```json
{
  "schemaVersion": 1,
  "change": "owner/changes#123",
  "mailRecords": [],
  "journalRuns": []
}
```

## Mail records

Each mail record preserves the store's integer `id` and string `body`. A JSON
body with a `ledger` object contributes its declared fields; other bodies remain
durable mail facts without entering the derived ledger. That object carries any
of `pass`, `head`, `verdict`, `decision`, `failure`, `findingProvenance`,
`read`, `spend`, and `wallTimeSeconds`. A `decision` event records its
autonomous class, choice, and reasoning. A `failure` event records an operator
instruction naming an officer session or an officer fact reporting an operator
interaction. A `read` event records one of the causes `message`,
`officer-state-change`, `bound-crossed`, and `operator-cadence`, as one object
or an array of them. `findingProvenance` is always an array.

## Journal runs

Each journal object preserves its `runToken` and carries the same event fields
at its own top level rather than under a `ledger` key — a run object holding
only its `runToken` therefore contributes no pass, verdict, spend, or duration.
The sources differ only in where the event fields sit and in which identity
stamps the entries they produce:

```json
{
  "runToken": "2026-09-22_10-14-02-117-af31c9d0e4b2",
  "pass": "round-2",
  "verdict": "REJECT",
  "spend": { "currency": "USD", "amount": "12.50" },
  "wallTimeSeconds": "93.5"
}
```

## The derived ledger

The ledger carries exactly `change`, `passes`, `heads`, `verdicts`, `decisions`,
`failures`, `findingProvenance`, `reads`, `runningSpend`, and `wallTimeSeconds`,
with source provenance on every entry: the mail record's integer store `id`, or
the journal run's `runToken`. A source repeating one identity — records sharing
a store `id` or runs sharing a `runToken` — contributes once, while a value one
record lists twice is recorded twice.

## Refused sources

A refusal ends the whole invocation: no ledger is derived, the result carries
the invalid-input status in place of one, and its `detail` names the cause. A
refusal a single record or run provokes names that position, so a document
holding many of them identifies the offending one.

The invocation refuses an argument vector other than the declared derive
operation, and that detail names the required operation and every token
received.

The document refuses when the parser cannot read it: syntax no JSON production
admits, an integer literal wider than the interpreter converts from a digit
string, nesting past the parser's own recursion guard, or bytes no codec
decodes.

A document the parser reads whole refuses when:

- the document is not a JSON object
- `schemaVersion` is anything other than the declared integer — absent, a
  boolean, a float, a string, null, an array, an object, or another integer,
  the boolean and the float that compare equal to the declared one included
- `change` is not a non-empty string
- `mailRecords` or `journalRuns` is absent or is not an array
- a mail record is not an object, or its `id` is not an integer
- a mail record's `body` is not a string — a record repeating an `id` an earlier
  record already carried is passed over before its body is read
- a journal run is not an object, or its `runToken` is not a non-empty string —
  a run repeating a `runToken` an earlier run carried is passed over before its
  event fields are read
- `findingProvenance` is not an array, or one of its entries is not an object
- `read` is neither an object nor an array of objects, or a read carries no
  `cause` at all or a `cause` outside the declared set — every JSON value that
  is not one of the declared strings lies outside it, a scalar and a container
  alike — whose detail names the admitted causes
- `spend` is not an object, its `currency` is not a non-empty string, or its
  `amount` is not a number or a string that reads as a finite decimal
- `wallTimeSeconds` is not a number or a string that reads as a finite decimal
  at or above zero

Every event field is optional, and `null` under one reads as its absence: a
record omitting a field, or carrying `null` there, contributes nothing to that
collection and refuses nothing. The scalar event fields — `pass`, `head`,
`verdict`, `decision`, and `failure` — carry no gate of their own: whatever
value other than `null` an admitted record places under one of them becomes
that collection's entry.

A value refusal turns on the value rather than on its shape: in a record or run
the derivation admits, a `wallTimeSeconds` of `-1` is well-formed text and still
refuses the whole document, so one admitted record's out-of-range value costs
every entry the derivation would have produced. A record or run passed over for
a repeated identity is never admitted, so the gates above reach none of its
event fields, and an out-of-range value it carries costs nothing.

A mail body the parser cannot read is not a refused document. That body carries
no `ledger` object, so its record stays a durable mail fact and contributes
nothing, exactly as a body whose JSON carries no such object does. A body whose
`ledger` value is read whole and is not an object stays a durable mail fact for
the same reason: the `ledger` key's shape decides membership, never admission.
Once a record or run is admitted as a ledger event, the gates above apply to it.
