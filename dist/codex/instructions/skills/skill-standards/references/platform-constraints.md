<overview>

Platform-specific constraints that affect skill authoring. The nested-code-fence constraint applies to every target; runtime-only sections render only where they apply.

</overview>

<nested_code_fences>

**Single-nested 3-backtick inside a 4-backtick fence is fine.**

`````text
````markdown
<example>
```yaml
name: demo
```
</example>
````
`````

**Multi-nested breaks.** Never nest multiple 3-backtick blocks inside a single 4-backtick fence — `markup_fmt` (dprint) prematurely closes the outer fence after the first inner fence, destroying all subsequent content.

**Workaround:** to show a markdown template that itself contains multiple code blocks, move the template into `references/` and point to it:

```markdown
<example_review>
Read `${SKILL_DIR}/references/example-audit.md` for a complete example.
</example_review>
```

</nested_code_fences>
