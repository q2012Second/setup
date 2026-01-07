---
description: Analyze logs for anomalies or investigate a specific problem
argument-hint: <source> [--problem "description"]
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Log Analysis

Analyze logs to detect anomalies or investigate specific problems using the Log-Analyzer subagent.

## Input
$ARGUMENTS

## Modes

### 1. Anomaly Detection (default)
```
/analyze-logs logs/export.csv
/analyze-logs docker:api-service
/analyze-logs local
```
Scans logs for any errors, warnings, anomalies, or patterns that indicate problems.

### 2. Problem-Focused Analysis
```
/analyze-logs logs/export.csv --problem "Orders failing after payment"
/analyze-logs docker:api-service --problem "Authentication timeout errors"
```
Targeted analysis searching for evidence related to a specific issue.

---

## Source Types

### File (CSV or plain text)
```
/analyze-logs path/to/logs.csv
/analyze-logs /tmp/server.log
```
- Reads file directly
- Auto-detects format (CSV, JSON lines, plain text)
- For CSV: parses columns, typically from Datadog exports

### Docker Container
```
/analyze-logs docker:<container_name>
/analyze-logs docker:easy-returns-api
/analyze-logs docker:cost-module-web
```
- Uses `docker logs` or `docker compose logs`
- Check project's docker-compose.yml for service names
- Retrieves recent logs (last 1000 lines by default)

### Local Server
```
/analyze-logs local
/analyze-logs local:<port>
```
- Checks common log locations for the project
- May need project-specific configuration
- Look in: `logs/`, `*.log`, stdout if running in foreground

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
# Create task directory
mkdir -p tasks/<task-name>/
```

---

## Instructions

### For File Source:
1. Verify file exists
2. Read first 50 lines to detect format
3. Pass file path to Log-Analyzer subagent

### For Docker Source:
1. Check if container is running: `docker ps | grep <container>`
2. If using docker-compose, check project's docker-compose.yml for service name
3. Fetch logs: `docker logs <container> --tail 2000 2>&1` or `docker compose logs <service> --tail 2000`
4. Pass log content to subagent

### For Local Source:
1. Check project's common log locations
2. Check for running process on specified port
3. Gather available logs
4. Pass to subagent

---

## Spawn Log-Analyzer Subagent

Use Task tool with model=sonnet:

```
You are a log analysis specialist. Your job is to analyze logs and identify issues, anomalies, or evidence related to specific problems.

## Analysis Mode
{mode}

## Problem Context (if problem-focused)
{problem_description}

## Log Source
Source type: {source_type}
Source: {source_identifier}

## Log Content
{log_content_or_file_path}

## Project Context
This is the {project_name} project. Key areas to look for:
- {project-specific hints from CLAUDE.md}

## Your Task

### Step 1: Detect Log Format
Examine the logs to understand:
- Format (CSV columns, JSON, plain text)
- Available fields (timestamp, level, message, service)
- Log levels used

### Step 2: Analyze Based on Mode

**Anomaly Detection:**
- Categorize ERROR/WARN/CRITICAL entries
- Find patterns and recurring issues
- Detect anomalies (spikes, unusual sequences)
- Build timeline of significant events

**Problem-Focused:**
- Search for entries related to the problem
- Reconstruct timeline leading to issue
- Find correlating entries
- Identify root cause indicators

### Step 3: Cross-Reference Codebase
For interesting log messages:
- Search codebase to find source location
- Understand the code path
- Add file:line references to findings

### Step 4: Generate Report
Use the standard Log Analysis Report format from AGENTS.md
```

---

## Output

Save subagent's report to: `tasks/<task-name>/log-analysis.md`

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

---

## Integration with Workflows

This command can be used:

1. **Standalone**: Direct log analysis anytime
2. **During /workflow**: After manual testing in Phase 4 or Phase 6
3. **Bug investigation**: As evidence gathering step

When called from another workflow:
- Results saved to same task directory
- Report referenced in subsequent phases
