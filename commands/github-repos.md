---
description: GitHub repos map - All 7 repos under it-awesomeree with branch conventions, file structures, and navigation guide
argument-hint: [repo name, file, or what you're looking for]
---

# GitHub Organization: it-awesomeree

**Account**: `it-awesomeree` (Awesomeree Sdn Bhd)
**Total Repos**: 7 (all private)
**Profile**: https://github.com/it-awesomeree

---

## Repository Inventory

| # | Repo | Purpose | Language | Key Paths |
|---|------|---------|----------|-----------|
| 1 | **awesomeree-web-app** | Next.js employee portal (employee.awesomeree.com.my) | TypeScript | `app/`, `pages/api/`, `components/`, `services/`, `migrations/` |
| 2 | **chatbot-ops** | All chatbot ops — Shopee + TikTok (DSL, changelogs, incidents) | -- | `.github/`, `shopee/`, `tiktok/`, `CLAUDE.md` |
| 3 | **infra-ops** | Cross-project infra (MCP servers, Dify, n8n, VM control plane) | TypeScript | `mcp/vm-control-plane/`, `mcp/webapp-server/`, `dify/`, `n8n/` |
| 4 | **ken-workspace** | Ken's consolidated workspace (skills, OpenClaw, plans) | JavaScript | `claude-code-skills/`, `claude-skills/`, `openclaw-skills/`, `openclaw-workspace/`, `webapp-multi-agent-workflow-plans/` |
| 5 | **natasha-workspace** | Natasha's consolidated workspace (skills) | -- | `claude-skills/`, `openclaw-skills-nat/` |
| 6 | **agnes-workspace** | Agnes's Claude Code skills + docs (CLAUDE.md, logs) | -- | `commands/`, `CLAUDE.md`, `WORKLOG.md`, `ERRORLOG.md`, `BACKLOG.md` |
| 7 | **bot-scripts** | Version-controlled bot scripts, VM automation, data pipelines | Python | `stock-adjustment/`, `chatbot-middleware/`, `schedulers/`, `data-pipeline/` |

---

## Repo-to-Platform Mapping

| Platform/Service | Repo |
|-----------------|------|
| Web App (employee.awesomeree.com.my) | `awesomeree-web-app` |
| Shopee Dify Chatbot | `chatbot-ops` -> `shopee/` |
| TikTok Dify Chatbot | `chatbot-ops` -> `tiktok/` |
| MCP Servers (VM, Webapp) | `infra-ops` |
| Bot scripts, VM automation | `bot-scripts` |
| VM Control Plane code | `infra-ops` -> `mcp/vm-control-plane/` |
| Dify workflow exports | `infra-ops` -> `dify/shopee-chatbot/` |
| n8n automation docs | `infra-ops` -> `n8n/` |

---

## chatbot-ops Structure

```
chatbot-ops/
├── .github/
│   ├── CODEOWNERS                @TeamIT-awesomeree
│   └── PULL_REQUEST_TEMPLATE.md  (platform checkboxes + compliance check)
├── .gitignore
├── CLAUDE.md                     Project instructions for Claude Code
├── LICENSE                       All Rights Reserved — Awesomeree Sdn Bhd
├── README.md                     Repo overview, tree, workflow guide
│
├── shopee/                      ← Shopee Dify chatbot (workflow, 69 nodes)
│   ├── CHANGELOG.md
│   ├── README.md                 Quick ref (App ID, models, node count)
│   ├── backlog.md
│   ├── docs/
│   │   ├── api-notes.md          Dify API quirks, auth, recipes
│   │   ├── architecture.md       Node inventory, model allocation, flow topology
│   │   └── compliance.md         Guardrails, PII rules, platform policies
│   ├── dsl/
│   │   └── shopee-chatbot.yml    ⚠️ PLACEHOLDER — needs manual Dify export
│   └── incidents/
│       ├── _TEMPLATE.md          Post-mortem template
│       ├── AW-258.md
│       ├── GRBT-160.md
│       ├── GRBT-161.md
│       ├── GRBT-169.md
│       ├── GRBT-175.md
│       └── GRBT-177.md
│
└── tiktok/                      ← TikTok Dify chatbot (chatflow, 42 nodes)
    ├── CHANGELOG.md
    ├── README.md                 Quick ref (App ID, models, node count)
    ├── backlog.md
    ├── docs/
    │   ├── api-notes.md
    │   ├── architecture.md
    │   └── compliance.md
    ├── dsl/
    │   └── tiktok-chat.yml       Full 128KB Dify DSL export
    ├── incidents/
    │   ├── _TEMPLATE.md
    │   ├── GRBT-175.md
    │   ├── GRBT-182.md
    │   └── GRBT-182/             Archived ticket artifacts
    │       ├── scenarios.md       CS-approved restock scenarios (was HTML)
    │       ├── session-state.md   Closed resume file
    │       └── scripts/           phase2.js, phase2-verify.js
    └── scripts/
        └── update-yaml-dsl.py    Reusable: update local YAML from Dify
```

---

## Workspace Repo Structures

### ken-workspace

```
ken-workspace/
├── claude-code-skills/       ← Ken's Claude Code skills
│   ├── commands/              24 .md skill files
│   ├── logs/                  9 learning logs
│   └── memory/                3 memory files
├── claude-skills/            ← Natasha's Claude Code skills (copy)
│   ├── skills/                10 .md skill files
│   └── CLAUDE.md
├── openclaw-skills/          ← Ken's OpenClaw skills
│   └── (16 skill folders, each with SKILL.md)
├── openclaw-workspace/       ← OpenClaw workspace
│   ├── agents/mission-control/
│   ├── admin-ui/
│   ├── captcha-bypass/
│   ├── docs/
│   ├── memory/
│   ├── mission-control/
│   ├── research/
│   └── skills/
├── webapp-multi-agent-workflow-plans/
│   └── MULTI_AGENT_*.md, WEBAPP_PRODUCT_BACKLOG.md
└── README.md
```

### natasha-workspace

```
natasha-workspace/
├── claude-skills/            ← Natasha's Claude Code skills
│   ├── skills/                10 .md skill files
│   ├── CLAUDE.md
│   └── .gitignore
└── openclaw-skills-nat/      ← Natasha's OpenClaw skills
    └── (10 skill folders, each with SKILL.md)
```

---

## Branch Conventions

All repos use `main` as default. Only `awesomeree-web-app` has multiple branches (30+):

| Pattern | Example | Purpose |
|---------|---------|---------|
| `main` | -- | Production |
| `feature/*` | `feature/AW-22-cumulative-sales-ui` | Jira-linked feature dev |
| `feat/*` | `feat/aw-288-compliance-guardrails` | Alternative feature prefix |
| `claude/*` | `claude/fix-designer-request-headers-arUiW` | Claude Code-generated |
| `codex/*` | `codex/history-log-user-attribution` | OpenAI Codex-generated |
| `docs/*` | `docs/restructure-repo-aw-298` | Documentation |
| Named | `OrderManagement`, `Parcel-Split-GRBT` | Direct feature branches |

---

## Quick Navigation Cheatsheet

| I want to... | Repo | Path |
|--------------|------|------|
| Check web app source code | `awesomeree-web-app` | `app/`, `pages/`, `components/` |
| Read web app API routes | `awesomeree-web-app` | `pages/api/` or `app/api/` |
| Check Shopee chatbot DSL | `chatbot-ops` | `shopee/dsl/` |
| Check TikTok chatbot DSL | `chatbot-ops` | `tiktok/dsl/` |
| See chatbot incident history | `chatbot-ops` | `shopee/incidents/` or `tiktok/incidents/` |
| Check chatbot changelogs | `chatbot-ops` | `shopee/CHANGELOG.md` or `tiktok/CHANGELOG.md` |
| Check chatbot compliance rules | `chatbot-ops` | `shopee/docs/compliance.md` or `tiktok/docs/compliance.md` |
| Check chatbot architecture | `chatbot-ops` | `shopee/docs/architecture.md` or `tiktok/docs/architecture.md` |
| Check chatbot backlog | `chatbot-ops` | `shopee/backlog.md` or `tiktok/backlog.md` |
| Find MCP server code | `infra-ops` | `mcp/` |
| Find Ken's Claude Code skills | `ken-workspace` | `claude-code-skills/commands/` |
| Find Ken's OpenClaw skills | `ken-workspace` | `openclaw-skills/` |
| Find Ken's OpenClaw workspace | `ken-workspace` | `openclaw-workspace/` |
| Find Natasha's Claude Code skills | `natasha-workspace` | `claude-skills/skills/` |
| Find Natasha's OpenClaw skills | `natasha-workspace` | `openclaw-skills-nat/` |
| Find Agnes's skills | `agnes-workspace` | `commands/` |
| See multi-agent plans | `ken-workspace` | `webapp-multi-agent-workflow-plans/` |
| Check web app product backlog | `ken-workspace` | `webapp-multi-agent-workflow-plans/WEBAPP_PRODUCT_BACKLOG.md` |

---

## Key Files in awesomeree-web-app

| File | Purpose |
|------|---------|
| `.mcp.json` | MCP server configuration |
| `.swarm-config.yml` | Multi-agent swarm config |
| `CLAUDE.md` | Claude Code project instructions |
| `app.yaml` | Google App Engine deployment |
| `package.json` | Dependencies |
| `middleware.ts` | Auth/routing middleware |
| `jest.config.ts` / `vitest.config.ts` | Test configuration |

---

## GitHub MCP Tool Reference

| Tool | Purpose |
|------|---------|
| `mcp__github__get_file_contents` | Read any file: `owner="it-awesomeree", repo="<name>", path="<file>"` |
| `mcp__github__search_repositories` | Find repos: `query="user:it-awesomeree <keyword>"` |
| `mcp__github__list_issues` | List open issues (7 on web app) |
| `mcp__github__list_pull_requests` | List PRs |
| `mcp__github__search_code` | Search code across all repos |
| `mcp__github__create_or_update_file` | Edit files directly on GitHub |
| `mcp__github__create_pull_request` | Open PRs |
| `mcp__github__push_files` | Push multiple files in one commit |
| `mcp__github__list_branches` | List branches on a repo |
| `mcp__github__list_commits` | View commit history |

**Tip**: Use `path="/"` with `get_file_contents` to list root directory. Use `ref="refs/heads/<branch>"` to read from a specific branch.
