#!/bin/bash
# PostToolUse hook for the spec-tree:applying skill.
# Fires after each Skill tool invocation. Returns additionalContext
# reminding the agent to invoke the corresponding audit skill.

INPUT=$(cat)
SKILL=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')

case "$SKILL" in
  *architecting-*)
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "GATE: Architecture phase complete. Invoke the architecture auditing skill NOW before proceeding to Phase 5 (tests)."
      }
    }'
    ;;
  *testing-python*|*testing-typescript*)
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "GATE: Testing phase complete. Invoke the test auditing skill NOW before proceeding to Phase 7 (implementation)."
      }
    }'
    ;;
  *coding-python*|*coding-typescript*)
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "GATE: Implementation phase complete. Invoke the code auditing skill NOW before declaring done."
      }
    }'
    ;;
esac
exit 0
