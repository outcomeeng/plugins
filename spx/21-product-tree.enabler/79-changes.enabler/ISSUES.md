# Issues: Changes

## The Change skills block a field write when the field offers options the record never uses

**Evidence:** The `store-options` assertion of `spx/21-product-tree.enabler/79-changes.enabler/changes.md` has author-change and manage-change stop with a blocked result when the options of the Maturity, Lifecycle, Value, or Investment field differ from the values `record-keys` names, and change-standards compares the two as a set before every write. No decision states that rule: [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) holds no `store-options` rule. On 2026-11-09 the outcomeeng Lifecycle field offered Claimed and Refined beside the four `record-keys` values, the Value field offered Product and Security, and no issue in the 18 outcomeeng repositories with issues carried any of those four options. manage-change refused to write Lifecycle Applied for outcomeeng/changes#915, although Applied is an option of the field.

**Impact:** An option no record uses blocks every write to its field across the organization until someone with organization rights edits the field, including while a rename keeps an old and a new option side by side.

**Settlement condition:** The Change skills check only that the value they write is an option of its field, and report a stored value outside the values `record-keys` names when they read it.

## The form check and the audit require a repository that the Change itself may create

**Evidence:** `record-keys` and `draft-base` of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) make the base of a Leaf the head of the default branch of its Product, and the form check and the audit read every Declarations line at that commit. On 2026-11-09 the Orchestration Maintainer reported, in mail 26253, that the Draft of outcomeeng/changes#942 failed the form check on `draft-base` alone, because its Product's repository, outcomeeng/marketplace-build, did not exist.

**Impact:** A Change whose first step creates its Product's repository cannot be recorded, checked, or audited before that repository exists, so the repository has to exist before the Change that creates it.

**Settlement condition:** A Leaf whose Product has no repository yet records, passes the form check, and passes the audit with no base, and its Declarations can create the repository.

## The change auditor has no request-file location on a harness that names no scratch directory

**Evidence:** `audit-change` and the `change-auditor` definition have the auditor write every runner request file in the scratch directory the harness names, with `$RUNNER_TEMP` on a hosted runner as the only fallback. On 2026-11-09 an at-close run on outcomeeng/changes#915, run `2026-11-09_15-24-36-636-2336a5438633`, ended `BLOCKED` after the session's scratch directory was withdrawn, and the next run, `2026-11-09_15-40-15-927-e89660553ded`, wrote 18 files to the fixed path `/private/tmp/change-auditor-915/`. The runner's `retain-record` operation retains the record's Change Draft, so the audit writes no payload file and no file whose bytes a formatter hook can invalidate; the request files remain.

**Impact:** On a harness that names no scratch directory and is no hosted runner, the change audit has no location for its request files, so it stops or writes outside every location its rules allow.

**Settlement condition:** [`spx/15-agent-tools.pdr.md`](spx/15-agent-tools.pdr.md) names the location a session without a harness-named scratch directory writes its request files to, and `audit-change` names that location.

## The change auditor reaches opposite verdicts on one record at one Base

**Evidence:** On 2026-11-15 the `change-auditor` of product-tree 0.114.3 audited outcomeeng/changes#867 twice before Applicable, both times at Base `7ce8f51a3d07e43b4d2c5b01c258c3a5d3fd545e`. Run `2026-11-15_23-33-14-190-06d4860de7bc` judged the body revision edited at 2026-11-15T23:29:34Z and sealed approved with no findings. Run `2026-11-15_23-57-50-594-7f779ed4b52a` judged the revision edited at 2026-11-15T23:53:44Z and sealed rejected, with blocking findings on `front-matter-block` and `audit-before-applicable`, both on the `spx/32-distribution.enabler/21-installation.enabler/21-repository-installation.enabler` subsection. The issue's edit history holds those two revisions byte-equal, and the Change Drafts the two runs retained, `.spx/worktree/change-drafts/9f0d94c6-a8f8-4f79-9f2f-ac1e11973410.md` and `.spx/worktree/change-drafts/8a178d3a-8200-4059-b4f5-359ba33b4e25.md` in the auditing worktree, share the SHA-256 `9440588beba1c759fbb5d7b2d1d19563381145c0f0c4162e58802f015fea7338`. Both runs ran under spx 0.10.0. The `audit-record` assertion of `changes.md` has the audit judge each Declarations line against every Decision Record that governs its Node at the Base, so both runs judged one subject against one set of decisions.

**Impact:** The verdict of a before-Applicable audit depends on the run, not on the record and its Base. An approval does not show that the record meets `front-matter-block` and `audit-before-applicable`, and a holder can advance a Leaf to Applicable on whichever run approves.

**Settlement condition:** Two `audit-change` runs on a byte-equal record body at one Base seal the same verdict with the same findings.
