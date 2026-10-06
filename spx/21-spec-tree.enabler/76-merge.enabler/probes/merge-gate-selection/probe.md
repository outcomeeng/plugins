# Merge gate selection

The protocol lives at `probes/merge-gate-selection/probe.md`, the target of the merge node's `[probe]` assertion on the merge composition. Working runs stay in an ignored `runs/` inside this directory; the attested run retains its transcript beside this file.

## Intent

The operator intends `/merge` to dispatch an evidence Auditor or the local review only where the merge composition selects it from the least malleable node the changeset touches. The uncertainty is whether a session that reads only the shipped skill text reaches that selection: a skill whose wording still reads as "review every changeset" passes every deterministic check and keeps dispatching Verifiers the methodology does not require. Only a session reading the text and naming its dispatches settles it.

## Environment and preconditions

- The changeset is committed, and `just build-skills` has regenerated `dist/claude/` from it.
- A scratch directory created with `mktemp -d` holds exactly three files: `dist/claude/spec-tree/skills/merge/SKILL.md` copied as `merge-SKILL.md`, `dist/claude/spec-tree/skills/merging-standards/references/merge-policy.md` copied as `merge-policy.md`, and `fixtures.md` from this directory.
- The session runs as a headless Claude Code process in that scratch directory, restricted to file-reading tools, with skills, MCP servers, and user, project, and local settings disabled, so it carries none of the Author's context and reaches no other source.
- No `spec-tree:probe` skill exists in the runtime catalog, and the subagent tool would start a session inside the Author's harness context. A separate headless process in a directory holding only the three files is the launch that gives the session no Author context and no repository access.

## Protocol

1. Create the scratch directory and copy the three files into it.
2. In that directory, run `claude -p --restricted --strict-mcp-config --disable-slash-commands --tools Read,Glob,Grep --no-session-persistence --output-format stream-json --verbose` with the contents of `prompt.md` on stdin, and capture standard output as the transcript.
3. Read the final JSON object of the transcript and compare it with the expected selection:
   - Fixture 1, every touched node `spec`-malleable: no Verifier; the deterministic commands only.
   - Fixture 2, one node whose spec declares no `malleability` field beside a `spec`-malleable node: `test-evidence-auditor` once, for `spx/30-ledger.capability` alone, then `changes-reviewer`; no evidence audit for the `spec`-malleable `spx/20-billing.capability`, and no `eval-evidence-auditor`, because no eval artifact changes.
   - Fixture 3, no `spx/` directory: no Verifier; the repository's declared verify command `make verify`.
   - Fixture 4, one `verification`-malleable node with a changed linked test: `changes-reviewer` alone; no evidence Auditor, because no touched node is `implementation`-malleable.
   - Fixture 5, the root product spec changes beside a `spec`-malleable node: `changes-reviewer`, which a product-spec change requires whatever the nodes select; no evidence Auditor.
   - Fixture 6, an outcome record of a `spec`-malleable node changes: `changes-reviewer`, which an outcome-record change requires; no evidence Auditor.
4. Copy the transcript into this directory as `transcript.jsonl` and record the run below.

## Attested run

- Date: 2026-10-06, against the committed head `2642503aa3ea4c0f1a892f7d5d8b974638934064` with `dist/claude/` rebuilt from it.
- Observations: the session read the three files and no other source, then reported these selections:
  - Fixture 1: no Verifier, the touched-scope validation and testing commands only; it named `billing.spec.md` an output spec, not the product spec.
  - Fixture 2: `test-evidence-auditor` once, for `spx/30-ledger.capability`, then `changes-reviewer`, with no evidence audit for `spx/20-billing.capability` and no `eval-evidence-auditor`.
  - Fixture 3: no Verifier, Validate and `make verify`, citing the absent `spx/` directory.
- An earlier working run selected `changes-reviewer` for fixture 1, reading the billing node's spec as a product spec, and audited the `spec`-malleable billing node in fixture 2. The skill text was repaired to define a product spec as the spec of a `.product` node and to audit only `implementation`-malleable nodes' evidence; a second run on head `243b164336e0ce8bfa15b3c57d8509e167bb4216` passed, and later skill edits made this run necessary.
- Artifacts: [transcript](transcript.jsonl), [fixtures](fixtures.md), [prompt](prompt.md)

## Verdict

Passing: every fixture's selection matches the expected selection in the protocol, so a session reading only the shipped `/merge` skill and its merge policy dispatches the Verifiers the merge composition selects and no others.

## Limitations

The protocol exercises the GitHub-PR path's verification predicates as the skill text states them, through a session that reads and reports rather than one that dispatches real Verifiers against a live repository. Direct-push publication and `MERGE_READINESS` are not exercised.
