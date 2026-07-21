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

## Decomposition disposition — the superset is a deliberate single node

`test-verification.md` carries roughly 24 Compliance assertions, well past the roughly-7 signal in `spx/21-spec-tree.enabler/54-decomposing.enabler/decomposing.md:ALWAYS:1`. This is the intended shape, not carried-forward duplication: the node is the single language-neutral **superset** of the test-evidence seam rules, and every language test-standard node cites it and declares only its language delta. Decomposing the superset into per-concern child nodes would re-fragment the exact union the design unifies, and language nodes would then cite a parent whose rules are spread across children — reintroducing the cross-language drift the superset removes. The count is a consequence of consolidating three languages' rules into one owner, so the decomposition signal is dispositioned as accepted here rather than acted on.
