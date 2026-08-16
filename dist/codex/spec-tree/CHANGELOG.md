# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

A version missing below shipped without an entry. Read the gap as an absent entry, never as an absent release.

An entry is written by the changeset that ships the change. A later changeset adds one only for a release its own diff modifies or reverses, and names that release's commit — the entry is then checkable against the diff carrying it. The entry covers that commit whole, because checkability comes from naming a commit a reader can open rather than from matching lines; a commit large enough that this reaches unfamiliar content is a commit whose entry belongs to whoever shipped it. Any other backfill reconstructs what a release's consumers needed from commits and diffs alone, which produces a guess, and a guess in this file is indistinguishable from a record. A gap not reachable that way stays open.

## 0.91.0

### Added

- **Product content is a defined term.** The `/understand` foundation defines product content as every product artifact a spec node governs or must govern — source, tests, evals, generated output, specs, decisions, coordination notes, spec-declared configuration, implementation being its code layer — with the governing node found by search under the live foundation marker: a path under a node directory belongs to that node; any other path to the node whose test file names it and whose spec links that test; several matching nodes resolve to their lowest common ancestor. Product content with no governing spec is not read or modified; the gap is recorded. The agent harness's own instruction and settings files, tool output, the session store, and scratch space are not product content.

### Changed

- **Post-compaction recovery reloads at the first product-content access.** After compaction, `/understand` precedes the next product-content access and `/contextualize` on the governing spec node precedes any product content that node governs being read or modified, and any discussion of that node; a compaction empties the set of contextualized nodes. An operational continuation — PR inspection, check wait, merge, deploy, release, `spx session` operations, occupancy proof — touches no product content and triggers neither reload.
- **`/manage-pr`, `/merge`, and `/manage-github-pr` reload at the first product-content access in the pass and at no earlier step.** PR inspection, check wait, merge, deploy, and release proceed on live PR and repository state alone; each skill carries the matching success criterion and failure mode.
- **`/handoff` reloads only immediately before it reads or edits coordination notes or other governed product content.** Claimed-session and marker recovery from conversation markers and `spx session` output needs no reload.
- **`/pickup` reloads at its first product-content access.** The claim, session presentation, checkout, base sync, and claim reconciliation touch no product content; `/understand` precedes the coordination-note path check under `spx/`, or `/contextualize` when the session names no node.
- **`/understand` reads the root instruction file from disk only when the live conversation does not already carry it complete.** A harness that injects the whole file satisfies the step; a truncated or absent injection requires the read.
- **The managed router's `/contextualize` rule and post-compaction STOP TRIGGER state the per-node product-content rule** (template 0.36.0).

### Requires

- Re-render the root instruction files with `/update-instruction-block` so the router block carries the product-content definition and the new STOP TRIGGER.

## 0.90.0

### Changed

- **`/issue` files into the invoking repository's own queue.** A same-repository observation no longer stops or routes into full `/handoff` closure. `/issue` recognizes the invoking repository by resolved absolute git-common-directory equality — a linked worktree in the same pool is the same repository, a separate clone with the same origin is not — files through a queue-safe checkout (the pool's main checkout from `spx diagnose`, or the single working tree), anchors the record to the origin default branch, and leaves the active worktree, its branch, and every existing session untouched. The explicit invocation authorizes that one write; every other repository still requires operator confirmation before mutation.
- **One fresh record per invocation, with overlaps named rather than judged.** Each authorized invocation creates exactly one `todo` follow-up. Before a same-repository write it reads only the `spx session list --json` headers and reports the full ids whose `goal` or `next_step` names an affected path or skill as possible overlaps; it never reads another session's body, reuses a session, or probes origin for a stored branch. Queue consumers reconcile overlap at pickup.

### Added

- **The plugins marketplace checkout identifies itself as the spec-tree target.** When the invoking repository's root carries `.claude-plugin/marketplace.json` naming the `outcomeeng` marketplace with the `spec-tree` plugin, `/issue` takes that repository as the target before any marketplace lookup, so a missing local marketplace registration no longer turns into an operator question for a checkout path.

## 0.89.2

### Fixed

