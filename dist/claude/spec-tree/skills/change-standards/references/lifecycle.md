<contents>

- `<scope>` — what this reference operationalizes
- `<lifecycle_rules>` — `store-binding`, `canonical-state`, `authority-read`, `ordered-write`, `complete-readback`, `write-inspection`, `inert-stdin`, `transition-comment`, `claim-record`, `handoff-record`, `terminal-record`, `lifecycle-transitions`

</contents>

<scope>

This reference operationalizes the Lifecycle, authority, and Handoff rules of the Change chapter `<authority>` names, for the store `spx/local/coordination.md` declares; it replaces nothing in the chapter. The relation of Lifecycle to Maturity is stated in `maturity-and-authority`.

</scope>

<lifecycle_rules>

<rule id="store-binding">

Read `spx/local/coordination.md` for the Change store (`owner/repo`) and the Product value. The store is a GitHub repository whose owner is an organization that defines the issue fields `canonical-state` names; a store of another kind is a blocked operation naming the declared store. Read no other overlay for the store; a transition that moves the checkout reads `spx/local/merging.md` for the safety checks the repository declares around a detach. Every store command names only that store; a `gh` grant admits any repository the account reaches, so this discipline is the containment. An absent overlay is a blocked operation naming the missing file; no Lifecycle transition runs without a declared store.

</rule>

<rule id="canonical-state">

The issue holds each Change field in its one home: the issue title holds `title`; the organization issue fields `Product`, `Maturity`, and `Lifecycle` hold `product`, `maturity`, and `lifecycle`; the organization text issue field `Predecessors` holds `predecessors` as canonical identities such as `owner/repo#N`, separated by a comma and one space and empty for a Change that absorbed none; the organization number issue field `Parent` holds `parent` as the Parent's issue number and is empty for none; native issue dependencies hold `blocked_by`; and the issue body holds the Intent and the sections its Maturity adds, with no front matter and no lineage line. Comments carry the transition blocks `transition-comment` defines, one per transition, and never the Change's content; the issue's field-change events carry the actor and time of every field move; the assignee list and its unassign events are the record of holding; and the Handoff commits on the Change's branch `change/<N>` carry continuation. No project field holds a Change field.

Read the issue with `gh issue view <N> --repo <store> --json number,title,state,stateReason,assignees,url` and, for a claim's winning-claim read only, `comments`. Read its fields with `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n){id issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} ... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`, selecting each value by its field `name`. `Product` and `Maturity` carry exactly one value, and so does `Lifecycle`; an absent `Maturity` or `Lifecycle` is a missing required field, and an absent `Product` is valid only for a root. `Lifecycle` is valid only as `Available`, `Submitted`, `Applied`, or `Abandoned`; any other value, a store record held at `Claimed` among them, is reported as unrecognized, with nothing written, until the Product's Maintainer writes `Available`. Never derive a field from issue prose.

Write a single-select field with `gh api graphql -f query='mutation($i:ID!,$f:ID!,$v:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,singleSelectOptionId:$v}]}){clientMutationId}}' -f i=<issue-id> -f f=<field-id> -f v=<option-id>`; the text field takes `textValue:$v` with `$v:String!` in place of the option, and the number field takes `numberValue:$v` with `$v:Float!`. The issue id is the `id` the field read returns. Resolve the field and option ids with `gh api graphql -f query='query($l:String!){organization(login:$l){issueFields(first:50){nodes{... on IssueFieldSingleSelect{id name options{id name}} ... on IssueFieldText{id name} ... on IssueFieldNumber{id name}}}}}' -f l=<owner>`; hardcode none of them. A Lifecycle value the organization field offers no option for is a blocked write naming the missing option.

Each nested connection above is read at 50 nodes. An `issueFieldValues` connection that returns 50 nodes, in the field read or in a node of a page of issues, is a blocked read naming `50 field values`, and an `issueFields` connection that returns 50 nodes is a blocked write naming `50 issue fields`; derive no field, child, absorber, or id from the partial result.

