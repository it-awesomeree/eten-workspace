---
description: Standard workflow for web app bug fixes and feature tickets (AW web app)
argument-hint: [TICKET-ID e.g. AW-250]
---

# Web App — Fix Workflow

Standard workflow for investigating, fixing, reviewing, testing, publishing, and documenting web app issues.

**Ticket:** $ARGUMENTS

## Workflow Steps

### Step 1 — Study Jira Ticket
- Navigate to the Jira ticket
- Read description, attachments, comments, status, assignee
- Understand the reported issue fully before touching any code

### Step 2 — Study the System
- Examine the web app code — frontend, backend, database
- Trace the relevant flow (API endpoints, components, queries)
- Identify which files/functions are involved and what the expected vs actual behavior is

#### Step 2A — Dev Compliance Check (TO REVIEW tickets)
If the ticket is in TO REVIEW (dev submitted work for review), cross-reference what was delivered against Agnes's original ticket description:

1. **Read Agnes's ticket description** — every requirement listed is expected to be implemented
2. **Read ALL comments** — check if the dev mentioned skipping, deferring, or modifying any requirement with a reason
3. **Build a compliance matrix** — for each requirement in the description:
   | Requirement | Implemented? | Dev Reason (if skipped) | Verdict |
   |-------------|-------------|------------------------|---------|
   | ... | Yes/No/Partial | ... | Accept / Rework |
4. **Evaluate skipped items**:
   - **Valid skip**: Sound technical reason (e.g., "API doesn't support X yet", "blocked by dependency Y") → accept and note
   - **Lazy skip**: No reason, weak excuse, or silence → **send back for rework**
5. **Present the compliance matrix to Agnes** before any further action

Devs do NOT get to silently ignore requirements. No implementation + no documented reason = rework.

### Step 3 — Comprehensive Debugging Analysis
- Document root cause with numbered contributing factors
- Use a scratchpad approach: predictions, hypotheses, evidence
- Map out which files/functions need changes and why

### Step 4 — Root Cause Classification (Bug Fix Tickets Only)

> **Skip this step if the ticket is a feature request or enhancement — only applies to bug fixes.**

Using the evidence from Step 3, classify the root cause into one of the categories below. This classification exists to **improve systems and processes** — not to assign individual blame.

#### Classification Categories

| Category | Definition | Examples |
|----------|-----------|----------|
| **System/Code Defect** | The application logic, implementation, or architecture produced incorrect behavior | Missing validation, logic error, race condition, unhandled edge case, incorrect query, null pointer |
| **Configuration/Environment Issue** | Correct code exists but was deployed with incorrect settings, parameters, or environment values | Wrong API key, incorrect env variable, misconfigured feature flag, wrong DB connection string |
| **Data/Input Anomaly** | The system received unexpected, malformed, or edge-case input it wasn't designed to handle | Unexpected data format from external API, missing required field, special characters in input, encoding mismatch |
| **Process/Workflow Gap** | A missing or unclear process allowed the issue to reach production — the process needs improvement, not any individual | No config validation in deployment checklist, missing test coverage requirement, unclear handoff documentation |

#### How to Classify

1. Review all evidence gathered in Step 3
2. Ask the **replay test**: "If we replayed the exact same sequence of events with a different person performing every action, would the bug still occur?"
   - **Yes** → Likely **System/Code Defect** or **Process/Workflow Gap** (the system allowed it to happen)
   - **No** → Likely **Configuration/Environment Issue** or **Data/Input Anomaly** (specific conditions triggered it)
3. For each contributing factor identified in Step 3, assign one category
4. Identify the **primary** root cause category — the one that, if addressed, would have prevented the issue entirely

#### Writing Rules — Neutral, Factual, System-Focused

Always frame findings as **systemic observations**, never personal attribution:

| DO (system-focused) | DON'T (blame-focused) |
|---|---|
| "The deployment pipeline does not validate config values before release, which allowed an incorrect value to reach production" | "Developer X forgot to check the config" |
| "The input validation layer does not enforce date format constraints, causing a crash on ISO-8601 input" | "The user entered the date in the wrong format" |
| "The code review checklist does not include a security review step for API endpoints" | "The reviewer missed the SQL injection vulnerability" |
| "The API does not handle null responses from the payment gateway, resulting in an unhandled exception" | "Nobody thought to handle nulls" |

#### Output — Include in Debugging Notes

```
ROOT CAUSE CLASSIFICATION
─────────────────────────
Category: [System/Code Defect | Configuration/Environment Issue | Data/Input Anomaly | Process/Workflow Gap]
Summary:  [1–2 sentence factual description of what happened]
Evidence: [Key facts from Step 3 that support this classification]
Prevention: [What systemic change — code fix, process improvement, or automation — would prevent recurrence]
```

> **Note:** This classification feeds into the Jira comment (Step 12/12B) and GitHub changelog (Step 11) for trend tracking. Over time, it helps the team identify whether recurring issues are systemic and where to invest in prevention.

---

### Step 5 — Review 1: Senior Dev
- Review the proposed fix as a **senior developer**
- Check: correctness, security (OWASP top 10), performance, code quality, regression risk
- Approve / modify / reject the fix
- If rejected, return to Step 3

