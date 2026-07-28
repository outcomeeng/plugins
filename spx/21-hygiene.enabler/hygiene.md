# Hygiene

PROVIDES the pre-commit hygiene operations that keep the working tree clean — markdown formatting fixers run by lefthook and on-demand workspace cleanup
SO THAT contributors and CI
CAN commit consistent markdown and reclaim disk space from gitignored caches without remembering ad-hoc shell incantations

The `outcomeeng.hygiene` package collects operations whose purpose is to remove or normalize working-tree state. Its children declare each operation's contract: `21-xml-spacing.enabler` fixes pseudo-XML tag spacing in markdown files before commit, and `21-clean.enabler` removes gitignored cache directories on demand. Each operation lives in its own module under `outcomeeng/hygiene/` and is invoked through a `just` recipe or a lefthook hook.

## Assertions

### Compliance

- ALWAYS: every hygiene operation is idempotent — running it twice produces the same working-tree state as running it once ([audit])
- NEVER: modify tracked content the user has not staged — hygiene operations only touch their declared targets (markdown bytes for `xml-spacing`, gitignored paths for `clean`) ([audit])
