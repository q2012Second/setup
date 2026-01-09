# Context Flow Diagram

This document explains how context is managed in the Claude Code workflow - what stays in the main agent, what's handled by subagents, and how user responses affect context.

---

## Main Agent Context

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           MAIN AGENT CONTEXT                                        │
│                                                                                     │
│  ACCUMULATES (persists across conversation):                                        │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │ • User messages (all requests, feedback, approvals)                        │    │
│  │ • Tool call results (Read, Edit, Bash outputs)                             │    │
│  │ • Subagent FINAL responses (summaries only, not their internal work)       │    │
│  │ • Files read during Phase 4 implementation                                 │    │
│  │ • Git diff outputs                                                         │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  DOES NOT ACCUMULATE (stays in subagent):                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │ • File contents from exploration (Phase 1, 2, 2.5)                         │    │
│  │ • Web search results and page contents                                     │    │
│  │ • Raw test/linter output                                                   │    │
│  │ • Raw log file contents                                                    │    │
│  │ • Plan revision iterations (only final plan returns)                       │    │
│  │ • Code review internal analysis                                            │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Context Flow by Phase

```
USER                          MAIN AGENT                      SUBAGENT
  │                               │                               │
  │  "Add Stripe payments"        │                               │
  │──────────────────────────────►│                               │
  │                               │                               │
  │     [User message saved       │  Spawn Problem-Analyst        │
  │      to main context]         │──────────────────────────────►│
  │                               │                               │
  │                               │                               │ Explores codebase
  │                               │                               │ (reads 20+ files)
  │                               │                               │ [stays in subagent]
  │                               │                               │
  │                               │◄──────────────────────────────│
  │                               │  Returns: Problem statement   │
  │                               │  (2KB summary, not 50KB files)│
  │                               │                               │
  │                               │  Spawn Web-Researcher         │
  │                               │──────────────────────────────►│
  │                               │                               │
  │                               │                               │ Web searches (5+)
  │                               │                               │ Fetches pages (10+)
  │                               │                               │ Reads repo via repomix
  │                               │                               │ [stays in subagent]
  │                               │                               │
  │                               │◄──────────────────────────────│
  │                               │  Returns: Research doc        │
  │                               │  (saved to research/*.md)     │
  │                               │                               │
  │  "Approved"                   │                               │
  │──────────────────────────────►│                               │
  │                               │                               │
  │     [Approval saved           │  Spawn Planner (opus)         │
  │      to main context]         │──────────────────────────────►│
  │                               │   Prompt includes:            │
  │                               │   - Problem statement         │
  │                               │   - Trimmed context           │
  │                               │   - Research doc              │
  │                               │                               │
  │                               │◄──────────────────────────────│
  │                               │  Returns: Implementation plan │
  │                               │  (saved to plan.md)           │
  │                               │                               │
  │  "Change to use webhooks"     │                               │
  │──────────────────────────────►│                               │
  │                               │                               │
  │     [Feedback saved           │  Spawn Planner (revision)     │
  │      to main context]         │──────────────────────────────►│
  │                               │   Prompt includes:            │
  │                               │   - Current plan              │
  │                               │   - User feedback             │
  │                               │                               │
  │                               │                               │ Revises plan
  │                               │                               │ (iterations stay
  │                               │                               │  in subagent)
  │                               │                               │
  │                               │◄──────────────────────────────│
  │                               │  Returns: FINAL revised plan  │
  │                               │  (overwrites plan.md)         │
  │                               │                               │
  │  "Approved"                   │                               │
  │──────────────────────────────►│                               │
  │                               │                               │
  │                               │  *** IMPLEMENTATION ***       │
  │                               │  Main agent reads files       │
  │                               │  (these DO go into context)   │
  │                               │                               │
  │                               │  Spawn Validator              │
  │                               │──────────────────────────────►│
  │                               │                               │
  │                               │                               │ Runs pytest
  │                               │                               │ (500 lines output)
  │                               │                               │ [stays in subagent]
  │                               │                               │
  │                               │◄──────────────────────────────│
  │                               │  Returns: "PASS - 47 tests"   │
  │                               │  (5 lines, not 500)           │
  │                               │                               │
  │  "I fixed the import"         │                               │
  │──────────────────────────────►│                               │
  │                               │                               │
  │     [Message saved]           │  git diff --name-only         │
  │                               │  Re-read changed files        │
  │                               │  Mark old reads as STALE      │
  │                               │                               │
```

---

## What Returns from Each Subagent

