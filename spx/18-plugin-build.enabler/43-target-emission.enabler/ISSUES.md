# ISSUES — target emission

## The registry-resolution assertion has no observable seam

The assertion that a target's native agent format, filename shape, and namespace resolve from the per-target agent-capability registry has no evidence that can fail. `project_emissions`, `_agent_aware_destination`, and `agent_capability` in `outcomeeng/distribution/build.py` read the module-global `AGENT_CAPABILITY_REGISTRY` and accept no registry, and `_emit_converted_agent` always calls the Codex TOML converter without consulting the registry. The linked test checks each registry suffix and `agent_slug` with a capability it is handed, so replacing `capability.suffix` with a literal suffix in `_agent_aware_destination`, or hardcoding a target branch for the slug prefix, leaves every test passing.

**Impact**: the claim that adding a target means adding a registry entry, not editing emission logic, holds only by reading the code. A change that hardcodes one target's format or namespace in emission ships with green evidence.

**Settlement condition**: emission takes the registry as an explicit input at its pure boundary, and the converter is chosen from the registry entry. The linked test then supplies a changed and an added registry entry and observes emission following each. `spec-tree:test-evidence-auditor` approves the node with no finding on this assertion.

**Why separate**: the repair restructures the emission boundary in `outcomeeng/distribution/build.py` for every target, beyond the `targets` field this node's last change added. The same boundary carries the optional-capability evidence gap `spx/18-plugin-build.enabler/ISSUES.md` records.

**Evidence**: `spec-tree:test-evidence-auditor` findings f-001 and f-002, severity `REJECT`, on `spx/18-plugin-build.enabler/43-target-emission.enabler` at head `133caf1aba9244c9f6f0706eecb2c0ccf3587b6f`.
