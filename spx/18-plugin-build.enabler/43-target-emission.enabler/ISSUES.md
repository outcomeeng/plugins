# ISSUES — target emission

## The registry-resolution assertion has no observable seam

The assertion that a target's native agent format, filename shape, and namespace resolve from the per-target agent-capability registry has no evidence that can fail. `project_emissions`, `_agent_aware_destination`, and `agent_capability` in `outcomeeng/distribution/build.py` read the module-global `AGENT_CAPABILITY_REGISTRY` and accept no registry, and `_emit_converted_agent` always calls the Codex TOML converter without consulting the registry. The linked test checks each registry suffix and `agent_slug` with a capability it is handed, so replacing `capability.suffix` with a literal suffix in `_agent_aware_destination`, or hardcoding a target branch for the slug prefix, leaves every test passing.

**Impact**: the claim that adding a target means adding a registry entry, not editing emission logic, holds only by reading the code. A change that hardcodes one target's format or namespace in emission ships with green evidence.

**Settlement condition**: emission takes the registry as an explicit input at its pure boundary, and the converter is chosen from the registry entry. The linked test then supplies a changed and an added registry entry and observes emission following each. `spec-tree:test-evidence-auditor` approves the node with no finding on this assertion.

**Why separate**: the repair restructures the emission boundary in `outcomeeng/distribution/build.py` for every target, beyond the `targets` field this node's last change added. The same boundary carries the optional-capability evidence gap `spx/18-plugin-build.enabler/ISSUES.md` records.

**Evidence**: `spec-tree:test-evidence-auditor` findings f-001 and f-002, severity `REJECT`, on `spx/18-plugin-build.enabler/43-target-emission.enabler` at head `133caf1aba9244c9f6f0706eecb2c0ccf3587b6f`, raised again as f-001 and f-002 at heads `bcf9b3d56a4c6ac629167b31d9daf4c5ac855f09` and `7ca471d52f9b82779c3cf5ea454eea545b0c2e20`; `spec-tree:implementation-auditor` run `2026-09-30_13-32-44-300-3a68e92d2980` raises the same gap as debt `registry-resolution-unfalsifiable`.

## Three linked tests back no assertion of this node

**Evidence**: `test_unescaped_path_rewrite_is_idempotent`, `test_frontmatter_strip_is_idempotent`, and `test_repeated_include_emits_shared_source_once_per_target` in `tests/test_target_emission.compliance.l1.py` assert behavior no assertion in `target-emission.md` declares. The two idempotence checks are property claims inside a file whose name declares compliance evidence. `spec-tree:test-evidence-auditor` finding f-005, severity `WARNING`, at head `c2d6ad239f6e60a90a2c172eafb80d0cba83477b` during Change #200; the three tests predate that Change.

**Impact**: the behavior these tests check can change without any declaration changing, and the file's assertion type misstates what two of its tests prove.

**Settlement condition**: `target-emission.md` declares path-rewrite idempotence, frontmatter-strip idempotence, and once-per-target emission of a repeatedly included shared source, the two idempotence tests move to a property-typed test file, and a test-evidence audit of this node raises no `alignment` finding on them.

**Why separate**: the repair adds three declarations to the spec and a test file of a new assertion type, each with its own spec audit and test-evidence audit, for tests Change #200 did not write. The operator directed recording it here on 2026-09-30.
