---
description: End-of-session checklist — push WORKLOG, ERRORLOG, BACKLOG, sync CLAUDE.md, and recap
---

# End-of-Session Checklist

Mandatory checklist before closing any session. Ensures all work, errors, ideas, and rule changes are documented and pushed to GitHub.

## Steps

### Step 1 — WORKLOG
- Review what was done this session
- Add new entries to `~/github-repos/agnes-workspace/WORKLOG.md`
- Include: ticket IDs, what was fixed/built, tools used, key decisions

### Step 2 — ERRORLOG
- Review errors encountered this session
- Add new entries to `~/github-repos/agnes-workspace/ERRORLOG.md`
- Include: error description, root cause, fix, prevention

### Step 3 — BACKLOG
- Review ideas, future tasks, or pre-Jira items discussed
- Add new entries to `~/github-repos/agnes-workspace/BACKLOG.md`
- Remove any items that were moved to Jira during this session

### Step 4 — CLAUDE.md Sync
- Check if `~/.claude/CLAUDE.md` was modified this session
- If yes, copy updated version to `~/github-repos/agnes-workspace/CLAUDE.md`

### Step 5 — Commit & Push
```bash
cd ~/github-repos/agnes-workspace && git add . && git status
```
- Only commit files that have actual changes
- Use descriptive commit message summarizing what was documented
- Push to GitHub

### Step 6 — Recap
Give Agnes a brief summary:
- What was logged in WORKLOG
- What was logged in ERRORLOG
- What was added to BACKLOG
- Whether CLAUDE.md was synced
- Confirm push succeeded

## Rules
- Do NOT skip any step — check each one even if you think nothing changed
- Do NOT assume previous sessions already logged everything
- If nothing changed for a step, say "no changes" and move on
- Push everything in a single commit to `agnes-workspace` repo
