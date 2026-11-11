<contents>

- `<store_binding>` — the overlay that names the store and the Product
- `<reads>` — the issue, its fields, its relations, its blockers, its edit history, and its field-change events
- `<writes>` — field writes, comments, the body, assignees, and blockers
- `<transition_comment>` — the comment that logs a Transition
- `<write_discipline>` — payload files, secret inspection, ordered writes, and readback
- `<store_options>` — the option check before a field write

</contents>

<store_binding>

Read `spx/local/changes.md` for the Change Store (`owner/repo`) and the Product value. The store is a GitHub repository whose owner is an organization that defines the issue fields `<github_store>` of the standards names. An absent overlay, or a store of another kind, is a blocked operation naming the missing file or the declared store. Every store command names only that store; a `gh` grant admits any repository the account reaches, so this discipline is the containment. A Change reference whose `owner/repo` differs from the declared store is a blocked operation naming both.

</store_binding>

<reads>

Read the issue with `gh issue view <N> --repo <store> --json number,title,body,state,stateReason,assignees,comments,url,createdAt`.

Read its fields and its edit stamp with:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){id createdAt lastEditedAt issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} ... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>
```

Select each value by its field `name`: `Product`, `Maturity`, `Lifecycle`, `Priority`, `Value`, and `Investment` are single-select; `Predecessors` and `Base` are text; `Parent` is a number. `Predecessors` holds Change references separated by a comma and one space and is empty for `[]`; `Parent` holds the Parent's issue number and is empty for `null`; an empty `Priority`, `Value`, or `Investment` is `null`. A Maturity or Lifecycle value outside the values `record-keys` names is reported as unrecognized, with nothing written. Never derive a field from issue prose. An `issueFieldValues` connection that returns 50 nodes is a blocked read naming `50 field values`.

Compose a Draft from a stored record by writing the keys in `record-keys` order, `holder` left out, from these homes, followed by the issue body. `blockers` lists the native dependencies as Change references. A record whose `Parent` is another record's number while it carries no Declarations is a Parent; a Parent holds no `base` key.

A Change's Children are the store records whose `Parent` value equals its issue number, and the Change that absorbed it is the store record whose `Predecessors` value names it. Read the store's issues one page of 100 at a time, at most 10 pages, with one `gh api graphql` call per page:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$after:String){repository(owner:$o,name:$r){issues(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{number url issueFieldValues(first:50){nodes{... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}}}}}}}}' -f o=<owner> -f r=<repo>
```

Add `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 issues per page, 10 pages`, and derive no Child or absorber from the partial read.

Read a Change's blockers as one page of 100 with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method GET -F per_page=100`; a page holding 100 entries is a blocked read naming `100 blockers, one page`.

