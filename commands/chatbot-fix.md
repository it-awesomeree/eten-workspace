---
name: chatbot-fix
description: This skill should be used when a new GRBT ticket is raised about the Shopee chatbot, or the user asks to "fix the chatbot", "investigate chatbot issue", or "handle GRBT ticket". Follows Agnes's operational playbook for 5W1H investigation, root cause analysis, fix implementation, crosscheck, and non-technical Jira comment.
version: 1.0.0
---

# Shopee Chatbot Issue Fix Workflow

## Overview
End-to-end workflow for investigating and fixing Shopee chatbot issues reported via GRBT Jira tickets. Follows Agnes's operational playbook: investigate, propose, implement, crosscheck, document.

## When This Skill Applies
- New GRBT ticket about chatbot behavior
- CS team reports chatbot said something wrong
- Customer complaint about chatbot response
- Any chatbot escalation issue

## Workflow Steps

### Step 1: Investigate (5W1H)
Open the GRBT ticket in Jira. Read the ticket carefully, especially any screenshots of the chat conversation.

Identify:
- **What** went wrong — exact words the chatbot used that are problematic
- **Who** is affected — which customer, what order, what product
- **When** did it happen — timestamp of the chat
- **Where** in the system — which path in the Dify workflow produced this response
- **Why** it happened — root cause in the chatbot's instructions/templates
- **How** to fix — proposed solution

### Step 2: Check Middleware Layer (VMs)
Before diving into Dify, determine if the issue originates in the **Python middleware** on the chatbot VMs. Reference `/chatbot-middleware` for full details.

**When to suspect middleware**:
- Bot gave NO response at all
- Bot responded to the wrong message or out of context
- Bot is missing conversation history
- Issue involves message ordering or context loss

**Quick checks** (requires VM access via Tailscale):
1. Is the bot process running? → `vm_processes` on VM CBMY / VM CBC3
2. Are messages reaching Dify? → Check Dify logs/monitoring for traffic
3. How is CHAT_HISTORY being built? → `vm_read_file` to inspect the Python script
4. Are there errors in the middleware logs? → `vm_execute` to tail log files

**If middleware looks fine** → proceed to Step 3 (Dify investigation).
**If middleware is the issue** → fix the Python script, restart the bot via `vm_task_control`, then test.

### Step 3: Trace in Dify
1. Open the Dify workflow tab (cloud.dify.ai)
2. Fetch the workflow draft via API:
   ```javascript
   fetch('/console/api/apps/2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df/workflows/draft', {
     method: 'GET', credentials: 'include',
     headers: {'Content-Type': 'application/json'}
   }).then(r => r.json()).then(d => { window._workflowData = d; })
   ```
3. Search all node prompts for the problematic text/pattern
4. Identify which node(s) generated the bad response
5. Understand the instruction that led to the issue

### Step 3: Propose Fix
Present findings to the user:
- Root cause explanation (plain language)
- Which nodes are affected
- Recommended fix with before/after
- Any risks or side effects

Wait for user approval before implementing.

### Step 4: Implement Fix
1. Re-fetch the latest workflow draft (fresh data with current hash)
2. Apply the fix to ALL affected nodes (use `split().join()` for global replace, NOT `String.replace()` which only does first occurrence)
3. POST the updated workflow with the hash:
   ```javascript
   fetch('/console/api/apps/{id}/workflows/draft', {
     method: 'POST', credentials: 'include',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({ graph, features, environment_variables, conversation_variables, hash })
   })
   ```
4. Verify the POST returns HTTP 200 with a new hash
5. If 409 error: re-fetch, reapply, POST again with fresh hash

### Step 5: Senior Dev / Tech Lead Crosscheck
After implementing, run a thorough audit:
- Verify ALL old problematic text is removed (0 remaining)
- Verify new fix is present in all affected nodes
- Check for duplicate/corrupted text
- Check for any edge cases or missed nodes
- Run smoke tests via `mcp__dify__Shopee_Current_`
- Report findings honestly — flag any concerns

### Step 6: Publish
Click the Publish button in the Dify UI (API publish endpoint requires CSRF token, use the UI instead).

### Step 7: Comment on Jira (Non-Technical)
Edit or add a comment on the GRBT ticket. Rules:
- **NO technical details** — no node names, no LLM, no Dify, no API references
- **Explain in plain language** — "Why this happened" and "What has been fixed"
- The audience is CS team and management, not developers
- Use the actual Chinese/Malay words if relevant to explain the language issue
- Structure: "Why this happened:" → explanation → "What has been fixed:" → fix summary

### Step 8: Move Ticket
- Move the GRBT ticket to **Done** column
- Move to **TOP of Done** (right-click > Move work item > To the top)

### Step 9: Document
Update `shopee-chatbot.md` in memory:
- Add entry to Error Log with severity, root cause, affected nodes, fix applied
- Add entry to Changelog
- Update To-Do List if new follow-up items discovered

## Common Patterns

### Language Ambiguity Issues
Chinese words with double meanings (e.g., "升级" = escalate/upgrade). Fix: Use unambiguous words like "转交" (transfer).

### Unauthorized Promises
Chatbot promises actions it can't deliver (refunds, replacements, upgrades). Fix: Add "NEVER promise" guardrails and use fixed pre-approved text.

### Free-Form Template Issues
Templates that say "write a sentence conveying X" give LLM creative freedom. Fix: Replace with exact pre-approved text per language.

### Prompt Injection Bypass
Customer tricks chatbot into revealing system prompt or changing behavior. Fix: Add prompt injection defense blocks.

### Step 10: Update Knowledge Skill (if architecture changed)
If the fix changed the chatbot's architecture (added/removed nodes, changed models, modified escalation flow, added guardrails):
- Update `/dify-shopee-chatbot` skill with the changes
- Only patch the sections that changed (node count, GPT inventory, escalation logic, guard rails, incident history)
- Skip if the fix was prompt-text-only (wording tweak, not structural change)

## API Notes
- Auth: Cookie-based (`credentials: 'include'`)
- Hash: Required for POST (optimistic concurrency)
- Prompt location: `node.data.prompt_template[0].text`
- Global replace: Use `text.split(old).join(new)` not `text.replace(old, new)`
- Publish: Use UI button, not API (CSRF required)
