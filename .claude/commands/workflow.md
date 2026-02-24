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
   - **If resuming:**
     - Read state.json
     - **If state.json contains `worktree_path` (new-style workflow):**
       - Verify the worktree still exists: `test -d <worktree_path>`
       - If it exists: restore `WORKTREE_PATH`, `TARGET_REPO_PATH`, `TASK_DIR`, `PROJECT_ROOT`, `ORIGINAL_BRANCH_SHA` from state.json
       - If it does not exist: re-create the worktree (same branch name — it may still exist as a branch)
     - **If state.json does NOT contain `worktree_path` (legacy pre-worktree workflow):**
       - Resume using legacy behavior: skip completed phases, continue from `current_phase` without worktree context
       - All worktree-specific phases (0, 7) are skipped for legacy workflows
       - All path variables default to project root (backward compatible)
       - Inform user: "This workflow was started before worktree isolation. Continuing in legacy mode (changes in main tree)."
   - **If starting fresh and a worktree exists from a previous run with the same task name:**
     - Load `target_repo_path` from the existing state.json (if available)
     - Check if the old branch has unmerged commits:
       ```bash
       UNMERGED=$(git -C <target_repo_path> log workflow/<task-name> --not --remotes --oneline 2>/dev/null | head -5)
       ```
     - **If unmerged commits exist:**
       - Ask user via **AskUserQuestion**: "Branch workflow/<task-name> has unmerged commits:\n[show first 5]\nDelete anyway?"
         - If yes: proceed with force-delete below
         - If no: abort "start fresh", suggest resuming instead
     - Remove the old worktree: `git -C <target_repo_path> worktree remove .worktrees/<task-name> --force`
     - Delete the old branch:
       - First try safe delete: `git -C <target_repo_path> branch -d workflow/<task-name>`
       - If that fails (unmerged) and user confirmed: `git -C <target_repo_path> branch -D workflow/<task-name>`

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

## Path Variables

These variables are set in Phase 0 and used throughout the workflow:

- `PROJECT_ROOT` = absolute path where `/workflow` was invoked
- `TARGET_REPO_PATH` = absolute path to the specific git repo being targeted
- `WORKTREE_PATH` = absolute path to the created worktree (`<TARGET_REPO_PATH>/.worktrees/<task-name>`)
- `TASK_DIR` = `<PROJECT_ROOT>/tasks/<task-name>` (absolute, in the main tree)
- `ORIGINAL_BRANCH` = branch name at workflow start
- `ORIGINAL_BRANCH_SHA` = SHA of that branch at workflow start

**Rule:** All task artifact references (problem.md, plan.md, etc.) use absolute `TASK_DIR` paths. All source code operations use `WORKTREE_PATH`. Never use relative `tasks/<task-name>/` paths.

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
| 0. Worktree Setup | NO | Git commands only |
| 1. Problem | NO | Problem-Analyst subagent explores |
| 1.5. Test Design (requirements) | NO | Test-Designer subagent designs tests from requirements |
| 2. Iterative Planning | NO (reads task dir files only) | Planner/Reviewer subagents explore codebase; Codex reviews delegated to Codex-Analyzer subagent |
| 2.5. Pre-Implementation | NO | Validator subagent runs commands |
| 2.7. Test Design (plan) | NO | Test-Designer subagent extends test list from plan |
| 3. Implementation | YES (only files being edited) | Need line numbers for Edit tool |
| 4. Code Quality | NO (except files being fixed) | Codex analysis delegated to Codex-Analyzer subagent; Code-Reviewer receives only VALID findings |
| 5. Verification | NO | Validator + Code-Goal subagents |
| 6. Final Review | NO | Use git diff for summary |
| 7. Merge & Conflict | NO (except conflict files) | Git commands, user-driven |

---

## Phase 0: Worktree Setup

**Context Rule:** This phase determines the target repo and creates a worktree. No codebase exploration.

1. **Determine project root and target repo:**
   - `PROJECT_ROOT` = current working directory (absolute path)
   - Run `git rev-parse --show-toplevel` to get the current git root
   - Check if this is a multi-repo workspace by looking for sub-directories with their own `.git`:
     ```bash
     find <PROJECT_ROOT> -maxdepth 2 -name ".git" ! -path "<PROJECT_ROOT>/.git"
     ```
     (No `-type d` filter — detects both independent repos and git submodules.)
   - **If sub-repos found (multi-repo workspace):**
     - Present the list of sub-repos to the user via **AskUserQuestion**:
       "This is a multi-repo workspace. Which repository should this workflow target?"
     - Options: list each sub-repo parent directory name
     - Store the selected sub-repo path as `TARGET_REPO_PATH` (absolute)
   - **If no sub-repos found (single-repo):**
     - `TARGET_REPO_PATH` = project root (absolute)

