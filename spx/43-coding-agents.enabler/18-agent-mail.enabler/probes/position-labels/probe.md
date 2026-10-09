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

## Attested run

- Date: 2026-10-09
- Subject: Agent Mail source commit `1f309419df08062942ae2f0c29b0990cf631cf5c`, binary `am 0.3.36` with SHA-256 `84296033ef2dcfb60b0ffd1f153e672c0ed9dd167d6a24d1f49a723778002c23`, whose `agents register --help` declares `--display-name`. The adapter and the doorbell script ran from the sources of committed head `9aae2df424bf93f9fa0e268c0164e98046a3f3c8` under `src/plugins/coding-agents/skills/`.
- Environment: an isolated store and server on `127.0.0.1:8877` (`--no-auth`), restarted before step 1 so that the first registration and the first send were the first requests after startup. The mail project key resolved to the isolated demo repository's `.git` directory.
- Positions: sender `CopperFinch`, recipient `SilverFinch` (a name new to the store), a bracket-label sender `CopperLark`, and an unlabeled sender `CopperWren`. The first send after startup (step 2) went to `SilverOtter`, a recipient already in the store with the label `Capture Reader`; every later send went to `SilverFinch`.
- Observations:
  1. Registration of `CopperFinch` with the label `Probe Sender` returned `display_name: "Probe Sender"`; the adapter result carried no token ([01](attested-run/01-register-sender.json)).
  2. The first send after startup authenticated (exit 0, message 17). The send result carried `sender_display_name: "Probe Sender"` and `to_display_names: {"SilverOtter": "Capture Reader"}` ([02a](attested-run/02a-send-mail-request.json), [02b](attested-run/02b-send-after-startup.json)).
  3. Registration of `SilverFinch` with the label `Probe Recipient` returned that `display_name` ([03](attested-run/03-register-recipient.json)). A first attempt with the name `IvoryMarten` was refused by the store as an invalid name (adjective plus noun word list) and was replaced by `SilverFinch`; the refusal is not retained.
  4. A send from `CopperFinch` to `SilverFinch` authenticated (message 19) with `sender_display_name: "Probe Sender"` and `to_display_names: {"SilverFinch": "Probe Recipient"}` ([04a](attested-run/04a-send-mail-request.json), [04b](attested-run/04b-send.json)). The store also delivered an auto-accepted contact notice (message 18) to the recipient's inbox, from the sender.
  5. The doorbell composed through the doorbell script read `[Probe Sender <CopperFinch>] mail 19` ([05](attested-run/05-doorbell-labelled.json)).
  6. The recipient's inbox, without bodies and with bodies, carried `sender_display_name` and `to_display_names` on every item; with bodies each item also carried `body_md` ([06](attested-run/06-inbox-no-bodies.json), [07](attested-run/07-inbox-bodies.json)). The adapter's `data.records` reads back the record without any label; the labels appear only in `response`.
  7. Registration of `CopperFinch` again with the label `Renamed Sender` returned that label ([08](attested-run/08-reregister-sender-new-label.json)). The immediate send authenticated (message 20) with `sender_display_name: "Renamed Sender"` ([09a](attested-run/09a-send-mail-request.json), [09b](attested-run/09b-send-after-label-change.json)), and the doorbell read `[Renamed Sender <CopperFinch>] mail 20` ([10](attested-run/10-doorbell-after-label-change.json)). The inbox read afterwards showed `Renamed Sender` on messages 20, 19, and 18, including those sent under `Probe Sender`: the store resolves the sender label at read time, so a label change reaches earlier messages ([11](attested-run/11-inbox-after-label-change.json)).
  8. Label with bracket and angle-bracket punctuation. `CopperLark` registered with the full label value `Ops [lead] <west> ]` (characters: `Ops`, space, `[`, `lead`, `]`, space, `<`, `west`, `>`, space, `]`). The store returned it verbatim as `display_name`, and the send (message 21) carried it verbatim as `sender_display_name` ([13](attested-run/13-register-bracket-label.json), [14a](attested-run/14a-bracket-mail-request.json), [14b](attested-run/14b-bracket-send.json)). The doorbell took the unlabeled form `[CopperLark] mail 21`, with the full label preserved in the retained capability result inside the doorbell result ([15](attested-run/15-doorbell-bracket-label.json)). The inbox item for message 21 carried the full label ([18](attested-run/18-inbox-final.json)).
  9. A position registered with no label (`CopperWren`) sent message 22 with `sender_display_name: null`, and its doorbell read `[CopperWren] mail 22` ([12](attested-run/12-register-unlabeled.json), [16a](attested-run/16a-unlabeled-mail-request.json), [16b](attested-run/16b-unlabeled-send.json), [17](attested-run/17-doorbell-unlabeled.json)). The final inbox read carried `sender_display_name: null` for message 22 ([18](attested-run/18-inbox-final.json)).
- Artifacts: every step above links its request and result in the `attested-run` directory beside this file.

## Verdict

`passed`. A registration with a label followed by send, inbox, and doorbell showed the label on each surface: the registration result, the send result, the inbox items with and without bodies, and the labeled doorbell. The first send after startup and the first send after a label change each authenticated through the credential the registration left, with no further credential step.

## Limitations

The protocol exercises one installed `am` build and one isolated store. It does not exercise the event stream, because the adapter exposes no operation for it and the run uses no raw store command. It does not exercise a label carrying a line break, a label above the store's length limit, or concurrent registrations. The run exercises the label `Ops [lead] <west> ]`: the store records and returns it verbatim on the registration result, the send result, and the inbox item, and the doorbell script renders the unlabeled form `[CopperLark] mail 21` for it, leaving the full value in the capability result; other bracket or angle-bracket placements are covered by the communication node's tests. The first send after startup went to a recipient that already existed in the store, so the run observed the recipient's label there only through the send result. The run did not resolve a doorbell line back to its sender and did not deliver a doorbell into a pane.
