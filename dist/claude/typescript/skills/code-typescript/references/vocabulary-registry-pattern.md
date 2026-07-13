# Vocabulary Registry Pattern (Flat `as const` + `keyof typeof`)

## Contents

- [When to use](#when-to-use)
- [The pattern](#the-pattern)
- [Why it satisfies "string occurs exactly once"](#why-it-satisfies-string-occurs-exactly-once)
- [Anti-patterns](#anti-patterns)
- [Sibling-codebase references](#sibling-codebase-references)
- [Testing](#testing)

## When to use

Any time a domain has a closed set of named values (kinds, statuses, event names, etc.) that:

- Need a TypeScript union type
- Need a runtime enumeration
- Need per-value metadata (suffix, label, category, ...)
- Must stay in sync — the "string occurs exactly once" rule

Examples: node kinds (`enabler`, `outcome`, `adr`, `pdr`), work-item statuses, API path segments, language markers.

## The pattern

```typescript
// Single source of truth — keys are the vocabulary, values are the metadata
export const KIND_REGISTRY = {
  enabler: { category: "node", suffix: ".enabler" },
  outcome: { category: "node", suffix: ".outcome" },
  adr: { category: "decision", suffix: ".adr.md" },
  pdr: { category: "decision", suffix: ".pdr.md" },
} as const;

// Types are inferred — no separate union declaration
export type Kind = keyof typeof KIND_REGISTRY;
export type KindDefinition<K extends Kind> = (typeof KIND_REGISTRY)[K];

// Category-filtered subtypes via mapped-type filtering
export type NodeKind = {
  [K in Kind]: (typeof KIND_REGISTRY)[K]["category"] extends "node" ? K : never;
}[Kind];

export type DecisionKind = {
  [K in Kind]: (typeof KIND_REGISTRY)[K]["category"] extends "decision" ? K : never;
}[Kind];

// Runtime sub-registries are computed at module scope from the single source
export const NODE_KINDS: readonly NodeKind[] = (Object.keys(KIND_REGISTRY) as Kind[]).filter(
  (k): k is NodeKind => KIND_REGISTRY[k].category === "node",
);

export const DECISION_KINDS: readonly DecisionKind[] = (Object.keys(KIND_REGISTRY) as Kind[]).filter(
  (k): k is DecisionKind => KIND_REGISTRY[k].category === "decision",
);

export const NODE_SUFFIXES: readonly string[] = NODE_KINDS.map((k) => KIND_REGISTRY[k].suffix);
```

## Why it satisfies "string occurs exactly once"

The string `"enabler"` appears in the codebase as the object key in `KIND_REGISTRY` and nowhere else. The union type, the runtime array, the sub-registries, and the suffix list all derive from that one declaration. A typo in a literal is flagged at the use site; exhaustive switch checks are automatic.

## Anti-patterns

Never declare a union type separately from the registry:

```typescript
// ❌ WRONG: duplicates the string
export type NodeKind = "enabler" | "outcome";
export const NODE_KINDS: NodeKind[] = ["enabler", "outcome"];

// ✅ RIGHT: one declaration, types inferred
export const NODE_KINDS_REGISTRY = { enabler: {...}, outcome: {...} } as const;
export type NodeKind = keyof typeof NODE_KINDS_REGISTRY;
```

Never duplicate sub-metadata in parallel constants:

```typescript
// ❌ WRONG: suffix appears twice (drift inevitable)
export const KIND_REGISTRY = { enabler: { suffix: ".enabler" }, ... } as const;
export const NODE_SUFFIXES = [".enabler", ".outcome"];  // parallel, will drift

// ✅ RIGHT: derive from the registry
export const NODE_SUFFIXES: readonly string[] = Object.values(KIND_REGISTRY).map((d) => d.suffix);
```

Never extract typed literal values to named constants to satisfy lint warnings:

```typescript
// ❌ WRONG: test-owned alias for source vocabulary
const STATE_DECLARED: NodeState = "declared";
expect(state).toBe(STATE_DECLARED);

// ✅ RIGHT: import the source-owned registry member
import { NODE_STATES } from "@/state/registry";

expect(state).toBe(NODE_STATES.DECLARED);
```

## Sibling-codebase references

The pattern is also known as a "path registry" in related codebases: a route or path-config object whose keys drive derived `PATHS`, `PATHNAMES`, and `URLS` types through inference, and an earlier, simpler variant that derives vocabulary arrays such as `WORK_ITEM_KINDS` and `WORK_ITEM_STATUSES` without per-entry metadata.

## Testing

The pattern is pure type algebra at compile time; runtime components (the object, the derived arrays) test straightforwardly:

```typescript
import { DECISION_KINDS, KIND_REGISTRY, NODE_KINDS } from "@/spec/config";
import { assertProperty } from "@testing/harnesses/properties";
import { kindRegistryDerivationProperty } from "@testing/harnesses/spec-kind-registry";
import { describe, it } from "vitest";

describe("KIND_REGISTRY", () => {
  it("derives disjoint kind partitions and collision-free suffixes", () => {
    assertProperty(kindRegistryDerivationProperty(KIND_REGISTRY, NODE_KINDS, DECISION_KINDS));
  });
});
```

Tests that need variable registry inputs use a generator to produce meaningful registry candidates and pass them through a harness. Source-owned keys and metadata enter through production contracts, and the production registry is never intercepted. See `test-typescript` for the DI pattern.
