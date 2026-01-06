# Claude Code Workflow Configuration

This repository contains a structured AI-assisted development workflow configuration for Claude Code. It defines a multi-phase workflow with specialized subagents for planning, code review, simplification, and verification.

## Repository Structure

```
.
├── CLAUDE.md                        # Root workspace configuration
├── AGENTS.md                        # Workflow and subagent specifications
├── README.md                        # This file
├── .gitignore                       # Git ignore (includes only setup files)
├── .claude/
│   └── commands/                    # Slash command definitions
│       ├── workflow.md              # Full 7-phase workflow
│       ├── plan.md                  # Planning subagent
│       ├── review-plan.md           # Plan review subagent
│       ├── gather-context.md        # Context gathering
│       ├── simplify.md              # Code simplification
│       ├── review-code.md           # Security-focused code review
│       ├── verify.md                # Implementation verification
│       └── prepare-chat.md          # External chat preparation
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

### Project-Specific Configuration Examples

These are example CLAUDE.md files for specific microservices. Copy and adapt them to your project's needs.

| File | Project | Stack |
|------|---------|-------|
| `projects/cost-module/CLAUDE.md` | Cost Module | FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery |
| `projects/easy-returns-service/CLAUDE.md` | Easy Returns Service | Django 4.2, DRF, PostgreSQL, Redis, Celery |

## Workflow Overview

The workflow is designed to minimize context usage by delegating exploratory work to subagents:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│  1. PROBLEM CLARIFICATION → Problem-Analyst subagent            │
│  2. CONTEXT GATHERING     → Explore subagent (file list)        │
│  2.5. CONTEXT LOADING     → Context-Loader subagent (trimmed)   │
│  3. PLANNING              → Planner + Plan-Reviewer (opus)      │
│  3.5. PRE-IMPLEMENTATION  → Validation checks                   │
│  4. IMPLEMENTATION        → Main agent (only phase reading)     │
│  5. CODE QUALITY          → Simplifier + Reviewer subagents     │
│  6. VERIFICATION          → Code-Goal subagent                  │
│  7. FINAL REVIEW          → Summary presentation                │
└─────────────────────────────────────────────────────────────────┘
```

### Task Classification

Tasks are classified by complexity to determine which phases to run:

| Complexity | Criteria | Phases |
|------------|----------|--------|
| **trivial** | Single file, <20 lines | 1 → 4 → 5 → 7 |
| **small** | 1-2 files, clear scope | 1 → 2 → 4 → 5 → 7 |
| **medium** | 3-5 files, some complexity | All phases |
| **large** | 5+ files, architectural | All + incremental batches |

### Checkpoint/Resume

Workflow state is saved after each phase to `tasks/<task-name>/state.json`, enabling:
- Resume interrupted workflows
- Track progress across sessions
- Audit trail of decisions

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
```

## Key Design Principles

1. **Context Isolation**: Subagents handle exploration; main agent only reads files during implementation
2. **User Approval Gates**: Required at problem clarification and plan approval
3. **Incremental Implementation**: Large tasks processed in reviewed batches
4. **Comprehensive Review**: Both simplification and security-focused code review
5. **Verification**: Automated check that implementation matches acceptance criteria

## Installation

1. Clone this repository to your workspace root
2. Claude Code will automatically read `CLAUDE.md` and recognize slash commands in `.claude/commands/`
3. Use `/workflow`, `/plan`, or other commands to invoke the workflow

## Notes

- Subagent prompts use appropriate models: opus for planning/review, sonnet for analysis
- Output files go to `tasks/<task-name>/` directory
- Settings files (`settings.local.json`) are excluded - they contain local configurations
