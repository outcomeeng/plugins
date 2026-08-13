# Issues

## The align eval-lane skip hides undeclared Markdown inside canonical eval directories

The `/align` discover step excludes every file inside an `evals/` directory sitting directly under a node directory, and the `<file_classification>` skip list mirrors that blanket exclusion. The closed artifact taxonomy admits only the artifacts each `eval.toml` declares (case, prompt, and template paths) plus the harness-generated files, so an undeclared free-form document such as `evals/{rule-slug}/notes.md` is misplaced content — yet the blanket directory skip removes it from the scan before classification, and a full-tree alignment reports clean.

**Resolution shape**: during discovery, resolve each `eval.toml`'s declared eval-relative paths and skip only those artifacts plus the harness-generated `history.jsonl`, leaving undeclared Markdown inside the eval directory in scope to be reported. This changes the discover step from static glob exclusions to per-eval declaration resolution, which is why it is a separate capability slice rather than a skip-list edit.

**Why tracked**: surfaced by the Codex reviewer on PR #517 (review-thread comment `3774887664`, head `42d0a9c865ea338a5e0cd259ba9387544b4a094a`); dispositioned as tracked debt by operator direction on that PR's round-six findings. The fix requires `/align` to parse `eval.toml` during discovery — a discover-algorithm capability change owned by this node, outside the closed-taxonomy changeset's bounded concern.

## Evidence-mechanism specialization is conflated with cross-cutting duplication

The `/align` audit flags a child node's `[test]`-evidence compliance rule as a "cross-cutting invariant in child" finding when an ancestor decision record carries an `[audit]`-evidence rule with overlapping content. The two rules are not the same artifact: `[audit]` is agentic semantic judgment, `[test]` is automated falsification. A child `[test]` rule that concretizes an ancestor `[audit]` rule against a specific code surface is legitimate evidence-type specialization, not placement debt.

### Concrete example

The marketplace ADR `spx/13-plugin-and-runtime-conventions.adr.md` carries:

- `NEVER: a helper or skill instruction spawns a daemon, background keep-alive, streaming-log command, open-ended watcher, or agent-owned polling loop ... ([audit])`

The child node `spx/21-spec-tree.enabler/13-infrastructure.enabler/21-github-actions.enabler/32-workflow-observability.enabler/workflow-observability.md` carries:

- `NEVER: helper modules invoke or reference gh run watch ... ([test])`
- `NEVER: helper modules implement polling waits — while ... : time.sleep(...) constructs are absent ([test])`

The ADR rule binds marketplace-wide and is verified by audit. The child rules bind the Python helpers under that node and are verified by automated grep, each naming one concrete construct the broader ancestor rule covers by category. The child rule is a stronger guarantee at a smaller scope; the ancestor rule is a weaker guarantee at a broader scope. Removing either weakens the verification stack.

The `/align` audit flagged both child rules as cross-cutting duplications of the ADR. That flag is incorrect — live `/understand` `<common_misplacements>` governs *where content lives*, not *what evidence verifies it*. Two rules with the same content but different evidence types serve different purposes.

### What needs to change

`/align`'s placement check (or the rule definition in `<common_misplacements>`) needs to recognize evidence-mechanism specialization:

- Same content + same evidence at child and ancestor → cross-cutting duplication finding (current behavior, correct)
- Same content + child `[test]` concretizing ancestor `[audit]` → legitimate specialization (current behavior flags as duplication, incorrect)

A possible discriminator: when a child node's compliance rule references a specific code surface (helper module, file path, function name) that the ancestor rule does not name, and tags the child rule with `[test]`, the rule is a specialization. The ancestor's `[audit]` evidence remains the marketplace-wide guarantee; the child's `[test]` adds a falsifiable check.

### Why this matters

Mechanically removing every child rule that overlaps content with an ancestor strips automated verification from the tree. The github-actions decomposition pulled three `[test]`-evidence rules at `32-workflow-observability` from the original audit because the ancestor ADR carried `[review]`-evidence equivalents — the user blocked the removal by pointing out that `[review]` at a higher level is not equivalent to `[test]` at a lower level. Future audits without this discriminator will repeat the mistake.
