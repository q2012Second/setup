# Meest Project - Claude Code Workflow

This document defines a structured AI-assisted development workflow using Claude Code subagents.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. PROBLEM CLARIFICATION                                                   │
│     └─► Problem-Analyst subagent → Explore & classify → User approval       │
│                                                                             │
│  [CONDITIONAL: Skip phases based on task complexity]                        │
│                                                                             │
│  2. CONTEXT GATHERING (skip for trivial)                                    │
│     └─► Explore subagent → Find relevant files                              │
│                                                                             │
│  2.5. CONTEXT LOADING (skip for trivial/small)                              │
│     └─► Context-Loader subagent → Read & trim files                         │
│                                                                             │
│  3. PLANNING (skip for trivial/small)                                       │
│     ├─► Planner subagent (opus) → Create plan                               │
│     ├─► Plan-Reviewer subagent → Review architecture                        │
│     └─► Iterate until sound → User approval                                 │
│                                                                             │
│  3.5. PRE-IMPLEMENTATION VALIDATION                                         │
│     └─► Validate files exist, git clean, tests pass                         │
│                                                                             │
│  4. IMPLEMENTATION                                                          │
│     ├─► [Large tasks: Incremental batches with review]                      │
│     └─► Execute plan step by step                                           │
│                                                                             │
│  5. CODE QUALITY (Loop until clean)                                         │
│     ├─► Code-Simplifier subagent → Remove complexity                        │
│     ├─► Code-Reviewer subagent → Find bugs/vulnerabilities                  │
│     └─► Apply fixes iteratively                                             │
│                                                                             │
│  6. VERIFICATION (skip for trivial)                                         │
│     ├─► Code-Goal subagent → Verify solution matches problem                │
│     └─► Run tests                                                           │
│                                                                             │
│  6.5. E2E TESTING (Optional)                                                │
│     ├─► Start mock server → Configure service URLs                          │
│     └─► Run service-tester E2E tests                                        │
│                                                                             │
│  7. FINAL REVIEW                                                            │
│     └─► Present changes to user                                             │
│                                                                             │
│  [CHECKPOINT: State saved after each phase for resume capability]           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Trigger Phrases

| Phrase | Behavior |
|--------|----------|
| "Use workflow to..." | Full workflow with all phases |
| "Plan and implement..." | Same as above |
| "Review this code..." | Skip to Code Quality phase |

---

## Context Management Rules

**Principle:** Minimize main agent context by delegating all exploratory work to subagents.

### Why This Matters

```
Main agent context accumulates:
- All user messages
- All tool calls & results (Read, Grep, Bash, etc.)
- All subagent FINAL responses (but NOT their internal tool calls)

Subagent context is isolated:
- Starts fresh (only receives prompt)
- Internal tool calls stay in subagent
- Only final response returns to main agent
```

### The Rule

| Action | Who Does It | Why |
|--------|-------------|-----|
| Analyze problem | Subagent (Problem-Analyst) | Explores codebase, returns problem statement |
| Find relevant files | Subagent (Explore) | Exploration reads stay isolated |
| Read & understand code | Subagent (Context-Loader) | Only trimmed excerpts return |
| Create plan | Subagent (Planner) | Receives context via prompt, not main agent reads |
| **Revise plan** | **Subagent (Planner)** | Previous versions discarded; only final returns |
| Review code | Subagent (Code-Reviewer) | Only issues list returns |
| Simplify code | Subagent (Code-Simplifier) | Only suggestions return |
| Verify solution | Subagent (Code-Goal) | Only verdict returns |
| **Analyze logs** | **Subagent (Log-Analyzer)** | Logs can be huge; only findings return |
| **Run tests/linters** | **Subagent (Validator)** | Output can be verbose; only verdict returns |
| **Edit files** | **Main agent** | Must read to know line numbers |
| **Show user a file** | **Main agent** | User explicitly requested |
| **Reload after user changes** | **Main agent** | Re-read to get current version; mark old as stale |

### CRITICAL: Log Analysis Delegation

**NEVER read logs directly in main agent context.** Logs can be thousands of lines and will consume context rapidly.

When logs need to be analyzed (any of these scenarios):
- User provides a log file
- Debugging an error during implementation
- Verifying behavior after manual testing
- Investigating a bug or issue

**Always delegate to Log-Analyzer subagent:**
```
Main agent: "Let me analyze those logs"
→ Spawn Log-Analyzer subagent with log source
→ Receive: Summary report with findings (NOT raw logs)
```

The subagent:
- Reads and parses all log content (stays in its isolated context)
- Returns only: summary, findings, timeline, recommendations
- Cross-references codebase to add file:line references

### CRITICAL: Validation Delegation

**NEVER run tests/linters directly in main agent context.** Test output can be hundreds of lines and will consume context rapidly.

When validation is needed (any of these scenarios):
- Pre-implementation baseline check
- After implementing a batch of changes
- Final verification before completing task

**Always delegate to Validator subagent:**
```
Main agent: "Let me run the tests"
→ Spawn Validator subagent with validation type and file list
→ Receive: Pass/fail verdict with failure summaries (NOT raw output)
```

The subagent:
- Runs all validation commands (stays in its isolated context)
- Parses verbose output for failures
- Returns only: verdict, failure summaries, infrastructure fix suggestions
- Does NOT suggest business logic fixes (lacks task context)

### CRITICAL: Plan Revision Delegation

**NEVER revise plans directly in main agent context.** Plan iterations accumulate and waste context.

When user requests plan changes (any of these scenarios):
- "Change X in the plan"
- "Add requirement Y"
- "Use approach Z instead"
- Any feedback that modifies the plan

**Always delegate to Planner subagent:**
```
Main agent: "User wants to change X"
→ Spawn Planner subagent with: current plan + user feedback + problem statement
→ Planner revises, updates Design Decisions section
→ Spawn Plan-Reviewer to validate changes
→ Receive: Updated plan (NOT previous versions)
→ Overwrite plan.md
```

The subagent:
- Receives current plan and user feedback
- Revises implementation steps
- Updates Design Decisions with rationale
- Returns only the final updated plan
- Previous iterations stay in subagent context (discarded)

**Result:** Main agent has only final plan with embedded rationale.

### CRITICAL: User Code Changes Handling

**When user notifies "I made changes" during a workflow:**

User may not provide a complete list of changed files. Always detect changes yourself.

**Flow:**
```
User: "I made some changes" / "I edited the code" / "I fixed X"
         ↓
Main Agent:
  1. Detect changed files: `git diff --name-only`
  2. Mark ALL previous reads of those files as STALE
  3. Re-read changed files to get CURRENT version
  4. Quick review of user's changes (lightweight, not full Code-Reviewer):
     - Obvious bugs? Syntax errors? Broken imports?
     - Inconsistency with existing plan?
     - If issue spotted → ASK user before fixing
  5. Continue workflow with current code in context
```

**Context Rules for User Changes:**
- Previous reads of modified files: **STALE - ignore**
- Always trust `git diff` over user's list (may be incomplete)
- Current reads: **Source of truth**
- User made changes for a reason - respect intent
- But user may make errors - validate and notify

