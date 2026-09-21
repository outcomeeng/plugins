# Marketplace PR Rules

Loaded by `/open-pr` in this repository. These additions preserve the parent
protocol's verification, review, branch-safety, and publication gates.

## Plugin version policy

A changeset warrants a plugin bump when it changes authored content under
`src/plugins/<name>/`, generated content under `dist/<target>/<name>/`, a
`src/_shared/` fragment that the plugin includes, or marketplace catalog fields
that change the plugin's discovery.

Changes confined to `spx/`, coordination notes, root `AGENTS.md` or `CLAUDE.md`,
local overlays, tests, validation configuration, or generated repository docs
warrant no plugin bump. The marketplace sync wrapper uses the same distribution
boundary: those changes alone do not refresh plugin caches.

The opening protocol owns version writes. Ordinary commits neither initiate a
bump nor ask for one. Never hand-edit a manifest `version` field:
`just bump` writes each affected plugin's source manifests
(`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`) in lockstep.

### Segment selection

- **MAJOR** requires an explicit operator request.
- **MINOR** covers adding, removing, or renaming a skill, thin agent, or manifest,
  and major functional changes or significant user-experience improvements.
- **PATCH** is the default for other plugin-distribution changes, including
  fixes, refactoring, installed documentation, and small enhancements.

Auto-detection recognizes structural additions, removals, and renames as
`minor`, and other changes as `patch`; it never selects `major`. A
non-structural major functional change or significant user-experience improvement
therefore needs the explicit `minor` argument.

The recipes accept positional `base_ref` (default `origin/main`) and then
`segment` (default auto-detection):

```bash
just bump-dry
just bump
just bump-check
just bump origin/main minor
```

Use the selected base's remote ref for a stacked branch. The segment is the
second positional argument; recipe flags such as `--segment` and
`segment=minor` are invalid.

## Final pre-opening commit

Complete ordinary changes and their verification before finalizing versions.
For a changeset that warrants a bump, the bump is the final content-changing
step before publication: it produces the last commit before the pull request
opens, after the branch is current with its selected base.

1. Invoke `/sync-base` for the assigned worktree and selected base. Require
   `already_current` or `rebased` and record its full head and base identities.
   Do not derive currency from an earlier verification result.
2. Run `just bump` against that base, with the explicit segment when the policy
   above requires it. Then run `just build-skills` so generated trees carry the
   source versions.
3. Commit the version changes and their generated output together through
   `/commit-changes`. The commit workflow commits these supplied files without
   initiating a bump of its own.
4. Re-establish `VERIFICATION_READINESS` on this exact clean committed head:
   the selected deterministic lane, every applicable audit, and local review.
   A pre-bump result cannot establish readiness for a changed diff. If a repair
   changes content, return to ordinary work and finalize the repaired branch
   again before opening.
5. Before the opening push and ready PR creation, invoke `/sync-base` again
   and require its successful result for the exact candidate head. Base
   advancement returns to step 2 and reopens the verification that the
   preservation proof invalidates.
6. Run `just bump-check` against the selected base on that head. Any nonzero
   exit blocks opening. Require the checked head to be the pushed and opened
   head; a later content change or base advancement invalidates the check.

A changeset with no plugin-distribution change skips version writing and its
version commit. It still passes the opening protocol's other checks.

`just bump-check` verifies that affected manifests agree and are ahead of the
base. The full CI gate does not run this comparison; this opening check is
required even when all CI-related verification is green.

## Open PR updates

After a later rebase or retarget of an open PR's branch, repeat the bump step
against its newly synchronized base before the next push: `just bump`, then
`just build-skills`, and one commit through `/commit-changes` when files
changed. A plugin whose manifests remain ahead of the base is unchanged by
`just bump`; when the base catches up or advances past them, it computes the
next version from that base. A content-only review commit does not initiate
another bump.

Re-establish readiness for the resulting head before pushing and require
`just bump-check` to exit zero on that head. A bump that changes the branch
diff invalidates earlier verification; the base-sync preservation proof permits
reuse only for the unchanged diff and unrelated base movement it proves.
The current-head CI review and checks still decide merge readiness. The merge
operation writes no version and merges the reviewed head.

If review changes the required segment, restore only the affected plugin's two
source manifests to the selected base versions before running `just bump`
with the corrected positional segment, rebuild, and commit the correction.
An explicit segment alone does not override the skip for a plugin already
ahead of the base. A newly affected plugin also passes this version-finalization
step before its changes are pushed.

## Other pre-flight additions

Verify these conditions before opening, alongside the parent protocol's checks:

| Check                                                                                                  | If failing                                                                       |
| ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Touched-scope verification selected by `spx/local/merging.md` and `AGENTS.md` passes on the final head | Fix the failing lane before publication.                                         |
| Both marketplace catalogs reflect added or removed plugins                                             | Update `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. |
| The `README.md` skill and thin-agent catalog matches changed artifacts                                 | Regenerate the catalog through the command in `AGENTS.md`.                       |
| The instruction-block template reflects changed skill structure                                        | Update its authored template and regenerate through the commands in `AGENTS.md`. |

Marketplace catalogs are edited for plugin additions, removals, or discovery
changes; a version bump alone does not require catalog edits.
The full gate checks that plugin directories appear in both catalogs.

## Required body sections

Append to the default template from `/open-pr`:

```text
## Versioning

- <plugin>: <old> → <new> (<MAJOR | MINOR | PATCH>)

## Validation

- [ ] Touched-scope deterministic verification passes
- [ ] `/reload-plugins` confirms the change loads in a running session
```

Drop **Versioning** when no `plugin.json` files changed. For a changeset that
ships no plugin content, record plugin reload as not applicable.
