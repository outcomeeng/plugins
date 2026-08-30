# Agents

PROVIDES conversion of rendered plugin agent definitions into the Codex-native custom-agent artifacts the build publishes with each plugin
SO THAT every Codex consumer and hosted agent environment
CAN run one canonical marketplace role per authored agent, which a Codex plugin manifest cannot declare, per `spx/12-marketplace-state.adr.md`.

## Assertions

### Mappings

- For a target whose agent namespace is flat, each converted agent's filename and `name` contain its owning plugin identity exactly once: an authored agent slug beginning with `<plugin>-` remains unchanged, and every other authored slug receives the `<plugin>_` prefix ([test](tests/test_agents.mapping.l1.py))

### Compliance

- ALWAYS: converted agents set the agent-type environment marker in `shell_environment_policy.set` to `<plugin>/<authored-agent-slug>`, so the owning plugin identity appears exactly once even when the flat generated role name already carries that plugin identity and local Codex policy surfaces can distinguish agents without matching prompt text or filenames ([test](tests/test_agents.compliance.l1.py))
- NEVER: an agent whose source path resolves to no `<plugin>/agents` ancestor receives a marker - the marker namespaces every generated agent by its owning plugin, so a source outside that namespace fails conversion rather than emitting an unnamespaced marker ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: two sources whose outputs claim the same path in a target's generated tree fail the build before it writes any generated file ([test](tests/test_agents.compliance.l1.py))
- NEVER: conversion returns two agents claiming one filename - source names differing only outside the slug alphabet converge on a single converted filename, so conversion fails rather than letting the later definition displace the earlier one ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: the build publishes each converted agent as plugin tree content in its target's generated tree, and the plugin manifest declares the surfaces that target resolves through the manifest without declaring agents ([test](tests/test_agents.compliance.l1.py))
