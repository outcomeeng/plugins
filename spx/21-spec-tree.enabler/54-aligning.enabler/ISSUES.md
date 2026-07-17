# Issues

## Evidence-mechanism specialization is conflated with cross-cutting duplication

The `/align` audit flags a child node's `[test]`-evidence compliance rule as a "cross-cutting invariant in child" finding when an ancestor decision record carries a `[review]`-evidence rule with overlapping content. The two rules are not the same artifact: `[review]` is human/agent semantic judgment, `[test]` is automated falsification. A child `[test]` rule that concretizes an ancestor `[review]` rule against a specific code surface is legitimate evidence-type specialization, not placement debt.

### Concrete example

The marketplace ADR `spx/13-plugin-and-runtime-conventions.adr.md` carries:

- `NEVER: Invoke or document gh run watch as an actionable instruction or include it in a code fence ... ([review])`
- `NEVER: Write polling waits in helpers ... while ... : time.sleep(N) in Python, until <check>; do sleep N; done in shell ... ([review])`

The child node `spx/21-spec-tree.enabler/13-infrastructure.enabler/22-github-actions.enabler/32-workflow-observability.enabler/workflow-observability.md` carries:

- `NEVER: helper modules invoke or reference gh run watch ... ([test])`
- `NEVER: helper modules implement polling waits — while ... : time.sleep(...) constructs are absent ([test])`

The ADR rule binds marketplace-wide and is verified by audit. The child rule binds the three Python helpers under that node and is verified by automated grep. The child rule is a stronger guarantee at a smaller scope; the ancestor rule is a weaker guarantee at a broader scope. Removing either weakens the verification stack.

The `/align` audit flagged both child rules as cross-cutting duplications of the ADR. That flag is incorrect — live `/understand` `<common_misplacements>` governs *where content lives*, not *what evidence verifies it*. Two rules with the same content but different evidence types serve different purposes.

### What needs to change

`/align`'s placement check (or the rule definition in `<common_misplacements>`) needs to recognize evidence-mechanism specialization:

- Same content + same evidence at child and ancestor → cross-cutting duplication finding (current behavior, correct)
- Same content + child `[test]` concretizing ancestor `[review]` → legitimate specialization (current behavior flags as duplication, incorrect)

A possible discriminator: when a child node's compliance rule references a specific code surface (helper module, file path, function name) that the ancestor rule does not name, and tags the child rule with `[test]`, the rule is a specialization. The ancestor's `[review]` evidence remains the marketplace-wide guarantee; the child's `[test]` adds a falsifiable check.

### Why this matters

Mechanically removing every child rule that overlaps content with an ancestor strips automated verification from the tree. The github-actions decomposition pulled three `[test]`-evidence rules at `32-workflow-observability` from the original audit because the ancestor ADR carried `[review]`-evidence equivalents — the user blocked the removal by pointing out that `[review]` at a higher level is not equivalent to `[test]` at a lower level. Future audits without this discriminator will repeat the mistake.