**Lightweight Review Checks:**
- Syntax errors (obvious typos, missing brackets)
- Import errors (missing/wrong imports)
- Type mismatches (if obvious)
- Breaks existing tests (if clearly visible)
- Inconsistent with plan (if significantly deviates)

**If Issue Spotted:**
```
"I noticed [issue] in your changes to [file].
You changed [X] but this might [cause Y].
Was this intentional, or should I fix it?"
```

**Do NOT:**
- Silently "fix" user's changes
- Assume user made a mistake without asking
- Keep stale code versions as source of truth

### Per-Phase Context Rules

| Phase | Main Agent Reads Files? | Subagent Reads Files? |
|-------|------------------------|----------------------|
| 1. Problem Clarification | NO | YES (Problem-Analyst) |
| 2. Context Gathering | NO | YES (Explore) |
| 2.5. Context Loading | NO | YES (Context-Loader) |
| 3. Planning | NO | YES (Planner) |
| 3.5. Pre-Implementation | NO | YES (Validator runs commands) |
| 4. Implementation | YES (only files being edited) | YES (Validator for batches) |
| 5. Code Quality | NO | YES (Simplifier, Reviewer) |
| 6. Verification | NO | YES (Code-Goal, Validator) |
| 7. Final Review | NO (use git diff) | NO |
| **Plan Revision (Phase 3)** | **NO** | **YES (Planner)** |
| **Log Analysis (any phase)** | **NO** | **YES (Log-Analyzer)** |
| **Validation (any phase)** | **NO** | **YES (Validator)** |
| **User Changes (any phase)** | **YES (re-read changed)** | **NO** |

### How to Pass Context Between Phases

```
Phase 2 (Explore) returns:
  → File list (not file contents)

Phase 2.5 (Context-Loader) receives:
  ← Problem statement + file list
  → Trimmed file contents

Phase 3 (Planner) receives:
  ← Problem statement + trimmed contents (in prompt)
  → Implementation plan

Phase 4 (Main agent):
  ← Reads plan from file
  ← Reads ONLY files being modified
```

---

## Phase 1: Problem Clarification

**Goal:** Ensure the problem is understood correctly before any work begins.

**Context Rule:** Main agent does NOT read any files. Delegate to Problem-Analyst subagent which explores codebase to understand current state.

### Subagent Used:
- **Problem-Analyst** (model: sonnet) - Explores codebase, understands current state, formulates problem

### Steps:
1. Spawn **Problem-Analyst subagent** (Task tool, model=sonnet) with:
   - User's original task description
   - Instructions to explore codebase and understand current state
2. Receive structured problem statement from subagent
3. Write to `tasks/<task-name>/problem.md`
4. Present to user for approval
5. **STOP - Wait for user approval before proceeding**

