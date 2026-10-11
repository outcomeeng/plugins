# Position Labels

The protocol lives at `probes/position-labels/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator reading a pane doorbell, an inbox item, or a send result expects the human-readable label of the position that sent the mail, beside the stable name, without ever running a label command. The uncertainty is whether the installed native `am` records the label that an owner's registration supplies at normal startup and at resume, keeps the owner's stable agent id and message history across a rename and a clear, permits duplicate position labels, and authenticates the next send without exposing a credential, and whether a real owner session resumed through the shipped `recover-prowl-agents` path registers its assigned position label before its first mail.

## Environment and preconditions

- The installed native `am` carries `agents register --display-name` and the label fields in its results; `am --version` reports the version the adapter decision pins.
- The repository resolves a mail project in an isolated store, and the store is writable.
- Two positions with distinct stable names exist for the lifecycle steps, and a third position holds the same label as the first to exercise duplicates.
- The resumed owner starts with its stored label absent or deliberately different from its assigned position label. The owner prepares this state itself in the isolated store through its own registration, with no operator label command and no registration of another identity.
- The owner session is a real coding-agent session whose position assignment supplies its ordinary label and whose resume note retains that assignment.

## Protocol

1. Start a fresh session with no cached credential. Register the owner through `src/plugins/coding-agents/skills/operate-agent-mail/scripts/agent_mail.py` at normal startup with the label from its position assignment, and record the stable agent id and the label the result returns.
2. Send one message to the recipient immediately, and record that the send authenticates, that no credential appears in any request or result, and that the send result carries the owner's `sender_display_name`.
3. Rename: register the same owner again with a different label, and record that the stable agent id is unchanged. Send immediately, and record that the send authenticates and carries the new label. Read the recipient's inbox, and record that earlier messages remain present under the same ids.
4. Clear: register the same owner with a blank label, and record that the stable agent id is unchanged and the label is cleared. Send immediately, and record that the send authenticates and `sender_display_name` is empty or null.
5. Duplicate labels: register a second position with the same label as the first, and record that the store accepts it and that both positions keep distinct stable names and ids.
6. Resume: prepare the precondition by leaving the owner's stored label absent or different from its assigned position label. Resume the real owner session through the shipped `recover-prowl-agents` path, with its assigned position context supplying the ordinary label, and issue no operator label command. Record that the owner registers its assigned label before its first mail and registers no other identity.
7. Have the resumed owner send its first mail to the recipient. Record the owner session, the sent message with its `sender_display_name`, the recipient's inbox read of that message, and the doorbell pointer that message produces.
8. Retain the request and result of every step as structured output beside this file.

## Retained evidence

- The owner session, identified by its full session identity.
- The message the resumed owner sent.
- The recipient's inbox read that returns that message.
- The doorbell pointer for that message.
- The request and result of steps 1 through 5 as structured output.

## Attested run

Pending. The Author executes the protocol after the node's last Mutation row and records the date, the subject build identity, the environment, each observation with links to its retained artifacts, and the verdict here.

## Verdict

Pending the attested run.

## Limitations

The protocol exercises one installed `am` build and one isolated store. It does not exercise the event stream, a label carrying a line break, a label above the store's length limit, or concurrent registrations. It does not resolve a doorbell line back to its sender and does not deliver a doorbell into a pane. The resume step covers one native-agent recovery path in one environment.
