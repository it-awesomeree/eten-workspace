# Lessons Learned — Eten

Insights from code reviews, debugging, and production incidents. Add entries as you learn.

---

## Code Review Lessons

### 1. Extract shared functions — don't duplicate logic
If two or more places do the same thing, extract it into a shared utility. Duplicated code is a maintenance burden and a bug magnet.

### 2. Always set safety limits on loops and arrays
Never iterate without a maximum bound. Use `.slice(0, MAX)` or break conditions to prevent runaway loops.

### 3. No magic strings — use constants
Strings like `"completed"`, `"active"`, `"admin"` should be constants or enums, not scattered across the codebase.

### 4. Never use `as any` in TypeScript
`as any` defeats the purpose of TypeScript. Find the proper type or create one. If you genuinely don't know the type, use `unknown` and narrow it.

### 5. Keep functions focused
If a function does more than one thing, split it. Each function should have a single clear purpose.

---

## Debugging Lessons

### Always check both layers for chatbot issues
Layer 1 (middleware) controls what Layer 2 (Dify) receives. If the input is wrong, the output will be wrong regardless of how perfect the Dify workflow is.

### Credential changes must be atomic
When rotating passwords/API keys, update ALL consumers at once. A half-updated state (e.g., DB password changed but app still using old one) causes cascading failures.

### Test with the actual webhook URL, not assumptions
n8n has separate production and test webhook URLs. Always verify which one you're hitting.

---

## Production Incident Lessons

_Add entries here as you encounter and resolve production issues._

<!-- Template:
### YYYY-MM-DD: [Incident Title]
**What happened**:
**Root cause**:
**What I learned**:
**What to do differently**:
-->
