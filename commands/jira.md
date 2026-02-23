---
description: Awesomeree Jira - Board structure, columns, assignees, labels, and workflow for AW and GRBT projects
argument-hint: [project, ticket, or workflow question]
---

# Awesomeree Jira Documentation

Complete reference for the Jira workspace at `awesomeree.atlassian.net`.

**Organization**: awesomeree
**Platform**: Jira Software (Kanban boards)
**Two active projects**: Awesomeree (AW) and General Request & Bug Tracker (GRBT)

---

## Project 1: Awesomeree (AW)

**URL**: `https://awesomeree.atlassian.net/jira/software/projects/AW/boards/34`
**Board ID**: 34
**Type**: Kanban Board
**Total items**: ~307 (incl. ~227 Done)
**Grouping**: Grouped by **Assignee** (default)

### Board Columns (left to right)
| Column | Description |
|--------|-------------|
| **TO DO** | Backlog items not yet started |
| **IN PROGRESS** | Actively being worked on |
| **TO REVIEW** | Completed work awaiting review |
| **DONE** | Finished and approved work |
| **BLOCKED** | Items blocked by dependencies or external factors |

### Navigation Tabs
Summary, Timeline, **Backlog**, Board, Calendar, List, Forms, More

### Assignees (team members)
| Name | Avatar | Typical Work Items |
|------|--------|-------------------|
| **anfal** (A) | Green | Web app, Shopee listing, misc dev/tech debt |
| **eten** (E) | Teal | Shopee MY listing auto-generator, prompt finalization |
| **Janarthan Nair** (JN) | Teal | Chatbot, bots/logging, scheduler-visibility, web app |
| **Kelly Ee** (KE) | Purple | Comp. Analysis, webapp, UI/UX, frontend |
| **Melinda** (M) | Blue | Comp. Analysis, variation-matching, AI, product-listing |
| **nisha** (N) | Red | Data pipeline, bot, Shopee integration |
| **Pang Yu Hang** (PH) | Blue | Chrome MCP, Claude Code, TikTok OTP, costing, web app |
| **Agnes Foong** (AF) | Purple | Lead/reviewer (appears as logged-in user) |

### Issue Types
- **Task** (blue checkbox icon) - Most common, general development work
- **Bug** (red icon) - Defects and issues
- **Story** (green bookmark icon) - Feature stories

### Labels / Categories (seen on cards)
Labels appear as colored badges on ticket cards:
- **MISC DEV / TECH DEBT** (red) - Technical debt and miscellaneous development
- **SHOPEE MY LISTING AUTO-GENERATOR** (grey) - Shopee listing automation project
- **WEB APP** (green) - Web application features
- **CHATBOT** (red) - Shopee chatbot features
- **COMP. ANALYSIS** (red) - Competitive analysis features

### Common Tags on Cards
Tags appear as outlined pills on cards:
`webapp`, `uiux`, `frontend`, `backend`, `bot`, `db`, `sql`, `api`, `ai`, `calculation-audit`, `backend-source-of-truth`, `data-integrity`, `user-management`, `bots`, `logging`, `scheduler-visibility`, `chatbot`, `chrome-mcp`, `claudecode`, `mcpstdio`, `email-forwarding`, `otp-parsing`, `product-listing`, `variation-matching`, `data-quality`, `data-pipeline`, `shopee-integration`

### Filter Options (List view)
Parent, Assignee, Work type, Labels, Status, Priority, Reporter

### Grouping Options (Board view)
Assignee (default selected), None, Subtask, Priority

---

## Project 2: General Request & Bug Tracker (GRBT)

**URL**: `https://awesomeree.atlassian.net/jira/software/projects/GRBT/boards/68`
**Board ID**: 68
**Type**: Kanban Board
**Total items**: ~183 (15 active on board, rest in Done)
**Grouping**: **None** (default - flat view, not grouped by assignee)

