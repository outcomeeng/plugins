# Changelog — spec-tree plugin

Spec Tree methodology skills and agents: `/understand`, `/contextualize`, `/author`, `/decompose`, `/refactor`, `/align`, `/apply`, `/verify`, the audit family, and the merge lifecycle.

What changed in **this plugin**, for a consumer repository. An entry appears when a change alters what a consumer can rely on, must do, or must know.

Sections are `Breaking`, `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Requires`. `Breaking` is separate from `Changed` because a renamed skill breaks invocation outright rather than behaving differently.

A version missing below shipped without an entry. Read the gap as an absent entry, never as an absent release.

An entry is written by the changeset that ships the change. A later changeset adds one only for a release its own diff modifies or reverses, and names that release's commit — the entry is then checkable against the diff carrying it. The entry covers that commit whole, because checkability comes from naming a commit a reader can open rather than from matching lines; a commit large enough that this reaches unfamiliar content is a commit whose entry belongs to whoever shipped it. Any other backfill reconstructs what a release's consumers needed from commits and diffs alone, which produces a guess, and a guess in this file is indistinguishable from a record. A gap not reachable that way stays open.

## 0.96.0

### Changed

- **`/wait-for-load` is one shell line chained ahead of the command it guards.** The waiter runs as `python3 "${CLAUDE_SKILL_DIR}/scripts/wait_for_load.py" && <command>`, on Claude Code and Codex alike, so its zero exit is the only thing that starts the command and a not-ready result skips it by construction. One invocation owns the whole readiness attempt for up to four hours: it observes, sleeps, rechecks, and after its first ready observation sleeps a settle delay of the elapsed wait modulo 180 seconds, then confirms against a second observation that must sit at capacity with a one-minute load not risen past the five-minute load by more than half a core. Waiters that arrived at different moments on one host therefore start at different moments, and a waiter that sees other work just starting returns to its loop instead of joining the herd. A `not_ready` result is terminal for the attempt; the agent-side retry of up to ten invocations is gone.
- **The waiter's terminal JSON document goes to standard error.** Standard output stays empty, so a pipe or redirect the agent attaches to the guarded command never swallows the readiness result, and no parser stage stands between the waiter's exit code and the `&&`.
- **A lost or truncated readiness result re-runs the line.** The command ran only if the waiter exited zero, so a result compaction removed is recovered by running the same line again; the workflow no longer stops for the operator.
- **The router requires the waiter only before a resource-intensive command.** A test suite, an eval, a full gate, a compiling build, or an install verification is chained behind the waiter; formatting, a single-file lint, a markdown or link validation, an instruction-block render, and a status read run directly. The Codex router keeps its process-handle lifecycle rules and drops the requirement to run the waiter and the command in separate `functions.exec` calls. The router template advances to 0.39.0.
- **No failure of a guarded command is called flaky before the waiter's observation is consulted.** Sustained load above capacity starves short-budgeted operations; the skill names that as starvation, not flakiness.

## 0.95.2

### Requires

- **`@outcomeeng/spx` 0.6.21 or newer.** Stage 4 enumerates the inventory from the `resolvedScope` array `spx verification run start` returns, and the stage 7 reconciler reads the recorded units from `render`'s `auditScopeUnits`. Both fields first appear in 0.6.21; below it `start` names the field `changedScope` and `render` omits the scope units entirely, so the reconciler cannot exit zero and `finish` is unreachable.

### Fixed

