<required_reading>

`${CLAUDE_SKILL_DIR}/references/authority.md`.

</required_reading>

<process>

1. Take the theme from the operator in one sentence, with the outcome that ends it. Record it at the top of the note.
2. Ask each Maintainer for its product's Changes that serve the theme, with what blocks each and what each blocks. Read no Change's content.
3. Order the work per product: one Change per position at a time, one Executor per product at a time. A Change whose output another consumes goes first; independent Changes in different products run in parallel. Record the order per product in the note.
4. Require vertical slices. Each Change carries a decision or spec evolution together with the evidence and implementation it governs, so it merges on its own and leaves the default branch passing. A Change that only writes specs for another to implement, or that cannot merge without its sibling, goes back to its Maintainer to re-slice; a fold of several Changes into one is the Maintainer's to propose.
5. Route each Change by its output: an instruction-only Change goes to a Contributor, which delivers it without an Executor; every other Change goes to its product's Orchestrator once it is Executable.
6. Hold the queue: a position finishing one Change gets the next in its product's order. A Change outside the theme waits unless it blocks a theme Change or the operator names it.
7. The theme ends when its outcome is observable on the default branches. Report it to the operator with the merged Changes and what remains, and clear the theme from the note.

</process>

<success_criteria>

- Every position works at most one theme Change at a time, and every product runs at most one Executor.
- Every theme Change merged on its own, with the default branch passing after each merge.

</success_criteria>
