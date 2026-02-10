---
description: Search web for docs/APIs/SDKs and save as reference
argument-hint: <topic> [--repo user/repo] [--output path/to/file.md]
allowed-tools: Task, WebSearch, WebFetch, Write, Read, Bash
---

# Web Research

Search the web for documentation, APIs, SDKs, and technical references, then save as a reusable reference file. Optionally fetch and pack GitHub source code using repomix.

## Input
$ARGUMENTS

## Usage Examples

```bash
# Basic research - saves to research/<topic>.md
/web-research NexHealth API

# With specific output path
/web-research Twilio Voice SDK --output research/twilio-voice.md

# Research + fetch GitHub source code
/web-research LiveKit Python SDK --repo livekit/python-sdks

# Auto-detect repo from topic (searches GitHub)
/web-research openai-python --repo auto

# Full example
/web-research LiveKit Agents --repo livekit/agents --output tasks/voice-agent/livekit-agents.md
```

---

## Parse Input

1. **Extract topic**: Everything before flags (--output, --repo, --branch)
2. **Extract flags**:
   - `--output <path>`: Custom output path (default: `research/<topic-slug>.md`)
   - `--repo <user/repo|url|auto>`: GitHub repo to fetch source code
   - `--branch <name>`: Specific branch/tag/commit (default: main branch)
3. **Create output directory** if needed: `mkdir -p <parent-dir>`

---

## Instructions

### Step 1: Setup

```bash
mkdir -p research/
```

### Step 2: Fetch GitHub Source (if --repo specified)

If `--repo` flag is provided:

1. **If `--repo auto`**: Search for GitHub repo first
2. **Run repomix to fetch and pack the repo**:
   ```bash
   repomix --remote <user/repo> \
     --remote-branch <branch> \
     --style markdown \
     --compress \
     --output research/.repomix-cache/<repo-name>.md
   ```

### Step 3: Spawn Web-Researcher Agent

Spawn **Web-Researcher** agent (Task tool):
- Use agent defined in `~/.claude/agents/web-researcher.md`
- model: sonnet

```
Task tool parameters:
- subagent_type: "Web-Researcher"
- model: "sonnet"
- prompt: |
    ## Research Topic
    [topic]

    ## Specific Questions (if any)
    [questions extracted from topic]

    ## Source Code Context (if repo was fetched)
    [repomix output - packed source code from GitHub]

    Research this topic following your guidelines.
```

### Step 4: Save Results

1. Receive markdown content from agent
2. Write to specified output path
3. Optionally keep repomix cache for future reference
4. Report completion

---

## Output

### Terminal Output
```
## Web Research Complete

**Topic:** [topic]
**Saved to:** `[output-path]`
**Sources consulted:** [count] pages
**Repository:** [user/repo] (if fetched)

### Summary
[2-3 sentence summary of what was found]
```

---

## Repomix Options Reference

```bash
# Basic remote fetch
repomix --remote user/repo

# Specific branch/tag
repomix --remote user/repo --remote-branch v2.0.0

# Compressed output
repomix --remote user/repo --compress

# Focus on specific directories
repomix --remote user/repo --include "src/**,lib/**,examples/**"
```

---

## Directory Structure

Default location for standalone research:
```
research/
├── nexhealth-api.md
├── twilio-voice-sdk.md
└── .repomix-cache/
    └── livekit-python-sdks.md
```
