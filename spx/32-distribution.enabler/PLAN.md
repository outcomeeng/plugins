# Plan: Collapse superseded plugin-cache versions so withdrawn hooks cannot resolve

`spx/15-hook-safety.pdr.md` declares (Audit) that a hook withdrawn or changed in source cannot survive in a pinned or cached install as a blocking hook or as a command whose script path no longer resolves. The Codex sync already collapses superseded versions to symlinks of the current one; the Claude plugin cache retains real per-version directories, so a session pinned to an older version still resolves the hook that version shipped — a withdrawn blocking hook plus its now-orphaned script keep trapping that session.

## Next implementation step

Extend the sync/distribution path so a superseded Claude cache version cannot serve a withdrawn or changed hook — either collapse older in-window cache versions to the current real version (as Codex sync does) or otherwise guarantee no pinned cache resolves a hook absent from current source. Land tests for the cache-collapse behavior under the appropriate sync node.

## Governing decision

`spx/15-hook-safety.pdr.md` — Product property 3; Audit assertion on distribution collapse.
