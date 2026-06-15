# Enforcement on Tracked Load-State

Methodology-load enforcement keys on a state the system tracks for the agent — whether the methodology foundation and the target node's context have been loaded since the most recent session-start or compaction boundary — never on the work category the agent believes it is performing nor on the agent noticing a path. The enforcement lives in a `PreToolUse` hook, the only hook that can block a tool call; a `SessionStart` directive informs but cannot enforce.

## Rationale

An injected `SessionStart` directive loses a priority fight. After a compaction the harness continuation prompt sits last in context and frames itself as the task ("resume directly", "as if the break never happened"); two contradictory orders coexist and the last-and-task-framed one wins, so the directive is read past. That prompt is almost purpose-built to skip a post-break reload, which is precisely when the foundation is gone.

Keying enforcement on the work category is circular: an agent cannot recognize "spec-tree work" until after the foundation that defines the category has loaded, so a rule gated on that recognition can never fire before the load it guards. Keying on the agent noticing a path relies on the exact attention that is already absent — the failure mode is not noticing the path. A tracked-state flag needs neither concept: it is a fact the system records, and the hook does the noticing by reading the tool's own path argument, so the agent's attention is never the trigger.

The marker scan is scoped strictly after the most recent boundary because a marker preserved only in a pre-compaction summary is stale. Counting it would let the stale marker satisfy the gate and make the enforcement worthless; demanding a fresh marker after the boundary is what makes the gate durable across compaction. The hook delegates the transcript I/O and the verdict to the `spx` CLI per `spx/21-spec-tree.enabler/15-hook-state-delegation.adr.md`, so where the CLI is absent enforcement degrades to the informational `SessionStart` layer rather than failing.

## Invariants

- A gate's decision is a function of tracked load-state since the most recent boundary, not of the work category or the agent's attention.
- The only hook that blocks a tool call is a `PreToolUse` hook.

## Verification

### Audit

- ALWAYS: methodology-load enforcement keys on whether the foundation and the target node's context are loaded since the most recent session-start or compaction boundary, never on the work category or on the agent noticing a path ([audit])
- ALWAYS: the only enforcement point that blocks a tool call is a `PreToolUse` hook; a `SessionStart` directive informs but never enforces ([audit])
- ALWAYS: a gate discounts a marker that survives only in a pre-compaction summary and requires a fresh marker emitted after the most recent boundary ([audit])
- NEVER: enforcement depends on the agent recognizing a work category or noticing a path before acting — the hook reads the tool's path argument so the agent's attention is never the trigger ([audit])
