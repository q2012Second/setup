# Claude Code Workflow Configuration

This repository contains a structured AI-assisted development workflow configuration for Claude Code. It defines a multi-phase workflow with specialized subagents for planning, code review, simplification, verification, log analysis, and validation.

## Repository Structure

```
.
├── CLAUDE.md                        # Root workspace configuration
├── AGENTS.md                        # Workflow and subagent specifications
├── README.md                        # This file
├── .gitignore                       # Git ignore (includes only setup files)
├── .claude/
│   ├── commands/                    # Slash command definitions
│   │   ├── workflow.md              # Full 7-phase workflow
│   │   ├── plan.md                  # Planning subagent
│   │   ├── review-plan.md           # Plan review subagent
│   │   ├── gather-context.md        # Context gathering
│   │   ├── simplify.md              # Code simplification
│   │   ├── review-code.md           # Security-focused code review
│   │   ├── verify.md                # Implementation verification
│   │   ├── prepare-chat.md          # External chat preparation
│   │   ├── analyze-logs.md          # Log analysis (anomaly/problem-focused)
│   │   └── web-research.md          # Web research for APIs/SDKs/docs
│   └── agents/                      # Subagent prompt definitions
│       ├── problem-analyst.md       # Problem clarification & classification
│       ├── planner.md               # Implementation planning (opus)
│       ├── plan-reviewer.md         # Plan review (opus)
│       ├── context-loader.md        # File reading & trimming
│       ├── code-simplifier.md       # Code simplification (opus)
│       ├── code-reviewer.md         # Bug/vulnerability detection (opus)
│       ├── code-goal.md             # Implementation verification
│       ├── validator.md             # Test/linter execution
│       ├── test-writer.md           # Test generation
│       ├── log-analyzer.md          # Log analysis
│       ├── e2e-tester.md            # E2E testing
│       └── web-researcher.md        # External API/SDK research
└── projects/                        # Example project configurations
    ├── cost-module/
    │   └── CLAUDE.md                # FastAPI microservice config example
    └── easy-returns-service/
        └── CLAUDE.md                # Django microservice config example
```

## File Descriptions

### Root Configuration Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Root workspace configuration. Defines available projects, shared code style, and important operational notes. Entry point for multi-project workspaces. |
| `AGENTS.md` | Comprehensive workflow specification. Defines the 7-phase development workflow, subagent prompts, context management rules, checkpoint/resume capability, and task classification system. |

### Slash Commands (`.claude/commands/`)

| Command | File | Description |
|---------|------|-------------|
| `/workflow` | `workflow.md` | Full 7-phase workflow: problem clarification → context gathering → planning → implementation → code quality → verification → final review |
| `/plan` | `plan.md` | Invoke Planner subagent (opus model) to create detailed implementation plans |
| `/review-plan` | `review-plan.md` | Invoke Plan-Reviewer subagent (opus model) for architectural review |
| `/gather-context` | `gather-context.md` | Find 10-20 most relevant files for a given task |
| `/simplify` | `simplify.md` | Code-Simplifier subagent to remove complexity, find abstractions, apply idioms |
| `/review-code` | `review-code.md` | Security-focused Code-Reviewer subagent (opus model) for bugs, vulnerabilities, performance |
| `/verify` | `verify.md` | Code-Goal subagent to verify implementation matches original problem |
| `/prepare-chat` | `prepare-chat.md` | Generate context files for use with external chat interfaces (Claude.ai, ChatGPT) |
| `/analyze-logs` | `analyze-logs.md` | Log-Analyzer subagent for anomaly detection or problem-focused log analysis |
| `/web-research` | `web-research.md` | Web-Researcher subagent for external API/SDK documentation with optional GitHub source analysis |

### Subagent Definitions (`.claude/agents/`)

Standalone prompt files for each subagent. These define the agent's model, allowed tools, and prompt template.

| File | Agent | Model |
|------|-------|-------|
| `problem-analyst.md` | Problem-Analyst | sonnet |
| `planner.md` | Planner | opus |
| `plan-reviewer.md` | Plan-Reviewer | opus |
| `context-loader.md` | Context-Loader | sonnet |
| `code-simplifier.md` | Code-Simplifier | opus |
| `code-reviewer.md` | Code-Reviewer | opus |
| `code-goal.md` | Code-Goal | sonnet |
| `validator.md` | Validator | sonnet |
| `test-writer.md` | Test-Writer | sonnet |
| `log-analyzer.md` | Log-Analyzer | sonnet |
| `e2e-tester.md` | E2E-Tester | sonnet |
| `web-researcher.md` | Web-Researcher | sonnet |

### Project-Specific Configuration Examples

These are example CLAUDE.md files for specific microservices. Copy and adapt them to your project's needs.

| File | Project | Stack |
|------|---------|-------|
| `projects/cost-module/CLAUDE.md` | Cost Module | FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery |
| `projects/easy-returns-service/CLAUDE.md` | Easy Returns Service | Django 4.2, DRF, PostgreSQL, Redis, Celery |

## Workflow Overview

The workflow is designed to minimize context usage by delegating exploratory work to subagents:

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
│     ├─► Explore subagent → Find relevant files                              │
│     └─► Web-Researcher subagent → External docs/APIs (if needed)            │
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
│     └─► Validator subagent → Tests pass, linter clean                       │
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
│     ├─► Validator subagent → Run final tests                                │
│     └─► Code-Goal subagent → Verify solution matches problem                │
│                                                                             │
│  6.5. E2E TESTING (Optional)                                                │
│     └─► Run E2E tests with mock server                                      │
│                                                                             │
│  7. FINAL REVIEW                                                            │
│     └─► Present changes to user                                             │
│                                                                             │
│  [CHECKPOINT: State saved after each phase for resume capability]           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Task Classification

