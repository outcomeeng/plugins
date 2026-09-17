# Issues: Artifact Registry

## Two shipped scripts each spell the rendered registry's field names

`src/plugins/spec-tree/skills/audit-implementation/scripts/resolve_scope.py` reads the rendered registry through its own `RegistryField` enum, and `src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py` through its own `_REGISTRY_*_FIELD` constants; `outcomeeng/distribution/artifact_registry.py` owns the vocabulary the build renders. Two shipped copies of the document's field names can drift from the declaration without any check noticing, because a shipped script runs in a consumer checkout that carries no `outcomeeng` package.

**Evidence.** Whole-changeset self-review of the artifact-registry changeset against `python:python-standards` source-ownership rules, after the fourth implementation audit.

**Settlement condition.** One provider skill ships the registry reader and its rendered data file, and every consuming skill reaches it from its own `scripts/` entrypoint by a `__file__`-relative import, as `spx/13-plugin-and-runtime-conventions.adr.md` prescribes for logic two skills each execute; or the build renders the field-name vocabulary into each consumer beside the document. Either is a Frame change — the Change declares two rendered data files and no provider skill — so it belongs to a successor Change refined from #64.