2. **Sanitize task name for branch validity:**
   - Verify the kebab-case task name is valid as a git branch component
   - No spaces, no `..`, no `~`, no `^`, no `:`, no `\`
   - No leading or trailing dots or hyphens
   - If invalid characters detected, strip them and warn user

3. **Record baseline state:**
   ```bash
   ORIGINAL_BRANCH=$(git -C <TARGET_REPO_PATH> rev-parse --abbrev-ref HEAD)
   ORIGINAL_BRANCH_SHA=$(git -C <TARGET_REPO_PATH> rev-parse HEAD)
   ```

4. **Create worktree:**
   ```bash
   git -C <TARGET_REPO_PATH> worktree add <TARGET_REPO_PATH>/.worktrees/<task-name> -b workflow/<task-name>
   ```
   - `WORKTREE_PATH` = `<TARGET_REPO_PATH>/.worktrees/<task-name>` (absolute)
   - If the branch `workflow/<task-name>` already exists (resume scenario):
     ```bash
     git -C <TARGET_REPO_PATH> worktree add <TARGET_REPO_PATH>/.worktrees/<task-name> workflow/<task-name>
     ```

5. **Ensure .worktrees/ is excluded via .git/info/exclude:**
   ```bash
   EXCLUDE_FILE=$(git -C <TARGET_REPO_PATH> rev-parse --git-path info/exclude)
   grep -q "^\.worktrees/" "$EXCLUDE_FILE" 2>/dev/null || echo ".worktrees/" >> "$EXCLUDE_FILE"
   ```

6. **Define path variables:**
   - `TASK_DIR` = `<PROJECT_ROOT>/tasks/<task-name>` (absolute path, in the main tree)

7. **Update state.json** (MERGE into existing state, do NOT overwrite):
   Read the current state.json first, then add/update only these fields:
   ```json
   {
     "current_phase": 0,
     "completed_phases": [0],
     "project_root": "<PROJECT_ROOT>",
     "target_repo_path": "<TARGET_REPO_PATH>",
     "worktree_path": "<WORKTREE_PATH>",
     "worktree_branch": "workflow/<task-name>",
     "original_branch": "<ORIGINAL_BRANCH>",
     "original_branch_sha": "<ORIGINAL_BRANCH_SHA>",
     "updated_at": "<timestamp>"
   }
   ```
   **Important:** Preserve existing fields like `task_name`, `use_codex_plan_review`.

8. **Inform user:**
   ```
   Worktree created:
     Branch: workflow/<task-name>
     Path: <WORKTREE_PATH>
     Task artifacts: <TASK_DIR>
     Original branch: <ORIGINAL_BRANCH> at <ORIGINAL_BRANCH_SHA>

   IDE navigation:
     Open worktree:  cd <WORKTREE_PATH>
     Return to main:  cd <TARGET_REPO_PATH>
   ```

---

## Phase 1: Problem Clarification

**Context Rule:** Do NOT read any files. Spawn Problem-Analyst subagent.

1. Spawn **Problem-Analyst subagent** (Task tool, model=sonnet) with:
   - User's task
   - `target_repo_path: TARGET_REPO_PATH` (for multi-repo awareness)
2. Receive: problem statement
3. Write to `<TASK_DIR>/problem.md`
4. **Save checkpoint** to `state.json`
5. **STOP and present to user for approval**

---

## Phase 1.5: Requirements-Based Test Design

**Context Rule:** Do NOT read source files. Delegate to Test-Designer subagent.

After user approves the problem statement, design tests based purely on requirements:

1. Spawn **Test-Designer subagent** (Task tool, model=opus, requirements-based mode) with:
   - Problem statement from `<TASK_DIR>/problem.md`
   - Instruction to find and read the project's testing conventions (linked in CLAUDE.md)
   - `target_repo_path: TARGET_REPO_PATH` (scope test file searches to correct repo)
2. Receive: test case list (focused + e2e) derived from requirements
3. Write to `<TASK_DIR>/test-design-requirements.md`
4. **If the agent reports no testing conventions file exists:** flag this to the user — the agent will have created one and CLAUDE.md needs a link added
5. **Save checkpoint**

**Note:** If the task is trivial and clearly needs no tests (e.g., config change, documentation), skip this phase.

---

## Phase 2: Iterative Planning

**Context Rule:** Do NOT read source code files. Read/write task directory files only (`<TASK_DIR>/plan.md`, `<TASK_DIR>/plan-review.md`, etc.). All codebase exploration via subagents. Codex analysis delegated to Codex-Analyzer subagent — main agent never reads Codex output files.

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
   - `target_repo_path: TARGET_REPO_PATH` (scope exploration to correct repo)
2. Write plan to `<TASK_DIR>/plan.md`
3. **Check for questions** → ask user if any, then spawn Planner (revision mode) with answers to update plan
4. **Save checkpoint**

### Step 2: Internal Plan-Review Loop

Track **REVIEW_ITERATION = 1**. Track **CODEX_LAST_VERDICT = null**.

#### 2a. Codex Plan Review (first iteration only)

**Skip this step if `use_codex_plan_review` is false, or if REVIEW_ITERATION > 1.**

Run Codex in read-only sandbox to review the plan against the actual codebase.

Use the `review_plan` MCP tool with:
- problem_statement: content of `<TASK_DIR>/problem.md`
- plan_content: content of `<TASK_DIR>/plan.md`
- output_file: `<TASK_DIR>/codex-plan-review-REVIEW_ITERATION.md` (absolute path)
- working_directory: WORKTREE_PATH

#### 2b. Analyze Codex Findings (via subagent)

**Skip if step 2a was skipped.**

Spawn **Codex-Analyzer subagent** (Task tool, model=sonnet) with:
- Codex review file path: `<TASK_DIR>/codex-plan-review-REVIEW_ITERATION.md`
- Analysis output path: `<TASK_DIR>/codex-plan-analysis-REVIEW_ITERATION.md`
- Review type: "plan"
- `working_directory: WORKTREE_PATH` (for verifying file paths)

Receive back: **CODEX_LAST_VERDICT** and **VALID findings only** (not the full analysis). Store the verdict.

**Main agent does NOT read the Codex output or analysis files.**

#### 2c. Plan-Reviewer Review

1. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with:
   - Current plan
   - If Codex ran this iteration: VALID findings only from step 2b (the summary returned by Codex-Analyzer)
   - If Codex did not run: no Codex findings
   - `target_repo_path: TARGET_REPO_PATH` (scope codebase exploration to correct repo)
2. Write review to `<TASK_DIR>/plan-review.md`
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
      - `target_repo_path: TARGET_REPO_PATH`
   b. Planner verifies each finding, incorporates valid ones, rejects others with reasoning in Review Addendum
   c. Update `<TASK_DIR>/plan.md`
   d. **Check for planner questions** → ask user if any, re-run planner with answers
   e. Increment REVIEW_ITERATION
   f. Go back to step 2a (which will skip Codex since REVIEW_ITERATION > 1)

#### 2e. Final Codex Verification

Run when Plan-Reviewer has approved but Codex hasn't reviewed the latest plan version.

1. Run `review_plan` MCP tool with:
   - Same params as 2a, with current REVIEW_ITERATION
   - output_file: `<TASK_DIR>/codex-plan-review-REVIEW_ITERATION.md` (absolute path)
   - working_directory: WORKTREE_PATH
2. Spawn **Codex-Analyzer subagent** to triage findings (same as 2b, with `working_directory: WORKTREE_PATH`)
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
   - Task directory: `<TASK_DIR>/`
   - Include agent instructions from `~/.claude/agents/chat-preparer.md`
   - `working_directory: WORKTREE_PATH` (so repomix picks up worktree files)
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

1. Read `<TASK_DIR>/external-review.md`
2. **Check if external review contains an "Alternative Approach" section:**
   - If yes, present the alternative to the user using **AskUserQuestion**:
     - Option 1: "Keep current plan (incorporate review findings only)"
     - Option 2: "Switch to the alternative approach"
     - Option 3: "Merge ideas from both approaches"
   - If user chooses to switch: Spawn Planner (creation mode) with the alternative approach as guidance + problem statement + `target_repo_path: TARGET_REPO_PATH`, then go to **Step 2** (internal plan-review loop)
   - If user chooses to merge: include merge instructions in the planner prompt below
3. Spawn **Planner subagent** (external review analysis mode) with:
   - Current plan
   - External review content (Part 1 findings)
   - Problem statement
   - User's decision about the alternative (if applicable)
   - `target_repo_path: TARGET_REPO_PATH`
4. Planner verifies each finding against codebase, classifies as VALID/INVALID/OVERENGINEERED, incorporates VALID ones
5. Write analysis to `<TASK_DIR>/external-analysis.md` (extract from planner output)
6. Update `<TASK_DIR>/plan.md` with revised plan
7. **Check for planner questions** → ask user if any, re-run planner with answers
8. **Save checkpoint**

### Step 5: Post-External Plan-Review Loop

Track **REVIEW_ITERATION** (continue from Step 2's counter). Same Codex-on-first-and-final pattern as Step 2. Track **POST_EXT_ITERATION = 1**.

**Codex gate:** Same as Step 2 — check `use_codex_plan_review` in state.json.

#### 5a. Codex Plan Review (first post-external iteration only)

**Skip if `use_codex_plan_review` is false, or if POST_EXT_ITERATION > 1.**

Use the `review_plan` MCP tool with:
- Same params as Step 2a, with current REVIEW_ITERATION
- output_file: `<TASK_DIR>/codex-plan-review-REVIEW_ITERATION.md` (absolute path)
- working_directory: WORKTREE_PATH

#### 5b. Analyze Codex Findings (via subagent)

**Skip if 5a was skipped.**

Spawn **Codex-Analyzer subagent** (model=sonnet) with `working_directory: WORKTREE_PATH`. Receive VALID findings only. Store Codex verdict.

**Main agent does NOT read Codex output or analysis files.**

#### 5c. Plan-Reviewer Review

1. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with:
   - Updated plan
   - If Codex ran this iteration: VALID findings only from step 5b
   - `target_repo_path: TARGET_REPO_PATH`
2. Write review to `<TASK_DIR>/plan-review.md` (overwrite)
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

   Please review the final plan in `<TASK_DIR>/plan.md`.
   Codex reviews (if enabled): codex-plan-review-*.md / codex-plan-analysis-*.md
   ```
