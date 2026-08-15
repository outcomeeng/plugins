# Issues

PROVIDES the opening and management of an issue in a repository the operator does not control
SO THAT an observation about that repository's behavior
CAN reach its maintainer as a report the maintainer can act on without access to the operator's machine

An issue is a report, not a change. Its value is whether the maintainer can reproduce what it describes, so the report carries the conditions of the observation rather than its conclusion alone.

An issue thread is the maintainer's. A reply answers what was asked and adds the evidence the answer needs; the flow reads the thread's current state once and acts on it.

## Assertions

### Compliance

- ALWAYS: a report states the observation, the environment it was observed in, and the exact command or interaction that produced it, so the maintainer can reproduce it without the operator's machine ([audit])
- ALWAYS: a report distinguishes what was observed from what was inferred, and marks an unreproduced condition as unverified rather than asserting it ([audit])
- ALWAYS: a reply to a maintainer answers the question asked before adding anything else ([audit])
- NEVER: the management pass polls, watches, or waits on the issue — it reads current state once, acts on it, and returns ([audit])
