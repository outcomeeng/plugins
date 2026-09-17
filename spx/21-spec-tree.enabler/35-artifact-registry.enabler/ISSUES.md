# Issues: Artifact Registry

## The registry reader crossed the shipped-script size threshold

`src/plugins/spec-tree/skills/select-artifacts/scripts/select_artifacts.py`
is 201 lines: the rendered-registry loader, the field vocabulary, the
per-path selection rule with its specificity ranking, the
extension-to-kind derivation, and the per-path selection record.
`spx/12-shipped-scripting.adr.md` holds that a generic shipped script beyond
fifty lines is debt awaiting extraction into the SPX CLI once it proves its
value. The reader is generic, deterministic, standard-library-only, and
agent-neutral, and two shipped consumers already execute it: the
implementation-audit scope resolver and the instruction-block generator.

The extraction shares its target with the scope resolver's recorded fold in
`spx/21-spec-tree.enabler/68-audit.enabler/ISSUES.md`: once SPX resolves an
implementation-audit scope from a selector at `spx verification run start`,
the registry selection is one more field of that resolution, so the rendered
registry and its reader move into the published CLI together with the
resolver — SPX reads the marketplace's registry document and returns each
resolved path's selection — and the instruction-block generator reads the
enabled-language set from the same CLI. Until that capability is published
and the repository floor advances, the reader ships as a stdlib script under
`spx/13-plugin-and-runtime-conventions.adr.md`, and no consumer carries a
second copy.

**Resolution shape**: fold registry loading and per-path selection into the
SPX `verification run` scope resolution alongside the scope resolver, expose
the enabled-language derivation through the same CLI, then remove the bundled
script and the rendered data file, and re-point both consumers. Filed with the
SPX-side Change that carries the scope-resolution fold.

**Evidence.** `debt` finding `shipped-script-size-threshold` of the isolated
implementation audit on head `d81dac1c544a721a5f176e31905326d0a1385341`
(run `2026-09-17_12-56-32-108-e6765eac1e94`), which found the sibling
resolver's record and none for this script.
