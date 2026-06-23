---
name: diagnose
description: >-
  ALWAYS invoke this skill when diagnosing the health of a spec-tree or spx
  environment, when checking whether the SessionStart hook fired for the current
  session, or when troubleshooting a missing session identity, worktree claim,
  or unreachable spx CLI. NEVER guess why session state is missing without
  running these checks first.
allowed-tools: Bash, Read
---

<objective>

A health report on a spec-tree / spx environment — a named, remediation-hinted verdict per read-only check across the `spx` CLI, the harness session environment, the git worktree layout, the `.spx/` session store, and the Claude and Codex plugin installs.

</objective>

<workflow>

1. Run each check in `<checks>` in the order they appear — the order is intentional where a check notes a cross-check interaction (the session-environment check calls `spx` before spx-reachability runs). Capture each reading verbatim — session identifiers, version strings, and `spx` status fields are reported exactly as their source emits them, NEVER paraphrased or rounded.
2. Classify each check's readings against its verdict table. A check yields exactly one verdict, and each verdict maps to one aggregation bucket — healthy, degraded, broken, or not-applicable — named in the check's table; a not-yet-classifiable reading falls to `unknown` per step 4. Pair each verdict with the matching remediation hint.
3. Aggregate into one report per `<report_format>`: one line per check plus an overall verdict.
4. When a reading is ambiguous, matches no verdict row (an inconsistent partial state), or a command errors, report the check as `unknown` with the captured readings rather than forcing a verdict — a misread check is worse than an honest gap.

</workflow>

<checks>

<check name="session-environment">

Verifies that the runtime's `SessionStart` hook delivered the session environment for the current session. The spec-tree plugin ships this hook for the Claude Code runtime: it writes the agent session identity and project directories into the harness environment and records a worktree-occupancy claim. This check reads the observable traces of that work.

The check applies only on a runtime that ships such a hook. On a runtime that does not — for example Codex, where the `CLAUDE_*` variables are never set — report `not-applicable` rather than classifying against the table below; absent variables there mean "no such hook here," not a failed hook.

Read the three harness variables and the `spx` worktree status, running the status query from inside the repository worktree:

```bash
echo "id=${CLAUDE_SESSION_ID:-UNSET} claimed=${CLAUDE_WORKTREE_CLAIMED:-UNSET} proj=${CLAUDE_PROJECT_DIR:-UNSET}"
spx worktree status --format json
```

`spx worktree status --format json` reports the worktree state in its `.status` field (`occupied`, `unclaimed`, or `stale`). A `stale` reading for the current worktree — a lingering claim from a dead session — matches no row below and falls to `unknown` per step 4. Classify:

