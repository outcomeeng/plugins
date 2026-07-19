<table_of_contents>

- `<file_format>` — {{! term('configured_agent_file') !}} shape and configuration fields
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
{{! term('configured_agent_file') | capitalize !}} structure:

{!% if target == 'codex' %!}

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
model = "{{! term('configured_agent_standard_model') !}}"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
{{! field('configured_agent_prompt') !}} = """
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

{!% else %!}

```text
---
name: your-subagent-name
description: Description of when this subagent should be invoked
tools: tool1, tool2, tool3 # Optional - inherits all tools if omitted
model: {{! term('configured_agent_standard_model') !}}
skills: # Optional - inject skill content at startup
  - skill-name-one
  - skill-name-two
---

<role>
Claude is a focused repository reviewer who identifies correctness, security, and test-coverage risks in scoped code changes.
</role>

<constraints>
Hard rules using NEVER/MUST/ALWAYS for critical boundaries.
</constraints>

<workflow>
Step-by-step process for consistency.
</workflow>
```

{!% endif %!}

**Critical**: Use pure XML structure in the body. Remove ALL markdown headings (##, ###). Keep markdown formatting within content (bold, lists, code blocks).

<configuration_fields>

{!% if target == 'codex' %!}
<codex_configuration_fields>

Required fields:

- `name`: agent name Codex uses when spawning or referring to this agent
- `description`: human-facing guidance for when Codex should use this agent
- `{{! field('configured_agent_prompt') !}}`: core instructions that define the {{! term('configured_agent') !}}'s behavior

Optional fields:

- `nickname_candidates`: display nicknames for spawned agents
- `model`: model override
- `model_reasoning_effort`: reasoning setting
- `sandbox_mode`: sandbox override, such as `read-only`
- `mcp_servers`: MCP server overrides

</codex_configuration_fields>
{!% endif %!}

{!% if target == 'claude' %!}
<claude_configuration_fields>

Required fields:

- `name`: unique identifier using lowercase letters and hyphens
- `description`: natural language description of purpose, including when Claude should invoke this

Optional fields:

- `tools`: comma-separated list; if omitted, inherits all tools from main thread
- `model`: `opus`, `sonnet`, `haiku`, or `inherit`; use explicit aliases when reproducibility matters
- `skills`: array of skill names; full skill content injects into subagent context at startup

</claude_configuration_fields>
{!% endif %!}

</configuration_fields>
</file_format>

<storage_locations>

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

When {{! term('configured_agent') !}} names conflict, higher priority takes precedence.
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
- ❌ **Subagents CANNOT use {{! tool('ask_user') !}}**
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
tools: {{! tool('ask_user') !}} # This won't work!
---

You ask the user questions to gather requirements...
```

```markdown
# ✅ CORRECT - Main chat handles interaction

Main chat: Uses {{! tool('ask_user') !}} to gather requirements
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

{!% if target == 'codex' %!}

```toml
name = "code_reviewer"
description = "Reviews code for quality and security."
{{! field('configured_agent_prompt') !}} = """
<role>
Review code for quality and security.
</role>
"""
```

{!% else %!}

```yaml
---
name: code-reviewer
description: Reviews code for quality and security
---
```

{!% endif %!}

{!% if target == 'codex' %!}
The custom agent inherits the parent session's available tools, sandbox, and MCP configuration unless supported Codex config keys override them.
{!% else %!}
Subagent has access to all tools, including MCP tools.
{!% endif %!}
</inherit_all_tools>

<specific_tools>
{!% if target == 'codex' %!}
Configure sandbox and MCP permission settings through supported Codex config keys:
{!% else %!}
Specify tools as comma-separated list for granular control:
{!% endif %!}

{!% if target == 'codex' %!}

```toml
name = "read_only_analyzer"
description = "Analyzes code without making changes."
sandbox_mode = "read-only"
{{! field('configured_agent_prompt') !}} = """
<role>
Analyze code without making changes.
</role>
"""
```

{!% else %!}

```yaml
---
name: read-only-analyzer
description: Analyzes code without making changes
tools: Read, Grep, Glob
---
```

{!% endif %!}

{!% if target == 'codex' %!}
Consult Codex custom-agent documentation or existing `.codex/agents/*.toml` files to choose runtime-supported tools.
{!% else %!}
Use `/agents` command to see full list of available tools.
{!% endif %!}
</specific_tools>
</tool_configuration>

<model_selection>
<model_capabilities>
{!% if target == 'codex' %!}
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

{!% endif %!}

{!% if target == 'claude' %!}
**Sonnet 4.5** (`sonnet`):

- "Best model in the world for agents" (Anthropic)
- Exceptional at agentic tasks: 64% problem-solving on coding benchmarks
- SWE-bench Verified: 49.0%
- **Use for**: Planning, complex reasoning, validation, critical decisions

**Haiku** (`haiku`):

- Fast, lower-cost model alias
- **Use for**: simple transformations, high-volume processing, and clear execution tasks when the owning workflow accepts lower-cost execution

**Opus** (`opus`):

- Highest performance on evaluation benchmarks
- Most capable but slowest and most expensive
- **Use for**: Highest-stakes decisions, most complex reasoning

**Session inheritance** (`inherit`):

- Uses the same model as the main conversation.
- NEVER use for verification, audit, review, or other reproducibility-sensitive agents.

{!% endif %!}

</model_capabilities>

<orchestration_strategy>
**Explicit model orchestration pattern**:

```text
1. {{! term('configured_agent_strong_models') !}} (Coordinator):
   - Creates plan
   - Breaks task into subtasks
   - Identifies parallelizable work

2. {{! term('configured_agent_fast_or_standard_models') !}} (Workers):
   - Execute subtasks in parallel
   - Use the faster model for simple or high-volume tasks when the owning workflow accepts lower-cost execution
   - Use the stronger model when comparable evidence quality or higher reasoning capability matters

3. {{! term('configured_agent_strong_models') !}} (Validator):
   - Integrates results
   - Validates output quality
   - Ensures coherence
```

**Benefit**: every role has an explicit model choice that survives session-model changes.
</orchestration_strategy>

<decision_framework>
**When to use each model**:

{!% if target == 'codex' %!}
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
{!% endif %!}

{!% if target == 'claude' %!}
<claude_decision_framework>

- Simple validation: Haiku for fast lower-cost execution
- Clear execution: Haiku for bounded tasks
- Complex analysis: Sonnet for stronger reasoning
- Multi-step planning: Sonnet for breaking down complexity
- Quality validation: Sonnet when the checkpoint needs more capability
- Batch processing: Haiku for cost efficiency at high volume
- Critical security: Sonnet for high-stakes review
- Output synthesis: Sonnet for coherence across inputs

</claude_decision_framework>
{!% endif %!}

</decision_framework>
</model_selection>

<invocation>
{!% if target == 'codex' %!}
<explicit_request>
Codex uses {{! term('configured_agent') !}} descriptions to select the right agent after the user explicitly asks for a {{! term('configured_agent') !}} or subagent workflow.
</explicit_request>
{!% else %!}
<automatic>
Claude automatically selects {{! term('configured_agents') !}} based on:
- Task description in user's request
- `description` field in {{! term('configured_agent') !}} configuration
- Current context

</automatic>
{!% endif %!}

<explicit>
Users can explicitly request a {{! term('configured_agent') !}}:

```
> Use the code-reviewer {{! term('configured_agent') !}} to check my recent changes
> Have the test-runner {{! term('configured_agent') !}} fix the failing tests
```

</explicit>
</invocation>

<management>
<using_agents_command>
{!% if target == 'codex' %!}
Manage project and user custom agents by editing TOML files directly:

- Project scope: `.codex/agents/*.toml`
- User scope: `~/.codex/agents/*.toml`

Use `/agent` to switch between active agent threads and inspect running subagents.
{!% else %!}
**Recommended**: Use `/agents` command for interactive management:

- View all available subagents (built-in, user, product, plugin)
- Create new subagents with guided setup
- Edit existing subagents and their tool access
- Delete custom subagents
- See which subagents take priority when names conflict

{!% endif %!}

</using_agents_command>

<direct_file_management>
**Alternative**: Edit {{! term('configured_agent_files') !}} directly:

{!% if target == 'codex' %!}

- Product: `.codex/agents/agent-name.toml`
- User: `~/.codex/agents/agent-name.toml`

{!% else %!}

- Product: `.claude/agents/subagent-name.md`
- User: `~/.claude/agents/subagent-name.md`

{!% endif %!}

{!% if target == 'codex' %!}
Follow the TOML file format specified above.
{!% else %!}
Follow the file format specified above (YAML frontmatter + {{! term('configured_agent_prompt') !}}).
{!% endif %!}
</direct_file_management>

{!% if target == 'claude' %!}
<cli_based_configuration>
**Temporary**: Define subagents via CLI for session-specific use:

```bash
claude --agents '{
  "code-reviewer": {
    "description": "Reviews code quality, security, and best practices. Use after code changes.",
    "prompt": "Claude is a senior code reviewer. Focus on quality, security, and best practices.",
    "tools": ["Read", "Grep", "Glob", "Bash"],
    "model": "sonnet"
  }
}'
```

Useful for testing configurations before saving them.
</cli_based_configuration>
{!% endif %!}
</management>

<example_subagents>
<test_writer>

{!% if target == 'codex' %!}

```toml
name = "test_writer"
description = "Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient."
sandbox_mode = "workspace-write"
model = "{{! term('configured_agent_standard_model') !}}"
{{! field('configured_agent_prompt') !}} = """
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

