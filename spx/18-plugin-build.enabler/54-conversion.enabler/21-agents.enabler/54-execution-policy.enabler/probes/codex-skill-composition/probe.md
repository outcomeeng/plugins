# Codex skill composition

## Intent

The operator expects a generated Codex implementation auditor to compose the installed concern skills its governing audit selects. This protocol exposes whether the generated definition and skill instructions support that composition without inventing a dedicated tool named `Skill`.

## Environment and preconditions

- The exact committed subject has passed the focused deterministic build tests.
- `just build-skills` has generated the Codex marketplace from that subject.
- The Codex CLI is installed and the selected persistent `CODEX_HOME` contains a file-backed ChatGPT login.
- `$RUN_DIR` names a new ignored `runs/<run-id>/` directory beneath this probe.

## Protocol

1. Run the repository's composition-probe adapter against the committed checkout:

   ```bash
   uv run python -m outcomeeng_testing.harnesses.codex_skill_composition "$RUN_DIR" --checkout "$PWD"
   ```

   The adapter selects authentication before constructing the disposable environment, installs the checkout into disposable state, links only the selected `auth.json` for the bounded authentication interval, forces the file credential store, and launches the parent once with `--sandbox danger-full-access`. The explicit sandbox mode gives the verifier the same filesystem reach as a host-launched verifier: it can read the worktree's shared Git common directory and write verification state under the shared `.spx/` directory even though both sit outside the checkout root. The bounded process runner and credential redactor remain the external execution boundary. The adapter uses the parent thread identity from `parent.jsonl` to list active and archived subagent children and retain the sole child's native thread record.
2. Inspect `installed-definition.toml`, `parent.jsonl`, `child.json`, `child-rollout.jsonl`, `replicated-shell.json`, `terminal.txt`, and `summary.json` for these observations:
   - the definition enables `spec-tree:audit-implementation` and carries no `Skill` tool grant or manual-review entry;
   - the child loads `spec-tree:audit-implementation` and every concern skill selected for the changed files;
   - the child completes the audit and returns the implementation-audit terminal result contract;
   - neither session searches for a tool named `Skill`, reports its absence, retries through another launch mechanism, or substitutes another auditor.
3. Copy the adapter's already-scrubbed installer report, installed definition, parent stream, native child record, child rollout, replicated-shell observation, terminal result, and summary from the successful run beside this protocol. Add the attested run, artifact links, and verdict to this file.

## Attested runs

### 2026-09-17 — Failed: isolated Codex authentication unavailable

- Subject: `a96ec3dd60588835a37f604ad891412c67d23fdd`
- Environment: Codex CLI 0.154.0; isolated installation completed 40 operations with no warnings.
- Observation: the parent thread started, then both WebSocket and HTTPS transports returned HTTP 401 because the isolated Codex home carried no usable bearer credential. No child session started, so skill composition was not observed. The one-shot protocol was not retried.
- Artifacts: [installer report](2026-09-17-installer-report.json), [installed definition](2026-09-17-installed-definition.toml), [parent transcript](2026-09-17-parent.jsonl).
- Verdict: **Failed** — the environment precondition was unsatisfied; this run supplies no evidence for or against runtime skill composition.

### 2026-09-17 — Failed: audit terminal contract incomplete

- Subject: `6c64464abf07a2e384dabea0d3d0bc19a1b12956`
- Environment: Codex CLI 0.154.0; isolated installation and saved-login authentication succeeded; parent thread `01a0afec-6fee-7801-aed3-09e5bd993d01` launched sole child `01a0afec-882d-7be2-9b12-c3ea07fa67a8` as `spec-tree_implementation-auditor`.
- Composition observation: the installed definition enabled `spec-tree:audit-implementation` without a `Skill` tool grant, the child read that skill and the installed Go and Python concern skills, and neither session searched for a tool named `Skill` or launched a substitute auditor.
- Audit observation: SPX run `2026-09-17_15-12-34-814-1080e7adf6da` sealed `approved` with zero findings, while all 319 changed paths were recorded as optional, skipped `coverage-gap` units, including the changed Python implementation. The child and parent terminal messages contained only the run token rather than the required run token plus rendered projection.
- Artifacts: [installer report](2026-09-17-6c64464ab-installer-report.json), [installed definition](2026-09-17-6c64464ab-installed-definition.toml), [parent transcript](2026-09-17-6c64464ab-parent.jsonl), [terminal result](2026-09-17-6c64464ab-terminal.txt), and [summary](2026-09-17-6c64464ab-summary.json). The SPX run token identifies the durable native child result without committing its 5 MB thread capture.
- Verdict: **Failed** — skill loading and the absence of a dedicated `Skill` dependency were observed, while the required concern-audit and terminal-result observations were not.

