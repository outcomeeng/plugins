# Plan Slice

PROVIDES selection of the next executable observable slice from an implementation plan — a coherent set of changesets, spanning one or more merges, that delivers demonstrable business and user value
SO THAT the per-node TDD flow (`spx/21-spec-tree.enabler/65-apply.enabler/54-node-flow.enabler`)
CAN run against a work queue scoped to a value-bearing increment rather than an ad hoc node selection

## Assertions

### Compliance

- ALWAYS: any implementation plan triggers slice selection before implementation begins — the selection is an applying preflight the operator and session decide together, not a step the per-node flow performs ([audit])
- ALWAYS: express the selected slice as a path through existing spec-tree nodes, addressable by full path from `spx/`, rather than as an ad hoc list of files — the slice is located in the durable map ([audit])
- ALWAYS: scope the slice to an observable increment — a coherent set of changesets, across one or more `/merge` cycles, whose delivered business and user value the operator can be shown; the slice boundary is the value boundary, not a convenient stopping point ([audit])
- ALWAYS: fully specify the next executable slice, and specify later slices only where they constrain the current slice's architecture, interfaces, or constraints — later slices are treated under the cone of uncertainty, not over-specified ([audit])
- ALWAYS: hand the selected slice's node set to the per-node TDD flow as its work queue — slice selection feeds `spx/21-spec-tree.enabler/65-apply.enabler/54-node-flow.enabler`, which runs each node in ascending index order ([audit])
- NEVER: create, split, re-scope, or reindex durable tree structure during slice selection — node boundaries, ordering evidence, and indices belong to `/decompose`; plan-slice selects an execution path across nodes that already exist ([audit])
