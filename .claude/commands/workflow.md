---
description: Run the full structured workflow for a task (problem clarification, planning, implementation, review, verification)
argument-hint: [task description]
allowed-tools: Task, Read, Glob, Grep, Edit, Write, Bash, TodoWrite, AskUserQuestion, mcp__codex-cli__review_plan, mcp__codex-cli__review_code
---

# Full Workflow

Execute the complete Claude Code workflow.

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

4. **Codex plan review opt-in**: If the user's task description does NOT explicitly mention "codex", "thorough", or "deep review":
   - Ask via **AskUserQuestion**: "Use Codex for plan review? (adds a second AI reviewer that scans the full codebase, costs more tokens)"
     - Option 1: "Yes" — Codex reviews the plan on first and final iteration
     - Option 2: "No" — Plan-Reviewer only (faster, cheaper)
   - Store decision in `state.json` as `use_codex_plan_review: true|false`
   - If the user explicitly mentions codex/thorough/deep review, default to `true` without asking
   - **Note:** Codex is ALWAYS used for code review (Phase 4) regardless of this setting

## Output Files
- `problem.md` - Problem statement (Phase 1)
- `plan.md` - Implementation plan, always the current version (Phase 2)
- `plan-review.md` - Latest plan review feedback (Phase 2)
- `codex-plan-review-N.md` - Raw Codex plan review output per review iteration (Phase 2)
- `codex-plan-analysis-N.md` - Analysis of Codex findings with VALID/INVALID/OVERENGINEERED classifications (Phase 2)
- `external-review.md` - External LLM review feedback (Phase 2)
- `external-analysis.md` - Analysis of external review findings with VALID/INVALID/OVERENGINEERED classifications (Phase 2)
- `chat-prompt.md` - Prompt for external chat (Phase 2)
- `chat-context.txt` - Code context for external chat (Phase 2)
- `chat-combined.md` - Combined prompt + instructions (Phase 2)
- `test-design-requirements.md` - Test cases from requirements (Phase 1.5)
- `test-design-plan.md` - Test cases from plan, including gap-exposing tests (Phase 2.7)
- `state.json` - Checkpoint state for resume capability
- `baseline-validation.md` - Pre-implementation validation (Phase 2.5)
- `code-review.md` - Bug/vulnerability findings (Phase 4)
- `codex-code-review-N.md` - Raw Codex code review output per review iteration (Phase 4)
- `codex-code-analysis-N.md` - Analysis of Codex code review findings with VALID/INVALID/OVERENGINEERED classifications (Phase 4)
- `final-validation.md` - Final tests/linter results (Phase 5)
- `verification.md` - Goal verification (Phase 5)
- `summary.md` - Final summary (Phase 6)

---

## CRITICAL: Context Management Rules

**Principle:** Minimize main agent context by delegating exploratory work to subagents. Each subagent searches for its own context — no centralized context gathering.

| Phase | Main Agent Reads Files? | Why |
|-------|------------------------|-----|
| 1. Problem | NO | Problem-Analyst subagent explores |
| 1.5. Test Design (requirements) | NO | Test-Designer subagent designs tests from requirements |
| 2. Iterative Planning | NO (reads task dir files only) | Planner/Reviewer subagents explore codebase; Codex reviews delegated to Codex-Analyzer subagent |
| 2.5. Pre-Implementation | NO | Validator subagent runs commands |
| 2.7. Test Design (plan) | NO | Test-Designer subagent extends test list from plan |
| 3. Implementation | YES (only files being edited) | Need line numbers for Edit tool |
| 4. Code Quality | NO (except files being fixed) | Codex analysis delegated to Codex-Analyzer subagent; Code-Reviewer receives only VALID findings |
| 5. Verification | NO | Validator + Code-Goal subagents |
| 6. Final Review | NO | Use git diff for summary |

---

## Phase 1: Problem Clarification

**Context Rule:** Do NOT read any files. Spawn Problem-Analyst subagent.