- **The configured-verifier contract for a craft plugin's `{plugin}-auditor` covers both output shapes.** It previously required a structured verdict with an authoritative `overall`, so a caller judged a correctly-behaving auditor that returns a sealed-run journal token as malformed output and blocked the gate. The contract now names both shapes — a structured verdict, or a raw run token rendered through `spx journal render --type <the skill's declared run type>` with the run's terminal status authoritative — and directs the caller to the owning plugin's audit skill for which one applies.
- **The instruction-block node asserts that contract against its roles.** Every configured verifier and reviewer role the routers name must state the output contract the shipped thin agent definition for that role produces, so a contract naming a shape its role does not produce is drift rather than something the render carries into every consumer.

## 0.89.1

### Added

- **`/open-pr` creates its own scratch directory without a permission prompt.** Its Step 3 already required capturing verbose verification output in a temporary log path, but `mktemp -d` sat outside `allowed-tools`, so the step stopped for per-call approval on every invocation. The grant covers `mktemp -d` and nothing else.

## 0.89.0

### Changed

- **The shared test-evidence standard decides artifact permission per assertion type and execution level.** `test-evidence-standards` is restructured into a levels → artifacts → per-type order. Execution levels (`l1`/`l2`/`l3`) are defined by dependency class with an ordered executable discriminator: an artifact of the product under test is `l1` when the suite exercises the form the checkout carries (the in-cycle build among its forms) and `l2` for every other acquired form — installed, bootstrapped, preinstalled, or otherwise obtained — with every other executable classified by whether the declared environment or in-cycle toolchain supplies it; the level floor stays `l3` where the evidence run itself must reach a remote, shared, credentialed, or network-dependent system. Each assertion type's section now states its artifact permissions, with per-level deltas only where the type changes the answer, and every cell is decided by composing the type's rules with the level's harness obligations — a permission undecidable from that composition is an amendment to the product's governing evidence decision, never an author's or auditor's inference.

### Added

- **The canonical test-filename model is part of the shared standard.** Each executed test file declares exactly one assertion type and one execution level through `<subject>.<evidence>.<level>[.<runner>]`; a product's language test standard declares its filename instantiation and the default runner an omitted runner token names — or the deterministic rule, including any repository override, by which that default is derived.
- **Cross-assertion value ownership has a decision procedure.** Two probes — negation and transplant — decide whether a value is harness-owned or the assertion's own; a cross-assertion value reaches the test only as a handle or observation, and the first executed test that touches a process, filesystem, clock, network, or randomness establishes the harness later tests reuse.
- **Language deltas are expression only.** A language test standard cites its product's governing evidence decision by full path, realizes the categories this standard permits in its language's terms, and neither narrows nor widens any seam, provenance, oracle, level, or permission rule; a category a language cannot realize routes to a decision amendment, never a silent per-language subtraction.

## 0.88.10

### Changed

- **The `/understand` artifact-placement taxonomy is closed.** The foundation now states that `spx/` admits no artifact outside the placement table — whose rows include the root product spec — the canonical node shape, and the optional knowledge root a node or the product root carries; that operational files (`spx/local/` overlays, the exclusion mechanism) are configuration rather than artifacts; and that coordination notes raise no placement question. Placement of unmatched content decides only between the governing layer (an ADR or PDR) and the declaring layer (a spec) — verification and implementation artifacts are never placed by classification, because assertion tags derive evidence locations and node ownership with the language's declared infrastructure home derives implementation locations. A repository carrying free-form documents under `spx/` outside these artifact kinds now has misplaced content: reclassify each such file into the decision or spec that owns its subject.

### Added

- **The canonical node shape names the optional `knowledge/` root.** A node may carry one knowledge root — a knowledge bundle whose `index.md` lists its contents — and the product root may carry `spx/knowledge/` the same way. `/align` skips files inside a `knowledge/` directory instead of reporting them as unrecognized Markdown.
- **The eval lane's file set follows `eval.toml`.** The canonical eval lane is `eval.toml` plus the case, prompt, and template artifacts it declares by eval-relative path — canonically `cases.jsonl`, `prompt.md`, and `prompt.template.md`. A declared case or prompt path may reach a sibling eval's shared artifact; a declared template stays inside the eval directory. A declared producer source is a repository path outside the eval directory. The eval harness generates `history.jsonl` and the ignored `runs/` transcripts at fixed names it owns. `/align` skips the files inside a node's `evals/` lane instead of reporting them as unrecognized Markdown.

## 0.88.9

### Fixed

- **`/audit-tests` stops rejecting a scenario case the spec itself declares.** Step 3a's ownership table rejected hand-picked test data unconditionally, and the per-assertion-type litmus that exonerates a legitimate case ran two steps later — so a scenario test carrying the exact interaction its assertion states was a deterministic reject, and the remediation the audit named was to move that case into a production module. That remediation is source laundering: the case gets a production address without a production contract, and nothing outside the test requires the symbol. The litmus now resolves anything case-shaped before the data rows, and three sources it assigns to the test — a spec-declared scenario case, an external conformance expectation, and the violating input a compliance rule names — are correctly owned where they sit.

  **Migration.** A test that moved a spec-declared case into production to satisfy an earlier audit can move it back into the test body; the audit no longer requires the production symbol, and the symbol itself is now a finding if nothing else requires it.

- **A symbol with no in-repository caller is no longer laundered on that basis alone.** Step 3a judged source ownership from the callers it could see, so a public error code, a package version dunder, or a protocol only third parties implement read as a symbol nothing requires — the same false positive in the opposite direction. Ownership now turns on a contract outside the test tree, and the absent caller opens that question instead of settling it: the audit reads the declared surfaces the checkout carries — packaging entry points and export declarations, protocol implementations, registry and reflective lookups, generated use, and declared schemas — and names those surfaces in any laundering finding it still reports. The evidence stays inside the checkout, so a symbol no declared surface requires is still reported; an unknowable external consumer cannot be searched for and never withholds the finding.

## 0.88.8

### Changed

- **The merge lifecycle's CLOSE phase requires a fresh `/handoff` invocation.** The final closeout is `/handoff`'s output, never transport-authored prose: however operator-useful a hand-written summary reads, the duties behind the message — claimed-session accounting, worktree-release verification, continuation disposition — run only when the skill runs. A `/handoff` completed earlier in the same conversation never satisfies CLOSE for work merged after it, because new merged work reopens the session and the handoff workflow's existing-session search makes the repeat invocation cheap, reconciling the earlier handoff's artifact as a same-owner continuation. `/merge`, `/manage-github-pr`, and the merge policy's close phase and success criteria all carry the rule, with a matching failure mode in both transport skills.

## 0.88.7

### Removed

- **Branch cleanup no longer advances the checkout that holds the base branch.** 0.88.4 added a step that fast-forwarded that checkout after every merge, on every transport. It was the wrong home: the base checkout predates the changeset and outlives it, while cleanup removes only what the lifecycle created, and reaching it meant writing outside the assigned worktree — which the merge lifecycle otherwise never does. Advancing a base checkout mutates local environment state and publishes nothing, which is the boundary `DEPLOY` sits on, so it becomes a deploy action a repository declares in `spx/local/merging.md` under `DEPLOYMENT_READINESS`. The branch-state closeout record drops its base-checkout-refresh field with the step.

  **Migration.** From 0.88.4 through 0.88.6 this ran for every repository on every transport, with nothing to declare. It now runs only where a repository declares it, and `DEPLOY` is a no-op where none is declared — so a base checkout that was being advanced automatically will stay at its pre-merge commit, as it did before 0.88.4. A repository that wants the behavior declares it as a deploy action; one that never relied on it needs no change.

## 0.88.4

Recorded by 0.88.7, which reverses this release's base-checkout refresh. Shipped in commit `dbd7b429cdc3744f7288553d1be8a4e91b76ab40`.

### Changed

- **The default merge strategy is a merge commit.** `gh pr merge` defaults to `--merge` rather than `--rebase`; `--rebase` and `--squash` remain available through the overlay's merge-flag declaration. A merge commit keeps every branch commit reachable, so the merged tip is a true ancestor of the base and `git branch -d` alone proves the branch deletable. The rewriting strategies reach that proof only through the patch-equivalence fallback, which a multi-commit squash fails outright. A repository that declares its own merge flag sees no change.

## 0.88.2

### Fixed

- **A project with no test files yet no longer receives empty per-language sections.** Two spans of the router introduce per-language content while carrying no per-language block of their own: the `## Test Naming Convention` heading with its preamble, and the paragraph introducing the composed per-language audit-skill tables. A project whose spec tree holds no test file — every project before its first test — rendered both above nothing, since the same render dropped every table they announce. Both are now gated on at least one enabled language and omitted whole when none is. A project that already has test files sees no change.

