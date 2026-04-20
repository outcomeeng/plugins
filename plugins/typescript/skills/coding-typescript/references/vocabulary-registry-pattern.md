# Vocabulary Registry Pattern (Flat `as const` + `keyof typeof`)

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
export type KindDefinition<K extends Kind> = typeof KIND_REGISTRY[K];

// Category-filtered subtypes via mapped-type filtering
export type NodeKind = {
  [K in Kind]: KIND_REGISTRY[K]["category"] extends "node" ? K : never;
}[Kind];

export type DecisionKind = {
  [K in Kind]: KIND_REGISTRY[K]["category"] extends "decision" ? K : never;
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
// ❌ WRONG: adds no information
const STATE_DECLARED: NodeState = "declared";
expect(state).toBe(STATE_DECLARED);

// ✅ RIGHT: the type annotation is the documentation
expect(state).toBe("declared" as NodeState); // or leave the literal; the test reads fine
```

## Sibling-codebase references

The pattern is used in related monorepo codebases under the name "path registry":

- `~/Code/CraftFinal/root/lib/config/middleware/routes/path-registry.ts` — `API_PATH_REGISTRY` drives `PATHS`, `PATHNAMES`, `URLS` through type inference
- `~/Code/outcomeeng/spx/src/types.ts` — `WORK_ITEM_KINDS`, `WORK_ITEM_STATUSES` (earlier, simpler variant without per-entry metadata)

## Testing

The pattern is pure type algebra at compile time; runtime components (the object, the derived arrays) test straightforwardly:

```typescript
import { DECISION_KINDS, KIND_REGISTRY, NODE_KINDS } from "@/spec/config";
import { describe, expect, it } from "vitest";

describe("KIND_REGISTRY", () => {
  it("every node kind has category 'node'", () => {
    for (const kind of NODE_KINDS) {
      expect(KIND_REGISTRY[kind].category).toBe("node");
    }
  });

  it("no suffix collisions within a category", () => {
    const nodeSuffixes = NODE_KINDS.map((k) => KIND_REGISTRY[k].suffix);
    expect(new Set(nodeSuffixes).size).toBe(nodeSuffixes.length);
  });
});
```

Tests that need a scoped registry construct their own as-const object and pass it in — the production registry is never intercepted. See `testing-typescript` for the DI pattern.
