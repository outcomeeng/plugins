# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

## Native-profile evidence restates protocol vocabulary the owning modules hold

`tests/test_native_profile_execution.compliance.l1.py` indexes the child-thread document with the literal `parentThreadId` while `outcomeeng/distribution/native_thread_evidence.py` owns that key as `ChildIdentityField.PARENT`, and `tests/test_native_profile_execution.compliance.l2.py` asserts the retained child-listing artifact through the literals `childIds`, `pages`, and `result`, which that module publishes no constant for — the producer-side gap the next entry records. Both are source-ownership defects: a rename in the owning module leaves the evidence asserting a contract production no longer emits.

`outcomeeng_testing/harnesses/native_thread_evidence.py` repeats the class in `RecordingThreadReader`: its failure-shaping methods hand-write `childIds`, `thread`, `turns`, `status`, and `items` while the same harness builds the payloads through `NativeChildLookupPayload`, `NativeChildThread`, and `NativeTurn` elsewhere. Its `_read_empty_native_state` builds the child environment from the literals `HOME`, `CODEX_HOME`, and `CODEX_SQLITE_HOME` while `outcomeeng/distribution/installation.py` publishes those names and the `STATE_ENV_NAMES` tuple.

Two clauses of the same assertion are also unfalsified: removing the ambient model and effort override filter from `_isolated_environment` in `outcomeeng_testing/harnesses/native_profile_execution.py`, or passing the unfiltered environment instead of `credential_free_environment`, breaks no linked test, because the tests inspect the recorded native calls only for their count and never read `NativeCall.environment`.

The mapping assertion's identifier and disposable-state-root derivation is unfalsified in the same way: collapsing `identifier` in `native_profile_rows` to a constant makes every row share one `state_root` and one artifact directory, while `test_native_profile_rows_cover_the_central_configuration_matrix` still keys on target and profile and `test_native_profile_artifacts_are_separate_from_disposable_state` checks only parent-directory relations, so no predicate observes that the identifier and state root derive from the registry entry or are distinct per row.

**Resolution shape**: import every key the test and the recording reader index from the module that owns it, which for the three listing-artifact keys waits on the publication the next entry records, add predicates over the recorded child environment that reject an ambient override or a second credential, and assert that every row's identifier and state root derive from its registry entry and differ from every other row's.

**Evidence**: test-evidence audit findings `f-001` and `f-002` against `06b86db6b31704c58203929603bb2f2ceea237cb`, `f-001` through `f-004` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`, `f-001` through `f-003` against `548f8cc7b598a30969b0e68c243acb17d387f1ef`, `f-001` through `f-003` against `d84b4d2cb433059d995e6271d33551e30deb306d`, `f-001` through `f-005` with `f-008` against `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, `f-001` through `f-007` against `be286e7e32cdfbb0cc782f6175ed0f274e428e8d`, `f-001` through `f-005` against `b9ee9c2ca56d3341f03ea81abb1ec2f4cd8df57b`, `f-005` through `f-009` against `ef8b057ab649bc3da5c642cc4a18fc6745023718`, `f-003` through `f-008` against `841e864a9759eae04c8988c2931aa44b1ca21c74`, `f-001` through `f-006` against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`, `f-001` through `f-006` with `f-008` against `c3b42a5514452b1b71e01c77467e7e45abfad048`, and `f-001` through `f-006` against each of `9ab0fc92c2f5c673edbfb2c73eea42502cef68e5` and `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322`, the last nine rounds naming the execution-level mismatch and the last five naming the environment literals; the unfalsified row identifier and state root reached a finding of its own in the last round; the cited test and harness files lie outside every changeset's diff. The round against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` raised the same six as `f-001` through `f-006`: `f-001` the literal `parentThreadId` where `ChildIdentityField.PARENT` owns the key; `f-002` the literals `childIds`, `pages` and `result`, for which production publishes no field constant; `f-003` the hand-written keys in `RecordingThreadReader` and the environment names in `_read_empty_native_state`; `f-004` the two `l1` cases that start the installed Codex CLI, whose floor is `l2`; `f-005` the unfalsified override and credential clauses; `f-006` the unfalsified row identifier and state root. The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised the same six again as `f-001` through `f-006`.

## The child-listing artifact's keys are written as literals and published nowhere

`outcomeeng/distribution/native_thread_evidence.py` builds and reads the retained
child-listing artifact through the bare literals `childIds`, `pages`, and `result`, and
publishes a constant for none of them. It publishes `ChildIdentityField` for the
thread/read identity fields (lines 27-35) and `NativeChildLookupPayload` for the payload's
shape, so the module already states which of its keys are a contract; these three are a
contract it emits and does not name.

**The eleven sites.** `childIds` at lines 139, 326, and 369; `pages` at lines 326, 368,
374, and 382; `result` at lines 254, 286, 334, 361, and 437 — twelve occurrences across
eleven lines, since line 326 carries two. Line 139 reads the key back out of a document the
same module wrote at 326, so a rename reaches both halves of one round trip through two
independently spelled literals.

**What it blocks.** `tests/test_native_profile_execution.compliance.l2.py` indexes the same
three keys at lines 24 and 25 and is a source-ownership defect for doing so, recorded in the
entry above. That defect cannot be repaired while this one stands: the rule requires the
evidence to import the name from the source complying with the declaration, and there is no
published name to import. The evidence half waits on this half.

**Resolution shape**: publish the three keys from this module beside
`NativeChildLookupPayload` — a field enum in the shape of `ChildIdentityField`, or module
constants — and read every one of the eleven sites from it, so the writer and the reader at
lines 326 and 139 spell the key once.

**Why separate**: the module lies outside this changeset's diff while the evidence file lies
inside it. Publishing a contract from a production module no Frame here names is a change to
the producer, which is neither the Author's to make nor the Executor's to authorise, so the
evidence half stays unrepaired until a Change carries the producer. Every round that audits
this node raises the evidence half again while that holds; the re-raise is this entry doing
its work, and each one is another reading for the Change that closes it.