### Step 6 — Review 2: Tech Lead Crosscheck
- Crosscheck the approved fix as a **tech lead**
- Validate: architecture alignment, scalability, security implications, regression risks
- Confirm the fix follows existing codebase patterns and conventions
- Approve / modify / reject
- If rejected, return to Step 5

### Step 7 — Run Tests: Senior QA + SRE
- Execute fix validation tests (does the fix solve the reported issue?)
- Execute regression tests (do existing features still work?)
- Run reliability/infra checks (error handling, edge cases, performance)
- All tests must pass before proceeding

### Step 8 — Branch: Who did the work?

Check the ticket assignee to determine the path forward:

#### Path A — Done by me (Agnes / Claude Code)
Continue to Step 9.

#### Path B — Done by a developer
Skip Steps 9–10. Go directly to **Step 8B**.

---

### Step 8B — Send Technical Review Comment to Developer (Path B only)
- Post a **technical** comment on the AW Jira ticket summarizing the review findings
- Include: what was reviewed, issues found (with file paths + line numbers), what passed, what failed
- Include the **Root Cause Classification** from Step 4 (if applicable) using neutral language
- If issues found: clearly list each issue with severity (critical/moderate/minor) and what the dev needs to fix
- If all passed: state the review passed and what was verified
- Use the Jira REST API to avoid keyboard shortcut issues
- **Do NOT implement any code fix** — the developer owns the fix
- After posting:
  - If review **failed**: leave ticket in TO REVIEW (dev will see the comment and fix). Stop here.
  - If review **passed**: proceed to **Step 11** (Document in GitHub).

---

### Step 9 — Implement the Fix (Path A only)
- **Only proceed if all reviews pass with zero errors**
- Write/edit the code changes
- Follow existing codebase patterns and conventions

### Step 10 — Publish to Production (Path A only)
- Run Senior Dev Review Crosscheck (per CLAUDE.md mandatory rule)
- Deploy to production environment
- Verify the deployment is successful and the fix is live

### Step 11 — Document in GitHub (Both Paths)
- Create a changelog entry at `docs/changelog/AW-XXX.md` in the web app repo
- Use the template below to document the **final corrected state** only (not initial wrong work)
- Commit and push to the relevant repo
- Include clear commit message referencing the ticket

#### Changelog Template
```markdown
# AW-XXX — [Ticket Title]

**Date:** YYYY-MM-DD
**Assignee:** [Name]
**Reviewed by:** Agnes (Claude Code)

## Summary
[1–2 sentences: what changed and why]

## Root Cause Classification
**Category:** [System/Code Defect | Configuration/Environment Issue | Data/Input Anomaly | Process/Workflow Gap]
**Summary:** [1 sentence factual description]
**Prevention:** [Systemic improvement to prevent recurrence]

## Files Changed
| File | Change |
|------|--------|
| `path/to/file.tsx` | [Brief description of final state] |

## Review Notes
Technical review details: [Jira ticket link]
```

### Step 12 — Write Jira Comment & Close (Path A only)
- Post a **technical** comment on the AW ticket (devs understand tools/code)
- Explain: root cause, root cause classification (using neutral language), code changes made, files modified, how it was tested
- Use the Jira REST API to avoid keyboard shortcut issues
- Transition the ticket to the **DONE** column
- Place it at the **top** of the Done column

### Step 12B — Close Ticket (Path B only)
- Transition the ticket to the **DONE** column (Jira REST API)
- Place it at the **top** of the Done column
- Note: The technical review comment was already posted in Step 8B

## GRBT Web App Tickets

This workflow also applies to **GRBT tickets** that involve web app code changes (not just AW tickets). Key differences for GRBT:

- **Two audiences for comments**: The GRBT requestor (CS team) and the assigned developer are different people with different needs.
- **Dev handoff comment** (Step 8B): Technical — include root cause, code changes, PR link, branch name, and step-by-step testing instructions. The dev must know exactly what to do.
- **Requestor-facing comment** (Step 12): Non-technical — plain language explaining what went wrong and what was fixed. No code, no GitHub, no jargon.
- **Column rules**: When assigning to a dev, move to **IN PROGRESS** (not TO REVIEW — that's Agnes's column). See `jira.md` for column ownership rules.

## CRITICAL RULES

- **NEVER publish without completing Steps 5-7 (reviews + tests)**
- **NEVER introduce security vulnerabilities** (SQL injection, XSS, command injection, etc.)
- **ALWAYS run regression tests** — fixing one feature must not break another
- **ALWAYS document in GitHub** (Step 11) before closing the ticket — applies to BOTH paths
- **NEVER move a ticket to TO REVIEW when assigning to a dev** — TO REVIEW is Agnes's review column
- **ALWAYS include clear action items** when assigning to a dev — they must know exactly what to do
- AW web app tickets: Jira comments must be **technical**
- GRBT web app tickets: Two comments — technical for dev, non-technical for requestor
- Changelog entries document the **final corrected state** only — not initial wrong work by the developer
- Root Cause Classification must use **neutral, system-focused language** — never attribute blame to individuals
