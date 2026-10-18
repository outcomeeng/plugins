# Writable Roots

The protocol lives at `probes/writable-roots/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator who supplies a writable root in a recover request expects each recovered native session to hold that root as writable, so verification writes that the host plans at launch succeed without a permission prompt. The uncertainty is whether the option recovery appends to each native resume command reaches the recovered session's effective permission policy, or whether the agent's resume path drops it.

## Environment and preconditions

- A running Prowl instance with one prepared Claude Code candidate and one prepared Codex candidate, each in its own worktree and its own pane, with an exact session identity, resume locator, and applicable native home. The operator chooses the Codex home, and the Codex candidate starts under it, so the prepared native home is that home.
- The Codex candidate's project is trusted in that home, because an untrusted Codex project runs read-only and a writable root cannot show there. The trust entry lives in the home's own configuration and carries no credential.
- The Author's own session runs in a Prowl pane on its worktree and is prepared as the third candidate, with `current-session` evidence. Recovery admits a candidate set only with exactly one such controller, and an already resumed controller is a normal prepared candidate that recovery never launches again.
- An absolute directory that lies outside both worktrees and outside each agent's default writable scope, supplied as the writable root for each probe candidate's worktree.
- Each agent's own status surface reachable from its pane: the effective permission display of Claude Code and the status display of Codex.
- An approval policy left at the operator's setting; the protocol adds no sandbox, approval, or permission option.

## Protocol

1. Prepare the two probe candidates and the controller, and record the manifest.
2. End each probe candidate's native session with its own exit, so its pane stays at its shell, and keep Prowl running.
3. Run recovery with a recover request that supplies the absolute directory as the writable root for each probe candidate's worktree.
4. Wait until recovery reports both probe candidates as resumed and verified, and the controller as already correlated.
5. Open each recovered agent's own status surface in its pane and read the directories it lists as writable.
6. Retain a screen capture of each status surface as an artifact in this directory.
7. Repeat steps 2 through 6 once with a recover request that supplies no root, and confirm the directory is absent from each status surface.

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
- Artifacts: [Claude Code with the root](claude-permissions-with-root.txt), [Claude Code without the root](claude-permissions-without-root.txt), [Codex with the root](codex-status-with-root.txt), [Codex without the root](codex-status-without-root.txt)

## Verdict

`failed` for the claim across both agents, with a split result.

Claude Code `passed`. The recovered session lists the supplied root among its workspace directories when recovery appends the option, and lists none when recovery appends none, so the option reaches the session's permission policy.

Codex `failed` to show the root. Both screens report `Custom (danger-full-access, Ask for approval)` and list no writable directory, so the supplied root shows on neither. The two screens are the same with and without the root, which shows neither that the option reached the session nor that the resume path dropped it.

## Limitations

- The protocol reads the policy each agent reports and never exercises a write through it.
- Under the operator's setting, `danger-full-access`, the Codex `/status` display lists no writable directory. Whether it lists the added directory under a restricting sandbox was not observed. A Codex run that decides the claim needs the same recovery under a restricting sandbox or on a surface that lists the added directory, and the protocol adds no sandbox option.
- The protocol ends each native session while Prowl keeps running, so recovery binds each prepared candidate to the existing pane in its worktree. Activation of an absent pane after a real Prowl restart lies outside the probe, because the assertion concerns the launch only; the node's mapping and compliance tests cover that activation.
- The Author session serves as the controller, and recovery launches nothing for it. A controller launch with a supplied root is not exercised.
- A Pi candidate is not exercised, because its resume command accepts no writable-root option and recovery launches none while a root is supplied.
- Agent versions that change the status surface's wording require the Author to read the equivalent display. The Claude Code version was not captured.
