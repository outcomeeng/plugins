---
name: migrate-3-to-4
description: >-
  ALWAYS invoke this skill when converting the decision citations of a 3.x Spec Tree product to the tree-absolute Markdown links the 4.0 methodology requires, or when `spx` rejects a decision cited as a code span, a bare path, or a node-local link. NEVER convert those citations by hand or by search and replace.
allowed-tools: Read, Bash(git rev-parse:*), Bash(git status:*), Bash(python3:*)
---

<objective>

Every decision citation in the product's `spx/` tree written as a Markdown inline link whose text and href are the full path from `spx/`, with each citation the conversion cannot convert listed in a report and left unchanged.

</objective>

<workflow>

<step name="locate_root">

The product root is the directory that holds `spx/`. Resolve it from the repository:

```bash
git rev-parse --show-toplevel
```

When that directory holds no `spx/`, report it and stop.

</step>

<step name="convert">

Run the conversion with the product root as its one parameter:

```bash
python3 "${SKILL_DIR}/scripts/convert_links.py" <product-root>
```

The conversion rewrites every decision citation in the Markdown files beneath `<product-root>/spx/` to a Markdown inline link whose text and href are the full path from `spx/`. It gives every `../` link, leading-slash link, link out of its node, and link into a descendant node a tree-absolute href, and it leaves fenced code blocks untouched. It prints one JSON document:

```text
{"schemaVersion": 1, "rewritten": [...], "unconvertible": [...]}
```

`rewritten` lists each changed file as a path from the product root. `unconvertible` lists each citation the conversion cannot convert, with its `file`, `line`, `form`, and `target`; the run continues past each one. Exit status 0 means no citation remains unconvertible. Exit status 3 means the report lists at least one, after the conversion rewrote every other citation. Exit status 1 means the root holds no `spx/` or another error stopped the run. Report any other exit status verbatim as an error and stop.

</step>

<step name="report">

Present the complete report: the rewritten files, then every unconvertible citation with its file, line, form, and target. The form `text-decision` is a decision path written as bare prose; the form `broken` is a target that does not exist. Leave each reported citation unchanged for the operator. After exit status 3, state that the operator resolves each reported citation and runs the conversion again, and that a second run changes no file the first run converted.

</step>

<step name="review">

Show which files the run changed:

```bash
git status --short
```

</step>

</workflow>

<constraints>

- NEVER rewrite a reported citation by reading its surrounding prose or by guessing its target; the operator names the intended target.
- NEVER convert more than decision citations: directory suffixes and spec file names stay as they are.
- NEVER run the conversion on a directory other than the repository root.

</constraints>

<success_criteria>

- The conversion exited 0 or 3 and printed its JSON document; any other exit status was reported verbatim and ended the run.
- Every rewritten file and every unconvertible citation, with its file, line, form, and target, appears in the presented report.
- Every citation the report lists as unconvertible stands unchanged in its file.
- A second run over the converted tree changes no file.

</success_criteria>
