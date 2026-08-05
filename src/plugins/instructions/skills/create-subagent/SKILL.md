---
name: create-subagent
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring {{! term('configured_agents') !}}.
  NEVER create {{! term('configured_agents') !}} without this skill.
allowed-tools: Read, Glob, Write, Edit, Skill
---

{!% require_skill 'instructions:agent-prompt-standards' %!}

<objective>
A {{! term('configured_agent') !}} configured for an isolated, focused role — its {{! term('configured_agent_prompt') !}}, tool access, and isolated-workflow orchestration.
</objective>

<quick_start>
{!% if target == 'codex' %!}
<workflow>

1. Create a standalone TOML file under `.codex/agents/` for product scope, the default. User scope (`~/.codex/agents/`) requires the operator confirmation `<scope_boundary>` defines.
2. Define the custom agent:
   - **name**: unique identifier Codex uses when spawning or referring to this agent
   - **description**: human-facing guidance for when Codex should use this agent
   - **{{! field('configured_agent_prompt') !}}**: core instructions that define the {{! term('configured_agent') !}}'s behavior
   - **model**: Optional model override
   - **model_reasoning_effort**: Optional reasoning setting
   - **sandbox_mode**, **mcp_servers**: Optional runtime configuration overrides
3. Write the developer instructions with clear role, constraints, workflow, and output expectations.
4. Include the post-skill invocation-check handoff from `<invocation_check_boundary>` in the result.

</workflow>
{!% else %!}
<workflow>

1. Run `/agents` command
2. Select "Create New Agent"
3. Choose product scope (`.claude/agents/`), the default. User scope (`~/.claude/agents/`) requires the operator confirmation `<scope_boundary>` defines.
4. Define the {{! term('configured_agent') !}}:
   - **name**: lowercase-with-hyphens
   - **description**: When should this {{! term('configured_agent') !}} be used?
   - **tools**: Optional comma-separated list (inherits all if omitted)
   - **model**: Optional (`opus`, `sonnet`, `haiku`, or `inherit`)
   - **skills**: Optional array of skill names to inject at startup
