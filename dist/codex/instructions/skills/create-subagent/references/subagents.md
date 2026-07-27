<table_of_contents>

- `<file_format>` — custom agent file shape and configuration fields
- `<storage_locations>` — product, user, CLI, and plugin placement
- `<execution_model>` — black-box execution and workflow implications
- `<tool_configuration>` — inherited and specific tool grants
- `<model_selection>` — model aliases and reproducibility-sensitive inheritance boundaries
- `<invocation>` — automatic and explicit subagent use
- `<management>` — runtime management surfaces, direct files, and CLI configuration
- `<example_subagents>` — test-writer and debugger examples
- `<tool_security>` — least privilege and audit checklist
- `<skill_injection>` — startup skill preloading
- `<prompt_caching>` — cache-aware prompt structure
- `<best_practices>` — focused prompts, triggers, tools, and XML structure

</table_of_contents>

<file_format>
Custom agent file structure:

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
<role>
Review code like an owner.
</role>

<constraints>
MUST prioritize correctness, security, behavior regressions, and missing test coverage.
</constraints>

<workflow>
1. Read the scoped change.
2. Inspect the relevant code paths.
3. Return concrete findings with file references.
</workflow>
"""
```

**Critical**: Use pure XML structure in the body. Remove ALL markdown headings (##, ###). Keep markdown formatting within content (bold, lists, code blocks).

<configuration_fields>

<codex_configuration_fields>

Required fields:

- `name`: agent name Codex uses when spawning or referring to this agent
- `description`: human-facing guidance for when Codex should use this agent
- `developer_instructions`: core instructions that define the custom agent's behavior

Optional fields:

- `nickname_candidates`: display nicknames for spawned agents
- `model`: model override
- `model_reasoning_effort`: reasoning setting
- `sandbox_mode`: sandbox override, such as `read-only`
- `mcp_servers`: MCP server overrides

</codex_configuration_fields>

</configuration_fields>
</file_format>

<storage_locations>

<codex_storage_locations>

Priority order:

1. Product: `.codex/agents/` for the current product
2. User: `~/.codex/agents/` for all projects

</codex_storage_locations>

When custom agent names conflict, higher priority takes precedence.
</storage_locations>

<execution_model>
<black_box_model>
Subagents execute in isolated contexts without user interaction.

**Key characteristics:**

- Subagent receives input parameters from main chat
- Subagent runs autonomously using available tools
- Subagent returns final output/report to main chat
- User only sees final result, not intermediate steps

**This means:**

- ✅ Subagents can use Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch
- ✅ Subagents can access MCP servers (non-interactive tools)
- ✅ Subagents can make decisions based on their prompt and available data
- ❌ **Subagents CANNOT use request_user_input**
- ❌ **Subagents CANNOT present options and wait for user selection**
- ❌ **Subagents CANNOT request confirmations or clarifications from user**
- ❌ **User does not see subagent's tool calls or intermediate reasoning**

</black_box_model>

<workflow_implications>
**When designing subagent workflows:**

Keep user interaction in main chat:

```text
# ❌ WRONG - Subagent cannot do this

---
name: requirement-gatherer
description: Gathers requirements from user
tools: request_user_input # This won't work!
---

You ask the user questions to gather requirements...
```

```markdown
# ✅ CORRECT - Main chat handles interaction

Main chat: Uses request_user_input to gather requirements
↓
Launch subagent: Uses requirements to research/build (no interaction)
↓
Main chat: Present subagent results to user
```

</workflow_implications>
</execution_model>

<tool_configuration>
<inherit_all_tools>
Omit the `tools` field to inherit all tools from main thread:

```toml
name = "code_reviewer"
description = "Reviews code for quality and security."
developer_instructions = """
<role>
Review code for quality and security.
</role>
"""
```

The custom agent inherits the parent session's available tools, sandbox, and MCP configuration unless supported Codex config keys override them.

</inherit_all_tools>

<specific_tools>

Configure sandbox and MCP permission settings through supported Codex config keys:

```toml
name = "read_only_analyzer"
description = "Analyzes code without making changes."
sandbox_mode = "read-only"
developer_instructions = """
<role>
Analyze code without making changes.
</role>
"""
```

Consult Codex custom-agent documentation or existing `.codex/agents/*.toml` files to choose runtime-supported tools.

</specific_tools>
</tool_configuration>

<model_selection>
<model_capabilities>

**gpt-5.5**:

- Strongest recommended Codex model for complex coding, computer use, knowledge work, and research workflows
- Use for demanding agents that need planning, tool use, validation, and follow-through across larger context

**gpt-5.4**:

- Strong coding, reasoning, tool use, and broader workflow capability
- Use when a workflow is pinned to GPT-5.4 or needs strong reasoning with a stable explicit choice

**gpt-5.4-mini**:

- Fast, efficient model for responsive coding tasks and subagents
- Use for read-heavy scans, large-file review, document processing, and lighter subagent work

**model_reasoning_effort**:

- `high`: complex logic, reviewer or security-focused agents, edge-case analysis
- `medium`: balanced default for most agents
- `low`: straightforward tasks where speed matters most

</model_capabilities>

<orchestration_strategy>
**Explicit model orchestration pattern**:

```text
1. gpt-5.5 or gpt-5.4 (Coordinator):
   - Creates plan
   - Breaks task into subtasks
   - Identifies parallelizable work

2. gpt-5.4-mini or gpt-5.4 (Workers):
   - Execute subtasks in parallel
   - Use the faster model for simple or high-volume tasks when the owning workflow accepts lower-cost execution
   - Use the stronger model when comparable evidence quality or higher reasoning capability matters

3. gpt-5.5 or gpt-5.4 (Validator):
   - Integrates results
   - Validates output quality
   - Ensures coherence
```

**Benefit**: every role has an explicit model choice that survives session-model changes.
</orchestration_strategy>

<decision_framework>
**When to use each model**:

<codex_decision_framework>

- Simple validation: `gpt-5.4-mini` for fast lower-cost execution
- Clear execution: `gpt-5.4-mini` for bounded tasks
- Complex analysis: `gpt-5.4` or `gpt-5.5` for stronger reasoning
- Multi-step planning: `gpt-5.5` for breaking down complexity
- Quality validation: `gpt-5.4` or `gpt-5.5` when the checkpoint needs more capability
- Batch processing: `gpt-5.4-mini` for cost efficiency at high volume
- Critical security: `gpt-5.5` for high-stakes review
- Output synthesis: `gpt-5.4` or `gpt-5.5` for coherence across inputs

</codex_decision_framework>

</decision_framework>
</model_selection>

<invocation>

<explicit_request>
Codex uses custom agent descriptions to select the right agent after the user explicitly asks for a custom agent or subagent workflow.
</explicit_request>

<explicit>
Users can explicitly request a custom agent:

```
> Use the code-reviewer custom agent to check my recent changes
> Have the test-runner custom agent fix the failing tests
```

</explicit>
</invocation>

<management>
<using_agents_command>

Manage project and user custom agents by editing TOML files directly:

- Project scope: `.codex/agents/*.toml`
- User scope: `~/.codex/agents/*.toml`

Use `/agent` to switch between active agent threads and inspect running subagents.

</using_agents_command>

<direct_file_management>
**Alternative**: Edit custom agent files directly:

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`

Follow the TOML file format specified above.

</direct_file_management>

</management>

<example_subagents>
<test_writer>

```toml
name = "test_writer"
description = "Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient."
sandbox_mode = "workspace-write"
model = "gpt-5.4"
developer_instructions = """
<role>
Claude is a test automation specialist creating thorough, maintainable test suites.
</role>

