---
description: Sync global ~/.claude agents and commands into this repo (global is source of truth)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Sync Global Agents & Skills

Copy global `~/.claude/agents/` and `~/.claude/commands/` into this repo's `.claude/` directory, then regenerate the Agents and Skills tables in `README.md`.

Global is the source of truth — this repo is just a versioned copy.

**IMPORTANT:** Never modify global files. Only copy global → local.

## Local-Only Files

These files exist only in this repo and are NOT synced from global:
- `.claude/commands/sync-global.md` (this skill)

## Instructions

### Step 1: Compare & Sync Agents

1. List global: `ls ~/.claude/agents/*.md`
2. List local: `ls .claude/agents/*.md`
3. For each global file, compare with local using `diff`
4. Track: added, updated, unchanged, removed (local files not in global)
5. Copy all new/updated files from global → local
6. Delete local agent files that no longer exist in global

### Step 2: Compare & Sync Commands

1. List global: `ls ~/.claude/commands/*.md`
2. List local: `ls .claude/commands/*.md`
3. For each global file, compare with local using `diff`
4. Track: added, updated, unchanged, removed (local files not in global)
5. Copy all new/updated files from global → local
6. Delete local command files that no longer exist in global
7. **Skip local-only files** listed above — do not delete them

### Step 3: Regenerate README Tables

After syncing, rebuild the **Agents** and **Skills** tables in `README.md`:

1. **Agents table** — for each `.claude/agents/*.md`, read the YAML frontmatter to extract `name`, `model`, and `description`. Rebuild the table between `## Agents` and `## Skills`:
   ```
   | Agent | Model | Purpose |
   |-------|-------|---------|
   | {name} | {model} | {description} |
   ```
   Keep the existing Codex row (`| Codex | gpt-5.3-codex | Verify plans/code against codebase in read-only sandbox |`) — it has no agent file.
   Sort alphabetically by name.

2. **Skills table** — for each `.claude/commands/*.md`, read the YAML frontmatter to extract the filename (as `/filename`) and `description`. Rebuild the table after `## Skills`:
   ```
   | Skill | Description |
   |-------|-------------|
   | `/filename` | {description} |
   ```
   Sort alphabetically by skill name.

Use the Edit tool to replace the old tables in-place.

**If anything is unclear** (e.g., a new agent doesn't fit the existing README structure, the README has extra content beyond the tables that might need updating, or an agent/skill was renamed in a way that affects the workflow diagram), use **AskUserQuestion** to clarify before making changes.

### Step 4: Report

```
## Sync Results

### Agents
- Added: [list or "none"]
- Updated: [list or "none"]
- Removed: [list or "none"]
- Unchanged: [count]

### Commands (Skills)
- Added: [list or "none"]
- Updated: [list or "none"]
- Removed: [list or "none"]
- Unchanged: [count]
- Skipped (local-only): sync-global.md

### README
- Agents table: [regenerated / no changes]
- Skills table: [regenerated / no changes]
```
