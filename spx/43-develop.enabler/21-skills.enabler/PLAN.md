# PLAN — Marketplace-wide gerund→imperative skill rename

**Status:** planned; execute in a dedicated session. Delete this file when the transition lands.

## Decision

`spx/local/skills.md` declares that new skills use imperative names and the marketplace is mid-transition. The remaining gerund-named skills (~70 across all plugins) migrate to imperative form as one coordinated, marketplace-wide breaking change — never folded into a single plugin's content work (per `spx/43-python.enabler/25-python-standards.enabler/ISSUES.md` item 1).

A Python-only rename is incoherent: the Python language skills reference shared foundations (`testing`, `auditing`, `architecting`) that the rust and typescript plugins also use, so renaming `testing-python`→`test-python` while `testing` stays gerund is a half-migration. The migration unit is the whole marketplace, landed in one PR so no half-migrated state ships.

## Naming scheme

Drop the `-ing`, use the bare imperative verb, keep the rest of the slug:

| Gerund prefix     | Imperative      |
| ----------------- | --------------- |
| `coding-*`        | `code-*`        |
| `testing-*`       | `test-*`        |
| `architecting-*`  | `architect-*`   |
| `auditing-*`      | `audit-*`       |
| `standardizing-*` | `standardize-*` |
| `reviewing-*`     | `review-*`      |
| `creating-*`      | `create-*`      |
| `writing-*`       | `write-*`       |

Single- and multi-word skills follow the same rule: `contextualizing→contextualize`, `understanding→understand`, `decomposing→decompose`, `refactoring→refactor`, `refocusing→refocus`, `aligning→align`, `applying→apply`, `authoring→author`, `bootstrapping→bootstrap`, `committing-changes→commit-changes`, `merging→merge`, `interviewing→interview`, `tracking-tasks→track-tasks`, `opening-pr→open-pr`, `managing-pr→manage-pr`, `designing-frontend→design-frontend`, `sanitizing-powerpoint→sanitize-powerpoint`, the `*-internal-docs` and `*-agent-prompts` and `*-merging` reference skills likewise. The `reviewing-*` skills `reviewing-pr→review-pr`, `reviewing-systemverilog→review-systemverilog`, and `reviewing-vhdl→review-vhdl` are covered by the same rule (`reviewing-changes` is the command-collision case above).

Already-imperative skills need no change: `clarify`, `merge`, `rtfm`, `audit-adr`, `audit-pdr`, `handoff`, `pickup`.

`apply`, `author`, `bootstrap`, `commit`, and `review-changes` are thin **command** wrappers (`src/plugins/spec-tree/commands/`), not skills — over the gerund skills `applying`, `authoring`, `bootstrapping`, `committing-changes`, and `reviewing-changes`. Renaming each of those skills to the bare imperative (`applying→apply`, …, `reviewing-changes→review-changes`) collides with the command of the same name; see the skill/command-duality open decision.

## Python subset (original session node 2)

The nine Python plugin skills and their targets — a subset of the transition, not a standalone change:

| Current                             | Target                            |
| ----------------------------------- | --------------------------------- |
| `architecting-python`               | `architect-python`                |
| `coding-python`                     | `code-python`                     |
| `testing-python`                    | `test-python`                     |
| `auditing-python`                   | `audit-python`                    |
| `auditing-python-architecture`      | `audit-python-architecture`       |
| `auditing-python-tests`             | `audit-python-tests`              |
| `standardizing-python`              | `standardize-python`              |
| `standardizing-python-architecture` | `standardize-python-architecture` |
| `standardizing-python-tests`        | `standardize-python-tests`        |

## Mechanical recipe (per skill)

1. `git mv skills/<gerund>` → `skills/<imperative>` (source under `src/plugins/<plugin>/skills/`).
2. Update the `name:` frontmatter to match the new directory.
3. Update every cross-reference `/<gerund>` → `/<imperative>` across ALL plugins' skill, command, and agent bodies (running text invokes skills by `/name`).
4. Update every `{!% require_skill 'plugin:<gerund>' %!}` directive.
5. Update every agent `skills:` frontmatter field that preloads a renamed skill.
6. Update catalogs — `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` — and regenerate `README.md` (`just docs`).
7. Update spx specs and conformance tests that assert skill names or `plugins/<plugin>/skills/<gerund>` paths (e.g. the `test_github_pr.conformance.l1.py`-style packaging tests).
8. Update `spx/local/*.md`, `AGENTS.md`/`CLAUDE.md`, and `methodology/` references that name skills.
9. `just build-skills`; bump every touched plugin; `just check`.

First step in the executing session — a repo-wide survey of the live reference set:

```bash
git grep -nP '/(coding|testing|architecting|auditing|standardizing|reviewing|creating|writing|contextualizing|understanding|decomposing|refactoring|refocusing|aligning|applying|authoring|bootstrapping|committing-changes|merging|interviewing|tracking-tasks|opening-pr|managing-pr)\b' -- ':!dist' ':!spx'
git grep -nP "require_skill '[a-z-]+:(coding|testing|auditing|standardizing|reviewing|creating|writing|architecting)" -- src
```

## Breaking-change handling

Hard rename — no aliases, no re-exports (per CLAUDE.md "NEVER maintain backward compatibility"). Every consumer's `/<gerund>` invocation, `require_skill` directive, and agent `skills:` entry breaks until updated; consumers pick up the rename on their next `claude plugin marketplace update`. Landing the whole transition in one PR keeps a half-migrated state from shipping.

## Sequencing vs the queued you-voice sweeps

Two queued sessions sweep `you`-voice in the same skill files: `2026-06-14_16-58-24` (develop/python/typescript) and `2026-06-14_16-58-25` (rust/work/hdl). The sweeps edit file CONTENT; the rename moves directories and updates cross-references. They must not run concurrently on the same files. Recommended order: finish the two `you`-sweeps first (content-only, lower-risk, already queued), then execute the rename over the swept files. Either order is correct if serialized; concurrent execution on the same files is the only failure mode.

## Open decisions for the executing session

- **Slug ordering**: `standardizing-skills` `<descriptions>` teaches language-after-artifact for descriptions ("audit ADRs for Python"), while current slugs put language in the middle (`auditing-python-architecture`). Decide whether imperative slugs reorder to language-last (`audit-architecture-python`) or keep the mechanical drop-`-ing` (`audit-python-architecture`). Recommendation: mechanical form, to bound the change.
- **Skill/command duality**: reconcile any skill-vs-command name collisions surfaced by the survey (e.g. an `applying` skill alongside an `apply` command); pick one canonical name per function.
- Confirm the full inventory from the survey grep before editing.