2. **STOP and wait for user approval**
3. If user approves → proceed to Phase 2.5
4. If user requests changes → Spawn Planner (revision mode) with user feedback + `target_repo_path: TARGET_REPO_PATH`, then go back to **Step 2**

---

## Phase 2.5: Pre-Implementation Validation

**Context Rule:** Do NOT run validation commands directly. Delegate to Validator subagent.

1. Spawn **Validator subagent** (Task tool, model=sonnet) with:
   - Validation type: "baseline"
   - Project info (path, CLAUDE.md location)
   - Working directory: WORKTREE_PATH
   - Files from plan
2. Receive validation verdict (NOT raw command output)
3. Write to `<TASK_DIR>/baseline-validation.md`
4. If BLOCKED: Stop and report to user
5. If PASS: **Save checkpoint**, continue to Phase 2.7

---

## Phase 2.7: Plan-Based Test Design

**Context Rule:** Do NOT read source files. Delegate to Test-Designer subagent.

After pre-implementation validation passes, extend the test list with plan-specific tests:

1. Spawn **Test-Designer subagent** (Task tool, model=opus, plan-based mode) with:
   - Problem statement from `<TASK_DIR>/problem.md`
   - Implementation plan from `<TASK_DIR>/plan.md`
   - Existing requirements-based test list from `<TASK_DIR>/test-design-requirements.md`
   - `target_repo_path: TARGET_REPO_PATH` (scope test searches to correct repo)
