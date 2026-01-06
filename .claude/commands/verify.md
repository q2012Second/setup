---
description: Verify that implementation solves the original problem using the Code-Goal subagent
argument-hint: [task-name]
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Code-Goal Subagent

Verify that the implementation actually solves the stated problem.

## Input
$ARGUMENTS

## Resolve Task

1. **Task name provided** (e.g., "add-rate-limiting"):
   - Problem: `tasks/<task-name>/problem.md`
   - Plan: `tasks/<task-name>/plan.md`
   - Output: `tasks/<task-name>/verification.md`

2. **If problem.md doesn't exist**:
   - Ask user for the problem statement
   - Create `tasks/<task-name>/problem.md` first

## Instructions

1. Read problem statement from `tasks/<task-name>/problem.md`
2. Get implementation changes: `git diff main` or staged changes
3. Find related test files
4. Invoke Code-Goal subagent:
   ```
   Task tool parameters:
   - subagent_type: "general-purpose"
   - model: "sonnet"
   - prompt: [Use template below]
   ```

## Code-Goal Prompt Template

```
You are verifying that an implementation matches its requirements.

## Original Problem Statement
[Content from problem.md]

## Acceptance Criteria
[Extracted from problem.md]

## Implementation Changes
[Git diff content]

## Test Cases
[Content from test files]

## Your Task
Verify:

### 1. Problem Solved
For each acceptance criterion:
- Is it addressed by the implementation?
- How specifically is it solved?

### 2. Test Coverage
- Are acceptance criteria covered by tests?
- Are edge cases tested?
- Any missing test scenarios?

### 3. Completeness
- Any partial implementations?
- TODO comments left behind?
- Incomplete error handling?

## Output Format
```markdown
# Verification: [Task Name]

## Acceptance Criteria Check

| Criterion | Status | Evidence |
|-----------|--------|----------|
| [Criterion 1] | [PASS/FAIL] | [How it's met or why it fails] |
| [Criterion 2] | [PASS/FAIL] | [How it's met or why it fails] |

## Test Coverage

| Criterion | Test File | Test Case |
|-----------|-----------|-----------|
| [Criterion 1] | `test_file.py` | `test_function_name` |
| [Criterion 2] | - | MISSING |

## Missing Tests
- [ ] [Test that should be added]

## Gaps Found
- [Gap 1]: [Description and how to fix]

## TODOs/Incomplete Items
- [ ] [TODO found in code]

## Verdict
**[VERIFIED / NEEDS WORK]**

### If NEEDS WORK:
1. [Action item 1]
2. [Action item 2]
```
```

## Output

Save to `tasks/<task-name>/verification.md`
