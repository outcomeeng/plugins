---
name: create-subagents
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring custom agents.
  NEVER create custom agents without this skill.
---

Invoke the `develop:agent-prompt-standards` skill before proceeding. If that skill is unavailable, report the missing skill and continue with the closest available workflow.

<objective>
A custom agent configured for an isolated, focused role — its developer instructions, tool access, and subagent-workflow orchestration.
</objective>

<quick_start>
<workflow>

1. Create a standalone TOML file under `.codex/agents/` for product scope or `~/.codex/agents/` for user scope.
2. Define the custom agent:
   - **name**: unique identifier Codex uses when spawning or referring to this agent
   - **description**: human-facing guidance for when Codex should use this agent
   - **developer_instructions**: core instructions that define the agent's behavior
   - **model**: Optional model override
   - **model_reasoning_effort**: Optional reasoning setting
   - **sandbox_mode**, **mcp_servers**: Optional runtime configuration overrides
3. Write the developer instructions with clear role, constraints, workflow, and output expectations.

</workflow>

<example>

```toml
name = "code_reviewer"
description = "Code reviewer focused on quality, security, and maintainability."
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
<role>
Review code for quality, security, and maintainability.
</role>

<focus_areas>

- Correctness and behavior regressions
- Security vulnerabilities
- Maintainability risks
- Missing test coverage

</focus_areas>

<output_format>
Provide concrete findings with file:line references.
</output_format>
"""
```

</example>
</quick_start>

<file_structure>

<codex_storage_locations>

Priority order:

1. Product: `.codex/agents/` for the current product
2. User: `~/.codex/agents/` for all projects
3. Plugin: plugin `agents/` directory for all projects

</codex_storage_locations>

Product-scope custom agents override user-scope when names conflict.
</file_structure>

<configuration>
<field name="name">

- Unique identifier Codex uses when spawning or referring to this agent
- Matching the filename to the agent name is the simplest convention

</field>

<field name="description">
- Natural language description of purpose
- Include when the runtime should invoke this custom agent
- Used for automatic custom agent selection

</field>

<field name="developer_instructions">

- Required multiline TOML string that defines the agent's behavior
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

**Subagent workflows are black boxes that cannot interact with users.**

Custom agents launched as subagents run in isolated contexts and return their final output to the main conversation. They:

- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use request_user_input** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees subagent-workflow intermediate steps**

The main conversation sees only the subagent workflow's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with subagents:**

Use **main chat** for:

- Gathering requirements from user (request_user_input)
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
Main Chat: Ask user for requirements (request_user_input)
↓
Subagent: Research API and create documentation (no user interaction)
↓
Main Chat: Review research with user, confirm approach
↓
Subagent: Generate code based on confirmed plan
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

```text
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: gpt-5.4
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

<subagent_xml_structure>
custom agent file bodies are developer instructions consumed by the target runtime. Like skills and slash commands, they should use pure XML structure for parsing and token efficiency.

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
</subagent_xml_structure>

<invocation>
<automatic>
The runtime automatically selects custom agents based on the `description` field when it matches the current task.
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

Edit `.codex/agents/*.toml` or `~/.codex/agents/*.toml` files to:

- Create new custom agents
- Edit existing custom agents and their configuration
- Choose project-scoped or user-scoped behavior

Use `/agent` to switch between active agent threads and inspect running subagents.

</using_agents_command>

<manual_editing>
Edit custom agent files directly:

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`

</manual_editing>
</management>

<reference>
**Core references**:

**Custom agent usage and configuration**: [subagents.md](${SKILL_DIR}/references/subagents.md)

- File format and configuration
- Skill injection (`skills:` field for preloading skill content)
- Model selection, including explicit aliases for reproducible agent behavior
- Tool security and least privilege
- Prompt caching optimization
- Complete examples

**Writing effective prompts**: [write-subagent-prompts.md](${SKILL_DIR}/references/write-subagent-prompts.md)

- Core principles and XML structure
- Description field optimization for routing
- Extended thinking for complex reasoning
- Security constraints and strong modal verbs
- Success criteria definition

**Advanced topics**:

**Evaluation and testing**: [evaluation-and-testing.md](${SKILL_DIR}/references/evaluation-and-testing.md)

- Evaluation metrics (task completion, tool correctness, robustness)
- Testing strategies (offline, simulation, online monitoring)
- Evaluation-driven development
- G-Eval for custom criteria

**Error handling and recovery**: [error-handling-and-recovery.md](${SKILL_DIR}/references/error-handling-and-recovery.md)

- Common failure modes and causes
- Recovery strategies (graceful degradation, retry, circuit breakers)
- Structured communication and observability
- Anti-patterns to avoid

**Context management**: [context-management.md](${SKILL_DIR}/references/context-management.md)

- Memory architecture (STM, LTM, working memory)
- Context strategies (summarization, sliding window, scratchpads)
- Managing long-running tasks
- Prompt caching interaction

**Orchestration patterns**: [orchestration-patterns.md](${SKILL_DIR}/references/orchestration-patterns.md)

- Sequential, parallel, hierarchical, coordinator patterns
- Model selection for orchestration roles
- Multi-agent coordination
- Pattern selection guidance

**Debugging and troubleshooting**: [debugging-agents.md](${SKILL_DIR}/references/debugging-agents.md)

- Logging, tracing, and correlation IDs
- Common failure types (hallucinations, format errors, tool misuse)
- Diagnostic procedures
- Continuous monitoring

</reference>

<success_criteria>
A well-configured custom agent has:

- Valid TOML file with `name`, `description`, and `developer_instructions`
- Clear role definition in developer instructions
- Appropriate sandbox and tool-surface restrictions
- XML-structured developer instructions with role, approach, and constraints

- Description field optimized for automatic routing
- Successfully tested on representative tasks
- Model selection appropriate for task complexity, cost, and reproducibility needs

</success_criteria>
