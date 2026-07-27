# Issues: installation evidence

## Catalog conformance oracle is captured after plan construction

Implementation audit run `2026-07-27_12-00-05-616-b2d3b2339685` rejected the
catalog conformance evidence because
`outcomeeng_testing/harnesses/installation.py:117` reads the committed catalog
bytes after `build_installation_plan` executes. A subject mutation that changes
the catalog can therefore change both the plan and the expected bytes while the
test remains green.

**Resolution:** capture immutable catalog bytes before plan construction and use
that pre-execution snapshot as the conformance oracle. Review the directly
changed installation evidence for the same post-execution-oracle defect class,
then rerun the focused deterministic checks and invalidated audits on a new
committed head.
