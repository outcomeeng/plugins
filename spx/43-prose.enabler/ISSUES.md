# Issues: Prose Plugin

## Eval evidence for the prose surface stays deferred

The kind-detection and style-adherence evals for the prose surface remain unwritten by operator decision: the eval harness is under repair in a separate concurrent effort, and no spec node names that effort yet, so this entry is the owning record rather than a pointer. Revisit when the eval surface is operational.

## `prose.md` exceeds the assertion-count decompose guidance (RESOLVED)

**Resolved by re-scope, the second of the two shapes this entry named.** The
kind-detection concern left the node entirely — the kind is now an input both
routers receive — so the cluster the entry identified as separable no longer
exists to separate. What remained collapsed to one rule per assertion: the
verdict contract absorbed the kindless-dispatch case it had stated separately,
and the three surface exclusions merged into the single ownership boundary they
always were. `spx/43-prose.enabler/prose.md` carries 7 assertions, inside the
guidance, with no `/decompose` pass.

**Evidence.** Surfaced by the changes reviewer on the prose router-surface
changeset (sealed review run `2026-08-05_21-08-16-860-5bf3b83599ce`, PR #501).
