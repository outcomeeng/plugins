# Issues: Apply

`/apply` cannot execute a **language-neutral artifact slice** because its language gate requires one implementation language and a complete architecture, test, and code skill trio.

## Add a language-neutral artifact route

**Evidence.** `src/plugins/product-tree/skills/apply/SKILL.md` lines 34-47 require exactly one supported implementation language before Steps 3-8 and stop when no language-specific skill trio applies. [`spx/21-product-tree.enabler/65-apply.enabler/apply.md`](apply.md) defines a general apply lifecycle whose selected slice can include language-neutral methodology artifacts.

**Impact.** A skill-only or documentation-only slice selected through `/slice` cannot continue through `/apply` without inventing irrelevant architecture, test, and code work or stopping before the artifact-specific authoring workflow.

**Deferral reason.** The fix is a separate larger concern because it changes `/apply`'s routing contract for every language-neutral artifact class, requires declaration and workflow changes under the apply node, and needs its own cross-artifact audit and review evidence. The selected creator-skill slice consumes that future route but does not own the general apply lifecycle.

**Required handling.** Define a language-neutral artifact route that preserves methodology loading, node contextualization, artifact-specific authoring, touched-scope deterministic verification, applicable artifact audits, whole-changeset review, the terminal full gate when required, and `/merge`. The route skips language architecture, language test, and language implementation steps when the selected slice contains no implementation-language surface.

**Revisit condition.** Resolve this entry before the next language-neutral artifact slice enters `/apply`, or in the next change to `/apply` language detection or Steps 3-8, whichever occurs first.

## `apply` grants `Read, Edit` while its steps create files and search the node

**Evidence.** `src/plugins/product-tree/skills/apply/SKILL.md:7` declares `allowed-tools: Read, Edit`. Steps 3, 5, and 7 create new ADR, test, and implementation files, and `<scope_detection>` and `<stabilized_diff_rule>` read the touched node's files. `instructions:skill-auditor` finding rule `allowed_tools_missing_write_and_search`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** File creation and same-class sweeps run behind per-call approval prompts inside a flow that line 28 says must not stop between nodes.

**Settlement condition.** The grant carries the file-creation and read-only search capabilities the flow itself performs, per `/skill-standards` `<tool_restriction_security>`'s "narrowest the task needs" rule. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` states three conditions more than once

**Evidence.** The Step 0 condition appears at `<invocation_modes>` line 22, footnote § line 177, and Step 0 line 189; the Step 9 skip condition at `<scope_detection>` line 56, footnote † line 178, Step 9 line 307, and `<review_gates>` line 354; the Step-9-as-done tendency at Step 10 line 331 and Failure 1 line 383, all in `src/plugins/product-tree/skills/apply/SKILL.md`. `instructions:skill-auditor` finding rule `redundant_restatement`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** About forty lines of eager payload carry no added rule, and one condition has several edit points.

**Settlement condition.** Each condition is stated once at its point of action and cross-referenced by tag name elsewhere, per `/skill-standards` `<conciseness>`. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` Step 5 names a skill the product-tree plugin does not ship

**Evidence.** `src/plugins/product-tree/skills/apply/SKILL.md:239` says `/verify` routes eval work through a dedicated eval skill "when that capability is installed"; no such skill ships in the product-tree plugin and `<skill_map>` carries no row for it. `instructions:skill-auditor` finding rule `unguarded_capability_name`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** The name resolves nowhere in a consumer checkout, and `/audit-skill`'s broken-reference check flags it once the conditional is read literally.

**Settlement condition.** Step 5 names only `/verify`'s own eval routing, or the unshipped skill name is gone. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` Step 8 opens with a hard-wrapped paragraph

**Evidence.** `src/plugins/product-tree/skills/apply/SKILL.md:281-285` is wrapped mid-sentence at about eighty columns while every other paragraph in the file is one line. `instructions:skill-auditor` finding rule `hard_wrapped_prose`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** Inconsistent dprint output and spurious diff noise on the next edit.

**Settlement condition.** The paragraph is one line, matching the file's convention. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## The preserved aggregate branch holds claims no merge cycle has drained

`origin/work/strict-finding-disposition` preserves an aggregate of 103 commits that changed 189 paths when it was recorded at `5f26a67a9aef9327e57fd5e02d130c8363578a07` against `origin/main` at `b8503c8147f9291a67d828e649baff0d9c078d9c`; it now points at `b913114806c4cabbb2009d94572050621700d483`. It is recovery material and never enters whole-changeset verification or publication as one pull request. Its behavioral claims belong to the nodes that own them: test-verification, the eval harness, reviewing-changes, audit, the TypeScript code standards and merge, and no merge cycle has drained them.

