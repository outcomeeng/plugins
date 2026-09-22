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

Three classes refuse the whole invocation, and each refusal names its cause in
the result's `detail`:

- an argument vector other than the declared derive operation, whose detail
  names the required operation and every token received
- a document the JSON parser cannot read: malformed syntax, an integer literal
  wider than the interpreter converts from a digit string, nesting past its
  recursion guard, or bytes no codec decodes
- a document the parser reads whose content the derivation refuses: a schema
  version other than the declared one, a structural field of the wrong shape, a
  read whose cause lies outside the declared set, an empty change, run token, or
  spend currency, a spend amount that does not read as a finite decimal, or a
  `wallTimeSeconds` that does not read as a finite decimal at or above zero

A value refusal turns on the value rather than on its shape: a `wallTimeSeconds`
of `-1` is well-formed text and still refuses the whole document, so one
record's out-of-range value costs every entry the derivation would have
produced.

A refusal caused by one record names that record's position, so a document
holding many records identifies the offending one.

A mail body the parser cannot read is not a refused document. That body carries
no `ledger` object, so its record stays a durable mail fact and contributes
nothing, exactly as a body whose JSON carries no such object does.
