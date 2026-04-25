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
| universal invariants               | `proptest` or `quickcheck`     |

</what_belongs_here>

<file_placement>
Unit evidence usually lives in one of two places:

- inline inside the production module with `#[cfg(test)]`
- co-located spec evidence in `spx/.../tests/{slug}.unit.rs`

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
#[test]
fn loads_config_from_temp_dir() {
    let temp = tempfile::tempdir().unwrap();
    let path = temp.path().join("app.toml");
    std::fs::write(&path, "mode = \"fast\"\n").unwrap();

    let config = load_config(&path).unwrap();

    assert_eq!(config.mode, Mode::Fast);
}
```

</tempdir_pattern>

<property_pattern>

```rust
proptest! {
    #[test]
    fn canonical_key_roundtrips(input in "[a-z0-9_-]{1,32}") {
        let parsed = CanonicalKey::parse(&input).unwrap();
        prop_assert_eq!(parsed.as_str(), input);
    }
}
```

</property_pattern>

<anti_patterns>

- generated mocks for the primary seam
- async runtimes or real binaries when a pure seam would give stronger evidence
- snapshotting hand-written fixtures instead of asserting structure
- filesystem writes outside a tempdir

</anti_patterns>
