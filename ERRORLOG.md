# Error Log — Eten

Errors encountered during development, with root causes and resolutions. Newest entries at the top.

---

## Template

```
### YYYY-MM-DD: [Error Title]
**Context**: What was being done when the error occurred
**Error**: The actual error message or behavior
**Root Cause**: What caused it
**Resolution**: How it was fixed
**Prevention**: How to avoid it in the future
```

---

### 2026-02-27: Cloudflare 524 kills regeneration that n8n is still processing
**Context**: Regenerating all images for product_id 46853536298 via n8n takes 14+ minutes, but Cloudflare proxy returns 524 at ~100s
**Error**: Frontend shows "Last AI request failed. AI service is temporarily unavailable (524)" — but n8n actually completed successfully
**Root Cause**: `n8n.barndoguru.com` is behind Cloudflare (DNS resolves to 2606:4700:* IPs). Cloudflare free/pro/business plans have ~100s proxy read timeout. Code-level 480s AbortController never fires because CF returns 524 first. Webapp catches the error and marks `n8n_job_status = 'failed'`, but n8n received the request and continues processing.
**Resolution**: (1) Return sentinel `{ __gatewayTimeout: true }` for 502/504/524 instead of throwing, (2) Keep job as "processing" — auto-completion detects n8n output on next page load, (3) Broadened `isRecoverableFailure` helper for safety net, (4) Frontend shows amber warning instead of red error
**Prevention**: For long-running n8n jobs behind Cloudflare, never rely on synchronous response. Fire-and-forget + poll for results.

### 2026-02-27: n8n $binary expression unreliable in Loop Over Items + IF node
**Context**: Has Binary? IF node checking `{{ Object.keys($binary).length > 0 }}` returned FALSE even though binary data was present on items
**Error**: Execution 660 and 661 — all items sent to FALSE branch, GCS upload skipped, resulting in 404 image URLs
**Root Cause**: `$binary` expression doesn't resolve to the item's binary data inside Loop Over Items v3 + IF node v2 with `typeValidation: "strict"`. The `$json` object IS accessible and contains `image_type` field set by the upstream Code node.
**Resolution**: Replaced both `$binary`-based conditions with `{{ $json.image_type !== "none" }}`, set `typeValidation: "loose"`. Deployed via n8n REST API PUT.
**Prevention**: In n8n, prefer `$json`-based checks over `$binary` in IF nodes, especially inside Loop Over Items. `$json` is reliably set by upstream Code nodes.

### 2026-02-26: n8n deploy script idempotency gap — Parse Webhook Data fix not pushed
**Context**: Re-deploying new_item_id changes to Variation Generation workflow after accidental revert
**Error**: `deploy-new-item-id-variation-gen.mjs` reported "Parse Webhook Data: added new_item_id" then "Already migrated to shopee_listing_products. Nothing to do." and exited without pushing
**Root Cause**: Script checks Prepare MySQL Data for `shopee_listing_products` as idempotency guard and calls `process.exit(0)` — this exits BEFORE Step 4 (push), so any fixes applied to other nodes (like Parse Webhook Data) in Steps 2-3 are lost
**Resolution**: Created `fix-parse-webhook.mjs` — targeted script that only fixes Parse Webhook Data and pushes immediately
**Prevention**: Deploy scripts should either (a) push after ALL node updates regardless of which were skipped, or (b) check idempotency per-node independently before exiting

### 2026-02-24: VM TT Selenium `SessionNotCreatedException` — Chrome not reachable on port 9222
**Context**: Testing updated Shopee.py with `debuggerAddress` on VM TT
**Error**: `session not created: cannot connect to chrome at 127.0.0.1:9222 from chrome not reachable`
**Root Cause**: Chrome was not started with `--remote-debugging-port=9222` before running the script
**Resolution**: Must run `start_chrome_debug.bat` first to launch Chrome with the debugging port
**Prevention**: Scripts depend on Chrome already running with debug port; add a pre-check or clear error message

### 2026-02-24: VM TT Selenium `driver.__del__()` kills Chrome between scrape and WhatsApp steps
**Context**: First version of fix used separate `setup_driver()` calls for scrape and WhatsApp send
**Error**: `SessionNotCreatedException` on WhatsApp step — Chrome gone despite scrape succeeding
**Root Cause**: After `scrape_shopee_report()` returned, the `driver` local variable went out of scope → Python GC called `driver.__del__()` → `driver.quit()` → all Chrome windows closed
**Resolution**: Changed to single shared driver in `main()`, passed to both functions, `driver.close()` only at the very end
**Prevention**: When using `debuggerAddress`, never let driver objects go out of scope mid-flow; share a single driver across all steps

### 2026-02-24: VM TT — Cannot launch GUI Chrome via WinRM
**Context**: Tried to start Chrome with debugging port remotely via `Start-Process` and `schtasks`
**Error**: Chrome processes started but no visible window on desktop; `Get-Process chrome` returned empty for `Start-Process`, and `schtasks /Run` also failed to show GUI
**Root Cause**: WinRM sessions run in Session 0 (non-interactive); GUI apps need the user's interactive session (Session 1)
**Resolution**: Used `Invoke-WmiMethod Win32_Process Create` which spawns in Session 0 (headless), OR user runs `start_chrome_debug.bat` manually from desktop
**Prevention**: For GUI apps on VMs, provide a batch file for the user to run manually; remote process creation via WinRM is non-interactive

