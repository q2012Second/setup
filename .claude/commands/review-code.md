---
description: Review code for bugs, vulnerabilities, and performance issues using Codex + Code-Reviewer subagent (opus model)
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
2. Run Codex review (reads codebase in its own read-only sandbox)
3. Triage Codex findings
4. Pass diff + triaged Codex findings to Code-Reviewer agent
5. Receive issue list from agent
6. Fix issues (read only files being fixed)
7. Re-review until clean

Codex explores the codebase in its sandbox. The Code-Reviewer subagent will also read files to check existing style and patterns.

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

Run Codex review against the changes:

```bash
codex review --uncommitted -m gpt-5.3-codex \
  -o tasks/<task-name>/codex-code-review-REVIEW_ITERATION.md \
  "<codex-review-prompt>"
```

**Note:** Use `--uncommitted` for unstaged/staged changes. If reviewing a specific branch, omit `--uncommitted` and use `--base <branch>` instead.

**Codex review prompt:**

```
Review these code changes for production readiness. Be thorough and critical.

Review the changes against the ACTUAL CODEBASE for:

1. SECURITY: SQL injection, XSS, command injection, auth bypass, secrets exposure, CSRF, insecure deserialization, SSRF, or any OWASP Top 10 vulnerability?
2. BUGS: Logic errors, off-by-one, null/undefined handling, race conditions, deadlocks, resource leaks, incorrect error handling?
3. BACKWARD COMPATIBILITY: Does this break existing API contracts, database schemas, message formats, or client expectations? Are migrations needed?
4. ACCURACY: Does the code correctly implement the stated intent? Wrong function calls, incorrect parameters, misunderstandings of the codebase?
5. OVER-ENGINEERING: Unnecessary abstractions, premature optimizations, feature flags, or complexity not justified by requirements?
6. EDGE CASES: Unhandled error paths, boundary conditions, empty/null inputs, timeout scenarios, concurrent access?
7. TESTING: Are changes adequately tested? Missing test cases for new behavior or edge cases?
8. PERFORMANCE: N+1 queries, missing indexes, unbounded loops, memory leaks, expensive operations in hot paths?

Format your response as a numbered list of findings. For each finding:
- File and lines it refers to
- Severity: CRITICAL (must fix before prod) / HIGH (should fix) / MEDIUM (recommended) / LOW (nice to have)
- Category (from the list above)
- Specific evidence from the codebase (file paths, line numbers, code snippets)
- A concrete suggestion for how to fix it

End with exactly one of:
- **NO ISSUES FOUND** — if no findings at all
- **APPROVED** — if no CRITICAL or HIGH findings
- **NEEDS FIXES** — if any CRITICAL or HIGH findings exist
```

**Bash timeout: 600000ms (10 min).** If it times out, retry once.

### Step 3: Analyze Codex Findings

Read `tasks/<task-name>/codex-code-review-REVIEW_ITERATION.md` and analyze each finding:

1. For each finding, do a quick verification against the codebase (use Grep/Glob — do NOT read full files unless fixing)
2. Classify each finding as:
   - **VALID** — Correct, the code should change. Preserve severity.
   - **INVALID** — Incorrect. State why with brief evidence.
   - **OVERENGINEERED** — Suggests unnecessary complexity. State why current code is sufficient.
3. Write analysis to `tasks/<task-name>/codex-code-analysis-REVIEW_ITERATION.md`

### Step 4: Code-Reviewer Review

Spawn **Code-Reviewer** agent (Task tool):
- Use agent defined in `~/.claude/agents/code-reviewer.md`
- model: opus
- Pass in prompt:
  - Diff content
  - Codex findings + classifications from Step 3 (full analysis so reviewer can agree/disagree)

```
Task tool parameters:
- subagent_type: "Code-Reviewer"
- model: "opus"
- prompt: |
    ## Changes to Review
    [Diff content from git diff]

    ## Codex Review Findings (pre-classified)
    [Full content of codex-code-analysis-REVIEW_ITERATION.md]

    Review this code following your guidelines across all 10 categories.
    The Codex findings above have been triaged — you may agree or disagree with the classifications.
    Add any issues Codex missed.
```

Write review to `tasks/<task-name>/code-review.md`.

### Step 5: Convergence Check

- If both Codex (Step 2) and Code-Reviewer (Step 4) returned **NO ISSUES FOUND** or **APPROVED** (only Low-severity remain) → done
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
