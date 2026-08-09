# ISSUES — contribute

Known defects in the contribute plugin. Each entry names the artifact, the observed
defect, and the smallest unit of work that resolves it.

## Every consuming skill re-encodes the resolver's path through its sibling's layout

Five of the plugin's skills — `open-parent-pr`, `manage-parent-pr`, `open-parent-issue`,
`manage-parent-issue`, and `sync-fork` — each grant
`Bash(python3 "${CLAUDE_SKILL_DIR}/../contribution-standards/scripts/resolve_target.py":*)`
in their own frontmatter. `${CLAUDE_SKILL_DIR}` resolves to the invoking skill's own
directory, so every one of those grants reaches the resolver by walking out of its own
directory and back into a sibling's, encoding `contribution-standards`'s directory name and
internal script layout into five unrelated permission grants. Renaming that skill or moving
its `scripts/` directory breaks all five silently: the grant stops matching, and the resolver
call falls back to a permission prompt rather than failing loudly.

The pattern works in the shipped plugin tree today, which is why it is recorded rather than
repaired in the changeset that introduced it.

**Resolution shape**: establish how a composed reference skill's bundled script becomes
reachable from a consuming skill without the consumer naming the owner's layout — whether an
invoked skill's own `allowed-tools` govern the commands it runs while active, or whether the
consumer must carry the grant. That answer decides between three outcomes: consumers name the
capability and `contribution-standards` alone spells the path; the resolver moves to a
plugin-root `scripts/` directory both reach by a stable path; or the coupling is accepted and
documented as the runtime's actual contract. The question is about skill-composition
permission semantics across two runtimes rather than about this plugin, so it is larger than
the placeholder repair that surfaced it and it changes five skills at once.

**Evidence**: raised by `instructions:skill-auditor` (f-006) against
`src/plugins/contribute/skills/open-parent-pr/SKILL.md`, which named the pattern as systemic
across the plugin rather than local to the skill under audit.
