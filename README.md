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
| Problem-Analyst | sonnet | Clarify problem, define acceptance criteria |
| Test-Designer | opus | Design test cases from requirements and plan |
| Planner | opus | Create and revise implementation plans |
| Plan-Reviewer | opus | Review plans for gaps and issues |
| Codex | gpt-5.3-codex | Verify plans/code against codebase in read-only sandbox |
| Chat-Preparer | sonnet | Prepare prompts for external LLM review |
| Validator | sonnet | Run tests, linters, type checks |
| Test-Writer | sonnet | Write tests following project conventions |
| Code-Reviewer | opus | Find bugs, vulnerabilities, perf issues |
| Code-Goal | sonnet | Verify implementation matches requirements |
| E2E-Tester | sonnet | Run e2e API tests against running services |
| Web-Researcher | sonnet | Search web for docs/APIs/references |
| Log-Analyzer | sonnet | Analyze logs for anomalies |

## Skills

| Skill | Description |
|-------|-------------|
| `/workflow` | Full structured workflow (diagram above) |
| `/plan` | Create implementation plan only |
| `/review-plan` | Review an existing plan |
| `/review-code` | Review code using Codex + Code-Reviewer |
| `/verify` | Verify implementation matches requirements |
| `/gather-context` | Find relevant files for a task |
| `/prepare-chat` | Prepare prompt for external LLM |
| `/analyze-logs` | Analyze logs for anomalies |
| `/web-research` | Search web for documentation |
