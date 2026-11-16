# Product Offering

DEFINES open-source tier AS the complete CLI toolchain — spec authoring, tree operations, test integration, and status derivation — released under an open-source license

GOVERNS the product offering
SO THAT developers adopting the toolchain
CAN RELY ON the open-source tier being a complete, production-ready toolchain, with commercial tiers adding only collaboration, hosting, and analytics

## Verification

### Test.Compliance: open-source tier

- full-core-toolchain: ALWAYS present the OSS tier as the full core toolchain — users can do all individual work without paying.
- no-auth-gating: NEVER gate CLI functionality behind authentication — breaks trust positioning.
- no-commercial-references: NEVER reference commercial-only features in CLI help text — creates confusion about what's available.

### Test.Conformance: documentation

- documented-features: Every CLI feature appears in the open-source documentation.
