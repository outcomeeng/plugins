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

## DEBT [evidence]: test-infrastructure quality in the sync test files

A test-evidence audit surfaced two pre-existing test-infrastructure defects in the node's test
files. Both are independent of the marketplace-state assertion alignment — the audit confirmed
every remaining assertion still resolves to a test that exercises its claimed behavior — and both
live in files the checkout-bounded cutover already rewrites, so they are addressed as part of that
cutover rather than in the spec-only alignment.

- `tests/test_sync.compliance.l1.py` hardcodes the production step-name literal
  `INITIAL_CODEX_LOCAL_REFRESH_STEP = "codex_local_refresh"`, which `outcomeeng/distribution/sync.py`
  does not export. The cutover exposes the step name from production and imports it, or removes the
  guard when the step is dropped.
- `tests/test_sync.scenario.l1.py` embeds a git-repo bootstrap helper (`_git`) directly in the test
  file, duplicated across the change-probe tests. The cutover moves git-repo bootstrap into a harness
  under `outcomeeng_testing/harnesses/` consumed by both tests.
