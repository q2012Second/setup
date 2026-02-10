---
description: Gather codebase context by finding relevant files for a task
argument-hint: [task-name or topic description]
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Context Gathering

Find the most relevant files in the codebase for a given task.

## Input
$ARGUMENTS

## Instructions

1. Use the Explore subagent (Task tool with subagent_type="Explore") to search thoroughly:
   - Search for related keywords
   - Find files by pattern matching
   - Look for existing similar implementations
   - Trace code paths from entry points through the call chain

2. Identify all relevant files (focus on relevance, not a fixed count):
   - Core files (directly involved in the task)
   - Related files (callers, callees — may be affected by changes)
   - Test files (existing tests to consider)
   - Config/migration files (if relevant)
   - Research files from `research/` directory (if relevant to the task domain)

3. Categorize files by relevance level

## Output

**Default:** Return file list directly in response (no file created):

```
## Relevant Files for: [Task]

### Core Files (directly involved)
- `path/to/file1.py` - [Brief relevance]
- `path/to/file2.py` - [Brief relevance]

### Related Files (may be affected)
- `path/to/related1.py` - [Brief relevance]

### Test Files
- `path/to/test_file.py` - [What it tests]

### Key Patterns Observed
- [Pattern 1]
- [Pattern 2]
```

**If user explicitly requests a file:** Save to `tasks/<task-name>/context.md`
