# Shopee Listing Page - Deep Analysis

> Reference doc for all shopee-listing work. Created 25 Feb 2026 from codebase analysis of `it-awesomeree/awesomeree-web-app` (main branch).

---

## 1. Database Tables

### requestDatabase (main DB for shopee-listing)

| Table | Rows | Role |
|---|---|---|
| `new_items` | 563 | Source of truth. One row per product event. Has `product_id`, `product_name_en`, `variation_list_en` (JSON), `variation_list_cn`, `shop`, `launch_type` (469 New Product, 94 New Variation), `date` |
| `shopee_listings` | 1940 | **LEGACY flat table.** One row per variation. The 1688 new_product scraper writes here. Has 1688 columns + n8n columns. Frontend no longer reads from this directly. |
| `shopee_listing_products` | 323 | **NORMALIZED** product-level data. Stores 1688 supplier columns (`1688_*`) and n8n AI output columns (`n8n_*`). Tracks job state. 304 new_product + 19 new_variation. |
| `shopee_listing_variations` | 1940 | **NORMALIZED** one row per variation per product. Has `1688_variation`, `1688_variation_image`, `n8n_variation`, `n8n_variation_image`, `sort_order` |
| `shopee_listing_reviews` | 3 | Staging table for regenerated content. Status: `pending_review` / `approved` / `rejected` |
| `shopee_existing_listing` | 12 | **Used by New Variation flow only.** Stores both 1688 data AND Shopee existing data for variation generation. Has `shopee_product_name`, `shopee_description`, `tier_name_*`, `t*_variation`, etc. |
| `hero_templates` | - | Hero image templates per shop. `shop_name` + `template_url` (GCS URL) |
| `ShopeeTokens` | - | Shop credentials for Shopee API. Has `shop_id`, `shop_name`, `access_token`, `expires_at` |

### allbots DB

| Table | Role |
|---|---|
| `Shopee_Comp` | Competitor data. Linked by `our_item_id`. Has `comp_product`, `comp_price`, `comp_rating`, `comp_monthly_sales`, `comp_shop`, `comp_variation`, `comp_link`, etc. |

---

## 2. Scripts Analysis (`eten-workspace/my_script/`)

### Script 1: `1688_web_scrape_new_product.py` (54KB)

**Purpose**: Scrape 1688 product pages for New Product items and store the data.

| Aspect | Detail |
|---|---|
| **Reads from** | `new_items` (WHERE `launch_type = 'New Product'`), `shopee_listings` (for dedup) |
| **Writes to** | `shopee_listings` (legacy flat table) — **NOT** `shopee_listing_products` |
| **SQL** | `INSERT INTO shopee_listings (product_id, launch_type, 1688_url, 1688_product_name, 1688_variation, 1688_variation_image, 1688_hero, 1688_supporting_image, 1688_product_description_text, 1688_product_description_image, status, item_date)` |
| **Row pattern** | One row PER variation (denormalized — hero/desc duplicated per variation row) |
| **Dedup** | `product_id NOT IN (SELECT product_id FROM shopee_listings)` |
| **Data formats** | `1688_hero` = single URL string, `1688_supporting_image` = `json.dumps(urls)`, `1688_variation` = single string, `1688_variation_image` = single URL |
| **n8n interaction** | None |

### Script 2: `1688_web_scrape_new_variation.py` (60KB)

**Purpose**: Scrape 1688 product pages for New Variation items — variation images + description images.

| Aspect | Detail |
|---|---|
| **Reads from** | `new_items` (WHERE `launch_type = 'New Variation'`), `shopee_existing_listing` (for dedup) |
| **Writes to** | `shopee_existing_listing` |
| **SQL** | `INSERT INTO shopee_existing_listing (product_id, 1688_url, 1688_product_name, 1688_variation, 1688_variation_images, 1688_description_images, item_date, updated_at) VALUES (...) ON DUPLICATE KEY UPDATE ...` |
| **Row pattern** | One row PER 1688 source URL per product_id. All variations stored as JSON arrays in a single row. |
| **Dedup** | Checks `(product_id, 1688_url)` pairs in `shopee_existing_listing` |
| **Data formats** | `1688_variation` = `json.dumps(["var1", "var2"])`, `1688_variation_images` = `json.dumps(["url1", "url2"])`, `1688_description_images` = `json.dumps(["url1", ...])` |
| **n8n interaction** | None |
| **Key difference vs new_product** | Writes to `shopee_existing_listing` not `shopee_listings`. Variations are JSON arrays not separate rows. Does NOT scrape hero/supporting images or description text — only variation images + description images. |

### Script 3: `shopee_api.py` (16KB)