**Settlement condition**: `outcomeeng/distribution/native_thread_evidence.py` publishes a
constant for each of `childIds`, `pages`, and `result`, every site in that module reads it,
and `tests/test_native_profile_execution.compliance.l2.py` imports the three names rather
than spelling them.

**Evidence**: the literal sites above against the module's own published
`ChildIdentityField` and `NativeChildLookupPayload`; and the test-evidence audit rounds
recorded in the entry above, whose finding on the evidence half named these keys as the ones
the owning module publishes no constant for.

## The ambient-marker entry was wrong on its premise, and the import landed

This entry recorded that `_isolated_environment` in
`outcomeeng_testing/harnesses/native_profile_execution.py` stripped the ambient marker
`CLAUDECODE` through an inline literal that no module declared, and proposed publishing the
name as the remedy.

The premise was wrong. `outcomeeng_evals/runner.py` declares it as `CLAUDECODE_ENV`, and
`outcomeeng_testing/harnesses/eval_runner.py` already imports it. The entry read "no module
under `outcomeeng/` declares it", which is true of that one package and false of the product,
and it drew the wrong remedy from it: nothing needed publishing, only importing.

**Landed.** The filter imports `CLAUDECODE_ENV` from its owner. The entry stays as the record
that a filing proposed a publication the product already had, so a later reader meets the
correction rather than the claim.

**Evidence**: `CLAUDECODE_ENV` at `outcomeeng_evals/runner.py:45`, its import in
`outcomeeng_testing/harnesses/eval_runner.py`, and the node's test-evidence audit finding on
the frozen head `3d1dbffd76393c71dbbaf455f5c81c81bf015064`, which named the owner this entry
said did not exist. The rounds against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` and
`cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised the same claim again as `f-018` and `f-016`
(INFO).

## The child-identity literal is checked by the type that declares it

An audit round raised `case.thread["parentThreadId"]` in
`tests/test_native_profile_execution.compliance.l1.py` as a source-ownership defect, on the
ground that `outcomeeng/distribution/native_thread_evidence.py` owns that key as
`ChildIdentityField.PARENT` and the same file already imports the enum.

The finding is wrong on its premise. `case.thread` is the TypedDict `NativeChildThread`,
which declares `parentThreadId` as one of its fields, so the literal is read against the type
that owns it and the type checker enforces the agreement: renaming the field makes this site
a `typeddict-item` error rather than a passing test over a key production no longer emits.
That is the guarantee the source-ownership rule asks for, supplied by the checker.

Substituting the enum makes it worse, not better. A TypedDict admits only a literal key, so
`case.thread[ChildIdentityField.PARENT]` fails `mypy --strict` with exactly that error — the
enum cannot index the payload at all. The two declarations coexist for different jobs: the
TypedDict field types the payload, and the enum keys the identity fields the reader iterates,
which is how lines 88 and 98 of the same test use it.

**Settlement condition.** None. A later round raising this site reads this entry first. If the
module's two declarations of the same key are themselves the defect, that is a change to the
producer and belongs with the entry on its unpublished listing keys.

**Evidence.** `NativeChildThread` at `outcomeeng/distribution/native_thread_evidence.py:61-69`
declaring `parentThreadId`; the `typeddict-item` error `mypy --strict` reports for the enum
form; and `ChildIdentityField` iterated at lines 88 and 98 of the test, which is the use the
enum is for.

## The installation harness restates names its product modules own

A source-ownership sweep over every string literal in this node's and the gate node's evidence files — matching each literal against the module-level string constants `outcomeeng/` declares, then judging each match by role — reports thirty-five same-value matches outside the changeset's own lines: thirty-three in `outcomeeng_testing/harnesses/installation.py` and two in `tests/test_repository_installation.compliance.l1.py`. Seven of the harness matches are the disposable `state` directory against a merge-record field of the same name and are not instances by role, leaving twenty-eight sites the classes below cover. None lies on a line the agent-disable-switch changeset touches. The classes are: the plugin-tree subdirectory names `skills`, `scripts`, and `agents` and the lifecycle template directory `plugin`, owned by `outcomeeng/distribution/contracts.py` (`SKILLS_SUBDIR_NAME`, `SCRIPTS_SUBDIR_NAME`, `AGENTS_SUBDIR_NAME`) and `outcomeeng/distribution/build.py` (`LIFECYCLE_TEMPLATE_NAME`); the CLI options `--checkout` and `--json`, owned by `outcomeeng/distribution/installation.py` (`CHECKOUT_OPTION`, `JSON_OUTPUT_OPTION`); the agent executable and home names `claude`, `codex`, and the source type `git`, owned by that same module (`CLAUDE_EXECUTABLE`, `CODEX_EXECUTABLE`, `CODEX_GIT_SOURCE_TYPE`); and the flat definition-name separator in `definition_name`, owned by `outcomeeng/distribution/build.py` (`FLAT_AGENT_PLUGIN_SEPARATOR`). A rename in any owner leaves the harness shaping a stimulus, or the test asserting an option, that production no longer emits.

The same sweep's remaining matches are not instances and need no change: a `pytest.mark.parametrize` parameter name (`switch`, `path`, `kind`), an f-string fragment that happens to equal a constant's value (the decorator sigil, a filename joiner), and a value whose role differs from its namesake's (the disposable `state` directory against a merge-record field name, a path separator against an environment separator).

**Resolution shape**: import each name from the module that owns it at every site, as the changeset did for the git status vocabulary, the Python source roots, and the justfile name. One sweep over the harness, then this node's test-evidence audit.

**Why separate**: every site lies outside the agent-disable-switch changeset's diff, and the sweep spans a 3,400-line harness whose other consumers this Change does not touch.

