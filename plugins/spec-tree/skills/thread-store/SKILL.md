---
name: thread-store
description: ALWAYS invoke this skill when persisting or retrieving branch-scoped vetting records. NEVER read or write a vetting record directly from the filesystem.
allowed-tools: Bash, Read
---

<objective>
Mediate persistence of branch-scoped vetting records for spec-tree vetting lenses. Lens skills and their wrapper agents call this skill's CRUD CLIs; no lens touches the storage surface directly.
</objective>

<api_surface>

Four CRUD CLIs sit under `${CLAUDE_SKILL_DIR}/scripts/`:

| CLI                | Effect                                       |
| ------------------ | -------------------------------------------- |
| `write_record.py`  | Persist payload at `(slug, name)` atomically |
| `read_record.py`   | Emit the payload at `(slug, name)` to stdout |
| `delete_record.py` | Remove the record at `(slug, name)`          |
| `list_records.py`  | Emit record names under `slug`, one per line |

Every CLI accepts `--slug <slug>` and (for write/read/delete) `--name <name>`. `write_record.py` reads the payload from stdin by default or from `--file <path>` when provided.

</api_surface>

<backend_selection>

The active backend resolves from `SPX_VET_BACKEND`. Default `local` selects the filesystem backend rooted at `.spx/reviews/<branch-slug>/`; `SPX_VET_LOCAL_ROOT` overrides the root for tests and runtime customization. Unknown backend names exit non-zero with a configuration error that enumerates the registered names.

</backend_selection>

<slug_derivation>

Slug derivation re-exports the canonical helper from `${CLAUDE_SKILL_DIR}/../auditing/scripts/audit_orchestrator.py`. The slug:

- replaces `/` in the branch name with `__`
- substitutes a whole-segment `.` / `..` value with a distinct token
- bounds the result at 64 characters; longer inputs truncate and append `--<sha8>`
- disambiguates state-file collisions with the same `--<sha8>` suffix when the caller passes a state directory

</slug_derivation>

<invocation>

Direct invocation from a wrapper agent:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/write_record.py" --slug "$SLUG" --name result.json < "$PAYLOAD_FILE"
python3 "${CLAUDE_SKILL_DIR}/scripts/read_record.py" --slug "$SLUG" --name result.json
python3 "${CLAUDE_SKILL_DIR}/scripts/list_records.py" --slug "$SLUG"
python3 "${CLAUDE_SKILL_DIR}/scripts/delete_record.py" --slug "$SLUG" --name result.json
```

Lens authors instruct the wrapper agent to invoke these commands rather than implementing the I/O inline.

</invocation>

<constraints>

- Scripts run against `python3` only — stdlib, no third-party imports
- Every script under `${CLAUDE_SKILL_DIR}/scripts/` dispatches through the `thread_store` facade; concrete backend modules are never imported directly by lens code
- Writes are atomic via temp-file plus `os.replace`; a crash mid-write leaves the prior payload intact

</constraints>

<success_criteria>

- [ ] Wrapper agent invocations of the four CLIs exit 0 on success
- [ ] `read_record.py` exits non-zero with a `NotFound` message that names slug and record
- [ ] `get_backend()` honors `SPX_VET_BACKEND` and rejects unknown values
- [ ] Slug re-export is identity-equal to the canonical helper

</success_criteria>