## 0.88.1

### Added

- **A root instruction file that only points at the other one is detected and resolved by answer, not by guess.** A repository whose `AGENTS.md` says little more than "see the other root instruction file" previously read as divergence: the two bodies shared almost nothing, so nothing was wrapped as a `shared` region and each file kept its own harness's router under a pointer to the other file's differently rendered one — sending a reader to the wrong harness's instructions. `/update-instruction-block` now reports such a file as a delegation candidate and holds the surface `stale` until the operator names the side both files take. Candidacy is decided from two facts about the file — the body names the other root instruction file, and its text stays within an absolute character bound — never from a reading of what the prose means, because adoption replaces a whole body and a wrong guess costs that file its instructions.

- **`--adopt {claude|codex}` applies that answer.** It requires `--write`, and it refuses four answers it cannot apply, each exiting nonzero and leaving both root files untouched: naming a side whose own body is a pointer, discarding a body carrying content of its own, arriving after the bootstrap pass has closed, and arriving with no write to apply it.

### Changed

- **The router block gained two sections, so they land in both root instruction files on the next run.** `### Agent identity in generated artifacts` bans naming the agent or its runtime in an operational artifact — a branch name, commit message, pull-request title or body, review comment, or authorship marker — while explicitly exempting instruction content that documents agent behavior as its subject. `### Operator questions` requires an operator question to go through the harness's structured-question tool rather than free-text prose, and reserves it for an answer that changes what happens next.

