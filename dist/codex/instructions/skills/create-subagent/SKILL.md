---
name: create-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring custom agents.
  NEVER create custom agents without this skill.
allowed-tools: Read, Glob, Write, Edit, Skill
---

Invoke the `instructions:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A custom agent configured for an isolated, focused role — its developer instructions, tool access, and isolated-workflow orchestration.
</objective>

<quick_start>

<workflow>

1. Create a standalone TOML file under `.codex/agents/` for product scope or `~/.codex/agents/` for user scope.
2. Define the custom agent:
   - **name**: unique identifier Codex uses when spawning or referring to this agent
   - **description**: human-facing guidance for when Codex should use this agent
   - **developer_instructions**: core instructions that define the custom agent's behavior
   - **model**: Optional model override
   - **model_reasoning_effort**: Optional reasoning setting
   - **sandbox_mode**, **mcp_servers**: Optional runtime configuration overrides
3. Write the developer instructions with clear role, constraints, workflow, and output expectations.
4. Include the post-skill invocation-check handoff from `<invocation_check_boundary>` in the result.

</workflow>

<example>
Read `${SKILL_DIR}/references/subagents.md` for complete custom agent file examples and field references.
</example>
</quick_start>

<file_structure>

<codex_storage_locations>

Priority order:

1. Product: `.codex/agents/` for the current product
2. User: `~/.codex/agents/` for all projects

</codex_storage_locations>

Product-scope custom agents override user-scope when names conflict.
</file_structure>

<configuration>
<field name="name">

- Unique identifier Codex uses when spawning or referring to this agent
- Matching the filename to the custom agent name is the simplest convention

</field>

<field name="description">
- Natural language description of purpose

- Guides selection after the user explicitly asks Codex for this custom agent or subagent workflow

</field>

<field name="developer_instructions">

- Required multiline TOML string that defines the custom agent's behavior
- Use clear role, constraints, workflow, and output expectations
- Prefer XML structure inside the string for prompt clarity

</field>

<field name="model">
- Optional model override
- Use explicit models for verification, audit, review, and evidence-producing agents
- Choose a faster, lower-cost model only when the owning workflow accepts that tradeoff

</field>

<field name="model_reasoning_effort">
- Optional reasoning setting
- Use `high` for complex logic, security review, or edge-case analysis
- Use `medium` as the default for most custom agents
- Use `low` only for straightforward work where speed matters

</field>

<field name="sandbox_mode">
- Optional sandbox override
- Use `read-only` for exploration, audit, and review agents that must not edit files

</field>

</configuration>

<execution_model>
<critical_constraint>

**Custom agent workflows are black boxes that cannot interact with users.**

Custom agents run in isolated contexts and return their final output to the main conversation. They:

- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use request_user_input** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees isolated-workflow intermediate steps**

The main conversation sees only the isolated workflow's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with custom agents:**

Use **main chat** for:

- Gathering requirements from user (request_user_input)
- Presenting options or decisions to user
- Any task requiring user confirmation/input
- Work where user needs visibility into progress

Use **custom agents** for:

- Research tasks (API documentation lookup, code analysis)
- Code generation based on pre-defined requirements
- Analysis and reporting (security review, test coverage)
- Context-heavy operations that don't need user interaction

**Example workflow pattern:**

```
Main Chat: Ask user for requirements (request_user_input)
↓
custom agent: Research API and create documentation (no user interaction)
↓
Main Chat: Review research with user, confirm approach
↓
custom agent: Generate code based on confirmed plan
↓
Main Chat: Present results, handle testing/deployment
```

</workflow_design>
</execution_model>

<system_prompt_guidelines>
<principle name="be_specific">
Clearly define the custom agent's role, capabilities, and constraints.
</principle>

<principle name="use_pure_xml_structure">
Structure the developer instructions with pure XML tags. Remove ALL markdown headings from the body.

```toml
name = "security_reviewer"
description = "Reviews code for security vulnerabilities. Use after security-sensitive code changes or before release."
sandbox_mode = "read-only"
model = "gpt-5.4"
developer_instructions = """
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
"""
```

</principle>

<principle name="task_specific">
Tailor instructions to the specific task domain. Don't create generic "helper" custom agents.

❌ Bad: "Helpful assistant for code"
✅ Good: "Claude is a React component refactoring specialist. Analyze components for hooks best practices, performance anti-patterns, and accessibility issues."
</principle>
</system_prompt_guidelines>

<configured_agent_xml_structure>
custom agent file bodies are developer instructions consumed by the target runtime. Like skills and slash commands, they should use pure XML structure for parsing and token efficiency.

<recommended_tags>
Common tags for custom agent structure:

- `<role>` - Who the custom agent is and what it does
- `<constraints>` - Hard rules (NEVER/MUST/ALWAYS)
- `<focus_areas>` - What to prioritize
- `<workflow>` - Step-by-step process
- `<output_format>` - How to structure deliverables
- `<success_criteria>` - Completion criteria
- `<validation>` - How to verify work

</recommended_tags>

<intelligence_rules>
**Simple custom agents** (single focused task):

- Use role + constraints + workflow minimum
- Example: code-reviewer, test-runner

**Medium custom agents** (multi-step process):

- Add workflow steps, output_format, success_criteria
- Example: api-researcher, documentation-generator

**Complex custom agents** (research + generation + validation):

- Add all tags as appropriate including validation, examples
- Example: mcp-api-researcher, comprehensive-auditor

</intelligence_rules>

<critical_rule>
**Remove ALL markdown headings (##, ###) from custom agent body.** Use semantic XML tags instead.

Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).

For XML structure principles and token efficiency details, read `/skill-standards` — the same principles apply to custom agents.
</critical_rule>
</configured_agent_xml_structure>

<invocation>

<explicit_request>
Codex uses custom agent descriptions to select the right agent after the user explicitly asks for a custom agent or subagent workflow.
</explicit_request>

<explicit>
Explicitly invoke a custom agent:

```
> Use the code-reviewer custom agent to check my recent changes
```

```
> Have the test-writer custom agent create tests for the new API endpoints
```

</explicit>
</invocation>

<management>
<using_agents_command>

Edit `.codex/agents/*.toml` or `~/.codex/agents/*.toml` files to:

- Create new custom agents
- Edit existing custom agents and their configuration
- Choose project-scoped or user-scoped behavior

Use `/agent` to switch between active agent threads and inspect running custom agents.

</using_agents_command>

<manual_editing>
Edit custom agent files directly:

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`

</manual_editing>
</management>

<invocation_check_boundary>
Include a target-specific invocation-check handoff with every created or edited configuration. Keep the invocation outside this skill's restricted execution; its `allowed-tools` intentionally omit custom agent-spawn authority.

The handoff names the configured `agent_type` and expected final-message fields or sections. It requires `spawn_agent` to return an `agent_id`, preserves that exact identifier, collects `wait_agent` until the identifier reaches `completed`, validates the completed final message, and closes the completed thread with `close_agent`.

</invocation_check_boundary>

<reference>
Read only the reference group needed for the current task.

**Configuration and prompt authoring**:

- [subagents.md](${SKILL_DIR}/references/subagents.md): file format, configuration, skill injection, model selection, tool security, prompt caching, complete examples.
- [write-subagent-prompts.md](${SKILL_DIR}/references/write-subagent-prompts.md): prompt structure, description routing, extended thinking, security constraints, success criteria.

**Evaluation and recovery**:

- [evaluation-and-testing.md](${SKILL_DIR}/references/evaluation-and-testing.md): evaluation metrics, testing strategies, evaluation-driven development, G-Eval.
- [error-handling-and-recovery.md](${SKILL_DIR}/references/error-handling-and-recovery.md): failure causes, recovery strategies, observability, anti-patterns.

**Context, orchestration, and debugging**:

- [context-management.md](${SKILL_DIR}/references/context-management.md): memory architecture, context strategies, long-running tasks, prompt caching.
- [orchestration-patterns.md](${SKILL_DIR}/references/orchestration-patterns.md): sequential, parallel, hierarchical, and coordinator patterns with model-selection guidance.
- [debugging-agents.md](${SKILL_DIR}/references/debugging-agents.md): logging, tracing, hallucinations, format errors, tool misuse, diagnostic procedures.

</reference>

<failure_modes>

**Failure: Runtime-specific examples made SKILL.md exceed the line budget**

What happened: Claude added target-specific TOML/YAML examples directly to this SKILL.md until the authored source exceeded `/skill-standards`' 500-line cap.

Why it failed: The fast path stopped being an overview and absorbed detail that belongs in references.

How to avoid: Keep SKILL.md under 500 lines; move extended examples and configuration matrices to the cited references.

</failure_modes>

<success_criteria>
A well-configured custom agent has:

- A TOML file with `name`, `description`, and `developer_instructions` that a fresh Codex session loads without a configuration error and exposes by name in `spawn_agent`'s `agent_type` values
- A `developer_instructions` containing XML-structured role, workflow, constraints, and output expectations
- Every sandbox and tool capability mapped to at least one workflow step, with no workflow step requiring an undeclared capability
- A post-skill invocation record produced from the handoff: `spawn_agent` uses the configured name as `agent_type` and returns an `agent_id`; `wait_agent` preserves that exact identifier and reaches `completed`; the completed final message contains every field or section declared by the output expectations; `close_agent` then closes the completed thread

- A description that states both what the custom agent does and when to invoke it
- A model identifier accepted by the target harness and consistent with the configuration's stated capability, cost, and reproducibility requirements
- The target-specific invocation check rerun after every configuration edit as a post-skill step outside this skill's restricted execution

</success_criteria>
