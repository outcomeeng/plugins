# Agents

PROVIDES conversion of rendered plugin agent definitions into the Codex-native custom-agent artifacts the build publishes with each plugin
SO THAT every Codex consumer and hosted agent environment
CAN run one canonical marketplace role per authored agent, which a Codex plugin manifest cannot declare, per `spx/12-agent-delivery.pdr.md`.

## Assertions

### Mappings

- Each supported harness and central profile resolves directly to its complete
  native configuration, with Standard as the absent-selection default
  ([test](tests/test_profiles.mapping.l1.py)).
- Every native model or reasoning field is rejected as an independent authored
  override, and every incomplete registry, foreign harness configuration, or
  unsupported control presence or absence is rejected
  ([test](tests/test_profiles.mapping.l1.py)).
- For every agent in the authored marketplace catalog, a flat target's generated filename stem and `name` agree with its dispatch name; namespaced targets retain the bare definition name and native plugin-qualified dispatch name ([test](tests/test_agents.mapping.l1.py))

### Conformance

- Complete profile serialization parses through the native TOML, YAML, and JSON
  parsers into every present field of its independently typed configuration;
  injecting another valid configuration propagates through each serialization
  ([test](tests/test_profile_serialization.conformance.l1.py)).

### Properties

- For every profile name outside the central profile domain, resolution rejects
  the selection without fallback or changes to generated state
  ([test](tests/test_profiles.property.l1.py)).
- For all plugin and authored-role names, a flat target's definition and dispatch names preserve both components as `<plugin>_<unchanged-authored-role>`, including when the role begins with the plugin name; namespaced targets preserve the bare definition name and dispatch as `<plugin>:<authored-role>` ([test](tests/test_agent_names.property.l1.py))

### Compliance

- ALWAYS: independent native field overrides, including template-generated
  values in agent or skill frontmatter, fail before the build deletes or writes
  any generated file ([test](tests/test_profile_build.compliance.l1.py)).
- ALWAYS: converted agents set the agent-type environment marker in `shell_environment_policy.set` to `<plugin>/<authored-agent-slug>`, separating plugin ownership from the authored role even when both components contain the same word, so local Codex policy surfaces can distinguish agents without matching prompt text or filenames ([test](tests/test_agents.compliance.l1.py))
- NEVER: an agent whose source path resolves to no `<plugin>/agents` ancestor receives a marker - the marker namespaces every generated agent by its owning plugin, so a source outside that namespace fails conversion rather than emitting an unnamespaced marker ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: two sources whose outputs claim the same path in a target's generated tree fail the build before it writes any generated file ([test](tests/test_agents.compliance.l1.py))
- NEVER: conversion returns two agents claiming one filename - source names differing only outside the slug alphabet converge on a single converted filename, so conversion fails rather than letting the later definition displace the earlier one ([test](tests/test_agents.compliance.l1.py))
- ALWAYS: the build publishes each converted agent as plugin tree content in its target's generated tree, and the plugin manifest declares the surfaces that target resolves through the manifest without declaring agents ([test](tests/test_agents.compliance.l1.py))
