---
name: create-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring subagents.
  NEVER create subagents without this skill.
allowed-tools: Read, Glob, Write, Edit, Skill, AskUserQuestion
---

Invoke the `instructions:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A subagent configured for an isolated, focused role — its system prompt, tool access, and isolated-workflow orchestration.
</objective>

<quick_start>

<workflow>

1. Run `/agents` command
2. Select "Create New Agent"
3. Choose product-scope (`.claude/agents/`) or user-scope (`~/.claude/agents/`)
4. Define the subagent:
   - **name**: lowercase-with-hyphens
   - **description**: When should this subagent be used?
   - **tools**: Optional comma-separated list (inherits all if omitted)
   - **model**: Optional (`opus`, `sonnet`, `haiku`, or `inherit`)
   - **skills**: Optional array of skill names to inject at startup
5. Write the system prompt (the subagent's instructions)
6. Include the post-skill invocation-check handoff from `<invocation_check_boundary>` in the result.

</workflow>

<example>
Read `${CLAUDE_SKILL_DIR}/references/subagents.md` for complete subagent file examples and field references.
</example>
</quick_start>

<file_structure>

<claude_storage_locations>

Priority order:

1. Product: `.claude/agents/` for the current product
2. CLI: `--agents` flag for the current session
3. User: `~/.claude/agents/` for all projects
4. Plugin: plugin `agents/` directory for all projects

</claude_storage_locations>

Product-scope subagents override user-scope when names conflict.
</file_structure>

<configuration>
<field name="name">

- Lowercase letters and hyphens only
- Must be unique

</field>

<field name="description">
- Natural language description of purpose

- Include when Claude should invoke this subagent
- Used for automatic subagent selection

</field>

<field name="tools">

- Comma-separated list: `Read, Write, Edit, Bash, Grep`
- If omitted: inherits all tools from main thread
- Use `/agents` interface to see all available tools

</field>

<field name="model">
- `opus`, `sonnet`, `haiku`, or `inherit`
- Prefer an explicit model alias when reproducibility matters.
- Use `sonnet` for verification, audit, review, and evidence-producing agents.
- Use `haiku` only when the owning workflow accepts lower-cost execution for simple or high-volume tasks.
- NEVER use `inherit` for verification, audit, review, or other reproducibility-sensitive agents.

</field>

<field name="skills">
- Array of skill names to inject into the subagent's context at startup
- The full SKILL.md content of each listed skill is loaded before the subagent runs
- Subagents do NOT inherit skills from the parent conversation — list every needed skill explicitly
- The subagent receives skill content as reference material, not as dynamically invocable skills
- If omitted: no skills injected

```yaml
skills:
  - audit-typescript-code
  - test-typescript
```

</field>

</configuration>

<execution_model>
<critical_constraint>

**Subagents are black boxes that cannot interact with users.**

Subagents run in isolated contexts and return their final output to the main conversation. They:

- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use AskUserQuestion** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees isolated-workflow intermediate steps**

The main conversation sees only the isolated workflow's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with subagents:**

Use **main chat** for:

- Gathering requirements from user (AskUserQuestion)
- Presenting options or decisions to user
- Any task requiring user confirmation/input
- Work where user needs visibility into progress

Use **subagents** for:

- Research tasks (API documentation lookup, code analysis)
- Code generation based on pre-defined requirements
- Analysis and reporting (security review, test coverage)
- Context-heavy operations that don't need user interaction

**Example workflow pattern:**

```
Main Chat: Ask user for requirements (AskUserQuestion)
↓
subagent: Research API and create documentation (no user interaction)
↓
Main Chat: Review research with user, confirm approach
↓
subagent: Generate code based on confirmed plan
↓
Main Chat: Present results, handle testing/deployment
```

</workflow_design>
</execution_model>

<system_prompt_guidelines>
<principle name="be_specific">
Clearly define the subagent's role, capabilities, and constraints.
</principle>

<principle name="use_pure_xml_structure">
Structure the system prompt with pure XML tags. Remove ALL markdown headings from the body.

```text
---
name: security-reviewer
description: Reviews code for security vulnerabilities. Use after security-sensitive code changes or before release.
tools: Read, Grep, Glob, Bash
model: sonnet
---

<role>
Claude is a senior code reviewer specializing in security.
</role>

<focus_areas>

- SQL injection vulnerabilities
- XSS attack vectors
- Authentication/authorization issues
- Sensitive data exposure

</focus_areas>