**Evidence**: the ownership sweep re-run while closing the same class inside the changeset's own lines, which found two instances there — a skip-report file suffix and the pytest module name — and repaired both.

## Pending plugins' prior owned definitions have no reconciliation evidence

The reconciliation assertion states that a pending plugin's prior owned definitions are preserved, and both `spx/12-marketplace-state.adr.md` and `21-installation-architecture.adr.md` require it, but no harness case combines a pending-publication plugin with agent-home reconciliation: `observe_agent_home_reconciliation` builds both preflights from a changed catalog with every plugin published. The clause therefore reaches no predicate, and the same observer retires one agent source rather than dropping a plugin from the home selection, so the clause that prunes owned definitions of plugins outside the catalog-bounded selection is likewise never driven. The plan builder also composes the agent-home plan before any command runs, so a plugin that turns out pending during execution still has its checkout definitions in the desired set; whether the applied plan copies definitions for unavailable skill content, against the decision, is undetermined until the scenario exists.

**Resolution shape**: add a harness scenario that installs, then re-runs with one plugin unpublished, and assert that the pending plugin's recorded definitions are neither pruned nor rewritten; if the scenario shows the plan copying definitions for a pending plugin, defer agent-home plan composition until the pending set is known. That is a new reconciliation capability with its own harness and a likely production change, independent of the machine-wide Claude Code refresh.

**Evidence**: test-evidence audit finding `f-005` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`, `f-004` against `548f8cc7b598a30969b0e68c243acb17d387f1ef`, `f-006` against `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, `f-008` against `be286e7e32cdfbb0cc782f6175ed0f274e428e8d`, `f-006` against `b9ee9c2ca56d3341f03ea81abb1ec2f4cd8df57b`, `f-004` against `ef8b057ab649bc3da5c642cc4a18fc6745023718`, and `f-009` against `841e864a9759eae04c8988c2931aa44b1ca21c74`; the round against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a` did not raise it, and `f-007` against each of `c3b42a5514452b1b71e01c77467e7e45abfad048`, `9ab0fc92c2f5c673edbfb2c73eea42502cef68e5`, and `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322` raises both its clauses. The recording runner's `unpublished` set now makes a pending plugin cheap to drive through the reconciliation observer, which lowers the cost of the harness scenario the resolution shape names. The round against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` raised both clauses again as `f-007`: "Two paths are never driven: the pending-publication reconciliation path, where a pending plugin's prior owned definitions must be preserved, and the pruning path for plugins that leave the catalog-bounded home selection." The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised both clauses again as `f-007`.

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

**Evidence**: test-evidence audit finding `f-010` (WARNING) against `841e864a9759eae04c8988c2931aa44b1ca21c74`, `f-007` (WARNING) against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`, `f-008` (WARNING) with the implementation audit's matching debt finding against `a47f88e39d2a5fe9318eb24e6140623ca774dcfa`, which names the same absent oracle from the recorded-command seam, `f-009` (WARNING) against `c3b42a5514452b1b71e01c77467e7e45abfad048`, and `f-008` (WARNING) against each of `9ab0fc92c2f5c673edbfb2c73eea42502cef68e5` and `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322`. The round against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` raised it as `f-013` (WARNING): "The read-count and retry clauses are falsified through the recorded commands. A lock is not a command, so adding an advisory lock around the listing read leaves both counts at one and the test passing. The no-lock clause has no deterministic oracle." The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-013` (WARNING).

## Claude Code renderings ship the Codex-only placement script and paraphrase its output

The `<plugin>-plugin` skill's Claude Code rendering carries `scripts/place_agents.py`, roughly 330 lines that its own `<agent_delivery>` section says are never invoked there, because the shared template `src/templates/plugin/SKILL.md` conditions other sections on the build target but not the script directory. The same skill's `<examples>` paraphrases the manifest-delivery line instead of quoting the sentence `<verbs>` prints, and the `<verbs>` table's result column for `init`, `upgrade`, and `check` describes the Codex home reconciliation in the Claude Code rendering too, leaving the next sentence to walk all three rows back for that target.

**Resolution shape**: exclude `scripts/` from the Claude Code rendering in the shared template, or state in `<agent_delivery>` why an inert copy must ship; quote the printed sentence verbatim in `<examples>`; render the three result cells per target. Either change touches every plugin's rendered skill, so it lands as one template change gated by the skill auditor.

**Evidence**: skill audit warnings `f-007` and `f-008` against `06b86db6b31704c58203929603bb2f2ceea237cb`, and `f-006` and `f-007` against `3e1ba91c9ec059d96dcd2007a2fe371681599df2`.

## Lifecycle evidence cases are hand-authored in the harness

The lifecycle tests in `tests/test_repository_installation.compliance.l1.py` take their agent-definition bytes, filenames, and slugs from `PluginLifecycleHarness` in `outcomeeng_testing/harnesses/installation.py`, and the foreign, external, concurrent-edit, malformed-digest, and malformed-settings payloads from constants the same module declares; every token the tests assert against is imported from the shipped placement script. Two verifier readings of that arrangement stand side by side. The isolated test-evidence audit on `f689b9b25cdd37f5e57545d313f30d29ad9cbd35`, finding `f-009`, names the payloads incidental harness-handle values, because the script treats definition bytes opaquely by digest and every asserted token is source-owned. Changeset review `2026-09-16_02-49-48-063-4c9876671778` holds that relocating hand-authored bytes into the harness settles no case provenance and asks for a generator under `outcomeeng_testing/generators/`; the audits on `ef8b057ab649bc3da5c642cc4a18fc6745023718` (`f-012`, INFO), `841e864a9759eae04c8988c2931aa44b1ca21c74` (`f-011`, INFO), `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a` (`f-008`, INFO), and `9ab0fc92c2f5c673edbfb2c73eea42502cef68e5` and `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322` (`f-009`, INFO) record the same split. The round against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` records it again as `f-017` (INFO), citing the definition bytes, slugs, and foreign, external, concurrent-edit and malformed payloads the harness declares.

