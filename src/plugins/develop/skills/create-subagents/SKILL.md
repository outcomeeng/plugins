---
name: create-subagents
description: >-
  ALWAYS invoke this skill when creating, editing, or configuring {{! term('configured_agents') !}}.
  NEVER create {{! term('configured_agents') !}} without this skill.
---

{!% require_skill 'develop:agent-prompt-standards' %!}

<objective>
A {{! term('configured_agent') !}} configured for an isolated, focused role — its {{! term('configured_agent_prompt') !}}, tool access, and subagent-workflow orchestration.
</objective>

<quick_start>
<workflow>

{!% if target == 'codex' %!}

1. Create a standalone TOML file under `.codex/agents/` for product scope or `~/.codex/agents/` for user scope.
2. Define the custom agent:
   - **name**: unique identifier Codex uses when spawning or referring to this agent
   - **description**: human-facing guidance for when Codex should use this agent
   - **{{! field('configured_agent_prompt') !}}**: core instructions that define the agent's behavior
   - **model**: Optional model override
   - **model_reasoning_effort**: Optional reasoning setting
   - **sandbox_mode**, **mcp_servers**, **skills.config**: Optional inherited configuration overrides
3. Write the developer instructions with clear role, constraints, workflow, and output expectations.
   {!% else %!}
4. Run `/agents` command
5. Select "Create New Agent"
6. Choose product-scope (`.claude/agents/`) or user-scope (`~/.claude/agents/`)
7. Define the {{! term('configured_agent') !}}:
   - **name**: lowercase-with-hyphens
   - **description**: When should this {{! term('configured_agent') !}} be used?
   - **tools**: Optional comma-separated list (inherits all if omitted)
   - **model**: Optional (`opus`, `sonnet`, `haiku`, or `inherit`)
   - **skills**: Optional array of skill names to inject at startup