### 2026-02-24: n8n PUT 400 — `active` is read-only (again, deploy-v2-prompt.mjs)
**Context**: Deploying v2 variation name prompt via `deploy-v2-prompt.mjs`
**Error**: `HTTP 400: request/body/active is read-only`
**Root Cause**: Same as previous — included `active: workflow.active` in PUT body
**Resolution**: Removed `active` field from PUT body in deploy script
**Prevention**: This keeps recurring in new deploy scripts. Consider creating a shared deploy utility that always strips `active` + filters settings.

### 2026-02-24: n8n PUT 400 — `active` is read-only
**Context**: Deploying bugfixes to Variation Generation workflow via PUT
**Error**: `HTTP 400: request/body/active is read-only`
**Root Cause**: Including `active: true` in the PUT body; n8n treats `active` as read-only in PUT
**Resolution**: Removed `active` field from PUT body; use separate POST `/activate` endpoint instead
**Prevention**: Never include `active` in PUT body; activation is a separate API call

### 2026-02-24: n8n Generate Variation Names — 60s timeout (ECONNABORTED)
**Context**: Testing regen workflow with id=52 (Pop Up Tent)
**Error**: `AxiosError: timeout of 60000ms exceeded` on Generate Variation Names node
**Root Cause**: GPT-5.2 API call with reasoning_effort=high sometimes exceeds 60s, especially for complex Chinese→English translation
**Resolution**: Increased timeout from 60s to 120s + added retry (3 tries, 5s wait) on both Generation and Regeneration workflows
**Prevention**: Always configure retries on external API calls; 60s is too low for reasoning models

### 2026-02-24: `typeof null === 'object'` crash in Parse Webhook Data
**Context**: Testing with id=46 where `1688_variation_images: [null, null]`
**Error**: `Cannot read properties of null (reading 'url')` — `varImg.url` when varImg is null
**Root Cause**: JavaScript `typeof null === 'object'` is true, so `(typeof varImg === 'object')` passed for null values
**Resolution**: Added null guard: `(varImg && typeof varImg === 'object')`
**Prevention**: Always null-check before typeof object checks in JavaScript

### 2026-02-24: n8n login field name — `emailOrLdapLoginId` not `email`
**Context**: Creating API key programmatically via n8n REST login
**Error**: `400 "code":"invalid_type","expected":"string","path":["emailOrLdapLoginId"]`
**Root Cause**: n8n login endpoint expects `emailOrLdapLoginId` field, not `email`
**Resolution**: Changed field name to `emailOrLdapLoginId`
**Prevention**: Check n8n REST API schema for exact field names

### 2026-02-24: MySQL MCP DDL blocked — `DDL operations are not allowed`
**Context**: Creating `shopee_variation_staging` table via MySQL MCP tool
**Error**: `DDL operations are not allowed for schema 'requestDatabase'`
**Root Cause**: MCP MySQL tool has DDL permissions disabled for that schema
**Resolution**: Provided CREATE TABLE SQL to user to run manually
**Prevention**: DDL must be run directly on the database server or by a user with DDL permissions

### 2026-02-23: n8n API PATCH 405 — Method Not Allowed
**Context**: Deploying workflow updates via n8n REST API
**Error**: `HTTP 405: PATCH method not allowed`
**Root Cause**: n8n v2.35.2 API uses PUT (full replacement), not PATCH (partial update) for workflow updates
**Resolution**: Changed `method: 'PATCH'` to `method: 'PUT'` in deploy script, sending full workflow body
**Prevention**: Check n8n API docs for supported HTTP methods; PUT is the standard for workflow updates

### 2026-02-23: n8n PUT 400 — Settings Must NOT Have Additional Properties
**Context**: PUTting updated workflow back to n8n
**Error**: `HTTP 400: settings must NOT have additional properties`
**Root Cause**: GET response includes settings like `availableInMCP`, `binaryMode` that PUT rejects as unknown
**Resolution**: Filter settings to allowlist of safe keys: `executionOrder`, `callerPolicy`, `errorWorkflow`, `timezone`, etc.
**Prevention**: Never pass settings object as-is from GET to PUT; always filter to known-safe keys

### 2026-02-23: n8n "JSON parameter needs to be valid JSON" (x2)
**Context**: GPT-5.2 httpRequest nodes failing after first deployment
**Error**: `JSON parameter needs to be valid JSON` on Generate Variation Names node
**Root Cause (attempt 1)**: Wrong field names in user prompt expressions (`existing_tier1_name` should be `tier_name_1`) + inline `{{ }}` expressions producing values with quotes/newlines breaking JSON structure
**Root Cause (attempt 2)**: `user_prompt_template` in JSON files had `={{ JSON.stringify(...) }}` — the leading `=` caused double expression nesting inside the already `=`-prefixed jsonBody
**Resolution**: (1) Corrected all field names to match workflow data, (2) switched to `{{ JSON.stringify(...) }}` unquoted pattern, (3) removed `=` prefix from template values in JSON files
**Prevention**: n8n expression rules: `=` prefix makes entire string an expression template; `{{ }}` inside are sub-expressions; `JSON.stringify()` output must be UNQUOTED; never nest `=` inside `=`

### 2026-02-23: MySQL "Table 'requestDatabase.shopee_existing_listing' doesn't exist"
**Context**: Workflow attempting to update MySQL after successful generation
**Error**: `Table 'requestDatabase.shopee_existing_listing' doesn't exist`
**Root Cause**: MySQL credential defaults to `requestDatabase` schema, but the table lives in `webapp_test`
**Resolution**: Qualified table name to `webapp_test.shopee_existing_listing` in the Prepare MySQL Data code node
**Prevention**: Always use fully qualified table names (`schema.table`) in SQL queries when the MySQL credential may default to a different schema