<workflow>
1. Analyze the code to understand functionality
2. Identify test cases (happy path, edge cases, error conditions)
3. Write tests using the product's testing framework
4. Run tests to verify they pass
</workflow>

<test_quality_criteria>

- Test one behavior per test
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Include edge cases and error conditions
- Avoid test interdependencies

</test_quality_criteria>
"""
```

</test_writer>

<debugger>

```toml
name = "debugger"
description = "Investigates and fixes bugs. Use when errors occur or behavior is unexpected."
sandbox_mode = "workspace-write"
model = "gpt-5.4"
developer_instructions = """
<role>
Claude is a debugging specialist skilled at root cause analysis and systematic problem-solving.
</role>

<workflow>
1. **Reproduce**: Understand and reproduce the issue
2. **Isolate**: Identify the failing component
3. **Analyze**: Examine code, logs, and stack traces
4. **Hypothesize**: Form theories about the cause
5. **Test**: Verify hypotheses systematically
6. **Fix**: Implement and verify the solution
</workflow>

<debugging_techniques>

- Add logging/print statements to trace execution
- Use binary search to isolate the problem
- Check assumptions (inputs, state, environment)
- Review recent changes that might have introduced the bug
- Verify fix doesn't break other functionality

</debugging_techniques>
"""
```

</debugger>
</example_subagents>

<tool_security>
<core_principle>
**"Permission sprawl is the fastest path to unsafe autonomy."** - Anthropic

Treat tool access like production IAM: start from deny-all, allowlist only what's needed.
</core_principle>

<why_it_matters>
**Security risks of over-permissioning**:

- Agent could modify wrong code (production instead of tests)
- Agent could run dangerous commands (rm -rf, data deletion)
- Agent could expose protected information
- Agent could skip critical steps (linting, testing, validation)

**Example vulnerability**:

```markdown
❌ Bad: Agent drafting sales email has full access to all tools
Risk: Could access revenue dashboard data, customer financial info

✅ Good: Agent drafting sales email has Read access to Salesforce only
Scope: Can draft email, cannot access sensitive financial data
```

</why_it_matters>

<permission_patterns>
**Tool access patterns by trust level**:

**Trusted data processing**:

- Full tool access appropriate
- Working with user's own code
- Example: refactoring user's codebase

**Untrusted data processing**:

- Restricted tool access essential
- Processing external inputs
- Example: analyzing third-party API responses
- Limit: Read-only tools, no execution

</permission_patterns>

<audit_checklist>
**Tool access audit**:

- [ ] Does this subagent need Write/Edit, or is Read sufficient?
- [ ] Should it execute code (Bash), or just analyze?
- [ ] Are all granted tools necessary for the task?
- [ ] What's the worst-case misuse scenario?
- [ ] Can we restrict further without blocking legitimate use?

**Default**: Grant minimum necessary. Add tools only when lack of access blocks task.
</audit_checklist>
</tool_security>

<skill_injection>

Codex custom agents do not preload individual skill bodies by name. Put the durable role, workflow, and standards the custom agent needs in `developer_instructions`, and use a main conversation workflow when the custom agent needs to choose skills dynamically.

<how_it_works>

- Codex custom agent files carry prompt guidance rather than a skill-preload field
- Put required standards and workflow constraints directly in `developer_instructions`
- Use a main conversation workflow when the custom agent needs to choose skills dynamically

</how_it_works>

<when_to_use>

**Use explicit `developer_instructions` when the custom agent needs durable guidance:**

- Read-only custom agents that must produce verdicts rather than edits
- Documentation-research custom agents that need repository-specific source guidance
- Worker custom agents that need a narrowed role and output contract

**Do NOT duplicate skill bodies when:**

- The agent needs to dynamically choose which skill to load
- A normal main conversation workflow can keep the decision clearer

</when_to_use>

<example>

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = """
<role>
Review code like an owner.
</role>

