# Unsafe and FFI Soundness Audit

Soundness audit for `unsafe` blocks and FFI boundaries — the undefined behavior, invariant violations, and FFI contract breaks the compiler cannot catch. Claude runs this pass as part of `/audit-rust` whenever the scope contains an `unsafe` block, `unsafe fn`, `unsafe impl`, or `extern "C"` boundary; a scope with no such sites skips it.

A single soundness violation rejects the audit. Claude never approves unsafe code that lacks a documented safety invariant, and never accepts a workaround that preserves unsafe code behind weaker documentation.

## Enumerate unsafe sites

Collect every site before judging any of them:

```bash
grep -rn "unsafe" <scope> --include="*.rs"
```

Count each `unsafe` block, `unsafe fn`, `unsafe impl`, and `extern "C"` / `#[no_mangle]` boundary. The verdict's `unsafe-soundness` row reports the totals.

## Per-block checks

For each `unsafe` block or `unsafe fn`:

1. **SAFETY comment present.** A `// SAFETY:` comment sits immediately above or inside the block, tied to the actual invariant the block relies on. Absence is a violation — reject.
2. **Invariant holds.** Read the full block body and cross-reference the documented invariant against the soundness-hazard categories below. The comment must name the real precondition, not restate the operation.
3. **Hazard categories.** Check the block against each category that applies; the first violated category rejects the block.

| Category  | Rule prefix | Hazard                                                                                        |
| --------- | ----------- | --------------------------------------------------------------------------------------------- |
| Pointers  | `ptr-*`     | Pointer validity, alignment, non-null, valid-for-N-bytes, no use-after-free                   |
| Aliasing  | `ptr-*`     | No two live `&mut`, no `&`/`&mut` overlap, provenance preserved                               |
| Lifetimes | `ptr-*`     | No lifetime extension past the referent, no dangling reference synthesized from a raw pointer |
| Validity  | `ptr-*`     | No invalid bit patterns, `MaybeUninit` discipline, no reads of uninitialized memory           |
| FFI       | `ffi-*`     | ABI-stable types only, panic unwinding contained, documented nullability and ownership        |
| Send/Sync | `ffi-*`     | `unsafe impl Send`/`Sync` justified by a real thread-safety argument, not convenience         |

Record each violation as a finding with `file`, `line`, the rule prefix, and the exact invariant that fails.

## Per-FFI-boundary checks

For each `extern "C"` function and `#[no_mangle]`:

1. **ABI-stable types only.** No `String`, `Vec`, trait object, or other non-`#[repr(C)]` Rust type crosses the boundary. Pass `*const`/`*mut` and `#[repr(C)]` types.
2. **Panic containment.** Unwinding cannot cross the boundary — the body is wrapped in `catch_unwind`, or panics abort. An `extern "C"` function that can unwind into foreign code is a violation.
3. **Pointer contracts.** Every pointer parameter documents nullability and ownership (who allocates, who frees).

## Verdict row

The audit folds an `unsafe-soundness` row into the JSON verdict (`PASS` when every site is sound, `FAIL` on any violation, `UNKNOWN`/`N/A` when the scope has no unsafe sites). Findings carry `severity: "REJECT"` and name the block, `file:line`, rule prefix, and failed invariant.