A Change's children are the store records whose `Parent` value equals its issue number, and the Change that absorbed it is the store record whose `Predecessors` value names its canonical identity; the entries of a Change's own `Predecessors` value are the Changes it absorbed, never the Change that absorbed it. Read the store's issues one page of 100 at a time, at most 10 pages, with one `gh api graphql` call per page: `gh api graphql -f query='query($o:String!,$r:String!,$after:String){repository(owner:$o,name:$r){issues(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{number url issueFieldValues(first:50){nodes{... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}} ... on IssueFieldTextValue{value field{... on IssueFieldText{name}}}}}}}}}' -f o=<owner> -f r=<repo>`, adding `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 issues per page, 10 pages` and derive no child or absorber from the partial read. Keep the records whose `Parent` value equals `<N>` as its children, and the records whose `Predecessors` value, split at every comma followed by one space, holds the canonical identity of the Change as its absorbers; a Change absorbed by no record is absorbed by none, and one absorbed by a record that has closed `Applied` is absorbed by a Change that has closed `Applied`. A Change is a Parent when at least one record is its child, a Leaf when its body carries a Governance mutations or Spec mutations block, and a root when it has neither a child nor such a block. A Change's blockers are its native dependencies, read as one page of 100 with `gh api repos/<store>/issues/<N>/dependencies/blocked_by --method GET -F per_page=100`; a page holding 100 entries is a blocked read that names the bound `100 blockers, one page`.

</rule>

<rule id="authority-read">

Read the issue's field-change events one page of 100 at a time, at most 10 pages, with one `gh api graphql` call per page: `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){issue(number:$n){timelineItems(first:100,after:$after,itemTypes:[ISSUE_FIELD_CHANGED_EVENT]){pageInfo{hasNextPage endCursor} nodes{... on IssueFieldChangedEvent{createdAt actor{login} previousValue newValue issueField{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}}}}}}' -f o=<owner> -f r=<repo> -F n=<N>`, adding `-f after=<endCursor>` from the previous page to each later page. When `hasNextPage` is still true after page 10, the read is blocked: name the bound `100 events per page, 10 pages` and report no authority from the partial read.
A move into `Submitted` is a `Lifecycle` event whose `newValue` is `Submitted`, and a move out of `Submitted` is a `Lifecycle` event whose `previousValue` is `Submitted` and whose `newValue` is `Available`. A Change's field-change events are ordered by `createdAt`, and at equal `createdAt` a `Maturity` event comes before a `Lifecycle` event. `Maturity` held `M` at an event's time when `M` is the `newValue` of the newest `Maturity` event before it in that order, so a rejecting lowering written before the move out of `Submitted` is the `Maturity` event before it; with no earlier `Maturity` event, the `previousValue` of the oldest later one; with no `Maturity` event at all, the current `Maturity`.

The authority for leaving Maturity `M` is the one `maturity-and-authority` states: a move out of `Submitted` whose Maturity at the move equals the Maturity at the move into `Submitted`, `M` being that Maturity. A move out of `Submitted` whose Maturity at the move is one level below the Maturity at the move into `Submitted` is a rejection and is no authority. The store records the authority as the event's `actor`, the account that wrote the move, and `createdAt`, its time. No comment is read for it.

Report each authority found with the event's `actor` login and `createdAt`. When no such move exists for `M`, report that the store shows no authority for leaving `M`.

</rule>

<rule id="ordered-write">

A transition records each successful write in its declared order. When a required command fails, a required field is absent, or a readback differs from the intended state, stop before every later mutation and report: the successful writes in order, the failed command or mismatched value, and the observed Product, Maturity, Lifecycle, assignees, issue state and reason, and the winning claim under `claim-record` where a claim is involved. Never repair a partial transition by guessing which later mutation would make it look complete.

</rule>

<rule id="complete-readback">

A transition completes only after re-reading the issue and its fields and finding every value equal to the intended state: Product equals the overlay Product, or is empty for a root, Maturity is unchanged, Lifecycle equals the target value, the assignee list equals the intended holder set, and for a claim, the winning claim under `claim-record` is the exact block the transition posted; for a release, the assignee list is empty; for a submit, the assignee list is unchanged. The readback reads no other comment. Report the readback values verbatim.

</rule>

<rule id="write-inspection">

Before any write that sends text to the store — a comment, an issue title or body, or a text field value — inspect the exact text about to be written for secret values and credential payloads: tokens, keys, passwords, connection strings, cookies, or any pasted credential-shaped content. When any appears, write nothing, report only the kind of content found, never the value, and ask through the structured-question tool whether the operator supplies a redacted text or abandons the write; on redaction, inspect the supplied text and continue; on abandon, the write does not happen and the result says so.

</rule>

<rule id="inert-stdin">

Every field a `gh` command receives from a Change body, conversation state, or interview output is passed as inert data. A comment body or an issue body is a payload: write it with the file-write tool to a file in the scratch directory the harness names for the session, under a file name unique to the agent, the store command, and the Change, and pass it through the command's file argument, `--body-file <file>`. No heredoc, pipe, or inline form carries a payload, and the agent never removes the file. A title, which `gh` takes only as an argument, and every other interpolated argument is one single-quoted argument; inside it a literal apostrophe is written as `'"'"'` and nothing else is escaped. Never `--body "…"`, never a double-quoted argument carrying such text, never a redirect built from it.

