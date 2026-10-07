# Marketplace PR Rules

Loaded by `/open-pr` in this repository. These additions preserve the parent
protocol's verification, review, branch-safety, and publication gates.

## Plugin version policy

A changeset warrants a plugin bump when it changes authored content under
`src/plugins/<name>/`, generated content under `dist/claude/<name>/` or
`dist/codex/<name>/`, or a `src/_shared/` fragment attributed to the plugin
through its authored include directives.

Changes confined to marketplace catalogs, `spx/`, coordination notes, root
`AGENTS.md` or `CLAUDE.md`, local overlays, tests, validation configuration,
or generated repository docs
warrant no plugin bump. The marketplace sync wrapper uses the same distribution
boundary: those changes alone do not refresh plugin caches.

The managing protocol owns version writes, at merge time. The PR opens
without a version commit. Ordinary commits neither initiate a bump nor ask for
one. Never hand-edit a manifest `version` field: `just bump` writes each
affected plugin's source manifests (`.claude-plugin/plugin.json` and
`.codex-plugin/plugin.json`) in lockstep.

### Segment selection

- **MAJOR** requires an explicit operator request.
- **MINOR** covers adding, removing, or renaming a skill, thin agent, or manifest,
  and major functional changes or significant user-experience improvements.
- **PATCH** is the default for other plugin-distribution changes, including
  fixes, refactoring, installed documentation, and small enhancements.

Auto-detection recognizes structural additions, removals, and renames as
`minor`, and other changes as `patch`; it never selects `major`. A
non-structural major functional change or significant user-experience improvement
therefore needs the explicit `minor` argument.

The recipes accept positional `base_ref` (default `origin/main`) and then
`segment` (default auto-detection):

```bash
just bump-dry
just bump
just bump-check
just bump origin/main minor
```

Use the selected base's remote ref for a stacked branch. The segment is the
second positional argument; recipe flags such as `--segment` and
`segment=minor` are invalid.

## No version commit before opening

The opening protocol writes no version. A changeset that warrants a bump opens
its PR on verified content, and the version commit follows when the content is
final. `spx/local/merging.md` declares that step for `/manage-pr`, which reads
that overlay during open-PR management. The plugin version policy above
supplies its distribution boundary and segment selection.

A changeset with no plugin-distribution change skips version writing and its
version commit. It still passes the opening protocol's other checks.

`just bump-check` verifies that affected manifests agree and are ahead of the
base. The full CI gate does not run this comparison; the merge-time check is
required even when all CI-related verification is green.

## Other pre-flight additions

Verify these conditions before opening, alongside the parent protocol's checks:

| Check                                                                                                  | If failing                                                                       |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Touched-scope verification selected by `spx/local/merging.md` and `AGENTS.md` passes on the final head | Fix the failing lane before publication.                                         |
| Both marketplace catalogs reflect added or removed plugins                                             | Update `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. |
| The `README.md` skill and thin-agent catalog matches changed artifacts                                 | Regenerate the catalog through the command in `AGENTS.md`.                       |
| The instruction-block template reflects changed skill structure                                        | Update its authored template and regenerate through the commands in `AGENTS.md`. |

Marketplace catalogs are edited for plugin additions, removals, or discovery
changes; a version bump alone does not require catalog edits.
The full gate checks that plugin directories appear in both catalogs.

## Required body sections

Append to the default template from `/open-pr`:

```text
## Versioning

- <plugin>: <MAJOR | MINOR | PATCH>, written before merge

## Validation

- [ ] Touched-scope deterministic verification passes
- [ ] `/reload-plugins` confirms the change loads in a running session
```

Drop **Versioning** when no `plugin.json` files changed. For a changeset that
ships no plugin content, record plugin reload as not applicable.
