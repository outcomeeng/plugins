# Plan: extract assertion ownership and test methodology

The test-verification merge cycle separates governing assertion ownership from the methodology and language-specific surfaces that consume it.

## Decision and assertion ownership

PR #448 on `work/assertion-flow-governance` carries the governing assertion-flow and test-infrastructure declarations. Reconcile it with current source-owned test-data decisions and merge it before implementation guidance that depends on those declarations.

## Methodology consumption

PR #454 on `work/python-test-seam-standards` currently changes 95 paths across shared test methodology and Python, Rust, and TypeScript test guidance. Before publication, classify the authored source by semantic contract:

- Keep one PR when every authored change implements the same cross-language ownership rule and the remaining breadth is deterministic generated fan-out.
- Split independently mergeable language or architecture contracts when each has its own verification and rollback story.
- Keep the governing decision, first affected specs, shared methodology, language consumers, evidence, and generated trees together only when separating them would leave a lower layer inconsistent.

## Revisit condition

This plan is complete when PR #448 is merged and the PR #454 branch has either passed a current semantic-cohesion review as one contract or been replaced by dependency-ordered reviewable PRs whose node-local plans name the remaining work.
