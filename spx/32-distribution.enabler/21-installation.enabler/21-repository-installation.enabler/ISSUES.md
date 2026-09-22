# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

## Native-profile evidence restates protocol vocabulary the owning modules hold

`tests/test_native_profile_execution.compliance.l1.py` indexes the child-thread document with the literal `parentThreadId` while `outcomeeng/distribution/native_thread_evidence.py` owns that key as `ChildIdentityField.PARENT`, and asserts the retained child-listing artifact through the literals `childIds`, `pages`, and `result`, for which that module publishes no field constants. Both are source-ownership defects: a rename in the owning module leaves the evidence asserting a contract production no longer emits.

`outcomeeng_testing/harnesses/native_thread_evidence.py` repeats the class in `RecordingThreadReader`: its failure-shaping methods hand-write `childIds`, `thread`, `turns`, `status`, and `items` while the same harness builds the payloads through `NativeChildLookupPayload`, `NativeChildThread`, and `NativeTurn` elsewhere. Its `_read_empty_native_state` builds the child environment from the literals `HOME`, `CODEX_HOME`, and `CODEX_SQLITE_HOME` while `outcomeeng/distribution/installation.py` publishes those names and the `STATE_ENV_NAMES` tuple.

Two clauses of the same assertion are also unfalsified: removing the ambient model and effort override filter from `_isolated_environment` in `outcomeeng_testing/harnesses/native_profile_execution.py`, or passing the unfiltered environment instead of `credential_free_environment`, breaks no linked test, because the tests inspect the recorded native calls only for their count and never read `NativeCall.environment`.

Two tests in the same compliance file, `test_real_native_read_reports_absent_thread_without_launching_a_turn` and `test_real_native_child_listing_retains_empty_pages_without_launching`, spawn the installed Codex CLI through the app-server read and listing commands while the file declares the `l1` cell; an installed agent CLI is an acquired executable whose level floor is `l2`, so those cases belong in an `l2` file.

The mapping assertion's identifier and disposable-state-root derivation is unfalsified in the same way: collapsing `identifier` in `native_profile_rows` to a constant makes every row share one `state_root` and one artifact directory, while `test_native_profile_rows_cover_the_central_configuration_matrix` still keys on target and profile and `test_native_profile_artifacts_are_separate_from_disposable_state` checks only parent-directory relations, so no predicate observes that the identifier and state root derive from the registry entry or are distinct per row.

**Resolution shape**: publish the listing-artifact field names from `outcomeeng/distribution/native_thread_evidence.py` beside `NativeChildLookupPayload`, import every key the test and the recording reader index from that module, add predicates over the recorded child environment that reject an ambient override or a second credential, and assert that every row's identifier and state root derive from its registry entry and differ from every other row's.