{!% else %!}

```text
---
name: test-writer
description: Creates comprehensive test suites. Use when new code needs tests or test coverage is insufficient.
tools: Read, Write, Grep, Glob, Bash
model: {{! term('configured_agent_standard_model') !}}
---

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
```

{!% endif %!}

</test_writer>

<debugger>
{!% if target == 'codex' %!}
```toml
name = "debugger"
description = "Investigates and fixes bugs. Use when errors occur or behavior is unexpected."
sandbox_mode = "workspace-write"
model = "{{! term('configured_agent_standard_model') !}}"
{{! field('configured_agent_prompt') !}} = """
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

````
{!% else %!}
```markdown
---
name: debugger
description: Investigates and fixes bugs. Use when errors occur or behavior is unexpected.
tools: Read, Edit, Bash, Grep, Glob
model: {{! term('configured_agent_standard_model') !}}
---

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
````

{!% endif %!}
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
{!% if target == 'codex' %!}
Codex custom agents do not preload individual skill bodies by name. Put the durable role, workflow, and standards the {{! term('configured_agent') !}} needs in `{{! field('configured_agent_prompt') !}}`, and use a main conversation workflow when the {{! term('configured_agent') !}} needs to choose skills dynamically.
{!% else %!}
Subagents can preload skills via the `skills:` frontmatter field. The full SKILL.md content of each listed skill is injected into the subagent's context at startup — not lazily loaded or dynamically invoked.
{!% endif %!}