**Purpose**: Fetch our own Shopee listing data (product name, description, tier structure, variation images) from the Shopee Partner API.

| Aspect | Detail |
|---|---|
| **Reads from** | `new_items` (WHERE `launch_type = 'New Variation'`), `ShopeeTokens` (JOIN on `shop = shop_name`) |
| **Writes to** | `shopee_existing_listing` — **UPDATE only, NO INSERT** |
| **SQL** | `UPDATE shopee_existing_listing SET shop_name=%s, shopee_product_name=%s, shopee_description=%s, tier_name_1=%s, t1_variation=%s, shopee_variation_images=%s, tier_name_2=%s, t2_variation=%s WHERE product_id=%s` |
| **Dependency** | Row MUST already exist in `shopee_existing_listing` (created by the 1688 variation scraper). If no matching row, update silently skips. |
| **Shopee API endpoints** | `GET /api/v2/product/get_item_base_info` (batch 50), `GET /api/v2/product/get_model_list` (per item) |
| **Data fetched** | `item_name`, extended description, `tier_variation[0]` (name + options + images), `tier_variation[1]` (name + options) |
| **Data formats** | `t1_variation` = `json.dumps(["Red", "Blue"])`, `shopee_variation_images` = `json.dumps(["url1", "url2"])` (tier 1 images only), `t2_variation` = `json.dumps(["S", "M", "L"])` |
| **Tier handling** | Index-based: tier_name_1 = variations[0].name, tier_name_2 = variations[1].name. Max 2 tiers supported. |
| **Auth** | HMAC-SHA256 signature with partner_id 2012161 |

---

## 3. Current Data Flow (What Actually Happens)

### New Product Path (WORKING)
```
new_items (launch_type = 'New Product', 469 items)
  |
  v
1688_web_scrape_new_product.py
  |  Writes to: shopee_listings (legacy, one row per variation)
  v
[SOME SYNC PROCESS — unknown]
  |  Copies to: shopee_listing_products + shopee_listing_variations (normalized)
  v
Frontend reads from shopee_listing_products + shopee_listing_variations
  |
  v
n8n webhook: /webhook/generate-listing
  |  Reads from: shopee_listing_products + shopee_listing_variations + Shopee_Comp
  v
n8n output written back to shopee_listing_products + shopee_listing_variations
```

### New Variation Path (BROKEN)
```
new_items (launch_type = 'New Variation', 94 items)
  |
  +-----> 1688_web_scrape_new_variation.py
  |         Writes to: shopee_existing_listing (1688 data: variation names + images + desc images)
  |
  +-----> shopee_api.py
  |         UPDATEs: shopee_existing_listing (Shopee data: product name, desc, tiers)
  |         DEPENDENCY: row must already exist (from 1688 scraper above)
  |
  v
shopee_existing_listing (rendezvous table — has both 1688 + Shopee data)
  |
  X  BROKEN: No process syncs this to shopee_listing_products
  X  BROKEN: shopee_listing_products has NO Shopee data columns
  X  BROKEN: Frontend cannot display Shopee existing data
  X  BROKEN: n8n variation webhook cannot get Shopee data from normalized tables
```

---

## 4. Gap Analysis (What's Broken)

### GAP 1: Script writes to WRONG table
- `1688_web_scrape_new_product.py` writes to `shopee_listings` (legacy), NOT `shopee_listing_products`
- There must be a sync/migration process copying data to the normalized tables, but it's not part of these scripts

