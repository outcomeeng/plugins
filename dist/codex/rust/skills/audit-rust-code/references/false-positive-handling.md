<overview>
Some surprises in a Rust review are legitimate once the boundary and invariant are clear.
</overview>

<non_findings>

1. Trait-mandated parameters that one implementation does not need
2. `Arc::clone`, `Bytes::clone`, or `Cow` usage that clearly expresses shared ownership rather than borrow-checker avoidance
3. `std::process::Command` inside a CLI or adapter layer where the program and arguments are typed or hardcoded
4. A narrow `unsafe` block with a precise `SAFETY:` comment tied to a real invariant
5. `anyhow` at the outer application boundary while domain and library layers stay typed

</non_findings>

<real_findings>

- the reviewer cannot explain the boundary or invariant in one sentence
- `unsafe` exists only to sidestep ownership design
- shell commands are assembled from user-controlled string fragments
- `clone()` appears repeatedly with no ownership reason
- generic error handling leaks into reusable library or domain code

</real_findings>

<reviewer_response_pattern>
When a suspicious pattern is valid:

1. name the boundary or invariant that makes it valid
2. state why that context changes the verdict
3. verify the explanation matches the actual code, not a hoped-for future state

</reviewer_response_pattern>

<example>
```rust
trait Handler {
    fn handle(&self, command: &Command, ctx: &RequestContext) -> Result<Response, Error>;
}

struct PingHandler;

impl Handler for PingHandler {
fn handle(&self, command: &Command, _ctx: &RequestContext) -> Result<Response, Error> {
match command {
Command::Ping => Ok(Response::Pong),
_ => Err(Error::Unsupported),
}
}
}

```
`_ctx` is acceptable here because the trait requires a uniform interface and the unused parameter is explicit.
</example>
```
