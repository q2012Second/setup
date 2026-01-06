---
description: Run the full structured workflow for a task (problem clarification, planning, implementation, review, verification)
argument-hint: [task description]
allowed-tools: Task, Read, Glob, Grep, Edit, Write, Bash, TodoWrite, AskUserQuestion
---

# Full Workflow

Execute the complete Claude Code workflow as defined in AGENTS.md.

## Task
$ARGUMENTS

## Setup

1. **Check for existing workflow to resume**:
   ```bash
   ls tasks/*/state.json 2>/dev/null
   ```
   If found and recent (<24h), ask user: Resume or start fresh?

2. **Create task directory**: Derive a kebab-case name from the task description
   - Example: "add rate limiting to login" → `tasks/add-rate-limiting-to-login/`
   - Create: `mkdir -p tasks/<task-name>/`

3. **Initialize state file**: `tasks/<task-name>/state.json`

## Output Files
- `problem.md` - Problem statement with classification (Phase 1)
- `plan.md` - Implementation plan (Phase 3)
- `plan-review.md` - Plan review feedback (Phase 3)
- `state.json` - Checkpoint state for resume capability
- `simplify-review.md` - Simplification suggestions (Phase 5)
- `code-review.md` - Bug/vulnerability findings (Phase 5)
- `verification.md` - Goal verification (Phase 6)
- `summary.md` - Final summary (Phase 7)

---

## CRITICAL: Context Management Rules

**Principle:** Minimize main agent context by delegating exploratory work to subagents.

| Phase | Main Agent Reads Files? | Why |
|-------|------------------------|-----|
| 1. Problem | NO | Problem-Analyst subagent explores |
| 2. Context Gathering | NO | Explore subagent returns file list only |
| 2.5. Context Loading | NO | Context-Loader returns trimmed content |
| 3. Planning | NO | Pass trimmed context to Planner via prompt |
| 3.5. Pre-Implementation | NO | Validation commands only |
| 4. Implementation | YES (only files being edited) | Need line numbers for Edit tool |
| 5. Code Quality | NO | Pass diff to reviewers, receive issues |
| 6. Verification | NO | Pass diff to Code-Goal, receive verdict |
| 7. Final Review | NO | Use git diff for summary |

---

## Phase 1: Problem Clarification

**Context Rule:** Do NOT read any files. Spawn Problem-Analyst subagent.

1. Spawn **Problem-Analyst subagent** (Task tool, model=sonnet) with user's task
2. Receive: problem statement + task classification
3. Write to `tasks/<task-name>/problem.md`
4. **Save checkpoint** to `state.json`
5. **STOP and present to user for approval**

### Task Classification (determines which phases to run):
- **trivial**: 1, 4, 5, 7 (skip context, planning, verification)
- **small**: 1, 2, 4, 5, 7 (skip context loading, planning)
- **medium**: All phases
- **large**: All phases + incremental implementation

---

## Conditional Phase Skipping

After Phase 1 approval, check classification and skip accordingly:

```
IF complexity == "trivial":
    SKIP phases 2, 2.5, 3, 3.5, 6
    GO TO phase 4

IF complexity == "small":
    SKIP phases 2.5, 3, 3.5, 6
    GO TO phase 2

IF complexity == "medium" OR "large":
    RUN all phases
```

User can override: "Use full workflow" or "Don't skip phases"

---

## Phase 2: Context Gathering (skip for trivial)

**Context Rule:** Do NOT read any files. Only spawn Explore subagent.

1. Spawn **Explore subagent** (Task tool, subagent_type="Explore") with problem description
2. Receive file list (NOT file contents)
3. **Save checkpoint**
4. Pass file list to Phase 2.5

---

## Phase 2.5: Context Loading (skip for trivial/small)

**Context Rule:** Do NOT read any files. Context-Loader reads and returns trimmed content.

1. Spawn **Context-Loader subagent** (Task tool, model=sonnet) with:
   - Problem statement
   - File list from Phase 2
2. Receive trimmed context (FULL/EXCERPT/SKIP per file)
3. **Save checkpoint**
4. Pass trimmed context to Phase 3

