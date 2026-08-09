# ISSUES — repository installation

Known defects in the repository-installation evidence. Each entry names the artifact, the observed failure, and the smallest unit of work that resolves it.

## The marketplace-refresh clone bound leaves no margin over the source's real clone cost

`test_real_agent_clis_install_every_catalog_plugin_idempotently` fails at the `marketplace-refresh` operation. `codex plugin marketplace upgrade outcomeeng --json` exits 1 with:

```text
Failed to upgrade marketplace `outcomeeng`: git clone marketplace source timed out after 30s
fatal: early EOF
```

`test_verification_recipe_aliases_the_exact_l2_evidence` fails only as a consequence, because it asserts `just verify-marketplace-installation` runs exactly that L2 test.

The failure is a timing margin, not a content defect. A quiet-machine `git clone` of `https://github.com/outcomeeng/plugins.git` completes in 18 seconds over 44 MB and 4358 commits, against a 30-second bound — a margin of roughly 1.7×. The refresh runs after 23 completed install operations, so it competes with the network and disk work those leave behind, and `fatal: early EOF` is the remote hanging up mid-transfer rather than a size limit being reached. The observation reports all ten Claude plugins installed before the refresh step, so catalog content and plugin payloads are not implicated. The bound is fixed inside the agent CLI, so no repository setting relaxes it.

The margin narrows as the source grows. The suite passed repeatedly earlier the same day and began failing after the default branch advanced, with no change to installation machinery in between.

**Resolution shape**: establish whether the clone the refresh performs can be shallow or filtered rather than full, since the marketplace source is consumed for its committed catalogs and plugin trees rather than its history. Failing that, raise the bound in the agent CLI through `/issue` against that dependency, and until either lands, treat a `marketplace-refresh` timeout in this test as this known defect rather than a regression in the changeset under test.

**Evidence**: reproduced twice on a host at 0.33 normalized load with `git ls-remote` against the same source returning in 0.58 seconds, so neither host starvation nor loss of connectivity explains it.
