# Ledger reconstruction after a compaction or restart

The parent skill's `<ledger_derivation>` states the entry point's invocation
form and the rule for accepting its result. This reference states how the input
document is acquired once the session's own memory of the Change is gone, which
is the only condition that requires reconstruction.

## Acquisition

1. Begin with the orchestrating and officer mail identities proven by the launch
   result.
2. Read each positively identified participant's inbox exactly once through
   `coding-agents:operate-agent-mail`, and select the records carrying the exact
   per-Change correlation.
3. Add any positively identified sender or recipient from those records to the
   finite read set, and repeat. Finish when one pass adds no unread identity.
4. Deduplicate the selected records by integer store `id`.
5. Collect every complete verification run identity from those records and
   inspect it through `spec-tree:project-run-journal`, accepting only a sealed
   run whose recorded identity equals the requested identity.
6. Submit the acquired records and sealed runs through the entry point named in
   `<ledger_derivation>`.

## Refusal

Missing, ambiguous, unavailable, or unsealed input makes reconstruction
incomplete and produces a failed read. Never derive or report a partial ledger,
and never substitute the session's recollection for a durable record.
