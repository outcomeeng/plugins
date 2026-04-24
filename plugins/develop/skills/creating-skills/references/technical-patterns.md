<overview>

Technical patterns for skills that execute processes — error handling, security, dependencies, performance. Reference these when the skill you're building processes data, calls APIs, handles files, or performs any multi-step operation with failure modes.

Skill structure standards (naming, frontmatter, XML tags, file organization) live in `/standardizing-skills`. This file covers concerns internal to what skills DO, not how they're shaped.

</overview>

<error_handling>

Document error scenarios and actions in a table:

```markdown
## Error Handling

| Scenario        | Detection               | Action                      |
| --------------- | ----------------------- | --------------------------- |
| Invalid input   | Validation fails        | Return error with specifics |
| File not found  | FileNotFoundError       | Clear message, suggest fix  |
| Network failure | Timeout/ConnectionError | Retry 3x with backoff       |
| Auth failure    | 401/403 response        | Prompt re-authentication    |
| Unknown error   | Catch-all exception     | Log context, safe default   |
```

**Retry with exponential backoff:**

```python
import time
import random


def retry_with_backoff(func, max_retries=3, base_delay=0.1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2**attempt) + random.uniform(0, 0.1)
            time.sleep(delay)
```

**Consistent error response shape:**

```typescript
interface ErrorResponse {
  isError: true;
  content: [{ type: "text"; text: string }]; // User-facing message
  _meta?: {
    errorCode: string; // Machine-readable code
    details: unknown; // Debug info (not shown to user)
    retryable: boolean; // Can the user retry?
  };
}
```

**Graceful degradation ladder:**

1. **Primary** — execute main logic
2. **Retry** — transient failure with backoff
3. **Cache** — serve cached result if available
4. **Fallback** — safe default or partial result
5. **Fail** — clear error message with next steps

</error_handling>

<security>

**Secrets:**

- NEVER hardcode API keys, tokens, or passwords in code.
- NEVER commit `.env` files.
- NEVER log sensitive values or put them in error messages.
- ALWAYS use environment variables; keep `.env` in `.gitignore`; provide `.env.example`.

**Path traversal prevention:**

```python
import os


def safe_path(base_dir: str, user_path: str) -> str:
    full_path = os.path.normpath(os.path.join(base_dir, user_path))
    if not full_path.startswith(os.path.normpath(base_dir)):
        raise ValueError("Invalid path: traversal detected")
    return full_path
```

**Input validation with schema:**

```typescript
import { z } from "zod";

const InputSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  count: z.number().int().positive().max(1000),
});

const result = InputSchema.safeParse(userInput);
if (!result.success) {
  return { error: result.error.format() };
}
```

**SQL — parameterized queries only:**

```python
# ❌ NEVER
query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection

# ✅ ALWAYS
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Output escaping for generated HTML:**

```typescript
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}
```

</security>

<dependencies>

Document dependencies so Claude knows what the skill requires:

```markdown
## Dependencies

### Required

- Python 3.10+ (for match statements)
- Node.js 18+ (for fetch API)

### Optional

- Redis 7+ (caching, improves performance)
- Docker (containerized deployment)

### External APIs

| API    | Purpose     | Rate Limit | Auth    |
| ------ | ----------- | ---------- | ------- |
| OpenAI | Embeddings  | 3000/min   | API key |
| GitHub | Repo access | 5000/hour  | OAuth   |
```

**Version compatibility matrix** (when version matters):

```markdown
| Component | Minimum | Recommended | Notes                     |
| --------- | ------- | ----------- | ------------------------- |
| Python    | 3.10    | 3.11+       | Match statements required |
| Node.js   | 18      | 20 LTS      | Native fetch required     |
```

</dependencies>

<performance>

**Timeout protection:**

```typescript
async function withTimeout<T>(promise: Promise<T>, ms: number, message = "Operation timed out"): Promise<T> {
  const timeout = new Promise<never>((_, reject) => setTimeout(() => reject(new Error(message)), ms));
  return Promise.race([promise, timeout]);
}

const result = await withTimeout(fetchData(), 5000);
```

**Resource limits** — document and enforce:

```markdown
| Resource            | Limit     | Reason             |
| ------------------- | --------- | ------------------ |
| Request timeout     | 25s       | Platform limit     |
| File size           | 10MB      | Memory constraints |
| Batch size          | 100 items | API rate limits    |
| Concurrent requests | 5         | Prevent overload   |
```

</performance>

<edge_cases>

Always handle:

| Category    | Edge cases                                     |
| ----------- | ---------------------------------------------- |
| **Input**   | Empty, null, undefined, very large             |
| **Files**   | Missing, locked, wrong format, empty           |
| **Network** | Timeout, DNS failure, rate limited             |
| **Data**    | Unicode, special chars, injection attempts     |
| **State**   | Concurrent access, stale data, race conditions |

</edge_cases>
