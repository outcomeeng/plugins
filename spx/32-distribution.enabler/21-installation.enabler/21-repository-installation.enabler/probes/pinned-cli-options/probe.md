# Pinned command-line options

The protocol lives at `probes/pinned-cli-options/probe.md`, which the `pinned-cli-options` slug in `repository-installation.md` links. It reads the hosted run the [native-profile-acceptance](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md) protocol dispatches and retains, and dispatches no run of its own. Every attested run retains at least one inspectable artifact beside this file.

## Intent

The native acceptance harness launches each parent session with command-line options, a stdin, and a probe definition name. A release the quality gate pins can reject an option a newer release accepts, and a harness can reject a definition name another harness accepts. Tests run against recorded commands, so they cannot show that the pinned releases accept what the harness passes. This probe shows, from one hosted run on the pinned releases, that every one of the twelve rows launches its parent session once, that no parent rejects an option, that every profile row retains one child execution, and that every auditor-dispatch row retains a completed run with a run token.

It observes [codex-probe-names](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md), [auditor-fixture-repository](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md), and [unusable-row-fails](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md). It leaves out every other assertion of the node.

## Environment and preconditions

- The native profile acceptance workflow ran once at the subject commit on a hosted runner, under the [native-profile-acceptance](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md) protocol, and that protocol's directory retains the twelve rows of the run.
- The run installed the Claude Code and Codex releases `.github/workflows/check.yml` pins at the subject commit.
- The Author holds an authenticated `gh` command-line tool with read access to the run.

## Protocol

1. Record the subject commit, the workflow run identifier, and the Claude Code and Codex versions `.github/workflows/check.yml` pins at the subject commit.
2. Read the run's log for the step that installs the agent command-line tools, and record the versions its `claude --version` and `codex --version` lines print. Save that log excerpt in this directory as `installed-versions.log`.
3. For each of the eight profile rows under `probes/native-profile-acceptance/profiles/`, read `result.json`: the parent command, the exit code, the standard error, the child observation, and the terminal condition.
4. For each of the four auditor-dispatch rows under `probes/native-profile-acceptance/auditors/`, read `result.json`: the parent command, the exit code, the standard error, the run token, the blocked flag, and the terminal condition.
5. For each row, record whether its standard error names an option the parent session rejects, such as `unknown option`, and whether a Codex row's standard error names a rejected agent or task name.
6. For each Codex profile row, record the `name` its retained definition declares, and whether that name holds only lowercase letters, digits, and underscores.
7. Under Attested run, list the run identifier, the subject commit, the date, the pinned and installed versions, one observation per row for all twelve rows, and a link to `installed-versions.log` and to each row's `result.json` in the native-profile-acceptance directory.
8. Under Verdict, name the probe `passed` only when the installed versions equal the pinned versions, every row's parent session launched once, no row's standard error names a rejected option or a rejected name, every profile row's result records exactly one child execution and no terminal condition, and every auditor-dispatch row's result records a run token, no blocked diagnostic, and no terminal condition. Otherwise name it `failed` and name each row that fails and why.

## Attested run

- Date: 2026-11-16 (dispatched 01:46:13Z, completed 01:53:42Z)
- Subject commit: `241956eb3404bf5b5a84964add38eb15d3aadc14`
- Workflow run: [43788185270](https://github.com/outcomeeng/plugins/actions/runs/43788185270), the run the native-profile-acceptance protocol dispatched and retains.
- Pinned versions: Claude Code `2.1.168` and Codex `0.162.1`, as `.github/workflows/check.yml` pins them at the subject commit.
- Installed versions: `2.1.168 (Claude Code)` and `codex-cli 0.162.1`, as the run's install step prints them.
- Observations:
  - `claude-standard`: `claude -p ...` launched once, exit 0, empty stderr, no rejected option; one child execution; terminal condition none.
  - `claude-strong`: `claude -p ...` launched once, exit 0, empty stderr, no rejected option; one child execution; terminal condition none.
  - `claude-thorough`: `claude -p ...` launched once, exit 0, empty stderr, no rejected option; one child execution; terminal condition none.
  - `claude-fast`: `claude -p ...` launched once, exit 0, empty stderr, no rejected option; one child execution; terminal condition none.
  - `codex-standard`: `codex exec` launched once, exit 0; stderr holds only the PATH-alias warning, no rejected option or name; one child execution; terminal condition none; retained definition `name` is `profile_probe_codex_standard`, lowercase letters and underscores only.
  - `codex-strong`: `codex exec` launched once, exit 0; stderr holds only the PATH-alias warning, no rejected option or name; one child execution; terminal condition none; retained definition `name` is `profile_probe_codex_strong`, lowercase letters and underscores only.
  - `codex-thorough`: `codex exec` launched once, exit 0; stderr holds only the PATH-alias warning, no rejected option or name; one child execution; terminal condition none; retained definition `name` is `profile_probe_codex_thorough`, lowercase letters and underscores only.
  - `codex-fast`: `codex exec` launched once, exit 0; stderr holds only the PATH-alias warning, no rejected option or name; one child execution; terminal condition none; retained definition `name` is `profile_probe_codex_fast`, lowercase letters and underscores only.
  - `claude-skill-auditor`: parent launched once, exit 0; no rejected option or name in stderr; run token none, blocked diagnostic recorded, terminal condition `auditor dispatch returned a blocked diagnostic`.
  - `claude-subagent-auditor`: parent launched once, exit 0; no rejected option or name in stderr; run token none, blocked diagnostic recorded, terminal condition `auditor dispatch returned a blocked diagnostic`.
  - `codex-skill-auditor`: parent launched once, exit 0; no rejected option or name in stderr; run token none, blocked diagnostic recorded, terminal condition `auditor dispatch returned a blocked diagnostic`.
  - `codex-subagent-auditor`: parent launched once, exit 0; no rejected option or name in stderr; run token none, blocked diagnostic recorded, terminal condition `auditor dispatch returned a blocked diagnostic`.
- Artifacts:
  - [installed-versions.log](installed-versions.log)
  - `claude-standard`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/claude-standard/result.json)
  - `claude-strong`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/claude-strong/result.json)
  - `claude-thorough`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/claude-thorough/result.json)
  - `claude-fast`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/claude-fast/result.json)
  - `codex-standard`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/codex-standard/result.json)
  - `codex-strong`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/codex-strong/result.json)
  - `codex-thorough`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/codex-thorough/result.json)
  - `codex-fast`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/profiles/codex-fast/result.json)
  - `claude-skill-auditor`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/auditors/claude-skill-auditor/result.json)
  - `claude-subagent-auditor`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/auditors/claude-subagent-auditor/result.json)
  - `codex-skill-auditor`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/auditors/codex-skill-auditor/result.json)
  - `codex-subagent-auditor`: [result.json](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/probes/native-profile-acceptance/auditors/codex-subagent-auditor/result.json)

## Verdict

`failed`. The installed versions equal the pinned versions. Every row's parent session launched once, no row's standard error names a rejected option or a rejected name, and every profile row records exactly one child execution and no terminal condition. Each of the four auditor-dispatch rows fails: `claude-skill-auditor`, `claude-subagent-auditor`, `codex-skill-auditor` and `codex-subagent-auditor` each record a blocked diagnostic and no run token.

## Limitations

- The probe observes one run on the pinned releases; a release the pin does not name stays unexercised.
- The probe judges whether each parent accepts what the harness passes and whether each row produced its child execution or run; the configuration each child recorded is judged by the native-profile-acceptance protocol.
- A missing or invalid credential stops every row of its harness before the launch, and the verdict records that condition rather than an option rejection.
