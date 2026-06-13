# Audit Result Delivery

An audit run reveals its result incrementally while it runs, not only once it finishes. A reader watching an audit — on a developer machine or on a hosted pull request — sees the run advance through its scope, sees each finding as it is raised, and then sees the final result. The same audit is observable in the same shape on both surfaces, so the audit a developer watches locally and the audit a reviewer watches on a pull request read alike. A long agentic audit is never an opaque wait for one result at the end.

## Rationale

Audit runs are minutes-long agentic work. A result that appears only when the run finishes leaves a reader unable to distinguish a working run from a stuck one and unable to act on early findings. Revealing the result as the run produces it — scope advanced, finding raised, final result — keeps the run legible while it executes. Keeping that reveal identical on a local surface and a hosted pull-request surface lets a developer and a reviewer read the same evidence in the same shape, so an audit's findings stay comparable across where the run happens.

## Product properties

1. An audit run reveals its result incrementally: scope progress is visible as the run advances, each finding appears as it is raised, and a final result follows.
2. The same audit run is observable in the same shape on a local surface and on a hosted pull-request surface.

## Verification

### Audit

- ALWAYS: an audit run reveals progress incrementally — scope advance and each finding are visible before the final result ([audit])
- ALWAYS: the same audit run is observable in the same shape on a local surface and on a hosted pull-request surface ([audit])
- NEVER: an audit run reveals nothing until it finishes — an opaque run that surfaces only a final result defeats in-flight legibility ([audit])
