<contents>

- `<scope>` — what this reference operationalizes
- `<lifecycle_rules>` — `store-binding`, `canonical-state`, `authority-read`, `ordered-write`, `complete-readback`, `write-inspection`, `inert-stdin`, `claim-record`, `handoff-record`, `confirmation-record`, `terminal-record`

</contents>

<scope>

This reference operationalizes the Lifecycle, authority, and Handoff rules of the Change chapter `<authority>` names, for the store `spx/local/coordination.md` declares; it replaces nothing in the chapter. Lifecycle records who holds a Change, whether it waits for the Product's Maintainer, or how it ended, and moves independently of Maturity.

</scope>

<lifecycle_rules>

<rule id="store-binding">

Read `spx/local/coordination.md` for the Change store (`owner/repo`) and the Product value. The store is a GitHub repository whose owner is an organization that defines the issue fields `canonical-state` names; a store of another kind is a blocked operation naming the declared store. Read no other overlay for the store; a transition that moves the checkout reads `spx/local/merging.md` for the safety checks the repository declares around a detach. Every store command names only that store; a `gh` grant admits any repository the account reaches, so this discipline is the containment. An absent overlay is a blocked operation naming the missing file; no Lifecycle transition runs without a declared store.

</rule>

<rule id="canonical-state">

The issue holds each Change field in its one home: the issue title holds `title`; the organization issue fields `Product`, `Maturity`, and `Lifecycle` hold `product`, `maturity`, and `lifecycle`; the organization text issue field `Predecessors` holds `refined_from` as canonical identities such as `owner/repo#N`, separated by a comma and one space and empty for a Change that absorbed none; the organization number issue field `Parent` holds `parent` as the Parent's issue number and is empty for none; native issue dependencies hold `blocked_by`; and the issue body holds the Intent and the sections its Maturity adds, with no front matter and no lineage line. Comments carry the Claim, Handoff, confirmation or rejection, and terminal records; the issue's field-change events carry the actor and time of every field move; and the assignee list represents the holder. No project field holds a Change field.

Read the issue with `gh issue view <N> --repo <store> --json number,title,state,stateReason,assignees,comments,url`. Read its fields with `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){id issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} ... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`, selecting each value by its field `name`. `Product` and `Maturity` carry exactly one value, and so does `Lifecycle`; an absent `Maturity` or `Lifecycle` is a missing required field, and an absent `Product` is valid only for a root. `Lifecycle` is valid only as `Available`, `Claimed`, `Submitted`, `Applied`, or `Abandoned`; any other value is reported as unrecognized, with nothing written. Never derive a field from issue prose.

Write a single-select field with `gh api graphql -f query='mutation($i:ID!,$f:ID!,$v:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,singleSelectOptionId:$v}]}){clientMutationId}}' -f i=<issue-id> -f f=<field-id> -f v=<option-id>`; the text field takes `textValue:$v` with `$v:String!` in place of the option, and the number field takes `numberValue:$v` with `$v:Float!`. The issue id is the `id` the field read returns. Resolve the field and option ids with `gh api graphql -f query='query($l:String!){organization(login:$l){issueFields(first:50){nodes{... on IssueFieldSingleSelect{id name options{id name}} ... on IssueFieldText{id name} ... on IssueFieldNumber{id name}}}}}' -f l=<owner>`; hardcode none of them. A Lifecycle value the organization field offers no option for is a blocked write naming the missing option.

Each nested connection above is read at 50 nodes. An `issueFieldValues` connection that returns 50 nodes, in the field read or in a node of a page of issues, is a blocked read naming `50 field values`, and an `issueFields` connection that returns 50 nodes is a blocked write naming `50 issue fields`; derive no field, child, absorber, or id from the partial result.

