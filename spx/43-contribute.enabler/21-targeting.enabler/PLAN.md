# Plan

Governing decision: `spx/13-plugin-and-runtime-conventions.adr.md` (grant locality).

## Emit the consumer entrypoints from the build instead of authoring them

Each consuming skill carries `scripts/resolve_target.py`, and the five files are
byte-identical. The decision requires each skill to *carry* the entrypoint; it
does not require the file to be authored five times. The build already renders
`src/plugins/` into both generated trees, and copy-paste detection already
excludes those trees, so emitting the entrypoint per skill would remove the
duplication from the authored source rather than exclude it from measurement —
which is what `.sonarcloud.properties` does today.

The obstacle is the shared-fragment contract: `src/_shared/{topic}/` accepts
`fragment.md` only, so a Python body cannot be included from there. Extending
that contract to non-markdown fragments, or adding a fan-out emission for a
per-skill script, is a build capability with its own assertions and evidence —
larger than the changeset that surfaced it.

**Resolution shape**: extend the shared-fragment contract to typed fragments, or
add a per-skill script fan-out; author the entrypoint once; declare the relation
in `spx/local/generated-sources.toml`; then drop the entrypoint line from
`sonar.cpd.exclusions`. The domain the linked tests derive from each skill's own
grant declaration continues to work unchanged, because it reads the grant rather
than the file.

**Revisit condition**: when a second plugin needs the same provider-and-consumer
shape, since the exclusion does not generalize — each plugin would need its own
line.
