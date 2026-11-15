# Pinned command-line options

The protocol lives at `probes/pinned-cli-options/probe.md`, which the `pinned-cli-options` slug in `repository-installation.md` links. It reads the hosted run the [native-profile-acceptance](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md#native-profile-acceptance) protocol dispatches and retains, and dispatches no run of its own. Every attested run retains at least one inspectable artifact beside this file.

## Intent

The native acceptance harness launches each parent session with command-line options, a stdin, and a probe definition name. A release the quality gate pins can reject an option a newer release accepts, and a harness can reject a definition name another harness accepts. Tests run against recorded commands, so they cannot show that the pinned releases accept what the harness passes. This probe shows, from one hosted run on the pinned releases, that every one of the twelve rows launches its parent session once, that no parent rejects an option, that every profile row retains one child execution, and that every auditor-dispatch row retains a completed run with a run token.

It observes [codex-probe-names](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md#codex-probe-names), [auditor-fixture-repository](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md#auditor-fixture-repository), and [unusable-row-fails](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md#unusable-row-fails). It leaves out every other assertion of the node.

## Environment and preconditions

- The native profile acceptance workflow ran once at the subject commit on a hosted runner, under the [native-profile-acceptance](spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler/repository-installation.md#native-profile-acceptance) protocol, and that protocol's directory retains the twelve rows of the run.
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

- Date:
- Subject commit:
- Workflow run:
- Pinned versions:
- Installed versions:
- Observations:
- Artifacts:

## Verdict

## Limitations

- The probe observes one run on the pinned releases; a release the pin does not name stays unexercised.
- The probe judges whether each parent accepts what the harness passes and whether each row produced its child execution or run; the configuration each child recorded is judged by the native-profile-acceptance protocol.
- A missing or invalid credential stops every row of its harness before the launch, and the verdict records that condition rather than an option rejection.
