# Issues: Officer Orchestration

## In-flight escalation conflicts with the methodology and generated router

The node requires an orchestrating session with officers in flight to write an
escalation as text in the Captain's own pane and never use the structured
question tool. That rule stands on the operator's instruction. It conflicts
with the `/understand` foundation's imperfection and closing protocols, which
require a blocking decision to use the structured-question tool. The generated
root guide's `Operator questions` and `Autonomy Boundary` sections, rendered
from the instruction-block template, preserve the same structured-question
boundary for decisions that require operator direction.

**Evidence**: the escalation assertion in
`spx/43-coding-agents.enabler/32-officer-orchestration.enabler/officer-orchestration.md`
and the `<imperfection_protocol>` and `<closing_protocol>` sections of the
shipped `/understand` foundation, together with the generated root guide's
`Operator questions` and `Autonomy Boundary` sections rendered from the
instruction-block template, prescribe different handling for the same blocking
decision.

**Impact**: the product-specific officer contract cannot compose with the
portable methodology foundation or generated router without an admitted
exception.

**Settlement condition**: a methodology Change admits the in-flight orchestration exception, and the plugin foundation and the router template follow that decision.

## Probe assertions have no attested-run pin

The officer-run probe protocol exists, while no live officer run can be
attested until the released `/orchestrate-officers` skill is available. The
current spec status therefore has no probe-run pin for the behavioral
assertions.

**Evidence**: `spx spec status --format json` reports the tagged node as
`specified` without an attested probe-run identity or pin, and
`probes/officer-run/probe.md` records no attested run or artifact.

**Impact**: the protocol fixes the future observation seam, while the officer
behavior remains Declared. The third-round, pane-prompt, lifecycle-exception,
and autonomy-boundary conditions cannot be claimed from an ordinary run.

**Settlement condition**: after a release contains `/orchestrate-officers`, a
fresh orchestrating session executes the protocol, preserves the named run
artifacts and complete identities, and pins the resulting attested run through
the methodology's published probe-evidence mechanism.
