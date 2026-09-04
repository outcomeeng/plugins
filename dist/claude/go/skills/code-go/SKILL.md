---
name: code-go
description: ALWAYS invoke this skill when writing or fixing implementation code for Go. NEVER write or repair Go implementation code without this skill.
allowed-tools: Read, Write, Glob, Grep, Edit, Skill, Bash(gofmt:*), Bash(go vet:*), Bash(go build:*), Bash(go test:*), Bash(staticcheck:*), Bash(golangci-lint:*)
---

Invoke the `go:go-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

Invoke the `go:go-test-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
Go implementation code with spec-driven behavior, explicit seams, and full validation passing.
</objective>

<bundled_files>
References live at `${CLAUDE_SKILL_DIR}/references/` and workflows at `${CLAUDE_SKILL_DIR}/workflows/`; the loading message supplies that base directory. Do not search the product directory for skill files.
</bundled_files>

<quick_start>

1. Read the repo-local Go overlays when present; the standards above are already loaded.
2. Follow `<context_loading>` when this is a spec-tree work item.
3. Read `${CLAUDE_SKILL_DIR}/workflows/implementation.md` for new work or `${CLAUDE_SKILL_DIR}/workflows/remediation.md` for review feedback.
4. Invoke `/verify` when behavior changes require new or revised evidence; use `/test-go` for Go expression after test is selected.
5. Finish with the repository validation sequence or, if none is published, `gofmt -l .`, `go vet ./...`, the repository's linter, and `go test -race ./...`.

`allowed-tools` preapproves only the listed raw-tool fallbacks. A repository-canonical wrapper outside those patterns uses the runtime's normal per-call approval path; NEVER select a fallback merely to avoid that approval.

</quick_start>

<essential_principles>

Behavior comes from specs and their selected test, eval, or audit evidence. Existing code is reference material, not authority.

Prefer explicit types, wrapped errors, and narrow seams over framework-heavy indirection. Interfaces and function parameters are for real architectural boundaries, defined where they are consumed, not for decoration.

No generated mocks as the default testing strategy. When a controlled implementation is needed, keep coupling to the real seam with a small hand-written recorder, harness, or interface implementation.

Every goroutine has an owner and an exit condition; every blocking call takes a `context.Context`.

NEVER declare work complete until the full validation sequence passes.

</essential_principles>

<repo_local_overlay>
After loading `/go-standards` and `/go-test-standards`, check for `spx/local/go.md` and `spx/local/go-tests.md` at the repository root. Read each file that exists before discovery and implementation. Treat each as repo-local routing to the product's governing specs and decisions; a local overlay supplements skill behavior and does not declare product truth.
</repo_local_overlay>

<hierarchy_of_authority>
Use guidance in this order:

1. this skill and its loaded Go standards
2. loaded ADRs, PDRs, and spec-tree artifacts
3. `CLAUDE.md`, `README.md`, `docs/`, and other product documentation
4. selected test, eval, or pathless audit evidence
5. existing code as the lowest-layer reference

When layers disagree, the higher authority wins.
</hierarchy_of_authority>

<codebase_discovery>
Before writing code, discover what already exists.

Read:

- `README.md`, `docs/`, `CLAUDE.md`, and `CONTRIBUTING.md` when present
- `go.mod` for the module path, Go version, and dependencies
- the linter configuration (`.golangci.yml` or `staticcheck.conf`) when present

Search for:

- similar packages, interfaces, structs, and error types
- existing seam patterns for process, storage, network, and time boundaries
- logging conventions (`log/slog` handlers and attribute names)
- harness and generator packages under `internal/testinfra/`

Before implementation, confirm:

- which dependencies are already in `go.mod`
- which package naming and error patterns the repository uses
- whether an existing seam or package already solves the problem

</codebase_discovery>

<testing_methodology>
Invoke `/verify` before adding or revising evidence. When it selects test, use `/test-go` for Go expression and follow RED/GREEN. When it selects evaluate, read the eval definition, cases, materialized prompt, real producer contract, selected product command, and threshold; run that command before and after implementation. When it selects audit, preserve the pathless requirement for the isolated verifier without inventing a test. If the change alters behavior and no evidence already proves that behavior, establish the selected evidence first.

Use `/go-test-standards` as the canonical source for filenames, evidence levels, controlled implementations, property tests, toolchain-oracle evidence, fixture placement, and coverage expectations. Keep production code aligned with those constraints instead of re-declaring test policy here.
</testing_methodology>

<audit_requirement_handoff>

For each `/verify` routing row whose verification type is audit, re-read the routed spec or decision artifact and confirm the exact subject still carries `([audit])`. The completion report includes one `Audit requirements` row per audit routing row with the full `spx/...` source path, exact subject text, and status `preserved`. The row count must equal the routing result's audit-row count; when that count is zero, report `Audit requirements: none selected`.

</audit_requirement_handoff>

<context_loading>
If this work belongs to a spec-tree node:

1. invoke `spec-tree:contextualize` with the full path
2. abort if required context is missing
3. implement only after the context is loaded

If the work is outside the spec tree, proceed with the provided requirements and repository context.
</context_loading>

<reference_guides>

- `${CLAUDE_SKILL_DIR}/references/outcome-engineering-patterns.md` -- Go-native code patterns for seams, config, errors, and cleanup
- `${CLAUDE_SKILL_DIR}/references/test-patterns.md` -- debuggability-first Go test organization
- `${CLAUDE_SKILL_DIR}/references/verification-checklist.md` -- completion checks and validation commands
- `${CLAUDE_SKILL_DIR}/workflows/implementation.md` -- protocol for new implementation work
- `${CLAUDE_SKILL_DIR}/workflows/remediation.md` -- protocol for fixing review feedback

</reference_guides>

<success_criteria>

- The Go implementation satisfies its governed evidence with no unresolved implementation-audit finding.
- The repository's canonical format, vet, and lint commands pass; its race-enabled test command passes; every test or eval command selected by `/verify` passes its declared criterion.
- Behavior-changing work has selected test or eval evidence, or an `Audit requirements` report whose `preserved` rows match `/verify`'s audit routing rows.
- No temporary debug code, commented-out implementation, or TODO/FIXME escape hatch remains.

</success_criteria>
