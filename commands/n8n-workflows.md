---
description: n8n automation platform - 43 workflows with deep dive on Shopee Listing New Variation Generation (Webhook + DB)
argument-hint: [workflow name, node, or what you're looking for]
---

# n8n Automation Platform

**Instance URL**: `https://n8n.barndoguru.com`
**Version**: 2.35.2
**Owner**: Agnes Foong (agnes@awesomeree.com.my)
**Total Workflows**: 43 (6 active)

---

## Active Workflows

| ID | Name | Nodes |
|----|------|-------|
| `6-RFpehM68nSiWt0uXbi8` | Webhook Test | 50 |
| `M6wBk9TCuMohMByU` | Webhook Regenerate V2 | 55 |
| `GqJsW8Zyiog87e5P` | Claude Code MCP Server | 1 |
| `QQDXSloFxsea6gAN` | PDF to Audio (Form Trigger + Custom HTML) | 9 |
| `elADIbj6TugH4r10` | Transcript Notes | 13 |
| `uWTOnir2FFROMCpn` | Frontend Form | 4 |

---

## Variation Generator Family (Evolution)

| Version | ID | Nodes | Status | Notes |
|---------|----|-------|--------|-------|
| v1 | `9LPwZozvCtFVXvnwLz9Q1` | 18 | Inactive | Original "Variation & Description" |
| v2 | `L4thBW21QnO3FILw` | 16 | Inactive | |
| v3 | `Yb0pwv7T4JKggqLfFUuHw` | 17 | Inactive | |
| **Shopee Listing New Variation Generation** | `_nYkX49YkTfTdwWTsDjM1` | **25** | **Inactive** | Added webhook + GCS + MySQL persistence |
| Description Only | `IfnGkVJvKFWf0PReAO7XA` | 17 | Inactive | Description-only variant |
| Webhook Regenerate | `6LdPkAKOYDDozU1M6yiLQ` | 55 | Inactive | Regeneration variant |
| Webhook Regenerate V2 | `M6wBk9TCuMohMByU` | 55 | **Active** | Latest regeneration |

---

## Deep Dive: Shopee Listing New Variation Generation

**Workflow ID**: `_nYkX49YkTfTdwWTsDjM1`
**Created**: 2026-02-05 | **Updated**: 2026-02-12 | **Version**: 9

### Dual Entry Points

**Entry 1 - Form Upload (Manual)**:
- URL: `https://n8n.barndoguru.com/form/d2f03224-28ce-46e3-bd02-2a6ceae26933` (when active)
- Accepts: `.xlsx` / `.xls` file upload
- Output: ZIP file (variation names + descriptions + images)

**Entry 2 - Webhook (Webapp)**:
- URL: `https://n8n.barndoguru.com/webhook/generate-variation-description` (when active)
- Test URL: `https://n8n.barndoguru.com/webhook-test/generate-variation-description`
- Method: POST with JSON body
- Output: Persists to MySQL + Google Cloud Storage

### Webhook Input Parameters (POST body)

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | number | Shopee product ID |
| `shop_name` | string | Shop name |
| `1688_product_name` | string | 1688 supplier product name |
| `1688_variation` | JSON array | 1688 variation names |
| `1688_variation_images` | JSON array | 1688 variation image URLs |
| `1688_description_images` | JSON array | 1688 description image URLs |
| `shopee_product_name` | string | Existing Shopee product name |
| `shopee_description` | string | Existing Shopee description |
| `tier_name_1` / `t1_variation` | string / array | Tier 1 variation |
| `tier_name_2` / `t2_variation` | string / array | Tier 2 variation |
| `shopee_variation_images` | JSON array | Existing Shopee variation images |

### All 25 Nodes

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | Upload Excel Form | formTrigger | Manual Excel upload trigger |
| 2 | Get Binary | code | Extract Excel binary |
| 3 | Parse Excel | spreadsheetFile | Parse .xlsx to JSON |
| 4 | Process Excel Data | code | Structure 1688 + Shopee rows |
| 5 | Webhook Trigger | webhook | POST webhook for webapp |
| 6 | Parse Webhook Data | code | Parse JSON body |
| 7 | SET API KEY | set | Inject Gemini + OpenAI API keys |
| 8 | Extract Description Image Info | code | Gemini Vision: extract specs from 1688 images |
| 9 | Filter Relevant Shopee Images | code | Gemini Vision: compare 1688 vs Shopee images |
| 10 | Generate Variation Names | httpRequest | OpenAI GPT-5.2: variation name comparison |
| 11 | Extract Variation Names | code | Parse OpenAI response |
| 12 | Generate Description | httpRequest | OpenAI GPT-5.2: bilingual EN+BM description |
| 13 | Extract Description | code | Parse description with Shopee template fallback |
| 14 | Process Variations | code | Gemini: generate variation images |
| 15 | Validate Variations | code | Validation stub (future logic) |
| 16 | Merge Text Results | merge | Merge variation images + description |
| 17 | Finalize Package | code | Assemble txt + images into binary |
| 18 | ZIP | compression | Compress to downloadable ZIP |
| 19 | Done (Form) | set | Final response for form path |
| 20 | Prepare GCS Uploads | code | Prepare images for GCS upload |
| 21 | Upload Images Loop | splitInBatches | Iterate images for batch upload |
| 22 | Upload to GCS | httpRequest | Upload to GCS bucket |
| 23 | Prepare MySQL Data | code | Build UPDATE SQL |
| 24 | Update MySQL | mySql | UPDATE `shopee_existing_listing` table |
| 25 | Done DB (Webhook) | set | Final confirmation for webhook path |

### Execution Flow

```
FORM PATH:                          WEBHOOK PATH:
Upload Excel -> Get Binary          Webhook Trigger (POST)
  -> Parse Excel                      -> Parse Webhook Data
  -> Process Excel Data                      |
            |                                |
            +---------- CONVERGE -----------+
                           |
                    SET API KEY (Gemini + OpenAI)
                           |
              Extract Description Image Info (Gemini Vision)
                           |
              Filter Relevant Shopee Images (Gemini Vision)
                           |
              Generate Variation Names (GPT-5.2)
                           |
              Extract Variation Names
                    /              \
          [BRANCH A]            [BRANCH B]
       Process Variations     Generate Description (GPT-5.2)
       (Gemini image gen)     Extract Description
       Validate Variations            |
                    \              /
                  Merge Text Results
                  Finalize Package
                    /              \
            [FORM OUTPUT]      [WEBHOOK OUTPUT]
            ZIP -> Done        Prepare GCS Uploads
                               Upload Images Loop
                               Upload to GCS
                               Prepare MySQL Data
                               Update MySQL -> Done DB
```

### External Services

| Service | Model/Bucket | Purpose |
|---------|-------------|---------|
| Google Gemini | gemini-2.5-flash-image | Image OCR, product profiling, image relevance |
| Google Gemini | gemini-3-pro-image-preview | Variation image generation (1024x1024) |
| OpenAI | gpt-5.2 | Variation name comparison + bilingual descriptions |
| Google Cloud Storage | `shopee-listing-images` bucket | Store generated variation images |
| MySQL | `shopee_existing_listing` table | Read/write product listing data |

### Database Columns Written

| Column | Content |
|--------|---------|
| `n8n_variation` | JSON array of generated variation names |
| `n8n_description` | Bilingual EN+BM description text |
| `n8n_variation_images` | JSON array of GCS public URLs |
| `updated_at` | NOW() |

**GCS URL pattern**: `https://storage.googleapis.com/shopee-listing-images/{product_id}/variations/variation_{N}.png`

### Key Config Values

- Max 1688 description images: 13
- Max image size: 4MB
- Download timeout: 15,000ms
- Max Shopee reference images: 3
- Variation image gen retries: 3 (2s delay)
- OpenAI timeout: 60s (variation), 120s (description)
- Gemini image gen timeout: 180s
- `continueOnFail` enabled on: most AI nodes

### Security Note
API keys (Gemini + OpenAI) are hardcoded in the SET API KEY node. Consider migrating to n8n credentials.

---

## Other Notable Workflows

| Name | ID | Nodes | Purpose |
|------|----|-------|---------|
| Shopee MY Listing Generator v10 | `D4V7jNP8l-5IbP0dM7qui` | 41 | Fixed loops version |
| Shopee MY Listing Generator v14 | `pIvGDAL-kJuyECws7EeFX` | 23 | No loops version |
| Boss Prompt | `DoL6M4-9dPabQZhU89sAg` | 26 | Boss-customized prompt |
| Screen & Voice to Engineering Prompt | `wHcgSSyAZU59ymxT` | 11 | Voice-to-prompt |
| PDF to Audio | `QQDXSloFxsea6gAN` | 9 | Active: PDF conversion |

---

## n8n MCP Tool Reference

| Tool | Purpose |
|------|---------|
| `n8n_health_check` | Instance status: `mode="status"` |
| `n8n_list_workflows` | List all workflows: `limit=100` |
| `n8n_get_workflow` | Get workflow details: `id="<id>", mode="full"/"structure"/"details"/"minimal"` |
| `n8n_update_partial_workflow` | Update specific nodes/settings |
| `n8n_update_full_workflow` | Replace entire workflow |
| `n8n_validate_workflow` | Validate before deploy |
| `n8n_autofix_workflow` | Auto-fix issues |
| `n8n_test_workflow` | Test execution |
| `n8n_executions` | View execution history |
| `n8n_workflow_versions` | View version history |
| `search_nodes` | Search available n8n node types |
| `get_node` | Get node documentation |
