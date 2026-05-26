# Product Offering

## Purpose

This decision governs what the product offers in its open-source tier versus commercial tiers. The open-source offering must be positioned as a complete, production-ready toolchain — not a limited trial.

## Context

**Business impact:** Open-source adoption drives commercial conversion. If the free tier feels incomplete, developers evaluate alternatives instead of upgrading. The product must deliver full value at the free tier to build trust.

**Technical constraints:** Some features require infrastructure (cloud storage, team collaboration) that cannot be self-hosted without significant effort. These naturally belong in commercial tiers.

## Decision

The open-source tier includes the complete CLI toolchain: spec authoring, tree operations, test integration, and status derivation. Commercial tiers add collaboration, hosting, and analytics.

## Rationale

Developers adopt tools that solve their immediate problem without friction. A complete CLI tool can be adopted by individual developers, creating bottom-up demand within organizations. Alternatives considered: freemium with feature gates (rejected: creates resentment), open-core with plugin architecture (rejected: adds complexity without clear value boundary).

## Trade-offs accepted

| Trade-off                               | Mitigation / reasoning                                               |
| --------------------------------------- | -------------------------------------------------------------------- |
| Full CLI means less conversion pressure | Trust-based conversion is slower but stickier than friction-based    |
| Must maintain full feature set as OSS   | Reduces scope of commercial tier, focusing it on genuinely new value |

## Product invariants

- The CLI toolchain is always fully functional without authentication or license keys
- Every feature documented in the open-source docs works without a commercial account

## Compliance

### Recognized by

All CLI commands execute successfully without network access or API keys.

### MUST

- Present the OSS tier as the full core toolchain — users can do all individual work without paying
- Document all CLI features in the open-source documentation

### NEVER

- Gate CLI functionality behind authentication — breaks trust positioning
- Reference commercial-only features in CLI help text — creates confusion about what's available
