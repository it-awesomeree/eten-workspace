---
description: Sync skills to Github repository
argument-hint: [commit-message]
---

# Sync Skills to Github

Push any new or modified skills to the Github repository.

**Commit message:** $ARGUMENTS (if not specified, use auto-generated message)

## Workflow

### Part A: Sync Agnes's skills → agnes-workspace

#### Step A1: Copy Agnes's skills to repo
```bash
cp ~/.claude/commands/chatbot-audit.md ~/.claude/commands/chatbot-fix.md ~/.claude/commands/chatbot-middleware.md ~/.claude/commands/chatbot-qa.md ~/.claude/commands/cicd-swarm.md ~/.claude/commands/dify-shopee-chatbot.md ~/.claude/commands/dify-tiktok-chatbot.md ~/.claude/commands/endsession.md ~/.claude/commands/github-repos.md ~/.claude/commands/jira.md ~/.claude/commands/mysql-schema.md ~/.claude/commands/n8n-workflows.md ~/.claude/commands/refresh-skills.md ~/.claude/commands/screen-intern-candidates.md ~/.claude/commands/syncskills.md ~/.claude/commands/vm-inventory.md ~/.claude/commands/workflow-chatbot.md ~/.claude/commands/workflow-webapp.md ~/github-repos/agnes-workspace/commands/
```

#### Step A2: Check for changes
```bash
cd ~/github-repos/agnes-workspace && git status
```

#### Step A3: If there are changes, commit and push
```bash
cd ~/github-repos/agnes-workspace && git add . && git commit -m "[message]" && git push
```

#### Step A4: Report result
- List files that were added/modified (or "no changes")
- Repository: https://github.com/it-awesomeree/agnes-workspace

### Part B: Sync Ken's skills → claude-code-skills

#### Step B1: Copy Ken's skills to repo
```bash
cp ~/.claude/commands/allroas.md ~/.claude/commands/checkcompetitor.md ~/.claude/commands/checkdailysales.md ~/.claude/commands/checkmonthsales.md ~/.claude/commands/googlecloud.md ~/.claude/commands/googlesheet.md ~/.claude/commands/itemprofit.md ~/.claude/commands/ordervalue.md ~/.claude/commands/trademark.md ~/.claude/commands/webapp-backend.md ~/.claude/commands/webapp-frontend.md ~/.claude/commands/webapp-inventory.md ~/.claude/commands/webapp-issues.md ~/github-repos/claude-code-skills/commands/
```

#### Step B2: Check for changes
```bash
cd ~/github-repos/claude-code-skills && git status
```

#### Step B3: If there are changes, commit and push
```bash
cd ~/github-repos/claude-code-skills && git add . && git commit -m "[message]" && git push
```

#### Step B4: Report result
- List files that were added/modified (or "no changes")
- Repository: https://github.com/it-awesomeree/claude-code-skills

### Summary
- Report both repos' sync status
- If no changes in either repo, inform the user

## Notes
- Agnes's skills (18): chatbot-audit, chatbot-fix, chatbot-middleware, chatbot-qa, cicd-swarm, dify-shopee-chatbot, dify-tiktok-chatbot, endsession, github-repos, jira, mysql-schema, n8n-workflows, refresh-skills, screen-intern-candidates, syncskills, vm-inventory, workflow-chatbot, workflow-webapp
- Ken's skills (13): allroas, checkcompetitor, checkdailysales, checkmonthsales, googlecloud, googlesheet, itemprofit, ordervalue, trademark, webapp-backend, webapp-frontend, webapp-inventory, webapp-issues
- If no changes detected in a repo, skip commit for that repo
- Use descriptive commit messages
