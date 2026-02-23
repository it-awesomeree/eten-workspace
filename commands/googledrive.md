# Google Drive Map — Agnes's Personal Drive

Agnes's Google Drive (`agnes.awesomeree@gmail.com`) — full recursive map.
**Last mapped**: 2026-02-16 | **Stats**: 420 folders, ~2,800 files, 3,301 lines

## MCP Access

- **MCP Server**: `google-workspace` in `~/.mcp.json`
- **Package**: `workspace-mcp` v1.11.2 (venv at `~/.local/google-workspace-mcp-venv/`)
- **GCP Project**: `agnes-487612` (personal account, NOT company deeptest-449907)
- **OAuth Client**: "Workspace MCP" (Desktop app)
- **Credentials**: `~/.google_workspace_mcp/credentials/agnes.awesomeree@gmail.com.json`
- **Keychain**: `google-workspace-mcp` (client-id + client-secret)
- **Scope**: `drive.readonly` (read-only mode)
- **Full map file**: `/Users/user/.local/drive-map.txt`

### CLI Usage
```bash
export GOOGLE_OAUTH_CLIENT_ID=$(security find-generic-password -s google-workspace-mcp -a client-id -w)
export GOOGLE_OAUTH_CLIENT_SECRET=$(security find-generic-password -s google-workspace-mcp -a client-secret -w)
MCP="/Users/user/.local/google-workspace-mcp-venv/bin/workspace-mcp"

# List root items
$MCP --tools drive --read-only --single-user --cli list_drive_items --args '{"user_google_email":"agnes.awesomeree@gmail.com"}'

# List specific folder
$MCP --tools drive --read-only --single-user --cli list_drive_items --args '{"folder_id":"FOLDER_ID","user_google_email":"agnes.awesomeree@gmail.com"}'

# Search files
$MCP --tools drive --read-only --single-user --cli search_drive_files --args '{"query":"name contains \"keyword\"","user_google_email":"agnes.awesomeree@gmail.com"}'
```

### Re-map Script
```bash
python3 /Users/user/.local/drive-mapper.py
```

---

## Root Level (67 items: 20 folders, 47 files)

### Bot Script Folders
| Folder | Contents | Purpose |
|--------|----------|---------|
| `Order Management Bot 2/` | 1 Python script | OM_Bot_2.py |
| `Costing Bot 2/` | 1 Python script + .env | costing_product_name_and_stock.py |
| `New Item Bot 1/` | 2 Python scripts | new_item_bot_1.py + updated version |
| `New Item Bot 2/` | 1 Python script | new_item_bot_2.py |
| `NI/SV Reorder Updater/` | 1 Python script | nisv_reorder.py |
| `Inventory Sync/` | 1 Python script | PKSU_SYNC.py |
| `Inventory (PSKU -> Shop)/` | 1 Python script | Inventory_Shop_Resolver.py |
| `STS & STT Bot/` | 4 Python scripts | Gemini, lowRating, transcribe |
| `Error Check Scripts/` | 2 Python scripts | return + new_items error check |

### Parcel Claim Folders
| Folder | Contents |
|--------|----------|
| `Parcel Claim Kinata/` | 2 Python scripts + 2 text files |
| `Parcel Claim: Failed Delivery/` | 1 Python script + 1 text file |
| `Shopee SG Parcel Claim/` | 1 Python script |
| `Shopee SG Parcel Claim ( New Record )/` | 3 Python scripts + 1 text file |

### Other Root Folders
| Folder | Contents |
|--------|----------|
| `Jimmy's Drive/` | Order mgmt scripts, costing sheets, misc docs |
| `BahEmas/` | 12 Shopee invoice PDFs (2025-06 to 2025-12) |
| `Meet Recordings/` | 3 items (video recordings + chat) |
| `Old Google Sheets/` | 33 archived sheets (bots, analytics, stock count) |
| `Mahmoud Aljaziri Interview/` | 2 MOV videos |
| `Shunyang/` | 9 incorporation/registration PDFs |

### Root Files (47 files — not in any folder)
Mostly: spreadsheets (daily reports, costing, candidates), PDFs (resumes, job apps, transcripts), and a few docs.

