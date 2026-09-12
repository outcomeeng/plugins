# Local Live Discovery Selection

Local verification includes live subagent discovery for installation, subagent-definition generation and placement, discovery, and their governing contracts or verification infrastructure. Explicit full verification and CI include it. Automatic widening of unrelated local deterministic verification does not add a live-model requirement.

## Rationale

Live discovery proves that a fresh session can discover the installed definitions and consumes model quota. Selecting it by the behavior a change can affect preserves that proof while avoiding unnecessary authentication and model use for unrelated work.

## Product properties

1. Relevant local changes and explicit full verification include live discovery, with the selection reason visible before execution.
2. Unrelated local changes retain their complete selected deterministic scope while excluding live discovery, including when that scope widens automatically to the full deterministic suite.
3. A selected live check requires a successful execution; missing or invalid credentials fail visibly without skipping or switching authentication mode.

## Verification

### Testing

- ALWAYS: local changed-path selection includes live discovery for installation, definition generation and placement, discovery, and their directly governing contracts and verification infrastructure. ([compliance])
- ALWAYS: explicit full verification, direct execution covering the live check, and CI full verification include live discovery. ([compliance])
- NEVER: automatic full-suite escalation for an unrelated local change selects live discovery or reduces the selected deterministic verification scope. ([compliance])
- ALWAYS: the execution plan displays the reason for including or excluding live discovery before running selected steps. ([compliance])
- NEVER: credential availability determines change relevance or turns selected required evidence into a passing skip. ([compliance])
