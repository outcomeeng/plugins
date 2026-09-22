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
`spx/43-coding-agents.enabler/32-officer-orchestration.enabler/officer-orchestration.md`,
realized by the standing delivery rule in
`src/plugins/coding-agents/skills/orchestrate-officers/references/standing-rules.md`
and the escalate workflow that performs it, and the `<imperfection_protocol>`
and `<closing_protocol>` sections of the shipped `/understand` foundation,
together with the generated root guide's `Operator questions` and `Autonomy
Boundary` sections rendered from the instruction-block template, prescribe
different handling for the same blocking decision.

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

## Two shipped references restate behaviour the entry point owns

`src/plugins/coding-agents/skills/orchestrate-officers/references/ledger-contract.md`
enumerates the refusal classes
`src/plugins/coding-agents/skills/orchestrate-officers/scripts/derive_ledger.py`
implements, and
`src/plugins/coding-agents/skills/orchestrate-officers/references/ledger-script-coverage.md`
enumerates the shapes
`outcomeeng_testing/generators/officer_orchestration.py` emits. Neither states a
claim its source does not already state. Every correct change to the code
therefore falsifies the document that restates it, by construction rather than
by oversight.

The evidence is a sequence, and the sequence is the point. Three correct code
repairs each falsified one of these documents as a side effect: a section shrink
that moved the ledger contract out of the skill body, a generator widening that
added parser-refusal shapes, and an inert-body fix that added a generated body
shape. Each repair was right. Each left a document false. Each was then repaired
as a single instance, and the next code change falsified the documents again.

A class sweep followed: both enumerations were derived from the source and
replaced whole rather than repaired instance by instance. That sweep found
thirteen disagreements between the documents and the code beyond the two a
review had named — among them an unstated top-level object gate,
absent-container refusals, mail-record and journal-run gates never named as
refusals, a run-token type gate, and a blanket phrase naming no field, which
could neither be falsified nor confirmed against any code path. The thirteen is
what that one reading found, not a running total; a later reader who sweeps
again should restate what that reading finds rather than add to this figure.

The same defect stood inside the generator's own docstring, which counted shapes
the strategy no longer carried. That instance sits in no shipped document at
all, which places the defect in prose restating executable behaviour rather than
in these two files.

The sweep did not end it. On head
`ab87d964b416a6e8067d3930fbc64748c378449e`, review run
`2026-09-22_18-30-17-398-2ea1e6382b59` raised a further drift finding against
`ledger-contract.md`: a universal value-refusal sentence the entry point does
not honour for a journal run repeating a `runToken`, because the derivation
passes such a run over before reading its event fields. That finding lands on a
document derived from the code in the same round.

**Evidence**: the class sweep at commit
`31401d957ab517228b600fc04e8e2d8ac148060f`, which replaced both enumerations
whole and whose message records the thirteen disagreements and the generator
docstring; and review run `2026-09-22_18-30-17-398-2ea1e6382b59` on head
`ab87d964b416a6e8067d3930fbc64748c378449e`, which raised the `runToken`
value-refusal drift against `ledger-contract.md` after that sweep.

**Impact**: a document hand-maintained against code is missed by whoever just
changed the code, reliably, including when that person knows the rule and has
just applied it elsewhere — the sequence above carries one instance where the
same correction was relayed and then repeated two commits later. Verification
does not catch the drift either: four Verifier passes approved these documents
across the rounds in which those thirteen unreported disagreements accumulated.
A consumer reading either document therefore reads a claim the installed entry
point may not honour, and no gate says which sentence is stale.

**Settlement condition**: a Frame decision settles whether these two documents
restate the executable's behaviour at all — either they carry only claims the
code cannot state, such as intent, boundaries, the reason behind a refusal, and
what a consumer must supply, with the enumerations generated from the source or
dropped; or the decision states why a hand-maintained restatement is worth its
drift and names the mechanism that catches it. Repairing the next drift instance
does not close this entry. Repairing instances was tried, and it established
that each repair holds only until the following code change. The class sweep was
tried, and it established two things: the drift was far wider than any round had
reported, and a document derived from the code in one round drifts again in the
next.

**Adjacent, and distinct**:
`spx/43-coding-agents.enabler/18-agent-mail.enabler/ISSUES.md` records a skill
body restating an adapter-owned predicate and dropping a different condition on
each rewrite, and its settlement asks for a rule choosing between stating the
outcome a caller must handle and restating the predicate a decision already
owns. That entry is a handful of sentences inside one skill body, where the
restatement is incidental to the body's purpose. This one is two whole reference
documents whose purpose is the enumeration, so the question here is whether the
documents should carry such content at all rather than how carefully they carry
it. A rule settling either bears on the other.
