---
description: Dify Shopee chatbot - 70-node workflow, 17 GPT nodes, escalation logic, guardrails, and navigation guide
argument-hint: [node name, issue, or what you're debugging]
---

# Shopee Dify Chatbot

**Platform**: Dify Cloud (cloud.dify.ai)
**App Name**: Shopee (Current)
**App ID**: `2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df`
**Type**: Workflow-based chatbot
**Total Nodes**: 70 (17 GPT-powered)
**MCP Tool**: `mcp__shopee-chat__Shopee_Current_`
**Ops Repo**: `shopee-chatbot-ops` (GitHub)

---

## Conversation Flow

```
Customer Message (Shopee Chat)
        |
  [Question Classifier] (gpt-5-mini)
        |
   +---------+-----------+-----------+
   |         |           |           |
  FAQ    Product      Image     Escalation
   |         |           |           |
[Param    [Check needs  [Image     [LLM 4/7/8/11]
Extractor] product?]   Analysis]   (gpt-5.2)
(gpt-5-mini) (gpt-5-mini) (gpt-5.2    |
   |         |        vision)      |
[KB Lookup] [Can answer?]  |       |
   |      (gpt-5-mini) [Image     |
[LLM Response]  |     Handler]    |
(gpt-5.2)   Y / N    (gpt-5.2)   |
   |        |    \        |       |
   |   [Response] [CS ESCALATION] |
   |   (gpt-5.2)  (gpt-5.2)      |
   |        |          |          |
   +--------+----------+----------+
                  |
        [OUTPUT GUARD CODE NODE]
        (8 instances, all paths)
                  |
        Checks: Contact Redirect → Cancel Filter
        → [HUMAN_ESCALATION] → PII Block → Markdown Strip
           /              \
      INTERCEPTED       Pass through
          |                 |
   _detect_language()   unchanged
   on sys.query
          |
   _pick_escalation(lang)
   (rotated from 4 messages per lang)
          |
        [ANSWER NODE] -> Customer
```

---

## GPT Node Inventory

### Routing Nodes (7 nodes, gpt-5-mini) -- lightweight, cost-effective
- Question Classifier -- routes to FAQ/Product/Image/Escalation
- Parameter Extractor (x3) -- extract intent and entities
- Translator -- language translation utility
- Check Question need Product info -- determines if KB needed
- To check question can be answered or no -- determines if escalation needed

### Customer-Facing Nodes (10 nodes, gpt-5.2) -- quality responses
- LLM 4, LLM 7, LLM 7 (1), LLM 8, LLM 8 (1), LLM 11 -- response generators
- Image Analysis for Customer Service -- vision: analyzes uploaded images
- Image Customer Service Handler -- generates response from image analysis
- Check knowledge base (1) -- KB-augmented response for product path
- CS ESCALATION (PRODUCT PATH) -- handles product escalation

---

## Escalation System

### Triggers (ALWAYS escalate)
- Refunds / returns / cancellations
- Compensation & financial matters (GRBT-169)
- Wrong item / damaged item
- Order status issues not in KB
- Customer explicitly requests human agent
- PII shared (phone, email, IC, bank)
- Sticker/image-only messages
- Prompt injection attempts

### Interceptor Architecture (Rotated Messages)
1. LLM node outputs `[HUMAN_ESCALATION]` tag (or cancel word detected by filter)
2. **Output Guard Code Node** (Python, 8 instances, OG-1 through OG-8) intercepts
3. `_detect_language()` detects language from `sys.query`:
   - CJK character regex -> ZH
   - 70+ Malay keyword list, 25% threshold -> MS
   - Default -> EN
4. `_pick_escalation(lang)` selects a random message from pool of 4 per language via `random.choice()`

### Output Guard Processing Order
Each Output Guard node runs these checks in sequence:
1. **Contact Info Redirect** -- catches external contact suggestions
2. **Cancel Word Filter** (GRBT-181) -- catches cancel/cancellation/batal/取消 in LLM output
3. **Escalation Interceptor** -- catches `[HUMAN_ESCALATION]` tag
4. **PII Blocking** -- catches personal data in output
5. **Markdown Strip** -- cleans formatting
6. **Passthrough** -- returns cleaned output

### Escalation Messages (4 rotated per language)

**EN:**
1. "Our team will attend to you at the earliest convenience."
2. "Our team will get back to you shortly."
3. "Our team will be with you as soon as possible."
4. "Our team is looking into this and will update you shortly."

**MS:**
1. "Pasukan kami akan melayan boss secepat mungkin."
2. "Pasukan kami akan hubungi boss sebentar lagi ya."
3. "Pasukan kami akan bantu boss dalam masa terdekat."
4. "Pasukan kami sedang semak dan akan maklumkan boss segera."

**ZH:**
1. "我们的团队会尽快为您服务。"
2. "我们的团队将尽快与您联系。"
3. "我们的团队会尽快处理，请稍候。"
4. "我们的团队正在跟进，稍后会回复您。"

All messages are prefixed with `[HUMAN_ESCALATION]` in the code dict. The Output Guard strips this tag and delivers the clean message to customers.

---

## Guard Rails & Compliance

| Guard Rail | What it does |
|------------|-------------|
| **PII Blocking** | Detects phone/email/IC/bank. Does NOT echo back, does NOT ask for more info. Escalates with reassurance. |
| **Prompt Injection Defense** | Blocks attempts to reveal system prompt, change behavior, impersonate other bots |
| **Financial Guardrail** (GRBT-169) | NEVER promise/agree/confirm/negotiate/discuss/calculate compensation amounts |
| **Platform Policy** | ALL communication stays in Shopee Chat. NEVER direct to external channels. Tracking: link to Shopee help article |
| **HUMAN_AGENT_INVOLVED** | If human agent was previously in conversation + financial matters involved -> always re-escalate |
| **Resolution Action Prevention** (GRBT-161) | NEVER promise upgrades/replacements/refunds -- Chinese "转交" not "升级" |
| **Cancel Word Filter** (GRBT-181) | Catches cancel/cancellation/batal/pembatalan/取消 in LLM output. Triggers escalation to human agent. Regex skips "cancelling" to avoid "Noise Cancelling Headphones" false positive. Also blocks "habis stok"/"缺货" (out of stock variants). |

---

## Language Support

- **English (EN)** -- default
- **Malay (MS)** -- including "Rojak" (mixed Malay-English)
- **Chinese Simplified (ZH)** -- Mandarin

Detection: `_detect_language()` in all 8 Output Guard Code nodes (CJK regex for ZH, 70+ keyword list for MS, EN default)

---

## API Access

### Fetch Workflow Draft (browser console on cloud.dify.ai)
```javascript
fetch('/console/api/apps/2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df/workflows/draft', {
  method: 'GET', credentials: 'include',
  headers: {'Content-Type': 'application/json'}
}).then(r => r.json()).then(d => { window._workflowData = d; console.log('Loaded', d.graph.nodes.length, 'nodes'); })
```

### Search Node Prompts
```javascript
window._workflowData.graph.nodes.forEach(n => {
  if (n.data?.prompt_template) {
    n.data.prompt_template.forEach(p => {
      if (p.text && p.text.includes('SEARCH_TERM')) {
        console.log(n.data.title, n.id, p.text.substring(0, 200));
      }
    });
  }
});
```

### Save Changes
```javascript
const { graph, features, environment_variables, conversation_variables, hash } = window._workflowData;
fetch('/console/api/apps/2d96b5ad-3c34-4e1f-bd15-2b2ed570c7df/workflows/draft', {
  method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ graph, features, environment_variables, conversation_variables, hash })
}).then(r => r.json()).then(d => console.log('Saved, new hash:', d.hash));
```

**Critical**: Use `text.split(old).join(new)` for global replacement, NOT `String.replace()`.

**Publish**: UI button only (CSRF token required for API).

---

## Testing

```
mcp__shopee-chat__Shopee_Current_ query="<test message>"
```

Test categories: product queries, escalation triggers, PII, language (EN/MS/ZH), forbidden words, prompt injection.

---

## Debugging Quick Reference

| Symptom | Likely Cause | Where to Look |
|---------|-------------|---------------|
| Wrong language response | Language detection threshold | Output Guard Code nodes, `_detect_language()` |
| Chatbot promises action | Missing guardrail | LLM prompt in the path that fired |
| "升级" in Chinese | Old template or LLM paraphrasing | Should not happen -- check Output Guard |
| System prompt revealed | Prompt injection gap | All customer-facing LLM nodes |
| PII echoed back | PII blocking rule missing | Compliance nodes |
| Wrong product info | KB data or retrieval issue | Knowledge Base nodes |
| Continues financial negotiation | HUMAN_AGENT_INVOLVED rule | Check all 8 customer-facing nodes |
| Cancel word in response | Cancel filter miss or regex gap | Output Guard nodes OG-1 to OG-8, `CANCEL_PATTERNS` regex |
| False positive escalation on product name | Cancel regex too broad | Check if product name contains cancel/batal/取消 substring |

---

## Incident History

| Ticket | Issue | Root Cause | Fix |
|--------|-------|-----------|-----|
| AW-288 | Model optimization | 7 routing nodes on gpt-5.2 | Downgraded to gpt-5-mini |
| GRBT-161 | "升级" ambiguity in Chinese | Free-form escalation text | Deterministic Code nodes |
| GRBT-169 | Agreed to RM60 compensation | Missing financial guardrails | Comprehensive financial guardrails + HUMAN_AGENT handling |
| GRBT-181 | "cancellation" word in chatbot responses | No cancel word filter | Cancel filter in all 8 Output Guard nodes (Layer 2) + LLM prompt instructions (Layer 1). Cancel requests escalate to human agent. |

---

## Related Skills
- `/chatbot-audit` -- Health check audit procedure
- `/chatbot-fix` -- GRBT ticket fix workflow
- `/chatbot-qa` -- Smoke test suite
- `/workflow-chatbot` -- Standard workflow for chatbot tickets
