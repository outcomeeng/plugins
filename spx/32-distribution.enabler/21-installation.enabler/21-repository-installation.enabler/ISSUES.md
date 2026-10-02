# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

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

**Evidence**: test-evidence audit finding `f-010` (WARNING) against `841e864a9759eae04c8988c2931aa44b1ca21c74`, `f-007` (WARNING) against `f011edcdd33c0fdec41d8ccfbcdfe1393fc6b35a`, `f-008` (WARNING) with the implementation audit's matching debt finding against `a47f88e39d2a5fe9318eb24e6140623ca774dcfa`, which names the same absent oracle from the recorded-command seam, `f-009` (WARNING) against `c3b42a5514452b1b71e01c77467e7e45abfad048`, and `f-008` (WARNING) against each of `9ab0fc92c2f5c673edbfb2c73eea42502cef68e5` and `c2f6d8e1c3bc87f24d775fcbc62451b9c2ff6322`. The round against `05a7165277750d69c88bc8abbece2c4f6a96bb7c` raised it as `f-013` (WARNING): "The read-count and retry clauses are falsified through the recorded commands. A lock is not a command, so adding an advisory lock around the listing read leaves both counts at one and the test passing. The no-lock clause has no deterministic oracle." The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-013` (WARNING). The round against `43e80d923e177a48707f433e9cf12b86ee6c4b9b` raised it again as `f-015` (WARNING). The round against `d357782498093adc369be5c335e65748b20c79d1` raised it again as `f-005` (WARNING). The round against `2a3987d45705b13bcb7351fec768ff8aa6fa280c` raised it again as `f-002` (WARNING).

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

`_is_pending_publication` in `outcomeeng/distribution/installation.py` classifies a failed plugin install, enable, or update as pending publication when `UNPUBLISHED_PLUGIN_FRAGMENT` — the literal `not found in marketplace` — appears in the lower-cased stderr. The inert fixtures `outcomeeng_testing/fixtures/installation/claude-code-plugin-install-unpublished.stderr.txt` and `outcomeeng_testing/fixtures/installation/codex-cli-plugin-add-unpublished.stderr.txt`, read by path in `outcomeeng_testing/harnesses/installation.py`, carry the independently captured real **install** wording for both CLIs, observed while adding the `contribute` plugin against a canonical marketplace that did not yet publish it:

```text
Claude Code: Failed to install plugin "contribute@outcomeeng": Plugin "contribute" not found in marketplace "outcomeeng".
Codex:       Error: plugin `contribute` was not found in marketplace `outcomeeng`
```

A constant that drifts from that captured wording now fails the linked tests. The Claude Code **enable** message was never observed: only the Claude plan issues an enable, and only when it bootstraps `spec-tree` into a checkout that records no plugin; the first observation run stopped at the Codex install before that enable ran. The Claude Code **update** that refreshes every recorded install record was never observed against an unpublished plugin either. The fragment also carries no per-agent prefix, unlike `CLAUDE_ALREADY_INSTALLED_FRAGMENT`, so the Claude Code enable and update wordings remain unverified.

If the enable message or the update message words the absence differently, the carve-out silently never engages for that operation and the run fails where it should report pending.

**Resolution shape**: build a disposable marketplace fixture that omits a plugin the built tree ships, register it as the source in the isolated homes the installation harness already provisions, and run the real `claude` and `codex` CLIs against it to record the install wording for both CLIs and the enable and update wording for Claude Code. That is a new real-CLI evidence lane with its own fixture, not a change to an existing test, which is why it is not folded into the changeset that surfaced it.

**Evidence**: raised by changeset review `2026-08-09_10-14-46-352-325b0ceb84d5` against the changeset that introduced the carve-out.

The two install captures also name no CLI version: their filenames carry none, and the harness docstring declaring them states that the versions of the capturing run were not recorded, so the evidence cannot tell a current capture from a stale oracle. The recapture lane above records each capture under a filename naming its tool and version, as `claude-code-2.1.285-plugin-update-unrecorded.stderr.txt` and `codex-cli-0.160.0-home-without-config.stderr.txt` do, and retires the unversioned pair. Raised as implementation-audit debt findings 82 and 83 in run `2026-10-02_12-15-14-254-77c7191ef444` over `d3b2825406e6c1e42680dd28d75eaf6809be3ead...2a3987d45705b13bcb7351fec768ff8aa6fa280c`; a recapture attempt in that repair round was refused by the session's permission boundary before either CLI ran.

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
plus the ADR say failed runs retain changed state without restoring a snapshot." The round against `cc5f3e86be4dbcc2c727c46f5c96593bab02b680` raised it again as `f-018` (INFO). The round against `43e80d923e177a48707f433e9cf12b86ee6c4b9b` raised it again as `f-019` (INFO). The round against `d357782498093adc369be5c335e65748b20c79d1` raised it again as `f-006` (INFO). The round against `2a3987d45705b13bcb7351fec768ff8aa6fa280c` raised it again as `f-004` (INFO).

## The real-agent Codex home domain is a hand-maintained mapping

The compliance assertion that every disposable Codex home the harness provisions
holds a plugin-free `config.toml` names three domains: the isolated
installation's home, the write-through preflight's temporary homes, and every
other home a real-agent observation points `CODEX_HOME` at. The third domain is
evidenced through `REAL_AGENT_CODEX_HOME_PROVISIONERS` in
`outcomeeng_testing/harnesses/installation.py`, a one-entry mapping the harness
maintains by hand. A real-agent observation that provisions its home another
way falls outside the evidence without failing any test.

