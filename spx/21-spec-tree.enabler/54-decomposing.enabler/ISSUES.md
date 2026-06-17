# ISSUES — Decomposing (archetype library)

Known issues and deferred decisions for the archetype-library work under `/decompose`. Coordination
note: verify each entry against the specs, decisions, and current intent before acting on it.

## Archetype manifest format: TOML now, ruamel.yaml the deferred alternative

The archetype manifests use TOML (`archetype.toml`, for recognition signals + outcome topology +
concern gates) paired with JSON (`seed-tree.json`, for the nested tree IR). TOML was chosen for stdlib
parsing (`tomllib`, 3.11+), the repo's existing config/data precedent (`eval.toml` + `cases.jsonl`),
and comment support for the human-tuned signals. The cost: TOML is poor at nested data, which forces
the toml-config + json-tree split across two machine formats (plus the markdown human surface).

The Plugin Portability Constraints (`AGENTS.md`) forbid non-stdlib parsers, so YAML is currently off
the table. If a future need wants a single richer human-editable nested format for archetype
manifests, the mature option is **ruamel.yaml**:

> ruamel.yaml is a YAML 1.2 loader/dumper derived from PyYAML. Critically, its pure Python
> implementation is fully YAML 1.2 compliant, just slower than the C path. Force the pure Python
> implementation with `pure=True`; otherwise it uses the faster C library when available, and that C
> code was split out into a separate package, `ruamel.yaml.clib`, so the core install doesn't require
> it. It has years of production use, a tox- and pytest-based test suite, and is actively maintained.
> License is MIT, so vendoring is fine. The real costs: it's a sizable package rather than a drop-in
> file (scanner, parser, composer, constructor, resolver, emitter, plus round-trip machinery), and it
> lives under the `ruamel` namespace — if you vendor it you'll want to rename the package to avoid
> colliding with any system-installed copy, and force `pure=True` so you can leave `clib` out
> entirely.

**Trigger to revisit:** archetype manifests need richer nested human-editable structure than the
toml+json split expresses cleanly, or a consumer wants one round-trippable format for both signals and
tree. **Resolution shape:** vendor ruamel.yaml (renamed namespace, `pure=True`, no `clib`) under the
plugin tree, or accept the toml+json split as permanent.

## Archetype library ships without a skill-level invocation path (router deferred)

The archetype library (`references/archetypes/{toolchain,website,platform}/`) ships as reference
material, but `/decompose` has no step that consults it: no read directive, no classification phase,
no mention of `archetype.toml` or `seed-tree.json`. The READMEs and `archetype.toml` recognition
fields describe "the router" that matches a product's signals — that router does not exist yet. Until
it lands, an agent is not pointed at these references by the skill; they are reachable only when an
operator names them.

This is intentional sequencing: the router (a classify → match → seed front phase in
`/decompose` keyed on `spx/` as the target, plus an `archetype.py` signal matcher and a thin
`decomposer` agent) is the next build step after the library. The library was extracted first so the
seeds it instantiates exist before the consumer that reads them.

**Trigger to revisit:** the router step is built. **Resolution shape:** add the classify/seed front
phase to `decomposing/SKILL.md`, the `archetype.py` matcher, the `decomposer` agent, and `[eval]`
classification cases; at that point the recognition fields and seed trees become reachable from the
skill and this entry is removed.
