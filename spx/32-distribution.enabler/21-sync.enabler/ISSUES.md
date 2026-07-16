# ISSUES -- sync enabler

Coordination note; not spec truth.

Both items below are superseded by `spx/12-marketplace-state.adr.md`: the checkout-bounded
cutover of `just sync-marketplace` removes the Codex cache-topology inspection, the user-scope
reconciliation orchestration, and the file-backed single-flight lock these notes concern. They
remain recorded until that cutover removes the machinery; neither is fixed independently.

## DEBT [structure]: split sync orchestration boundaries (superseded)

An implementation audit raised a decomposition finding when `sync.md` carried more than roughly
seven assertions mixing prerequisite tool checks, marketplace source reconciliation,
distribution-change detection, Codex cache topology health checks, file-backed single-flight
coordination, ordered sync-step orchestration, and named forbidden-step compliance. The aligned
spec now declares four assertions bounded to the checkout, so the assertion-count trigger no
longer holds. The cutover removes the reconciliation, topology, and single-flight concerns from
the implementation; no separate `/decompose` pass is owed once the checkout-bounded rewrite lands.

## DEBT [correctness]: PID reuse identity limits (superseded)

The file-backed refresh lock detected stale owners by combining the owner PID with the process
start timestamp reported by `ps -p <pid> -o lstart=`, whose whole-second resolution let a PID
reused within the same wall-clock second produce the same lock-owner identity string. The
checkout-bounded model removes the lock entirely, dissolving the PID-reuse window rather than
bounding it.
