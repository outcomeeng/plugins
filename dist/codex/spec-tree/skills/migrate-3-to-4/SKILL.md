---
name: migrate-3-to-4
description: >-
  ALWAYS invoke this skill when converting the decision citations of a 3.x Spec Tree product to the tree-absolute Markdown links the 4.0 methodology requires, or when `spx` rejects a decision cited as a code span, a bare path, or a node-local link. NEVER convert those citations by hand or by search and replace.
allowed-tools: Read, Bash(git rev-parse:*), Bash(git status:*), Bash(python3 "${SKILL_DIR}/scripts/convert_links.py":*)
---

<objective>

Every decision citation in the product's `spx/` tree written as a Markdown link with a tree-absolute href, every `../`, leading-slash, out-of-node, and descendant-node link carrying a tree-absolute href, and each citation the conversion cannot convert listed in a report and left unchanged.

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

The conversion rewrites the Markdown files beneath `<product-root>/spx/`:

- A code span holding a decision path becomes a Markdown inline link whose text and href are the full path from `spx/`.
- A link to a decision record, including a decision of the citing node, gets the full path from `spx/` as its href; its text becomes that path only when its text was the path it replaces.
- A link that climbs with `../`, leads with a slash, leaves its node, or reaches into a descendant node gets a tree-absolute href; its text stays.
- A reference-style definition follows the rules of an inline link and stays a reference definition.
- Fenced code blocks stay untouched.

It prints one JSON document:

```text
{"schemaVersion": 1, "rewritten": [...], "unconvertible": [...]}
```

`rewritten` lists each changed file as a path from the product root. `unconvertible` lists each citation the conversion cannot convert, with its `file`, `line`, `form`, and `target`; the run continues past each one. Exit status 0 means no citation remains unconvertible. Exit status 3 means the report lists at least one, after the conversion rewrote every other citation.

Exit status 1 means the root holds no `spx/` or another error stopped the run, and the conversion may already have rewritten files before it stopped. Report the error message, which names the files already rewritten, report those files as a partial rewrite, and stop. Report any other exit status verbatim as an error and stop.

</step>

<step name="verify">

Run the same command a second time. Its `rewritten` list is empty and its exit status equals the first run's; report any difference as an error and stop.

</step>

<step name="report">

Present the complete report of the first run: the rewritten files, then every unconvertible citation with its file, line, form, and target. The form `text-decision` is a decision path written as bare prose or held in a code span beside other text; the form `broken` is a target that does not exist. Leave each reported citation unchanged for the operator. After exit status 3, state that the operator resolves each reported citation and runs the conversion again.

</step>

<step name="review">

Show the working tree's changes; the files the conversion rewrote are the ones the first run's `rewritten` list names:

```bash
git status --short
```

</step>

</workflow>

<testing>

The conversion ran over fixture trees before release, with these recorded results:

- A tree holding every citation form — a code span, a link to a decision of the citing node, `../`, leading-slash, out-of-node and descendant-node links, a reference definition, and a fenced block — converts to the expected tree byte for byte, `rewritten` lists exactly the changed files, and the run exits 3 with the expected report.
- A tree whose citations all convert prints no report line and exits 0.
- A second run over a converted tree rewrites nothing and prints the same report.
- A root without `spx/` exits 1 and changes no file.
- A tree holding an undecodable file exits 1, names the file, and lists the files already rewritten.
- A path with a template placeholder stays unchanged and unreported; a bare prose path and a decision path a code span holds beside other text each print as `text-decision` and stay unchanged.

</testing>

<constraints>

- NEVER rewrite a reported citation by reading its surrounding prose or by guessing its target; the operator names the intended target.
- NEVER rename a directory or a spec file: directory suffixes and spec file names stay as they are.
- NEVER run the conversion on a directory other than the repository root.

</constraints>

<success_criteria>

- The first run exited 0 or 3 and printed its JSON document; any other exit status was reported verbatim and ended the run.
- The second run's `rewritten` list is empty and its exit status equals the first run's.
- Every rewritten file and every unconvertible citation, with its file, line, form, and target, appears in the presented report.
- Every citation the report lists as unconvertible stands unchanged in its file.
- A decision path the run leaves as text outside a link and a fenced block, and carrying no template placeholder, appears in the report as `text-decision` or `broken`, so a run that exits 0 leaves none.

</success_criteria>