Read the body's edit history, newest first, as one page of 100:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){lastEditedAt userContentEdits(first:100){totalCount nodes{editedAt editor{login} diff}}}}}' -f o=<owner> -f r=<repo> -F n=<N>
```

A `totalCount` above 100 is a blocked read naming `100 edits, one page`.

Read the field-change events one page of 100 at a time, at most 10 pages:

```bash
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){issue(number:$n){timelineItems(first:100,after:$after,itemTypes:[ISSUE_FIELD_CHANGED_EVENT]){pageInfo{hasNextPage endCursor} nodes{... on IssueFieldChangedEvent{createdAt actor{login} previousValue newValue issueField{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>
```

When `hasNextPage` is still true after page 10, the read is blocked naming `100 events per page, 10 pages`. The `Base` events give the Base value at a time for `github-binding`; no event is read as authority.

The holder is the issue's one assignee; the session and the worktree that hold the Change are the `session` and `worktree` of the newest `claim` comment under `<transition_comment>`. More than one assignee breaks `github-one-holder` and stops every Transition but a release by one of them.

</reads>

<writes>

Resolve the field and option ids from the organization; hardcode none of them:

```bash
gh api graphql -f query='query($l:String!){organization(login:$l){issueFields(first:50){nodes{... on IssueFieldSingleSelect{id name options{id name}} ... on IssueFieldText{id name} ... on IssueFieldNumber{id name}}}}}' -f l=<owner>
```

An `issueFields` connection that returns 50 nodes is a blocked write naming `50 issue fields`. Write a single-select field with:

```bash
gh api graphql -f query='mutation($i:ID!,$f:ID!,$v:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,singleSelectOptionId:$v}]}){clientMutationId}}' -f i=<issue-id> -f f=<field-id> -f v=<option-id>
```

A text field takes `textValue:$v` with `$v:String!` in place of the option, and a number field takes `numberValue:$v` with `$v:Float!`. The issue id is the `id` the field read returns.

- Title and body: `gh issue create --repo <store> --title '<title>' --body-file <body-file>`, or `gh issue edit <N> --repo <store> --title '<title>' --body-file <body-file>`.
- Holder: `gh issue edit <N> --repo <store> --add-assignee @me` and `--remove-assignee @me`.
- Blockers: add one with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method POST -F issue_id=<id>`, remove one with `gh api repos/<store>/issues/<N>/dependencies/blocked_by/<id> --method DELETE`, where `<id>` is the numeric id `gh api repos/<owner>/<repo>/issues/<M> --jq .id` prints.
- Comment: `gh issue comment <N> --repo <store> --body-file <comment-file>`.
- Close: `gh issue close <N> --repo <store> --reason 'completed'` for Applied, `--reason 'not planned'` for Abandoned.

</writes>

<transition_comment>

Every Transition posts exactly one comment, whose whole text is one fenced YAML block:

````markdown
```yaml
transition: <claim | release | submit | advance | lower | applied | abandoned>
maturity: <the Maturity at the move, as the Maturity field spells it>
harness: <claude or codex>
session: <the harness's session id>
machine: <user>@<short host name>
worktree: <absolute path of the worktree the session works in>
position: <the Position held, only when one is held>
```
````

A lower adds `reason: <one sentence>`. A release adds:

```yaml
handoff:
  branch: <pushed work branch, or none>
  head: <full head commit SHA of that branch, or of the default branch for none>
  next: <the path of the next Declarations subsection, or the next Refinement step>
  completed: [<the path of each completed subsection>]
  blockers: [
    <each blocking Change still open,
    and each open question,
    verbatim>,
  ]
  hazards: [
    <what the next holder cannot derive quickly,
    each with the read-only command that confirms it>,
  ]
```

`branch`, `head`, and `next` are required; `completed`, `blockers`, and `hazards` appear when they hold an entry. An applied Transition of a Leaf adds `changeset: <owner/repo>@<merge commit SHA>`. No other key, no prose outside `reason`, no party on whose behalf the holder acts, and no words of the Operator appear in the block. Resolve `session` from the harness's session variable, `machine` from `id -un` and `hostname -s`, and `worktree` from `git rev-parse --show-toplevel`.

</transition_comment>

<write_discipline>

- Payloads: a body or comment is written with the file-write tool to a file in the scratch directory the harness names for the session, under a file name unique to the agent, the command, and the Change, and passed through `--body-file <file>`; where the harness names no scratch directory, use the one the environment designates, such as `$RUNNER_TEMP` on a hosted runner. A title and every other argument is one single-quoted argument, a literal apostrophe written as `'"'"'`. NEVER pass a payload through a heredoc, a pipe, or an inline form, and NEVER remove a payload file.
- Secret inspection: before any write that sends text, inspect it for tokens, keys, passwords, connection strings, cookies, and pasted credentials; when any appears, write nothing, report only the kind of content found, and stop.
- Ordered writes: record each successful write in its declared order. When a command fails, a field is absent, or a readback differs from the intended state, stop before every later write and report the successful writes in order, the failed command or mismatched value, and the observed fields, assignees, issue state, and newest Transition comment. Never repair a partial write by guessing which later write would make it look complete.
- Readback: an operation completes only after it re-reads the issue and its fields and finds every value equal to the intended state, and its own comment the newest Transition comment. Report the readback values verbatim.

</write_discipline>

<store_options>

Before the first write to `Maturity`, `Lifecycle`, `Value`, or `Investment`, read the field's options with the organization field read and compare them, as a set, with the values `record-keys` names: `Proposed`, `Framed`, `Sliced`, `Applicable` for Maturity; `Available`, `Submitted`, `Applied`, `Abandoned` for Lifecycle; `Offering`, `Quality`, `Capability`, `Safety` for Value; `Harvest`, `Shield`, `Frontier`, `Seed` for Investment. A field whose options differ stops the operation before any write with a blocked result naming the field, the options the store offers, and the values the standards name.

</store_options>
