<overview>
These patterns capture Rust-native seams and boundary shapes that keep implementation code testable and explicit.
</overview>

<external_command_boundary>

```rust
use std::process::Command;

pub trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}

pub struct SystemCommandRunner;

impl CommandRunner for SystemCommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError> {
        let output = Command::new(program).args(args).output()?;
        CommandOutput::from_output(output)
    }
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

</external_command_boundary>

<resource_cleanup_with_raii>

```rust
pub struct TempWorkspace {
    root: tempfile::TempDir,
}

impl TempWorkspace {
    pub fn new() -> std::io::Result<Self> {
        Ok(Self {
            root: tempfile::tempdir()?,
        })
    }

    pub fn path(&self) -> &std::path::Path {
        self.root.path()
    }
}
```

Prefer owned guards and `Drop`-driven cleanup over ad hoc shell cleanup logic.
</resource_cleanup_with_raii>

<typed_config_with_boundary_validation>

```rust
#[derive(serde::Deserialize)]
struct RawConfig {
    source: std::path::PathBuf,
    destination: std::path::PathBuf,
    dry_run: Option<bool>,
}

pub struct SyncConfig {
    pub source: std::path::PathBuf,
    pub destination: std::path::PathBuf,
    pub dry_run: bool,
}

impl TryFrom<RawConfig> for SyncConfig {
    type Error = LoadConfigError;

    fn try_from(raw: RawConfig) -> Result<Self, Self::Error> {
        if raw.source.as_os_str().is_empty() || raw.destination.as_os_str().is_empty() {
            return Err(LoadConfigError::MissingPath);
        }

        Ok(Self {
            source: raw.source,
            destination: raw.destination,
            dry_run: raw.dry_run.unwrap_or(false),
        })
    }
}
```

</typed_config_with_boundary_validation>

<typed_errors>

```rust
#[derive(thiserror::Error, Debug)]
pub enum LoadConfigError {
    #[error("missing path in configuration")]
    MissingPath,
    #[error("failed to parse config file")]
    Parse(#[source] toml::de::Error),
}
```

Use `thiserror` at reusable boundaries and reserve `anyhow` for outer orchestration where callers do not depend on structured variants.
</typed_errors>

<async_service_boundary>

```rust
#[async_trait::async_trait]
pub trait UserStore {
    async fn load(&self, id: UserId) -> Result<User, LoadUserError>;
}

pub struct UserService<S> {
    store: S,
}

impl<S: UserStore> UserService<S> {
    pub async fn fetch(&self, id: UserId) -> Result<UserDto, FetchUserError> {
        let user = self.store.load(id).await?;
        Ok(UserDto::from(user))
    }
}
```

Keep the async boundary at the collaborator seam and keep the service body free of transport details.
</async_service_boundary>
