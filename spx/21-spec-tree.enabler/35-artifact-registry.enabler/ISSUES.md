# Issues: Artifact Registry

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The registry reader exceeds the shipped-script size threshold

The registry reader in the provider skill holds the rendered-registry loader, the field vocabulary, the per-path selection rule with its specificity ranking, and the per-path selection record. `spx/12-shipped-scripting.adr.md` holds that a generic shipped script beyond fifty lines is debt awaiting extraction into the SPX CLI once it proves its value. The reader is generic, deterministic, standard-library-only and agent-neutral, and the implementation-audit scope resolver executes it.

The extraction shares its target with the scope resolver's recorded fold in `spx/21-spec-tree.enabler/68-audit.enabler/ISSUES.md`: once SPX resolves an implementation-audit scope from a selector at `spx verification run start`, the registry selection is one more field of that resolution, and the rendered registry and its reader move into the published CLI together with the resolver. Until that capability is published and the repository floor advances, the reader ships as a stdlib script under `spx/13-plugin-and-runtime-conventions.adr.md`, and no consumer carries a second copy.

**Impact.** A script past the threshold stays in the shipped plugin and in every consumer checkout, and the scope resolver and the reader stay separate artifacts until the CLI absorbs both.

**Settlement condition.** SPX reads the marketplace's registry document and returns each resolved path's selection through its scope resolution, no bundled reader script or rendered data file ships, and the scope resolver reads the selection from the CLI.

**Evidence.** The Change `outcomeeng/changes#337` records the reader's size debt and its fold into the scope resolution.
