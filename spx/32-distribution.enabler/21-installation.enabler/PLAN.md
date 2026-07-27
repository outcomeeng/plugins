# Plan: installation slices

`spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler` is the first installation slice. It establishes the repository command, orchestration module, real-agent disposable-home harness, and checkout lifecycle placement contract.

Reserve `spx/32-distribution.enabler/21-installation.enabler/32-consumer-installation.enabler` for explicit installation into caller-named consumer homes. The higher index records a vertical-slice dependency: consumer installation uses the repository slice's declaration parsing, agent adapters, command result contract, and harness boundary. Without the repository slice, the consumer workflow would duplicate those contracts or leave them unverified.

The repository slice preserves the existing plugin lifecycle capability and `src/templates/plugin/scripts/place_agents.py`. It removes source-repair, cache-topology, compatibility-symlink, single-flight-lock, and push-coupled synchronization behavior.
