# Issues: Verification Enabler

## Downstream enforcement for `[audit]` decision-rule modes (deferred)

`spx/14-verification.pdr.md` carries four `[audit]` rules under `## Verification` / `### Audit` (an activity declares its type and purpose; a type's verdict mode is fixed by definition; a model never judges a deterministic type's verdict; the type set and the two verdict modes are closed). `spx/21-spec-tree.enabler/32-decisions.enabler/decisions.md` asserts that a decision record's rules flow into spec assertions that enforce them somewhere in the governed subtree — but an `[audit]`-mode rule is enforced by an auditing skill's judgment, not by a `[test]`/`[eval]` spec assertion, and no node spec yet enforces these four rules individually.

Establish how `[audit]` decision-rule modes are enforced downstream: either author node-spec `[audit]` assertions an auditing skill checks against each rule, or refine the `decisions.md` flow rule so it recognizes audit/eval enforcement for `[audit]`/`[eval]` modes. This is a methodology question broader than the verification-taxonomy change that introduced the modes.

Surfaced by the local `reviewing-changes` review on PR #103.
