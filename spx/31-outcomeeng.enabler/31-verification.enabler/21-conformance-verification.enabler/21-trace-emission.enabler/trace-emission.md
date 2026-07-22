# Trace Emission

PROVIDES the script-emitted workflow-trace substrate — a versioned JSONL event schema carrying sequence, skill instance, parent instance, state, success, duration, and argument digest, written to a sidecar path with append-atomic single-line writes
SO THAT conformance contracts, conformance checking, and contract inference
CAN read one ordered, instance-scoped record of what a skill's scripts actually did
