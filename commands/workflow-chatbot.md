---
description: Standard workflow for Dify chatbot & n8n bug fixes and feature tickets (GRBT / AW chatbot)
argument-hint: [TICKET-ID e.g. GRBT-160 or AW-258]
---

# Dify Chatbot & n8n — Fix Workflow

Standard workflow for investigating, fixing, reviewing, testing, publishing, and documenting chatbot/n8n issues.

**Ticket:** $ARGUMENTS

## Workflow Steps

### Step 1 — Study Jira Ticket
- Navigate to the Jira ticket
- Read description, attachments, comments, status, assignee
- Understand the reported issue fully before touching Dify/n8n

### Step 2 — Study the System on Dify/n8n

#### Step 2a — Check Middleware Layer (Chatbot tickets only)
Before investigating Dify nodes, check if the issue originates in the **Python middleware** on the chatbot VMs. Reference `/chatbot-middleware` for full architecture and debugging decision tree.

- **VM CBMY**: `hiranai-ai`, `murahya-ai`, `chatbot-script` (Shopee MY)
- **VM CBC3**: `ai-chatbot` (additional store)
- **VM CBSG**: `sg-auto-clicker` (SG, not AI-connected — skip)

Quick checks (requires VM access):
1. Bot process running? → `vm_processes`
2. Messages reaching Dify? → Dify monitoring/logs
3. CHAT_HISTORY correctly built? → `vm_read_file` on Python script
4. Middleware logs show errors? → `vm_execute` to tail logs

**If the issue is about missing context, wrong message, no response, or message ordering** → the root cause is likely in the middleware, not Dify.

#### Step 2b — Study Dify/n8n Workflow
- Open the relevant workflow (Shopee chatbot on Dify, or n8n workflow)
- Examine the relevant nodes, trace the flow
- Identify which nodes are involved and what the expected vs actual behavior is

### Step 3 — Comprehensive Debugging Analysis
- Document root cause with numbered contributing factors
- Use a scratchpad approach: predictions, hypotheses, evidence
- Map out which nodes/fields need changes and why

### Step 4 — Root Cause Classification (Bug Fix Tickets Only)

> **Skip this step if the ticket is a feature request or enhancement — only applies to bug fixes.**

Using the evidence from Step 3, classify the root cause into one of the categories below. This classification exists to **improve systems and processes** — not to assign individual blame.

#### Classification Categories

| Category | Definition | Examples |
|----------|-----------|----------|
| **System/Code Defect** | The chatbot logic, node configuration, or workflow architecture produced incorrect behavior | Wrong condition in IF node, missing branch, incorrect LLM prompt, broken variable reference, logic gap in workflow |
| **Configuration/Environment Issue** | Correct workflow exists but was published with incorrect settings, API keys, or model parameters | Wrong model selected, incorrect API endpoint, expired credentials, wrong environment variable |
| **Data/Input Anomaly** | The chatbot received unexpected, malformed, or edge-case user input it wasn't designed to handle | Unusual language mix, unexpected emoji/special characters, ambiguous phrasing the LLM misinterpreted, PII in unexpected format |
| **Process/Workflow Gap** | A missing or unclear process allowed the issue to reach production — the process needs improvement, not any individual | No pre-publish QA checklist, missing regression test for this path, unclear escalation criteria, no monitoring for this node type |

#### How to Classify

1. Review all evidence gathered in Step 3
2. Ask the **replay test**: "If we replayed the exact same sequence of events with a different person performing every action, would the bug still occur?"
   - **Yes** → Likely **System/Code Defect** or **Process/Workflow Gap** (the system allowed it to happen)
   - **No** → Likely **Configuration/Environment Issue** or **Data/Input Anomaly** (specific conditions triggered it)
3. For each contributing factor identified in Step 3, assign one category
4. Identify the **primary** root cause category — the one that, if addressed, would have prevented the issue entirely

#### Writing Rules — Neutral, Factual, System-Focused

Always frame findings as **systemic observations**, never personal attribution:

| DO (system-focused) | DON'T (blame-focused) |
|---|---|
| "The workflow does not include a language-detection node before routing, which caused Malay input to be processed by the English-only branch" | "The developer forgot to add language detection" |
| "The LLM prompt does not include instructions for handling PII, resulting in the bot asking for additional personal details" | "Agnes wrote the prompt wrong" |
| "The pre-publish checklist does not include a regression test for the returns flow, which allowed a broken path to go live" | "QA missed this during testing" |
| "The IF node condition uses exact string matching instead of contains, causing it to fail on inputs with trailing whitespace" | "Someone set the condition incorrectly" |

#### Output — Include in Debugging Notes

```
ROOT CAUSE CLASSIFICATION
─────────────────────────
Category: [System/Code Defect | Configuration/Environment Issue | Data/Input Anomaly | Process/Workflow Gap]
Summary:  [1–2 sentence factual description of what happened]
Evidence: [Key facts from Step 3 that support this classification]
Prevention: [What systemic change — code fix, process improvement, or automation — would prevent recurrence]
```