### What Main Agent Receives:
- Structured problem statement (current state, desired state, constraints, criteria)
- Task classification (see below)
- NO file contents (those stay in Problem-Analyst's isolated context)

### Task Classification (for Conditional Phase Skipping):
Problem-Analyst also classifies the task:
```
**Task Type:** [feature|bugfix|refactor|docs|config]
**Complexity:** [trivial|small|medium|large]
**Suggested Phases:** [list of phases to run]
```

Classification criteria:
- **trivial**: Single file, <20 lines change → Phases: 1, 4, 7
- **small**: 1-2 files, clear scope → Phases: 1, 2, 4, 5, 7
- **medium**: 3-5 files, some complexity → Phases: 1, 2, 2.5, 3, 4, 5, 6, 7
- **large**: 5+ files, architectural impact → All phases + incremental implementation

### Output Format:
```markdown
# Problem Statement: [Task Name]

## Task Classification
- **Type:** [feature|bugfix|refactor|docs|config]
- **Complexity:** [trivial|small|medium|large]
- **Suggested Phases:** [1, 2, 4, 5, 7] (example)

## Current State
[What exists now - based on codebase exploration]

## Desired State
[What should exist after implementation]

## Constraints
- [Constraint 1]
- [Constraint 2]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Relevant Areas (for Phase 2)
- [Hint about where to look: module, pattern, etc.]

## Questions (if any)
- [Any clarifying questions]
```

---

## Phase 2: Context Gathering

**Goal:** Identify all relevant files in the codebase.

**Context Rule:** Main agent does NOT read any files. Delegate ALL exploration to Explore subagent.

### Steps:
1. Spawn **Explore subagent** (Task tool, subagent_type="Explore") with the problem description
2. Receive file list from subagent (NOT file contents)
3. Pass file list to Phase 2.5

### What Main Agent Receives:
- List of 10-20 relevant file paths with brief descriptions
- NO file contents (those stay in Explore subagent's isolated context)

### Output:
File list kept in memory. Only save to `context.md` if user explicitly requests.

---

## Phase 2.5: Context Loading

**Goal:** Load only relevant content from identified files, trimming irrelevant sections to reduce context noise for planning.

**Context Rule:** Main agent does NOT read any files. Context-Loader subagent reads and returns trimmed content.

### Subagent Used:
- **Context-Loader** (model: sonnet) - Reads files and extracts relevant content

### Steps:
1. Spawn **Context-Loader subagent** (Task tool, model=sonnet) with:
   - Problem statement
   - File list from Phase 2 (passed directly in prompt)
2. Subagent reads each file and decides:
   - **FULL**: Include entire file (small files, high relevance)
   - **EXCERPT**: Include only relevant sections (large files, mixed relevance)
   - **SKIP**: Exclude file entirely (incorrectly identified as relevant)
3. Receive trimmed context from subagent
4. Pass trimmed context to Phase 3 (no file needed)
5. Only save to `trimmed.md` if user explicitly requests

### What Main Agent Receives:
- Trimmed file contents (full or excerpts based on relevance)
- NOT raw file reads (those stay in Context-Loader's isolated context)

### Why This Phase Exists:
This phase uses a fresh subagent that:
- Starts with clean context (no exploration noise from Phase 2)
- Reads ONLY the curated file list
- Makes intelligent decisions about what to include
- Returns trimmed context directly to main agent

---

## Phase 3: Planning

**Goal:** Create a sound, reviewed implementation plan.

**Context Rule:** Main agent does NOT read any files. Pass trimmed context from Phase 2.5 to Planner via prompt.

### Subagents Used:
- **Planner** (model: opus) - Creates the implementation plan
- **Plan-Reviewer** (model: opus) - Reviews from architecture standpoint

### Planning Loop:
```
┌──────────────────────────────────────────────────────┐
│                    PLANNING LOOP                     │
│                                                      │
│  ┌─────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Planner │───►│ Plan-Reviewer│───►│ Revisions? │  │
│  └─────────┘    └──────────────┘    └─────┬──────┘  │
│       ▲                                   │         │
│       │         Yes                       │ No      │
│       └───────────────────────────────────┘         │
│                                           ▼         │
│                                    User Approval    │
└──────────────────────────────────────────────────────┘
```

### Steps:
1. Spawn **Planner subagent** (Task tool, model=opus) with:
   - Problem statement
   - Trimmed context from Phase 2.5 (passed in prompt, NOT re-read by main agent)
2. Receive initial plan from subagent
3. Spawn **Plan-Reviewer subagent** (Task tool, model=opus) with:
   - Problem statement
   - Proposed plan
   - Trimmed context (same as Planner received)
4. Review feedback and revise plan if needed
5. Repeat steps 3-4 until plan is approved by reviewer
6. Save plan to `tasks/<task-name>/plan.md`
7. **STOP - Present plan to user for approval**

### What Main Agent Receives:
- Implementation plan from Planner
- Review feedback from Plan-Reviewer
- NO file contents (passed through prompts, not re-read)

### Plan Format:
```markdown
## Implementation Plan: [Task Name]

### Overview
[Brief description of what will be implemented]

### Design Decisions
[Accumulates through revisions - captures rationale for current approach]

| Decision | Rationale |
|----------|-----------|
| [Choice made] | [Why this approach was chosen] |
| [User requirement] | [How it's addressed] |

**User Requirements:**
- [Explicit user request 1]
- [Explicit user request 2]

**Alternative Approaches Considered:**
- [Alternative 1]: [Why not chosen]
- [Alternative 2]: [Why not chosen]

### Prerequisites
- [Any setup or preparation needed]

### Implementation Steps

#### Step 1: [Step Title]
**Files:** `path/to/file.py`
**Changes:**
- [Specific change 1]
- [Specific change 2]

**Code:**
```python
# Example code snippet if helpful
```

#### Step 2: [Step Title]
...

### Testing Strategy
- [ ] [Test case 1]
- [ ] [Test case 2]

### Edge Cases Considered
- [Edge case 1 and how it's handled]
- [Edge case 2 and how it's handled]

### Risks and Mitigations
- **Risk:** [Potential risk]
  **Mitigation:** [How to address it]
```

### Plan Revision Flow

**When user requests changes to a plan, ALWAYS delegate to Planner subagent.**

This keeps main agent context clean - only the final approved plan remains.

```
User: "Change X in the plan" / "Add requirement Y" / "Use approach Z instead"
         ↓
Main Agent: Does NOT revise plan directly
         ↓
Spawns Planner subagent (Task tool, model=opus) with:
  - Current plan (from plan.md)
  - User's feedback/new requirements
  - Original problem statement
  - Trimmed context (if significant architectural change)
         ↓
Planner: Revises plan
  - Updates Implementation Steps as needed
  - Adds to Design Decisions section:
    - New user requirement
    - Rationale for change
    - Alternatives considered (if applicable)
         ↓
Spawns Plan-Reviewer subagent (Task tool, model=opus)
         ↓
Returns: Updated plan with Design Decisions updated
         ↓
Main Agent: Overwrites plan.md with new version
         ↓
Present to user for approval (repeat if more changes requested)
```

**Context Management for Revisions:**
- Main agent receives: User feedback (unavoidable) + final plan only
- Previous plan versions: Discarded (not kept in main context)
- Rationale for changes: Embedded in Design Decisions section of plan.md
- Subagent context: Contains revision work, discarded after returning plan

**Design Decisions Section Accumulates:**
- User requirements (explicit requests)
- Implementation choices and why
- Alternatives considered and why rejected
- Trade-offs acknowledged

This ensures that after approval, main agent has clean context with only:
1. Original task description
2. Final problem.md
3. Final plan.md (with all rationale embedded)

---

## Conditional Phase Skipping

Based on task classification from Phase 1, skip phases that aren't needed:

| Complexity | Phases to Run | Phases to Skip |
|------------|---------------|----------------|
| **trivial** | 1, 4, 5, 7 | 2, 2.5, 3, 3.5, 6 |
| **small** | 1, 2, 4, 5, 7 | 2.5, 3, 3.5, 6 |
| **medium** | 1, 2, 2.5, 3, 3.5, 4, 5, 6, 7 | None |
| **large** | All + incremental | None |

### Skip Conditions:
- **Skip Phase 2 (Context Gathering)**: If Problem-Analyst already identified all relevant files
- **Skip Phase 2.5 (Context Loading)**: If <3 files involved
- **Skip Phase 3 (Planning)**: If <2 files and obvious changes
- **Skip Phase 6 (Verification)**: If refactor with no behavior change

### User Override:
User can always request full workflow regardless of classification:
- "Use full workflow for [task]"
- "Don't skip any phases"

---

## Phase 3.5: Pre-Implementation Validation

**Goal:** Validate that implementation can proceed without issues.

**Context Rule:** Main agent does NOT run validation commands directly. Delegate to Validator subagent.

### When to Run:
- Always for medium/large tasks
- Skip for trivial/small tasks

### Steps:
1. Spawn **Validator subagent** (Task tool, model=sonnet) with:
   - Validation type: "baseline"
   - Project info (path, CLAUDE.md location)
   - Files from plan (for targeted validation)
2. Receive validation report (NOT raw command output)
3. Write to `tasks/<task-name>/baseline-validation.md`
4. If BLOCKED: Stop and report to user
5. If PASS/FAIL: Note baseline and continue (failures are pre-existing)

**Note:** Git status is NOT checked. User manages git themselves.

### What Main Agent Receives:
- Pass/fail verdict
- List of pre-existing test failures (if any)
- Infrastructure issues that might block implementation
- NOT raw test/linter output

### On Failure:
- If files missing: Stop, report to user
- If tests fail: Note as baseline (not a blocker unless critical)
- If syntax errors: Stop, report to user
- If infrastructure issues: Apply suggested fixes or report to user

---

## Phase 4: Implementation

**Goal:** Execute the approved plan methodically.

**Context Rule:** Main agent DOES read files here - but ONLY files being modified. This is the only phase where main agent reads files directly.

### Incremental Implementation (for Large Tasks)

For tasks classified as **large** (5+ files), implement in batches:

```
┌─────────────────────────────────────────────────────────┐
│              INCREMENTAL IMPLEMENTATION                  │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ Batch 1  │──►│ Validate │──►│ Batch 2  │──► ...     │
│  │(2-3 steps)│   │& Review  │   │(2-3 steps)│           │
│  └──────────┘   └──────────┘   └──────────┘            │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│  (Validator)    Fix issues    (Validator)              │
└─────────────────────────────────────────────────────────┘
```

#### Batch Implementation Steps:
1. Group plan steps into batches of 2-3 related changes
2. For each batch:
   - Implement the steps
   - Spawn **Validator subagent** (type: "batch") with changed files
   - Receive pass/fail verdict (NOT raw test output)
   - Spawn Code-Simplifier for batch review
   - Fix any issues found
   - Save checkpoint (see Checkpoint section)
3. Continue to next batch

**Note:** Do NOT run tests/linters directly - delegate to Validator subagent.

#### Batch Size Guidelines:
- 2-3 steps per batch for large tasks
- Group related changes together (e.g., model + serializer + view)
- Keep batches independently testable when possible

### Standard Steps (all tasks):
1. Read plan from `tasks/<task-name>/plan.md`
2. Create TODO list from the plan
3. For each step (or batch for large tasks):
   - Read ONLY the file being modified (need exact line numbers for Edit)
   - Make the edit
   - Mark TODO as completed
   - [Large tasks: Review after each batch]
4. If blocked or plan needs adjustment:
   - Document the issue
   - Propose solution
   - Get user approval if significant deviation

### Guidelines:
- Follow existing code patterns
- Keep changes minimal and focused
- Don't add unnecessary features
- Write tests as you go (if applicable)
- **Do NOT read files "for context"** - that was done in earlier phases
- **Large tasks**: Review after each batch, not just at the end

### Handling User's Manual Code Changes

When user says "I made changes" / "I edited the code" / "I fixed X" during implementation:

1. **Detect changed files:**
   ```bash
   git diff --name-only
   ```
   Don't rely solely on user's list - may be incomplete.

2. **Mark previous reads as STALE:**
   Any files you read earlier that appear in git diff are now stale.
   Do NOT trust previous versions in context.

3. **Re-read changed files:**
   Read current version to get source of truth.

4. **Lightweight review of user's changes:**
   - Obvious syntax errors?
   - Broken imports?
   - Inconsistent with plan?
   - If issue spotted → **ASK before fixing**

   ```
   "I noticed [issue] in your changes to [file].
   Was this intentional, or should I fix it?"
   ```

5. **Continue workflow with current code.**

**Important:**
- User changed code for a reason - respect intent
- But user may make errors - validate and ask if needed
- Never silently "fix" user's changes

---

## Phase 5: Code Quality

**Goal:** Ensure code is clean, simple, and bug-free.

**Context Rule:** Main agent does NOT read files. Delegate ALL review to subagents. Only receive issue summaries.

### Subagents Used:
- **Code-Simplifier** (model: sonnet) - Removes unnecessary complexity
- **Code-Reviewer** - Finds bugs, vulnerabilities, performance issues

### Quality Loop:
```
┌────────────────────────────────────────────────────────────┐
│                    CODE QUALITY LOOP                       │
│                                                            │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────┐  │
│  │Code-Simplifier│───►│ Code-Reviewer │───►│  Issues?  │  │
│  └───────────────┘    └───────────────┘    └─────┬─────┘  │
│         ▲                                        │        │
│         │              Yes                       │ No     │
│         └────────────────────────────────────────┘        │
│                                              ▼            │
│                                        Verification       │
└────────────────────────────────────────────────────────────┘
```

### Steps:
1. Generate diff of all changes using `git diff`
2. Spawn **Code-Simplifier subagent** (Task tool, model=sonnet) with:
   - Diff content (NOT by re-reading files)
   - Problem context
3. Receive simplification suggestions
4. Apply suggestions (main agent reads only files being modified)
5. Spawn **Code-Reviewer subagent** (Task tool, model=opus) with:
   - Updated diff
   - Problem context
6. Receive issue list
7. Fix any identified issues (main agent reads only files being modified)
8. Repeat until no significant issues remain

### What Main Agent Receives:
- List of simplification suggestions with file:line references
- List of issues with severity and suggested fixes
- NO full file contents from reviewers

---

## Phase 6: Verification

**Goal:** Confirm the implementation solves the original problem.

**Context Rule:** Main agent does NOT read files or run tests directly. Delegate validation to Validator, verification to Code-Goal.

### Subagents Used:
- **Validator** (model: sonnet) - Runs final tests/linters
- **Code-Goal** (model: sonnet) - Verifies solution matches problem statement

### Steps:
1. Spawn **Validator subagent** (Task tool, model=sonnet) with:
   - Validation type: "final"
   - Project info
   - All changed files
2. Receive validation verdict (NOT raw test output)
3. Write to `tasks/<task-name>/final-validation.md`
4. Spawn **Code-Goal subagent** (Task tool, model=sonnet) with:
   - Original problem statement (from `problem.md`)
   - Implementation diff (from `git diff`)
   - Validation results summary (from step 2)
5. Receive verification verdict
6. Write to `tasks/<task-name>/verification.md`
7. Address any gaps identified

### What Main Agent Receives:
- Validation verdict with failure summaries (NOT raw output)
- Pass/fail verdict for each acceptance criterion
- List of gaps or concerns
- NO file contents, NO raw test output

---

## Phase 6.5: E2E Testing (Optional)

**Goal:** Verify service behavior through end-to-end API tests with mocked external dependencies.

### When to Use:
- Changes to API endpoints
- Changes to external service integrations
- Changes to authentication/authorization flows
- When specified by user

### Prerequisites:
1. **Service-tester** project at `../service-tester/`
2. Target service running locally
3. Mock server running (for mocked dependencies)

### Steps:
1. Start mock server:
   ```bash
   cd ../service-tester && ./scripts/start_mock_server.sh
   ```
2. Configure target service to use mock URLs (if needed):
   - **cost-module:** Set `MWL_USER_AUTH_BASE_URL=http://localhost:8888`
   - **easy-returns:** Run `./scripts/seed_easy_returns.sh`
3. Run E2E tests:
   ```bash
   cd ../service-tester && poetry run pytest -m <service_marker>
   ```
4. Review request logs in `../service-tester/logs/`

### Service Markers:
- `cost_module` - Tests for cost-module service
- `easy_returns` - Tests for easy-returns-service

### Mock Coverage by Service:

| Service | Mocked | NOT Mocked |
|---------|--------|------------|
| cost-module | MWL Auth | - |
| easy-returns | Portmone | MWL Connection (hardcoded URLs) |

### Notes:
- Request logs generate curl commands for debugging
- Mock server state persists across tests within a session
- Reset state via `POST /api/state/reset`

---

## Phase 7: Final Review

**Goal:** Present completed work to user.

**Context Rule:** Main agent does NOT read files. Use `git diff` and test output for summary.

### Steps:
1. Generate final diff with `git diff`
2. Compile summary from:
   - Problem statement (from `problem.md`)
   - Plan (from `plan.md`)
   - Verification results (from Phase 6)
   - Test output (from Phase 6)
3. Present summary to user

### Output Format:
```markdown
## Implementation Complete

### Summary
[Brief description of what was implemented]

### Files Changed
- `path/to/file1.py` - [What changed]
- `path/to/file2.py` - [What changed]

### Tests
- [Test results summary]
- Coverage: [X%]

### Verification
- [x] Solves original problem
- [x] Tests pass
- [x] Code reviewed for bugs/vulnerabilities
- [x] Code simplified where possible

### Notes
[Any important notes or follow-up items]
```

---

## Checkpoint/Resume Capability

**Goal:** Save workflow state after each phase to enable resumption if interrupted.

### State File Location
```
tasks/<task-name>/state.json
```

### State Structure
```json
{
  "task_name": "add-rate-limiting",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "complexity": "medium",
  "current_phase": 4,
  "completed_phases": [1, 2, "2.5", 3, "3.5"],
  "skipped_phases": [],
  "phase_outputs": {
    "1": {"file": "problem.md", "classification": "medium"},
    "2": {"file_list": ["path/to/file1.py", "path/to/file2.py"]},
    "2.5": {"trimmed_context_summary": "..."},
    "3": {"file": "plan.md", "approved": true},
    "3.5": {"validation": "PASS"}
  },
  "implementation": {
    "total_steps": 5,
    "completed_steps": 2,
    "current_batch": 1,
    "batches_completed": 0
  }
}
```

### When to Save Checkpoint
- After each phase completes successfully
- After each batch during incremental implementation
- Before any user approval prompt

### How to Save
```python
# Pseudocode - main agent updates state.json after each phase
state = {
    "current_phase": completed_phase + 1,
    "completed_phases": [...existing, completed_phase],
    "phase_outputs": {...existing, phase_output},
    "updated_at": now()
}
write_file(f"tasks/{task_name}/state.json", json.dumps(state))
```

### How to Resume

When user says "continue workflow" or "resume [task-name]":

1. **Detect existing state**:
   ```bash
   ls tasks/*/state.json  # Find incomplete workflows
   ```

2. **Load state**:
   - Read `state.json`
   - Determine next phase to run
   - Load necessary context from phase_outputs

3. **Resume from checkpoint**:
   - Skip completed phases
   - Reload context needed for current phase
   - Continue execution

### Resume Prompt Template
```
## Resuming Workflow: {task_name}

**Last completed phase:** {current_phase - 1}
**Next phase:** {current_phase}
**Completed:** {completed_phases}

### Context from Previous Phases:
{phase_outputs_summary}

Continuing from Phase {current_phase}...
```

### Trigger Phrases for Resume
- "Continue workflow"
- "Resume [task-name]"
- "Continue from where we left off"
- "What was I working on?"

### Handling Stale State
If state is >24 hours old, prompt user:
```
Found incomplete workflow "{task_name}" from {time_ago}.
- Resume this workflow?
- Start fresh?
- Delete and start new task?
```

---

## Subagent Specifications

### Problem-Analyst Subagent

**Purpose:** Explore codebase to understand current state and formulate a clear problem statement with task classification.

**Model:** sonnet (good balance of exploration and analysis)

**Prompt Template:**
```
You are a software analyst. Your job is to understand a user's task request by exploring the codebase and formulating a clear problem statement.

## User's Task Request
{user_task_description}

## Your Task

1. **Explore the codebase** to understand:
   - Current implementation related to the task
   - Existing patterns and conventions
   - Files that might be affected

2. **Classify the task**:
   - **Type:** feature | bugfix | refactor | docs | config
   - **Complexity:**
     - trivial: Single file, <20 lines change
     - small: 1-2 files, clear scope
     - medium: 3-5 files, some complexity
     - large: 5+ files, architectural impact

3. **Formulate a problem statement** with:
   - Current state (what exists now, based on your exploration)
   - Desired state (what should exist after)
   - Constraints (technical, business, compatibility)
   - Acceptance criteria (testable conditions for success)

4. **Suggest phases to run** based on complexity:
   - trivial: 1, 4, 7
   - small: 1, 2, 4, 5, 7
   - medium: 1, 2, 2.5, 3, 4, 5, 6, 7
   - large: All phases + incremental implementation

## Output Format
```markdown
# Problem Statement: [Task Name]

## Task Classification
- **Type:** [feature|bugfix|refactor|docs|config]
- **Complexity:** [trivial|small|medium|large]
- **Suggested Phases:** [1, 4, 7] (example for trivial)

## Current State
[What exists now - be specific, reference files you found]

## Desired State
[What should exist after implementation]

## Constraints
- [Constraint 1]
- [Constraint 2]

## Acceptance Criteria
- [ ] [Criterion 1 - testable]
- [ ] [Criterion 2 - testable]

## Relevant Areas (hints for Phase 2)
- [Module/directory to focus on]
- [Related patterns to follow]

## Questions (if any)
- [Clarifying questions for user]
```
```

---

### Planner Subagent

**Purpose:** Create or revise implementation plans from problem statements and codebase context.

**Model:** opus (maximum thinking capability)

**Modes:** Creation (new plan) or Revision (update existing plan)

**Prompt Template (Creation Mode):**
```
You are a senior software architect creating an implementation plan.

## Problem Statement
{problem_statement}

## Codebase Context
### Relevant Files:
{relevant_files_list}

### File Contents:
{file_contents}

## Your Task
Create a detailed, step-by-step implementation plan that:
1. Follows existing patterns and conventions in the codebase
2. Minimizes changes while fully solving the problem
3. Considers edge cases and error handling
4. Includes specific code locations and changes
5. Defines clear testing strategy

Include a **Design Decisions** section that captures:
- Key implementation choices and rationale
- User requirements (from problem statement)
- Alternatives considered and why rejected

Output a complete plan in markdown format using the plan format from AGENTS.md.
```

**Prompt Template (Revision Mode):**
```
You are a senior software architect revising an implementation plan based on user feedback.

## Problem Statement
{problem_statement}

## Current Plan
{current_plan_content}

## User Feedback / New Requirements
{user_feedback}

## Codebase Context (if architectural change)
{trimmed_context_if_needed}

## Your Task
Revise the plan to address the user's feedback:

1. **Update Implementation Steps** as needed
2. **Update Design Decisions section** - ADD (do not remove previous):
   - New user requirement: "{user_feedback summary}"
   - Rationale for the change
   - Alternatives considered (if applicable)
3. Keep unaffected parts of the plan intact
4. Ensure the revised plan is internally consistent

**Important:**
- The Design Decisions section should ACCUMULATE user requirements and rationale
- Do not remove previous design decisions unless they're obsolete
- Make the plan self-contained - all context needed to understand decisions should be in the plan

Output the complete revised plan in markdown format.
```

---

### Plan-Reviewer Subagent

**Purpose:** Review implementation plans from an architecture standpoint.

**Model:** opus (maximum thinking capability)

**Prompt Template:**
```
You are a senior software architect reviewing an implementation plan.

## Problem Statement
{problem_statement}

## Proposed Plan
{plan_content}

## Codebase Context
{context_summary}

## Your Task
Review this plan critically for:

1. **Correctness**: Does this plan actually solve the problem?
2. **Completeness**: Are all edge cases handled?
3. **Architecture**: Does it fit well with existing patterns?
4. **Simplicity**: Is this the simplest solution? Can anything be removed?
5. **Risks**: What could go wrong? Missing error handling?
6. **Testing**: Is the test strategy adequate?

For each issue found, provide:
- Severity (Critical/Major/Minor)
- Description of the issue
- Suggested fix

If the plan is acceptable, state "PLAN APPROVED" at the end.
```

---

### Code-Simplifier Subagent

**Purpose:** Remove unnecessary complexity and improve code quality.

**Model:** sonnet (fast, good for code analysis)

**Prompt Template:**
```
You are a code simplification expert. Your goal is to make code cleaner and simpler.

## Changes to Review
{diff_content}

## Your Task
Analyze the code for:

1. **Redundant code**: Duplicate logic that can be consolidated
2. **Dead code**: Unused variables, unreachable branches
3. **Unnecessary abstraction**: Over-engineering, premature generalization
4. **Missed abstractions**: Repeated patterns that should be functions
5. **Verbose constructs**: Code that can be simplified using language idioms
6. **Redundant checks**: Conditions that are always true/false

For each finding:
- Location (file:line)
- Issue description
- Suggested simplification with code example

Focus only on the changed code. Don't suggest changes to unmodified code.
```

---

### Code-Reviewer Subagent

**Purpose:** Find bugs, vulnerabilities, and performance issues.

**Model:** opus (thorough analysis needed)

**Prompt Template:**
```
You are a security-focused code reviewer.

## Changes to Review
{diff_content}

## Original Files Context
{original_files}

## Your Task
Review the code for:

1. **Security Vulnerabilities**
   - SQL injection, XSS, command injection
   - Authentication/authorization bypasses
   - Exposed secrets or sensitive data
   - Insecure deserialization

2. **Bugs**
   - Null/undefined references
   - Off-by-one errors
   - Race conditions
   - Incorrect error handling
   - Logic errors

3. **Performance Issues**
   - N+1 queries
   - Memory leaks
   - Blocking operations in async code
   - Inefficient algorithms

4. **Breaking Changes**
   - API compatibility issues
   - Database migration risks

For each issue:
- Severity (Critical/High/Medium/Low)
- Location (file:line)
- Description
- Suggested fix
- Impact if not fixed

If no issues found, state "NO ISSUES FOUND".
```

---

### Code-Goal Subagent

**Purpose:** Verify that implementation solves the original problem.

**Model:** sonnet (analytical comparison)

**Prompt Template:**
```
You are verifying that an implementation matches its requirements.

## Original Problem Statement
{problem_statement}

## Acceptance Criteria
{acceptance_criteria}

## Implementation Changes
{diff_content}

## Test Cases
{test_cases}

## Your Task
Verify:

1. **Problem Solved**: Does the implementation address the problem statement?
   - For each acceptance criterion, explain how it's met (or not)

2. **Test Coverage**: Do the tests actually verify the solution?
   - Are acceptance criteria covered by tests?
   - Are edge cases tested?
   - Any missing test scenarios?

3. **Completeness**: Is anything missing?
   - Partial implementations
   - TODO comments left behind
   - Incomplete error handling

Output:
- [ ] or [x] for each acceptance criterion with explanation
- List of any gaps or concerns
- Overall verdict: VERIFIED / NEEDS WORK
```

---

### Context-Loader Subagent

**Purpose:** Load and intelligently trim context from files identified during exploration, keeping only relevant content for planning.

**Model:** sonnet (good balance of speed and judgment)

**When Used:** After Phase 2 (Context Gathering), before Phase 3 (Planning)

**Prompt Template:**
```
You are a context extraction specialist. Your job is to read source files and extract only the content relevant to a specific task.

## Problem Statement
{problem_statement}

## Files to Load
{files_list_from_context_md}

## Your Task
For each file listed, read it and decide how much context to include:

### Decision Criteria:

1. **FULL FILE** - Include entire file when:
   - File is small (<150 lines) AND at least moderately relevant
   - File is a configuration/settings file directly related to task
   - File is a test file that will need modification
   - File defines core interfaces/models needed for the task

2. **KEY EXCERPTS** - Include only relevant sections when:
   - File is large (>150 lines) with mixed relevance
   - Only specific functions/classes are relevant
   - File contains boilerplate that's not useful for planning

3. **SKIP ENTIRELY** - Do not include when:
   - File was incorrectly identified as relevant
   - File's relevance is too tangential to justify context cost

### Output Format:

For each file, output in this exact format:

---
## `path/to/file.py` [FULL|EXCERPT|SKIPPED]
**Relevance:** [One sentence explaining why this file matters]
**Lines:** [X-Y] or [FULL] or [SKIPPED]

```python
[file content or excerpt]
```
---

### Guidelines:
- For EXCERPT: Include complete functions/classes, not partial snippets
- Include imports only if they reveal important dependencies
- Preserve enough context for a planner to understand the code structure
- When in doubt, include more rather than less - planning needs good context
- Add brief inline comments like `# ... (auth middleware, not relevant)` when skipping sections

Output your extracted context now.
```

---

### Log-Analyzer Subagent

**Purpose:** Analyze logs to detect anomalies, errors, and investigate specific problems. Supports CSV files (Datadog exports), Docker container logs, and local server logs.

**Model:** sonnet (good balance of speed and analytical capability)

**Modes:**
1. **Anomaly Detection** - General scan for any issues (default)
2. **Problem-Focused** - Targeted analysis for a specific problem

**Prompt Template:**
```
You are a log analysis specialist. Your job is to analyze logs and identify issues, anomalies, or evidence related to specific problems.

## Analysis Mode
{mode: "anomaly" | "problem-focused"}

## Problem Context (if problem-focused mode)
{problem_description}

## Log Source
{source_type: "csv" | "docker" | "local" | "file"}
{source_path_or_command}

## Your Task

### Step 1: Detect Log Format
First, examine a sample of the logs to understand:
- Format (CSV with columns, JSON lines, plain text, structured text)
- Available fields (timestamp, level, message, service, etc.)
- Timestamp format
- Log levels used (ERROR, WARN, INFO, DEBUG, etc.)

### Step 2: Parse and Analyze

**For Anomaly Detection Mode:**
1. **Error Summary**: Count and categorize all ERROR/CRITICAL/FATAL entries
2. **Warning Patterns**: Identify recurring warnings
3. **Anomalies**: Look for:
   - Sudden spikes in error rates
   - Unusual patterns (repeated failures, timeouts)
   - Out-of-order events
   - Missing expected log entries
   - Performance degradation indicators (slow queries, timeouts)
4. **Timeline**: Build chronological view of significant events

**For Problem-Focused Mode:**
1. **Keyword Search**: Find entries related to the problem
2. **Timeline Reconstruction**: Build sequence of events leading to the issue
3. **Correlation**: Find related entries across different components
4. **Root Cause Indicators**: Identify potential causes
5. **Supporting Evidence**: Gather log excerpts that support findings

### Step 3: Cross-Reference with Codebase (if helpful)
When you find interesting log entries:
- Search codebase for the log message to find source location
- Understand what code path generated the log
- Identify related error handling or business logic

### Step 4: Generate Report

## Output Format

```markdown
# Log Analysis Report

## Analysis Info
- **Source:** [source description]
- **Mode:** [Anomaly Detection / Problem-Focused: "problem description"]
- **Time Range:** [start] to [end]
- **Total Entries:** [count]
- **Log Format:** [detected format]

## Executive Summary
[2-3 sentences: main findings, severity assessment]

## Findings

### Critical Issues
#### [Issue Title]
- **Severity:** Critical/High/Medium/Low
- **Occurrences:** [count]
- **First seen:** [timestamp]
- **Last seen:** [timestamp]
- **Log excerpt:**
  ```
  [relevant log lines]
  ```
- **Code reference:** `file.py:123` (if found)
- **Analysis:** [what this means, potential impact]

### Warnings and Patterns
[Similar structure for non-critical findings]

### Anomalies Detected
[Unusual patterns, spikes, etc.]

## Timeline of Significant Events
| Time | Event | Severity |
|------|-------|----------|
| ... | ... | ... |

## Code References (if applicable)
| Log Pattern | Source File | Line |
|-------------|-------------|------|
| "Error processing..." | `service/handler.py` | 234 |

## Recommendations
- [Actionable next steps]

## Raw Evidence
<details>
<summary>Relevant log excerpts</summary>

[Full log excerpts for reference]

</details>
```
```

**Log Source Handling:**

| Source Type | How to Access |
|-------------|---------------|
| CSV file | Read file directly, parse CSV columns |
| Docker container | `docker logs <container>` or `docker compose logs <service>` |
| Local server | Check common locations: `logs/`, project-specific log paths |
| Generic file | Read and auto-detect format |

**CSV Format Notes (Datadog exports):**
- Columns vary but typically include: timestamp, status/level, service, message
- May have additional fields like host, trace_id, etc.
- First row is usually headers

---

### Validator Subagent

**Purpose:** Run tests, linters, type checks, and other validation commands. Parse verbose output and return concise verdict.

**Model:** sonnet (needs to run commands and parse output)

**When Used:**
- Phase 3.5: Pre-Implementation Validation (establish baseline)
- Phase 4: After implementation batches (for large tasks)
- Phase 6: Final verification

**Prompt Template:**
```
You are a validation specialist. Your job is to run tests, linters, and other validation commands, then report results concisely.

## Validation Type
{type: "baseline" | "batch" | "final"}

## Project Info
Project: {project_name}
Project root: {project_path}
Project CLAUDE.md: {path to project CLAUDE.md if exists}

## Files Changed (if applicable)
{list of changed files for targeted validation}

## Your Task

### Step 1: Detect Project Setup
Read the project's CLAUDE.md or pyproject.toml to understand:
- Test framework (pytest, unittest, etc.)
- Test command (poetry run pytest, tox, etc.)
- Linter (ruff, flake8, etc.)
- Type checker (mypy, pyright, etc.)
- Any special setup or environment variables

### Step 2: Run Validation Commands

**For baseline validation:**
1. Check files exist (if file list provided)
2. Run syntax check: `poetry run python -m py_compile <files>`
3. Run linter on changed files (if any)
4. Run relevant tests (related to changed files)

**For batch validation (during implementation):**
1. Run linter on changed files
2. Run tests related to changed files
3. Quick type check if configured

**For final validation:**
1. Run full linter
2. Run full test suite
3. Run type checker
4. Check coverage if configured

### Step 3: Parse Results
For each command:
- Capture exit code (0 = pass, non-zero = fail)
- Parse output for specific failures
- Extract relevant error messages

### Step 4: Generate Report

## Output Format

```markdown
# Validation Report

## Summary
- **Overall:** PASS | FAIL
- **Tests:** X passed, Y failed, Z skipped
- **Linter:** X issues (Y errors, Z warnings)
- **Type Check:** X errors

## Test Results
### Status: PASS | FAIL

#### Failed Tests (if any)
| Test | Error |
|------|-------|
| `test_module::test_name` | Brief error description |

#### Test Output Summary
[2-3 line summary of what was tested]

## Linter Results
### Status: PASS | FAIL

#### Issues (if any)
| File | Line | Rule | Message |
|------|------|------|---------|
| `path/file.py` | 42 | E501 | Line too long |

## Type Check Results
### Status: PASS | FAIL | SKIPPED

#### Errors (if any)
| File | Line | Error |
|------|------|-------|
| `path/file.py` | 42 | Incompatible types... |

## Infrastructure Issues (fixable)
[Only list issues with test config, linter config, missing deps - NOT business logic]

| Issue | Suggested Fix |
|-------|---------------|
| Missing test dependency | `poetry add --dev pytest-mock` |
| Linter config missing rule | Add to pyproject.toml: ... |

## Verdict
**{PASS | FAIL | BLOCKED}**

{If FAIL: Brief summary of what needs fixing}
{If BLOCKED: What's preventing validation from running}
```

**IMPORTANT:**
- Do NOT suggest fixes for business logic failures - you lack task context
- Only suggest fixes for infrastructure/config issues
- Keep failure descriptions brief - main agent will investigate if needed
```

**What Returns to Main Agent:**
- Pass/fail verdict
- Failure summaries (not full stack traces)
- Infrastructure fix suggestions only
- NOT raw command output (stays in subagent context)

---

## Task Directory Structure

**IMPORTANT:** Every workflow creates a dedicated task directory under `tasks/`.

### Directory Creation
1. Derive task name from description using kebab-case
   - "add rate limiting to login" → `add-rate-limiting-to-login`
   - "fix auth bug" → `fix-auth-bug`
2. Create directory: `mkdir -p tasks/<task-name>/`

### Output Files
```
tasks/
└── <task-name>/
    ├── state.json              # Checkpoint state for resume capability
    ├── problem.md              # Problem statement with classification (Phase 1)
    ├── plan.md                 # Implementation plan (Phase 3)
    ├── plan-review.md          # Plan review feedback (Phase 3)
    ├── baseline-validation.md  # Pre-implementation validation (Phase 3.5)
    ├── simplify-review.md      # Code simplification suggestions (Phase 5)
    ├── code-review.md          # Bug/vulnerability findings (Phase 5)
    ├── final-validation.md     # Final tests/linter results (Phase 6)
    ├── verification.md         # Goal verification results (Phase 6)
    ├── summary.md              # Final summary of changes (Phase 7)
    ├── log-analysis.md         # (Optional) Log analysis report if logs examined
    ├── context.md              # (Optional) Only if user requests
    └── trimmed.md              # (Optional) Only if user requests
```

### File Purposes

| File | Phase | Contains |
|------|-------|----------|
| `state.json` | All | Checkpoint state: current phase, completed phases, complexity |
| `problem.md` | 1 | Task classification + current/desired state + acceptance criteria |
| `plan.md` | 3 | Step-by-step implementation with code snippets |
| `plan-review.md` | 3 | Architectural review feedback, issues, verdict |
| `baseline-validation.md` | 3.5 | Pre-implementation test/lint results, baseline failures |
| `simplify-review.md` | 5 | Complexity issues, before/after code |
| `code-review.md` | 5 | Security, bugs, performance issues by severity |
| `final-validation.md` | 6 | Final test/lint results, pass/fail verdict |
| `verification.md` | 6 | Acceptance criteria check, test coverage, verdict |
| `summary.md` | 7 | Overview, files changed, test results, notes |
| `log-analysis.md` | Any | (Optional) Log analysis findings, timeline, code references |
| `context.md` | 2 | (Optional) List of relevant files - only if requested |
| `trimmed.md` | 2.5 | (Optional) Trimmed file contents - only if requested |

---

## Commands Reference

### Slash Commands
```
/workflow [task]              # Full 7-phase workflow
/plan [task]                  # Create plan with Planner subagent
/review-plan [task-name]      # Review plan with Plan-Reviewer subagent
/gather-context [topic]       # Find relevant files
/simplify [task|file|staged]  # Simplify code
/review-code [task|file|staged] # Review for bugs/vulnerabilities
/verify [task-name]           # Verify implementation matches problem
/prepare-chat [task]          # Generate files for external chat
/analyze-logs <source>        # Analyze logs (anomaly detection or problem-focused)
```

### Log Analysis Command

**Standalone usage:**
```bash
# Anomaly detection - find any issues
/analyze-logs logs/datadog-export.csv
/analyze-logs docker:api-service

# Problem-focused - investigate specific issue
/analyze-logs logs/export.csv --problem "Payment failures after 3pm"
/analyze-logs docker:cost-module-web --problem "Timeout errors on invoice endpoint"
```

**Source types:**
- File: `/analyze-logs path/to/logs.csv` (CSV from Datadog, JSON lines, plain text)
- Docker: `/analyze-logs docker:<container_name>` (uses docker logs)
- Local: `/analyze-logs local` (checks project log locations)

**Workflow integration:**
Log analysis can be invoked at various points in development workflows:

| Context | When to Use | Example |
|---------|-------------|---------|
| During `/workflow` | After manual testing in Phase 4 or 6 | "Let me check the logs" → `/analyze-logs docker:api --problem "the error we just saw"` |
| Bug investigation | As evidence gathering before fixing | `/analyze-logs logs/prod.csv --problem "Users report 500 errors"` |
| Feature validation | After implementing a feature | `/analyze-logs local --problem "New payment flow"` |
| General health check | Proactive anomaly detection | `/analyze-logs docker:api-service` |

When used within an existing workflow task:
- Results are saved to the same `tasks/<task-name>/` directory
- Report is referenced in subsequent phases (verification, summary)
- Findings inform implementation decisions

### External Chat Workflow
Use `/prepare-chat` when you want to use Claude.ai or ChatGPT for planning:

```
/prepare-chat add rate limiting to login

# Creates:
# - tasks/add-rate-limiting-to-login/chat-context.txt  (repomix output)
# - tasks/add-rate-limiting-to-login/chat-prompt.md    (prompt to paste)
# - tasks/add-rate-limiting-to-login/chat-combined.md  (instructions)

# Then:
# 1. Open chat-prompt.md, copy to external chat
# 2. Attach chat-context.txt
# 3. Save response to plan.md
# 4. Continue with /review-plan add-rate-limiting-to-login
```

### Natural Language Triggers
```
"Use workflow to [task description]"     # Full workflow
"Continue workflow"                       # Resume paused workflow
"Skip to implementation"                  # Skip planning (if plan exists)
"Review code changes"                     # Run Code Quality phase only
```

---

## Example Workflow Session

```
User: Use workflow to add rate limiting to the login endpoint

Claude: ## Problem Statement

**Current State:** The login endpoint accepts unlimited authentication
attempts, making it vulnerable to brute force attacks.

**Desired State:** The login endpoint should limit authentication
attempts to prevent brute force attacks.

**Constraints:**
- Must not break existing authentication flow
- Should use existing Redis infrastructure
- Rate limit should be configurable

**Acceptance Criteria:**
- [ ] Login attempts limited to 5 per minute per IP
- [ ] Clear error message when rate limited
- [ ] Rate limit configurable via settings
- [ ] Existing tests still pass

Do you approve this problem statement?

User: Yes, but make it 10 attempts per minute

Claude: Updated. Now gathering context...

[Uses Explore subagent to find relevant files]

## Relevant Files

### Core Files:
1. `users/api/views/auth.py` - Login endpoint
2. `meestpost_backend/settings/django.py` - Settings
3. `common/helpers/cache.py` - Redis utilities

### Related Files:
1. `users/api/serializers/auth.py` - Auth serializers
2. `common/middlewares/rate_limit.py` - Existing rate limit (if any)

### Test Files:
1. `users/tests/test_auth.py` - Auth tests

Now invoking Planner subagent...

[Planner creates detailed plan]
[Plan-Reviewer reviews and approves]

## Implementation Plan

### Overview
Add rate limiting to login endpoint using Redis-based counter.

### Step 1: Add rate limit decorator
**File:** `common/decorators/rate_limit.py`
...

Do you approve this plan?

User: Approved

Claude: Beginning implementation...

[Creates TODO list]
[Implements step by step]
[Runs Code-Simplifier]
[Runs Code-Reviewer]
[Runs Code-Goal verification]
[Runs tests]

## Implementation Complete

### Summary
Added configurable rate limiting to login endpoint.

### Files Changed
- `common/decorators/rate_limit.py` (new) - Rate limit decorator
- `users/api/views/auth.py` - Applied decorator to login
- `meestpost_backend/settings/django.py` - Added config
- `users/tests/test_auth.py` - Added rate limit tests

### Tests
- All existing tests pass
- 3 new tests added for rate limiting

### Verification
- [x] Login attempts limited to 10 per minute per IP
- [x] Clear error message when rate limited
- [x] Rate limit configurable via settings
- [x] Existing tests still pass
```

---

## Notes

- All subagents use the Task tool with appropriate `subagent_type` and `model` parameters
- User approval is required at Phase 1 (problem) and Phase 3 (plan)
- The workflow can be paused and resumed at any phase
- Task artifacts are saved to enable resumption and audit trails

## CRITICAL: Explicit Plan Approval Required

**NEVER proceed to implementation without explicit user approval of the plan.**

After presenting the plan, you MUST:
1. Ask the user explicitly: "Do you approve this plan? (yes/no)"
2. Wait for the user to respond with explicit approval (e.g., "yes", "approved", "proceed")
3. Do NOT interpret "review plan first", questions, or clarifications as approval
4. Do NOT proceed if the user says things like "let me think" or asks questions

Only proceed to Phase 4 (Implementation) when the user explicitly says one of:
- "yes" / "approved" / "proceed" / "go ahead" / "implement it"
- Or other clear affirmative response

If unclear, ask again: "Just to confirm - should I proceed with implementation?"

## CRITICAL: Plan Output Format

**Always save plans to MD files. Never dump full plans in terminal.**

When presenting a plan:
1. Create `tasks/<short-name>/` directory in current working directory
2. Save the complete plan to `tasks/<short-name>/plan.md`
3. Use short, kebab-case names (e.g., `cost-fields`, `auth-fix`, `rate-limit`)
4. In terminal, show ONLY:
   - Brief 2-3 line summary of what the plan does
   - Path to the plan file
   - "Do you approve this plan? (yes/no)"

Example terminal output:
```
## Plan Summary
Configure mandatory/optional fields for Cost Information with defaults.
4 files to modify, ~50 lines of changes.

**Full plan:** `tasks/cost-fields/plan.md`

Do you approve this plan? (yes/no)
```
