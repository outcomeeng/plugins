<contents>

- `<overview>` — what Level 1 covers
- `<what_belongs_here>` — concern-to-tooling table
- `<file_placement>` — co-located spec test path
- `<dependency_seam_pattern>` — narrow trait and function seams
- `<recorder_pattern>` — recording collaborator that exposes calls
- `<tempdir_pattern>` — harness-owned temporary product, test-owned predicate
- `<property_pattern>` — generator domain, harness run policy, test-owned invariant
- `<anti_patterns>` — Level 1 rejections

</contents>

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
Level 1 `[test]` evidence lives in co-located spec files at
`spx/.../tests/{subject}.{evidence}.l1.rs`. Keep the typed assertion file
there even when the governed production code is pure or module-local.

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
The harness creates the temporary product and releases it through `Drop`. The fixture reaches the governed function as a path. The `#[test]` holds the predicate.

```rust
use <product>_testing::fixtures::configs::fast_mode_config_path;
use <product>_testing::harnesses::filesystem::TempProduct;

#[test]
fn loads_config_from_temp_dir() {
    let product = TempProduct::seeded_from(fast_mode_config_path());

    let config = load_config(product.path()).unwrap();

    assert_eq!(config.mode, product::config::Mode::Fast);
}
```

</tempdir_pattern>

<property_pattern>
The generator owns the domain. The harness owns case count, seed, regression persistence, and replay output. The closure inside the `#[test]` owns the invariant.

```rust
use <product>_testing::generators::keys::canonical_key_strings;
use <product>_testing::harnesses::properties::run_property;

#[test]
fn canonical_key_roundtrips() {
    run_property(canonical_key_strings(), |raw| {
        let parsed = CanonicalKey::parse(&raw).unwrap();

        prop_assert_eq!(parsed.to_string(), raw);
        Ok(())
    });
}
```

</property_pattern>

<anti_patterns>

- generated mocks for the primary seam
- async runtimes or real binaries when a pure seam would give stronger evidence
- snapshotting hand-written fixtures instead of asserting structure
- filesystem writes outside a tempdir

</anti_patterns>
