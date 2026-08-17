### Dangerous-command guard

🛑 **STOP TRIGGER — a dangerous-command guard (DCG) block terminates the attempted command family.** Treat the blocked attempt as a mistake.

- **NEVER** pass dynamic branch names to `git branch -d` or `git branch -D`: variables, command substitutions, arrays, and globs are denied, including when quoted or placed after `--`. Type every branch name literally; delete several literal names in one command.
- **ALWAYS** follow the active skills, repository instructions, and declared overlays to find a sanctioned operation that accomplishes the goal.
- When no sanctioned operation exists, abandon the goal, report the blocked command with secrets redacted, explain its purpose and the guard's reason, ask the operator for direction, and stop.