**Settlement condition.** Every preserved behavioral claim is merged, explicitly superseded by current product truth, or retained in its owning node's `ISSUES.md` with a concrete revisit condition.

**Evidence.** `git ls-remote origin refs/heads/work/strict-finding-disposition` prints the branch head. The changeset-coherence auditor branch the earlier plan excluded is no longer on origin.

## A merging decision still holds the four dispatch rules that `apply.md` declares

`apply.md` declares the readiness-record, defect-class-stop, bounded-projection and author-work-before-wait rules for the apply flow's per-node and whole-changeset Verifier dispatches and cites no decision for them. `/apply` reaches the record through `<verification_checkpoint>` and the projection through `<result_carryover>`. [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) product property 3 still states the same four rules. The decision is titled for merging and opens on the delivery lifecycle, while these four rules concern agentic dispatch, whose natural owner is [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

**Settlement condition.** The rules relocate into the verification decision and the four assertions in `apply.md` cite them there. The full entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/ISSUES.md`.

## Three artifact auditors still emit the structured JSON verdict

The `sealed-run-verdict` assertion in `apply.md` and the `/apply` gate steps read the verdict of `adr-auditor`, `test-evidence-auditor`, `eval-evidence-auditor` and `implementation-auditor` from the terminal status of a sealed run. `implementation-auditor` relays the run token, the run file and the rendered projection. The shipped `audit-adr`, `audit-tests` and `audit-eval-evidence` skills and their wrappers, among them `src/plugins/product-tree/agents/adr-auditor.md`, still emit a plain JSON verdict with no run token or run file. The assertion therefore describes behavior those three auditors do not yet have. The gate-remediation assertion in `54-node-flow.enabler/node-flow.md`, which treats a sealed run whose terminal status is `rejected` as a rejecting gate verdict, depends on the same conversion.

**Settlement condition.** outcomeeng/changes#513 rewrites the `audit-adr`, `audit-tests` and `audit-eval-evidence` skills and their wrappers onto one `spx verification run` each, under an unchanged semantic verdict model. The sibling entries in `spx/21-product-tree.enabler/32-decisions.enabler/21-adr-auditing.enabler/ISSUES.md`, `spx/21-product-tree.enabler/68-audit.enabler/32-audit-tests.enabler/ISSUES.md` and `spx/21-product-tree.enabler/68-audit.enabler/32-audit-eval-evidence.enabler/ISSUES.md` settle under the same change.

**Evidence**: current-head CI review of pull request 671.

## `decision-line-repair` names only the Operator's review

**Evidence.** The `decision-line-repair` row of [`apply.md`](apply.md) returns the Change to Sliced "for the Operator's review", while `review-carry` and `maturity-actor` of [`spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md`](spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md) give that review to the Operator or to the delegate of the advance to Sliced, and the `/apply` skill line under the row names both.

**Impact.** The row stays true, because the Operator may still review, but it omits the delegate, so the spec reads narrower than the decision that governs it.

**Settlement condition.** The `decision-line-repair` row names the review of the Operator, or of the delegate of the advance to Sliced, as the decision does.

## `sync-before-verification` syncs before every verification step `spx/21-product-tree.enabler/65-apply.enabler/apply.md` `sync-before-verification` `consistency`

**Evidence:** `apply.md` row `sync-before-verification` has the apply lifecycle invoke `/sync-base` before every deterministic verification command and every Verifier dispatch, and treat a Verifier's `stale-base` block as no verdict. That contradicts `no-own-account-sync` of [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md), under which no deterministic verification command and no Verifier dispatch runs `/sync-base` on its own account, and `sync-timing`, under which a session syncs at pickup or for a named reason only. The current-head CI review of pull request 804, at head `745efa7c9232f4b572c8f20c3f2aa4deb0963359`, raised it as a `BLOCKING` `consistency` finding.

**Impact:** A reader of the apply Node finds a per-step sync that its governing decision forbids. Each sync on a behind-base head takes in base changes the work has not judged and reopens evidence the work already holds.

**Separate larger concern:** The row states what the `/apply` skill does, and the skill's per-step sync and its `stale-base` handling stand in its workflow and references. Restating the row alone would leave the skill contradicting its own spec. The fix spans the Node's spec, its skill and their verification, which reach beyond the decision text that changed.

**Settlement condition:** `sync-before-verification` has the apply lifecycle run `/sync-base` only at pickup or for a named reason, and record the result of the latest run in the readiness record.