1. Spawn **Problem-Analyst subagent** (Task tool, model=sonnet) with user's task
2. Receive: problem statement
3. Write to `tasks/<task-name>/problem.md`
4. **Save checkpoint** to `state.json`
5. **STOP and present to user for approval**

---

## Phase 1.5: Requirements-Based Test Design

**Context Rule:** Do NOT read source files. Delegate to Test-Designer subagent.

After user approves the problem statement, design tests based purely on requirements:

1. Spawn **Test-Designer subagent** (Task tool, model=opus, requirements-based mode) with:
   - Problem statement from `problem.md`
   - Instruction to find and read the project's testing conventions (linked in CLAUDE.md)
2. Receive: test case list (focused + e2e) derived from requirements
3. Write to `tasks/<task-name>/test-design-requirements.md`
4. **If the agent reports no testing conventions file exists:** flag this to the user — the agent will have created one and CLAUDE.md needs a link added
5. **Save checkpoint**

**Note:** If the task is trivial and clearly needs no tests (e.g., config change, documentation), skip this phase.

---

## Phase 2: Iterative Planning

**Context Rule:** Do NOT read source code files. Read/write task directory files only (`plan.md`, `plan-review.md`, etc.). All codebase exploration via subagents. Codex analysis delegated to Codex-Analyzer subagent — main agent never reads Codex output files.

This phase runs a full planning cycle with iterative refinement:
1. Internal plan-review loop (Codex on first iteration only → Plan-Reviewer every iteration → final Codex verification)
2. External review (prepare-chat → user gets external feedback)
3. External review analysis + another plan-review loop (same pattern)
4. User manual review

**Codex gate:** Check `state.json` → `use_codex_plan_review`. If `false`, skip all Codex steps in this phase (2a/2b become no-ops, convergence depends on Plan-Reviewer only).

---

### Questions Protocol

Both Planner and Plan-Reviewer may surface **Questions for the User** in their output. After each subagent response:

1. Check if the output contains questions (look for "Questions for the User" section)
2. If questions exist and are NOT "None", present them to the user using **AskUserQuestion**
3. Pass user answers to the next subagent invocation (include in the prompt as "User Answers")
4. The Planner will incorporate answers into the plan's Design Decisions section

---

### Step 1: Initial Plan Creation

1. Spawn **Planner subagent** (Task tool, model=opus, creation mode) with:
   - Problem statement
   - Instruction to explore the codebase for relevant context
2. Write plan to `tasks/<task-name>/plan.md`
3. **Check for questions** → ask user if any, then spawn Planner (revision mode) with answers to update plan
4. **Save checkpoint**

### Step 2: Internal Plan-Review Loop

Track **REVIEW_ITERATION = 1**. Track **CODEX_LAST_VERDICT = null**.

#### 2a. Codex Plan Review (first iteration only)

**Skip this step if `use_codex_plan_review` is false, or if REVIEW_ITERATION > 1.**

Run Codex in read-only sandbox to review the plan against the actual codebase.

Use the `review_plan` MCP tool with:
- problem_statement: content of problem.md
- plan_content: content of plan.md
- output_file: "tasks/<task-name>/codex-plan-review-REVIEW_ITERATION.md"
- working_directory: project root path

#### 2b. Analyze Codex Findings (via subagent)

**Skip if step 2a was skipped.**

Spawn **Codex-Analyzer subagent** (Task tool, model=sonnet) with:
- Codex review file path: `tasks/<task-name>/codex-plan-review-REVIEW_ITERATION.md`
- Analysis output path: `tasks/<task-name>/codex-plan-analysis-REVIEW_ITERATION.md`
- Review type: "plan"

Receive back: **CODEX_LAST_VERDICT** and **VALID findings only** (not the full analysis). Store the verdict.

**Main agent does NOT read the Codex output or analysis files.**

#### 2c. Plan-Reviewer Review

1. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with:
   - Current plan
   - If Codex ran this iteration: VALID findings only from step 2b (the summary returned by Codex-Analyzer)
   - If Codex did not run: no Codex findings
