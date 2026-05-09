# Infrastructure

PROVIDES the host-platform bridging surfaces — repository hosting authentication state and external workflow observability — packaged as structured agent-callable APIs
SO THAT spec-tree methodology skills and downstream language plugins
CAN reason about hosted-CI and host-authentication state through native runtime APIs rather than filesystem heuristics or unstructured CLI access

## Assertions

### Properties

- Hosted-platform state is sourced from native APIs: host authentication from `gh api`, workflow state from `gh run view --json`, repository identity from `git remote` parsed against the host's URL forms — never from filesystem timestamps, directory enumeration, or pattern matching against user prose ([test](tests/test_infrastructure.property.l1.py))
