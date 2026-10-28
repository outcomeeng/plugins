---
id: 01a1812d-b7b7-7c8d-b71b-129e6e7d9565
malleability: spec
---

# Probe Skill

PROVIDES probe-protocol authoring, attested-run recording, and artifact linking for claims only an executed observation of the running node settles
SO THAT `/verify`
CAN construct `[probe]` evidence through one portable lifecycle without conflating an attested result with a deterministic or agentic verdict

## Assertions

- ALWAYS: the product-tree plugin ships the probe specialist as the skill `/probe`, the skill `/verify` routes a probe assertion to
- ALWAYS: `/probe` writes the probe protocol at `probes/{probe-slug}/probe.md` from the probe template and links every retained artifact of the attested run
- ALWAYS: `/probe` records the Author's verdict and the inspectable artifacts of the executed protocol, and the verification run supplies the actor provenance
- NEVER: `/probe` lets an attested result stand in for a deterministic or agentic verdict
