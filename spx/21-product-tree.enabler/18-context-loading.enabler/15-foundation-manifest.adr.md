# Foundation Resource Manifest

The product-tree plugin package identifies its methodology resource surface through an authored machine-readable manifest at the package-relative path `skills/understand/manifest.json`: JSON carrying an integer `schema_version`, exactly one package-relative core entry naming the consolidated foundation document `skills/understand/SKILL.md`, three deterministically ordered, duplicate-free catalogs of package-relative extended resource paths — references, templates, and examples — in curated reading order, and one package-relative `compact_recovery` entry naming the post-compaction reminder resource `skills/understand/compact-recovery.md`. The `compact_recovery` entry is an additive shape change within schema version 1, follows the snake-case spelling of the existing `schema_version` key, and names the resource without carrying its text. The manifest is metadata only and never duplicates, summarizes, or restructures the foundation document body; within a schema version the shape evolves additively, and a breaking shape change increments `schema_version`. Package checks validate the shipped manifest in every generated tree so every declared path exists, the `compact_recovery` entry names a shipped file, and every shipped extended resource is declared.

## Rationale

The SPX CLI consumes the package's resource surface as structured package data — the same trusted-third-party structured-data boundary [`spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md`](spx/21-product-tree.enabler/18-context-loading.enabler/13-context-enumeration.adr.md) establishes for tree enumeration — rather than parsing skill prose or inferring resource groups from directory layout, while authored curation keeps catalog order meaningful and package-check validation closes the drift between the manifest and the shipped files. The post-compaction reminder resource is named in the same manifest because the manifest is the one surface through which the SPX CLI and the `SessionStart` hook's compact entry locate shipped methodology resources, package checks then keep the named file present in every generated tree, and the hook command carries a path and no prose. The entry is additive within schema version 1 because a consumer that ignores unknown keys is unaffected by it.

## Invariants

- Exactly one core entry names the consolidated foundation document; the catalogs carry no duplicate paths and preserve their authored order.
- Within a schema version the manifest shape evolves additively; a breaking shape change increments `schema_version`.
- The authored manifest ships verbatim into every generated tree.
- Exactly one `compact_recovery` entry names the package-relative reminder resource `skills/understand/compact-recovery.md`; the entry is metadata only and the resource it names ships in every generated tree.

## Verification

- ALWAYS: the manifest carries exactly one package-relative `compact_recovery` entry naming `skills/understand/compact-recovery.md`, and package checks reject a shipped manifest whose `compact_recovery` entry is absent or names a file a generated tree lacks
- NEVER: the `compact_recovery` entry carries the reminder's text — it names the resource and holds a path only

### Testing

- ALWAYS: the product-tree plugin ships `skills/understand/manifest.json` in every generated tree, declaring an integer `schema_version`, exactly one core entry naming the consolidated foundation document, and the references, templates, and examples catalogs as ordered arrays of package-relative paths ([conformance])
- ALWAYS: package checks validate the shipped manifest — parse validity, a known `schema_version`, exactly one core path, every declared path resolving to a file in the generated tree, no duplicate paths, and every file under the understand skill's `references/`, `templates/`, and `examples/` directories declared in its catalog ([compliance])
- NEVER: the manifest duplicates, summarizes, or restructures foundation or resource content — it carries paths and schema metadata only ([compliance])
- NEVER: the authored manifest and its generated-tree copies diverge — the build ships the authored file verbatim into every generated tree ([compliance])

### Audit

- ALWAYS: a manifest shape change within a schema version is additive; a breaking shape change increments `schema_version` ([audit])
