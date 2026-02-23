# Work Log — Eten

Session-by-session record of work done. Newest entries at the top.

---

## W09: Feb 23, 2026+

### Session 0223-2: n8n Shopee Listing New Variation Generation — 5-Node Enhancement + Deployment

**Workflow**: Shopee Listing New Variation Generation (`_nYkX49YkTfTdwWTsDjM1`)

**What was done**:
- Enhanced 5 core nodes in the n8n workflow via REST API (PUT):
  - **Generate Variation Names** (httpRequest): Replaced comparator prompt with pattern-matching name generator (analyzes existing Shopee naming style, generates matching names from 1688 data)
  - **Generate Description** (httpRequest): Replaced full-rewrite prompt with append/merge updater (preserves existing description as base, only adds new variation info)
  - **Extract Variation Names** (code): Multi-format parser with CJK stripping, 20-char enforcement, fallback chain
  - **Extract Description** (code): Merge validation, markdown stripping, 2999-char smart truncation, fallback to existing description
  - **Validate Variations** (code): Real validation replacing stub — name length, image MIME/size/dimensions, aspect ratio checks
- Built deployment tooling: `deploy.mjs`, `check-latest.mjs`, `check-execution.mjs`, `test-webhook.mjs`, `verify.mjs`
- Fixed MySQL table reference: `requestDatabase.shopee_existing_listing` → `webapp_test.shopee_existing_listing`
- Successfully tested end-to-end via webhook (Execution #603 — all 21 nodes passed, 94s)

**Tools used**: n8n REST API (PUT), Node.js scripts, GPT-5.2, Gemini Vision

**Key decisions**:
- Use `{{ JSON.stringify(...) }}` unquoted pattern for safe JSON encoding in n8n expression templates
- Filter workflow settings to safe keys only when PUTting (n8n rejects unknown settings fields)
- Fall back to existing description (not empty string) on generation failure

### Session 0223-3: Skill Creation + Git Remote Fix
- Created `/endsession` skill adapted from agnes-workspace for Eten's use
- Updated `~/eten-workspace` git remote from `Eten24/eten-workspace` → `it-awesomeree/eten-workspace`

### Session 0223-1: Workspace Setup
- Created `Eten24/eten-workspace` repo on GitHub
- Cloned all 21 command files from `it-awesomeree/agnes-workspace`
- Created personalized documentation: CLAUDE.md, README.md, SKILLS.md, WORKLOG.md, ERRORLOG.md, BACKLOG.md
- Created dev notes: getting-started, contributing, cicd, skills-and-technologies, lessons-learned
- **Outcome**: Workspace fully set up and pushed to GitHub