8. Write the {{! term('configured_agent_prompt') !}} (the {{! term('configured_agent') !}}'s instructions)
   {!% endif %!}

</workflow>

<example>
{!% if target == 'codex' %!}
```toml
name = "code_reviewer"
description = "Code reviewer focused on quality, security, and maintainability."
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
{{! field('configured_agent_prompt') !}} = """
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

````
{!% else %!}
```markdown
---
name: code-reviewer
description: Expert code reviewer. Use proactively after code changes to review for quality, security, and best practices.
tools: Read, Grep, Glob, Bash
model: {{! term('configured_agent_standard_model') !}}
---

<role>
Claude is a senior code reviewer focused on quality, security, and best practices.
</role>

<focus_areas>

- Code quality and maintainability
- Security vulnerabilities
- Performance issues
- Best practices adherence

</focus_areas>

<output_format>
Provide specific, actionable feedback with file:line references.
</output_format>
````

{!% endif %!}
</example>
</quick_start>

<file_structure>

{!% if target == 'codex' %!}
<codex_storage_locations>

Priority order:

1. Product: `.codex/agents/` for the current product
2. User: `~/.codex/agents/` for all projects
3. Plugin: plugin `agents/` directory for all projects

</codex_storage_locations>
{!% endif %!}

{!% if target == 'claude' %!}
<claude_storage_locations>

Priority order:

1. Product: `.claude/agents/` for the current product
2. User: `~/.claude/agents/` for all projects
3. Plugin: plugin `agents/` directory for all projects

</claude_storage_locations>
{!% endif %!}

Product-scope {{! term('configured_agents') !}} override user-scope when names conflict.
</file_structure>

<configuration>
<field name="name">
{!% if target == 'codex' %!}
- Unique identifier Codex uses when spawning or referring to this agent
- Matching the filename to the agent name is the simplest convention
{!% else %!}
- Lowercase letters and hyphens only
- Must be unique
{!% endif %!}

</field>

<field name="description">
- Natural language description of purpose
- Include when the runtime should invoke this {{! term('configured_agent') !}}
- Used for automatic {{! term('configured_agent') !}} selection

</field>

{!% if target == 'codex' %!}
<field name="{{! field('configured_agent_prompt') !}}">

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

<field name="skills.config">
- Optional skill configuration inherited from the parent session when omitted
- Configure only when the custom agent needs a different skill surface from the parent session

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
  - audit-typescript
  - testing
```

</field>
{!% endif %!}
</configuration>

<execution_model>
<critical_constraint>
{!% if target == 'codex' %!}
**Subagent workflows are black boxes that cannot interact with users.**

Custom agents launched as subagents run in isolated contexts and return their final output to the main conversation. They:
{!% else %!}
**Subagents are black boxes that cannot interact with users.**

Subagents run in isolated contexts and return their final output to the main conversation. They:
{!% endif %!}

- ✅ Can use tools like Read, Write, Edit, Bash, Grep, Glob
- ✅ Can access MCP servers and other non-interactive tools
- ❌ **Cannot use {{! tool('ask_user') !}}** or any tool requiring user interaction
- ❌ **Cannot present options or wait for user input**
- ❌ **User never sees subagent-workflow intermediate steps**

The main conversation sees only the subagent workflow's final report/output.
</critical_constraint>

<workflow_design>
**Designing workflows with subagents:**

Use **main chat** for:

- Gathering requirements from user ({{! tool('ask_user') !}})
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
Main Chat: Ask user for requirements ({{! tool('ask_user') !}})
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
Clearly define the {{! term('configured_agent') !}}'s role, capabilities, and constraints.
</principle>

<principle name="use_pure_xml_structure">
Structure the {{! term('configured_agent_prompt') !}} with pure XML tags. Remove ALL markdown headings from the body.

```text
---
name: security-reviewer
description: Reviews code for security vulnerabilities
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

</principle>

<principle name="task_specific">
Tailor instructions to the specific task domain. Don't create generic "helper" subagents.

❌ Bad: "Helpful assistant for code"
✅ Good: "Claude is a React component refactoring specialist. Analyze components for hooks best practices, performance anti-patterns, and accessibility issues."
</principle>
</system_prompt_guidelines>

<subagent_xml_structure>
{{! term('configured_agent_file') !}} bodies are {{! term('configured_agent_prompts') !}} consumed by the target runtime. Like skills and slash commands, they should use pure XML structure for parsing and token efficiency.

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

For XML structure principles and token efficiency details, read `/skill-standards` — the same principles apply to {{! term('configured_agents') !}}.
</critical_rule>
</subagent_xml_structure>

<invocation>
<automatic>
The runtime automatically selects {{! term('configured_agents') !}} based on the `description` field when it matches the current task.
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
{!% if target == 'codex' %!}
Edit `.codex/agents/*.toml` or `~/.codex/agents/*.toml` files to:
- Create new custom agents
- Edit existing custom agents and their configuration
- Choose project-scoped or user-scoped behavior

Use `/agent` to switch between active agent threads and inspect running subagents.
{!% else %!}
Run `/agents` for an interactive interface to:

- View all available subagents
- Create new subagents
- Edit existing subagents
- Delete custom subagents
  {!% endif %!}

</using_agents_command>

<manual_editing>
Edit {{! term('configured_agent_files') !}} directly:

{!% if target == 'codex' %!}

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`
  {!% else %!}
- Product: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`
  {!% endif %!}

</manual_editing>
</management>

<reference>
**Core references**:

**{{! term('configured_agent') | capitalize !}} usage and configuration**: [subagents.md](${CLAUDE_SKILL_DIR}/references/subagents.md)

- File format and configuration
- Skill injection (`skills:` field for preloading skill content)
- Model selection, including explicit aliases for reproducible agent behavior
- Tool security and least privilege
- Prompt caching optimization
- Complete examples

**Writing effective prompts**: [write-subagent-prompts.md](${CLAUDE_SKILL_DIR}/references/write-subagent-prompts.md)

- Core principles and XML structure
- Description field optimization for routing
- Extended thinking for complex reasoning
- Security constraints and strong modal verbs
- Success criteria definition

**Advanced topics**:

**Evaluation and testing**: [evaluation-and-testing.md](${CLAUDE_SKILL_DIR}/references/evaluation-and-testing.md)

- Evaluation metrics (task completion, tool correctness, robustness)
- Testing strategies (offline, simulation, online monitoring)
- Evaluation-driven development
- G-Eval for custom criteria

**Error handling and recovery**: [error-handling-and-recovery.md](${CLAUDE_SKILL_DIR}/references/error-handling-and-recovery.md)

- Common failure modes and causes
- Recovery strategies (graceful degradation, retry, circuit breakers)
- Structured communication and observability
- Anti-patterns to avoid

**Context management**: [context-management.md](${CLAUDE_SKILL_DIR}/references/context-management.md)

- Memory architecture (STM, LTM, working memory)
- Context strategies (summarization, sliding window, scratchpads)
- Managing long-running tasks
- Prompt caching interaction

**Orchestration patterns**: [orchestration-patterns.md](${CLAUDE_SKILL_DIR}/references/orchestration-patterns.md)

- Sequential, parallel, hierarchical, coordinator patterns
- Model selection for orchestration roles
- Multi-agent coordination
- Pattern selection guidance

**Debugging and troubleshooting**: [debugging-agents.md](${CLAUDE_SKILL_DIR}/references/debugging-agents.md)

- Logging, tracing, and correlation IDs
- Common failure types (hallucinations, format errors, tool misuse)
- Diagnostic procedures
- Continuous monitoring

</reference>

<success_criteria>
A well-configured {{! term('configured_agent') !}} has:

{!% if target == 'codex' %!}

- Valid TOML file with `name`, `description`, and `{{! field('configured_agent_prompt') !}}`
- Clear role definition in {{! term('configured_agent_prompt') !}}
- Appropriate sandbox and tool-surface restrictions
- XML-structured {{! term('configured_agent_prompt') !}} with role, approach, and constraints
  {!% else %!}
- Valid YAML frontmatter (name matches file, description includes triggers)
- Clear role definition in {{! term('configured_agent_prompt') !}}
- Appropriate tool restrictions (least privilege)
- XML-structured {{! term('configured_agent_prompt') !}} with role, approach, and constraints
  {!% endif %!}
- Description field optimized for automatic routing
- Successfully tested on representative tasks
- Model selection appropriate for task complexity, cost, and reproducibility needs

</success_criteria>