**Settlement condition.** A generator-sourced origin for the definition bytes and ownership documents, recorded in the assertion-design record, or an operator ruling that the audit's reading governs, recorded here.

The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` records it again as `f-017` (INFO).

The round against `01fa8e8acc904fb102bffa8dc66f5c4a14374748` raised the class at the test sites as `f-009` (REJECT)
against `tests/test_repository_installation.compliance.l1.py:108`: "The lifecycle
tests choose incidental plugin and agent slugs as call-site literals:
plugin_name=\"fixture\", and ship(\"auditor\"/\"current\"/\"retired\"/\"exact\"/\"changed\")
at 108-110, 143-146, 226-229, 296-299 and elsewhere. No assertion states these
values, and they survive both negation and transplant, so they belong to a
harness or generator rather than the test file." The same settlement closes
it: a generator supplies the slugs, or an operator ruling decides the reading.

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

## The unrefreshable record disposition, and the rewrite half of the unresolved one, reach no evidence

`plan_install_record_rewrite` in `outcomeeng/distribution/installation.py`
reports a record whose target version has no cache directory with
`UNREFRESHABLE_RECORD_WARNING`, and `unresolved_target_warnings` reports a
record whose plugin resolves to no target version with
`UNRESOLVED_TARGET_RECORD_WARNING`; both are blocking, and
`21-installation-architecture.adr.md` declares both in prose.

The unresolved disposition now reaches a declaration and a case in the shape
where its domain and the rewrite's diverge: the scenario assertion linking
`tests/test_repository_installation.scenario.l1.py` drives a clone whose
manifest for one cataloged plugin carries no version, with that plugin
recorded only in the invocation checkout, and asserts the report's warning,
the absent target version, the empty off-target set, another plugin's record
still moving, and the nonzero exit. Two gaps survive that case.

The unrefreshable disposition is still never entered. Every observer in
`outcomeeng_testing/harnesses/installation.py` serves the target version for
the whole catalog through `_serve_clone_versions` and creates a cache
directory for every cataloged plugin, so removing that warning leaves every
linked test passing.

The unresolved disposition's other half is likewise undriven: the new case
records the unresolved plugin in the invocation checkout alone, so no case
carries such a plugin recorded in another checkout, where the record is left
unchanged rather than natively updated.

Neither disposition is a member of the record-mapping assertion's domain
either: that assertion enumerates the out-of-catalog and out-of-scope
warnings only, so for the mapping lane the gap is a declaration gap before it
is an evidence gap.

**Resolution shape**: give the record-mapping assertion both dispositions,
then drive each from the harness — a served target version with no cache
directory for the unrefreshable record, and a clone that cannot version a
plugin another checkout records for the rewrite half of the unresolved one —
asserting that the named record is left unchanged while every other plugin's
records still move.

**Why separate**: each needs a clone or cache shape no present observer
builds, so the pair is a new evidence lane with its own harness support, and
carrying either into the mapping assertion's finite domain is a decision
amendment rather than a predicate over the assertions this changeset carries.

**Settlement condition**: the record-mapping assertion names both
dispositions and a case drives each with another plugin's records moving
beside it.

**Evidence**: found by this changeset's sweep for states the spec declares
whose linked evidence carries no invocation-checkout record; both warnings
are introduced by this changeset. The invocation-checkout reach of the
unresolved disposition was a defect rather than a gap — the disposition was
computed over the rewrite candidates alone, so a run whose only record of an
unresolvable plugin belonged to the invocation checkout exited zero — and is
repaired in this changeset against the architecture decision's exit-code and
coverage assertions.

## The listing-defect evidence never pairs a defect with an invocation-checkout record

`observe_defective_record_listing` in `outcomeeng_testing/harnesses/installation.py`
builds its listing from `generated_listing_defect_records`, which emits a
pathless entry, a versionless entry, and one well-formed record in another
checkout. The invocation checkout records nothing there, so the run's
continuation past either defect is observed for the rewrite disposition and for
the bootstrap install and enable, never for the native update of a record the
invocation checkout holds. `21-installation-architecture.adr.md` states that
neither defect settles anything about the rest of the machine's records, and the
native update is one of the dispositions that rest carries, so a regression that
abandoned that branch on a defect would leave every linked test passing.

**Resolution shape**: give `generated_listing_defect_records` an
invocation-checkout record beside the two defects and the other checkout's
record, and retain the present listing as a second case, so the defect state is
paired with the native-update disposition as well as the bootstrap one.

**Why separate**: the present case's assertion that the bootstrap install and
enable still run past each defect is itself the evidence for the bootstrap
disposition, and an invocation-checkout record suppresses bootstrap, so the
pairing adds an observation rather than widening this one — a second observer
and a generator parameter, not an assertion.

**Settlement condition**: a defect case whose listing carries a record of the
invocation checkout, asserting that its native update still runs.

**Evidence**: found by this changeset's sweep for states the spec declares whose
linked evidence carries no invocation-checkout record — the same class that
produced the withheld-registration case now covered in
`tests/test_repository_installation.scenario.l1.py`.

The round against `114c56d96942138058a10caae796bd59d83e20ec` raised it as
`f-013` (WARNING): "generated_listing_defect_records, consumed by
observe_defective_record_listing, carries no record of the invocation checkout.
Continuation past a defect is therefore observed only for the rewrite and
bootstrap dispositions, never for the native update of a record the invocation
checkout holds."

## Two review surfaces report success for something that did not happen

The changeset review has two surfaces that read as success while the thing they
appear to report never occurred. They are one defect class, and both are silent:
the officer sees a success and stops looking.

**The mention dispatches nothing.** `spx/local/merging.md` documents a trigger
phrase for re-running the changeset review, and `.github/workflows/spec-tree-review.yml`
passes that phrase to the reusable workflow it calls. The caller's own triggers
are `pull_request` on `opened`, `synchronize`, and `reopened` alone, so no
comment event reaches it and the phrase can dispatch no run on this repository.
The failure is not an inert control: runs of that workflow appear continuously
for other pull requests, so an officer who comments, then reads the run list,
sees a run start and concludes it is theirs. Establishing otherwise takes reading
each run's head.

**A green check row is not an approval.** The `spec-tree-review` check row
reports the workflow's exit status, and the workflow exits zero whether the
review approves or rejects; the verdict is written as a pull-request
conversation comment. The row and the verdict are therefore two readings that
can disagree, and the disagreement is invisible from the row: a pull request can
read CLEAN with every check green while carrying an unaddressed BLOCKING finding
on its current head.

**Resolution shape**: for the mention, either give the caller a
`issue_comment` trigger that honours the documented phrase and guards it to
pull-request comments on the right head, or remove the phrase from the overlay
and from the caller's inputs and state in the overlay that a re-run is a
re-dispatch of the run rather than a comment. For the check row, either make the
workflow's exit status carry the verdict, or name the row in the overlay as a
liveness signal and state that `MERGE_READINESS`'s review predicate reads the
conversation comment on the current head.

**Why separate**: both artifacts are the review workflow's own surface and its
overlay, governed by the merge lifecycle rather than by installation; neither
lies in this changeset's diff, and the exit-status change alters what every
pull request in the repository reports.

**Settlement condition**: the documented trigger dispatches a run on the pull
request it is commented on, or no trigger phrase is documented; and the check
row either carries the verdict or is declared a liveness signal beside the
predicate that reads the verdict.

**Evidence**: established against pull request 601. The mention posted at
2026-09-22T13:52Z dispatched no run — the run that appeared next,
`35730806082`, belongs to a different pull request on branch
`work/apply-output-lanes` — and the review had to be re-dispatched by re-running
`35726901359` instead. The same pull request's `spec-tree-review` row read green
while the 2026-09-22T12:40:10Z conversation comment carried three unaddressed
DEBT findings. Both were found by reading the surfaces against what they
claimed, not by any gate.

## The lifecycle evidence hand-writes the placement script's flags and exit statuses

`tests/test_repository_installation.compliance.l1.py` passes `--home`, `--checkout`
and `--check` to the shipped placement script as hand-written literals, and
`PluginLifecycleHarness.run` in `outcomeeng_testing/harnesses/installation.py`
spells the same three. `src/templates/plugin/scripts/place_agents.py` declares
them only inline in its `argparse` block and publishes no constant, so the
evidence copies a command-line vocabulary it cannot import. The lifecycle tests also assert
the script's exit statuses as the literals `1` and `2`, which the script returns
bare, so the status vocabulary is copied the same way.

**Impact**: a flag renamed in the script leaves the evidence invoking a command
line the script rejects, and the failure reads as a placement defect rather
than a renamed flag.

**Resolution shape**: publish the three flags and the two exit statuses as
module constants of the placement script, build its `argparse` block and its
returns from them, and import them in the test and the harness. The script ships in every plugin's rendered skill, so the
change takes a plugin version bump and the skill auditor's gate.

**Settlement condition**: the placement script publishes its flags and exit
statuses, and no test or harness under this node spells one.

**Evidence**: test-evidence audit finding `f-010` (REJECT) against `05a7165277750d69c88bc8abbece2c4f6a96bb7c`:
"The placement script's command tokens \"--home\", \"--checkout\" and \"--check\"
are hand-written in the test (:376, :408) and in PluginLifecycleHarness.run
(outcomeeng_testing/harnesses/installation.py:502-508). The shipped script
declares them only inline in argparse (src/templates/plugin/scripts/place_agents.py:220-222)
and publishes no constant, so the lifecycle evidence copies a CLI vocabulary it
cannot import." The finding sits in a file the discovery-login security fix
touches; the fix changes a shipped script and bumps a plugin, which that fix
does not carry.

The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-008` (REJECT), adding the exit
statuses the tests assert as literals.

