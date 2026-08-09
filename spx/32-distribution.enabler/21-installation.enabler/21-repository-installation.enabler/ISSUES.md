# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

## The marketplace-refresh clone bound leaves no margin over the source's real clone cost

`test_real_agent_clis_install_every_catalog_plugin_idempotently` fails at the `marketplace-refresh` operation. `codex plugin marketplace upgrade outcomeeng --json` exits 1 with:

```text
Failed to upgrade marketplace `outcomeeng`: git clone marketplace source timed out after 30s
fatal: early EOF
```

`test_verification_recipe_aliases_the_exact_l2_evidence` fails only as a consequence, because it asserts `just verify-marketplace-installation` runs exactly that L2 test.

The same bound breaks the declared RELEASE action. `just install-marketplace`, which `spx/local/merging.md` declares under `RELEASE_READINESS`, fails at the identical operation and recipe line, so a merge lifecycle cannot complete its release phase on a host where the clone exceeds the bound. The run's 23-operation prefix — the Claude marketplace replace, ten install and enable pairs, and the list — completes first, so Claude Code project scope is refreshed while the Codex marketplace is not. That is a partial release reporting failure, never a cosmetic non-zero exit.

The failure is a timing margin, not a content defect. A quiet-machine `git clone` of `https://github.com/outcomeeng/plugins.git` completes in 18 seconds over 44 MB and 4358 commits, against a 30-second bound — a margin of roughly 1.7×. The refresh runs after 23 completed install operations, so it competes with the network and disk work those leave behind. The observation reports all ten Claude plugins installed before the refresh step, so catalog content and plugin payloads are not implicated.

`fatal: early EOF` is not evidence about the remote. The bound is the constant `MARKETPLACE_UPGRADE_GIT_TIMEOUT`, fixed at 30 seconds inside the agent CLI at version 0.147.0 with no flag or configuration key, and a generic `-c` override cannot reach a constant. On expiry the CLI observes the clone still running, kills it, and only then appends the stderr it collected, so the `early EOF` is that kill's own residue and carries no evidence of a remote-side exit. Reading it as the remote hanging up mistakes the symptom for the cause.

Each killed clone leaves its staging directory behind under the Codex account state; six stale ones have accumulated in `.tmp/marketplaces/.staging/`.

A correct end state never proves the action succeeded. Codex refreshes its marketplace at startup, so the caches can reach the merged commit shortly after a failed release run, through a path the release action neither took nor controls. Establish release completion from the action's own result rather than from an inventory that later looks current.

The margin narrows as the source grows. The suite passed repeatedly earlier the same day and began failing after the default branch advanced, with no change to installation machinery in between.

**Resolution shape**: establish whether the clone the refresh performs can be shallow or filtered rather than full, since the marketplace source is consumed for its committed catalogs and plugin trees rather than its history. Failing that, raise the bound in the agent CLI through `/issue` against that dependency. Until either lands, treat a `marketplace-refresh` timeout in this test as this known defect rather than a regression in the changeset under test, and treat the release phase as incomplete whenever `just install-marketplace` exits non-zero at this operation.

**Evidence**: reproduced twice on a host at 0.33 normalized load with `git ls-remote` against the same source returning in 0.58 seconds, so neither host starvation nor loss of connectivity explains it. Reproduced twice again in the release path after PR #515 merged, from a checkout at `33467bab05164e2974f179041f23eb6ff63669dd`, with identical structured records; clone duration was not measured in those two runs.

## The unpublished-plugin fragment is matched but its real wording is only half observed

`_is_pending_publication` in `outcomeeng/distribution/installation.py` classifies a failed plugin install or enable as pending publication when `UNPUBLISHED_PLUGIN_FRAGMENT` — the literal `not found in marketplace` — appears in the lower-cased stderr. The only evidence is `UnpublishedPluginRunner`, whose canned stderr was authored alongside the constant it matches, so the test cannot fail on a wording mismatch.

Both real **install** messages were observed while adding the `contribute` plugin, against a canonical marketplace that did not yet publish it:

- Claude Code: `Failed to install plugin "contribute@outcomeeng": Plugin "contribute" not found in marketplace "outcomeeng".`
- Codex: `Error: plugin`contribute`was not found in marketplace`outcomeeng``

Both contain the fragment, so the install path is real. Neither **enable** message was ever observed: the Claude plan issues install then enable per plugin, and the first observation run stopped at the Codex install before any enable ran. The fragment also carries no per-agent prefix, unlike `CLAUDE_ALREADY_INSTALLED_FRAGMENT`, so one unverified wording spans two CLIs.

If either enable message words the absence differently, the carve-out silently never engages for that operation and the run fails where it should report pending.

**Resolution shape**: build a disposable marketplace fixture that omits a plugin the built tree ships, register it as the source in the isolated homes the installation harness already provisions, and run the real `claude` and `codex` CLIs against it to record the install and enable wording for both. That is a new real-CLI evidence lane with its own fixture, not a change to an existing test, which is why it is not folded into the changeset that surfaced it.

**Evidence**: raised by changeset review `2026-08-09_10-14-46-352-325b0ceb84d5` against the changeset that introduced the carve-out.
