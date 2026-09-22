<required_reading>

Read `${SKILL_DIR}/references/officer-order.md` and
`${SKILL_DIR}/references/standing-rules.md`.

</required_reading>

<process>

1. Refuse an order with an unfilled template field, unproven worktree, or
   unregistered mail identity.
2. Use skill `coding-agents:operate-agent-mail`. Ask it to send the complete
   order as one `order` record.
3. Validate the capability result under the parent skill's
   `<essential_principles>`. Require the returned record to preserve every
   supplied field and carry its integer store-assigned `id`.
4. Record that store identity in the per-Change ledger.

</process>

<success_criteria>

One validated durable order record and its integer store identity appear in
the result and ledger provenance.

</success_criteria>