- **An implementation audit can no longer record a scope unit only where it found something.** `audit-implementation` now persists a concern's complete claimed-path coverage *before* any of that concern's findings, so a path inspected and found clean produces a scope row rather than none, and a raised finding or a `rejected` terminal status never shortens the inspection — rejection is a verdict about what was inspected, not permission to leave a concern or a resolved path unrecorded. An observed run piped in the correct 48-path inventory, loaded all three concern skills, read fourteen subject bodies, then recorded two `code` units — both carrying its single finding — and sealed `rejected` with no `tests` or `architecture` unit at all.
- **Pre-finish reconciliation is a command with an exit code, not an account the run driver gives of itself.** `resolve_scope.py` accepts `--reconcile-run <token>` with `--scope-identity <base>..<head>`, reads the run's sealed start inventory and recorded scope units back through `spx verification run input` and `render`, and reports `unaccounted`, `unexpected`, `drifted`, and `nonfinal`. The sealed identity addresses the run and the selector is resolved afresh only to detect drift; addressing the run by a freshly resolved identity makes SPX reject the locator in exactly the drifted case, reporting a command failure instead of the drift. Exit 1 naming only unaccounted paths returns the run to inspection; exit 1 naming drift, an unexpected subject, or a non-final required unit returns the blocked diagnostic, since the append-only run revises none of those; `finish` is reachable only from exit 0. A run the reconciler cannot read — the CLI absent from `PATH`, a nonzero `spx` exit, or a unit shaped so the comparison cannot run — exits 2 with the diagnostic prefix, never 1, so a driver never mistakes a command failure for an unreconciled run. Drift dominates an exit-1 verdict: a selector that no longer resolves to the sealed inventory returns the blocked diagnostic, never another inspection pass. An advisory `worktree:` run seals its live paths under `live_paths` in the start input, and the reconciler expects them beside the committed inventory without counting them as drift. A discovered language's missing concern is one required `missing-skill` unit naming the absent skill, which the reconciler never counts as an unexpected subject. Coverage is judged against the run's own sealed inventory rather than against the plan the run driver holds, because a plan narrowed before enumeration reconciles with itself; the fresh resolution of the selector is a separate freshness check, reported as `drifted` when it no longer agrees with that inventory. The prior stage-7 wording asked for the same reconciliation in prose and two consecutive released versions omitted it without leaving a trace.
- **A preloaded audit skill binds its target from the request text when its argument is empty.** A harness that preloads a skill into a configured agent renders the `$ARGUMENTS` substitution before any request exists, so it is always empty there. `audit-implementation`, `audit-changeset-coherence`, `audit-pdr`, `audit-adr`, `audit-specs`, `audit-eval-evidence`, and `audit-tests` now take the target from `$ARGUMENTS` when it is non-empty and from the request text otherwise, and report a missing target only when the request carries none. An observed 0.94.3 run returned `BLOCKED` on the empty substitution while three runs on the identical input bound `HEAD` from the request.
- **Language discovery reads the installed skill inventory instead of probing it.** `audit-implementation` now states that the installed skill list the dispatched context carries is the discovery source for `code-{lang}` names, and that invoking a concern skill is dispatch to a discovered language, never a probe for whether one exists. An observed run on a TypeScript changeset invoked `python:audit-python-code` and `rust:audit-rust-code`, received `Unknown skill` for both, and read the errors as discovery evidence — one prose judgment away from recording two `missing-skill` units for languages the changeset never touched.

### Changed

- **A sealed run's recorded subject set equals the changed-path inventory its own start input carries.** Every resolved path a concern did not claim is now recorded as an accounting record — `auditKind` `coverage-gap`, `coverageRequirement` `optional`, `coverageStatus` `skipped`, no `languagePartition`, `producerProvenance` omitted — which states that the path was considered and left to its artifact-type auditor. It claims no coverage, creates no language partition, and rejects no run. Previously such a path carried no unit at all, so a run that stopped early and a run that finished were indistinguishable in the projection. Consumers reading `auditScopeUnits` will see one row per changed path where earlier versions emitted rows only for claimed paths.

## 0.95.0

### Changed

- **Change state now lives in project fields.** `/pickup` and `/handoff` treat Product, Maturity, and Status as the canonical metadata source.
- **Transitions stop at partial state.** Each workflow reports completed writes, the failed operation, and the complete observed state before ending.
- **Terminal transitions are complete.** `/handoff` verifies the terminal precondition, posts the authorized record, removes the holder, writes `Applied`, `Refined`, or `Abandoned`, closes the issue with the matching reason, and reads the complete terminal state back.

### Fixed