2. The agent will:
   - Add focused tests for hard/algorithmic parts of the implementation
   - Add e2e tests covering the full implementation flow
   - **Design gap-exposing tests** — tests that would catch things the plan doesn't address but the requirements imply
   - Check plan-based tests don't duplicate requirements-based tests
3. Write to `<TASK_DIR>/test-design-plan.md`
4. **Save checkpoint**
5. Continue to Phase 3

**Note:** Skip if Phase 1.5 was skipped (trivial task with no tests needed).

---

## Phase 3: Implementation

**Context Rule:** This is the ONLY phase where main agent reads files - and ONLY files being edited.

**Worktree Rule:** All file reads and edits in this phase MUST use absolute paths under `WORKTREE_PATH`. If the plan references `src/app/service.py`, the actual path to edit is `<WORKTREE_PATH>/src/app/service.py`. Task artifacts (plan.md, test designs) are at `TASK_DIR` (in the main tree).

### For Large Tasks (Incremental Implementation):
1. Group plan steps into batches of 2-3 related changes
2. For each batch:
   - Implement steps (all file paths under `WORKTREE_PATH`)
   - Spawn **Validator subagent** (type: "batch") with changed files and `working_directory: WORKTREE_PATH`
   - Receive pass/fail verdict
   - Fix issues
   - **Save checkpoint**
