# Backlog — Eten

Prioritized parking lot for ideas, deferred tasks, and improvements. Organized by domain.

---

## Web App

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | _Add items as they come up_ | — | — | — |

---

## n8n Workflows

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | Migrate hardcoded API keys in SET API KEY node to n8n credentials | Medium | Open | Gemini + OpenAI keys are hardcoded; should use n8n credential store |
| 2 | Test Shopee Listing New Variation Generation with more product types | Medium | Open | Execution #603 passed with plant shelf; test with clothing, electronics, etc. |
| 3 | Add error notification to Shopee Listing New Variation Generation | Low | Open | Slack/email alert when workflow execution fails |
| 4 | Improve Validate Variations to catch bad variation names | Medium | Open | Names like "- 1-2" pass validation; add min-length, starts-with-dash, and meaningful-content checks |
| 5 | Webapp integration for Variation Regeneration webhook | High | Open | Build UI to trigger `POST /webhook/regenerate-variation-description` with field selection (variation/description/variation_image) |
| 6 | Staging review UI for `shopee_variation_staging` | Medium | Open | Approve/reject regenerated variations before promoting to live listing |
| 7 | Adapt image generation prompt for current from-scratch workflow | High | Open | User's template-swap prompt needs rewrite for Node 14 (Process Variations). See senior review in Session 0224-2. Key: keep from-scratch approach, add better style-matching rules, improve label logic |
| 8 | Create shared n8n deploy utility | Low | Open | Recurring `active` field + settings filter issue across deploy scripts. Extract to `n8n-deploy-utils.mjs` shared module |
| 9 | Check id=61 execution result | High | Open | v2 prompt deployed + webhook triggered for id=61 (ValueSnap RC Truck). Need to verify GPT output quality and downstream completion |
| 10 | Webapp webhook integration — document JSON format | Medium | Open | Full webhook payload format documented in session. Build into webapp's trigger UI |

---

## VM Bot Scripts

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | VM TT: Add auto-login fallback (Option B) to screenshot scripts | Medium | Open | If Chrome crashes or VM reboots, scripts fail until manual re-login. Auto-detect login page + enter credentials as fallback |
| 2 | VM TT: Auto-start Chrome with debug port on boot/login | Medium | Open | Create Windows Task Scheduler task to run `start_chrome_debug.bat` on user logon, so Chrome is always ready |
| 3 | VM TT: Fix `low_rating_0600` DB auth error | High | Open | Today's log shows "DB auth error" — database credentials issue, separate from the Selenium fix |
| 4 | VM TT: Apply same remote debugging fix to `TikTok.py` XPath | Low | Open | TikTok XPath `/div/div[1]/div[2]/button[2]` may also be stale if employee webapp UI changed. Needs verification once Chrome debug is running |

---

## General / Cross-Domain

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | _Add items as they come up_ | — | — | — |

---

## Completed / Resolved

| # | Item | Domain | Completed | Notes |
|---|------|--------|-----------|-------|
| — | — | — | — | — |
