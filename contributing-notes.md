# Contributing Guidelines — Eten

Standards for code contributions across all domains at Awesomeree.

---

## Branch Naming

```
feature/AW-XXX-short-description    # New feature
fix/AW-XXX-short-description        # Bug fix
hotfix/AW-XXX-short-description     # Urgent production fix
chore/AW-XXX-short-description      # Maintenance, cleanup
```

Always include the Jira ticket ID in the branch name.

---

## Pull Request Requirements

### PR Target
- **Always PR to `test` branch first** — never directly to `main`
- `test` → `main` promotion happens after validation

### PR Template
```markdown
## Summary
<!-- 1-3 sentences: what this PR does and why -->

## Changes
-

## Testing
- [ ] Changes tested locally
- [ ] No regressions on existing functionality
```

### PR Checklist
- [ ] Branch is up to date with `test`
- [ ] All tests pass locally
- [ ] No console errors or warnings
- [ ] TypeScript compiles with zero errors
- [ ] No hardcoded secrets or credentials
- [ ] Jira ticket referenced in branch name and PR

---

## Code Standards (Web App)

### TypeScript
- Strict mode enabled — no `any` types (never use `as any`)
- Use proper typing for all function parameters and return values
- Prefer interfaces over type aliases for object shapes

### React / Next.js
- Server Components by default, `"use client"` only when necessary
- Extract shared logic into utility functions (don't duplicate)
- Use existing shadcn/ui components before creating custom ones
- Follow existing file/folder naming conventions in the project

### Styling
- Tailwind CSS utility classes — no custom CSS unless absolutely necessary
- Use design tokens from the existing theme

### General
- No magic strings — use constants or enums
- No duplicated code — extract shared functions
- Safety limits on loops and arrays (always have a max)
- Meaningful variable and function names
- Keep functions small and focused

---

## Code Standards (n8n Workflows)

- Always test with webhook-test URL before activating
- Use n8n credentials for API keys — never hardcode in nodes
- Add error handling (`continueOnFail`) on external API nodes
- Document node purpose in the node description/notes field
- Version workflows before making breaking changes

---

## Code Standards (VM Bot Scripts)

- All config values in `config.json` — never hardcoded in scripts
- Proper error handling and logging for all bot operations
- Test scripts locally before deploying to VM
- Document any VM-specific setup in the bot's README

---

## Jira Workflow for Developers

1. **Pick up ticket** → Move from TO DO to IN PROGRESS
2. **Do the work** → Follow branch naming, code standards
3. **Submit PR** → Target `test` branch
4. **Move ticket to TO REVIEW** → Add comment explaining:
   - What was implemented
   - Any deviations from the ticket description (with reasons)
   - How it was tested
5. **Wait for Agnes's review** → Fix any rework items
6. **Never silently skip requirements** — if something can't be done, explain why

---

## AI Usage Rules

- Claude Code can assist with development, but you own the code
- Always review AI-generated code before committing
- Never commit code you don't understand
- AI-generated test cases should be verified manually