> **Note:** This classification feeds into the Jira comment (Step 12) and GitHub documentation (Step 11) for trend tracking. Over time, it helps the team identify whether recurring issues are systemic and where to invest in prevention.

---

### Step 5 — Review 1: Senior AI Engineer (Chatbot & n8n)
- Review the proposed fix as a **senior AI engineer specializing in chatbots and n8n**
- Check: correctness, edge cases, platform policy compliance, regression risk
- Approve / modify / reject the fix
- If rejected, return to Step 3

### Step 6 — Review 2: Senior AI Tester/QA Crosscheck
- Crosscheck the approved fix as a **senior AI tester/QA**
- Validate: test coverage completeness, edge case coverage, regression test plan
- Confirm the fix doesn't break existing working paths
- Approve / modify / reject
- If rejected, return to Step 5

### Step 7 — Run Tests: Senior QA + SRE
- Execute fix validation tests (does the fix solve the reported issue?)
- Execute regression tests (do existing working paths still work?)
- Run reliability/infra checks (error handling, timeouts, model availability)
- All tests must pass before proceeding

### Step 8 — Branch: Who did the work?

Check the ticket assignee to determine the path forward:

#### Path A — Done by me (Agnes / Claude Code)
Continue to Step 9.

#### Path B — Done by a developer
Skip Steps 9–11. Go directly to **Step 8B**.

---

### Step 8B — Send Technical Review Comment to Developer (Path B only)
- Post a **technical** comment on the Jira ticket summarizing the review findings
- Include: what was reviewed, issues found (with node names, field details, logic errors), what passed, what failed
- Include the **Root Cause Classification** from Step 4 (if applicable) using neutral language
- If issues found: clearly list each issue with severity (critical/moderate/minor) and what the dev needs to fix
- If all passed: state the review passed and what was verified
- Use the Jira REST API to avoid keyboard shortcut issues
- **Do NOT implement any fix** — the developer owns the fix
- After posting, proceed to close:
  - If review **passed**: move ticket to DONE
  - If review **failed**: leave ticket in TO REVIEW (dev will see the comment and fix)

---

### Step 9 — Implement the Fix (Path A only)
- **Only proceed if all reviews pass with zero errors**
- Edit the node(s) via Dify/n8n API or UI
- Save draft with hash-based concurrency (Dify) or proper versioning (n8n)

### Step 10 — Publish to Production (Path A only)
- Run Senior Dev Review Crosscheck (per CLAUDE.md mandatory rule)
- Publish the workflow live on Dify/n8n
- Verify the published version is active

### Step 11 — Document in GitHub (Path A only)
- Update `CHANGELOG.md` with date, ticket, and change table
- Create `incidents/{TICKET-ID}.md` using the `_TEMPLATE.md` format
- Include the **Root Cause Classification** in the incident file
- Update `docs/architecture.md` if node structure changed
- Commit and push to the relevant ops repo (`shopee-chatbot-ops` or `tiktok-chatbot-ops`)

### Step 12 — Write Jira Comment & Close (Path A only)
- Post a **non-technical** comment on the GRBT ticket (users know nothing about tools/code)
- Explain: what was the problem, what was fixed, how it was tested
- Include root cause classification in plain language (e.g., "This was caused by a system logic gap" not "Code Defect in IF node")
- Use the Jira REST API to avoid keyboard shortcut issues
- Transition the ticket to the **DONE** column
- Place it at the **top** of the Done column

### Step 13 — Update Knowledge Skills (Path A only, if architecture changed)

If the fix changed the chatbot's architecture (added/removed/renamed nodes, changed models, modified escalation flow, added guardrails, changed conversation paths), update the relevant knowledge skill:

- **Shopee chatbot changes** → Update `/dify-shopee-chatbot` skill:
  - Node count, GPT node inventory, conversation flow, escalation logic, guard rails, incident history
- **TikTok chatbot changes** → Update `/dify-tiktok-chatbot` skill:
  - Node count, LLM node inventory, conversation flow, escalation logic, guard rails, backlog items
- **n8n workflow changes** → Update `/n8n-workflows` skill:
  - Workflow inventory, node changes, active status

**What to update**: Only the sections that actually changed. Don't re-audit everything — just patch the relevant sections.

**Skip this step** if the fix was prompt-text-only (e.g., tweaking wording in an existing guardrail without changing the architecture).

---

## CRITICAL RULES

- **NEVER publish without completing Steps 5-7 (reviews + tests)**
- **NEVER direct customers to contact external customer service** (Shopee/TikTok policy violation)
- **ALWAYS run regression tests** — fixing one path must not break another
- **ALWAYS document in GitHub** before closing the ticket
- For GRBT tickets: Jira comments must be **non-technical**
- For AW chatbot tickets: Jira comments should be **technical**
- Root Cause Classification must use **neutral, system-focused language** — never attribute blame to individuals
