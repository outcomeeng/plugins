# Issues: Host Readiness

## Waiter complexity belongs in the SPX CLI (accepted debt)

`src/plugins/spec-tree/skills/wait-for-load/scripts/wait_for_load.py` carries a
growing stateful surface — five terminal statuses, two lookup tables, normalized
load observation, load-aware interval arithmetic, and a bounded-deadline loop.
`spx/12-shipped-scripting.adr.md` requires a proven shipped script's complexity
to move into the SPX CLI, tested there and consumed as a trusted third party,
rather than accreting in a standalone script. Its stated rationale is that a
standalone script "resists isolated testing" because it is invoked, not
imported. `outcomeeng_testing/harnesses/host_readiness.py` works around that by
loading the script through `importlib.util.spec_from_file_location` and calling
its internals with injected dependencies, which delivers isolated testing
without resolving the placement the decision prescribes.

Accepted debt: the extraction is a cross-repo port into `@outcomeeng/spx`, a
separate product, and the plugins product may depend on the resulting capability
only once it is published to npm and `REQUIRED_SPX_VERSION` advances to it. That
sequencing puts the fix outside any changeset confined to this repository. The
same standing tension between `spx/12-shipped-scripting.adr.md` (extract to the
CLI) and `spx/13-plugin-and-runtime-conventions.adr.md` (ship Python under
`scripts/`) is already tracked for the instruction-block generator in
`spx/21-spec-tree.enabler/43-instruction-block.enabler/ISSUES.md`.

**Resolution shape**: decide the tension once for both components rather than
per script — either amend `spx/12-shipped-scripting.adr.md` to carve out an
explicit exception for a shipped script whose internals are isolation-tested
through an importlib-loading harness, recording why that satisfies the
decision's testability rationale without CLI extraction, or schedule both
extractions behind the published `@outcomeeng/spx` capability and the advanced
version floor.
