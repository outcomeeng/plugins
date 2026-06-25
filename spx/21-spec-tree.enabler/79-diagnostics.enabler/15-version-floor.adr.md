# spx Version Floor

The diagnose manifest carries the required `spx` version floor, and that floor
is the product's single source of truth for the `spx` version its shipped skills
depend on. The plugin build renders the floor into the shipped manifest, and
`spx diagnose` compares the installed `spx` version against that manifest field
inside its `spx-reachability` check.

## Rationale

The shipped diagnose skill runs in a consumer checkout that contains only the installed plugin tree, so the floor it judges against must travel inside that tree — a product-internal constant the consumer never receives cannot be read at runtime. The build renders source through a template pass, so injecting the floor as a template value keeps one source of truth: the floor rises only where the product declares it, and the shipped skill re-renders from that same value, so the shipped floor cannot drift from the floor the product enforces in CI.

The floor judgment belongs in `spx-reachability` because that check reads
`spx --version` — the only surface a floor comparison needs — so a below-floor
degraded verdict extends the verdict it produces rather than adding a second
check that re-reads the same command. A field in the runtime plugin manifest is
rejected: that manifest's schema is the runtime's, an unknown field risks the
runtime validator rejecting it, and the value would still need syncing with the
source of truth. The diagnose manifest is a distinct, product-owned data file
the build renders the floor into. Hand-duplicating the floor in the shipped tree
is rejected for the same drift it invites.

## Invariants

- The floor the shipped check judges against is identical on every build target — it is a single source-owned value, not a runtime-divergent name.

## Verification

### Audit

- ALWAYS: the floor the `spx-reachability` check judges against is the product's single source-of-truth spx-version floor, rendered into the shipped diagnose manifest by the plugin build's template pass and identical on every target ([audit])
- ALWAYS: the spx version-floor judgment folds into the `spx-reachability` check as a below-floor degraded verdict, because both it and the existing reachability verdict read the same `spx --version` surface ([audit])
- NEVER: the shipped floor is hand-duplicated in the plugin tree or declared in a field of the runtime plugin manifest whose schema the runtime owns — it is build-rendered into the diagnose manifest from the single source of truth so it cannot drift from the floor the product enforces ([audit])