3. Continue to next batch

### For All Tasks:
1. Read plan from `<TASK_DIR>/plan.md`
2. Create TODO list (include test writing as final steps, using `<TASK_DIR>/test-design-requirements.md` and `<TASK_DIR>/test-design-plan.md`)
3. For each step:
   - Read ONLY the file being modified (using `<WORKTREE_PATH>/...` absolute path)
   - Make the edit
   - Mark TODO complete
4. **Write tests** using the Test-Writer subagent with both test design files as input and `working_directory: WORKTREE_PATH`
5. **Save checkpoint** after completion

**After implementation, inform user:**
```
Implementation complete. Code changes are in the worktree.

To inspect in IDE:  cd <WORKTREE_PATH>
To return to main:  cd <TARGET_REPO_PATH>
```

---

## Phase 4: Code Quality

**Context Rule:** Do NOT read source files except those being fixed. Codex analysis delegated to Codex-Analyzer subagent — main agent never reads Codex output. Only VALID findings are passed to Code-Reviewer.

**Codex is ALWAYS used for code review** regardless of the `use_codex_plan_review` setting.

Track **CODE_REVIEW_ITERATION = 1**. Repeat until both Codex and Code-Reviewer agree no Critical/High/Medium issues remain:

### 4a. Generate Diff

```bash
git -C <WORKTREE_PATH> diff > <TASK_DIR>/diff.patch
```

Save the diff for both reviewers to reference.

### 4b. Codex Code Review (mandatory, every iteration)

Run Codex code review against the uncommitted changes.

Use the `review_code` MCP tool with:
- output_file: `<TASK_DIR>/codex-code-review-CODE_REVIEW_ITERATION.md` (absolute path)
- task_context: "This code implements: [INLINE SUMMARY OF PLAN]. Problem: [INLINE SUMMARY OF PROBLEM]." (Pass inline content — Codex sandbox cannot access TASK_DIR files.)
- uncommitted: true
- working_directory: WORKTREE_PATH

### 4c. Analyze Codex Code Review Findings (via subagent)

Spawn **Codex-Analyzer subagent** (Task tool, model=sonnet) with:
- Codex review file path: `<TASK_DIR>/codex-code-review-CODE_REVIEW_ITERATION.md`
- Analysis output path: `<TASK_DIR>/codex-code-analysis-CODE_REVIEW_ITERATION.md`
- Review type: "code"
- `working_directory: WORKTREE_PATH` (for verifying file paths)

Receive back: **Codex verdict** and **VALID findings only**.

**Main agent does NOT read the Codex output or analysis files.**

### 4d. Code-Reviewer Review

1. Spawn **Code-Reviewer subagent** (Task tool, model=opus) with:
   - The diff
   - VALID Codex findings only (the summary returned by Codex-Analyzer, NOT the full analysis file)
   - `working_directory: WORKTREE_PATH` (for Read/Glob/Grep on source files)
2. Write review to `<TASK_DIR>/code-review.md`

### 4e. Convergence Check

- If both Codex verdict (from 4c) and Code-Reviewer (step 4d) returned **NO ISSUES FOUND** or **APPROVED** (only Low-severity remain) → done
- If either returned **NEEDS FIXES** (Critical, High, or Medium issues):
   a. Collect all VALID findings from both reviews
   b. Fix issues (read only files being modified, using `<WORKTREE_PATH>/...` paths)
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
   - `working_directory: WORKTREE_PATH`
2. Write to `<TASK_DIR>/final-validation.md`
3. Spawn **Code-Goal subagent** (Task tool, model=sonnet) with:
   - Problem statement
   - Diff (from `git -C <WORKTREE_PATH> diff`)
   - Validation results summary
   - `working_directory: WORKTREE_PATH` (so it explores the worktree to verify what was built)