**Evidence**: test-evidence audit findings `f-001` and `f-002` against `06b86db6b31704c58203929603bb2f2ceea237cb`, `f-001` through `f-004` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`, `f-001` through `f-003` against `548f8cc7b598a30969b0e68c243acb17d387f1ef`, `f-001` through `f-003` against `d84b4d2cb433059d995e6271d33551e30deb306d`, `f-001` through `f-005` with `f-008` against `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, `f-001` through `f-007` against `be286e7e32cdfbb0cc782f6175ed0f274e428e8d`, `f-001` through `f-005` against `b9ee9c2ca56d3341f03ea81abb1ec2f4cd8df57b`, `f-005` through `f-009` against `ef8b057ab649bc3da5c642cc4a18fc6745023718`, `f-003` through `f-008` against `841e864a9759eae04c8988c2931aa44b1ca21c74`, `f-001` through `f-006` against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`, and `f-001` through `f-006` with `f-008` against `c3b42a5514452b1b71e01c77467e7e45abfad048`, the last seven rounds naming the execution-level mismatch and the last five naming the environment literals; the unfalsified row identifier and state root reached a finding of its own in the last round; the cited test and harness files lie outside every changeset's diff.

## The profile isolation filter strips an ambient marker no module declares

`_isolated_environment` in `outcomeeng_testing/harnesses/native_profile_execution.py`
removes the ambient overrides a profile probe must not inherit. Two of the three
names it strips come from imported constant sets their owning module publishes;
the third is the inline literal `CLAUDECODE`, which no module under `outcomeeng/`
declares. The harness therefore holds one name of the isolation policy that has
no source contract, so a change to that marker in production reaches no importer
and the filter keeps stripping a name the product no longer uses, or stops
stripping one it does.

This is not the class the native-profile entry above records. That entry covers
evidence restating vocabulary the owning modules hold, whose remedy is to import
from the owner; here there is no owner to import from and the remedy is to
publish the name first.

**Resolution shape**: publish the ambient marker from the module that owns the
isolation policy, beside the constant sets the filter already imports, and have
`_isolated_environment` import it.

**Settlement condition**: the marker is published from an owning module and the
filter imports it rather than spelling it.

**Evidence**: test-evidence audit finding `f-010` (INFO) against `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322`. The cited
harness lies outside that changeset's diff, and the remedy publishes a constant
from a production module the changeset's Frame does not name.

## Pending plugins' prior owned definitions have no reconciliation evidence

The reconciliation assertion states that a pending plugin's prior owned definitions are preserved, and both `spx/12-marketplace-state.adr.md` and `21-installation-architecture.adr.md` require it, but no harness case combines a pending-publication plugin with agent-home reconciliation: `observe_agent_home_reconciliation` builds both preflights from a changed catalog with every plugin published. The clause therefore reaches no predicate, and the same observer retires one agent source rather than dropping a plugin from the home selection, so the clause that prunes owned definitions of plugins outside the catalog-bounded selection is likewise never driven. The plan builder also composes the agent-home plan before any command runs, so a plugin that turns out pending during execution still has its checkout definitions in the desired set; whether the applied plan copies definitions for unavailable skill content, against the decision, is undetermined until the scenario exists.

**Resolution shape**: add a harness scenario that installs, then re-runs with one plugin unpublished, and assert that the pending plugin's recorded definitions are neither pruned nor rewritten; if the scenario shows the plan copying definitions for a pending plugin, defer agent-home plan composition until the pending set is known. That is a new reconciliation capability with its own harness and a likely production change, independent of the machine-wide Claude Code refresh.

**Evidence**: test-evidence audit finding `f-005` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`, `f-004` against `548f8cc7b598a30969b0e68c243acb17d387f1ef`, `f-006` against `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, `f-008` against `be286e7e32cdfbb0cc782f6175ed0f274e428e8d`, `f-006` against `b9ee9c2ca56d3341f03ea81abb1ec2f4cd8df57b`, `f-004` against `ef8b057ab649bc3da5c642cc4a18fc6745023718`, and `f-009` against `841e864a9759eae04c8988c2931aa44b1ca21c74`; the round against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a` did not raise it, and `f-007` against `c3b42a5514452b1b71e01c77467e7e45abfad048` raises both its clauses. The recording runner's `unpublished` set now makes a pending plugin cheap to drive through the reconciliation observer, which lowers the cost of the harness scenario the resolution shape names.

## A dead-parameter sweep matched a spelling rather than the class

A repair round swept for parameters a function body discards with an explicit
delete statement and reported the class closed. The class is every parameter of
a non-Protocol function that no call site supplies and no interface obliges,
however the body treats it, so a parameter read inside a branch no caller can
reach never matched the spelling. The next audit round raised one such parameter
as blocking: a private command helper carried a working-directory keyword whose
only reachable effect was forbidden by the governing decision.

**Resolution shape**: a dead-parameter scan cross-references every function the
changeset adds or changes against its call sites and exempts only Protocol
methods, constructors reached through the class name, methods reached through an
instance, and framework-supplied test parameters. Matching text finds the
instance; matching the call graph finds the class.

