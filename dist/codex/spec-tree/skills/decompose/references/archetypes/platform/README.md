# Platform archetype

A self-hosted service that runs isolated per-tenant runtimes over shared infrastructure.

**Outcome topology: none.** The services behave to spec, tenants are few and known, and any
productivity goal is measured per-principal rather than as a multi-user behavior bet — so every node
is an enabler. A product seeded from this archetype is correctly outcome-free.

**Signature: heavy governance.** What distinguishes this archetype is a thin *node* structure over a
deep infrastructure substrate, with tenancy, isolation, and autonomy carried by **root decisions**
(`isolation-model`, `autonomy-model`, `architecture`, `application-services`, `operational-runbook`)
rather than nodes — because they are cross-cutting policies every node must honor.

## When the router matches a product here

- Multiple isolated tenants/principals, not anonymous public visitors.
- Services behave to spec; no measurable multi-user behavior bet.
- Primary surface is a deployed service (plus chat/API endpoints).
- The natural decomposition is tenancy/isolation + runtime infrastructure, governed by decisions.

## What it seeds

- **Core enablers** (always): `infrastructure` (host, secrets, orchestrator, runtime-services,
  connectors, observability, state) and `capabilities` (per-tenant integrations + a test harness).
- **Governance decisions** (always, prominent): the five-decision spine above.

`host` seeds `local` + `production` deployment targets; production's provider-specific depth (host
provider, ingress, IaC, gitops) is left to the per-product decomposition. `capabilities` seeds one
template capability slot plus the harness — the real integrations are per-product.

## Source

Generalized from **leoherd** (`leoherds/leoherd`), an always-on personal AI-agent platform with
per-principal and per-profile isolation. See `example/` for the real authored bookend tree.