<workflow>
1. Read the modified files
2. Identify security risks
3. Provide specific remediation steps
4. Rate severity (Critical/High/Medium/Low)
</workflow>
```

</principle>

<principle name="task_specific">
Tailor instructions to the specific task domain. Don't create generic "helper" subagents.

❌ Bad: "Helpful assistant for code"
✅ Good: "Claude is a React component refactoring specialist. Analyze components for hooks best practices, performance anti-patterns, and accessibility issues."
</principle>
</system_prompt_guidelines>

<configured_agent_xml_structure>
subagent file bodies are system prompts consumed by the target runtime. Like skills and slash commands, they should use pure XML structure for parsing and token efficiency.

<recommended_tags>
Common tags for subagent structure:

- `<role>` - Who the subagent is and what it does
- `<constraints>` - Hard rules (NEVER/MUST/ALWAYS)
- `<focus_areas>` - What to prioritize
- `<workflow>` - Step-by-step process
- `<output_format>` - How to structure deliverables
- `<success_criteria>` - Completion criteria
- `<validation>` - How to verify work

</recommended_tags>

<intelligence_rules>
**Simple subagents** (single focused task):

- Use role + constraints + workflow minimum
- Example: code-reviewer, test-runner

**Medium subagents** (multi-step process):

- Add workflow steps, output_format, success_criteria
- Example: api-researcher, documentation-generator

**Complex subagents** (research + generation + validation):

- Add all tags as appropriate including validation, examples
- Example: mcp-api-researcher, comprehensive-auditor

</intelligence_rules>

<critical_rule>
**Remove ALL markdown headings (##, ###) from subagent body.** Use semantic XML tags instead.

Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).

For XML structure principles and token efficiency details, read `/skill-standards` — the same principles apply to subagents.
</critical_rule>
</configured_agent_xml_structure>

<invocation>

<automatic>
Claude automatically selects subagents based on the `description` field when it matches the current task.
</automatic>

<explicit>
Explicitly invoke a subagent:

```
> Use the code-reviewer subagent to check my recent changes
```

```
> Have the test-writer subagent create tests for the new API endpoints
```

</explicit>
</invocation>

<management>
<using_agents_command>

Run `/agents` for an interactive interface to:

- View all available subagents
- Create new subagents
- Edit existing subagents
- Delete custom subagents

</using_agents_command>

<manual_editing>
Edit subagent files directly:

- Product: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`

</manual_editing>
</management>

<invocation_check_boundary>
Include a target-specific invocation-check handoff with every created or edited configuration. Keep the invocation outside this skill's restricted execution; its `allowed-tools` intentionally omit subagent-spawn authority.

The handoff names the configured `subagent_type`, the expected final-message fields or sections, and the `completed` result required from the Agent tool.

</invocation_check_boundary>

<reference>
Read only the reference group needed for the current task.

**Configuration and prompt authoring**:

- [subagents.md](${CLAUDE_SKILL_DIR}/references/subagents.md): file format, configuration, skill injection, model selection, tool security, prompt caching, complete examples.
- [write-subagent-prompts.md](${CLAUDE_SKILL_DIR}/references/write-subagent-prompts.md): prompt structure, description routing, extended thinking, security constraints, success criteria.

**Evaluation and recovery**:

- [evaluation-and-testing.md](${CLAUDE_SKILL_DIR}/references/evaluation-and-testing.md): evaluation metrics, testing strategies, evaluation-driven development, G-Eval.
- [error-handling-and-recovery.md](${CLAUDE_SKILL_DIR}/references/error-handling-and-recovery.md): failure causes, recovery strategies, observability, anti-patterns.

**Context, orchestration, and debugging**:

- [context-management.md](${CLAUDE_SKILL_DIR}/references/context-management.md): memory architecture, context strategies, long-running tasks, prompt caching.
- [orchestration-patterns.md](${CLAUDE_SKILL_DIR}/references/orchestration-patterns.md): sequential, parallel, hierarchical, and coordinator patterns with model-selection guidance.
- [debugging-agents.md](${CLAUDE_SKILL_DIR}/references/debugging-agents.md): logging, tracing, hallucinations, format errors, tool misuse, diagnostic procedures.

</reference>

<failure_modes>

**Failure: Runtime-specific examples made SKILL.md exceed the line budget**

What happened: Claude added target-specific TOML/YAML examples directly to this SKILL.md until the authored source exceeded `/skill-standards`' 500-line cap.

Why it failed: The fast path stopped being an overview and absorbed detail that belongs in references.

How to avoid: Keep SKILL.md under 500 lines; move extended examples and configuration matrices to the cited references, then run `wc -l "${CLAUDE_SKILL_DIR}/SKILL.md"` before audit.

</failure_modes>

<success_criteria>
A well-configured subagent has:

- A YAML-frontmatter file whose name matches the filename and whose configured name and scope appear in `/agents` after saving
- A `system prompt` containing XML-structured role, workflow, constraints, and output expectations
- Every declared tool mapped to at least one workflow step, with no workflow step requiring an undeclared tool
- A post-skill Agent-tool invocation record produced from the handoff, using the configured name as `subagent_type` and reaching `completed`; its final message contains every field or section declared by the output expectations

- A description that states both what the subagent does and when to invoke it
- A model identifier accepted by the target harness and consistent with the configuration's stated capability, cost, and reproducibility requirements
- The target-specific invocation check rerun after every configuration edit as a post-skill step outside this skill's restricted execution

</success_criteria>
