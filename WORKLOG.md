# Work Log — Eten

Session-by-session record of work done. Newest entries at the top.

---

## W11: Feb 26, 2026

### Session 0226-1: Data Cleanup — Fix Display Issues for Shared product_ids

**Context**: After new_item_id migration (Phases 1-4), existing data was corrupt from old backfill. 224 of 555 events had no product row, 37 had wrong item_type, 61 collision products had mixed/wrong 1688 data.

**What was done**:

**Step 1 — Fix item_type mismatches (SQL)**:
- Ran UPDATE on both `requestDatabase` and `webapp_test` to fix 37 product rows where `item_type = 'new_product'` but linked `new_items.launch_type = 'New Variation'`
- Verified: 0 mismatches remaining on both databases

**Step 2 — Delete corrupt collision data (SQL)**:
- Identified 63 product_ids with multiple events (both New Product + New Variation)
- Deleted all product rows + variation rows for collision product_ids on both databases
- Verified: 0 collision product rows, 0 collision variation rows remaining
- Post-cleanup state: 270 correct products (requestDatabase), 264 (webapp_test), 285+ missing events awaiting scraper re-run

**Step 3 — Scrapers already running**:
- Confirmed scrapers (updated in Phase 2) are already populating data correctly
- Verified product_id 9193675690: new_item_id 429 (Toilet Cleaner, 2 vars) and 485 (Expanding Foam, 1 var) already created with correct isolated data
- new_item_id 397 (Glue Gun / New Product) not yet scraped — awaiting New Product scraper

**n8n Workflow Fix — Parse Webhook Data**:
- User accidentally reverted changes to Shopee Listing New Variation Generation workflow (`_nYkX49YkTfTdwWTsDjM1`)
- Diagnosed: "Prepare MySQL Data" node was intact (already had new_item_id code), but "Parse Webhook Data" was missing `new_item_id` extraction
- Deploy script's idempotency check on Prepare MySQL Data caused early exit before pushing Parse Webhook Data fix
- Created `fix-parse-webhook.mjs` to push just the Parse Webhook Data fix
- Deployed successfully — version `ba68a222`, verified `new_item_id` present

**Files created**: `n8n-updates/fix-parse-webhook.mjs`

**Tools used**: MySQL MCP, n8n REST API, Node.js

**Key decisions**:
- Delete collision data rather than attempt repair — scrapers will recreate correctly with per-new_item_id isolation
- Fix deploy script idempotency gap by creating targeted single-node fix script

---

## W10: Feb 24, 2026

### Session 0224-2: Variation Name Prompt v2 + Image Generation Prompt Review

**Workflow**: Shopee Listing New Variation Generation (`_nYkX49YkTfTdwWTsDjM1`)

**What was done**:

**Webhook JSON format documentation**:
- Documented the full webhook POST payload format for triggering from webapp
- Verified with id=55 (MasonGym Pilates Bar) — user sent test data, webhook triggered successfully (Execution #620, all 20 nodes passed)

**New variation name prompt (v2) — reviewed, adapted, deployed**:
- User provided a new per-variation prompt with comparator logic, reserved names, positioning_hint
- **Senior review identified 7 incompatibilities**: per-variation loop (no loop node), output schema mismatch (downstream parser expects `new_variation_names[].generated_name`), 7/12 input variables don't exist, comparator node doesn't exist
- **Adapted to Option 2**: rewrote prompt for batch mode, removed comparator/reserved names/positioning_hint, kept same output schema + user_prompt_template
- Key improvements over v1: explicit tier-count inference, normalization spec for uniqueness, cross-candidate uniqueness, abbreviation rules, input parsing notes
- Saved as `node2-generate-variation-names-prompt-v2.json`
- **Deployed via `deploy-v2-prompt.mjs`** — system prompt updated (4503 → 9489 chars), verified in n8n
- **Tested with id=61** (ValueSnap RC Truck) — webhook triggered, workflow started (awaiting result check tomorrow)

**Image generation prompt — senior review (no changes)**:
- User provided a template-swap based image generation prompt
- **Reviewed against current workflow (Node 14: Process Variations)** — identified fundamental incompatibilities:
  - Template-swap approach vs current from-scratch generation
  - `newVariationsJson` structured input doesn't exist (current uses plain string `generated_variation_names[i]`)
  - FAIL/SKIP text output not handled downstream (expects binary image always)
  - `existingTierCount`/`targetTier` variables don't exist
  - Text replacement logic overcomplicated for typical Shopee variation images
- **Verdict**: NOT compatible as-is, needs adaptation (same as variation name prompt)
- **Status**: Review complete, adaptation deferred to next session

**Files created**: `node2-generate-variation-names-prompt-v2.json`, `deploy-v2-prompt.mjs`

**Tools used**: n8n REST API (GET/PUT), MySQL MCP, Node.js, GPT-5.2

**Key decisions**:
- Adapt prompts to workflow (Option 2) rather than restructure workflow (Option 1)
- Keep same output schema to avoid breaking downstream parser
- Keep same user_prompt_template (n8n expressions unchanged)

---

### Session 0224-3: VM TT schedule.py Investigation & Shopee/TikTok Screenshot Script Fix

**VM**: VM TT (port 65504, role: scheduler, bot: tiktok-schedule)

**What was done**:
- **Investigation**: Diagnosed why Shopee SG, Shopee MY, and TikTok WhatsApp notifications stopped sending
  - `schedule.py` (APScheduler) was running correctly — all 7 jobs firing on time (mon-fri)
  - Root cause: All 3 screenshot scripts (`Shopee.py`, `SGShopee.py`, `TikTok.py`) crashing at `scrape_shopee_report()` with Selenium `TimeoutException` on export button XPath
  - Deeper root cause: `employee.awesomeree.com.my` webapp requires login, but Chrome profile had **zero awesomeree cookies** (only 4 cookies total: google + whatsapp). Session cookies destroyed each run because scripts killed Chrome before launching new instance
  - Broken since ~Jan 27, 2026 (1 month of silent failures, all rc=1)

- **Fix — Chrome Remote Debugging (Option A)**:
  - Rewrote `setup_driver()` in all 3 scripts to connect via `debuggerAddress` on port 9222 instead of launching/killing Chrome
  - Changed from two separate driver connections to **single shared driver** per script — avoids Python GC `__del__()` → `quit()` killing Chrome between scrape and WhatsApp steps
  - Replaced `driver.quit()` with `driver.close()` (closes only the work tab)
  - Created `start_chrome_debug.bat` to launch Chrome with `--remote-debugging-port=9222`

- **Files modified on VM TT** (`C:\Users\Admin\Desktop\schedule\Screenshots my sg tt\`):
  - `Shopee.py` (Shopee MY — backup: `.bak.20260224103421`)
  - `SGShopee.py` (Shopee SG — backup: `.bak.20260224103439`)
  - `TikTok.py` (TikTok — backup: `.bak.20260224112826`)
  - `start_chrome_debug.bat` (new file in `schedule\`)

- **Tested**: User manually ran updated Shopee.py — confirmed working

**Tools used**: VM Control Plane MCP (vm_execute, vm_write_file, vm_read_file, vm_status, vm_inventory), Python sqlite3 cookie DB inspection

**Key decisions**:
- Single driver per script run prevents Python GC from killing Chrome between steps
- Chrome must be started once with `start_chrome_debug.bat` + manual login; session persists while Chrome runs
- Future: Option B (auto-login) as fallback if Chrome crashes become frequent

**Also discovered**: `low_rating_0600` failing with "DB auth error" — separate issue, not addressed

---

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
