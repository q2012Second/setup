# Meest Project Workspace

This is the root workspace for the Meest project containing multiple interconnected services.

## CRITICAL: Prefer Subagents

**Use subagents proactively and aggressively.** Subagents keep main context clean and provide specialized capabilities.

| When | Use This |
|------|----------|
| Exploring codebase | Task tool with `subagent_type="Explore"` |
| Clarifying problem/task | Problem-Analyst subagent (sonnet) |
| Need external docs/API info | `/web-research` - Web-Researcher subagent (sonnet) |
| Loading file context | Context-Loader subagent (sonnet) |
| Planning implementation | `/plan` - Planner subagent (opus) |
| Reviewing a plan | `/review-plan` - Plan-Reviewer subagent (opus) |
| Simplifying code | `/simplify` - Code-Simplifier subagent (opus) |
| Reviewing code | `/review-code` - Code-Reviewer subagent (opus) |
| Verifying solution | `/verify` - Code-Goal subagent (sonnet) |
| Running tests/linters | Validator subagent (sonnet) |
| Writing tests | Test-Writer subagent (sonnet) |
| Analyzing logs | `/analyze-logs` - Log-Analyzer subagent (sonnet) |

**Default behavior:** If a task can be handled by a subagent, use the subagent. Don't do exploratory work in main context.

---

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
| `/web-research <topic> [--repo]` | Search web + optionally fetch GitHub source via repomix |

### Workflow Phases
1. Problem clarification (requires approval) - Task classification for phase skipping
2. Context gathering (skip for trivial tasks)
2.5. Context loading (skip for trivial/small tasks)
3. Planning with subagent review (requires approval, skip for trivial/small)
3.5. Pre-implementation validation
4. Implementation (incremental batches for large tasks)
5. Code quality review
6. Verification and testing (skip for trivial)
6.5. E2E testing (conditional - if flagged by Problem-Analyst)
7. Final review

### Subagent Prompts
Detailed prompts for each subagent are in `AGENTS.md` under "Subagent Specifications" section

### Proactive Web Research

**Use `/web-research` automatically when:**
- User asks about an API, SDK, or library you're not confident about
- Task requires integrating with external services (MWL, Portmone, Stripe, etc.)
- You need current documentation (your knowledge may be outdated)
- User asks "how do I use X" for an external technology

**Examples:**
```
User: "How do I integrate with MWL API?"
→ Run /web-research MWL API documentation
→ Then answer based on researched docs

User: "Add Stripe checkout to the service"
→ During context gathering, run /web-research Stripe Python SDK --repo stripe/stripe-python
→ Use research in planning phase
```

**Research files are cached** in `research/` directory. Check for existing research before spawning new searches.

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

- **CRITICAL: No workflow terminology in code** - Never include workflow implementation details (chunk, batch, phase, step numbers, task references) in code, comments, variable names, or test file names. All code artifacts must reference only business domain entities or technical concepts. Workflow state files in `tasks/` are exempt.
- NEVER make assumptions about the codebase - use search tools
- Use pytest/tox for testing
- Mock external services in tests
- Follow existing patterns and conventions
- Use `poetry run python` or activate poetry shell first
- **Keep this file updated**: When discovering new commands, solutions to problems, or operational knowledge not documented here, add them to this file immediately so the knowledge persists across sessions
- **Docker daemon**: If any task requires Docker and the daemon is not running, STOP and ask the user to start Docker daemon before proceeding
- **Keep files consistent**: If requirements change after files were created (e.g., plan.md), those files MUST be updated immediately to reflect the new requirements. All output files must stay consistent with current requirements at every point during work
- **No context.md files**: Do NOT create context.md files unless the user explicitly asks for one
