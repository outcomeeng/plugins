<table_of_contents>

- `<overview>` and `<what_belongs_here>` — Level 1 scope and tooling
- `<file_placement>` — linked Spec Tree evidence location
- `<dependency_seam_pattern>` and `<recorder_pattern>` — controlled implementation seams
- `<tempdir_pattern>` and `<property_pattern>` — infrastructure-backed Level 1 evidence
- `<anti_patterns>` — rejected Level 1 shapes

</table_of_contents>

<overview>
Level 1 covers logic that can run with Rust stdlib, normal developer tooling, and temporary local fixtures. The goal is fast, deterministic evidence with direct coupling to the governed code.
</overview>

<what_belongs_here>

| Concern                            | Typical tooling                |
| ---------------------------------- | ------------------------------ |
| parsing, validation, serialization | `#[test]`, `assert_eq!`        |
| tempdir-backed filesystem logic    | `tempfile`                     |
| deterministic command building     | hand-written trait seams       |
| finite input/output mappings       | `rstest` or table-driven tests |
| universal invariants               | property harness wrapper       |

</what_belongs_here>

<file_placement>
Linked Spec Tree evidence lives in `spx/.../tests/{subject}.{evidence}.l1.rs`. Keep assertion files there and keep reusable harnesses, generators, and inert fixtures in the `<package>-testing` workspace crate; inline `#[cfg(test)]` modules are not linked Spec Tree evidence.

</file_placement>

<dependency_seam_pattern>
Use real Rust seams with narrow traits or function parameters.

```rust
pub trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}

pub fn build_sync_args(config: &SyncConfig) -> Vec<String> {
    vec![
        "--delete".to_owned(),
        config.source.display().to_string(),
        config.destination.display().to_string(),
    ]
}

pub fn sync_repo<R: CommandRunner>(
    config: &SyncConfig,
    runner: &R,
) -> Result<SyncResult, SyncError> {
    let args = build_sync_args(config);
    let borrowed = args.iter().map(String::as_str).collect::<Vec<_>>();
    runner.run("rsync", &borrowed)?;
    Ok(SyncResult::success())
}
```

</dependency_seam_pattern>

<recorder_pattern>

```rust
use std::cell::RefCell;

struct RecordingRunner {
    calls: RefCell<Vec<(String, Vec<String>)>>,
    result: Result<CommandOutput, CommandError>,
}

impl CommandRunner for RecordingRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError> {
        self.calls.borrow_mut().push((
            program.to_owned(),
            args.iter().map(|arg| (*arg).to_owned()).collect(),
        ));
        self.result.clone()
    }
}
```

</recorder_pattern>

<tempdir_pattern>

```rust
use <package>_testing::fixtures::configs::fast_mode_config;
use <package>_testing::harnesses::filesystem::assert_loads_config_from_temp_dir;

#[test]
fn loads_config_from_temp_dir() {
    assert_loads_config_from_temp_dir(fast_mode_config(), load_config);
}
```

</tempdir_pattern>

<property_pattern>

```rust
use <package>_testing::generators::keys::canonical_key_strings;
use <package>_testing::harnesses::properties::assert_canonical_key_roundtrips;

#[test]
fn canonical_key_roundtrips() {
    assert_canonical_key_roundtrips(canonical_key_strings(), CanonicalKey::parse);
}
```

</property_pattern>

<anti_patterns>

- generated mocks for the primary seam
- async runtimes or real binaries when a pure seam would give stronger evidence
- snapshotting hand-written fixtures instead of asserting structure
- filesystem writes outside a tempdir

</anti_patterns>
