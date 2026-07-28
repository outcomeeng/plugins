# GitHub Actions Skills: No complete skills available from official sources

Objective: upskill Codex and Claude on

1. when to use Github Actions - and when to reject user suggestions and which alternatives to suggest
2. how to create GitHub Actions workflows and how to architect them
3. when and how to audit GitHub Actions workflows and for what
4. how to rearchitect GitHub Actions workflows
5. how to secure GitHub Actions workflows
6. how to maintain up to date GitHub Actions workflows using dependabot etc.
7. how to debug and run

## Pseudo-official sources

1. **`github/awesome-copilot`** — referenced by GitHub's own CLI examples (`gh skill install github/awesome-copilot ...`). That's the official GitHub-published skills repo.
2. **`openai/gh-fix-ci`** — OpenAI's official skill specifically for "Debug and fix failing GitHub Actions PR checks". Plus `openai/gh-address-comments`.

## Official agent skills for GitHub Actions

There is **no single official Anthropic-published Skill named "inspect-github-actions"** — neither in [`anthropics/skills`](https://github.com/anthropics/skills) (their public skills repo) nor [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official). What exists is GitHub's and OpenAI's own published Skills, plus narrower-scoped Anthropic skills that touch GitHub Actions (e.g. `claude-api`).

The official material splits cleanly into two camps:

### 1. GitHub's official repo: `github/awesome-copilot`

GitHub publishes [`github/awesome-copilot`](https://github.com/github/awesome-copilot) — referenced by name in their own docs and the `gh skill` CLI examples. It uses the open Agent Skills spec (works in Claude Code, Codex, Copilot CLI, etc.), but they split GitHub Actions guidance across **three primitive types**, not a single Skill:

**Skills** (under `skills/<name>/SKILL.md`):

- **`codeql`** — CodeQL scanning configured via GitHub Actions workflows; SARIF, alert management, troubleshooting. Bundles 6 reference files including `workflow-configuration.md`.
- **`create-github-action-workflow-specification`** — Reverse-engineers a formal spec from an existing `.github/workflows/*.yml` for AI consumption and maintenance.

**Agents** (`agents/<name>.agent.md`):

- **`github-actions-expert`** — Secure CI/CD workflows, action pinning by SHA, OIDC authentication, least-privilege permissions, supply-chain hardening. This is the closest thing to a general "GitHub Actions" skill in their catalog.
- **`github-actions-node-upgrade`** — Upgrade a JS/TS action's Node runtime (e.g. node20 → node24) with major bump, CI updates, validation.

**Instructions** (`instructions/<name>.instructions.md`):

- **`github-actions-ci-cd-best-practices`** — Always-on guidance file rather than a triggered Skill.

Install any of these with `gh skill install github/awesome-copilot <name>` (CLI v2.90.0+).

### 2. OpenAI's official repo: `openai/skills`

[`openai/skills`](https://github.com/openai/skills) ships two curated Skills under `skills/.curated/` that cover the **debug / fix** half of your wish-list:

- **`gh-fix-ci`** — Locate failing PR checks via `gh`, fetch GitHub Actions logs, summarize the failure, propose a fix plan, implement after approval. Bundles `scripts/inspect_pr_checks.py`. (External CI like Buildkite is explicitly out of scope.)
- **`gh-address-comments`** — Address PR review and issue comments via the `gh` CLI; not Actions-specific but adjacent.

### What this means for the `outcomeeng` marketplace

There's a real gap. None of the official skills above is a comprehensive "create / audit / maintain / debug / decide-when-to-use Actions" skill — they're each narrow:

| Concern                       | Closest official coverage                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| Create workflows from scratch | *(gap)* — `create-github-action-workflow-specification` only goes the other direction |
| Audit / harden                | `github-actions-expert` (security focus only)                                         |
| Debug failures                | `openai/.curated/gh-fix-ci`                                                           |
| Maintain (runtime upgrades)   | `github-actions-node-upgrade` (JS actions only)                                       |
| When to use vs. alternatives  | *(gap)*                                                                               |
| Code-scanning workflows       | `codeql`                                                                              |

So if we build one for `outcomeeng/plugins`, the meaningful prior art to read first — and worth either vendoring/forking or linking from our own SKILL.md — is `github/awesome-copilot`'s `github-actions-expert` agent and `openai/skills`'s `gh-fix-ci`. Together they cover roughly 40% of what we need; the create / when-to-use / general-maintenance pieces are open territory.

## Review: `21-github-actions.enabler` scope mismatch

The current `21-github-actions.enabler` spec is narrower than the intention above. It describes GitHub Actions investigation, workflow status reading, and CI failure triage. The intended product surface is a broader GitHub Actions skill family: decide when to use Actions, create and architect workflows, audit existing workflows, rearchitect workflows, secure workflows, maintain workflows over time, and debug or run workflows.

The current spec also reads like an end-user troubleshooting skill. Under `13-infrastructure.enabler`, the stronger abstraction is host-platform infrastructure: structured, Python-driven access to repository identity, authentication state, workflow metadata, run logs, check results, and mutation gates. User-facing skills can consume that infrastructure, but the node itself should declare the platform capability rather than only one troubleshooting path.

### Proposed revision

Rewrite `21-github-actions.enabler/inspect-github-actions.md` around the complete skill surface and keep dependency-specific detail out of the parent spec:

```markdown
# GitHub Actions

PROVIDES GitHub Actions platform guidance, workflow safety policy, workflow design guidance, and Python-driven runtime observability
SO THAT Spec Tree plugin users and marketplace maintainers
CAN choose, build, review, secure, maintain, and diagnose hosted automation through structured runtime guidance

## Assertions

### Compliance

- ALWAYS: route new automation requests through platform-boundary guidance before recommending GitHub Actions over local hooks, repository scripts, scheduled services, or another CI platform ([audit])
- ALWAYS: apply workflow safety policy before authoring, editing, rerunning, dispatching, canceling, or approving any workflow behavior ([audit])
- ALWAYS: source workflow state from Python orchestration of `gh` JSON output and GitHub API responses before summarizing runs, jobs, logs, checks, or workflow files ([audit])
- ALWAYS: separate workflow design, workflow review, runtime operation, and workflow evolution guidance so each surface consumes the lower-index infrastructure it needs ([audit])
- ALWAYS: keep authoring guidance explicit about triggers, permissions, secrets, cache boundaries, runner requirements, validation commands, reusable workflow boundaries, and repository script boundaries ([audit])
- ALWAYS: keep audit guidance explicit about least-privilege permissions, pinned third-party actions, untrusted pull request safety, secret exposure, cache poisoning risk, OIDC use, concurrency controls, and dependency freshness ([audit])
- NEVER: mutate credentials, trigger workflows, rerun jobs, cancel runs, or edit workflow files without explicit user instruction in the same turn ([audit])
```

This revision keeps the node audit-only for now. It also avoids forward test links because this work includes spec and implementation only.

### Dependency-shaped child nodes

The immediate children should expose dependency direction rather than mirror the life cycle list. A better structure has low-index shared enablers, same-index independent surfaces, and one higher-index evolution node that consumes findings from review and runtime operation.

```text
21-platform-boundary
  -> 32-workflow-safety
  -> 32-workflow-observability

21-platform-boundary + 32-workflow-safety
  -> 43-workflow-design

43-workflow-design + 32-workflow-safety + 32-workflow-observability
  -> 54-workflow-review

43-workflow-design + 32-workflow-safety + 32-workflow-observability
  -> 54-runtime-operations

43-workflow-design + 54-workflow-review + 54-runtime-operations
  -> 65-workflow-evolution
```

| Child node                          | Provides                                                                                                                                                                      | Consumed by                                                                                                                              |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `21-platform-boundary.enabler`      | The fit/rejection policy for GitHub Actions versus local hooks, repository scripts, schedulers, hosted CI alternatives, or non-CI services                                    | Workflow design and workflow evolution; read-only investigation consults it only when the user asks whether Actions is the right surface |
| `32-workflow-safety.enabler`        | The security and mutation policy: permissions, event trust, OIDC, secrets, pinning, cache boundaries, runner trust, concurrency, and run-control gates                        | Workflow design, workflow review, runtime operations, and workflow evolution                                                             |
| `32-workflow-observability.enabler` | Python-driven repository identity, authentication, workflow file, run, job, log, check, and artifact inspection                                                               | Workflow review, runtime operations, workflow evolution, and any skill response that summarizes observed GitHub state                    |
| `43-workflow-design.enabler`        | Workflow architecture patterns: triggers, jobs, matrices, reusable workflows, composite actions, repository scripts, caches, artifacts, environments, and validation commands | Workflow authoring, workflow review, and workflow rearchitecture                                                                         |
| `54-workflow-review.enabler`        | Static and semantic audit of existing workflows against the design model, safety policy, and observed repository state                                                        | Workflow evolution; independent of runtime operations because a workflow can be audited without a failed run                             |
| `54-runtime-operations.enabler`     | Failure triage and explicitly requested run controls using observed runs, jobs, logs, checks, and mutation gates                                                              | Workflow evolution; independent of workflow review because a failed run can be diagnosed before a static audit                           |
| `65-workflow-evolution.enabler`     | Maintenance and rearchitecture decisions that change existing automation after lower-index evidence identifies drift, fragility, or bad structure                             | Narrower descendants that perform specific evolution work                                                                                |

This shape encodes these dependency claims:

- Platform boundary and workflow safety occupy different dependency roles. Platform boundary decides whether Actions is a valid answer; workflow safety constrains any answer that touches Actions.
- Observability is a shared lower-level capability, not debugging itself. Audit, maintenance, and failure triage all need the same repository identity, workflow metadata, run metadata, logs, and check data.
- Workflow design comes before authoring and auditing because both need the same architectural vocabulary: triggers, jobs, reusable workflows, composite actions, repository scripts, caches, artifacts, matrices, environments, and validation commands.
- Workflow review and runtime operations share the same index because neither provides a service to the other. Review analyzes the workflow definition; runtime operation analyzes execution evidence through the same workflow-design vocabulary.
- Workflow evolution sits higher because maintenance and rearchitecture consume lower-index evidence and rules. Dependabot configuration, runtime upgrades, action updates, and structural rewrites are changes to existing automation after a lower-level concern explains why the change is needed.

Likely descendants, created only when assertions justify the extra depth:

| Parent                          | Potential descendants                                                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `43-workflow-design.enabler`    | `21-workflow-authoring.enabler`, `32-reusable-workflow-architecture.enabler`, `43-repository-script-boundaries.enabler` |
| `54-workflow-review.enabler`    | `21-correctness-audit.enabler`, `32-security-audit.enabler`, `43-maintainability-audit.enabler`                         |
| `54-runtime-operations.enabler` | `21-failure-triage.enabler`, `32-explicit-run-control.enabler`                                                          |
| `65-workflow-evolution.enabler` | `21-dependency-maintenance.enabler`, `32-runner-runtime-upgrades.enabler`, `43-workflow-rearchitecture.enabler`         |

Coordinate with the sibling `22-github-actions.enabler` before creating these children. That directory may be another agent's active work on the same problem, and the final tree should have one coherent GitHub Actions branch rather than duplicate siblings.
