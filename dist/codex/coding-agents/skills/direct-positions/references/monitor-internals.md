<overview>

The skill bundles one monitor for every watched position and a roster that lists them. Both read sessions only through the sibling `operate-prowl`, `operate-herdr` and `operate-agent-mail` adapters, so they own no Prowl, herdr or agent-mail command grammar.

</overview>

<watch_file>

`.spx/worktree/director/watch.json` in the Director's worktree:

```json
{
  "position": "Methodology Director",
  "mail": { "channel": "/abs/path/changes.git", "agent": "<Director mail name>" },
  "sessions": [
    {
      "position": "SPX Maintainer",
      "mail_name": "<registered mail name>",
      "backend": "prowl",
      "cwd": "/abs/path/spx/worktrees/maintainer",
      "stall_minutes": 45,
      "context_percent": 80,
      "report_background": false,
      "blocked_remind_minutes": 15
    }
  ],
  "groups": [
    { "label": "Executor", "backend": "herdr", "cwd_prefix": "/abs/path", "exclude": [], "expect_members": false }
  ]
}
```

- `mail` names the agent-mail channel: the repository whose common Git directory keys the store, and the Director's own name. Omit it to watch sessions only.
- A `sessions` entry matches its live session by `cwd`, or by `handle` (a Prowl pane id or a herdr agent name).
- A `groups` entry watches every session under `cwd_prefix` except the paths in `exclude`, so Executors appear and disappear without editing the file. `expect_members: true` reports `ABSENT` for the group's label while no session lives under the prefix.
- `stall_minutes` and `context_percent` turn on pane reads for that entry; without them the monitor reads only the server state. Thresholds are positive numbers, and `report_background` and `expect_members` are booleans.
- Both scripts reject a missing or malformed watch file, and the monitor rejects a malformed state file or an `--every` that is not a positive, finite number of seconds. Each exits with status 2 and names the defect on standard error.
- `report_background: false` silences `WAITING-ON-BACKGROUND` for a position that rests on its own monitor.

</watch_file>

<signals>

| Signal                  | Meaning                                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| `MAIL <id> from <name>` | A new record in the Director's inbox; the first run after a fresh state file withholds existing mail |
| `BLOCKED`               | The session waits at an approval or question; repeated every `blocked_remind_minutes`                |
| `WENT-IDLE`             | The session moved from working to idle or done with no background work                               |
| `WAITING-ON-BACKGROUND` | The turn ended while a shell or background agent still runs                                          |
| `STALLED`               | The pane text, digits removed, has not changed for `stall_minutes` while working                     |
| `COMPACT-NOW`           | Context at or above 85%                                                                              |
| `COMPACT-AT-BOUNDARY`   | Context at or above 75%                                                                              |
| `COMPACT-IDLE`          | Context at or above 50% with the turn ended                                                          |
| `ABSENT`                | No live session matches the entry, or a group member ended                                           |
| `WATCH-BROKEN`          | An adapter read failed; the loop goes on                                                             |
| `WATCH-DUPLICATE`       | Another loop holds the lock for this state file; this copy exits                                     |

A compaction tier is reported once per 5% step. Prowl's status stays `working` while a session's own monitor runs; the environment reads the screen state `idle` under a `working` status as idle with background work.

</signals>

<state_and_lock>

`state.json` holds the last mail id and each session's last state, timestamps, pane digest and reported tiers. Only the monitor writes it. `state.json.lock` holds the loop's process id under an exclusive file lock taken atomically; a re-arm finds the lock held and exits with `WATCH-DUPLICATE`, so a re-arm never doubles signals. A lock file left by a process that is gone is taken over.

</state_and_lock>

<arming>

The harness caps a monitor at 30 minutes. Arm it through the harness monitor tool at the maximum timeout and re-arm it on every expiry notice: an expired monitor sees nothing, and mail arriving in the gap shows on the next run. A watch run as a backgrounded shell dies at the shell's limit with no notice, so never use one.

</arming>

<roster>

`roster.py WATCH.json` prints one Markdown row per position — mail name, backend, worktree, pane, server state, context — and one row per group member. A failed inventory shows as `inventory failed` with the adapter's message, never as `absent`. Pipe it to `spx change draft create --input stdin` to keep it in the worktree across reboots.

</roster>