<how_it_works>

{!% if target == 'codex' %!}

- Codex custom agent files carry prompt guidance rather than a skill-preload field
- Put required standards and workflow constraints directly in `{{! field('configured_agent_prompt') !}}`
- Use a main conversation workflow when the {{! term('configured_agent') !}} needs to choose skills dynamically

{!% else %!}

- Claude Code reads each skill's SKILL.md and injects the content before the subagent runs
- The subagent sees the skill content as reference material in its context
- The subagent does NOT invoke skills at runtime with `/skill-name` — the content is already there
- Subagents do NOT inherit skills from the parent conversation — every needed skill must be listed explicitly

{!% endif %!}

</how_it_works>

<when_to_use>

{!% if target == 'codex' %!}
**Use explicit `{{! field('configured_agent_prompt') !}}` when the custom agent needs durable guidance:**

- Read-only custom agents that must produce verdicts rather than edits
- Documentation-research custom agents that need repository-specific source guidance
- Worker custom agents that need a narrowed role and output contract

**Do NOT duplicate skill bodies when:**

- The agent needs to dynamically choose which skill to load
- A normal main conversation workflow can keep the decision clearer

{!% else %!}

**Use `skills:` when the subagent needs domain methodology:**

- Audit subagents that need the full audit methodology (phases, evidence models, verdict format)
- Builder subagents that need coding standards or architecture conventions
- Any subagent that would otherwise duplicate what a skill already provides

**Do NOT use `skills:` when:**

- The {{! term('configured_agent') !}}'s {{! term('configured_agent_prompt') !}} already contains all needed instructions
- The skill content is too large and would consume excessive context
- The subagent needs to dynamically choose which skill to load (use main conversation instead)

{!% endif %!}

</when_to_use>

<example>

{!% if target == 'codex' %!}

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
model = "{{! term('configured_agent_standard_model') !}}"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
{{! field('configured_agent_prompt') !}} = """
<role>
Review code like an owner.
</role>

<constraints>
MUST produce concrete findings with file references.
</constraints>
"""
```

{!% else %!}

```text
---
name: adr-auditor
description: Audit an ADR for structure, atemporal voice, and tag validity
tools: Read, Glob, Grep, Skill
skills:
  - spec-tree:audit-adr
---

<role>
Adversarial ADR auditor. Follow the injected audit methodology exactly.
</role>

<constraints>
- Read-only — produce verdicts, not code changes
- Output structured APPROVED or REJECTED verdict
</constraints>
```

The `audit-adr` skill content (audit workflow, evidence model, verdict format) is available in the subagent's context from the start.
{!% endif %!}

</example>

<relationship_to_context_fork>

{!% if target == 'codex' %!}
Codex custom-agent configuration does not provide a per-agent `skills:` preload equivalent. Treat skill requirements as prompt guidance unless local Codex configuration gains an explicit, tested skill surface.
{!% else %!}
The `skills:` field is the inverse of a skill's `context: fork` property:

- **`skills:` in subagent**: Subagent pulls skill content in (subagent controls the {{! term('configured_agent_prompt') !}})
- **`context: fork` in skill**: Skill pushes its content into a subagent (skill controls the {{! term('configured_agent_prompt') !}})

Both use the same underlying mechanism — eager injection of skill content at startup.
{!% endif %!}

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

{!% if target == 'codex' %!}

```toml
name = "security_reviewer"
description = "..."
sandbox_mode = "read-only"
model = "{{! term('configured_agent_standard_model') !}}"
{{! field('configured_agent_prompt') !}} = """
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

{!% else %!}

```text
---
name: security-reviewer
description: ...
tools: ...
model: {{! term('configured_agent_standard_model') !}}
---

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
```

{!% endif %!}

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
✅ Good: "Reviews code for security risks. Use after changes involving authentication, data access, or user input."
</clear_triggers>

<focused_tools>
Grant only the tools needed for the task (least privilege):

- Read-only analysis: `Read, Grep, Glob`
- Code modification: `Read, Edit, Bash, Grep`
- Test running: `Read, Write, Bash`

**Security note**: Over-permissioning is primary risk vector. Start minimal, add only when necessary.
</focused_tools>

<structured_prompts>
Use XML tags to structure the {{! term('configured_agent_prompt') !}} for clarity:

```markdown
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
