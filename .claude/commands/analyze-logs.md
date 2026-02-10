---
description: Analyze logs for anomalies or investigate a specific problem
argument-hint: <source> [--problem "description"]
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Log Analysis

Analyze logs to detect anomalies or investigate specific problems using the Log-Analyzer agent.

## Input
$ARGUMENTS

## Modes

### 1. Anomaly Detection (default)
```
/analyze-logs logs/export.csv
/analyze-logs docker:<service>
/analyze-logs local
```
Scans logs for any errors, warnings, anomalies, or patterns that indicate problems.

### 2. Problem-Focused Analysis
```
/analyze-logs logs/export.csv --problem "Orders failing after payment"
/analyze-logs docker:<service> --problem "Authentication timeout errors"
```
Targeted analysis searching for evidence related to a specific issue.

---

## Source Types

### File (CSV or plain text)
```
/analyze-logs path/to/logs.csv
/analyze-logs /tmp/server.log
```

### Docker Container
```
/analyze-logs docker:<container_name>
/analyze-logs docker:<service>
```
Check project's CLAUDE.md for specific service/container names.

### Local Server
```
/analyze-logs local
/analyze-logs local:<port>
```

---

## Parse Input

1. **Extract source**: First argument (required)
   - If starts with `docker:` → Docker container
   - If `local` or `local:` → Local server logs
   - Otherwise → File path

2. **Extract problem**: Look for `--problem "..."` or `--problem '...'`
   - If present → Problem-Focused mode
   - If absent → Anomaly Detection mode

3. **Derive task name**:
   - From problem description if present: `logs-<kebab-case-problem>`
   - Otherwise: `logs-<source-identifier>`

---

## Setup

```bash
mkdir -p tasks/<task-name>/
```

---

## CRITICAL: Context Rule

**Main agent does NOT read logs directly.** Only:
1. Determine log source and mode
2. Spawn Log-Analyzer agent
3. Receive summary report (NOT raw log content)

The agent reads and parses logs in its isolated context.

---

## Instructions

### For File Source:
1. Verify file exists
2. Pass file path to Log-Analyzer agent (do NOT read file content)

### For Docker Source:
1. Check if container is running: `docker ps | grep <container>`
2. Tell agent to fetch logs: `docker logs <container> --tail 2000 2>&1`

### For Local Source:
1. Check project's common log locations
2. Tell agent to gather available logs

---

## Agent Invocation

Spawn **Log-Analyzer** agent (Task tool):
- Use agent defined in `~/.claude/agents/log-analyzer.md`
- model: sonnet

```
Task tool parameters:
- subagent_type: "Log-Analyzer"
- model: "sonnet"
- prompt: |
    ## Analysis Mode
    [anomaly | problem-focused]

    ## Problem Context (if problem-focused)
    [problem description]

    ## Log Source
    Source type: [file | docker | local]
    Source: [path or container name]

    ## Project Context
    Check the project's CLAUDE.md for service names and log locations.

    Analyze the logs following your guidelines.
```

---

## Output

Save agent's report to: `tasks/<task-name>/log-analysis.md`

### Terminal Output
```
## Log Analysis Complete

**Source:** [source description]
**Mode:** [Anomaly Detection / Problem-Focused]
**Findings:** X critical, Y high, Z medium issues

**Full report:** `tasks/<task-name>/log-analysis.md`

### Key Findings
- [Top 3-5 findings summary]

### Recommended Actions
- [Top actions to take]
```
