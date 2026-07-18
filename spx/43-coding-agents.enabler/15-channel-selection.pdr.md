# Coding-Agent Channel Selection

Coding-agent communication is available only when public runtime evidence positively identifies the caller and a supported channel. Prowl panes are the sole supported channel; unsupported or ambiguous terminals fail explicitly without selecting a fallback.

## Rationale

One explicit channel keeps identity, delivery, and acknowledgement semantics inspectable. Heuristic fallback would turn missing authority into an apparently successful message on an unintended surface.

## Product properties

1. A supported caller receives the complete Prowl pane channel and identity values supplied by Prowl.
2. An unsupported or ambiguous caller receives a named unavailable result and no send occurs.
3. Transport delivery remains distinct from recipient acknowledgement and agreement.

## Verification

### Testing

- ALWAYS: a uniquely identified Prowl caller maps to the `prowl-pane` channel ([mapping])
- ALWAYS: unsupported and ambiguous callers map to named unavailable results without sending a message ([mapping])
- NEVER: communication falls back to transcript scanning, terminal titles, pane position, another terminal multiplexer, or operator relay ([compliance])
