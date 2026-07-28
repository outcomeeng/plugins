# Platform Boundary

PROVIDES the fit/rejection policy for choosing GitHub Actions over local hooks, repository scripts, scheduled services, or alternative CI platforms
SO THAT workflow design, workflow evolution, and any skill that fields a "should we automate this on Actions?" request
CAN evaluate hosted-automation choices against an explicit policy rather than ad hoc preference

## Assertions

### Compliance

- ALWAYS: a recommendation to use GitHub Actions names the alternatives considered (local hooks, repository scripts, schedulers, alternative CI) and the concrete reason Actions was selected — alternatives are part of the decision record, never retrospective justification ([audit])
- ALWAYS: a recommendation against GitHub Actions names the constraint that disqualifies it (cost, runner trust, latency, secret exposure, vendor coupling) so the rejection is durable ([audit])
- NEVER: recommend GitHub Actions for tasks that the developer can run on a local pre-commit hook with the same evidence — local hooks fail faster and avoid runner cost ([audit])