2. Write review to `tasks/<task-name>/plan-review.md`
3. **Check for reviewer questions** → ask user if any

#### 2d. Convergence Check

**If `use_codex_plan_review` is false:**
- If Plan-Reviewer returned **PLAN APPROVED** → proceed to Step 3
- If **NEEDS REVISION** → go to revision step below

**If `use_codex_plan_review` is true:**
- If Plan-Reviewer returned **PLAN APPROVED**:
  - If REVIEW_ITERATION == 1 and CODEX_LAST_VERDICT was also **PLAN APPROVED** → proceed to Step 3
  - If REVIEW_ITERATION > 1 (Codex hasn't run since iteration 1) → run **final Codex verification** (step 2e)
- If Plan-Reviewer returned **NEEDS REVISION** → go to revision step below

**Revision step:**
   a. Spawn **Planner subagent** (revision mode) with:
      - Current plan
      - VALID Codex findings only (if Codex ran this iteration)
      - Plan-Reviewer findings
      - Any user answers to questions
      - Problem statement
   b. Planner verifies each finding, incorporates valid ones, rejects others with reasoning in Review Addendum
   c. Update `tasks/<task-name>/plan.md`
   d. **Check for planner questions** → ask user if any, re-run planner with answers
   e. Increment REVIEW_ITERATION
   f. Go back to step 2a (which will skip Codex since REVIEW_ITERATION > 1)

#### 2e. Final Codex Verification

Run when Plan-Reviewer has approved but Codex hasn't reviewed the latest plan version.

1. Run `review_plan` MCP tool (same params as 2a, with current REVIEW_ITERATION)
2. Spawn **Codex-Analyzer subagent** to triage findings (same as 2b)
3. If Codex verdict is **PLAN APPROVED** → proceed to Step 3
4. If Codex verdict is **NEEDS REVISION**:
   - Run ONE more Plan-Reviewer round with the VALID Codex findings
   - If Plan-Reviewer agrees with Codex → Planner revision, then re-run final Codex verification
   - If Plan-Reviewer disagrees (still approves) → proceed to Step 3 (Plan-Reviewer overrides on non-critical)
   - **Cap:** Max 2 final-verification rounds to prevent loops

6. **Save checkpoint**

### Step 3: External Review

1. Spawn **Chat-Preparer subagent** (Task tool, model=sonnet) with:
   - Mode: "plan-review"
   - Task directory: `tasks/<task-name>/`
   - Include agent instructions from `~/.claude/agents/chat-preparer.md`
2. Subagent creates:
   - `chat-context.txt` - Code context via repomix
   - `chat-prompt.md` - Plan review prompt
   - `chat-combined.md` - Combined instructions
   - `external-review.md` - Placeholder for response
3. **Save checkpoint**
4. **STOP and inform user**:
   ```
   Internal plan-review loop complete. Plan approved by reviewer.

   Now prepare for external review:
   1. Copy `chat-prompt.md` to Claude.ai/ChatGPT
   2. Attach `chat-context.txt`
   3. Paste the response into `external-review.md`
   4. Say "continue workflow" to resume
   ```

### Step 4: External Review Analysis

When user says **"continue workflow"** after external review:

1. Read `tasks/<task-name>/external-review.md`
2. **Check if external review contains an "Alternative Approach" section:**
   - If yes, present the alternative to the user using **AskUserQuestion**:
     - Option 1: "Keep current plan (incorporate review findings only)"
     - Option 2: "Switch to the alternative approach"
     - Option 3: "Merge ideas from both approaches"
   - If user chooses to switch: Spawn Planner (creation mode) with the alternative approach as guidance + problem statement, then go to **Step 2** (internal plan-review loop)
   - If user chooses to merge: include merge instructions in the planner prompt below
3. Spawn **Planner subagent** (external review analysis mode) with:
   - Current plan
   - External review content (Part 1 findings)
   - Problem statement
   - User's decision about the alternative (if applicable)
4. Planner verifies each finding against codebase, classifies as VALID/INVALID/OVERENGINEERED, incorporates VALID ones
5. Write analysis to `tasks/<task-name>/external-analysis.md` (extract from planner output)
6. Update `tasks/<task-name>/plan.md` with revised plan
7. **Check for planner questions** → ask user if any, re-run planner with answers
8. **Save checkpoint**

### Step 5: Post-External Plan-Review Loop

Track **REVIEW_ITERATION** (continue from Step 2's counter). Same Codex-on-first-and-final pattern as Step 2. Track **POST_EXT_ITERATION = 1**.

**Codex gate:** Same as Step 2 — check `use_codex_plan_review` in state.json.

#### 5a. Codex Plan Review (first post-external iteration only)

**Skip if `use_codex_plan_review` is false, or if POST_EXT_ITERATION > 1.**

Use the `review_plan` MCP tool (same params as Step 2a, with current REVIEW_ITERATION).

#### 5b. Analyze Codex Findings (via subagent)

**Skip if 5a was skipped.**

Spawn **Codex-Analyzer subagent** (model=sonnet). Receive VALID findings only. Store Codex verdict.

**Main agent does NOT read Codex output or analysis files.**

#### 5c. Plan-Reviewer Review

1. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with:
   - Updated plan
   - If Codex ran this iteration: VALID findings only from step 5b
2. Write review to `tasks/<task-name>/plan-review.md` (overwrite)
3. **Check for reviewer questions** → ask user if any

#### 5d. Convergence Check

Same logic as Step 2d:
- If `use_codex_plan_review` is false: Plan-Reviewer approval alone is sufficient
- If true: When Plan-Reviewer approves and Codex hasn't run recently → final Codex verification (same as step 2e)
- If NEEDS REVISION: Planner revision with VALID findings only, increment POST_EXT_ITERATION, go to 5a

6. **Save checkpoint**

### Step 6: User Manual Review

1. Present the final plan to the user with a summary:
   ```
   Planning iteration complete:
   - Codex plan review: [enabled/disabled]
   - Internal review loop: N rounds (Plan-Reviewer each round, Codex on first + final)
   - External review: X findings (Y valid, Z rejected)
   - Post-external review loop: M rounds (same pattern)

   Please review the final plan in `tasks/<task-name>/plan.md`.
   Codex reviews (if enabled): codex-plan-review-*.md / codex-plan-analysis-*.md
   ```
2. **STOP and wait for user approval**
3. If user approves → proceed to Phase 2.5
4. If user requests changes → Spawn Planner (revision mode) with user feedback, then go back to **Step 2**

---

## Phase 2.5: Pre-Implementation Validation

**Context Rule:** Do NOT run validation commands directly. Delegate to Validator subagent.

1. Spawn **Validator subagent** (Task tool, model=sonnet) with:
   - Validation type: "baseline"
   - Project info (path, CLAUDE.md location)
   - Files from plan
2. Receive validation verdict (NOT raw command output)
3. Write to `tasks/<task-name>/baseline-validation.md`
4. If BLOCKED: Stop and report to user
5. If PASS: **Save checkpoint**, continue to Phase 2.7

---

## Phase 2.7: Plan-Based Test Design

**Context Rule:** Do NOT read source files. Delegate to Test-Designer subagent.

After pre-implementation validation passes, extend the test list with plan-specific tests:

1. Spawn **Test-Designer subagent** (Task tool, model=opus, plan-based mode) with:
   - Problem statement from `problem.md`
   - Implementation plan from `plan.md`
   - Existing requirements-based test list from `test-design-requirements.md`
2. The agent will:
   - Add focused tests for hard/algorithmic parts of the implementation
   - Add e2e tests covering the full implementation flow
   - **Design gap-exposing tests** — tests that would catch things the plan doesn't address but the requirements imply
   - Check plan-based tests don't duplicate requirements-based tests
3. Write to `tasks/<task-name>/test-design-plan.md`
4. **Save checkpoint**
5. Continue to Phase 3

**Note:** Skip if Phase 1.5 was skipped (trivial task with no tests needed).

---

## Phase 3: Implementation

**Context Rule:** This is the ONLY phase where main agent reads files - and ONLY files being edited.

### For Large Tasks (Incremental Implementation):
1. Group plan steps into batches of 2-3 related changes
2. For each batch:
   - Implement steps
   - Spawn **Validator subagent** (type: "batch") with changed files
   - Receive pass/fail verdict
   - Fix issues
   - **Save checkpoint**
3. Continue to next batch

### For All Tasks:
1. Read plan from `tasks/<task-name>/plan.md`
2. Create TODO list (include test writing as final steps, using `test-design-requirements.md` and `test-design-plan.md`)
3. For each step:
   - Read ONLY the file being modified
   - Make the edit
   - Mark TODO complete
4. **Write tests** using the Test-Writer subagent with both test design files as input
5. **Save checkpoint** after completion

---

## Phase 4: Code Quality

**Context Rule:** Do NOT read source files except those being fixed. Codex analysis delegated to Codex-Analyzer subagent — main agent never reads Codex output. Only VALID findings are passed to Code-Reviewer.

**Codex is ALWAYS used for code review** regardless of the `use_codex_plan_review` setting.

Track **CODE_REVIEW_ITERATION = 1**. Repeat until both Codex and Code-Reviewer agree no Critical/High/Medium issues remain:

### 4a. Generate Diff

```bash
git diff > tasks/<task-name>/diff.patch
```

Save the diff for both reviewers to reference.

### 4b. Codex Code Review (mandatory, every iteration)

Run Codex code review against the uncommitted changes.

Use the `review_code` MCP tool with:
- output_file: "tasks/<task-name>/codex-code-review-CODE_REVIEW_ITERATION.md"
- task_context: "This code implements the plan described in tasks/<task-name>/plan.md for the problem in tasks/<task-name>/problem.md. Read both files for context."
- uncommitted: true
- working_directory: project root path

### 4c. Analyze Codex Code Review Findings (via subagent)

Spawn **Codex-Analyzer subagent** (Task tool, model=sonnet) with:
- Codex review file path: `tasks/<task-name>/codex-code-review-CODE_REVIEW_ITERATION.md`
- Analysis output path: `tasks/<task-name>/codex-code-analysis-CODE_REVIEW_ITERATION.md`
- Review type: "code"

Receive back: **Codex verdict** and **VALID findings only**.

**Main agent does NOT read the Codex output or analysis files.**

### 4d. Code-Reviewer Review

1. Spawn **Code-Reviewer subagent** (Task tool, model=opus) with:
   - The diff
   - VALID Codex findings only (the summary returned by Codex-Analyzer, NOT the full analysis file)
2. Write review to `tasks/<task-name>/code-review.md`

### 4e. Convergence Check

- If both Codex verdict (from 4c) and Code-Reviewer (step 4d) returned **NO ISSUES FOUND** or **APPROVED** (only Low-severity remain) → done
- If either returned **NEEDS FIXES** (Critical, High, or Medium issues):
   a. Collect all VALID findings from both reviews
   b. Fix issues (read only files being modified)
   c. Increment CODE_REVIEW_ITERATION
   d. Go back to step 4a

6. **Save checkpoint**

---

## Phase 5: Verification

**Context Rule:** Do NOT read files or run tests directly. Delegate to subagents.

1. Spawn **Validator subagent** (Task tool, model=sonnet) with:
   - Validation type: "final"
   - Project info
   - All changed files
2. Write to `tasks/<task-name>/final-validation.md`
3. Spawn **Code-Goal subagent** (Task tool, model=sonnet) with:
   - Problem statement
   - Diff
   - Validation results summary
4. Write to `tasks/<task-name>/verification.md`
5. **Save checkpoint**

---

## Phase 6: Final Review

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
  "updated_at": "<timestamp>"
}
```

### Resume Workflow:
User says: "Continue workflow" or "Resume <task-name>"
1. Read `state.json`
2. Skip completed phases
3. Continue from `current_phase`
