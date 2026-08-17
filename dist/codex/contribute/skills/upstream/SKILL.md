---
name: upstream
description: >-
  ALWAYS invoke this skill when starting a contribution to a repository the operator does not control, or when a contribution step needs that target and no live UPSTREAM_TARGET marker carries it — it resolves the upstream a fork came from, the head to push from, and the operator's permission on it.
  NEVER read that target from a git remote, an account name, or a successful push.
allowed-tools: Bash(python3 "${SKILL_DIR}/scripts/resolve_target.py":*)
---

<objective>
One `<UPSTREAM_TARGET>` marker carrying the resolved base repository, head repository, operator permission, and classification for this contribution, whether it continues or stops.
</objective>

<workflow>

**Step 1 — Resolve the target.** Run the resolver once per contribution.

```bash
python3 "${SKILL_DIR}/scripts/resolve_target.py"
```

It prints one JSON object:

```json
{
  "classification": "head-ambiguous",
  "base": "someone/example",
  "head": null,
  "permission": "READ",
  "fork": {
    "matches": ["operator/example", "silvarbor/example"],
    "candidates": ["operator", "silvarbor"]
  },
  "detail": "2 forks of someone/example to contribute from (operator/example, silvarbor/example); choosing among them is the operator's"
}
```

**Step 2 — Emit the marker.** Report `base`, `head`, and `permission` verbatim, then emit:

```text
<UPSTREAM_TARGET base="<base>" head="<head>" permission="<permission>" classification="<classification>" />
```

A later stage reads this marker instead of resolving again. Emit it for every classification, including one that stops the contribution, so a stage that follows knows the answer without repeating the search.

**Step 3 — Act on the classification.**

| `classification`        | Meaning                                                         | Action                                                                              |
| ----------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `upstream-contribution` | A base the operator does not control, and one head to push from | Continue. The contribution proceeds under `/contribution-standards` `<invariants>`. |
| `head-ambiguous`        | Several forks of the base, across the operator's accounts       | STOP. Report every entry in `fork.matches`; choosing among them is the operator's.  |
| `fork-absent`           | No fork of the base under any account the operator holds        | STOP. Report `fork.candidates` and the exact `gh repo fork` command.                |
| `controlled`            | `ADMIN`, `MAINTAIN`, or `WRITE` on the base                     | STOP. A repository the operator controls belongs to its own workflow.               |
| `blocked`               | Permission unreadable, or `gh` unavailable or unauthenticated   | STOP and report the resolver's `detail` verbatim.                                   |

</workflow>

<constraints>

- MUST run the resolver once per contribution and emit the marker from its output.
- MUST report `base`, `head`, and `permission` verbatim from the resolver.
- NEVER reconstruct the classification from `gh` output read by eye.
- NEVER select among several forks — report them and stop.
- NEVER treat a git remote, the authenticated account, or a successful push as evidence of permission on the base.

</constraints>

<success_criteria>

- The resolver ran once, and the `base`, `head`, and `permission` reported match its JSON output field for field.
- One `<UPSTREAM_TARGET>` marker carries those same values and the classification the resolver printed.
- A `head-ambiguous` result named every match and selected none.
- A `fork-absent` result named the candidate destinations and the fork command.
- `controlled` and `blocked` each stopped, and `blocked` reported the resolver's `detail` verbatim.

</success_criteria>