| Subagent | Returns to Main | Stays in Subagent |
|----------|-----------------|-------------------|
| **Problem-Analyst** | Problem statement (~2KB) | 20+ file reads, grep results (~50KB+) |
| **Explore** | File list with reasons (20 paths, ~1KB) | File reads for verification (~30KB+) |
| **Web-Researcher** | Structured reference (saved to .md, ~5KB) | 10+ web fetches, search results (~100KB+) |
| **Context-Loader** | Trimmed file excerpts (~10KB) | Full file contents, skipped parts (~50KB+) |
| **Planner** | Final plan only (saved to .md, ~5KB) | Research, iterations, alternatives (~20KB+) |
| **Plan-Reviewer** | Issues + verdict (~2KB) | Full plan analysis (~10KB+) |
| **Validator** | PASS/FAIL + summary (~500 bytes) | Raw pytest/ruff output (~50KB+) |
| **Log-Analyzer** | Findings report (~3KB) | Raw log contents (~500KB+) |
| **Code-Simplifier** | Suggestions list (~2KB) | Full diff analysis (~15KB+) |
| **Code-Reviewer** | Issues by severity (~3KB) | Full security analysis (~20KB+) |
| **Code-Goal** | Criteria checklist (~1KB) | Full verification analysis (~10KB+) |
| **Test-Writer** | Test code + coverage (~5KB) | Pattern analysis, fixture research (~30KB+) |

---

## User Responses & Context Impact

| User Says | Context Impact |
|-----------|----------------|
| `"Approved"` / `"Yes"` / `"Proceed"` | Small addition (~10 bytes), workflow continues |
| `"Change X to Y"` | Message saved (~100 bytes) → Spawns Planner with current plan + feedback → Previous plan iterations discarded → Only final revised plan returns |
| `"I made changes"` / `"I fixed X"` | Message saved (~50 bytes) → Main agent runs: `git diff --name-only` → Previous reads of those files: MARKED STALE → Re-reads changed files (adds to context) → Lightweight review (no subagent) |
| `"Use full workflow"` | Overrides complexity classification, no extra context, just changes behavior |
| `"Skip to implementation"` | Skips phases, no extra context |
| `"Continue workflow"` | Reads state.json, resumes from checkpoint, previous context preserved |

---

## Files & Persistence

```
                    ┌─────────────────────────────────────────┐
                    │           tasks/<task-name>/            │
                    ├─────────────────────────────────────────┤
                    │  state.json ◄── Resume point            │
                    │  problem.md ◄── From Problem-Analyst    │
                    │  research-*.md ◄── From Web-Researcher  │
                    │  plan.md ◄── From Planner               │
                    │  plan-review.md ◄── From Plan-Reviewer  │
                    │  *-validation.md ◄── From Validator     │
                    │  code-review.md ◄── From Code-Reviewer  │
                    │  verification.md ◄── From Code-Goal     │
                    └─────────────────────────────────────────┘
                                        │
                    Main agent reads these files instead of
                    keeping everything in memory context
                                        │
                    ┌─────────────────────────────────────────┐
                    │              research/                  │
                    ├─────────────────────────────────────────┤
                    │  stripe-api.md ◄── Reusable across tasks│
                    │  mwl-api.md                             │
                    │  portmone-api.md                        │
                    └─────────────────────────────────────────┘
```

---

## Context Efficiency Example

### Without Subagents (everything in main context):

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ User request ───────────────────────────────────────────────────────  100B   │
│ Explore codebase (read 25 files) ───────────────────────────────────  75KB   │
│ Web search Stripe API (10 fetches) ─────────────────────────────────  120KB  │
│ Read files for planning ────────────────────────────────────────────  50KB   │
│ Create plan ────────────────────────────────────────────────────────  5KB    │
│ User: "change to webhooks" ─────────────────────────────────────────  50B    │
│ Revise plan (iteration 1) ──────────────────────────────────────────  5KB    │
│ Revise plan (iteration 2) ──────────────────────────────────────────  5KB    │
│ Revise plan (final) ────────────────────────────────────────────────  5KB    │
│ Run tests (raw output) ─────────────────────────────────────────────  50KB   │
│ Implementation files ───────────────────────────────────────────────  20KB   │
│ ════════════════════════════════════════════════════════════════════════════ │
│ TOTAL: ~335KB (context exhausted quickly)                                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### With Subagents (isolated context):

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ User request ───────────────────────────────────────────────────────  100B   │
│ Problem-Analyst RESULT ─────────────────────────────────────────────  2KB    │
│ Web-Researcher RESULT (ref to file) ────────────────────────────────  200B   │
│ Context-Loader RESULT ──────────────────────────────────────────────  10KB   │
│ Planner RESULT (ref to file) ───────────────────────────────────────  200B   │
│ User: "change to webhooks" ─────────────────────────────────────────  50B    │
│ Planner REVISED RESULT (ref to file) ───────────────────────────────  200B   │
│ Validator RESULT ───────────────────────────────────────────────────  500B   │
│ Implementation files (only ones being edited) ──────────────────────  15KB   │
│ ════════════════════════════════════════════════════════════════════════════ │
│ TOTAL: ~28KB (90%+ reduction, room for complex tasks)                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Subagents are disposable** - their internal work disappears after returning results
2. **Files save context** - plans/research go to .md files, main agent reads path only
3. **User feedback is cheap** - short messages don't bloat context
4. **Plan revisions are free** - iterations stay in Planner subagent
5. **Main agent only reads during implementation** (Phase 4)
