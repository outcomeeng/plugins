<overview>
Some surprises in a Go review are legitimate once the boundary and invariant are clear.
</overview>

<non_findings>

1. Interface-mandated parameters that one implementation does not need, named `_`
2. A `context.Context` parameter accepted and passed straight through to the one blocking call
3. `exec.Command` inside a CLI or adapter layer where the program and arguments come from a typed, exported command vocabulary
4. A narrow `unsafe` conversion with a precise `SAFETY:` comment tied to a real invariant
5. `fmt.Errorf` without `%w` at the outermost presentation boundary, where the wrapped chain is deliberately cut for the user
6. A package-level `var` holding an immutable value such as a compiled regular expression or a `sync.OnceValue`

</non_findings>

<real_findings>

- Claude cannot explain the boundary or invariant in one sentence
- `unsafe` exists only to sidestep type design
- shell commands are assembled from user-controlled string fragments
- errors are discarded with `_` or returned unwrapped across a domain boundary
- a goroutine's owner or exit condition cannot be named
- generic error handling leaks into reusable library or domain code

</real_findings>

<valid_pattern_response>
When a suspicious pattern is valid:

1. name the boundary or invariant that makes it valid
2. state why that context changes the verdict
3. verify the explanation matches the actual code, not a hoped-for future state

</valid_pattern_response>

<example>
    type Handler interface {
        Handle(ctx context.Context, cmd Command, rc *RequestContext) (Response, error)
    }

    type PingHandler struct{}

    func (PingHandler) Handle(_ context.Context, cmd Command, _ *RequestContext) (Response, error) {
        if cmd != CommandPing {
            return Response{}, ErrUnsupported
        }
        return Response{Kind: ResponsePong}, nil
    }

The blank parameters are acceptable here because the interface requires a uniform signature and the unused inputs are explicit.
</example>
