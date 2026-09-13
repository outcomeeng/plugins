<contents>

- Native wrapper example
- Complete profile configurations
- Authoring and placement
- Capability inspection

</contents>

<native_wrapper_example>

Use a thin wrapper when a skill owns the behavior. This example delegates spec
auditing and preserves the skill's result contract.

```markdown
---
name: spec-auditor
description: ALWAYS invoke when the governing skill requests an audit of one spec node.
model: "opus"
effort: "medium"
skills: spec-tree:audit-specs
---

<workflow>
Invoke spec-tree:audit-specs with the supplied target.
Return the skill's complete structured verdict.
</workflow>
```

Resolve definition and dispatch names through the owning product's distribution mapping.
The example uses the native definition name for this harness.

</native_wrapper_example>

<complete_profile_configurations>

These complete blocks come from the same configuration owner as the native definitions.
Use the profile selected by the governing requirement.

Standard:

```yaml
model: "opus"
effort: "medium"
```

Strong:

```yaml
model: "opus"
effort: "high"
```

Fast:

```yaml
model: "haiku"
```

</complete_profile_configurations>

<authoring_and_placement>

1. Identify whether the target is authored marketplace source or a product-owned native definition.
2. In marketplace source, select a profile and run the product's build command.
3. Inspect the emitted native definition and the mapping from authored name to dispatch name.
4. Use the owning installation workflow for marketplace definitions, retaining its scope and ownership evidence.
5. For a product-owned native definition, use the confirmed destination and complete profile block.
6. Pass the exact saved artifact to the owning verification workflow.

</authoring_and_placement>

<capability_inspection>

Read the invoked skill's actual steps before choosing operational settings.
Compare every external access with the role's tool permissions and sandbox.
A setting that merely mentions a tool in prompt text cannot establish an enforced restriction.
For skill-backed definitions, inspect how the native harness exposes the named skill;
a configuration field's presence alone is insufficient evidence that its behavior loaded.

</capability_inspection>
