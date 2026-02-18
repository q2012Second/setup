# Claude Code Setup

Custom agents and skills for Claude Code.

## Workflow Diagram

```mermaid
flowchart TD
    START(["/workflow task description"]) --> P1

    subgraph "Phase 1 — Problem"
        P1[Problem-Analyst] --> problem.md
        problem.md --> USER1{User Approval}
    end

    USER1 -->|Approved| P15

    subgraph "Phase 1.5 — Test Design"
        P15[Test-Designer<br><i>from requirements</i>]
    end

    P15 --> P2

    subgraph "Phase 2 — Planning"
        P2[Planner<br><i>explores codebase</i>] --> CDX["Codex (read-only sandbox)<br><i>verify plan vs codebase</i>"]
        CDX --> TRIAGE1[Main Agent<br><i>triage Codex findings</i>]
        TRIAGE1 --> P2R{Plan-Reviewer}
        P2R -->|Both approve| EXT
        P2R -->|Needs Revision| P2

        EXT[Chat-Preparer<br><i>generate prompt</i>] --> USER2{User sends to<br>external LLM}
        USER2 --> ANAL[Planner<br><i>analyze external review</i>]
        ANAL --> CDX2["Codex (read-only sandbox)"]
        CDX2 --> TRIAGE2[Main Agent<br><i>triage Codex findings</i>]
        TRIAGE2 --> P2R2{Plan-Reviewer}
        P2R2 -->|Both approve| USER3{User Approval}
        P2R2 -->|Needs Revision| P2
    end

    USER3 -->|Approved| P25

    subgraph "Phase 2.5+ — Pre-Implementation"
        P25[Validator<br><i>baseline check</i>] --> P27[Test-Designer<br><i>from plan</i>]
    end

    P27 --> P3

    subgraph "Phase 3 — Implementation"
        P3[Implement plan steps] --> TESTS[Test-Writer]
    end

    TESTS --> P4

    subgraph "Phase 4 — Code Quality"
        P4CDX["Codex (read-only sandbox)<br><i>review changes</i>"] --> P4TRI[Main Agent<br><i>triage Codex findings</i>]
        P4TRI --> P4CR[Code-Reviewer]
        P4CR -->|Issues found| FIX[Fix issues] --> P4CDX
        P4CR -->|Clean| DONE4[✓]
    end

    DONE4 --> P5

    subgraph "Phase 5 — Verification"
        P5[Validator<br><i>final check</i>] --> P5G[Code-Goal<br><i>requirements met?</i>]
    end

    P5G --> P6

    subgraph "Phase 6 — Summary"
        P6[Generate summary.md]
    end

    P6 --> END([Done])

    style START fill:#4a9eff,color:#fff
    style END fill:#22c55e,color:#fff
    style USER1 fill:#f59e0b,color:#fff
    style USER2 fill:#f59e0b,color:#fff
    style USER3 fill:#f59e0b,color:#fff
```

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| Chat-Preparer | sonnet | Prepare context and prompts for external LLM chat (Claude.ai, ChatGPT) |
| Code-Goal | sonnet | Verify that implementation solves the original problem |
| Code-Reviewer | opus | Find bugs, vulnerabilities, performance issues, over-engineering, and style violations in code |
| Codex | gpt-5.3-codex | Verify plans/code against codebase in read-only sandbox |
| Log-Analyzer | sonnet | Analyze logs to detect anomalies, errors, and investigate specific problems |
| Plan-Reviewer | opus | Review implementation plans from an architecture standpoint |
| Planner | opus | Create or revise implementation plans from problem statements and codebase context |
| Problem-Analyst | sonnet | Explore codebase to understand current state and formulate a clear problem statement |
| Test-Designer | opus | Design test cases from requirements and implementation plans |
| Test-Writer | sonnet | Write tests for implemented features, following existing test patterns in the codebase |
| Validator | sonnet | Run tests, linters, type checks, and other validation commands |
| Web-Researcher | sonnet | Search the web for documentation, APIs, SDKs, and technical references |

## Skills

| Skill | Description |
|-------|-------------|
| `/analyze-logs` | Analyze logs for anomalies or investigate a specific problem |
| `/gather-context` | Gather codebase context by finding relevant files for a task |
| `/plan` | Create an implementation plan using the Planner subagent (opus model) |
| `/prepare-chat` | Prepare context and prompt files for external chat (Claude.ai, ChatGPT) to generate or review a plan |
| `/review-code` | Review code for bugs, vulnerabilities, and performance issues using Codex + Code-Reviewer subagent (opus model) |
| `/review-plan` | Review an implementation plan using the Plan-Reviewer subagent (opus model) |
| `/sync-global` | Sync global ~/.claude agents and commands into this repo (global is source of truth) |
| `/verify` | Verify that implementation solves the original problem using the Code-Goal subagent |
| `/web-research` | Search web for docs/APIs/SDKs and save as reference |
| `/workflow` | Run the full structured workflow for a task (problem clarification, planning, implementation, review, verification) |
