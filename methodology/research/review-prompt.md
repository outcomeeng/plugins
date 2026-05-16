# PR Review Prompt

Review one pull request and post one comment with the review. Follow the steps in order. The environment constraints in the "Environment" section below are real — every constraint listed there cost a previous run between 5 and 20 wasted tool calls.

## Inputs

- `REPO` — `<owner>/<repo>` (e.g. `leoherds/leoherd`)
- `PR_NUMBER` — integer

## Steps

1. **Load repository conventions.** Read `REVIEW.md` and `CLAUDE.md` from the repository root if present. Resolve the finding-classification taxonomy and comment shape in this order: (a) `REVIEW.md` if present, (b) a taxonomy defined in `CLAUDE.md` if `REVIEW.md` is absent, (c) the defaults in the "Review shape" section below if neither file specifies one. Always read `CLAUDE.md` for project conventions independent of where the taxonomy comes from.

2. **Gather PR context.** Run:

   ```bash
   gh pr view "$PR_NUMBER" --repo "$REPO" --json number,title,body,author,baseRefName,headRefName,additions,deletions,changedFiles
   gh pr diff "$PR_NUMBER" --repo "$REPO" | sed -n '1,1000p'
   ```

   For longer diffs, keep using the same `sed` form for every chunk — `| sed -n '1001,2000p'`, `| sed -n '2001,3000p'`, and so on. To list affected files first, pipe to `| grep '^diff --git'`; to read around one file, pipe to `| sed -n '/^diff --git a\/path\/to\/file/,/^diff --git /p'`.

   Use the same `sed -n 'A,Bp'` form when reading any file in the working tree by line range — it is one process per call and the same idiom for any chunk position.

3. **Compose the review in memory.** Do not write the body to a file. Do not call the `Write` tool. Do not redirect Bash output to disk.

4. **Post the review with one command, using `printf` and stdin:**

   ```bash
   printf '%s\n' \
     '## Code Review — PR #'"$PR_NUMBER"': <PR title>' \
     '' \
     '**Summary.** <one or two sentences>' \
     '' \
     'BLOCKING [correctness]: path/to/file.py:42' \
     'Evidence: <quote the diff and explain the failure mode>.' \
     'Required before merge: <concrete change>.' \
     '' \
     '## Findings out of scope for merge' \
     '' \
     'FOLLOW-UP [test-evidence]: path/to/test.py' \
     'Evidence: <what is missing>.' \
     'Track under: <issues file or tracker>.' \
     | gh pr comment "$PR_NUMBER" --repo "$REPO" --body-file /dev/stdin
   ```

   Quoting rule: wrap literal text in single quotes so `$`, backticks, and backslashes pass through unchanged; splice variables with `"$VAR"` only where expansion is required. Concatenate the two by adjacency, as in `'## Code Review — PR #'"$PR_NUMBER"': <title>'` — that whole expression is one argument to `printf`, producing one line. Each argument to `printf '%s\n'` is one line of output. Blank lines are `''`.

5. **If you need to revise the comment you just posted,** use `--edit-last`:

   ```bash
   printf '%s\n' '<revised content>' \
     | gh pr comment "$PR_NUMBER" --repo "$REPO" --edit-last --body-file /dev/stdin
   ```

## Environment

The runner sandboxes filesystem writes. The forms below have all been observed to fail in this workflow — skip the rediscovery and use the form in step 4 directly.

| Do not use                                           | Why                                                                                                                                                                                                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Write` tool                                         | Blocked by filesystem allowlist; every attempt errors.                                                                                                                                                                                            |
| `> file`, `tee file`, `cat > file <<EOF`             | Same filesystem allowlist applies to Bash redirection outside the repo working tree.                                                                                                                                                              |
| `gh pr comment --body "$(cat <<'EOF' … EOF)"`        | Command substitution with embedded heredoc is brittle here and silently truncates on some bodies.                                                                                                                                                 |
| `gh pr comment --body-file /dev/stdin <<HEREDOC`     | Heredoc directly to `gh` does not reliably reach the body-file reader.                                                                                                                                                                            |
| `gh api repos/<o>/<r>/issues/comments/<id> -X PATCH` | The Actions integration token lacks permission. Use `gh pr comment --edit-last` instead.                                                                                                                                                          |
| `gh pr view <N> --repo <O/R>` without `--json`       | Default view fetches `statusCheckRollup`, which the token cannot access. Always pass `--json`, and never request the `statusCheckRollup` field. Safe fields: `number,title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`. |
| Helper scripts written to disk to assemble the body  | Same write blockage; also adds turns for nothing the `printf` form does not already do.                                                                                                                                                           |

## Review shape

Cover, in this order: correctness, project conventions (from `CLAUDE.md`), potential bugs, performance, security, test coverage.

Classify every finding by required receiver action. When `REVIEW.md` is present, it overrides this default taxonomy.

| Class          | Receiver action              | Use when                                                                                      |
| -------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| `BLOCKING`     | Fix in this PR before merge. | Correctness bug, security risk, data-loss risk, broken required validation, policy violation. |
| `NEEDS-ANSWER` | Answer before merge.         | A required fact is missing and the answer can clear the concern or upgrade it to `BLOCKING`.  |
| `FOLLOW-UP`    | Track outside this PR.       | Valid concern, but fixing it would widen the PR or does not affect merge safety.              |
| `NOTE`         | No action expected.          | Context, praise, or observation that does not create work. Omit when it adds noise.           |

Do not use `P0`/`P1`/`P2`/`P3` or `critical`/`high`/`medium`/`low`/`minor`/`nit` as finding headings.

Finding shape:

```text
BLOCKING [correctness]: path/to/file.py:42
Evidence: <quote the diff or behavior and explain the failure mode>.
Required before merge: <concrete change>.
```

```text
FOLLOW-UP [test-evidence]: path/to/test.py
Evidence: <what is missing>.
Track under: <issues file or tracker>.
```

If the diff has no `BLOCKING` or `NEEDS-ANSWER` findings, say so directly in the comment. Do not invent lower-priority findings to prove the review happened.
