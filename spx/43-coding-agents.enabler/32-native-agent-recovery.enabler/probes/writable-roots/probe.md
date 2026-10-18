# Writable Roots

The protocol lives at `probes/writable-roots/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator who supplies a writable root in a recover request expects each recovered native session to hold that root as writable, so verification writes that the host plans at launch succeed without a permission prompt. The uncertainty is whether the option recovery appends to each native resume command reaches the recovered session's effective permission policy, or whether the agent's resume path drops it.

## Environment and preconditions

- A running Prowl instance with one prepared Claude Code candidate and one prepared Codex candidate, each in its own worktree and its own pane, with an exact session identity, resume locator, and applicable native home.
- The Codex candidate runs in a disposable Codex home that the executable provisions. Its `config.toml` sets `sandbox_mode = "workspace-write"` and `daemon_auto_start = false`, and trusts the candidate's project, because an untrusted Codex project runs read-only and a writable root cannot show there, and because under `danger-full-access` the Codex status display lists no writable directory. The home holds no credential of its own: its only credential is a link to the operator's selected saved-login file, which `outcomeeng_testing/harnesses/discovery_auth.py` creates after its write-through check, holds for the run, and scrubs from every capture. The protocol runs no login or logout, and adds no sandbox, approval, or permission option to any recovery launch.
- The Codex candidate is a fresh seed thread, one that no earlier recovery has launched, because a resumed thread keeps the options of its earlier launches and a reused thread cannot separate an appended root from them. The shared Codex home's `config.toml` is read for its SHA-256 before and after the run and is never written.
- The Author's own session runs in a Prowl pane on its worktree and is prepared as the controller, with `current-session` evidence. Recovery admits a candidate set only with exactly one such controller, and an already resumed controller is a normal prepared candidate that recovery never launches again. The prepared roster holds the controller and the probe candidates only, so no other live session enters the manifest.
- A fresh absolute directory that lies outside the candidate worktree, outside the disposable home, outside every temporary directory, and outside each agent's default writable scope, supplied as the writable root for the candidate's worktree in the second recovery only.
- Each agent's own status surface reachable from its pane: the effective permission display of Claude Code and the status display of Codex.

## Protocol

1. Start the fresh candidate session, and for Codex read its status display to take its session identity and to confirm the workspace sandbox, the candidate directory, no server attachment, and the root absent.
2. Prepare the candidate and the controller, and record the manifest.
3. End the candidate's native session with its own exit, so its pane stays at its shell, confirm no agent and no server socket remain, and keep Prowl running.
4. Run recovery with a recover request that supplies no root, wait until recovery reports the candidate as resumed and verified and the controller as already correlated, read the directories the status surface lists as writable, and retain a screen capture as the control artifact. A control that already lists the root, a changed sandbox, or a server attachment ends the protocol as invalid.
5. End the candidate's native session again and confirm the same absences.
6. Run recovery with a recover request that supplies the fresh directory as the writable root for the candidate's worktree, wait for the same resumed and verified result, read the directories the status surface lists as writable, and retain a screen capture as the treatment artifact.
7. End the candidate's native session and compare the shared configuration digest read after the run with the digest read before it.

The protocol stops at the first invalid or undecided condition with the evidence it holds. It never retries a step, never reorders steps, and never reuses a spent thread.

## Executable

`outcomeeng_testing/harnesses/writable_roots_probe.py` executes the Codex form of this protocol through `just probe-writable-roots-codex`. It reserves a Prowl pane in the candidate worktree, starts the seed thread, prepares and recovers the candidate through `src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py`, drives each pane through the shipped Prowl adapter, captures each status screen with the credential scrubbed, and prints the observations and the first stop condition. It judges no verdict. The Author reads the captures and records the verdict under Verdict. The Claude Code form was executed by hand, and its recorded run stands.

## Attested run

- Date: 2026-10-18
- Candidates: the controller, the Author session `7bf0c1b6-f0d0-4aa0-a4dd-d7ab1614c4ae` in pane `D2FFFB6A-ED0A-4F6A-A43A-2E34D4E067CB` with `current-session` evidence; a Claude Code session `88e5fc76-9a78-419a-9324-02539d39c4b7` in pane `C961086A-0C1F-4786-ADE4-44A229B55C3D` on `/Users/shz/Code/outcomeeng/plugins/worktrees/frame-120/` with `public-agent` evidence; a Codex session `01a14e61-8774-7581-bd90-7a6bad4ef72d` (Codex v0.163.0) in pane `B807CE23-D8E9-4C7C-88D2-BB5856E81C78` on `/Users/shz/Code/outcomeeng/plugins/worktrees/frame-577/` under `CODEX_HOME=/Users/shz/.local/state/codex/accounts/outcomeeng` with `native-status` evidence. The Codex project was trusted in that home before the run.
- Writable root: `/Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root`, supplied for both probe worktrees.
- Preparation: `prepare` returned `prepared` with three candidates. Each probe session then ended with `/exit` and its pane stayed at its shell.
- Recovery with the root: activation returned `ready` with no `open` action, and recovery planned `claude --resume 88e5fc76-9a78-419a-9324-02539d39c4b7 --add-dir /Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root` and `env CODEX_HOME=/Users/shz/.local/state/codex/accounts/outcomeeng codex resume 01a14e61-8774-7581-bd90-7a6bad4ef72d --add-dir /Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root`. It reported the controller as `already-correlated` and both probe candidates as `resumed`, and launched nothing for the controller. Each send carried `trailing_enter_sent: true`, each session reached an input-ready prompt, and `verify` returned `verified` with three targets and empty missing, duplicate, and unexpected arrays.
- Claude Code with the root: `/permissions`, Workspace tab, lists the root as a workspace directory. The directory lines read `/Users/shz/Code/outcomeeng/plugins/worktrees/frame-120 (Original working directory)`, `/private/tmp`, and `/Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root`.
- Codex with the root: `/status` reports `Permissions:         Custom (danger-full-access, Ask for approval)` and `Session:             01a14e61-8774-7581-bd90-7a6bad4ef72d`. The screen carries no writable-directory line, and the supplied root appears nowhere on it.
- Recovery without the root: the same sequence with no `writableRoots`. Recovery planned `claude --resume 88e5fc76-9a78-419a-9324-02539d39c4b7` and `env CODEX_HOME=/Users/shz/.local/state/codex/accounts/outcomeeng codex resume 01a14e61-8774-7581-bd90-7a6bad4ef72d`, both probe candidates resumed, and `verify` returned `verified` with three targets and empty missing, duplicate, and unexpected arrays.
- Claude Code without the root: the Workspace tab lists `/Users/shz/Code/outcomeeng/plugins/worktrees/frame-120 (Original working directory)` and `/private/tmp`. The root is absent.
- Codex without the root: the `/status` screen matches the screen with the root line for line. Under `danger-full-access` the display lists no writable directory, so the two Codex screens do not differ.
- The probe stopped after verification. Reassessment sends work instructions to the recovered sessions and lies outside the protocol.
- Codex printed `Disconnected from this task. Any running work continues.` after each exit, and `/status` reported `Server: Local background server`. The resumed session therefore attached to Codex's background server, which this probe does not exercise further.
- Codex rerun at `workspace-write`: the `sandbox_mode` line of the Codex home's `config.toml` read `sandbox_mode = "danger-full-access"` before the rerun, `sandbox_mode = "workspace-write"` during it, and `sandbox_mode = "danger-full-access"` after it, restored exactly and read back. The rerun prepared this session as the controller and the Codex candidate, and left the Claude Code candidate out of the manifest, so its recorded result stands.
- Codex rerun with the root: `prepare` returned `prepared` with two candidates, the Codex session ended with `/exit`, and activation returned `ready` with no `open` action. Recovery planned `env CODEX_HOME=/Users/shz/.local/state/codex/accounts/outcomeeng codex resume 01a14e61-8774-7581-bd90-7a6bad4ef72d --add-dir /Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root`, reported the controller `already-correlated` and the Codex candidate `resumed`, and `verify` returned `verified` with two targets and empty missing, duplicate, and unexpected arrays. `/status` reports `Permissions:         Custom (workspace with network access [/Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root], Ask for approval)`.
- Codex rerun without the root: the same sequence with no `writableRoots`. Recovery planned `env CODEX_HOME=/Users/shz/.local/state/codex/accounts/outcomeeng codex resume 01a14e61-8774-7581-bd90-7a6bad4ef72d`, and `verify` returned `verified` with two targets and empty arrays. `/status` reports the same `Permissions` line, with the root listed in brackets, and matches the screen with the root line for line.
- The two rerun screens do not differ. The same Codex thread had been resumed with the root in the first run and in the first recovery of the rerun, and every screen reports `Server: Local background server`. The probe did not establish whether the listed root persists in the thread, in the background server, or in the resume path.
- Artifacts: [Claude Code with the root](claude-permissions-with-root.txt), [Claude Code without the root](claude-permissions-without-root.txt), [Codex with the root, full access](codex-status-with-root.txt), [Codex without the root, full access](codex-status-without-root.txt), [Codex with the root, workspace-write](codex-status-workspace-write-with-root.txt), [Codex without the root, workspace-write](codex-status-workspace-write-without-root.txt)

## Verdict

`failed` for the claim across both agents, with a split result.

Claude Code `passed`. The recovered session lists the supplied root among its workspace directories when recovery appends the option, and lists none when recovery appends none, so the option reaches the session's permission policy.

Codex `failed`. Under `danger-full-access`, both screens report `Custom (danger-full-access, Ask for approval)` and list no writable directory, so the supplied root shows on neither. Under `workspace-write`, the screen after a recovery that supplies the root lists it in `Permissions:         Custom (workspace with network access [/Users/shz/Code/outcomeeng/plugins/worktrees/executor-593/.spx/probe-writable-root], Ask for approval)`, and the screen after a recovery that supplies none lists it too. The control does not separate the appended option from earlier state of the same thread, so the screens show neither that the option reached the session nor that the resume path dropped it.

## Limitations

- The protocol reads the policy each agent reports and never exercises a write through it.
- Under the operator's setting, `danger-full-access`, the Codex `/status` display lists no writable directory. Under `workspace-write` it lists an added directory in the `Permissions` line.
- The Codex rerun reused the thread that the first run had resumed with the root, so the no-root control lacks independence. A Codex run that decides the claim needs a Codex thread that has never carried the root, resumed first without the root and then with it, under `workspace-write`.
- The `workspace-write` setting applied to the operator's Codex home for the rerun alone. It was restored afterwards, and the protocol adds no sandbox option to any launch command.
- The protocol ends each native session while Prowl keeps running, so recovery binds each prepared candidate to the existing pane in its worktree. Activation of an absent pane after a real Prowl restart lies outside the probe, because the assertion concerns the launch only; the node's mapping and compliance tests cover that activation.
- The Author session serves as the controller, and recovery launches nothing for it. A controller launch with a supplied root is not exercised.
- A Pi candidate is not exercised, because its resume command accepts no writable-root option and recovery launches none while a root is supplied.
- Agent versions that change the status surface's wording require the Author to read the equivalent display. The Claude Code version was not captured.
