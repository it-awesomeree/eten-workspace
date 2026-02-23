# CLAUDE.md — Eten's Workspace

Global instructions for Claude Code sessions in this workspace.

**Owner**: Eten (eten@awesomeree.com.my)
**Role**: Developer — Web App, n8n Workflows, VM Bot Scripts
**Company**: Awesomeree Sdn Bhd

---

## Proactive Documentation Rule (MANDATORY)

Every session must update the relevant documentation files. This is non-negotiable.

### What to Document and Where

| File | What goes here |
|------|----------------|
| `WORKLOG.md` | Every session: what was done, tickets touched, outcomes |
| `ERRORLOG.md` | Every error encountered and how it was resolved |
| `BACKLOG.md` | New ideas, deferred tasks, parking lot items |
| `CLAUDE.md` | New rules, lessons learned, permanent process changes |

### Self-Enforcement Rules
1. **Before ending any session**, check all 4 files above
2. If context compaction occurs mid-session, immediately re-read CLAUDE.md and WORKLOG.md
3. Never declare a task "done" until documentation is updated

### End-of-Session Checklist
- [ ] WORKLOG.md updated with session summary
- [ ] ERRORLOG.md updated if any errors occurred
- [ ] BACKLOG.md updated if any new ideas/tasks surfaced
- [ ] All changes committed and pushed to `eten-workspace`

---

## My Development Domains

### 1. Web App (Next.js)
- **Stack**: React 19, Next.js 15, TypeScript 5, Tailwind CSS, shadcn/ui, MySQL, Firebase, Google Cloud App Engine
- **Repo**: `it-awesomeree/awesomeree-webapp` (or assigned webapp repo)
- **Jira Project**: AW board — my tickets are under assignee "eten"

### 2. n8n Workflows
- **Instance**: `https://n8n.barndoguru.com` (v2.35.2)
- **Key workflows**: Variation & Description Generator family, Webhook Regenerate V2, Shopee Listing generators
- **Reference skill**: `/n8n-workflows` command for full workflow inventory and MCP tools

### 3. VM Bot Scripts
- **Gateway**: 100.86.32.62 (Tailscale VPN)
- **All VMs**: Windows (DESKTOP-* hostnames), accessed via WinRM on different ports
- **Reference skill**: `/vm-inventory` command for full VM/bot mapping and MCP tools
- **Source code**: `it-awesomeree/bot-scripts`

---

## Mandatory Rules

### PR Target Rule
- All web app PRs must target the `test` branch first, **never `main` directly**
- Only after test branch validation can changes be promoted to main

### Code Review Before Publish
- Never publish to production without a senior dev review crosscheck
- Review must cover: correctness, security (OWASP top 10), performance, regression risk

### Jira Workflow
- **My tickets**: Check AW board filtered by assignee "eten"
- **Column flow**: TO DO → IN PROGRESS → TO REVIEW → DONE
- **TO REVIEW**: Submit completed work here for Agnes's review
- When moving to TO REVIEW, always add a comment explaining what was done and any deviations from the ticket description
- **Never silently skip requirements** — if something can't be done, document why in a Jira comment

### Jira API Access
- **Base URL**: `https://awesomeree.atlassian.net`
- **Projects**: AW (Awesomeree), GRBT (General Request & Bug Tracker)
- Use REST API for Jira operations to avoid browser keyboard shortcut issues

### Chatbot Debugging — Always Check Both Layers
When debugging chatbot issues:
1. **Layer 1**: Node.js middleware on VMs (Puppeteer scripts) — controls what Dify receives
2. **Layer 2**: Dify workflow — processes the structured query
- If the middleware sends wrong input, Dify will produce wrong output even if the workflow is correct
- Reference `/chatbot-middleware` for the full architecture

### Cross-Platform Chatbot Rule
- Every chatbot fix must include a cross-platform check (Shopee MY, Shopee SG, TikTok where applicable)
- A fix for one platform should not break another

### Credential Change Rule
- Credential changes must be atomic — update ALL consumers simultaneously
- Never leave a half-updated state (e.g., DB password changed but Dify still using old one)

### GCP Configuration Rule
- Never use browser automation for GCP changes — use `gcloud` CLI
- Document any authorized network changes in snapshots

---

## Root Cause Classification (For Bug Fixes)

When fixing bugs, classify the root cause:

| Category | Definition |
|----------|-----------|
| **System/Code Defect** | Logic error, missing validation, race condition, unhandled edge case |
| **Configuration/Environment Issue** | Wrong API key, incorrect env variable, misconfigured setting |
| **Data/Input Anomaly** | Unexpected input format, special characters, encoding mismatch |
| **Process/Workflow Gap** | Missing checklist step, no test coverage, unclear handoff |

**Replay test**: "If we replayed the exact same events with a different person, would the bug still occur?"
- Yes → System/Code Defect or Process/Workflow Gap
- No → Configuration/Environment Issue or Data/Input Anomaly

Always use **neutral, system-focused language** — never attribute blame to individuals.

---

## Lessons Learned

<!-- Add entries as: ### YYYY-MM-DD: Title -->
<!-- Format: what happened, what was learned, what to do differently -->

_No entries yet. Add lessons as you encounter them._
