<required_reading>

`${CLAUDE_SKILL_DIR}/references/authority.md` and `${CLAUDE_SKILL_DIR}/references/classifier-triggers.md`.

</required_reading>

<process>

1. Take the Frame or Slice from the Maintainer that brings it, by mail: the Change's link and the exact Frame or Slice. A Frame or Slice no Maintainer brings is not attested.
2. Read the Change from the store the repository's coordination overlay declares (`gh issue view` for a GitHub store) and compare the Frame or Slice with the operator's direction and intent recorded in the note and with the theme in force. Verify every claim the mail makes against the Change.
3. Decide:
   - Inside the direction and intent: answer yes.
   - Outside it, or short of what the direction names: answer with the exact change the Maintainer makes.
   - A question the direction leaves unsettled: raise it to the operator through the structured-question tool, with the exact passage and link, after every action that does not depend on the answer.
4. Use skill `coding-agents:message-agents` to answer the Maintainer that brought it, stating the judgment and its ground in the operator's direction. Write the answer as the Director's judgment, with no authority text and no restated Change.
5. Append one dated line to the note: the Change, what was attested or confirmed, and the mail id of the answer.

The Maintainer's publication records the attestation. The Director writes no Change, adds no text to one and restates none.

</process>

<success_criteria>

- Every Frame attested and Slice confirmed lies inside the operator's direction, and the answer names the change when it does not.
- Every answer went to the Maintainer that brought the Frame or Slice, and no Change carries text the Director wrote.

</success_criteria>