## A failed persistent run restores the committed selection, which the decisions forbid

`execute_persistent_installation` in `outcomeeng/distribution/installation.py`
re-applies the checkout's declared plugin selection in a `finally` block through
`_restore_plugin_selection`, so a run that fails partway writes the pre-run
selection back into the checkout's settings.
`test_failed_persistent_run_restores_the_committed_selection` in
`tests/test_repository_installation.compliance.l1.py` asserts that write. The
decisions say the opposite: `spx/12-marketplace-state.adr.md` states that
verification reports an unexpected selection or activation change as failure and
preserves the diagnostic state, and that refresh never restores an old settings
snapshot; `21-installation-architecture.adr.md` states that unexpected changes
are terminal diagnostics with no snapshot restoration or compensating activation
writes; and the node spec's untagged assertion states that the run retains the
changed state for diagnosis without restoring an earlier settings snapshot. No
linked assertion declares the restore the test evidences.

**Impact**: production and its evidence agree with each other and disagree with
the decision. A failed run leaves no diagnostic state for the selection it
changed, and a reader of the passing test takes the restore for declared
behavior.

**Settlement condition**: either the decisions declare the restore and the spec
links the test to that declaration, or production stops restoring and the test
asserts that the changed state is retained. The choice between them is a
decision change, not a test repair.

**Evidence**: test-evidence audit finding `f-019` (INFO) against `05a7165277750d69c88bc8abbece2c4f6a96bb7c`:
"test_failed_persistent_run_restores_the_committed_selection checks that
production re-applies the declared plugin selection after a failed run
(_restore_plugin_selection, outcomeeng/distribution/installation.py:1485). No
linked [test] assertion declares that behavior, and the untagged spec assertion
plus the ADR say failed runs retain changed state without restoring a snapshot." The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-018` (INFO).

