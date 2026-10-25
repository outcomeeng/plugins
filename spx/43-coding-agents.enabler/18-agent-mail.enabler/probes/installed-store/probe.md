# Installed Store

The protocol lives at `probes/installed-store/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator relying on the agent-mail adapter expects every operation to reach the store through an argument vector the installed `am` accepts, and expects every response the adapter parses to be a shape that `am` emits. The uncertainty is grammar and response drift: one `am` version string covers builds with different command grammars and different response fields, so the adapter's argument vectors and parsers can disagree with the installed build while every deterministic test passes against captured fixtures. The probe drives each operation against the installed store, and its attested run is the one home of the build pin and the source of every captured usage and public-response fixture.

## Environment and preconditions

- The installed native `am` is the build under test. The run records the Agent Mail source commit it was built from and the binary's SHA-256, taken from the executable the adapter invokes; `am --version` is recorded as reported and identifies no build.
- The store is isolated: a disposable mail project whose key the repository itself resolves, a writable store, and no foreign records. The run touches no persistent store.
- Three positions with distinct stable names exist: a sender, a recipient, and a second recipient. Each registers through the adapter with its own label.
- The adapter runs from the sources of the committed head under test, through `python3 "${CLAUDE_SKILL_DIR}/scripts/agent_mail.py" run` for each request operation, with each request written to a scratch file and submitted through the input redirect.
- No step constructs a raw `am` command except the observation steps that record the build and capture usage text.

## Protocol

1. Record the build: the path of the executable the adapter invokes, its `am --version` output, its SHA-256, and the Agent Mail source commit it was built from.
2. Capture the usage text of every store command the adapter builds an argument vector for, from the installed `am`, and retain each as a fixture naming the tool and the build recorded in step 1.
3. Register the sender, the recipient, and the second recipient through the adapter's register operation, each with a label. Record that each result is `succeeded` and that the adapter accepted every argument it passed.
4. Send one record from the sender to the recipient with an acknowledgement required, and one record whose correlation lies outside the store's thread alphabet. Record that each is `succeeded`, that the store assigned an id, and that the outside-alphabet correlation round-trips through the stored thread id.
5. List the recipient's records without options. Record the argument vector, that the store accepted it, that every listed record is unread, and the response shape each record carries.
6. List the recipient's records with the all-records option, with bodies, and with a limit. Record that the store accepted each vector and that the response shape parses.
7. Wait for the recipient with an `afterId` below the first sent id and a short timeout. Record the `received` outcome. Wait again with an `afterId` equal to the last sent id and record the `timeout` outcome.
8. List the recipient's records unjudged, then again, and record that neither listing, nor either wait, changed any record's read state.
9. Read the first record as the recipient through the adapter's read operation. Record that the store accepted the vector, that the read state of that record changed for the recipient, and that the sender's view of the record shows no acknowledgement.
10. Acknowledge the second record as the recipient through the adapter's acknowledge operation. Record that the store accepted the vector and that the sender observes the acknowledgement.
11. List the recipient's records unjudged and with the all-records option. Record that the read record and the acknowledged record leave the unjudged listing and remain in the complete listing, and that a record whose acknowledgement status is owed or given reads back with `ackRequired` true.
12. Submit a request carrying a text argument with a NUL byte, a correlation whose written thread id exceeds 128 characters, and a request that does not parse. Record that each is rejected before any store command runs, with the versioned result shape.
13. Retain the request, the adapter result, and the store's raw response for every step as structured output beside this file, with the fixtures from step 2.

## Attested run

No run is attested.

## Verdict

No verdict is recorded before an attested run.

## Limitations

The protocol exercises one installed `am` build and one isolated store. It does not exercise concurrent senders, a store whose project holds foreign records of unusual shapes, a registration refused by the store's name rules, or a runner failure class such as an absent binary; the deterministic tests cover those against fixtures the run captures. It reads the sender's view of an acknowledgement and a read through the store's own surfaces, because the adapter exposes no operation that reports a record from the sender's side.
