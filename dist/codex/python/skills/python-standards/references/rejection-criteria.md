# Python Rejection Criteria Summary

Recap of the standards stated normatively in `python-standards/SKILL.md`, indexed by the ruff rule code (or `manual` / `review` / `mypy`) that enforces each. The SKILL.md body is authoritative; this table is a lookup.

| Issue                             | Example                           | Rule    |
| --------------------------------- | --------------------------------- | ------- |
| Missing `-> None` on test         | `def test_foo(self):`             | ANN201  |
| Untyped fixture parameter         | `def test_foo(self, tmp_path):`   | ANN001  |
| Missing `-> None` on init         | `def __init__(self, x: int):`     | ANN204  |
| Magic values in assertions        | `assert result == 42`             | PLR2004 |
| Uppercase argument names          | `def __init__(self, WIDTH=8):`    | N803    |
| Shadowing builtins                | `def foo(input: str):`            | A002    |
| Bare `except:`                    | `except: pass`                    | E722    |
| Swallowing exceptions             | `except Exception: pass`          | S110    |
| Hardcoded secrets                 | `API_KEY = "sk-..."`              | S105    |
| `eval()` / `exec()`               | `eval(user_input)`                | S307    |
| `shell=True`                      | `subprocess.run(cmd, shell=True)` | S602    |
| Pickle with untrusted data        | `pickle.loads(data)`              | S301    |
| SSL disabled                      | `requests.get(url, verify=False)` | S501    |
| No context manager                | `f = open(...); f.close()`        | SIM115  |
| Old union syntax                  | `Optional[X]`, `Union[X, Y]`      | UP007   |
| Old generic syntax                | `List[str]`, `Dict[str, int]`     | UP006   |
| Commented-out code                | `# old_function(x)`               | ERA001  |
| Unused imports                    | `import os  # never used`         | F401    |
| Deep relative imports             | `from ... import x`               | manual  |
| `sys.path` manipulation           | `sys.path.insert(0, ...)`         | manual  |
| Unqualified `Any`                 | `def f(x: Any) -> Any:`           | mypy    |
| `type: ignore` no reason          | `x = foo()  # type: ignore`       | manual  |
| Plain class with uppercase fields | `class Status: PASS = "pass"`     | review  |
| Re-export of library constants    | `HTTP_OK = HTTPStatus.OK`         | review  |
