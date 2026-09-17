# Codex skill composition

## Intent

The operator expects a generated Codex implementation auditor to compose the installed concern skills its governing audit selects. This protocol exposes whether the generated definition and skill instructions support that composition without inventing a dedicated tool named `Skill`.

## Environment and preconditions

- The exact committed subject has passed the focused deterministic build tests.
- `just build-skills` has generated the Codex marketplace from that subject.
- The Codex CLI is installed and its selected saved login is available to the repository's isolated installer.
- `$PROBE_ROOT` names a new disposable directory and `$RUN_DIR` names the ignored `runs/<run-id>/` directory beneath this probe.

## Protocol

1. Run the repository's isolated installer against the committed checkout and retain its JSON report:

   ```bash
   uv run python -m outcomeeng.distribution.installation --checkout "$PWD" --state-root "$PROBE_ROOT" --json
   ```

2. Copy the installed `spec-tree_implementation-auditor` definition into `$RUN_DIR` before the session starts.
3. Launch one Codex parent session with the isolated roots bound explicitly:

   ```bash
   printf '%s\n' 'Launch spec-tree_implementation-auditor exactly once with target HEAD. Return its terminal result.' | env HOME="$PROBE_ROOT/home" CLAUDE_CONFIG_DIR="$PROBE_ROOT/claude" CODEX_HOME="$PROBE_ROOT/codex" CODEX_SQLITE_HOME="$PROBE_ROOT/codex-sqlite" codex exec --json -C "$PWD" -o "$RUN_DIR/terminal.txt" - | tee "$RUN_DIR/parent.jsonl"
   ```

4. Identify the one spawned child from the parent JSONL and retain that child's rollout in `$RUN_DIR`.
5. Inspect the definition, parent JSONL, child rollout, and terminal result for these observations:
   - the definition enables `spec-tree:audit-implementation` and carries no `Skill` tool grant or manual-review entry;
   - the child loads `spec-tree:audit-implementation` and every concern skill selected for the changed files;
   - the child completes the audit and returns the implementation-audit terminal result contract;
   - neither session searches for a tool named `Skill`, reports its absence, retries through another launch mechanism, or substitutes another auditor.
6. Scrub credentials and copy the installer report, installed definition, parent JSONL, child rollout, and terminal result from the successful run beside this protocol. Add the attested run, artifact links, and verdict to this file.

## Attested runs

### 2026-09-17 — Failed: isolated Codex authentication unavailable

- Subject: `a96ec3dd60588835a37f604ad891412c67d23fdd`
- Environment: Codex CLI 0.154.0; isolated installation completed 40 operations with no warnings.
- Observation: the parent thread started, then both WebSocket and HTTPS transports returned HTTP 401 because the isolated Codex home carried no usable bearer credential. No child session started, so skill composition was not observed. The one-shot protocol was not retried.
- Artifacts: [installer report](2026-09-17-installer-report.json), [installed definition](2026-09-17-installed-definition.toml), [parent transcript](2026-09-17-parent.jsonl).
- Verdict: **Failed** — the environment precondition was unsatisfied; this run supplies no evidence for or against runtime skill composition.

## Limitations

The protocol exercises Codex skill composition through the generated implementation-auditor definition. It does not establish Claude Code behavior, other configured subagents, or unrelated Codex tool conversion.