A Change's children are the store records whose `Parent` value equals its issue number, and the Change that absorbed it is the store record whose `Predecessors` value names its canonical identity; the entries of a Change's own `Predecessors` value are the Changes it absorbed, never the Change that absorbed it. Read the store's issues one page of 100 at a time, at most 10 pages, with one `gh api graphql` call per page: `gh api graphql -f query='query($o:String!,$r:String!,$after:String){repository(owner:$o,name:$r){issues(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{number url issueFieldValues(first:50){nodes{... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}}}}}}}}' -f o=<owner> -f r=<repo>`, adding `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 issues per page, 10 pages` and derive no child or absorber from the partial read. Keep the records whose `Parent` value equals `<N>` as its children, and the records whose `Predecessors` value, split at every comma followed by one space, holds the canonical identity of the Change as its absorbers; a Change absorbed by no record is absorbed by none, and one absorbed by a record that has closed `Applied` is absorbed by a Change that has closed `Applied`. A Change is a Parent when at least one record is its child, a Leaf when its body carries a Governance mutations or Spec mutations block, and a root when it has neither a child nor such a block. A Change's blockers are its native dependencies, read as one page of 100 with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method GET -F per_page=100`; a page holding 100 entries is a blocked read that names the bound `100 blockers, one page`.

</rule>

<rule id="authority-read">

Authority is read from the store, never from the body. Read the issue's field-change events one page of 100 at a time, at most 10 pages, with one `gh api graphql` call per page: `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){issue(number:$n){timelineItems(first:100,after:$after,itemTypes:[ISSUE_FIELD_CHANGED_EVENT]){pageInfo{hasNextPage endCursor} nodes{... on IssueFieldChangedEvent{createdAt actor{login} previousValue newValue issueField{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`, adding `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 events per page, 10 pages` and report no authority from the partial read. Read its comments the same way, one page of 100 at a time and at most 10 pages: `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){issue(number:$n){comments(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{createdAt author{login} body}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`, adding `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 comments per page, 10 pages` and report no authority from the partial read.

A move out of `Submitted` is a `Lifecycle` event whose `previousValue` is `Submitted` and whose `newValue` is `Available`. Its deciding comment is the newest `Confirmation:` or `Rejection:` comment under `confirmation-record` posted after the move into `Submitted` that it ends and before the move itself; `complete-readback` selects the same comment. `Maturity` held `M` at an event's time when `M` is the `newValue` of the newest `Maturity` event before it; with no earlier `Maturity` event, the `previousValue` of the oldest later one; with no `Maturity` event at all, the current `Maturity`.

The authority for leaving Maturity `M` is one move out of `Submitted`, posted while `Maturity` held `M`, whose deciding comment is a `Confirmation:` naming `M`. A move whose deciding comment is a `Rejection:` grants no authority, and so does a move with no deciding comment or a comment with no move. The move is the Product's Maintainer's as the store records it: the comment's `For:` line names the operator the move acts for, and the event's `actor` names the account that wrote it; no other store state identifies the Maintainer.

Report each authority found with the event's `actor` login and `createdAt` and the deciding comment's lines verbatim. When no confirmation exists for `M`, report that the store shows no authority for leaving `M`; a body line never stands in for it.

</rule>

<rule id="ordered-write">

A transition records each successful write in its declared order. When a required command fails, a required field is absent, or a readback differs from the intended state, stop before every later mutation and report: the successful writes in order, the failed command or mismatched value, and the observed Product, Maturity, Lifecycle, assignees, issue state and reason, and newest `Claim:`, `Handoff:`, `Confirmation:`, `Rejection:`, or terminal comment. Never repair a partial transition by guessing which later mutation would make it look complete.

</rule>

<rule id="complete-readback">

A transition completes only after re-reading the issue and its fields and finding every value equal to the intended state: Product equals the overlay Product, or is empty for a root, Maturity is unchanged, Lifecycle equals the target value, the assignee list equals the intended holder set, and the transition's own record is the one its rule selects: for a claim, the winning Claim under `claim-record` is the exact comment the transition posted; for a confirmation, the deciding comment under `authority-read` is the exact `Confirmation:` or `Rejection:` comment the transition posted; for a release or a close, the newest `Handoff:` or terminal comment is. Report the readback values verbatim.

</rule>

<rule id="write-inspection">

Before any write that sends text to the store — a comment, an issue title or body, or a text field value — inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found, never the value, and ask through the structured-question tool whether the operator supplies a redacted text or abandons the write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the result says so.

</rule>

<rule id="inert-stdin">

Every field a `gh` command receives from a Change body, conversation state, or interview output is passed as inert data. A comment body or an issue body is a payload: write it with the file-write tool to a file in the scratch directory the harness names for the session, under a file name unique to the agent, the store command, and the Change, and pass it through the command's file argument, `--body-file <file>`. No heredoc, pipe, or inline form carries a payload, and the agent never removes the file. A title, which `gh` takes only as an argument, and every other interpolated argument is one single-quoted argument; inside it a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a redirect built from it.

</rule>

<rule id="claim-record">

A Claim is one comment, `Claim: <agent session id> <claim root>`, posted after the assignee is added; the claim root is the worktree root the Change is claimed for — the claiming session's own assigned root, or a root it names. The Change's holder is the session whose assigned worktree root equals the claim root of the winning Claim. Holder exclusivity comes from the Claim, never from the assignee alone, because one account may run several sessions: the earliest `Claim:` posted after the newest `Handoff:` — or since issue creation when none exists — wins. Only an `Available` Change whose Product is the configured Product, or a root that carries no Product, is claimed; a `Submitted` Change waits for its confirmation.

</rule>

<rule id="handoff-record">

A Handoff is one comment carrying exactly these lines in this order: the opening line `Handoff:`, one blank line, the five required lines, and optionally the two context lines. It carries nothing else, and nothing that belongs in the body:

```markdown
Handoff:

- Branch or PR: <pushed work branch, or the PR URL, or `none`>
- Completed blocks: <the completed Governance mutations and Spec mutations blocks, by their path, or `none`>
- Next block: <the first uncompleted block, by its path, or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active, and each question the stopped work leaves for the operator, verbatim; or `none`>
- Hazards: <why the work stopped, and what the next holder cannot derive quickly — an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
- Session: <the current agent session id>
- Worktree: <the assigned worktree root>
```

The `Session:` and `Worktree:` lines are the only optional lines, and each appears at most once, after the five. The Handoff records what was true when it was posted; refinement of the Output belongs in the body, before the release. A release that moves the Change to `Submitted` runs only at `Proposed`, `Framed`, or `Sliced`, posts its Handoff before it writes `Submitted`, and its Next block line names the confirmation the Change waits for: `confirmation: <Maturity>`.

</rule>

<rule id="confirmation-record">

A confirmation or rejection is one comment posted on a `Submitted` Change before its Lifecycle moves to `Available`. A confirmation carries exactly these lines in this order — the opening line, one blank line, and four required lines — and nothing else:

```markdown
Confirmation: <Maturity>

- Delegate: <the agent that performs the move>
- For: <the operator it acts for>
- Harness: <the agent harness>
- Session: <the agent session id>
```

A rejection carries the same lines with two differences, and nothing else: its opening line is `Rejection: <Maturity>`, and a fifth required line `- Reason: <the operator's stated reason>` follows the `Session:` line. `<Maturity>` is the Change's current Maturity: `Proposed`, `Framed`, or `Sliced`. The comment names the delegate and the operator because every session acts through one account, so the field-change event's actor names the account and never the delegate.

</rule>

<rule id="terminal-record">

A terminal record is one comment whose text the terminal value fixes: `Application complete: changeset integrated, evidence satisfied, and Output delivered.` for `Applied`; `Abandoned: <the operator's stated reason>` for `Abandoned`. The close reason is `completed` for `Applied` and `not planned` for `Abandoned`. A Change closed `Abandoned` is absorbed when the absorber lookup under `canonical-state` finds a store record whose `Predecessors` value names it; the lookup, never the closed Change's own `Predecessors` value, decides what absorbed it. A terminal Change receives no Handoff and never returns to `Available`.

`Applied` for a Leaf requires a link in `## Artifacts` for every record and Node the Change adds or modifies, every `## Artifacts` link integrated into the default branch through its merge gates, no Node of the Spec mutations failing, and the Intent's Evidence met. A link is integrated when `git merge-base --is-ancestor` of the merge commit the link pins and the default branch exits zero. `Applied` for a Parent requires every child closed and its last child closed `Applied`; a Parent whose last child closed `Abandoned` stays open. A root closes `Applied` when the operator judges its Intent met and `Abandoned` when the operator drops it, and a close of a root runs only on the operator's direction. After a close of `Applied` whose Parent has a Parent and no open child, the same session claims that Parent and closes it `Applied`, repeating upward, and never closes a root this way.

</rule>

</lifecycle_rules>
