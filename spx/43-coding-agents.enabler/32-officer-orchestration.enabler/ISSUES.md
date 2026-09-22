# Issues: Officer Orchestration

## In-flight escalation conflicts with the methodology and generated router

The node requires an orchestrating session with officers in flight to write an
escalation as text in its own pane and never use the structured question tool.
That rule stands on the operator's instruction. It conflicts
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
behavior remains Declared. The third-round, pane-prompt, and autonomy-boundary
conditions cannot be claimed from an ordinary run. The node's `[audit]`-tagged
assertions, which the node spec enumerates, are settled by an audit verdict and
lie outside this protocol's scope.

**Settlement condition**: after a release contains `/orchestrate-officers`, a
fresh orchestrating session executes the protocol, preserves the named run
artifacts and complete identities, and pins the resulting attested run through
the methodology's published probe-evidence mechanism.

## The shipped ledger script is unproven generic logic past the size bound

`src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py`
runs past the fifty-line bound — the source-owned field vocabulary and scalar-
event registry, per-event parsing for passes, heads, verdicts, decisions,
failures, finding provenance and reads, decimal spend accumulation across
currencies, wall-time totalling, source provenance on every entry, and the
versioned entry point with its success and invalid-input result contracts. None
of that is agent-specific: it derives a record from durable inputs and would
behave identically for any coding agent, so `spx/12-shipped-scripting.adr.md`
governs it as a generic shipped script and states that past fifty lines such a
script "is debt awaiting extraction once proven, or removal when it is not". The
plugin-local adapter exemption in the same decision does not reach it, because
moving this logic into SPX would couple SPX to no coding agent.

Which branch it owes is undecided, and that is what separates this entry from
the marketplace's other oversized-script entries: the waiter and the worktree
provisioner have proven their value in use and owe extraction outright, while
`/orchestrate-officers` has never run against a live fleet. The node's own
`probes/officer-run/probe.md` records no attested run, so the script's value is
asserted rather than observed, and the ADR's removal branch remains live.

**Evidence**: `spx/12-shipped-scripting.adr.md` `## Verification` carries
"NEVER: a generic shipped script beyond fifty lines stands as settled" and
"NEVER: retain an unproven shipped script"; the script named above exceeds that
bound, and `wc -l` over its path derives the length it stands at. The length is
the file's own, so this entry states the relation and never a copy of the
figure, which every edit to the script would falsify;
`probes/officer-run/probe.md` records `Artifacts: none` and no attested run of
the skill that invokes it.

**Impact**: a consumer repository carries the whole of that generic derivation
logic, which it cannot version independently and cannot repair without a
marketplace release, for a capability no observed run has yet shown is wanted.

**Settlement condition**: an attested officer run establishes whether the
derivation earns its place. If it does, the logic ports into the agent-neutral
SPX CLI, is published to npm, `REQUIRED_SPX_VERSION` advances to that release,
and the skill keeps its instruction with no script. If it does not, the script is
removed rather than extracted, and `<ledger_derivation>` and `<script_validation>`
are withdrawn with it.

## The supervision skill's own result carries no declared shape

`/orchestrate-officers` validates every value it composes against a declared
versioned shape — the herdr and agent-mail results under `schemaVersion: 1`, and
the ledger under the entry point's own key set — while its `<result>` section
names the content it returns as prose: the operation, officer identity, absolute
worktree, Change, triggering event, capability results, ledger change, and next
event boundary. A caller therefore compares the emitted operation against a list
of nouns rather than against field names, and no deterministic reader can check
a returned operation for completeness.

**Evidence**: `instructions:skill-auditor` on
`src/plugins/coding-agents/skills/orchestrate-officers/`, verdict `APPROVED`
with `must-fix` empty, finding `f-007` (severity `WARNING`) against
`SKILL.md` `<result>`.

**Gap**: no assertion in this node declares a result envelope for the
supervision skill. Naming the fields in the skill body alone would make the
surface claim a contract no assertion carries, which the truth hierarchy
forbids; declaring the envelope first means choosing its field spelling,
nesting, and versioning for every routed operation, and the `[probe]`-tagged
behavioral assertions that would exercise it still have no attested run.

**Settlement condition**: the node declares the supervision result's envelope as
an assertion — its fields, nesting, and version — the skill body states that
envelope once, and each workflow's success criteria names the fields its
operation fills.

## The router loads the journal capability on every routed operation

`/orchestrate-officers` composes `spec-tree:project-run-journal` at the router
level, while only the reconstruction path consumes it — the read workflow after
a compaction or restart, and the pre-compaction housekeep path. The other routed
operations carry that capability's payload without inspecting a journal run.

**Evidence**: `instructions:skill-auditor` on
`src/plugins/coding-agents/skills/orchestrate-officers/`, verdict `APPROVED`
with `must-fix` empty, finding `f-007` (severity `WARNING`).

**Gap**: moving the composition into the consuming workflow's required reading
changes which capabilities a routed invocation loads. Which paths genuinely
reach a journal run is settled by the officer-run probe, and
`probes/officer-run/probe.md` records no attested run, so the consuming set is
asserted rather than observed.

**Settlement condition**: an attested officer run establishes which routed
operations inspect a sealed journal run, and the composition moves to those
workflows' required reading while the capabilities nearly every operation uses
stay at the router level.
