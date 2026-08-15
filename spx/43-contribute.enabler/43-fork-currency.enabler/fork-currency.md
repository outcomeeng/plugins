# Fork Currency

PROVIDES the head repository's default branch brought current with the base repository's
SO THAT an operator maintaining a long-lived fork
CAN keep its default branch a faithful copy of the base without inspecting how far it has fallen behind

A fork's default branch exists to mirror the base repository's. A fork whose default branch has fallen behind still serves contributions, because a contribution branch is cut from the base repository's default branch rather than the fork's, so currency is maintenance rather than a precondition.

A fork's default branch that carries commits absent from the base is not behind — it is diverged, and someone committed there. Bringing it current would discard that work.

## Assertions

### Compliance

- ALWAYS: the head repository's default branch is synced from the base repository's default branch, resolved through the fork's parent rather than a remote name ([audit])
- NEVER: a sync discards commits — a head default branch carrying commits absent from the base stops the flow with those commits named ([audit])
- NEVER: currency of the head default branch is treated as a precondition for opening a contribution, which is cut from the base default branch ([audit])
