# Skills & Knowledge Reference — Eten

Consolidated reference of skills, tools, and domain knowledge for my three development areas.

---

## Web App Development

### Tech Stack
| Technology | Version | Role |
|-----------|---------|------|
| React | 19 | UI framework |
| Next.js | 15 | Full-stack framework (App Router) |
| TypeScript | 5 | Type safety |
| Tailwind CSS | 4 | Utility-first styling |
| shadcn/ui | latest | Component library |
| MySQL | 8.4 | Primary database (Cloud SQL) |
| Firebase | — | Auth, storage |
| Google Cloud App Engine | — | Hosting/deployment |

### Key Patterns
- **App Router** (Next.js 15) — `app/` directory structure with layouts, pages, loading states
- **Server Components** by default, `"use client"` only when needed (interactivity, hooks, browser APIs)
- **Server Actions** for form submissions and mutations
- **API Routes** at `app/api/` for external integrations
- **Tailwind + shadcn/ui** for consistent design — use existing components before creating new ones

### Database (MySQL)
- **5 databases**, ~220 tables across 13 domains
- Key domains: competitor analysis, inventory, orders, sales, customer service, products, pricing, chatbot, TikTok, Shopee automation
- Reference: `/mysql-schema` for full schema documentation

### Webapp Workflow
1. Study Jira ticket → understand requirements
2. Study the system → trace relevant code paths
3. Implement → follow existing patterns
4. Self-review → correctness, security, performance
5. PR to `test` branch → never directly to `main`
6. Move ticket to TO REVIEW → add comment explaining work done
7. Wait for Agnes's review → fix any rework items

---

## n8n Workflow Automation

### Instance
- **URL**: `https://n8n.barndoguru.com`
- **Version**: 2.35.2
- **Total Workflows**: 43 (6 active)

### Key Workflows I Work With
| Workflow | ID | Nodes | Purpose |
|----------|----|-------|---------|
| Webhook Regenerate V2 | `M6wBk9TCuMohMByU` | 55 | Active — regeneration webhook |
| Variation & Description v4 | `_nYkX49YkTfTdwWTsDjM1` | 25 | Webhook + GCS + MySQL persistence |
| Shopee MY Listing Generator v10 | `D4V7jNP8l-5IbP0dM7qui` | 41 | Fixed loops version |
| Shopee MY Listing Generator v14 | `pIvGDAL-kJuyECws7EeFX` | 23 | No loops version |

### Variation Generator v4 — Quick Reference
- **Dual entry**: Form upload (manual Excel) + Webhook (webapp POST)
- **Webhook URL**: `https://n8n.barndoguru.com/webhook/generate-variation-description`
- **AI services**: Gemini 2.5 Flash (image OCR/profiling), Gemini 3 Pro (image gen), GPT-5.2 (variation names + descriptions)
- **Output**: MySQL `shopee_existing_listing` table + GCS `shopee-listing-images` bucket
- **Columns written**: `n8n_variation`, `n8n_description`, `n8n_variation_images`, `updated_at`

### n8n MCP Tools
| Tool | Purpose |
|------|---------|
| `n8n_health_check` | Instance status |
| `n8n_list_workflows` | List all workflows |
| `n8n_get_workflow` | Get workflow details (full/structure/details/minimal) |
| `n8n_update_partial_workflow` | Update specific nodes/settings |
| `n8n_validate_workflow` | Validate before deploy |
| `n8n_test_workflow` | Test execution |
| `n8n_executions` | View execution history |

---

## VM Bot Scripts

### Infrastructure
- **Total VMs**: 17 (16 active, 1 offline)
- **Total Bots**: 29
- **Gateway**: 100.86.32.62 (Tailscale VPN)
- **OS**: All Windows
- **Source code**: `it-awesomeree/bot-scripts`

### VMs by Role
| Role | VMs | Bot Count |
|------|-----|-----------|
| Chatbot | VM CBMY, VM CBC3, VM CBSG | 5 |
| Parcel Claim | VM-8, VM3, VM 9 | 7 |
| Order | VM1, VM OD | 4 |
| Scheduler | nisv, VM2, VM5, VM TT | 6 |
| Scraper | VM4, VM6, VM10 | 5 |
| Database | Kaushal SQL Machine | 0 |

### Chatbot Middleware Architecture
Two-layer system:
1. **Layer 1**: Node.js/Puppeteer middleware on VMs — reads Shopee chat DOM, builds structured query, POSTs to Dify API
2. **Layer 2**: Dify workflow — processes query, generates response

**Key insight**: If middleware sends wrong input → Dify produces wrong output (even if workflow is perfect).

### VM MCP Tools
| Tool | Purpose |
|------|---------|
| `vm_inventory` | List VMs / filter by role |
| `vm_status` | CPU, memory, uptime, processes |
| `vm_processes` | Detailed process list |
| `vm_configs` | Read JSON configs from VM |
| `vm_schedules` | Active scheduled tasks |
| `vm_read_file` | Read file from VM |
| `vm_execute` | Run command on VM |
| `vm_task_control` | Start/stop/restart bots |
| `vm_multi_status` | Bulk health check |

---

## Jira Quick Reference

- **AW Board**: `https://awesomeree.atlassian.net/jira/software/projects/AW/boards/34`
- **GRBT Board**: `https://awesomeree.atlassian.net/jira/software/projects/GRBT/boards/35`
- **My assignee name**: `eten`
- **Columns**: TO DO → IN PROGRESS → TO REVIEW → DONE → BLOCKED
- **TO REVIEW** is Agnes's review column — submit work there with a comment

---

## GitHub Repos

| Repo | Purpose |
|------|---------|
| `it-awesomeree/awesomeree-webapp` | Main web application |
| `it-awesomeree/bot-scripts` | VM bot scripts and chatbot middleware |
| `it-awesomeree/shopee-chatbot-ops` | Shopee chatbot operations |
| `it-awesomeree/tiktok-chatbot-ops` | TikTok chatbot operations |
| `Eten24/eten-workspace` | This workspace — skills, notes, docs |
