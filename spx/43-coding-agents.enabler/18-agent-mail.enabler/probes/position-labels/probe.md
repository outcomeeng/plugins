# Position Labels

The protocol lives at `probes/position-labels/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator reading a pane doorbell, an inbox item, or a send result expects the human-readable label of the position that sent the mail, beside the stable name. The uncertainty is whether the installed native `am` records the label a registration supplies, returns it on every result surface, and authenticates a send right after startup and right after a label change, so the label the adapter carries is the label a reader sees.

## Environment and preconditions

- The installed native `am` carries `agents register --display-name` and the label fields in its results; `am --version` reports the version the adapter decision pins.
- The repository resolves a mail project, and the store is writable.
- Two positions with distinct stable names exist, and the protocol registers each with its own label.

## Protocol

1. Start a fresh session with no cached credential and register the sender through `/operate-agent-mail` with a label.
2. Send one message to the recipient immediately, and record that the send authenticates and that the send result carries the sender's `sender_display_name` and the recipient's entry in `to_display_names`.
3. Register the recipient with its own label, read its inbox with and without bodies, and read the event stream; record `sender_display_name` on each item and event.
4. Compose the doorbell for the send result through `/message-agents` and record that it reads `[<Label> <<StableName>>] mail <id>`.
5. Register the sender again with a different label, send again immediately, and record that the send authenticates and the new label appears on each surface.
6. Register a position with no label and record that its doorbell reads `[<StableName>] mail <id>`.
7. Retain the request and result of every step as structured output beside this file.

## Limitations

The protocol exercises one installed `am` build and one store. It does not exercise labels carrying a line break or any of `[`, `]`, `<`, `>`, whose doorbell rendering the communication node's tests cover, and it does not exercise concurrent registrations.
