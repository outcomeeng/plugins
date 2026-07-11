---
name: slice
description: >-
  ALWAYS invoke this skill when selecting the next executable slice to implement
  or deciding which spec-tree nodes /apply should build next from an
  implementation plan. NEVER choose the next nodes by ad hoc selection — this
  skill scopes an existing plan to demonstrable value before /apply runs.
---

<objective>
The next executable observable slice — a path through existing spec-tree nodes whose merged result demonstrates business and user value — selected from an implementation plan and handed to `/apply` as its work queue.
</objective>

<observable_slice>
A slice is observable when its merged result can be shown to the operator as a concrete increment of business and user value — a capability they can see work, not a layer or a refactor that only makes sense alongside later work.

- The slice boundary is the value boundary, not a convenient stopping point. A slice that lands code but demonstrates nothing is mis-scoped.
- A slice spans one or more `/merge` cycles. A single observable increment may take several merges to deliver; the slice is the whole coherent set, not one merge.
- A slice is a path through nodes that already exist in the durable map. Selecting a slice never creates, splits, re-scopes, or reindexes nodes — that is `/decompose`.

</observable_slice>

<workflow>

<step number="1" name="Load methodology" frequency="once per session">
Invoke `/understand`. Skip when the `SPEC_TREE_FOUNDATION` marker is already present.
</step>

<step number="2" name="Load tree context">
Identify the candidate area the plan touches, then invoke `/contextualize` on the lowest common ancestor of the nodes the plan reaches. Load the existing nodes, their ancestry, and the governing decisions — the slice is selected from nodes that already exist, so their current specs and ordering constrain what a coherent increment can be.

When the plan names no existing node — the work needs nodes that do not exist yet — stop and route to `/decompose` (to compose the structure) or `/author` (to create a node), then return. Slice selection operates over an existing tree.
</step>

<step number="3" name="Select the slice with the operator">
Invoke `/interview` to decide the slice. Reason to a recommendation first: the smallest coherent node set whose merged result demonstrates business and user value. Ask the operator only what the plan, the specs, and the loaded context do not settle — the value the next increment should demonstrate, and which of several coherent slices to take first.

Confirm with the operator:

- The demonstrable business and user value the slice delivers — stated as what the operator will be shown working.
- The node set that delivers it, and whether it spans one or several `/merge` cycles.
- The observable path: actor, invocation, inputs, product behavior, persisted or externalized result, and inspection surface.

</step>

<step number="4" name="Specify the slice">
Specify the selected slice fully:

- List the node set as full paths from the product's `spx/` root, in the ascending index order `/apply` will run them. Never list ad hoc files — the slice lives in the durable map.
- State the demonstrable-value statement the slice delivers.
- State the invocation, input shape, behavior, persistence or side effect, inspection surface, first useful failure behavior, and verification gates.
- Tie every dependency in the slice to the observable path. Infrastructure that does not enable the path belongs outside the slice.

Specify later slices only where they constrain the current slice's architecture, interfaces, or constraints. Treat the rest of the program under the cone of uncertainty — naming a later slice's effect on a current interface is in scope; designing a later slice's internals is not.
</step>

<step number="5" name="Boundary check">
Confirm the slice changes no durable tree structure. If selecting the slice surfaced a need to create, split, re-scope, or reindex a node, that is `/decompose` (structure) or `/author` (a new node) — stop, route there, and resume slice selection over the updated tree. Slice selection chooses an execution path across nodes that already exist; it never restructures them.

Confirm that delivering the slice makes one real invocation more useful and inspectable than before. A dependency-ordered list of infrastructure without that observable path is not an executable slice.
</step>

<step number="6" name="Hand off to apply">
Hand the selected slice's node set to `/apply` as its work queue. `/apply` runs the per-node TDD flow over each node in ascending index order, then carries the changeset through `/merge`.
</step>

</workflow>

<constraints>

- NEVER create, split, re-scope, or reindex a node during slice selection — node boundaries, ordering evidence, and indices belong to `/decompose`.
- NEVER express a slice as a list of files — express it as a path through existing nodes, addressable by full path from the product's `spx/` root.
- NEVER scope a slice to a stopping point that demonstrates no value — the slice boundary is the value boundary.
- NEVER over-specify later slices — specify them only where they constrain the current slice's architecture, interfaces, or constraints.
- ALWAYS decide the slice with the operator — slice selection is an operator decision the preflight surfaces, not a unilateral pick.

</constraints>

<success_criteria>

- [ ] The slice's demonstrable business and user value is stated and confirmed with the operator
- [ ] The slice names its actor, invocation, inputs, behavior, externalized result, inspection surface, failure behavior, and verification
- [ ] Every dependency is justified by the observable path
- [ ] The slice is expressed as an ordered node set of full paths, not a file list
- [ ] Later slices are specified only where they constrain the current slice's architecture, interfaces, or constraints
- [ ] No durable tree structure was created, split, re-scoped, or reindexed — any such need was routed to `/decompose` or `/author`

</success_criteria>
