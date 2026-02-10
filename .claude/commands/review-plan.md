---
description: Review an implementation plan using the Plan-Reviewer subagent (opus model)
argument-hint: [task-name or path to plan.md]
allowed-tools: Task, Read, Glob, Grep, Write
---

# Review Plan

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
3. Spawn **Plan-Reviewer** agent (Task tool):
   - Use agent defined in `~/.claude/agents/plan-reviewer.md`
   - model: opus
   - Pass plan content and context in prompt
4. Receive review from agent
5. Save to output file

## Agent Invocation

```
Task tool parameters:
- subagent_type: "Plan-Reviewer"
- model: "opus"
- prompt: |
    ## Problem Statement
    [Extract from plan or problem.md]

    ## Proposed Plan
    [Full plan content]

    ## Codebase Context
    [From context.md or summary]

    Review this plan following your guidelines. Verify all claims against the actual codebase.
    Output a numbered list of findings with: plan reference, category, evidence, and suggestion.
```

## Output

Save review to `tasks/<task-name>/plan-review.md`