| Reading                                                                                                    | Verdict            | Bucket         | Remediation                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ------------------ | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id` is a session identifier, `claimed=1`, `proj` set, and worktree status reports the worktree `occupied` | **working**        | healthy        | None — the hook reached `spx`, which wrote identity and project dirs and claimed the worktree, and `spx` recognizes the claim.                                                                                                |
| `id` is a session identifier, `claimed=UNSET`, worktree status `unclaimed`                                 | **identity-only**  | degraded       | An older hook that does not delegate to `spx` is active for this session. Update the plugin to the version whose `SessionStart` hook delegates to `spx`, then start a new session.                                            |
| `id=UNSET` and worktree status `unclaimed`, on a runtime that ships the hook                               | **silent no-op**   | degraded       | `spx` is not on the hook's PATH, or the hook kill switch is set. Put `spx` on PATH, unset the hook's disable variable, then start a new session. The hook fails open, so nothing is broken — only session identity is absent. |
| The runtime ships no such hook (for example Codex)                                                         | **not-applicable** | not-applicable | None — this runtime has no spec-tree `SessionStart` hook, so session-identity delivery does not apply.                                                                                                                        |

The strongest single signal is worktree status `occupied` together with `claimed=1`: that pair is reachable only when the hook reached `spx`, `spx` claimed the worktree, and the claim's controlling process — the live session — is alive.

This check calls `spx` before the spx-reachability check runs; that ordering is intentional and the two checks classify different conditions. When `spx` is missing from the hook's PATH but installed where the skill runs, this check reads `silent no-op` while spx-reachability reads `reachable`. When `spx` is absent from the system entirely, `spx worktree status` errors and this check falls to `unknown` per step 4 while spx-reachability reads `unreachable`. Neither check depends on the other, so the report's line order is stable.

</check>

<check name="spx-reachability">

Verifies that the `spx` CLI is installed and on PATH, reports its version, and judges that version against the floor the spec-tree skills depend on. That floor is `0.6.0` — the lowest `spx` version whose capabilities the shipped skills assume.

```bash
command -v spx && spx --version
```

Classify the resolution, reporting the resolved path and version verbatim and comparing the reported version against the floor `0.6.0` by dotted-numeric order:

| Reading                                                               | Verdict         | Bucket   | Remediation                                                                                                                    |
| --------------------------------------------------------------------- | --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `spx` resolves on PATH and its version is at or above `0.6.0`         | **reachable**   | healthy  | None — report the resolved path and version verbatim.                                                                          |
| `spx` resolves on PATH and reports a version, but it is below `0.6.0` | **below-floor** | degraded | Update `spx` to at least `0.6.0`; the spec-tree skills assume its capabilities. Report the resolved path and version verbatim. |
| `command -v spx` finds nothing                                        | **unreachable** | broken   | Install `spx` and put it on PATH; the spec-tree skills and the `SessionStart` hook depend on it.                               |

A reported version that is not dotted-numeric — a prerelease or build-tagged value that cannot be ordered against `0.6.0` — matches no row and falls to `unknown` per step 4, reported with the version verbatim.

</check>

<check name="worktree-pool">

Verifies the repository's git worktree layout and flags stale occupancy claims. A spec-tree checkout is either a lone working tree or a bare-repository worktree pool; `spx worktree status` reports each worktree's occupancy as `occupied`, `unclaimed`, or `stale` — a claim whose holding session is dead.

Read the worktree set, then query each non-bare worktree's occupancy:

```bash
git worktree list
git worktree list --porcelain |
  awk '/^worktree /{p=substr($0,10);b=0} /^bare$/{b=1} /^$/{if(p&&!b)print p;p=""} END{if(p&&!b)print p}' |
  while IFS= read -r wt; do spx worktree status --format json "$wt"; done
```

`git worktree list --porcelain` puts each worktree on its own `worktree <path>` line and marks the bare entry with a `bare` line; the `awk` extracts the non-bare paths verbatim (spaces preserved) and the loop queries each with single-path `spx worktree status --format json "$wt"` — the path is quoted, so a path containing spaces stays one argument, and the single-path form is the one existing skills already rely on. Each call returns a `{worktree, status}` object whose `status` is `occupied`, `unclaimed`, or `stale`; a bare path is excluded because `spx worktree status` resolves occupancy only for real worktrees. Classify:

| Reading                                                                                               | Verdict           | Bucket   | Remediation                                                                                                                        |
| ----------------------------------------------------------------------------------------------------- | ----------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| A lone working tree, or a bare-repository pool with linked worktrees, and no worktree reports `stale` | **compliant**     | healthy  | None — report the layout shape and worktree count.                                                                                 |
| A recognized layout (lone tree or bare pool), but one or more worktrees report `stale`                | **stale-claims**  | degraded | Release each stale claim — run `spx worktree release` from that worktree, or let a live session reclaim it.                        |
| Linked worktrees attached to a non-bare repository                                                    | **non-compliant** | broken   | The layout is neither a lone working tree nor a bare-repository pool. Provision the pool so worktrees attach to a bare repository. |

`spx worktree status` exposes occupancy and staleness; this check reports the worktree set, the layout shape, and any stale claim, but does not re-derive the full repository-layout compliance rules — the repository-name main checkout, the `.spx/` placement beside the git-common-dir. Auditing those is test-bearing classification that belongs in the `spx` CLI; surface it here once `spx` exposes it.

</check>

<check name="session-store">

Verifies the `.spx/` session store reads consistently and flags orphaned `doing` claims. `spx session list --json` returns `{"doing": [...], "todo": [...]}`, each session carrying its `git_ref` and `agent_session_id`; `spx session list --status archive --json` reports the archive. A `doing` session is orphaned when the agent that claimed it is gone — observable through the worktree that backs the claim: the worktree on the session's `git_ref` reporting `stale` occupancy, or no worktree existing on that branch.

Read the store and the worktree occupancy backing each doing claim:

```bash
spx session list --json
spx session list --status archive --json
# for each doing session, substitute <git_ref> with that session's git_ref and resolve its worktree:
git worktree list --porcelain |
  awk -v ref="<git_ref>" '/^worktree /{p=substr($0,10)} /^branch /{if($2=="refs/heads/" ref) print p}'
