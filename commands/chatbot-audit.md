---
name: chatbot-audit
description: This skill should be used when the user asks to "audit the chatbot", "check chatbot health", "verify chatbot nodes", or wants a quick health check on the Shopee Dify chatbot workflow. Runs a comprehensive audit of all GPT node models, escalation templates, guardrails, and compliance checks.
version: 1.0.0
---

# Shopee Chatbot Audit

## Overview
Run a comprehensive health check on the Shopee (Current) Dify chatbot workflow. Verifies all GPT node models are correct, escalation templates use fixed pre-approved text, guardrails are in place, and no unsafe patterns exist.

## When This Skill Applies
- After any change to the Dify chatbot workflow
- When a new GRBT ticket is raised about chatbot behavior
- Periodic health check (weekly recommended)
- Before and after publishing workflow changes

## Reference
- Full documentation in memory: `shopee-chatbot.md`
- Dify App ID: `2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df`
- API: `/console/api/apps/2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df/workflows/draft`

## Audit Checklist

### 1. Model Verification (17 nodes)
Fetch the workflow draft via Dify API (browser console on cloud.dify.ai tab, using `fetch()` with `credentials: 'include'`). For each node with a GPT model, verify:
- **7 nodes should be on gpt-5-mini**: Question Classifier, Parameter Extractor, Parameter Extractor (1), Parameter Extractor 3, Translator, Check Question need Product info, To check question can be answered or no
- **10 nodes should be on gpt-5.2**: LLM 4, LLM 7, LLM 8, Image Analysis for Customer Service, Image Customer Service Handler, Check knowledge base (1), LLM 7 (1), LLM 11, LLM 8 (1), CS ESCALATION (PRODUCT PATH)
- Report any mismatches as FAIL

### 2. Escalation Template Check
Search all node prompts for these OLD patterns that should NOT exist:
- `write a single casual and friendly sentence conveying` — old free-form template
- `Vary the wording each time` — old creative-freedom instruction
- `use different synonyms and sentence structures` — old variation instruction

Search for these NEW patterns that SHOULD exist:
- `EXACT pre-approved message` — fixed text instruction
- `转交` — Chinese "transfer" (correct word)
- `NEVER promise` or `NEVER promise any specific actions` — guardrail

### 3. Unsafe Word Check
Search all prompts for the word `升级` (upgrade). It should ONLY appear in "NEVER use" guardrail context, never in a response template or example.

### 4. Compliance Check
Verify these compliance features are present:
- PII blocking rules (phone, email, IC, bank details)
- Prompt injection defense blocks
- `[HUMAN_ESCALATION]` tag usage for escalation routing
- Compliance tracking nodes logging events

### 5. Report Format
Present results as a table:

| Check | Status | Details |
|-------|--------|---------|
| Model verification (17 nodes) | PASS/FAIL | X/17 correct |
| Old templates removed | PASS/FAIL | X remaining |
| Fixed text present | PASS/FAIL | X instances |
| Guardrails present | PASS/FAIL | X instances |
| Unsafe 升级 usage | PASS/FAIL | X unsafe occurrences |
| PII blocking | PASS/FAIL | |
| Prompt injection defense | PASS/FAIL | |

## API Notes
- Auth is cookie-based. Use browser console on the Dify tab with `credentials: 'include'`.
- Prompt data is in `node.data.prompt_template[0].text` (array of `{role, text}` objects).
- Use `console.log()` + `read_console_messages` to extract data (extension blocks some direct returns).
