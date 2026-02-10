---
description: Create an implementation plan using the Planner subagent (opus model)
argument-hint: [task description]
allowed-tools: Task, Read, Glob, Grep, Write, Bash, TodoWrite, AskUserQuestion
---

# Create Plan

Create a detailed implementation plan for the given task.

## Task
$ARGUMENTS

## Setup

1. **Create task directory**: Derive kebab-case name from task
   - Example: "add user notifications" → `tasks/add-user-notifications/`
   - Run: `mkdir -p tasks/<task-name>/`

2. **If context doesn't exist**: First run context gathering and save to `tasks/<task-name>/context.md`

## Instructions

1. Gather context by finding relevant files (save to `context.md` if not exists)
2. Spawn **Planner** agent (Task tool):
   - Use agent defined in `~/.claude/agents/planner.md`
   - model: opus
   - Pass problem statement and context in prompt
3. Receive plan from agent
4. Save to `tasks/<task-name>/plan.md`
5. **Check for questions** in the plan's "Questions for the User" section
   - If questions exist (not "None"), present them to user using AskUserQuestion
   - Spawn Planner (revision mode) with answers to update plan

## Agent Invocation

```
Task tool parameters:
- subagent_type: "Planner"
- model: "opus"
- prompt: |
    ## Problem Statement
    [Task description from arguments]

    ## Codebase Context
    ### Relevant Files:
    [List from context.md or exploration]

    ### File Contents:
    [Include contents of core files - read them first]

    Create a plan following your guidelines. Explore the codebase thoroughly before writing.
    Surface any questions about ambiguous requirements in the "Questions for the User" section.
```

## Output

Save the plan to `tasks/<task-name>/plan.md`
