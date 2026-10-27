# Position Labels

The protocol lives at `probes/position-labels/probe.md`, the target of the assertion's `[probe]` tag. Working runs stay in an ignored `runs/` inside this directory; every attested run retains at least one inspectable artifact beside this file.

## Intent

An operator reading a pane doorbell, an inbox item, or a send result expects the human-readable label of the position that sent the mail, beside the stable name. The uncertainty is whether the installed native `am` records the label a registration supplies, returns it on every result surface, and authenticates a send right after startup and right after a label change, so the label the adapter carries is the label a reader sees.

## Environment and preconditions

- The installed native `am` carries `agents register --display-name` and the label fields in its results; `am --version` reports the version string that the attested run of `probes/installed-store/probe.md` records as the build pin. The version string identifies no build, so the run's registration result, which carries `display_name`, is the check that the installed build carries the label fields.
- The adapter resolves a mail project from a scratch Git repository, and the store is writable. The installed `am` ignores environment overrides of its store, so the run writes to the installed store under the scratch project key.
- Two positions with distinct stable names exist, and the protocol registers each with its own label.

## Protocol

1. Start a fresh session with no cached credential and register the sender through `/operate-agent-mail` with a label.
2. Send one message to the recipient immediately, and record that the send authenticates and that the send result carries the sender's `sender_display_name` and the recipient's entry in `to_display_names`.
3. Register the recipient with its own label, read its inbox with and without bodies; record `sender_display_name` on each item.
4. Compose the doorbell for the send result through `/message-agents` and record that it reads `[<Label> <<StableName>>] mail <id>`.
5. Register the sender again with a different label, send again immediately, and record that the send authenticates and the new label appears on each surface.
6. Register a position with no label and record that its doorbell reads `[<StableName>] mail <id>`.
7. Retain the request and result of every step as structured output beside this file.

## Attested run

- Date: 2026-10-25
- Subject: the adapter and the doorbell script at committed head `02b557b2a3dae8a9131e66a34abb948cb577672c` under `src/plugins/coding-agents/skills/`, driving the installed `am 0.3.36`, which reports no source commit; the build pin is that version string, recorded in `probes/installed-store/probe.md`. The registration results carry `display_name`, so the installed build carries the label fields.
- Environment: the installed store under the scratch project key `/private/tmp/claude-502/-Users-shz-Code-outcomeeng-plugins-worktrees-contributor-4/4d58f2f5-4e26-4e2d-aa23-2117c0421768/scratchpad/pl-repo2/.git`, a key no earlier run used. The store was not restarted, because the installed `am` ignores environment overrides.
- Positions: sender `CopperFinch`, recipient `SilverFinch`, a bracket-label sender `CopperLark`, an unlabeled sender `CopperWren`, and `SilverOtter`, a recipient registered beforehand with the label `Capture Reader` ([00](attested-run/00-register-prelabelled-recipient.json)). The first send went to `SilverOtter`; every later send went to `SilverFinch`.
- Observations:
  1. Registration of `CopperFinch` with the label `Probe Sender` returned `display_name: "Probe Sender"` ([01](attested-run/01-register-sender.json)).
  2. The first send after that registration authenticated, id 18801, and the send result carried `sender_display_name: "Probe Sender"` and `to_display_names: {"SilverOtter": "Capture Reader"}` ([02a](attested-run/02a-send-mail-request.json), [02b](attested-run/02b-send-after-startup.json)).
  3. Registration of `SilverFinch` with the label `Probe Recipient` returned that `display_name` ([03](attested-run/03-register-recipient.json)).
  4. A send from `CopperFinch` to `SilverFinch` authenticated (id 18803) with `sender_display_name: "Probe Sender"` and `to_display_names: {"SilverFinch": "Probe Recipient"}` ([04a](attested-run/04a-send-mail-request.json), [04b](attested-run/04b-send.json)). The store also delivered an auto-accepted contact notice (id 18802) to the recipient, from the sender.
  5. The doorbell composed through the doorbell script read `[Probe Sender <CopperFinch>] mail 18803` ([05](attested-run/05-doorbell-labelled.json)).
  6. The recipient's inbox, without and with bodies, carried `sender_display_name` and `to_display_names` on every item; with bodies each item also carried `body_md` ([06](attested-run/06-inbox-no-bodies.json), [07](attested-run/07-inbox-bodies.json)). The adapter's `data.records` carries no label; the labels appear only in `response`.
  7. Registration of `CopperFinch` again with the label `Renamed Sender` returned that label ([08](attested-run/08-reregister-sender-new-label.json)). The immediate send authenticated (id 18804) with `sender_display_name: "Renamed Sender"` ([09a](attested-run/09a-send-mail-request.json), [09b](attested-run/09b-send-after-label-change.json)), and the doorbell read `[Renamed Sender <CopperFinch>] mail 18804` ([10](attested-run/10-doorbell-after-label-change.json)). The complete listing afterwards showed `Renamed Sender` on 18804, 18803, and 18802, including the records sent under `Probe Sender`: the store resolves the label at read time ([11](attested-run/11-inbox-after-label-change.json)).
  8. `CopperLark` registered with the label `Ops [lead] <west> ]`; the store returned it verbatim as `display_name`, and the send (id 18805) carried it verbatim as `sender_display_name` ([13](attested-run/13-register-bracket-label.json), [14a](attested-run/14a-bracket-mail-request.json), [14b](attested-run/14b-bracket-send.json)). The doorbell took the unlabeled form `[CopperLark] mail 18805` ([15](attested-run/15-doorbell-bracket-label.json)).
  9. `CopperWren`, registered with no label, sent id 18806 with `sender_display_name: null`, and its doorbell read `[CopperWren] mail 18806` ([12](attested-run/12-register-unlabeled.json), [16a](attested-run/16a-unlabeled-mail-request.json), [16b](attested-run/16b-unlabeled-send.json), [17](attested-run/17-doorbell-unlabeled.json)). The final complete listing carried `sender_display_name: null` for 18806 ([18](attested-run/18-inbox-final.json)).
- Artifacts: every step above links its request and result in the `attested-run` directory beside this file.

## Verdict

`passed`. A registration with a label followed by send, list, and doorbell showed the label on each surface: the registration result, the send result, the listed items with and without bodies, and the labeled doorbell. The first send after a registration and the first send after a label change each authenticated through the credential the registration left, with no further credential step. The store was not restarted, so the claim that a send right after startup authenticates rests on the first send under a project key no earlier run used.

## Limitations

The protocol exercises one installed `am` build, identified only by its version string because the CLI reports no source commit, and one store under a scratch project key; the installed `am` ignores environment overrides, so isolation holds by project key only. It does not exercise a send right after a store restart, because the run does not restart the shared store. It does not exercise a label carrying a line break, a label above the store's length limit, or concurrent registrations. The run exercises the label `Ops [lead] <west> ]`: the store records and returns it verbatim on the registration result, the send result, and the inbox item, and the doorbell script renders the unlabeled form `[CopperLark] mail 21` for it, leaving the full value in the capability result; other bracket or angle-bracket placements are covered by the communication node's tests. The first send went to a recipient registered beforehand, so the run observed that recipient's label there only through the send result. The run did not resolve a doorbell line back to its sender and did not deliver a doorbell into a pane.