</rule>

<rule id="transition-comment">

Every transition posts exactly one comment, and that comment is one fenced YAML block and nothing else, in exactly this form:

```yaml
transition: claim
maturity: Framed
harness: claude
session: 1eac3860-9961-4a52-b8cf-5172095e5f04
machine: shz@sibook
worktree: /Users/shz/Code/outcomeeng/methodology/worktrees/director
position: Methodology Director
```

`transition` is one of `claim`, `release`, `submit`, `confirm`, `reject`, `applied`, and `abandoned`. `maturity` is the Maturity at the move, spelled as the store spells it. `harness` is the agent-harness token the coding-agents plugin owns as `AgentType`: `claude`, `codex`, or `pi`. `session` is the harness session id. `machine` is `$USER@$(hostname -s)`, such as `shz@sibook`. `worktree` is the absolute path of the worktree the session works in. `position` is optional and the only optional key. A reject adds `reason`, the instruction naming what to fix, and a release adds `handoff`, naming the branch, its head commit, and the next block. The comment's timestamp gives the time. The block carries no Delegate line, no For line, no prose, and no other key. No skill reads a comment except under `claim-record`.

</rule>

<rule id="claim-record">

A claim is the transition block with `transition: claim`, posted after the assignee is added when the assignee list is empty. A release is an unassign event that removes the account that posted the winning claim standing before it, so that event opens a new claim window; the unassign event by which a losing claimant withdraws its own account removes no winning claim and is no release. A session claims only for itself and the worktree it works in; an Orchestrator that starts an Executor posts no claim, and the Executor claims the Change when it starts. The claim exception reads only the YAML block of each comment whose block carries `transition: claim` and that was posted after the newest release; the earliest live one wins, liveness being `spx worktree status` on this machine, and a claim whose `machine` names another machine is never voided on age. The session the winning claim names holds the Change, and a release or a close runs only for that session. Holder exclusivity comes from the winning claim, never from the assignee alone, because one account may run several sessions. A claim requires an open record whose Product is the configured Product, or that is a root carrying no Product, whose Maturity is one declared value, whose Lifecycle is `Available`, and whose winning claim, if any, is not live; any other state, `Submitted` included, is reported without mutation.

</rule>

<rule id="handoff-record">

A Handoff is one empty commit on the Change's branch `change/<N>` on origin, where the next holder checks out; the branch name derives from the Change number, a work branch that carries another name keeps it until it merges, and every branch created for a Change takes `change/<N>`. The commit message is the Handoff, pushed to `refs/heads/change/<N>` on origin before the release comment, whatever name the work branch carries; the next holder reads the Handoff from `change/<N>` alone. The holder commits it when it releases the Change, and the Executor commits one after every completed block and after integration while it keeps the Change. No Handoff is a comment, and nothing lands as a file on the default branch. The message carries exactly these lines in this order: the opening line `Handoff:`, one blank line, the five required lines, and optionally the two context lines. It carries nothing else, and nothing that belongs in the body:

