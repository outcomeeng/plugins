# Worked example: leoherd (platform)

A real, authored self-hosted multi-tenant platform spec tree — the pattern-match reference for the
`platform` archetype. Source: `leoherds/leoherd`. 77 enablers, 0 outcomes — correctly outcome-free,
and governance-heavy.

## Top-level partition (as authored)

```text
spx/
  10-operational-runbook-model.pdr.md · 12-leoherd-isolation-model.pdr.md · 13-leoherd-autonomy-model.pdr.md
  16-application-services.pdr.md · 17-leoherd-architecture.adr.md   (+ test/evidence ADRs 14,15,18,19,20)
  21-infrastructure.enabler/   deployment + runtime substrate
  21-skills.enabler/           per-profile capability integrations (Obsidian, Notion, Linear)
```

Only two top-level nodes over a deep substrate — the platform shape. The governance is carried by the
root PDRs/ADRs, not by nodes.

## infrastructure substrate (as authored)

```text
infrastructure ->
  21-host (-> 21-local | 43-production -> hetzner / iac / tailscale / cloudflare-tunnel / gitops ...)
  21-secrets · 32-test-harness · 34-leoherd-python · 37-herder (orchestrator)
  43-agent · 49-container-observability · 49-profile-state-repositories
  54-actions-runner · 54-chat-frontend · 54-claude-code · 54-dashboard · 54-m365-mcp · 54-slack-adapter
```

## The authored voice

- **infrastructure** — PROVIDES deployment, secrets management, and inference API access SO THAT the
  agent runtime and skills CAN operate reliably on any host (local Docker Compose or persistent
  production VPS).
- **skills** — PROVIDES per-profile bundled-skill integrations for the three knowledge surfaces SO
  THAT each profile's agent CAN read and write Obsidian, Notion, and Linear within that profile's
  template under the autonomy + isolation models.
- **host** — PROVIDES container orchestration and host provisioning SO THAT every per-profile agent
  and chat-frontend container CAN run on both a local development machine and a persistent production VPS.

## How the seed generalizes this

- Renames `skills → capabilities` (avoids collision with the methodology's own "skills" concept).
- Rebases indices: `infrastructure` 21 / `capabilities` 38 (both were 21); governance decisions into
  the 15–20 band (leoherd authored them at 10–13).
- Generalizes `host → {local, production}`; the provider-specific production depth (Hetzner,
  Cloudflare, Tailscale, GitOps) stays here in the authored reference only.
- Folds leoherd's many `54-*` runtime containers into generic `runtime-services` + `connectors`.
- Seeds the five governance decisions as the archetype spine.

leoherd's own tree is preserved here as the authored reference; the generalized seed lives in
`../seed-tree.json`.
