<contents>

- `<overview>` — when this pass runs and what a violation means
- `<enumerate_sites>` — collect every `unsafe` and cgo site first
- `<per_conversion_checks>` — SAFETY comment, invariant, hazard categories
- `<per_cgo_boundary_checks>` — Go types, memory ownership, panics, threads
- `<verdict_row>` — how the pass folds into the verdict

</contents>

<overview>
Soundness pass for `unsafe` conversions and cgo boundaries — the invariant violations, lifetime bugs, and C memory faults the compiler cannot catch. Claude runs this pass as part of `/audit-go-code` whenever the scope contains `unsafe.Pointer`, `unsafe.Slice`, `unsafe.String`, `unsafe.SliceData`, `unsafe.StringData`, `import "C"`, or an `//export` directive; a scope with no such sites skips it.

A single soundness violation rejects the audit. Claude never approves an `unsafe` conversion that lacks a documented invariant, and never accepts a workaround that preserves the conversion behind weaker documentation.
</overview>

<enumerate_sites>
Collect every site before judging any of them:

```bash
grep -rn "unsafe\.\|import \"C\"\|//export \|C\.[A-Za-z_]" <scope> --include="*.go"
```

Count each `unsafe` conversion, each cgo call, and each `//export` boundary. The verdict's `unsafe-soundness` row reports the totals.
</enumerate_sites>

<per_conversion_checks>
For each `unsafe` conversion:

1. **SAFETY comment present.** A `// SAFETY:` comment sits immediately above the conversion, tied to the actual invariant it relies on. Absence is a violation — reject.
2. **Invariant holds.** Read the surrounding code and cross-reference the documented invariant against the hazard categories below. The comment must name the real precondition, not restate the operation.
3. **Hazard categories.** Check the conversion against each category that applies; the first violated category rejects the site.

| Category | Rule prefix | Hazard                                                                                                  |
| -------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| Lifetime | `ptr-*`     | The referent outlives every use; no pointer derived from a value the garbage collector may move or free |
| Aliasing | `ptr-*`     | A string produced by `unsafe.String` is never mutated through the original bytes                        |
| Layout   | `ptr-*`     | Struct layout assumptions match the Go spec and are not dependent on field reordering                   |
| Validity | `ptr-*`     | No pointer arithmetic outside the six `unsafe.Pointer` patterns `go vet` accepts                        |

</per_conversion_checks>

<per_cgo_boundary_checks>
For each cgo call and `//export` function:

1. **Go types at the boundary.** C values convert to Go types in the same package; no `C.*` type escapes the package's exported API.
2. **Memory ownership.** Every `C.malloc` has a matching `C.free` in the same package on every exit path, and Go memory passed to C follows the cgo pointer-passing rules — no Go pointer stored by C, no Go memory containing Go pointers passed across.
3. **Panic containment.** An `//export` function never panics into C; it recovers and returns an error code.
4. **Thread safety.** C callbacks into Go document which goroutine or thread runs them and hold no Go lock across the C call.

</per_cgo_boundary_checks>

<verdict_row>
The audit folds an `unsafe-soundness` row into the JSON verdict: `PASS` when every site is sound, `FAIL` on any violation, and `NOT_APPLICABLE` when the scope has no unsafe or cgo sites. A `NOT_APPLICABLE` row carries `explanation` naming why the concern does not apply. Findings use `blocking` or `debt` severity and name the site, `file:line`, rule prefix, failed invariant, and observed-versus-expected evidence.
</verdict_row>
