# Local Live Discovery Selection

Local verification includes live subagent discovery for installation, subagent-definition generation and placement, discovery, and their governing contracts or verification infrastructure. The selection layer's own full-gate plan includes it. Automatic widening of unrelated local deterministic verification does not add a live-model requirement. A selected row that starts a real coding-agent process is declared optional for one local run by that agent's own disable switch, and then skips with a reason naming that switch while the run's report carries the skip. Nothing in the product sets a switch, so CI, whose environment carries none, proves every selected live row with its own credential, while any local run, explicit full verification included, proves only the rows the environment it inherits leaves unswitched.

## Rationale

Live discovery proves that a fresh session can discover the installed definitions and consumes model quota, so selecting it by the behavior a change can affect preserves that proof while avoiding unnecessary authentication and model use for unrelated work. A declared switch keeps a local gate honest on a machine whose quota is exhausted — a silent skip would hide a broken session path, and a row that must run blocks every unrelated change — while the reported skip and the unswitched CI run keep the proof intact.

## Product properties

1. Relevant local changes and the selection layer's own full-gate plan include live discovery, with the selection reason visible before execution.
2. Unrelated local changes retain their complete selected deterministic scope while excluding live discovery, including when that scope widens automatically to the full deterministic suite.
3. A selected live check requires a successful execution unless its agent's disable switch declares that row optional for the run, in which case the row skips with a reason naming the switch and the report carries that skip by name; missing or invalid credentials fail visibly without skipping or switching authentication mode.

## Verification

- ALWAYS: a run carrying rows skipped by a declared switch names each skipped row and the switch that declared it, under a status distinct from a pass, so a summary carrying skipped rows never reads as all-green without them.
- ALWAYS: the execution plan names each agent's disable-switch state before the selected steps run, so a reader sees a declared skip before it happens.
- NEVER: a harness, a skill, a generated instruction surface, or the CI workflow sets a disable switch over this repository's own selected live rows, the proof no switch suppresses — CI, whose environment carries no switch, requires the successful execution of every selected live row with its own credential. A harness that sets both switches in the environment of a disposable child, over rows that child's own run generates and confines to the state it creates, reaches none of this repository's selected live rows and falls outside this rule's subject.

### Testing

- ALWAYS: a declared per-agent disable switch makes a selected live row optional for that one local run — the row is selected, runs its own skip, and reports a reason naming the switch, rather than leaving the plan. ([mapping])
- ALWAYS: local changed-path selection includes live discovery for installation, definition generation and placement, discovery, and their directly governing contracts and verification infrastructure. ([compliance])
- ALWAYS: the selection layer's own full-gate plan and direct execution covering the live check include live discovery. ([compliance])
- NEVER: automatic full-suite escalation for an unrelated local change selects live discovery or reduces the selected deterministic verification scope. ([compliance])
- ALWAYS: the execution plan displays the reason for including or excluding live discovery before running selected steps. ([compliance])
- NEVER: credential availability determines change relevance or turns selected required evidence into a passing skip. ([compliance])
