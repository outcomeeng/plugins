# Writable Roots

The protocol lives at `probes/writable-roots/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator who supplies a writable root in a recover request expects each recovered native session to hold that root as writable, so verification writes that the host plans at launch succeed without a permission prompt. The uncertainty is whether the option recovery appends to each native resume command reaches the recovered session's effective permission policy, or whether the agent's resume path drops it.

## Environment and preconditions

- A running Prowl instance with one prepared Claude Code candidate and one prepared Codex candidate, each in its own worktree and its own pane, with an exact session identity, resume locator, and applicable native home. The operator chooses the Codex home, and the Codex candidate starts under it, so the prepared native home is that home.
- The Codex candidate's project is trusted in that home, because an untrusted Codex project runs read-only and a writable root cannot show there. The trust entry lives in the home's own configuration and carries no credential.
- An absolute directory that lies outside both worktrees and outside each agent's default writable scope, supplied as the writable root for each candidate's worktree.
- Each agent's own status surface reachable from its pane: the effective permission display of Claude Code and the status display of Codex.
- An approval policy left at the operator's setting; the protocol adds no sandbox, approval, or permission option.

## Protocol

1. Prepare the two candidates and record the manifest.
2. End each candidate's native session with its own exit, so its pane stays at its shell, and keep Prowl running.
3. Run recovery with a recover request that supplies the absolute directory as the writable root for each candidate's worktree.
4. Wait until recovery reports both candidates as resumed and verified.
5. Open each recovered agent's own status surface in its pane and read the directories it lists as writable.
6. Retain a screen capture of each status surface as an artifact in this directory.
7. Repeat steps 3 through 6 once with a recover request that supplies no root, and confirm the directory is absent from each status surface.

## Limitations

- The protocol reads the policy each agent reports and never exercises a write through it.
- The protocol ends each native session while Prowl keeps running, so recovery binds each prepared candidate to the existing pane in its worktree. Activation of an absent pane after a real Prowl restart lies outside the probe, because the assertion concerns the launch only; the node's mapping and compliance tests cover that activation.
- A Pi candidate is not exercised, because its resume command accepts no writable-root option and recovery launches none while a root is supplied.
- Agent versions that change the status surface's wording require the Author to read the equivalent display.
