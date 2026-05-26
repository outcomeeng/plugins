# Example Architecture Review

This is a complete REJECTED review showing the concern table and the level of detail expected from `auditing-rust-architecture`.

# ARCHITECTURE REVIEW

**Decision:** REJECTED

## Verdict

| # | Concern               | Status | Detail                                      |
| - | --------------------- | ------ | ------------------------------------------- |
| 1 | Section structure     | REJECT | Contains phantom "Testing Strategy" section |
| 2 | Testability in Compl. | REJECT | Compliance omits DI and no-mocking rules    |
| 3 | Atemporal voice       | REJECT | Context narrates present code state         |
| 4 | Mocking prohibition   | REJECT | Decision prescribes `mockall` at the seam   |
| 5 | Level accuracy        | PASS   | Level references are consistent             |
| 6 | Anti-patterns         | REJECT | Level assignment table moved into ADR       |
| 7 | Ancestor consistency  | PASS   | No contradiction with ancestor decisions    |

---

## Violations

### Mocking At The Boundary

**Where:** Decision section, "Use `mockall` for all command runner tests"
**Concern:** Mocking prohibition
**Why this fails:** The ADR turns generated mocks into the intended seam. The Rust architecture standard requires dependency injection with real traits or function seams so tests preserve coupling to the boundary.

**Correct approach:**

```rust
pub trait CommandRunner {
    fn run(&self, program: &str, args: &[&str]) -> Result<CommandOutput, CommandError>;
}

pub fn build_site<R: CommandRunner>(
    config: &BuildConfig,
    runner: &R,
) -> Result<BuildResult, BuildError> {
    runner.run("hugo", &["--destination", config.output_dir.as_str()])?;
    Ok(BuildResult::success())
}
```

---

### Phantom Testing Strategy Section

**Where:** `## Testing Strategy` with a level assignment table
**Concern:** Section structure, Anti-patterns
**Why this fails:** The ADR template has no Testing Strategy section. Level assignments are a downstream `/testing` concern. The ADR should define the seam that makes Level 1 or Level 2 verification possible, then leave the final level choice to the testing workflow.

**Correct approach:**

```markdown
## Compliance

### MUST

- External tool invocations accept an injected runner trait or function parameter -- preserves isolated verification of command logic ([review])

### NEVER

- `mockall`, `faux`, or generated mocks as the primary strategy for architectural seams ([review])
```

---

### Missing Testability Constraints

**Where:** Compliance section
**Concern:** Testability in Compliance
**Why this fails:** The ADR governs build orchestration, but Compliance has no rules that force observable seams. Removing the phantom section is insufficient unless those constraints move into MUST and NEVER rules.

---

### Temporal Context Language

**Where:** Context section, "The current `build.rs` wrapper shells out directly..."
**Concern:** Atemporal voice
**Why this fails:** The sentence describes a code snapshot that expires. An ADR states enduring architecture, not the condition of one file on one date.

**Correct approach:**

```markdown
**Technical constraints:** Build orchestration invokes external binaries. Injected runner seams isolate command construction from process execution.
```

---

## Required Changes

1. Remove the Testing Strategy section and fold testability into Compliance
2. Replace `mockall` language with injected trait or function seams
3. Rewrite Context in atemporal voice
4. Add MUST and NEVER rules that make the intended test shape observable

---

## References

- /standardizing-rust-architecture: `<adr_sections>`
- /standardizing-rust-architecture: `<testability_in_compliance>`
- /standardizing-rust-architecture: `<atemporal_voice>`
- /standardizing-rust-architecture: `<di_patterns>`

---

Revise and resubmit.