### Board Columns (left to right)
| Column | Description | Owner |
|--------|-------------|-------|
| **TO DO** | Requests/bugs not yet started | Anyone |
| **USER ACTION** | Waiting for user/requester to provide info or take action | Anyone |
| **IN PROGRESS** | Actively being worked on | Anyone |
| **TO REVIEW** | Completed, awaiting Agnes's review | **Agnes only** |
| **APPROVAL** | Reviewed, awaiting final approval | **Agnes only** |
| **DONE** | Finished and closed | Anyone |

**Key difference from AW**: GRBT has **USER ACTION** and **APPROVAL** columns that AW does not have. GRBT does NOT have a **BLOCKED** column.

### Column Ownership Rules (CRITICAL)
- **TO REVIEW** and **APPROVAL** are Agnes's columns. Only Agnes moves tickets there (after she reviews dev work). NEVER place a ticket in TO REVIEW when assigning it to a developer.
- When assigning a ticket to a dev for code review/testing: use **IN PROGRESS** (work is ongoing, dev needs to review and test before it can move forward).
- When sending a ticket back to a dev for rework: use **IN PROGRESS**.
- When a ticket hasn't been started yet: use **TO DO**.

### Navigation Tabs
Summary, Timeline, Board, Calendar, List, Forms, Development, More

**Key difference from AW**: GRBT has a **Development** tab but NO **Backlog** tab.

### Assignees
| Name | Avatar |
|------|--------|
| **Janarthan Nair** (JN) | Teal |
| **Kelly Ee** (KE) | Purple |
| **Pang Yu Hang** (PH) | Blue |
| **Agnes Foong** (AF) | Purple |
| **eten** (E) | Teal |
| **anfal** (A) | Green |
| **Melinda** (M) | Blue |
| **Unassigned** | Grey |

### Reporter
Almost all GRBT tickets are reported by **CS Team** (Customer Support Team).

### Issue Types
- **Task** (blue checkbox icon)
- **Bug** (red icon)
- **Story** (lightning icon)

### Common Tags on Cards
`form`, `form-45`, `form-46`, `form-47`, `form-354`, `form-390` (form submission references)

### Grouping Options (Board view)
None (default), Assignee, Subtask

### Ticket Naming Patterns
GRBT tickets tend to be operational requests and bug reports from the CS team:
- Missing/incorrect data issues
- Bot not functioning
- Page updates needed
- QR code checks
- Tab/routing issues
- Stock adjustment flows
- New feature requests from operations

---

## Key Differences Between AW and GRBT

| Aspect | AW (Awesomeree) | GRBT (General Request & Bug Tracker) |
|--------|-----------------|--------------------------------------|
| **Purpose** | Development sprint work | Operational requests & bug reports |
| **Board columns** | TO DO, IN PROGRESS, TO REVIEW, DONE, BLOCKED | TO DO, USER ACTION, IN PROGRESS, TO REVIEW, APPROVAL, DONE |
| **Default grouping** | By Assignee | None (flat) |
| **Total items** | ~307 | ~183 |
| **Reporter** | Various team members | Primarily CS Team |
| **Ticket source** | Dev planning | Form submissions from CS/ops |
| **Has Backlog tab** | Yes | No |
| **Has Development tab** | No | Yes |
| **Has BLOCKED column** | Yes | No |
| **Has USER ACTION column** | No | Yes |
| **Has APPROVAL column** | No | Yes |

---

## Developer Workflow: IN PROGRESS → TO REVIEW

When a dev moves a ticket to **TO REVIEW**, the following work has (assumingly) been completed. In practice, many devs cut corners or skip steps, so reviews must catch gaps.

### What devs should have done locally
1. **Code complete** - Feature, bug fix, enhancement, or product work is functionally done
2. **Acceptance criteria met** - All requirements from the ticket are addressed
3. **Tests added/updated** - Unit tests, integration tests as applicable
4. **Logging & metrics** - Appropriate observability instrumentation
5. **Documentation** - Updated if needed (API docs, README, inline docs)
6. **Jira ticket updated** with:
   - What changed (summary of work done)
   - How to test (reproduction/verification steps)
   - Screenshots or video for UI changes

### What devs should have created in Git
1. **Feature branch** created from main
2. **Pull Request** opened with:
   - Summary and reason for the change
   - Testing done (how the dev verified it works)
   - Risk notes and rollback plan
   - Feature flag plan (if applicable)
   - Migration notes (if DB changes involved)
