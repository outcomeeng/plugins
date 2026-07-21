# Foundation Resource Manifest

The spec-tree plugin package identifies its methodology resource surface through an authored machine-readable manifest at the package-relative path `skills/understand/manifest.json`: JSON carrying an integer `schema_version`, exactly one package-relative core entry naming the consolidated foundation document `skills/understand/SKILL.md`, and three deterministically ordered, duplicate-free catalogs of package-relative extended resource paths — references, templates, and examples — in curated reading order. The manifest is metadata only and never duplicates, summarizes, or restructures the foundation document body; within a schema version the shape evolves additively, and a breaking shape change increments `schema_version`. Package checks validate the shipped manifest in every generated tree so every declared path exists and every shipped extended resource is declared.

## Rationale

The SPX CLI consumes the package's resource surface as structured package data — the same trusted-third-party structured-data boundary `spx/21-spec-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md` establishes for tree enumeration — rather than parsing skill prose or inferring resource groups from directory layout, while authored curation keeps catalog order meaningful and package-check validation closes the drift between the manifest and the shipped files.

## Invariants

- Exactly one core entry names the consolidated foundation document; the catalogs carry no duplicate paths and preserve their authored order.
- Within a schema version the manifest shape evolves additively; a breaking shape change increments `schema_version`.
- The authored manifest ships verbatim into every generated tree.

## Verification

### Testing

- ALWAYS: the spec-tree plugin ships `skills/understand/manifest.json` in every generated tree, declaring an integer `schema_version`, exactly one core entry naming the consolidated foundation document, and the references, templates, and examples catalogs as ordered arrays of package-relative paths ([conformance])
- ALWAYS: package checks validate the shipped manifest — parse validity, a known `schema_version`, exactly one core path, every declared path resolving to a file in the generated tree, no duplicate paths, and every file under the understand skill's `references/`, `templates/`, and `examples/` directories declared in its catalog ([compliance])
- NEVER: the manifest duplicates, summarizes, or restructures foundation or resource content — it carries paths and schema metadata only ([compliance])
- NEVER: the authored manifest and its generated-tree copies diverge — the build ships the authored file verbatim into every generated tree ([compliance])

### Audit

- ALWAYS: a manifest shape change within a schema version is additive; a breaking shape change increments `schema_version` ([audit])