### 2026-09-17 — Failed: configured auditor selected unsupported Python

- Subject: `759e3abccc5f90b0cbc18a284557caeb9d07766e`
- Probe adapter: Change #86 commit `04ef3aa632ba7e4b6ce450c013a00de0cc916347`.
- Environment: Codex CLI 0.154.0; isolated installation and saved-login authentication succeeded; parent thread `01a0b0de-44d4-78e2-b0ac-8716d8e56100` launched sole child `01a0b0de-610b-7ac0-9abe-787c3a565ca0` as `spec-tree_implementation-auditor` with history disabled.
- Composition observation: the installed definition enabled `spec-tree:audit-implementation` without a `Skill` tool grant or manual-review entry, and the child read the installed `spec-tree:audit-implementation` skill. Neither session searched for a tool named `Skill`, retried through another launch mechanism, or substituted another auditor.
- Failure observation: the child invoked the skill's `resolve_scope.py` through `python3`; that command resolved to Xcode Python 3.9 and failed before starting an SPX run because `enum.StrEnum` was unavailable. No concern skill was selected or read, and no implementation-audit terminal projection was produced. The one-shot protocol was not retried.
- Artifacts: [installer report](2026-09-17-759e3abcc/installer-report.json), [installed definition](2026-09-17-759e3abcc/installed-definition.toml), [parent transcript](2026-09-17-759e3abcc/parent.jsonl), [native child record](2026-09-17-759e3abcc/child.json), [terminal result](2026-09-17-759e3abcc/terminal.txt), and [summary](2026-09-17-759e3abcc/summary.json).
- Verdict: **Failed** — the repaired composition instruction was observed, while the required concern-skill composition and completed audit observations were unreachable because the configured child selected an unsupported interpreter.

### 2026-09-17 — Failed: login shell path rewriting selected unsupported Python

- Subject: `12f88eb9468cbe3f78245d11f14c234631ee9f2d`
- Probe adapter: Change #86 commit `283d1e63f2bdd635c89b751bd76c1a89c929b859`.
- Environment: Codex CLI 0.154.0; isolated installation and saved-login authentication succeeded; parent thread `01a0b158-8f2f-7a11-bb27-a72ad9ba8f7c` launched sole child `01a0b158-a781-7161-ae2f-9c1e1a8958e3` as `spec-tree_implementation-auditor` with authoring history disabled.
- Composition observation: the installed definition enabled `spec-tree:audit-implementation` without a `Skill` tool grant or manual-review entry, and the child read the installed `spec-tree:audit-implementation` skill. Neither session searched for a tool named `Skill`, retried through another launch mechanism, or substituted another auditor.
- Child observation: the child invoked `resolve_scope.py` through bare `python3`. The retained traceback shows the process imported `enum.py` from `/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/` and failed because Python 3.9 lacks `enum.StrEnum`. No SPX run started, no concern skill was selected, and no implementation-audit projection was produced.
- Replicated-shell observation: the adapter-supplied `PATH` began with `/Users/shz/Code/outcomeeng/plugins/codex-skill-tool-fix/.venv/bin`. The separately labelled `/bin/zsh -lc` run with the same working directory and environment reported an effective `PATH` beginning `/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin`, followed by the cryptexd bootstrap paths before the adapter-supplied virtual-environment and Homebrew entries; `command -v python3` reported `/usr/bin/python3`, and `python3 --version` reported `Python 3.9.6`.
- Mechanism: the login shell reads `/etc/zprofile`; macOS `path_helper` prepends the system and cryptexd paths ahead of the adapter-supplied managed-interpreter entries. Bare `python3` therefore resolves to the `/usr/bin/python3` Xcode shim, matching the child traceback.
- Artifacts: [installer report](2026-09-17-12f88eb94/installer-report.json), [installed definition](2026-09-17-12f88eb94/installed-definition.toml), [parent transcript](2026-09-17-12f88eb94/parent.jsonl), [native child record](2026-09-17-12f88eb94/child.json), [native child rollout](2026-09-17-12f88eb94/child-rollout.jsonl), [replicated shell](2026-09-17-12f88eb94/replicated-shell.json), [terminal result](2026-09-17-12f88eb94/terminal.txt), [summary](2026-09-17-12f88eb94/summary.json), and [parent stderr](2026-09-17-12f88eb94/parent.stderr.txt).
- Verdict: **Failed** — the configured child loaded the intended audit skill, while login-shell path rewriting selected an unsupported interpreter before the child could compose the required concern skills or complete the audit.

## Limitations

The protocol exercises Codex skill composition through the generated implementation-auditor definition. It does not establish Claude Code behavior, other configured subagents, or unrelated Codex tool conversion.