```markdown
Handoff:

- Branch or PR: <the branch `change/<N>`, or the PR URL, followed by `@` and the full head commit SHA of that branch or pull request; after integration, the merged pull request followed by `@` and its merge commit; or `none`>
- Completed blocks: <the completed Governance mutations and Spec mutations blocks, by their path, with no run token; or `none`. A Governance mutations block counts as completed only when its decision-record audit approved; after integration, every block>
- Next block: <the first uncompleted block, by its path; `none` after integration, when every block is completed; or `refinement: <Maturity> → <next level>` below Executable>
- Blockers: <blocking Change URLs still active, and each question the stopped work leaves for the operator, verbatim; or `none`>
- Hazards: <why the work stopped, and what the next holder cannot derive quickly — an unsealed run, a held checkout, a flaky check — each with the read-only command that re-confirms it>
- Session: <the current agent session id>
- Worktree: <the assigned worktree root>
```

The head commit on the `Branch or PR` line is the tip the work stopped at; a reader takes the changeset from the branch or the pull request and reads that commit as the state the Handoff describes, never as the commit a later close checks for integration, except after integration, when the line names the merged pull request with its merge commit. A close reads the merge commit from the newest Handoff commit, and treats a record its Governance mutations blocks amend or create as audited when that Handoff's `Completed blocks` line lists the block; the decision-record audit seals no verification run, so the line carries no token. A Handoff committed without a release leaves the assignee and the winning claim in force. The `Session:` and `Worktree:` lines are the only optional lines, and each appears at most once, after the five. The Handoff records what was true when it was committed; refinement of the Output belongs in the body, before the release. A release that moves the Change to `Submitted` is a submit: it follows `maturity-and-authority` for the Maturities that admit it, commits its Handoff before it writes `Submitted`, and its Next block line names the Maturity whose review the Change waits for: `confirmation: <Maturity>`.

</rule>

<rule id="lifecycle-transitions">

`Available` means the Change waits for no confirmation; `Submitted` means a finished stage waits for the Product's Maintainer, as `maturity-and-authority` states; `Applied` and `Abandoned` are terminal. The holder is the assignee in every Lifecycle. A transition is one of seven moves, each writes only the fields it names, and each is performed separately:

- A claim adds the assignee and writes no Lifecycle.
- A release removes the assignee, and writes `Available` only for a `Submitted` Change, whose pending confirmation then lapses. The unassign event that removes the holder is the release, and no comment is read for it.
- A submit writes `Submitted` at Proposed, Framed, or Sliced and keeps the assignee.
- A confirm writes `Available` with Maturity unchanged and keeps the assignee.
- A reject posts the reject block, writes the Maturity one level lower, then writes `Available`, and keeps the assignee; it is refused at Proposed.
- An applied and an abandoned write the terminal value each names and keep the assignee.

Each transition posts exactly one transition block under `transition-comment` and no other comment, and none writes a body section. Only a reject writes Maturity among the Lifecycle transitions. A confirm and a reject act for the Product's Maintainer on a `Submitted` Change only, and report any other Lifecycle without mutation. No operation posts, reads, or parses a `Rejection:` comment, and none writes the Lifecycle value `Claimed`.

</rule>

<rule id="terminal-record">

A terminal record is the `applied` or `abandoned` transition block. The close reason is `completed` for `Applied` and `not planned` for `Abandoned`. A Change closed `Abandoned` is absorbed when the absorber lookup under `canonical-state` finds a store record whose `Predecessors` value names it; the lookup, never the closed Change's own `Predecessors` value, decides what absorbed it. A terminal Change receives no Handoff and never returns to `Available`.

`Applied` for a Leaf requires its integration commit — the merge commit of the merged pull request whose head is the Change's branch, or that branch's tip where the transport opens no pull request — to be an ancestor of the default branch, every Node to hold every result the merge composition for its malleability after selects, every amended or new record to hold an approving decision-record audit, which the newest Handoff's `Completed blocks` line lists, and the Intent's Evidence met. The integration commit is an ancestor when `git merge-base --is-ancestor` of it and the default branch exits zero. `Applied` for a Parent requires every child closed and its last child closed `Applied`; a Parent whose last child closed `Abandoned` stays open. A root closes `Applied` when the operator judges its Intent met and `Abandoned` when the operator drops it, and a close of a root runs only on the operator's direction. After a close of `Applied` whose Parent has a Parent and no open child, the same session claims that Parent and closes it `Applied`, repeating upward, and never closes a root this way.

</rule>

</lifecycle_rules>
