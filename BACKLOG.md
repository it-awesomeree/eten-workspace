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

---

## VM Bot Scripts

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | _Add items as they come up_ | — | — | — |

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
