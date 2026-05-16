# Thread Store

PROVIDES a stdlib-only Python package — the `thread_store` facade, the abstract `Backend` protocol, the filesystem-backend implementation, the branch-slug helper re-exported from the audit-orchestrator, a CRUD CLI surface, and the co-located test harness — that mediates persistence and retrieval of branch-scoped vetting records
SO THAT vetting lenses and the thin wrapper agents that wrap them
CAN persist and retrieve lens outputs (machine-readable JSON, human-readable markdown) against one CRUD contract, with one canonical slug derivation shared across lenses, without knowing which backend stores the records

## Assertions

### Scenarios

- Given a fresh worktree, `thread_store.write(slug, name, payload)` creates a record under the filesystem backend's root and a subsequent `read(slug, name)` returns the bytes verbatim ([test](tests/test_thread_store.scenario.l1.py))
- Given an existing record, `thread_store.write(slug, name, new_payload)` overwrites it and a subsequent `read(slug, name)` returns `new_payload` ([test](tests/test_thread_store.scenario.l1.py))
- Given an existing record, `thread_store.delete(slug, name)` removes it and a subsequent `read(slug, name)` raises `NotFound` ([test](tests/test_thread_store.scenario.l1.py))
- Given no record at `name`, `thread_store.read(slug, name)` raises `NotFound` with a structured error message naming the slug and the name ([test](tests/test_thread_store.scenario.l1.py))
- Given a thread with records, `thread_store.list(slug)` returns the set of record names present ([test](tests/test_thread_store.scenario.l1.py))
- Given `SPX_VET_BACKEND` unset, `thread_store.get_backend()` returns the filesystem backend rooted at `.spx/reviews/<branch-slug>/` ([test](tests/test_thread_store.scenario.l1.py))
- Given `SPX_VET_BACKEND` set to a known backend name, `thread_store.get_backend()` returns that backend ([test](tests/test_thread_store.scenario.l1.py))
- Given `SPX_VET_BACKEND` set to an unknown backend name, `thread_store.get_backend()` raises a configuration error naming the unknown value and the set of registered backends ([test](tests/test_thread_store.scenario.l1.py))
- The filesystem backend's `thread_path(slug)` resolves to `<root>/<slug>` and returns the same path across repeated calls for the same slug ([test](tests/test_fs_backend.scenario.l1.py))
- The CRUD CLIs (`write_record.py`, `read_record.py`, `delete_record.py`, `list_records.py`) accept slug, name, and payload via stdin or `--file` and exit 0 on success ([test](tests/test_cli.scenario.l1.py))

### Properties

- `branch_slug(name)` is idempotent — `branch_slug(branch_slug(name)) == branch_slug(name)` for every valid branch name ([test](tests/test_slug.property.l1.py))
- `branch_slug` is injective on valid branch names — distinct branch names produce distinct slugs ([test](tests/test_slug.property.l1.py))
- `branch_slug` output contains no forward slashes and no characters that resolve filesystem paths — slashes, `.`, and `..` segments cannot appear in the output ([test](tests/test_slug.property.l1.py))
- `branch_slug` output length is bounded by a fixed constant — long branch names cannot exhaust filesystem path-length limits ([test](tests/test_slug.property.l1.py))

### Compliance

- ALWAYS: a backend module conforms to the `Backend` protocol — `thread_path`, `write`, `read`, `delete`, `list` are all present with the declared signatures, and `thread_store.get_backend()` refuses to return a non-conforming backend ([test](tests/test_backend_protocol.compliance.l1.py))
- ALWAYS: `thread_store.write` is atomic — the prior content of `<name>` is preserved if `write` is interrupted between the temp-write and the rename ([test](tests/test_thread_store.compliance.l1.py))
- ALWAYS: `branch_slug` is the symbol re-exported from `plugins/spec-tree/skills/auditing/scripts/audit_orchestrator.py` — slug derivation lives in exactly one function source ([test](tests/test_thread_store.compliance.l1.py))
- ALWAYS: every CRUD CLI under `plugins/spec-tree/skills/thread-store/scripts/` performs its filesystem effects through `thread_store.get_backend()` — no CLI calls `open()`, `pathlib.Path.write_*`, `os.remove`, or any other direct filesystem primitive ([test](tests/test_cli.compliance.l1.py))
- ALWAYS: the filesystem backend confines every write to its configured root — `<root>/<slug>/<name>` is the only target shape, and no path resolves outside `<root>` ([test](tests/test_thread_store.compliance.l1.py))
- ALWAYS: the test harness at `outcomeeng_testing/harnesses/thread_store.py` exposes `make_pr_json(tmp_path, base_ref, **kw)`, `with_temp_local_store(tmp_path)`, `run_script(script, *args, stdin=None, env=None)`, and an importlib loader for the `thread_store` facade module ([test](tests/test_thread_store.compliance.l1.py))
- NEVER: a script under `plugins/spec-tree/skills/thread-store/scripts/` imports a third-party package, depends on `uv` at runtime, or imports any `outcomeeng_*` module — stdlib only, per the Plugin Portability Constraints in `AGENTS.md` and `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md` ([test](tests/test_plugin_portability.compliance.l1.py))
- NEVER: a lens skill or wrapper agent imports a backend module directly — every read and write routes through the `thread_store` facade per `spx/21-spec-tree.enabler/32-evidence.enabler/21-vetting.enabler/21-thread-store.enabler/21-backend-abstraction.adr.md` ([test](tests/test_plugin_portability.compliance.l1.py))
