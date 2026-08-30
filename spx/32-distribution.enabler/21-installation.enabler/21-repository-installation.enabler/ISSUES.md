# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

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

**Resolution shape**: establish whether the clone the refresh performs can be shallow or filtered rather than full, since the marketplace source is consumed for its committed catalogs and plugin trees rather than its history. Failing that, raise the bound in the agent CLI through `/issue` against that dependency. Until either lands, treat a `marketplace-refresh` timeout in this test as this known defect rather than a regression in the changeset under test, and treat the release phase as incomplete whenever `just install-marketplace` exits non-zero at this operation.

**Evidence**: reproduced twice on a host at 0.33 normalized load with `git ls-remote` against the same source returning in 0.58 seconds, so neither host starvation nor loss of connectivity explains it. Reproduced twice again in the release path after PR #515 merged, from a checkout at `33467bab05164e2974f179041f23eb6ff63669dd`, with identical structured records; clone duration was not measured in those two runs.

## The unpublished-plugin enable wording is unobserved

`_is_pending_publication` in `outcomeeng/distribution/installation.py` classifies a failed plugin install or enable as pending publication when `UNPUBLISHED_PLUGIN_FRAGMENT` — the literal `not found in marketplace` — appears in the lower-cased stderr. The simulated stimuli in `outcomeeng_testing/harnesses/installation.py` carry the independently transcribed real **install** wording for both CLIs, observed while adding the `contribute` plugin against a canonical marketplace that did not yet publish it:

```text
Claude Code: Failed to install plugin "contribute@outcomeeng": Plugin "contribute" not found in marketplace "outcomeeng".
Codex:       Error: plugin `contribute` was not found in marketplace `outcomeeng`
```

A constant that drifts from that captured wording now fails the linked tests. Neither **enable** message was ever observed: the Claude plan issues install then enable per plugin, and the first observation run stopped at the Codex install before any enable ran. The fragment also carries no per-agent prefix, unlike `CLAUDE_ALREADY_INSTALLED_FRAGMENT`, so the enable wording remains unverified for both CLIs.

If either enable message words the absence differently, the carve-out silently never engages for that operation and the run fails where it should report pending.

**Resolution shape**: build a disposable marketplace fixture that omits a plugin the built tree ships, register it as the source in the isolated homes the installation harness already provisions, and run the real `claude` and `codex` CLIs against it to record the install and enable wording for both. That is a new real-CLI evidence lane with its own fixture, not a change to an existing test, which is why it is not folded into the changeset that surfaced it.

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
scope-split classifier at roughly 250 lines. `spx/12-shipped-scripting.adr.md`
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
amend `21-installation-architecture.adr.md` to name the placement script a
Codex-specific adapter kept plugin-local under the exemption, or schedule the
extraction into `spx` and reduce the shipped script to the skill instruction the
ADR prescribes for a proven script. The duplicated algorithm in
`outcomeeng/distribution/installation.py` weighs toward extraction.

**Revisit condition**: with the next behavior change to placement, since any
addition deepens whichever path is not chosen.

**Evidence**: raised by changeset review `2026-08-17_01-03-44-668-0ddd9fe582a1`;
supersedes the ceiling entry the agents-conversion node carried for the earlier
fifty-line version.

## Cross-plugin agent-home cleanup is reachable only through the maintainers' installer

`spx/12-marketplace-state.adr.md` separates a plugin's namespace-bounded
placement from marketplace-scope reconciliation — the pass that prunes
definitions of plugins later removed or renamed from the catalog under the
marketplace's recorded ownership. The shipped `place_agents.py` implements only
its own plugin's namespace; the marketplace-scope pass lives in
`outcomeeng/distribution/installation.py` and is reachable solely through
`just install-marketplace` in this repository. An ordinary consumer whose
`$CODEX_HOME/agents/` carries a definition for a plugin the catalog no longer
publishes has no shipped path to prune it: the definition stays until the
consumer removes it by hand.

The retired plan for this node proposed embedding a committed-catalog snapshot,
stamped with a deterministic catalog revision, in each plugin's shipped tree so
any single plugin's lifecycle skill could run the marketplace-scope pass. That
mechanism was not built; the ownership record shipped instead, which lets the
maintainers' installer prune safely but gives a shipped script no view of the
current catalog.

**Resolution shape**: either ship the consumer-reachable marketplace-scope pass —
an embedded catalog snapshot the shipped script consults, or an `spx` command
that reads the marketplace source directly — or narrow the decision's
reconciliation invariant to the maintainers' installer and say so where the
consumer would look for the missing prune.

**Revisit condition**: before a plugin is removed or renamed in the catalog,
since that is the event that leaves a stale owned definition in consumer homes.

**Evidence**: raised by changeset review `2026-08-17_01-03-44-668-0ddd9fe582a1`.
