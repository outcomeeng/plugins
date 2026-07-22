# Conversion

PROVIDES coding-agent-surface conversion contracts for authored plugin artifacts
SO THAT artifact-specific conversion children, target emission, and the build
CAN preserve source semantics while producing the Codex-native artifacts each plugin publishes.

## Assertions

### Compliance

- ALWAYS: every conversion child names its source artifact class, Codex target surface, and semantic caveats - conversion behavior is explicit per artifact class ([review])
- ALWAYS: conversion output the Codex runtime reads is published as plugin tree content by the build, and the plugin manifest declares only the surfaces Codex resolves through the manifest ([review])
