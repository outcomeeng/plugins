# Marketplace Commit Rules

This file is loaded by `/commit-changes` in this repository.

## Plugin versions

The commit workflow never runs a plugin version bump and never asks for one.
Commits before the merge-time version step preserve the unbumped source
manifests; generated plugin trees still follow the source through
`just build-skills`.

`spx/local/open-pr.md` owns the bump policy. `spx/local/merging.md` runs
`just bump` as the merge-time step, after base synchronization and once review
and checks are green on the final content, and repeats it after a later rebase.
When that step supplies changed manifests and generated output,
`/commit-changes` commits the supplied files without initiating another bump.

Never hand-edit a manifest `version` field. Version writes belong to the
merge-time step's `just bump` operation.
