# Eten's Workspace

Claude Code skills, notes, and documentation for Eten @ Awesomeree Sdn Bhd.

## Domains
- **Web App** — Next.js 15 / React 19 / TypeScript 5 frontend + backend
- **n8n Workflows** — Automation platform (Variation Generator, webhooks, integrations)
- **VM Bot Scripts** — Windows VM infrastructure running Node.js/Puppeteer bots

---

## Skills (commands/)

### Chatbot Operations
| Skill | Description |
|-------|-------------|
| `/chatbot-audit` | Health check: models, escalation, guardrails |
| `/chatbot-fix` | End-to-end GRBT ticket fix workflow |
| `/chatbot-middleware` | Node.js middleware architecture & debugging |
| `/chatbot-qa` | 20-query standardized test suite |
| `/workflow-chatbot` | Standard workflow for Dify/n8n tickets |

### Platform Knowledge
| Skill | Description |
|-------|-------------|
| `/dify-shopee-chatbot` | Shopee Dify chatbot (70 nodes, 17 GPT nodes) |
| `/dify-tiktok-chatbot` | TikTok Dify chatbot (48 nodes, 13 LLM nodes) |
| `/mysql-schema` | MySQL reference: 5 DBs, 220 tables, 13 domains |
| `/n8n-workflows` | n8n platform: 43 workflows, MCP tools |
| `/vm-inventory` | 17 VMs, 29 bots, role mapping, MCP tools |
| `/github-repos` | 7 GitHub repos under it-awesomeree |
| `/jira` | AW + GRBT boards, columns, workflows, API |

### Web App Workflows
| Skill | Description |
|-------|-------------|
| `/workflow-webapp` | Standard workflow for web app tickets |
| `/cicd-swarm` | 7-agent CI/CD pipeline specification |

### Operations
| Skill | Description |
|-------|-------------|
| `/daily-work-report` | Daily report automation (Google Sheets) |
| `/screen-intern-candidates` | Intern screening automation |
| `/googledrive` | Google Drive folder structure reference |
| `/refresh-skills` | Skill drift detection and refresh |

### Utility
| Skill | Description |
|-------|-------------|
| `/syncskills` | Sync skills to GitHub |
| `/endsession` | End-of-session checklist |

---

## Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Global rules, processes, and lessons learned |
| `WORKLOG.md` | Session-by-session work log |
| `ERRORLOG.md` | Error log with resolutions |
| `BACKLOG.md` | Parking lot for ideas, deferred tasks |
| `SKILLS.md` | Consolidated skills and tech reference |
| `skills-and-technologies.md` | Tech stack details |
| `getting-started-notes.md` | Setup guides for all 3 domains |
| `contributing-notes.md` | Branch naming, PR, code standards |
| `cicd-notes.md` | CI/CD pipeline notes |
| `lessons-learned.md` | Code review and debugging insights |

---

## Usage

Invoke any skill in Claude Code:
```
/workflow-webapp AW-250
/n8n-workflows webhook regenerate
/vm-inventory VM CBMY
```