**Evidence**: implementation audit finding against
`a47f88e39d2a5fe9318eb24e6140623ca774dcfa`, under the same rule as a finding
repaired one round earlier against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`.
The widened scan over that changeset examined 310 functions, found five members
of the class where the narrow sweep had found one, and changed all five.

## The no-lock clause of the listing-read rule has no deterministic oracle

The compliance assertion that a persistent run reads the install-record listing once before and once after execution also states that it issues no lock, wait, or retry against the agent's record store. `test_a_persistent_run_reads_the_listing_once_before_and_once_after_execution` falsifies the read-count and retry clauses through the recorded commands; a lock is not a command, so adding an advisory lock around the listing read in production leaves both listing counts at one and the test passing.

**Resolution shape**: route the no-lock clause to audit evidence in the governing decision, where the absence of a lock is a structural judgment, or add a record-store observation the harness owns — a runner that reports every open on the record file — so the clause reaches a predicate.

**Evidence**: test-evidence audit finding `f-010` (WARNING) against `841e864a9759eae04c8988c2931aa44b1ca21c74`, `f-007` (WARNING) against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`, `f-008` (WARNING) with the implementation audit's matching debt finding against `a47f88e39d2a5fe9318eb24e6140623ca774dcfa`, which names the same absent oracle from the recorded-command seam, and `f-009` (WARNING) against `c3b42a5514452b1b71e01c77467e7e45abfad048`.

## Claude Code renderings ship the Codex-only placement script and paraphrase its output

The `<plugin>-plugin` skill's Claude Code rendering carries `scripts/place_agents.py`, roughly 330 lines that its own `<agent_delivery>` section says are never invoked there, because the shared template `src/templates/plugin/SKILL.md` conditions other sections on the build target but not the script directory. The same skill's `<examples>` paraphrases the manifest-delivery line instead of quoting the sentence `<verbs>` prints, and the `<verbs>` table's result column for `init`, `upgrade`, and `check` describes the Codex home reconciliation in the Claude Code rendering too, leaving the next sentence to walk all three rows back for that target.

**Resolution shape**: exclude `scripts/` from the Claude Code rendering in the shared template, or state in `<agent_delivery>` why an inert copy must ship; quote the printed sentence verbatim in `<examples>`; render the three result cells per target. Either change touches every plugin's rendered skill, so it lands as one template change gated by the skill auditor.

**Evidence**: skill audit warnings `f-007` and `f-008` against `06b86db6b31704c58203929603bb2f2ceea237cb`, and `f-006` and `f-007` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`.

## Lifecycle evidence cases are hand-authored in the harness

The lifecycle tests in `tests/test_repository_installation.compliance.l1.py` take their agent-definition bytes, filenames, and slugs from `PluginLifecycleHarness` in `outcomeeng_testing/harnesses/installation.py`, and the foreign, external, concurrent-edit, malformed-digest, and malformed-settings payloads from constants the same module declares; every token the tests assert against is imported from the shipped placement script. Two verifier readings of that arrangement stand side by side. The isolated test-evidence audit on `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, finding `f-009`, names the payloads incidental harness-handle values, because the script treats definition bytes opaquely by digest and every asserted token is source-owned. Changeset review `2026-09-16_02-49-48-063-4c9876671778` holds that relocating hand-authored bytes into the harness settles no case provenance and asks for a generator under `outcomeeng_testing/generators/`; the audits on `ef8b057ab649bc3da5c642cc4a18fc6745023718` (`f-012`, INFO), `841e864a9759eae04c8988c2931aa44b1ca21c74` (`f-011`, INFO), and `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a` (`f-008`, INFO) record the same split.

**Settlement condition.** A generator-sourced origin for the definition bytes and ownership documents, recorded in the assertion-design record, or an operator ruling that the audit's reading governs, recorded here.

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
