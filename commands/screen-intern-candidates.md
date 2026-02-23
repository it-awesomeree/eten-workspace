---
description: Screen intern candidates in Google Sheet and alert Haikhal to send interview invitations
argument-hint:
---

# Screen Intern Candidates & Send Interview Instructions

Screen intern candidates by marking unqualified ones as "Do not proceed" in Google Sheet, then send WhatsApp reminder to Haikhal to send interview invitation emails to filtered candidates.

## CRITICAL: Always use Claude Chrome extension tools
- Use mcp__claude-in-chrome__* tools for ALL browser interactions
- Call tabs_context_mcp first to get available tabs

## Prerequisites

### Google Sheet Details
- **Sheet Name:** AI/Frontend/Backend Developer Intern — Prescreen Form (Responses)
- **Column X:** "Qualified" (dropdown: "Proceed to invitation" / "Do not proceed")
- **Column Y:** "Invitation" (checkbox - TRUE if already sent)
- **Column H:** SPM results
- **Column L:** Final/Current CGPA

### Qualification Criteria
**Qualified ("Proceed to invitation")** if they meet **EITHER**:
- CGPA >= 3.5, OR
- 5As or more in SPM results

**Disqualified ("Do not proceed")** if:
- CGPA < 3.5 AND less than 5As in SPM, OR
- No CGPA and no SPM data provided (incomplete application)

### WhatsApp Contact
- **Contact:** Admin Haikhal Work

---

## Part 1: Mark Unqualified Candidates in Google Sheet

### Step 1: Open Google Sheet
1. Navigate to Google Drive or directly to the sheet URL
2. Open "AI/Frontend/Backend Developer Intern — Prescreen Form (Responses)"

### Step 2: Remove All Existing Filters
**IMPORTANT: Always start with a clean slate**
1. Go to Data menu > Remove filter (if filter exists)
2. Or click on any active filter icon and select "Select all" then "OK"
3. Verify all rows are now visible

### Step 3: Navigate to Column X and Filter for Unscreened Candidates
1. Scroll right to find Column X ("Qualified")
2. Use Name Box (top-left) to jump directly: type "X1" and press Enter
3. Click on the filter icon in Column X header (funnel icon)
4. Click "Filter by values" to expand
5. Click "Clear" to deselect all values
6. Select only "(Blanks)" checkbox
7. Click "OK" to apply filter

**Expected Result:** Only rows with blank Column X cells are displayed (unscreened candidates only)

**NOTE:** Ignore candidates already marked as "Do not proceed" or "Proceed to invitation" - they have already been screened.

### Step 4: Screen Each Candidate
For each visible row in filtered view, check CGPA (Column L) and SPM results (Column H):

**Mark as "Do not proceed" if:**
- CGPA is blank AND SPM results is blank (no data provided), OR
- CGPA < 3.5 AND less than 5As in SPM

**Mark as "Proceed to invitation" if:**
- CGPA >= 3.5, OR
- 5As or more in SPM results

**How to mark:**
1. Click on the blank cell in Column X
2. Wait for dropdown to appear
3. Click appropriate option ("Proceed to invitation" or "Do not proceed")
4. Repeat for all remaining blank rows

**IMPORTANT:**
- Candidates with NO CGPA and NO SPM data = "Do not proceed" (incomplete application)
- Use click-and-select method, NOT typing (typing may cause validation errors)

### Step 5: Verify All Cells Filled
1. Click filter icon in Column X header
2. Click "Select all" to show all values
3. Click "OK"
4. Confirm no blank cells remain in Column X
5. Scroll through to verify mix of "Do not proceed" (red) and "Proceed to invitation" (green)

---

## Part 2: Check for Pending Invitations & Send WhatsApp Message (Conditional)

**IMPORTANT: Only send the WhatsApp message if there are shortlisted candidates with unsent invitations.**

### Step 1: Check for Pending Invitations
After completing Part 1, check if there are candidates who need invitations sent:
1. Remove all existing filters first (Data > Remove filter)
2. Re-create filter (Data > Create a filter)
3. Filter **Column X** for only "Proceed to invitation"
4. Then filter **Column Y** ("Invitation") for only **FALSE/unchecked** (unsent invitations)
5. Check the row count at the bottom of the sheet