# pass the resolved path (if any) to spx — substitute it for <resolved worktree path>; no match means the branch has no worktree (absent):
spx worktree status --format json "<resolved worktree path>"
```

The `awk` matches the doing session's `git_ref` to a worktree's branch and prints that worktree's path (spaces preserved); if it prints nothing, the branch has no worktree and the claim is `absent`. Join each `doing` session to that occupancy and classify:

| Reading                                                                                                                                                  | Verdict             | Bucket   | Remediation                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| The store reads and every `doing` session's backing worktree is `occupied` (holder live)                                                                 | **consistent**      | healthy  | None — report the doing / todo / archive counts.                                                                                                       |
| The store reads but one or more `doing` sessions are orphaned — the worktree on the session's `git_ref` is `stale`, or no worktree exists on that branch | **orphaned-claims** | degraded | Release or archive each orphaned session — `spx session release <id>` returns it to the queue, or `spx session archive <id>` once its work has landed. |

`spx session` exposes the store but reports no holder-liveness signal of its own, so this check infers it from the worktree-claim occupancy that backs each doing session; a reading that cannot be joined falls to `unknown` per step 4. When `.spx/` does not exist or `spx session list` errors, the check falls to `unknown` per step 4 — there is no not-applicable case for this surface, since any spec-tree environment has a session store. A future `spx session` orphan signal would replace the join.

</check>

<check name="marketplace-install">

Verifies that the methodology marketplace — the marketplace that provides the spec-tree plugins this project depends on — is registered and its offered plugins are installed, enabled, and current, across the two plugin surfaces a consumer may run: Claude Code (`claude plugin`) and Codex (`codex plugin`).

The check applies only where a plugin CLI is present. On a runtime that exposes neither `claude plugin` nor `codex plugin`, report `not-applicable` rather than classifying — there is no install surface to inspect, not a failed install.

Read each present surface's registration and the offered-against-installed plugin state, skipping a surface whose CLI is absent:

```bash
# Claude surface (skip when `claude` is absent):
command -v claude && claude plugin marketplace list --json
command -v claude && claude plugin list --available --json
# Codex surface (skip when `codex` is absent):
command -v codex && codex plugin marketplace list
command -v codex && codex plugin list
```

`claude plugin marketplace list --json` reports whether the methodology marketplace is registered (a `name`/`source` entry). `claude plugin list --available --json` lists every plugin the registered marketplaces offer — the `--available` flag adds the offered-but-not-installed plugins to the installed set, so the listing is the union of offered and installed; an installed entry carries `id` (of the form `<plugin>@<marketplace>`), `version`, and `enabled`. Join the two by plugin name to read, per offered plugin: whether it is installed, whether it is enabled, its installed version, and the offered version. The Codex surface mirrors this — `codex plugin marketplace list` reports registration and `codex plugin list` reports each plugin available from the configured marketplace snapshots and its installed state. Classify across the present surfaces, taking the worst verdict over them (unregistered worse than drifted worse than installed):

| Reading                                                                                                                          | Verdict            | Bucket         | Remediation                                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Every present surface has the marketplace registered and every offered plugin installed, enabled, and at the offered version     | **installed**      | healthy        | None — report the present surfaces, the marketplace, and the plugin count.                                                                                                                                                  |
| The marketplace is registered on the present surfaces, but a plugin is missing, disabled, or installed below the offered version | **drifted**        | degraded       | Install, enable, or update each diverging plugin to the offered set — `claude plugin install\|enable\|update <plugin>@<marketplace>` on the Claude surface, `codex plugin add <plugin>@<marketplace>` on the Codex surface. |
| A present plugin surface does not have the marketplace registered, so its offered plugins cannot resolve                         | **unregistered**   | broken         | Register the marketplace on that surface — `claude plugin marketplace add <source>` or `codex plugin marketplace add <source>` — then install its plugins.                                                                  |
| Neither the Claude nor the Codex plugin CLI is present                                                                           | **not-applicable** | not-applicable | None — this runtime exposes no plugin install surface, so install state does not apply.                                                                                                                                     |

A reading that matches no row — an inconsistent registration-versus-install state — or a surface whose command errors falls to `unknown` per step 4. The plugin CLIs expose registration, the offered set, and the installed-and-enabled state directly; this check joins and compares them but does not re-derive version-floor compliance — judging the installed version against a required minimum needs a minimum-version declaration the installed plugin tree exposes, which extracts into the `spx` CLI once it ships.

</check>

</checks>

<report_format>

Emit one report. Each check is one line: its name, its verdict, and a trailing detail — the remediation hint when the verdict is not healthy, or the captured readings or error when the verdict is `unknown`. Map each verdict to its bucket per the check's table, then close with an overall verdict over the buckets, in precedence order: **broken** when any check is broken, else **unknown** when any check is `unknown`, else **degraded** when any check is degraded, else **healthy** when every applicable check is healthy. A `not-applicable` check is reported on its own line but excluded from the overall verdict; when every check is `not-applicable`, the overall is **not-applicable**.

```text
diagnose — environment report

  session-environment   unknown — id set, claimed=1, but spx worktree status reports unclaimed
  spx-reachability      reachable — /opt/homebrew/bin/spx, 0.61.0
  worktree-pool         stale-claims — plugins-c holds a stale claim
  session-store         consistent — 1 doing, 4 todo, 22 archived
  marketplace-install   drifted — develop installed below offered version on the claude surface

