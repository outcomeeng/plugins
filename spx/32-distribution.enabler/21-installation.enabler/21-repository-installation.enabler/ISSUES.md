# Issues: repository installation evidence

## Real-installation catalog oracle is captured after execution

Implementation audit run `2026-07-27_12-00-05-616-b2d3b2339685` rejected the
real-installation evidence because
`outcomeeng_testing/harnesses/installation.py:183` reads the mirrored catalog
bytes after two installation runs. An installation mutation that changes the
mirror can therefore change both the observed behavior and its expected catalog
while the test remains green.

**Resolution:** capture immutable catalog bytes before either installation run
and use that pre-execution snapshot as the independent oracle.

## Scenario omits marketplace-target and disposable-home assertions

Test-evidence audit finding `f-001` rejected
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.scenario.l2.py:22`.
The scenario proves installed and enabled catalog membership, while it does not
assert that marketplace registration targets the invocation checkout or that
installation state remains confined to the disposable homes.

**Resolution:** expose the registration target and selected state roots as raw
harness observations, then assert both boundaries in the linked scenario test.

## Lifecycle-placement scenario permits a stable no-op

Test-evidence audit finding `f-002` rejected
`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/tests/test_repository_installation.scenario.l2.py:40`.
The scenario compares placement snapshots across repeated runs and preserves an
unowned file, while it does not prove that any plugin-owned agent definition was
placed. A lifecycle implementation that performs no placement can remain green.

**Resolution:** capture the initial agent-directory observation and assert a
positive plugin-owned placement effect before asserting repeated-run stability
and preservation of unowned definitions. Rerun the focused deterministic checks
and both invalidated audits on a new committed head.
