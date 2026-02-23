---
description: Shopee chatbot Node.js middleware - VM scripts bridging Shopee Chat to Dify via Puppeteer, message formatting, context building, escalation, and known behaviors
argument-hint: [VM name, bot name, issue, or what you're investigating]
---

# Shopee Chatbot Middleware (Node.js Scripts on VMs)

**Status**: Fully documented from `bot-scripts` repo (PR #1 merged)
**Last updated**: 2026-02-17
**Source code**: `it-awesomeree/bot-scripts` → `chatbot-middleware/`

## Overview

The Shopee chatbot is a **two-layer system**. Most debugging only looks at Dify (Layer 2), but the Node.js middleware (Layer 1) controls what Dify receives and is often the actual root cause.

> **Correction**: The middleware is **Node.js (Puppeteer)**, not Python. All live scripts are JavaScript. Legacy dead Python scripts (`aibot.py`, `C1_OneChat.py`, etc.) have been deleted from VMs.

```
Layer 1: NODE.JS MIDDLEWARE (this skill)         Layer 2: DIFY WORKFLOW (/dify-shopee-chatbot)
─────────────────────────────────────            ─────────────────────────────────────────────
Customer sends message on Shopee Chat            Receives structured query from middleware
        ↓                                                ↓
Puppeteer reads message(s) from DOM              Question Classifier (gpt-5-mini)
        ↓                                                ↓
10-second debounce (waits for more msgs)         Routes to FAQ / Product / Image / Escalation
        ↓                                                ↓
Builds structured query:                         LLM nodes generate response (gpt-5.2)
  CURRENT_QUERY || PRODUCT_CONTEXT ||                    ↓
  CHAT_HISTORY || HUMAN_AGENT_INVOLVED           Output Guard Code nodes
        ↓                                                ↓
POSTs to Dify API (blocking mode)                Returns response to middleware
  api.dify.ai/v1/chat-messages                           ↓
        ↓                                        ─────────────────────────────────────────────
Receives Dify response
        ↓
Detects HUMAN_ESCALATION / SAMPLE tags
        ↓
Strips markdown, sends reply via humanType()
        ↓
If escalation: marks chat unread, resets conversation_id
```

**Key insight**: If the middleware sends the wrong input to Dify, Dify will produce the wrong output — even if the Dify workflow is perfect.

---

## Codebase Architecture

**Two generations of code exist** in the `bot-scripts/chatbot-middleware/` repo:

### 1. Legacy Standalone Scripts (currently deployed on VMs)
Self-contained single-file bots with all logic inline:
```
chatbot-middleware/
  cbmy/
    HiranaiAI.js       — Hiranai shop (port 9450, C2 sub-account)
    MurahyaAI.js       — Murahya shop (port 9270, C4 sub-account)
    ChatbotScript.js   — C1 sub-account (port 9450)
    HiranaiAutoReply.js — Hiranai simpler autoreply mode
    MurahyaAutoReply.js — Murahya simpler autoreply mode
    C1AutoReply.js     — C1 simpler autoreply mode
  cbc3/
    AIChatbot.js       — KarlMobel shop (port 9333, ~2340 lines)
    spare.js           — Backup/alternate version (not deployed)
```

### 2. Refactored Modular System (may not yet be deployed)
Shared modules with per-store entry points and JSON configs:
```
chatbot-middleware/
  core/
    config-loader.js   — JSON config + .env loader
    logger.js          — Logger factory (error + chat logs)
    utils.js           — randomSleep, removeNonBmp, humanType, randomUserId
    user-threads.js    — shopeeUserList.txt read/write + Dify user ID management
    chat-history.js    — formatChatHistory, detectHumanAgentContext
    dify-client.js     — difyResponse, uploadImageToDify, autoResponse
    text-processing.js — stripMarkdownForShopee, escalation detection
    puppeteer-base.js  — Browser launch/connect, DOM scraping
    main-loop-ai.js    — Shared AI bot main loop
    main-loop-autoreply.js — Shared autoreply main loop
  stores/
    hiranai-ai.js      — Entry point: loads config, calls runAiBot()
    murahya-ai.js      — Entry point
    c1-ai.js           — Entry point
    cbc3-ai.js         — Entry point (CBC3/KarlMobel)
  configs/
    hiranai-shopee.json
    murahya-shopee.json
    c1-shopee.json
    cbc3-shopee.json
    hiranai-shopee-autoreply.json
    murahya-shopee-autoreply.json
    c1-shopee-autoreply.json
    tiktok.json
```

---

## VM Inventory

> **There are 3 Shopee chatbot VMs — CBMY, CBC3, and CBSG. Never say "2".** CBSG runs an auto-clicker (not AI-powered) but is still a Shopee chatbot VM. All middleware is Node.js/Puppeteer, not Python.

| VM | Bot Script | Chrome Port | Sub-Account | Shop | Dify API Key |
|----|-----------|-------------|-------------|------|-------------|
| **CBMY** | `HiranaiAI.js` | 9450 | cservice2 (C2) | Hiranai | `app-yTWchMglN1o1FnsCfDZa6NQ6` |
| **CBMY** | `MurahyaAI.js` | 9270 | cservice4 (C4) | Murahya | Same key |
| **CBMY** | `ChatbotScript.js` | 9450 | cservice (C1) | TBD | Same key |
| **CBC3** | `AIChatbot.js` | 9333 | cservice3 (C3) | KarlMobel | Same key |
| **CBSG** | Unknown | 9333 | TBD | SG shop | Unknown |

**WinRM access** (via Tailscale VPN — `100.86.32.62` gateway):
- VM CBMY: port 65506
- VM CBC3: port 65507
- VM CBSG: port 65508

---

## Structured Query Format

The middleware constructs a delimited string before sending to Dify:

```
CURRENT_QUERY: <message> || PRODUCT_CONTEXT: <product info> || CHAT_HISTORY: CUSTOMER: ...\nAGENT: ... || HUMAN_AGENT_INVOLVED: yes
```

Full example:
```
CURRENT_QUERY: Ada warna hitam tak? || PRODUCT_CONTEXT: Product: Kerusi Gaming XYZ123 || CHAT_HISTORY: CUSTOMER: Berapa harga?\nAGENT: Hi Boss! Harga RM299. Thank you! || HUMAN_AGENT_INVOLVED: yes
```

The `|| CHAT_HISTORY: ...` section is only appended when `shouldIncludeHistory()` returns true.
The `|| HUMAN_AGENT_INVOLVED: yes` is only appended when a real human agent message is detected in the thread.

**Code** (`dify-client.js:78` / `HiranaiAI.js:325`):
```javascript
const fullQuery = `CURRENT_QUERY: ${latestUserMessage} || PRODUCT_CONTEXT: ${shopProductContext}${chatHistoryContext}`;
```

### What the Middleware Controls (and Dify Does NOT)

| Behavior | Controlled by | Impact if wrong |
|----------|--------------|-----------------|
| **How many prior messages** in CHAT_HISTORY | Middleware (max 10) | Bot loses conversation context |
| **Which message is CURRENT_QUERY** | Middleware (last user msg) | Bot responds to wrong message |
| **Whether PRODUCT_CONTEXT is included** | Middleware (DOM scrape) | Bot can't answer product questions |
| **Delimiter formatting** (`\|\|`) | Middleware | Customer message containing `\|\|` breaks Dify parsing |
| **HUMAN_AGENT_INVOLVED flag** | Middleware | Bot may not re-escalate when human was involved |
| **10-second debounce** | Middleware | Without it, bot responds to first msg of multi-msg send |
| **conversation_id persistence** | Middleware (`shopeeUserList.txt`) | Without it, Dify loses conversation context |
| **conversation_id reset on escalation** | Middleware | Without reset, bot re-escalates in a loop |
| **Whether message is forwarded at all** | Middleware | Customer gets no response (silent failure) |
| **Retry on Dify API failure** | Middleware (3 retries, 20s) | Messages dropped; canned response sent instead |

---

## CURRENT_QUERY Extraction

The latest customer message is extracted by scanning the DOM conversation history backwards.

**Code** (`HiranaiAI.js:547-555`):
```javascript
function getLastUserMessage(conversationHistory) {
  for (let i = conversationHistory.length - 1; i >= 0; i--) {
    if (conversationHistory[i].role === "user") {
      return conversationHistory[i].content;
    }
  }
  return null;
}
```

**Process** (main loop):
1. `getChatBox(page)` scrapes all messages from DOM
2. `getLastUserMessage(conversationHistory)` finds the most recent `role === "user"` entry
3. 10-second debounce: polls every 1s for new messages, resets timer if new message arrives
4. After debounce: re-calls `getChatBox(page)` to get final state
5. `latestUserMessage` = the post-debounce value

---

## CHAT_HISTORY Construction

**Code** (`core/chat-history.js:37-98`):
```javascript
function formatChatHistory(conversationHistory, maxMessages = 10) {
  // Take all messages except the last one (that's CURRENT_QUERY)
  const historyMessages = conversationHistory.slice(0, -1).slice(-maxMessages);
  // Filter out escalation exchanges and canned responses
  // (removes the agent response AND the preceding customer message that triggered it)
  return filtered.map(msg => {
    const role = msg.role === 'user' ? 'CUSTOMER' : 'AGENT';
    if (msg.type === 'sticker')  content = '[Customer sent a sticker]';
    if (msg.type === 'image')    content = '[Customer sent an image]';
    if (msg.type === 'faq_box')  content = '[FAQ suggestion displayed]';
    return `${role}: ${content}`;
  }).join('\n');
}
```

**When history is included** (`shouldIncludeHistory`):
- No existing `conversationId` (fresh start or after escalation reset)
- A human agent was detected in the conversation
- Conversation has more than 1 message

**Escalation response patterns filtered out** (`chat-history.js:20-28`):
```javascript
const ESCALATION_RESPONSE_PATTERNS = [
  "our team will attend to you shortly",
  "our team will get back to you",
  "your case has been transferred to our team",
  "tengah semak sekarang",
  "kes boss dah dihantar",
  "已转交给我们的团队",
  "正在处理中",
];
```

**Human agent detection** (`detectHumanAgentContext`): Looks for agent messages that are NOT canned responses AND NOT messages the bot itself sent (50-char normalized prefix comparison). If found, appends `HUMAN_AGENT_INVOLVED: yes` to the query.

---

## PRODUCT_CONTEXT Assembly

Product context comes from DOM scraping with a 3-tier fallback:

**Tier 1 — Product banner** (primary):
- Selector: `#messagesContainer > div.Wy5_SjKidw > div.eEQpRXnxhJ`
- Alt selector: `#messagesContainer .rFHc1_XxbI`
- If found: `select = 1`, formatted as `Product: <title>`

**Tier 2 — Inquiry card in messages** (secondary):
- Scans `div.DEwekPN7v2` rows for `.psS_4N86Xq` containing "Customer is inquiring about this item"
- Extracts title from `.AxQ3a11H1U`

**Tier 3 — Shipping info** (fallback):
- Selector: `#messagesContainer > div.Wy5_SjKidw > div._ki3uOms2o > div.wioEqhn453 > div.DBRPBVwDN7`
- When no product found at all (`select === 2`): context is blank space

**Code** (`HiranaiAI.js:293-304`):
```javascript
let shopProductContext = ` `;
if (productInfo && productInfo.trim() !== " ") {
  if (productInfo.includes("Collapse")) {
    productInfo = productInfo.replace("Collapse", "");
  }
  productInfo = productInfo.split(/\s+/).join(" ");
  if (select === 1) {
    shopProductContext = `Product: ${productInfo}`;
  }
}
```

---

## Dify API Call

**Endpoint**: `POST https://api.dify.ai/v1/chat-messages`

**Headers**:
```javascript
{ Authorization: `Bearer ${DIFY_API_KEY}`, "Content-Type": "application/json" }
```

**Payload**:
```javascript
{
  inputs: {},
  query: fullQuery,           // "CURRENT_QUERY: ... || PRODUCT_CONTEXT: ... || CHAT_HISTORY: ..."
  response_mode: "blocking",  // waits for complete response
  user: userId,               // 8-char random alphanumeric per customer (persistent)
  conversation_id: "...",     // only if continuing existing conversation (omitted on first msg)
  files: [...]                // only if images were uploaded
}
```

**Retry logic**:
- Max retries: 3 (AI mode) / 20 (AutoReply mode)
- Retry delay: 20 seconds
- On all retries exhausted: returns first `STANDARD_RESPONSES` canned phrase ("Dear Buyer, We will get back to you...")
- No explicit HTTP timeout set on chat-messages call

**Response parsing**: Extracts `data.answer` from Dify response. If `conversation_id` is returned (first message), stores it in `shopeeUserList.txt` for future continuity.

---

## Escalation / Human Handoff

**Detection triggers** (`HiranaiAI.js:2151-2153`):
```javascript
const needsHuman = /HUMAN_ESCALATION/i.test(reply || "") || /\bHUMAN\./i.test(reply || "");
```

**Tag stripping** (before sending to customer):
```javascript
const cleanedReply = (reply || "")
  .replace(/^\s*\[(HUMAN_ESCALATION|SAMPLE)\]\s*/i, "")
  .replace(/\bHUMAN_ESCALATION\b/gi, "")
  .trim();
```

**Escalation flow** (`HiranaiAI.js:2155-2179`):
1. Send `cleanedReply` to customer (escalation message without internal tags)
2. Log as "MARKED FOR HUMAN FOLLOW-UP"
3. Call `markAsUnread(page, name)` — right-clicks chat, selects "Unread" from dropdown
4. **Reset `conversation_id` to null** (critical — prevents re-escalation loop)
5. Save user threads to `shopeeUserList.txt`
6. Disconnect and continue to next chat

**SAMPLE branch**: Same flow but triggered by `/\bSAMPLE\b/i` — marks chat unread for sample product follow-up.

**`markAsUnread()` mechanics** (`puppeteer-base.js:834-948`):
1. Scroll chat list to top
2. Search for customer name in list (up to 15 scroll attempts)
3. Hover to show context menu (`div.molVzJV3QI > div`)
4. Click "Unread" option (`div.shopee-react-dropdown-item.pkVMV0Sxlh:nth-child(1)`)

---

## Conversation Persistence

**Storage**: `shopeeUserList.txt` (JSON) in same directory as the bot script.

**Structure per customer**:
```json
{
  "ShopeeUsername123": {
    "dify_id": "AbCdEfGh",
    "conversation_id": "conv-abc123-...",
    "created_at": "2026-02-17T00:00:00.000Z",
    "last_active": "2026-02-17T12:00:00.000Z"
  }
}
```

- Each Shopee customer gets a stable random 8-char `dify_id` on first contact
- `conversation_id` returned by Dify on first message, stored for continuity
- `conversation_id` set to `null` after escalation (forces fresh Dify conversation)

---

## Image Handling

**Process** (`HiranaiAI.js:2080-2110`):
1. After debounce, check if latest user message has `imageUrls`
2. Download each image via `axios.get()` with 30s timeout
3. Upload to `https://api.dify.ai/v1/files/upload` as multipart form-data
4. Collect returned file IDs, add to Dify payload:
```javascript
payload.files = imageFileIds.map(fileId => ({
  type: "image",
  transfer_method: "local_file",
  upload_file_id: fileId,
}));
```
- Max 2 images per message (`slice(-2)`)
- Excludes stickers (`/packs/`), emoji packs, and thumbnails (`_tn`)

---

## Message Reading from Shopee Chat DOM

**`getChatBox(page)`** (`HiranaiAI.js:1018-1364`):
1. Connect to existing Chrome via `puppeteer.connect({ browserURL: "http://localhost:<port>" })`
2. Navigate to `https://seller.shopee.com.my/webchat/conversations`
3. Apply "Unread" filter (click `div.Ph4EKTE0SS` → 4th child option)
4. Scroll to bottom of chat list, iterate backwards to find oldest unprocessed chat
5. Wait for `##message-virtualized-list` in selected chat
6. Scroll bottom → up 2 screens → PageDown 3x (loads React virtual list rows)
7. Scrape all `div > div.DEwekPN7v2` rows:
   - Sender: `[data-cy="webchat-message-send"]` = agent, `[data-cy="webchat-message-system"]` = system, else = user
   - Text: `pre[class*="Fkk7VvR2qX"]`, `pre[class*="FTxHHZcaH8"]`, `div[class*="ssIhmxFOh6"]`
   - Stickers: `img[src*="/packs/"]`
   - Images: non-sticker `img` elements
8. Sort by CSS `top` value (chronological order)
9. Filter out system messages and canned "Dear Buyer..." responses
10. Merge consecutive user bubbles into single messages
11. Return `[{role, content, text, type, hasImage, imageUrls, isFAQBox}]`

**Request interception**: Blocks `orders/orders_by_buyer` API calls which cause captcha triggers.

---

## Message Sending

**`replyToDraft(page, reply)`** (`HiranaiAI.js:1503-1537`):
1. Click draft button if present: `.KkePTkfUj9`
2. Wait for reply input: `.E2MWg3w8y6`
3. Clear input via `element.value = ""`
4. Type with `humanType()` — 40-140ms delay per character
5. Strip non-BMP Unicode chars before typing (`removeNonBmp()`)
6. Press Enter to send
7. Handle repetitive message popup (click "Send" on modal)

**Markdown stripping** (`core/text-processing.js:6-15`):
```javascript
function stripMarkdownForShopee(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "$1")     // **bold**
    .replace(/__(.*?)__/g, "$1")           // __bold__
    .replace(/\*(.*?)\*/g, "$1")           // *italic*
    .replace(/_(.*?)_/g, "$1")             // _italic_
    .replace(/`([^`]*)`/g, "$1")           // `code`
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1");  // [links](url)
}
```

Legacy scripts also flatten newlines: `reply.split("\n").join(" ")`

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| **Dify API failure (all 3 retries)** | Returns `STANDARD_RESPONSES[0]` canned phrase. Bot still sends to customer. |
| **Empty conversation history** | Sends canned response + marks chat unread for human follow-up |
| **No user message found** | Disconnects browser, continues loop. No message sent. |
| **Network/browser error** | Caught at both inner (chat) and outer (main loop) level. Browser disconnected, random sleep 7-15s, retry. |
| **Ban page detected** | Checks for Shopee ban element. If found: disconnect and continue loop. |
| **Captcha popup** | 5-method approach tried in sequence: force-click close, Escape key, coordinate click, alt selectors, backdrop click |

---

## Logging

**Log files** (in same directory as bot script):

| File | Contents |
|------|----------|
| `error.txt` / `c3_error.txt` | All INFO and ERROR events (Asia/Singapore timestamps) |
| `chat_logs.txt` / `c3_chat_logs.txt` | Every Dify interaction: username, full query, Dify answer |

**Chat log format**:
```
2/17/2026, 12:00:00 PM - - ShopeeUsername123
query sent --- CURRENT_QUERY: Ada stock? || PRODUCT_CONTEXT: Product: XYZ
Dify Answer --- Hi Boss! Kalau boleh checkout, memang ada stok. Thank you!
--------------------------------------------
```

Sessions delimited with `===...=== STARTING NEW SESSION ===...===` separator.

---

## Config Files

**AI mode** (`configs/hiranai-shopee.json` — representative):
```json
{
  "store": { "id": "hiranai-shopee", "name": "Hiranai Shopee", "vm": "CBMY" },
  "chrome": { "port": 9450, "userDataDir": "chrome-shopeeChatC2" },
  "logging": { "errorLogFile": "error.txt", "chatLogFile": "chat_logs.txt" },
  "dify": {
    "endpoint": "https://api.dify.ai/v1/chat-messages",
    "fileUploadEndpoint": "https://api.dify.ai/v1/files/upload",
    "maxRetries": 3,
    "retryDelayMs": 20000
  },
  "platform": { "url": "https://seller.shopee.com.my/webchat/conversations" },
  "features": {
    "chatHistory": true,
    "imageUpload": true,
    "debounce": true,
    "debounceMs": 10000,
    "stripMarkdown": true,
    "queryFormat": "structured"
  }
}
```

**AutoReply mode** differs:
- `chatHistory: false`, `imageUpload: false`, `debounce: false`
- `queryFormat: "legacy"` → format is `<message> || <product>` (no `CURRENT_QUERY:` prefix)
- `maxRetries: 20`, `retryDelayMs: 25000`
- Returns random `STANDARD_RESPONSES` canned phrase (does NOT use Dify's actual response)

**API keys**: Not in JSON configs. Come from `DIFY_API_KEY` env var (refactored) or hardcoded fallback in legacy scripts (`app-yTWchMglN1o1FnsCfDZa6NQ6`).

---

## Bot Differences

### CBMY: Hiranai vs Murahya vs C1

| Property | HiranaiAI.js | MurahyaAI.js | ChatbotScript.js |
|----------|-------------|-------------|-----------------|
| Chrome port | 9450 | 9270 | 9450 |
| Sub-account | C2 | C4 | C1 |
| Max retries | 3 | 5 | 3 |
| Dify API key | Same | Same | Same |
| Logic | Identical | Identical | Identical |

### CBMY vs CBC3

| Aspect | CBMY (HiranaiAI.js etc.) | CBC3 (AIChatbot.js) |
|--------|-------------------------|---------------------|
| Language | Node.js | Node.js |
| Architecture | Standalone per-shop files | Single monolithic file |
| Chrome port | 9450 / 9270 | 9333 |
| Shop | Hiranai / Murahya | KarlMobel |
| Dify API key | `app-yTWchMglN1o1FnsCfDZa6NQ6` | Same key |
| Query format | Same structured format | Same |
| Chat history | Yes (max 10 msgs) | Yes (max 10 msgs) |
| Image upload | Yes | Yes |
| Debounce | 10s | 10s |
| Log files | `error.txt`, `chat_logs.txt` | `c3_error.txt`, `c3_chat_logs.txt` |
| State file | `cbmy/shopeeUserList.txt` | `cbc3/shopeeUserList.txt` |

### AI Bot vs AutoReply Mode

| Feature | AI Bot | AutoReply |
|---------|--------|-----------|
| Dify integration | Full conversation with `conversation_id` | Sends query but ignores Dify response |
| Chat history | Yes (max 10 msgs, escalation-stripped) | No |
| Image upload | Yes | No |
| Debounce | 10s | No |
| Escalation detection | Yes | No |
| Reply source | Dify response | Random `STANDARD_RESPONSES` canned phrase |
| Max retries | 3 | 20 |

---

## Anti-Detection Measures

**Stealth** (in `createBrowser()` / page setup):
- `navigator.webdriver` overridden to `undefined`
- `navigator.plugins` faked as `[1, 2, 3, 4, 5]`
- `navigator.languages` set to `["en-US", "en", "bn"]`
- Canvas fingerprint spoofing
- Random user agent from pool of 10
- Human-like typing: 40-140ms per character
- Random sleep between operations

**Anti-bot bypass** (CBC3-specific fix):
- `browser.newPage()` and `page.goto()` trigger Shopee traffic verification
- Fix: reuse existing webchat pages via `browser.pages()`, avoid creating new pages
- Clear chat filter via `localStorage.removeItem("chat-filter")` on disconnect

**Request blocking**: Aborts `orders/orders_by_buyer` API calls to prevent captcha triggers.

---

## Known Issues from Incident History

### GRBT-160: Middleware Completely Down (Feb 2026)
**What happened**: Chatbot stopped replying to ALL customers. ~300 conversations/day to near-zero.
**Root cause**: Middleware stopped forwarding messages to Dify. Dify workflow was functional (6/6 tests passed).
**Key finding**: Middleware was not version-controlled at the time. No monitoring existed — outage went undetected for 5+ days.
**Lesson**: When chatbot "stops working entirely," check middleware FIRST. If Dify tests pass, the problem is in the scripts.

### GRBT-177: Context-Unaware Responses (Feb 2026)
**What happened**: Customer asked "when will you ship?" then "terima kasih". Bot replied "you're welcome" without addressing shipping.
**Root cause (multi-layer)**: Middleware CHAT_HISTORY construction + Dify PII Guard scanning full query string + no acknowledgment override.
**Fix**: Both layers fixed. PII Guard now extracts only CURRENT_QUERY. Added acknowledgment override. LLM reads CHAT_HISTORY.

### GRBT-178: Three Simultaneous Issues (Feb 2026)
**What happened**: Neutral escalation not working, asterisks in responses, wrong language detection.
**Fix**: Dify workflow fixes + middleware `conversation_id` reset after escalation. All 3 bots restarted.

---

## Debugging Decision Tree

```
Customer reports chatbot issue
        |
        +-- Bot gave NO response at all?
        |   +-- CHECK MIDDLEWARE FIRST
        |      +-- Is bot process running? (vm_processes on CBMY/CBC3)
        |      +-- Check error.txt / c3_error.txt for crashes
        |      +-- Are messages reaching Dify? (chat_logs.txt shows queries sent)
        |      +-- Is Dify API returning errors? (error.txt shows retries)
        |
        +-- Bot responded but response is WRONG?
        |   +-- Wrong because of missing context?
        |   |   +-- CHECK MIDDLEWARE: chat_logs.txt — is CHAT_HISTORY populated?
        |   |   +-- CHECK: Is conversation_id set? (shopeeUserList.txt)
        |   +-- Wrong because of bad routing/classification?
        |   |   +-- CHECK DIFY: Question Classifier / IF nodes
        |   +-- Wrong because of bad response text?
        |   |   +-- CHECK DIFY: LLM node prompts
        |   +-- Wrong because of policy violation?
        |       +-- CHECK DIFY: Guardrail / Output Guard nodes
        |
        +-- Bot responded to wrong message / out of context?
        |   +-- CHECK MIDDLEWARE: Which message is CURRENT_QUERY?
        |   +-- CHECK: Debounce — did customer send multiple messages quickly?
        |   +-- CHECK: Is delimiter || in customer message breaking parsing?
        |
        +-- Bot re-escalated after human already helped?
            +-- CHECK MIDDLEWARE: Was conversation_id reset after escalation?
            +-- CHECK: Is HUMAN_AGENT_INVOLVED flag being set correctly?
            +-- CHECK: detectHumanAgentContext excluding bot's own messages?
```

---

## VM MCP Tools Reference

| Tool | Use Case |
|------|----------|
| `vm_status` | Check if VM is up, CPU/memory health |
| `vm_processes` | Check if bot processes are running |
| `vm_execute` | Run commands on VM (e.g., `Get-Content 'path' -Raw` to read files) |
| `vm_task_control` | Restart a bot process via Task Scheduler (NOT Start-Process) |

**Important**: Don't use `vm_read_file` — its `max_lines` default gets misinterpreted as path. Use `vm_execute` with `Get-Content 'path' -Raw` instead.

**Bot restart method**: Use Task Scheduler, NOT `Start-Process` (Puppeteer bots crash without interactive session context):
```powershell
$action = New-ScheduledTaskAction -Execute 'node' -Argument 'C:\path\to\script.js'
Register-ScheduledTask -TaskName 'TempRestart' -Action $action -Force
Start-ScheduledTask -TaskName 'TempRestart'
# Clean up after:
Unregister-ScheduledTask -TaskName 'TempRestart' -Confirm:$false
```

---

## TikTok Chatbot Middleware

A separate script exists for TikTok (`configs/tiktok.json` found in the refactored system) but is **not yet deployed to a VM**. When deployed, it will follow the same architecture with TikTok-specific DOM selectors.

---

## Related Skills

- `/dify-shopee-chatbot` — Dify workflow layer (70 nodes, 17 GPT nodes)
- `/dify-tiktok-chatbot` — TikTok Dify chatbot (48 nodes, 13 LLM nodes)
- `/chatbot-fix` — GRBT ticket fix workflow (includes middleware check)
- `/workflow-chatbot` — Standard chatbot fix workflow (includes middleware check)
- `/vm-inventory` — All 17 VMs, bot-to-VM mapping
- `/chatbot-audit` — Health check on Dify workflow nodes
- `/chatbot-qa` — Standardized test suite against published chatbot