- **Claim and release write Status.** Pickup writes `Claimed`; handoff writes `Available`; both verify project fields, assignees, and the transition comment.
- **New Change bodies contain no metadata line.** Legacy metadata is removed only after project fields are reconciled and verified from issue history.

## 0.94.2

### Fixed

- **An implementation audit can no longer seal a narrowed inspection as a complete one.** `audit-implementation`'s pre-finish reconciliation compared the run's recorded units against the run's own planned inventory, so a plan narrowed before enumeration reconciled with itself and sealed `approved`. Stage 7 now reconciles against a fresh resolution of the same selector: every resolved path a discovered concern claimed carries a recorded unit, every remaining resolved path is named with the ownership reason it carries none, and a recorded subject set accounting for fewer paths than the resolver returned cannot seal. An observed run recorded 4 units for a 48-path changeset and sealed approved with zero findings.
- **The resolved changed-path inventory reaches the run through a pipe instead of being retyped.** `resolve_scope.py` accepts `--audit-input`, a JSON object of the short values the invocation supplies, and merges it *beneath* the git-resolved scope; the skill pipes the result into `spx verification run start --input stdin`. A supplied `base`, `head`, or `changed_paths` key is discarded rather than honored. Previously the skill read the resolver's changed paths out and re-emitted them into a hand-composed payload; an observed run transcribed 47 of 48 paths, dropping two and substituting a third same-named file from another directory, with nothing downstream able to notice.

### Changed

- **`audit-implementation` hands every language trio the complete resolved changed-path set.** The run driver no longer pre-filters that set by extension, directory, or its own guess at applicability — each concern skill owns its language's applicability and answers for the paths it claims — and it records one scope unit per path a concern returned, never fewer and never a representative row standing for several. Leaving a path to another artifact-type auditor still records no coverage unit for it, but stage 7 now names that path and its ownership reason, so a reader can tell a path considered and left to its owner from a path never reached.

## 0.94.1

### Fixed

- **An implementation audit can no longer seal an unfinished inspection.** `incomplete` and `skipped` are no longer admissible final statuses for a required coverage unit in `audit-implementation`; a required unit reaches only `audited`, `not-applicable`, `missing-skill`, or `unsupported`. A run that reaches none of those returns the existing blocked diagnostic naming the concrete failed operation or absent prerequisite. Remaining work, elapsed time, context pressure, and unfinished reading are never such a cause. Previously `finish` was reachable directly from a self-declared stop, and the resulting sealed `rejected` run with zero findings was indistinguishable from a completed audit that found a coverage gap.

### Changed

- **`audit-implementation` runs an ordered execution sequence with a pre-finish reconciliation gate.** Seven stages — anchor, open the run, load, enumerate, inspect, resolve, reconcile — replace an ordering that was distributed across four sections. Stage 7 confirms every planned unit carries a final status and every recorded finding references an accepted unit before `finish`; a failed reconciliation returns the run to inspection rather than sealing. Stage 5 requires each subject body to be read complete from the resolved `base..head` scope, re-issuing a truncated read in bounded ranges and never deriving a subject from a single commit's patch. Stage 3 loads each concern's governing standards and the audited repository's declared `spx/local/` overlays before any concern judgment; a finding raised before that load is withdrawn rather than recorded.
- **`audit-implementation`'s description states what it judges.** The skill listing now names the subject and the standards judged against — a changeset's implementation against its governing decisions, specs, and language standards — instead of its internal dispatch and persistence mechanics. Skill selection reads the same way as every sibling `audit-*` skill.
- **`audit-implementation` carries its SPX command forms once.** A duplicated block repeating the `scope add` and `finding add` command skeletons is removed, and the idempotency-key derivation is stated as its rules rather than its reasoning. The key composition, quoting rule, and payload field contracts are unchanged.

## 0.93.0

### Changed