- **The five ambiguity reports read the same way.** Each now carries the same Detected/Recommend/Apply shape instead of five differing prose forms.

## 0.88.0

### Added

- `MARKETPLACE-CHANGELOG.md`, previously shipped in every plugin

### Removed

- `METHODOLOGY-CHANGELOG.md`
- `Skill` from the lifecycle skill's `allowed-tools`

### Changed

- `help` reports two changelogs instead of three

## 0.87.2

### Changed

- **Merge cleanup recognizes rebase-merged local branches as merged.** The close-phase branch cleanup deletes a local feature branch whose remote ref is absent, which no live worktree checks out, and whose work is fully upstream — its tip an ancestor of the fetched base, or every branch commit patch-equivalent to an upstream commit (a successful `git cherry` reporting no `+` commit, the state a rebase merge or single-commit squash leaves behind). Previously the merged-proof was ancestry only, so every rebase-merged branch was retained. The patch-equivalence path deletes with `git branch -D` because `-d` re-checks ancestry; a branch carrying any unmatched commit, a multi-commit squash, or a `git cherry` invocation that fails keeps the branch retained with its evidence.

## 0.87.1

### Changed

- **`/handoff` closeout reports only operator-actionable session mechanics.** The propose and execute workflows drop internal bookkeeping from the operator-facing closeout.

## 0.87.0

### Changed

- **`[review]` is no longer tolerated as a spelling of `[audit]`.** The foundation described it as the legacy spelling of the `[audit]` assertion tag. That description is gone: the assertion tags are `[test]`, `[eval]`, and `[audit]`. An assertion still carrying `([review])` now reports an invalid tag under `/audit-specs`, and `/audit-tests` no longer lists it among the tags it skips. Migrate `([review])` to `([audit])` — the assertion text is unchanged, only the tag spelling.

  The tolerance was this plugin's own. An assertion carrying `([review])` is migration debt against the methodology version a repository declares, and resolving it to `([audit])` never made that artifact valid.

### Added

- **`help` names where the changelogs are.** The lifecycle skill's `help` verb reports this plugin's changelog and the marketplace changelog. Each is read from disk, without network access.

This changelog begins here; earlier history predates the line.