**Impact**: the "every other home" clause covers the observations someone
remembered to list, not the observations that exist.

**Resolution shape**: route every real-agent observation's disposable Codex
home through one harness provisioner that records each home it creates, and
derive the evidence domain from those records rather than from a list.

**Progress**: the subagent-discovery observation and the isolated-installation
observation now read the Codex home from the plan they execute, which
production provisions, instead of rebuilding it as `state / "codex"`; the
native-profile row reads it from its plan as well. The `l2` native-profile
evidence now drives the producer's own row, whose home the isolated plan
provisions, so the harness-owned empty native-read state and its mapping entry
are gone. The listed mapping remains the domain for the one harness-owned
state left, the selected real-agent state.

**Settlement condition**: the evidence's real-agent home domain is derived from
the provisioning records, and a new observation that provisions a home reaches
the evidence without an edit to a list.

**Evidence**: test-evidence audit finding `f-018` (WARNING) against `43e80d923e177a48707f433e9cf12b86ee6c4b9b`:
"The 'every other home a real-agent observation points CODEX_HOME at' domain is
the hand-maintained two-entry REAL_AGENT_CODEX_HOME_PROVISIONERS mapping. It is
not derived from the observations." The round against `d357782498093adc369be5c335e65748b20c79d1` raised it again as `f-004`
(WARNING). The round against `2a3987d45705b13bcb7351fec768ff8aa6fa280c` raised it again as `f-003` (WARNING).

## The shipped placement script restates the agent naming relation

`src/templates/plugin/scripts/place_agents.py` classifies a checkout definition
as plugin-owned by the literal flat prefix `<plugin>_` and by the literal `:`
before a skill entry's name. The build owns both through
`FLAT_AGENT_PLUGIN_SEPARATOR` and `NATIVE_AGENT_PLUGIN_SEPARATOR` in
`outcomeeng/distribution/contracts.py`, which the installer's own scope-split
classification and the installation harness consume. The shipped script is a
standalone, standard-library-only file in a consumer's plugin tree, so it cannot
import that owner, and a separator change would reach the installer and leave
the script classifying against the old one.

**Resolution shape**: render both separators into the script from the build's
owner through the template renderer, the way `PLUGIN` is rendered, so every
plugin's shipped copy carries the owner's values; the change rewrites every
plugin's rendered skill surface and passes the skill-auditor gate.

**Why separate**: it changes every plugin's shipped script and the template
render contract, which the evidence repair that surfaced it does not touch.

**Settlement condition**: the rendered script carries no separator literal of
its own.

**Evidence**: same-class sweep after test-evidence audit finding `f-003`
(REJECT) against `d357782498093adc369be5c335e65748b20c79d1`, which found the installation harness
restating the same relation.

## The native-profile override set has no oracle independent of the filter that strips it

The compliance assertion that a native-profile row removes ambient model and
effort overrides is evidenced by
`tests/test_native_profile_execution.compliance.l1.py`, whose two isolation
tests take the expected stripped set from
`NATIVE_PROFILE_AMBIENT_ENVIRONMENT_VARIABLES` in
`outcomeeng_testing/harnesses/native_profile_execution.py`. The isolation
filter `_isolated_environment` strips exactly that set, and `ambient_environment`
in `outcomeeng_testing/harnesses/native_profile_launch.py` plants exactly that
set, so removing a name from `NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES`
leaves both tests passing while a row inherits that override.

No source independent of the filter declares which variables are model and
effort overrides. The spec states the class, not its members, and
`spx/12-shipped-scripting.adr.md` routes the agreement between a declared value
and the source complying with it to audit, so declaring the members in the spec
alone moves the agreement to audit rather than giving the test an oracle. The
installed Claude Code CLI's own vocabulary is the candidate separately owned
registry, but no stable surface exposes it: `claude --help` names no
environment variable, and the names carried in the 2.1.287 binary are
recoverable only by string extraction, which also yields fragments that are no
variable.

The same extraction indicates the set is incomplete, not only unwitnessed. The
2.1.287 binary carries model-selection variables the filter does not strip,
among them `ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL`,
`ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`,
`ANTHROPIC_SMALL_FAST_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, and
`CLAUDE_EFFORT`. An alias remap such as `ANTHROPIC_DEFAULT_OPUS_MODEL` changes
the model a profile's `model: opus` resolves to, so an operator shell carrying
one would let a Standard or Strong row run on a model its profile does not
name.

**Settlement condition**: the governing decision names the source of the
override set — a declared contract whose agreement with the filter is audit
evidence, or a captured, versioned CLI artifact the test reads by path — and
the linked test fails when a member of that set is removed from the filter.

**Evidence**: implementation-audit blocking finding 81, rule
`oracle-independence`, in run `2026-10-02_12-15-14-254-77c7191ef444` over
`d3b2825406e6c1e42680dd28d75eaf6809be3ead...2a3987d45705b13bcb7351fec768ff8aa6fa280c`;
the variable names come from `strings` over the installed Claude Code 2.1.287
binary, filtered for model, effort, and thinking tokens.
