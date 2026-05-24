# Conversion

PROVIDES runtime-surface conversion contracts for authored plugin artifacts
SO THAT artifact-specific conversion children, target emission, and sync orchestration
CAN preserve source semantics while producing Codex-usable local artifacts.

## Assertions

### Compliance

- ALWAYS: every conversion child names its source artifact class, Codex target surface, and semantic caveats - conversion behavior is explicit per artifact class ([review])
- ALWAYS: conversion outputs that require local Codex configuration stay scoped to local installation orchestration - generated local config is not published as plugin manifest content ([review])