4. Write to `<TASK_DIR>/verification.md`
5. **Save checkpoint**

---

## Phase 6: Final Review

**Context Rule:** Do NOT read files. Use git diff and previous phase outputs.

1. Generate summary from:
   - Problem statement (from `<TASK_DIR>/problem.md`)
   - Plan (from `<TASK_DIR>/plan.md`)
   - Verification (from `<TASK_DIR>/verification.md`)
   - Git diff: `git -C <WORKTREE_PATH> diff`
2. Write to `<TASK_DIR>/summary.md`
3. **Save checkpoint:** Set `current_phase: 7` (NOT "completed" — Phase 7 still needs to run)
4. Present summary to user:
   ```
   Workflow complete. Code changes are in the worktree:
     Path: <WORKTREE_PATH>
     Branch: workflow/<task-name>

   To inspect in IDE:  cd <WORKTREE_PATH>
   To return to main:  cd <TARGET_REPO_PATH>

   To proceed with merging, say "merge workflow" or continue to Phase 7.
   ```

---

## Phase 7: Merge & Conflict Resolution

**Context Rule:** Do NOT read source files except conflict files. Use git commands for merge operations.

**Trigger:** User says "merge workflow" or "continue" after Phase 6.

### Step 0: Pre-Transfer Checks

**Check worktree for uncommitted changes:**
```bash
git -C <WORKTREE_PATH> status --porcelain
```

**If uncommitted changes exist in worktree:**
Present to user via **AskUserQuestion**:
- Option 1: "Commit changes to worktree branch" — commit all changes, then continue
- Option 2: "Show changes" — run `git -C <WORKTREE_PATH> diff --stat` and ask again
- Option 3: "Discard changes" — `git -C <WORKTREE_PATH> checkout .` and continue
- Option 4: "Leave uncommitted and continue" — warn that uncommitted changes will NOT be included in merge/diff/cherry-pick

**Check main tree for uncommitted changes:**
```bash
git -C <TARGET_REPO_PATH> status --porcelain
```

**If uncommitted changes exist in main tree:**
Warn user: "The original branch has uncommitted changes. Please commit or stash them before merging."
- Option 1: "I'll handle it, continue" — proceed (user takes responsibility)
- Option 2: "Abort" — stop Phase 7, user handles manually

### Step 1: Status Report

1. Show worktree state:
   ```bash
   git -C <WORKTREE_PATH> log <original_branch>..HEAD --oneline
   git -C <WORKTREE_PATH> diff --stat
   ```

2. Check if original branch has advanced (using saved baseline SHA):
   ```bash
   DIVERGENCE=$(git -C <TARGET_REPO_PATH> rev-list --count <original_branch_sha>..<original_branch> 2>/dev/null || echo "0")
   ```

3. Present status to user:
   ```
   Worktree status for workflow/<task-name>:
     Commits on worktree branch: N commits ahead of <original_branch>
     Original branch status: [unchanged / advanced by N commits since workflow started]

   Worktree path: <WORKTREE_PATH>
   To inspect in IDE:  cd <WORKTREE_PATH>
   To return to main:  cd <TARGET_REPO_PATH>
   ```

### Step 2: User-Driven Transfer

Present options via **AskUserQuestion**:

**Option A: "Merge worktree branch into original branch"**
   1. Attempt merge:
      ```bash
      git -C <TARGET_REPO_PATH> checkout <original_branch>
      git -C <TARGET_REPO_PATH> merge workflow/<task-name> --no-ff
      ```
   2. If conflicts: proceed to Step 3
   3. If clean merge: run quick validation (Validator subagent with `working_directory: TARGET_REPO_PATH`)

**Option B: "Apply diff to original branch"**
   1. Generate diff: `git -C <WORKTREE_PATH> diff <original_branch>..HEAD > <TASK_DIR>/changes.patch`
   2. Present command: `git -C <TARGET_REPO_PATH> apply <TASK_DIR>/changes.patch`
   3. Let user apply manually

**Option C: "Cherry-pick specific commits"**
   1. List commits: `git -C <WORKTREE_PATH> log <original_branch>..HEAD --oneline`
   2. Present cherry-pick commands for each commit
   3. Let user cherry-pick manually

**Option D: "Just show me the commands, I'll handle it"**
   1. Present all relevant commands (merge, cherry-pick, diff apply, branch checkout)
   2. Skip to Step 4 (cleanup)

