# Workflow: Verify Skill Content is Current

<required_reading>
Read these reference files NOW:

1. `references/core-principles.md`

</required_reading>

<process>
## Step 1: Identify Skill to Verify

**If user provided path**: Use that skill

**If not specified**: Ask which skill to verify

## Step 2: Inventory External Dependencies

Read the skill and identify:

1. **APIs/Services referenced**
   - External APIs (OpenAI, Stripe, etc.)
   - Cloud services (AWS, GCP, Azure)
   - Third-party tools

2. **Libraries/Packages**
   - Python packages
   - npm packages
   - Other dependencies

3. **Documentation links**
   - Official docs URLs
   - Tutorial links
   - Reference material

4. **Best practices/patterns**
   - Date-sensitive recommendations
   - Version-specific guidance

## Step 3: Check for Staleness

For each external dependency:

### APIs/Services

```
Use WebFetch or WebSearch to check:
- Has the API version changed?
- Are endpoints still valid?
- Have authentication methods changed?
- Are there breaking changes?
```

### Libraries/Packages

```bash
# Check latest versions
npm show {package} version  # for npm
pip index versions {package}  # for pip
```

### Documentation Links

```
Use WebFetch to verify:
- Does the URL still work?
- Has the content moved?
- Is the information current?
```

### Best Practices

```
Use WebSearch for:
"{technology} best practices 2025"
"{technology} deprecated features"
```

## Step 4: Document Findings

Create a verification report:

```
## Verification Report: {skill-name}

### Current
- [ ] {Item}: Still accurate as of {date}

### Needs Update
- [ ] {Item}: {What changed}
  → Recommendation: {How to fix}

### Broken
- [ ] {Item}: {What's wrong}
  → Recommendation: {How to fix}

### Verified On: {date}
```

## Step 5: Offer Updates

If issues found, ask:
"Would you like me to update the skill with current information?"

Options:

1. **Update all** - Apply all recommended updates
2. **Update one by one** - Review each update
3. **Just the report** - No changes needed

## Step 6: Apply Updates (if requested)

For each update:

1. Make the change
2. Note what was updated
3. Verify the new content is accurate

## Step 7: Add Verification Timestamp

Consider adding to SKILL.md:

```text
<last_verified>Content verified current as of: {YYYY-MM-DD}</last_verified>
```

</process>

<staleness_indicators>
Signs a skill may need verification:

| Indicator               | Check                              |
| ----------------------- | ---------------------------------- |
| Time-sensitive info     | Dates, version numbers, "as of..." |
| External URLs           | Links to docs, tutorials           |
| API references          | Endpoints, authentication          |
| Library versions        | Package versions, imports          |
| Best practices          | Recommendations that evolve        |
| Deprecated features     | Old patterns still referenced      |
| </staleness_indicators> |                                    |

<success_criteria>
Verification is complete when:

- [ ] All external dependencies inventoried
- [ ] Each dependency checked for currency
- [ ] Report generated with findings
- [ ] Updates applied (if requested)
- [ ] Verification timestamp added
- [ ] User has confidence in skill accuracy

</success_criteria>
