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

   The adapter selects authentication before constructing the disposable environment, installs the checkout into disposable state, links only the selected `auth.json` for the bounded authentication interval, forces the file credential store, launches the parent once, and scrubs captured output. It uses the parent thread identity from `parent.jsonl` to list active and archived subagent children and retain the sole child's native thread record.
2. Inspect `installed-definition.toml`, `parent.jsonl`, `child.json`, `terminal.txt`, and `summary.json` for these observations:
   - the definition enables `spec-tree:audit-implementation` and carries no `Skill` tool grant or manual-review entry;
   - the child loads `spec-tree:audit-implementation` and every concern skill selected for the changed files;
   - the child completes the audit and returns the implementation-audit terminal result contract;
   - neither session searches for a tool named `Skill`, reports its absence, retries through another launch mechanism, or substitutes another auditor.
3. Copy the adapter's already-scrubbed installer report, installed definition, parent stream, native child record, terminal result, and summary from the successful run beside this protocol. Add the attested run, artifact links, and verdict to this file.

## Attested runs

### 2026-09-17 — Failed: isolated Codex authentication unavailable

- Subject: `a96ec3dd60588835a37f604ad891412c67d23fdd`
- Environment: Codex CLI 0.154.0; isolated installation completed 40 operations with no warnings.
- Observation: the parent thread started, then both WebSocket and HTTPS transports returned HTTP 401 because the isolated Codex home carried no usable bearer credential. No child session started, so skill composition was not observed. The one-shot protocol was not retried.
- Artifacts: [installer report](2026-09-17-installer-report.json), [installed definition](2026-09-17-installed-definition.toml), [parent transcript](2026-09-17-parent.jsonl).
- Verdict: **Failed** — the environment precondition was unsatisfied; this run supplies no evidence for or against runtime skill composition.

## Limitations

The protocol exercises Codex skill composition through the generated implementation-auditor definition. It does not establish Claude Code behavior, other configured subagents, or unrelated Codex tool conversion.