### Step 3: Conflict Resolution

1. **Assess conflict severity:**
   - Count conflicting files:
     ```bash
     git -C <TARGET_REPO_PATH> diff --name-only --diff-filter=U
     ```
   - Check if conflicts are in structural files:
     ```bash
     git -C <TARGET_REPO_PATH> diff --name-only --diff-filter=U | grep -E "(models|migrations|schema|config|settings)"
     ```
   - **If structural conflicts > 2 files OR total conflicts > 5 files:**
     ```
     CRITICAL CONFLICT DETECTED

     The original branch has diverged significantly from when this workflow started.
     Conflicts affect structural files that are risky to merge manually.

     Recommended action: Start a new /workflow that incorporates the latest changes.

     Conflicting files:
     [list]

     To force merge anyway: say "resolve conflicts"
     To abort merge: say "abort merge" (your worktree branch is preserved)
     To start fresh workflow: say "new workflow"
     ```
     - If user says "abort merge": `git -C <TARGET_REPO_PATH> merge --abort`
     - If user says "new workflow": abort merge, keep worktree branch for reference
     - If user says "resolve conflicts": continue below

2. **Resolve conflicts:**
   - For each conflicting file, read the conflict markers and resolve
   - After resolution: `git -C <TARGET_REPO_PATH> add <resolved-files>`

3. **Mandatory post-conflict code review:**
   - Generate diff of the conflict resolution:
     ```bash
     git -C <TARGET_REPO_PATH> diff --cached > <TASK_DIR>/conflict-resolution.patch
     ```
   - Run Codex code review:
     - `review_code` with `working_directory: TARGET_REPO_PATH`, `uncommitted: true`
   - Spawn Code-Reviewer subagent with the conflict resolution diff and `working_directory: TARGET_REPO_PATH`
   - If issues found: fix and re-review
   - When clean: commit the merge

4. Complete the merge:
   ```bash
   git -C <TARGET_REPO_PATH> commit -m "Merge workflow/<task-name> with conflict resolution"
   ```

### Step 4: Cleanup

1. Present cleanup commands:
   ```
   Merge complete. Cleanup options:

   Remove worktree (recommended):
     git -C <TARGET_REPO_PATH> worktree remove .worktrees/<task-name>
     git -C <TARGET_REPO_PATH> branch -d workflow/<task-name>

   Keep worktree for reference:
     The worktree will remain at <WORKTREE_PATH>
     To remove later: git -C <TARGET_REPO_PATH> worktree remove .worktrees/<task-name>
   ```

2. Ask user via **AskUserQuestion**: "Remove worktree and branch?"
   - If yes: execute cleanup commands
   - If no: leave in place

3. Update `state.json`:
   ```json
   {
     "current_phase": "completed",
     "merge_status": "merged | aborted | new_workflow_recommended",
     "merged_at": "<timestamp>"
   }
   ```

---

## Checkpoint Management

### Save Checkpoint (after each phase):
```json
{
  "task_name": "<task-name>",
  "current_phase": <next_phase>,
  "completed_phases": [...],
  "project_root": "<PROJECT_ROOT>",
  "target_repo_path": "<TARGET_REPO_PATH>",
  "worktree_path": "<WORKTREE_PATH>",
  "worktree_branch": "workflow/<task-name>",
  "original_branch": "<branch name>",
  "original_branch_sha": "<SHA at workflow start>",
  "use_codex_plan_review": true|false,
  "updated_at": "<timestamp>"
}
```

### Resume Workflow:
User says: "Continue workflow" or "Resume <task-name>"
1. Read `state.json`
2. **Legacy migration check:**
   - If `state.json` does NOT contain `worktree_path`:
     - This is a pre-worktree workflow
     - Resume using legacy behavior: skip completed phases, continue from `current_phase`
     - All path variables default to project root
     - Phases 0 and 7 are not available for legacy workflows
     - Inform user: "This workflow was started before worktree isolation. Continuing in legacy mode."
3. **If `state.json` contains `worktree_path`:**
   - Restore path variables: `PROJECT_ROOT`, `TARGET_REPO_PATH`, `WORKTREE_PATH`, `TASK_DIR`, `ORIGINAL_BRANCH_SHA`
   - Verify worktree exists: `test -d <WORKTREE_PATH>`
     - If missing: re-create from the branch (which should still exist)
   - Skip completed phases
   - Continue from `current_phase`
