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