Key root files:
- `Kaushal's 17th Cycle` (Sheet) — most recently modified
- `Laptop & CCTV Trackers` (Sheet)
- `AW-288 Compliance Guardrails — Test Matrix` (Sheet)
- `TikTok Account Health-Updated` (Sheet)
- Various candidate assessment response sheets
- Various candidate resume/transcript PDFs

---

## Awesomeree/ (Main Company Folder)

The largest folder — contains all company operations.

### Awesomeree/ → Draft/
14 Google Docs — draft letters/messages (Upwork, HR, recruitment)

### Awesomeree/ → Upwork/
- `Website/` — Brand assets (favicons, headers, logos for Awesomeree, Shopee, TikTok, Lazada, client brands)
- Sample sheets and talent tracking

### Awesomeree/ → Jahan/
13 sheets — Competitor analysis, bot roster, costing, sales databases, analytics

### Awesomeree/ → Agnes/
- `Daily Meeting Minutes/` — 9 meeting docs (2025-11 to 2026-01)
- `Template Message/` — Recruitment WhatsApp template + AI job ad
- `Daily Report/` — Monthly report sheets from 2024/12 to 2026/02
- Misc docs: profit counting steps, prompts, proposals

### Awesomeree/ → Work/
**The operational hub.** Major subfolders:

#### Work/ → Password/
9 sheets — **ALL company login credentials** (Awesomeree Logins, Company Email, Anydesk, IT Logins, Admin Logins, etc.)

#### Work/ → Brands/ (deep)
| Brand | Contents |
|-------|----------|
| `Lenza Eyewear/` | Product images organized by date (11 subfolders) + master sheet |
| `Roar Plunge/` | QC doc |
| `SEO/` | 6 audit reports (XLSX/DOCX) for MRYC, Barndo Guru, Cuebera |
| `CollabX/` | Empty media folder |
| `Roar Commerce/` | AI logo designs (11 images) + logo files |
| `Bardominium/` | Web content QC + strategy slides |
| `My Recipe, You Cook/` | Recipe docs, SEO checklists, website setup docs |
| `Cuebera/` | Product images (pool tables), price list, website docs, proposals |
| `Luxbin/` | Website docs + checklist |
| `Awesomation/` | Website PRD |
Plus: Scrape to SQL checklist, Brand Indexing slides, SEO workflow docs

#### Work/ → Bank/
7 items — SG Fintech comparison, SC cash withdrawal, HLB checklist/resolution, Maybank email update, capital funding

#### Work/ → Admin/
- `2025 Annual Dinner/` — 4 items (sheet, menu, 2 slide decks)
- HR January sheet, website content, bot report template, HK registration, laptop tracker

#### Work/ → Government/ (deep)
| Sub-path | Contents |
|----------|----------|
| `DBKL/Premise License [Janamuda]/` | 3 PDFs (license copies) |
| `DBKL/Premise License [Awesomeree]/` | 2025 + 2026 license renewals (8 PDFs) |
| `Company/Roar Commerce SG/` | 9 PDFs (OCBC, incorporation docs) |
| `Company/Natken/` | Natken docs (7 PDFs) + MDEC application |
| `Company/Awesomeree/` | Incorporation docs, KWSP, tenancy + TalentCorp + MDEC |
| `Company/Awesomeree/TalentCorp/LiKES/` | 5 intern claim submissions (Nisha, Poh, Angel, Jin Ming, Zhi Yang) |
| `Company/Awesomeree/MDEC/` | MYFutureJobs, EXpats (hiring reports, ICT app), MD Tax Incentive, MD Status |
| `Company/Janamuda/` | 18 PDFs (incorporation, SSM, M&A) + MIDA application |
| `IC Copy/` | 5 items (IC copies for Agnes, Jess, Ken, Natasha) |

#### Work/ → Social Media/
- `LinkedIn/` — 4 social media post docs
- `Website/Luxbin/` — Domain invoice
- TikTok sub-accounts + user accounts sheets

#### Work/ → HR/ (very deep — ~1,600 lines)
**Largest section.** Contains ALL recruitment materials.

