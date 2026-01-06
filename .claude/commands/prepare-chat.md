---
description: Prepare context and prompt files for external chat (Claude.ai, ChatGPT) to generate or review a plan
argument-hint: [task description]
allowed-tools: Task, Read, Glob, Grep, Bash, Write
---

# Prepare Chat Prompt

Generate context and prompt files for use in external chat interfaces.

## Task
$ARGUMENTS

## Setup

1. **Derive task name** (kebab-case from description)
2. **Create task directory**: `mkdir -p tasks/<task-name>/`

## Instructions

### Step 1: Gather Relevant Files

1. Use Explore subagent to find 10-20 most relevant files for the task
2. List the files to include in repomix

### Step 2: Generate Context with Repomix

Run repomix to create the context file:

```bash
repomix -o tasks/<task-name>/chat-context.txt --include "file1.py,file2.py,..."
```

**Important repomix notes:**
- Use relative paths from workspace root (e.g., `easy-returns-service/parcels/models/parcel.py`)
- Comma-separated, no spaces
- Output goes to task directory

### Step 3: Generate Prompt File

Create `tasks/<task-name>/chat-prompt.md` with the following structure:

```markdown
# Task: [Task Name]

## Problem Statement
[Reformulated problem description]

## Current State
[What exists now - based on codebase exploration]

## Desired State
[What should exist after implementation]

## Constraints
- Follow existing patterns in the codebase
- Minimize changes while fully solving the problem
- Consider edge cases and error handling
- [Any task-specific constraints]

## Codebase Context
The attached file `chat-context.txt` contains the relevant source code.

Key files included:
1. `path/to/file1.py` - [Why it's relevant]
2. `path/to/file2.py` - [Why it's relevant]
...

## Your Task
Create a detailed, step-by-step implementation plan that:

1. **Follows existing patterns** - Match the coding style and architecture in the context
2. **Is specific** - Include exact file paths, function names, and code snippets
3. **Handles edge cases** - Consider what could go wrong
4. **Includes testing** - Define test cases for the implementation

## Expected Output Format

```
# Implementation Plan: [Task Name]

## Overview
[Brief description]

## Prerequisites
- [Any setup needed]

## Implementation Steps

### Step 1: [Title]
**File:** `path/to/file.py`
**Changes:**
- [Specific change]

**Code:**
\`\`\`python
# Code snippet
\`\`\`

### Step 2: [Title]
...

## Testing Strategy
- [ ] [Test case 1]
- [ ] [Test case 2]

## Edge Cases
- [Edge case]: [How it's handled]

## Risks & Mitigations
- **Risk:** [Description]
  **Mitigation:** [Solution]
```
```

### Step 4: Create Combined File (Optional)

For convenience, create `tasks/<task-name>/chat-combined.md` that includes both the prompt and instructions for attaching context:

```markdown
[Contents of chat-prompt.md]

---

## Instructions for Use

1. Copy this entire prompt
2. Attach `chat-context.txt` as a file (or paste its contents if the chat doesn't support attachments)
3. Send to Claude.ai or ChatGPT
4. Save the response to `tasks/<task-name>/plan.md`
```

## Output Files

After running this command, the task directory will contain:

```
tasks/<task-name>/
├── chat-context.txt    # Repomix output with source code
├── chat-prompt.md      # Prompt to paste into chat
└── chat-combined.md    # Combined instructions + prompt
```

## Usage

1. Run: `/prepare-chat add rate limiting to login endpoint`
2. Open `tasks/add-rate-limiting-to-login/chat-prompt.md`
3. Copy prompt to Claude.ai/ChatGPT
4. Attach `chat-context.txt` or paste its contents
5. Get the plan response
6. Save response to `tasks/add-rate-limiting-to-login/plan.md`
7. Continue with `/review-plan add-rate-limiting-to-login`
