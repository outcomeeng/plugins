# Issues: Host Readiness

## Waiter extraction awaits a published SPX CLI capability

`src/plugins/spec-tree/skills/wait-for-load/scripts/wait_for_load.py` runs to
308 lines — five terminal statuses, two lookup tables, normalized load
observation, load-aware interval arithmetic, and a bounded-deadline loop. Past
fifty lines `spx/12-shipped-scripting.adr.md` makes a shipped script debt whose
logic moves into the SPX CLI once the script proves its value. The waiter has
proven its value in use, so extraction is what it owes.

The extraction is a cross-repo port into `@outcomeeng/spx`, a separate product,
and the plugins product may depend on the resulting capability only once it is
published to npm and `REQUIRED_SPX_VERSION` advances to it. That sequencing puts
the fix outside any changeset confined to this repository. The same dependency
gates the instruction-block generator, tracked in
`spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.

**Resolution shape**: port the waiter's observation, interval, and deadline
behavior into the SPX CLI, publish it, advance the floor, and reduce the shipped
skill to its instruction with no script. Revisit when the capability publishes.
