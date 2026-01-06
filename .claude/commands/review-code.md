---
description: Review code for bugs, vulnerabilities, and performance issues using the Code-Reviewer subagent (opus model)
argument-hint: [task-name, file path, or 'staged']
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Code-Reviewer Subagent

Perform security-focused code review to find bugs, vulnerabilities, and performance issues.

## Input
$ARGUMENTS

## CRITICAL: Context Rule

**Main agent does NOT read files.** Only:
1. Get diff via `git diff`
2. Pass diff to Code-Reviewer subagent
3. Receive issue list from subagent

The subagent will read files if it needs additional context.

## Resolve Input

1. **If task-name** (e.g., "add-rate-limiting"):
   - Get diff: `git diff` or from task branch
   - Output: `tasks/<task-name>/code-review.md`

2. **If file path**:
   - Get diff: `git diff <file>`
   - Derive task name or use "code-review"
   - Output: `tasks/<task-name>/code-review.md`

3. **If 'staged'**:
   - Get diff: `git diff --cached`
   - Output: `tasks/staged-review/code-review.md`

4. **If nothing provided**:
   - Get diff: `git diff`
   - Output: `tasks/uncommitted-review/code-review.md`

## Setup
```bash
mkdir -p tasks/<task-name>/
```

## Instructions

1. Get diff via `git diff` (do NOT read files directly)
2. Spawn **Code-Reviewer subagent** (Task tool, model=opus):
   - Pass diff content in prompt
   - Subagent will read files if needed (stays in its isolated context)
3. Receive issue list from subagent
4. Write to output file

## Code-Reviewer Prompt Template

```
You are a security-focused code reviewer.

## Changes to Review
[Diff content from git diff]

## Your Task
Review the code for:

### 1. Security Vulnerabilities
- SQL injection, XSS, command injection
- Authentication/authorization bypasses
- Exposed secrets or sensitive data
- Insecure deserialization
- CSRF vulnerabilities
- Path traversal
- SSRF (Server-Side Request Forgery)

### 2. Bugs
- Null/undefined references
- Off-by-one errors
- Race conditions
- Incorrect error handling
- Logic errors
- Type mismatches
- Resource leaks

### 3. Performance Issues
- N+1 queries
- Memory leaks
- Blocking operations in async code
- Inefficient algorithms
- Missing database indexes
- Unnecessary database calls
- Large payload handling

### 4. Breaking Changes
- API compatibility issues
- Database migration risks
- Changed return types/signatures
- Removed functionality

**If you need more context**, use the Read tool to examine specific files.
Your file reads stay in your isolated context and don't pollute the main agent.

## Output Format
```markdown
# Code Review: [Task/File Name]

## Summary
[Overview - X critical, Y high, Z medium, W low issues]

## Critical Issues
### [Issue Title]
- **Location:** `file.py:123`
- **Type:** [Security/Bug/Performance/Breaking]
- **Description:** [What's wrong]
- **Impact:** [What could happen]
- **Fix:**
\`\`\`python
# suggested fix
\`\`\`

## High Issues
...

## Medium Issues
...

## Low Issues
...

## Recommendations
- [General improvement suggestions]

## Verdict
[PASS / PASS WITH WARNINGS / FAIL]
```

If no issues: "NO ISSUES FOUND - Code review passed."
```

## Output

Save subagent's response to `tasks/<task-name>/code-review.md`
