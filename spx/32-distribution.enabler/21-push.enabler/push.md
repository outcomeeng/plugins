# Push

PROVIDES a repository push wrapper that forwards the caller's complete argument sequence to `git push`
SO THAT marketplace maintainers and lifecycle workflows
CAN publish an explicit ref without coupling origin publication to marketplace installation

## Assertions

- Given caller-supplied push arguments including leading flags and explicit refspecs, when push runs, then every argument is forwarded verbatim to `git push` without parser interpretation.
- Given `git push` returns an exit code, when push runs, then push exits with the same code and performs no marketplace installation operation.
- Given caller arguments request git help, when push runs, then it checks only git availability before forwarding the help request.
- ALWAYS: push checks git availability before publication and requires no agent CLI, process-inspection, package-runner, marketplace, or installation dependency.
