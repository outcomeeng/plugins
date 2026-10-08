# Issues: Apply

`/apply` cannot execute a **language-neutral artifact slice** because its language gate requires one implementation language and a complete architecture, test, and code skill trio.

## Add a language-neutral artifact route

**Evidence.** `src/plugins/spec-tree/skills/apply/SKILL.md` lines 50-60 require exactly one supported implementation language before Steps 3-8 and stop when no language-specific skill trio applies. [`spx/21-spec-tree.enabler/65-apply.enabler/apply.md`](apply.md) defines a general apply lifecycle whose selected slice can include language-neutral methodology artifacts.

**Impact.** A skill-only or documentation-only slice selected through `/slice` cannot continue through `/apply` without inventing irrelevant architecture, test, and code work or stopping before the artifact-specific authoring workflow.

**Deferral reason.** The fix is a separate larger concern because it changes `/apply`'s routing contract for every language-neutral artifact class, requires declaration and workflow changes under the apply node, and needs its own cross-artifact audit and review evidence. The selected creator-skill slice consumes that future route but does not own the general apply lifecycle.

**Required handling.** Define a language-neutral artifact route that preserves methodology loading, node contextualization, artifact-specific authoring, touched-scope deterministic verification, applicable artifact audits, whole-changeset review, the terminal full gate when required, and `/merge`. The route skips language architecture, language test, and language implementation steps when the selected slice contains no implementation-language surface.

**Revisit condition.** Resolve this entry before the next language-neutral artifact slice enters `/apply`, or in the next change to `/apply` language detection or Steps 3-8, whichever occurs first.

## `apply` grants `Read, Edit` while its steps create files and search the node

**Evidence.** `src/plugins/spec-tree/skills/apply/SKILL.md:7` declares `allowed-tools: Read, Edit`. Steps 3, 5, and 7 create new ADR, test, and implementation files, and `<scope_detection>` and `<stabilized_diff_rule>` read the touched node's files. `instructions:skill-auditor` finding rule `allowed_tools_missing_write_and_search`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** File creation and same-class sweeps run behind per-call approval prompts inside a flow that line 29 says must not stop between nodes.

**Settlement condition.** The grant carries the file-creation and read-only search capabilities the flow itself performs, per `/skill-standards` `<tool_restriction_security>`'s "narrowest the task needs" rule. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` states three conditions more than once

**Evidence.** The Step 0 condition appears at `<invocation_modes>` line 22, footnote § line 144, and Step 0 line 156; the Step 9 skip condition at `<scope_detection>` line 57, footnote † line 145, Step 9 line 280, and `<review_gates>` line 327; the Step-9-as-done tendency at Step 10 line 304 and Failure 1 line 350, all in `src/plugins/spec-tree/skills/apply/SKILL.md`. `instructions:skill-auditor` finding rule `redundant_restatement`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** About forty lines of eager payload carry no added rule, and one condition has several edit points.

**Settlement condition.** Each condition is stated once at its point of action and cross-referenced by tag name elsewhere, per `/skill-standards` `<conciseness>`. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` Step 5 names a skill the spec-tree plugin does not ship

**Evidence.** `src/plugins/spec-tree/skills/apply/SKILL.md:206` says `/verify` routes eval work through a dedicated eval skill "when that capability is installed"; no such skill ships in the spec-tree plugin and `<skill_map>` carries no row for it. `instructions:skill-auditor` finding rule `unguarded_capability_name`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** The name resolves nowhere in a consumer checkout, and `/audit-skill`'s broken-reference check flags it once the conditional is read literally.

**Settlement condition.** Step 5 names only `/verify`'s own eval routing, or the unshipped skill name is gone. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## `apply` Step 8 opens with a hard-wrapped paragraph

**Evidence.** `src/plugins/spec-tree/skills/apply/SKILL.md:254-258` is wrapped mid-sentence at about eighty columns while every other paragraph in the file is one line. `instructions:skill-auditor` finding rule `hard_wrapped_prose`, severity `WARNING`, on head `524b9c46c7960a106d84ef856b4020a0ce904b16` during Change #76.

**Impact.** Inconsistent dprint output and spurious diff noise on the next edit.

**Settlement condition.** The paragraph is one line, matching the file's convention. [Change #95](https://github.com/outcomeeng/changes/issues/95) carries the `/apply` pass that owns it.

## The preserved aggregate branch holds claims no merge cycle has drained

`origin/work/strict-finding-disposition` preserves an aggregate of 103 commits that changed 189 paths when it was recorded at `5f26a67a9aef9327e57fd5e02d130c8363578a07` against `origin/main` at `b8503c8147f9291a67d828e649baff0d9c078d9c`; it now points at `b913114806c4cabbb2009d94572050621700d483`. It is recovery material and never enters whole-changeset verification or publication as one pull request. Its behavioral claims belong to the nodes that own them: test-verification, the eval harness, reviewing-changes, audit, the TypeScript code standards and merge, and no merge cycle has drained them.

**Settlement condition.** Every preserved behavioral claim is merged, explicitly superseded by current product truth, or retained in its owning node's `ISSUES.md` with a concrete revisit condition.

**Evidence.** `git ls-remote origin refs/heads/work/strict-finding-disposition` prints the branch head. The changeset-coherence auditor branch the earlier plan excluded is no longer on origin.

## A merging decision governs the apply flow's Verifier dispatches

`apply.md` declares all four rules of [`spx/15-merging.pdr.md`](spx/15-merging.pdr.md) product property 3 for the apply flow: each per-node and whole-changeset Verifier dispatch is preceded by the readiness record, a repeated rejected defect class stops the queue for a widened repair, the flow carries only the bounded projection of each Verifier result, and every independent Author-side action finishes before a blocking check or Verifier wait. `/apply` reaches the record through `<verification_checkpoint>` and the projection through `<result_carryover>`. The decision is titled for merging and opens on the delivery lifecycle, while these four rules concern agentic dispatch, whose natural owner is [`spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md`](spx/31-outcomeeng.enabler/31-verification.enabler/14-verification.pdr.md).

**Settlement condition.** The rules relocate into the verification decision and the realizing assertions in `apply.md` re-point to them. The full entry is in `spx/31-outcomeeng.enabler/31-verification.enabler/ISSUES.md`.
