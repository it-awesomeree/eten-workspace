---
description: Dify TikTok chatbot - 48-node chatflow, 13 LLM nodes, escalation logic, gaps vs Shopee, and navigation guide
argument-hint: [node name, issue, or what you're debugging]
---

# TikTok Dify Chatbot

**Platform**: Dify Cloud (cloud.dify.ai)
**App Name**: TikTok Chat
**App ID**: `099dbd92-1c63-4d87-b484-7e8780440181`
**Type**: advanced-chat (chatflow) -- NOT workflow (unlike Shopee)
**Total Nodes**: 48 (13 LLM, 7 code, 11 template-transform, 7 answer, 3 knowledge-retrieval, 3 parameter-extractor, 3 if-else, 1 start)
**LLM Nodes**: 13
**MCP Tool**: `mcp__tiktok-chat__TikTok_Chat`
**MCP Endpoint**: `https://api.dify.ai/mcp/server/KjYNxSSL1Z2sLZdV/mcp`
**Ops Repo**: `chatbot-ops` → `tiktok/` (GitHub)

---

## Conversation Flow

```
START -> PE (1) [Extract question, candidate_id, shop_name]
           |
        LLM 7 (gpt-5-mini) [Intent: Product/General/Human]
           |
     IF/ELSE 3
     /        |         \
  Human    General     Product
    |         |            |
 Answer 7  LLM 10(1)    PE [Extract question, candidate_id]
 "HUMAN"  (gpt-5.2)       |
    |     Fallback      Template [Combine q + candidate_id]
   END       |            |
         Template 11(1)  PE2 [Extract sku, variation_kw, attr_kw]
         (HUMAN check)     |
              |         IF/ELSE [SKU routing]
         Answer 8(1)    /    |    \    \
                    SKU    no ID  q+sku  q+product
                   found  (795e) (969c)  (b580)
                     |      |      |       |
                 Knowledge  LLM(1) |   Knowledge
                 Retrieval  general|   Retrieval 2
                     |      |      |       |
                  LLM main  |      |   Template 20
                  (gpt-5.2) |      |   (Parse SKUs)
                     |      |      |       |
                  LLM(4)  LLM(5)   |    LLM 8
                  gate    gate     |   (Question parser)
                     |      |      |       |
                  Answer Answer 4  |   IF/ELSE 4
                                   |   /    |    \
                                  NEED  GEN   ANS
                                   |    |      |
                                 KR3  LLM(2) LLM 10
                                   |  variation var.list
                                 LLM(1)  |      |
                                detail LLM(3) LLM(4)
                                   |   gate   gate
                                 LLM(4)  |      |
                                 gate  Ans9(1) Ans8
                                   |
                                 Ans9
```

---

## LLM Node Inventory

### Response Generators (6 nodes, gpt-5.2) -- customer-visible output
| Node | ID | Purpose |
|------|----|---------|
| LLM | `llm` | Main product support (fed by Knowledge Retrieval) |
| LLM (1) | `17452230115260` | Product detail (fed by KR3) |
| LLM (1) | `17453054480730` | General query (no KB -- escalates if product question) |
| LLM (2) | `17455566047520` | Product variation handler |
| LLM 10 | `1745229622274` | Variation list handler |
| LLM 10 (1) | `17455716141261` | Fallback/escalation (broadest special cases) |

### Routing & Classification (2 nodes, gpt-5-mini)
| Node | ID | Purpose | Output |
|------|----|---------|--------|
| LLM 7 | `1745568390974` | Intent router | One word: `Product`, `General`, or `Human` |
| LLM 8 | `1745222310274` | Question parser | JSON: `{need_desc, general, answer, chosen_sku}` |

### Quality Gates (5 nodes, gpt-5-mini) -- check if LLM answer is sufficient
| Node | Validates | Logic |
|------|-----------|-------|
| LLM (3) | LLM (2) variation | If info unavailable -> "HUMAN", else pass |
| LLM (4) x3 | LLM main, LLM 10, LLM (1) detail | Same logic |
| LLM (5) | LLM (1) general | Same logic |

---

## Escalation Logic

### Triggers (LLM 7 returns "Human" for)
- Returns, refunds, exchanges, replacements, missing/damaged parts
- Explicit request for human agent
- PII shared without context
- Delivery cost, warranty, payment methods, store policies
- Shipment status complaints with frustration
- Out of stock complaints
- Abusive or incoherent language
- Order number only or product detail only messages

### Escalation Format
Quality gate LLM nodes output `"HUMAN"` → Output Guard Code nodes intercept and replace with deterministic `[HUMAN_ESCALATION]` tagged messages in the detected language (EN/MS/ZH).

**NOW MATCHES SHOPEE**: 7 Output Guard Code nodes (OG-1 through OG-7) intercept all LLM output before it reaches Answer nodes. See "Output Guard Architecture" section below.

---

## Output Guard Architecture (7 Code Nodes)

All 7 Answer nodes pass through an Output Guard Code node before the customer sees the response. Implemented 2026-02-16, reworked 2026-02-18.

### Full Guards (OG-1 through OG-6) — 2 parameters: `llm_output`, `customer_query`
| Node | ID | Upstream LLM | Answer |
|------|----|-------------|--------|
| OG-1 | `1800000000001` | LLM (main product) | Answer |
| OG-2 | `1800000000002` | LLM (4) gate | Answer 4 |
| OG-3 | `1800000000003` | LLM (1) detail | Answer 9 |
| OG-4 | `1800000000004` | LLM (3) gate | Answer 9 (1) |
| OG-5 | `1800000000005` | LLM (4) gate | Answer 8 |
| OG-6 | `17471061908100` | LLM 10(1) fallback | Answer 8 (1) |

**Logic pipeline** (in order):
1. **Contact Info Redirect** — 8 regex patterns (4 EN/MS + 4 ZH) detect customer asking for phone/email/contact info → neutral escalation (no yes/no, no promise, no rejection)
2. **Escalation Interceptor** — if LLM output contains `[HUMAN_ESCALATION]` or `HUMAN` → deterministic escalation message in detected language
3. **PII Blocking** — blocks email addresses (`@` pattern), phone numbers (`+60` pattern), and requests asking for PII
4. **Normal passthrough** — clean LLM output returned as-is

### Escalation-Only (OG-7) — 1 parameter: `customer_query`
| Node | ID | Source | Answer |
|------|----|--------|--------|
| OG-7 | `1800000000007` | IF/ELSE 3 (Human branch) | Answer 7 |

OG-7 always returns a deterministic escalation message — no LLM output, no PII filter, no contact redirect. Just language detection + escalation.

### Deterministic Messages (4 variants per language, random rotation)
- **ESCALATION_MESSAGES** (EN/MS/ZH, 4 each) — used for escalation interception
- **CONTACT_REDIRECT** (EN/MS/ZH, 3 each) — used for contact info requests
- All messages tagged with `[HUMAN_ESCALATION]` for middleware routing

### Language Detection (`_detect_language()`)
- CJK character count >= 2 → ZH
- Malay bigram detection + word-ratio >= 0.15 (70+ Malay words in set) → MS
- Default → EN
- None guards: `llm_output = llm_output or ''`, `customer_query = customer_query or ''`

---

## Guard Rails & Compliance

| Guard Rail | Status | Notes |
|------------|--------|-------|
| **PII Protection** | Implemented (GRBT-175) | Don't ask for more info, reassure + escalate |
| **External Contact Prohibition** | Implemented (GRBT-175) | Never suggest calling/emailing external support |
| **Forbidden Words** | Implemented (5 of 6 response nodes) | Physical shop, Walk-in, Cancel, Return, Refund, etc. |
| **Word Obfuscation** | Implemented (5 of 6 response nodes) | "0ut of st0ck", "phys1cal st0re", "s3lf-p1ck Up" |
| **Deterministic Escalation Messages** | Implemented (2026-02-18) | 7 Output Guard Code nodes, 4 variants per language (EN/MS/ZH) |
| **Language Detection** | Implemented (2026-02-18) | `_detect_language()` in all 7 OG nodes (CJK + bigram + word-ratio) |
| **Contact Info Redirect** | Implemented (2026-02-18) | 8 regex patterns (4 EN/MS + 4 ZH), neutral escalation |
| **PII Output Filter** | Implemented (2026-02-18) | Email + phone + PII request blocking in OG-1 through OG-6 |
| **Financial Guardrail** | **NOT IMPLEMENTED** | Shopee has this via GRBT-169 |
| **Prompt Injection Defense** | **NOT IMPLEMENTED** | Shopee has this via AW-288 |
| **Resolution Action Prevention** | **NOT IMPLEMENTED** | Shopee has this via GRBT-161 |

**KNOWN GAPS**:
- LLM 10 (`1745229622274`, variation list) generates customer-visible text but is NOT in the forbidden words list
- OG escalation interceptor uses broad `'HUMAN' in llm_output` match — could false-positive on words containing "HUMAN" (LOW risk, inherited from Shopee)
- Phone regex `\+?6?0\d{1,2}[\-\s]?\d{7,8}` may match SKU-like numbers (LOW risk)

---

## Language Support

- English (EN), Chinese (ZH), Bahasa Malaysia (MS)
- **NO Bahasa Indonesia** (explicitly excluded in all prompts)
- Malay abbreviation handling: sy->saya, utk->untuk, kefai->kedai, sane->sana, ke->kah
- Language detection: deterministic `_detect_language()` in all 7 Output Guard nodes (CJK count for ZH, bigram + word-ratio for MS, EN default)

---

## Key Differences from Shopee Chatbot

| Aspect | TikTok | Shopee |
|--------|--------|--------|
| App Type | advanced-chat (chatflow) | workflow |
| Nodes | 48 | 70 |
| LLM Nodes | 13 | 17 |
| Code Nodes | 7 (all Output Guards) | 17 (incl. 8 Output Guards) |
| Escalation | `[HUMAN_ESCALATION]` via 7 OG nodes | `[HUMAN_ESCALATION]` via 8 OG nodes |
| Lang Detection | `_detect_language()` in OG nodes | `_detect_language()` in OG nodes |
| Contact Redirect | 8 regex patterns (EN/MS/ZH) | 8 regex patterns (EN/MS/ZH) |
| Image Handling | Not supported | Vision (gpt-5.2) |
| Financial Guard | Not implemented | GRBT-169 |
| Prompt Injection | Not implemented | AW-288 |

---

## Input Format from TikTok

The chatbot receives messages in structured format:
```
<question> || Product/SKUs: <value> || Shop Name: <shop>
```
Or TikTok order inquiry metadata:
```
when will this arrive?
10:24 || Product: Customer is inquiring about this order: Completed Time: 24-04-2025...
```

---

## Knowledge Base

- Vector-based retrieval with `text-embedding-3-large` embeddings
- 3 Knowledge Retrieval nodes with different routing (SKU-based, candidate_id, detail)
- Reranking enabled (gpt-4.1-nano for main, gpt-3.5-turbo for metadata)
- Weighted scoring: pure vector, no keyword

---

## API Access

### Fetch Workflow Draft (browser console on cloud.dify.ai)
```javascript
fetch('/console/api/apps/099dbd92-1c63-4d87-b484-7e8780440181/workflows/draft', {
  method: 'GET', credentials: 'include',
  headers: {'Content-Type': 'application/json'}
}).then(r => r.json()).then(d => { window._workflowData = d; console.log('Loaded', d.graph.nodes.length, 'nodes'); })
```

### Save Changes (requires hash for concurrency)
```javascript
const { graph, features, environment_variables, conversation_variables, hash } = window._workflowData;
fetch('/console/api/apps/099dbd92-1c63-4d87-b484-7e8780440181/workflows/draft', {
  method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ graph, features, environment_variables, conversation_variables, hash })
}).then(r => r.json()).then(d => console.log('Saved, new hash:', d.hash));
```

**Publish**: UI button only.

---

## Testing

```
mcp__tiktok-chat__TikTok_Chat query="<test message>"
```

Test: product queries, escalation ("I want a refund"), PII, WAIT handler, sticker/image, language (EN/MS/ZH).

---

## Debugging Quick Reference

| Symptom | Likely Cause | Where to Look |
|---------|-------------|---------------|
| Bot gave wrong product info | Wrong KB retrieval or SKU extraction | PE2 extraction -> IF/ELSE routing -> KR node |
| Bot didn't escalate | LLM 7 didn't return "Human" | Check intent routing, then quality gates |
| Bot said forbidden word | Node missing from forbidden words list | Check which LLM produced it (LLM 10 is a known gap) |
| Wrong language response | `_detect_language()` misclassified | Check OG node language detection (CJK count, bigram match, 0.15 threshold) |

---

## Backlog (Open Items)

| Priority | Item |
|----------|------|
| **HIGH** | TikTok order tracking flow -- determine correct guidance |
| **MEDIUM** | Add financial commitment prevention guardrail (Shopee has GRBT-169) |
| **MEDIUM** | Add prompt injection defense (Shopee has AW-288) |
| **MEDIUM** | Add resolution action prevention (Shopee has GRBT-161) |
| **LOW** | Cover LLM 10 with forbidden words/obfuscation |
| **LOW** | OG broad `HUMAN` match — could false-positive (inherited from Shopee pattern) |
| **LOW** | OG phone regex may match SKU-like numbers |

### Recently Completed
- ~~Port deterministic escalation messages from Shopee~~ — Done 2026-02-18 (7 OG nodes)
- ~~Port `_detect_language()` from Shopee~~ — Done 2026-02-18 (all 7 OG nodes)
- ~~Add contact info redirect~~ — Done 2026-02-18 (8 regex patterns, OG-1 through OG-6)
- ~~Add PII output filter~~ — Done 2026-02-18 (OG-1 through OG-6)

---

## Related Skills
- `/dify-shopee-chatbot` -- Shopee chatbot reference (more mature)
- `/workflow-chatbot` -- Standard workflow for chatbot tickets
- `/chatbot-fix` -- GRBT ticket fix workflow
