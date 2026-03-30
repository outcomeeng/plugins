# Review Protocol (Phases 0-5)

## Phase 0: Identify Scope

1. Determine the target files/directories to review
2. Check `CLAUDE.md`/`README.md` for the project validation command
3. Prefer project command over tool-by-tool execution

### Project-Specific Commands

Many projects define custom validation commands in `CLAUDE.md` or `README.md`. Check for and run these before concluding review:

```bash
# Common patterns to look for:
just check        # Justfile task runner
just validate
pnpm run check    # pnpm scripts
pnpm run validate
npm run check     # npm scripts
npm run validate
make check        # Makefile targets
make lint
```

**If CLAUDE.md specifies validation commands**: Run them. Failures = REJECTED.

## Phase 1: Project Validation

Run exactly one project validation command. Do not run `tsc`, `eslint`, or `semgrep` individually during review.

### 1.0 Import Hygiene Check (Automated)

**Run FIRST before other tools.** Deep relative imports are a blocking violation.

```bash
# Detect deep relative imports (2+ levels of ../)
grep -rn --include="*.ts" --include="*.tsx" 'from ["'"'"']\.\.\/\.\.\/' src/ test/ tests/
```

**Interpretation:**

| Output        | Verdict | Action                                        |
| ------------- | ------- | --------------------------------------------- |
| No matches    | ✅ PASS | Continue to next check                        |
| Matches found | ❌ FAIL | List violations, continue checks, will REJECT |

**Example output (blocking):**

```text
src/commands/build/index.ts:5:import { Config } from "../../shared/config";
tests/unit/parser.test.ts:3:import { helper } from "../../../test-utils/fixtures";
```

**For each match, determine:**

1. **Is this module-internal?** (Same module, moves together) → ❌ REJECT, must use alias
2. **Is this a stable location?** (lib/, tests/helpers/, shared/) → ❌ REJECT, must use alias

See `references/manual-review-checklist.md` → "Import Hygiene" for the full decision tree.

### 1.1 Validation Command

Use the project command from `CLAUDE.md` first. If unspecified, prefer:

```bash
pnpm validate
```

**Blocking**: Any non-zero exit code = REJECTION

## Phase 2: Infrastructure Provisioning

Before running tests, ensure required infrastructure is available.

### Detect Infrastructure Requirements

```bash
# Find infrastructure-related test patterns
grep -r "describe.*integration\|describe.*e2e" test/

# Check for docker-compose
ls docker-compose*.yml 2>/dev/null
```

Common patterns:

| Pattern             | Infrastructure  | How to Start                |
| ------------------- | --------------- | --------------------------- |
| `test/integration/` | Real binaries   | Ensure Hugo/Caddy installed |
| `test/e2e/`         | Chrome + server | `npm run dev` + Chrome      |
| `docker-compose.*`  | Docker services | `docker compose up -d`      |

### Provision Infrastructure

```bash
# For Docker services
docker compose up -d
docker compose ps --format json | jq '.Health'
```

### Infrastructure Failures

If infrastructure cannot start:

1. Document what was tried and what failed
2. Report the blocker
3. Use verdict **REJECTED**

```markdown
## Infrastructure Provisioning Failed

**Required**: Docker with PostgreSQL container
**Attempted**: `docker compose up -d`
**Error**: `docker: command not found`

**Verdict**: REJECTED (infrastructure unavailable; review cannot verify quality)
```

## Phase 3: Test Execution

Run the **full** test suite with coverage. ALL tests must pass.

```bash
npx vitest run --coverage
# Or: npm test -- --coverage
```

**Blocking**: ANY test failure = REJECTION

### Coverage Requirements (MANDATORY)

| Scenario                      | Verdict      | Rationale              |
| ----------------------------- | ------------ | ---------------------- |
| Coverage ≥80%                 | PASS         | Verified               |
| Coverage <80%                 | REJECTED     | Insufficient evidence  |
| Coverage = 0%                 | REJECTED     | No tests covering code |
| Coverage plugin NOT installed | **REJECTED** | Coverage unverifiable  |
| vitest fails to run           | **REJECTED** | Tests unverifiable     |

**Crystal Clear**: You cannot approve code with unmeasured coverage.

### Distinguish Failure Types

| Failure Type           | Example                         | Verdict  |
| ---------------------- | ------------------------------- | -------- |
| **Code defect**        | Assertion failed                | REJECTED |
| **Infrastructure**     | "Connection refused"            | REJECTED |
| **Missing dependency** | Import error for test framework | REJECTED |

## Phase 4: Manual Code Review

Read ALL code under review. See `references/manual-review-checklist.md` for full checklist.

Key areas:

- Type Safety (no unjustified `any`, no `@ts-ignore`)
- Error Handling (no empty catch blocks)
- Resource Management (streams/connections closed)
- Security (no hardcoded secrets, no eval)
- Code Quality (JSDoc, no dead code)
- Testing (see `references/verification-tests.md`)

## Phase 5: Determine Verdict

Based on findings:

| Verdict      | Criteria                                  | Next Phase             |
| ------------ | ----------------------------------------- | ---------------------- |
| **APPROVED** | All checks pass, no issues                | Phase 6 (Verification) |
| **REJECTED** | Real bugs, security issues, test failures | Return to coder        |

**If verdict is APPROVED**: Continue to `workflows/verification-protocol.md`
**If verdict is REJECTED**: Return rejection feedback
