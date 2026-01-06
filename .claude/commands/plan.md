---
description: Create an implementation plan using the Planner subagent (opus model)
argument-hint: [task description]
allowed-tools: Task, Read, Glob, Grep, Write, Bash, TodoWrite
---

# Planner Subagent

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
2. Invoke the Planner subagent:
   ```
   Task tool parameters:
   - subagent_type: "general-purpose"
   - model: "opus"
   - prompt: [Use template below with filled placeholders]
   ```

## Planner Prompt Template

```
You are a senior software architect creating an implementation plan.

## Problem Statement
[Task description from arguments]

## Codebase Context
### Relevant Files:
[List from context.md or exploration]

### File Contents:
[Include contents of core files - read them first]

## Your Task
Create a detailed, step-by-step implementation plan that:
1. Follows existing patterns and conventions in the codebase
2. Minimizes changes while fully solving the problem
3. Considers edge cases and error handling
4. Includes specific code locations and changes
5. Defines clear testing strategy

## Output Format
```markdown
# Implementation Plan: [Task Name]

## Overview
[Brief description]

## Prerequisites
- [Setup needed]

## Implementation Steps

### Step 1: [Title]
**Files:** `path/to/file.py`
**Changes:**
- [Specific change]

**Code:**
\`\`\`python
# Example if helpful
\`\`\`

### Step 2: [Title]
...

## Testing Strategy
- [ ] [Test case]

## Edge Cases
- [Edge case and handling]

## Risks
- **Risk:** [Description]
  **Mitigation:** [Solution]
```
```

## Output

Save the plan to `tasks/<task-name>/plan.md`
