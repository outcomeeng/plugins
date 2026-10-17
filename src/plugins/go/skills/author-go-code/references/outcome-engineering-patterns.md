<contents>

- `<overview>` — what these patterns cover
- `<external_command_boundary>` — interface-typed runner at the process edge
- `<resource_cleanup>` — release through `Close` and `defer`
- `<typed_config_with_boundary_validation>` — parse once at the boundary
- `<typed_errors>` — errors the caller can match with `errors.Is` and `errors.As`
- `<context_bound_service_boundary>` — service seams that honor cancellation

</contents>

<overview>
These patterns capture Go-native seams and boundary shapes that keep implementation code testable and explicit.
</overview>

<external_command_boundary>

```go
type CommandRunner interface {
    Run(ctx context.Context, program string, args ...string) (CommandOutput, error)
}

type SystemCommandRunner struct{}

func (SystemCommandRunner) Run(ctx context.Context, program string, args ...string) (CommandOutput, error) {
    out, err := exec.CommandContext(ctx, program, args...).CombinedOutput()
    return CommandOutput{Combined: out}, err
}

func BuildSyncArgs(cfg *SyncConfig) []string {
    return []string{"--delete", cfg.Source, cfg.Destination}
}

func SyncRepo(ctx context.Context, cfg *SyncConfig, runner CommandRunner) (SyncResult, error) {
    if _, err := runner.Run(ctx, "rsync", BuildSyncArgs(cfg)...); err != nil {
        return SyncResult{}, fmt.Errorf("sync repo: %w", err)
    }
    return SyncResult{Success: true}, nil
}
```

</external_command_boundary>

<resource_cleanup>

```go
type Workspace struct {
    root string
}

func NewWorkspace() (*Workspace, error) {
    root, err := os.MkdirTemp("", "workspace-")
    if err != nil {
        return nil, fmt.Errorf("create workspace: %w", err)
    }
    return &Workspace{root: root}, nil
}

func (w *Workspace) Path() string { return w.root }

func (w *Workspace) Close() error { return os.RemoveAll(w.root) }
```

Callers `defer ws.Close()` immediately after a successful constructor. Prefer a `Close` method the caller defers over cleanup hidden in a finalizer.
</resource_cleanup>

<typed_config_with_boundary_validation>

```go
type rawConfig struct {
    Source      string `json:"source"`
    Destination string `json:"destination"`
    DryRun      *bool  `json:"dry_run"`
}

type SyncConfig struct {
    Source      string
    Destination string
    DryRun      bool
}

func parseConfig(raw rawConfig) (SyncConfig, error) {
    if raw.Source == "" || raw.Destination == "" {
        return SyncConfig{}, ErrMissingPath
    }
    dryRun := raw.DryRun != nil && *raw.DryRun
    return SyncConfig{Source: raw.Source, Destination: raw.Destination, DryRun: dryRun}, nil
}
```

</typed_config_with_boundary_validation>

<typed_errors>

```go
var ErrMissingPath = errors.New("missing path in configuration")

type ParseError struct {
    Path string
    Err  error
}

func (e *ParseError) Error() string { return "parse " + e.Path + ": " + e.Err.Error() }
func (e *ParseError) Unwrap() error { return e.Err }
```

Use sentinel errors for conditions callers branch on and error structs for conditions that carry data. Wrap with `%w` at every boundary so `errors.Is` and `errors.As` still resolve.
</typed_errors>

<context_bound_service_boundary>

```go
type UserStore interface {
    Load(ctx context.Context, id UserID) (User, error)
}

type UserService struct {
    store UserStore
}

func NewUserService(store UserStore) *UserService { return &UserService{store: store} }

func (s *UserService) Fetch(ctx context.Context, id UserID) (UserDTO, error) {
    user, err := s.store.Load(ctx, id)
    if err != nil {
        return UserDTO{}, fmt.Errorf("fetch user %d: %w", id, err)
    }
    return dtoFrom(user), nil
}
```

Keep the boundary at the collaborator seam, propagate the context, and keep the service body free of transport details.
</context_bound_service_boundary>