| Sub-path | Contents |
|----------|----------|
| `Recruitment/Awesomeree Recruitment/` | Google Form response folders (AI, Frontend, Backend, PA, Marketing, CS interns) |
| `Recruitment/.../AI Developer — Prescreen Form/` | 11+ candidate docs each in transcript/SPM/resume/form folders |
| `Recruitment/.../Backend Developer Strong Match/` | Hiredly (40+), SEEK (4), LinkedIn (50+) resumes |
| `Recruitment/.../Job Ad/` | 6 job ad docs |
| `Recruitment/.../Backend Developer — Prescreen Form/` | 11+ candidate submissions |
| `Recruitment/.../Frontend Developer Intern — Prescreen/` | Candidate submissions |
| `Recruitment/.../Senior Python Developer — Prescreen/` | Candidate submissions |
| `Recruitment/Janamuda/...` | Similar prescreen forms for Janamuda roles |
| `Accounts HR/` | Timesheets (2025/01-12), payslips, leave records, offer letters |
| `IT HR/` | IT-specific HR docs (contracts, timesheets, performance reviews) |

#### Work/ → Finance/
- `Invoice/` — Invoices organized by company (Awesomeree, Natken, Janamuda, Shunyang) with monthly subfolders
- `Natken/` — Tax computation, financial statements
- `Payment/` — Payment proof organized by company

#### Work/ → Warehouse/
- `SOP/` — 3 SOP docs + 1 slides
- `Store Count/` — Store count sheets by month + packaging checklist

#### Work/ → Meeting/
Meeting docs (Agnes-Ken), weekly sales reports

#### Work/ → Media/
Media files (images, videos for brands)

#### Work/ → IT Team/
- `Agnes/` — Assessment forms, interview sheets, Claude sessions, technical tests
- `Interview/` — Interview recordings organized by candidate

#### Work/ → Interview/
More interview recordings, trial task responses

### Awesomeree/ → Personal/
- `Company Invoice/` — Personal company invoices
- `Property/` — 24+ property-related documents
- `20251021 Driver cum Bodyguard/` — 9 candidate documents
- `Meeting Agenda/` — 4 meeting docs
- `Darwin Trip/` — 4 trip documents

---

## Quick Navigation

| I want to find... | Path |
|-------------------|------|
| Bot scripts | Root level folders (Order Mgmt Bot, Costing Bot, etc.) |
| Company passwords/logins | `Awesomeree/Work/Password/` |
| Daily reports | `Awesomeree/Agnes/Daily Report/` |
| Meeting minutes | `Awesomeree/Agnes/Daily Meeting Minutes/` |
| Recruitment/resumes | `Awesomeree/Work/HR/Recruitment/` |
| Job ads | `Awesomeree/Work/HR/Recruitment/.../Job Ad/` |
| Government docs | `Awesomeree/Work/Government/` |
| Company incorporation | `Awesomeree/Work/Government/Company/` |
| MDEC/EXpats | `Awesomeree/Work/Government/Company/Awesomeree/MDEC/` |
| TalentCorp/LiKES | `Awesomeree/Work/Government/Company/Awesomeree/TalentCorp/LiKES/` |
| Invoices | `Awesomeree/Work/Finance/Invoice/` |
| Brand assets | `Awesomeree/Work/Brands/` |
| Lenza Eyewear images | `Awesomeree/Work/Brands/Lenza Eyewear/` |
| Bank documents | `Awesomeree/Work/Bank/` |
| Annual dinner | `Awesomeree/Work/Admin/2025 Annual Dinner/` |
| Old bot sheets | `Old Google Sheets/` |
| Shopee invoices | `BahEmas/` |
| Upwork/freelancer | `Awesomeree/Upwork/` |
| HR timesheets/payslips | `Awesomeree/Work/HR/Accounts HR/` |
| IT team assessments | `Awesomeree/Work/IT Team/Agnes/` |
| Premise licenses | `Awesomeree/Work/Government/DBKL/` |
| Warehouse SOPs | `Awesomeree/Work/Warehouse/SOP/` |
