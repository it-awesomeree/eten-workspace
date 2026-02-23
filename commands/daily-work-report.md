# Daily Work Report

Automates Agnes's daily work report workflow in her Google Sheets tracker (2026/02).

## Sheet URL
https://docs.google.com/spreadsheets/d/1dXdtMbDTCBFJKwM6JF2mDg-2vkT_vmNKabX11nSfJpI/edit

## Workflow Steps

### Step 1: Open the Sheet
- Navigate to the Google Sheet URL above
- Identify the last sheet tab (rightmost tab at bottom, format: MMDD)

### Step 2: Create New Sheet Tab
- **Date rule**: Use the LAST WORKDAY date (Mon-Fri), NOT today's date. Agnes works late nights past midnight, so the report date is typically yesterday or the last working day.
- **Skip weekends**: Sheet tabs are Mon-Fri only (no Sat/Sun)
- **Public holidays**: Skip Malaysian public holidays (check if unsure)
- **Format**: `MMDD` (e.g., `0217` for Feb 17)
- Right-click the last tab → Duplicate
- Right-click the new "Copy of XXXX" tab → Rename to the correct MMDD date
- **Important**: Use the `find` tool to locate menu items (Duplicate, Rename, Delete) by ref_id to avoid misclicks

### Step 3: Remove Completed Rows
- Scroll through the entire sheet to catalog all rows
- Delete ALL rows where Status = "Completed"
- Also delete rows where the task is confirmed done (e.g., a "Blocked" task whose blocker is resolved and work is finished)
- To delete: Click row number → Shift+click last row number → Right-click → Delete rows

### Step 4: Cross-Reference WORKLOG
- Read `WORKLOG.md` from `it-awesomeree/agnes-workspace` repo on GitHub
- Identify work done since the last report date
- Add completed work items as new rows with Status = "Completed"
- **Deduplication**: Compare task names loosely — Agnes may use shortened names, different phrasing, or group related tasks. Do NOT add duplicates.
- Match worklog entries to existing sheet rows where possible (update status instead of adding new row)

### Step 5: Cross-Reference BACKLOG
- Read `BACKLOG.md` from `it-awesomeree/agnes-workspace` repo on GitHub
- Identify active backlog items (not completed, not already moved to Jira)
- Add as new rows with Status = "Not started"
- **Deduplication**: Cross-check against both existing sheet rows AND Jira tickets (Step 6)

### Step 6: Cross-Reference Jira
- Fetch all AW project tickets not in Done status:
  ```bash
  source ~/.zshrc && jira-api POST /search/jql -d '{"jql":"project = AW ORDER BY status ASC","maxResults":50}'
  ```
  Then fetch each issue by ID for details (v3 search/jql returns IDs only)
- Backlog items that already exist as Jira tickets should NOT be duplicated
- Update statuses of existing sheet rows if Jira status has changed

### Step 7: Update Existing Row Statuses
- Check if any "In progress", "Not started", or "Blocked" items have changed status based on WORKLOG or Jira data
- Update statuses accordingly (e.g., Blocked → Completed if blocker resolved)

## Sheet Format (Columns A-E)
| Column | Header | Values |
|--------|--------|--------|
| A | Category | Dropdown: Ad Hoc, IT Team, Content, Government, Recruitment |
| B | Priority | P0, P1, P2, P3 |
| C | Task | Free text. Format: `Module: Feature` for solo tasks, `TaskName \ AssigneeName [DevName]` for team tasks |
| D | Status | Dropdown: Completed, In progress, Not started, Follow-Up, On Hold, Pending, Blocked |
| E | Note | Free text. Numbered sub-tasks or context notes |

## Status Order in Sheet (top to bottom)
1. Blocked (red)
2. Completed (green) — removed next session
3. Follow-Up (yellow)
4. In progress (yellow-green)
5. Not started (purple)
6. On Hold (orange/red)
7. Pending (pink)

## Task Naming Convention
- **Solo tasks**: `Module: Feature` — separate the module/system and the specific work with a colon
  - Examples: `Shopee Listing: Activity Panel`, `QC Testing: Shopee Listing AI`, `Fix: Confirmation popup stuck on product switch`
- **Team tasks**: `DateCode TaskName \ BossName [DevName]` — date prefix, backslash separates task from assignees
  - Examples: `20260205 Shopee Listing \ Ken [Eten]`, `20260210 Bot Monitoring \ Ken [Jana]`
- **Keep names short and non-technical** — Agnes is non-technical, task names should be understandable at a glance
- **Jira ticket references go in Column E (Note)**, NOT in the task name
- **No overly formal/engineering-style names** — use plain language (e.g., "Fix: Confirmation popup stuck" not "Hotfix: setConfirmPending")

## Key Rules
- **One sheet per workday** (Mon-Fri only, skip Malaysian public holidays)
- **Backdate**: Sheet date = last workday, not current calendar date
- **No duplicates**: Same task under different names counts as one entry
- **Team tasks format**: `TaskDescription \ BossName [DevName]` for team tasks (e.g., `20260205 Shopee Listing \ Ken [Eten]`)
- **Category mapping**: Ad Hoc = internal/Agnes tasks, IT Team = dev team tasks, Content = marketing, Government = permits/compliance, Recruitment = hiring
- **Completed rows are removed** when creating the next day's sheet — they represent "done since last report"

## Browser Automation Tips
- Google Sheets tab bar is at the very bottom of the viewport
- Use `read_page` with `ref_id` for the sheet tab navigation area (`ref_152`) to find tab buttons
- Use `find` tool to locate specific menu items (Delete, Duplicate, Rename) after right-clicking — coordinate-based clicks on context menus are unreliable due to position shifts
- Dropdown columns (Category, Status) use colored chips — click the cell then the dropdown arrow to change values
- To delete rows: select row numbers on the left, right-click → Delete rows
