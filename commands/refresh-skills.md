---
description: Automated audit and refresh of all knowledge skills - checks for drift and updates stale skills
argument-hint: [all | skill-name e.g. mysql-schema | quick-check]
---

# Refresh Knowledge Skills

Automated audit that checks each knowledge skill against live platform data, detects drift, and updates stale skills.

**Target:** $ARGUMENTS (default: all)

---

## Quick Check Mode (if argument is "quick-check")

Run a fast drift detection across all skills without updating. Report a table of skill health:

| Skill | Expected | Actual | Status |
|-------|----------|--------|--------|

Checks to run:
1. **mysql-schema**: `SHOW DATABASES;` then count tables per DB. Compare against skill's documented counts.
2. **vm-inventory**: `vm_inventory` MCP tool. Compare VM count and bot count against skill.
3. **n8n-workflows**: `n8n_list_workflows`. Compare workflow count and active count against skill.
4. **github-repos**: `mcp__github__search_repositories` for `user:it-awesomeree`. Compare repo count.
5. **dify-shopee-chatbot**: Fetch workflow draft via browser, count nodes. Compare against skill's "69 nodes".
6. **dify-tiktok-chatbot**: Fetch workflow draft, count nodes. Compare against skill's "42 nodes".
7. **jira**: Check team roster via board view. Compare against skill's assignee list.

If all match: "All skills are current." If drift detected: list which skills need refresh and what changed.

---

## Full Refresh Mode (default or "all")

Run full audits in parallel using Task agents, then update each stale skill.

### Step 1: Audit all platforms in parallel

Launch 7 parallel Task agents (same as the initial audit process):

1. **MySQL**: Query all databases, tables, row counts. Compare against `/mysql-schema`.
2. **VMs**: Get full inventory, check statuses/processes. Compare against `/vm-inventory`.
3. **n8n**: List all workflows, get details on active ones. Compare against `/n8n-workflows`.
4. **GitHub**: Search all repos, check branches. Compare against `/github-repos`.
5. **Dify Shopee**: Fetch workflow draft, count nodes, check models. Compare against `/dify-shopee-chatbot`.
6. **Dify TikTok**: Fetch workflow draft, count nodes, check models. Compare against `/dify-tiktok-chatbot`.
7. **Jira**: Check board via browser, verify team roster and columns. Compare against `/jira`.

### Step 2: Detect drift

For each skill, compare the audit results against the current skill file. Flag as:
- **Current**: No meaningful changes detected
- **Drift detected**: Specific differences found (list them)
- **Major change**: Structure significantly different (new tables, new VMs, new nodes, etc.)

### Step 3: Update stale skills

For each skill with drift:
- Read the current skill file
- Patch only the sections that changed (don't rewrite the whole file)
- Preserve the skill's structure, navigation tips, and MCP tool references
- Update the "Last Verified" date

### Step 4: Report

Output a summary table:

| Skill | Status | Changes |
|-------|--------|---------|
| mysql-schema | Updated | 3 new tables added to requestDatabase |
| vm-inventory | Current | No changes |
| ... | ... | ... |

### Step 5: Sync to GitHub

After all updates, run `/syncskills` to push changes to GitHub.

---

## Single Skill Refresh (if argument is a specific skill name)

Only refresh the named skill. Run the relevant audit, compare, update if needed.

Valid skill names: `mysql-schema`, `vm-inventory`, `n8n-workflows`, `github-repos`, `dify-shopee-chatbot`, `dify-tiktok-chatbot`, `jira`

---

## Freshness Schedule

| Skill | Risk Level | Recommended Refresh |
|-------|-----------|-------------------|
| github-repos | Low | Quarterly |
| jira | Low | Quarterly |
| vm-inventory | Medium | Monthly |
| mysql-schema | Medium | Monthly |
| n8n-workflows | Medium | Monthly |
| dify-shopee-chatbot | High | After every chatbot fix (auto via /chatbot-fix and /workflow-chatbot) |
| dify-tiktok-chatbot | High | After every chatbot fix (auto via /chatbot-fix and /workflow-chatbot) |