<constraints>
MUST produce concrete findings with file references.
</constraints>
"""
```

</example>

<relationship_to_context_fork>

Codex custom-agent configuration does not provide a per-agent `skills:` preload equivalent. Treat skill requirements as prompt guidance unless local Codex configuration gains an explicit, tested skill surface.

</relationship_to_context_fork>

</skill_injection>

<prompt_caching>
<benefits>
Prompt caching for frequently-invoked subagents:

- **90% cost reduction** on cached tokens
- **85% latency reduction** for cache hits
- Cached content: ~10% cost of uncached tokens
- Cache TTL: 5 minutes (default) or 1 hour (extended)

</benefits>

<cache_structure>
**Structure prompts for caching**:

```toml
name = "security_reviewer"
description = "..."
sandbox_mode = "read-only"
model = "gpt-5.4"
developer_instructions = """
[CACHEABLE SECTION - Stable content]
<role>
Claude is a senior security engineer...
</role>

<focus_areas>

- SQL injection
- XSS attacks
  ...

</focus_areas>

<workflow>
1. Read modified files
2. Identify risks
...
</workflow>

<severity_ratings>
...
</severity_ratings>

--- [CACHE BREAKPOINT] ---

[VARIABLE SECTION - Task-specific content]
Current task: {dynamic context}
Recent changes: {varies per invocation}
"""
```

**Principle**: Stable instructions at beginning (cached), variable context at end (fresh).
</cache_structure>

<when_to_use>
**Best candidates for caching**:

- Frequently-invoked subagents (multiple times per session)
- Large, stable prompts (extensive guidelines, examples)
- Consistent tool definitions across invocations
- Long-running sessions with repeated subagent use

**Not beneficial**:

- Rarely-used subagents (once per session)
- Prompts that change frequently
- Very short prompts (caching overhead > benefit)

</when_to_use>

<cache_management>
**Cache lifecycle**:

- First invocation: Writes to cache (25% cost premium)
- Subsequent invocations: 90% cheaper on cached portion
- Cache refreshes on each use (extends TTL)
- Expires after 5 minutes of non-use (or 1 hour for extended TTL)

**Invalidation triggers**:

- Subagent prompt modified
- Tool definitions changed
- Cache TTL expires

</cache_management>
</prompt_caching>

<best_practices>
<be_specific>
Create task-specific subagents, not generic helpers.

❌ Bad: "You are a helpful assistant"
✅ Good: "React performance optimizer specializing in hooks and memoization"
</be_specific>

<clear_triggers>
Make the `description` clear about when to invoke:

❌ Bad: "Helps with code"
✅ Good: "ALWAYS invoke when changes involve authentication, data access, or user input."

The directive opening is the form `/agent-prompt-standards` `<description_style>` measures highest; it governs skill and custom agent descriptions alike.
</clear_triggers>

<focused_tools>
Grant only the tools needed for the task (least privilege):

- Read-only analysis: `Read, Grep, Glob`
- Code modification: `Read, Edit, Bash, Grep`
- Test running: `Read, Write, Bash`

**Security note**: Over-permissioning is primary risk vector. Start minimal, add only when necessary.
</focused_tools>

<structured_prompts>
Use XML tags to structure the developer instructions for clarity:

```text
<role>
Claude is a senior security engineer specializing in web application security.
</role>

<focus_areas>

- SQL injection
- XSS attacks
- CSRF vulnerabilities
- Authentication/authorization flaws

</focus_areas>

<workflow>
1. Analyze code changes
2. Identify security risks
3. Provide specific remediation
4. Rate severity
</workflow>
```

</structured_prompts>
</best_practices>
