---
description: Simplify code using the Code-Simplifier subagent - removes complexity, finds abstractions, uses idioms
argument-hint: [task-name, file path, or 'staged']
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Code-Simplifier Subagent

Analyze code for unnecessary complexity and suggest simplifications.

## Input
$ARGUMENTS

## CRITICAL: Context Rule

**Main agent does NOT read files.** Only:
1. Get diff via `git diff`
2. Pass diff to Code-Simplifier subagent
3. Receive suggestions from subagent

The subagent will read files if it needs additional context.

## Resolve Input

1. **If task-name** (e.g., "add-rate-limiting"):
   - Get diff: `git diff` or from task branch
   - Output: `tasks/<task-name>/simplify-review.md`

2. **If file path**:
   - Get diff: `git diff <file>`
   - Derive task name or use "code-simplify"
   - Output: `tasks/<task-name>/simplify-review.md`

3. **If 'staged'**:
   - Get diff: `git diff --cached`
   - Output: `tasks/staged-review/simplify-review.md`

4. **If nothing provided**:
   - Get diff: `git diff`
   - Output: `tasks/uncommitted-review/simplify-review.md`

## Setup
```bash
mkdir -p tasks/<task-name>/
```

## Instructions

1. Get diff via `git diff` (do NOT read files directly)
2. Spawn **Code-Simplifier subagent** (Task tool, model=opus):
   - Pass diff content in prompt
   - Subagent will read files if needed (stays in its isolated context)
3. Receive suggestions from subagent
4. Write to output file

## Code-Simplifier Prompt Template

```
You are a code simplification expert. Your goal is to make code cleaner and simpler.

## Code to Review
[Diff content from git diff]

## Your Task
Analyze the code for:

1. **Redundant code**: Duplicate logic that can be consolidated
2. **Dead code**: Unused variables, unreachable branches
3. **Unnecessary abstraction**: Over-engineering, premature generalization
4. **Missed abstractions**: Repeated patterns that should be functions
5. **Verbose constructs**: Code that can use language idioms
6. **Redundant checks**: Conditions that are always true/false

## Python Idioms to Consider
- List/dict/set comprehensions
- Context managers (with statements)
- Unpacking and multiple assignment
- f-strings over .format()
- Built-in functions (any, all, zip, enumerate)
- collections module (defaultdict, Counter)
- itertools for iteration patterns
- walrus operator (:=) where appropriate

**If you need more context**, use the Read tool to examine specific files.
Your file reads stay in your isolated context and don't pollute the main agent.

## Output Format
```markdown
# Simplification Review

## Summary
[Overview of findings]

## Findings

### High Impact
#### [Issue Title]
- **Location:** `file.py:123`
- **Issue:** [Description]
- **Before:**
\`\`\`python
# current code
\`\`\`
- **After:**
\`\`\`python
# simplified code
\`\`\`
- **Benefit:** [Why this is better]

### Medium Impact
...

### Low Impact (Nice to Have)
...

## Metrics
- Redundant code instances: X
- Dead code instances: X
- Simplification opportunities: X
```
```

## Output

Save subagent's response to `tasks/<task-name>/simplify-review.md`
