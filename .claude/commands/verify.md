---
description: Verify that implementation solves the original problem using the Code-Goal subagent
argument-hint: [task-name]
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Verify Implementation

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
4. Spawn **Code-Goal** agent (Task tool):
   - Use agent defined in `~/.claude/agents/code-goal.md`
   - model: sonnet
   - Pass problem, diff, and test info in prompt
5. Receive verification verdict from agent
6. Save to output file

## Agent Invocation

```
Task tool parameters:
- subagent_type: "Code-Goal"
- model: "sonnet"
- prompt: |
    ## Original Problem Statement
    [Content from problem.md]

    ## Acceptance Criteria
    [Extracted from problem.md]

    ## Implementation Changes
    [Git diff content]

    ## Test Cases
    [Content from test files]

    Verify this implementation following your guidelines.
```

## Output

Save to `tasks/<task-name>/verification.md`
