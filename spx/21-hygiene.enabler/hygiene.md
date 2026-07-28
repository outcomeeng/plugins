# Hygiene

PROVIDES the pre-commit hygiene operations that keep the working tree clean — markdown formatting fixers run by lefthook and on-demand workspace cleanup
SO THAT contributors and CI
CAN commit consistent markdown and reclaim disk space from gitignored caches without remembering ad-hoc shell incantations

## Assertions

### Properties

- Every hygiene operation is idempotent — running it twice produces the same working-tree state as running it once ([test](tests/test_hygiene.property.l1.py))

### Compliance

- NEVER: modify content outside an operation's declared targets — `xml-spacing` changes only supplied markdown paths, and `clean` removes only gitignored paths while preserving tracked bytes ([test](tests/test_hygiene.compliance.l1.py))
