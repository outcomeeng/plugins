# Live Discovery Selection

Live discovery is the two real-agent Codex tests: the fresh-session subagent discovery test and the real-agent bootstrap test. Both belong to the on-demand suite that [`spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md`](spx/13-infrastructure.enabler/21-test-infrastructure.enabler/14-on-demand-suite.pdr.md) declares, so no changeset selects them into local changed-path verification, explicit full verification, or CI, whatever the changeset changes, including a changeset that changes an agent definition. An operator runs them through the on-demand command, or by direct execution that names one of them, and a run reaches a verdict on the Codex CLI the host installs.

## Rationale

The real-agent Codex tests prove that the definitions an installation places reach a fresh agent session, and they consume model quota on a host CLI whose version moves outside the repository. Repeating that cost in every gate that a changeset touching an agent definition triggers is too expensive, and the tests keep their value as evidence an operator gathers deliberately. Their file names already carry the execution level `l3`, so the on-demand suite places them without a selection rule of their own, and one exclusion mechanism serves every default verification path. The record stays in this node because a maintainer reading the selected gate looks here to learn why live discovery never appears in a plan.

## Product properties

1. Local changed-path verification, explicit full verification, and CI select no live-discovery test, whatever the changeset changes.
2. Direct execution that names a live-discovery test, and the on-demand command, run it.
3. A live-discovery run requires a successful execution; missing or invalid credentials fail visibly without skipping or switching authentication mode.

## Verification

- ALWAYS: the fresh-session subagent discovery test and the real-agent bootstrap test belong to the on-demand suite, and no changeset selects them into local, full, or CI verification
- ALWAYS: direct execution that names a live-discovery test runs it, whatever the changeset changes
- NEVER: the exclusion of live discovery removes any other step or test from the selected deterministic scope, including when that scope widens automatically to the full deterministic suite
- NEVER: credential availability determines change relevance or turns a required live-discovery run into a passing skip
