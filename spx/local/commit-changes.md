# Marketplace Commit Rules

This file is loaded by `/commit-changes` in this repository.

## Plugin versions

The commit workflow never runs a plugin version bump and never asks for one.
Commits before pull-request opening preserve the unbumped source manifests;
generated plugin trees still follow the source through `just build-skills`.

`spx/local/open-pr.md` owns the bump policy, its final pre-opening commit,
the check against the current base, and re-evaluation after a later rebase.
When that protocol supplies changed manifests and generated output,
`/commit-changes` commits the supplied files without initiating another bump.

Never hand-edit a manifest `version` field. Version writes belong to the
opening protocol's `just bump` operation.
