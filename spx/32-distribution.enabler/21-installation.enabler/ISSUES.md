# ISSUES — installation

Known defects in the installation node. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

## A tagged assertion sits outside a claim-shape heading

`installation.md` carries a tagged assertion directly under `## Assertions` with no claim-shape heading: the correspondence between each supported agent's selection and its plan, linking `tests/test_installation.mapping.l1.py`. The node-spec form groups every routed assertion under the heading naming its claim shape, and untagged authoring drafts are the only entries a spec keeps ungrouped. The spec declares no `### Mappings` heading, so the repair adds that heading and moves the assertion under it rather than relocating it to an existing group.

**Resolution shape**: add `### Mappings` to `installation.md` and move that assertion under it, leaving the untagged declarations above and the existing `### Compliance` group unchanged.

**Why separate**: the same shape in the child node `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler` was repaired where its `### Scenarios` heading already existed. This node's instance needs a new heading in a spec no changeset touched, so it is recorded rather than repaired there.

**Evidence**: surfaced by the spec audit of the child node on head `74daf924ea1e27fcf84ddc813bfed715bb14d611`, whose finding named this spec as the second instance of the same class.
