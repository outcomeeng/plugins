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

## The frontmatter strip runs in one direction

`strip_frontmatter_fields` removes Claude-only fields from Codex output and removes nothing in the other direction. [`spx/18-plugin-build.enabler/15-build-architecture.adr.md`](spx/18-plugin-build.enabler/15-build-architecture.adr.md) declares the symmetric model, and the one-directional strip is the only populated direction because no Codex-only field exists.

**Settlement condition.** A real Codex-only field exists, and `strip_frontmatter_fields` generalizes to a per-target frontmatter schema that strips every field the target's schema does not carry, in either direction.

## DEBT [evidence]: seam-dependent registry findings repeat at the latest audit (f-001, f-002)

Two findings (both REJECT) on
`spx/18-plugin-build.enabler/43-target-emission.enabler/tests/test_target_emission.compliance.l1.py`:

- f-001 at `outcomeeng/distribution/build.py:1646` (untestable source): emission
  reads the module-global `AGENT_CAPABILITY_REGISTRY` and accepts no registry
  input, and `_emit_converted_agent` always calls `convert_agent_markdown`
  without consulting the registry entry, so no seam lets a test supply a
  changed registry entry. This repeats the entry "The registry-resolution
  assertion has no observable seam" above; its resolution and settlement
  condition apply unchanged.
- f-002 at line 337: `test_agent_capabilities_resolve_from_the_source_owned_registry`
  passes the registry's own capability into `agent_slug` and never drives
  emission; a hardcoded `.toml` suffix and `plugin_` prefix in
  `_agent_aware_destination` would pass every linked check.

The audit is a `spec-tree:test-evidence-auditor` verdict on this node at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`. The verdict carries no sealed run
token.

**Resolution shape**: f-001 takes the resolution of the entry above. f-002 is
settled by the same seam: the test drives emission over a changed and an added
registry entry and observes the suffix and prefix follow each.

**Out-of-change evidence**: the text lies outside the Change.
`git diff -U0 origin/main...HEAD` reports no hunk in the cited test, the
harness, or `outcomeeng/distribution/build.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited test drives target
emission through `outcomeeng/distribution/build.py`, which the changeset does
not change.

**Settlement condition**: emission accepts the registry as an input and the
test at line 337 drives emission over a changed and an added registry entry; a
hardcoded suffix or prefix then fails it.

## DEBT [evidence]: portable frontmatter expectation shares the output render path (f-003)

Finding f-003 (REJECT, oracle independence) at
`spx/18-plugin-build.enabler/43-target-emission.enabler/tests/test_target_emission.compliance.l1.py:247`:
for portable frontmatter fields the expectation
`(field in output_fields) == (field in source_fields)` derives from the same
render path that produces the output, so the "all items unavailable" exception
has no independent oracle.

The audit is the verdict named in the entry above, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`; the verdict carries no sealed run
token.

**Resolution shape**: state an independent law for which fields survive
emission, computed without the render path, and compare the output to it.

**Out-of-change evidence**: the text lies outside the Change.
`git diff -U0 origin/main...HEAD` reports no hunk in the cited test, the
harness, or `outcomeeng/distribution/build.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited test drives target
emission through `outcomeeng/distribution/build.py`, which the changeset does
not change.

**Settlement condition**: the expectation for portable fields comes from an
independent law, so a render-path defect that drops or adds a field fails the
test.

## DEBT [evidence]: required emission actions are hand-picked (f-005)

Finding f-005 (WARNING) at
`spx/18-plugin-build.enabler/43-target-emission.enabler/tests/test_target_emission.compliance.l1.py:116`:
the test hand-picks `required_actions = {FAN_OUT, CONVERT_AGENT}` instead of
deriving it from the `EmissionAction` domain. Finding f-004 of the same audit,
on lines 155, 288, and 302, repeats the entry "Three linked tests back no
assertion of this node" above.

The audit is the verdict named in the entry above, at head
`6ef55dd4d93b24b8fa701b8779116bbe7c9bbc04`; the verdict carries no sealed run
token.

**Resolution shape**: derive the set from the `EmissionAction` enumeration, so
a new action extends the check.

**Out-of-change evidence**: the text lies outside the Change.
`git diff -U0 origin/main...HEAD` reports no hunk in the cited test, the
harness, or `outcomeeng/distribution/build.py`, against merge base
`149a55f71befdf61e88be9bda2aae725db1f2381`.

**Invalidation check.** The cited text neither cites, restates, nor depends on
anything this changeset changed. The changeset adds symbols to
`outcomeeng/distribution/profiles.py`, narrows the guard in
`outcomeeng/validation/profile_configuration.py`, and adds model-price and
profile-binding generators, harnesses, and tests. The cited test drives target
emission through `outcomeeng/distribution/build.py`, which the changeset does
not change.

**Settlement condition**: the required actions derive from the `EmissionAction`
domain, so an added action is covered without editing the test.
