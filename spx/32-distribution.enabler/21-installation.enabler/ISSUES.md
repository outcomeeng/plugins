# Installation evidence gaps

## Pending plugins' prior owned definitions have no reconciliation evidence

The reconciliation assertion states that a pending plugin's prior owned definitions are preserved, and both `spx/32-distribution.enabler/21-installation.enabler/12-installation-state.pdr.md` and `spx/32-distribution.enabler/21-installation.enabler/15-installation-architecture.adr.md` require it, but no harness case combines a pending-publication plugin with agent-home reconciliation: `observe_agent_home_reconciliation` builds both preflights from a changed catalog with every plugin published. The clause therefore reaches no predicate, and the same observer retires one agent source rather than dropping a plugin from the home selection, so the clause that prunes owned definitions of plugins outside the catalog-bounded selection is likewise never driven. The plan builder also composes the agent-home plan before any command runs, so a plugin that turns out pending during execution still has its checkout definitions in the desired set; whether the applied plan copies definitions for unavailable skill content, against the decision, is undetermined until the scenario exists.

**Resolution shape**: add a harness scenario that installs, then re-runs with one plugin unpublished, and assert that the pending plugin's recorded definitions are neither pruned nor rewritten; if the scenario shows the plan copying definitions for a pending plugin, defer agent-home plan composition until the pending set is known. That is a new reconciliation capability with its own harness and a likely production change, independent of the machine-wide Claude Code refresh.

**Evidence**: test-evidence audit finding `f-005` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`, `f-004` against `548f8cc7b598a30969b0e68c243acb17d387f1ef`, `f-006` against `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, and `f-008` against `be286e7e32cdfbb0cc782f6175ed0f274e428e8d`.

## Claude Code renderings ship the Codex-only placement script and paraphrase its output

The `<plugin>-plugin` skill's Claude Code rendering carries `scripts/place_agents.py`, roughly 330 lines that its own `<agent_delivery>` section says are never invoked there, because the shared template `src/templates/plugin/SKILL.md` conditions other sections on the build target but not the script directory. The same skill's `<examples>` paraphrases the manifest-delivery line instead of quoting the sentence `<verbs>` prints, and the `<verbs>` table's result column for `init`, `upgrade`, and `check` describes the Codex home reconciliation in the Claude Code rendering too, leaving the next sentence to walk all three rows back for that target.

**Resolution shape**: exclude `scripts/` from the Claude Code rendering in the shared template, or state in `<agent_delivery>` why an inert copy must ship; quote the printed sentence verbatim in `<examples>`; render the three result cells per target. Either change touches every plugin's rendered skill, so it lands as one template change gated by the skill auditor.

**Evidence**: skill audit warnings `f-007` and `f-008` against `06b86db6b31704c58203929603bb2f2ceea237cb`, and `f-006` and `f-007` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`.

## The marketplace-refresh clone bound leaves no margin over the source's real clone cost

`test_real_agent_clis_map_full_and_generated_subsets` can fail at the `marketplace-refresh` operation. `codex plugin marketplace upgrade outcomeeng --json` then exits 1 with:

```text
Failed to upgrade marketplace `outcomeeng`: git clone marketplace source timed out after 30s
fatal: early EOF
```

The same bound breaks the declared RELEASE action. `just install-marketplace`, which `spx/local/merging.md` declares under `RELEASE_READINESS`, fails at the identical operation and recipe line, so a merge lifecycle cannot complete its release phase on a host where the clone exceeds the bound. Claude Code's selected plugin operations can complete before the Codex marketplace refresh, so Claude Code project scope may be refreshed while the Codex marketplace is not. That is a partial release reporting failure, never a cosmetic non-zero exit.

The failure is a timing margin, not a content defect. A quiet-machine `git clone` of `https://github.com/outcomeeng/plugins.git` completes in 18 seconds over 44 MB and 4358 commits, against a 30-second bound — a margin of roughly 1.7×. The refresh runs after Claude Code's selected plugin operations, so it competes with the network and disk work those leave behind. The observation reports those Claude Code operations complete before the refresh step, so catalog content and plugin payloads are not implicated.

`fatal: early EOF` is not evidence about the remote. The bound is the constant `MARKETPLACE_UPGRADE_GIT_TIMEOUT`, fixed at 30 seconds inside the agent CLI at version 0.147.0 with no flag or configuration key, and a generic `-c` override cannot reach a constant. On expiry the CLI observes the clone still running, kills it, and only then appends the stderr it collected, so the `early EOF` is that kill's own residue and carries no evidence of a remote-side exit. Reading it as the remote hanging up mistakes the symptom for the cause.

Each killed clone leaves its staging directory behind under the Codex account state; six stale ones have accumulated in `.tmp/marketplaces/.staging/`.

A correct end state never proves the action succeeded. Codex refreshes its marketplace at startup, so the caches can reach the merged commit shortly after a failed release run, through a path the release action neither took nor controls. Establish release completion from the action's own result rather than from an inventory that later looks current.

The margin narrows as the source grows. The suite passed repeatedly earlier the same day and began failing after the default branch advanced, with no change to installation machinery in between.

**Resolution shape**: establish whether the clone the refresh performs can be shallow or filtered rather than full, since the marketplace source is consumed for its committed catalogs and plugin trees rather than its history. Failing that, raise the bound in the agent CLI through an issue filed against that dependency's own repository, tracked here by a Proposed Change through `author-change`. Until either lands, treat a `marketplace-refresh` timeout in this test as this known defect rather than a regression in the changeset under test, and treat the release phase as incomplete whenever `just install-marketplace` exits non-zero at this operation.

