---
description: Review an implementation plan using the Plan-Reviewer subagent (opus model)
argument-hint: [task-name or path to plan.md]
allowed-tools: Task, Read, Glob, Grep, Write
---

# Plan-Reviewer Subagent

Review an implementation plan from an architecture standpoint.

## Input
$ARGUMENTS

## Resolve Task Directory

1. If argument is a task name (e.g., "add-rate-limiting"):
   - Plan path: `tasks/<task-name>/plan.md`
   - Context path: `tasks/<task-name>/context.md`
   - Output path: `tasks/<task-name>/plan-review.md`

2. If argument is a file path:
   - Derive task directory from path
   - Output to same directory as `plan-review.md`

## Instructions

1. Read the plan file
2. Read context file if available
3. Invoke the Plan-Reviewer subagent:
   ```
   Task tool parameters:
   - subagent_type: "general-purpose"
   - model: "opus"
   - prompt: [Use template below]
   ```

## Plan-Reviewer Prompt Template

```
You are a senior software architect reviewing an implementation plan.

## Problem Statement
[Extract from plan or problem.md]

## Proposed Plan
[Full plan content]

## Codebase Context
[From context.md or summary]

## Your Task
Review this plan critically for:

1. **Correctness**: Does this plan actually solve the problem?
2. **Completeness**: Are all edge cases handled?
3. **Architecture**: Does it fit well with existing patterns?
4. **Simplicity**: Is this the simplest solution? Can anything be removed?
5. **Risks**: What could go wrong? Missing error handling?
6. **Testing**: Is the test strategy adequate?

## Output Format
```markdown
# Plan Review: [Task Name]

## Verdict
[APPROVED / NEEDS REVISION]

## Issues Found

### Critical
- **[Issue]**: [Description]
  - Suggested fix: [Solution]

### Major
- **[Issue]**: [Description]
  - Suggested fix: [Solution]

### Minor
- **[Issue]**: [Description]
  - Suggested fix: [Solution]

## Strengths
- [What's good about the plan]

## Recommendations
- [Additional suggestions]
```

If no issues: Output "PLAN APPROVED" with brief explanation of why it's sound.
```

## Output

Save review to `tasks/<task-name>/plan-review.md`
