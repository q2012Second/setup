# Meest Project Workspace

This is the root workspace for the Meest project containing multiple interconnected services.

## Workflow

For complex tasks, use the structured Claude Code workflow defined in `AGENTS.md`.

### Slash Commands

| Command | Description |
|---------|-------------|
| `/workflow [task]` | Full 7-phase workflow (problem → plan → implement → review → verify) |
| `/plan [task]` | Create implementation plan using Planner subagent (opus) |
| `/review-plan [plan.md]` | Review plan using Plan-Reviewer subagent (opus) |
| `/gather-context [topic]` | Find 10-20 relevant files for a topic |
| `/simplify [file\|staged]` | Simplify code using Code-Simplifier subagent |
| `/review-code [file\|staged]` | Review code for bugs/vulnerabilities (opus) |
| `/verify [problem]` | Verify implementation solves the problem |
| `/prepare-chat [task]` | Generate context + prompt files for external chat (Claude.ai/ChatGPT) |
| `/analyze-logs <source>` | Analyze logs for anomalies or specific problems |

### Workflow Phases
1. Problem clarification (requires approval)
2. Context gathering
3. Planning with subagent review (requires approval)
4. Implementation
5. Code quality review
6. Verification and testing

### Subagent Prompts
Detailed prompts for each subagent are in `AGENTS.md` under "Subagent Specifications" section

---

## Available Projects

| Project | Location | Description |
|---------|----------|-------------|
| Easy Returns Service | `easy-returns-service/` | Django microservice for parcel returns, carrier integration, pricing, payments |
| Cost Module | `cost-module/` | FastAPI microservice for invoice processing, cost calculation, financial data |

Each project has its own `CLAUDE.md` with detailed structure, commands, and configuration.

---

## Code Style (Shared)

- Python 3.12 with type hints
- 4 spaces indentation, 120 char line length
- Use ruff for formatting/linting (rules: E, F, UP, B, SIM, I)
- Use `poetry run` prefix for all commands
- Coverage target: 80%+

---

## Important Notes

- NEVER make assumptions about the codebase - use search tools
- Use pytest/tox for testing
- Mock external services in tests
- Follow existing patterns and conventions
- Use `poetry run python` or activate poetry shell first
- **Keep this file updated**: When discovering new commands, solutions to problems, or operational knowledge not documented here, add them to this file immediately so the knowledge persists across sessions
- **Docker daemon**: If any task requires Docker and the daemon is not running, STOP and ask the user to start Docker daemon before proceeding
- **Keep files consistent**: If requirements change after files were created (e.g., plan.md), those files MUST be updated immediately to reflect the new requirements. All output files must stay consistent with current requirements at every point during work
- **No context.md files**: Do NOT create context.md files unless the user explicitly asks for one
