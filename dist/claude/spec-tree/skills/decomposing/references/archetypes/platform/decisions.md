# Platform archetype — decision topics

Decisions a self-hosted multi-tenant platform typically needs, as **prompts to confirm or prune**
against the new product's hypothesis. For this archetype the decisions are the *governing* spine —
tenancy, isolation, and autonomy are cross-cutting policies every node honors, so they live as root
decisions rather than nodes. Derived from the decision records in the source product (leoherd).

## Root-level — the governance spine

- **Isolation model** (`15`, PDR) — Tenancy boundaries: what isolates one tenant (and one sub-context
  within a tenant) from another at the data, credential, and runtime layers.
- **Autonomy model** (`16`, PDR) — Per-capability action gating: what a service/agent may do
  autonomously within a tenant vs what blocks on explicit approval.
- **Architecture** (`17`, ADR) — The runtime realization: how per-tenant runtimes, the shared
  substrate, and ingress compose.
- **Application services** (`18`, PDR) — Which services the platform composes and how they wire per tenant.
- **Operational runbook** (`19`, PDR) — Production operations obligations and their runbook gates.

## Under `infrastructure → host → production`

- **Host provider / immutability / replacement** (`15`–`20`, ADRs) — Where production runs, how the
  host is provisioned immutably, and how it is replaced deterministically.
- **Ingress / network policy** (`15`+, ADRs) — Tunnel/route ownership, private-network policy.
- **GitOps deployment** (`15`+, ADRs) — How production state is declared and converged from git.

## Under `infrastructure → secrets`

- **Secret identity & backend boundaries** (`15`+, ADRs) — Platform-plane vs application-plane secrets
  and which backend owns each.

## Under `infrastructure → connectors`

- **Auth bridge / provisioning** (`15`+, ADRs) — How each external connector authenticates and is
  provisioned per tenant.