3. **Code owners** automatically requested as reviewers

### Where the dev stops
The dev's job ends at PR creation. Everything after this point is the review and deployment pipeline.

---

## Workflow Notes

### Moving tickets
- Drag-and-drop is unreliable on the board
- Use **right-click > Move work item > To the top** to move tickets between columns
- When moving to DONE, always move to **TOP** of Done column

### Board interaction tips
- @mention dropdown in Jira comments causes misclicks - type plain text instead
- Board URL for AW: `https://awesomeree.atlassian.net/jira/software/projects/AW/boards/34`
- Board URL for GRBT: `https://awesomeree.atlassian.net/jira/software/projects/GRBT/boards/68`
- Individual ticket URL pattern: `https://awesomeree.atlassian.net/browse/AW-XXX` or `https://awesomeree.atlassian.net/browse/GRBT-XXX`

### Email workflow for Jira notifications
- "Moved to In Progress" emails → tell user to delete (prohibited action)
- TO REVIEW emails → open ticket, check comments, review using Senior Review Prompt
- If TO REVIEW ticket already changed back to In Progress → tell user to close/delete email
- Time Doctor daily summary emails → skip, tell user to delete

---

## Jira Interaction Methods (for Claude Code)

### Browser Automation
Navigate to ticket URLs using `claude-in-chrome` MCP tools. Read ticket content, click UI elements.

### REST API (Preferred for comments & transitions)
Use the Jira REST API to avoid keyboard shortcut issues in the browser.

**Base URL**: `https://awesomeree.atlassian.net/rest/api/3`

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Read ticket | GET | `/issue/{issueKey}` |
| Add comment | POST | `/issue/{issueKey}/comment` |
| Change status | POST | `/issue/{issueKey}/transitions` |
| List available transitions | GET | `/issue/{issueKey}/transitions` |

**Comment format**: Use Atlassian Document Format (ADF) for POST body:
```json
{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Your comment here"}]}]
  }
}
```

**Transition a ticket** (e.g., move to DONE):
1. First GET `/issue/{key}/transitions` to discover available transition IDs
2. Then POST `/issue/{key}/transitions` with `{"transition": {"id": "<transition_id>"}}`

**Auth**: Cookie-based via browser console, or API token via Authorization header.

### Comment Style Rules
Comment style depends on **who the comment is addressed to**, not just which project:

| Audience | Style | What to include | What to avoid |
|----------|-------|-----------------|---------------|
| **CS team / end-users** (GRBT requestors) | Non-technical | Plain language: what went wrong, what was fixed, current status | Code, file paths, GitHub, branch names, technical jargon |
| **Developers** (assigned for review/testing) | Technical | Root cause, code changes, file paths, branch name, PR link, **clear step-by-step instructions** | Vague descriptions without actionable next steps |

**When assigning to a developer, ALWAYS include:**
1. Root cause explanation (technical)
2. What was changed and where (file paths, code snippets)
3. PR link and branch name
4. Exact testing steps (what to checkout, where to navigate, what to verify)
5. What to do after testing passes (approve, merge, which branch)

A dev without clear instructions will not know whether to work on the user's original ticket or act on your comment. Remove all ambiguity.

### JQL Examples (for searching tickets)
```
# All open tickets assigned to a person
project = AW AND assignee = "Agnes Foong" AND status != Done

# All GRBT tickets in TO REVIEW
project = GRBT AND status = "TO REVIEW"

# Tickets with a specific label
project = AW AND labels = "WEB APP" AND status != Done

# Recently updated tickets
project = GRBT AND updated >= -7d ORDER BY updated DESC

# All chatbot-related tickets
project IN (AW, GRBT) AND (labels = "CHATBOT" OR text ~ "chatbot")
```

---

## Atlassian Organization

**Org name**: awesomeree
**Available apps**: Jira, Confluence, Loom, Trello, Teams, Search

---

## Last Verified
**Date**: 2026-02-17
**Note**: Team roster and item counts are point-in-time snapshots. Verify before relying on specific numbers.
