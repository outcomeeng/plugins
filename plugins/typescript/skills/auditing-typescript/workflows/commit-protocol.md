# Commit Protocol (Phase 8)

> **APPROVED Only**: Committing is the reviewer's seal of approval.

After all tests pass, commit the completed work item.

**Follow the `committing-changes` skill** for core commit protocol (selective staging, verification, Conventional Commits format).

## Reviewer-Specific Context

When committing as part of review approval, apply these additional guidelines:

### Files to Stage (Work Item Scope)

Stage **only** files from the approved work item:

| Category         | Example Paths                               |
| ---------------- | ------------------------------------------- |
| Implementation   | `src/{modified files for this work item}`   |
| Co-located tests | `spx/.../NN-{slug}.outcome/tests/*.test.ts` |

**Exclude**: Unrelated files, experimental code, files from other work items.

### Commit Message Context

Include work item reference in footer:

```text
feat({scope}): implement {node-slug}

- {brief description of what was implemented}
- Tests passing

Refs: {node-path}
```

### Return APPROVED

After successful commit:

```markdown
## Verdict: APPROVED

Commit: {commit_hash}
Files committed: {count}
Tests passing: {count}

Work item is DONE.
```
