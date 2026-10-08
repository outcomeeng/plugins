# Issues: Artifact Registry

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The registry reader exceeds the shipped-script size threshold

The registry reader in the provider skill holds the rendered-registry loader, the field vocabulary, the per-path selection rule with its specificity ranking, and the per-path selection record. [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) holds that a generic shipped script beyond fifty lines is debt awaiting extraction into the SPX CLI once it proves its value. The reader is generic, deterministic, standard-library-only and agent-neutral, and the implementation-audit scope resolver executes it.

The extraction shares its target with the scope resolver's recorded fold in `spx/21-spec-tree.enabler/68-audit.enabler/ISSUES.md`: once SPX resolves an implementation-audit scope from a selector at `spx verification run start`, the registry selection is one more field of that resolution, and the rendered registry and its reader move into the published CLI together with the resolver. Until that capability is published and the repository floor advances, the reader ships as a stdlib script under [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md), and no consumer carries a second copy.

**Impact.** A script past the threshold stays in the shipped plugin and in every consumer checkout, and the scope resolver and the reader stay separate artifacts until the CLI absorbs both.

**Settlement condition.** SPX reads the marketplace's registry document and returns each resolved path's selection through its scope resolution, no bundled reader script or rendered data file ships, and the scope resolver reads the selection from the CLI.

**Evidence.** The Change `outcomeeng/changes#337` records the reader's size debt and its fold into the scope resolution.

## The specs kind detects only the 4.x spec form

The specs kind selects `spx/**/*.spec.md`. A tree authored under the 3.x grammar carries `{slug}.md` specs beside decision records, `ISSUES.md` notes and other Markdown files in the same directory, so no path pattern separates them, and `spx/21-spec-tree.enabler/ISSUES.md` records this tree's migration to the 4.x grammar as open. The product root, the 3.x node specs of this repository and the `{slug}.md` specs of every consumer on the 3.x grammar select nothing, so an implementation audit accounts for their paths as unmatched.

**Impact.** The `spec-tree:audit-specs` skill is never named in the accounting units of a changeset that edits a 3.x spec.

**Settlement condition.** The registry detects a spec in the form every supported grammar carries, either through a detection that separates the `{slug}.md` spec of a node directory from the other Markdown it holds or through the tree migration that leaves one spec form, and a mapping case selects `audit-specs` for a spec path of each form.
