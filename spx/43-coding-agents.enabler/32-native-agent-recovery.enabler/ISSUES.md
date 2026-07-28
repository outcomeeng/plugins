# ISSUES — native agent recovery

Coordination note; not spec truth.

## DEBT [evidence]: no deterministic guard rejects an oversized destroyed fact

`reassessment_prompt` concatenates `NON_CONTROLLER_BOUNDARY` (~190 characters) with the
operator-supplied `restored[].text` and `_restored_facts` accepts that text unchecked, so the
one-short-line rule the skill's `<constraints>` and `<failure_modes>` declare is enforced only by
prose instructing the invoking agent. An oversized destroyed fact still reaches `send`, collapses
into a `[Pasted text #1]` attachment no `Enter` submits, and strands silently in the recipient's
editor — the exact incident the failure mode records.

**Resolution shape**: reject the delivery in `_restored_facts` with an `AdapterError` when the
combined boundary and destroyed fact exceed the recipient TUI's paste-collapse threshold, and cover
the rejection with compliance evidence.

**Deferral reason**: the guard needs a threshold this product has not established. The recorded
incident proves 1,300 characters collapses; it does not locate the boundary, which belongs to the
recipient TUI rather than to this script and differs between the Claude and Codex surfaces this
skill drives. Writing a guessed constant into a deterministic guard would reject valid deliveries on
an invented number, so the bounded code change waits on measuring the real threshold per surface —
an empirical task against two external TUIs, not an edit to this file.
