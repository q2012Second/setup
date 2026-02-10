---
description: Review code for bugs, vulnerabilities, and performance issues using the Code-Reviewer subagent (opus model)
argument-hint: [task-name, file path, or 'staged']
allowed-tools: Task, Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion
---

# Review Code

Perform code review to find over-engineering, style inconsistencies, bugs, vulnerabilities, and performance issues. Iterates until clean.

## Input
$ARGUMENTS

## CRITICAL: Context Rule

**Main agent does NOT read source files for review.** Only:
1. Get diff via `git diff`
2. Pass diff to Code-Reviewer agent
3. Receive issue list from agent
4. Fix issues (read only files being fixed)
5. Re-review until clean

The agent will read files to check existing style and patterns.

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

### Review Loop

Repeat until Code-Reviewer returns **NO ISSUES FOUND** or only Low-severity issues remain:

1. Get diff via `git diff` (do NOT read files directly)
2. Spawn **Code-Reviewer** agent (Task tool):
   - Use agent defined in `~/.claude/agents/code-reviewer.md`
   - model: opus
   - Pass diff content in prompt
3. Write review to output file
4. If **Critical, High, or Medium** issues found:
   a. Fix issues (read only files being modified)
   b. Go back to step 1 with fresh diff
5. If only **Low** or **NO ISSUES FOUND** → done

## Agent Invocation

```
Task tool parameters:
- subagent_type: "Code-Reviewer"
- model: "opus"
- prompt: |
    ## Changes to Review
    [Diff content from git diff]

    Review this code following your guidelines across all 10 categories.
```

## Output

Save final review to `tasks/<task-name>/code-review.md`

Present summary:
```
Code review complete after N iteration(s).
- Issues found: X total (Y fixed, Z low-severity remaining)
- Categories: [breakdown]
- Full report: tasks/<task-name>/code-review.md
```
