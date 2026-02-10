---
description: Prepare context and prompt files for external chat (Claude.ai, ChatGPT) to generate or review a plan
argument-hint: [task description or "review plan for <task-name>"]
allowed-tools: Task
---

# Prepare Chat Prompt

Generate context and prompt files for use in external chat interfaces.

## Task
$ARGUMENTS

## Instructions

**Context Rule:** Do NOT read files or run commands directly. Delegate all work to Chat-Preparer subagent.

### Determine Mode

1. If task starts with "review plan" or "review <task-name>":
   - Mode: "plan-review"
   - Extract task name from arguments
   - Task directory: `tasks/<task-name>/`

2. Otherwise:
   - Mode: "plan-generation"
   - Derive task name (kebab-case from description)
   - Create task directory: `mkdir -p tasks/<task-name>/`

### Spawn Chat-Preparer Subagent

Use the Task tool with:
- `subagent_type`: "general-purpose"
- `model`: "sonnet"
- `prompt`: Include the Chat-Preparer agent instructions from `~/.claude/agents/chat-preparer.md` along with:
  - Task description or plan to review
  - Task directory path
  - Mode ("plan-generation" or "plan-review")

Example prompt for the subagent:

```
You are the Chat-Preparer agent. Your job is to prepare context and prompts for external LLM chat.

[Include full agent instructions from chat-preparer.md]

## Your Input

**Mode:** [plan-generation|plan-review]
**Task Directory:** tasks/<task-name>/
**Task:** [description or "review plan"]

Execute the steps and create all required files.
```

### Report Results

After subagent completes, inform user:

**For plan-generation:**
```
Chat files ready in `tasks/<task-name>/`:

1. Copy `chat-prompt.md` to Claude.ai/ChatGPT
2. Attach `chat-context.txt`
3. Save response to `tasks/<task-name>/plan.md`
4. Then run `/review-plan <task-name>`
```

**For plan-review:**
```
Chat files ready in `tasks/<task-name>/`:

1. Copy `chat-prompt.md` to Claude.ai/ChatGPT
2. Attach `chat-context.txt`
3. Paste response into `tasks/<task-name>/external-review.md`
4. Then say "continue workflow" to resume
```

## Output Files

```
tasks/<task-name>/
├── chat-context.txt    # Repomix output with source code
├── chat-prompt.md      # Prompt to paste into chat
├── chat-combined.md    # Combined instructions + prompt
└── external-review.md  # Placeholder for review response (plan-review mode only)
```