overall: unknown
```

On a runtime without the spec-tree `SessionStart` hook, that check is reported and excluded from the overall:

```text
diagnose — environment report

  session-environment   not-applicable — runtime has no spec-tree SessionStart hook
  spx-reachability      reachable — /opt/homebrew/bin/spx, 0.61.0
  worktree-pool         compliant — bare-repository pool, 7 worktrees, no stale claims
  session-store         consistent — 2 doing, 3 todo, 22 archived
  marketplace-install   installed — outcomeeng registered, 4 plugins current on codex

overall: healthy
```

Report every reading verbatim. Never collapse a session identifier or version string to a summary; downstream comparison against the source depends on the literal value.

</report_format>

<extending>

Each check is an independent named diagnostic: a reading step, a verdict table that maps each reading to a named verdict and its aggregation bucket — healthy, degraded, broken, or not-applicable, with `unknown` for readings that match no row or a command that errors — and a remediation hint per non-healthy state. A check that inspects a runtime-specific surface reports `not-applicable` where that surface is absent rather than misclassifying. Add a check for a new surface by appending a new `<check>` block and one line to the report; a new judgment of a surface an existing check already reads — as the below-floor verdict extends `spx-reachability`, both reading `spx --version` — adds a verdict row to that owning check rather than a second check over the same command. Neither extension rewrites the unrelated existing checks. A check MUST remain a light orchestration of surfaces the environment already exposes. Heavy, test-bearing classification logic MUST live in the `spx` CLI — invoked here as one more non-mutating command — never embedded in this skill.

</extending>

<success_criteria>

- Every check in `<checks>` ran and reported a single verdict — its named verdict, an honest `unknown` with the captured error, or `not-applicable` where its surface is absent.
- Each reading appears verbatim in the report.
- Each non-healthy verdict carries its remediation hint, and each `unknown` verdict carries the captured readings or error.
- The report closes with an overall verdict over the aggregation buckets in precedence order — broken, else unknown, else degraded, else healthy — with `not-applicable` checks excluded.

</success_criteria>
