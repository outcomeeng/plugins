# Issues: Host Readiness

## Settle-delay modulo is not exercised beyond one settle window `spx/13-infrastructure.enabler/13-host-readiness.enabler/tests/test_host_readiness.scenario.l1.py` `test_ready_after_a_wait_is_confirmed_after_a_settle_delay (driven by run_ready_confirmed_after_wait, elapsed 60s)` `misaligned`

Every settle-delay case has an elapsed wait below the 180s settle window, so removing the modulo from `settle_seconds` leaves every scenario passing.

**Settlement condition**: A scenario drives an elapsed wait beyond one settle window.