5. Write the {{! term('configured_agent_prompt') !}} (the {{! term('configured_agent') !}}'s instructions)
6. Include the post-skill invocation-check handoff from `<invocation_check_boundary>` in the result.

</workflow>
{!% endif %!}

<example>
Read `${CLAUDE_SKILL_DIR}/references/subagents.md` for complete {{! term('configured_agent') !}} file examples and field references.
</example>
</quick_start>

<file_structure>

{!% if target == 'codex' %!}
<codex_storage_locations>

Priority order:

1. Product: `.codex/agents/` for the current product
2. User: `~/.codex/agents/` for all projects

</codex_storage_locations>
{!% endif %!}

{!% if target == 'claude' %!}
<claude_storage_locations>

Priority order:

1. Product: `.claude/agents/` for the current product
2. CLI: `--agents` flag for the current session
3. User: `~/.claude/agents/` for all projects
4. Plugin: plugin `agents/` directory for all projects

</claude_storage_locations>
{!% endif %!}

Product-scope {{! term('configured_agents') !}} override user-scope when names conflict.

<scope_boundary>

Product scope is inside the checkout Claude was invoked in; a write there is part of the requested work and is reviewable in that repository's history. User scope is not: `~/.codex/agents/` and `~/.claude/agents/` sit outside the checkout, apply to every project on the machine, and are covered by no repository's review.

Default to product scope. Choose user scope only when the operator asks for a {{! term('configured_agent') !}} available across projects, and obtain confirmation naming the absolute destination path before the write. Being able to resolve a home-directory path is not authorization to write to it, and one approval covers one file — a second user-scope write asks again.

Never widen an approved product-scope write to user scope because the {{! term('configured_agent') !}} "seems generally useful"; that judgment belongs to the operator who owns the machine.

</scope_boundary>
</file_structure>

<configuration>
<field name="name">
{!% if target == 'codex' %!}
- Unique identifier Codex uses when spawning or referring to this agent
- Matching the filename to the {{! term('configured_agent') !}} name is the simplest convention
{!% else %!}
- Lowercase letters and hyphens only
- Must be unique
{!% endif %!}

</field>

<field name="description">
- Natural language description of purpose
{!% if target == 'codex' %!}
- Guides selection after the user explicitly asks Codex for this {{! term('configured_agent') !}} or subagent workflow
{!% else %!}
- Include when Claude should invoke this {{! term('configured_agent') !}}
- Used for automatic {{! term('configured_agent') !}} selection
{!% endif %!}

</field>

{!% if target == 'codex' %!}
<field name="{{! field('configured_agent_prompt') !}}">

- Required multiline TOML string that defines the {{! term('configured_agent') !}}'s behavior
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

{!% else %!}
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
- Array of skill names to inject into the {{! term('configured_agent') !}}'s context at startup
- The full SKILL.md content of each listed skill is loaded before the subagent runs
- Subagents do NOT inherit skills from the parent conversation — list every needed skill explicitly
- The {{! term('configured_agent') !}} receives skill content as reference material, not as dynamically invocable skills
- If omitted: no skills injected

```yaml
skills:
  - audit-typescript-code
  - test-typescript
```

</field>
{!% endif %!}
</configuration>

<execution_model>
<critical_constraint>
{!% if target == 'codex' %!}
**Custom agent workflows are black boxes that cannot interact with users.**

Custom agents run in isolated contexts and return their final output to the main conversation. They:
{!% else %!}
**Subagents are black boxes that cannot interact with users.**

Subagents run in isolated contexts and return their final output to the main conversation. They:
{!% endif %!}

- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use {{! tool('ask_user') !}}** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees isolated-workflow intermediate steps**

The main conversation sees only the isolated workflow's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with {{! term('configured_agents') !}}:**

Use **main chat** for:

- Gathering requirements from user ({{! tool('ask_user') !}})
- Presenting options or decisions to user
- Any task requiring user confirmation/input
- Work where user needs visibility into progress

Use **{{! term('configured_agents') !}}** for:

- Research tasks (API documentation lookup, code analysis)
- Code generation based on pre-defined requirements
- Analysis and reporting (security review, test coverage)
- Context-heavy operations that don't need user interaction

**Example workflow pattern:**

```
Main Chat: Ask user for requirements ({{! tool('ask_user') !}})
↓
{{! term('configured_agent') !}}: Research API and create documentation (no user interaction)
↓
Main Chat: Review research with user, confirm approach
↓
{{! term('configured_agent') !}}: Generate code based on confirmed plan
↓
Main Chat: Present results, handle testing/deployment
```

</workflow_design>
</execution_model>

<system_prompt_guidelines>
<principle name="be_specific">
Clearly define the {{! term('configured_agent') !}}'s role, capabilities, and constraints.
</principle>

<principle name="use_pure_xml_structure">
Structure the {{! term('configured_agent_prompt') !}} with pure XML tags. Remove ALL markdown headings from the body.

{!% if target == 'codex' %!}

```toml
name = "security_reviewer"
description = "Reviews code for security vulnerabilities. Use after security-sensitive code changes or before release."
sandbox_mode = "read-only"
model = "{{! term('configured_agent_standard_model') !}}"
{{! field('configured_agent_prompt') !}} = """
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

{!% else %!}

```text
---
name: security-reviewer
description: Reviews code for security vulnerabilities. Use after security-sensitive code changes or before release.
tools: Read, Grep, Glob, Bash
model: {{! term('configured_agent_standard_model') !}}
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

{!% endif %!}

</principle>

<principle name="task_specific">
Tailor instructions to the specific task domain. Don't create generic "helper" {{! term('configured_agents') !}}.

❌ Bad: "Helpful assistant for code"
✅ Good: "Claude is a React component refactoring specialist. Analyze components for hooks best practices, performance anti-patterns, and accessibility issues."
</principle>
</system_prompt_guidelines>

<configured_agent_xml_structure>
{{! term('configured_agent_file') !}} bodies are {{! term('configured_agent_prompts') !}} consumed by the target runtime. Like skills and slash commands, they should use pure XML structure for parsing and token efficiency.

<recommended_tags>
Common tags for {{! term('configured_agent') !}} structure:

- `<role>` - Who the {{! term('configured_agent') !}} is and what it does
- `<constraints>` - Hard rules (NEVER/MUST/ALWAYS)
- `<focus_areas>` - What to prioritize
- `<workflow>` - Step-by-step process
- `<output_format>` - How to structure deliverables
- `<success_criteria>` - Completion criteria
- `<validation>` - How to verify work

</recommended_tags>

<intelligence_rules>
**Simple {{! term('configured_agents') !}}** (single focused task):

- Use role + constraints + workflow minimum
- Example: code-reviewer, test-runner

**Medium {{! term('configured_agents') !}}** (multi-step process):

- Add workflow steps, output_format, success_criteria
- Example: api-researcher, documentation-generator

**Complex {{! term('configured_agents') !}}** (research + generation + validation):

- Add all tags as appropriate including validation, examples
- Example: mcp-api-researcher, comprehensive-auditor

</intelligence_rules>

<critical_rule>
**Remove ALL markdown headings (##, ###) from {{! term('configured_agent') !}} body.** Use semantic XML tags instead.

Keep markdown formatting WITHIN content (bold, italic, lists, code blocks, links).

Invoke the `instructions:skill-standards` skill before structuring the body; its XML structure principles and token-efficiency rules apply unchanged to {{! term('configured_agents') !}}.
</critical_rule>
</configured_agent_xml_structure>

<invocation>
{!% if target == 'codex' %!}
<explicit_request>
Codex uses {{! term('configured_agent') !}} descriptions to select the right agent after the user explicitly asks for a {{! term('configured_agent') !}} or subagent workflow.
</explicit_request>
{!% else %!}
<automatic>
Claude automatically selects {{! term('configured_agents') !}} based on the `description` field when it matches the current task.
</automatic>
{!% endif %!}

<explicit>
Explicitly invoke a {{! term('configured_agent') !}}:

```
> Use the code-reviewer {{! term('configured_agent') !}} to check my recent changes
```

```
> Have the test-writer {{! term('configured_agent') !}} create tests for the new API endpoints
```

</explicit>
</invocation>

<management>
<using_agents_command>
{!% if target == 'codex' %!}
Edit `.codex/agents/*.toml` or `~/.codex/agents/*.toml` files to:
- Create new custom agents
- Edit existing custom agents and their configuration
- Choose project-scoped or user-scoped behavior

Use `/agent` to switch between active agent threads and inspect running custom agents.
{!% else %!}
Run `/agents` for an interactive interface to:

- View all available subagents
- Create new subagents
- Edit existing subagents
- Delete custom subagents
  {!% endif %!}

</using_agents_command>

<manual_editing>
Edit {{! term('configured_agent_files') !}} directly. A user-scope path below is outside the checkout, so editing one requires the confirmation `<scope_boundary>` defines — for an edit or a delete as much as for a create:

{!% if target == 'codex' %!}

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`
  {!% else %!}
- Product: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`
  {!% endif %!}

</manual_editing>
</management>

<invocation_check_boundary>
Include a target-specific invocation-check handoff with every created or edited configuration. Keep the invocation outside this skill's restricted execution; its `allowed-tools` intentionally omit {{! term('configured_agent') !}}-spawn authority.

{!% if target == 'codex' %!}
The handoff names the configured `agent_type` and expected final-message fields or sections. It requires `spawn_agent` to return an `agent_id`, preserves that exact identifier, collects `wait_agent` until the identifier reaches `completed`, validates the completed final message, and closes the completed thread with `close_agent`.
{!% else %!}
The handoff names the configured `subagent_type`, the expected final-message fields or sections, and the `completed` result required from the Agent tool.
{!% endif %!}

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

How to avoid: Keep SKILL.md under 500 lines; move extended examples and configuration matrices to the cited references.

</failure_modes>

<success_criteria>
A well-configured {{! term('configured_agent') !}} has:

{!% if target == 'codex' %!}

- A TOML file with `name`, `description`, and `{{! field('configured_agent_prompt') !}}` that a fresh Codex session loads without a configuration error and exposes by name in `spawn_agent`'s `agent_type` values
- A `{{! field('configured_agent_prompt') !}}` containing XML-structured role, workflow, constraints, and output expectations
- Every sandbox and tool capability mapped to at least one workflow step, with no workflow step requiring an undeclared capability
- A post-skill invocation record produced from the handoff: `spawn_agent` uses the configured name as `agent_type` and returns an `agent_id`; `wait_agent` preserves that exact identifier and reaches `completed`; the completed final message contains every field or section declared by the output expectations; `close_agent` then closes the completed thread
  {!% else %!}
- A YAML-frontmatter file whose name matches the filename and whose configured name and scope appear in `/agents` after saving
- A `{{! field('configured_agent_prompt') !}}` containing XML-structured role, workflow, constraints, and output expectations
- Every declared tool mapped to at least one workflow step, with no workflow step requiring an undeclared tool
- A post-skill Agent-tool invocation record produced from the handoff, using the configured name as `subagent_type` and reaching `completed`; its final message contains every field or section declared by the output expectations
  {!% endif %!}
- A description that states both what the {{! term('configured_agent') !}} does and when to invoke it
- A model identifier accepted by the target harness and consistent with the configuration's stated capability, cost, and reproducibility requirements
- The target-specific invocation check rerun after every configuration edit as a post-skill step outside this skill's restricted execution

</success_criteria>