- **The `/understand` foundation states methodology 4.0.** The inline foundation declares the seven node kinds — `.product`, `.substrate`, `.capability`, `.domain`, `.interface`, `.surface`, `.variant` — with their openings, order, and containment; the `{slug}.spec.md` spec file with front matter carrying `id`, `kind` at the root, and `malleability`; the outcome record, the machine-written status claim, and `ISSUES.md` as the only node-local note; decision records placed in the node whose subtree they govern; six verification types over the Deterministic, Agentic, and Attested modes with the `[test]`, `[eval]`, `[probe]`, and `[audit:{rule-slug}]` tags; malleability, state, and the merge composition by the least malleable node; index semantics where prerequisites precede consumers and independent siblings may differ; the context walk over every sibling contract; and the Change with its Maturity, Lifecycle, and capitalized roles. Work ordering lives in a Change, never in a `PLAN.md`. The passing-scope list is operational configuration a toolchain that has not adopted the status claim still reads.
- **Templates and examples follow the 4.0 kinds.** The product template is front matter and a title; one spec template per output kind plus the variant, an outcome-record template, and a probe protocol template replace the enabler and outcome templates; capability, domain, outcome-record, and probe examples replace the enabler and outcome examples.
- **References carry the conditional detail.** `kind-decision.md` holds the ordered kind tests and the structural-quality scorecards, `grammar.md` the EBNF and link forms, `artifact-placement.md` the test-infrastructure boundary and the ruled-out placements, and `status-claims.md` the claim's shape and state derivation; `excluded-nodes.md` is removed.

### Requires

- A consumer declaring methodology 4.0 authors under these rules; the SPX CLI's admission of the 4.0 suffixes, front matter, probes, and status claims ships in its own release, and a tree keeps its current directory suffixes until then.
- No `/probe` skill ships yet: `/verify` routes a probe assertion to `/probe` when the runtime skill catalog carries it and otherwise reports the capability gap, so a probe protocol is authored by hand from the `/understand` template until that skill ships.

## 0.92.9

### Changed

- **Skills and the router name the Author and Verifier roles.** The `/understand` foundation, `/open-pr`, and the merging-standards policy reference describe who produces and who verifies a changeset with the capitalized roles the spec-tree methodology defines — the Author's agent session, a Verifier's agent session, the Reviewer — in place of "authoring agent session" and "verifier agent session". The managed instruction block carries the same names in its dispatch and boundary rules, and its template advances to 0.37.1 so consumer routers re-render.

## 0.92.8

### Added

- **The router names the methodology declaration.** The managed instruction block's `/understand` section now directs the reader to `spx.config.yaml` at the repository root, where `methodology.source` and `methodology.version` declare the methodology the repository follows, to read it again whenever `/understand` runs, and states that an absent file, a missing `methodology` block, or a `methodology.version` of the sentinel `installed` means no declared methodology version, never one inferred from a plugin's distribution version, a changelog, or prose.
- **The template advances to 0.37.0.** `/update-instruction-block` re-renders a consumer's router block once its recorded version is behind. New in this release is the methodology-declaration paragraph above. Already present in the template, and reaching consumer routers only through this bump, are the Go language block and the registry check command that shipped after 0.36.0 without a template version change.

## 0.92.3

### Changed

- **`/issue` attaches the marketplace name with `--name=`.** The resolver invocation passed the name as a separate argv token, which option parsing reads as another option when the value begins with `-`. The shipped invocation now uses `--name=outcomeeng`, so the name reaches the resolver whatever its first character. The name the skill passes is a fixed literal, so no consumer invocation changed behaviour.
- **`/issue` matches a Claude Directory source exactly.** The marketplace resolver previously case-folded the entry's `source` before comparing it to the `directory` token, so `Directory` and `DIRECTORY` resolved a path. The token is a fixed literal, so the resolver now compares it exactly and a source differing in case resolves nothing. A registration emitting the token in any other case was never produced by `claude plugin marketplace list --json`.

### Fixed

- **`/issue` files its follow-up from a programmatic runner.** The handoff payload previously reached `spx session handoff` through a quoted heredoc alone, so a programmatic Claude Code or Codex run, or a hosted runner whose parser requires one physical command line, had no supported form. The skill now names both stdin forms and which harness selects each, and grants `printf`, matching `/handoff`'s existing treatment of the same payload.
- **Codex marketplace resolution reads only the fields Codex emits.** `/issue`'s marketplace resolver looked for a local checkout path at a top-level `path` field and a `sourceType` at the entry level; neither appears in `codex plugin marketplace list --json` output. Resolution now reads `marketplaceSource.sourceType`, then `marketplaceSource.source`, then the top-level `root` every entry carries, so a marketplace registered from a local directory resolves from `root` when `source` is absent.

