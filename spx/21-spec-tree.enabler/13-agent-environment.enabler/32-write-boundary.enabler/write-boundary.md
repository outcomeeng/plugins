---
id: 01a15094-e103-71f2-8cab-638037c2bdfa
malleability: spec
---

# Write Boundary

PROVIDES a pre-write check that bounds the destination of a Claude Code Write or Edit call to the granted roots
SO THAT agent sessions
CAN write files only where the harness grants them

## Assertions

- Given a Claude Code Write or Edit call whose destination lies inside a granted root, when the shipped pre-write hook command runs, then it exits zero with a valid empty result and the write proceeds
- Given a Claude Code Write or Edit call whose destination is a file beside a misspelled copy of an ancestor directory of the project directory, a fabricated sibling of the session's scratch directory, or a dummy file inside a misspelled copy of the session's scratch directory, when the shipped pre-write hook command runs, then it denies the call with a reason naming the destination and the granted roots
- Given a session whose verification runs record their journals, when the session runs `spx verification run` and writes its payload files in its scratch directory, then every write passes, because SPX writes the journal through the shell and the payload files lie inside a granted root
- ALWAYS: the granted roots are exactly the project directory the harness supplies to the hook as `CLAUDE_PROJECT_DIR`, the payload session's scratch directory, the harness configuration directory `CLAUDE_CONFIG_DIR` or `~/.claude` when it is unset, and each `permissions.additionalDirectories` entry of the user, project, and local Claude Code settings files that apply to the project directory
- ALWAYS: the payload session's scratch directory is the `scratchpad` directory the harness creates under its temporary root for the payload's `session_id` and for the project key that names the directory holding the payload's `transcript_path`, and no sibling or parent of that directory is granted
- ALWAYS: inside the harness's temporary root, only the payload session's own scratch directory is granted, whatever an additional directory admits
- ALWAYS: the check resolves a destination and each root alike: every existing ancestor through its symbolic links, so `/tmp` resolves to `/private/tmp` where the file system links them, and the components that do not exist yet lexically, so a destination whose leaf does not exist resolves through its nearest existing ancestor
- ALWAYS: the check compares resolved paths by whole components and case-sensitively, so a case variant of a granted root is denied
- ALWAYS: the check judges only the destination of a Write or Edit call; a write a shell command performs stays with the harness's sandbox and permission rules
- ALWAYS: the shipped pre-write hook command allows the call, exiting zero with a valid empty result, on every failure: an absent, unreadable, or malformed payload, an unset project directory, an unreadable settings file, a missing adapter script, an absent interpreter, an exception, and a timeout
- ALWAYS: the shipped pre-write hook entry declares a five-second timeout, and `SPECTREE_WRITE_BOUNDARY_HOOK_DISABLED=1` makes its command exit zero with a valid empty result without reading the payload
- ALWAYS: the write-boundary adapter reads only the hook payload, the harness environment, and the Claude Code settings files, runs no subprocess, and complies with [`spx/13-plugin-and-runtime-conventions.adr.md`](spx/13-plugin-and-runtime-conventions.adr.md) and [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) as a deterministic, bounded, standard-library-only agent adapter
- ALWAYS: on Codex the write-boundary adapter bounds no write — it finds no `CLAUDE_PROJECT_DIR` and allows the call — and a session in the workspace-write sandbox writes only inside the sandbox's writable roots
