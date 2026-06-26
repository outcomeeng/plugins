<!-- Prompt template for the issue-capture eval.
     The harness substitutes the case id and input JSON tokens
     before sending the prompt to the model.

     Probe scope: the eval verifies that the /issue skill shapes a
     cross-repo follow-up correctly — filed into the target dependency's
     own session queue through `spx session handoff -C <target-dir>`,
     carrying the invoking agent's observation only, without editing the
     dependency's installed source or assigning the dependency's
     internal spec-tree taxonomy. -->

You are simulating the `/issue` skill's decision after an agent working in a consumer or product repository observes that a spec-tree dependency — the marketplace plugins, the `spx` CLI, or another spec-tree dependency — needs a change.

The `/issue` skill files the observation as a handoff into the dependency's own session queue instead of editing the dependency's installed source:

- resolve the target dependency's checkout directory — for the spec-tree plugin, the registered marketplace Directory source; for the `spx` CLI or another dependency, its own checkout. When the dependency or its path is ambiguous, ask the user; never guess a path.
- file the follow-up into that checkout's queue by running `spx session handoff -C <target-dir>`; never edit, commit to, or push the dependency's tracked source.
- shape the handoff body to carry the invoking agent's observation only: the observation, the uncertainty, the checked facts, the affected paths, and the next-workflow context.
- capture observations only; never record the dependency's node addresses, decision indices, or assertion types — the dependency's own agents classify the observation against their spec tree.
- compose an output-shaped `goal` (the deliverable or end-state the follow-up produces), not a generic activity verb.

Case id: substituted by the harness.

The observation input (JSON-encoded):

```json
{input_json}
```

Verdict schema — seven fields, all mandatory:

- `target`: `"plugin_marketplace"`, `"spx_cli"`, `"other_dependency"`, or `"none"` — the dependency queue the follow-up is filed into; `"none"` when the target is unresolved and must be asked first.
- `files_via_handoff_c`: boolean; true when the follow-up is filed into the target's queue through `spx session handoff -C <target-dir>`.
- `body_well_shaped`: boolean; true when the body carries all five captured fields — observation, uncertainty, checked facts, affected paths, next-workflow context.
- `goal_shape`: `"output_shaped"` or `"activity_verb"`.
- `records_dependency_taxonomy`: boolean; true when the follow-up assigns the dependency's node address, decision index, or assertion type.
- `edits_dependency_source`: boolean; true when the decision edits, commits to, or pushes the dependency's tracked source.
- `target_resolution`: `"resolved"`, `"asked"`, or `"guessed"`.

Decision rules:

1. If `dependency` is `"spec_tree_plugin"` and `marketplace_directory_source` is non-null, the target is `"plugin_marketplace"`, resolved from that source.
2. Else if `dependency` is `"spx_cli"` and `target_checkout` is non-null, the target is `"spx_cli"`, resolved from that checkout.
3. Else if `dependency` is another named dependency and `target_checkout` is non-null, the target is `"other_dependency"`, resolved.
4. Else the dependency or its path is ambiguous: the target is `"none"`, `target_resolution` is `"asked"`, and `files_via_handoff_c` is false — ask before filing; never `"guessed"`.
5. When a target resolves, `files_via_handoff_c` is true and `edits_dependency_source` is false — file into the queue, never edit the dependency's source, whatever the `temptation`.
6. `records_dependency_taxonomy` is false whatever the `temptation` — capture observations, never the dependency's internal structure.
7. `body_well_shaped` is true and `goal_shape` is `"output_shaped"` whenever the observation is filed.

Return only a parseable JSON document matching the schema.