**Evidence**: reproduced twice on a host at 0.33 normalized load with `git ls-remote` against the same source returning in 0.58 seconds, so neither host starvation nor loss of connectivity explains it. Reproduced twice again in the release path after PR #515 merged, from a checkout at `33467bab05164e2974f179041f23eb6ff63669dd`, with identical structured records; clone duration was not measured in those two runs.

## The unpublished-plugin enable and update wordings are unobserved

`_is_pending_publication` in `outcomeeng/distribution/installation.py` classifies a failed plugin install, enable, or update as pending publication when `UNPUBLISHED_PLUGIN_FRAGMENT` — the literal `not found in marketplace` — appears in the lower-cased stderr. The simulated stimuli in `outcomeeng_testing/harnesses/installation.py` carry the independently transcribed real **install** wording for both CLIs, observed while adding the `contribute` plugin against a canonical marketplace that did not yet publish it:

```text
Claude Code: Failed to install plugin "contribute@outcomeeng": Plugin "contribute" not found in marketplace "outcomeeng".
Codex:       Error: plugin `contribute` was not found in marketplace `outcomeeng`
```

A constant that drifts from that captured wording now fails the linked tests. The Claude Code **enable** message was never observed: only the Claude plan issues an enable, and only when it bootstraps `spec-tree` into a checkout that records no plugin; the first observation run stopped at the Codex install before that enable ran. The Claude Code **update** that refreshes every recorded install record was never observed against an unpublished plugin either. The fragment also carries no per-agent prefix, unlike `CLAUDE_ALREADY_INSTALLED_FRAGMENT`, so the Claude Code enable and update wordings remain unverified.

If the enable message or the update message words the absence differently, the carve-out silently never engages for that operation and the run fails where it should report pending.

**Resolution shape**: build a disposable marketplace fixture that omits a plugin the built tree ships, register it as the source in the isolated homes the installation harness already provisions, and run the real `claude` and `codex` CLIs against it to record the install wording for both CLIs and the enable and update wording for Claude Code. That is a new real-CLI evidence lane with its own fixture, not a change to an existing test, which is why it is not folded into the changeset that surfaced it.

**Evidence**: raised by changeset review `2026-08-09_10-14-46-352-325b0ceb84d5` against the changeset that introduced the carve-out.

## The L3 installation evidence stalls on a Full Disk Access prompt

Running the repository-installation L3 evidence launches the real Claude Code and
Codex CLIs. On macOS that spawn requests `kTCCServiceSystemPolicyAllFiles` and
`kTCCServiceSystemPolicyAppBundles` through the invoking shell, so a machine that
has not yet answered that request shows a modal Full Disk Access dialog and the
test blocks until the operator dismisses it.

The dialog names the *responsible* application — whichever agent harness hosts the
session — not the test, the shell, or either agent CLI. Nothing identifies the run
as the cause, so the observed symptom is `just verify-marketplace-installation` or
`just check` hanging for minutes with no output and no failure.

**Evidence.** With the permission already denied the requests still appear and the
run completes normally: `accessing={TCCDProcess: identifier=com.apple.sh}`,
`responsible={the host application}`, `service=kTCCServiceSystemPolicyAllFiles`,
`authValue=0`. A bare shell, `just`, `uv`, and `git` produce no TCC activity at
all, so the request originates in the agent-CLI spawn rather than the toolchain
around it. Observed while the gate appeared to take twelve minutes; the same gate
measures 11m13s once the decision is cached.

**Resolution shape**: decide whether the evidence can prove installation without
the permission surface — the agent CLIs may only need it for features these runs
never exercise — and otherwise state the prerequisite where a developer meets it,
so a first run fails fast with the reason instead of stalling on an unattributed
dialog. Neither the denial nor the grant changes the result: the evidence passes
with the request refused.

**Revisit condition**: before onboarding documentation claims a clean first-run
gate on macOS, or when a contributor reports the gate hanging with no output.

## The shipped placement script exceeds the fifty-line ceiling

`src/templates/plugin/scripts/place_agents.py` — rendered once per plugin as
`skills/<plugin>-plugin/scripts/place_agents.py` — carries the ownership-record
parser, the digest-bound collision detector, the atomic writer, and the
scope-split classifier at 333 lines. `spx/12-shipped-scripting.adr.md`
sets fifty lines as the point where a generic shipped script becomes debt
awaiting extraction into the SPX CLI once proven, or removal when it is not,
and exempts only runtime-specific adapter logic whose extraction would couple
SPX to one external agent while the adapter stays deterministic, bounded,
standard-library-only, and independently tested.

The script satisfies each exemption predicate — it targets Codex's agent home
alone, performs one bounded reconciliation and exits, imports only the standard
library, and is exercised by this node's lifecycle tests — but no decision
records the exemption, and the same reconciliation algorithm exists a second
time in `outcomeeng/distribution/installation.py`, which argues the logic is
generic rather than Codex-bound.

**Resolution shape**: choose one of the two paths the ADR admits and record it —
amend `spx/32-distribution.enabler/21-installation.enabler/15-installation-architecture.adr.md` to name the placement script a
Codex-specific adapter kept plugin-local under the exemption, or schedule the
extraction into `spx` and reduce the shipped script to the skill instruction the
ADR prescribes for a proven script. The duplicated algorithm in
`outcomeeng/distribution/installation.py` weighs toward extraction.

**Revisit condition**: with the next behavior change to placement, since any
addition deepens whichever path is not chosen.

**Evidence**: raised by changeset review `2026-08-17_01-03-44-668-0ddd9fe582a1`;
supersedes the ceiling entry the agents-conversion node carried for the earlier
fifty-line version.