## The discovery harness rebuilds the isolated Codex home instead of reading the plan

`outcomeeng_testing/harnesses/installation.py` rebuilds the isolated Codex home
as `state / "codex"` in the subagent-discovery observation rather than reading
`plan.roots.codex_home`, and `outcomeeng/distribution/installation.py` spells
the same directory inline and publishes no constant for it.

**Impact**: a change to where isolated installation places the Codex home
leaves the discovery probe pointed at a directory the installation never
populated.

**Settlement condition**: the harness reads the Codex home from the plan it
executed, and production names the directory once.

**Evidence**: test-evidence audit finding `f-015` (WARNING) against `05a7165277750d69c88bc8abbece2c4f6a96bb7c`; the
harness lies outside the diff of the discovery-login security fix. The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-012` (WARNING).

## The record-mapping test picks its publication rows in the test file

`test_every_claude_install_record_maps_to_one_update_one_rewrite_or_one_warning`
in `tests/test_repository_installation.mapping.l1.py` parametrizes over two rows
the test file chooses — no plugin pending, and the first committed catalog plugin
pending — and picks its case plugin with `sorted(...)[0]`. The mapping assertion
states no publication dimension, and no source-owned domain or generator selects
the rows.

**Impact**: the publication cases are the test author's choice, so the mapping
claims no coverage of pending publication beyond the two rows picked.

**Settlement condition**: a generator supplies the publication rows over a
declared domain, or the mapping assertion states the publication dimension and
its domain supplies the rows.

**Evidence**: test-evidence audit finding `f-010` (REJECT) against `01fa8e8acc904fb102bffa8dc66f5c4a14374748`: "The test
file chooses parametrize rows [frozenset(), frozenset({sorted(committed_catalog_plugin_names())[0]})]
with ids all-published/one-pending (172-176). Line 143 picks a case plugin with
sorted(...)[0]. These rows introduce a publication dimension the mapping
assertion does not state, and neither a source-owned domain nor a generator
selects them." The rows predate the discovery-login security fix, which touches
this file only to add the git-source mapping; they are recorded here under the
convergence-stall rule by the Director's ruling.

## The scenario tests pick their case plugin in the test file

The isolated-absence and pending-publication scenarios in
`tests/test_repository_installation.scenario.l1.py` choose their case plugin
with `sorted(committed_catalog_plugin_names())[0]`. The assertions name no
particular plugin, so the choice is a call-site value no assertion states. This
is the class the record-mapping entry above records for the mapping test.

**Settlement condition**: a generator supplies the case plugin, and no scenario
under this node picks one at the call site.

**Evidence**: test-evidence audit finding `f-010` (REJECT) against
`114c56d96942138058a10caae796bd59d83e20ec`: "The scenario tests pick their case
plugin in the test file with sorted(committed_catalog_plugin_names())[0] at lines
172, 195, 208 and 233. The assertion names no particular plugin, so the choice
is a call-site value the assertion does not state and should come from a
generator." The lines predate the discovery-login security fix; recorded here
under the convergence-stall rule by the Director's ruling.

## The unlocated-registry scenario never checks that the source is named

The spec's scenario states that planning stops "with that entry's source named".
`test_a_registry_entry_naming_no_install_location_stops_planning` in
`tests/test_repository_installation.scenario.l1.py` asserts only that the error
carries `UNLOCATED_REGISTRY_DIAGNOSTIC`, so a diagnostic that dropped the source
would leave it passing.

**Settlement condition**: the test asserts that the planning error names the
registered entry's source, and removing the source from the diagnostic fails it.

**Evidence**: test-evidence audit finding `f-011` (REJECT) against
`114c56d96942138058a10caae796bd59d83e20ec`:
"test_a_registry_entry_naming_no_install_location_stops_planning asserts only
that the error contains UNLOCATED_REGISTRY_DIAGNOSTIC (\"the marketplace registry
entry names no clone\"). It never checks that the entry's source is named.
Removing `from {claude_registered.source}` from the diagnostic in
outcomeeng/distribution/installation.py:1295-1296 leaves the test passing." The
test predates the discovery-login security fix; recorded here under the
convergence-stall rule by the Director's ruling.

## The fresh-home scenario never checks which source the plan registers

The spec's scenario states that the plan "registers that source for that agent".
`test_fresh_home_plan_adds_the_declared_marketplace` in
`tests/test_repository_installation.scenario.l1.py` asserts only that the Claude
source operations equal a single marketplace add, so a plan that adds any other
source still passes.

**Settlement condition**: the test asserts that the add carries the source the
checkout declares, and a plan adding another source fails it.

**Evidence**: test-evidence audit finding `f-012` (REJECT) against
`0be471a0f4ee4a5316e1a42eec3801aba02bef18`:
"test_fresh_home_plan_adds_the_declared_marketplace asserts only that the Claude
source operations equal [MARKETPLACE_ADD]. It never checks that the add registers
the source the checkout declares (DECLARED_CLAUDE_SOURCE). A plan that adds any
other source still passes, so the \"registers that source\" clause is unverified
by this scenario's evidence." The test predates the discovery-login security
fix; recorded here under the convergence-stall rule by the Director's ruling.

## Codex 0.155.1 poisons a fresh home during the marketplace listing, then refuses it

`codex plugin marketplace list --json` against a `CODEX_HOME` that is a freshly
created empty directory succeeds and writes `tmp/arg0` into that home, writing no
`config.toml`. The next command against the same home is then refused, because the
home now exists, holds no `config.toml`, and holds more than provisioned agent
definitions — the state the listing itself produced.

The defect is the CLI's and the exposure is every caller that runs those two
commands in that order against a fresh home. This repository's persistent preflight
is one such caller, not the subject: it builds four inspections in a fixed tuple —
Claude marketplace inspect, Claude plugin inspect, Codex marketplace inspect, Codex
plugin inspect — and the third poisons the home the fourth is refused for.

**Reproduction**, two commands and a control, needing nothing from this repository.
With `codex-cli 0.155.1`:

```bash
home="$(mktemp -d)"
CODEX_HOME="$home" codex plugin marketplace list --json   # exit 0; writes tmp/arg0
CODEX_HOME="$home" codex plugin list --marketplace outcomeeng --json
```

The second command prints:

```text
codex: CODEX_HOME is not a Codex home: it exists, holds no config.toml, and holds more than provisioned agent definitions; got <home>. Set CODEX_HOME to an existing Codex home, an empty or freshly provisioned directory, or a path Codex may create, then retry.
```

The control — the same `plugin list` as the first command against a pristine
`mktemp -d` home — exits zero with empty `installed` and `available` sets, so the
poisoning is what the marketplace listing leaves behind rather than a property of
the second command.

**What this blocks here**: `test_real_agent_clis_bootstrap_empty_persistent_state`
in `tests/test_repository_installation.scenario.l3.py` fails at the fourth
inspection with that exact rejection, three operations completed.

**Settlement condition**: a Codex release whose marketplace listing does not leave a
fresh home in a state its own next command refuses. There is no repair in this tree:
the ordering is preflight's contract, the four inspections are reads that must
precede planning, and the home is the operator's selected `CODEX_HOME`.

**Evidence**: established against pull request 601. The failing run's own record
carries the argv `codex plugin list --marketplace outcomeeng --json` and
`completed_operations: 3`. The inspection tuple is identical in order, agent, and
operation at the base `dca260ec8ef9a19803096b028be21dd700c05fa5`, so neither the
prefix nor its membership moved; position four's argv is byte-identical to the
retired constant's. The load waiter released `ready` before the run with normalized
averages 0.17, 0.47 and 0.91 of capacity, so the failure is not starvation. This
lane's earlier recorded Codex defect was observed at `0.147.0`, eight minor versions
below the version that produces this one.

**Cause, established with `codex-cli 0.159.2`**: the refusal is not a property of
the marketplace listing. Codex 0.159.2 refuses any existing `CODEX_HOME` that holds
no `config.toml`, and the same two commands succeed in order against a fresh home
that carries an empty `config.toml`. The settlement is therefore a home the
harness provisions with a `config.toml`, not a Codex release; that repair is
outcomeeng/changes#180.

## Subscription discovery reports the Codex credential writer cannot preserve the saved-login link

`test_fresh_codex_session_discovers_every_placed_canonical_subagent` fails before any
agent process runs: `_check_write_through` in
`outcomeeng_testing/harnesses/discovery_auth.py` raises
`DiscoveryAuthenticationError` — the CLI credential writer cannot preserve the
saved-login link, so subscription discovery is unsupported by this CLI. The
compatibility preflight is doing its declared job: it fabricates credentials in
temporary homes and checks write-through before the real saved login is ever
exposed, and it refused.

**Settlement condition**: a Codex release whose credential writer preserves a linked
`auth.json` through a refresh, or a decision here to select a different
authentication mode for this evidence. The preflight is not to be relaxed — it is
what keeps the operator's real saved login out of a CLI that would replace rather
than update it.

**Evidence**: established against pull request 601 with `codex-cli 0.155.1`. The
raising module has zero changed lines in that changeset, so the failure lies wholly
outside the diff. The Codex quota on the account this lane authenticates against is
exhausted until 2026-09-28, which is separate from this failure — this one fails on
the write-through check before authentication — but it is why the lane has been
unreliable all week and why a green run here needs both conditions cleared.

The same refusal was reached independently from a separate changeset and lane, against the same `codex-cli 0.155.1`, with the raising module again carrying zero changed lines there. Two sessions converging on the same environmental verdict from different subjects is why this is recorded as an environment condition rather than a defect of either changeset.

**Cause, established with `codex-cli 0.159.2`**: the credential writer preserves
the link. Against a disposable home carrying an empty `config.toml`,
`codex -c 'cli_auth_credentials_store="file"' login --with-api-key` exits zero,
leaves `auth.json` a symbolic link to the same inode, and writes through it. The
preflight reports a link failure because it reads every nonzero login exit as
one, and the login exits nonzero only because the home it provisions holds no
`config.toml`, which Codex refuses. The repair is the provisioned `config.toml`
and a diagnostic that names the observed refusal; both belong to
outcomeeng/changes#180.

## Release acceptance for the Executor profile and the gpt-6 Codex configurations is unretained

`spx/15-subagent-execution.pdr.md` requires release acceptance for every profile of each harness, and the release-acceptance assertion in `repository-installation.md` requires configuration, native loading, and one minimal isolated execution result for each. `outcomeeng.distribution.profiles.AGENT_PROFILES` carries the Executor profile, and every Codex profile names a gpt-6 model: Standard and Executor `gpt-6.1-sol`, Strong `gpt-6-astra`, Fast `gpt-6-luna`. `native_profile_rows` therefore derives `claude-executor`, `codex-standard`, `codex-strong`, `codex-executor`, and `codex-fast` rows whose configurations no retained run covers.

**Impact**: no artifact shows the Claude Code `sonnet` configuration at high effort, or any gpt-6 Codex configuration, loading and executing as a native subagent. A combined acceptance claim for either harness is therefore incomplete.

**Settlement condition**: `just verify-native-profile-execution` retains passing `claude-executor`, `codex-standard`, `codex-strong`, `codex-executor`, and `codex-fast` rows.

## The discovery-recipe case transcribes a path its own location supplies

`tests/test_repository_installation.scenario.l1.py` builds the expected argv for the
verification recipe with this node's tests-directory path written as a string literal,
while the executing file's own location supplies that path. The oracle stays independent
of the justfile, so the evidence holds and the recipe's own value is still read from the
justfile rather than from the test; what the literal duplicates is a value the test can
derive from itself.

**Resolution shape**: derive the directory from the test file's own location, as the
projection cases in the sibling compliance file do.

**Why separate**: the file lies outside this changeset's diff, and the transcription is a
value the test could derive rather than a name another module owns, so it is not an
instance of the ownership sweep recorded above.

**Evidence**: the node's test-evidence audit finding `f-008`, WARNING, against the
source-ownership rule, whose message records that the evidence holds.

## The real-process entry-point map is hand-maintained with no guard

`REAL_PROCESS_PROJECTIONS` in `outcomeeng_testing/harnesses/installation.py` binds six
entry-point names to the projections of the agents each starts, and
`rows_without_their_projection` reports a row only when it names an entry point present
in that mapping. The reading now covers every executed test file in the tree at the cells
an acquired executable reaches, so a real-process row outside this node is no longer
invisible. The map itself is still hand-written: a new entry point that starts a real
agent process and never reaches the map makes every row calling it conform.

No case asserts that the map holds every such entry point.
`test_every_declared_projection_resolves_in_its_home` asserts only that each projection
name resolves in its home module.

**Resolution shape**: give the entry points a source-owned declaration of the agent each
starts — the map derived from that declaration rather than maintained beside it — so an
undeclared entry point is reported instead of silently conforming. Deriving the set by
inspecting which functions name an agent executable was rejected: helpers that name an
executable without starting a row's process would be reported, and the guard would fail
on legitimate code.

**Settlement condition**: `REAL_PROCESS_PROJECTIONS` is derived from a declaration each
entry point carries, and a case drives an entry point that declares an agent and is
absent from the map.

**Evidence**: the implementation audit's debt finding
`rule-subject-narrower-than-its-assertion` under run token
`2026-09-22_15-12-00-805-5176b12acfb1`, whose file-set half this changeset closed.

## Two implementation-audit runs name opposite homes for the recipe name and the justfile reader

Two runs of `spec-tree:implementation-auditor`, one round apart on this branch, name opposite
homes for the same five symbols: `NATIVE_PROFILE_RECIPE`, `RECIPE_DECLARATION_TERMINATOR`,
`RecipeAbsent`, `_declares_recipe`, and `recipe_block`.

The earlier run, `2026-09-22_23-21-00-406-86e7068248ea` through `python:audit-python-tests`,
raised them as a `source-ownership` debt finding at
`outcomeeng_testing/harnesses/installation.py:4611 (NATIVE_PROFILE_RECIPE), :4614-4653
(RECIPE_DECLARATION_TERMINATOR, _declares_recipe, recipe_block, repository_justfile_text,
native_profile_execution_recipe)`. It expects the recipe name and the justfile recipe-block
reader to live in the production module that consumes the justfile, beside `JUSTFILE_NAME` and
`INSTRUCTIONS_CHECK_RECIPE` in `outcomeeng/distribution/instruction_block.py`, with the harness
and the linked test importing them. The symbols moved there.

The later run, `2026-09-23_01-56-58-981-0c36eae59330` through `python:audit-python-code`, raised
that home as a `single-responsibility-per-module` debt finding at
`outcomeeng/distribution/instruction_block.py:72-130 (NATIVE_PROFILE_RECIPE, RecipeAbsent,
_declares_recipe, recipe_block)`. It expects the release-acceptance recipe name to be owned by
the module whose subject is native-profile release acceptance, and a reusable justfile
recipe-body reader to be owned by a module whose subject is reading the repository justfile. It
reads the module's own docstring, "root-instruction-block writer and drift reporter", as the
subject the insertion departs from, and records that no instruction-block code path reads either
symbol.

**The two readings do not compose.** The product carries no module whose subject is reading the
repository justfile, so the later run's home for the reader names a module that does not exist.
The only module whose subject is native-profile release acceptance is
`outcomeeng_testing/harnesses/native_profile_execution.py`, and the recipe name's home before
the move was `outcomeeng_testing/harnesses/installation.py`; both are test infrastructure, the
home the earlier run rejected.
`spx/31-outcomeeng.enabler/31-verification.enabler/31-test-verification.enabler/15-test-infrastructure.pdr.md`
requires a value the evidence depends on to come from the source complying with the declaration,
and `spx/12-shipped-scripting.adr.md` makes that declaration-to-source agreement audit evidence
rather than a value a harness may hold. Each reading is coherent against the rule it cites.
Together they leave no home the product has.

**What the symbols serve.** The node's compliance assertion `NEVER: the native profile-execution
recipe reads a disable switch` links `tests/test_native_profile_execution.compliance.l1.py`,
whose subject is a justfile recipe. `outcomeeng_testing/harnesses/installation.py` imports
`NATIVE_PROFILE_RECIPE` and `recipe_block` at lines 33 and 34 and composes them in
`native_profile_execution_recipe` at line 4620, which supplies that test its recipe text. The
containing module is governed by `spx/21-spec-tree.enabler/43-instruction-block.enabler` as well,
whose five compliance tests reach it, and a reader of that node meets neither finding.

Nothing moved. Both findings carry `debt` severity, so neither blocks a merge under
`spx/15-merging.pdr.md`, and the symbols stand where the earlier reading placed them.

**Settlement condition**: a decision names the home. Either
`outcomeeng/distribution/instruction_block.py` owns the recipe name and the justfile reader and
the single-responsibility reading is dropped for them, or a production module whose subject is
reading the repository justfile is authored and both move there with their consumers' imports.

**Evidence**: the two sealed audit runs named above, both under branch slug
`work-change-126-agent-disable-switch-4c0c25b3`, each carrying its finding's rule, `debt`
severity, and location; the module docstring at `outcomeeng/distribution/instruction_block.py:1`;
and the consumer sites at `outcomeeng_testing/harnesses/installation.py:33-34` and `:4620`.
