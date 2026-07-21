# Foundation Resource Manifest

The spec-tree plugin package publishes a machine-readable foundation-resource manifest at the package-relative path `skills/understand/manifest.json`: authored JSON carrying an integer `schema_version`, exactly one package-relative core entry naming the consolidated foundation document `skills/understand/SKILL.md`, and three deterministically ordered, duplicate-free catalogs of package-relative extended resource paths — references, templates, and examples — in curated reading order. The manifest is metadata only and never duplicates, summarizes, or restructures the foundation document body. Within a schema version the manifest shape evolves additively; a breaking shape change increments `schema_version`. Package checks validate the shipped manifest in every generated tree so every declared path exists and every shipped extended resource is declared.

## Rationale

A deterministic package consumer — the SPX CLI serving the methodology's core foundation and extended resources — reads the package's resource surface from explicit versioned package data rather than parsing skill prose or inferring resource groups from directory layout, while authored curation keeps catalog order meaningful and package-check validation closes the drift between the manifest and the shipped files.

## Product properties

1. A deterministic consumer resolves the single core foundation document and the ordered references, templates, and examples catalogs from `skills/understand/manifest.json` alone, without reading skill prose or enumerating directories.
2. The manifest identifies its shape by an integer `schema_version`; shape changes within a version are additive, and a breaking change increments the version.
3. Every declared path resolves inside the installed package and every shipped reference, template, and example file is declared, so the manifest and the shipped resource set never drift.

## Verification

### Testing

- ALWAYS: the spec-tree plugin ships `skills/understand/manifest.json` in every generated tree, declaring an integer `schema_version`, exactly one core entry naming the consolidated foundation document, and the references, templates, and examples catalogs as ordered arrays of package-relative paths ([conformance])
- ALWAYS: package checks validate the shipped manifest — parse validity, a known `schema_version`, exactly one core path, every declared path resolving to a file in the generated tree, no duplicate paths, and every file under the understand skill's `references/`, `templates/`, and `examples/` directories declared in its catalog ([compliance])
- NEVER: the manifest duplicates, summarizes, or restructures foundation or resource content — it carries paths and schema metadata only ([compliance])
- NEVER: the authored manifest and its generated-tree copies diverge — the build ships the authored file verbatim into every generated tree ([compliance])

### Audit

- ALWAYS: a manifest shape change within a schema version is additive; a breaking shape change increments `schema_version` ([audit])
