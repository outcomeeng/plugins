# Scratch Path Validation

PROVIDES a validator that flags a fixed temporary path in authored plugin content — an absolute temporary root, a home-relative temporary directory, or a shell parameter-expansion fallback that reintroduces one — while passing the unique-per-invocation sources that replace them
SO THAT the marketplace quality gate and skill and agent authors
CAN keep shipped scratch storage collision-free under concurrent runs and inside the directories a consumer's session declares

## Assertions

### Scenarios

- Given a file naming a fixed temporary path, when the validator scans it, then it reports the file, line, and path and exits non-zero ([test](tests/test_scratch_path.scenario.l1.py))
- Given a file whose scratch storage is all unique-per-invocation, when the validator scans it, then it reports nothing and exits zero ([test](tests/test_scratch_path.scenario.l1.py))

### Compliance

- NEVER: the validator passes a fixed temporary path in authored plugin content — an absolute temporary root (`/tmp`, `/var/tmp`, and the macOS firmlink spellings `/private/tmp` and `/private/var/tmp`), that root carrying any child path, a home-relative temporary directory (`~/tmp`, `$HOME/tmp`, `${HOME}/tmp`), a shell parameter-expansion fallback naming one (`${TMPDIR:-/tmp}`), or a named child of the environment's own temporary root (`$TMPDIR/<name>`, `${TMPDIR}/<name>`) — because every such path is identical across concurrent invocations and lies outside the directories a consumer's session declares ([test](tests/test_scratch_path.compliance.l1.py))
- ALWAYS: the validator exempts a line carrying the build-comment allow marker and no other line, so content stating the rule may name the paths it prohibits while every unmarked line in the same file stays enforced ([test](tests/test_scratch_path.compliance.l1.py))
- ALWAYS: the validator passes scratch storage a consumer's session can hold — a unique-per-invocation source that names no path (`mktemp -d`, `mktemp -t`, `tempfile.mkdtemp`, `tempfile.TemporaryDirectory`), the environment's own temporary root named by variable and nothing appended to it (`$TMPDIR`, `${TMPDIR}`), because that root resolves per environment while a segment under it resolves the same for every invocation, and a token that merely contains the prohibited spelling without being one (`/tmpfs`, `/opt/tmp/…`, `tmp_path`, `tempfile::tempdir()`) ([test](tests/test_scratch_path.compliance.l1.py))
