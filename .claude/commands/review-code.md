---
description: Review code for bugs, vulnerabilities, and performance issues using Codex + Code-Reviewer subagent (opus model)
argument-hint: [task-name, file path, or 'staged']
allowed-tools: Task, Read, Glob, Grep, Bash, Write, Edit, AskUserQuestion, mcp__codex-cli__review_code
---

# Review Code

Perform code review to find over-engineering, style inconsistencies, bugs, vulnerabilities, and performance issues. Iterates until clean.

## Input
$ARGUMENTS

## CRITICAL: Context Rule

**Main agent does NOT read source files for review.** Only:
1. Get diff via `git diff`
2. Run Codex review (reads codebase in its own read-only sandbox)
3. Delegate Codex triage to **Codex-Analyzer subagent** (sonnet) — main agent never reads Codex output
4. Pass diff + **VALID findings only** to Code-Reviewer agent
5. Receive issue list from agent
6. Fix issues (read only files being fixed)
7. Re-review until clean

Codex explores the codebase in its sandbox. The Codex-Analyzer subagent triages findings and returns only VALID ones. The Code-Reviewer subagent will also read files to check existing style and patterns.

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

Track **REVIEW_ITERATION = 1**. Repeat until both Codex and Code-Reviewer agree no Critical/High/Medium issues remain:

### Step 1: Generate Diff

Get the appropriate diff based on input type (do NOT read files directly):
- Task name: `git diff` or branch diff
- File path: `git diff <file>`
- Staged: `git diff --cached`
- Nothing: `git diff`

Save to `tasks/<task-name>/diff.patch`.

### Step 2: Codex Code Review (mandatory)

Run Codex review against the changes.

Use the `review_code` MCP tool with:
- output_file: "tasks/<task-name>/codex-code-review-REVIEW_ITERATION.md"
- uncommitted: true
- working_directory: project root path

**Note:** Use `uncommitted: true` for unstaged/staged changes. For reviewing a specific branch, use `base_branch: "<branch>"` instead.

### Step 3: Analyze Codex Findings (via subagent)

Spawn **Codex-Analyzer subagent** (Task tool, model=sonnet) with:
- Codex review file path: `tasks/<task-name>/codex-code-review-REVIEW_ITERATION.md`
- Analysis output path: `tasks/<task-name>/codex-code-analysis-REVIEW_ITERATION.md`
- Review type: "code"

Receive back: **Codex verdict** and **VALID findings only**.

**Main agent does NOT read the Codex output or analysis files.**

### Step 4: Code-Reviewer Review

Spawn **Code-Reviewer** agent (Task tool):
- Use agent defined in `~/.claude/agents/code-reviewer.md`
- model: opus
- Pass in prompt:
  - Diff content
  - VALID Codex findings only (the summary returned by Codex-Analyzer, NOT the full analysis file)

```
Task tool parameters:
- subagent_type: "Code-Reviewer"
- model: "opus"
- prompt: |
    ## Changes to Review
    [Diff content from git diff]

    ## Codex Review Findings (VALID only)
    [VALID findings summary from Codex-Analyzer subagent response]

    Review this code following your guidelines across all 10 categories.
    The Codex findings above have been pre-triaged (VALID only) — add any issues Codex missed.
```

Write review to `tasks/<task-name>/code-review.md`.

### Step 5: Convergence Check

- If both Codex verdict (from Step 3) and Code-Reviewer (Step 4) returned **NO ISSUES FOUND** or **APPROVED** (only Low-severity remain) → done
- If either returned **NEEDS FIXES** (Critical, High, or Medium issues):
   a. Collect all VALID findings from both reviews
   b. Fix issues (read only files being modified)
   c. Increment REVIEW_ITERATION
   d. Go back to Step 1 with fresh diff

## Output

Save final review to `tasks/<task-name>/code-review.md`

Present summary:
```
Code review complete after N iteration(s).
- Codex reviews: N (artifacts: codex-code-review-*.md / codex-code-analysis-*.md)
- Code-Reviewer reviews: N
- Issues found: X total (Y fixed, Z low-severity remaining)
- Categories: [breakdown]
- Full report: tasks/<task-name>/code-review.md
```