### Decision Logic:
- **If there are rows visible** (candidates marked "Proceed to invitation" with Column Y = FALSE) → There are pending unsent invitations. Proceed to send WhatsApp message to Haikhal.
- **If NO rows are visible** (all shortlisted candidates already have invitations sent, or no shortlisted candidates exist) → Skip WhatsApp message entirely. Inform the user: "All shortlisted candidates already have invitations sent. No need to alert Haikhal."
- **If there were NO unscreened candidates (0 blank rows found in Part 1)** AND no pending invitations → Skip WhatsApp message entirely. Inform the user: "No new candidates to screen and no pending invitations. Skipping WhatsApp reminder to Haikhal."

**After checking, remove the filter again before proceeding (Data > Remove filter).**

### Step 2: Open WhatsApp Web
1. Create new tab or navigate to `https://web.whatsapp.com`
2. Wait for WhatsApp to load (ensure phone is connected)

### Step 3: Search for Contact
1. Click on search bar "Search or start a new chat"
2. Type "haikhal"
3. Select "Admin Haikhal Work" from results

### Step 4: Compose Message
Type a simple reminder message:

```
Hi Haikhal,

Please send interview invitation emails to the filtered candidates that haven't been sent yet.

Thanks!
```

**Note:** Interview schedule details (starting Monday, 6 candidates/day max) are already established - no need to repeat.

### Step 4: Send Message
1. Review message for accuracy
2. Press Enter or click send button (green arrow)
3. Verify message shows double checkmarks (delivered)

---

## Checklist Summary
- [ ] Open Google Sheet with candidate responses
- [ ] Remove all existing filters first
- [ ] Filter Column X for blank cells only (unscreened candidates)
- [ ] For each unscreened candidate:
  - [ ] No CGPA and no SPM data → "Do not proceed"
  - [ ] CGPA >= 3.5 OR 5As+ in SPM → "Proceed to invitation"
  - [ ] Otherwise → "Do not proceed"
- [ ] Remove filter and verify all cells filled
- [ ] Check for pending invitations (Column X = "Proceed to invitation" AND Column Y = FALSE)
- [ ] If pending invitations exist: Open WhatsApp Web → Find Admin Haikhal Work → Send reminder → Confirm delivery
- [ ] If no pending invitations: Skip WhatsApp and inform user

---

## Common Issues & Solutions

### Issue: Dropdown validation error when typing
**Solution:** Don't type directly - click cell to open dropdown, then click the option

### Issue: Copy/paste doesn't work for dropdown cells
**Solution:** Mark each cell individually by clicking and selecting from dropdown

### Issue: Missing some blank cells
**Solution:** Use filter feature (Filter > Filter by values > Blanks) to systematically find all blank cells

### Issue: WhatsApp message sends as one chunk
**Solution:** Use Shift+Enter (not Enter) to create line breaks within the message

---

## Scheduled Runs
This skill runs automatically via macOS launchd:
- **Daily at 8:00 AM and 1:00 PM** (Malaysia time, UTC+8)
- **Auto-opens Chrome** if not running (waits 20s for extension to connect)
- **Catches missed runs on login** — if laptop was shut down during a scheduled time, it runs when you log back in

### Files
| File | Purpose |
|------|---------|
| `~/.claude/scripts/screen-intern-cron.sh` | Main runner (opens Chrome, runs skill) |
| `~/.claude/scripts/screen-intern-missed-check.sh` | Login checker for missed runs |
| `~/Library/LaunchAgents/com.claude.screen-intern.plist` | 8am & 1pm schedule |
| `~/Library/LaunchAgents/com.claude.screen-intern-missed.plist` | Login catch-up |
| `~/.claude/logs/` | Logs (auto-cleaned after 30 days) |

### Managing the Schedule
```bash
# Stop the schedule
launchctl unload ~/Library/LaunchAgents/com.claude.screen-intern.plist
launchctl unload ~/Library/LaunchAgents/com.claude.screen-intern-missed.plist

# Restart the schedule
launchctl load ~/Library/LaunchAgents/com.claude.screen-intern.plist
launchctl load ~/Library/LaunchAgents/com.claude.screen-intern-missed.plist

# Check status
launchctl list | grep screen-intern
```

---

## Notes
- Always verify qualification criteria before marking
- The filter shows count of displayed rows (e.g., "17 of 287 rows displayed")
- Double checkmarks in WhatsApp indicate message delivered
- Interview dates should be weekdays only