## 0.92.2

### Changed

- **Session identity is read from the variable the agent publishes.** The `/handoff` and `/issue` skills resolve the agent session identity with `printenv CLAUDE_CODE_SESSION_ID` on the Claude Code surface — the variable Claude Code injects itself, which Pi's Claude-Code-compatible surface also publishes — and `printenv CODEX_THREAD_ID` under Codex. The grants match: each render carries only its own agent's `printenv` grant. A consumer whose `spx` still writes `CLAUDE_SESSION_ID` into the env file is unaffected; that export is no longer what these skills read.

## 0.92.1

### Changed

- **`/pickup`'s issue-dependency grant names the endpoint.** The pickup skill's `gh api` grant for the Change store's dependency graph is `gh api repos/*/issues/*/dependencies/blocked_by:*`; the tool boundary admits the `blocked_by` read and the `-X POST -F issue_id=…` write the Framed step performs and no other dependency endpoint. The store repository stays bound by the workflow, as with every `gh --repo` grant.

## 0.92.0

### Added

- **Changes and Handoffs as GitHub issues, opted into by an overlay.** When a repository declares a Change store in `spx/local/coordination.md` — the issue repository, the org project carrying `Product` and `Maturity` fields with `Status` projecting Lifecycle, and the repository's `Product` value — `/pickup` follows `workflows/change.md` and `/handoff` follows `workflows/05-change.md`, per methodology `versions/next/11-coordination.md` and its GitHub realization. `/pickup` claims a Change by assignee, turns a legacy `.spx/sessions` file into a Proposed Change carrying the whole file as received input and archives the file only then, routes by Maturity — refinement through `/interview` below Executable, execution only at Executable after the Frame's Nodes, Assertions, Decisions, blockers, and lineage are validated against current truth — and continues from the newest `Handoff:` comment's Next Activity. `/handoff` refines what was learned into the Change body, then posts the five-line `Handoff:` comment and removes the assignee, or closes the Change as Applied, Refined, or Abandoned with the authorized comment. Both skills carry the `gh issue` and `gh project` grants the workflows use, and every issue body and comment reaches `gh` on stdin.

### Changed

- **Without `spx/local/coordination.md` nothing changes.** The session-file workflows remain the default; the overlay selects the Change workflows.

## 0.91.0

### Added

- **Product content is a defined term.** The `/understand` foundation defines product content as every product artifact a spec node governs or must govern — source, tests, evals, generated output, specs, decisions, coordination notes, spec-declared configuration, implementation being its code layer — with the governing node found by search under the live foundation marker: a path under a node directory belongs to that node; any other path to the node whose test file names it and whose spec links that test, or whose spec or decision names that path in an `[audit]` assertion; several matching nodes resolve to their lowest common ancestor. Product content with no governing spec is not read or modified; the gap is recorded. Operational configuration — the `spx/local/` overlays and the exclusion mechanism, read by the skill that declares them without the marker — and the agent harness's own instruction and settings files, tool output, the session store, and scratch space are not product content.

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

- **A root instruction file that only points at the other one is detected and resolved by answer, not by guess.** A repository whose `CLAUDE.md` says little more than "see the other root instruction file" previously read as divergence: the two bodies shared almost nothing, so nothing was wrapped as a `shared` region and each file kept its own harness's router under a pointer to the other file's differently rendered one — sending a reader to the wrong harness's instructions. `/update-instruction-block` now reports such a file as a delegation candidate and holds the surface `stale` until the operator names the side both files take. Candidacy is decided from two facts about the file — the body names the other root instruction file, and its text stays within an absolute character bound — never from a reading of what the prose means, because adoption replaces a whole body and a wrong guess costs that file its instructions.

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
