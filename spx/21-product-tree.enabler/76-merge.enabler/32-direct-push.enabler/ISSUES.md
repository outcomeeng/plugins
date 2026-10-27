# Issues: Direct-push transport

Known defects, contradictions and gaps in this node. Coordination note; not spec truth.

## The direct-push gate bindings have no eval coverage

The node's `[audit]` assertions are its Declared-state evidence. The variant-1 execution path, the push of the verified changeset to the remote default branch, now exists in the `/merge` skill (`<direct_push_lifecycle>`), so evals can replay the direct-push gate bindings: the review predicate bound to the local review, no pull request, no CI wait. The GitHub-PR transport has gate evals; this transport has none.

**Settlement condition.** `[eval]` coverage mirrors the GitHub-PR transport gate evals for the direct-push bindings.

## The local-trunk-checkout variant has no execution or worktree-safety model

The transport declares a second variant: merge into a local default-branch worktree, then push. It depends on the local trunk being available, and no model of its execution or its worktree safety exists.

**Settlement condition.** A consumer requires the variant, and a decision then records its execution and worktree-safety model.