---

## Phase 3: Planning (skip for trivial/small)

**Context Rule:** Do NOT read any files. Pass trimmed context via prompt.

1. Spawn **Planner subagent** (Task tool, model=opus) with:
   - Problem statement
   - Trimmed context (in prompt, NOT re-read)
2. Write plan to `tasks/<task-name>/plan.md`
3. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with plan
4. Write review to `tasks/<task-name>/plan-review.md`
5. Iterate until "PLAN APPROVED"
6. **Save checkpoint**
7. **STOP and present plan to user for approval**

---

## Phase 3.5: Pre-Implementation Validation (skip for trivial/small)

**Context Rule:** Do NOT read files. Only run validation commands.

1. Run validation checks:
   ```bash
   # File existence
   for file in [files_from_plan]; do test -f "$file"; done

   # Baseline tests
   poetry run pytest [relevant_tests] --tb=short

   # Syntax check
   poetry run python -m py_compile [files_from_plan]
   ```
   **Note:** Git status NOT checked - user manages git.
2. If BLOCKED: Stop and report to user
3. If PASS: **Save checkpoint**, continue to Phase 4

---

## Phase 4: Implementation

**Context Rule:** This is the ONLY phase where main agent reads files - and ONLY files being edited.

### For Large Tasks (Incremental Implementation):
1. Group plan steps into batches of 2-3 related changes
2. For each batch:
   - Implement steps
   - Run relevant tests
   - Spawn Code-Simplifier for batch review
   - Fix issues
   - **Save checkpoint**
3. Continue to next batch

### For All Tasks:
1. Read plan from `tasks/<task-name>/plan.md`
2. Create TODO list
3. For each step:
   - Read ONLY the file being modified
   - Make the edit
   - Mark TODO complete
4. **Save checkpoint** after completion
5. Do NOT read files "for context"

---

## Phase 5: Code Quality

**Context Rule:** Do NOT read files. Pass diff to subagents, receive issue lists.

1. Generate diff: `git diff`
2. Spawn **Code-Simplifier subagent** (Task tool, model=sonnet) with diff
3. Write to `tasks/<task-name>/simplify-review.md`
4. Apply suggestions (read only files being modified)
5. Spawn **Code-Reviewer subagent** (Task tool, model=opus) with updated diff
6. Write to `tasks/<task-name>/code-review.md`
7. Fix issues (read only files being modified)
8. **Save checkpoint**

---

## Phase 6: Verification (skip for trivial)

**Context Rule:** Do NOT read files. Pass diff and problem to Code-Goal.

1. Spawn **Code-Goal subagent** (Task tool, model=sonnet) with:
   - Problem statement (from problem.md)
   - Diff (from git diff)
   - Test results
2. Write to `tasks/<task-name>/verification.md`
3. Run tests: `poetry run pytest`
4. **Save checkpoint**

---

## Phase 7: Final Review

**Context Rule:** Do NOT read files. Use git diff and previous phase outputs.

1. Generate summary from:
   - Problem statement (from problem.md)
   - Plan (from plan.md)
   - Verification (from verification.md)
   - Git diff
2. Write to `tasks/<task-name>/summary.md`
3. Mark state as "completed" in `state.json`
4. Present summary to user

---

## Checkpoint Management

### Save Checkpoint (after each phase):
```json
{
  "task_name": "<task-name>",
  "current_phase": <next_phase>,
  "completed_phases": [...],
  "complexity": "<trivial|small|medium|large>",
  "updated_at": "<timestamp>"
}
```

### Resume Workflow:
User says: "Continue workflow" or "Resume <task-name>"
1. Read `state.json`
2. Skip completed phases
3. Continue from `current_phase`

---

## Quick Reference

| Complexity | Phases | Est. Context |
|------------|--------|--------------|
| trivial | 1→4→5→7 | Minimal |
| small | 1→2→4→5→7 | Low |
| medium | 1→2→2.5→3→3.5→4→5→6→7 | Medium |
| large | All + incremental batches | Higher but managed |
