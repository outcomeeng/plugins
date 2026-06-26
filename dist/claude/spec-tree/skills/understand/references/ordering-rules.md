<overview>
Numeric prefixes drive deterministic context loading within each directory. This reference explains how an existing tree is read. It does not decide new structure; use `/decompose` for child boundaries, ordering evidence, and index assignment.
</overview>

<context_loading_rule>

For a target node, lower-index siblings are read before the target because the existing tree declares them as constraining context. Same-index siblings are listed but not read as constraints. Higher-index siblings are not read because they do not constrain the target's context.

```text
15-decision.adr.md        # Read for targets at 16+
21-infra.enabler/         # Read for targets at 22+
32-auth.outcome/          # Same-index peer of billing
32-billing.outcome/       # Same-index peer of auth
43-integration.outcome/   # Reads 15, 21, and both 32 siblings
```

</context_loading_rule>

<assignment_is_the_inverse>

This reference explains how an existing tree is read: the index a sibling already carries decides whether `/contextualize` reads it as a constraint. Assigning an index to a new child is the inverse operation, owned by `/decompose`: choosing a child's index chooses what every later context load treats as constraining for it. A higher index than a sibling declares that sibling constraining context for the new child; the same index declares an independent peer. A loaded `<SPEC_TREE_FOUNDATION>` marker records that this reading rule was read once — it neither assigns indices nor stands in for `/decompose` applying the rule in reverse when it chooses one.

</assignment_is_the_inverse>

<decision_records>

ADRs and PDRs share the same numeric namespace as sibling nodes. A decision record at a lower index constrains higher-index siblings and their descendants. Decision records at the same index do not constrain each other through index order.

</decision_records>

<full_paths>

Always refer to nodes, ADRs, and PDRs with their full path from `spx/`. Never use a bare node name, bare decision filename, or numeric prefix by itself.

Bare references are ambiguous because numeric prefixes are sibling-local:

```text
Wrong: 32-parser.enabler
Right: spx/55-example.enabler/12-infra.enabler/32-parser.enabler

Wrong: 15-build.adr.md
Right: spx/55-example.enabler/15-build.adr.md
```

This rule applies most strongly to ADRs and PDRs. A decision file cannot be found from `15-build.adr.md` alone because any directory can contain its own `15-build.adr.md`.

</full_paths>

<same_index>

Items with the same index are unordered relative to each other for context loading. `/contextualize` lists same-index siblings in the manifest and does not read them as constraining context.

</same_index>

<higher_index>

Higher-index siblings may depend on the target, but they do not constrain the target. `/contextualize` lists them in the manifest and does not read their specs while loading target context.

</higher_index>

<unified_number_space>

Within each directory, all indexed artifacts share one number space: nodes, ADRs, and PDRs. The numeric prefix sorts the artifact; the suffix identifies the artifact type.

```text
15-auth-strategy.adr.md
15-pricing-model.pdr.md
21-test-harness.enabler/
32-user-auth.outcome/
```

</unified_number_space>

<scope>

Numeric prefixes are unique only among siblings within the same directory. Different directories can reuse the same numbers.

```text
21-infra.enabler/21-setup.enabler/
21-infra.enabler/32-config.enabler/
32-feature.outcome/21-sub-setup.enabler/
```

Always use full paths when referencing nodes. `32-parser.enabler` is ambiguous; `spx/55-example.enabler/12-infra.enabler/32-parser.enabler` is not.

</scope>
