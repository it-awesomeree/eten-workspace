# Work Log — Eten

Session-by-session record of work done. Newest entries at the top.

---

## W10: Feb 24, 2026

### Session 0224-1: Shopee Listing New Variation Regeneration — Full Regen Support + Bugfixes

**Workflows**: Variation Generation (`_nYkX49YkTfTdwWTsDjM1`) + Variation Regeneration (`rKOMjD071lkvvZDe`)

**What was done**:

**Bugfixes deployed to Variation Generation**:
- Bug 2: Process Variations timeout — sequential → parallel batch processing (BATCH_SIZE=3)
- Bug 4: Hardcoded database name — centralized `target_database` in SET API KEY node
- Bug 6: No execution timeout — added `executionTimeout: 600` (10 min)
- Bug 1: GCS empty batch crash — added "Check Has Images" IF node
- Bug 1b: Parse Webhook Data null image crash — null guard for `typeof null === 'object'`

**Regeneration support added to Variation Regeneration (`rKOMjD071lkvvZDe`)**:
- 2 Gate IF nodes: Gate: Variation Names, Gate: Description — skip GPT calls when not regenerating
- Parse Webhook Data: parses `regenerate[]`, `current_outputs`, computes skip flags
- Extract Variation Names / Description: passthrough from `current_outputs` when skipping
- Process Variations: skips Gemini image gen when `skip_variation_image` is true
- Prepare MySQL Data: regen → INSERT INTO `shopee_variation_staging`; normal → UPDATE `shopee_existing_listing`
- Webhook path: `regenerate-variation-description` (distinct from Generation workflow)

**New table**: `requestDatabase.shopee_variation_staging` (separate from `shopee_listings_staging` — different column schema for variation vs product workflows)

**Timeout fix (both workflows)**: Generate Variation Names 60s → 120s + retry (3 tries, 5s wait)

**n8n API key**: Created programmatically via REST login + POST /rest/api-keys

**Deploy scripts**: `deploy-bugfixes.mjs`, `deploy-bug1-fix.mjs`, `deploy-bug1b-fix.mjs`, `deploy-regen-support.mjs`, `deploy-regen-staging.mjs`, `create-api-key.mjs`, `test-id46.mjs`, `test-id52.mjs`, `test-regen-id52.mjs`, `monitor-exec.mjs`

**Tools used**: n8n REST API, Node.js, MySQL DDL via VM, GPT-5.2, Gemini Vision

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