Tasks are classified by complexity to determine which phases to run:

| Complexity | Criteria | Phases |
|------------|----------|--------|
| **trivial** | Single file, <20 lines | 1, 4, 7 |
| **small** | 1-2 files, clear scope | 1, 2, 4, 5, 7 |
| **medium** | 3-5 files, some complexity | All phases |
| **large** | 5+ files, architectural | All + incremental batches |

### Context Management

The workflow minimizes main agent context by delegating to subagents:

| Action | Delegated To | Returns |
|--------|--------------|---------|
| Analyze problem | Problem-Analyst | Problem statement (not file contents) |
| Find files | Explore | File list (not contents) |
| Research external APIs/docs | Web-Researcher | Structured reference document |
| Read & trim files | Context-Loader | Trimmed excerpts only |
| Create/revise plan | Planner | Final plan only |
| Run tests/linters | Validator | Pass/fail verdict (not raw output) |
| Analyze logs | Log-Analyzer | Findings summary (not raw logs) |
| Review code | Code-Reviewer | Issues list only |
| Simplify code | Code-Simplifier | Suggestions only |
| Verify solution | Code-Goal | Verdict only |

**Critical rules:**
- Never read logs directly in main agent - delegate to Log-Analyzer
- Never run tests/linters directly - delegate to Validator
- Never revise plans in main context - delegate to Planner subagent
- Main agent only reads files during implementation (Phase 4)

### Checkpoint/Resume

Workflow state is saved after each phase to `tasks/<task-name>/state.json`, enabling:
- Resume interrupted workflows
- Track progress across sessions
- Audit trail of decisions

Resume with: "Continue workflow" or "Resume [task-name]"

## Usage Examples

```bash
# Full workflow for a task
/workflow add rate limiting to login endpoint

# Just planning
/plan add user notifications

# Review existing code changes
/review-code staged

# Simplify uncommitted changes
/simplify

# Verify implementation matches requirements
/verify add-rate-limiting

# Prepare files for external chat
/prepare-chat implement caching layer

# Analyze logs for anomalies
/analyze-logs logs/datadog-export.csv
/analyze-logs docker:api-service

# Analyze logs for specific problem
/analyze-logs logs/export.csv --problem "Payment failures after 3pm"
/analyze-logs docker:cost-module-web --problem "Timeout errors"

# Research external APIs/SDKs
/web-research MWL API documentation
/web-research Stripe Python SDK --repo stripe/stripe-python
```

## Key Design Principles

1. **Context Isolation**: Subagents handle exploration; main agent only reads files during implementation
2. **User Approval Gates**: Required at problem clarification and plan approval
3. **Incremental Implementation**: Large tasks processed in reviewed batches
4. **Comprehensive Review**: Both simplification and security-focused code review
5. **Verification**: Automated check that implementation matches acceptance criteria
6. **Validation Delegation**: Tests/linters run in subagent to avoid verbose output in context
7. **Log Analysis Delegation**: Logs analyzed in subagent to avoid consuming context with raw logs

## Subagents

| Subagent | Model | Purpose |
|----------|-------|---------|
| Problem-Analyst | sonnet | Explores codebase, classifies task, formulates problem statement |
| Explore | sonnet | Finds relevant files without loading contents |
| Web-Researcher | sonnet | Searches web for API/SDK docs, optionally fetches GitHub source via repomix |
| Context-Loader | sonnet | Reads files and extracts relevant excerpts for planning |
| Planner | opus | Creates and revises implementation plans |
| Plan-Reviewer | opus | Reviews plans for architecture and correctness |
| Validator | sonnet | Runs tests/linters, returns pass/fail verdicts |
| Test-Writer | sonnet | Writes tests for implemented features following project patterns |
| Code-Simplifier | opus | Identifies complexity and suggests simplifications |
| Code-Reviewer | opus | Finds bugs, vulnerabilities, performance issues |
| Code-Goal | sonnet | Verifies implementation matches problem statement |
| Log-Analyzer | sonnet | Analyzes logs for anomalies or specific problems |

## Installation

1. Clone this repository to your workspace root
2. Claude Code will automatically read `CLAUDE.md` and recognize slash commands in `.claude/commands/`
3. Use `/workflow`, `/plan`, or other commands to invoke the workflow

## Task Directory Structure

Each workflow creates a task directory with output files:

```
tasks/<task-name>/
├── state.json              # Checkpoint state for resume
├── problem.md              # Problem statement with classification
├── research-<topic>.md     # (Optional) External API/SDK research
├── plan.md                 # Implementation plan
├── plan-review.md          # Plan review feedback
├── baseline-validation.md  # Pre-implementation validation
├── simplify-review.md      # Code simplification suggestions
├── code-review.md          # Bug/vulnerability findings
├── final-validation.md     # Final tests/linter results
├── verification.md         # Goal verification results
├── summary.md              # Final summary
└── log-analysis.md         # (Optional) Log analysis report

research/                   # Cached standalone research (reusable across tasks)
└── <topic>.md
```

## Notes

- Subagent prompts use appropriate models: opus for planning/review, sonnet for analysis/validation
- Output files go to `tasks/<task-name>/` directory
- Settings files (`settings.local.json`) are excluded - they contain local configurations
- Plans are saved to files, not dumped in terminal (only summary shown)
- User approval required before implementation proceeds