### GAP 2: `shopee_existing_listing` is disconnected from everything
- Only 12 rows total (vs 94 New Variation items in `new_items`)
- 5 of 12 rows are missing Shopee data (1688 scraper ran but Shopee API didn't update)
- Has duplicate rows (no unique constraint issues but duplicated product_ids)
- Only 2 rows overlap with `shopee_listing_products` (new_variation)
- Frontend page does NOT read from this table
- n8n variation webhook cannot access this data through the normalized service layer

### GAP 3: `shopee_listing_products` missing Shopee data columns
The normalized table has these column groups:
- 1688 data: `1688_url`, `1688_product_name`, `1688_product_description_text`, `1688_product_description_image`, `1688_hero`, `1688_supporting_image`
- n8n output: `n8n_product_name`, `n8n_product_description`, `n8n_hero`, `n8n_supporting_image`
- Job tracking: `n8n_job_status`, etc.

**Missing entirely:**
- `shopee_product_name`
- `shopee_description`
- `shopee_variation_images`
- `tier_name_1`, `t1_variation`
- `tier_name_2`, `t2_variation`

### GAP 4: 19 new_variation items in shopee_listing_products have ZERO data
- All 19 have `n8n_job_status = NULL`
- None have n8n output
- None have a path to get Shopee existing data
- They're visible on the frontend but completely empty

### GAP 5: Shopee API script dependency chain is fragile
- `shopee_api.py` does UPDATE only — if the 1688 scraper hasn't created the row first, the update silently does nothing
- No error reporting or alerting when rows don't match

---

## 5. `shopee_existing_listing` Schema (Current)

```
id                      bigint PK
shop_name               varchar(100)          -- from Shopee API
product_id              bigint (indexed)      -- links to new_items.product_id
1688_url                varchar(500)          -- from 1688 scraper
1688_product_name       varchar(500)          -- from 1688 scraper
1688_variation          json                  -- from 1688 scraper (JSON array of names)
1688_variation_images   json                  -- from 1688 scraper (JSON array of URLs)
1688_description_images json                  -- from 1688 scraper (JSON array of URLs)
shopee_product_name     varchar(500)          -- from Shopee API
shopee_description      longtext              -- from Shopee API
tier_name_1             varchar(100)          -- from Shopee API (e.g. "Colour")
t1_variation            json                  -- from Shopee API (JSON array of option names)
shopee_variation_images json                  -- from Shopee API (tier 1 image URLs)
tier_name_2             varchar(100)          -- from Shopee API (e.g. "Size")
t2_variation            json                  -- from Shopee API (JSON array of option names)
n8n_variation           json                  -- n8n output (JSON array)
n8n_description         longtext              -- n8n output
n8n_variation_images    json                  -- n8n output (JSON array)
created_at              datetime
updated_at              datetime
item_date               date
```

---

## 6. File Structure (awesomeree-web-app repo)

### Route
```
app/inventory/shopee-listing/page.tsx
  -> Just wraps <ShopeeListingPage /> with Suspense
```

### Frontend Components
```
components/shopee-listing/
  page.tsx                     # 72KB - Main orchestrating component (the whole page UI)
  FilterBar.tsx                # Region (MY/SG) + Type (new_product/new_variation) toggle buttons
  ActivityPanel.tsx            # Side sheet showing global activity log
  ComparisonDialog.tsx         # Side-by-side current vs regenerated comparison dialog
  GenerateConfirmDialog.tsx    # Confirmation dialog before generate/regenerate
  TemplateLibraryDialog.tsx    # Hero template browse/upload dialog
  AuditHintTooltip.tsx         # Tooltip showing last audit entry on action buttons
  ErrorBoundary.tsx            # React error boundary wrapper
  sub-components.tsx           # StatusDot, ImageGallery, DescriptionBlock
  utils.ts                    # Constants, helpers, type re-exports
```

### Frontend Hooks
```
components/shopee-listing/hooks/
  useProductList.ts            # Product list fetch, client-side search/sort/pagination
  useProductDetail.ts          # Selected product detail fetch, variation selection
  useGenerateFlow.ts           # Generate/regenerate/staging review state machine (17KB)
  useFilterState.ts            # URL-synced region/type filters via useSearchParams
  useActivityLog.ts            # Activity log fetch with filters
  useActionAudit.ts            # Per-product audit trail with hints
  useDebounce.ts               # Generic debounce hook (300ms default)
```

### API Routes
```
app/api/shopee-listings/
  route.ts                     # GET - summary list or single product detail
  generate/route.ts            # POST - trigger n8n generation/regeneration
  staging/route.ts             # POST - approve/reject regenerated content
  templates/route.ts           # GET + POST - hero template management
```

### Backend Service Layer
```
lib/services/shopee-listings/
  index.ts                     # Barrel re-exports
  generate.ts                  # 45KB - Main orchestration (summary, detail, generate logic)
  db.ts                        # MySQL connections, table constants, query executors
  staging.ts                   # Approve/reject transactional logic
  n8n-webhook.ts               # n8n webhook caller + response parser
  job-tracker.ts               # Mutex/locking, job state management
  normalizers.ts               # 38KB - All data normalization (images, strings, categories)
  types.ts                     # Backend TypeScript types
```

---

## 7. API Endpoints

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/shopee-listings` | GET | None | Fetch product list (summary) or single product detail |
| `/api/shopee-listings/generate` | POST | None | Trigger n8n AI generate/regenerate |
| `/api/shopee-listings/staging` | POST | None | Approve/reject regenerated content |
| `/api/shopee-listings/templates` | GET | None | List hero templates |
| `/api/shopee-listings/templates` | POST | Firebase session | Upload hero template image to GCS |

---

## 8. n8n Integration

### Webhook Endpoints
| Flow | URL | Item Type |
|---|---|---|
| Generate | `https://n8n.barndoguru.com/webhook/generate-listing` | new_product |
| Regenerate | `https://n8n.barndoguru.com/webhook/regenerate-listing` | new_product |
| Variation Generate | `https://n8n.barndoguru.com/webhook/generate-variation-listing` | new_variation |
| Variation Regenerate | `https://n8n.barndoguru.com/webhook/regenerate-variation-listing` | new_variation |

### New Product Payload (to n8n)
```json
{
  "product_id": "123456",
  "product_name_1688": "Original Chinese product name",
  "description_1688": "Original description text",
  "hero_images": ["https://..."],
  "variation_images": ["https://..."],
  "description_images": ["https://..."],
  "supporting_images": ["https://..."],
  "variations_1688": ["Color A", "Color B"],
  "competitors": [{ "product_name": "...", "description": "...", "variations": [...] }],
  "shop_name": "MyShop",
  "hero_template_url": "https://storage.googleapis.com/...",
  "targets": ["all"]
}
```

### New Variation Payload (to n8n — NEEDS Shopee existing data)
The variation webhook needs ADDITIONAL fields not currently in the normalized schema:
- `shopee_product_name` — our existing Shopee listing name
- `shopee_description` — our existing Shopee description
- `shopee_variation_images` — our existing variation images
- `tier_name_1`, `t1_variation` — tier 1 structure
- `tier_name_2`, `t2_variation` — tier 2 structure
- `1688_variation` — new 1688 variation names (JSON array)
- `1688_variation_images` — new 1688 variation images (JSON array)
- `1688_description_images` — 1688 description images (JSON array)

### n8n Variation Output
- `n8n_variation` — generated variation names
- `n8n_description` — generated description
- `n8n_variation_images` — generated variation images

---

## 9. Key Frontend Types

```typescript
ListingProductSummary {
  id, productId, productName, heroImage,
  region, itemType, category, itemDate,
  variationCount, readyVariationCount,
  hasOptimizedContent, n8nJob: ListingJobState,
  competitorCount, ourShopName
}

ListingProductDetail extends ListingProductSummary {
  variations: ListingVariation[],
  competitors: Competitor[],
  heroTemplateUrl,
  regeneratedData?: ListingRegeneratedData
}

ListingVariation {
  id, name, n8nStatus: "ready"|"pending"|"generating",
  supplier: ListingContent,       // 1688 data
  optimized?: ListingContent,     // n8n output
  competitors: Competitor[]
}

ListingContent {
  productName, variation, price?,
  description?, descriptionImages?,
  heroImage?, supportingImages?,
  variationImages?, url?
}
```

---

## 10. Key Design Patterns

- **Single-job mutex**: Only one product can be generating at a time globally (enforced via `FOR UPDATE` row locking in `claimProductForProcessing()`)
- **Stale job recovery**: Jobs stuck in "processing" > 45 minutes are auto-failed on next request
- **Variation count fallback** (PR #334): When `shopee_listing_variations` has no rows (pre-n8n processing), falls back to parsing `new_items.variation_list_en`
- **Null product ID guard** (PR #335): Products without `product_id` are dimmed and unclickable
- **Selected row highlight** (PR #336): Clicked row gets `bg-muted/60`
- **Connection-per-query**: Each DB operation opens/closes its own MySQL connection
- **Regeneration staging**: Regen results go to `shopee_listing_reviews` first, not directly applied. Requires explicit approve/reject with field-level selection.

---

## 11. UI Structure (Master-Detail Pattern)

### Left Panel (Product List)
- Header: "Shopee Listing" title + stats badges
- FilterBar: Region (ALL/MY/SG), Type (ALL/New Product/New Variation)
- Search input (debounced 300ms, client-side filter on name/id)
- Toolbar: History button (ActivityPanel), Library button (TemplateLibraryDialog)
- Table with sortable columns: Product, Variations (ready/total), n8n Coverage (%), Competitors, Date
- Pagination: 10 per page, prev/next buttons

### Right Panel (Product Detail - shown on row click)
- Header: back button, product name, "Generate All" button
- n8n status banner (processing spinner / failed error / completed)
- Variation sidebar: search + list with StatusDot (green=ready, blue=generating, amber=pending)
- Per-variation content (3 accordions):
  - Supplier Data (amber) - 1688 originals
  - Optimized / AI Output (indigo) - n8n output with current/regenerated toggle
  - Competitors (rose) - competitor listings
- Regenerate panel: checkboxes per field + regenerate button
- Staging review banner when pending regenerated data exists

### Dialogs
- GenerateConfirmDialog - confirmation before generate/regenerate
- ComparisonDialog - side-by-side current vs regenerated
- TemplateLibraryDialog - hero template browse/upload
- ActivityPanel - side sheet with filtered activity log
